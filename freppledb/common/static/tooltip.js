const f = { show: 500, hide: 100 };
function a(t) {
  return typeof t == "string" ? { title: t } : { ...t || {} };
}
function d(t, n) {
  return n.title ?? t.getAttribute("data-bs-title") ?? t.getAttribute("title") ?? "";
}
function p(t, n) {
  if (t.hasAttribute("data-bs-delay"))
    try {
      return JSON.parse(t.getAttribute("data-bs-delay"));
    } catch {
    }
  return n.delay !== void 0 ? n.delay : { ...f };
}
function u(t, n) {
  const o = a(n);
  return JSON.stringify([
    d(t, o),
    o.placement ?? t.getAttribute("data-bs-placement") ?? "top",
    o.trigger ?? "hover",
    p(t, o),
    o.html ?? t.getAttribute("data-bs-html") ?? "false"
  ]);
}
function b(t, n) {
  const o = a(n), i = d(t, o);
  i && t.setAttribute("data-bs-title", i);
  const e = t.getAttribute("data-bs-html");
  return window.bootstrap.Tooltip.getOrCreateInstance(t, {
    container: "body",
    trigger: o.trigger ?? "hover",
    placement: o.placement ?? t.getAttribute("data-bs-placement") ?? "top",
    delay: p(t, o),
    html: o.html ?? e === "true"
  });
}
function w(t) {
  return t == null || t === !1 ? !1 : typeof t == "string" ? t !== "" : t.title !== null && t.title !== void 0 && t.title !== "";
}
function l(t) {
  return c(t).some(
    (n) => n.classList.contains("show") || n.getAttribute("aria-expanded") === "true"
  );
}
function r(t, n) {
  var i;
  const o = window.bootstrap.Tooltip.getInstance(t);
  if (o && o.dispose(), t.removeAttribute("data-bs-original-title"), !w(n)) {
    t._vTooltipSig = null;
    return;
  }
  b(t, n), l(t) && ((i = window.bootstrap.Tooltip.getInstance(t)) == null || i.disable()), t._vTooltipSig = u(t, n);
}
function c(t) {
  var n;
  return (n = t.matches) != null && n.call(t, '[data-bs-toggle="dropdown"]') ? [t] : [...t.querySelectorAll('[data-bs-toggle="dropdown"]')];
}
function g(t) {
  const n = c(t);
  if (!n.length)
    return null;
  const o = () => {
    const e = window.bootstrap.Tooltip.getInstance(t);
    e && (e.hide(), e.disable());
  }, i = () => {
    var e;
    (e = window.bootstrap.Tooltip.getInstance(t)) == null || e.enable();
  };
  return n.forEach((e) => {
    e.addEventListener("show.bs.dropdown", o), e.addEventListener("hide.bs.dropdown", i);
  }), () => {
    n.forEach((e) => {
      e.removeEventListener("show.bs.dropdown", o), e.removeEventListener("hide.bs.dropdown", i);
    });
  };
}
function s(t) {
  typeof t._vTooltipDropdownCleanup == "function" && (t._vTooltipDropdownCleanup(), t._vTooltipDropdownCleanup = null);
}
const h = {
  mounted(t, n) {
    window.bootstrap && (r(t, n.value), s(t), t._vTooltipDropdownCleanup = g(t));
  },
  updated(t, n) {
    window.bootstrap && u(t, n.value) !== t._vTooltipSig && r(t, n.value);
  },
  unmounted(t) {
    if (s(t), !window.bootstrap) return;
    const n = window.bootstrap.Tooltip.getInstance(t);
    n && n.dispose(), t._vTooltipSig = null;
  }
};
export {
  h as tooltip
};
