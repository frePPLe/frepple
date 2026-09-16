/*
 * Copyright (C) 2026 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 *
 */

/*
 * Reusable tooltip directive with the same style and behavior as the
 * Django (Bootstrap/Popper) tooltips initialized in
 * freppledb/common/templates/admin/base.html:
 *   container 'body', trigger 'hover', delay {show: 500, hide: 100}.
 *
 * Usage:
 *   <button v-tooltip="ttt('Save changes')">…</button>
 *   <span v-tooltip="{ title: row.description, placement: 'left' }">…</span>
 *
 * The directive honors per-element `data-bs-placement`, `data-bs-html`
 * and `data-bs-delay` attributes, so existing markup keeps working while
 * migrating. Falsy values (null, undefined, false, '') disable the tooltip.
 *
 * Note: an element with data-bs-toggle="dropdown" cannot also carry a
 * Bootstrap tooltip (Bootstrap limitation). Wrap such elements in a span
 * and put v-tooltip on the wrapper instead. When the wrapper owns a
 * dropdown menu, the tooltip is automatically suppressed while the menu
 * is open (via show.bs.dropdown / hide.bs.dropdown).
 */

const DEFAULT_DELAY = { show: 500, hide: 100 };

function normalizeOptions(value) {
  return typeof value === "string" ? { title: value } : { ...(value || {}) };
}

function resolveTitle(el, opts) {
  return (
    opts.title ??
    el.getAttribute("data-bs-title") ??
    el.getAttribute("title") ??
    ""
  );
}

function resolveDelay(el, opts) {
  if (el.hasAttribute("data-bs-delay")) {
    try {
      return JSON.parse(el.getAttribute("data-bs-delay"));
    } catch (e) {
      // Fall through to Django-compatible defaults on malformed input
    }
  }
  return opts.delay !== undefined ? opts.delay : { ...DEFAULT_DELAY };
}

function signature(el, value) {
  const opts = normalizeOptions(value);
  return JSON.stringify([
    resolveTitle(el, opts),
    opts.placement ?? el.getAttribute("data-bs-placement") ?? "top",
    opts.trigger ?? "hover",
    resolveDelay(el, opts),
    opts.html ?? el.getAttribute("data-bs-html") ?? "false",
  ]);
}

function createInstance(el, value) {
  const opts = normalizeOptions(value);
  const title = resolveTitle(el, opts);
  if (title) {
    el.setAttribute("data-bs-title", title);
  }
  const htmlAttr = el.getAttribute("data-bs-html");
  return window.bootstrap.Tooltip.getOrCreateInstance(el, {
    container: "body",
    trigger: opts.trigger ?? "hover",
    placement:
      opts.placement ?? el.getAttribute("data-bs-placement") ?? "top",
    delay: resolveDelay(el, opts),
    html: opts.html ?? (htmlAttr === "true"),
  });
}

function enabled(value) {
  if (value === null || value === undefined || value === false) return false;
  if (typeof value === "string") return value !== "";
  return value.title !== null && value.title !== undefined && value.title !== "";
}

function ownsOpenMenu(el) {
  return dropdownToggles(el).some(
    toggle =>
      toggle.classList.contains("show") ||
      toggle.getAttribute("aria-expanded") === "true"
  );
}

function refresh(el, value) {
  const instance = window.bootstrap.Tooltip.getInstance(el);
  if (instance) {
    instance.dispose();
  }
  // Drop Bootstrap's cached title so the new text takes effect
  el.removeAttribute("data-bs-original-title");
  if (!enabled(value)) {
    el._vTooltipSig = null;
    return;
  }
  createInstance(el, value);
  // A refresh (e.g. language switch) while an owned menu is open must
  // not resurrect an enabled tooltip; hide.bs.dropdown re-enables later.
  if (ownsOpenMenu(el)) {
    window.bootstrap.Tooltip.getInstance(el)?.disable();
  }
  el._vTooltipSig = signature(el, value);
}

function dropdownToggles(el) {
  // The tooltip may sit on a wrapper owning a dropdown menu, or (for
  // future use) directly on a dropdown toggle itself.
  if (el.matches?.('[data-bs-toggle="dropdown"]')) {
    return [el];
  }
  return [...el.querySelectorAll('[data-bs-toggle="dropdown"]')];
}

function wireDropdownSuppression(el) {
  // While an owned dropdown menu is open, hovering it would otherwise
  // keep the wrapper tooltip visible. Suppress it for the duration.
  // Needed for the "favorites" dropdown menu.
  const toggles = dropdownToggles(el);
  if (!toggles.length) {
    return null;
  }
  const onShow = () => {
    const instance = window.bootstrap.Tooltip.getInstance(el);
    if (instance) {
      instance.hide();
      instance.disable();
    }
  };
  const onHide = () => {
    window.bootstrap.Tooltip.getInstance(el)?.enable();
  };
  toggles.forEach(toggle => {
    toggle.addEventListener("show.bs.dropdown", onShow);
    toggle.addEventListener("hide.bs.dropdown", onHide);
  });
  return () => {
    toggles.forEach(toggle => {
      toggle.removeEventListener("show.bs.dropdown", onShow);
      toggle.removeEventListener("hide.bs.dropdown", onHide);
    });
  };
}

function unwireDropdownSuppression(el) {
  if (typeof el._vTooltipDropdownCleanup === "function") {
    el._vTooltipDropdownCleanup();
    el._vTooltipDropdownCleanup = null;
  }
}

export const tooltip = {
  mounted(el, binding) {
    if (!window.bootstrap) return;
    refresh(el, binding.value);
    unwireDropdownSuppression(el);
    el._vTooltipDropdownCleanup = wireDropdownSuppression(el);
  },
  updated(el, binding) {
    if (!window.bootstrap) return;
    if (signature(el, binding.value) === el._vTooltipSig) return;
    refresh(el, binding.value);
  },
  unmounted(el) {
    unwireDropdownSuppression(el);
    if (!window.bootstrap) return;
    const instance = window.bootstrap.Tooltip.getInstance(el);
    if (instance) {
      instance.dispose();
    }
    el._vTooltipSig = null;
  },
};
