import { toValue as _, ref as C } from "vue";
function ke(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: tt } = Object.prototype, { getPrototypeOf: pe } = Object, { iterator: Z, toStringTag: Fe } = Symbol, Y = /* @__PURE__ */ ((e) => (t) => {
  const r = tt.call(t);
  return e[r] || (e[r] = r.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), N = (e) => (e = e.toLowerCase(), (t) => Y(t) === e), ee = (e) => (t) => typeof t === e, { isArray: q } = Array, M = ee("undefined");
function $(e) {
  return e !== null && !M(e) && e.constructor !== null && !M(e.constructor) && A(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const _e = N("ArrayBuffer");
function nt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && _e(e.buffer), t;
}
const rt = ee("string"), A = ee("function"), Ue = ee("number"), z = (e) => e !== null && typeof e == "object", st = (e) => e === !0 || e === !1, W = (e) => {
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
function v(e, t, { allOwnKeys: r = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let n, s;
  if (typeof e != "object" && (e = [e]), q(e))
    for (n = 0, s = e.length; n < s; n++)
      t.call(null, e[n], n, e);
  else {
    if ($(e))
      return;
    const i = r ? Object.getOwnPropertyNames(e) : Object.keys(e), o = i.length;
    let c;
    for (n = 0; n < o; n++)
      c = i[n], t.call(null, e[c], c, e);
  }
}
function De(e, t) {
  if ($(e))
    return null;
  t = t.toLowerCase();
  const r = Object.keys(e);
  let n = r.length, s;
  for (; n-- > 0; )
    if (s = r[n], t === s.toLowerCase())
      return s;
  return null;
}
const D = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, Be = (e) => !M(e) && e !== D;
function ae() {
  const { caseless: e } = Be(this) && this || {}, t = {}, r = (n, s) => {
    const i = e && De(t, s) || s;
    W(t[i]) && W(n) ? t[i] = ae(t[i], n) : W(n) ? t[i] = ae({}, n) : q(n) ? t[i] = n.slice() : t[i] = n;
  };
  for (let n = 0, s = arguments.length; n < s; n++)
    arguments[n] && v(arguments[n], r);
  return t;
}
const wt = (e, t, r, { allOwnKeys: n } = {}) => (v(t, (s, i) => {
  r && A(s) ? e[i] = ke(s, r) : e[i] = s;
}, { allOwnKeys: n }), e), Et = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), gt = (e, t, r, n) => {
  e.prototype = Object.create(t.prototype, n), e.prototype.constructor = e, Object.defineProperty(e, "super", {
    value: t.prototype
  }), r && Object.assign(e.prototype, r);
}, Rt = (e, t, r, n) => {
  let s, i, o;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), i = s.length; i-- > 0; )
      o = s[i], (!n || n(o, e, t)) && !c[o] && (t[o] = e[o], c[o] = !0);
    e = r !== !1 && pe(e);
  } while (e && (!r || r(e, t)) && e !== Object.prototype);
  return t;
}, St = (e, t, r) => {
  e = String(e), (r === void 0 || r > e.length) && (r = e.length), r -= t.length;
  const n = e.indexOf(t, r);
  return n !== -1 && n === r;
}, Ot = (e) => {
  if (!e) return null;
  if (q(e)) return e;
  let t = e.length;
  if (!Ue(t)) return null;
  const r = new Array(t);
  for (; t-- > 0; )
    r[t] = e[t];
  return r;
}, Tt = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && pe(Uint8Array)), At = (e, t) => {
  const n = (e && e[Z]).call(e);
  let s;
  for (; (s = n.next()) && !s.done; ) {
    const i = s.value;
    t.call(e, i[0], i[1]);
  }
}, xt = (e, t) => {
  let r;
  const n = [];
  for (; (r = e.exec(t)) !== null; )
    n.push(r);
  return n;
}, Ct = N("HTMLFormElement"), Nt = (e) => e.toLowerCase().replace(
  /[-_\s]([a-z\d])(\w*)/g,
  function(r, n, s) {
    return n.toUpperCase() + s;
  }
), be = (({ hasOwnProperty: e }) => (t, r) => e.call(t, r))(Object.prototype), Pt = N("RegExp"), Le = (e, t) => {
  const r = Object.getOwnPropertyDescriptors(e), n = {};
  v(r, (s, i) => {
    let o;
    (o = t(s, i, e)) !== !1 && (n[i] = o || s);
  }), Object.defineProperties(e, n);
}, kt = (e) => {
  Le(e, (t, r) => {
    if (A(e) && ["arguments", "caller", "callee"].indexOf(r) !== -1)
      return !1;
    const n = e[r];
    if (A(n)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + r + "'");
      });
    }
  });
}, Ft = (e, t) => {
  const r = {}, n = (s) => {
    s.forEach((i) => {
      r[i] = !0;
    });
  };
  return q(e) ? n(e) : n(String(e).split(t)), r;
}, _t = () => {
}, Ut = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Dt(e) {
  return !!(e && A(e.append) && e[Fe] === "FormData" && e[Z]);
}
const Bt = (e) => {
  const t = new Array(10), r = (n, s) => {
    if (z(n)) {
      if (t.indexOf(n) >= 0)
        return;
      if ($(n))
        return n;
      if (!("toJSON" in n)) {
        t[s] = n;
        const i = q(n) ? [] : {};
        return v(n, (o, c) => {
          const u = r(o, s + 1);
          !M(u) && (i[c] = u);
        }), t[s] = void 0, i;
      }
    }
    return n;
  };
  return r(e, 0);
}, Lt = N("AsyncFunction"), jt = (e) => e && (z(e) || A(e)) && A(e.then) && A(e.catch), je = ((e, t) => e ? setImmediate : t ? ((r, n) => (D.addEventListener("message", ({ source: s, data: i }) => {
  s === D && i === r && n.length && n.shift()();
}, !1), (s) => {
  n.push(s), D.postMessage(r, "*");
}))(`axios@${Math.random()}`, []) : (r) => setTimeout(r))(
  typeof setImmediate == "function",
  A(D.postMessage)
), qt = typeof queueMicrotask < "u" ? queueMicrotask.bind(D) : typeof process < "u" && process.nextTick || je, It = (e) => e != null && A(e[Z]), a = {
  isArray: q,
  isArrayBuffer: _e,
  isBuffer: $,
  isFormData: ft,
  isArrayBufferView: nt,
  isString: rt,
  isNumber: Ue,
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
  toFiniteNumber: Ut,
  findKey: De,
  global: D,
  isContextDefined: Be,
  isSpecCompliantForm: Dt,
  toJSONObject: Bt,
  isAsyncFn: Lt,
  isThenable: jt,
  setImmediate: je,
  asap: qt,
  isIterable: It
};
function m(e, t, r, n, s) {
  Error.call(this), Error.captureStackTrace ? Error.captureStackTrace(this, this.constructor) : this.stack = new Error().stack, this.message = e, this.name = "AxiosError", t && (this.code = t), r && (this.config = r), n && (this.request = n), s && (this.response = s, this.status = s.status ? s.status : null);
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
m.from = (e, t, r, n, s, i) => {
  const o = Object.create(qe);
  return a.toFlatObject(e, o, function(u) {
    return u !== Error.prototype;
  }, (c) => c !== "isAxiosError"), m.call(o, e.message, t, r, n, s), o.cause = e, o.name = e.name, i && Object.assign(o, i), o;
};
const Ht = null;
function ce(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function He(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function we(e, t, r) {
  return e ? e.concat(t).map(function(s, i) {
    return s = He(s), !r && i ? "[" + s + "]" : s;
  }).join(r ? "." : "") : t;
}
function Mt(e) {
  return a.isArray(e) && !e.some(ce);
}
const $t = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function te(e, t, r) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData(), r = a.toFlatObject(r, {
    metaTokens: !0,
    dots: !1,
    indexes: !1
  }, !1, function(y, h) {
    return !a.isUndefined(h[y]);
  });
  const n = r.metaTokens, s = r.visitor || f, i = r.dots, o = r.indexes, u = (r.Blob || typeof Blob < "u" && Blob) && a.isSpecCompliantForm(t);
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
        y = n ? y : y.slice(0, -2), p = JSON.stringify(p);
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
  return encodeURIComponent(e).replace(/[!'()~]|%20|%00/g, function(n) {
    return t[n];
  });
}
function he(e, t) {
  this._pairs = [], e && te(e, this, t);
}
const Me = he.prototype;
Me.append = function(t, r) {
  this._pairs.push([t, r]);
};
Me.toString = function(t) {
  const r = t ? function(n) {
    return t.call(this, n, Ee);
  } : Ee;
  return this._pairs.map(function(s) {
    return r(s[0]) + "=" + r(s[1]);
  }, "").join("&");
};
function zt(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+").replace(/%5B/gi, "[").replace(/%5D/gi, "]");
}
function $e(e, t, r) {
  if (!t)
    return e;
  const n = r && r.encode || zt;
  a.isFunction(r) && (r = {
    serialize: r
  });
  const s = r && r.serialize;
  let i;
  if (s ? i = s(t, r) : i = a.isURLSearchParams(t) ? t.toString() : new he(t, r).toString(n), i) {
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
  use(t, r, n) {
    return this.handlers.push({
      fulfilled: t,
      rejected: r,
      synchronous: n ? n.synchronous : !1,
      runWhen: n ? n.runWhen : null
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
    a.forEach(this.handlers, function(n) {
      n !== null && t(n);
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
    visitor: function(r, n, s, i) {
      return O.isNode && a.isBuffer(r) ? (this.append(n, r.toString("base64")), !1) : i.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function Yt(e) {
  return a.matchAll(/\w+|\[(\w*)]/g, e).map((t) => t[0] === "[]" ? "" : t[1] || t[0]);
}
function en(e) {
  const t = {}, r = Object.keys(e);
  let n;
  const s = r.length;
  let i;
  for (n = 0; n < s; n++)
    i = r[n], t[i] = e[i];
  return t;
}
function ve(e) {
  function t(r, n, s, i) {
    let o = r[i++];
    if (o === "__proto__") return !0;
    const c = Number.isFinite(+o), u = i >= r.length;
    return o = !o && a.isArray(s) ? s.length : o, u ? (a.hasOwnProp(s, o) ? s[o] = [s[o], n] : s[o] = n, !c) : ((!s[o] || !a.isObject(s[o])) && (s[o] = []), t(r, n, s[o], i) && a.isArray(s[o]) && (s[o] = en(s[o])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const r = {};
    return a.forEachEntry(e, (n, s) => {
      t(Yt(n), s, r, 0);
    }), r;
  }
  return null;
}
function tn(e, t, r) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (n) {
      if (n.name !== "SyntaxError")
        throw n;
    }
  return (r || JSON.stringify)(e);
}
const J = {
  transitional: ze,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [function(t, r) {
    const n = r.getContentType() || "", s = n.indexOf("application/json") > -1, i = a.isObject(t);
    if (i && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
      return s ? JSON.stringify(ve(t)) : t;
    if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
      return t;
    if (a.isArrayBufferView(t))
      return t.buffer;
    if (a.isURLSearchParams(t))
      return r.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
    let c;
    if (i) {
      if (n.indexOf("application/x-www-form-urlencoded") > -1)
        return Zt(t, this.formSerializer).toString();
      if ((c = a.isFileList(t)) || n.indexOf("multipart/form-data") > -1) {
        const u = this.env && this.env.FormData;
        return te(
          c ? { "files[]": t } : t,
          u && new u(),
          this.formSerializer
        );
      }
    }
    return i || s ? (r.setContentType("application/json", !1), tn(t)) : t;
  }],
  transformResponse: [function(t) {
    const r = this.transitional || J.transitional, n = r && r.forcedJSONParsing, s = this.responseType === "json";
    if (a.isResponse(t) || a.isReadableStream(t))
      return t;
    if (t && a.isString(t) && (n && !this.responseType || s)) {
      const o = !(r && r.silentJSONParsing) && s;
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
  let r, n, s;
  return e && e.split(`
`).forEach(function(o) {
    s = o.indexOf(":"), r = o.substring(0, s).trim().toLowerCase(), n = o.substring(s + 1).trim(), !(!r || t[r] && nn[r]) && (r === "set-cookie" ? t[r] ? t[r].push(n) : t[r] = [n] : t[r] = t[r] ? t[r] + ", " + n : n);
  }), t;
}, Re = Symbol("internals");
function H(e) {
  return e && String(e).trim().toLowerCase();
}
function K(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(K) : String(e);
}
function sn(e) {
  const t = /* @__PURE__ */ Object.create(null), r = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let n;
  for (; n = r.exec(e); )
    t[n[1]] = n[2];
  return t;
}
const on = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function se(e, t, r, n, s) {
  if (a.isFunction(n))
    return n.call(this, t, r);
  if (s && (t = r), !!a.isString(t)) {
    if (a.isString(n))
      return t.indexOf(n) !== -1;
    if (a.isRegExp(n))
      return n.test(t);
  }
}
function an(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, r, n) => r.toUpperCase() + n);
}
function cn(e, t) {
  const r = a.toCamelCase(" " + t);
  ["get", "set", "has"].forEach((n) => {
    Object.defineProperty(e, n + r, {
      value: function(s, i, o) {
        return this[n].call(this, t, s, i, o);
      },
      configurable: !0
    });
  });
}
let x = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, r, n) {
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
      o(t, r);
    else if (a.isString(t) && (t = t.trim()) && !on(t))
      o(rn(t), r);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, u, l;
      for (const f of t) {
        if (!a.isArray(f))
          throw TypeError("Object iterator must return a key-value pair");
        c[l = f[0]] = (u = c[l]) ? a.isArray(u) ? [...u, f[1]] : [u, f[1]] : f[1];
      }
      o(c, r);
    } else
      t != null && i(r, t, n);
    return this;
  }
  get(t, r) {
    if (t = H(t), t) {
      const n = a.findKey(this, t);
      if (n) {
        const s = this[n];
        if (!r)
          return s;
        if (r === !0)
          return sn(s);
        if (a.isFunction(r))
          return r.call(this, s, n);
        if (a.isRegExp(r))
          return r.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, r) {
    if (t = H(t), t) {
      const n = a.findKey(this, t);
      return !!(n && this[n] !== void 0 && (!r || se(this, this[n], n, r)));
    }
    return !1;
  }
  delete(t, r) {
    const n = this;
    let s = !1;
    function i(o) {
      if (o = H(o), o) {
        const c = a.findKey(n, o);
        c && (!r || se(n, n[c], c, r)) && (delete n[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(i) : i(t), s;
  }
  clear(t) {
    const r = Object.keys(this);
    let n = r.length, s = !1;
    for (; n--; ) {
      const i = r[n];
      (!t || se(this, this[i], i, t, !0)) && (delete this[i], s = !0);
    }
    return s;
  }
  normalize(t) {
    const r = this, n = {};
    return a.forEach(this, (s, i) => {
      const o = a.findKey(n, i);
      if (o) {
        r[o] = K(s), delete r[i];
        return;
      }
      const c = t ? an(i) : String(i).trim();
      c !== i && delete r[i], r[c] = K(s), n[c] = !0;
    }), this;
  }
  concat(...t) {
    return this.constructor.concat(this, ...t);
  }
  toJSON(t) {
    const r = /* @__PURE__ */ Object.create(null);
    return a.forEach(this, (n, s) => {
      n != null && n !== !1 && (r[s] = t && a.isArray(n) ? n.join(", ") : n);
    }), r;
  }
  [Symbol.iterator]() {
    return Object.entries(this.toJSON())[Symbol.iterator]();
  }
  toString() {
    return Object.entries(this.toJSON()).map(([t, r]) => t + ": " + r).join(`
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
  static concat(t, ...r) {
    const n = new this(t);
    return r.forEach((s) => n.set(s)), n;
  }
  static accessor(t) {
    const n = (this[Re] = this[Re] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function i(o) {
      const c = H(o);
      n[c] || (cn(s, o), n[c] = !0);
    }
    return a.isArray(t) ? t.forEach(i) : i(t), this;
  }
};
x.accessor(["Content-Type", "Content-Length", "Accept", "Accept-Encoding", "User-Agent", "Authorization"]);
a.reduceDescriptors(x.prototype, ({ value: e }, t) => {
  let r = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(n) {
      this[r] = n;
    }
  };
});
a.freezeMethods(x);
function oe(e, t) {
  const r = this || J, n = t || r, s = x.from(n.headers);
  let i = n.data;
  return a.forEach(e, function(c) {
    i = c.call(r, i, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), i;
}
function Je(e) {
  return !!(e && e.__CANCEL__);
}
function I(e, t, r) {
  m.call(this, e ?? "canceled", m.ERR_CANCELED, t, r), this.name = "CanceledError";
}
a.inherits(I, m, {
  __CANCEL__: !0
});
function Ve(e, t, r) {
  const n = r.config.validateStatus;
  !r.status || !n || n(r.status) ? e(r) : t(new m(
    "Request failed with status code " + r.status,
    [m.ERR_BAD_REQUEST, m.ERR_BAD_RESPONSE][Math.floor(r.status / 100) - 4],
    r.config,
    r.request,
    r
  ));
}
function ln(e) {
  const t = /^([-+\w]{1,25})(:?\/\/|:)/.exec(e);
  return t && t[1] || "";
}
function un(e, t) {
  e = e || 10;
  const r = new Array(e), n = new Array(e);
  let s = 0, i = 0, o;
  return t = t !== void 0 ? t : 1e3, function(u) {
    const l = Date.now(), f = n[i];
    o || (o = l), r[s] = u, n[s] = l;
    let d = i, b = 0;
    for (; d !== s; )
      b += r[d++], d = d % e;
    if (s = (s + 1) % e, s === i && (i = (i + 1) % e), l - o < t)
      return;
    const g = f && l - f;
    return g ? Math.round(b * 1e3 / g) : void 0;
  };
}
function fn(e, t) {
  let r = 0, n = 1e3 / t, s, i;
  const o = (l, f = Date.now()) => {
    r = f, s = null, i && (clearTimeout(i), i = null), e(...l);
  };
  return [(...l) => {
    const f = Date.now(), d = f - r;
    d >= n ? o(l, f) : (s = l, i || (i = setTimeout(() => {
      i = null, o(s);
    }, n - d)));
  }, () => s && o(s)];
}
const G = (e, t, r = 3) => {
  let n = 0;
  const s = un(50, 250);
  return fn((i) => {
    const o = i.loaded, c = i.lengthComputable ? i.total : void 0, u = o - n, l = s(u), f = o <= c;
    n = o;
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
  }, r);
}, Se = (e, t) => {
  const r = e != null;
  return [(n) => t[0]({
    lengthComputable: r,
    total: e,
    loaded: n
  }), t[1]];
}, Oe = (e) => (...t) => a.asap(() => e(...t)), dn = O.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (r) => (r = new URL(r, O.origin), e.protocol === r.protocol && e.host === r.host && (t || e.port === r.port)))(
  new URL(O.origin),
  O.navigator && /(msie|trident)/i.test(O.navigator.userAgent)
) : () => !0, pn = O.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(e, t, r, n, s, i) {
      const o = [e + "=" + encodeURIComponent(t)];
      a.isNumber(r) && o.push("expires=" + new Date(r).toGMTString()), a.isString(n) && o.push("path=" + n), a.isString(s) && o.push("domain=" + s), i === !0 && o.push("secure"), document.cookie = o.join("; ");
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
function We(e, t, r) {
  let n = !hn(t);
  return e && (n || r == !1) ? mn(e, t) : t;
}
const Te = (e) => e instanceof x ? { ...e } : e;
function L(e, t) {
  t = t || {};
  const r = {};
  function n(l, f, d, b) {
    return a.isPlainObject(l) && a.isPlainObject(f) ? a.merge.call({ caseless: b }, l, f) : a.isPlainObject(f) ? a.merge({}, f) : a.isArray(f) ? f.slice() : f;
  }
  function s(l, f, d, b) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(l))
        return n(void 0, l, d, b);
    } else return n(l, f, d, b);
  }
  function i(l, f) {
    if (!a.isUndefined(f))
      return n(void 0, f);
  }
  function o(l, f) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(l))
        return n(void 0, l);
    } else return n(void 0, f);
  }
  function c(l, f, d) {
    if (d in t)
      return n(l, f);
    if (d in e)
      return n(void 0, l);
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
    a.isUndefined(b) && d !== c || (r[f] = b);
  }), r;
}
const Ke = (e) => {
  const t = L({}, e);
  let { data: r, withXSRFToken: n, xsrfHeaderName: s, xsrfCookieName: i, headers: o, auth: c } = t;
  t.headers = o = x.from(o), t.url = $e(We(t.baseURL, t.url, t.allowAbsoluteUrls), e.params, e.paramsSerializer), c && o.set(
    "Authorization",
    "Basic " + btoa((c.username || "") + ":" + (c.password ? unescape(encodeURIComponent(c.password)) : ""))
  );
  let u;
  if (a.isFormData(r)) {
    if (O.hasStandardBrowserEnv || O.hasStandardBrowserWebWorkerEnv)
      o.setContentType(void 0);
    else if ((u = o.getContentType()) !== !1) {
      const [l, ...f] = u ? u.split(";").map((d) => d.trim()).filter(Boolean) : [];
      o.setContentType([l || "multipart/form-data", ...f].join("; "));
    }
  }
  if (O.hasStandardBrowserEnv && (n && a.isFunction(n) && (n = n(t)), n || n !== !1 && dn(t.url))) {
    const l = s && i && pn.read(i);
    l && o.set(s, l);
  }
  return t;
}, yn = typeof XMLHttpRequest < "u", bn = yn && function(e) {
  return new Promise(function(r, n) {
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
      Ve(function(U) {
        r(U), y();
      }, function(U) {
        n(U), y();
      }, T), h = null;
    }
    "onloadend" in h ? h.onloadend = w : h.onreadystatechange = function() {
      !h || h.readyState !== 4 || h.status === 0 && !(h.responseURL && h.responseURL.indexOf("file:") === 0) || setTimeout(w);
    }, h.onabort = function() {
      h && (n(new m("Request aborted", m.ECONNABORTED, e, h)), h = null);
    }, h.onerror = function() {
      n(new m("Network Error", m.ERR_NETWORK, e, h)), h = null;
    }, h.ontimeout = function() {
      let k = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const T = s.transitional || ze;
      s.timeoutErrorMessage && (k = s.timeoutErrorMessage), n(new m(
        k,
        T.clarifyTimeoutError ? m.ETIMEDOUT : m.ECONNABORTED,
        e,
        h
      )), h = null;
    }, i === void 0 && o.setContentType(null), "setRequestHeader" in h && a.forEach(o.toJSON(), function(k, T) {
      h.setRequestHeader(T, k);
    }), a.isUndefined(s.withCredentials) || (h.withCredentials = !!s.withCredentials), c && c !== "json" && (h.responseType = s.responseType), l && ([b, p] = G(l, !0), h.addEventListener("progress", b)), u && h.upload && ([d, g] = G(u), h.upload.addEventListener("progress", d), h.upload.addEventListener("loadend", g)), (s.cancelToken || s.signal) && (f = (S) => {
      h && (n(!S || S.type ? new I(null, e, h) : S), h.abort(), h = null);
    }, s.cancelToken && s.cancelToken.subscribe(f), s.signal && (s.signal.aborted ? f() : s.signal.addEventListener("abort", f)));
    const R = ln(s.url);
    if (R && O.protocols.indexOf(R) === -1) {
      n(new m("Unsupported protocol " + R + ":", m.ERR_BAD_REQUEST, e));
      return;
    }
    h.send(i || null);
  });
}, wn = (e, t) => {
  const { length: r } = e = e ? e.filter(Boolean) : [];
  if (t || r) {
    let n = new AbortController(), s;
    const i = function(l) {
      if (!s) {
        s = !0, c();
        const f = l instanceof Error ? l : this.reason;
        n.abort(f instanceof m ? f : new I(f instanceof Error ? f.message : f));
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
    const { signal: u } = n;
    return u.unsubscribe = () => a.asap(c), u;
  }
}, En = function* (e, t) {
  let r = e.byteLength;
  if (r < t) {
    yield e;
    return;
  }
  let n = 0, s;
  for (; n < r; )
    s = n + t, yield e.slice(n, s), n = s;
}, gn = async function* (e, t) {
  for await (const r of Rn(e))
    yield* En(r, t);
}, Rn = async function* (e) {
  if (e[Symbol.asyncIterator]) {
    yield* e;
    return;
  }
  const t = e.getReader();
  try {
    for (; ; ) {
      const { done: r, value: n } = await t.read();
      if (r)
        break;
      yield n;
    }
  } finally {
    await t.cancel();
  }
}, Ae = (e, t, r, n) => {
  const s = gn(e, t);
  let i = 0, o, c = (u) => {
    o || (o = !0, n && n(u));
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
        if (r) {
          let b = i += d;
          r(b);
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
    !Q[t] && (Q[t] = a.isFunction(e[t]) ? (r) => r[t]() : (r, n) => {
      throw new m(`Response type '${t}' is not supported`, m.ERR_NOT_SUPPORT, n);
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
  const r = a.toFiniteNumber(e.getContentLength());
  return r ?? Tn(t);
}, xn = ne && (async (e) => {
  let {
    url: t,
    method: r,
    data: n,
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
    if (u && On && r !== "get" && r !== "head" && (h = await An(f, n)) !== 0) {
      let T = new Request(t, {
        method: "POST",
        body: n,
        duplex: "half"
      }), F;
      if (a.isFormData(n) && (F = T.headers.get("content-type")) && f.setContentType(F), T.body) {
        const [U, V] = Se(
          h,
          G(Oe(u))
        );
        n = Ae(T.body, xe, U, V);
      }
    }
    a.isString(d) || (d = d ? "include" : "omit");
    const w = "credentials" in Request.prototype;
    p = new Request(t, {
      ...b,
      signal: g,
      method: r.toUpperCase(),
      headers: f.normalize().toJSON(),
      body: n,
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
      const F = a.toFiniteNumber(R.headers.get("content-length")), [U, V] = c && Se(
        F,
        G(Oe(c), !0)
      ) || [];
      R = new Response(
        Ae(R.body, xe, U, () => {
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
    let r, n;
    const s = {};
    for (let i = 0; i < t; i++) {
      r = e[i];
      let o;
      if (n = r, !Cn(r) && (n = fe[(o = String(r)).toLowerCase()], n === void 0))
        throw new m(`Unknown adapter '${o}'`);
      if (n)
        break;
      s[o || "#" + i] = n;
    }
    if (!n) {
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
    return n;
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
  ), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), Qe.getAdapter(e.adapter || J.adapter)(e).then(function(n) {
    return ie(e), n.data = oe.call(
      e,
      e.transformResponse,
      n
    ), n.headers = x.from(n.headers), n;
  }, function(n) {
    return Je(n) || (ie(e), n && n.response && (n.response.data = oe.call(
      e,
      e.transformResponse,
      n.response
    ), n.response.headers = x.from(n.response.headers))), Promise.reject(n);
  });
}
const Ze = "1.11.0", re = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  re[e] = function(n) {
    return typeof n === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Pe = {};
re.transitional = function(t, r, n) {
  function s(i, o) {
    return "[Axios v" + Ze + "] Transitional option '" + i + "'" + o + (n ? ". " + n : "");
  }
  return (i, o, c) => {
    if (t === !1)
      throw new m(
        s(o, " has been removed" + (r ? " in " + r : "")),
        m.ERR_DEPRECATED
      );
    return r && !Pe[o] && (Pe[o] = !0, console.warn(
      s(
        o,
        " has been deprecated since v" + r + " and will be removed in the near future"
      )
    )), t ? t(i, o, c) : !0;
  };
};
re.spelling = function(t) {
  return (r, n) => (console.warn(`${n} is likely a misspelling of ${t}`), !0);
};
function Nn(e, t, r) {
  if (typeof e != "object")
    throw new m("options must be an object", m.ERR_BAD_OPTION_VALUE);
  const n = Object.keys(e);
  let s = n.length;
  for (; s-- > 0; ) {
    const i = n[s], o = t[i];
    if (o) {
      const c = e[i], u = c === void 0 || o(c, i, e);
      if (u !== !0)
        throw new m("option " + i + " must be " + u, m.ERR_BAD_OPTION_VALUE);
      continue;
    }
    if (r !== !0)
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
  async request(t, r) {
    try {
      return await this._request(t, r);
    } catch (n) {
      if (n instanceof Error) {
        let s = {};
        Error.captureStackTrace ? Error.captureStackTrace(s) : s = new Error();
        const i = s.stack ? s.stack.replace(/^.+\n/, "") : "";
        try {
          n.stack ? i && !String(n.stack).endsWith(i.replace(/^.+\n.+\n/, "")) && (n.stack += `
` + i) : n.stack = i;
        } catch {
        }
      }
      throw n;
    }
  }
  _request(t, r) {
    typeof t == "string" ? (r = r || {}, r.url = t) : r = t || {}, r = L(this.defaults, r);
    const { transitional: n, paramsSerializer: s, headers: i } = r;
    n !== void 0 && X.assertOptions(n, {
      silentJSONParsing: P.transitional(P.boolean),
      forcedJSONParsing: P.transitional(P.boolean),
      clarifyTimeoutError: P.transitional(P.boolean)
    }, !1), s != null && (a.isFunction(s) ? r.paramsSerializer = {
      serialize: s
    } : X.assertOptions(s, {
      encode: P.function,
      serialize: P.function
    }, !0)), r.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? r.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : r.allowAbsoluteUrls = !0), X.assertOptions(r, {
      baseUrl: P.spelling("baseURL"),
      withXsrfToken: P.spelling("withXSRFToken")
    }, !0), r.method = (r.method || this.defaults.method || "get").toLowerCase();
    let o = i && a.merge(
      i.common,
      i[r.method]
    );
    i && a.forEach(
      ["delete", "get", "head", "post", "put", "patch", "common"],
      (p) => {
        delete i[p];
      }
    ), r.headers = x.concat(o, i);
    const c = [];
    let u = !0;
    this.interceptors.request.forEach(function(y) {
      typeof y.runWhen == "function" && y.runWhen(r) === !1 || (u = u && y.synchronous, c.unshift(y.fulfilled, y.rejected));
    });
    const l = [];
    this.interceptors.response.forEach(function(y) {
      l.push(y.fulfilled, y.rejected);
    });
    let f, d = 0, b;
    if (!u) {
      const p = [Ne.bind(this), void 0];
      for (p.unshift(...c), p.push(...l), b = p.length, f = Promise.resolve(r); d < b; )
        f = f.then(p[d++], p[d++]);
      return f;
    }
    b = c.length;
    let g = r;
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
    const r = We(t.baseURL, t.url, t.allowAbsoluteUrls);
    return $e(r, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  B.prototype[t] = function(r, n) {
    return this.request(L(n || {}, {
      method: t,
      url: r,
      data: (n || {}).data
    }));
  };
});
a.forEach(["post", "put", "patch"], function(t) {
  function r(n) {
    return function(i, o, c) {
      return this.request(L(c || {}, {
        method: t,
        headers: n ? {
          "Content-Type": "multipart/form-data"
        } : {},
        url: i,
        data: o
      }));
    };
  }
  B.prototype[t] = r(), B.prototype[t + "Form"] = r(!0);
});
let Pn = class Ye {
  constructor(t) {
    if (typeof t != "function")
      throw new TypeError("executor must be a function.");
    let r;
    this.promise = new Promise(function(i) {
      r = i;
    });
    const n = this;
    this.promise.then((s) => {
      if (!n._listeners) return;
      let i = n._listeners.length;
      for (; i-- > 0; )
        n._listeners[i](s);
      n._listeners = null;
    }), this.promise.then = (s) => {
      let i;
      const o = new Promise((c) => {
        n.subscribe(c), i = c;
      }).then(s);
      return o.cancel = function() {
        n.unsubscribe(i);
      }, o;
    }, t(function(i, o, c) {
      n.reason || (n.reason = new I(i, o, c), r(n.reason));
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
    const r = this._listeners.indexOf(t);
    r !== -1 && this._listeners.splice(r, 1);
  }
  toAbortSignal() {
    const t = new AbortController(), r = (n) => {
      t.abort(n);
    };
    return this.subscribe(r), t.signal.unsubscribe = () => this.unsubscribe(r), t.signal;
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
  return function(r) {
    return e.apply(null, r);
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
  const t = new B(e), r = ke(B.prototype.request, t);
  return a.extend(r, B.prototype, t, { allOwnKeys: !0 }), a.extend(r, t, null, { allOwnKeys: !0 }), r.create = function(s) {
    return et(L(e, s));
  }, r;
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
function Qn() {
  const e = "csrftoken=", r = decodeURIComponent(document.cookie).split(";");
  for (let n of r)
    if (n = n.trim(), n.indexOf(e) === 0)
      return n.substring(e.length);
  return "";
}
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
function Zn(e, t = {}) {
  const r = _(e), n = C(null), s = C(null), i = C(!0), o = j.get(r, {
    headers: t
  }).then((c) => (s.value = c.data, i.value = !1, { loading: i, backendError: n, responseData: s })).catch((c) => (n.value = c, i.value = !1, { loading: i, backendError: n, responseData: s }));
  return {
    loading: i,
    backendError: n,
    responseData: s,
    then: (c, u) => o.then(c, u)
  };
}
function Yn(e, t, r = {}) {
  const n = _(e), s = C(null), i = C(null), o = C(!0), c = j.post(n, _(t), {
    headers: r
  }).then((u) => (console.log(u.statusText), i.value = u.data, o.value = !1, { loading: o, backendError: s, responseData: i })).catch((u) => (s.value = u, o.value = !1, { loading: o, backendError: s, responseData: i }));
  return {
    loading: o,
    backendError: s,
    responseData: i,
    then: (u, l) => c.then(u, l)
  };
}
function er(e, t, r = {}) {
  const n = _(e), s = C(null), i = _(t), o = C(!0), c = j.put(n, i, {
    headers: r
  }).then((u) => (console.log(u.statusText), o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, l) => c.then(u, l)
  };
}
function tr(e, t, r = {}) {
  const n = _(e), s = C(null), i = _(t), o = C(!0), c = j.patch(n, i, {
    headers: r
  }).then((u) => (o.value = !1, { loading: o, backendError: s })).catch((u) => (console.log(u), s.value = u, o.value = !1, { loading: o, backendError: s }));
  return {
    loading: o,
    backendError: s,
    then: (u, l) => c.then(u, l)
  };
}
function nr(e, t = {}) {
  const r = _(e), n = C(null), s = C(!0), i = j.delete(r, {
    headers: t
  }).then((o) => (s.value = !1, { loading: s, backendError: n })).catch((o) => (console.log(o), n.value = o, s.value = !1, { loading: s, backendError: n }));
  return {
    loading: s,
    backendError: n,
    then: (o, c) => i.then(o, c)
  };
}
export {
  Qn as getCsrfToken,
  nr as useDeleteBackendData,
  Zn as useGetBackendData,
  tr as usePatchBackendData,
  Yn as usePostBackendData,
  er as usePutBackendData
};
