//#region node_modules/.pnpm/@noble+hashes@2.4.0/node_modules/@noble/hashes/utils.js
function e(e) {
	return e instanceof Uint8Array || ArrayBuffer.isView(e) && e.constructor.name === "Uint8Array" && "BYTES_PER_ELEMENT" in e && e.BYTES_PER_ELEMENT === 1;
}
var t = (e) => e ? `"${e}" ` : "";
function n(e, n = "") {
	if (typeof e != "number") throw TypeError(t(n) + "expected number, got " + typeof e);
	if (!Number.isSafeInteger(e) || e < 0) throw RangeError(t(n) + "expected integer >= 0, got " + e);
	return e;
}
function r(r, i, a = "") {
	if (e(r) && (i === void 0 || r.length === i)) return r;
	i !== void 0 && n(i, "length");
	let o = e(r), s = i === void 0 ? "" : ` of length ${i}`, c = o ? `length=${r.length}` : `type=${typeof r}`, l = t(a) + "expected Uint8Array" + s + ", got " + c;
	throw o ? RangeError(l) : TypeError(l);
}
function i(e) {
	if (typeof e != "function" || typeof e.create != "function") throw TypeError("expected hash wrapped by utils.createHasher");
	if (n(e.outputLen), n(e.blockLen), e.outputLen < 1 || e.blockLen < 1) throw Error("hash blockLen / outputLen must be >= 1");
}
var a = (e, t) => {
	if (typeof e != "object" || !e || Array.isArray(e)) throw TypeError((t === "object" ? "" : `"${t}" `) + "expected object, got type=" + typeof e);
}, o = (e, t) => {
	a(e, t);
	let n = Object.getPrototypeOf(e);
	if (n !== Object.prototype && n !== null) throw TypeError(`"${t}" expected plain object`);
	if (Object.hasOwn(e, "__proto__")) throw TypeError(`"${t}.__proto__" is not allowed`);
};
function s(e, t = !0) {
	if (e.destroyed) throw Error("hash was destroyed");
	if (t && e.finished) throw Error("digest() was already called");
}
function c(e, t) {
	r(e, void 0, "output");
	let n = t.outputLen;
	if (!(e.length >= n)) throw RangeError("\"output\" expected length >= " + n);
}
function l(...e) {
	for (let t = 0; t < e.length; t++) e[t].fill(0);
}
function u(e) {
	return new DataView(e.buffer, e.byteOffset, e.byteLength);
}
function d(e, t) {
	return e << 32 - t | e >>> t;
}
new Uint8Array(new Uint32Array([287454020]).buffer)[0];
var f = typeof Uint8Array.from([]).toHex == "function" && typeof Uint8Array.fromHex == "function", p = /* @__PURE__ */ Array.from({ length: 256 }, (e, t) => t.toString(16).padStart(2, "0"));
function m(e) {
	if (r(e), f) return e.toHex();
	let t = "";
	for (let n = 0; n < e.length; n++) t += p[e[n]];
	return t;
}
function h(e) {
	return e >= 48 && e <= 57 ? e - 48 : e >= 65 && e <= 70 ? e - 55 : e >= 97 && e <= 102 ? e - 87 : void 0;
}
function g(e) {
	if (typeof e != "string") throw TypeError("hex string expected, got " + typeof e);
	if (f) try {
		return Uint8Array.fromHex(e);
	} catch (e) {
		throw e instanceof SyntaxError ? RangeError(e.message) : e;
	}
	let t = e.length, n = t / 2;
	if (t % 2) throw RangeError("hex string expected, got unpadded hex of length " + t);
	let r = new Uint8Array(n);
	for (let t = 0, i = 0; t < n; t++, i += 2) {
		let n = h(e.charCodeAt(i)), a = h(e.charCodeAt(i + 1));
		if (n === void 0 || a === void 0) {
			let t = e[i] + e[i + 1];
			throw RangeError("hex string expected, got non-hex character \"" + t + "\" at index " + i);
		}
		r[t] = n * 16 + a;
	}
	return r;
}
function _(e) {
	if (typeof e != "string") throw TypeError("string expected");
	let t = new TextEncoder().encode(e);
	try {
		return new Uint8Array(t);
	} finally {
		l(t);
	}
}
function v(e, t = "") {
	return typeof e == "string" ? _(e) : r(e, void 0, t);
}
function y(e, t, n = "opts") {
	return o(e, "defaults"), t !== void 0 && o(t, n), Object.assign(Object.create(null), e, t);
}
function b(e, t = {}) {
	if (typeof e != "function") throw TypeError("\"hashCons\" expected function, got type=" + typeof e);
	t = y({}, t, "info");
	let n = (t, n) => e(n).update(t).digest(), r = e(void 0);
	return n.outputLen = r.outputLen, n.blockLen = r.blockLen, n.canXOF = r.canXOF, n.create = (t) => e(t), Object.assign(n, t), Object.freeze(n);
}
var x = (e) => ({ oid: Uint8Array.from([
	6,
	9,
	96,
	134,
	72,
	1,
	101,
	3,
	4,
	2,
	e
]) });
//#endregion
//#region \0@oxc-project+runtime@0.130.0/helpers/typeof.js
function S(e) {
	"@babel/helpers - typeof";
	return S = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, S(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.130.0/helpers/toPrimitive.js
function C(e, t) {
	if (S(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (S(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.130.0/helpers/toPropertyKey.js
function w(e) {
	var t = C(e, "string");
	return S(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.130.0/helpers/defineProperty.js
function T(e, t, n) {
	return (t = w(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region node_modules/.pnpm/@noble+hashes@2.4.0/node_modules/@noble/hashes/hmac.js
var E = class {
	constructor(e, t) {
		if (T(this, "oHash", void 0), T(this, "iHash", void 0), T(this, "blockLen", void 0), T(this, "outputLen", void 0), T(this, "canXOF", !1), T(this, "finished", !1), T(this, "destroyed", !1), i(e), r(t, void 0, "key"), this.iHash = e.create(), typeof this.iHash.update != "function") throw Error("expected Hash instance");
		this.blockLen = this.iHash.blockLen, this.outputLen = this.iHash.outputLen;
		let n = this.blockLen, a = new Uint8Array(n);
		a.set(t.length > n ? e.create().update(t).digest() : t);
		for (let e = 0; e < a.length; e++) a[e] ^= 54;
		this.iHash.update(a), this.oHash = e.create();
		for (let e = 0; e < a.length; e++) a[e] ^= 106;
		this.oHash.update(a), l(a);
	}
	update(e) {
		return s(this), this.iHash.update(e), this;
	}
	digestInto(e) {
		s(this), c(e, this), this.finished = !0;
		let t = e.subarray(0, this.outputLen);
		this.iHash.digestInto(t), this.oHash.update(t), this.oHash.digestInto(t), this.destroy();
	}
	digest() {
		let e = new Uint8Array(this.oHash.outputLen);
		return this.digestInto(e), e;
	}
	_cloneInto(e) {
		e || (e = Object.create(Object.getPrototypeOf(this), {}));
		let { oHash: t, iHash: n, finished: r, destroyed: i, blockLen: a, outputLen: o, canXOF: s } = this;
		return e = e, e.finished = r, e.destroyed = i, e.blockLen = a, e.outputLen = o, e.canXOF = s, e.oHash = t._cloneInto(e.oHash), e.iHash = n._cloneInto(e.iHash), e;
	}
	clone() {
		return this._cloneInto();
	}
	destroy() {
		this.destroyed = !0, this.oHash.destroy(), this.iHash.destroy();
	}
}, D = /* @__PURE__ */ (() => {
	let e = ((e, t, n) => new E(e, t).update(n).digest());
	return e.create = (e, t) => new E(e, t), e;
})();
//#endregion
//#region node_modules/.pnpm/@noble+hashes@2.4.0/node_modules/@noble/hashes/pbkdf2.js
function O(e, t, r, a) {
	i(e);
	let { c: o, dkLen: s, asyncTick: c } = y({
		dkLen: 32,
		asyncTick: 10
	}, a);
	if (n(o, "c"), n(s, "dkLen"), n(c, "asyncTick"), o < 1) throw Error("\"c\" (iterations) must be >= 1");
	if (s < 1) throw Error("\"dkLen\" must be >= 1");
	if (s > (2 ** 32 - 1) * e.outputLen) throw Error("derived key too long");
	let u = v(t, "password");
	try {
		let t = v(r, "salt");
		try {
			let n = new Uint8Array(s), { iHash: r, oHash: i, outputLen: a } = D.create(e, u);
			return {
				c: o,
				dkLen: s,
				asyncTick: c,
				DK: n,
				outputLen: a,
				eng: k(r, i, t, new Uint8Array(a))
			};
		} finally {
			typeof r == "string" && l(t);
		}
	} finally {
		typeof t == "string" && l(u);
	}
}
function k(e, t, n, r) {
	let i = new Uint8Array(4), a = u(i), o = e._cloneInto().update(n), s = t._cloneInto(), c = e._cloneInto, d = t._cloneInto;
	return {
		u1: (e, n) => {
			a.setInt32(0, e, !1), o._cloneInto(s).update(i).digestInto(r), t._cloneInto(s).update(r).digestInto(r), n.set(r.subarray(0, n.length));
		},
		rounds: (n, i) => {
			for (let a = 1; a < n; a++) {
				c.call(e, s).update(r).digestInto(r), d.call(t, s).update(r).digestInto(r);
				for (let e = 0; e < i.length; e++) i[e] ^= r[e];
			}
		},
		output: (n) => (e.destroy(), t.destroy(), o.destroy(), s.destroy(), l(r), n)
	};
}
function A(e, t, n, r) {
	let { c: i, dkLen: a, DK: o, outputLen: s, eng: c } = O(e, t, n, r);
	for (let e = 1, t = 0; t < a; e++, t += s) {
		let n = o.subarray(t, t + s);
		c.u1(e, n), c.rounds(i, n);
	}
	return c.output(o);
}
//#endregion
//#region node_modules/.pnpm/@noble+hashes@2.4.0/node_modules/@noble/hashes/_u64.js
var j = BigInt(2 ** 32 - 1), M = /* @__PURE__ */ BigInt(32);
function N(e, t = !1) {
	return t ? {
		h: Number(e & j),
		l: Number(e >> M & j)
	} : {
		h: Number(e >> M & j) | 0,
		l: Number(e & j) | 0
	};
}
function P(e, t = !1) {
	let n = e.length, r = new Uint32Array(n), i = new Uint32Array(n);
	for (let a = 0; a < n; a++) {
		let { h: n, l: o } = N(e[a], t);
		[r[a], i[a]] = [n, o];
	}
	return [r, i];
}
var F = (e) => e / 2 ** 32 | 0, I = (e) => e >>> 0;
function L(e, t, n, r) {
	let i = F(n), a = I(n);
	e.setUint32(t, r ? a : i, r), e.setUint32(t + 4, r ? i : a, r);
}
//#endregion
//#region node_modules/.pnpm/@noble+hashes@2.4.0/node_modules/@noble/hashes/_md.js
function R(e, t, n) {
	return e & t ^ ~e & n;
}
function z(e, t, n) {
	return e & t ^ e & n ^ t & n;
}
var B = class {
	constructor(e, t, n, r) {
		T(this, "blockLen", void 0), T(this, "outputLen", void 0), T(this, "canXOF", !1), T(this, "padOffset", void 0), T(this, "isLE", void 0), T(this, "buffer", void 0), T(this, "view", void 0), T(this, "finished", !1), T(this, "length", 0), T(this, "pos", 0), T(this, "destroyed", !1), this.blockLen = e, this.outputLen = t, this.padOffset = n, this.isLE = r, this.buffer = new Uint8Array(e), this.view = u(this.buffer);
	}
	update(e) {
		s(this), r(e);
		let { view: t, buffer: n, blockLen: i } = this, a = e.length, o = !1;
		for (let r = 0; r < a;) {
			let s = Math.min(i - this.pos, a - r);
			if (s === i) {
				let t = u(e);
				for (; i <= a - r; r += i) this.process(t, r);
				o = !0;
				continue;
			}
			n.set(r === 0 && s === a ? e : e.subarray(r, r + s), this.pos), this.pos += s, r += s, this.pos === i && (this.process(t, 0), this.pos = 0, o = !0);
		}
		return this.length += e.length, o && this.roundClean(), this;
	}
	digestInto(e) {
		s(this), c(e, this), this.finished = !0;
		let { buffer: t, view: n, blockLen: r, isLE: i } = this, { pos: a } = this;
		t[a++] = 128, t.fill(0, a), this.padOffset > r - a && (this.process(n, 0), t.fill(0)), L(n, r - 8, this.length * 8, i), this.process(n, 0), this.roundClean();
		let o = e === t ? n : u(e), l = this.outputLen, d = l / 4, f = this.get();
		if (l % 4 || d > f.length) throw Error("invalid outputLen");
		for (let e = 0; e < d; e++) o.setUint32(4 * e, f[e], i);
	}
	digest() {
		let { buffer: e, outputLen: t } = this;
		this.digestInto(e);
		let n = e.slice(0, t);
		return this.destroy(), n;
	}
	_cloneIntoMeta(e) {
		let { buffer: t, length: n, finished: r, destroyed: i, pos: a } = this;
		return e.destroyed = i, e.finished = r, e.length = n, e.pos = a, a && e.buffer.set(t), e;
	}
	clone() {
		return this._cloneInto();
	}
}, V = /* @__PURE__ */ Uint32Array.from([
	1779033703,
	3144134277,
	1013904242,
	2773480762,
	1359893119,
	2600822924,
	528734635,
	1541459225
]), H = /* @__PURE__ */ Uint32Array.from([
	1116352408,
	1899447441,
	3049323471,
	3921009573,
	961987163,
	1508970993,
	2453635748,
	2870763221,
	3624381080,
	310598401,
	607225278,
	1426881987,
	1925078388,
	2162078206,
	2614888103,
	3248222580,
	3835390401,
	4022224774,
	264347078,
	604807628,
	770255983,
	1249150122,
	1555081692,
	1996064986,
	2554220882,
	2821834349,
	2952996808,
	3210313671,
	3336571891,
	3584528711,
	113926993,
	338241895,
	666307205,
	773529912,
	1294757372,
	1396182291,
	1695183700,
	1986661051,
	2177026350,
	2456956037,
	2730485921,
	2820302411,
	3259730800,
	3345764771,
	3516065817,
	3600352804,
	4094571909,
	275423344,
	430227734,
	506948616,
	659060556,
	883997877,
	958139571,
	1322822218,
	1537002063,
	1747873779,
	1955562222,
	2024104815,
	2227730452,
	2361852424,
	2428436474,
	2756734187,
	3204031479,
	3329325298
]), U = /* @__PURE__ */ new Uint32Array(64), W = class extends B {
	constructor(e, t) {
		super(64, e, 8, !1), T(this, "A", 0), T(this, "B", 0), T(this, "C", 0), T(this, "D", 0), T(this, "E", 0), T(this, "F", 0), T(this, "G", 0), T(this, "H", 0), this.A = t[0] | 0, this.B = t[1] | 0, this.C = t[2] | 0, this.D = t[3] | 0, this.E = t[4] | 0, this.F = t[5] | 0, this.G = t[6] | 0, this.H = t[7] | 0;
	}
	get() {
		let { A: e, B: t, C: n, D: r, E: i, F: a, G: o, H: s } = this;
		return [
			e,
			t,
			n,
			r,
			i,
			a,
			o,
			s
		];
	}
	set(e, t, n, r, i, a, o, s) {
		this.A = e | 0, this.B = t | 0, this.C = n | 0, this.D = r | 0, this.E = i | 0, this.F = a | 0, this.G = o | 0, this.H = s | 0;
	}
	_cloneInto(e) {
		return (e || (e = new this.constructor())).set(...this.get()), this._cloneIntoMeta(e);
	}
	process(e, t) {
		for (let n = 0; n < 16; n++, t += 4) U[n] = e.getUint32(t, !1);
		for (let e = 16; e < 64; e++) {
			let t = U[e - 15], n = U[e - 2], r = d(t, 7) ^ d(t, 18) ^ t >>> 3;
			U[e] = (d(n, 17) ^ d(n, 19) ^ n >>> 10) + U[e - 7] + r + U[e - 16] | 0;
		}
		let { A: n, B: r, C: i, D: a, E: o, F: s, G: c, H: l } = this;
		for (let e = 0; e < 64; e++) {
			let t = d(o, 6) ^ d(o, 11) ^ d(o, 25), u = l + t + R(o, s, c) + H[e] + U[e] | 0, f = (d(n, 2) ^ d(n, 13) ^ d(n, 22)) + z(n, r, i) | 0;
			l = c, c = s, s = o, o = a + u | 0, a = i, i = r, r = n, n = u + f | 0;
		}
		n = n + this.A | 0, r = r + this.B | 0, i = i + this.C | 0, a = a + this.D | 0, o = o + this.E | 0, s = s + this.F | 0, c = c + this.G | 0, l = l + this.H | 0, this.set(n, r, i, a, o, s, c, l);
	}
	roundClean() {
		l(U);
	}
	destroy() {
		this.destroyed = !0, this.set(0, 0, 0, 0, 0, 0, 0, 0), l(this.buffer);
	}
}, G = class extends W {
	constructor() {
		super(32, V);
	}
}, K = P((/* @__PURE__ */ "0x428a2f98d728ae22.0x7137449123ef65cd.0xb5c0fbcfec4d3b2f.0xe9b5dba58189dbbc.0x3956c25bf348b538.0x59f111f1b605d019.0x923f82a4af194f9b.0xab1c5ed5da6d8118.0xd807aa98a3030242.0x12835b0145706fbe.0x243185be4ee4b28c.0x550c7dc3d5ffb4e2.0x72be5d74f27b896f.0x80deb1fe3b1696b1.0x9bdc06a725c71235.0xc19bf174cf692694.0xe49b69c19ef14ad2.0xefbe4786384f25e3.0x0fc19dc68b8cd5b5.0x240ca1cc77ac9c65.0x2de92c6f592b0275.0x4a7484aa6ea6e483.0x5cb0a9dcbd41fbd4.0x76f988da831153b5.0x983e5152ee66dfab.0xa831c66d2db43210.0xb00327c898fb213f.0xbf597fc7beef0ee4.0xc6e00bf33da88fc2.0xd5a79147930aa725.0x06ca6351e003826f.0x142929670a0e6e70.0x27b70a8546d22ffc.0x2e1b21385c26c926.0x4d2c6dfc5ac42aed.0x53380d139d95b3df.0x650a73548baf63de.0x766a0abb3c77b2a8.0x81c2c92e47edaee6.0x92722c851482353b.0xa2bfe8a14cf10364.0xa81a664bbc423001.0xc24b8b70d0f89791.0xc76c51a30654be30.0xd192e819d6ef5218.0xd69906245565a910.0xf40e35855771202a.0x106aa07032bbd1b8.0x19a4c116b8d2d0c8.0x1e376c085141ab53.0x2748774cdf8eeb99.0x34b0bcb5e19b48a8.0x391c0cb3c5c95a63.0x4ed8aa4ae3418acb.0x5b9cca4f7763e373.0x682e6ff3d6b2b8a3.0x748f82ee5defb2fc.0x78a5636f43172f60.0x84c87814a1f0ab72.0x8cc702081a6439ec.0x90befffa23631e28.0xa4506cebde82bde9.0xbef9a3f7b2c67915.0xc67178f2e372532b.0xca273eceea26619c.0xd186b8c721c0c207.0xeada7dd6cde0eb1e.0xf57d4f7fee6ed178.0x06f067aa72176fba.0x0a637dc5a2c898a6.0x113f9804bef90dae.0x1b710b35131c471b.0x28db77f523047d84.0x32caab7b40c72493.0x3c9ebe0a15c9bebc.0x431d67c49c100d4c.0x4cc5d4becb3e42b6.0x597f299cfc657e2a.0x5fcb6fab3ad6faec.0x6c44198c4a475817".split(".")).map((e) => BigInt(e)));
K[0], K[1];
var q = /* @__PURE__ */ b(() => new G(), /* @__PURE__ */ x(1));
//#endregion
//#region runtime/crypto-entry.mjs
function J(e, t, n, r) {
	if (!Number.isInteger(n) || n < 1 || n > 2e6 || !Number.isInteger(r) || r < 1 || r > 64) throw Error("Unsupported PBKDF2 parameters");
	return m(A(q, g(e), g(t), {
		c: n,
		dkLen: r
	}));
}
//#endregion
export { J as pbkdf2_hex };
