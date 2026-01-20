import { ref as c } from "vue";
const p = (e) => e == null, g = (e) => e && typeof e == "object", b = (e) => p(e) || Array.isArray(e) && e.length === 0 || g(e) && Object.keys(e).length === 0 || typeof e == "string" && e.trim().length === 0, F = (e) => e === "" || e === null || e === void 0 ? !1 : !isNaN(parseFloat(e)) && isFinite(e), w = () => {
  const e = c(window.database);
  return e.value === "default" ? "" : `/${e.value}`;
}, S = (e, r) => {
  if (!e) return "";
  const n = new Date(e);
  return moment(n).format(window.datetimeformat);
};
function y(e, r = { reactive: !1 }) {
  return c(window[e]);
}
const h = (e, r) => {
  if (!e) return "";
  const n = new Date(e);
  return moment(n).format(window.dateformat);
}, j = (e) => {
  if (!e) return "";
  const r = new Date(e);
  return moment(r).format("HH:mm:ss");
};
function N(e, r = 300) {
  let n;
  return function(...o) {
    const t = () => {
      n = null, e.apply(this, o);
    };
    clearTimeout(n), n = setTimeout(t, r), n || e.apply(this, o);
  };
}
const x = (e, r = 6) => {
  if (typeof e > "u" || e === "")
    return "";
  if (F(e)) {
    e *= 1;
    const l = e < 0, o = Math.abs(e);
    let t = 0;
    o > 1e5 || r <= 0 ? t = String(parseFloat(e.toFixed())) : o > 1e4 || r <= 1 ? t = String(parseFloat(e.toFixed(1))) : o > 1e3 || r <= 2 ? t = String(parseFloat(e.toFixed(2))) : o > 100 || r <= 3 ? t = String(parseFloat(e.toFixed(3))) : o > 10 || r <= 4 ? t = String(parseFloat(e.toFixed(4))) : o > 1 || r <= 5 ? t = String(parseFloat(e.toFixed(5))) : t = String(parseFloat(e.toFixed(r))), t = (l ? "-" : "") + t;
    const f = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    f !== "." && (t = t.replace(".", f));
    const m = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (o >= 1e3) {
      let i = t.lastIndexOf(f);
      i = i > -1 ? i : t.length;
      let u = f === void 0 ? "" : t.substring(i), d = -1, s;
      for (s = i; s > 0; s--)
        d++, d % 3 === 0 && s !== i && (!l || s > 1) && (u = m + u), u = t.charAt(s - 1) + u;
      t = u;
    }
    return t.replace("--", "-");
  }
  return (e == null ? void 0 : e.toLocaleString()) || "0";
};
export {
  h as dateFormat,
  S as dateTimeFormat,
  N as debouncedInputHandler,
  y as getDjangoTemplateVariable,
  w as getURLprefix,
  b as isBlank,
  p as isEmpty,
  F as isNumeric,
  g as isObject,
  x as numberFormat,
  j as timeFormat
};
