import { toValue as K, ref as j } from "vue";
function At(e, t) {
  return function() {
    return e.apply(t, arguments);
  };
}
const { toString: an } = Object.prototype, { getPrototypeOf: X } = Object, { iterator: be, toStringTag: Pt } = Symbol, me = (({ hasOwnProperty: e }) => (t, n) => e.call(t, n))(Object.prototype), Tt = (e) => typeof e == "string" && (e === "__proto__" || e === "constructor" || e === "prototype"), xt = (e, t, n) => e === Object.prototype || !n && t === null, cn = (e) => {
  if (!Object.isExtensible(e))
    return !1;
  const t = Object.getOwnPropertyNames(e);
  return Object.getOwnPropertySymbols && t.push(...Object.getOwnPropertySymbols(e)), t.every((n) => {
    if (Tt(n))
      return !1;
    const r = Object.getOwnPropertyDescriptor(e, n);
    return !!r && r.configurable && r.writable === !0;
  });
}, ye = (e, t) => {
  let n = e;
  const r = [];
  for (; n != null; ) {
    if (r.indexOf(n) !== -1)
      return !1;
    r.push(n);
    const s = X(n);
    if (xt(n, s, n === e))
      return !1;
    if (me(n, t))
      return !0;
    n = s;
  }
  return !1;
}, ln = (e, t) => e != null && ye(e, t) ? e[t] : void 0, un = (e) => {
  if (e == null || typeof e != "object" && typeof e != "function")
    return e;
  const t = X(e);
  if (t === null && cn(e))
    return e;
  const n = /* @__PURE__ */ Object.create(null), r = /* @__PURE__ */ Object.create(null), s = [];
  let o = e;
  for (; o != null && s.indexOf(o) === -1; ) {
    s.push(o);
    const i = o === e ? t : X(o);
    if (xt(o, i, o === e))
      break;
    const c = Object.getOwnPropertyNames(o);
    Object.getOwnPropertySymbols && c.push(...Object.getOwnPropertySymbols(o));
    for (const l of c)
      Tt(l) || me(r, l) || (n[l] = e[l], r[l] = !0);
    o = i;
  }
  return n;
}, Je = /* @__PURE__ */ ((e) => (t) => {
  const n = an.call(t);
  return e[n] || (e[n] = n.slice(8, -1).toLowerCase());
})(/* @__PURE__ */ Object.create(null)), k = (e) => (e = e.toLowerCase(), (t) => Je(t) === e), Ne = (e) => (t) => typeof t === e, { isArray: te } = Array, ne = Ne("undefined");
function ae(e) {
  return e !== null && !ne(e) && e.constructor !== null && !ne(e.constructor) && F(e.constructor.isBuffer) && e.constructor.isBuffer(e);
}
const Ct = k("ArrayBuffer");
function fn(e) {
  let t;
  return typeof ArrayBuffer < "u" && ArrayBuffer.isView ? t = ArrayBuffer.isView(e) : t = e && e.buffer && Ct(e.buffer), t;
}
const dn = Ne("string"), F = Ne("function"), Dt = Ne("number"), ce = (e) => e !== null && typeof e == "object", pn = (e) => e === !0 || e === !1, Ae = (e) => {
  if (!ce(e))
    return !1;
  const t = X(e);
  return (t === null || t === Object.prototype || X(t) === null) && // Treat safe own/inherited Symbol.toStringTag or Symbol.iterator members as
  // evidence the value is tagged/iterable, while ignoring members reachable
  // only through shared or terminal prototype boundaries.
  !ye(e, Pt) && !ye(e, be);
}, hn = (e) => {
  if (!ce(e) || ae(e))
    return !1;
  try {
    return Object.keys(e).length === 0 && Object.getPrototypeOf(e) === Object.prototype;
  } catch {
    return !1;
  }
}, mn = k("Date"), yn = k("File"), bn = (e) => !!(e && typeof e.uri < "u"), wn = (e) => e && typeof e.getParts < "u", gn = k("Blob"), En = k("FileList"), Rn = k("Set"), On = (e) => ce(e) && F(e.pipe);
function Sn() {
  return typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
}
const ot = Sn(), it = typeof ot.FormData < "u" ? ot.FormData : void 0, _n = (e) => {
  if (!e) return !1;
  if (it && e instanceof it) return !0;
  const t = X(e);
  if (!t || t === Object.prototype || !F(e.append)) return !1;
  const n = Je(e);
  return n === "formdata" || // detect form-data instance
  n === "object" && F(e.toString) && e.toString() === "[object FormData]";
}, An = k("URLSearchParams"), [Pn, Tn, xn, Cn] = [
  "ReadableStream",
  "Request",
  "Response",
  "Headers"
].map(k), Dn = (e) => e.trim ? e.trim() : e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, "");
function we(e, t, { allOwnKeys: n = !1 } = {}) {
  if (e === null || typeof e > "u")
    return;
  let r, s;
  if (typeof e != "object" && (e = [e]), te(e))
    for (r = 0, s = e.length; r < s; r++)
      t.call(null, e[r], r, e);
  else {
    if (ae(e))
      return;
    const o = n ? Object.getOwnPropertyNames(e) : Object.keys(e), i = o.length;
    let c;
    for (r = 0; r < i; r++)
      c = o[r], t.call(null, e[c], c, e);
  }
}
function Nt(e, t) {
  if (ae(e))
    return null;
  t = t.toLowerCase();
  const n = Object.keys(e);
  let r = n.length, s;
  for (; r-- > 0; )
    if (s = n[r], t === s.toLowerCase())
      return s;
  return null;
}
const Y = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : global, Ut = (e) => !ne(e) && e !== Y;
function ve(...e) {
  const { caseless: t, skipUndefined: n } = Ut(this) && this || {}, r = {}, s = (o, i) => {
    if (i === "__proto__" || i === "constructor" || i === "prototype")
      return;
    const c = t && typeof i == "string" && Nt(r, i) || i, l = me(r, c) ? r[c] : void 0;
    Ae(l) && Ae(o) ? r[c] = ve(l, o) : Ae(o) ? r[c] = ve({}, o) : te(o) ? r[c] = o.slice() : (!n || !ne(o)) && (r[c] = o);
  };
  for (let o = 0, i = e.length; o < i; o++) {
    const c = e[o];
    if (!c || ae(c) || (we(c, s), typeof c != "object" || te(c)))
      continue;
    const l = Object.getOwnPropertySymbols(c);
    for (let d = 0; d < l.length; d++) {
      const f = l[d];
      $n.call(c, f) && s(c[f], f);
    }
  }
  return r;
}
const Nn = (e, t, n, { allOwnKeys: r } = {}) => (we(
  t,
  (s, o) => {
    n && F(s) ? Object.defineProperty(e, o, {
      // Null-proto descriptor so a polluted Object.prototype.get cannot
      // hijack defineProperty's accessor-vs-data resolution.
      __proto__: null,
      value: At(s, n),
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
), e), Un = (e) => (e.charCodeAt(0) === 65279 && (e = e.slice(1)), e), Ln = (e, t, n, r) => {
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
}, Fn = (e, t, n, r) => {
  let s, o, i;
  const c = {};
  if (t = t || {}, e == null) return t;
  do {
    for (s = Object.getOwnPropertyNames(e), o = s.length; o-- > 0; )
      i = s[o], (!r || r(i, e, t)) && !c[i] && (t[i] = e[i], c[i] = !0);
    e = n !== !1 && X(e);
  } while (e && (!n || n(e, t)) && e !== Object.prototype);
  return t;
}, Bn = (e, t, n) => {
  e = String(e), (n === void 0 || n > e.length) && (n = e.length), n -= t.length;
  const r = e.indexOf(t, n);
  return r !== -1 && r === n;
}, jn = (e) => {
  if (!e) return null;
  if (te(e)) return e;
  let t = e.length;
  if (!Dt(t)) return null;
  const n = new Array(t);
  for (; t-- > 0; )
    n[t] = e[t];
  return n;
}, kn = /* @__PURE__ */ ((e) => (t) => e && t instanceof e)(typeof Uint8Array < "u" && X(Uint8Array)), In = (e, t) => {
  const r = (e && e[be]).call(e);
  let s;
  for (; (s = r.next()) && !s.done; ) {
    const o = s.value;
    t.call(e, o[0], o[1]);
  }
}, qn = (e, t) => {
  let n;
  const r = [];
  for (; (n = e.exec(t)) !== null; )
    r.push(n);
  return r;
}, Hn = k("HTMLFormElement"), Mn = (e) => e.toLowerCase().replace(/[-_\s]([a-z\d])(\w*)/g, function(n, r, s) {
  return r.toUpperCase() + s;
}), { propertyIsEnumerable: $n } = Object.prototype, zn = k("RegExp"), Lt = (e, t) => {
  const n = Object.getOwnPropertyDescriptors(e), r = {};
  we(n, (s, o) => {
    let i;
    (i = t(s, o, e)) !== !1 && (r[o] = i || s);
  }), Object.defineProperties(e, r);
}, vn = (e) => {
  Lt(e, (t, n) => {
    if (F(e) && ["arguments", "caller", "callee"].includes(n))
      return !1;
    const r = e[n];
    if (F(r)) {
      if (t.enumerable = !1, "writable" in t) {
        t.writable = !1;
        return;
      }
      t.set || (t.set = () => {
        throw Error("Can not rewrite read-only method '" + n + "'");
      });
    }
  });
}, Vn = (e, t) => {
  const n = {}, r = (s) => {
    s.forEach((o) => {
      n[o] = !0;
    });
  };
  return te(e) ? r(e) : r(String(e).split(t)), n;
}, Wn = () => {
}, Jn = (e, t) => e != null && Number.isFinite(e = +e) ? e : t;
function Kn(e) {
  return !!(e && F(e.append) && e[Pt] === "FormData" && e[be]);
}
const Xn = (e) => {
  const t = /* @__PURE__ */ new WeakSet(), n = (r) => {
    if (ce(r)) {
      if (t.has(r))
        return;
      if (ae(r))
        return r;
      if (!("toJSON" in r)) {
        t.add(r);
        let s;
        if (Rn(r)) {
          s = [];
          for (const o of r) {
            const i = n(o);
            !ne(i) && s.push(i);
          }
        } else
          s = te(r) ? [] : {}, we(r, (o, i) => {
            const c = n(o);
            !ne(c) && (s[i] = c);
          });
        return t.delete(r), s;
      }
    }
    return r;
  };
  return n(e);
}, Gn = k("AsyncFunction"), Qn = (e) => e && (ce(e) || F(e)) && F(e.then) && F(e.catch), Ft = ((e, t) => e ? setImmediate : t ? ((n, r) => (Y.addEventListener(
  "message",
  ({ source: s, data: o }) => {
    s === Y && o === n && r.length && r.shift()();
  },
  !1
), (s) => {
  r.push(s), Y.postMessage(n, "*");
}))(`axios@${Math.random()}`, []) : (n) => setTimeout(n))(typeof setImmediate == "function", F(Y.postMessage)), Zn = typeof queueMicrotask < "u" ? queueMicrotask.bind(Y) : typeof process < "u" && process.nextTick || Ft, Bt = (e) => e != null && F(e[be]), Yn = (e) => e != null && ye(e, be) && Bt(e), a = {
  isArray: te,
  isArrayBuffer: Ct,
  isBuffer: ae,
  isFormData: _n,
  isArrayBufferView: fn,
  isString: dn,
  isNumber: Dt,
  isBoolean: pn,
  isObject: ce,
  isPlainObject: Ae,
  isEmptyObject: hn,
  isReadableStream: Pn,
  isRequest: Tn,
  isResponse: xn,
  isHeaders: Cn,
  isUndefined: ne,
  isDate: mn,
  isFile: yn,
  isReactNativeBlob: bn,
  isReactNative: wn,
  isBlob: gn,
  isRegExp: zn,
  isFunction: F,
  isStream: On,
  isURLSearchParams: An,
  isTypedArray: kn,
  isFileList: En,
  forEach: we,
  merge: ve,
  extend: Nn,
  trim: Dn,
  stripBOM: Un,
  inherits: Ln,
  toFlatObject: Fn,
  kindOf: Je,
  kindOfTest: k,
  endsWith: Bn,
  toArray: jn,
  forEachEntry: In,
  matchAll: qn,
  isHTMLForm: Hn,
  hasOwnProperty: me,
  hasOwnProp: me,
  // an alias to avoid ESLint no-prototype-builtins detection
  hasOwnInPrototypeChain: ye,
  getSafeProp: ln,
  toSafeFlatObject: un,
  reduceDescriptors: Lt,
  freezeMethods: vn,
  toObjectSet: Vn,
  toCamelCase: Mn,
  noop: Wn,
  toFiniteNumber: Jn,
  findKey: Nt,
  global: Y,
  isContextDefined: Ut,
  isSpecCompliantForm: Kn,
  toJSONObject: Xn,
  isAsyncFn: Gn,
  isThenable: Qn,
  setImmediate: Ft,
  asap: Zn,
  isIterable: Bt,
  isSafeIterable: Yn
}, er = a.toObjectSet([
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
]), tr = (e) => {
  const t = {};
  let n, r, s;
  return e && e.split(`
`).forEach(function(i) {
    s = i.indexOf(":"), n = i.substring(0, s).trim().toLowerCase(), r = i.substring(s + 1).trim();
    const c = a.hasOwnProp(t, n);
    !n || c && a.hasOwnProp(er, n) || (n === "set-cookie" ? c ? t[n].push(r) : t[n] = [r] : t[n] = c ? t[n] + ", " + r : r);
  }), t;
};
function nr(e) {
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
const rr = new RegExp("[\\u0000-\\u0008\\u000a-\\u001f\\u007f]+", "g"), sr = new RegExp("[^\\u0009\\u0020-\\u007e\\u0080-\\u00ff]+", "g");
function Ke(e, t) {
  return a.isArray(e) ? e.map((n) => Ke(n, t)) : nr(String(e).replace(t, ""));
}
const or = (e) => Ke(e, rr), ir = (e) => Ke(e, sr);
function jt(e) {
  const t = /* @__PURE__ */ Object.create(null);
  return a.forEach(e.toJSON(), (n, r) => {
    t[r] = ir(n);
  }), t;
}
const at = Symbol("internals");
function de(e) {
  return e && String(e).trim().toLowerCase();
}
function Pe(e) {
  return e === !1 || e == null ? e : a.isArray(e) ? e.map(Pe) : or(String(e));
}
function ar(e) {
  const t = /* @__PURE__ */ Object.create(null), n = /([^\s,;=]+)\s*(?:=\s*([^,;]+))?/g;
  let r;
  for (; r = n.exec(e); )
    t[r[1]] = r[2];
  return t;
}
const cr = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;
function ke(e) {
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
function lr(e) {
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
function ur(e) {
  const t = /* @__PURE__ */ Object.create(null), n = String(e);
  let r = 0, s = !1, o = !1;
  function i(c) {
    const l = ke(n.slice(r, c)), d = l.indexOf("=");
    if (d < 1)
      return;
    const f = ke(l.slice(0, d));
    if (!cr.test(f))
      return;
    const p = f.toLowerCase();
    if (p === "__proto__" || p === "constructor" || p === "prototype")
      return;
    const y = ke(l.slice(d + 1));
    t[p] = lr(y);
  }
  for (let c = 0; c < n.length; c++) {
    const l = n.charCodeAt(c);
    s ? o ? o = !1 : l === 92 ? o = !0 : l === 34 && (s = !1) : l === 34 ? s = !0 : (l === 44 || l === 59) && (i(c), r = c + 1);
  }
  return i(n.length), t;
}
const fr = (e) => /^[-_a-zA-Z0-9^`|~,!#$%&'*+.]+$/.test(e.trim());
function Ie(e, t, n, r, s) {
  if (a.isFunction(r))
    return r.call(this, t, n);
  if (s && (t = n), !!a.isString(t)) {
    if (a.isString(r))
      return t.indexOf(r) !== -1;
    if (a.isRegExp(r))
      return r.test(t);
  }
}
function dr(e) {
  return e.trim().toLowerCase().replace(/([a-z\d])(\w*)/g, (t, n, r) => n.toUpperCase() + r);
}
function pr(e, t) {
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
let L = class {
  constructor(t) {
    t && this.set(t);
  }
  set(t, n, r) {
    const s = this;
    function o(c, l, d) {
      const f = de(l);
      if (!f)
        return;
      const p = a.findKey(s, f);
      (!p || s[p] === void 0 || d === !0 || d === void 0 && s[p] !== !1) && (s[p || l] = Pe(c));
    }
    const i = (c, l) => a.forEach(c, (d, f) => o(d, f, l));
    if (a.isPlainObject(t) || t instanceof this.constructor)
      i(t, n);
    else if (a.isString(t) && (t = t.trim()) && !fr(t))
      i(tr(t), n);
    else if (a.isObject(t) && a.isSafeIterable(t)) {
      let c = /* @__PURE__ */ Object.create(null), l, d;
      for (const f of t) {
        if (!a.isArray(f))
          throw new TypeError("Object iterator must return a key-value pair");
        d = f[0], a.hasOwnProp(c, d) ? (l = c[d], c[d] = a.isArray(l) ? [...l, f[1]] : [l, f[1]]) : c[d] = f[1];
      }
      i(c, n);
    } else
      t != null && o(n, t, r);
    return this;
  }
  get(t, n) {
    if (t = de(t), t) {
      const r = a.findKey(this, t);
      if (r) {
        const s = this[r];
        if (!n)
          return s;
        if (n === !0)
          return ar(s);
        if (a.isFunction(n))
          return n.call(this, s, r);
        if (a.isRegExp(n))
          return n.exec(s);
        throw new TypeError("parser must be boolean|regexp|function");
      }
    }
  }
  has(t, n) {
    if (t = de(t), t) {
      const r = a.findKey(this, t);
      return !!(r && this[r] !== void 0 && (!n || Ie(this, this[r], r, n)));
    }
    return !1;
  }
  delete(t, n) {
    const r = this;
    let s = !1;
    function o(i) {
      if (i = de(i), i) {
        const c = a.findKey(r, i);
        c && (!n || Ie(r, r[c], c, n)) && (delete r[c], s = !0);
      }
    }
    return a.isArray(t) ? t.forEach(o) : o(t), s;
  }
  clear(t) {
    const n = Object.keys(this);
    let r = n.length, s = !1;
    for (; r--; ) {
      const o = n[r];
      (!t || Ie(this, this[o], o, t, !0)) && (delete this[o], s = !0);
    }
    return s;
  }
  normalize(t) {
    const n = this, r = {};
    return a.forEach(this, (s, o) => {
      const i = a.findKey(r, o);
      if (i) {
        n[i] = Pe(s), delete n[o];
        return;
      }
      const c = t ? dr(o) : String(o).trim();
      c !== o && delete n[o], n[c] = Pe(s), r[c] = !0;
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
    return ur(t);
  }
  static concat(t, ...n) {
    const r = new this(t);
    return n.forEach((s) => r.set(s)), r;
  }
  static accessor(t) {
    const r = (this[at] = this[at] = {
      accessors: {}
    }).accessors, s = this.prototype;
    function o(i) {
      const c = de(i);
      r[c] || (pr(s, i), r[c] = !0);
    }
    return a.isArray(t) ? t.forEach(o) : o(t), this;
  }
};
L.accessor([
  "Content-Type",
  "Content-Length",
  "Accept",
  "Accept-Encoding",
  "User-Agent",
  "Authorization"
]);
a.reduceDescriptors(L.prototype, ({ value: e }, t) => {
  let n = t[0].toUpperCase() + t.slice(1);
  return {
    get: () => e,
    set(r) {
      this[n] = r;
    }
  };
});
a.freezeMethods(L);
const Ce = "[REDACTED ****]";
function hr(e) {
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
function mr(e, t) {
  const n = new Set(t.map((o) => String(o).toLowerCase())), r = [], s = (o) => {
    if (o === null || typeof o != "object" || a.isBuffer(o)) return o;
    if (r.indexOf(o) !== -1) return;
    o instanceof L && (o = o.toJSON()), r.push(o);
    let i;
    if (a.isArray(o))
      i = [], o.forEach((c, l) => {
        const d = s(c);
        a.isUndefined(d) || (i[l] = d);
      });
    else {
      if (!a.isPlainObject(o) && hr(o))
        return r.pop(), o;
      i = /* @__PURE__ */ Object.create(null);
      for (const [c, l] of Object.entries(o)) {
        const d = n.has(c.toLowerCase()) ? Ce : s(l);
        a.isUndefined(d) || (i[c] = d);
      }
    }
    return r.pop(), i;
  };
  return s(e);
}
function ct(e) {
  try {
    return String(e);
  } catch {
    return "";
  }
}
function yr(e) {
  return e.errors.map((n) => {
    try {
      return n && n.message ? ct(n.message) : ct(n);
    } catch {
      return "";
    }
  }).filter(Boolean).join("; ") || e.name || "AggregateError";
}
let h = class kt extends Error {
  static from(t, n, r, s, o, i) {
    let c = t.message;
    !c && a.isArray(t.errors) && t.errors.length && (c = yr(t));
    const l = new kt(c, n || t.code, r, s, o);
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
    const t = this.config, n = t && a.hasOwnProp(t, "redact") ? t.redact : void 0, r = a.isArray(n) && n.length > 0 ? mr(t, n) : a.toJSONObject(t);
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
const br = null, It = 100;
function Ve(e) {
  return a.isPlainObject(e) || a.isArray(e);
}
function qt(e) {
  return a.endsWith(e, "[]") ? e.slice(0, -2) : e;
}
function qe(e, t, n) {
  return e ? e.concat(t).map(function(s, o) {
    return s = qt(s), !n && o ? "[" + s + "]" : s;
  }).join(n ? "." : "") : t;
}
function wr(e) {
  return a.isArray(e) && !e.some(Ve);
}
const gr = a.toFlatObject(a, {}, null, function(t) {
  return /^is[A-Z]/.test(t);
});
function Ue(e, t, n) {
  if (!a.isObject(e))
    throw new TypeError("target must be an object");
  t = t || new FormData();
  const r = (m, g) => {
    const b = a.getSafeProp(n, m);
    return a.isUndefined(b) ? g : b;
  }, s = r("metaTokens", !0), o = r("visitor") || S, i = r("dots", !1), c = r("indexes", !1), l = r("Blob") || typeof Blob < "u" && Blob, d = r("maxDepth", It), f = l && a.isSpecCompliantForm(t), p = [];
  if (!a.isFunction(o))
    throw new TypeError("visitor must be a function");
  function y(m) {
    if (m === null) return "";
    if (a.isDate(m))
      return m.toISOString();
    if (a.isBoolean(m))
      return m.toString();
    if (!f && a.isBlob(m))
      throw new h("Blob is not supported. Use a Buffer instead.");
    if (a.isArrayBuffer(m) || a.isTypedArray(m)) {
      if (f && typeof l == "function")
        return new l([m]);
      throw new h(
        "Blob is not supported. Use a Buffer instead.",
        h.ERR_NOT_SUPPORT
      );
    }
    return m;
  }
  function E(m) {
    if (m > d)
      throw new h(
        "Object is too deeply nested (" + m + " levels). Max depth: " + d,
        h.ERR_FORM_DATA_DEPTH_EXCEEDED
      );
  }
  function R(m, g) {
    if (d === 1 / 0)
      return JSON.stringify(m);
    const b = [];
    return JSON.stringify(m, function(D, _) {
      if (!a.isObject(_))
        return _;
      for (; b.length && b[b.length - 1] !== this; )
        b.pop();
      return b.push(_), E(g + b.length - 1), _;
    });
  }
  function S(m, g, b) {
    let T = m;
    if (a.isReactNative(t) && a.isReactNativeBlob(m))
      return t.append(qe(b, g, i), y(m)), !1;
    if (m && !b && typeof m == "object") {
      if (a.endsWith(g, "{}"))
        g = s ? g : g.slice(0, -2), m = R(m, 1);
      else if (a.isArray(m) && wr(m) || (a.isFileList(m) || a.endsWith(g, "[]")) && (T = a.toArray(m)))
        return g = qt(g), T.forEach(function(_, q) {
          !(a.isUndefined(_) || _ === null) && t.append(
            // eslint-disable-next-line no-nested-ternary
            c === !0 ? qe([g], q, i) : c === null ? g : g + "[]",
            y(_)
          );
        }), !1;
    }
    return Ve(m) ? !0 : (t.append(qe(b, g, i), y(m)), !1);
  }
  const P = Object.assign(gr, {
    defaultVisitor: S,
    convertValue: y,
    isVisitable: Ve
  });
  function u(m, g, b = 0) {
    if (!a.isUndefined(m)) {
      if (E(b), p.indexOf(m) !== -1)
        throw new Error("Circular reference detected in " + g.join("."));
      p.push(m), a.forEach(m, function(D, _) {
        (!(a.isUndefined(D) || D === null) && o.call(t, D, a.isString(_) ? _.trim() : _, g, P)) === !0 && u(D, g ? g.concat(_) : [_], b + 1);
      }), p.pop();
    }
  }
  if (!a.isObject(e))
    throw new TypeError("data must be an object");
  return u(e), t;
}
function lt(e) {
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
function Xe(e, t) {
  this._pairs = [], e && Ue(e, this, t);
}
const Ht = Xe.prototype;
Ht.append = function(t, n) {
  this._pairs.push([t, n]);
};
Ht.toString = function(t) {
  const n = t ? (r) => t.call(this, r, lt) : lt;
  return this._pairs.map(function(s) {
    return n(s[0]) + "=" + n(s[1]);
  }, "").join("&");
};
function Er(e) {
  return encodeURIComponent(e).replace(/%3A/gi, ":").replace(/%24/g, "$").replace(/%2C/gi, ",").replace(/%20/g, "+");
}
function Mt(e, t, n) {
  if (!t)
    return e;
  e = e || "";
  const r = a.isFunction(n) ? {
    serialize: n
  } : n, s = a.getSafeProp(r, "encode") || Er, o = a.getSafeProp(r, "serialize");
  let i;
  if (o ? i = o(t, r) : i = a.isURLSearchParams(t) ? t.toString() : new Xe(t, r).toString(s), i) {
    const c = e.indexOf("#");
    c !== -1 && (e = e.slice(0, c)), e += (e.indexOf("?") === -1 ? "?" : "&") + i;
  }
  return e;
}
const pe = Symbol("internals");
function $t(e) {
  return e ? e.length : 0;
}
function ut(e) {
  if (e)
    for (; e.length && e[e.length - 1] === null; )
      e.pop();
}
function he(e, t) {
  const n = e.handlers, r = $t(n);
  n !== t.handlersRef ? (t.handlersRef = n, t.handlerEntries.clear()) : r !== t.handlersLength && (r ? t.handlerEntries.forEach(function(o, i) {
    n[o.index] !== o.handler && t.handlerEntries.delete(i);
  }) : t.handlerEntries.clear()), t.handlersLength = r;
}
class ft {
  constructor() {
    this.handlers = [], this[pe] = {
      handlersRef: this.handlers,
      handlersLength: this.handlers.length,
      handlerEntries: /* @__PURE__ */ new Map(),
      iterationDepth: 0,
      nextId: 0
    };
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
    const s = {
      fulfilled: t,
      rejected: n,
      synchronous: r ? r.synchronous : !1,
      runWhen: r ? r.runWhen : null
    }, o = this[pe];
    this.handlers == null && (this.handlers = []), he(this, o);
    const i = o.nextId++;
    return this.handlers.push(s), o.handlerEntries.set(i, {
      handler: s,
      index: this.handlers.length - 1
    }), o.handlersLength = this.handlers.length, i;
  }
  /**
   * Remove an interceptor from the stack
   *
   * @param {Number} id The ID that was returned by `use`
   *
   * @returns {void}
   */
  eject(t) {
    const n = this[pe];
    he(this, n);
    const r = n.handlerEntries.get(t);
    if (r) {
      if (n.handlerEntries.delete(t), this.handlers[r.index] !== r.handler)
        return;
      this.handlers[r.index] = null, n.iterationDepth || (ut(this.handlers), n.handlersLength = this.handlers.length);
    }
  }
  /**
   * Clear all interceptors from the stack
   *
   * @returns {void}
   */
  clear() {
    this.handlers && (this.handlers = [], he(this, this[pe]));
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
    const n = this[pe];
    he(this, n), n.iterationDepth++;
    try {
      a.forEach(this.handlers, function(s) {
        s !== null && t(s);
      });
    } finally {
      --n.iterationDepth || (he(this, n), ut(this.handlers), n.handlersLength = $t(this.handlers));
    }
  }
}
const Ge = {
  silentJSONParsing: !0,
  forcedJSONParsing: !0,
  clarifyTimeoutError: !1,
  legacyInterceptorReqResOrdering: !0,
  advertiseZstdAcceptEncoding: !1,
  validateStatusUndefinedResolves: !0
}, Rr = typeof URLSearchParams < "u" ? URLSearchParams : Xe, Or = typeof FormData < "u" ? FormData : null, Sr = typeof Blob < "u" ? Blob : null, _r = {
  isBrowser: !0,
  classes: {
    URLSearchParams: Rr,
    FormData: Or,
    Blob: Sr
  },
  protocols: ["http", "https", "file", "blob", "url", "data"]
}, Qe = typeof window < "u" && typeof document < "u", We = typeof navigator == "object" && navigator || void 0, Ar = Qe && (!We || ["ReactNative", "NativeScript", "NS"].indexOf(We.product) < 0), Pr = typeof WorkerGlobalScope < "u" && // eslint-disable-next-line no-undef
self instanceof WorkerGlobalScope && typeof self.importScripts == "function", Tr = Qe && window.location.href || "http://localhost", xr = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  hasBrowserEnv: Qe,
  hasStandardBrowserEnv: Ar,
  hasStandardBrowserWebWorkerEnv: Pr,
  navigator: We,
  origin: Tr
}, Symbol.toStringTag, { value: "Module" })), x = {
  ...xr,
  ..._r
};
function Cr(e, t) {
  return Ue(e, new x.classes.URLSearchParams(), {
    visitor: function(n, r, s, o) {
      return x.isNode && a.isBuffer(n) ? (this.append(r, n.toString("base64")), !1) : o.defaultVisitor.apply(this, arguments);
    },
    ...t
  });
}
const dt = It;
function zt(e) {
  if (e > dt)
    throw new h(
      "FormData field is too deeply nested (" + e + " levels). Max depth: " + dt,
      h.ERR_FORM_DATA_DEPTH_EXCEEDED
    );
}
function Dr(e) {
  const t = [], n = /[^.[\]]+|\[([^.[\]]*)]/g;
  let r;
  for (; (r = n.exec(e)) !== null; )
    zt(t.length), t.push(r[0] === "[]" ? "" : r[1] || r[0]);
  return t;
}
function Nr(e) {
  const t = {}, n = Object.keys(e);
  let r;
  const s = n.length;
  let o;
  for (r = 0; r < s; r++)
    o = n[r], t[o] = e[o];
  return t;
}
function vt(e) {
  function t(n, r, s, o) {
    zt(o);
    let i = n[o++];
    if (i === "__proto__") return !0;
    const c = Number.isFinite(+i), l = o >= n.length;
    return i = !i && a.isArray(s) ? s.length : i, l ? (a.hasOwnProp(s, i) ? s[i] = a.isArray(s[i]) ? s[i].concat(r) : [s[i], r] : s[i] = r, !c) : ((!a.hasOwnProp(s, i) || !a.isObject(s[i])) && (s[i] = []), t(n, r, s[i], o) && a.isArray(s[i]) && (s[i] = Nr(s[i])), !c);
  }
  if (a.isFormData(e) && a.isFunction(e.entries)) {
    const n = {};
    return a.forEachEntry(e, (r, s) => {
      t(Dr(r), s, n, 0);
    }), n;
  }
  return null;
}
const Vt = Object.freeze([
  "get",
  "delete",
  "head",
  "options",
  "post",
  "put",
  "patch",
  "purge",
  "link",
  "unlink",
  "query"
]), ie = (e, t) => e != null && a.hasOwnProp(e, t) ? e[t] : void 0;
function Ur(e, t, n) {
  if (a.isString(e))
    try {
      return (t || JSON.parse)(e), a.trim(e);
    } catch (r) {
      if (r.name !== "SyntaxError")
        throw r;
    }
  return (n || JSON.stringify)(e);
}
const ge = {
  transitional: Ge,
  adapter: ["xhr", "http", "fetch"],
  transformRequest: [
    function(t, n) {
      const r = n.getContentType() || "", s = r.indexOf("application/json") > -1, o = a.isObject(t);
      if (o && a.isHTMLForm(t) && (t = new FormData(t)), a.isFormData(t))
        return s ? JSON.stringify(vt(t)) : t;
      if (a.isArrayBuffer(t) || a.isBuffer(t) || a.isStream(t) || a.isFile(t) || a.isBlob(t) || a.isReadableStream(t))
        return t;
      if (a.isArrayBufferView(t))
        return t.buffer;
      if (a.isURLSearchParams(t))
        return n.setContentType("application/x-www-form-urlencoded;charset=utf-8", !1), t.toString();
      let c;
      if (o) {
        const l = ie(this, "formSerializer");
        if (r.indexOf("application/x-www-form-urlencoded") > -1)
          return Cr(t, l).toString();
        if ((c = a.isFileList(t)) || r.indexOf("multipart/form-data") > -1) {
          const d = ie(this, "env"), f = d && d.FormData;
          return Ue(
            c ? { "files[]": t } : t,
            f && new f(),
            l
          );
        }
      }
      return o || s ? (n.setContentType("application/json", !1), Ur(t)) : t;
    }
  ],
  transformResponse: [
    function(t) {
      const n = ie(this, "transitional") || ge.transitional, r = n && n.forcedJSONParsing, s = ie(this, "responseType"), o = s === "json";
      if (a.isResponse(t) || a.isReadableStream(t))
        return t;
      if (t && a.isString(t) && (r && !s || o)) {
        const c = !(n && n.silentJSONParsing) && o;
        try {
          return JSON.parse(t, ie(this, "parseReviver"));
        } catch (l) {
          if (c)
            throw l.name === "SyntaxError" ? h.from(l, h.ERR_BAD_RESPONSE, this, null, ie(this, "response")) : l;
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
a.forEach(Vt, (e) => {
  ge.headers[e] = {};
});
function He(e, t) {
  const n = this || ge, r = t || n, s = L.from(r.headers);
  let o = r.data;
  return a.forEach(e, function(c) {
    o = c.call(n, o, s.normalize(), t ? t.status : void 0);
  }), s.normalize(), o;
}
function Wt(e) {
  return !!(e && e.__CANCEL__);
}
let Ee = class extends h {
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
function Jt(e, t, n) {
  const r = n.config.validateStatus;
  !n.status || !r || r(n.status) ? e(n) : t(new h(
    "Request failed with status code " + n.status,
    n.status >= 400 && n.status < 500 ? h.ERR_BAD_REQUEST : h.ERR_BAD_RESPONSE,
    n.config,
    n.request,
    n
  ));
}
const Lr = /[\t\n\r]/g;
function Kt(e) {
  if (typeof e != "string")
    return e;
  let t = 0;
  for (; t < e.length && e.charCodeAt(t) <= 32; )
    t++;
  return e.slice(t).replace(Lr, "");
}
function Me(e) {
  const t = /^([-+\w]{1,25}):(?:\/\/)?/.exec(e);
  return t && t[1] || "";
}
function Fr(e, t) {
  e = e || 10;
  const n = new Array(e), r = new Array(e);
  let s = 0, o = 0, i;
  return t = t !== void 0 ? t : 1e3, function(l) {
    const d = Date.now(), f = r[o];
    i || (i = d), n[s] = l, r[s] = d;
    let p = o, y = 0;
    for (; p !== s; )
      y += n[p++], p = p % e;
    if (s = (s + 1) % e, s === o && (o = (o + 1) % e), d - i < t)
      return;
    const E = f && d - f;
    return E ? Math.round(y * 1e3 / E) : void 0;
  };
}
function Br(e, t) {
  let n = 0, r = 1e3 / t, s, o;
  const i = (f, p = Date.now()) => {
    n = p, s = null, o && (clearTimeout(o), o = null), e(...f);
  };
  return [(...f) => {
    const p = Date.now(), y = p - n;
    y >= r ? i(f, p) : (s = f, o || (o = setTimeout(() => {
      o = null, i(s);
    }, r - y)));
  }, () => s && i(s), (...f) => i(f)];
}
const De = (e, t, n = 3) => {
  let r = 0;
  const s = Fr(50, 250);
  return Br((o) => {
    if (!o || !a.isNumber(o.loaded))
      return;
    const i = o.loaded, c = o.lengthComputable ? o.total : void 0, l = Math.max(0, c != null ? Math.min(i, c) : i), d = Math.max(0, l - r), f = s(d);
    r = Math.max(r, l);
    const p = {
      loaded: l,
      total: c,
      progress: c ? l / c : void 0,
      bytes: d,
      rate: f || void 0,
      estimated: f && c ? (c - l) / f : void 0,
      event: o,
      lengthComputable: c != null,
      [t ? "download" : "upload"]: !0
    };
    e(p);
  }, n);
}, pt = (e, t) => {
  const n = e != null;
  return [
    (r) => t[0]({
      lengthComputable: n,
      total: e,
      loaded: r
    }),
    t[1]
  ];
}, ht = (e, t = a.asap) => (...n) => t(() => e(...n)), jr = x.hasStandardBrowserEnv ? /* @__PURE__ */ ((e, t) => (n) => (n = new URL(n, x.origin), e.protocol === n.protocol && e.host === n.host && (t || e.port === n.port)))(
  new URL(x.origin),
  x.navigator && /(msie|trident)/i.test(x.navigator.userAgent)
) : () => !0, kr = x.hasStandardBrowserEnv ? (
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
function Ir(e) {
  return typeof e != "string" ? !1 : /^([a-z][a-z\d+\-.]*:)?\/\//i.test(e);
}
function qr(e, t) {
  if (!t)
    return e;
  let n = e.length;
  for (; n > 0 && e.charCodeAt(n - 1) === 47; )
    n--;
  return e.slice(0, n) + "/" + t.replace(/^\/+/, "");
}
const Hr = /^https?:(?!\/\/)/i;
function Mr(e) {
  return e && e.replace(/(^|&)([^=&]*=)?[^&]+/g, (t, n, r = "") => `${n}${r}${Ce}`);
}
function $r(e) {
  const t = e.replace(/^(https?:\/{0,2})[^/?#]*@/i, `$1${Ce}@`), n = t.indexOf("#"), s = (n === -1 ? t : t.slice(0, n)).replace(
    /([?&][^=&#]*=)[^&#]*/g,
    `$1${Ce}`
  );
  return n === -1 ? s : `${s}#${Mr(t.slice(n + 1))}`;
}
function mt(e, t) {
  if (typeof e == "string") {
    const n = Kt(e);
    if (Hr.test(n))
      throw new h(
        `Invalid URL ${JSON.stringify($r(n))}: missing "//" after protocol`,
        h.ERR_INVALID_URL,
        t
      );
  }
}
function Xt(e, t, n, r) {
  mt(t, r);
  let s = !Ir(t);
  return e && (s || n === !1) ? (mt(e, r), qr(e, t)) : t;
}
const yt = (e) => e instanceof L ? { ...e } : e, zr = (e) => Object.getOwnPropertySymbols && Object.getOwnPropertyDescriptor ? Object.keys(e).concat(
  Object.getOwnPropertySymbols(e).filter(
    (t) => Object.getOwnPropertyDescriptor(e, t).enumerable
  )
) : Object.keys(e);
function re(e, t) {
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
  function r(f, p, y, E) {
    return a.isPlainObject(f) && a.isPlainObject(p) ? a.merge.call({ caseless: E }, f, p) : a.isPlainObject(p) ? a.merge({}, p) : a.isArray(p) ? p.slice() : p;
  }
  function s(f, p, y, E) {
    if (a.isUndefined(p)) {
      if (!a.isUndefined(f))
        return r(void 0, f, y, E);
    } else return r(f, p, y, E);
  }
  function o(f, p) {
    if (!a.isUndefined(p))
      return r(void 0, p);
  }
  function i(f, p) {
    if (a.isUndefined(p)) {
      if (!a.isUndefined(f))
        return r(void 0, f);
    } else return r(void 0, p);
  }
  function c(f) {
    const p = a.hasOwnProp(t, "transitional") ? t.transitional : void 0;
    if (!a.isUndefined(p))
      if (a.isPlainObject(p)) {
        if (a.hasOwnProp(p, f))
          return p[f];
      } else
        return;
    const y = a.hasOwnProp(e, "transitional") ? e.transitional : void 0;
    if (a.isPlainObject(y) && a.hasOwnProp(y, f))
      return y[f];
  }
  function l(f, p, y) {
    if (a.hasOwnProp(t, y))
      return r(f, p);
    if (a.hasOwnProp(e, y))
      return r(void 0, f);
  }
  const d = {
    url: o,
    method: o,
    data: o,
    baseURL: i,
    transformRequest: i,
    transformResponse: i,
    paramsSerializer: i,
    timeout: i,
    timeoutErrorMessage: i,
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
    headers: (f, p, y) => s(yt(f), yt(p), y, !0)
  };
  return a.forEach(zr({ ...e, ...t }), function(p) {
    if (p === "__proto__" || p === "constructor" || p === "prototype") return;
    const y = a.hasOwnProp(d, p) ? d[p] : s, E = a.hasOwnProp(e, p) ? e[p] : void 0, R = a.hasOwnProp(t, p) ? t[p] : void 0, S = y(E, R, p);
    a.isUndefined(S) && y !== l || (n[p] = S);
  }), a.hasOwnProp(t, "validateStatus") && a.isUndefined(t.validateStatus) && c("validateStatusUndefinedResolves") === !1 && (a.hasOwnProp(e, "validateStatus") ? n.validateStatus = r(void 0, e.validateStatus) : delete n.validateStatus), n;
}
const vr = ["content-type", "content-length"];
function Vr(e, t, n) {
  if (n !== "content-only") {
    e.set(t);
    return;
  }
  Object.entries(t || {}).forEach(([r, s]) => {
    vr.includes(r.toLowerCase()) && e.set(r, s);
  });
}
const Wr = (e) => encodeURIComponent(e).replace(
  /%([0-9A-F]{2})/gi,
  (t, n) => String.fromCharCode(parseInt(n, 16))
);
function Gt(e) {
  const t = re({}, e), n = (y) => a.hasOwnProp(t, y) ? t[y] : void 0, r = n("data");
  let s = n("withXSRFToken");
  const o = n("xsrfHeaderName"), i = n("xsrfCookieName");
  let c = n("headers");
  const l = n("auth"), d = n("baseURL"), f = n("allowAbsoluteUrls"), p = n("url");
  if (t.headers = c = L.from(c), t.url = Mt(
    Xt(d, p, f, t),
    n("params"),
    n("paramsSerializer")
  ), l) {
    const y = a.getSafeProp(l, "username") || "", E = a.getSafeProp(l, "password") || "";
    try {
      c.set(
        "Authorization",
        "Basic " + btoa(y + ":" + (E ? Wr(E) : ""))
      );
    } catch (R) {
      throw h.from(R, h.ERR_BAD_OPTION_VALUE, e);
    }
  }
  if (a.isFormData(r)) {
    const y = a.getSafeProp(r, "getHeaders");
    x.hasStandardBrowserEnv || x.hasStandardBrowserWebWorkerEnv || a.isReactNative(r) ? c.setContentType(void 0) : a.isFunction(y) && Vr(c, y.call(r), n("formDataHeaderPolicy"));
  }
  if (x.hasStandardBrowserEnv && (a.isFunction(s) && (s = s(t)), s === !0 || s == null && jr(t.url))) {
    const E = o && i && kr.read(i);
    E && c.set(o, E);
  }
  return t;
}
const Jr = typeof XMLHttpRequest < "u", Kr = Jr && function(e) {
  return new Promise(function(n, r) {
    const s = Gt(e);
    let o = s.data;
    const i = L.from(s.headers).normalize();
    let { responseType: c, onUploadProgress: l, onDownloadProgress: d } = s, f, p, y, E, R, S;
    function P() {
      E && E(), R && R(), s.cancelToken && s.cancelToken.unsubscribe(f), s.signal && s.signal.removeEventListener("abort", f);
    }
    let u = new XMLHttpRequest();
    u.open(s.method.toUpperCase(), s.url, !0), u.timeout = s.timeout;
    function m(b) {
      if (!u)
        return;
      if (u.status === 0 && (Me(Kt(s.url)) || Me(x.origin)) !== "file" && !(u.responseURL && u.responseURL.startsWith("file:"))) {
        r(new h("Request aborted", h.ECONNABORTED, e, u)), P(), u = null;
        return;
      }
      try {
        b ? S && S(b) : R && R();
      } catch (q) {
        setTimeout(() => {
          throw q;
        });
      }
      if (!u)
        return;
      const T = L.from(
        "getAllResponseHeaders" in u && u.getAllResponseHeaders()
      ), _ = {
        data: !c || c === "text" || c === "json" ? u.responseText : u.response,
        status: u.status,
        statusText: u.statusText,
        headers: T,
        config: e,
        request: u
      };
      Jt(
        function(G) {
          n(G), P();
        },
        function(G) {
          r(G), P();
        },
        _
      ), u = null;
    }
    "onloadend" in u ? u.onloadend = m : u.onreadystatechange = function() {
      !u || u.readyState !== 4 || u.status === 0 && !(u.responseURL && u.responseURL.startsWith("file:")) || setTimeout(m);
    }, u.onabort = function() {
      u && (r(new h("Request aborted", h.ECONNABORTED, e, u)), P(), u = null);
    }, u.onerror = function(T) {
      const D = T && T.message ? T.message : "Network Error", _ = new h(D, h.ERR_NETWORK, e, u);
      _.event = T || null, r(_), P(), u = null;
    }, u.ontimeout = function() {
      let T = s.timeout ? "timeout of " + s.timeout + "ms exceeded" : "timeout exceeded";
      const D = s.transitional || Ge;
      s.timeoutErrorMessage && (T = s.timeoutErrorMessage), r(
        new h(
          T,
          D.clarifyTimeoutError ? h.ETIMEDOUT : h.ECONNABORTED,
          e,
          u
        )
      ), P(), u = null;
    }, o === void 0 && i.setContentType(null), "setRequestHeader" in u && a.forEach(jt(i), function(T, D) {
      u.setRequestHeader(D, T);
    }), a.isUndefined(s.withCredentials) || (u.withCredentials = !!s.withCredentials), c && c !== "json" && (u.responseType = s.responseType), d && ([y, R, S] = De(
      d,
      !0
    ), u.addEventListener("progress", y)), l && u.upload && ([p, E] = De(l), u.upload.addEventListener("progress", p), u.upload.addEventListener("loadend", E)), (s.cancelToken || s.signal) && (f = (b) => {
      u && (r(!b || b.type ? new Ee(null, e, u) : b), u.abort(), P(), u = null);
    }, s.cancelToken && s.cancelToken.subscribe(f), s.signal && (s.signal.aborted ? f() : s.signal.addEventListener("abort", f)));
    const g = Me(s.url);
    if (g && !x.protocols.includes(g)) {
      r(
        new h(
          "Unsupported protocol " + g + ":",
          h.ERR_BAD_REQUEST,
          e
        )
      ), P();
      return;
    }
    u.send(o || null);
  });
}, Xr = (e, t) => {
  if (e = e ? e.filter(Boolean) : [], !t && !e.length)
    return;
  const n = new AbortController();
  let r = !1;
  const s = function(l) {
    if (!r) {
      r = !0, i();
      const d = l instanceof Error ? l : this.reason;
      n.abort(
        d instanceof h ? d : new Ee(d instanceof Error ? d.message : d)
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
}, Gr = function* (e, t) {
  let n = e.byteLength;
  if (n < t) {
    yield e;
    return;
  }
  let r = 0, s;
  for (; r < n; )
    s = r + t, yield e.slice(r, s), r = s;
}, Qr = async function* (e, t) {
  for await (const n of Zr(e))
    yield* Gr(n, t);
}, Zr = async function* (e) {
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
}, bt = (e, t, n, r) => {
  const s = Qr(e, t);
  let o = 0, i, c = (l) => {
    i || (i = !0, r && r(l));
  };
  return new ReadableStream(
    {
      async pull(l) {
        try {
          const { done: d, value: f } = await s.next();
          if (d) {
            c(), l.close();
            return;
          }
          let p = f.byteLength;
          if (n) {
            let y = o += p;
            n(y);
          }
          l.enqueue(new Uint8Array(f));
        } catch (d) {
          throw c(d), d;
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
}, wt = (e) => e >= 48 && e <= 57 || e >= 65 && e <= 70 || e >= 97 && e <= 102, Qt = (e, t, n) => t + 2 < n && wt(e.charCodeAt(t + 1)) && wt(e.charCodeAt(t + 2)), gt = (e) => e <= 57 ? e - 48 : (e & 223) - 55, Yr = (e) => e >= 65 && e <= 90 || // A-Z
e >= 97 && e <= 122 || // a-z
e >= 48 && e <= 57 || // 0-9
e === 43 || // +
e === 47 || // /
e === 45 || // - (base64url)
e === 95, es = (e) => e === 9 || e === 10 || e === 12 || e === 13 || e === 32, ts = (e) => {
  const t = Math.floor(e / 4), n = e % 4;
  return t * 3 + (n === 2 ? 1 : n === 3 ? 2 : 0);
}, ns = (e) => {
  const t = e.length;
  let n = 0;
  return t > 0 && e.charCodeAt(t - 1) === 61 && (n++, t > 1 && e.charCodeAt(t - 2) === 61 && n++), Math.floor((t - n) * 3 / 4);
}, rs = (e) => {
  const t = e.length;
  let n = 0, r = 0, s = !1;
  for (let o = 0; o < t; o++) {
    let i = e.charCodeAt(o);
    if (i === 37 && Qt(e, o, t) && (i = gt(e.charCodeAt(o + 1)) * 16 + gt(e.charCodeAt(o + 2)), o += 2), !es(i)) {
      if (i === 61) {
        r++;
        continue;
      }
      if (!Yr(i) || r > 0) {
        s = !0;
        continue;
      }
      n++;
    }
  }
  return s || r > 2 || r > 0 && (n + r) % 4 !== 0 || n % 4 === 1 ? ns(e) : ts(n);
}, ss = (e, t) => {
  if (!e || typeof e != "string" || !e.startsWith("data:")) return 0;
  const n = e.indexOf(",");
  if (n < 0) return 0;
  const r = e.slice(5, n), s = e.slice(n + 1);
  if (/;base64/i.test(r))
    return t(s);
  let i = 0;
  for (let c = 0, l = s.length; c < l; c++) {
    const d = s.charCodeAt(c);
    if (d === 37 && Qt(s, c, l))
      i += 1, c += 2;
    else if (d < 128)
      i += 1;
    else if (d < 2048)
      i += 2;
    else if (d >= 55296 && d <= 56319 && c + 1 < l) {
      const f = s.charCodeAt(c + 1);
      f >= 56320 && f <= 57343 ? (i += 4, c++) : i += 3;
    } else
      i += 3;
  }
  return i;
};
function os(e) {
  const t = typeof e == "string" ? e.indexOf("#") : -1;
  return ss(
    t === -1 ? e : e.slice(0, t),
    rs
  );
}
const Ze = "1.20.0", Et = 64 * 1024, is = {
  cache: "default",
  redirect: "follow",
  referrer: "about:client",
  referrerPolicy: "",
  mode: "cors",
  integrity: "",
  keepalive: !1,
  priority: "auto",
  window: null
}, { isFunction: _e } = a, as = (e) => encodeURIComponent(e).replace(
  /%([0-9A-F]{2})/gi,
  (t, n) => String.fromCharCode(parseInt(n, 16))
), Rt = (e) => {
  if (!a.isString(e))
    return e;
  try {
    return decodeURIComponent(e);
  } catch {
    return e;
  }
}, Ot = (e, ...t) => {
  try {
    return !!e(...t);
  } catch {
    return !1;
  }
}, cs = (e) => {
  const t = e.indexOf("://");
  let n = e;
  return t !== -1 && (n = n.slice(t + 3)), n.includes("@") || n.includes(":");
}, ls = (e) => {
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
  const { fetch: s, Request: o, Response: i } = e, c = s ? _e(s) : typeof fetch == "function", l = _e(o), d = _e(i);
  if (!c)
    return !1;
  const f = c && _e(n), p = c && (typeof r == "function" ? /* @__PURE__ */ ((u) => (m) => u.encode(m))(new r()) : async (u) => new Uint8Array(await new o(u).arrayBuffer())), y = l && f && Ot(() => {
    let u = !1;
    const m = new o(x.origin, {
      body: new n(),
      method: "POST",
      get duplex() {
        return u = !0, "half";
      }
    }), g = m.headers.has("Content-Type");
    return m.body != null && m.body.cancel(), u && !g;
  }), E = d && f && Ot(() => a.isReadableStream(new i("").body)), R = {
    stream: E && ((u) => u.body)
  };
  c && ["text", "arrayBuffer", "blob", "formData", "stream"].forEach((u) => {
    !R[u] && (R[u] = (m, g) => {
      let b = m && m[u];
      if (b)
        return b.call(m);
      throw new h(
        `Response type '${u}' is not supported`,
        h.ERR_NOT_SUPPORT,
        g
      );
    });
  });
  const S = async (u) => {
    if (u == null)
      return 0;
    if (a.isBlob(u))
      return u.size;
    if (a.isSpecCompliantForm(u))
      return (await new o(x.origin, {
        method: "POST",
        body: u
      }).arrayBuffer()).byteLength;
    if (a.isArrayBufferView(u) || a.isArrayBuffer(u))
      return u.byteLength;
    if (a.isURLSearchParams(u) && (u = u + ""), a.isString(u))
      return (await p(u)).byteLength;
  }, P = async (u, m) => {
    const g = a.toFiniteNumber(u.getContentLength());
    return g ?? S(m);
  };
  return async (u) => {
    let {
      url: m,
      method: g,
      data: b,
      signal: T,
      cancelToken: D,
      timeout: _,
      onDownloadProgress: q,
      onUploadProgress: G,
      responseType: v,
      headers: V,
      withCredentials: Re = "same-origin",
      fetchOptions: Fe,
      maxContentLength: H,
      maxBodyLength: Oe,
      maxRedirects: nn
    } = Gt(u);
    const le = a.isNumber(H) && H > -1, Be = a.isNumber(Oe) && Oe > -1, rn = (O) => a.hasOwnProp(u, O) ? u[O] : void 0;
    let et = s || fetch;
    v = v ? (v + "").toLowerCase() : "text";
    let W = Xr(
      [T, D && D.toAbortSignal()],
      _
    ), C = null;
    const Q = W && W.unsubscribe && (() => {
      W.unsubscribe();
    });
    let oe, ue = null;
    const tt = () => new h(
      "Request body larger than maxBodyLength limit",
      h.ERR_BAD_REQUEST,
      u,
      C
    );
    try {
      let O;
      const B = rn("auth");
      if (B) {
        const w = a.getSafeProp(B, "username") || "", N = a.getSafeProp(B, "password") || "";
        O = {
          username: w,
          password: N
        };
      }
      if (cs(m)) {
        const w = new URL(m, x.origin);
        if (!O && (w.username || w.password)) {
          const N = Rt(w.username), J = Rt(w.password);
          O = {
            username: N,
            password: J
          };
        }
        (w.username || w.password) && (w.username = "", w.password = "", m = w.href);
      }
      if (O && (V.delete("authorization"), V.set(
        "Authorization",
        "Basic " + btoa(as((O.username || "") + ":" + (O.password || "")))
      )), le && typeof m == "string" && m.startsWith("data:") && os(m) > H)
        throw new h(
          "maxContentLength size of " + H + " exceeded",
          h.ERR_BAD_RESPONSE,
          u,
          C
        );
      if (Be && g !== "get" && g !== "head") {
        const w = await S(b);
        if (typeof w == "number" && isFinite(w) && (oe = w, w > Oe))
          throw tt();
      }
      const Se = Be && (a.isReadableStream(b) || a.isStream(b)), nt = (w, N, J) => bt(
        w,
        Et,
        (Z) => {
          if (Be && Z > Oe)
            throw ue = tt();
          N && N(Z);
        },
        J
      );
      if (y && g !== "get" && g !== "head" && (G || Se)) {
        if (oe = oe ?? await P(V, b), oe !== 0 || Se) {
          let w = new o(m, {
            method: "POST",
            body: b,
            duplex: "half"
          }), N;
          if (a.isFormData(b) && (N = w.headers.get("content-type")) && V.setContentType(N), w.body) {
            const [J, Z] = G && pt(
              oe,
              De(ht(G))
            ) || [];
            b = nt(w.body, J, Z);
          }
        }
      } else if (Se && !l && f && g !== "get" && g !== "head")
        b = nt(b);
      else if (Se && l && !y && g !== "get" && g !== "head")
        throw new h(
          "Stream request bodies are not supported by the current fetch implementation",
          h.ERR_NOT_SUPPORT,
          u,
          C
        );
      a.isString(Re) || (Re = Re ? "include" : "omit");
      const sn = l && "credentials" in o.prototype;
      if (a.isFormData(b)) {
        const w = V.getContentType();
        w && /^multipart\/form-data/i.test(w) && !/boundary=/i.test(w) && V.delete("content-type");
      }
      V.set("User-Agent", "axios/" + Ze, !1);
      const I = Fe == null ? Fe : Object.assign(/* @__PURE__ */ Object.create(null), Fe);
      I && (delete I.body, delete I.headers, delete I.method, delete I.signal, delete I.duplex, delete I.credentials);
      const M = Object.assign(/* @__PURE__ */ Object.create(null), I, {
        signal: W,
        method: g.toUpperCase(),
        headers: jt(V.normalize()),
        body: b,
        duplex: "half",
        credentials: sn ? Re : void 0
      });
      l && (a.forEach(is, (w, N) => {
        M[N] === void 0 && (M[N] = w);
      }), M.signal === void 0 && (M.signal = null), M.body === void 0 && (M.body = null)), nn === 0 && (M.redirect = "manual", I && (I.redirect = "manual")), C = l && new o(m, M);
      let $ = await (l ? et(C, I) : et(m, M));
      const rt = L.from($.headers);
      if (le) {
        const w = a.toFiniteNumber(rt.getContentLength());
        if (w != null && w > H)
          throw new h(
            "maxContentLength size of " + H + " exceeded",
            h.ERR_BAD_RESPONSE,
            u,
            C
          );
      }
      const je = E && (v === "stream" || v === "response");
      if (E && $.body && (q || le || je && Q)) {
        const w = {};
        ["status", "statusText", "headers"].forEach((fe) => {
          w[fe] = $[fe];
        });
        const N = a.toFiniteNumber(rt.getContentLength()), [J, Z] = q && pt(
          N,
          De(ht(q), !0)
        ) || [];
        let st = 0;
        const on = (fe) => {
          if (le && (st = fe, st > H))
            throw new h(
              "maxContentLength size of " + H + " exceeded",
              h.ERR_BAD_RESPONSE,
              u,
              C
            );
          J && J(fe);
        };
        $ = new i(
          bt($.body, Et, on, () => {
            Z && Z(), Q && Q();
          }),
          w
        );
      }
      v = v || "text";
      let z = await R[a.findKey(R, v) || "text"](
        $,
        u
      );
      if (le && !E && !je) {
        let w;
        if (z != null && (typeof z.byteLength == "number" ? w = z.byteLength : typeof z.size == "number" ? w = z.size : typeof z == "string" && (w = typeof r == "function" ? new r().encode(z).byteLength : z.length)), typeof w == "number" && w > H)
          throw new h(
            "maxContentLength size of " + H + " exceeded",
            h.ERR_BAD_RESPONSE,
            u,
            C
          );
      }
      return !je && Q && Q(), await new Promise((w, N) => {
        Jt(w, N, {
          data: z,
          headers: L.from($.headers),
          status: $.status,
          statusText: $.statusText,
          config: u,
          request: C
        });
      });
    } catch (O) {
      if (Q && Q(), W && W.aborted && W.reason instanceof h) {
        const B = W.reason;
        throw B.config = u, C && (B.request = C), O !== B && Object.defineProperty(B, "cause", {
          __proto__: null,
          value: O,
          writable: !0,
          enumerable: !1,
          configurable: !0
        }), B;
      }
      if (ue)
        throw C && !ue.request && (ue.request = C), ue;
      if (O instanceof h)
        throw C && !O.request && (O.request = C), O;
      if (O && O.name === "TypeError" && /Load failed|fetch/i.test(O.message)) {
        const B = new h(
          "Network Error",
          h.ERR_NETWORK,
          u,
          C,
          O && O.response
        );
        throw Object.defineProperty(B, "cause", {
          __proto__: null,
          value: O.cause || O,
          writable: !0,
          enumerable: !1,
          configurable: !0
        }), B;
      }
      throw h.from(O, O && O.code, u, C, O && O.response);
    }
  };
}, us = /* @__PURE__ */ new Map(), Zt = (e) => {
  let t = e && e.env || {};
  const { fetch: n, Request: r, Response: s } = t, o = [r, s, n];
  let i = o.length, c = i, l, d, f = us;
  for (; c--; )
    l = o[c], d = f.get(l), d === void 0 && f.set(l, d = c ? /* @__PURE__ */ new Map() : ls(t)), f = d;
  return d;
};
Zt();
const Ye = {
  http: br,
  xhr: Kr,
  fetch: {
    get: Zt
  }
};
a.forEach(Ye, (e, t) => {
  if (e) {
    try {
      Object.defineProperty(e, "name", { __proto__: null, value: t });
    } catch {
    }
    Object.defineProperty(e, "adapterName", { __proto__: null, value: t });
  }
});
const St = (e) => `- ${e}`, fs = (e) => a.isFunction(e) || e === null || e === !1;
function ds(e, t) {
  e = a.isArray(e) ? e : [e];
  const { length: n } = e;
  let r, s;
  const o = {};
  for (let i = 0; i < n; i++) {
    r = e[i];
    let c;
    if (s = r, !fs(r) && (s = Ye[(c = String(r)).toLowerCase()], s === void 0))
      throw new h(`Unknown adapter '${c}'`);
    if (s && (a.isFunction(s) || (s = s.get(t))))
      break;
    o[c || "#" + i] = s;
  }
  if (!s) {
    const i = Object.entries(o).map(
      ([l, d]) => `adapter ${l} ` + (d === !1 ? "is not supported by the environment" : "is not available in the build")
    );
    let c = n ? i.length > 1 ? `since :
` + i.map(St).join(`
`) : " " + St(i[0]) : "as no adapter specified";
    throw new h(
      "There is no suitable adapter to dispatch the request " + c,
      h.ERR_NOT_SUPPORT
    );
  }
  return s;
}
const Yt = {
  /**
   * Resolve an adapter from a list of adapter names or functions.
   * @type {Function}
   */
  getAdapter: ds,
  /**
   * Exposes all known adapters
   * @type {Object<string, Function|Object>}
   */
  adapters: Ye
};
function $e(e) {
  if (e.cancelToken && e.cancelToken.throwIfRequested(), e.signal && e.signal.aborted)
    throw new Ee(null, e);
}
function ze(e) {
  const t = a.toSafeFlatObject(e);
  return $e(t), t.headers = L.from(a.getSafeProp(t, "headers")), t.data = He.call(t, t.transformRequest), ["post", "put", "patch"].indexOf(t.method) !== -1 && t.headers.setContentType("application/x-www-form-urlencoded", !1), Yt.getAdapter(t.adapter || ge.adapter, t)(t).then(
    function(s) {
      $e(t), t.response = s;
      try {
        s.data = He.call(t, t.transformResponse, s);
      } finally {
        delete t.response;
      }
      return s.headers = L.from(s.headers), s;
    },
    function(s) {
      if (!Wt(s) && ($e(t), s && s.response)) {
        t.response = s.response;
        try {
          s.response.data = He.call(
            t,
            t.transformResponse,
            s.response
          );
        } finally {
          delete t.response;
        }
        s.response.headers = L.from(s.response.headers);
      }
      return Promise.reject(s);
    }
  );
}
const Le = {};
["object", "boolean", "number", "function", "string", "symbol"].forEach((e, t) => {
  Le[e] = function(r) {
    return typeof r === e || "a" + (t < 1 ? "n " : " ") + e;
  };
});
const _t = {};
Le.transitional = function(t, n, r) {
  function s(o, i) {
    return "[Axios v" + Ze + "] Transitional option '" + o + "'" + i + (r ? ". " + r : "");
  }
  return (o, i, c) => {
    if (t === !1)
      throw new h(
        s(i, " has been removed" + (n ? " in " + n : "")),
        h.ERR_DEPRECATED
      );
    return n && !_t[i] && (_t[i] = !0, console.warn(
      s(
        i,
        " has been deprecated since v" + n + " and will be removed in the near future"
      )
    )), t ? t(o, i, c) : !0;
  };
};
Le.spelling = function(t) {
  return (n, r) => (console.warn(`${r} is likely a misspelling of ${t}`), !0);
};
function ps(e, t, n) {
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
const Te = {
  assertOptions: ps,
  validators: Le
}, U = Te.validators;
let ee = class {
  constructor(t) {
    this.defaults = t || {}, this.interceptors = {
      request: new ft(),
      response: new ft()
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
      if (r instanceof Error)
        try {
          let s = {};
          Error.captureStackTrace ? Error.captureStackTrace(s) : s = new Error();
          const o = s.stack;
          let i = "";
          if (typeof o == "string") {
            const c = o.indexOf(`
`);
            i = c === -1 ? "" : o.slice(c + 1);
          }
          if (!r.stack)
            r.stack = i;
          else if (i) {
            const c = i.indexOf(`
`), l = c === -1 ? -1 : i.indexOf(`
`, c + 1), d = l === -1 ? "" : i.slice(l + 1);
            String(r.stack).endsWith(d) || (r.stack += `
` + i);
          }
        } catch {
        }
      throw r;
    }
  }
  _request(t, n) {
    typeof t == "string" ? (n = n || {}, n.url = t) : n = t || {}, n = re(this.defaults, n);
    const { transitional: r, paramsSerializer: s, headers: o } = n;
    r !== void 0 && Te.assertOptions(
      r,
      {
        silentJSONParsing: U.transitional(U.boolean),
        forcedJSONParsing: U.transitional(U.boolean),
        clarifyTimeoutError: U.transitional(U.boolean),
        legacyInterceptorReqResOrdering: U.transitional(U.boolean),
        advertiseZstdAcceptEncoding: U.transitional(U.boolean),
        validateStatusUndefinedResolves: U.transitional(U.boolean)
      },
      !1
    ), s != null && (a.isFunction(s) ? n.paramsSerializer = {
      serialize: s
    } : Te.assertOptions(
      s,
      {
        encode: U.function,
        serialize: U.function
      },
      !0
    )), n.allowAbsoluteUrls !== void 0 || (this.defaults.allowAbsoluteUrls !== void 0 ? n.allowAbsoluteUrls = this.defaults.allowAbsoluteUrls : n.allowAbsoluteUrls = !0), Te.assertOptions(
      n,
      {
        baseUrl: U.spelling("baseURL"),
        withXsrfToken: U.spelling("withXSRFToken")
      },
      !0
    ), n.method = (a.getSafeProp(n, "method") || a.getSafeProp(this.defaults, "method") || "get").toLowerCase();
    let i = o && a.merge(o.common, o[n.method]);
    o && a.forEach(Vt.concat("common"), (R) => {
      delete o[R];
    }), n.headers = L.concat(i, o);
    const c = [];
    let l = !0;
    this.interceptors.request.forEach(function(S) {
      if (typeof S.runWhen == "function" && S.runWhen(n) === !1)
        return;
      l = l && S.synchronous;
      const P = n.transitional || Ge;
      P && P.legacyInterceptorReqResOrdering ? c.unshift(S.fulfilled, S.rejected) : c.push(S.fulfilled, S.rejected);
    });
    const d = [];
    this.interceptors.response.forEach(function(S) {
      d.push(S.fulfilled, S.rejected);
    });
    let f, p = 0, y;
    if (!l) {
      const R = [ze.bind(this), void 0];
      for (R.unshift(...c), R.push(...d), y = R.length, f = Promise.resolve(n); p < y; )
        f = f.then(R[p++], R[p++]);
      return f;
    }
    y = c.length;
    let E = n;
    for (; p < y; ) {
      const R = c[p++], S = c[p++];
      try {
        E = R ? R(E) : E;
      } catch (P) {
        if (!S) {
          f = Promise.reject(P);
          break;
        }
        try {
          const u = S.call(this, P);
          a.isThenable(u) && (f = Promise.resolve(u).then(
            () => ze.call(this, E)
          ));
        } catch (u) {
          f = Promise.reject(u);
        }
        break;
      }
    }
    if (!f)
      try {
        f = ze.call(this, E);
      } catch (R) {
        f = Promise.reject(R);
      }
    for (p = 0, y = d.length; p < y; )
      f = f.then(d[p++], d[p++]);
    return f;
  }
  getUri(t) {
    t = re(this.defaults, t);
    const n = Xt(t.baseURL, t.url, t.allowAbsoluteUrls, t);
    return Mt(n, t.params, t.paramsSerializer);
  }
};
a.forEach(["delete", "get", "head", "options"], function(t) {
  ee.prototype[t] = function(n, r) {
    return this.request(
      re(r || {}, {
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
        re(c || {}, {
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
  ee.prototype[t] = n(), t !== "query" && (ee.prototype[t + "Form"] = n(!0));
});
let hs = class en {
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
      r.reason || (r.reason = new Ee(o, i, c), n(r.reason));
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
      token: new en(function(s) {
        t = s;
      }),
      cancel: t
    };
  }
};
function ms(e) {
  return function(n) {
    return e.apply(null, n);
  };
}
function ys(e) {
  return a.isObject(e) && e.isAxiosError === !0;
}
const xe = {
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
  /**
   * @deprecated Use `ContentTooLarge` instead.
   */
  PayloadTooLarge: 413,
  ContentTooLarge: 413,
  UriTooLong: 414,
  UnsupportedMediaType: 415,
  RangeNotSatisfiable: 416,
  ExpectationFailed: 417,
  ImATeapot: 418,
  MisdirectedRequest: 421,
  /**
   * @deprecated Use `UnprocessableContent` instead.
   */
  UnprocessableEntity: 422,
  UnprocessableContent: 422,
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
Object.entries(xe).forEach(([e, t]) => {
  xe[t] === void 0 && (xe[t] = e);
});
function tn(e) {
  const t = new ee(e), n = At(ee.prototype.request, t);
  return a.extend(n, ee.prototype, t, { allOwnKeys: !0 }), a.extend(n, t, null, { allOwnKeys: !0 }), n.create = function(s) {
    return tn(re(e, s));
  }, n;
}
const A = tn(ge);
A.Axios = ee;
A.CanceledError = Ee;
A.CancelToken = hs;
A.isCancel = Wt;
A.VERSION = Ze;
A.toFormData = Ue;
A.AxiosError = h;
A.Cancel = A.CanceledError;
A.all = function(t) {
  return Promise.all(t);
};
A.spread = ms;
A.isAxiosError = ys;
A.mergeConfig = re;
A.AxiosHeaders = L;
A.formToJSON = (e) => vt(a.isHTMLForm(e) ? new FormData(e) : e);
A.getAdapter = Yt.getAdapter;
A.HttpStatusCode = xe;
A.default = A;
const {
  Axios: Rs,
  AxiosError: Os,
  CanceledError: Ss,
  isCancel: _s,
  CancelToken: As,
  VERSION: Ps,
  all: Ts,
  Cancel: xs,
  isAxiosError: Cs,
  spread: Ds,
  toFormData: Ns,
  AxiosHeaders: Us,
  HttpStatusCode: Ls,
  formToJSON: Fs,
  getAdapter: Bs,
  mergeConfig: js,
  create: ks
} = A, se = A.create({
  withCredentials: !0,
  timeout: 18e4,
  // Add a timeout of 3 minutes
  headers: {
    "Content-Type": "application/json"
  }
});
function Is() {
  const e = "csrftoken=", n = decodeURIComponent(document.cookie).split(";");
  for (let r of n)
    if (r = r.trim(), r.indexOf(e) === 0)
      return r.substring(e.length);
  return "";
}
se.interceptors.request.use(
  (e) => e,
  (e) => Promise.reject(e)
);
se.interceptors.response.use(
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
function qs(e, t = {}) {
  const n = K(e), r = j(null), s = j(null), o = j(!0), i = se.get(n, {
    headers: t
  }).then((c) => (s.value = c.data, o.value = !1, { loading: o, backendError: r, responseData: s })).catch((c) => (r.value = c, o.value = !1, { loading: o, backendError: r, responseData: s }));
  return {
    loading: o,
    backendError: r,
    responseData: s,
    then: (c, l) => i.then(c, l)
  };
}
function Hs(e, t, n = {}) {
  const r = K(e), s = j(null), o = j(null), i = j(!0), c = se.post(r, K(t), {
    headers: n
  }).then((l) => (o.value = l.data, i.value = !1, { loading: i, backendError: s, responseData: o })).catch((l) => (s.value = l, i.value = !1, { loading: i, backendError: s, responseData: o }));
  return {
    loading: i,
    backendError: s,
    responseData: o,
    then: (l, d) => c.then(l, d)
  };
}
function Ms(e, t, n = {}) {
  const r = K(e), s = j(null), o = K(t), i = j(!0), c = se.put(r, o, {
    headers: n
  }).then((l) => (console.log(l.statusText), i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, d) => c.then(l, d)
  };
}
function $s(e, t, n = {}) {
  const r = K(e), s = j(null), o = K(t), i = j(!0), c = se.patch(r, o, {
    headers: n
  }).then((l) => (i.value = !1, { loading: i, backendError: s })).catch((l) => (console.log(l), s.value = l, i.value = !1, { loading: i, backendError: s }));
  return {
    loading: i,
    backendError: s,
    then: (l, d) => c.then(l, d)
  };
}
function zs(e, t = {}) {
  const n = K(e), r = j(null), s = j(!0), o = se.delete(n, {
    headers: t
  }).then((i) => (s.value = !1, { loading: s, backendError: r })).catch((i) => (console.log(i), r.value = i, s.value = !1, { loading: s, backendError: r }));
  return {
    loading: s,
    backendError: r,
    then: (i, c) => o.then(i, c)
  };
}
export {
  Is as getCsrfToken,
  zs as useDeleteBackendData,
  qs as useGetBackendData,
  $s as usePatchBackendData,
  Hs as usePostBackendData,
  Ms as usePutBackendData
};
