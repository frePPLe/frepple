import { ref as i } from "vue";
const c = (t) => t == null, u = (t) => t && typeof t == "object", s = (t) => c(t) || Array.isArray(t) && t.length === 0 || u(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, m = () => {
  const t = i(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, d = (t, n) => {
  if (!t) return "";
  const e = new Date(t), r = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  return n ? e.toLocaleString() : r.format(e);
};
function f(t, n = { reactive: !1 }) {
  return i(window[t]);
}
const g = (t, n) => {
  if (!t) return "";
  const e = new Date(t), r = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
  return n ? e.toLocaleString() : r.format(e);
};
function y(t, n = 300) {
  let e;
  return function(...o) {
    const a = () => {
      e = null, t.apply(this, o);
    };
    clearTimeout(e), e = setTimeout(a, n), e || t.apply(this, o);
  };
}
export {
  g as dateFormat,
  d as dateTimeFormat,
  y as debouncedInputHandler,
  f as getDjangoTemplateVariable,
  m as getURLprefix,
  s as isBlank,
  c as isEmpty,
  u as isObject
};
