import { toValue as B, ref as _ } from "vue";
function Xe(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: Et } = Object.prototype, { getPrototypeOf: ge } = Object, { iterator: ie, toStringTag: Ge } = Symbol, ae = /* @__PURE__ */ ((e) => (t) => {
  const n = Et.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), k = (e) => (e = e.toLowerCase(), (t) => ae(t) === e), ce = (e) => (t) => typeof t === e, { isArray: v } = Array, z = ce("undefined");
function W(e) {
  return e !== null && !z(e) && e.constructor !== null && !z(e.constructor) && A(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const Qe = k("ArrayBuffer");
function Rt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && Qe(e.buffer), t;
}
const gt = ce("string"), A = ce("function"), Ye = ce("number"), K = (e) => e !== null && typeof e == "object", St = (e) => e === !0 || e === !1, ne = (e) => {
  if (ae(e) !== "object")
    return !1;
  const t = ge(e);
  return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(Ge in e) && !(ie in e);
}, Ot = (e) => {
  if (!K(e) || W(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, Tt = k("Date"), At = k("File"), Ct = (e) => !!(e && typeof e.uri < "u"), xt = (e) => e && typeof e.getParts < "u", Nt = k("Blob"), Pt = k("FileList"), _t = (e) => K(e) && A(e.pipe);
function Ft() {
  return typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
}
const ke = Ft(), Ue = typeof ke.FormData < "u" ? ke.FormData : void 0, kt = (e) => {
  let t;
  return e && (Ue && e instanceof Ue || A(e.append) && ((t = ae(e)) === "formdata" || // detect form-data instance
  t === "object" && A(e.toString) && e.toString() === "[object FormData]"));
}, Ut = k("URLSearchParams"), [Dt, Bt, Lt, jt] = [
  "ReadableStream",
  "Request",
  "Response",
  "Headers"
].map(k), It = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function X(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), v(e))
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
function Ze(e, t) {
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
const I = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, et = (e) => !z(e) && e !== I;
function ye() {
  const { caseless: e, skipUndefined: t } = et(this) && this || {}, n = {}, r = (s, i) => {
    if (i === "__proto__" || i === "constructor" || i === "prototype")
      return;
    const o = e && Ze(n, i) || i;
    ne(n[o]) && ne(s) ? n[o] = ye(n[o], s) : ne(s) ? n[o] = ye({}, s) : v(s) ? n[o] = s.slice() : (!t || !z(s)) && (n[o] = s);
  };
  for (let s = 0, i = arguments.length; s < i; s++)
    arguments[s] && X(arguments[s], r);
  return n;
}
const qt = (e, t, n, { allOwnKeys: r } = {}) => (X(
  t,
  (s, i) => {
    n && A(s) ? Object.defineProperty(e, i, {
      value: Xe(s, n),
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
), e), Ht = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Mt = (e, t, n, r) => {
  e.prototype = Object.create(t.prototype, r), Object.defineProperty(e.prototype, "constructor", {
    value: e,
    writable: !0,
    enumerable: !1,
    configurable: !0
  }), Object.defineProperty(e, "super", {
    value: t.prototype
  }), n && Object.assign(e.prototype, n);
}, $t = (e, t, n, r) => {
  let s, i, o;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0; )
      o = s[i], (!r || r(o, e, t)) && !c[o] && (t[o] = e[o], c[o] = !0);
    e = n !== !1 && ge(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, zt = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, vt = (e) => {
  if (!e) return null;
  if (v(e)) return e;
  let t = e.length;
  if (!Ye(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, Vt = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && ge(Uint8Array)), Jt = (e, t) => {
  const r = (e && e[ie]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const i = s.value;
    t.call(e, i[0], i[1]);
  }
}, Wt = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, Kt = k("HTMLFormElement"), Xt = (e) => e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function(n, r, s) {
  return r.toUpperCase() + s;
}), De = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), Gt = k("RegExp"), tt = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  X(n, (s, i) => {
    let o;
    (o = t(s, i, e)) !== !1 && (r[i] = o || s);
  }), Object.defineProperties(e, r);
}, Qt = (e) => {
  tt(e, (t, n) => {
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
}, Yt = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((i) => {
      n[i] = !0;
    });
  };
  return v(e) ? r(e) : r(String(e).split(t)), n;
}, Zt = () => {
}, en = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function tn(e) {
  return !!(e && A(e.append) && e[Ge] === "FormData" && e[ie]);
}
const nn = (e) => {
  const t = new Array(10), n = (r, s) => {
    if (K(r)) {
      if (t.indexOf(r) >= 0)
        return;
      if (W(r))
        return r;
      if (!("toJSON" in r)) {
        t[s] = r;
        const i = v(r) ? [] : {};
        return X(r, (o, c) => {
          const u = n(o, s + 1);
          !z(u) && (i[c] = u);
        }), t[s] = void 0, i;
      }
    }
    return r;
  };
  return n(e, 0);
}, rn = k("AsyncFunction"), sn = (e) => e && (K(e) || A(e)) && A(e.then) && A(e.catch), nt = ((e, t) => e ? setImmediate : t ? ((n, r) => (I.addEventListener(
  "message",
  ({ source: s, data: i }) => {
    s === I && i === n && r.length && r.shift()();
  },
  !1
), (s) => {
  r.push(s), I.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(typeof setImmediate == "function", A(I.postMessage)), on = typeof queueMicrotask < "u" ? queueMicrotask.bind(I) : typeof process < "u" && process.nextTick || nt, an = (e) => e != null && A(e[ie]), a = {
  isArray: v,
  isArrayBuffer: Qe,
  isBuffer: W,
  isFormData: kt,
  isArrayBufferView: Rt,
  isString: gt,
  isNumber: Ye,
  isBoolean: St,
  isObject: K,
  isPlainObject: ne,
  isEmptyObject: Ot,
  isReadableStream: Dt,
  isRequest: Bt,
  isResponse: Lt,
  isHeaders: jt,
  isUndefined: z,
  isDate: Tt,
  isFile: At,
  isReactNativeBlob: Ct,
  isReactNative: xt,
  isBlob: Nt,
  isRegExp: Gt,
  isFunction: A,
  isStream: _t,
  isURLSearchParams: Ut,
  isTypedArray: Vt,
  isFileList: Pt,
  forEach: X,
  merge: ye,
  extend: qt,
  trim: It,
  stripBOM: Ht,
  inherits: Mt,
  toFlatObject: $t,
  kindOf: ae,
  kindOfTest: k,
  endsWith: zt,
  toArray: vt,
  forEachEntry: Jt,
  matchAll: Wt,
  isHTMLForm: Kt,
  hasOwnProperty: De,
  hasOwnProp: De,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors: tt,
  freezeMethods: Qt,
  toObjectSet: Yt,
  toCamelCase: Xt,
  noop: Zt,
  toFiniteNumber: en,
  findKey: Ze,
  global: I,
  isContextDefined: et,
  isSpecCompliantForm: tn,
  toJSONObject: nn,
  isAsyncFn: rn,
  isThenable: sn,
  setImmediate: nt,
  asap: on,
  isIterable: an
};
let b = class rt extends Error {
  static from(t, n, r, s, i, o) {
    const c = new rt(t.message, n || t.code, r, s, i);
    return c.cause = t, c.name = t.name, t.status != null && c.status == null && (c.status = t.status), o && Object.assign(c, o), c;
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
    super(t), Object.defineProperty(this, "message", {
      value: t,
      enumerable: !0,
      writable: !0,
      configurable: !0
    }), this.name = "AxiosError", this.isAxiosError = !0, n && (this.code = n), r && (this.config = r), s && (this.request = s), i && (this.response = i, this.status = i.status);
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
const cn = null;
function we(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function st(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function pe(e, t, n) {
  return e ? e.concat(t).map(function(s, i) {
    return s = st(s), !n && i ? "[" + s + "]" : s;
  }).join(n ? "." : "") : t;
}
function ln(e) {
  return a.isArray(e) && !e.some(we);
}
const un = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function le(e, t, n) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData(), n = a.toFlatObject(
    n,
    {
      metaTokens: !0,
      dots: !1,
      indexes: !1
    },
    !1,
    function(m, p) {
      return !a.isUndefined(p[m]);
    }
  );
  const r = n.metaTokens, s = n.visitor || l, i = n.dots, o = n.indexes, u = (n.Blob || typeof Blob < "u" && Blob) && a.isSpecCompliantForm(t);
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function f(d) {
    if (d === null) return "";
    if (a.isDate(d))
      return d.toISOString();
    if (a.isBoolean(d))
      return d.toString();
    if (!u && a.isBlob(d))
      throw new b("Blob is not supported. Use a Buffer instead.");
    return a.isArrayBuffer(d) || a.isTypedArray(d) ? u && typeof Blob == "function" ? new Blob([d]) : Buffer.from(d) : d;
  }
  function l(d, m, p) {
    let E = d;
    if (a.isReactNative(t) && a.isReactNativeBlob(d))
      return t.append(pe(p, m, i), f(d)), !1;
    if (d && !p && typeof d == "object") {
      if (a.endsWith(m, "{}"))
        m = r ? m : m.slice(0, -2), d = JSON.stringify(d);
      else if (a.isArray(d) && ln(d) || (a.isFileList(d) || a.endsWith(m, "[]")) && (E = a.toArray(d)))
        return m = st(m), E.forEach(function(R, O) {
          !(a.isUndefined(R) || R === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            o === !0 ? pe([m], O, i) : o === null ? m : m + "[]",
            f(R)
          );
        }), !1;
    }
    return we(d) ? !0 : (t.append(pe(p, m, i), f(d)), !1);
  }
  const h = [], y = Object.assign(un, {
    defaultVisitor: l,
    convertValue: f,
    isVisitable: we
  });
  function g(d, m) {
    if (!a.isUndefined(d)) {
      if (h.indexOf(d) !== -1)
        throw Error("Circular reference detected in " + m.join("."));
      h.push(d), a.forEach(d, function(E, x) {
        (!(a.isUndefined(E) || E === null) && s.call(t, E, a.isString(x) ? x.trim() : x, m, y)) === !0 && g(E, m ? m.concat(x) : [x]);
      }), h.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return g(e), t;
}
function Be(e) {
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
const ot = Se.prototype;
ot.append = function(t, n) {
  this._pairs.push([t, n]);
};
ot.toString = function(t) {
  const n = t ? function(r) {
    return t.call(this, r, Be);
  } : Be;
  return this._pairs.map(function(s) {
    return n(s[0]) + "=" + n(s[1]);
  }, "").join("&");
};
function fn(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function it(e, t, n) {
  if (!t)
    return e;
  const r = n && n.encode || fn, s = a.isFunction(n) ? {
    serialize: n
  } : n, i = s && s.serialize;
  let o;
  if (i ? o = i(t, s) : o = a.isURLSearchParams(t) ? t.toString() : new Se(t, s).toString(r), o) {
    const c = e.indexOf("#");
    c !== -1 && (e = e.slice(0, c)), e += (e.indexOf("?") === -1 ? "?" : "&") + o;
  }
  return e;
}
class Le {
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
const Oe = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1,
  legacyInterceptorReqResOrdering: !0
}, dn = typeof URLSearchParams < "u" ? URLSearchParams : Se, pn = typeof FormData < "u" ? FormData : null, hn = typeof Blob < "u" ? Blob : null, mn = {
  isBrowser: !0,
  classes: {
    URLSearchParams: dn,
    FormData: pn,
    Blob: hn
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, Te = typeof window < "u" && typeof document < "u", Ee = typeof navigator == "object" && navigator || void 0, bn = Te && (!Ee || ["ReactNative", "NativeScript", "NS"].indexOf(Ee.product) < 0), yn = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", wn = Te && window.location.href || "http://localhost", En = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: Te,
  hasStandardBrowserEnv: bn,
  hasStandardBrowserWebWorkerEnv: yn,
  navigator: Ee,
  origin: wn
}, Symbol.toStringTag, { value: "Module" })), S = {
  ...En,
  ...mn
};
function Rn(e, t) {
  return le(e, new S.classes.URLSearchParams(), {
    visitor: function(n, r, s, i) {
      return S.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function gn(e) {
  return a.matchAll(/\w+|\[(\w*)]/g, e).map((t) => t[0] === "[]" ? "" : t[1] || t[0]);
}
function Sn(e) {
  const t = {}, n = Object.keys(e);
  let r;
  const s = n.length;
  let i;
  for (r = 0; r < s; r++)
    i = n[r], t[i] = e[i];
  return t;
}
function at(e) {
  function t(n, r, s, i) {
    let o = n[i++];
    if (o === "__proto__") return !0;
    const c = Number.isFinite(+o), u = i >= n.length;
    return o = !o && a.isArray(s) ? s.length : o, u ? (a.hasOwnProp(s, o) ? s[o] = [s[o], r] : s[o] = r, !c) : ((!s[o] || !a.isObject(s[o])) && (s[o] = []), t(n, r, s[o], i) && a.isArray(s[o]) && (s[o] = Sn(s[o])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(gn(r), s, n, 0);
    }), n;
  }
  return null;
}
function On(e, t, n) {
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
  transitional: Oe,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [
    function(t, n) {
      const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, i = a.isObject(t);
      if (i && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
        return s ? JSON.stringify(at(t)) : t;
      if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
        return t;
      if (a.isArrayBufferView(t))
        return t.buffer;
      if (a.isURLSearchParams(t))
        return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
      let c;
      if (i) {
        if (r.indexOf("application/x-www-form-urlencoded") > -1)
          return Rn(t, this.formSerializer).toString();
        if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
          const u = this.env && this.env.FormData;
          return le(
            c ? { "files[]": t } : t,
            u && new u(),
            this.formSerializer
          );
        }
      }
      return i || s ? (n.setContentType("application/json", !1), On(t)) : t;
    }
  ],
  transformResponse: [
    function(t) {
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
    }
  ],
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
const Tn = a.toObjectSet([
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
]), An = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(o) {
    s = o.indexOf(":"), n = o.substring(0, s).trim().toLowerCase(), r = o.substring(s + 1).trim(), !(!n || t[n] && Tn[n]) && (n === "set-cookie" ? t[n] ? t[n].push(r) : t[n] = [r] : t[n] = t[n] ? t[n] + ", " + r : r);
  }), t;
}, je = Symbol("internals"), Cn = (e) => !/[\r\n]/.test(e);
function ct(e, t) {
  if (!(e === !1 || e == null)) {
    if (a.isArray(e)) {
      e.forEach((n) => ct(n, t));
      return;
    }
    if (!Cn(String(e)))
      throw new Error(`Invalid character in header content ["${t}"]`);
  }
}
function J(e) {
  return e && String(e).trim().toLowerCase();
}
function xn(e) {
  let t = e.length;
  for (; t > 0; ) {
    const n = e.charCodeAt(t - 1);
    if (n !== 10 && n !== 13)
      break;
    t -= 1;
  }
  return t === e.length ? e : e.slice(0, t);
}
function re(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(re) : xn(String(e));
}
function Nn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const Pn = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function he(e, t, n, r, s) {
  if (a.isFunction(r))
    return r.call(this, t, n);
  if (s && (t = n), !!a.isString(t)) {
    if (a.isString(r))
      return t.indexOf(r) !== -1;
    if (a.isRegExp(r))
      return r.test(t);
  }
}
function _n(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function Fn(e, t) {
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
    function i(c, u, f) {
      const l = J(u);
      if (!l)
        throw new Error("header name must be a non-empty string");
      const h = a.findKey(s, l);
      (!h || s[h] === void 0 || f === !0 || f === void 0 && s[h] !== !1) && (ct(c, u), s[h || u] = re(c));
    }
    const o = (c, u) => a.forEach(c, (f, l) => i(f, l, u));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      o(t, n);
    else if (a.isString(t) && (t = t.trim()) && !Pn(t))
      o(An(t), n);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, u, f;
      for (const l of t) {
        if (!a.isArray(l))
          throw TypeError("Object iterator must return a key-value pair");
        c[f = l[0]] = (u = c[f]) ? a.isArray(u) ? [...u, l[1]] : [u, l[1]] : l[1];
      }
      o(c, n);
    } else
      t != null && i(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = J(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return Nn(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = J(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || he(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function i(o) {
      if (o = J(o), o) {
        const c = a.findKey(r, o);
        c && (!n || he(r, r[c], c, n)) && (delete r[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(i) : i(t), s;
  }
  clear(t) {
    const n = Object.keys(this);
    let r = n.length, s = !1;
    for (; r--; ) {
      const i = n[r];
      (!t || he(this, this[i], i, t, !0)) && (delete this[i], s = !0);
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
      const c = t ? _n(i) : String(i).trim();
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
    const r = (this[je] = this[je] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function i(o) {
      const c = J(o);
      r[c] || (Fn(s, o), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(i) : i(t), this;
  }
};
C.accessor([
  "Content-Type",
  "Content-Length",
  "Accept",
  "Accept-Encoding",
  "User-Agent",
  "Authorization"
]);
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
function me(e, t) {
  const n = this || G, r = t || n, s = C.from(r.headers);
  let i = r.data;
  return a.forEach(e, function(c) {
    i = c.call(n, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function lt(e) {
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
function ut(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(
    new b(
      "Request failed with status code " + n.status,
      [b.ERR_BAD_REQUEST, b.ERR_BAD_RESPONSE][Math.floor(n.status / 100) - 4],
      n.config,
      n.request,
      n
    )
  );
}
function kn(e) {
  const t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function Un(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, i = 0, o;
  return t = t !== void 0 ? t : 1e3, function(u) {
    const f = Date.now(), l = r[i];
    o || (o = f), n[s] = u, r[s] = f;
    let h = i, y = 0;
    for (; h !== s; )
      y += n[h++], h = h % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), f - o < t)
      return;
    const g = l && f - l;
    return g ? Math.round(y * 1e3 / g) : void 0;
  };
}
function Dn(e, t) {
  let n = 0, r = 1e3 / t, s, i;
  const o = (f, l = Date.now()) => {
    n = l, s = null, i && (clearTimeout(i), i = null), e(...f);
  };
  return [(...f) => {
    const l = Date.now(), h = l - n;
    h >= r ? o(f, l) : (s = f, i || (i = setTimeout(() => {
      i = null, o(s);
    }, r - h)));
  }, () => s && o(s)];
}
const oe = (e, t, n = 3) => {
  let r = 0;
  const s = Un(50, 250);
  return Dn((i) => {
    const o = i.loaded, c = i.lengthComputable ? i.total : void 0, u = o - r, f = s(u), l = o <= c;
    r = o;
    const h = {
      loaded: o,
      total: c,
      progress: c ? o / c : void 0,
      bytes: u,
      rate: f || void 0,
      estimated: f && c && l ? (c - o) / f : void 0,
      event: i,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(h);
  }, n);
}, Ie = (e, t) => {
  const n = e != null;
  return [
    (r) => t[0]({
      lengthComputable: n,
      total: e,
      loaded: r
    }),
    t[1]
  ];
}, qe = (e) => (...t) => a.asap(() => e(...t)), Bn = S.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, S.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(S.origin),
  S.navigator && /(msie|trident)/i.test(S.navigator.userAgent)
) : () => !0, Ln = S.hasStandardBrowserEnv ? (
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
function jn(e) {
  return typeof e != "string" ? !1 : /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function In(e, t) {
  return t ? e.replace(/\/?\/$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function ft(e, t, n) {
  let r = !jn(t);
  return e && (r || n == !1) ? In(e, t) : t;
}
const He = (e) => e instanceof C ? { ...e } : e;
function H(e, t) {
  t = t || {};
  const n = {};
  function r(f, l, h, y) {
    return a.isPlainObject(f) && a.isPlainObject(l) ? a.merge.call({ caseless: y }, f, l) : a.isPlainObject(l) ? a.merge({}, l) : a.isArray(l) ? l.slice() : l;
  }
  function s(f, l, h, y) {
    if (a.isUndefined(l)) {
      if (!a.isUndefined(f))
        return r(void 0, f, h, y);
    } else return r(f, l, h, y);
  }
  function i(f, l) {
    if (!a.isUndefined(l))
      return r(void 0, l);
  }
  function o(f, l) {
    if (a.isUndefined(l)) {
      if (!a.isUndefined(f))
        return r(void 0, f);
    } else return r(void 0, l);
  }
  function c(f, l, h) {
    if (h in t)
      return r(f, l);
    if (h in e)
      return r(void 0, f);
  }
  const u = {
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
    headers: (f, l, h) => s(He(f), He(l), h, !0)
  };
  return a.forEach(Object.keys({ ...e, ...t }), function(l) {
    if (l === "__proto__" || l === "constructor" || l === "prototype") return;
    const h = a.hasOwnProp(u, l) ? u[l] : s, y = h(e[l], t[l], l);
    a.isUndefined(y) && h !== c || (n[l] = y);
  }), n;
}
const dt = (e) => {
  const t = H({}, e);
  let { data: n, withXSRFToken: r, xsrfHeaderName: s, xsrfCookieName: i, headers: o, auth: c } = t;
  if (t.headers = o = C.from(o), t.url = it(
    ft(t.baseURL, t.url, t.allowAbsoluteUrls),
    e.params,
    e.paramsSerializer
  ), c && o.set(
    "Authorization",
    "Basic " + btoa(
      (c.username || "") + ":" + (c.password ? unescape(encodeURIComponent(c.password)) : "")
    )
  ), a.isFormData(n)) {
    if (S.hasStandardBrowserEnv || S.hasStandardBrowserWebWorkerEnv)
      o.setContentType(void 0);
    else if (a.isFunction(n.getHeaders)) {
      const u = n.getHeaders(), f = ["content-type", "content-length"];
      Object.entries(u).forEach(([l, h]) => {
        f.includes(l.toLowerCase()) && o.set(l, h);
      });
    }
  }
  if (S.hasStandardBrowserEnv && (r && a.isFunction(r) && (r = r(t)), r || r !== !1 && Bn(t.url))) {
    const u = s && i && Ln.read(i);
    u && o.set(s, u);
  }
  return t;
}, qn = typeof XMLHttpRequest < "u", Hn = qn && function(e) {
  return new Promise(function(n, r) {
    const s = dt(e);
    let i = s.data;
    const o = C.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: u, onDownloadProgress: f } = s, l, h, y, g, d;
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
      ), F = {
        data: !c || c === "text" || c === "json" ? p.responseText : p.response,
        status: p.status,
        statusText: p.statusText,
        headers: R,
        config: e,
        request: p
      };
      ut(
        function(N) {
          n(N), m();
        },
        function(N) {
          r(N), m();
        },
        F
      ), p = null;
    }
    "onloadend" in p ? p.onloadend = E : p.onreadystatechange = function() {
      !p || p.readyState !== 4 || p.status === 0 && !(p.responseURL && p.responseURL.indexOf("file:") === 0) || setTimeout(E);
    }, p.onabort = function() {
      p && (r(new b("Request aborted", b.ECONNABORTED, e, p)), p = null);
    }, p.onerror = function(O) {
      const F = O && O.message ? O.message : "Network Error", L = new b(F, b.ERR_NETWORK, e, p);
      L.event = O || null, r(L), p = null;
    }, p.ontimeout = function() {
      let O = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const F = s.transitional || Oe;
      s.timeoutErrorMessage && (O = s.timeoutErrorMessage), r(
        new b(
          O,
          F.clarifyTimeoutError ? b.ETIMEDOUT : b.ECONNABORTED,
          e,
          p
        )
      ), p = null;
    }, i === void 0 && o.setContentType(null), "setRequestHeader" in p && a.forEach(o.toJSON(), function(O, F) {
      p.setRequestHeader(F, O);
    }), a.isUndefined(s.withCredentials) || (p.withCredentials = !!s.withCredentials), c && c !== "json" && (p.responseType = s.responseType), f && ([y, d] = oe(f, !0), p.addEventListener("progress", y)), u && p.upload && ([h, g] = oe(u), p.upload.addEventListener("progress", h), p.upload.addEventListener("loadend", g)), (s.cancelToken || s.signal) && (l = (R) => {
      p && (r(!R || R.type ? new Q(null, e, p) : R), p.abort(), p = null);
    }, s.cancelToken && s.cancelToken.subscribe(l), s.signal && (s.signal.aborted ? l() : s.signal.addEventListener("abort", l)));
    const x = kn(s.url);
    if (x && S.protocols.indexOf(x) === -1) {
      r(
        new b(
          "Unsupported protocol " + x + ":",
          b.ERR_BAD_REQUEST,
          e
        )
      );
      return;
    }
    p.send(i || null);
  });
}, Mn = (e, t) => {
  const { length: n } = e = e ? e.filter(Boolean) : [];
  if (t || n) {
    let r = new AbortController(), s;
    const i = function(f) {
      if (!s) {
        s = !0, c();
        const l = f instanceof Error ? f : this.reason;
        r.abort(
          l instanceof b ? l : new Q(l instanceof Error ? l.message : l)
        );
      }
    };
    let o = t && setTimeout(() => {
      o = null, i(new b(`timeout of ${t}ms exceeded`, b.ETIMEDOUT));
    }, t);
    const c = () => {
      e && (o && clearTimeout(o), o = null, e.forEach((f) => {
        f.unsubscribe ? f.unsubscribe(i) : f.removeEventListener("abort", i);
      }), e = null);
    };
    e.forEach((f) => f.addEventListener("abort", i));
    const { signal: u } = r;
    return u.unsubscribe = () => a.asap(c), u;
  }
}, $n = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, zn = async function* (e, t) {
  for await (const n of vn(e))
    yield* $n(n, t);
}, vn = async function* (e) {
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
}, Me = (e, t, n, r) => {
  const s = zn(e, t);
  let i = 0, o, c = (u) => {
    o || (o = !0, r && r(u));
  };
  return new ReadableStream(
    {
      async pull(u) {
        try {
          const { done: f, value: l } = await s.next();
          if (f) {
            c(), u.close();
            return;
          }
          let h = l.byteLength;
          if (n) {
            let y = i += h;
            n(y);
          }
          u.enqueue(new Uint8Array(l));
        } catch (f) {
          throw c(f), f;
        }
      },
      cancel(u) {
        return c(u), s.return();
      }
    },
    {
      highWaterMark: 2
    }
  );
}, $e = 64 * 1024, { isFunction: te } = a, Vn = (({ Request: e, Response: t }) => ({
  Request: e,
  Response: t
}))(a.global), { ReadableStream: ze, TextEncoder: ve } = a.global, Ve = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, Jn = (e) => {
  e = a.merge.call(
    {
      skipUndefined: !0
    },
    Vn,
    e
  );
  const { fetch: t, Request: n, Response: r } = e, s = t ? te(t) : typeof fetch == "function", i = te(n), o = te(r);
  if (!s)
    return !1;
  const c = s && te(ze), u = s && (typeof ve == "function" ? /* @__PURE__ */ ((d) => (m) => d.encode(m))(new ve()) : async (d) => new Uint8Array(await new n(d).arrayBuffer())), f = i && c && Ve(() => {
    let d = !1;
    const m = new ze(), p = new n(S.origin, {
      body: m,
      method: "POST",
      get duplex() {
        return d = !0, "half";
      }
    }).headers.has("Content-Type");
    return m.cancel(), d && !p;
  }), l = o && c && Ve(() => a.isReadableStream(new r("").body)), h = {
    stream: l && ((d) => d.body)
  };
  s && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((d) => {
    !h[d] && (h[d] = (m, p) => {
      let E = m && m[d];
      if (E)
        return E.call(m);
      throw new b(
        `Response type '${d}' is not supported`,
        b.ERR_NOT_SUPPORT,
        p
      );
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
      return (await u(d)).byteLength;
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
      onDownloadProgress: F,
      onUploadProgress: L,
      responseType: N,
      headers: fe,
      withCredentials: Y = "same-origin",
      fetchOptions: Ce
    } = dt(d), xe = t || fetch;
    N = N ? (N + "").toLowerCase() : "text";
    let Z = Mn(
      [x, R && R.toAbortSignal()],
      O
    ), V = null;
    const j = Z && Z.unsubscribe && (() => {
      Z.unsubscribe();
    });
    let Ne;
    try {
      if (L && f && p !== "get" && p !== "head" && (Ne = await g(fe, E)) !== 0) {
        let D = new n(m, {
          method: "POST",
          body: E,
          duplex: "half"
        }), $;
        if (a.isFormData(E) && ($ = D.headers.get("content-type")) && fe.setContentType($), D.body) {
          const [de, ee] = Ie(
            Ne,
            oe(qe(L))
          );
          E = Me(D.body, $e, de, ee);
        }
      }
      a.isString(Y) || (Y = Y ? "include" : "omit");
      const T = i && "credentials" in n.prototype, Pe = {
        ...Ce,
        signal: Z,
        method: p.toUpperCase(),
        headers: fe.normalize().toJSON(),
        body: E,
        duplex: "half",
        credentials: T ? Y : void 0
      };
      V = i && new n(m, Pe);
      let U = await (i ? xe(V, Ce) : xe(m, Pe));
      const _e = l && (N === "stream" || N === "response");
      if (l && (F || _e && j)) {
        const D = {};
        ["status", "statusText", "headers"].forEach((Fe) => {
          D[Fe] = U[Fe];
        });
        const $ = a.toFiniteNumber(U.headers.get("content-length")), [de, ee] = F && Ie(
          $,
          oe(qe(F), !0)
        ) || [];
        U = new r(
          Me(U.body, $e, de, () => {
            ee && ee(), j && j();
          }),
          D
        );
      }
      N = N || "text";
      let wt = await h[a.findKey(h, N) || "text"](
        U,
        d
      );
      return !_e && j && j(), await new Promise((D, $) => {
        ut(D, $, {
          data: wt,
          headers: C.from(U.headers),
          status: U.status,
          statusText: U.statusText,
          config: d,
          request: V
        });
      });
    } catch (T) {
      throw j && j(), T && T.name === "TypeError" && /Load failed|fetch/i.test(T.message) ? Object.assign(
        new b(
          "Network Error",
          b.ERR_NETWORK,
          d,
          V,
          T && T.response
        ),
        {
          cause: T.cause || T
        }
      ) : b.from(T, T && T.code, d, V, T && T.response);
    }
  };
}, Wn = /* @__PURE__ */ new Map(), pt = (e) => {
  let t = e && e.env || {};
  const { fetch: n, Request: r, Response: s } = t, i = [r, s, n];
  let o = i.length, c = o, u, f, l = Wn;
  for (; c--; )
    u = i[c], f = l.get(u), f === void 0 && l.set(u, f = c ? /* @__PURE__ */ new Map() : Jn(t)), l = f;
  return f;
};
pt();
const Ae = {
  http: cn,
  xhr: Hn,
  fetch: {
    get: pt
  }
};
a.forEach(Ae, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { value: t });
  }
});
const Je = (e) => `- ${e}`, Kn = (e) => a.isFunction(e) || e === null || e === !1;
function Xn(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: n } = e;
  let r, s;
  const i = {};
  for (let o = 0; o < n; o++) {
    r = e[o];
    let c;
    if (s = r, !Kn(r) && (s = Ae[(c = String(r)).toLowerCase()], s === void 0))
      throw new b(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    i[c || "#" + o] = s;
  }
  if (!s) {
    const o = Object.entries(i).map(
      ([u, f]) => `adapter ${u} ` + (f === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = n ? o.length > 1 ? `since :
` + o.map(Je).join(`
`) : " " + Je(o[0]) : "as no adapter specified";
    throw new b(
      "There is no suitable adapter to dispatch the request " + c,
      "ERR_NOT_SUPPORT"
    );
  }
  return s;
}
const ht = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: Xn,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: Ae
};
function be(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new Q(null, e);
}
function We(e) {
  return be(e), e.headers = C.from(e.headers), e.data = me.call(e, e.transformRequest), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), ht.getAdapter(e.adapter || G.adapter, e)(e).then(
    function(r) {
      return be(e), r.data = me.call(e, e.transformResponse, r), r.headers = C.from(r.headers), r;
    },
    function(r) {
      return lt(r) || (be(e), r && r.response && (r.response.data = me.call(
        e,
        e.transformResponse,
        r.response
      ), r.response.headers = C.from(r.response.headers))), Promise.reject(r);
    }
  );
}
const mt = "1.15.0", ue = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  ue[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Ke = {};
ue.transitional = function(t, n, r) {
  function s(i, o) {
    return "[Axios v" + mt + "] Transitional option '" + i + "'" + o + (r ? ". " + r : "");
  }
  return (i, o, c) => {
    if (t === !1)
      throw new b(
        s(o, " has been removed" + (n ? " in " + n : "")),
        b.ERR_DEPRECATED
      );
    return n && !Ke[o] && (Ke[o] = !0, console.warn(
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
function Gn(e, t, n) {
  if (typeof e != "object")
    throw new b("options must be an object", b.ERR_BAD_OPTION_VALUE);
  const r = Object.keys(e);
  let s = r.length;
  for (; s-- > 0; ) {
    const i = r[s], o = t[i];
    if (o) {
      const c = e[i], u = c === void 0 || o(c, i, e);
      if (u !== !0)
        throw new b(
          "option " + i + " must be " + u,
          b.ERR_BAD_OPTION_VALUE
        );
      continue;
    }
    if (n !== !0)
      throw new b("Unknown option " + i, b.ERR_BAD_OPTION);
  }
}
const se = {
  assertOptions: Gn,
  validators: ue
}, P = se.validators;
let q = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new Le(),
      response: new Le()
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
        const i = (() => {
          if (!s.stack)
            return "";
          const o = s.stack.indexOf(`
`);
          return o === -1 ? "" : s.stack.slice(o + 1);
        })();
        try {
          if (!r.stack)
            r.stack = i;
          else if (i) {
            const o = i.indexOf(`
`), c = o === -1 ? -1 : i.indexOf(`
`, o + 1), u = c === -1 ? "" : i.slice(c + 1);
            String(r.stack).endsWith(u) || (r.stack += `
` + i);
          }
        } catch {
        }
      }
      throw r;
    }
  }
  _request(t, n) {
    typeof t == "string" ? (n = n || {}, n.url = t) : n = t || {}, n = H(this.defaults, n);
    const { transitional: r, paramsSerializer: s, headers: i } = n;
    r !== void 0 && se.assertOptions(
      r,
      {
        silentJSONParsing: P.transitional(P.boolean),
        forcedJSONParsing: P.transitional(P.boolean),
        clarifyTimeoutError: P.transitional(P.boolean),
        legacyInterceptorReqResOrdering: P.transitional(P.boolean)
      },
      !1
    ), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : se.assertOptions(
      s,
      {
        encode: P.function,
        serialize: P.function
      },
      !0
    )), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), se.assertOptions(
      n,
      {
        baseUrl: P.spelling("baseURL"),
        withXsrfToken: P.spelling("withXSRFToken")
      },
      !0
    ), n.method = (n.method || this.defaults.method || "get").toLowerCase();
    let o = i && a.merge(i.common, i[n.method]);
    i && a.forEach(["delete", "get", "head", "post", "put", "patch", "common"], (d) => {
      delete i[d];
    }), n.headers = C.concat(o, i);
    const c = [];
    let u = !0;
    this.interceptors.request.forEach(function(m) {
      if (typeof m.runWhen == "function" && m.runWhen(n) === !1)
        return;
      u = u && m.synchronous;
      const p = n.transitional || Oe;
      p && p.legacyInterceptorReqResOrdering ? c.unshift(m.fulfilled, m.rejected) : c.push(m.fulfilled, m.rejected);
    });
    const f = [];
    this.interceptors.response.forEach(function(m) {
      f.push(m.fulfilled, m.rejected);
    });
    let l, h = 0, y;
    if (!u) {
      const d = [We.bind(this), void 0];
      for (d.unshift(...c), d.push(...f), y = d.length, l = Promise.resolve(n); h < y; )
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
      l = We.call(this, g);
    } catch (d) {
      return Promise.reject(d);
    }
    for (h = 0, y = f.length; h < y; )
      l = l.then(f[h++], f[h++]);
    return l;
  }
  getUri(t) {
    t = H(this.defaults, t);
    const n = ft(t.baseURL, t.url, t.allowAbsoluteUrls);
    return it(n, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  q.prototype[t] = function(n, r) {
    return this.request(
      H(r || {}, {
        method: t,
        url: n,
        data: (r || {}).data
      })
    );
  };
});
a.forEach(["post", "put", "patch"], function(t) {
  function n(r) {
    return function(i, o, c) {
      return this.request(
        H(c || {}, {
          method: t,
          headers: r ? {
            "Content-Type": "multipart/form-data"
          } : {},
          url: i,
          data: o
        })
      );
    };
  }
  q.prototype[t] = n(), q.prototype[t + "Form"] = n(!0);
});
let Qn = class bt {
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
      token: new bt(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function Yn(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function Zn(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const Re = {
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
Object.entries(Re).forEach(([e, t]) => {
  Re[t] = e;
});
function yt(e) {
  const t = new q(e), n = Xe(q.prototype.request, t);
  return a.extend(n, q.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return yt(H(e, s));
  }, n;
}
const w = yt(G);
w.Axios = q;
w.CanceledError = Q;
w.CancelToken = Qn;
w.isCancel = lt;
w.VERSION = mt;
w.toFormData = le;
w.AxiosError = b;
w.Cancel = w.CanceledError;
w.all = function(t) {
  return Promise.all(t);
};
w.spread = Yn;
w.isAxiosError = Zn;
w.mergeConfig = H;
w.AxiosHeaders = C;
w.formToJSON = (e) => at(a.isHTMLForm(e) ? new FormData(e) : e);
w.getAdapter = ht.getAdapter;
w.HttpStatusCode = Re;
w.default = w;
const {
  Axios: sr,
  AxiosError: or,
  CanceledError: ir,
  isCancel: ar,
  CancelToken: cr,
  VERSION: lr,
  all: ur,
  Cancel: fr,
  isAxiosError: dr,
  spread: pr,
  toFormData: hr,
  AxiosHeaders: mr,
  HttpStatusCode: br,
  formToJSON: yr,
  getAdapter: wr,
  mergeConfig: Er
} = w, M = w.create({
  withCredentials: !0,
  timeout: 18e4,
  // Add a timeout of 3 minutes
  headers: {
    "Content-Type": "application/json"
  }
});
function Rr() {
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
function gr(e, t = {}) {
  const n = B(e), r = _(null), s = _(null), i = _(!0), o = M.get(n, {
    headers: t
  }).then((c) => (s.value = c.data, i.value = !1, { loading: i, backendError: r, responseData: s })).catch((c) => (r.value = c, i.value = !1, { loading: i, backendError: r, responseData: s }));
  return {
    loading: i,
    backendError: r,
    responseData: s,
    then: (c, u) => o.then(c, u)
  };
}
function Sr(e, t, n = {}) {
  const r = B(e), s = _(null), i = _(null), o = _(!0), c = M.post(r, B(t), {
    headers: n
  }).then((u) => (i.value = u.data, o.value = !1, { loading: o, backendError: s, responseData: i })).catch((u) => (s.value = u, o.value = !1, { loading: o, backendError: s, responseData: i }));
  return {
    loading: o,
    backendError: s,
    responseData: i,
    then: (u, f) => c.then(u, f)
  };
}
function Or(e, t, n = {}) {
  const r = B(e), s = _(null), i = B(t), o = _(!0), c = M.put(r, i, {
    headers: n
  }).then((u) => (console.log(u.statusText), o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, f) => c.then(u, f)
  };
}
function Tr(e, t, n = {}) {
  const r = B(e), s = _(null), i = B(t), o = _(!0), c = M.patch(r, i, {
    headers: n
  }).then((u) => (o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, f) => c.then(u, f)
  };
}
function Ar(e, t = {}) {
  const n = B(e), r = _(null), s = _(!0), i = M.delete(n, {
    headers: t
  }).then((o) => (s.value = !1, { loading: s, backendError: r })).catch((o) => (console.log(o), r.value = o, s.value = !1, { loading: s, backendError: r }));
  return {
    loading: s,
    backendError: r,
    then: (o, c) => i.then(o, c)
  };
}
export {
  Rr as getCsrfToken,
  Ar as useDeleteBackendData,
  gr as useGetBackendData,
  Tr as usePatchBackendData,
  Sr as usePostBackendData,
  Or as usePutBackendData
};
