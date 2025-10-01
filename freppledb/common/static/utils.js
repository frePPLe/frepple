import { ref as o } from "vue";
const a = (t) => t == null, c = (t) => t && typeof t == "object", l = (t) => a(t) || Array.isArray(t) && t.length === 0 || c(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, m = (t) => t === "" || t === null || t === void 0 ? !1 : !isNaN(parseFloat(t)) && isFinite(t), d = () => {
  const t = o(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, f = (t, n) => {
  if (!t) return "";
  const e = new Date(t), i = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  return n ? e.toLocaleString() : i.format(e);
};
function g(t, n = { reactive: !1 }) {
  return o(window[t]);
}
const p = (t, n) => {
  if (!t) return "";
  const e = new Date(t), i = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
  return n ? e.toLocaleString() : i.format(e);
};
function y(t, n = 300) {
  let e;
  return function(...r) {
    const s = () => {
      e = null, t.apply(this, r);
    };
    clearTimeout(e), e = setTimeout(s, n), e || t.apply(this, r);
  };
}
export {
  p as dateFormat,
  f as dateTimeFormat,
  y as debouncedInputHandler,
  g as getDjangoTemplateVariable,
  d as getURLprefix,
  l as isBlank,
  a as isEmpty,
  m as isNumeric,
  c as isObject
};
