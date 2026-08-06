import { toValue as V, ref as B } from "vue";
function Rt(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: Xt } = Object.prototype, { getPrototypeOf: ne } = Object, { iterator: ue, toStringTag: gt } = Symbol, ge = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), le = (e, t) => {
  let n = e;
  const r = [];
  for (; n != null && n !== Object.prototype; ) {
    if (r.indexOf(n) !== -1)
      return !1;
    if (r.push(n), ge(n, t))
      return !0;
    n = ne(n);
  }
  return !1;
}, Gt = (e, t) => e != null && le(e, t) ? e[t] : void 0, Me = /* @__PURE__ */ ((e) => (t) => {
  const n = Xt.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), k = (e) => (e = e.toLowerCase(), (t) => Me(t) === e), Ae = (e) => (t) => typeof t === e, { isArray: G } = Array, Q = Ae("undefined");
function re(e) {
  return e !== null && !Q(e) && e.constructor !== null && !Q(e.constructor) && U(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const Ot = k("ArrayBuffer");
function Qt(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && Ot(e.buffer), t;
}
const Zt = Ae("string"), U = Ae("function"), St = Ae("number"), se = (e) => e !== null && typeof e == "object", Yt = (e) => e === !0 || e === !1, we = (e) => {
  if (!se(e))
    return !1;
  const t = ne(e);
  return (t === null || t === Object.prototype || ne(t) === null) && // Treat any genuine (non-Object.prototype-polluted) Symbol.toStringTag or
  // Symbol.iterator as evidence the value is a tagged/iterable type rather
  // than a plain object, while ignoring keys injected onto Object.prototype.
  !le(e, gt) && !le(e, ue);
}, en = (e) => {
  if (!se(e) || re(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, tn = k("Date"), nn = k("File"), rn = (e) => !!(e && typeof e.uri < "u"), sn = (e) => e && typeof e.getParts < "u", on = k("Blob"), an = k("FileList"), cn = k("Set"), ln = (e) => se(e) && U(e.pipe);
function un() {
  return typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
}
const tt = un(), nt = typeof tt.FormData < "u" ? tt.FormData : void 0, fn = (e) => {
  if (!e) return !1;
  if (nt && e instanceof nt) return !0;
  const t = ne(e);
  if (!t || t === Object.prototype || !U(e.append)) return !1;
  const n = Me(e);
  return n === "formdata" || // detect form-data instance
  n === "object" && U(e.toString) && e.toString() === "[object FormData]";
}, dn = k("URLSearchParams"), [pn, hn, mn, yn] = [
  "ReadableStream",
  "Request",
  "Response",
  "Headers"
].map(k), bn = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function fe(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), G(e))
    for (r = 0, s = e.length; r < s; r++)
      t.call(null, e[r], r, e);
  else {
    if (re(e))
      return;
    const o = n ? Object.getOwnPropertyNames(e) : Object.keys(e), i = o.length;
    let c;
    for (r = 0; r < i; r++)
      c = o[r], t.call(null, e[c], c, e);
  }
}
function At(e, t) {
  if (re(e))
    return null;
  t = t.toLowerCase();
  const n = Object.keys(e);
  let r = n.length, s;
  for (; r-- > 0; )
    if (s = n[r], t === s.toLowerCase())
      return s;
  return null;
}
const K = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, _t = (e) => !Q(e) && e !== K;
function je(...e) {
  const { caseless: t, skipUndefined: n } = _t(this) && this || {}, r = {}, s = (o, i) => {
    if (i === "__proto__" || i === "constructor" || i === "prototype")
      return;
    const c = t && typeof i == "string" && At(r, i) || i, l = ge(r, c) ? r[c] : void 0;
    we(l) && we(o) ? r[c] = je(l, o) : we(o) ? r[c] = je({}, o) : G(o) ? r[c] = o.slice() : (!n || !Q(o)) && (r[c] = o);
  };
  for (let o = 0, i = e.length; o < i; o++) {
    const c = e[o];
    if (!c || re(c) || (fe(c, s), typeof c != "object" || G(c)))
      continue;
    const l = Object.getOwnPropertySymbols(c);
    for (let f = 0; f < l.length; f++) {
      const u = l[f];
      Cn.call(c, u) && s(c[u], u);
    }
  }
  return r;
}
const wn = (e, t, n, { allOwnKeys: r } = {}) => (fe(
  t,
  (s, o) => {
    n && U(s) ? Object.defineProperty(e, o, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot
      // hijack defineProperty's accessor-vs-data resolution.
      __proto__: null,
      value: Rt(s, n),
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
  { allOwnKeys: r }
), e), En = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Rn = (e, t, n, r) => {
  e.prototype = Object.create(t.prototype, r), Object.defineProperty(e.prototype, "constructor", {
    __proto__: null,
    value: e,
    writable: !0,
    enumerable: !1,
    configurable: !0
  }), Object.defineProperty(e, "super", {
    __proto__: null,
    value: t.prototype
  }), n && Object.assign(e.prototype, n);
}, gn = (e, t, n, r) => {
  let s, o, i;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), o = s.length; o-- > 0; )
      i = s[o], (!r || r(i, e, t)) && !c[i] && (t[i] = e[i], c[i] = !0);
    e = n !== !1 && ne(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, On = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, Sn = (e) => {
  if (!e) return null;
  if (G(e)) return e;
  let t = e.length;
  if (!St(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, An = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && ne(Uint8Array)), _n = (e, t) => {
  const r = (e && e[ue]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const o = s.value;
    t.call(e, o[0], o[1]);
  }
}, Tn = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, Pn = k("HTMLFormElement"), xn = (e) => e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function(n, r, s) {
  return r.toUpperCase() + s;
}), { propertyIsEnumerable: Cn } = Object.prototype, Nn = k("RegExp"), Tt = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  fe(n, (s, o) => {
    let i;
    (i = t(s, o, e)) !== !1 && (r[o] = i || s);
  }), Object.defineProperties(e, r);
}, Dn = (e) => {
  Tt(e, (t, n) => {
    if (U(e) && ["arguments", "caller", "callee"].includes(n))
      return !1;
    const r = e[n];
    if (U(r)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + n + "'");
      });
    }
  });
}, Un = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((o) => {
      n[o] = !0;
    });
  };
  return G(e) ? r(e) : r(String(e).split(t)), n;
}, Ln = () => {
}, Fn = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Bn(e) {
  return !!(e && U(e.append) && e[gt] === "FormData" && e[ue]);
}
const kn = (e) => {
  const t = /* @__PURE__ */ new WeakSet(), n = (r) => {
    if (se(r)) {
      if (t.has(r))
        return;
      if (re(r))
        return r;
      if (!("toJSON" in r)) {
        t.add(r);
        let s;
        if (cn(r)) {
          s = [];
          for (const o of r) {
            const i = n(o);
            !Q(i) && s.push(i);
          }
        } else
          s = G(r) ? [] : {}, fe(r, (o, i) => {
            const c = n(o);
            !Q(c) && (s[i] = c);
          });
        return t.delete(r), s;
      }
    }
    return r;
  };
  return n(e);
}, jn = k("AsyncFunction"), In = (e) => e && (se(e) || U(e)) && U(e.then) && U(e.catch), Pt = ((e, t) => e ? setImmediate : t ? ((n, r) => (K.addEventListener(
  "message",
  ({ source: s, data: o }) => {
    s === K && o === n && r.length && r.shift()();
  },
  !1
), (s) => {
  r.push(s), K.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(typeof setImmediate == "function", U(K.postMessage)), qn = typeof queueMicrotask < "u" ? queueMicrotask.bind(K) : typeof process < "u" && process.nextTick || Pt, xt = (e) => e != null && U(e[ue]), Hn = (e) => e != null && le(e, ue) && xt(e), a = {
  isArray: G,
  isArrayBuffer: Ot,
  isBuffer: re,
  isFormData: fn,
  isArrayBufferView: Qt,
  isString: Zt,
  isNumber: St,
  isBoolean: Yt,
  isObject: se,
  isPlainObject: we,
  isEmptyObject: en,
  isReadableStream: pn,
  isRequest: hn,
  isResponse: mn,
  isHeaders: yn,
  isUndefined: Q,
  isDate: tn,
  isFile: nn,
  isReactNativeBlob: rn,
  isReactNative: sn,
  isBlob: on,
  isRegExp: Nn,
  isFunction: U,
  isStream: ln,
  isURLSearchParams: dn,
  isTypedArray: An,
  isFileList: an,
  forEach: fe,
  merge: je,
  extend: wn,
  trim: bn,
  stripBOM: En,
  inherits: Rn,
  toFlatObject: gn,
  kindOf: Me,
  kindOfTest: k,
  endsWith: On,
  toArray: Sn,
  forEachEntry: _n,
  matchAll: Tn,
  isHTMLForm: Pn,
  hasOwnProperty: ge,
  hasOwnProp: ge,
  // an alias to avoid ESLint no-prototype-builtins detection
  hasOwnInPrototypeChain: le,
  getSafeProp: Gt,
  reduceDescriptors: Tt,
  freezeMethods: Dn,
  toObjectSet: Un,
  toCamelCase: xn,
  noop: Ln,
  toFiniteNumber: Fn,
  findKey: At,
  global: K,
  isContextDefined: _t,
  isSpecCompliantForm: Bn,
  toJSONObject: kn,
  isAsyncFn: jn,
  isThenable: In,
  setImmediate: Pt,
  asap: qn,
  isIterable: xt,
  isSafeIterable: Hn
}, Mn = a.toObjectSet([
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
]), $n = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(i) {
    s = i.indexOf(":"), n = i.substring(0, s).trim().toLowerCase(), r = i.substring(s + 1).trim();
    const c = a.hasOwnProp(t, n);
    !n || c && a.hasOwnProp(Mn, n) || (n === "set-cookie" ? c ? t[n].push(r) : t[n] = [r] : t[n] = c ? t[n] + ", " + r : r);
  }), t;
};
function zn(e) {
  let t = 0, n = e.length;
  for (; t < n; ) {
    const r = e.charCodeAt(t);
    if (r !== 9 && r !== 32)
      break;
    t += 1;
  }
  for (; n > t; ) {
    const r = e.charCodeAt(n - 1);
    if (r !== 9 && r !== 32)
      break;
    n -= 1;
  }
  return t === 0 && n === e.length ? e : e.slice(t, n);
}
const vn = new RegExp("[\\u0000-\\u0008\\u000a-\\u001f\\u007f]+", "g"), Vn = new RegExp("[^\\u0009\\u0020-\\u007e\\u0080-\\u00ff]+", "g");
function $e(e, t) {
  return a.isArray(e) ? e.map((n) => $e(n, t)) : zn(String(e).replace(t, ""));
}
const Wn = (e) => $e(e, vn), Jn = (e) => $e(e, Vn);
function Ct(e) {
  const t = /* @__PURE__ */ Object.create(null);
  return a.forEach(e.toJSON(), (n, r) => {
    t[r] = Jn(n);
  }), t;
}
const rt = Symbol("internals");
function ce(e) {
  return e && String(e).trim().toLowerCase();
}
function Ee(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(Ee) : Wn(String(e));
}
function Kn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const Xn = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;
function De(e) {
  let t = 0, n = e.length;
  for (; t < n; ) {
    const r = e.charCodeAt(t);
    if (r !== 9 && r !== 32)
      break;
    t += 1;
  }
  for (; n > t; ) {
    const r = e.charCodeAt(n - 1);
    if (r !== 9 && r !== 32)
      break;
    n -= 1;
  }
  return t === 0 && n === e.length ? e : e.slice(t, n);
}
function Gn(e) {
  const t = e.length - 1;
  if (t < 1 || e.charCodeAt(0) !== 34 || e.charCodeAt(t) !== 34)
    return e;
  let n = "";
  for (let r = 1; r < t; r++) {
    const s = e.charCodeAt(r);
    if (s === 34 || s === 92 && (r += 1, r >= t))
      return e;
    n += e[r];
  }
  return n;
}
function Qn(e) {
  const t = /* @__PURE__ */ Object.create(null), n = String(e);
  let r = 0, s = !1, o = !1;
  function i(c) {
    const l = De(n.slice(r, c)), f = l.indexOf("=");
    if (f < 1)
      return;
    const u = De(l.slice(0, f));
    if (!Xn.test(u))
      return;
    const p = u.toLowerCase();
    if (p === "__proto__" || p === "constructor" || p === "prototype")
      return;
    const b = De(l.slice(f + 1));
    t[p] = Gn(b);
  }
  for (let c = 0; c < n.length; c++) {
    const l = n.charCodeAt(c);
    s ? o ? o = !1 : l === 92 ? o = !0 : l === 34 && (s = !1) : l === 34 ? s = !0 : (l === 44 || l === 59) && (i(c), r = c + 1);
  }
  return i(n.length), t;
}
const Zn = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function Ue(e, t, n, r, s) {
  if (a.isFunction(r))
    return r.call(this, t, n);
  if (s && (t = n), !!a.isString(t)) {
    if (a.isString(r))
      return t.indexOf(r) !== -1;
    if (a.isRegExp(r))
      return r.test(t);
  }
}
function Yn(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function er(e, t) {
  const n = a.toCamelCase(" " + t);
  ["get", "set", "has"].forEach((r) => {
    Object.defineProperty(e, r + n, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: function(s, o, i) {
        return this[r].call(this, t, s, o, i);
      },
      configurable: !0
    });
  });
}
let D = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, n, r) {
    const s = this;
    function o(c, l, f) {
      const u = ce(l);
      if (!u)
        return;
      const p = a.findKey(s, u);
      (!p || s[p] === void 0 || f === !0 || f === void 0 && s[p] !== !1) && (s[p || l] = Ee(c));
    }
    const i = (c, l) => a.forEach(c, (f, u) => o(f, u, l));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      i(t, n);
    else if (a.isString(t) && (t = t.trim()) && !Zn(t))
      i($n(t), n);
    else if (a.isObject(t) && a.isSafeIterable(t)) {
      let c = /* @__PURE__ */ Object.create(null), l, f;
      for (const u of t) {
        if (!a.isArray(u))
          throw new TypeError("Object iterator must return a key-value pair");
        f = u[0], a.hasOwnProp(c, f) ? (l = c[f], c[f] = a.isArray(l) ? [...l, u[1]] : [l, u[1]]) : c[f] = u[1];
      }
      i(c, n);
    } else
      t != null && o(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = ce(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return Kn(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = ce(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || Ue(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function o(i) {
      if (i = ce(i), i) {
        const c = a.findKey(r, i);
        c && (!n || Ue(r, r[c], c, n)) && (delete r[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(o) : o(t), s;
  }
  clear(t) {
    const n = Object.keys(this);
    let r = n.length, s = !1;
    for (; r--; ) {
      const o = n[r];
      (!t || Ue(this, this[o], o, t, !0)) && (delete this[o], s = !0);
    }
    return s;
  }
  normalize(t) {
    const n = this, r = {};
    return a.forEach(this, (s, o) => {
      const i = a.findKey(r, o);
      if (i) {
        n[i] = Ee(s), delete n[o];
        return;
      }
      const c = t ? Yn(o) : String(o).trim();
      c !== o && delete n[o], n[c] = Ee(s), r[c] = !0;
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
    const t = this.get("set-cookie");
    return a.isArray(t) ? t : t == null || t === !1 ? [] : [t];
  }
  get [Symbol.toStringTag]() {
    return "AxiosHeaders";
  }
  static from(t) {
    return t instanceof this ? t : new this(t);
  }
  static parseParameters(t) {
    return Qn(t);
  }
  static concat(t, ...n) {
    const r = new this(t);
    return n.forEach((s) => r.set(s)), r;
  }
  static accessor(t) {
    const r = (this[rt] = this[rt] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function o(i) {
      const c = ce(i);
      r[c] || (er(s, i), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(o) : o(t), this;
  }
};
D.accessor([
  "Content-Type",
  "Content-Length",
  "Accept",
  "Accept-Encoding",
  "User-Agent",
  "Authorization"
]);
a.reduceDescriptors(D.prototype, ({ value: e }, t) => {
  let n = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(r) {
      this[n] = r;
    }
  };
});
a.freezeMethods(D);
const Oe = "[REDACTED ****]";
function tr(e) {
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
function nr(e, t) {
  const n = new Set(t.map((o) => String(o).toLowerCase())), r = [], s = (o) => {
    if (o === null || typeof o != "object" || a.isBuffer(o)) return o;
    if (r.indexOf(o) !== -1) return;
    o instanceof D && (o = o.toJSON()), r.push(o);
    let i;
    if (a.isArray(o))
      i = [], o.forEach((c, l) => {
        const f = s(c);
        a.isUndefined(f) || (i[l] = f);
      });
    else {
      if (!a.isPlainObject(o) && tr(o))
        return r.pop(), o;
      i = /* @__PURE__ */ Object.create(null);
      for (const [c, l] of Object.entries(o)) {
        const f = n.has(c.toLowerCase()) ? Oe : s(l);
        a.isUndefined(f) || (i[c] = f);
      }
    }
    return r.pop(), i;
  };
  return s(e);
}
function st(e) {
  try {
    return String(e);
  } catch {
    return "";
  }
}
function rr(e) {
  return e.errors.map((n) => {
    try {
      return n && n.message ? st(n.message) : st(n);
    } catch {
      return "";
    }
  }).filter(Boolean).join("; ") || e.name || "AggregateError";
}
let h = class Nt extends Error {
  static from(t, n, r, s, o, i) {
    let c = t.message;
    !c && a.isArray(t.errors) && t.errors.length && (c = rr(t));
    const l = new Nt(c, n || t.code, r, s, o);
    return Object.defineProperty(l, "cause", {
      __proto__: null,
      value: t,
      writable: !0,
      enumerable: !1,
      configurable: !0
    }), l.name = t.name, t.status != null && l.status == null && (l.status = t.status), i && Object.assign(l, i), l;
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
  constructor(t, n, r, s, o) {
    super(t), Object.defineProperty(this, "message", {
      // Null-proto descriptor so a polluted Object.prototype.get cannot turn
      // this data descriptor into an accessor descriptor on the way in.
      __proto__: null,
      value: t,
      enumerable: !0,
      writable: !0,
      configurable: !0
    }), this.name = "AxiosError", this.isAxiosError = !0, n && (this.code = n), r && (this.config = r), s && (this.request = s), o && (this.response = o, this.status = o.status);
  }
  toJSON() {
    const t = this.config, n = t && a.hasOwnProp(t, "redact") ? t.redact : void 0, r = a.isArray(n) && n.length > 0 ? nr(t, n) : a.toJSONObject(t);
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
      config: r,
      code: this.code,
      status: this.status
    };
  }
};
h.ERR_BAD_OPTION_VALUE = "ERR_BAD_OPTION_VALUE";
h.ERR_BAD_OPTION = "ERR_BAD_OPTION";
h.ECONNABORTED = "ECONNABORTED";
h.ETIMEDOUT = "ETIMEDOUT";
h.ECONNREFUSED = "ECONNREFUSED";
h.ERR_NETWORK = "ERR_NETWORK";
h.ERR_FR_TOO_MANY_REDIRECTS = "ERR_FR_TOO_MANY_REDIRECTS";
h.ERR_DEPRECATED = "ERR_DEPRECATED";
h.ERR_BAD_RESPONSE = "ERR_BAD_RESPONSE";
h.ERR_BAD_REQUEST = "ERR_BAD_REQUEST";
h.ERR_CANCELED = "ERR_CANCELED";
h.ERR_NOT_SUPPORT = "ERR_NOT_SUPPORT";
h.ERR_INVALID_URL = "ERR_INVALID_URL";
h.ERR_FORM_DATA_DEPTH_EXCEEDED = "ERR_FORM_DATA_DEPTH_EXCEEDED";
const sr = null, Dt = 100;
function Ie(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function Ut(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function Le(e, t, n) {
  return e ? e.concat(t).map(function(s, o) {
    return s = Ut(s), !n && o ? "[" + s + "]" : s;
  }).join(n ? "." : "") : t;
}
function or(e) {
  return a.isArray(e) && !e.some(Ie);
}
const ir = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function _e(e, t, n) {
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
    function(y, w) {
      return !a.isUndefined(w[y]);
    }
  );
  const r = n.metaTokens, s = n.visitor || g, o = n.dots, i = n.indexes, c = n.Blob || typeof Blob < "u" && Blob, l = n.maxDepth === void 0 ? Dt : n.maxDepth, f = c && a.isSpecCompliantForm(t), u = [];
  if (!a.isFunction(s))
    throw new TypeError("visitor must be a function");
  function p(d) {
    if (d === null) return "";
    if (a.isDate(d))
      return d.toISOString();
    if (a.isBoolean(d))
      return d.toString();
    if (!f && a.isBlob(d))
      throw new h("Blob is not supported. Use a Buffer instead.");
    if (a.isArrayBuffer(d) || a.isTypedArray(d)) {
      if (f && typeof c == "function")
        return new c([d]);
      throw new h("Blob is not supported. Use a Buffer instead.", h.ERR_NOT_SUPPORT);
    }
    return d;
  }
  function b(d) {
    if (d > l)
      throw new h(
        "Object is too deeply nested (" + d + " levels). Max depth: " + l,
        h.ERR_FORM_DATA_DEPTH_EXCEEDED
      );
  }
  function R(d, y) {
    if (l === 1 / 0)
      return JSON.stringify(d);
    const w = [];
    return JSON.stringify(d, function(C, _) {
      if (!a.isObject(_))
        return _;
      for (; w.length && w[w.length - 1] !== this; )
        w.pop();
      return w.push(_), b(y + w.length - 1), _;
    });
  }
  function g(d, y, w) {
    let O = d;
    if (a.isReactNative(t) && a.isReactNativeBlob(d))
      return t.append(Le(w, y, o), p(d)), !1;
    if (d && !w && typeof d == "object") {
      if (a.endsWith(y, "{}"))
        y = r ? y : y.slice(0, -2), d = R(d, 1);
      else if (a.isArray(d) && or(d) || (a.isFileList(d) || a.endsWith(y, "[]")) && (O = a.toArray(d)))
        return y = Ut(y), O.forEach(function(_, H) {
          !(a.isUndefined(_) || _ === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            i === !0 ? Le([y], H, o) : i === null ? y : y + "[]",
            p(_)
          );
        }), !1;
    }
    return Ie(d) ? !0 : (t.append(Le(w, y, o), p(d)), !1);
  }
  const S = Object.assign(ir, {
    defaultVisitor: g,
    convertValue: p,
    isVisitable: Ie
  });
  function m(d, y, w = 0) {
    if (!a.isUndefined(d)) {
      if (b(w), u.indexOf(d) !== -1)
        throw new Error("Circular reference detected in " + y.join("."));
      u.push(d), a.forEach(d, function(C, _) {
        (!(a.isUndefined(C) || C === null) && s.call(t, C, a.isString(_) ? _.trim() : _, y, S)) === !0 && m(C, y ? y.concat(_) : [_], w + 1);
      }), u.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return m(e), t;
}
function ot(e) {
  const t = {
    "!": "%21",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "~": "%7E",
    "%20": "+"
  };
  return encodeURIComponent(e).replace(/[!'()~]|%20/g, function(r) {
    return t[r];
  });
}
function ze(e, t) {
  this._pairs = [], e && _e(e, this, t);
}
const Lt = ze.prototype;
Lt.append = function(t, n) {
  this._pairs.push([t, n]);
};
Lt.toString = function(t) {
  const n = t ? (r) => t.call(this, r, ot) : ot;
  return this._pairs.map(function(s) {
    return n(s[0]) + "=" + n(s[1]);
  }, "").join("&");
};
function ar(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function Ft(e, t, n) {
  if (!t)
    return e;
  e = e || "";
  const r = a.isFunction(n) ? {
    serialize: n
  } : n, s = a.getSafeProp(r, "encode") || ar, o = a.getSafeProp(r, "serialize");
  let i;
  if (o ? i = o(t, r) : i = a.isURLSearchParams(t) ? t.toString() : new ze(t, r).toString(s), i) {
    const c = e.indexOf("#");
    c !== -1 && (e = e.slice(0, c)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
class it {
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
const ve = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1,
  legacyInterceptorReqResOrdering: !0,
  advertiseZstdAcceptEncoding: !1,
  validateStatusUndefinedResolves: !0
}, cr = typeof URLSearchParams < "u" ? URLSearchParams : ze, lr = typeof FormData < "u" ? FormData : null, ur = typeof Blob < "u" ? Blob : null, fr = {
  isBrowser: !0,
  classes: {
    URLSearchParams: cr,
    FormData: lr,
    Blob: ur
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, Ve = typeof window < "u" && typeof document < "u", qe = typeof navigator == "object" && navigator || void 0, dr = Ve && (!qe || ["ReactNative", "NativeScript", "NS"].indexOf(qe.product) < 0), pr = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", hr = Ve && window.location.href || "http://localhost", mr = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: Ve,
  hasStandardBrowserEnv: dr,
  hasStandardBrowserWebWorkerEnv: pr,
  navigator: qe,
  origin: hr
}, Symbol.toStringTag, { value: "Module" })), x = {
  ...mr,
  ...fr
};
function yr(e, t) {
  return _e(e, new x.classes.URLSearchParams(), {
    visitor: function(n, r, s, o) {
      return x.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : o.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
const at = Dt;
function Bt(e) {
  if (e > at)
    throw new h(
      "FormData field is too deeply nested (" + e + " levels). Max depth: " + at,
      h.ERR_FORM_DATA_DEPTH_EXCEEDED
    );
}
function br(e) {
  const t = [], n = /[^.[\]]+|\[([^.[\]]*)]/g;
  let r;
  for (; (r = n.exec(e)) !== null; )
    Bt(t.length), t.push(r[0] === "[]" ? "" : r[1] || r[0]);
  return t;
}
function wr(e) {
  const t = {}, n = Object.keys(e);
  let r;
  const s = n.length;
  let o;
  for (r = 0; r < s; r++)
    o = n[r], t[o] = e[o];
  return t;
}
function kt(e) {
  function t(n, r, s, o) {
    Bt(o);
    let i = n[o++];
    if (i === "__proto__") return !0;
    const c = Number.isFinite(+i), l = o >= n.length;
    return i = !i && a.isArray(s) ? s.length : i, l ? (a.hasOwnProp(s, i) ? s[i] = a.isArray(s[i]) ? s[i].concat(r) : [s[i], r] : s[i] = r, !c) : ((!a.hasOwnProp(s, i) || !a.isObject(s[i])) && (s[i] = []), t(n, r, s[i], o) && a.isArray(s[i]) && (s[i] = wr(s[i])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(br(r), s, n, 0);
    }), n;
  }
  return null;
}
const te = (e, t) => e != null && a.hasOwnProp(e, t) ? e[t] : void 0;
function Er(e, t, n) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (r) {
      if (r.name !== "SyntaxError")
        throw r;
    }
  return (n || JSON.stringify)(e);
}
const de = {
  transitional: ve,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [
    function(t, n) {
      const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, o = a.isObject(t);
      if (o && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
        return s ? JSON.stringify(kt(t)) : t;
      if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
        return t;
      if (a.isArrayBufferView(t))
        return t.buffer;
      if (a.isURLSearchParams(t))
        return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
      let c;
      if (o) {
        const l = te(this, "formSerializer");
        if (r.indexOf("application/x-www-form-urlencoded") > -1)
          return yr(t, l).toString();
        if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
          const f = te(this, "env"), u = f && f.FormData;
          return _e(
            c ? { "files[]": t } : t,
            u && new u(),
            l
          );
        }
      }
      return o || s ? (n.setContentType("application/json", !1), Er(t)) : t;
    }
  ],
  transformResponse: [
    function(t) {
      const n = te(this, "transitional") || de.transitional, r = n && n.forcedJSONParsing, s = te(this, "responseType"), o = s === "json";
      if (a.isResponse(t) || a.isReadableStream(t))
        return t;
      if (t && a.isString(t) && (r && !s || o)) {
        const c = !(n && n.silentJSONParsing) && o;
        try {
          return JSON.parse(t, te(this, "parseReviver"));
        } catch (l) {
          if (c)
            throw l.name === "SyntaxError" ? h.from(l, h.ERR_BAD_RESPONSE, this, null, te(this, "response")) : l;
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
    FormData: x.classes.FormData,
    Blob: x.classes.Blob
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
  de.headers[e] = {};
});
function Fe(e, t) {
  const n = this || de, r = t || n, s = D.from(r.headers);
  let o = r.data;
  return a.forEach(e, function(c) {
    o = c.call(n, o, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), o;
}
function jt(e) {
  return !!(e && e.__CANCEL__);
}
let pe = class extends h {
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
    super(t ?? "canceled", h.ERR_CANCELED, n, r), this.name = "CanceledError", this.__CANCEL__ = !0;
  }
};
function It(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(new h(
    "Request failed with status code " + n.status,
    n.status >= 400 && n.status < 500 ? h.ERR_BAD_REQUEST : h.ERR_BAD_RESPONSE,
    n.config,
    n.request,
    n
  ));
}
function Rr(e) {
  const t = /^([-+\w]{1,25}):(?:\/\/)?/.exec(e);
  return t && t[1] || "";
}
function gr(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, o = 0, i;
  return t = t !== void 0 ? t : 1e3, function(l) {
    const f = Date.now(), u = r[o];
    i || (i = f), n[s] = l, r[s] = f;
    let p = o, b = 0;
    for (; p !== s; )
      b += n[p++], p = p % e;
    if (s = (s + 1) % e, s === o && (o = (o + 1) % e), f - i < t)
      return;
    const R = u && f - u;
    return R ? Math.round(b * 1e3 / R) : void 0;
  };
}
function Or(e, t) {
  let n = 0, r = 1e3 / t, s, o;
  const i = (f, u = Date.now()) => {
    n = u, s = null, o && (clearTimeout(o), o = null), e(...f);
  };
  return [(...f) => {
    const u = Date.now(), p = u - n;
    p >= r ? i(f, u) : (s = f, o || (o = setTimeout(() => {
      o = null, i(s);
    }, r - p)));
  }, () => s && i(s)];
}
const Se = (e, t, n = 3) => {
  let r = 0;
  const s = gr(50, 250);
  return Or((o) => {
    if (!o || typeof o.loaded != "number")
      return;
    const i = o.loaded, c = o.lengthComputable ? o.total : void 0, l = Math.max(0, c != null ? Math.min(i, c) : i), f = Math.max(0, l - r), u = s(f);
    r = Math.max(r, l);
    const p = {
      loaded: l,
      total: c,
      progress: c ? l / c : void 0,
      bytes: f,
      rate: u || void 0,
      estimated: u && c ? (c - l) / u : void 0,
      event: o,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(p);
  }, n);
}, ct = (e, t) => {
  const n = e != null;
  return [
    (r) => t[0]({
      lengthComputable: n,
      total: e,
      loaded: r
    }),
    t[1]
  ];
}, lt = (e, t = a.asap) => (...n) => t(() => e(...n)), Sr = x.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, x.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(x.origin),
  x.navigator && /(msie|trident)/i.test(x.navigator.userAgent)
) : () => !0, Ar = x.hasStandardBrowserEnv ? (
  // Standard browser envs support document.cookie
  {
    write(e, t, n, r, s, o, i) {
      if (typeof document > "u") return;
      const c = [`${e}=${encodeURIComponent(t)}`];
      a.isNumber(n) && c.push(`expires=${new Date(n).toUTCString()}`), a.isString(r) && c.push(`path=${r}`), a.isString(s) && c.push(`domain=${s}`), o === !0 && c.push("secure"), a.isString(i) && c.push(`SameSite=${i}`), document.cookie = c.join("; ");
    },
    read(e) {
      if (typeof document > "u") return null;
      const t = document.cookie.split(";");
      for (let n = 0; n < t.length; n++) {
        const r = t[n].replace(/^\s+/, ""), s = r.indexOf("=");
        if (s !== -1 && r.slice(0, s) === e)
          try {
            return decodeURIComponent(r.slice(s + 1));
          } catch {
            return r.slice(s + 1);
          }
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
function _r(e) {
  return typeof e != "string" ? !1 : /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function Tr(e, t) {
  if (!t)
    return e;
  let n = e.length;
  for (; n > 0 && e.charCodeAt(n - 1) === 47; )
    n--;
  return e.slice(0, n) + "/" + t.replace(/^\/+/, "");
}
const Pr = /^https?:(?!\/\/)/i, xr = /[\t\n\r]/g;
function Cr(e) {
  let t = 0;
  for (; t < e.length && e.charCodeAt(t) <= 32; )
    t++;
  return e.slice(t);
}
function Nr(e) {
  return Cr(e).replace(xr, "");
}
function Dr(e) {
  return e && e.replace(/(^|&)([^=&]*=)?[^&]+/g, (t, n, r = "") => `${n}${r}${Oe}`);
}
function Ur(e) {
  const t = e.replace(/^(https?:\/{0,2})[^/?#]*@/i, `$1${Oe}@`), n = t.indexOf("#"), s = (n === -1 ? t : t.slice(0, n)).replace(
    /([?&][^=&#]*=)[^&#]*/g,
    `$1${Oe}`
  );
  return n === -1 ? s : `${s}#${Dr(t.slice(n + 1))}`;
}
function ut(e, t) {
  if (typeof e == "string") {
    const n = Nr(e);
    if (Pr.test(n))
      throw new h(
        `Invalid URL ${JSON.stringify(Ur(n))}: missing "//" after protocol`,
        h.ERR_INVALID_URL,
        t
      );
  }
}
function qt(e, t, n, r) {
  ut(t, r);
  let s = !_r(t);
  return e && (s || n === !1) ? (ut(e, r), Tr(e, t)) : t;
}
const ft = (e) => e instanceof D ? { ...e } : e, Lr = (e) => Object.getOwnPropertySymbols && Object.getOwnPropertyDescriptor ? Object.keys(e).concat(
  Object.getOwnPropertySymbols(e).filter(
    (t) => Object.getOwnPropertyDescriptor(e, t).enumerable
  )
) : Object.keys(e);
function Z(e, t) {
  e = e || {}, t = t || {};
  const n = /* @__PURE__ */ Object.create(null);
  Object.defineProperty(n, "hasOwnProperty", {
    // Null-proto descriptor so a polluted Object.prototype.get cannot turn
    // this data descriptor into an accessor descriptor on the way in.
    __proto__: null,
    value: Object.prototype.hasOwnProperty,
    enumerable: !1,
    writable: !0,
    configurable: !0
  });
  function r(u, p, b, R) {
    return a.isPlainObject(u) && a.isPlainObject(p) ? a.merge.call({ caseless: R }, u, p) : a.isPlainObject(p) ? a.merge({}, p) : a.isArray(p) ? p.slice() : p;
  }
  function s(u, p, b, R) {
    if (a.isUndefined(p)) {
      if (!a.isUndefined(u))
        return r(void 0, u, b, R);
    } else return r(u, p, b, R);
  }
  function o(u, p) {
    if (!a.isUndefined(p))
      return r(void 0, p);
  }
  function i(u, p) {
    if (a.isUndefined(p)) {
      if (!a.isUndefined(u))
        return r(void 0, u);
    } else return r(void 0, p);
  }
  function c(u) {
    const p = a.hasOwnProp(t, "transitional") ? t.transitional : void 0;
    if (!a.isUndefined(p))
      if (a.isPlainObject(p)) {
        if (a.hasOwnProp(p, u))
          return p[u];
      } else
        return;
    const b = a.hasOwnProp(e, "transitional") ? e.transitional : void 0;
    if (a.isPlainObject(b) && a.hasOwnProp(b, u))
      return b[u];
  }
  function l(u, p, b) {
    if (a.hasOwnProp(t, b))
      return r(u, p);
    if (a.hasOwnProp(e, b))
      return r(void 0, u);
  }
  const f = {
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
    validateStatus: l,
    headers: (u, p, b) => s(ft(u), ft(p), b, !0)
  };
  return a.forEach(Lr({ ...e, ...t }), function(p) {
    if (p === "__proto__" || p === "constructor" || p === "prototype") return;
    const b = a.hasOwnProp(f, p) ? f[p] : s, R = a.hasOwnProp(e, p) ? e[p] : void 0, g = a.hasOwnProp(t, p) ? t[p] : void 0, S = b(R, g, p);
    a.isUndefined(S) && b !== l || (n[p] = S);
  }), a.hasOwnProp(t, "validateStatus") && a.isUndefined(t.validateStatus) && c("validateStatusUndefinedResolves") === !1 && (a.hasOwnProp(e, "validateStatus") ? n.validateStatus = r(void 0, e.validateStatus) : delete n.validateStatus), n;
}
const Fr = ["content-type", "content-length"];
function Br(e, t, n) {
  if (n !== "content-only") {
    e.set(t);
    return;
  }
  Object.entries(t || {}).forEach(([r, s]) => {
    Fr.includes(r.toLowerCase()) && e.set(r, s);
  });
}
const kr = (e) => encodeURIComponent(e).replace(
  /%([0-9A-F]{2})/gi,
  (t, n) => String.fromCharCode(parseInt(n, 16))
);
function Ht(e) {
  const t = Z({}, e), n = (b) => a.hasOwnProp(t, b) ? t[b] : void 0, r = n("data");
  let s = n("withXSRFToken");
  const o = n("xsrfHeaderName"), i = n("xsrfCookieName");
  let c = n("headers");
  const l = n("auth"), f = n("baseURL"), u = n("allowAbsoluteUrls"), p = n("url");
  if (t.headers = c = D.from(c), t.url = Ft(
    qt(f, p, u, t),
    n("params"),
    n("paramsSerializer")
  ), l) {
    const b = a.getSafeProp(l, "username") || "", R = a.getSafeProp(l, "password") || "";
    try {
      c.set(
        "Authorization",
        "Basic " + btoa(b + ":" + (R ? kr(R) : ""))
      );
    } catch (g) {
      throw h.from(g, h.ERR_BAD_OPTION_VALUE, e);
    }
  }
  if (a.isFormData(r) && (x.hasStandardBrowserEnv || x.hasStandardBrowserWebWorkerEnv || a.isReactNative(r) ? c.setContentType(void 0) : a.isFunction(r.getHeaders) && Br(c, r.getHeaders(), n("formDataHeaderPolicy"))), x.hasStandardBrowserEnv && (a.isFunction(s) && (s = s(t)), s === !0 || s == null && Sr(t.url))) {
    const R = o && i && Ar.read(i);
    R && c.set(o, R);
  }
  return t;
}
const jr = typeof XMLHttpRequest < "u", Ir = jr && function(e) {
  return new Promise(function(n, r) {
    const s = Ht(e);
    let o = s.data;
    const i = D.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: l, onDownloadProgress: f } = s, u, p, b, R, g;
    function S() {
      R && R(), g && g(), s.cancelToken && s.cancelToken.unsubscribe(u), s.signal && s.signal.removeEventListener("abort", u);
    }
    let m = new XMLHttpRequest();
    m.open(s.method.toUpperCase(), s.url, !0), m.timeout = s.timeout;
    function d() {
      if (!m)
        return;
      const w = D.from(
        "getAllResponseHeaders" in m && m.getAllResponseHeaders()
      ), C = {
        data: !c || c === "text" || c === "json" ? m.responseText : m.response,
        status: m.status,
        statusText: m.statusText,
        headers: w,
        config: e,
        request: m
      };
      It(
        function(H) {
          n(H), S();
        },
        function(H) {
          r(H), S();
        },
        C
      ), m = null;
    }
    "onloadend" in m ? m.onloadend = d : m.onreadystatechange = function() {
      !m || m.readyState !== 4 || m.status === 0 && !(m.responseURL && m.responseURL.startsWith("file:")) || setTimeout(d);
    }, m.onabort = function() {
      m && (r(new h("Request aborted", h.ECONNABORTED, e, m)), S(), m = null);
    }, m.onerror = function(O) {
      const C = O && O.message ? O.message : "Network Error", _ = new h(C, h.ERR_NETWORK, e, m);
      _.event = O || null, r(_), S(), m = null;
    }, m.ontimeout = function() {
      let O = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const C = s.transitional || ve;
      s.timeoutErrorMessage && (O = s.timeoutErrorMessage), r(
        new h(
          O,
          C.clarifyTimeoutError ? h.ETIMEDOUT : h.ECONNABORTED,
          e,
          m
        )
      ), S(), m = null;
    }, o === void 0 && i.setContentType(null), "setRequestHeader" in m && a.forEach(Ct(i), function(O, C) {
      m.setRequestHeader(C, O);
    }), a.isUndefined(s.withCredentials) || (m.withCredentials = !!s.withCredentials), c && c !== "json" && (m.responseType = s.responseType), f && ([b, g] = Se(f, !0), m.addEventListener("progress", b)), l && m.upload && ([p, R] = Se(l), m.upload.addEventListener("progress", p), m.upload.addEventListener("loadend", R)), (s.cancelToken || s.signal) && (u = (w) => {
      m && (r(!w || w.type ? new pe(null, e, m) : w), m.abort(), S(), m = null);
    }, s.cancelToken && s.cancelToken.subscribe(u), s.signal && (s.signal.aborted ? u() : s.signal.addEventListener("abort", u)));
    const y = Rr(s.url);
    if (y && !x.protocols.includes(y)) {
      r(
        new h(
          "Unsupported protocol " + y + ":",
          h.ERR_BAD_REQUEST,
          e
        )
      ), S();
      return;
    }
    m.send(o || null);
  });
}, qr = (e, t) => {
  if (e = e ? e.filter(Boolean) : [], !t && !e.length)
    return;
  const n = new AbortController();
  let r = !1;
  const s = function(l) {
    if (!r) {
      r = !0, i();
      const f = l instanceof Error ? l : this.reason;
      n.abort(
        f instanceof h ? f : new pe(f instanceof Error ? f.message : f)
      );
    }
  };
  let o = t && setTimeout(() => {
    o = null, s(new h(`timeout of ${t}ms exceeded`, h.ETIMEDOUT));
  }, t);
  const i = () => {
    e && (o && clearTimeout(o), o = null, e.forEach((l) => {
      l.unsubscribe ? l.unsubscribe(s) : l.removeEventListener("abort", s);
    }), e = null);
  };
  e.forEach((l) => {
    if (!r) {
      if (l.aborted) {
        s.call(l);
        return;
      }
      l.addEventListener("abort", s, { once: !0 });
    }
  });
  const { signal: c } = n;
  return c.unsubscribe = () => a.asap(i), c;
}, Hr = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, Mr = async function* (e, t) {
  for await (const n of $r(e))
    yield* Hr(n, t);
}, $r = async function* (e) {
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
}, dt = (e, t, n, r) => {
  const s = Mr(e, t);
  let o = 0, i, c = (l) => {
    i || (i = !0, r && r(l));
  };
  return new ReadableStream(
    {
      async pull(l) {
        try {
          const { done: f, value: u } = await s.next();
          if (f) {
            c(), l.close();
            return;
          }
          let p = u.byteLength;
          if (n) {
            let b = o += p;
            n(b);
          }
          l.enqueue(new Uint8Array(u));
        } catch (f) {
          throw c(f), f;
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
}, pt = (e) => e >= 48 && e <= 57 || e >= 65 && e <= 70 || e >= 97 && e <= 102, Mt = (e, t, n) => t + 2 < n && pt(e.charCodeAt(t + 1)) && pt(e.charCodeAt(t + 2)), ht = (e) => e <= 57 ? e - 48 : (e & 223) - 55, zr = (e) => e >= 65 && e <= 90 || // A-Z
e >= 97 && e <= 122 || // a-z
e >= 48 && e <= 57 || // 0-9
e === 43 || // +
e === 47 || // /
e === 45 || // - (base64url)
e === 95, vr = (e) => e === 9 || e === 10 || e === 12 || e === 13 || e === 32, Vr = (e) => {
  const t = Math.floor(e / 4), n = e % 4;
  return t * 3 + (n === 2 ? 1 : n === 3 ? 2 : 0);
}, Wr = (e) => {
  const t = e.length;
  let n = 0;
  return t > 0 && e.charCodeAt(t - 1) === 61 && (n++, t > 1 && e.charCodeAt(t - 2) === 61 && n++), Math.floor((t - n) * 3 / 4);
}, Jr = (e) => {
  const t = e.length;
  let n = 0, r = 0, s = !1;
  for (let o = 0; o < t; o++) {
    let i = e.charCodeAt(o);
    if (i === 37 && Mt(e, o, t) && (i = ht(e.charCodeAt(o + 1)) * 16 + ht(e.charCodeAt(o + 2)), o += 2), !vr(i)) {
      if (i === 61) {
        r++;
        continue;
      }
      if (!zr(i) || r > 0) {
        s = !0;
        continue;
      }
      n++;
    }
  }
  return s || r > 2 || r > 0 && (n + r) % 4 !== 0 || n % 4 === 1 ? Wr(e) : Vr(n);
}, Kr = (e, t) => {
  if (!e || typeof e != "string" || !e.startsWith("data:")) return 0;
  const n = e.indexOf(",");
  if (n < 0) return 0;
  const r = e.slice(5, n), s = e.slice(n + 1);
  if (/;base64/i.test(r))
    return t(s);
  let i = 0;
  for (let c = 0, l = s.length; c < l; c++) {
    const f = s.charCodeAt(c);
    if (f === 37 && Mt(s, c, l))
      i += 1, c += 2;
    else if (f < 128)
      i += 1;
    else if (f < 2048)
      i += 2;
    else if (f >= 55296 && f <= 56319 && c + 1 < l) {
      const u = s.charCodeAt(c + 1);
      u >= 56320 && u <= 57343 ? (i += 4, c++) : i += 3;
    } else
      i += 3;
  }
  return i;
};
function Xr(e) {
  const t = typeof e == "string" ? e.indexOf("#") : -1;
  return Kr(
    t === -1 ? e : e.slice(0, t),
    Jr
  );
}
const We = "1.19.0", mt = 64 * 1024, { isFunction: be } = a, Gr = (e) => encodeURIComponent(e).replace(
  /%([0-9A-F]{2})/gi,
  (t, n) => String.fromCharCode(parseInt(n, 16))
), yt = (e) => {
  if (!a.isString(e))
    return e;
  try {
    return decodeURIComponent(e);
  } catch {
    return e;
  }
}, bt = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, Qr = (e) => {
  const t = e.indexOf("://");
  let n = e;
  return t !== -1 && (n = n.slice(t + 3)), n.includes("@") || n.includes(":");
}, Zr = (e) => {
  const t = a.global !== void 0 && a.global !== null ? a.global : globalThis, { ReadableStream: n, TextEncoder: r } = t;
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
  const { fetch: s, Request: o, Response: i } = e, c = s ? be(s) : typeof fetch == "function", l = be(o), f = be(i);
  if (!c)
    return !1;
  const u = c && be(n), p = c && (typeof r == "function" ? /* @__PURE__ */ ((d) => (y) => d.encode(y))(new r()) : async (d) => new Uint8Array(await new o(d).arrayBuffer())), b = l && u && bt(() => {
    let d = !1;
    const y = new o(x.origin, {
      body: new n(),
      method: "POST",
      get duplex() {
        return d = !0, "half";
      }
    }), w = y.headers.has("Content-Type");
    return y.body != null && y.body.cancel(), d && !w;
  }), R = f && u && bt(() => a.isReadableStream(new i("").body)), g = {
    stream: R && ((d) => d.body)
  };
  c && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((d) => {
    !g[d] && (g[d] = (y, w) => {
      let O = y && y[d];
      if (O)
        return O.call(y);
      throw new h(
        `Response type '${d}' is not supported`,
        h.ERR_NOT_SUPPORT,
        w
      );
    });
  });
  const S = async (d) => {
    if (d == null)
      return 0;
    if (a.isBlob(d))
      return d.size;
    if (a.isSpecCompliantForm(d))
      return (await new o(x.origin, {
        method: "POST",
        body: d
      }).arrayBuffer()).byteLength;
    if (a.isArrayBufferView(d) || a.isArrayBuffer(d))
      return d.byteLength;
    if (a.isURLSearchParams(d) && (d = d + ""), a.isString(d))
      return (await p(d)).byteLength;
  }, m = async (d, y) => {
    const w = a.toFiniteNumber(d.getContentLength());
    return w ?? S(y);
  };
  return async (d) => {
    let {
      url: y,
      method: w,
      data: O,
      signal: C,
      cancelToken: _,
      timeout: H,
      onDownloadProgress: Pe,
      onUploadProgress: xe,
      responseType: M,
      headers: $,
      withCredentials: he = "same-origin",
      fetchOptions: Ke,
      maxContentLength: j,
      maxBodyLength: me
    } = Ht(d);
    const oe = a.isNumber(j) && j > -1, Ce = a.isNumber(me) && me > -1, Wt = (A) => a.hasOwnProp(d, A) ? d[A] : void 0;
    let Xe = s || fetch;
    M = M ? (M + "").toLowerCase() : "text";
    let z = qr(
      [C, _ && _.toAbortSignal()],
      H
    ), P = null;
    const W = z && z.unsubscribe && (() => {
      z.unsubscribe();
    });
    let ee, ie = null;
    const Ge = () => new h(
      "Request body larger than maxBodyLength limit",
      h.ERR_BAD_REQUEST,
      d,
      P
    );
    try {
      let A;
      const F = Wt("auth");
      if (F) {
        const E = a.getSafeProp(F, "username") || "", L = a.getSafeProp(F, "password") || "";
        A = {
          username: E,
          password: L
        };
      }
      if (Qr(y)) {
        const E = new URL(y, x.origin);
        if (!A && (E.username || E.password)) {
          const L = yt(E.username), v = yt(E.password);
          A = {
            username: L,
            password: v
          };
        }
        (E.username || E.password) && (E.username = "", E.password = "", y = E.href);
      }
      if (A && ($.delete("authorization"), $.set(
        "Authorization",
        "Basic " + btoa(Gr((A.username || "") + ":" + (A.password || "")))
      )), oe && typeof y == "string" && y.startsWith("data:") && Xr(y) > j)
        throw new h(
          "maxContentLength size of " + j + " exceeded",
          h.ERR_BAD_RESPONSE,
          d,
          P
        );
      if (Ce && w !== "get" && w !== "head") {
        const E = await S(O);
        if (typeof E == "number" && isFinite(E) && (ee = E, E > me))
          throw Ge();
      }
      const ye = Ce && (a.isReadableStream(O) || a.isStream(O)), Qe = (E, L, v) => dt(
        E,
        mt,
        (J) => {
          if (Ce && J > me)
            throw ie = Ge();
          L && L(J);
        },
        v
      );
      if (b && w !== "get" && w !== "head" && (xe || ye)) {
        if (ee = ee ?? await m($, O), ee !== 0 || ye) {
          let E = new o(y, {
            method: "POST",
            body: O,
            duplex: "half"
          }), L;
          if (a.isFormData(O) && (L = E.headers.get("content-type")) && $.setContentType(L), E.body) {
            const [v, J] = xe && ct(
              ee,
              Se(lt(xe))
            ) || [];
            O = Qe(E.body, v, J);
          }
        }
      } else if (ye && !l && u && w !== "get" && w !== "head")
        O = Qe(O);
      else if (ye && l && !b && w !== "get" && w !== "head")
        throw new h(
          "Stream request bodies are not supported by the current fetch implementation",
          h.ERR_NOT_SUPPORT,
          d,
          P
        );
      a.isString(he) || (he = he ? "include" : "omit");
      const Jt = l && "credentials" in o.prototype;
      if (a.isFormData(O)) {
        const E = $.getContentType();
        E && /^multipart\/form-data/i.test(E) && !/boundary=/i.test(E) && $.delete("content-type");
      }
      $.set("User-Agent", "axios/" + We, !1);
      const Ze = {
        ...Ke,
        signal: z,
        method: w.toUpperCase(),
        headers: Ct($.normalize()),
        body: O,
        duplex: "half",
        credentials: Jt ? he : void 0
      };
      P = l && new o(y, Ze);
      let I = await (l ? Xe(P, Ke) : Xe(y, Ze));
      const Ye = D.from(I.headers);
      if (oe) {
        const E = a.toFiniteNumber(Ye.getContentLength());
        if (E != null && E > j)
          throw new h(
            "maxContentLength size of " + j + " exceeded",
            h.ERR_BAD_RESPONSE,
            d,
            P
          );
      }
      const Ne = R && (M === "stream" || M === "response");
      if (R && I.body && (Pe || oe || Ne && W)) {
        const E = {};
        ["status", "statusText", "headers"].forEach((ae) => {
          E[ae] = I[ae];
        });
        const L = a.toFiniteNumber(Ye.getContentLength()), [v, J] = Pe && ct(
          L,
          Se(lt(Pe), !0)
        ) || [];
        let et = 0;
        const Kt = (ae) => {
          if (oe && (et = ae, et > j))
            throw new h(
              "maxContentLength size of " + j + " exceeded",
              h.ERR_BAD_RESPONSE,
              d,
              P
            );
          v && v(ae);
        };
        I = new i(
          dt(I.body, mt, Kt, () => {
            J && J(), W && W();
          }),
          E
        );
      }
      M = M || "text";
      let q = await g[a.findKey(g, M) || "text"](
        I,
        d
      );
      if (oe && !R && !Ne) {
        let E;
        if (q != null && (typeof q.byteLength == "number" ? E = q.byteLength : typeof q.size == "number" ? E = q.size : typeof q == "string" && (E = typeof r == "function" ? new r().encode(q).byteLength : q.length)), typeof E == "number" && E > j)
          throw new h(
            "maxContentLength size of " + j + " exceeded",
            h.ERR_BAD_RESPONSE,
            d,
            P
          );
      }
      return !Ne && W && W(), await new Promise((E, L) => {
        It(E, L, {
          data: q,
          headers: D.from(I.headers),
          status: I.status,
          statusText: I.statusText,
          config: d,
          request: P
        });
      });
    } catch (A) {
      if (W && W(), z && z.aborted && z.reason instanceof h) {
        const F = z.reason;
        throw F.config = d, P && (F.request = P), A !== F && Object.defineProperty(F, "cause", {
          __proto__: null,
          value: A,
          writable: !0,
          enumerable: !1,
          configurable: !0
        }), F;
      }
      if (ie)
        throw P && !ie.request && (ie.request = P), ie;
      if (A instanceof h)
        throw P && !A.request && (A.request = P), A;
      if (A && A.name === "TypeError" && /Load failed|fetch/i.test(A.message)) {
        const F = new h(
          "Network Error",
          h.ERR_NETWORK,
          d,
          P,
          A && A.response
        );
        throw Object.defineProperty(F, "cause", {
          __proto__: null,
          value: A.cause || A,
          writable: !0,
          enumerable: !1,
          configurable: !0
        }), F;
      }
      throw h.from(A, A && A.code, d, P, A && A.response);
    }
  };
}, Yr = /* @__PURE__ */ new Map(), $t = (e) => {
  let t = e && e.env || {};
  const { fetch: n, Request: r, Response: s } = t, o = [r, s, n];
  let i = o.length, c = i, l, f, u = Yr;
  for (; c--; )
    l = o[c], f = u.get(l), f === void 0 && u.set(l, f = c ? /* @__PURE__ */ new Map() : Zr(t)), u = f;
  return f;
};
$t();
const Je = {
  http: sr,
  xhr: Ir,
  fetch: {
    get: $t
  }
};
a.forEach(Je, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { __proto__: null, value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { __proto__: null, value: t });
  }
});
const wt = (e) => `- ${e}`, es = (e) => a.isFunction(e) || e === null || e === !1;
function ts(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: n } = e;
  let r, s;
  const o = {};
  for (let i = 0; i < n; i++) {
    r = e[i];
    let c;
    if (s = r, !es(r) && (s = Je[(c = String(r)).toLowerCase()], s === void 0))
      throw new h(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    o[c || "#" + i] = s;
  }
  if (!s) {
    const i = Object.entries(o).map(
      ([l, f]) => `adapter ${l} ` + (f === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = n ? i.length > 1 ? `since :
` + i.map(wt).join(`
`) : " " + wt(i[0]) : "as no adapter specified";
    throw new h(
      "There is no suitable adapter to dispatch the request " + c,
      h.ERR_NOT_SUPPORT
    );
  }
  return s;
}
const zt = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: ts,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: Je
};
function Be(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new pe(null, e);
}
function ke(e) {
  return Be(e), e.headers = D.from(e.headers), e.data = Fe.call(e, e.transformRequest), ["post", "put", "patch"].indexOf(e.method) !== -1 && e.headers.setContentType("application/x-www-form-urlencoded", !1), zt.getAdapter(e.adapter || de.adapter, e)(e).then(
    function(r) {
      Be(e), e.response = r;
      try {
        r.data = Fe.call(e, e.transformResponse, r);
      } finally {
        delete e.response;
      }
      return r.headers = D.from(r.headers), r;
    },
    function(r) {
      if (!jt(r) && (Be(e), r && r.response)) {
        e.response = r.response;
        try {
          r.response.data = Fe.call(
            e,
            e.transformResponse,
            r.response
          );
        } finally {
          delete e.response;
        }
        r.response.headers = D.from(r.response.headers);
      }
      return Promise.reject(r);
    }
  );
}
const Te = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  Te[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const Et = {};
Te.transitional = function(t, n, r) {
  function s(o, i) {
    return "[Axios v" + We + "] Transitional option '" + o + "'" + i + (r ? ". " + r : "");
  }
  return (o, i, c) => {
    if (t === !1)
      throw new h(
        s(i, " has been removed" + (n ? " in " + n : "")),
        h.ERR_DEPRECATED
      );
    return n && !Et[i] && (Et[i] = !0, console.warn(
      s(
        i,
        " has been deprecated since v" + n + " and will be removed in the near future"
      )
    )), t ? t(o, i, c) : !0;
  };
};
Te.spelling = function(t) {
  return (n, r) => (console.warn(`${r} is likely a misspelling of ${t}`), !0);
};
function ns(e, t, n) {
  if (typeof e != "object" || e === null)
    throw new h("options must be an object", h.ERR_BAD_OPTION_VALUE);
  const r = Object.keys(e);
  let s = r.length;
  for (; s-- > 0; ) {
    const o = r[s], i = Object.prototype.hasOwnProperty.call(t, o) ? t[o] : void 0;
    if (i) {
      const c = e[o], l = c === void 0 || i(c, o, e);
      if (l !== !0)
        throw new h(
          "option " + o + " must be " + l,
          h.ERR_BAD_OPTION_VALUE
        );
      continue;
    }
    if (n !== !0)
      throw new h("Unknown option " + o, h.ERR_BAD_OPTION);
  }
}
const Re = {
  assertOptions: ns,
  validators: Te
}, N = Re.validators;
let X = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new it(),
      response: new it()
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
        const o = (() => {
          if (!s.stack)
            return "";
          const i = s.stack.indexOf(`
`);
          return i === -1 ? "" : s.stack.slice(i + 1);
        })();
        try {
          if (!r.stack)
            r.stack = o;
          else if (o) {
            const i = o.indexOf(`
`), c = i === -1 ? -1 : o.indexOf(`
`, i + 1), l = c === -1 ? "" : o.slice(c + 1);
            String(r.stack).endsWith(l) || (r.stack += `
` + o);
          }
        } catch {
        }
      }
      throw r;
    }
  }
  _request(t, n) {
    typeof t == "string" ? (n = n || {}, n.url = t) : n = t || {}, n = Z(this.defaults, n);
    const { transitional: r, paramsSerializer: s, headers: o } = n;
    r !== void 0 && Re.assertOptions(
      r,
      {
        silentJSONParsing: N.transitional(N.boolean),
        forcedJSONParsing: N.transitional(N.boolean),
        clarifyTimeoutError: N.transitional(N.boolean),
        legacyInterceptorReqResOrdering: N.transitional(N.boolean),
        advertiseZstdAcceptEncoding: N.transitional(N.boolean),
        validateStatusUndefinedResolves: N.transitional(N.boolean)
      },
      !1
    ), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : Re.assertOptions(
      s,
      {
        encode: N.function,
        serialize: N.function
      },
      !0
    )), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), Re.assertOptions(
      n,
      {
        baseUrl: N.spelling("baseURL"),
        withXsrfToken: N.spelling("withXSRFToken")
      },
      !0
    ), n.method = (n.method || this.defaults.method || "get").toLowerCase();
    let i = o && a.merge(o.common, o[n.method]);
    o && a.forEach(["delete", "get", "head", "post", "put", "patch", "query", "common"], (g) => {
      delete o[g];
    }), n.headers = D.concat(i, o);
    const c = [];
    let l = !0;
    this.interceptors.request.forEach(function(S) {
      if (typeof S.runWhen == "function" && S.runWhen(n) === !1)
        return;
      l = l && S.synchronous;
      const m = n.transitional || ve;
      m && m.legacyInterceptorReqResOrdering ? c.unshift(S.fulfilled, S.rejected) : c.push(S.fulfilled, S.rejected);
    });
    const f = [];
    this.interceptors.response.forEach(function(S) {
      f.push(S.fulfilled, S.rejected);
    });
    let u, p = 0, b;
    if (!l) {
      const g = [ke.bind(this), void 0];
      for (g.unshift(...c), g.push(...f), b = g.length, u = Promise.resolve(n); p < b; )
        u = u.then(g[p++], g[p++]);
      return u;
    }
    b = c.length;
    let R = n;
    for (; p < b; ) {
      const g = c[p++], S = c[p++];
      try {
        R = g ? g(R) : R;
      } catch (m) {
        if (!S) {
          u = Promise.reject(m);
          break;
        }
        try {
          const d = S.call(this, m);
          a.isThenable(d) && (u = Promise.resolve(d).then(
            () => ke.call(this, R)
          ));
        } catch (d) {
          u = Promise.reject(d);
        }
        break;
      }
    }
    if (!u)
      try {
        u = ke.call(this, R);
      } catch (g) {
        u = Promise.reject(g);
      }
    for (p = 0, b = f.length; p < b; )
      u = u.then(f[p++], f[p++]);
    return u;
  }
  getUri(t) {
    t = Z(this.defaults, t);
    const n = qt(t.baseURL, t.url, t.allowAbsoluteUrls, t);
    return Ft(n, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  X.prototype[t] = function(n, r) {
    return this.request(
      Z(r || {}, {
        method: t,
        url: n,
        data: r && a.hasOwnProp(r, "data") ? r.data : void 0
      })
    );
  };
});
a.forEach(["post", "put", "patch", "query"], function(t) {
  function n(r) {
    return function(o, i, c) {
      return this.request(
        Z(c || {}, {
          method: t,
          headers: r ? {
            "Content-Type": "multipart/form-data"
          } : {},
          url: o,
          data: i
        })
      );
    };
  }
  X.prototype[t] = n(), t !== "query" && (X.prototype[t + "Form"] = n(!0));
});
let rs = class vt {
  constructor(t) {
    if (typeof t != "function")
      throw new TypeError("executor must be a function.");
    let n;
    this.promise = new Promise(function(o) {
      n = o;
    });
    const r = this;
    this.promise.then((s) => {
      if (!r._listeners) return;
      let o = r._listeners.length;
      for (; o-- > 0; )
        r._listeners[o](s);
      r._listeners = null;
    }), this.promise.then = (s) => {
      let o;
      const i = new Promise((c) => {
        r.subscribe(c), o = c;
      }).then(s);
      return i.cancel = function() {
        r.unsubscribe(o);
      }, i;
    }, t(function(o, i, c) {
      r.reason || (r.reason = new pe(o, i, c), n(r.reason));
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
      token: new vt(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function ss(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function os(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const He = {
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
  WebServerReturnsAnUnknownError: 520,
  WebServerIsDown: 521,
  ConnectionTimedOut: 522,
  OriginIsUnreachable: 523,
  TimeoutOccurred: 524,
  SslHandshakeFailed: 525,
  InvalidSslCertificate: 526
};
Object.entries(He).forEach(([e, t]) => {
  He[t] = e;
});
function Vt(e) {
  const t = new X(e), n = Rt(X.prototype.request, t);
  return a.extend(n, X.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return Vt(Z(e, s));
  }, n;
}
const T = Vt(de);
T.Axios = X;
T.CanceledError = pe;
T.CancelToken = rs;
T.isCancel = jt;
T.VERSION = We;
T.toFormData = _e;
T.AxiosError = h;
T.Cancel = T.CanceledError;
T.all = function(t) {
  return Promise.all(t);
};
T.spread = ss;
T.isAxiosError = os;
T.mergeConfig = Z;
T.AxiosHeaders = D;
T.formToJSON = (e) => kt(a.isHTMLForm(e) ? new FormData(e) : e);
T.getAdapter = zt.getAdapter;
T.HttpStatusCode = He;
T.default = T;
const {
  Axios: us,
  AxiosError: fs,
  CanceledError: ds,
  isCancel: ps,
  CancelToken: hs,
  VERSION: ms,
  all: ys,
  Cancel: bs,
  isAxiosError: ws,
  spread: Es,
  toFormData: Rs,
  AxiosHeaders: gs,
  HttpStatusCode: Os,
  formToJSON: Ss,
  getAdapter: As,
  mergeConfig: _s,
  create: Ts
} = T, Y = T.create({
  withCredentials: !0,
  timeout: 18e4,
  // Add a timeout of 3 minutes
  headers: {
    "Content-Type": "application/json"
  }
});
function Ps() {
  const e = "csrftoken=", n = decodeURIComponent(document.cookie).split(";");
  for (let r of n)
    if (r = r.trim(), r.indexOf(e) === 0)
      return r.substring(e.length);
  return "";
}
Y.interceptors.request.use(
  (e) => e,
  (e) => Promise.reject(e)
);
Y.interceptors.response.use(
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
function xs(e, t = {}) {
  const n = V(e), r = B(null), s = B(null), o = B(!0), i = Y.get(n, {
    headers: t
  }).then((c) => (s.value = c.data, o.value = !1, { loading: o, backendError: r, responseData: s })).catch((c) => (r.value = c, o.value = !1, { loading: o, backendError: r, responseData: s }));
  return {
    loading: o,
    backendError: r,
    responseData: s,
    then: (c, l) => i.then(c, l)
  };
}
function Cs(e, t, n = {}) {
  const r = V(e), s = B(null), o = B(null), i = B(!0), c = Y.post(r, V(t), {
    headers: n
  }).then((l) => (o.value = l.data, i.value = !1, { loading: i, backendError: s, responseData: o })).catch((l) => (s.value = l, i.value = !1, { loading: i, backendError: s, responseData: o }));
  return {
    loading: i,
    backendError: s,
    responseData: o,
    then: (l, f) => c.then(l, f)
  };
}
function Ns(e, t, n = {}) {
  const r = V(e), s = B(null), o = V(t), i = B(!0), c = Y.put(r, o, {
    headers: n
  }).then((l) => (console.log(l.statusText), i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, f) => c.then(l, f)
  };
}
function Ds(e, t, n = {}) {
  const r = V(e), s = B(null), o = V(t), i = B(!0), c = Y.patch(r, o, {
    headers: n
  }).then((l) => (i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, f) => c.then(l, f)
  };
}
function Us(e, t = {}) {
  const n = V(e), r = B(null), s = B(!0), o = Y.delete(n, {
    headers: t
  }).then((i) => (s.value = !1, { loading: s, backendError: r })).catch((i) => (console.log(i), r.value = i, s.value = !1, { loading: s, backendError: r }));
  return {
    loading: s,
    backendError: r,
    then: (i, c) => o.then(i, c)
  };
}
export {
  Ps as getCsrfToken,
  Us as useDeleteBackendData,
  xs as useGetBackendData,
  Ds as usePatchBackendData,
  Cs as usePostBackendData,
  Ns as usePutBackendData
};
