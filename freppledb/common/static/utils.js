import { ref as i } from "vue";
const s = (t) => t == null, m = (t) => t && typeof t == "object", u = (t) => s(t) || Array.isArray(t) && t.length === 0 || m(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, a = (t) => t === "" || t === null || t === void 0 ? !1 : !isNaN(parseFloat(t)) && isFinite(t), l = () => {
  const t = i(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, d = (t, n) => {
  if (!t) return "";
  const e = new Date(t);
  return moment(e).format(window.datetimeformat);
}, p = (t, n) => {
  if (!t) return "";
  const e = new Date(t);
  return moment(e).format(window.dateformat);
}, w = (t) => {
  if (!t) return "";
  const n = new Date(t);
  return moment(n).format("HH:mm:ss");
};
function y(t, n = 300) {
  let e;
  return function(...r) {
    const o = () => {
      e = null, t.apply(this, r);
    };
    clearTimeout(e), e = setTimeout(o, n), e || t.apply(this, r);
  };
}
export {
  p as dateFormat,
  d as dateTimeFormat,
  y as debouncedInputHandler,
  l as getURLprefix,
  u as isBlank,
  s as isEmpty,
  a as isNumeric,
  m as isObject,
  w as timeFormat
};
