import { ref as o } from "vue";
const u = (t) => t == null, c = (t) => t && typeof t == "object", d = (t) => u(t) || Array.isArray(t) && t.length === 0 || c(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, f = () => {
  const t = o(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, g = (t, e) => {
  if (!t) return "";
  const r = new Date(t), n = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  return e ? r.toLocaleString() : n.format(r);
};
function y(t, e = { reactive: !1 }) {
  return o(window[t]);
}
const p = (t, e) => {
  if (!t) return "";
  const r = new Date(t), n = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
  return e ? r.toLocaleString() : n.format(r);
};
function l(t, e = 300, r = !1) {
  let n;
  return function(...i) {
    const a = () => {
      n = null, t.apply(this, i);
    };
    clearTimeout(n), n = setTimeout(a, e), n || t.apply(this, i);
  };
}
function b(t, e = 300) {
  return l(t, e);
}
export {
  p as dateFormat,
  g as dateTimeFormat,
  b as debouncedInputHandler,
  y as getDjangoTemplateVariable,
  f as getURLprefix,
  d as isBlank,
  u as isEmpty,
  c as isObject
};
