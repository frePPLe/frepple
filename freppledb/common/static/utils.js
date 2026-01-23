import { ref as d } from "vue";
const p = (e) => e == null, a = (e) => e && typeof e == "object", b = (e) => p(e) || Array.isArray(e) && e.length === 0 || a(e) && Object.keys(e).length === 0 || typeof e == "string" && e.trim().length === 0, g = (e) => e === "" || e === null || e === void 0 ? !1 : !isNaN(parseFloat(e)) && isFinite(e), w = () => {
  const e = d(window.database);
  return e.value === "default" ? "" : `/${e.value}`;
}, y = (e, r) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.datetimeformat);
};
function S(e, r = { reactive: !1 }) {
  return d(window[e]);
}
const h = (e, r) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.dateformat);
}, j = (e) => {
  if (!e) return "";
  const r = new Date(e);
  return moment(r).format("HH:mm:ss");
};
function N(e, r = 300) {
  let o;
  return function(...n) {
    const t = () => {
      o = null, e.apply(this, n);
    };
    clearTimeout(o), o = setTimeout(t, r), o || e.apply(this, n);
  };
}
const T = (e, r = 6) => {
  if (typeof e > "u" || e === "")
    return "";
  if (g(e)) {
    e *= 1;
    const u = e < 0, n = Math.abs(e);
    let t = 0;
    n > 1e5 || r <= 0 ? t = String(parseFloat(e.toFixed())) : n > 1e4 || r <= 1 ? t = String(parseFloat(e.toFixed(1))) : n > 1e3 || r <= 2 ? t = String(parseFloat(e.toFixed(2))) : n > 100 || r <= 3 ? t = String(parseFloat(e.toFixed(3))) : n > 10 || r <= 4 ? t = String(parseFloat(e.toFixed(4))) : n > 1 || r <= 5 ? t = String(parseFloat(e.toFixed(5))) : t = String(parseFloat(e.toFixed(r))), t = (u ? "-" : "") + t;
    const l = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    l !== "." && (t = t.replace(".", l));
    const m = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (n >= 1e3) {
      let i = t.lastIndexOf(l);
      i = i > -1 ? i : t.length;
      let f = l === void 0 ? "" : t.substring(i), c = -1, s;
      for (s = i; s > 0; s--)
        c++, c % 3 === 0 && s !== i && (!u || s > 1) && (f = m + f), f = t.charAt(s - 1) + f;
      t = f;
    }
    return t.replace("--", "-");
  }
  return (e == null ? void 0 : e.toLocaleString()) || "0";
};
function x(e, r = 150) {
  let o;
  return (...u) => {
    clearTimeout(o), o = setTimeout(() => e(...u), r);
  };
}
function I(e) {
  return typeof window.admin_escape == "function" ? window.admin_escape(e) : encodeURIComponent(e);
}
export {
  I as adminEscape,
  h as dateFormat,
  y as dateTimeFormat,
  x as debounce,
  N as debouncedInputHandler,
  S as getDjangoTemplateVariable,
  w as getURLprefix,
  b as isBlank,
  p as isEmpty,
  g as isNumeric,
  a as isObject,
  T as numberFormat,
  j as timeFormat
};
