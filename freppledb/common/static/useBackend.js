import { toValue as B, ref as P } from "vue";
function We(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: bt } = Object.prototype, { getPrototypeOf: Re } = Object, { iterator: ie, toStringTag: Ke } = Symbol, ae = /* @__PURE__ */ ((e) => (t) => {
  const n = bt.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), F = (e) => (e = e.toLowerCase(), (t) => ae(t) === e), ce = (e) => (t) => typeof t === e, { isArray: z } = Array, v = ce("undefined");
function W(e) {
  return e !== null && !v(e) && e.constructor !== null && !v(e.constructor) && A(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const Xe = F("ArrayBuffer");
function yt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && Xe(e.buffer), t;
}
const wt = ce("string"), A = ce("function"), Ge = ce("number"), K = (e) => e !== null && typeof e == "object", Et = (e) => e === !0 || e === !1, ne = (e) => {
  if (ae(e) !== "object")
    return !1;
  const t = Re(e);
  return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(Ke in e) && !(ie in e);
}, Rt = (e) => {
  if (!K(e) || W(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, gt = F("Date"), St = F("File"), Ot = F("Blob"), Tt = F("FileList"), At = (e) => K(e) && A(e.pipe), Ct = (e) => {
  let t;
  return e && (typeof FormData == "function" && e instanceof FormData || A(e.append) && ((t = ae(e)) === "formdata" || // detect form-data instance
  t === "object" && A(e.toString) && e.toString() === "[object FormData]"));
}, xt = F("URLSearchParams"), [_t, Nt, Pt, Dt] = [
  "ReadableStream",
  "Request",
  "Response",
  "Headers"
].map(F), Ft = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function X(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), z(e))
    for (r = 0, s = e.length; r < s; r++)
      t.call(null, e[r], r, e);
  else {
    if (W(e))
      return;
    const i = n ? Object.getOwnPropertyNames(e) : Object.keys(e), o = i.length;
    let c;
    for (r = 0; r < o; r++)
      c = i[r], t.call(null, e[c], c, e);
  }
}
function Qe(e, t) {
  if (W(e))
    return null;
  t = t.toLowerCase();
  const n = Object.keys(e);
  let r = n.length, s;
  for (; r-- > 0; )
    if (s = n[r], t === s.toLowerCase())
      return s;
  return null;
}
const q = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, Ye = (e) => !v(e) && e !== q;
function be() {
  const { caseless: e, skipUndefined: t } = Ye(this) && this || {}, n = {}, r = (s, i) => {
    if (i === "__proto__" || i === "constructor" || i === "prototype")
      return;
    const o = e && Qe(n, i) || i;
    ne(n[o]) && ne(s) ? n[o] = be(n[o], s) : ne(s) ? n[o] = be({}, s) : z(s) ? n[o] = s.slice() : (!t || !v(s)) && (n[o] = s);
  };
  for (let s = 0, i = arguments.length; s < i; s++)
    arguments[s] && X(arguments[s], r);
  return n;
}
const Ut = (e, t, n, { allOwnKeys: r } = {}) => (X(
  t,
  (s, i) => {
    n && A(s) ? Object.defineProperty(e, i, {
      value: We(s, n),
      writable: !0,
      enumerable: !0,
      configurable: !0
    }) : Object.defineProperty(e, i, {
      value: s,
      writable: !0,
      enumerable: !0,
      configurable: !0
    });
  },
  { allOwnKeys: r }
), e), kt = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Bt = (e, t, n, r) => {
  e.prototype = Object.create(
    t.prototype,
    r
  ), Object.defineProperty(e.prototype, "constructor", {
    value: e,
    writable: !0,
    enumerable: !1,
    configurable: !0
  }), Object.defineProperty(e, "super", {
    value: t.prototype
  }), n && Object.assign(e.prototype, n);
}, Lt = (e, t, n, r) => {
  let s, i, o;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0; )
      o = s[i], (!r || r(o, e, t)) && !c[o] && (t[o] = e[o], c[o] = !0);
    e = n !== !1 && Re(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, jt = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, qt = (e) => {
  if (!e) return null;
  if (z(e)) return e;
  let t = e.length;
  if (!Ge(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, It = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && Re(Uint8Array)), Ht = (e, t) => {
  const r = (e && e[ie]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const i = s.value;
    t.call(e, i[0], i[1]);
  }
}, Mt = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, $t = F("HTMLFormElement"), vt = (e) => e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function(n, r, s) {
  return r.toUpperCase() + s;
}), De = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), zt = F("RegExp"), Ze = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  X(n, (s, i) => {
    let o;
    (o = t(s, i, e)) !== !1 && (r[i] = o || s);
  }), Object.defineProperties(e, r);
}, Jt = (e) => {
  Ze(e, (t, n) => {
    if (A(e) && ["arguments", "caller", "callee"].indexOf(n) !== -1)
      return !1;
    const r = e[n];
    if (A(r)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + n + "'");
      });
    }
  });
}, Vt = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((i) => {
      n[i] = !0;
    });
  };
  return z(e) ? r(e) : r(String(e).split(t)), n;
}, Wt = () => {
}, Kt = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Xt(e) {
  return !!(e && A(e.append) && e[Ke] === "FormData" && e[ie]);
}
const Gt = (e) => {
  const t = new Array(10), n = (r, s) => {
    if (K(r)) {
      if (t.indexOf(r) >= 0)
        return;
      if (W(r))
        return r;
      if (!("toJSON" in r)) {
        t[s] = r;
        const i = z(r) ? [] : {};
        return X(r, (o, c) => {
          const f = n(o, s + 1);
          !v(f) && (i[c] = f);
        }), t[s] = void 0, i;
      }
    }
    return r;
  };
  return n(e, 0);
}, Qt = F("AsyncFunction"), Yt = (e) => e && (K(e) || A(e)) && A(e.then) && A(e.catch), et = ((e, t) => e ? setImmediate : t ? ((n, r) => (q.addEventListener(
  "message",
  ({ source: s, data: i }) => {
    s === q && i === n && r.length && r.shift()();
  },
  !1
), (s) => {
  r.push(s), q.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(typeof setImmediate == "function", A(q.postMessage)), Zt = typeof queueMicrotask < "u" ? queueMicrotask.bind(q) : typeof process < "u" && process.nextTick || et, en = (e) => e != null && A(e[ie]), a = {
  isArray: z,
  isArrayBuffer: Xe,
  isBuffer: W,
  isFormData: Ct,
  isArrayBufferView: yt,
  isString: wt,
  isNumber: Ge,
  isBoolean: Et,
  isObject: K,
  isPlainObject: ne,
  isEmptyObject: Rt,
  isReadableStream: _t,
  isRequest: Nt,
  isResponse: Pt,
  isHeaders: Dt,
  isUndefined: v,
  isDate: gt,
  isFile: St,
  isBlob: Ot,
  isRegExp: zt,
  isFunction: A,
  isStream: At,
  isURLSearchParams: xt,
  isTypedArray: It,
  isFileList: Tt,
  forEach: X,
  merge: be,
  extend: Ut,
  trim: Ft,
  stripBOM: kt,
  inherits: Bt,
  toFlatObject: Lt,
  kindOf: ae,
  kindOfTest: F,
  endsWith: jt,
  toArray: qt,
  forEachEntry: Ht,
  matchAll: Mt,
  isHTMLForm: $t,
  hasOwnProperty: De,
  hasOwnProp: De,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors: Ze,
  freezeMethods: Jt,
  toObjectSet: Vt,
  toCamelCase: vt,
  noop: Wt,
  toFiniteNumber: Kt,
  findKey: Qe,
  global: q,
  isContextDefined: Ye,
  isSpecCompliantForm: Xt,
  toJSONObject: Gt,
  isAsyncFn: Qt,
  isThenable: Yt,
  setImmediate: et,
  asap: Zt,
  isIterable: en
};
let b = class tt extends Error {
  static from(t, n, r, s, i, o) {
    const c = new tt(t.message, n || t.code, r, s, i);
    return c.cause = t, c.name = t.name, o && Object.assign(c, o), c;
  }
  /**
   * Create an Error with the specified message, config, error code, request and response.
   *
   * @param {string} message The error message.
   * @param {string} [code] The error code (for example, 'ECONNABORTED').
   * @param {Object} [config] The config.
   * @param {Object} [request] The request.
   * @param {Object} [response] The response.
   *
   * @returns {Error} The created error.
   */
  constructor(t, n, r, s, i) {
    super(t), this.name = "AxiosError", this.isAxiosError = !0, n && (this.code = n), r && (this.config = r), s && (this.request = s), i && (this.response = i, this.status = i.status);
  }
  toJSON() {
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
};
b.ERR_BAD_OPTION_VALUE = "ERR_BAD_OPTION_VALUE";
b.ERR_BAD_OPTION = "ERR_BAD_OPTION";
b.ECONNABORTED = "ECONNABORTED";
b.ETIMEDOUT = "ETIMEDOUT";
b.ERR_NETWORK = "ERR_NETWORK";
b.ERR_FR_TOO_MANY_REDIRECTS = "ERR_FR_TOO_MANY_REDIRECTS";
b.ERR_DEPRECATED = "ERR_DEPRECATED";
b.ERR_BAD_RESPONSE = "ERR_BAD_RESPONSE";
b.ERR_BAD_REQUEST = "ERR_BAD_REQUEST";
b.ERR_CANCELED = "ERR_CANCELED";
b.ERR_NOT_SUPPORT = "ERR_NOT_SUPPORT";
b.ERR_INVALID_URL = "ERR_INVALID_URL";
const tn = null;
function ye(e) {
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
function nn(e) {
  return a.isArray(e) && !e.some(ye);
}
const rn = a.toFlatObject(a, {}, null, function(t) {
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
  const r = n.metaTokens, s = n.visitor || l, i = n.dots, o = n.indexes, f = (n.Blob || typeof Blob < "u" && Blob) && a.isSpecCompliantForm(t);
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function u(d) {
    if (d === null) return "";
    if (a.isDate(d))
      return d.toISOString();
    if (a.isBoolean(d))
      return d.toString();
    if (!f && a.isBlob(d))
      throw new b("Blob is not supported. Use a Buffer instead.");
    return a.isArrayBuffer(d) || a.isTypedArray(d) ? f && typeof Blob == "function" ? new Blob([d]) : Buffer.from(d) : d;
  }
  function l(d, m, p) {
    let E = d;
    if (d && !p && typeof d == "object") {
      if (a.endsWith(m, "{}"))
        m = r ? m : m.slice(0, -2), d = JSON.stringify(d);
      else if (a.isArray(d) && nn(d) || (a.isFileList(d) || a.endsWith(m, "[]")) && (E = a.toArray(d)))
        return m = nt(m), E.forEach(function(R, O) {
          !(a.isUndefined(R) || R === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            o === !0 ? Fe([m], O, i) : o === null ? m : m + "[]",
            u(R)
          );
        }), !1;
    }
    return ye(d) ? !0 : (t.append(Fe(p, m, i), u(d)), !1);
  }
  const h = [], y = Object.assign(rn, {
    defaultVisitor: l,
    convertValue: u,
    isVisitable: ye
  });
  function g(d, m) {
    if (!a.isUndefined(d)) {
      if (h.indexOf(d) !== -1)
        throw Error("Circular reference detected in " + m.join("."));
      h.push(d), a.forEach(d, function(E, x) {
        (!(a.isUndefined(E) || E === null) && s.call(
          t,
          E,
          a.isString(x) ? x.trim() : x,
          m,
          y
        )) === !0 && g(E, m ? m.concat(x) : [x]);
      }), h.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return g(e), t;
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
function ge(e, t) {
  this._pairs = [], e && le(e, this, t);
}
const rt = ge.prototype;
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
function sn(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function st(e, t, n) {
  if (!t)
    return e;
  const r = n && n.encode || sn, s = a.isFunction(n) ? {
    serialize: n
  } : n, i = s && s.serialize;
  let o;
  if (i ? o = i(t, s) : o = a.isURLSearchParams(t) ? t.toString() : new ge(t, s).toString(r), o) {
    const c = e.indexOf("#");
    c !== -1 && (e = e.slice(0, c)), e += (e.indexOf("?") === -1 ? "?" : "&") + o;
  }
  return e;
}
class ke {
  constructor() {
    this.handlers = [];
  }
  /**
   * Add a new interceptor to the stack
   *
   * @param {Function} fulfilled The function to handle `then` for a `Promise`
   * @param {Function} rejected The function to handle `reject` for a `Promise`
   * @param {Object} options The options for the interceptor, synchronous and runWhen
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
const Se = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1,
  legacyInterceptorReqResOrdering: !0
}, on = typeof URLSearchParams < "u" ? URLSearchParams : ge, an = typeof FormData < "u" ? FormData : null, cn = typeof Blob < "u" ? Blob : null, ln = {
  isBrowser: !0,
  classes: {
    URLSearchParams: on,
    FormData: an,
    Blob: cn
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, Oe = typeof window < "u" && typeof document < "u", we = typeof navigator == "object" && navigator || void 0, un = Oe && (!we || ["ReactNative", "NativeScript", "NS"].indexOf(we.product) < 0), fn = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", dn = Oe && window.location.href || "http://localhost", pn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: Oe,
  hasStandardBrowserEnv: un,
  hasStandardBrowserWebWorkerEnv: fn,
  navigator: we,
  origin: dn
}, Symbol.toStringTag, { value: "Module" })), S = {
  ...pn,
  ...ln
};
function hn(e, t) {
  return le(e, new S.classes.URLSearchParams(), {
    visitor: function(n, r, s, i) {
      return S.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function mn(e) {
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
function ot(e) {
  function t(n, r, s, i) {
    let o = n[i++];
    if (o === "__proto__") return !0;
    const c = Number.isFinite(+o), f = i >= n.length;
    return o = !o && a.isArray(s) ? s.length : o, f ? (a.hasOwnProp(s, o) ? s[o] = [s[o], r] : s[o] = r, !c) : ((!s[o] || !a.isObject(s[o])) && (s[o] = []), t(n, r, s[o], i) && a.isArray(s[o]) && (s[o] = bn(s[o])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(mn(r), s, n, 0);
    }), n;
  }
  return null;
}
function yn(e, t, n) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (r) {
      if (r.name !== "SyntaxError")
        throw r;
    }
  return (n || JSON.stringify)(e);
}
const G = {
  transitional: Se,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [function(t, n) {
    const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, i = a.isObject(t);
    if (i && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
      return s ? JSON.stringify(ot(t)) : t;
    if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
      return t;
    if (a.isArrayBufferView(t))
      return t.buffer;
    if (a.isURLSearchParams(t))
      return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
    let c;
    if (i) {
      if (r.indexOf("application/x-www-form-urlencoded") > -1)
        return hn(t, this.formSerializer).toString();
      if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
        const f = this.env && this.env.FormData;
        return le(
          c ? { "files[]": t } : t,
          f && new f(),
          this.formSerializer
        );
      }
    }
    return i || s ? (n.setContentType("application/json", !1), yn(t)) : t;
  }],
  transformResponse: [function(t) {
    const n = this.transitional || G.transitional, r = n && n.forcedJSONParsing, s = this.responseType === "json";
    if (a.isResponse(t) || a.isReadableStream(t))
      return t;
    if (t && a.isString(t) && (r && !this.responseType || s)) {
      const o = !(n && n.silentJSONParsing) && s;
      try {
        return JSON.parse(t, this.parseReviver);
      } catch (c) {
        if (o)
          throw c.name === "SyntaxError" ? b.from(c, b.ERR_BAD_RESPONSE, this, null, this.response) : c;
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
    FormData: S.classes.FormData,
    Blob: S.classes.Blob
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
  G.headers[e] = {};
});
const wn = a.toObjectSet([
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
]), En = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(o) {
    s = o.indexOf(":"), n = o.substring(0, s).trim().toLowerCase(), r = o.substring(s + 1).trim(), !(!n || t[n] && wn[n]) && (n === "set-cookie" ? t[n] ? t[n].push(r) : t[n] = [r] : t[n] = t[n] ? t[n] + ", " + r : r);
  }), t;
}, Be = Symbol("internals");
function V(e) {
  return e && String(e).trim().toLowerCase();
}
function re(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(re) : String(e);
}
function Rn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const gn = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
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
function Sn(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function On(e, t) {
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
let C = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, n, r) {
    const s = this;
    function i(c, f, u) {
      const l = V(f);
      if (!l)
        throw new Error("header name must be a non-empty string");
      const h = a.findKey(s, l);
      (!h || s[h] === void 0 || u === !0 || u === void 0 && s[h] !== !1) && (s[h || f] = re(c));
    }
    const o = (c, f) => a.forEach(c, (u, l) => i(u, l, f));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      o(t, n);
    else if (a.isString(t) && (t = t.trim()) && !gn(t))
      o(En(t), n);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, f, u;
      for (const l of t) {
        if (!a.isArray(l))
          throw TypeError("Object iterator must return a key-value pair");
        c[u = l[0]] = (f = c[u]) ? a.isArray(f) ? [...f, l[1]] : [f, l[1]] : l[1];
      }
      o(c, n);
    } else
      t != null && i(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = V(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return Rn(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = V(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || pe(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function i(o) {
      if (o = V(o), o) {
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
      const c = t ? Sn(i) : String(i).trim();
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
    const r = (this[Be] = this[Be] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function i(o) {
      const c = V(o);
      r[c] || (On(s, o), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(i) : i(t), this;
  }
};
C.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
a.reduceDescriptors(C.prototype, ({ value: e }, t) => {
  let n = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(r) {
      this[n] = r;
    }
  };
});
a.freezeMethods(C);
function he(e, t) {
  const n = this || G, r = t || n, s = C.from(r.headers);
  let i = r.data;
  return a.forEach(e, function(c) {
    i = c.call(n, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function it(e) {
  return !!(e && e.__CANCEL__);
}
let Q = class extends b {
  /**
   * A `CanceledError` is an object that is thrown when an operation is canceled.
   *
   * @param {string=} message The message.
   * @param {Object=} config The config.
   * @param {Object=} request The request.
   *
   * @returns {CanceledError} The created error.
   */
  constructor(t, n, r) {
    super(t ?? "canceled", b.ERR_CANCELED, n, r), this.name = "CanceledError", this.__CANCEL__ = !0;
  }
};
function at(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(new b(
    "Request failed with status code " + n.status,
    [b.ERR_BAD_REQUEST, b.ERR_BAD_RESPONSE][Math.floor(n.status / 100) - 4],
    n.config,
    n.request,
    n
  ));
}
function Tn(e) {
  const t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function An(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, i = 0, o;
  return t = t !== void 0 ? t : 1e3, function(f) {
    const u = Date.now(), l = r[i];
    o || (o = u), n[s] = f, r[s] = u;
    let h = i, y = 0;
    for (; h !== s; )
      y += n[h++], h = h % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), u - o < t)
      return;
    const g = l && u - l;
    return g ? Math.round(y * 1e3 / g) : void 0;
  };
}
function Cn(e, t) {
  let n = 0, r = 1e3 / t, s, i;
  const o = (u, l = Date.now()) => {
    n = l, s = null, i && (clearTimeout(i), i = null), e(...u);
  };
  return [(...u) => {
    const l = Date.now(), h = l - n;
    h >= r ? o(u, l) : (s = u, i || (i = setTimeout(() => {
      i = null, o(s);
    }, r - h)));
  }, () => s && o(s)];
}
const oe = (e, t, n = 3) => {
  let r = 0;
  const s = An(50, 250);
  return Cn((i) => {
    const o = i.loaded, c = i.lengthComputable ? i.total : void 0, f = o - r, u = s(f), l = o <= c;
    r = o;
    const h = {
      loaded: o,
      total: c,
      progress: c ? o / c : void 0,
      bytes: f,
      rate: u || void 0,
      estimated: u && c && l ? (c - o) / u : void 0,
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
}, je = (e) => (...t) => a.asap(() => e(...t)), xn = S.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, S.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(S.origin),
  S.navigator && /(msie|trident)/i.test(S.navigator.userAgent)
) : () => !0, _n = S.hasStandardBrowserEnv ? (
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
function Nn(e) {
  return typeof e != "string" ? !1 : /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function Pn(e, t) {
  return t ? e.replace(/\/?\/$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function ct(e, t, n) {
  let r = !Nn(t);
  return e && (r || n == !1) ? Pn(e, t) : t;
}
const qe = (e) => e instanceof C ? { ...e } : e;
function H(e, t) {
  t = t || {};
  const n = {};
  function r(u, l, h, y) {
    return a.isPlainObject(u) && a.isPlainObject(l) ? a.merge.call({ caseless: y }, u, l) : a.isPlainObject(l) ? a.merge({}, l) : a.isArray(l) ? l.slice() : l;
  }
  function s(u, l, h, y) {
    if (a.isUndefined(l)) {
      if (!a.isUndefined(u))
        return r(void 0, u, h, y);
    } else return r(u, l, h, y);
  }
  function i(u, l) {
    if (!a.isUndefined(l))
      return r(void 0, l);
  }
  function o(u, l) {
    if (a.isUndefined(l)) {
      if (!a.isUndefined(u))
        return r(void 0, u);
    } else return r(void 0, l);
  }
  function c(u, l, h) {
    if (h in t)
      return r(u, l);
    if (h in e)
      return r(void 0, u);
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
    headers: (u, l, h) => s(qe(u), qe(l), h, !0)
  };
  return a.forEach(
    Object.keys({ ...e, ...t }),
    function(l) {
      if (l === "__proto__" || l === "constructor" || l === "prototype")
        return;
      const h = a.hasOwnProp(f, l) ? f[l] : s, y = h(e[l], t[l], l);
      a.isUndefined(y) && h !== c || (n[l] = y);
    }
  ), n;
}
const lt = (e) => {
  const t = H({}, e);
  let { data: n, withXSRFToken: r, xsrfHeaderName: s, xsrfCookieName: i, headers: o, auth: c } = t;
  if (t.headers = o = C.from(o), t.url = st(ct(t.baseURL, t.url, t.allowAbsoluteUrls), e.params, e.paramsSerializer), c && o.set(
    "Authorization",
    "Basic " + btoa((c.username || "") + ":" + (c.password ? unescape(encodeURIComponent(c.password)) : ""))
  ), a.isFormData(n)) {
    if (S.hasStandardBrowserEnv || S.hasStandardBrowserWebWorkerEnv)
      o.setContentType(void 0);
    else if (a.isFunction(n.getHeaders)) {
      const f = n.getHeaders(), u = ["content-type", "content-length"];
      Object.entries(f).forEach(([l, h]) => {
        u.includes(l.toLowerCase()) && o.set(l, h);
      });
    }
  }
  if (S.hasStandardBrowserEnv && (r && a.isFunction(r) && (r = r(t)), r || r !== !1 && xn(t.url))) {
    const f = s && i && _n.read(i);
    f && o.set(s, f);
  }
  return t;
}, Dn = typeof XMLHttpRequest < "u", Fn = Dn && function(e) {
  return new Promise(function(n, r) {
    const s = lt(e);
    let i = s.data;
    const o = C.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: f, onDownloadProgress: u } = s, l, h, y, g, d;
    function m() {
      g && g(), d && d(), s.cancelToken && s.cancelToken.unsubscribe(l), s.signal && s.signal.removeEventListener("abort", l);
    }
    let p = new XMLHttpRequest();
    p.open(s.method.toUpperCase(), s.url, !0), p.timeout = s.timeout;
    function E() {
      if (!p)
        return;
      const R = C.from(
        "getAllResponseHeaders" in p && p.getAllResponseHeaders()
      ), D = {
        data: !c || c === "text" || c === "json" ? p.responseText : p.response,
        status: p.status,
        statusText: p.statusText,
        headers: R,
        config: e,
        request: p
      };
      at(function(_) {
        n(_), m();
      }, function(_) {
        r(_), m();
      }, D), p = null;
    }
    "onloadend" in p ? p.onloadend = E : p.onreadystatechange = function() {
      !p || p.readyState !== 4 || p.status === 0 && !(p.responseURL && p.responseURL.indexOf("file:") === 0) || setTimeout(E);
    }, p.onabort = function() {
      p && (r(new b("Request aborted", b.ECONNABORTED, e, p)), p = null);
    }, p.onerror = function(O) {
      const D = O && O.message ? O.message : "Network Error", L = new b(D, b.ERR_NETWORK, e, p);
      L.event = O || null, r(L), p = null;
    }, p.ontimeout = function() {
      let O = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const D = s.transitional || Se;
      s.timeoutErrorMessage && (O = s.timeoutErrorMessage), r(new b(
        O,
        D.clarifyTimeoutError ? b.ETIMEDOUT : b.ECONNABORTED,
        e,
        p
      )), p = null;
    }, i === void 0 && o.setContentType(null), "setRequestHeader" in p && a.forEach(o.toJSON(), function(O, D) {
      p.setRequestHeader(D, O);
    }), a.isUndefined(s.withCredentials) || (p.withCredentials = !!s.withCredentials), c && c !== "json" && (p.responseType = s.responseType), u && ([y, d] = oe(u, !0), p.addEventListener("progress", y)), f && p.upload && ([h, g] = oe(f), p.upload.addEventListener("progress", h), p.upload.addEventListener("loadend", g)), (s.cancelToken || s.signal) && (l = (R) => {
      p && (r(!R || R.type ? new Q(null, e, p) : R), p.abort(), p = null);
    }, s.cancelToken && s.cancelToken.subscribe(l), s.signal && (s.signal.aborted ? l() : s.signal.addEventListener("abort", l)));
    const x = Tn(s.url);
    if (x && S.protocols.indexOf(x) === -1) {
      r(new b("Unsupported protocol " + x + ":", b.ERR_BAD_REQUEST, e));
      return;
    }
    p.send(i || null);
  });
}, Un = (e, t) => {
  const { length: n } = e = e ? e.filter(Boolean) : [];
  if (t || n) {
    let r = new AbortController(), s;
    const i = function(u) {
      if (!s) {
        s = !0, c();
        const l = u instanceof Error ? u : this.reason;
        r.abort(l instanceof b ? l : new Q(l instanceof Error ? l.message : l));
      }
    };
    let o = t && setTimeout(() => {
      o = null, i(new b(`timeout of ${t}ms exceeded`, b.ETIMEDOUT));
    }, t);
    const c = () => {
      e && (o && clearTimeout(o), o = null, e.forEach((u) => {
        u.unsubscribe ? u.unsubscribe(i) : u.removeEventListener("abort", i);
      }), e = null);
    };
    e.forEach((u) => u.addEventListener("abort", i));
    const { signal: f } = r;
    return f.unsubscribe = () => a.asap(c), f;
  }
}, kn = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, Bn = async function* (e, t) {
  for await (const n of Ln(e))
    yield* kn(n, t);
}, Ln = async function* (e) {
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
}, Ie = (e, t, n, r) => {
  const s = Bn(e, t);
  let i = 0, o, c = (f) => {
    o || (o = !0, r && r(f));
  };
  return new ReadableStream({
    async pull(f) {
      try {
        const { done: u, value: l } = await s.next();
        if (u) {
          c(), f.close();
          return;
        }
        let h = l.byteLength;
        if (n) {
          let y = i += h;
          n(y);
        }
        f.enqueue(new Uint8Array(l));
      } catch (u) {
        throw c(u), u;
      }
    },
    cancel(f) {
      return c(f), s.return();
    }
  }, {
    highWaterMark: 2
  });
}, He = 64 * 1024, { isFunction: te } = a, jn = (({ Request: e, Response: t }) => ({
  Request: e,
  Response: t
}))(a.global), {
  ReadableStream: Me,
  TextEncoder: $e
} = a.global, ve = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, qn = (e) => {
  e = a.merge.call({
    skipUndefined: !0
  }, jn, e);
  const { fetch: t, Request: n, Response: r } = e, s = t ? te(t) : typeof fetch == "function", i = te(n), o = te(r);
  if (!s)
    return !1;
  const c = s && te(Me), f = s && (typeof $e == "function" ? /* @__PURE__ */ ((d) => (m) => d.encode(m))(new $e()) : async (d) => new Uint8Array(await new n(d).arrayBuffer())), u = i && c && ve(() => {
    let d = !1;
    const m = new n(S.origin, {
      body: new Me(),
      method: "POST",
      get duplex() {
        return d = !0, "half";
      }
    }).headers.has("Content-Type");
    return d && !m;
  }), l = o && c && ve(() => a.isReadableStream(new r("").body)), h = {
    stream: l && ((d) => d.body)
  };
  s && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((d) => {
    !h[d] && (h[d] = (m, p) => {
      let E = m && m[d];
      if (E)
        return E.call(m);
      throw new b(`Response type '${d}' is not supported`, b.ERR_NOT_SUPPORT, p);
    });
  });
  const y = async (d) => {
    if (d == null)
      return 0;
    if (a.isBlob(d))
      return d.size;
    if (a.isSpecCompliantForm(d))
      return (await new n(S.origin, {
        method: "POST",
        body: d
      }).arrayBuffer()).byteLength;
    if (a.isArrayBufferView(d) || a.isArrayBuffer(d))
      return d.byteLength;
    if (a.isURLSearchParams(d) && (d = d + ""), a.isString(d))
      return (await f(d)).byteLength;
  }, g = async (d, m) => {
    const p = a.toFiniteNumber(d.getContentLength());
    return p ?? y(m);
  };
  return async (d) => {
    let {
      url: m,
      method: p,
      data: E,
      signal: x,
      cancelToken: R,
      timeout: O,
      onDownloadProgress: D,
      onUploadProgress: L,
      responseType: _,
      headers: fe,
      withCredentials: Y = "same-origin",
      fetchOptions: Ae
    } = lt(d), Ce = t || fetch;
    _ = _ ? (_ + "").toLowerCase() : "text";
    let Z = Un([x, R && R.toAbortSignal()], O), J = null;
    const j = Z && Z.unsubscribe && (() => {
      Z.unsubscribe();
    });
    let xe;
    try {
      if (L && u && p !== "get" && p !== "head" && (xe = await g(fe, E)) !== 0) {
        let k = new n(m, {
          method: "POST",
          body: E,
          duplex: "half"
        }), $;
        if (a.isFormData(E) && ($ = k.headers.get("content-type")) && fe.setContentType($), k.body) {
          const [de, ee] = Le(
            xe,
            oe(je(L))
          );
          E = Ie(k.body, He, de, ee);
        }
      }
      a.isString(Y) || (Y = Y ? "include" : "omit");
      const T = i && "credentials" in n.prototype, _e = {
        ...Ae,
        signal: Z,
        method: p.toUpperCase(),
        headers: fe.normalize().toJSON(),
        body: E,
        duplex: "half",
        credentials: T ? Y : void 0
      };
      J = i && new n(m, _e);
      let U = await (i ? Ce(J, Ae) : Ce(m, _e));
      const Ne = l && (_ === "stream" || _ === "response");
      if (l && (D || Ne && j)) {
        const k = {};
        ["status", "statusText", "headers"].forEach((Pe) => {
          k[Pe] = U[Pe];
        });
        const $ = a.toFiniteNumber(U.headers.get("content-length")), [de, ee] = D && Le(
          $,
          oe(je(D), !0)
        ) || [];
        U = new r(
          Ie(U.body, He, de, () => {
            ee && ee(), j && j();
          }),
          k
        );
      }
      _ = _ || "text";
      let mt = await h[a.findKey(h, _) || "text"](U, d);
      return !Ne && j && j(), await new Promise((k, $) => {
        at(k, $, {
          data: mt,
          headers: C.from(U.headers),
          status: U.status,
          statusText: U.statusText,
          config: d,
          request: J
        });
      });
    } catch (T) {
      throw j && j(), T && T.name === "TypeError" && /Load failed|fetch/i.test(T.message) ? Object.assign(
        new b("Network Error", b.ERR_NETWORK, d, J, T && T.response),
        {
          cause: T.cause || T
        }
      ) : b.from(T, T && T.code, d, J, T && T.response);
    }
  };
}, In = /* @__PURE__ */ new Map(), ut = (e) => {
  let t = e && e.env || {};
  const { fetch: n, Request: r, Response: s } = t, i = [
    r,
    s,
    n
  ];
  let o = i.length, c = o, f, u, l = In;
  for (; c--; )
    f = i[c], u = l.get(f), u === void 0 && l.set(f, u = c ? /* @__PURE__ */ new Map() : qn(t)), l = u;
  return u;
};
ut();
const Te = {
  http: tn,
  xhr: Fn,
  fetch: {
    get: ut
  }
};
a.forEach(Te, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { value: t });
  }
});
const ze = (e) => `- ${e}`, Hn = (e) => a.isFunction(e) || e === null || e === !1;
function Mn(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: n } = e;
  let r, s;
  const i = {};
  for (let o = 0; o < n; o++) {
    r = e[o];
    let c;
    if (s = r, !Hn(r) && (s = Te[(c = String(r)).toLowerCase()], s === void 0))
      throw new b(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    i[c || "#" + o] = s;
  }
  if (!s) {
    const o = Object.entries(i).map(
      ([f, u]) => `adapter ${f} ` + (u === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = n ? o.length > 1 ? `since :
` + o.map(ze).join(`
`) : " " + ze(o[0]) : "as no adapter specified";
    throw new b(
      "There is no suitable adapter to dispatch the request " + c,
      "ERR_NOT_SUPPORT"
    );
  }
  return s;
}
const ft = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: Mn,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: Te
};
function me(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new Q(null, e);
}
function Je(e) {
  return me(e), e.headers = C.from(e.headers), e.data = he.call(
    e,
    e.transformRequest
  ), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), ft.getAdapter(e.adapter || G.adapter, e)(e).then(function(r) {
    return me(e), r.data = he.call(
      e,
      e.transformResponse,
      r
    ), r.headers = C.from(r.headers), r;
  }, function(r) {
    return it(r) || (me(e), r && r.response && (r.response.data = he.call(
      e,
      e.transformResponse,
      r.response
    ), r.response.headers = C.from(r.response.headers))), Promise.reject(r);
  });
}
const dt = "1.13.5", ue = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  ue[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Ve = {};
ue.transitional = function(t, n, r) {
  function s(i, o) {
    return "[Axios v" + dt + "] Transitional option '" + i + "'" + o + (r ? ". " + r : "");
  }
  return (i, o, c) => {
    if (t === !1)
      throw new b(
        s(o, " has been removed" + (n ? " in " + n : "")),
        b.ERR_DEPRECATED
      );
    return n && !Ve[o] && (Ve[o] = !0, console.warn(
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
function $n(e, t, n) {
  if (typeof e != "object")
    throw new b("options must be an object", b.ERR_BAD_OPTION_VALUE);
  const r = Object.keys(e);
  let s = r.length;
  for (; s-- > 0; ) {
    const i = r[s], o = t[i];
    if (o) {
      const c = e[i], f = c === void 0 || o(c, i, e);
      if (f !== !0)
        throw new b("option " + i + " must be " + f, b.ERR_BAD_OPTION_VALUE);
      continue;
    }
    if (n !== !0)
      throw new b("Unknown option " + i, b.ERR_BAD_OPTION);
  }
}
const se = {
  assertOptions: $n,
  validators: ue
}, N = se.validators;
let I = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new ke(),
      response: new ke()
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
      silentJSONParsing: N.transitional(N.boolean),
      forcedJSONParsing: N.transitional(N.boolean),
      clarifyTimeoutError: N.transitional(N.boolean),
      legacyInterceptorReqResOrdering: N.transitional(N.boolean)
    }, !1), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : se.assertOptions(s, {
      encode: N.function,
      serialize: N.function
    }, !0)), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), se.assertOptions(n, {
      baseUrl: N.spelling("baseURL"),
      withXsrfToken: N.spelling("withXSRFToken")
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
    ), n.headers = C.concat(o, i);
    const c = [];
    let f = !0;
    this.interceptors.request.forEach(function(m) {
      if (typeof m.runWhen == "function" && m.runWhen(n) === !1)
        return;
      f = f && m.synchronous;
      const p = n.transitional || Se;
      p && p.legacyInterceptorReqResOrdering ? c.unshift(m.fulfilled, m.rejected) : c.push(m.fulfilled, m.rejected);
    });
    const u = [];
    this.interceptors.response.forEach(function(m) {
      u.push(m.fulfilled, m.rejected);
    });
    let l, h = 0, y;
    if (!f) {
      const d = [Je.bind(this), void 0];
      for (d.unshift(...c), d.push(...u), y = d.length, l = Promise.resolve(n); h < y; )
        l = l.then(d[h++], d[h++]);
      return l;
    }
    y = c.length;
    let g = n;
    for (; h < y; ) {
      const d = c[h++], m = c[h++];
      try {
        g = d(g);
      } catch (p) {
        m.call(this, p);
        break;
      }
    }
    try {
      l = Je.call(this, g);
    } catch (d) {
      return Promise.reject(d);
    }
    for (h = 0, y = u.length; h < y; )
      l = l.then(u[h++], u[h++]);
    return l;
  }
  getUri(t) {
    t = H(this.defaults, t);
    const n = ct(t.baseURL, t.url, t.allowAbsoluteUrls);
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
let vn = class pt {
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
      r.reason || (r.reason = new Q(i, o, c), n(r.reason));
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
      token: new pt(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function zn(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function Jn(e) {
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
function ht(e) {
  const t = new I(e), n = We(I.prototype.request, t);
  return a.extend(n, I.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return ht(H(e, s));
  }, n;
}
const w = ht(G);
w.Axios = I;
w.CanceledError = Q;
w.CancelToken = vn;
w.isCancel = it;
w.VERSION = dt;
w.toFormData = le;
w.AxiosError = b;
w.Cancel = w.CanceledError;
w.all = function(t) {
  return Promise.all(t);
};
w.spread = zn;
w.isAxiosError = Jn;
w.mergeConfig = H;
w.AxiosHeaders = C;
w.formToJSON = (e) => ot(a.isHTMLForm(e) ? new FormData(e) : e);
w.getAdapter = ft.getAdapter;
w.HttpStatusCode = Ee;
w.default = w;
const {
  Axios: Gn,
  AxiosError: Qn,
  CanceledError: Yn,
  isCancel: Zn,
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
  timeout: 18e4,
  // Add a timeout of 3 minutes
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
  const n = B(e), r = P(null), s = P(null), i = P(!0), o = M.get(n, {
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
  const r = B(e), s = P(null), i = P(null), o = P(!0), c = M.post(r, B(t), {
    headers: n
  }).then((f) => (i.value = f.data, o.value = !1, { loading: o, backendError: s, responseData: i })).catch((f) => (s.value = f, o.value = !1, { loading: o, backendError: s, responseData: i }));
  return {
    loading: o,
    backendError: s,
    responseData: i,
    then: (f, u) => c.then(f, u)
  };
}
function mr(e, t, n = {}) {
  const r = B(e), s = P(null), i = B(t), o = P(!0), c = M.put(r, i, {
    headers: n
  }).then((f) => (console.log(f.statusText), o.value = !1, { loading: o, backendError: s })).catch((f) => (console.log(f), s.value = f, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (f, u) => c.then(f, u)
  };
}
function br(e, t, n = {}) {
  const r = B(e), s = P(null), i = B(t), o = P(!0), c = M.patch(r, i, {
    headers: n
  }).then((f) => (o.value = !1, { loading: o, backendError: s })).catch((f) => (console.log(f), s.value = f, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (f, u) => c.then(f, u)
  };
}
function yr(e, t = {}) {
  const n = B(e), r = P(null), s = P(!0), i = M.delete(n, {
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
  yr as useDeleteBackendData,
  pr as useGetBackendData,
  br as usePatchBackendData,
  hr as usePostBackendData,
  mr as usePutBackendData
};
