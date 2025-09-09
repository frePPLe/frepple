import { toValue as _, ref as C } from "vue";
function ke(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: tt } = Object.prototype, { getPrototypeOf: pe } = Object, { iterator: Z, toStringTag: Fe } = Symbol, Y = /* @__PURE__ */ ((e) => (t) => {
  const n = tt.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), N = (e) => (e = e.toLowerCase(), (t) => Y(t) === e), ee = (e) => (t) => typeof t === e, { isArray: q } = Array, M = ee("undefined");
function $(e) {
  return e !== null && !M(e) && e.constructor !== null && !M(e.constructor) && A(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const _e = N("ArrayBuffer");
function nt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && _e(e.buffer), t;
}
const rt = ee("string"), A = ee("function"), De = ee("number"), z = (e) => e !== null && typeof e == "object", st = (e) => e === !0 || e === !1, W = (e) => {
  if (Y(e) !== "object")
    return !1;
  const t = pe(e);
  return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(Fe in e) && !(Z in e);
}, ot = (e) => {
  if (!z(e) || $(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, it = N("Date"), at = N("File"), ct = N("Blob"), lt = N("FileList"), ut = (e) => z(e) && A(e.pipe), ft = (e) => {
  let t;
  return e && (typeof FormData == "function" && e instanceof FormData || A(e.append) && ((t = Y(e)) === "formdata" || // detect form-data instance
  t === "object" && A(e.toString) && e.toString() === "[object FormData]"));
}, dt = N("URLSearchParams"), [pt, ht, mt, yt] = ["ReadableStream", "Request", "Response", "Headers"].map(N), bt = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function v(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), q(e))
    for (r = 0, s = e.length; r < s; r++)
      t.call(null, e[r], r, e);
  else {
    if ($(e))
      return;
    const i = n ? Object.getOwnPropertyNames(e) : Object.keys(e), o = i.length;
    let c;
    for (r = 0; r < o; r++)
      c = i[r], t.call(null, e[c], c, e);
  }
}
function Ue(e, t) {
  if ($(e))
    return null;
  t = t.toLowerCase();
  const n = Object.keys(e);
  let r = n.length, s;
  for (; r-- > 0; )
    if (s = n[r], t === s.toLowerCase())
      return s;
  return null;
}
const U = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, Be = (e) => !M(e) && e !== U;
function ae() {
  const { caseless: e } = Be(this) && this || {}, t = {}, n = (r, s) => {
    const i = e && Ue(t, s) || s;
    W(t[i]) && W(r) ? t[i] = ae(t[i], r) : W(r) ? t[i] = ae({}, r) : q(r) ? t[i] = r.slice() : t[i] = r;
  };
  for (let r = 0, s = arguments.length; r < s; r++)
    arguments[r] && v(arguments[r], n);
  return t;
}
const wt = (e, t, n, { allOwnKeys: r } = {}) => (v(t, (s, i) => {
  n && A(s) ? e[i] = ke(s, n) : e[i] = s;
}, { allOwnKeys: r }), e), Et = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), gt = (e, t, n, r) => {
  e.prototype = Object.create(t.prototype, r), e.prototype.constructor = e, Object.defineProperty(e, "super", {
    value: t.prototype
  }), n && Object.assign(e.prototype, n);
}, Rt = (e, t, n, r) => {
  let s, i, o;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0; )
      o = s[i], (!r || r(o, e, t)) && !c[o] && (t[o] = e[o], c[o] = !0);
    e = n !== !1 && pe(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, St = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, Ot = (e) => {
  if (!e) return null;
  if (q(e)) return e;
  let t = e.length;
  if (!De(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, Tt = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && pe(Uint8Array)), At = (e, t) => {
  const r = (e && e[Z]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const i = s.value;
    t.call(e, i[0], i[1]);
  }
}, xt = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, Ct = N("HTMLFormElement"), Nt = (e) => e.toLowerCase().replace(
  /[-_\s]([a-z\d])(\w*)/g,
  function(n, r, s) {
    return r.toUpperCase() + s;
  }
), be = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), Pt = N("RegExp"), Le = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  v(n, (s, i) => {
    let o;
    (o = t(s, i, e)) !== !1 && (r[i] = o || s);
  }), Object.defineProperties(e, r);
}, kt = (e) => {
  Le(e, (t, n) => {
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
}, Ft = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((i) => {
      n[i] = !0;
    });
  };
  return q(e) ? r(e) : r(String(e).split(t)), n;
}, _t = () => {
}, Dt = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Ut(e) {
  return !!(e && A(e.append) && e[Fe] === "FormData" && e[Z]);
}
const Bt = (e) => {
  const t = new Array(10), n = (r, s) => {
    if (z(r)) {
      if (t.indexOf(r) >= 0)
        return;
      if ($(r))
        return r;
      if (!("toJSON" in r)) {
        t[s] = r;
        const i = q(r) ? [] : {};
        return v(r, (o, c) => {
          const u = n(o, s + 1);
          !M(u) && (i[c] = u);
        }), t[s] = void 0, i;
      }
    }
    return r;
  };
  return n(e, 0);
}, Lt = N("AsyncFunction"), jt = (e) => e && (z(e) || A(e)) && A(e.then) && A(e.catch), je = ((e, t) => e ? setImmediate : t ? ((n, r) => (U.addEventListener("message", ({ source: s, data: i }) => {
  s === U && i === n && r.length && r.shift()();
}, !1), (s) => {
  r.push(s), U.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(
  typeof setImmediate == "function",
  A(U.postMessage)
), qt = typeof queueMicrotask < "u" ? queueMicrotask.bind(U) : typeof process < "u" && process.nextTick || je, It = (e) => e != null && A(e[Z]), a = {
  isArray: q,
  isArrayBuffer: _e,
  isBuffer: $,
  isFormData: ft,
  isArrayBufferView: nt,
  isString: rt,
  isNumber: De,
  isBoolean: st,
  isObject: z,
  isPlainObject: W,
  isEmptyObject: ot,
  isReadableStream: pt,
  isRequest: ht,
  isResponse: mt,
  isHeaders: yt,
  isUndefined: M,
  isDate: it,
  isFile: at,
  isBlob: ct,
  isRegExp: Pt,
  isFunction: A,
  isStream: ut,
  isURLSearchParams: dt,
  isTypedArray: Tt,
  isFileList: lt,
  forEach: v,
  merge: ae,
  extend: wt,
  trim: bt,
  stripBOM: Et,
  inherits: gt,
  toFlatObject: Rt,
  kindOf: Y,
  kindOfTest: N,
  endsWith: St,
  toArray: Ot,
  forEachEntry: At,
  matchAll: xt,
  isHTMLForm: Ct,
  hasOwnProperty: be,
  hasOwnProp: be,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors: Le,
  freezeMethods: kt,
  toObjectSet: Ft,
  toCamelCase: Nt,
  noop: _t,
  toFiniteNumber: Dt,
  findKey: Ue,
  global: U,
  isContextDefined: Be,
  isSpecCompliantForm: Ut,
  toJSONObject: Bt,
  isAsyncFn: Lt,
  isThenable: jt,
  setImmediate: je,
  asap: qt,
  isIterable: It
};
function m(e, t, n, r, s) {
  Error.call(this), Error.captureStackTrace ? Error.captureStackTrace(this, this.constructor) : this.stack = new Error().stack, this.message = e, this.name = "AxiosError", t && (this.code = t), n && (this.config = n), r && (this.request = r), s && (this.response = s, this.status = s.status ? s.status : null);
}
a.inherits(m, Error, {
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
const qe = m.prototype, Ie = {};
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
  Ie[e] = { value: e };
});
Object.defineProperties(m, Ie);
Object.defineProperty(qe, "isAxiosError", { value: !0 });
m.from = (e, t, n, r, s, i) => {
  const o = Object.create(qe);
  return a.toFlatObject(e, o, function(u) {
    return u !== Error.prototype;
  }, (c) => c !== "isAxiosError"), m.call(o, e.message, t, n, r, s), o.cause = e, o.name = e.name, i && Object.assign(o, i), o;
};
const Ht = null;
function ce(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function He(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function we(e, t, n) {
  return e ? e.concat(t).map(function(s, i) {
    return s = He(s), !n && i ? "[" + s + "]" : s;
  }).join(n ? "." : "") : t;
}
function Mt(e) {
  return a.isArray(e) && !e.some(ce);
}
const $t = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function te(e, t, n) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData(), n = a.toFlatObject(n, {
    metaTokens: !0,
    dots: !1,
    indexes: !1
  }, !1, function(y, h) {
    return !a.isUndefined(h[y]);
  });
  const r = n.metaTokens, s = n.visitor || f, i = n.dots, o = n.indexes, u = (n.Blob || typeof Blob < "u" && Blob) && a.isSpecCompliantForm(t);
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function l(p) {
    if (p === null) return "";
    if (a.isDate(p))
      return p.toISOString();
    if (a.isBoolean(p))
      return p.toString();
    if (!u && a.isBlob(p))
      throw new m("Blob is not supported. Use a Buffer instead.");
    return a.isArrayBuffer(p) || a.isTypedArray(p) ? u && typeof Blob == "function" ? new Blob([p]) : Buffer.from(p) : p;
  }
  function f(p, y, h) {
    let w = p;
    if (p && !h && typeof p == "object") {
      if (a.endsWith(y, "{}"))
        y = r ? y : y.slice(0, -2), p = JSON.stringify(p);
      else if (a.isArray(p) && Mt(p) || (a.isFileList(p) || a.endsWith(y, "[]")) && (w = a.toArray(p)))
        return y = He(y), w.forEach(function(S, k) {
          !(a.isUndefined(S) || S === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            o === !0 ? we([y], k, i) : o === null ? y : y + "[]",
            l(S)
          );
        }), !1;
    }
    return ce(p) ? !0 : (t.append(we(h, y, i), l(p)), !1);
  }
  const d = [], b = Object.assign($t, {
    defaultVisitor: f,
    convertValue: l,
    isVisitable: ce
  });
  function g(p, y) {
    if (!a.isUndefined(p)) {
      if (d.indexOf(p) !== -1)
        throw Error("Circular reference detected in " + y.join("."));
      d.push(p), a.forEach(p, function(w, R) {
        (!(a.isUndefined(w) || w === null) && s.call(
          t,
          w,
          a.isString(R) ? R.trim() : R,
          y,
          b
        )) === !0 && g(w, y ? y.concat(R) : [R]);
      }), d.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return g(e), t;
}
function Ee(e) {
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
function he(e, t) {
  this._pairs = [], e && te(e, this, t);
}
const Me = he.prototype;
Me.append = function(t, n) {
  this._pairs.push([t, n]);
};
Me.toString = function(t) {
  const n = t ? function(r) {
    return t.call(this, r, Ee);
  } : Ee;
  return this._pairs.map(function(s) {
    return n(s[0]) + "=" + n(s[1]);
  }, "").join("&");
};
function zt(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+").replace(/%5B/gi, "[").replace(/%5D/gi, "]");
}
function $e(e, t, n) {
  if (!t)
    return e;
  const r = n && n.encode || zt;
  a.isFunction(n) && (n = {
    serialize: n
  });
  const s = n && n.serialize;
  let i;
  if (s ? i = s(t, n) : i = a.isURLSearchParams(t) ? t.toString() : new he(t, n).toString(r), i) {
    const o = e.indexOf("#");
    o !== -1 && (e = e.slice(0, o)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
class ge {
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
   * @returns {Boolean} `true` if the interceptor was removed, `false` otherwise
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
const ze = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1
}, vt = typeof URLSearchParams < "u" ? URLSearchParams : he, Jt = typeof FormData < "u" ? FormData : null, Vt = typeof Blob < "u" ? Blob : null, Wt = {
  isBrowser: !0,
  classes: {
    URLSearchParams: vt,
    FormData: Jt,
    Blob: Vt
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, me = typeof window < "u" && typeof document < "u", le = typeof navigator == "object" && navigator || void 0, Kt = me && (!le || ["ReactNative", "NativeScript", "NS"].indexOf(le.product) < 0), Xt = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", Gt = me && window.location.href || "http://localhost", Qt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: me,
  hasStandardBrowserEnv: Kt,
  hasStandardBrowserWebWorkerEnv: Xt,
  navigator: le,
  origin: Gt
}, Symbol.toStringTag, { value: "Module" })), O = {
  ...Qt,
  ...Wt
};
function Zt(e, t) {
  return te(e, new O.classes.URLSearchParams(), {
    visitor: function(n, r, s, i) {
      return O.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function Yt(e) {
  return a.matchAll(/\w+|\[(\w*)]/g, e).map((t) => t[0] === "[]" ? "" : t[1] || t[0]);
}
function en(e) {
  const t = {}, n = Object.keys(e);
  let r;
  const s = n.length;
  let i;
  for (r = 0; r < s; r++)
    i = n[r], t[i] = e[i];
  return t;
}
function ve(e) {
  function t(n, r, s, i) {
    let o = n[i++];
    if (o === "__proto__") return !0;
    const c = Number.isFinite(+o), u = i >= n.length;
    return o = !o && a.isArray(s) ? s.length : o, u ? (a.hasOwnProp(s, o) ? s[o] = [s[o], r] : s[o] = r, !c) : ((!s[o] || !a.isObject(s[o])) && (s[o] = []), t(n, r, s[o], i) && a.isArray(s[o]) && (s[o] = en(s[o])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(Yt(r), s, n, 0);
    }), n;
  }
  return null;
}
function tn(e, t, n) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (r) {
      if (r.name !== "SyntaxError")
        throw r;
    }
  return (n || JSON.stringify)(e);
}
const J = {
  transitional: ze,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [function(t, n) {
    const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, i = a.isObject(t);
    if (i && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
      return s ? JSON.stringify(ve(t)) : t;
    if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
      return t;
    if (a.isArrayBufferView(t))
      return t.buffer;
    if (a.isURLSearchParams(t))
      return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
    let c;
    if (i) {
      if (r.indexOf("application/x-www-form-urlencoded") > -1)
        return Zt(t, this.formSerializer).toString();
      if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
        const u = this.env && this.env.FormData;
        return te(
          c ? { "files[]": t } : t,
          u && new u(),
          this.formSerializer
        );
      }
    }
    return i || s ? (n.setContentType("application/json", !1), tn(t)) : t;
  }],
  transformResponse: [function(t) {
    const n = this.transitional || J.transitional, r = n && n.forcedJSONParsing, s = this.responseType === "json";
    if (a.isResponse(t) || a.isReadableStream(t))
      return t;
    if (t && a.isString(t) && (r && !this.responseType || s)) {
      const o = !(n && n.silentJSONParsing) && s;
      try {
        return JSON.parse(t);
      } catch (c) {
        if (o)
          throw c.name === "SyntaxError" ? m.from(c, m.ERR_BAD_RESPONSE, this, null, this.response) : c;
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
    FormData: O.classes.FormData,
    Blob: O.classes.Blob
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
  J.headers[e] = {};
});
const nn = a.toObjectSet([
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
]), rn = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(o) {
    s = o.indexOf(":"), n = o.substring(0, s).trim().toLowerCase(), r = o.substring(s + 1).trim(), !(!n || t[n] && nn[n]) && (n === "set-cookie" ? t[n] ? t[n].push(r) : t[n] = [r] : t[n] = t[n] ? t[n] + ", " + r : r);
  }), t;
}, Re = Symbol("internals");
function H(e) {
  return e && String(e).trim().toLowerCase();
}
function K(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(K) : String(e);
}
function sn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const on = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function se(e, t, n, r, s) {
  if (a.isFunction(r))
    return r.call(this, t, n);
  if (s && (t = n), !!a.isString(t)) {
    if (a.isString(r))
      return t.indexOf(r) !== -1;
    if (a.isRegExp(r))
      return r.test(t);
  }
}
function an(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function cn(e, t) {
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
let x = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, n, r) {
    const s = this;
    function i(c, u, l) {
      const f = H(u);
      if (!f)
        throw new Error("header name must be a non-empty string");
      const d = a.findKey(s, f);
      (!d || s[d] === void 0 || l === !0 || l === void 0 && s[d] !== !1) && (s[d || u] = K(c));
    }
    const o = (c, u) => a.forEach(c, (l, f) => i(l, f, u));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      o(t, n);
    else if (a.isString(t) && (t = t.trim()) && !on(t))
      o(rn(t), n);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, u, l;
      for (const f of t) {
        if (!a.isArray(f))
          throw TypeError("Object iterator must return a key-value pair");
        c[l = f[0]] = (u = c[l]) ? a.isArray(u) ? [...u, f[1]] : [u, f[1]] : f[1];
      }
      o(c, n);
    } else
      t != null && i(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = H(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return sn(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = H(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || se(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function i(o) {
      if (o = H(o), o) {
        const c = a.findKey(r, o);
        c && (!n || se(r, r[c], c, n)) && (delete r[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(i) : i(t), s;
  }
  clear(t) {
    const n = Object.keys(this);
    let r = n.length, s = !1;
    for (; r--; ) {
      const i = n[r];
      (!t || se(this, this[i], i, t, !0)) && (delete this[i], s = !0);
    }
    return s;
  }
  normalize(t) {
    const n = this, r = {};
    return a.forEach(this, (s, i) => {
      const o = a.findKey(r, i);
      if (o) {
        n[o] = K(s), delete n[i];
        return;
      }
      const c = t ? an(i) : String(i).trim();
      c !== i && delete n[i], n[c] = K(s), r[c] = !0;
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
    const r = (this[Re] = this[Re] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function i(o) {
      const c = H(o);
      r[c] || (cn(s, o), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(i) : i(t), this;
  }
};
x.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
a.reduceDescriptors(x.prototype, ({ value: e }, t) => {
  let n = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(r) {
      this[n] = r;
    }
  };
});
a.freezeMethods(x);
function oe(e, t) {
  const n = this || J, r = t || n, s = x.from(r.headers);
  let i = r.data;
  return a.forEach(e, function(c) {
    i = c.call(n, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function Je(e) {
  return !!(e && e.__CANCEL__);
}
function I(e, t, n) {
  m.call(this, e ?? "canceled", m.ERR_CANCELED, t, n), this.name = "CanceledError";
}
a.inherits(I, m, {
  __CANCEL__: !0
});
function Ve(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(new m(
    "Request failed with status code " + n.status,
    [m.ERR_BAD_REQUEST, m.ERR_BAD_RESPONSE][Math.floor(n.status / 100) - 4],
    n.config,
    n.request,
    n
  ));
}
function ln(e) {
  const t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function un(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, i = 0, o;
  return t = t !== void 0 ? t : 1e3, function(u) {
    const l = Date.now(), f = r[i];
    o || (o = l), n[s] = u, r[s] = l;
    let d = i, b = 0;
    for (; d !== s; )
      b += n[d++], d = d % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), l - o < t)
      return;
    const g = f && l - f;
    return g ? Math.round(b * 1e3 / g) : void 0;
  };
}
function fn(e, t) {
  let n = 0, r = 1e3 / t, s, i;
  const o = (l, f = Date.now()) => {
    n = f, s = null, i && (clearTimeout(i), i = null), e(...l);
  };
  return [(...l) => {
    const f = Date.now(), d = f - n;
    d >= r ? o(l, f) : (s = l, i || (i = setTimeout(() => {
      i = null, o(s);
    }, r - d)));
  }, () => s && o(s)];
}
const G = (e, t, n = 3) => {
  let r = 0;
  const s = un(50, 250);
  return fn((i) => {
    const o = i.loaded, c = i.lengthComputable ? i.total : void 0, u = o - r, l = s(u), f = o <= c;
    r = o;
    const d = {
      loaded: o,
      total: c,
      progress: c ? o / c : void 0,
      bytes: u,
      rate: l || void 0,
      estimated: l && c && f ? (c - o) / l : void 0,
      event: i,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(d);
  }, n);
}, Se = (e, t) => {
  const n = e != null;
  return [(r) => t[0]({
    lengthComputable: n,
    total: e,
    loaded: r
  }), t[1]];
}, Oe = (e) => (...t) => a.asap(() => e(...t)), dn = O.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, O.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(O.origin),
  O.navigator && /(msie|trident)/i.test(O.navigator.userAgent)
) : () => !0, pn = O.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(e, t, n, r, s, i) {
      const o = [e + "=" + encodeURIComponent(t)];
      a.isNumber(n) && o.push("expires=" + new Date(n).toGMTString()), a.isString(r) && o.push("path=" + r), a.isString(s) && o.push("domain=" + s), i === !0 && o.push("secure"), document.cookie = o.join("; ");
    },
    read(e) {
      const t = document.cookie.match(new RegExp("(^|;\\s*)(" + e + ")=([^;]*)"));
      return t ? decodeURIComponent(t[3]) : null;
    },
    remove(e) {
      this.write(e, "", Date.now() - 864e5);
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
function hn(e) {
  return /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function mn(e, t) {
  return t ? e.replace(/\/?\/$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function We(e, t, n) {
  let r = !hn(t);
  return e && (r || n == !1) ? mn(e, t) : t;
}
const Te = (e) => e instanceof x ? { ...e } : e;
function L(e, t) {
  t = t || {};
  const n = {};
  function r(l, f, d, b) {
    return a.isPlainObject(l) && a.isPlainObject(f) ? a.merge.call({ caseless: b }, l, f) : a.isPlainObject(f) ? a.merge({}, f) : a.isArray(f) ? f.slice() : f;
  }
  function s(l, f, d, b) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(l))
        return r(void 0, l, d, b);
    } else return r(l, f, d, b);
  }
  function i(l, f) {
    if (!a.isUndefined(f))
      return r(void 0, f);
  }
  function o(l, f) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(l))
        return r(void 0, l);
    } else return r(void 0, f);
  }
  function c(l, f, d) {
    if (d in t)
      return r(l, f);
    if (d in e)
      return r(void 0, l);
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
    headers: (l, f, d) => s(Te(l), Te(f), d, !0)
  };
  return a.forEach(Object.keys({ ...e, ...t }), function(f) {
    const d = u[f] || s, b = d(e[f], t[f], f);
    a.isUndefined(b) && d !== c || (n[f] = b);
  }), n;
}
const Ke = (e) => {
  const t = L({}, e);
  let { data: n, withXSRFToken: r, xsrfHeaderName: s, xsrfCookieName: i, headers: o, auth: c } = t;
  t.headers = o = x.from(o), t.url = $e(We(t.baseURL, t.url, t.allowAbsoluteUrls), e.params, e.paramsSerializer), c && o.set(
    "Authorization",
    "Basic " + btoa((c.username || "") + ":" + (c.password ? unescape(encodeURIComponent(c.password)) : ""))
  );
  let u;
  if (a.isFormData(n)) {
    if (O.hasStandardBrowserEnv || O.hasStandardBrowserWebWorkerEnv)
      o.setContentType(void 0);
    else if ((u = o.getContentType()) !== !1) {
      const [l, ...f] = u ? u.split(";").map((d) => d.trim()).filter(Boolean) : [];
      o.setContentType([l || "multipart/form-data", ...f].join("; "));
    }
  }
  if (O.hasStandardBrowserEnv && (r && a.isFunction(r) && (r = r(t)), r || r !== !1 && dn(t.url))) {
    const l = s && i && pn.read(i);
    l && o.set(s, l);
  }
  return t;
}, yn = typeof XMLHttpRequest < "u", bn = yn && function(e) {
  return new Promise(function(n, r) {
    const s = Ke(e);
    let i = s.data;
    const o = x.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: u, onDownloadProgress: l } = s, f, d, b, g, p;
    function y() {
      g && g(), p && p(), s.cancelToken && s.cancelToken.unsubscribe(f), s.signal && s.signal.removeEventListener("abort", f);
    }
    let h = new XMLHttpRequest();
    h.open(s.method.toUpperCase(), s.url, !0), h.timeout = s.timeout;
    function w() {
      if (!h)
        return;
      const S = x.from(
        "getAllResponseHeaders" in h && h.getAllResponseHeaders()
      ), T = {
        data: !c || c === "text" || c === "json" ? h.responseText : h.response,
        status: h.status,
        statusText: h.statusText,
        headers: S,
        config: e,
        request: h
      };
      Ve(function(D) {
        n(D), y();
      }, function(D) {
        r(D), y();
      }, T), h = null;
    }
    "onloadend" in h ? h.onloadend = w : h.onreadystatechange = function() {
      !h || h.readyState !== 4 || h.status === 0 && !(h.responseURL && h.responseURL.indexOf("file:") === 0) || setTimeout(w);
    }, h.onabort = function() {
      h && (r(new m("Request aborted", m.ECONNABORTED, e, h)), h = null);
    }, h.onerror = function() {
      r(new m("Network Error", m.ERR_NETWORK, e, h)), h = null;
    }, h.ontimeout = function() {
      let k = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const T = s.transitional || ze;
      s.timeoutErrorMessage && (k = s.timeoutErrorMessage), r(new m(
        k,
        T.clarifyTimeoutError ? m.ETIMEDOUT : m.ECONNABORTED,
        e,
        h
      )), h = null;
    }, i === void 0 && o.setContentType(null), "setRequestHeader" in h && a.forEach(o.toJSON(), function(k, T) {
      h.setRequestHeader(T, k);
    }), a.isUndefined(s.withCredentials) || (h.withCredentials = !!s.withCredentials), c && c !== "json" && (h.responseType = s.responseType), l && ([b, p] = G(l, !0), h.addEventListener("progress", b)), u && h.upload && ([d, g] = G(u), h.upload.addEventListener("progress", d), h.upload.addEventListener("loadend", g)), (s.cancelToken || s.signal) && (f = (S) => {
      h && (r(!S || S.type ? new I(null, e, h) : S), h.abort(), h = null);
    }, s.cancelToken && s.cancelToken.subscribe(f), s.signal && (s.signal.aborted ? f() : s.signal.addEventListener("abort", f)));
    const R = ln(s.url);
    if (R && O.protocols.indexOf(R) === -1) {
      r(new m("Unsupported protocol " + R + ":", m.ERR_BAD_REQUEST, e));
      return;
    }
    h.send(i || null);
  });
}, wn = (e, t) => {
  const { length: n } = e = e ? e.filter(Boolean) : [];
  if (t || n) {
    let r = new AbortController(), s;
    const i = function(l) {
      if (!s) {
        s = !0, c();
        const f = l instanceof Error ? l : this.reason;
        r.abort(f instanceof m ? f : new I(f instanceof Error ? f.message : f));
      }
    };
    let o = t && setTimeout(() => {
      o = null, i(new m(`timeout ${t} of ms exceeded`, m.ETIMEDOUT));
    }, t);
    const c = () => {
      e && (o && clearTimeout(o), o = null, e.forEach((l) => {
        l.unsubscribe ? l.unsubscribe(i) : l.removeEventListener("abort", i);
      }), e = null);
    };
    e.forEach((l) => l.addEventListener("abort", i));
    const { signal: u } = r;
    return u.unsubscribe = () => a.asap(c), u;
  }
}, En = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, gn = async function* (e, t) {
  for await (const n of Rn(e))
    yield* En(n, t);
}, Rn = async function* (e) {
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
}, Ae = (e, t, n, r) => {
  const s = gn(e, t);
  let i = 0, o, c = (u) => {
    o || (o = !0, r && r(u));
  };
  return new ReadableStream({
    async pull(u) {
      try {
        const { done: l, value: f } = await s.next();
        if (l) {
          c(), u.close();
          return;
        }
        let d = f.byteLength;
        if (n) {
          let b = i += d;
          n(b);
        }
        u.enqueue(new Uint8Array(f));
      } catch (l) {
        throw c(l), l;
      }
    },
    cancel(u) {
      return c(u), s.return();
    }
  }, {
    highWaterMark: 2
  });
}, ne = typeof fetch == "function" && typeof Request == "function" && typeof Response == "function", Xe = ne && typeof ReadableStream == "function", Sn = ne && (typeof TextEncoder == "function" ? /* @__PURE__ */ ((e) => (t) => e.encode(t))(new TextEncoder()) : async (e) => new Uint8Array(await new Response(e).arrayBuffer())), Ge = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, On = Xe && Ge(() => {
  let e = !1;
  const t = new Request(O.origin, {
    body: new ReadableStream(),
    method: "POST",
    get duplex() {
      return e = !0, "half";
    }
  }).headers.has("Content-Type");
  return e && !t;
}), xe = 64 * 1024, ue = Xe && Ge(() => a.isReadableStream(new Response("").body)), Q = {
  stream: ue && ((e) => e.body)
};
ne && ((e) => {
  ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((t) => {
    !Q[t] && (Q[t] = a.isFunction(e[t]) ? (n) => n[t]() : (n, r) => {
      throw new m(`Response type '${t}' is not supported`, m.ERR_NOT_SUPPORT, r);
    });
  });
})(new Response());
const Tn = async (e) => {
  if (e == null)
    return 0;
  if (a.isBlob(e))
    return e.size;
  if (a.isSpecCompliantForm(e))
    return (await new Request(O.origin, {
      method: "POST",
      body: e
    }).arrayBuffer()).byteLength;
  if (a.isArrayBufferView(e) || a.isArrayBuffer(e))
    return e.byteLength;
  if (a.isURLSearchParams(e) && (e = e + ""), a.isString(e))
    return (await Sn(e)).byteLength;
}, An = async (e, t) => {
  const n = a.toFiniteNumber(e.getContentLength());
  return n ?? Tn(t);
}, xn = ne && (async (e) => {
  let {
    url: t,
    method: n,
    data: r,
    signal: s,
    cancelToken: i,
    timeout: o,
    onDownloadProgress: c,
    onUploadProgress: u,
    responseType: l,
    headers: f,
    withCredentials: d = "same-origin",
    fetchOptions: b
  } = Ke(e);
  l = l ? (l + "").toLowerCase() : "text";
  let g = wn([s, i && i.toAbortSignal()], o), p;
  const y = g && g.unsubscribe && (() => {
    g.unsubscribe();
  });
  let h;
  try {
    if (u && On && n !== "get" && n !== "head" && (h = await An(f, r)) !== 0) {
      let T = new Request(t, {
        method: "POST",
        body: r,
        duplex: "half"
      }), F;
      if (a.isFormData(r) && (F = T.headers.get("content-type")) && f.setContentType(F), T.body) {
        const [D, V] = Se(
          h,
          G(Oe(u))
        );
        r = Ae(T.body, xe, D, V);
      }
    }
    a.isString(d) || (d = d ? "include" : "omit");
    const w = "credentials" in Request.prototype;
    p = new Request(t, {
      ...b,
      signal: g,
      method: n.toUpperCase(),
      headers: f.normalize().toJSON(),
      body: r,
      duplex: "half",
      credentials: w ? d : void 0
    });
    let R = await fetch(p, b);
    const S = ue && (l === "stream" || l === "response");
    if (ue && (c || S && y)) {
      const T = {};
      ["status", "statusText", "headers"].forEach((ye) => {
        T[ye] = R[ye];
      });
      const F = a.toFiniteNumber(R.headers.get("content-length")), [D, V] = c && Se(
        F,
        G(Oe(c), !0)
      ) || [];
      R = new Response(
        Ae(R.body, xe, D, () => {
          V && V(), y && y();
        }),
        T
      );
    }
    l = l || "text";
    let k = await Q[a.findKey(Q, l) || "text"](R, e);
    return !S && y && y(), await new Promise((T, F) => {
      Ve(T, F, {
        data: k,
        headers: x.from(R.headers),
        status: R.status,
        statusText: R.statusText,
        config: e,
        request: p
      });
    });
  } catch (w) {
    throw y && y(), w && w.name === "TypeError" && /Load failed|fetch/i.test(w.message) ? Object.assign(
      new m("Network Error", m.ERR_NETWORK, e, p),
      {
        cause: w.cause || w
      }
    ) : m.from(w, w && w.code, e, p);
  }
}), fe = {
  http: Ht,
  xhr: bn,
  fetch: xn
};
a.forEach(fe, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { value: t });
  }
});
const Ce = (e) => `- ${e}`, Cn = (e) => a.isFunction(e) || e === null || e === !1, Qe = {
  getAdapter: (e) => {
    e = a.isArray(e) ? e : [e];
    const { length: t } = e;
    let n, r;
    const s = {};
    for (let i = 0; i < t; i++) {
      n = e[i];
      let o;
      if (r = n, !Cn(n) && (r = fe[(o = String(n)).toLowerCase()], r === void 0))
        throw new m(`Unknown adapter '${o}'`);
      if (r)
        break;
      s[o || "#" + i] = r;
    }
    if (!r) {
      const i = Object.entries(s).map(
        ([c, u]) => `adapter ${c} ` + (u === !1 ? "is not supported by the environment" : "is not available in the build")
      );
      let o = t ? i.length > 1 ? `since :
` + i.map(Ce).join(`
`) : " " + Ce(i[0]) : "as no adapter specified";
      throw new m(
        "There is no suitable adapter to dispatch the request " + o,
        "ERR_NOT_SUPPORT"
      );
    }
    return r;
  },
  adapters: fe
};
function ie(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new I(null, e);
}
function Ne(e) {
  return ie(e), e.headers = x.from(e.headers), e.data = oe.call(
    e,
    e.transformRequest
  ), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), Qe.getAdapter(e.adapter || J.adapter)(e).then(function(r) {
    return ie(e), r.data = oe.call(
      e,
      e.transformResponse,
      r
    ), r.headers = x.from(r.headers), r;
  }, function(r) {
    return Je(r) || (ie(e), r && r.response && (r.response.data = oe.call(
      e,
      e.transformResponse,
      r.response
    ), r.response.headers = x.from(r.response.headers))), Promise.reject(r);
  });
}
const Ze = "1.11.0", re = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  re[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Pe = {};
re.transitional = function(t, n, r) {
  function s(i, o) {
    return "[Axios v" + Ze + "] Transitional option '" + i + "'" + o + (r ? ". " + r : "");
  }
  return (i, o, c) => {
    if (t === !1)
      throw new m(
        s(o, " has been removed" + (n ? " in " + n : "")),
        m.ERR_DEPRECATED
      );
    return n && !Pe[o] && (Pe[o] = !0, console.warn(
      s(
        o,
        " has been deprecated since v" + n + " and will be removed in the near future"
      )
    )), t ? t(i, o, c) : !0;
  };
};
re.spelling = function(t) {
  return (n, r) => (console.warn(`${r} is likely a misspelling of ${t}`), !0);
};
function Nn(e, t, n) {
  if (typeof e != "object")
    throw new m("options must be an object", m.ERR_BAD_OPTION_VALUE);
  const r = Object.keys(e);
  let s = r.length;
  for (; s-- > 0; ) {
    const i = r[s], o = t[i];
    if (o) {
      const c = e[i], u = c === void 0 || o(c, i, e);
      if (u !== !0)
        throw new m("option " + i + " must be " + u, m.ERR_BAD_OPTION_VALUE);
      continue;
    }
    if (n !== !0)
      throw new m("Unknown option " + i, m.ERR_BAD_OPTION);
  }
}
const X = {
  assertOptions: Nn,
  validators: re
}, P = X.validators;
let B = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new ge(),
      response: new ge()
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
    typeof t == "string" ? (n = n || {}, n.url = t) : n = t || {}, n = L(this.defaults, n);
    const { transitional: r, paramsSerializer: s, headers: i } = n;
    r !== void 0 && X.assertOptions(r, {
      silentJSONParsing: P.transitional(P.boolean),
      forcedJSONParsing: P.transitional(P.boolean),
      clarifyTimeoutError: P.transitional(P.boolean)
    }, !1), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : X.assertOptions(s, {
      encode: P.function,
      serialize: P.function
    }, !0)), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), X.assertOptions(n, {
      baseUrl: P.spelling("baseURL"),
      withXsrfToken: P.spelling("withXSRFToken")
    }, !0), n.method = (n.method || this.defaults.method || "get").toLowerCase();
    let o = i && a.merge(
      i.common,
      i[n.method]
    );
    i && a.forEach(
      ["delete", "get", "head", "post", "put", "patch", "common"],
      (p) => {
        delete i[p];
      }
    ), n.headers = x.concat(o, i);
    const c = [];
    let u = !0;
    this.interceptors.request.forEach(function(y) {
      typeof y.runWhen == "function" && y.runWhen(n) === !1 || (u = u && y.synchronous, c.unshift(y.fulfilled, y.rejected));
    });
    const l = [];
    this.interceptors.response.forEach(function(y) {
      l.push(y.fulfilled, y.rejected);
    });
    let f, d = 0, b;
    if (!u) {
      const p = [Ne.bind(this), void 0];
      for (p.unshift(...c), p.push(...l), b = p.length, f = Promise.resolve(n); d < b; )
        f = f.then(p[d++], p[d++]);
      return f;
    }
    b = c.length;
    let g = n;
    for (d = 0; d < b; ) {
      const p = c[d++], y = c[d++];
      try {
        g = p(g);
      } catch (h) {
        y.call(this, h);
        break;
      }
    }
    try {
      f = Ne.call(this, g);
    } catch (p) {
      return Promise.reject(p);
    }
    for (d = 0, b = l.length; d < b; )
      f = f.then(l[d++], l[d++]);
    return f;
  }
  getUri(t) {
    t = L(this.defaults, t);
    const n = We(t.baseURL, t.url, t.allowAbsoluteUrls);
    return $e(n, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  B.prototype[t] = function(n, r) {
    return this.request(L(r || {}, {
      method: t,
      url: n,
      data: (r || {}).data
    }));
  };
});
a.forEach(["post", "put", "patch"], function(t) {
  function n(r) {
    return function(i, o, c) {
      return this.request(L(c || {}, {
        method: t,
        headers: r ? {
          "Content-Type": "multipart/form-data"
        } : {},
        url: i,
        data: o
      }));
    };
  }
  B.prototype[t] = n(), B.prototype[t + "Form"] = n(!0);
});
let Pn = class Ye {
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
      r.reason || (r.reason = new I(i, o, c), n(r.reason));
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
      token: new Ye(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function kn(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function Fn(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const de = {
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
  NetworkAuthenticationRequired: 511
};
Object.entries(de).forEach(([e, t]) => {
  de[t] = e;
});
function et(e) {
  const t = new B(e), n = ke(B.prototype.request, t);
  return a.extend(n, B.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return et(L(e, s));
  }, n;
}
const E = et(J);
E.Axios = B;
E.CanceledError = I;
E.CancelToken = Pn;
E.isCancel = Je;
E.VERSION = Ze;
E.toFormData = te;
E.AxiosError = m;
E.Cancel = E.CanceledError;
E.all = function(t) {
  return Promise.all(t);
};
E.spread = kn;
E.isAxiosError = Fn;
E.mergeConfig = L;
E.AxiosHeaders = x;
E.formToJSON = (e) => ve(a.isHTMLForm(e) ? new FormData(e) : e);
E.getAdapter = Qe.getAdapter;
E.HttpStatusCode = de;
E.default = E;
const {
  Axios: Bn,
  AxiosError: Ln,
  CanceledError: jn,
  isCancel: qn,
  CancelToken: In,
  VERSION: Hn,
  all: Mn,
  Cancel: $n,
  isAxiosError: zn,
  spread: vn,
  toFormData: Jn,
  AxiosHeaders: Vn,
  HttpStatusCode: Wn,
  formToJSON: Kn,
  getAdapter: Xn,
  mergeConfig: Gn
} = E, j = E.create({
  withCredentials: !0,
  timeout: 5e3,
  // Add a timeout of 5 seconds
  headers: {
    "Content-Type": "application/json"
  }
});
j.interceptors.request.use(
  (e) => e,
  (e) => Promise.reject(e)
);
j.interceptors.response.use(
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
function Qn(e, t = {}) {
  const n = _(e), r = C(null), s = C(null), i = C(!0), o = j.get(n, {
    headers: t
  }).then((c) => (s.value = c.data, i.value = !1, { loading: i, backendError: r, responseData: s })).catch((c) => (r.value = c, i.value = !1, { loading: i, backendError: r, responseData: s }));
  return {
    loading: i,
    backendError: r,
    responseData: s,
    then: (c, u) => o.then(c, u)
  };
}
function Zn(e, t, n = {}) {
  const r = _(e), s = C(null), i = C(null), o = C(!0), c = j.post(r, _(t), {
    headers: n
  }).then((u) => (console.log(u.statusText), i.value = u.data, o.value = !1, { loading: o, backendError: s, responseData: i })).catch((u) => (s.value = u, o.value = !1, { loading: o, backendError: s, responseData: i }));
  return {
    loading: o,
    backendError: s,
    responseData: i,
    then: (u, l) => c.then(u, l)
  };
}
function Yn(e, t, n = {}) {
  const r = _(e), s = C(null), i = _(t), o = C(!0), c = j.put(r, i, {
    headers: n
  }).then((u) => (console.log(u.statusText), o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, l) => c.then(u, l)
  };
}
function er(e, t, n = {}) {
  const r = _(e), s = C(null), i = _(t), o = C(!0), c = j.patch(r, i, {
    headers: n
  }).then((u) => (o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, l) => c.then(u, l)
  };
}
function tr(e, t = {}) {
  const n = _(e), r = C(null), s = C(!0), i = j.delete(n, {
    headers: t
  }).then((o) => (s.value = !1, { loading: s, backendError: r })).catch((o) => (console.log(o), r.value = o, s.value = !1, { loading: s, backendError: r }));
  return {
    loading: s,
    backendError: r,
    then: (o, c) => i.then(o, c)
  };
}
export {
  tr as useDeleteBackendData,
  Qn as useGetBackendData,
  er as usePatchBackendData,
  Zn as usePostBackendData,
  Yn as usePutBackendData
};
