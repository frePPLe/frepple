import { ref as m } from "vue";
const g = (e) => e == null, F = (e) => e && typeof e == "object", w = (e) => g(e) || Array.isArray(e) && e.length === 0 || F(e) && Object.keys(e).length === 0 || typeof e == "string" && e.trim().length === 0, a = (e) => e === "" || e === null || e === void 0 ? !1 : !isNaN(parseFloat(e)) && isFinite(e), S = () => {
  const e = m(window.database);
  return e.value === "default" ? "" : `/${e.value}`;
}, y = (e, t) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.datetimeformat);
};
function h(e, t = { reactive: !1 }) {
  return m(window[e]);
}
const j = (e, t) => {
  if (!e) return "";
  const o = new Date(e);
  return moment(o).format(window.dateformat);
}, N = (e) => {
  if (!e) return "";
  const t = new Date(e);
  return moment(t).format("HH:mm:ss");
};
function x(e, t = 300) {
  let o;
  return function(...n) {
    const r = () => {
      o = null, e.apply(this, n);
    };
    clearTimeout(o), o = setTimeout(r, t), o || e.apply(this, n);
  };
}
const O = (e, t = 6) => {
  if (typeof e > "u" || e === "")
    return "";
  if (a(e)) {
    e *= 1;
    const d = e < 0, n = Math.abs(e);
    let r = 0;
    n > 1e5 || t <= 0 ? r = String(parseFloat(e.toFixed())) : n > 1e4 || t <= 1 ? r = String(parseFloat(e.toFixed(1))) : n > 1e3 || t <= 2 ? r = String(parseFloat(e.toFixed(2))) : n > 100 || t <= 3 ? r = String(parseFloat(e.toFixed(3))) : n > 10 || t <= 4 ? r = String(parseFloat(e.toFixed(4))) : n > 1 || t <= 5 ? r = String(parseFloat(e.toFixed(5))) : r = String(parseFloat(e.toFixed(t)));
    let i = (d ? "-" : "") + r;
    const l = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    l !== "." && (i = i.replace(".", l));
    const p = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    {
      let s = i.lastIndexOf(l);
      s = s > -1 ? s : i.length;
      let f = l === void 0 ? "" : i.substring(s), c = -1, u;
      for (u = s; u > 0; u--)
        c++, c % 3 === 0 && u !== s && (!d || u > 1) && (f = p + f), f = i.charAt(u - 1) + f;
      i = f;
    }
    return i;
  }
  return (e == null ? void 0 : e.toLocaleString()) || "0";
};
export {
  j as dateFormat,
  y as dateTimeFormat,
  x as debouncedInputHandler,
  h as getDjangoTemplateVariable,
  S as getURLprefix,
  w as isBlank,
  g as isEmpty,
  a as isNumeric,
  F as isObject,
  O as numberFormat,
  N as timeFormat
};
