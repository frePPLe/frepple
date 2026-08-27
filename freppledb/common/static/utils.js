import { ref as u } from "vue";
const d = (t) => t == null, c = (t) => t && typeof t == "object", w = (t) => d(t) || Array.isArray(t) && t.length === 0 || c(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, Y = (t) => t === "" || t === null || t === void 0 ? !1 : !isNaN(parseFloat(t)) && isFinite(t), h = () => {
  const t = u(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, F = (t, e) => {
  if (!t) return "";
  const o = new Date(t);
  return moment(o).format(e || window.datetimeformat);
};
function y(t, e = { reactive: !1 }) {
  return u(window[t]);
}
const T = (t, e) => {
  if (!t) return "";
  const o = new Date(t);
  return moment(o).format(e || window.dateformat);
}, b = (t) => {
  if (!t) return "";
  const e = new Date(t);
  return moment(e).format("HH:mm:ss");
}, H = (t) => {
  if (!t) return "";
  if (t instanceof Date) return moment(t).format("YYYY-MM-DDTHH:mm:ss");
  const e = window.datetimeformat || "YYYY-MM-DDTHH:mm:ss", o = moment(t, e, !0);
  if (o.isValid()) return o.format("YYYY-MM-DDTHH:mm:ss");
  const n = window.dateformat || "YYYY-MM-DD", r = moment(t, n, !0);
  if (r.isValid()) return r.format("YYYY-MM-DDTHH:mm:ss");
  const i = moment(t);
  return i.isValid() ? i.format("YYYY-MM-DDTHH:mm:ss") : t;
};
function M(t, e = 300) {
  let o;
  return function(...r) {
    const i = () => {
      o = null, t.apply(this, r);
    };
    clearTimeout(o), o = setTimeout(i, e), o || t.apply(this, r);
  };
}
const S = (t, e = 6) => {
  if (typeof t > "u" || t === "")
    return "";
  if (t !== "" && t !== null && !isNaN(t) && isFinite(t)) {
    t *= 1;
    const n = t < 0, r = Math.abs(t);
    let i = 0;
    r > 1e5 || e <= 0 ? i = String(parseFloat(r.toFixed())) : r > 1e4 || e <= 1 ? i = String(parseFloat(r.toFixed(1))) : r > 1e3 || e <= 2 ? i = String(parseFloat(r.toFixed(2))) : r > 100 || e <= 3 ? i = String(parseFloat(r.toFixed(3))) : r > 10 || e <= 4 ? i = String(parseFloat(r.toFixed(4))) : r > 1 || e <= 5 ? i = String(parseFloat(r.toFixed(5))) : i = String(parseFloat(r.toFixed(e))), i = (n ? "-" : "") + i;
    const a = jQuery("#grid").jqGrid("getGridRes", "formatter.number.decimalSeparator") || ".";
    a !== "." && (i = i.replace(".", a));
    const p = jQuery("#grid").jqGrid("getGridRes", "formatter.number.thousandsSeparator") || ",";
    if (r >= 1e3) {
      let s = i.lastIndexOf(a);
      s = s > -1 ? s : i.length;
      let f = a === void 0 ? "" : i.substring(s), m = -1, l;
      for (l = s; l > 0; l--)
        m++, m % 3 === 0 && l !== s && (!n || l > 1) && (f = p + f), f = i.charAt(l - 1) + f;
      i = f;
    }
    return i;
  }
  return (t ? t.toLocaleString() : null) || "0";
};
function v(t, e = 150) {
  let o;
  return (...n) => {
    clearTimeout(o), o = setTimeout(() => t(...n), e);
  };
}
function x(t) {
  return typeof window.admin_escape == "function" ? window.admin_escape(t) : encodeURIComponent(t);
}
function D(t) {
  return t ? {
    showTooltip: function(e) {
      let o = t.select("#tooltip");
      o.empty() && (o = t.select("body").append("div").attr("id", "tooltip").attr("role", "tooltip").attr("class", "card p-2").style("position", "absolute")), o.html("" + e).style("display", "block"), this.moveTooltip();
    },
    hideTooltip: function() {
      t.select("#tooltip").style("display", "none"), t.event.stopPropagation();
    },
    moveTooltip: function() {
      const e = t.event.pageX + 5;
      let o = t.event.pageY - 28;
      const n = t.select("#tooltip"), r = window.innerWidth - n.node().offsetWidth - 20, i = window.innerHeight - n.node().offsetHeight - 20;
      e > r && (o = t.event.pageY + 5), o > i && (o = t.event.pageY - n.node().offsetHeight - 25), n.style({
        left: e + "px",
        top: o + "px"
      }), t.event.stopPropagation();
    }
  } : (console.warn("Graph tooltip helper created without d3 instance"), {
    showTooltip: () => {
    },
    hideTooltip: () => {
    },
    moveTooltip: () => {
    }
  });
}
export {
  x as adminEscape,
  D as createGraphTooltipHelper,
  T as dateFormat,
  F as dateTimeFormat,
  H as dateToISO,
  v as debounce,
  M as debouncedInputHandler,
  y as getDjangoTemplateVariable,
  h as getURLprefix,
  w as isBlank,
  d as isEmpty,
  Y as isNumeric,
  c as isObject,
  S as numberFormat,
  b as timeFormat
};
