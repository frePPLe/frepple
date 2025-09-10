import { ref as o } from "vue";
const i = (t) => t == null, a = (t) => t && typeof t == "object", c = (t) => i(t) || Array.isArray(t) && t.length === 0 || a(t) && Object.keys(t).length === 0 || typeof t == "string" && t.trim().length === 0, m = () => {
  const t = o(window.database);
  return t.value === "default" ? "" : `/${t.value}`;
}, l = (t, n) => {
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
  return o(window[t]);
}
const u = (t, n) => {
  if (!t) return "";
  const e = new Date(t), r = new Intl.DateTimeFormat("default", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit"
  });
  return n ? e.toLocaleString() : r.format(e);
};
export {
  u as dateFormat,
  l as dateTimeFormat,
  f as getDjangoTemplateVariable,
  m as getURLprefix,
  c as isBlank,
  i as isEmpty,
  a as isObject
};
