import { toValue as L, ref as N } from "vue";
function Ve(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: bt } = Object.prototype, { getPrototypeOf: ge } = Object, { iterator: ie, toStringTag: We } = Symbol, ae = /* @__PURE__ */ ((e) => (t) => {
  const n = bt.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), k = (e) => (e = e.toLowerCase(), (t) => ae(t) === e), ce = (e) => (t) => typeof t === e, { isArray: z } = Array, v = ce("undefined");
function K(e) {
  return e !== null && !v(e) && e.constructor !== null && !v(e.constructor) && T(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const Ke = k("ArrayBuffer");
function wt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && Ke(e.buffer), t;
}
const Et = ce("string"), T = ce("function"), Xe = ce("number"), X = (e) => e !== null && typeof e == "object", gt = (e) => e === !0 || e === !1, ne = (e) => {
  if (ae(e) !== "object")
    return !1;
  const t = ge(e);
  return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(We in e) && !(ie in e);
}, St = (e) => {
  if (!X(e) || K(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, Rt = k("Date"), Ot = k("File"), Tt = k("Blob"), At = k("FileList"), Ct = (e) => X(e) && T(e.pipe), xt = (e) => {
  let t;
  return e && (typeof FormData == "function" && e instanceof FormData || T(e.append) && ((t = ae(e)) === "formdata" || // detect form-data instance
  t === "object" && T(e.toString) && e.toString() === "[object FormData]"));
}, Nt = k("URLSearchParams"), [Pt, kt, Ft, Ut] = ["ReadableStream", "Request", "Response", "Headers"].map(k), _t = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function G(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), z(e))
    for (r = 0, s = e.length; r < s; r++)
      t.call(null, e[r], r, e);
  else {
    if (K(e))
      return;
    const i = n ? Object.getOwnPropertyNames(e) : Object.keys(e), o = i.length;
    let c;
    for (r = 0; r < o; r++)
      c = i[r], t.call(null, e[c], c, e);
  }
}
function Ge(e, t) {
  if (K(e))
    return null;
  t = t.toLowerCase();
  const n = Object.keys(e);
  let r = n.length, s;
  for (; r-- > 0; )
    if (s = n[r], t === s.toLowerCase())
      return s;
  return null;
}
const q = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, Qe = (e) => !v(e) && e !== q;
function ye() {
  const { caseless: e, skipUndefined: t } = Qe(this) && this || {}, n = {}, r = (s, i) => {
    const o = e && Ge(n, i) || i;
    ne(n[o]) && ne(s) ? n[o] = ye(n[o], s) : ne(s) ? n[o] = ye({}, s) : z(s) ? n[o] = s.slice() : (!t || !v(s)) && (n[o] = s);
  };
  for (let s = 0, i = arguments.length; s < i; s++)
    arguments[s] && G(arguments[s], r);
  return n;
}
const Dt = (e, t, n, { allOwnKeys: r } = {}) => (G(t, (s, i) => {
  n && T(s) ? e[i] = Ve(s, n) : e[i] = s;
}, { allOwnKeys: r }), e), Lt = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Bt = (e, t, n, r) => {
  e.prototype = Object.create(t.prototype, r), e.prototype.constructor = e, Object.defineProperty(e, "super", {
    value: t.prototype
  }), n && Object.assign(e.prototype, n);
}, jt = (e, t, n, r) => {
  let s, i, o;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0; )
      o = s[i], (!r || r(o, e, t)) && !c[o] && (t[o] = e[o], c[o] = !0);
    e = n !== !1 && ge(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, qt = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, It = (e) => {
  if (!e) return null;
  if (z(e)) return e;
  let t = e.length;
  if (!Xe(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, Ht = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && ge(Uint8Array)), Mt = (e, t) => {
  const r = (e && e[ie]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const i = s.value;
    t.call(e, i[0], i[1]);
  }
}, $t = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, vt = k("HTMLFormElement"), zt = (e) => e.toLowerCase().replace(
  /[-_\s]([a-z\d])(\w*)/g,
  function(n, r, s) {
    return r.toUpperCase() + s;
  }
), ke = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), Jt = k("RegExp"), Ze = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  G(n, (s, i) => {
    let o;
    (o = t(s, i, e)) !== !1 && (r[i] = o || s);
  }), Object.defineProperties(e, r);
}, Vt = (e) => {
  Ze(e, (t, n) => {
    if (T(e) && ["arguments", "caller", "callee"].indexOf(n) !== -1)
      return !1;
    const r = e[n];
    if (T(r)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + n + "'");
      });
    }
  });
}, Wt = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((i) => {
      n[i] = !0;
    });
  };
  return z(e) ? r(e) : r(String(e).split(t)), n;
}, Kt = () => {
}, Xt = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Gt(e) {
  return !!(e && T(e.append) && e[We] === "FormData" && e[ie]);
}
const Qt = (e) => {
  const t = new Array(10), n = (r, s) => {
    if (X(r)) {
      if (t.indexOf(r) >= 0)
        return;
      if (K(r))
        return r;
      if (!("toJSON" in r)) {
        t[s] = r;
        const i = z(r) ? [] : {};
        return G(r, (o, c) => {
          const f = n(o, s + 1);
          !v(f) && (i[c] = f);
        }), t[s] = void 0, i;
      }
    }
    return r;
  };
  return n(e, 0);
}, Zt = k("AsyncFunction"), Yt = (e) => e && (X(e) || T(e)) && T(e.then) && T(e.catch), Ye = ((e, t) => e ? setImmediate : t ? ((n, r) => (q.addEventListener("message", ({ source: s, data: i }) => {
  s === q && i === n && r.length && r.shift()();
}, !1), (s) => {
  r.push(s), q.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(
  typeof setImmediate == "function",
  T(q.postMessage)
), en = typeof queueMicrotask < "u" ? queueMicrotask.bind(q) : typeof process < "u" && process.nextTick || Ye, tn = (e) => e != null && T(e[ie]), a = {
  isArray: z,
  isArrayBuffer: Ke,
  isBuffer: K,
  isFormData: xt,
  isArrayBufferView: wt,
  isString: Et,
  isNumber: Xe,
  isBoolean: gt,
  isObject: X,
  isPlainObject: ne,
  isEmptyObject: St,
  isReadableStream: Pt,
  isRequest: kt,
  isResponse: Ft,
  isHeaders: Ut,
  isUndefined: v,
  isDate: Rt,
  isFile: Ot,
  isBlob: Tt,
  isRegExp: Jt,
  isFunction: T,
  isStream: Ct,
  isURLSearchParams: Nt,
  isTypedArray: Ht,
  isFileList: At,
  forEach: G,
  merge: ye,
  extend: Dt,
  trim: _t,
  stripBOM: Lt,
  inherits: Bt,
  toFlatObject: jt,
  kindOf: ae,
  kindOfTest: k,
  endsWith: qt,
  toArray: It,
  forEachEntry: Mt,
  matchAll: $t,
  isHTMLForm: vt,
  hasOwnProperty: ke,
  hasOwnProp: ke,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors: Ze,
  freezeMethods: Vt,
  toObjectSet: Wt,
  toCamelCase: zt,
  noop: Kt,
  toFiniteNumber: Xt,
  findKey: Ge,
  global: q,
  isContextDefined: Qe,
  isSpecCompliantForm: Gt,
  toJSONObject: Qt,
  isAsyncFn: Zt,
  isThenable: Yt,
  setImmediate: Ye,
  asap: en,
  isIterable: tn
};
function y(e, t, n, r, s) {
  Error.call(this), Error.captureStackTrace ? Error.captureStackTrace(this, this.constructor) : this.stack = new Error().stack, this.message = e, this.name = "AxiosError", t && (this.code = t), n && (this.config = n), r && (this.request = r), s && (this.response = s, this.status = s.status ? s.status : null);
}
a.inherits(y, Error, {
  toJSON: function() {
    return {
      // Standard
      message: this.message,
      name: this.name,
      // Microsoft
      description: this.description,
      number: this.number,
      // Mozilla
      fileName: this.fileName,
      lineNumber: this.lineNumber,
      columnNumber: this.columnNumber,
      stack: this.stack,
      // Axios
      config: a.toJSONObject(this.config),
      code: this.code,
      status: this.status
    };
  }
});
const et = y.prototype, tt = {};
[
  "ERR_BAD_OPTION_VALUE",
  "ERR_BAD_OPTION",
  "ECONNABORTED",
  "ETIMEDOUT",
  "ERR_NETWORK",
  "ERR_FR_TOO_MANY_REDIRECTS",
  "ERR_DEPRECATED",
  "ERR_BAD_RESPONSE",
  "ERR_BAD_REQUEST",
  "ERR_CANCELED",
  "ERR_NOT_SUPPORT",
  "ERR_INVALID_URL"
  // eslint-disable-next-line func-names
].forEach((e) => {
  tt[e] = { value: e };
});
Object.defineProperties(y, tt);
Object.defineProperty(et, "isAxiosError", { value: !0 });
y.from = (e, t, n, r, s, i) => {
  const o = Object.create(et);
  a.toFlatObject(e, o, function(u) {
    return u !== Error.prototype;
  }, (l) => l !== "isAxiosError");
  const c = e && e.message ? e.message : "Error", f = t == null && e ? e.code : t;
  return y.call(o, c, f, n, r, s), e && o.cause == null && Object.defineProperty(o, "cause", { value: e, configurable: !0 }), o.name = e && e.name || "Error", i && Object.assign(o, i), o;
};
const nn = null;
function be(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function nt(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function Fe(e, t, n) {
  return e ? e.concat(t).map(function(s, i) {
    return s = nt(s), !n && i ? "[" + s + "]" : s;
  }).join(n ? "." : "") : t;
}
function rn(e) {
  return a.isArray(e) && !e.some(be);
}
const sn = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function le(e, t, n) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData(), n = a.toFlatObject(n, {
    metaTokens: !0,
    dots: !1,
    indexes: !1
  }, !1, function(m, p) {
    return !a.isUndefined(p[m]);
  });
  const r = n.metaTokens, s = n.visitor || u, i = n.dots, o = n.indexes, f = (n.Blob || typeof Blob < "u" && Blob) && a.isSpecCompliantForm(t);
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function l(d) {
    if (d === null) return "";
    if (a.isDate(d))
      return d.toISOString();
    if (a.isBoolean(d))
      return d.toString();
    if (!f && a.isBlob(d))
      throw new y("Blob is not supported. Use a Buffer instead.");
    return a.isArrayBuffer(d) || a.isTypedArray(d) ? f && typeof Blob == "function" ? new Blob([d]) : Buffer.from(d) : d;
  }
  function u(d, m, p) {
    let E = d;
    if (d && !p && typeof d == "object") {
      if (a.endsWith(m, "{}"))
        m = r ? m : m.slice(0, -2), d = JSON.stringify(d);
      else if (a.isArray(d) && rn(d) || (a.isFileList(d) || a.endsWith(m, "[]")) && (E = a.toArray(d)))
        return m = nt(m), E.forEach(function(g, O) {
          !(a.isUndefined(g) || g === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            o === !0 ? Fe([m], O, i) : o === null ? m : m + "[]",
            l(g)
          );
        }), !1;
    }
    return be(d) ? !0 : (t.append(Fe(p, m, i), l(d)), !1);
  }
  const h = [], b = Object.assign(sn, {
    defaultVisitor: u,
    convertValue: l,
    isVisitable: be
  });
  function S(d, m) {
    if (!a.isUndefined(d)) {
      if (h.indexOf(d) !== -1)
        throw Error("Circular reference detected in " + m.join("."));
      h.push(d), a.forEach(d, function(E, C) {
        (!(a.isUndefined(E) || E === null) && s.call(
          t,
          E,
          a.isString(C) ? C.trim() : C,
          m,
          b
        )) === !0 && S(E, m ? m.concat(C) : [C]);
      }), h.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return S(e), t;
}
function Ue(e) {
  const t = {
    "!": "%21",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "~": "%7E",
    "%20": "+",
    "%00": "\0"
  };
  return encodeURIComponent(e).replace(/[!'()~]|%20|%00/g, function(r) {
    return t[r];
  });
}
function Se(e, t) {
  this._pairs = [], e && le(e, this, t);
}
const rt = Se.prototype;
rt.append = function(t, n) {
  this._pairs.push([t, n]);
};
rt.toString = function(t) {
  const n = t ? function(r) {
    return t.call(this, r, Ue);
  } : Ue;
  return this._pairs.map(function(s) {
    return n(s[0]) + "=" + n(s[1]);
  }, "").join("&");
};
function on(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function st(e, t, n) {
  if (!t)
    return e;
  const r = n && n.encode || on;
  a.isFunction(n) && (n = {
    serialize: n
  });
  const s = n && n.serialize;
  let i;
  if (s ? i = s(t, n) : i = a.isURLSearchParams(t) ? t.toString() : new Se(t, n).toString(r), i) {
    const o = e.indexOf("#");
    o !== -1 && (e = e.slice(0, o)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
class _e {
  constructor() {
    this.handlers = [];
  }
  /**
   * Add a new interceptor to the stack
   *
   * @param {Function} fulfilled The function to handle `then` for a `Promise`
   * @param {Function} rejected The function to handle `reject` for a `Promise`
   *
   * @return {Number} An ID used to remove interceptor later
   */
  use(t, n, r) {
    return this.handlers.push({
      fulfilled: t,
      rejected: n,
      synchronous: r ? r.synchronous : !1,
      runWhen: r ? r.runWhen : null
    }), this.handlers.length - 1;
  }
  /**
   * Remove an interceptor from the stack
   *
   * @param {Number} id The ID that was returned by `use`
   *
   * @returns {void}
   */
  eject(t) {
    this.handlers[t] && (this.handlers[t] = null);
  }
  /**
   * Clear all interceptors from the stack
   *
   * @returns {void}
   */
  clear() {
    this.handlers && (this.handlers = []);
  }
  /**
   * Iterate over all the registered interceptors
   *
   * This method is particularly useful for skipping over any
   * interceptors that may have become `null` calling `eject`.
   *
   * @param {Function} fn The function to call for each interceptor
   *
   * @returns {void}
   */
  forEach(t) {
    a.forEach(this.handlers, function(r) {
      r !== null && t(r);
    });
  }
}
const ot = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1
}, an = typeof URLSearchParams < "u" ? URLSearchParams : Se, cn = typeof FormData < "u" ? FormData : null, ln = typeof Blob < "u" ? Blob : null, un = {
  isBrowser: !0,
  classes: {
    URLSearchParams: an,
    FormData: cn,
    Blob: ln
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, Re = typeof window < "u" && typeof document < "u", we = typeof navigator == "object" && navigator || void 0, fn = Re && (!we || ["ReactNative", "NativeScript", "NS"].indexOf(we.product) < 0), dn = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", pn = Re && window.location.href || "http://localhost", hn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: Re,
  hasStandardBrowserEnv: fn,
  hasStandardBrowserWebWorkerEnv: dn,
  navigator: we,
  origin: pn
}, Symbol.toStringTag, { value: "Module" })), R = {
  ...hn,
  ...un
};
function mn(e, t) {
  return le(e, new R.classes.URLSearchParams(), {
    visitor: function(n, r, s, i) {
      return R.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function yn(e) {
  return a.matchAll(/\w+|\[(\w*)]/g, e).map((t) => t[0] === "[]" ? "" : t[1] || t[0]);
}
function bn(e) {
  const t = {}, n = Object.keys(e);
  let r;
  const s = n.length;
  let i;
  for (r = 0; r < s; r++)
    i = n[r], t[i] = e[i];
  return t;
}
function it(e) {
  function t(n, r, s, i) {
    let o = n[i++];
    if (o === "__proto__") return !0;
    const c = Number.isFinite(+o), f = i >= n.length;
    return o = !o && a.isArray(s) ? s.length : o, f ? (a.hasOwnProp(s, o) ? s[o] = [s[o], r] : s[o] = r, !c) : ((!s[o] || !a.isObject(s[o])) && (s[o] = []), t(n, r, s[o], i) && a.isArray(s[o]) && (s[o] = bn(s[o])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(yn(r), s, n, 0);
    }), n;
  }
  return null;
}
function wn(e, t, n) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (r) {
      if (r.name !== "SyntaxError")
        throw r;
    }
  return (n || JSON.stringify)(e);
}
const Q = {
  transitional: ot,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [function(t, n) {
    const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, i = a.isObject(t);
    if (i && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
      return s ? JSON.stringify(it(t)) : t;
    if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
      return t;
    if (a.isArrayBufferView(t))
      return t.buffer;
    if (a.isURLSearchParams(t))
      return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
    let c;
    if (i) {
      if (r.indexOf("application/x-www-form-urlencoded") > -1)
        return mn(t, this.formSerializer).toString();
      if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
        const f = this.env && this.env.FormData;
        return le(
          c ? { "files[]": t } : t,
          f && new f(),
          this.formSerializer
        );
      }
    }
    return i || s ? (n.setContentType("application/json", !1), wn(t)) : t;
  }],
  transformResponse: [function(t) {
    const n = this.transitional || Q.transitional, r = n && n.forcedJSONParsing, s = this.responseType === "json";
    if (a.isResponse(t) || a.isReadableStream(t))
      return t;
    if (t && a.isString(t) && (r && !this.responseType || s)) {
      const o = !(n && n.silentJSONParsing) && s;
      try {
        return JSON.parse(t, this.parseReviver);
      } catch (c) {
        if (o)
          throw c.name === "SyntaxError" ? y.from(c, y.ERR_BAD_RESPONSE, this, null, this.response) : c;
      }
    }
    return t;
  }],
  /**
   * A timeout in milliseconds to abort a request. If set to 0 (default) a
   * timeout is not created.
   */
  timeout: 0,
  xsrfCookieName: "XSRF-TOKEN",
  xsrfHeaderName: "X-XSRF-TOKEN",
  maxContentLength: -1,
  maxBodyLength: -1,
  env: {
    FormData: R.classes.FormData,
    Blob: R.classes.Blob
  },
  validateStatus: function(t) {
    return t >= 200 && t < 300;
  },
  headers: {
    common: {
      Accept: "application/json, text/plain, */*",
      "Content-Type": void 0
    }
  }
};
a.forEach(["delete", "get", "head", "post", "put", "patch"], (e) => {
  Q.headers[e] = {};
});
const En = a.toObjectSet([
  "age",
  "authorization",
  "content-length",
  "content-type",
  "etag",
  "expires",
  "from",
  "host",
  "if-modified-since",
  "if-unmodified-since",
  "last-modified",
  "location",
  "max-forwards",
  "proxy-authorization",
  "referer",
  "retry-after",
  "user-agent"
]), gn = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(o) {
    s = o.indexOf(":"), n = o.substring(0, s).trim().toLowerCase(), r = o.substring(s + 1).trim(), !(!n || t[n] && En[n]) && (n === "set-cookie" ? t[n] ? t[n].push(r) : t[n] = [r] : t[n] = t[n] ? t[n] + ", " + r : r);
  }), t;
}, De = Symbol("internals");
function W(e) {
  return e && String(e).trim().toLowerCase();
}
function re(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(re) : String(e);
}
function Sn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const Rn = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function pe(e, t, n, r, s) {
  if (a.isFunction(r))
    return r.call(this, t, n);
  if (s && (t = n), !!a.isString(t)) {
    if (a.isString(r))
      return t.indexOf(r) !== -1;
    if (a.isRegExp(r))
      return r.test(t);
  }
}
function On(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function Tn(e, t) {
  const n = a.toCamelCase(" " + t);
  ["get", "set", "has"].forEach((r) => {
    Object.defineProperty(e, r + n, {
      value: function(s, i, o) {
        return this[r].call(this, t, s, i, o);
      },
      configurable: !0
    });
  });
}
let A = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, n, r) {
    const s = this;
    function i(c, f, l) {
      const u = W(f);
      if (!u)
        throw new Error("header name must be a non-empty string");
      const h = a.findKey(s, u);
      (!h || s[h] === void 0 || l === !0 || l === void 0 && s[h] !== !1) && (s[h || f] = re(c));
    }
    const o = (c, f) => a.forEach(c, (l, u) => i(l, u, f));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      o(t, n);
    else if (a.isString(t) && (t = t.trim()) && !Rn(t))
      o(gn(t), n);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, f, l;
      for (const u of t) {
        if (!a.isArray(u))
          throw TypeError("Object iterator must return a key-value pair");
        c[l = u[0]] = (f = c[l]) ? a.isArray(f) ? [...f, u[1]] : [f, u[1]] : u[1];
      }
      o(c, n);
    } else
      t != null && i(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = W(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return Sn(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = W(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || pe(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function i(o) {
      if (o = W(o), o) {
        const c = a.findKey(r, o);
        c && (!n || pe(r, r[c], c, n)) && (delete r[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(i) : i(t), s;
  }
  clear(t) {
    const n = Object.keys(this);
    let r = n.length, s = !1;
    for (; r--; ) {
      const i = n[r];
      (!t || pe(this, this[i], i, t, !0)) && (delete this[i], s = !0);
    }
    return s;
  }
  normalize(t) {
    const n = this, r = {};
    return a.forEach(this, (s, i) => {
      const o = a.findKey(r, i);
      if (o) {
        n[o] = re(s), delete n[i];
        return;
      }
      const c = t ? On(i) : String(i).trim();
      c !== i && delete n[i], n[c] = re(s), r[c] = !0;
    }), this;
  }
  concat(...t) {
    return this.constructor.concat(this, ...t);
  }
  toJSON(t) {
    const n = /* @__PURE__ */ Object.create(null);
    return a.forEach(this, (r, s) => {
      r != null && r !== !1 && (n[s] = t && a.isArray(r) ? r.join(", ") : r);
    }), n;
  }
  [Symbol.iterator]() {
    return Object.entries(this.toJSON())[Symbol.iterator]();
  }
  toString() {
    return Object.entries(this.toJSON()).map(([t, n]) => t + ": " + n).join(`
`);
  }
  getSetCookie() {
    return this.get("set-cookie") || [];
  }
  get [Symbol.toStringTag]() {
    return "AxiosHeaders";
  }
  static from(t) {
    return t instanceof this ? t : new this(t);
  }
  static concat(t, ...n) {
    const r = new this(t);
    return n.forEach((s) => r.set(s)), r;
  }
  static accessor(t) {
    const r = (this[De] = this[De] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function i(o) {
      const c = W(o);
      r[c] || (Tn(s, o), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(i) : i(t), this;
  }
};
A.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
a.reduceDescriptors(A.prototype, ({ value: e }, t) => {
  let n = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(r) {
      this[n] = r;
    }
  };
});
a.freezeMethods(A);
function he(e, t) {
  const n = this || Q, r = t || n, s = A.from(r.headers);
  let i = r.data;
  return a.forEach(e, function(c) {
    i = c.call(n, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function at(e) {
  return !!(e && e.__CANCEL__);
}
function J(e, t, n) {
  y.call(this, e ?? "canceled", y.ERR_CANCELED, t, n), this.name = "CanceledError";
}
a.inherits(J, y, {
  __CANCEL__: !0
});
function ct(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(new y(
    "Request failed with status code " + n.status,
    [y.ERR_BAD_REQUEST, y.ERR_BAD_RESPONSE][Math.floor(n.status / 100) - 4],
    n.config,
    n.request,
    n
  ));
}
function An(e) {
  const t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function Cn(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, i = 0, o;
  return t = t !== void 0 ? t : 1e3, function(f) {
    const l = Date.now(), u = r[i];
    o || (o = l), n[s] = f, r[s] = l;
    let h = i, b = 0;
    for (; h !== s; )
      b += n[h++], h = h % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), l - o < t)
      return;
    const S = u && l - u;
    return S ? Math.round(b * 1e3 / S) : void 0;
  };
}
function xn(e, t) {
  let n = 0, r = 1e3 / t, s, i;
  const o = (l, u = Date.now()) => {
    n = u, s = null, i && (clearTimeout(i), i = null), e(...l);
  };
  return [(...l) => {
    const u = Date.now(), h = u - n;
    h >= r ? o(l, u) : (s = l, i || (i = setTimeout(() => {
      i = null, o(s);
    }, r - h)));
  }, () => s && o(s)];
}
const oe = (e, t, n = 3) => {
  let r = 0;
  const s = Cn(50, 250);
  return xn((i) => {
    const o = i.loaded, c = i.lengthComputable ? i.total : void 0, f = o - r, l = s(f), u = o <= c;
    r = o;
    const h = {
      loaded: o,
      total: c,
      progress: c ? o / c : void 0,
      bytes: f,
      rate: l || void 0,
      estimated: l && c && u ? (c - o) / l : void 0,
      event: i,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(h);
  }, n);
}, Le = (e, t) => {
  const n = e != null;
  return [(r) => t[0]({
    lengthComputable: n,
    total: e,
    loaded: r
  }), t[1]];
}, Be = (e) => (...t) => a.asap(() => e(...t)), Nn = R.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, R.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(R.origin),
  R.navigator && /(msie|trident)/i.test(R.navigator.userAgent)
) : () => !0, Pn = R.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(e, t, n, r, s, i, o) {
      if (typeof document > "u") return;
      const c = [`${e}=${encodeURIComponent(t)}`];
      a.isNumber(n) && c.push(`expires=${new Date(n).toUTCString()}`), a.isString(r) && c.push(`path=${r}`), a.isString(s) && c.push(`domain=${s}`), i === !0 && c.push("secure"), a.isString(o) && c.push(`SameSite=${o}`), document.cookie = c.join("; ");
    },
    read(e) {
      if (typeof document > "u") return null;
      const t = document.cookie.match(new RegExp("(?:^|; )" + e + "=([^;]*)"));
      return t ? decodeURIComponent(t[1]) : null;
    },
    remove(e) {
      this.write(e, "", Date.now() - 864e5, "/");
    }
  }
) : (
  // Non-standard browser env (web workers, react-native) lack needed support.
  {
    write() {
    },
    read() {
      return null;
    },
    remove() {
    }
  }
);
function kn(e) {
  return /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function Fn(e, t) {
  return t ? e.replace(/\/?\/$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function lt(e, t, n) {
  let r = !kn(t);
  return e && (r || n == !1) ? Fn(e, t) : t;
}
const je = (e) => e instanceof A ? { ...e } : e;
function H(e, t) {
  t = t || {};
  const n = {};
  function r(l, u, h, b) {
    return a.isPlainObject(l) && a.isPlainObject(u) ? a.merge.call({ caseless: b }, l, u) : a.isPlainObject(u) ? a.merge({}, u) : a.isArray(u) ? u.slice() : u;
  }
  function s(l, u, h, b) {
    if (a.isUndefined(u)) {
      if (!a.isUndefined(l))
        return r(void 0, l, h, b);
    } else return r(l, u, h, b);
  }
  function i(l, u) {
    if (!a.isUndefined(u))
      return r(void 0, u);
  }
  function o(l, u) {
    if (a.isUndefined(u)) {
      if (!a.isUndefined(l))
        return r(void 0, l);
    } else return r(void 0, u);
  }
  function c(l, u, h) {
    if (h in t)
      return r(l, u);
    if (h in e)
      return r(void 0, l);
  }
  const f = {
    url: i,
    method: i,
    data: i,
    baseURL: o,
    transformRequest: o,
    transformResponse: o,
    paramsSerializer: o,
    timeout: o,
    timeoutMessage: o,
    withCredentials: o,
    withXSRFToken: o,
    adapter: o,
    responseType: o,
    xsrfCookieName: o,
    xsrfHeaderName: o,
    onUploadProgress: o,
    onDownloadProgress: o,
    decompress: o,
    maxContentLength: o,
    maxBodyLength: o,
    beforeRedirect: o,
    transport: o,
    httpAgent: o,
    httpsAgent: o,
    cancelToken: o,
    socketPath: o,
    responseEncoding: o,
    validateStatus: c,
    headers: (l, u, h) => s(je(l), je(u), h, !0)
  };
  return a.forEach(Object.keys({ ...e, ...t }), function(u) {
    const h = f[u] || s, b = h(e[u], t[u], u);
    a.isUndefined(b) && h !== c || (n[u] = b);
  }), n;
}
const ut = (e) => {
  const t = H({}, e);
  let { data: n, withXSRFToken: r, xsrfHeaderName: s, xsrfCookieName: i, headers: o, auth: c } = t;
  if (t.headers = o = A.from(o), t.url = st(lt(t.baseURL, t.url, t.allowAbsoluteUrls), e.params, e.paramsSerializer), c && o.set(
    "Authorization",
    "Basic " + btoa((c.username || "") + ":" + (c.password ? unescape(encodeURIComponent(c.password)) : ""))
  ), a.isFormData(n)) {
    if (R.hasStandardBrowserEnv || R.hasStandardBrowserWebWorkerEnv)
      o.setContentType(void 0);
    else if (a.isFunction(n.getHeaders)) {
      const f = n.getHeaders(), l = ["content-type", "content-length"];
      Object.entries(f).forEach(([u, h]) => {
        l.includes(u.toLowerCase()) && o.set(u, h);
      });
    }
  }
  if (R.hasStandardBrowserEnv && (r && a.isFunction(r) && (r = r(t)), r || r !== !1 && Nn(t.url))) {
    const f = s && i && Pn.read(i);
    f && o.set(s, f);
  }
  return t;
}, Un = typeof XMLHttpRequest < "u", _n = Un && function(e) {
  return new Promise(function(n, r) {
    const s = ut(e);
    let i = s.data;
    const o = A.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: f, onDownloadProgress: l } = s, u, h, b, S, d;
    function m() {
      S && S(), d && d(), s.cancelToken && s.cancelToken.unsubscribe(u), s.signal && s.signal.removeEventListener("abort", u);
    }
    let p = new XMLHttpRequest();
    p.open(s.method.toUpperCase(), s.url, !0), p.timeout = s.timeout;
    function E() {
      if (!p)
        return;
      const g = A.from(
        "getAllResponseHeaders" in p && p.getAllResponseHeaders()
      ), P = {
        data: !c || c === "text" || c === "json" ? p.responseText : p.response,
        status: p.status,
        statusText: p.statusText,
        headers: g,
        config: e,
        request: p
      };
      ct(function(x) {
        n(x), m();
      }, function(x) {
        r(x), m();
      }, P), p = null;
    }
    "onloadend" in p ? p.onloadend = E : p.onreadystatechange = function() {
      !p || p.readyState !== 4 || p.status === 0 && !(p.responseURL && p.responseURL.indexOf("file:") === 0) || setTimeout(E);
    }, p.onabort = function() {
      p && (r(new y("Request aborted", y.ECONNABORTED, e, p)), p = null);
    }, p.onerror = function(O) {
      const P = O && O.message ? O.message : "Network Error", B = new y(P, y.ERR_NETWORK, e, p);
      B.event = O || null, r(B), p = null;
    }, p.ontimeout = function() {
      let O = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const P = s.transitional || ot;
      s.timeoutErrorMessage && (O = s.timeoutErrorMessage), r(new y(
        O,
        P.clarifyTimeoutError ? y.ETIMEDOUT : y.ECONNABORTED,
        e,
        p
      )), p = null;
    }, i === void 0 && o.setContentType(null), "setRequestHeader" in p && a.forEach(o.toJSON(), function(O, P) {
      p.setRequestHeader(P, O);
    }), a.isUndefined(s.withCredentials) || (p.withCredentials = !!s.withCredentials), c && c !== "json" && (p.responseType = s.responseType), l && ([b, d] = oe(l, !0), p.addEventListener("progress", b)), f && p.upload && ([h, S] = oe(f), p.upload.addEventListener("progress", h), p.upload.addEventListener("loadend", S)), (s.cancelToken || s.signal) && (u = (g) => {
      p && (r(!g || g.type ? new J(null, e, p) : g), p.abort(), p = null);
    }, s.cancelToken && s.cancelToken.subscribe(u), s.signal && (s.signal.aborted ? u() : s.signal.addEventListener("abort", u)));
    const C = An(s.url);
    if (C && R.protocols.indexOf(C) === -1) {
      r(new y("Unsupported protocol " + C + ":", y.ERR_BAD_REQUEST, e));
      return;
    }
    p.send(i || null);
  });
}, Dn = (e, t) => {
  const { length: n } = e = e ? e.filter(Boolean) : [];
  if (t || n) {
    let r = new AbortController(), s;
    const i = function(l) {
      if (!s) {
        s = !0, c();
        const u = l instanceof Error ? l : this.reason;
        r.abort(u instanceof y ? u : new J(u instanceof Error ? u.message : u));
      }
    };
    let o = t && setTimeout(() => {
      o = null, i(new y(`timeout ${t} of ms exceeded`, y.ETIMEDOUT));
    }, t);
    const c = () => {
      e && (o && clearTimeout(o), o = null, e.forEach((l) => {
        l.unsubscribe ? l.unsubscribe(i) : l.removeEventListener("abort", i);
      }), e = null);
    };
    e.forEach((l) => l.addEventListener("abort", i));
    const { signal: f } = r;
    return f.unsubscribe = () => a.asap(c), f;
  }
}, Ln = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, Bn = async function* (e, t) {
  for await (const n of jn(e))
    yield* Ln(n, t);
}, jn = async function* (e) {
  if (e[Symbol.asyncIterator]) {
    yield* e;
    return;
  }
  const t = e.getReader();
  try {
    for (; ; ) {
      const { done: n, value: r } = await t.read();
      if (n)
        break;
      yield r;
    }
  } finally {
    await t.cancel();
  }
}, qe = (e, t, n, r) => {
  const s = Bn(e, t);
  let i = 0, o, c = (f) => {
    o || (o = !0, r && r(f));
  };
  return new ReadableStream({
    async pull(f) {
      try {
        const { done: l, value: u } = await s.next();
        if (l) {
          c(), f.close();
          return;
        }
        let h = u.byteLength;
        if (n) {
          let b = i += h;
          n(b);
        }
        f.enqueue(new Uint8Array(u));
      } catch (l) {
        throw c(l), l;
      }
    },
    cancel(f) {
      return c(f), s.return();
    }
  }, {
    highWaterMark: 2
  });
}, Ie = 64 * 1024, { isFunction: te } = a, qn = (({ Request: e, Response: t }) => ({
  Request: e,
  Response: t
}))(a.global), {
  ReadableStream: He,
  TextEncoder: Me
} = a.global, $e = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, In = (e) => {
  e = a.merge.call({
    skipUndefined: !0
  }, qn, e);
  const { fetch: t, Request: n, Response: r } = e, s = t ? te(t) : typeof fetch == "function", i = te(n), o = te(r);
  if (!s)
    return !1;
  const c = s && te(He), f = s && (typeof Me == "function" ? /* @__PURE__ */ ((d) => (m) => d.encode(m))(new Me()) : async (d) => new Uint8Array(await new n(d).arrayBuffer())), l = i && c && $e(() => {
    let d = !1;
    const m = new n(R.origin, {
      body: new He(),
      method: "POST",
      get duplex() {
        return d = !0, "half";
      }
    }).headers.has("Content-Type");
    return d && !m;
  }), u = o && c && $e(() => a.isReadableStream(new r("").body)), h = {
    stream: u && ((d) => d.body)
  };
  s && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((d) => {
    !h[d] && (h[d] = (m, p) => {
      let E = m && m[d];
      if (E)
        return E.call(m);
      throw new y(`Response type '${d}' is not supported`, y.ERR_NOT_SUPPORT, p);
    });
  });
  const b = async (d) => {
    if (d == null)
      return 0;
    if (a.isBlob(d))
      return d.size;
    if (a.isSpecCompliantForm(d))
      return (await new n(R.origin, {
        method: "POST",
        body: d
      }).arrayBuffer()).byteLength;
    if (a.isArrayBufferView(d) || a.isArrayBuffer(d))
      return d.byteLength;
    if (a.isURLSearchParams(d) && (d = d + ""), a.isString(d))
      return (await f(d)).byteLength;
  }, S = async (d, m) => {
    const p = a.toFiniteNumber(d.getContentLength());
    return p ?? b(m);
  };
  return async (d) => {
    let {
      url: m,
      method: p,
      data: E,
      signal: C,
      cancelToken: g,
      timeout: O,
      onDownloadProgress: P,
      onUploadProgress: B,
      responseType: x,
      headers: fe,
      withCredentials: Z = "same-origin",
      fetchOptions: Te
    } = ut(d), Ae = t || fetch;
    x = x ? (x + "").toLowerCase() : "text";
    let Y = Dn([C, g && g.toAbortSignal()], O), V = null;
    const j = Y && Y.unsubscribe && (() => {
      Y.unsubscribe();
    });
    let Ce;
    try {
      if (B && l && p !== "get" && p !== "head" && (Ce = await S(fe, E)) !== 0) {
        let D = new n(m, {
          method: "POST",
          body: E,
          duplex: "half"
        }), $;
        if (a.isFormData(E) && ($ = D.headers.get("content-type")) && fe.setContentType($), D.body) {
          const [de, ee] = Le(
            Ce,
            oe(Be(B))
          );
          E = qe(D.body, Ie, de, ee);
        }
      }
      a.isString(Z) || (Z = Z ? "include" : "omit");
      const F = i && "credentials" in n.prototype, xe = {
        ...Te,
        signal: Y,
        method: p.toUpperCase(),
        headers: fe.normalize().toJSON(),
        body: E,
        duplex: "half",
        credentials: F ? Z : void 0
      };
      V = i && new n(m, xe);
      let _ = await (i ? Ae(V, Te) : Ae(m, xe));
      const Ne = u && (x === "stream" || x === "response");
      if (u && (P || Ne && j)) {
        const D = {};
        ["status", "statusText", "headers"].forEach((Pe) => {
          D[Pe] = _[Pe];
        });
        const $ = a.toFiniteNumber(_.headers.get("content-length")), [de, ee] = P && Le(
          $,
          oe(Be(P), !0)
        ) || [];
        _ = new r(
          qe(_.body, Ie, de, () => {
            ee && ee(), j && j();
          }),
          D
        );
      }
      x = x || "text";
      let yt = await h[a.findKey(h, x) || "text"](_, d);
      return !Ne && j && j(), await new Promise((D, $) => {
        ct(D, $, {
          data: yt,
          headers: A.from(_.headers),
          status: _.status,
          statusText: _.statusText,
          config: d,
          request: V
        });
      });
    } catch (F) {
      throw j && j(), F && F.name === "TypeError" && /Load failed|fetch/i.test(F.message) ? Object.assign(
        new y("Network Error", y.ERR_NETWORK, d, V),
        {
          cause: F.cause || F
        }
      ) : y.from(F, F && F.code, d, V);
    }
  };
}, Hn = /* @__PURE__ */ new Map(), ft = (e) => {
  let t = e && e.env || {};
  const { fetch: n, Request: r, Response: s } = t, i = [
    r,
    s,
    n
  ];
  let o = i.length, c = o, f, l, u = Hn;
  for (; c--; )
    f = i[c], l = u.get(f), l === void 0 && u.set(f, l = c ? /* @__PURE__ */ new Map() : In(t)), u = l;
  return l;
};
ft();
const Oe = {
  http: nn,
  xhr: _n,
  fetch: {
    get: ft
  }
};
a.forEach(Oe, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { value: t });
  }
});
const ve = (e) => `- ${e}`, Mn = (e) => a.isFunction(e) || e === null || e === !1;
function $n(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: n } = e;
  let r, s;
  const i = {};
  for (let o = 0; o < n; o++) {
    r = e[o];
    let c;
    if (s = r, !Mn(r) && (s = Oe[(c = String(r)).toLowerCase()], s === void 0))
      throw new y(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    i[c || "#" + o] = s;
  }
  if (!s) {
    const o = Object.entries(i).map(
      ([f, l]) => `adapter ${f} ` + (l === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = n ? o.length > 1 ? `since :
` + o.map(ve).join(`
`) : " " + ve(o[0]) : "as no adapter specified";
    throw new y(
      "There is no suitable adapter to dispatch the request " + c,
      "ERR_NOT_SUPPORT"
    );
  }
  return s;
}
const dt = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: $n,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: Oe
};
function me(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new J(null, e);
}
function ze(e) {
  return me(e), e.headers = A.from(e.headers), e.data = he.call(
    e,
    e.transformRequest
  ), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), dt.getAdapter(e.adapter || Q.adapter, e)(e).then(function(r) {
    return me(e), r.data = he.call(
      e,
      e.transformResponse,
      r
    ), r.headers = A.from(r.headers), r;
  }, function(r) {
    return at(r) || (me(e), r && r.response && (r.response.data = he.call(
      e,
      e.transformResponse,
      r.response
    ), r.response.headers = A.from(r.response.headers))), Promise.reject(r);
  });
}
const pt = "1.13.1", ue = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  ue[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Je = {};
ue.transitional = function(t, n, r) {
  function s(i, o) {
    return "[Axios v" + pt + "] Transitional option '" + i + "'" + o + (r ? ". " + r : "");
  }
  return (i, o, c) => {
    if (t === !1)
      throw new y(
        s(o, " has been removed" + (n ? " in " + n : "")),
        y.ERR_DEPRECATED
      );
    return n && !Je[o] && (Je[o] = !0, console.warn(
      s(
        o,
        " has been deprecated since v" + n + " and will be removed in the near future"
      )
    )), t ? t(i, o, c) : !0;
  };
};
ue.spelling = function(t) {
  return (n, r) => (console.warn(`${r} is likely a misspelling of ${t}`), !0);
};
function vn(e, t, n) {
  if (typeof e != "object")
    throw new y("options must be an object", y.ERR_BAD_OPTION_VALUE);
  const r = Object.keys(e);
  let s = r.length;
  for (; s-- > 0; ) {
    const i = r[s], o = t[i];
    if (o) {
      const c = e[i], f = c === void 0 || o(c, i, e);
      if (f !== !0)
        throw new y("option " + i + " must be " + f, y.ERR_BAD_OPTION_VALUE);
      continue;
    }
    if (n !== !0)
      throw new y("Unknown option " + i, y.ERR_BAD_OPTION);
  }
}
const se = {
  assertOptions: vn,
  validators: ue
}, U = se.validators;
let I = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new _e(),
      response: new _e()
    };
  }
  /**
   * Dispatch a request
   *
   * @param {String|Object} configOrUrl The config specific for this request (merged with this.defaults)
   * @param {?Object} config
   *
   * @returns {Promise} The Promise to be fulfilled
   */
  async request(t, n) {
    try {
      return await this._request(t, n);
    } catch (r) {
      if (r instanceof Error) {
        let s = {};
        Error.captureStackTrace ? Error.captureStackTrace(s) : s = new Error();
        const i = s.stack ? s.stack.replace(/^.+\n/, "") : "";
        try {
          r.stack ? i && !String(r.stack).endsWith(i.replace(/^.+\n.+\n/, "")) && (r.stack += `
` + i) : r.stack = i;
        } catch {
        }
      }
      throw r;
    }
  }
  _request(t, n) {
    typeof t == "string" ? (n = n || {}, n.url = t) : n = t || {}, n = H(this.defaults, n);
    const { transitional: r, paramsSerializer: s, headers: i } = n;
    r !== void 0 && se.assertOptions(r, {
      silentJSONParsing: U.transitional(U.boolean),
      forcedJSONParsing: U.transitional(U.boolean),
      clarifyTimeoutError: U.transitional(U.boolean)
    }, !1), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : se.assertOptions(s, {
      encode: U.function,
      serialize: U.function
    }, !0)), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), se.assertOptions(n, {
      baseUrl: U.spelling("baseURL"),
      withXsrfToken: U.spelling("withXSRFToken")
    }, !0), n.method = (n.method || this.defaults.method || "get").toLowerCase();
    let o = i && a.merge(
      i.common,
      i[n.method]
    );
    i && a.forEach(
      ["delete", "get", "head", "post", "put", "patch", "common"],
      (d) => {
        delete i[d];
      }
    ), n.headers = A.concat(o, i);
    const c = [];
    let f = !0;
    this.interceptors.request.forEach(function(m) {
      typeof m.runWhen == "function" && m.runWhen(n) === !1 || (f = f && m.synchronous, c.unshift(m.fulfilled, m.rejected));
    });
    const l = [];
    this.interceptors.response.forEach(function(m) {
      l.push(m.fulfilled, m.rejected);
    });
    let u, h = 0, b;
    if (!f) {
      const d = [ze.bind(this), void 0];
      for (d.unshift(...c), d.push(...l), b = d.length, u = Promise.resolve(n); h < b; )
        u = u.then(d[h++], d[h++]);
      return u;
    }
    b = c.length;
    let S = n;
    for (; h < b; ) {
      const d = c[h++], m = c[h++];
      try {
        S = d(S);
      } catch (p) {
        m.call(this, p);
        break;
      }
    }
    try {
      u = ze.call(this, S);
    } catch (d) {
      return Promise.reject(d);
    }
    for (h = 0, b = l.length; h < b; )
      u = u.then(l[h++], l[h++]);
    return u;
  }
  getUri(t) {
    t = H(this.defaults, t);
    const n = lt(t.baseURL, t.url, t.allowAbsoluteUrls);
    return st(n, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  I.prototype[t] = function(n, r) {
    return this.request(H(r || {}, {
      method: t,
      url: n,
      data: (r || {}).data
    }));
  };
});
a.forEach(["post", "put", "patch"], function(t) {
  function n(r) {
    return function(i, o, c) {
      return this.request(H(c || {}, {
        method: t,
        headers: r ? {
          "Content-Type": "multipart/form-data"
        } : {},
        url: i,
        data: o
      }));
    };
  }
  I.prototype[t] = n(), I.prototype[t + "Form"] = n(!0);
});
let zn = class ht {
  constructor(t) {
    if (typeof t != "function")
      throw new TypeError("executor must be a function.");
    let n;
    this.promise = new Promise(function(i) {
      n = i;
    });
    const r = this;
    this.promise.then((s) => {
      if (!r._listeners) return;
      let i = r._listeners.length;
      for (; i-- > 0; )
        r._listeners[i](s);
      r._listeners = null;
    }), this.promise.then = (s) => {
      let i;
      const o = new Promise((c) => {
        r.subscribe(c), i = c;
      }).then(s);
      return o.cancel = function() {
        r.unsubscribe(i);
      }, o;
    }, t(function(i, o, c) {
      r.reason || (r.reason = new J(i, o, c), n(r.reason));
    });
  }
  /**
   * Throws a `CanceledError` if cancellation has been requested.
   */
  throwIfRequested() {
    if (this.reason)
      throw this.reason;
  }
  /**
   * Subscribe to the cancel signal
   */
  subscribe(t) {
    if (this.reason) {
      t(this.reason);
      return;
    }
    this._listeners ? this._listeners.push(t) : this._listeners = [t];
  }
  /**
   * Unsubscribe from the cancel signal
   */
  unsubscribe(t) {
    if (!this._listeners)
      return;
    const n = this._listeners.indexOf(t);
    n !== -1 && this._listeners.splice(n, 1);
  }
  toAbortSignal() {
    const t = new AbortController(), n = (r) => {
      t.abort(r);
    };
    return this.subscribe(n), t.signal.unsubscribe = () => this.unsubscribe(n), t.signal;
  }
  /**
   * Returns an object that contains a new `CancelToken` and a function that, when called,
   * cancels the `CancelToken`.
   */
  static source() {
    let t;
    return {
      token: new ht(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function Jn(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function Vn(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const Ee = {
  Continue: 100,
  SwitchingProtocols: 101,
  Processing: 102,
  EarlyHints: 103,
  Ok: 200,
  Created: 201,
  Accepted: 202,
  NonAuthoritativeInformation: 203,
  NoContent: 204,
  ResetContent: 205,
  PartialContent: 206,
  MultiStatus: 207,
  AlreadyReported: 208,
  ImUsed: 226,
  MultipleChoices: 300,
  MovedPermanently: 301,
  Found: 302,
  SeeOther: 303,
  NotModified: 304,
  UseProxy: 305,
  Unused: 306,
  TemporaryRedirect: 307,
  PermanentRedirect: 308,
  BadRequest: 400,
  Unauthorized: 401,
  PaymentRequired: 402,
  Forbidden: 403,
  NotFound: 404,
  MethodNotAllowed: 405,
  NotAcceptable: 406,
  ProxyAuthenticationRequired: 407,
  RequestTimeout: 408,
  Conflict: 409,
  Gone: 410,
  LengthRequired: 411,
  PreconditionFailed: 412,
  PayloadTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  UnprocessableEntity: 422,
  Locked: 423,
  FailedDependency: 424,
  TooEarly: 425,
  UpgradeRequired: 426,
  PreconditionRequired: 428,
  TooManyRequests: 429,
  RequestHeaderFieldsTooLarge: 431,
  UnavailableForLegalReasons: 451,
  InternalServerError: 500,
  NotImplemented: 501,
  BadGateway: 502,
  ServiceUnavailable: 503,
  GatewayTimeout: 504,
  HttpVersionNotSupported: 505,
  VariantAlsoNegotiates: 506,
  InsufficientStorage: 507,
  LoopDetected: 508,
  NotExtended: 510,
  NetworkAuthenticationRequired: 511,
  WebServerIsDown: 521,
  ConnectionTimedOut: 522,
  OriginIsUnreachable: 523,
  TimeoutOccurred: 524,
  SslHandshakeFailed: 525,
  InvalidSslCertificate: 526
};
Object.entries(Ee).forEach(([e, t]) => {
  Ee[t] = e;
});
function mt(e) {
  const t = new I(e), n = Ve(I.prototype.request, t);
  return a.extend(n, I.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return mt(H(e, s));
  }, n;
}
const w = mt(Q);
w.Axios = I;
w.CanceledError = J;
w.CancelToken = zn;
w.isCancel = at;
w.VERSION = pt;
w.toFormData = le;
w.AxiosError = y;
w.Cancel = w.CanceledError;
w.all = function(t) {
  return Promise.all(t);
};
w.spread = Jn;
w.isAxiosError = Vn;
w.mergeConfig = H;
w.AxiosHeaders = A;
w.formToJSON = (e) => it(a.isHTMLForm(e) ? new FormData(e) : e);
w.getAdapter = dt.getAdapter;
w.HttpStatusCode = Ee;
w.default = w;
const {
  Axios: Gn,
  AxiosError: Qn,
  CanceledError: Zn,
  isCancel: Yn,
  CancelToken: er,
  VERSION: tr,
  all: nr,
  Cancel: rr,
  isAxiosError: sr,
  spread: or,
  toFormData: ir,
  AxiosHeaders: ar,
  HttpStatusCode: cr,
  formToJSON: lr,
  getAdapter: ur,
  mergeConfig: fr
} = w, M = w.create({
  withCredentials: !0,
  timeout: 5e3,
  // Add a timeout of 5 seconds
  headers: {
    "Content-Type": "application/json"
  }
});
function dr() {
  const e = "csrftoken=", n = decodeURIComponent(document.cookie).split(";");
  for (let r of n)
    if (r = r.trim(), r.indexOf(e) === 0)
      return r.substring(e.length);
  return "";
}
M.interceptors.request.use(
  (e) => e,
  (e) => Promise.reject(e)
);
M.interceptors.response.use(
  (e) => e,
  (e) => {
    if (e.response)
      switch (e.response.status) {
        case 401:
          console.error("Unauthorized: Please log in", e.response.data);
          break;
        case 403:
          console.error(
            "Forbidden: You don't have permission",
            e.response.data
          );
          break;
        case 404:
          console.error(
            "Not Found: The requested resource doesn't exist",
            e.response.data
          );
          break;
        case 422:
          console.error("Validation Error:", e.response.data);
          break;
        case 500:
          console.error(
            "Server Error: Please try again later",
            e.response.data
          );
          break;
        default:
          console.error(
            `Error ${e.response.status}: ${e.response.data}`
          );
      }
    else e.request ? console.error("Network Error: No response received") : console.error("Request Error:", e.message);
    return Promise.reject(e);
  }
);
function pr(e, t = {}) {
  const n = L(e), r = N(null), s = N(null), i = N(!0), o = M.get(n, {
    headers: t
  }).then((c) => (s.value = c.data, i.value = !1, { loading: i, backendError: r, responseData: s })).catch((c) => (r.value = c, i.value = !1, { loading: i, backendError: r, responseData: s }));
  return {
    loading: i,
    backendError: r,
    responseData: s,
    then: (c, f) => o.then(c, f)
  };
}
function hr(e, t, n = {}) {
  const r = L(e), s = N(null), i = N(null), o = N(!0), c = M.post(r, L(t), {
    headers: n
  }).then((f) => (i.value = f.data, o.value = !1, { loading: o, backendError: s, responseData: i })).catch((f) => (s.value = f, o.value = !1, { loading: o, backendError: s, responseData: i }));
  return {
    loading: o,
    backendError: s,
    responseData: i,
    then: (f, l) => c.then(f, l)
  };
}
function mr(e, t, n = {}) {
  const r = L(e), s = N(null), i = L(t), o = N(!0), c = M.put(r, i, {
    headers: n
  }).then((f) => (console.log(f.statusText), o.value = !1, { loading: o, backendError: s })).catch((f) => (console.log(f), s.value = f, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (f, l) => c.then(f, l)
  };
}
function yr(e, t, n = {}) {
  const r = L(e), s = N(null), i = L(t), o = N(!0), c = M.patch(r, i, {
    headers: n
  }).then((f) => (o.value = !1, { loading: o, backendError: s })).catch((f) => (console.log(f), s.value = f, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (f, l) => c.then(f, l)
  };
}
function br(e, t = {}) {
  const n = L(e), r = N(null), s = N(!0), i = M.delete(n, {
    headers: t
  }).then((o) => (s.value = !1, { loading: s, backendError: r })).catch((o) => (console.log(o), r.value = o, s.value = !1, { loading: s, backendError: r }));
  return {
    loading: s,
    backendError: r,
    then: (o, c) => i.then(o, c)
  };
}
export {
  dr as getCsrfToken,
  br as useDeleteBackendData,
  pr as useGetBackendData,
  yr as usePatchBackendData,
  hr as usePostBackendData,
  mr as usePutBackendData
};
