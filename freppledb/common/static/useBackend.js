import { toValue as H, ref as L } from "vue";
function st(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: xt } = Object.prototype, { getPrototypeOf: me } = Object, { iterator: ye, toStringTag: ot } = Symbol, be = /* @__PURE__ */ ((e) => (t) => {
  const r = xt.call(t);
  return e[r] || (e[r] = r.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), F = (e) => (e = e.toLowerCase(), (t) => be(t) === e), Ee = (e) => (t) => typeof t === e, { isArray: Q } = Array, G = Ee("undefined");
function ne(e) {
  return e !== null && !G(e) && e.constructor !== null && !G(e.constructor) && x(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const it = F("ArrayBuffer");
function Nt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && it(e.buffer), t;
}
const Pt = Ee("string"), x = Ee("function"), at = Ee("number"), re = (e) => e !== null && typeof e == "object", Dt = (e) => e === !0 || e === !1, fe = (e) => {
  if (be(e) !== "object")
    return !1;
  const t = me(e);
  return (t === null || t === Object.prototype || Object.getPrototypeOf(t) === null) && !(ot in e) && !(ye in e);
}, Lt = (e) => {
  if (!re(e) || ne(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, Ft = F("Date"), Ut = F("File"), Bt = (e) => !!(e && typeof e.uri < "u"), kt = (e) => e && typeof e.getParts < "u", jt = F("Blob"), qt = F("FileList"), It = (e) => re(e) && x(e.pipe);
function Ht() {
  return typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
}
const ve = Ht(), Ve = typeof ve.FormData < "u" ? ve.FormData : void 0, Mt = (e) => {
  if (!e) return !1;
  if (Ve && e instanceof Ve) return !0;
  const t = me(e);
  if (!t || t === Object.prototype || !x(e.append)) return !1;
  const r = be(e);
  return r === "formdata" || // detect form-data instance
  r === "object" && x(e.toString) && e.toString() === "[object FormData]";
}, zt = F("URLSearchParams"), [$t, vt, Vt, Jt] = [
  "ReadableStream",
  "Request",
  "Response",
  "Headers"
].map(F), Wt = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function se(e, t, { allOwnKeys: r = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let n, s;
  if (typeof e != "object" && (e = [e]), Q(e))
    for (n = 0, s = e.length; n < s; n++)
      t.call(null, e[n], n, e);
  else {
    if (ne(e))
      return;
    const o = r ? Object.getOwnPropertyNames(e) : Object.keys(e), i = o.length;
    let c;
    for (n = 0; n < i; n++)
      c = o[n], t.call(null, e[c], c, e);
  }
}
function ct(e, t) {
  if (ne(e))
    return null;
  t = t.toLowerCase();
  const r = Object.keys(e);
  let n = r.length, s;
  for (; n-- > 0; )
    if (s = r[n], t === s.toLowerCase())
      return s;
  return null;
}
const v = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, lt = (e) => !G(e) && e !== v;
function xe(...e) {
  const { caseless: t, skipUndefined: r } = lt(this) && this || {}, n = {}, s = (o, i) => {
    if (i === "__proto__" || i === "constructor" || i === "prototype")
      return;
    const c = t && ct(n, i) || i, l = Ne(n, c) ? n[c] : void 0;
    fe(l) && fe(o) ? n[c] = xe(l, o) : fe(o) ? n[c] = xe({}, o) : Q(o) ? n[c] = o.slice() : (!r || !G(o)) && (n[c] = o);
  };
  for (let o = 0, i = e.length; o < i; o++)
    e[o] && se(e[o], s);
  return n;
}
const Kt = (e, t, r, { allOwnKeys: n } = {}) => (se(
  t,
  (s, o) => {
    r && x(s) ? Object.defineProperty(e, o, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot
      // hijack defineProperty's accessor-vs-data resolution.
      __proto__: null,
      value: st(s, r),
      writable: !0,
      enumerable: !0,
      configurable: !0
    }) : Object.defineProperty(e, o, {
      __proto__: null,
      value: s,
      writable: !0,
      enumerable: !0,
      configurable: !0
    });
  },
  { allOwnKeys: n }
), e), Xt = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Gt = (e, t, r, n) => {
  e.prototype = Object.create(t.prototype, n), Object.defineProperty(e.prototype, "constructor", {
    __proto__: null,
    value: e,
    writable: !0,
    enumerable: !1,
    configurable: !0
  }), Object.defineProperty(e, "super", {
    __proto__: null,
    value: t.prototype
  }), r && Object.assign(e.prototype, r);
}, Qt = (e, t, r, n) => {
  let s, o, i;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), o = s.length; o-- > 0; )
      i = s[o], (!n || n(i, e, t)) && !c[i] && (t[i] = e[i], c[i] = !0);
    e = r !== !1 && me(e);
  } while (e && (!r || r(e, t)) && e !== Object.prototype);
  return t;
}, Yt = (e, t, r) => {
  e = String(e), (r === void 0 || r > e.length) && (r = e.length), r -= t.length;
  const n = e.indexOf(t, r);
  return n !== -1 && n === r;
}, Zt = (e) => {
  if (!e) return null;
  if (Q(e)) return e;
  let t = e.length;
  if (!at(t)) return null;
  const r = new Array(t);
  for (; t-- > 0; )
    r[t] = e[t];
  return r;
}, en = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && me(Uint8Array)), tn = (e, t) => {
  const n = (e && e[ye]).call(e);
  let s;
  for (; (s = n.next()) && !s.done; ) {
    const o = s.value;
    t.call(e, o[0], o[1]);
  }
}, nn = (e, t) => {
  let r;
  const n = [];
  for (; (r = e.exec(t)) !== null; )
    n.push(r);
  return n;
}, rn = F("HTMLFormElement"), sn = (e) => e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function(r, n, s) {
  return n.toUpperCase() + s;
}), Ne = (({ hasOwnProperty: e }) => (t, r) => e.call(t, r))(Object.prototype), on = F("RegExp"), ut = (e, t) => {
  const r = Object.getOwnPropertyDescriptors(e), n = {};
  se(r, (s, o) => {
    let i;
    (i = t(s, o, e)) !== !1 && (n[o] = i || s);
  }), Object.defineProperties(e, n);
}, an = (e) => {
  ut(e, (t, r) => {
    if (x(e) && ["arguments", "caller", "callee"].includes(r))
      return !1;
    const n = e[r];
    if (x(n)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + r + "'");
      });
    }
  });
}, cn = (e, t) => {
  const r = {}, n = (s) => {
    s.forEach((o) => {
      r[o] = !0;
    });
  };
  return Q(e) ? n(e) : n(String(e).split(t)), r;
}, ln = () => {
}, un = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function fn(e) {
  return !!(e && x(e.append) && e[ot] === "FormData" && e[ye]);
}
const dn = (e) => {
  const t = /* @__PURE__ */ new WeakSet(), r = (n) => {
    if (re(n)) {
      if (t.has(n))
        return;
      if (ne(n))
        return n;
      if (!("toJSON" in n)) {
        t.add(n);
        const s = Q(n) ? [] : {};
        return se(n, (o, i) => {
          const c = r(o);
          !G(c) && (s[i] = c);
        }), t.delete(n), s;
      }
    }
    return n;
  };
  return r(e);
}, pn = F("AsyncFunction"), hn = (e) => e && (re(e) || x(e)) && x(e.then) && x(e.catch), ft = ((e, t) => e ? setImmediate : t ? ((r, n) => (v.addEventListener(
  "message",
  ({ source: s, data: o }) => {
    s === v && o === r && n.length && n.shift()();
  },
  !1
), (s) => {
  n.push(s), v.postMessage(r, "*");
}))(`axios@${Math.random()}`, []) : (r) => setTimeout(r))(typeof setImmediate == "function", x(v.postMessage)), mn = typeof queueMicrotask < "u" ? queueMicrotask.bind(v) : typeof process < "u" && process.nextTick || ft, yn = (e) => e != null && x(e[ye]), a = {
  isArray: Q,
  isArrayBuffer: it,
  isBuffer: ne,
  isFormData: Mt,
  isArrayBufferView: Nt,
  isString: Pt,
  isNumber: at,
  isBoolean: Dt,
  isObject: re,
  isPlainObject: fe,
  isEmptyObject: Lt,
  isReadableStream: $t,
  isRequest: vt,
  isResponse: Vt,
  isHeaders: Jt,
  isUndefined: G,
  isDate: Ft,
  isFile: Ut,
  isReactNativeBlob: Bt,
  isReactNative: kt,
  isBlob: jt,
  isRegExp: on,
  isFunction: x,
  isStream: It,
  isURLSearchParams: zt,
  isTypedArray: en,
  isFileList: qt,
  forEach: se,
  merge: xe,
  extend: Kt,
  trim: Wt,
  stripBOM: Xt,
  inherits: Gt,
  toFlatObject: Qt,
  kindOf: be,
  kindOfTest: F,
  endsWith: Yt,
  toArray: Zt,
  forEachEntry: tn,
  matchAll: nn,
  isHTMLForm: rn,
  hasOwnProperty: Ne,
  hasOwnProp: Ne,
  // an alias to avoid ESLint no-prototype-builtins detection
  reduceDescriptors: ut,
  freezeMethods: an,
  toObjectSet: cn,
  toCamelCase: sn,
  noop: ln,
  toFiniteNumber: un,
  findKey: ct,
  global: v,
  isContextDefined: lt,
  isSpecCompliantForm: fn,
  toJSONObject: dn,
  isAsyncFn: pn,
  isThenable: hn,
  setImmediate: ft,
  asap: mn,
  isIterable: yn
}, bn = a.toObjectSet([
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
  let r, n, s;
  return e && e.split(`
`).forEach(function(i) {
    s = i.indexOf(":"), r = i.substring(0, s).trim().toLowerCase(), n = i.substring(s + 1).trim(), !(!r || t[r] && bn[r]) && (r === "set-cookie" ? t[r] ? t[r].push(n) : t[r] = [n] : t[r] = t[r] ? t[r] + ", " + n : n);
  }), t;
};
function wn(e) {
  let t = 0, r = e.length;
  for (; t < r; ) {
    const n = e.charCodeAt(t);
    if (n !== 9 && n !== 32)
      break;
    t += 1;
  }
  for (; r > t; ) {
    const n = e.charCodeAt(r - 1);
    if (n !== 9 && n !== 32)
      break;
    r -= 1;
  }
  return t === 0 && r === e.length ? e : e.slice(t, r);
}
const Rn = new RegExp("[\\u0000-\\u0008\\u000a-\\u001f\\u007f]+", "g"), gn = new RegExp("[^\\u0009\\u0020-\\u007e\\u0080-\\u00ff]+", "g");
function Fe(e, t) {
  return a.isArray(e) ? e.map((r) => Fe(r, t)) : wn(String(e).replace(t, ""));
}
const On = (e) => Fe(e, Rn), Sn = (e) => Fe(e, gn);
function dt(e) {
  const t = /* @__PURE__ */ Object.create(null);
  return a.forEach(e.toJSON(), (r, n) => {
    t[n] = Sn(r);
  }), t;
}
const Je = Symbol("internals");
function te(e) {
  return e && String(e).trim().toLowerCase();
}
function de(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(de) : On(String(e));
}
function An(e) {
  const t = /* @__PURE__ */ Object.create(null), r = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let n;
  for (; n = r.exec(e); )
    t[n[1]] = n[2];
  return t;
}
const _n = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function Ae(e, t, r, n, s) {
  if (a.isFunction(n))
    return n.call(this, t, r);
  if (s && (t = r), !!a.isString(t)) {
    if (a.isString(n))
      return t.indexOf(n) !== -1;
    if (a.isRegExp(n))
      return n.test(t);
  }
}
function Tn(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, r, n) => r.toUpperCase() + n);
}
function Cn(e, t) {
  const r = a.toCamelCase(" " + t);
  ["get", "set", "has"].forEach((n) => {
    Object.defineProperty(e, n + r, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: function(s, o, i) {
        return this[n].call(this, t, s, o, i);
      },
      configurable: !0
    });
  });
}
let C = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, r, n) {
    const s = this;
    function o(c, l, u) {
      const f = te(l);
      if (!f)
        throw new Error("header name must be a non-empty string");
      const y = a.findKey(s, f);
      (!y || s[y] === void 0 || u === !0 || u === void 0 && s[y] !== !1) && (s[y || l] = de(c));
    }
    const i = (c, l) => a.forEach(c, (u, f) => o(u, f, l));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      i(t, r);
    else if (a.isString(t) && (t = t.trim()) && !_n(t))
      i(En(t), r);
    else if (a.isObject(t) && a.isIterable(t)) {
      let c = {}, l, u;
      for (const f of t) {
        if (!a.isArray(f))
          throw TypeError("Object iterator must return a key-value pair");
        c[u = f[0]] = (l = c[u]) ? a.isArray(l) ? [...l, f[1]] : [l, f[1]] : f[1];
      }
      i(c, r);
    } else
      t != null && o(r, t, n);
    return this;
  }
  get(t, r) {
    if (t = te(t), t) {
      const n = a.findKey(this, t);
      if (n) {
        const s = this[n];
        if (!r)
          return s;
        if (r === !0)
          return An(s);
        if (a.isFunction(r))
          return r.call(this, s, n);
        if (a.isRegExp(r))
          return r.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, r) {
    if (t = te(t), t) {
      const n = a.findKey(this, t);
      return !!(n && this[n] !== void 0 && (!r || Ae(this, this[n], n, r)));
    }
    return !1;
  }
  delete(t, r) {
    const n = this;
    let s = !1;
    function o(i) {
      if (i = te(i), i) {
        const c = a.findKey(n, i);
        c && (!r || Ae(n, n[c], c, r)) && (delete n[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(o) : o(t), s;
  }
  clear(t) {
    const r = Object.keys(this);
    let n = r.length, s = !1;
    for (; n--; ) {
      const o = r[n];
      (!t || Ae(this, this[o], o, t, !0)) && (delete this[o], s = !0);
    }
    return s;
  }
  normalize(t) {
    const r = this, n = {};
    return a.forEach(this, (s, o) => {
      const i = a.findKey(n, o);
      if (i) {
        r[i] = de(s), delete r[o];
        return;
      }
      const c = t ? Tn(o) : String(o).trim();
      c !== o && delete r[o], r[c] = de(s), n[c] = !0;
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
    const n = (this[Je] = this[Je] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function o(i) {
      const c = te(i);
      n[c] || (Cn(s, i), n[c] = !0);
    }
    return a.isArray(t) ? t.forEach(o) : o(t), this;
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
  let r = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(n) {
      this[r] = n;
    }
  };
});
a.freezeMethods(C);
const xn = "[REDACTED ****]";
function Nn(e) {
  if (a.hasOwnProp(e, "toJSON"))
    return !0;
  let t = Object.getPrototypeOf(e);
  for (; t && t !== Object.prototype; ) {
    if (a.hasOwnProp(t, "toJSON"))
      return !0;
    t = Object.getPrototypeOf(t);
  }
  return !1;
}
function Pn(e, t) {
  const r = new Set(t.map((o) => String(o).toLowerCase())), n = [], s = (o) => {
    if (o === null || typeof o != "object" || a.isBuffer(o)) return o;
    if (n.indexOf(o) !== -1) return;
    o instanceof C && (o = o.toJSON()), n.push(o);
    let i;
    if (a.isArray(o))
      i = [], o.forEach((c, l) => {
        const u = s(c);
        a.isUndefined(u) || (i[l] = u);
      });
    else {
      if (!a.isPlainObject(o) && Nn(o))
        return n.pop(), o;
      i = /* @__PURE__ */ Object.create(null);
      for (const [c, l] of Object.entries(o)) {
        const u = r.has(c.toLowerCase()) ? xn : s(l);
        a.isUndefined(u) || (i[c] = u);
      }
    }
    return n.pop(), i;
  };
  return s(e);
}
let p = class pt extends Error {
  static from(t, r, n, s, o, i) {
    const c = new pt(t.message, r || t.code, n, s, o);
    return c.cause = t, c.name = t.name, t.status != null && c.status == null && (c.status = t.status), i && Object.assign(c, i), c;
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
  constructor(t, r, n, s, o) {
    super(t), Object.defineProperty(this, "message", {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: t,
      enumerable: !0,
      writable: !0,
      configurable: !0
    }), this.name = "AxiosError", this.isAxiosError = !0, r && (this.code = r), n && (this.config = n), s && (this.request = s), o && (this.response = o, this.status = o.status);
  }
  toJSON() {
    const t = this.config, r = t && a.hasOwnProp(t, "redact") ? t.redact : void 0, n = a.isArray(r) && r.length > 0 ? Pn(t, r) : a.toJSONObject(t);
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
      config: n,
      code: this.code,
      status: this.status
    };
  }
};
p.ERR_BAD_OPTION_VALUE = "ERR_BAD_OPTION_VALUE";
p.ERR_BAD_OPTION = "ERR_BAD_OPTION";
p.ECONNABORTED = "ECONNABORTED";
p.ETIMEDOUT = "ETIMEDOUT";
p.ECONNREFUSED = "ECONNREFUSED";
p.ERR_NETWORK = "ERR_NETWORK";
p.ERR_FR_TOO_MANY_REDIRECTS = "ERR_FR_TOO_MANY_REDIRECTS";
p.ERR_DEPRECATED = "ERR_DEPRECATED";
p.ERR_BAD_RESPONSE = "ERR_BAD_RESPONSE";
p.ERR_BAD_REQUEST = "ERR_BAD_REQUEST";
p.ERR_CANCELED = "ERR_CANCELED";
p.ERR_NOT_SUPPORT = "ERR_NOT_SUPPORT";
p.ERR_INVALID_URL = "ERR_INVALID_URL";
p.ERR_FORM_DATA_DEPTH_EXCEEDED = "ERR_FORM_DATA_DEPTH_EXCEEDED";
const Dn = null;
function Pe(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function ht(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function _e(e, t, r) {
  return e ? e.concat(t).map(function(s, o) {
    return s = ht(s), !r && o ? "[" + s + "]" : s;
  }).join(r ? "." : "") : t;
}
function Ln(e) {
  return a.isArray(e) && !e.some(Pe);
}
const Fn = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function we(e, t, r) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData(), r = a.toFlatObject(
    r,
    {
      metaTokens: !0,
      dots: !1,
      indexes: !1
    },
    !1,
    function(d, m) {
      return !a.isUndefined(m[d]);
    }
  );
  const n = r.metaTokens, s = r.visitor || y, o = r.dots, i = r.indexes, c = r.Blob || typeof Blob < "u" && Blob, l = r.maxDepth === void 0 ? 100 : r.maxDepth, u = c && a.isSpecCompliantForm(t);
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function f(h) {
    if (h === null) return "";
    if (a.isDate(h))
      return h.toISOString();
    if (a.isBoolean(h))
      return h.toString();
    if (!u && a.isBlob(h))
      throw new p("Blob is not supported. Use a Buffer instead.");
    return a.isArrayBuffer(h) || a.isTypedArray(h) ? u && typeof Blob == "function" ? new Blob([h]) : Buffer.from(h) : h;
  }
  function y(h, d, m) {
    let O = h;
    if (a.isReactNative(t) && a.isReactNativeBlob(h))
      return t.append(_e(m, d, o), f(h)), !1;
    if (h && !m && typeof h == "object") {
      if (a.endsWith(d, "{}"))
        d = n ? d : d.slice(0, -2), h = JSON.stringify(h);
      else if (a.isArray(h) && Ln(h) || (a.isFileList(h) || a.endsWith(d, "[]")) && (O = a.toArray(h)))
        return d = ht(d), O.forEach(function(R, N) {
          !(a.isUndefined(R) || R === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            i === !0 ? _e([d], N, o) : i === null ? d : d + "[]",
            f(R)
          );
        }), !1;
    }
    return Pe(h) ? !0 : (t.append(_e(m, d, o), f(h)), !1);
  }
  const w = [], b = Object.assign(Fn, {
    defaultVisitor: y,
    convertValue: f,
    isVisitable: Pe
  });
  function E(h, d, m = 0) {
    if (!a.isUndefined(h)) {
      if (m > l)
        throw new p(
          "Object is too deeply nested (" + m + " levels). Max depth: " + l,
          p.ERR_FORM_DATA_DEPTH_EXCEEDED
        );
      if (w.indexOf(h) !== -1)
        throw Error("Circular reference detected in " + d.join("."));
      w.push(h), a.forEach(h, function(g, R) {
        (!(a.isUndefined(g) || g === null) && s.call(t, g, a.isString(R) ? R.trim() : R, d, b)) === !0 && E(g, d ? d.concat(R) : [R], m + 1);
      }), w.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return E(e), t;
}
function We(e) {
  const t = {
    "!": "%21",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "~": "%7E",
    "%20": "+"
  };
  return encodeURIComponent(e).replace(/[!'()~]|%20/g, function(n) {
    return t[n];
  });
}
function Ue(e, t) {
  this._pairs = [], e && we(e, this, t);
}
const mt = Ue.prototype;
mt.append = function(t, r) {
  this._pairs.push([t, r]);
};
mt.toString = function(t) {
  const r = t ? function(n) {
    return t.call(this, n, We);
  } : We;
  return this._pairs.map(function(s) {
    return r(s[0]) + "=" + r(s[1]);
  }, "").join("&");
};
function Un(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function yt(e, t, r) {
  if (!t)
    return e;
  const n = r && r.encode || Un, s = a.isFunction(r) ? {
    serialize: r
  } : r, o = s && s.serialize;
  let i;
  if (o ? i = o(t, s) : i = a.isURLSearchParams(t) ? t.toString() : new Ue(t, s).toString(n), i) {
    const c = e.indexOf("#");
    c !== -1 && (e = e.slice(0, c)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
class Ke {
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
    a.forEach(this.handlers, function(n) {
      n !== null && t(n);
    });
  }
}
const Be = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1,
  legacyInterceptorReqResOrdering: !0
}, Bn = typeof URLSearchParams < "u" ? URLSearchParams : Ue, kn = typeof FormData < "u" ? FormData : null, jn = typeof Blob < "u" ? Blob : null, qn = {
  isBrowser: !0,
  classes: {
    URLSearchParams: Bn,
    FormData: kn,
    Blob: jn
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, ke = typeof window < "u" && typeof document < "u", De = typeof navigator == "object" && navigator || void 0, In = ke && (!De || ["ReactNative", "NativeScript", "NS"].indexOf(De.product) < 0), Hn = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", Mn = ke && window.location.href || "http://localhost", zn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: ke,
  hasStandardBrowserEnv: In,
  hasStandardBrowserWebWorkerEnv: Hn,
  navigator: De,
  origin: Mn
}, Symbol.toStringTag, { value: "Module" })), T = {
  ...zn,
  ...qn
};
function $n(e, t) {
  return we(e, new T.classes.URLSearchParams(), {
    visitor: function(r, n, s, o) {
      return T.isNode && a.isBuffer(r) ? (this.append(n, r.toString("base64")), !1) : o.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
function vn(e) {
  return a.matchAll(/\w+|\[(\w*)]/g, e).map((t) => t[0] === "[]" ? "" : t[1] || t[0]);
}
function Vn(e) {
  const t = {}, r = Object.keys(e);
  let n;
  const s = r.length;
  let o;
  for (n = 0; n < s; n++)
    o = r[n], t[o] = e[o];
  return t;
}
function bt(e) {
  function t(r, n, s, o) {
    let i = r[o++];
    if (i === "__proto__") return !0;
    const c = Number.isFinite(+i), l = o >= r.length;
    return i = !i && a.isArray(s) ? s.length : i, l ? (a.hasOwnProp(s, i) ? s[i] = a.isArray(s[i]) ? s[i].concat(n) : [s[i], n] : s[i] = n, !c) : ((!a.hasOwnProp(s, i) || !a.isObject(s[i])) && (s[i] = []), t(r, n, s[i], o) && a.isArray(s[i]) && (s[i] = Vn(s[i])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const r = {};
    return a.forEachEntry(e, (n, s) => {
      t(vn(n), s, r, 0);
    }), r;
  }
  return null;
}
const X = (e, t) => e != null && a.hasOwnProp(e, t) ? e[t] : void 0;
function Jn(e, t, r) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (n) {
      if (n.name !== "SyntaxError")
        throw n;
    }
  return (r || JSON.stringify)(e);
}
const oe = {
  transitional: Be,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [
    function(t, r) {
      const n = r.getContentType() || "", s = n.indexOf("application/json") > -1, o = a.isObject(t);
      if (o && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
        return s ? JSON.stringify(bt(t)) : t;
      if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
        return t;
      if (a.isArrayBufferView(t))
        return t.buffer;
      if (a.isURLSearchParams(t))
        return r.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
      let c;
      if (o) {
        const l = X(this, "formSerializer");
        if (n.indexOf("application/x-www-form-urlencoded") > -1)
          return $n(t, l).toString();
        if ((c = a.isFileList(t)) || n.indexOf("multipart/form-data") > -1) {
          const u = X(this, "env"), f = u && u.FormData;
          return we(
            c ? { "files[]": t } : t,
            f && new f(),
            l
          );
        }
      }
      return o || s ? (r.setContentType("application/json", !1), Jn(t)) : t;
    }
  ],
  transformResponse: [
    function(t) {
      const r = X(this, "transitional") || oe.transitional, n = r && r.forcedJSONParsing, s = X(this, "responseType"), o = s === "json";
      if (a.isResponse(t) || a.isReadableStream(t))
        return t;
      if (t && a.isString(t) && (n && !s || o)) {
        const c = !(r && r.silentJSONParsing) && o;
        try {
          return JSON.parse(t, X(this, "parseReviver"));
        } catch (l) {
          if (c)
            throw l.name === "SyntaxError" ? p.from(l, p.ERR_BAD_RESPONSE, this, null, X(this, "response")) : l;
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
    FormData: T.classes.FormData,
    Blob: T.classes.Blob
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
a.forEach(["delete", "get", "head", "post", "put", "patch", "query"], (e) => {
  oe.headers[e] = {};
});
function Te(e, t) {
  const r = this || oe, n = t || r, s = C.from(n.headers);
  let o = n.data;
  return a.forEach(e, function(c) {
    o = c.call(r, o, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), o;
}
function Et(e) {
  return !!(e && e.__CANCEL__);
}
let ie = class extends p {
  /**
   * A `CanceledError` is an object that is thrown when an operation is canceled.
   *
   * @param {string=} message The message.
   * @param {Object=} config The config.
   * @param {Object=} request The request.
   *
   * @returns {CanceledError} The created error.
   */
  constructor(t, r, n) {
    super(t ?? "canceled", p.ERR_CANCELED, r, n), this.name = "CanceledError", this.__CANCEL__ = !0;
  }
};
function wt(e, t, r) {
  const n = r.config.validateStatus;
  !r.status || !n || n(r.status) ? e(r) : t(new p(
    "Request failed with status code " + r.status,
    r.status >= 400 && r.status < 500 ? p.ERR_BAD_REQUEST : p.ERR_BAD_RESPONSE,
    r.config,
    r.request,
    r
  ));
}
function Wn(e) {
  const t = /^([-+\w]{1,25}):(?:\/\/)?/.exec(e);
  return t && t[1] || "";
}
function Kn(e, t) {
  e = e || 10;
  const r = new Array(e), n = new Array(e);
  let s = 0, o = 0, i;
  return t = t !== void 0 ? t : 1e3, function(l) {
    const u = Date.now(), f = n[o];
    i || (i = u), r[s] = l, n[s] = u;
    let y = o, w = 0;
    for (; y !== s; )
      w += r[y++], y = y % e;
    if (s = (s + 1) % e, s === o && (o = (o + 1) % e), u - i < t)
      return;
    const b = f && u - f;
    return b ? Math.round(w * 1e3 / b) : void 0;
  };
}
function Xn(e, t) {
  let r = 0, n = 1e3 / t, s, o;
  const i = (u, f = Date.now()) => {
    r = f, s = null, o && (clearTimeout(o), o = null), e(...u);
  };
  return [(...u) => {
    const f = Date.now(), y = f - r;
    y >= n ? i(u, f) : (s = u, o || (o = setTimeout(() => {
      o = null, i(s);
    }, n - y)));
  }, () => s && i(s)];
}
const he = (e, t, r = 3) => {
  let n = 0;
  const s = Kn(50, 250);
  return Xn((o) => {
    if (!o || typeof o.loaded != "number")
      return;
    const i = o.loaded, c = o.lengthComputable ? o.total : void 0, l = c != null ? Math.min(i, c) : i, u = Math.max(0, l - n), f = s(u);
    n = Math.max(n, l);
    const y = {
      loaded: l,
      total: c,
      progress: c ? l / c : void 0,
      bytes: u,
      rate: f || void 0,
      estimated: f && c ? (c - l) / f : void 0,
      event: o,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(y);
  }, r);
}, Xe = (e, t) => {
  const r = e != null;
  return [
    (n) => t[0]({
      lengthComputable: r,
      total: e,
      loaded: n
    }),
    t[1]
  ];
}, Ge = (e) => (...t) => a.asap(() => e(...t)), Gn = T.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (r) => (r = new URL(r, T.origin), e.protocol === r.protocol && e.host === r.host && (t || e.port === r.port)))(
  new URL(T.origin),
  T.navigator && /(msie|trident)/i.test(T.navigator.userAgent)
) : () => !0, Qn = T.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(e, t, r, n, s, o, i) {
      if (typeof document > "u") return;
      const c = [`${e}=${encodeURIComponent(t)}`];
      a.isNumber(r) && c.push(`expires=${new Date(r).toUTCString()}`), a.isString(n) && c.push(`path=${n}`), a.isString(s) && c.push(`domain=${s}`), o === !0 && c.push("secure"), a.isString(i) && c.push(`SameSite=${i}`), document.cookie = c.join("; ");
    },
    read(e) {
      if (typeof document > "u") return null;
      const t = document.cookie.split(";");
      for (let r = 0; r < t.length; r++) {
        const n = t[r].replace(/^\s+/, ""), s = n.indexOf("=");
        if (s !== -1 && n.slice(0, s) === e)
          return decodeURIComponent(n.slice(s + 1));
      }
      return null;
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
function Yn(e) {
  return typeof e != "string" ? !1 : /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function Zn(e, t) {
  return t ? e.replace(/\/?\/$/, "") + "/" + t.replace(/^\/+/, "") : e;
}
function Rt(e, t, r) {
  let n = !Yn(t);
  return e && (n || r === !1) ? Zn(e, t) : t;
}
const Qe = (e) => e instanceof C ? { ...e } : e;
function J(e, t) {
  t = t || {};
  const r = /* @__PURE__ */ Object.create(null);
  Object.defineProperty(r, "hasOwnProperty", {
    // Null-proto descriptor so a polluted Object.prototype.get cannot turn
    // this data descriptor into an accessor descriptor on the way in.
    __proto__: null,
    value: Object.prototype.hasOwnProperty,
    enumerable: !1,
    writable: !0,
    configurable: !0
  });
  function n(u, f, y, w) {
    return a.isPlainObject(u) && a.isPlainObject(f) ? a.merge.call({ caseless: w }, u, f) : a.isPlainObject(f) ? a.merge({}, f) : a.isArray(f) ? f.slice() : f;
  }
  function s(u, f, y, w) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(u))
        return n(void 0, u, y, w);
    } else return n(u, f, y, w);
  }
  function o(u, f) {
    if (!a.isUndefined(f))
      return n(void 0, f);
  }
  function i(u, f) {
    if (a.isUndefined(f)) {
      if (!a.isUndefined(u))
        return n(void 0, u);
    } else return n(void 0, f);
  }
  function c(u, f, y) {
    if (a.hasOwnProp(t, y))
      return n(u, f);
    if (a.hasOwnProp(e, y))
      return n(void 0, u);
  }
  const l = {
    url: o,
    method: o,
    data: o,
    baseURL: i,
    transformRequest: i,
    transformResponse: i,
    paramsSerializer: i,
    timeout: i,
    timeoutMessage: i,
    withCredentials: i,
    withXSRFToken: i,
    adapter: i,
    responseType: i,
    xsrfCookieName: i,
    xsrfHeaderName: i,
    onUploadProgress: i,
    onDownloadProgress: i,
    decompress: i,
    maxContentLength: i,
    maxBodyLength: i,
    beforeRedirect: i,
    transport: i,
    httpAgent: i,
    httpsAgent: i,
    cancelToken: i,
    socketPath: i,
    allowedSocketPaths: i,
    responseEncoding: i,
    validateStatus: c,
    headers: (u, f, y) => s(Qe(u), Qe(f), y, !0)
  };
  return a.forEach(Object.keys({ ...e, ...t }), function(f) {
    if (f === "__proto__" || f === "constructor" || f === "prototype") return;
    const y = a.hasOwnProp(l, f) ? l[f] : s, w = a.hasOwnProp(e, f) ? e[f] : void 0, b = a.hasOwnProp(t, f) ? t[f] : void 0, E = y(w, b, f);
    a.isUndefined(E) && y !== c || (r[f] = E);
  }), r;
}
const er = ["content-type", "content-length"];
function tr(e, t, r) {
  if (r !== "content-only") {
    e.set(t);
    return;
  }
  Object.entries(t).forEach(([n, s]) => {
    er.includes(n.toLowerCase()) && e.set(n, s);
  });
}
const nr = (e) => encodeURIComponent(e).replace(
  /%([0-9A-F]{2})/gi,
  (t, r) => String.fromCharCode(parseInt(r, 16))
), gt = (e) => {
  const t = J({}, e), r = (w) => a.hasOwnProp(t, w) ? t[w] : void 0, n = r("data");
  let s = r("withXSRFToken");
  const o = r("xsrfHeaderName"), i = r("xsrfCookieName");
  let c = r("headers");
  const l = r("auth"), u = r("baseURL"), f = r("allowAbsoluteUrls"), y = r("url");
  if (t.headers = c = C.from(c), t.url = yt(
    Rt(u, y, f),
    e.params,
    e.paramsSerializer
  ), l && c.set(
    "Authorization",
    "Basic " + btoa((l.username || "") + ":" + (l.password ? nr(l.password) : ""))
  ), a.isFormData(n) && (T.hasStandardBrowserEnv || T.hasStandardBrowserWebWorkerEnv ? c.setContentType(void 0) : a.isFunction(n.getHeaders) && tr(c, n.getHeaders(), r("formDataHeaderPolicy"))), T.hasStandardBrowserEnv && (a.isFunction(s) && (s = s(t)), s === !0 || s == null && Gn(t.url))) {
    const b = o && i && Qn.read(i);
    b && c.set(o, b);
  }
  return t;
}, rr = typeof XMLHttpRequest < "u", sr = rr && function(e) {
  return new Promise(function(r, n) {
    const s = gt(e);
    let o = s.data;
    const i = C.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: l, onDownloadProgress: u } = s, f, y, w, b, E;
    function h() {
      b && b(), E && E(), s.cancelToken && s.cancelToken.unsubscribe(f), s.signal && s.signal.removeEventListener("abort", f);
    }
    let d = new XMLHttpRequest();
    d.open(s.method.toUpperCase(), s.url, !0), d.timeout = s.timeout;
    function m() {
      if (!d)
        return;
      const g = C.from(
        "getAllResponseHeaders" in d && d.getAllResponseHeaders()
      ), N = {
        data: !c || c === "text" || c === "json" ? d.responseText : d.response,
        status: d.status,
        statusText: d.statusText,
        headers: g,
        config: e,
        request: d
      };
      wt(
        function(Y) {
          r(Y), h();
        },
        function(Y) {
          n(Y), h();
        },
        N
      ), d = null;
    }
    "onloadend" in d ? d.onloadend = m : d.onreadystatechange = function() {
      !d || d.readyState !== 4 || d.status === 0 && !(d.responseURL && d.responseURL.startsWith("file:")) || setTimeout(m);
    }, d.onabort = function() {
      d && (n(new p("Request aborted", p.ECONNABORTED, e, d)), h(), d = null);
    }, d.onerror = function(R) {
      const N = R && R.message ? R.message : "Network Error", M = new p(N, p.ERR_NETWORK, e, d);
      M.event = R || null, n(M), h(), d = null;
    }, d.ontimeout = function() {
      let R = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const N = s.transitional || Be;
      s.timeoutErrorMessage && (R = s.timeoutErrorMessage), n(
        new p(
          R,
          N.clarifyTimeoutError ? p.ETIMEDOUT : p.ECONNABORTED,
          e,
          d
        )
      ), h(), d = null;
    }, o === void 0 && i.setContentType(null), "setRequestHeader" in d && a.forEach(dt(i), function(R, N) {
      d.setRequestHeader(N, R);
    }), a.isUndefined(s.withCredentials) || (d.withCredentials = !!s.withCredentials), c && c !== "json" && (d.responseType = s.responseType), u && ([w, E] = he(u, !0), d.addEventListener("progress", w)), l && d.upload && ([y, b] = he(l), d.upload.addEventListener("progress", y), d.upload.addEventListener("loadend", b)), (s.cancelToken || s.signal) && (f = (g) => {
      d && (n(!g || g.type ? new ie(null, e, d) : g), d.abort(), h(), d = null);
    }, s.cancelToken && s.cancelToken.subscribe(f), s.signal && (s.signal.aborted ? f() : s.signal.addEventListener("abort", f)));
    const O = Wn(s.url);
    if (O && !T.protocols.includes(O)) {
      n(
        new p(
          "Unsupported protocol " + O + ":",
          p.ERR_BAD_REQUEST,
          e
        )
      );
      return;
    }
    d.send(o || null);
  });
}, or = (e, t) => {
  if (e = e ? e.filter(Boolean) : [], !t && !e.length)
    return;
  const r = new AbortController();
  let n = !1;
  const s = function(l) {
    if (!n) {
      n = !0, i();
      const u = l instanceof Error ? l : this.reason;
      r.abort(
        u instanceof p ? u : new ie(u instanceof Error ? u.message : u)
      );
    }
  };
  let o = t && setTimeout(() => {
    o = null, s(new p(`timeout of ${t}ms exceeded`, p.ETIMEDOUT));
  }, t);
  const i = () => {
    e && (o && clearTimeout(o), o = null, e.forEach((l) => {
      l.unsubscribe ? l.unsubscribe(s) : l.removeEventListener("abort", s);
    }), e = null);
  };
  e.forEach((l) => l.addEventListener("abort", s));
  const { signal: c } = r;
  return c.unsubscribe = () => a.asap(i), c;
}, ir = function* (e, t) {
  let r = e.byteLength;
  if (r < t) {
    yield e;
    return;
  }
  let n = 0, s;
  for (; n < r; )
    s = n + t, yield e.slice(n, s), n = s;
}, ar = async function* (e, t) {
  for await (const r of cr(e))
    yield* ir(r, t);
}, cr = async function* (e) {
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
}, Ye = (e, t, r, n) => {
  const s = ar(e, t);
  let o = 0, i, c = (l) => {
    i || (i = !0, n && n(l));
  };
  return new ReadableStream(
    {
      async pull(l) {
        try {
          const { done: u, value: f } = await s.next();
          if (u) {
            c(), l.close();
            return;
          }
          let y = f.byteLength;
          if (r) {
            let w = o += y;
            r(w);
          }
          l.enqueue(new Uint8Array(f));
        } catch (u) {
          throw c(u), u;
        }
      },
      cancel(l) {
        return c(l), s.return();
      }
    },
    {
      highWaterMark: 2
    }
  );
};
function lr(e) {
  if (!e || typeof e != "string" || !e.startsWith("data:")) return 0;
  const t = e.indexOf(",");
  if (t < 0) return 0;
  const r = e.slice(5, t), n = e.slice(t + 1);
  if (/;base64/i.test(r)) {
    let i = n.length;
    const c = n.length;
    for (let b = 0; b < c; b++)
      if (n.charCodeAt(b) === 37 && b + 2 < c) {
        const E = n.charCodeAt(b + 1), h = n.charCodeAt(b + 2);
        (E >= 48 && E <= 57 || E >= 65 && E <= 70 || E >= 97 && E <= 102) && (h >= 48 && h <= 57 || h >= 65 && h <= 70 || h >= 97 && h <= 102) && (i -= 2, b += 2);
      }
    let l = 0, u = c - 1;
    const f = (b) => b >= 2 && n.charCodeAt(b - 2) === 37 && // '%'
    n.charCodeAt(b - 1) === 51 && // '3'
    (n.charCodeAt(b) === 68 || n.charCodeAt(b) === 100);
    u >= 0 && (n.charCodeAt(u) === 61 ? (l++, u--) : f(u) && (l++, u -= 3)), l === 1 && u >= 0 && (n.charCodeAt(u) === 61 || f(u)) && l++;
    const w = Math.floor(i / 4) * 3 - (l || 0);
    return w > 0 ? w : 0;
  }
  if (typeof Buffer < "u" && typeof Buffer.byteLength == "function")
    return Buffer.byteLength(n, "utf8");
  let o = 0;
  for (let i = 0, c = n.length; i < c; i++) {
    const l = n.charCodeAt(i);
    if (l < 128)
      o += 1;
    else if (l < 2048)
      o += 2;
    else if (l >= 55296 && l <= 56319 && i + 1 < c) {
      const u = n.charCodeAt(i + 1);
      u >= 56320 && u <= 57343 ? (o += 4, i++) : o += 3;
    } else
      o += 3;
  }
  return o;
}
const je = "1.16.1", Ze = 64 * 1024, { isFunction: ue } = a, et = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, ur = (e) => {
  const t = a.global !== void 0 && a.global !== null ? a.global : globalThis, { ReadableStream: r, TextEncoder: n } = t;
  e = a.merge.call(
    {
      skipUndefined: !0
    },
    {
      Request: t.Request,
      Response: t.Response
    },
    e
  );
  const { fetch: s, Request: o, Response: i } = e, c = s ? ue(s) : typeof fetch == "function", l = ue(o), u = ue(i);
  if (!c)
    return !1;
  const f = c && ue(r), y = c && (typeof n == "function" ? /* @__PURE__ */ ((m) => (O) => m.encode(O))(new n()) : async (m) => new Uint8Array(await new o(m).arrayBuffer())), w = l && f && et(() => {
    let m = !1;
    const O = new o(T.origin, {
      body: new r(),
      method: "POST",
      get duplex() {
        return m = !0, "half";
      }
    }), g = O.headers.has("Content-Type");
    return O.body != null && O.body.cancel(), m && !g;
  }), b = u && f && et(() => a.isReadableStream(new i("").body)), E = {
    stream: b && ((m) => m.body)
  };
  c && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((m) => {
    !E[m] && (E[m] = (O, g) => {
      let R = O && O[m];
      if (R)
        return R.call(O);
      throw new p(
        `Response type '${m}' is not supported`,
        p.ERR_NOT_SUPPORT,
        g
      );
    });
  });
  const h = async (m) => {
    if (m == null)
      return 0;
    if (a.isBlob(m))
      return m.size;
    if (a.isSpecCompliantForm(m))
      return (await new o(T.origin, {
        method: "POST",
        body: m
      }).arrayBuffer()).byteLength;
    if (a.isArrayBufferView(m) || a.isArrayBuffer(m))
      return m.byteLength;
    if (a.isURLSearchParams(m) && (m = m + ""), a.isString(m))
      return (await y(m)).byteLength;
  }, d = async (m, O) => {
    const g = a.toFiniteNumber(m.getContentLength());
    return g ?? h(O);
  };
  return async (m) => {
    let {
      url: O,
      method: g,
      data: R,
      signal: N,
      cancelToken: M,
      timeout: Y,
      onDownloadProgress: ge,
      onUploadProgress: Ie,
      responseType: j,
      headers: z,
      withCredentials: ae = "same-origin",
      fetchOptions: He,
      maxContentLength: U,
      maxBodyLength: Oe
    } = gt(m);
    const Z = a.isNumber(U) && U > -1, Tt = a.isNumber(Oe) && Oe > -1;
    let Me = s || fetch;
    j = j ? (j + "").toLowerCase() : "text";
    let q = or(
      [N, M && M.toAbortSignal()],
      Y
    ), P = null;
    const $ = q && q.unsubscribe && (() => {
      q.unsubscribe();
    });
    let ze;
    try {
      if (Z && typeof O == "string" && O.startsWith("data:") && lr(O) > U)
        throw new p(
          "maxContentLength size of " + U + " exceeded",
          p.ERR_BAD_RESPONSE,
          m,
          P
        );
      if (Tt && g !== "get" && g !== "head") {
        const S = await d(z, R);
        if (typeof S == "number" && isFinite(S) && S > Oe)
          throw new p(
            "Request body larger than maxBodyLength limit",
            p.ERR_BAD_REQUEST,
            m,
            P
          );
      }
      if (Ie && w && g !== "get" && g !== "head" && (ze = await d(z, R)) !== 0) {
        let S = new o(O, {
          method: "POST",
          body: R,
          duplex: "half"
        }), K;
        if (a.isFormData(R) && (K = S.headers.get("content-type")) && z.setContentType(K), S.body) {
          const [ce, le] = Xe(
            ze,
            he(Ge(Ie))
          );
          R = Ye(S.body, Ze, ce, le);
        }
      }
      a.isString(ae) || (ae = ae ? "include" : "omit");
      const _ = l && "credentials" in o.prototype;
      if (a.isFormData(R)) {
        const S = z.getContentType();
        S && /^multipart\/form-data/i.test(S) && !/boundary=/i.test(S) && z.delete("content-type");
      }
      z.set("User-Agent", "axios/" + je, !1);
      const I = {
        ...He,
        signal: q,
        method: g.toUpperCase(),
        headers: dt(z.normalize()),
        body: R,
        duplex: "half",
        credentials: _ ? ae : void 0
      };
      P = l && new o(O, I);
      let B = await (l ? Me(P, He) : Me(O, I));
      if (Z) {
        const S = a.toFiniteNumber(B.headers.get("content-length"));
        if (S != null && S > U)
          throw new p(
            "maxContentLength size of " + U + " exceeded",
            p.ERR_BAD_RESPONSE,
            m,
            P
          );
      }
      const Se = b && (j === "stream" || j === "response");
      if (b && B.body && (ge || Z || Se && $)) {
        const S = {};
        ["status", "statusText", "headers"].forEach((ee) => {
          S[ee] = B[ee];
        });
        const K = a.toFiniteNumber(B.headers.get("content-length")), [ce, le] = ge && Xe(
          K,
          he(Ge(ge), !0)
        ) || [];
        let $e = 0;
        const Ct = (ee) => {
          if (Z && ($e = ee, $e > U))
            throw new p(
              "maxContentLength size of " + U + " exceeded",
              p.ERR_BAD_RESPONSE,
              m,
              P
            );
          ce && ce(ee);
        };
        B = new i(
          Ye(B.body, Ze, Ct, () => {
            le && le(), $ && $();
          }),
          S
        );
      }
      j = j || "text";
      let k = await E[a.findKey(E, j) || "text"](
        B,
        m
      );
      if (Z && !b && !Se) {
        let S;
        if (k != null && (typeof k.byteLength == "number" ? S = k.byteLength : typeof k.size == "number" ? S = k.size : typeof k == "string" && (S = typeof n == "function" ? new n().encode(k).byteLength : k.length)), typeof S == "number" && S > U)
          throw new p(
            "maxContentLength size of " + U + " exceeded",
            p.ERR_BAD_RESPONSE,
            m,
            P
          );
      }
      return !Se && $ && $(), await new Promise((S, K) => {
        wt(S, K, {
          data: k,
          headers: C.from(B.headers),
          status: B.status,
          statusText: B.statusText,
          config: m,
          request: P
        });
      });
    } catch (_) {
      if ($ && $(), q && q.aborted && q.reason instanceof p) {
        const I = q.reason;
        throw I.config = m, P && (I.request = P), _ !== I && (I.cause = _), I;
      }
      throw _ && _.name === "TypeError" && /Load failed|fetch/i.test(_.message) ? Object.assign(
        new p(
          "Network Error",
          p.ERR_NETWORK,
          m,
          P,
          _ && _.response
        ),
        {
          cause: _.cause || _
        }
      ) : p.from(_, _ && _.code, m, P, _ && _.response);
    }
  };
}, fr = /* @__PURE__ */ new Map(), Ot = (e) => {
  let t = e && e.env || {};
  const { fetch: r, Request: n, Response: s } = t, o = [n, s, r];
  let i = o.length, c = i, l, u, f = fr;
  for (; c--; )
    l = o[c], u = f.get(l), u === void 0 && f.set(l, u = c ? /* @__PURE__ */ new Map() : ur(t)), f = u;
  return u;
};
Ot();
const qe = {
  http: Dn,
  xhr: sr,
  fetch: {
    get: Ot
  }
};
a.forEach(qe, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { __proto__: null, value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { __proto__: null, value: t });
  }
});
const tt = (e) => `- ${e}`, dr = (e) => a.isFunction(e) || e === null || e === !1;
function pr(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: r } = e;
  let n, s;
  const o = {};
  for (let i = 0; i < r; i++) {
    n = e[i];
    let c;
    if (s = n, !dr(n) && (s = qe[(c = String(n)).toLowerCase()], s === void 0))
      throw new p(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    o[c || "#" + i] = s;
  }
  if (!s) {
    const i = Object.entries(o).map(
      ([l, u]) => `adapter ${l} ` + (u === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = r ? i.length > 1 ? `since :
` + i.map(tt).join(`
`) : " " + tt(i[0]) : "as no adapter specified";
    throw new p(
      "There is no suitable adapter to dispatch the request " + c,
      "ERR_NOT_SUPPORT"
    );
  }
  return s;
}
const St = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: pr,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: qe
};
function Ce(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new ie(null, e);
}
function nt(e) {
  return Ce(e), e.headers = C.from(e.headers), e.data = Te.call(e, e.transformRequest), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), St.getAdapter(e.adapter || oe.adapter, e)(e).then(
    function(n) {
      Ce(e), e.response = n;
      try {
        n.data = Te.call(e, e.transformResponse, n);
      } finally {
        delete e.response;
      }
      return n.headers = C.from(n.headers), n;
    },
    function(n) {
      if (!Et(n) && (Ce(e), n && n.response)) {
        e.response = n.response;
        try {
          n.response.data = Te.call(
            e,
            e.transformResponse,
            n.response
          );
        } finally {
          delete e.response;
        }
        n.response.headers = C.from(n.response.headers);
      }
      return Promise.reject(n);
    }
  );
}
const Re = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  Re[e] = function(n) {
    return typeof n === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const rt = {};
Re.transitional = function(t, r, n) {
  function s(o, i) {
    return "[Axios v" + je + "] Transitional option '" + o + "'" + i + (n ? ". " + n : "");
  }
  return (o, i, c) => {
    if (t === !1)
      throw new p(
        s(i, " has been removed" + (r ? " in " + r : "")),
        p.ERR_DEPRECATED
      );
    return r && !rt[i] && (rt[i] = !0, console.warn(
      s(
        i,
        " has been deprecated since v" + r + " and will be removed in the near future"
      )
    )), t ? t(o, i, c) : !0;
  };
};
Re.spelling = function(t) {
  return (r, n) => (console.warn(`${n} is likely a misspelling of ${t}`), !0);
};
function hr(e, t, r) {
  if (typeof e != "object")
    throw new p("options must be an object", p.ERR_BAD_OPTION_VALUE);
  const n = Object.keys(e);
  let s = n.length;
  for (; s-- > 0; ) {
    const o = n[s], i = Object.prototype.hasOwnProperty.call(t, o) ? t[o] : void 0;
    if (i) {
      const c = e[o], l = c === void 0 || i(c, o, e);
      if (l !== !0)
        throw new p(
          "option " + o + " must be " + l,
          p.ERR_BAD_OPTION_VALUE
        );
      continue;
    }
    if (r !== !0)
      throw new p("Unknown option " + o, p.ERR_BAD_OPTION);
  }
}
const pe = {
  assertOptions: hr,
  validators: Re
}, D = pe.validators;
let V = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new Ke(),
      response: new Ke()
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
        const o = (() => {
          if (!s.stack)
            return "";
          const i = s.stack.indexOf(`
`);
          return i === -1 ? "" : s.stack.slice(i + 1);
        })();
        try {
          if (!n.stack)
            n.stack = o;
          else if (o) {
            const i = o.indexOf(`
`), c = i === -1 ? -1 : o.indexOf(`
`, i + 1), l = c === -1 ? "" : o.slice(c + 1);
            String(n.stack).endsWith(l) || (n.stack += `
` + o);
          }
        } catch {
        }
      }
      throw n;
    }
  }
  _request(t, r) {
    typeof t == "string" ? (r = r || {}, r.url = t) : r = t || {}, r = J(this.defaults, r);
    const { transitional: n, paramsSerializer: s, headers: o } = r;
    n !== void 0 && pe.assertOptions(
      n,
      {
        silentJSONParsing: D.transitional(D.boolean),
        forcedJSONParsing: D.transitional(D.boolean),
        clarifyTimeoutError: D.transitional(D.boolean),
        legacyInterceptorReqResOrdering: D.transitional(D.boolean)
      },
      !1
    ), s != null && (a.isFunction(s) ? r.paramsSerializer = {
      serialize: s
    } : pe.assertOptions(
      s,
      {
        encode: D.function,
        serialize: D.function
      },
      !0
    )), r.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? r.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : r.allowAbsoluteUrls = !0), pe.assertOptions(
      r,
      {
        baseUrl: D.spelling("baseURL"),
        withXsrfToken: D.spelling("withXSRFToken")
      },
      !0
    ), r.method = (r.method || this.defaults.method || "get").toLowerCase();
    let i = o && a.merge(o.common, o[r.method]);
    o && a.forEach(["delete", "get", "head", "post", "put", "patch", "query", "common"], (E) => {
      delete o[E];
    }), r.headers = C.concat(i, o);
    const c = [];
    let l = !0;
    this.interceptors.request.forEach(function(h) {
      if (typeof h.runWhen == "function" && h.runWhen(r) === !1)
        return;
      l = l && h.synchronous;
      const d = r.transitional || Be;
      d && d.legacyInterceptorReqResOrdering ? c.unshift(h.fulfilled, h.rejected) : c.push(h.fulfilled, h.rejected);
    });
    const u = [];
    this.interceptors.response.forEach(function(h) {
      u.push(h.fulfilled, h.rejected);
    });
    let f, y = 0, w;
    if (!l) {
      const E = [nt.bind(this), void 0];
      for (E.unshift(...c), E.push(...u), w = E.length, f = Promise.resolve(r); y < w; )
        f = f.then(E[y++], E[y++]);
      return f;
    }
    w = c.length;
    let b = r;
    for (; y < w; ) {
      const E = c[y++], h = c[y++];
      try {
        b = E(b);
      } catch (d) {
        h.call(this, d);
        break;
      }
    }
    try {
      f = nt.call(this, b);
    } catch (E) {
      return Promise.reject(E);
    }
    for (y = 0, w = u.length; y < w; )
      f = f.then(u[y++], u[y++]);
    return f;
  }
  getUri(t) {
    t = J(this.defaults, t);
    const r = Rt(t.baseURL, t.url, t.allowAbsoluteUrls);
    return yt(r, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  V.prototype[t] = function(r, n) {
    return this.request(
      J(n || {}, {
        method: t,
        url: r,
        data: (n || {}).data
      })
    );
  };
});
a.forEach(["post", "put", "patch", "query"], function(t) {
  function r(n) {
    return function(o, i, c) {
      return this.request(
        J(c || {}, {
          method: t,
          headers: n ? {
            "Content-Type": "multipart/form-data"
          } : {},
          url: o,
          data: i
        })
      );
    };
  }
  V.prototype[t] = r(), t !== "query" && (V.prototype[t + "Form"] = r(!0));
});
let mr = class At {
  constructor(t) {
    if (typeof t != "function")
      throw new TypeError("executor must be a function.");
    let r;
    this.promise = new Promise(function(o) {
      r = o;
    });
    const n = this;
    this.promise.then((s) => {
      if (!n._listeners) return;
      let o = n._listeners.length;
      for (; o-- > 0; )
        n._listeners[o](s);
      n._listeners = null;
    }), this.promise.then = (s) => {
      let o;
      const i = new Promise((c) => {
        n.subscribe(c), o = c;
      }).then(s);
      return i.cancel = function() {
        n.unsubscribe(o);
      }, i;
    }, t(function(o, i, c) {
      n.reason || (n.reason = new ie(o, i, c), r(n.reason));
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
      token: new At(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function yr(e) {
  return function(r) {
    return e.apply(null, r);
  };
}
function br(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const Le = {
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
Object.entries(Le).forEach(([e, t]) => {
  Le[t] = e;
});
function _t(e) {
  const t = new V(e), r = st(V.prototype.request, t);
  return a.extend(r, V.prototype, t, { allOwnKeys: !0 }), a.extend(r, t, null, { allOwnKeys: !0 }), r.create = function(s) {
    return _t(J(e, s));
  }, r;
}
const A = _t(oe);
A.Axios = V;
A.CanceledError = ie;
A.CancelToken = mr;
A.isCancel = Et;
A.VERSION = je;
A.toFormData = we;
A.AxiosError = p;
A.Cancel = A.CanceledError;
A.all = function(t) {
  return Promise.all(t);
};
A.spread = yr;
A.isAxiosError = br;
A.mergeConfig = J;
A.AxiosHeaders = C;
A.formToJSON = (e) => bt(a.isHTMLForm(e) ? new FormData(e) : e);
A.getAdapter = St.getAdapter;
A.HttpStatusCode = Le;
A.default = A;
const {
  Axios: Or,
  AxiosError: Sr,
  CanceledError: Ar,
  isCancel: _r,
  CancelToken: Tr,
  VERSION: Cr,
  all: xr,
  Cancel: Nr,
  isAxiosError: Pr,
  spread: Dr,
  toFormData: Lr,
  AxiosHeaders: Fr,
  HttpStatusCode: Ur,
  formToJSON: Br,
  getAdapter: kr,
  mergeConfig: jr,
  create: qr
} = A, W = A.create({
  withCredentials: !0,
  timeout: 18e4,
  // Add a timeout of 3 minutes
  headers: {
    "Content-Type": "application/json"
  }
});
function Ir() {
  const e = "csrftoken=", r = decodeURIComponent(document.cookie).split(";");
  for (let n of r)
    if (n = n.trim(), n.indexOf(e) === 0)
      return n.substring(e.length);
  return "";
}
W.interceptors.request.use(
  (e) => e,
  (e) => Promise.reject(e)
);
W.interceptors.response.use(
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
function Hr(e, t = {}) {
  const r = H(e), n = L(null), s = L(null), o = L(!0), i = W.get(r, {
    headers: t
  }).then((c) => (s.value = c.data, o.value = !1, { loading: o, backendError: n, responseData: s })).catch((c) => (n.value = c, o.value = !1, { loading: o, backendError: n, responseData: s }));
  return {
    loading: o,
    backendError: n,
    responseData: s,
    then: (c, l) => i.then(c, l)
  };
}
function Mr(e, t, r = {}) {
  const n = H(e), s = L(null), o = L(null), i = L(!0), c = W.post(n, H(t), {
    headers: r
  }).then((l) => (o.value = l.data, i.value = !1, { loading: i, backendError: s, responseData: o })).catch((l) => (s.value = l, i.value = !1, { loading: i, backendError: s, responseData: o }));
  return {
    loading: i,
    backendError: s,
    responseData: o,
    then: (l, u) => c.then(l, u)
  };
}
function zr(e, t, r = {}) {
  const n = H(e), s = L(null), o = H(t), i = L(!0), c = W.put(n, o, {
    headers: r
  }).then((l) => (console.log(l.statusText), i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, u) => c.then(l, u)
  };
}
function $r(e, t, r = {}) {
  const n = H(e), s = L(null), o = H(t), i = L(!0), c = W.patch(n, o, {
    headers: r
  }).then((l) => (i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, u) => c.then(l, u)
  };
}
function vr(e, t = {}) {
  const r = H(e), n = L(null), s = L(!0), o = W.delete(r, {
    headers: t
  }).then((i) => (s.value = !1, { loading: s, backendError: n })).catch((i) => (console.log(i), n.value = i, s.value = !1, { loading: s, backendError: n }));
  return {
    loading: s,
    backendError: n,
    then: (i, c) => o.then(i, c)
  };
}
export {
  Ir as getCsrfToken,
  vr as useDeleteBackendData,
  Hr as useGetBackendData,
  $r as usePatchBackendData,
  Mr as usePostBackendData,
  zr as usePutBackendData
};
