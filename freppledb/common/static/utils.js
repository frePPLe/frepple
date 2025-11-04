import { ref as o } from "vue";
const s = (t) => t == null, m = (t) => t && typeof t == "object", f = (t) => s(t) || Array.isArray(t) && t.length === 0 || m(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, u = (t) => t === "" || t === null || t === void 0 ? !1 : !isNaN(parseFloat(t)) && isFinite(t), l = () => {
  const t = o(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, d = (t, n) => {
  if (!t) return "";
  const e = new Date(t);
  return moment(e).format(window.datetimeformat);
};
function p(t, n = { reactive: !1 }) {
  return o(window[t]);
}
const w = (t, n) => {
  if (!t) return "";
  const e = new Date(t);
  return moment(e).format(window.dateformat);
}, y = (t) => {
  if (!t) return "";
  const n = new Date(t);
  return moment(n).format("HH:mm:ss");
};
function b(t, n = 300) {
  let e;
  return function(...r) {
    const i = () => {
      e = null, t.apply(this, r);
    };
    clearTimeout(e), e = setTimeout(i, n), e || t.apply(this, r);
  };
}
export {
  w as dateFormat,
  d as dateTimeFormat,
  b as debouncedInputHandler,
  p as getDjangoTemplateVariable,
  l as getURLprefix,
  f as isBlank,
  s as isEmpty,
  u as isNumeric,
  m as isObject,
  y as timeFormat
};
