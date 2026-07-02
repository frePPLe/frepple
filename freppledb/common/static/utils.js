import { ref as d } from "vue";
const m = (e) => e == null, p = (e) => e && typeof e == "object", b = (e) => m(e) || Array.isArray(e) && e.length === 0 || p(e) && Object.keys(e).length === 0 || typeof e == "string" && e.trim().length === 0, g = (e) => e === "" || e === null || e === void 0 ? !1 : !isNaN(parseFloat(e)) && isFinite(e), w = () => {
  const e = d(window.database);
  return e.value === "default" ? "" : `/${e.value}`;
}, y = (e, n) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.datetimeformat);
};
function S(e, n = { reactive: !1 }) {
  return d(window[e]);
}
const h = (e, n) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.dateformat);
}, j = (e) => {
  if (!e) return "";
  const n = new Date(e);
  return moment(n).format("HH:mm:ss");
};
function N(e, n = 300) {
  let o;
  return function(...r) {
    const t = () => {
      o = null, e.apply(this, r);
    };
    clearTimeout(o), o = setTimeout(t, n), o || e.apply(this, r);
  };
}
const T = (e, n = 6) => {
  if (typeof e > "u" || e === "")
    return "";
  if (g(e)) {
    e *= 1;
    const u = e < 0, r = Math.abs(e);
    let t = 0;
    r > 1e5 || n <= 0 ? t = String(parseFloat(r.toFixed())) : r > 1e4 || n <= 1 ? t = String(parseFloat(r.toFixed(1))) : r > 1e3 || n <= 2 ? t = String(parseFloat(r.toFixed(2))) : r > 100 || n <= 3 ? t = String(parseFloat(r.toFixed(3))) : r > 10 || n <= 4 ? t = String(parseFloat(r.toFixed(4))) : r > 1 || n <= 5 ? t = String(parseFloat(r.toFixed(5))) : t = String(parseFloat(r.toFixed(n))), t = (u ? "-" : "") + t;
    const a = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    a !== "." && (t = t.replace(".", a));
    const c = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (r >= 1e3) {
      let i = t.lastIndexOf(a);
      i = i > -1 ? i : t.length;
      let f = a === void 0 ? "" : t.substring(i), l = -1, s;
      for (s = i; s > 0; s--)
        l++, l % 3 === 0 && s !== i && (!u || s > 1) && (f = c + f), f = t.charAt(s - 1) + f;
      t = f;
    }
    return t;
  }
  return (e ? e.toLocaleString() : null) || "0";
};
function x(e, n = 150) {
  let o;
  return (...u) => {
    clearTimeout(o), o = setTimeout(() => e(...u), n);
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
  m as isEmpty,
  g as isNumeric,
  p as isObject,
  T as numberFormat,
  j as timeFormat
};
