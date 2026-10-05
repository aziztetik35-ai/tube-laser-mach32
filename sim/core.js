// ===== Boru kesim simülasyonu – çekirdek (G-kod → hareketler → örnekler → açınım) =====
var SIMCORE = (function () {
  var RAPID_L = 3000;   // mm/dk  (tahmini süre için)
  var RAPID_A = 10000;  // °/dk
  var D2R = Math.PI / 180;

  // lim: eksen max hızları (mm/dk, °/dk) – Mach3 Motor Tuning. Mach3 hiçbir ekseni bu hızın üstünde sürmez.
  function parseGcode(lines, lim) {
    lim = lim || {};
    var VX = lim.x > 0 ? lim.x : RAPID_L, VY = lim.y > 0 ? lim.y : RAPID_L, VZ = lim.z > 0 ? lim.z : RAPID_L, VA = lim.a > 0 ? lim.a : RAPID_A;
    var st = { x: 0, y: 0, z: 0, a: 0, mode: 0, g93: false, laser: false, f: 0, s: 0 };
    var moves = [], pierces = [], warn = { rapidLaser: 0, noFeed: 0 };
    var t = 0;
    for (var li = 0; li < lines.length; li++) {
      var l = String(lines[li] || "").replace(/\(.*?\)/g, "").replace(/;.*/, "").toUpperCase().trim();
      if (!l) continue;
      var re = /([A-Z])\s*([-+]?(?:\d+\.?\d*|\.\d+))/g, m;
      var tgt = { x: st.x, y: st.y, z: st.z, a: st.a }, hasAxis = false, dwell = false, p = 0, mc = [];
      while ((m = re.exec(l))) {
        var c = m[1], v = parseFloat(m[2]);
        if (c === "G") {
          if (v === 0 || v === 1) st.mode = v;
          else if (v === 93) st.g93 = true;
          else if (v === 94) st.g93 = false;
          else if (v === 4) dwell = true;
        } else if (c === "M") mc.push(v);
        else if (c === "X") { tgt.x = v; hasAxis = true; }
        else if (c === "Y") { tgt.y = v; hasAxis = true; }
        else if (c === "Z") { tgt.z = v; hasAxis = true; }
        else if (c === "A") { tgt.a = v; hasAxis = true; }
        else if (c === "F") st.f = v;
        else if (c === "S") st.s = v;
        else if (c === "P") p = v;
      }
      for (var k = 0; k < mc.length; k++) {
        if ((mc[k] === 3 || mc[k] === 4) && !st.laser) {
          st.laser = true;
          pierces.push({ x: st.x, y: st.y, z: st.z, a: st.a, t: t, line: li + 1 });
        }
        if (mc[k] === 5 || mc[k] === 30 || mc[k] === 2) st.laser = false;
      }
      if (dwell) {
        moves.push({ kind: "dwell", from: { x: st.x, y: st.y, z: st.z, a: st.a }, to: { x: st.x, y: st.y, z: st.z, a: st.a },
                     t0: t, dur: p, laser: st.laser, line: li + 1 });
        t += p;
      }
      if (hasAxis) {
        var dx = tgt.x - st.x, dy = tgt.y - st.y, dz = tgt.z - st.z, da = tgt.a - st.a;
        var dist = Math.sqrt(dx * dx + dy * dy + dz * dz), prog;
        var kind = st.mode === 0 ? "rapid" : (st.laser ? "cut" : "feed");
        // eksen limitine göre en kısa süre
        var tAx = Math.max(Math.abs(dx) / VX, Math.abs(dy) / VY, Math.abs(dz) / VZ, Math.abs(da) / VA) * 60;
        if (st.mode === 0) {
          if (st.laser) warn.rapidLaser++;
          prog = 0;
        } else if (st.g93) {
          if (st.f > 0) prog = 60 / st.f; else { prog = 0; warn.noFeed++; }
        } else {
          var len = dist > 1e-9 ? dist : Math.abs(da);
          if (st.f > 0) prog = len / st.f * 60; else { prog = 0; warn.noFeed++; }
        }
        var dur = Math.max(prog, tAx);
        moves.push({ kind: kind, from: { x: st.x, y: st.y, z: st.z, a: st.a }, to: tgt, t0: t, dur: dur, prog: prog,
                     limited: st.mode !== 0 && tAx > prog * 1.05 + 1e-6,
                     laser: st.laser, rapidLaser: st.mode === 0 && st.laser, line: li + 1 });
        t += dur;
        st.x = tgt.x; st.y = tgt.y; st.z = tgt.z; st.a = tgt.a;
      }
    }
    return { moves: moves, pierces: pierces, warn: warn, total: t };
  }

  function lerp(a, b, k) {
    return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, z: a.z + (b.z - a.z) * k, a: a.a + (b.a - a.a) * k };
  }

  // Makine konumu (nozul) → boru koordinatı (yüzey noktası): u yatay, v dikey (A=0'da)
  function toTube(p, stof) {
    var A = p.a * D2R, zz = p.z - stof;
    return { x: p.x, u: p.y * Math.cos(A) + zz * Math.sin(A), v: -p.y * Math.sin(A) + zz * Math.cos(A) };
  }

  // Hareketleri eşit olmayan adımlarla örnekle (A değişimi ~1°, yol ~2 mm)
  function sampleMoves(moves, stof) {
    var cut = [], rapid = [];
    for (var i = 0; i < moves.length; i++) {
      var mv = moves[i];
      if (mv.kind === "dwell") continue;
      var d = Math.hypot(mv.to.x - mv.from.x, mv.to.y - mv.from.y, mv.to.z - mv.from.z);
      var n = Math.max(1, Math.ceil(Math.abs(mv.to.a - mv.from.a) / 1), Math.ceil(d / 2));
      n = Math.min(n, 400);
      var prev = mv.from;
      for (var j = 1; j <= n; j++) {
        var k = j / n, cur = lerp(mv.from, mv.to, k), te = mv.t0 + mv.dur * k;
        if (mv.kind === "cut") {
          cut.push({ p0: toTube(prev, stof), p1: toTube(cur, stof), t: te, move: i, limited: mv.limited });
        } else {
          rapid.push({ p0: prev, p1: cur, t: te, move: i });
        }
        prev = cur;
      }
    }
    return { cut: cut, rapid: rapid };
  }

  // Profil çevresi: üst yüzün sol ucundan başlayıp +u yönünde (A artışıyla aynı sıra)
  function buildPerimeter(a, b, r, n) {
    r = Math.max(0, Math.min(r, a, b));
    var pts = [], faces = [];
    var segs = [
      { t: "L", p0: [-(a - r), b], p1: [a - r, b], face: 1 },
      { t: "C", c: [a - r, b - r], a0: 90, a1: 0 },
      { t: "L", p0: [a, b - r], p1: [a, -(b - r)], face: 2 },
      { t: "C", c: [a - r, -(b - r)], a0: 0, a1: -90 },
      { t: "L", p0: [a - r, -b], p1: [-(a - r), -b], face: 3 },
      { t: "C", c: [-(a - r), -(b - r)], a0: -90, a1: -180 },
      { t: "L", p0: [-a, -(b - r)], p1: [-a, b - r], face: 4 },
      { t: "C", c: [-(a - r), b - r], a0: 180, a1: 90 }
    ];
    var P = 4 * (a - r) + 4 * (b - r) + 2 * Math.PI * r;
    var step = P / (n || 2400), s = 0, last = null;
    for (var i = 0; i < segs.length; i++) {
      var g = segs[i], len, s0 = s;
      if (g.t === "L") len = Math.hypot(g.p1[0] - g.p0[0], g.p1[1] - g.p0[1]);
      else len = Math.abs(g.a1 - g.a0) * D2R * r;
      if (len < 1e-9) continue;
      var m = Math.max(1, Math.ceil(len / step));
      for (var j = 0; j <= m; j++) {
        if (j === 0 && last) continue;
        var k = j / m, u, v;
        if (g.t === "L") { u = g.p0[0] + (g.p1[0] - g.p0[0]) * k; v = g.p0[1] + (g.p1[1] - g.p0[1]) * k; }
        else { var an = (g.a0 + (g.a1 - g.a0) * k) * D2R; u = g.c[0] + r * Math.cos(an); v = g.c[1] + r * Math.sin(an); }
        pts.push({ u: u, v: v, s: s0 + len * k });
        last = true;
      }
      s += len;
      if (g.t === "L") faces.push({ face: g.face, s0: s0, s1: s });
    }
    return { pts: pts, P: P, faces: faces, round: (r >= a - 1e-9 && r >= b - 1e-9) };
  }

  // Yüzey noktasını çevre konumuna (s) çevir; d = yüzeye uzaklık (havada mı?)
  function sOf(per, u, v) {
    var best = 1e18, bi = 0, pts = per.pts;
    for (var i = 0; i < pts.length; i++) {
      var du = pts[i].u - u, dv = pts[i].v - v, dd = du * du + dv * dv;
      if (dd < best) { best = dd; bi = i; }
    }
    return { s: pts[bi].s, d: Math.sqrt(best) };
  }

  // A açısında nozulun altına gelen yüzey noktasının s değeri (etiketler için)
  function sAtA(per, Adeg) {
    var A = Adeg * D2R, dir = [Math.sin(A), Math.cos(A)], best = -1e18, i, p;
    for (i = 0; i < per.pts.length; i++) { p = per.pts[i]; best = Math.max(best, p.u * dir[0] + p.v * dir[1]); }
    var sum = 0, n = 0;   // eşit uzaklıktaki noktaların (düz yüzey) ortası
    for (i = 0; i < per.pts.length; i++) {
      p = per.pts[i];
      if (p.u * dir[0] + p.v * dir[1] > best - 1e-6) { sum += p.s; n++; }
    }
    return sum / n;
  }

  function profileOf(D) {
    if (+D.tip === 0) { var R = D.D / 2; return { a: R, b: R, r: R, t: +D.t || 0 }; }
    return { a: D.A / 2, b: D.B / 2, r: Math.max(0, +D.R || 0), t: +D.t || 0 };
  }

  function stats(parsed, samples) {
    var cutLen = 0, cutTime = 0, extra = 0, limN = 0;
    for (var i = 0; i < samples.cut.length; i++) {
      var c = samples.cut[i];
      cutLen += Math.hypot(c.p1.x - c.p0.x, c.p1.u - c.p0.u, c.p1.v - c.p0.v);
    }
    for (var j = 0; j < parsed.moves.length; j++) {
      var mv = parsed.moves[j];
      if (mv.kind !== "cut") continue;
      cutTime += mv.dur;
      if (mv.limited) { extra += mv.dur - mv.prog; limN++; }
    }
    return { cutLen: cutLen, cutTime: cutTime, total: parsed.total, pierces: parsed.pierces.length, extra: extra, limN: limN };
  }

  return { parseGcode: parseGcode, sampleMoves: sampleMoves, buildPerimeter: buildPerimeter, sOf: sOf,
           sAtA: sAtA, toTube: toTube, lerp: lerp, profileOf: profileOf, stats: stats };
})();
if (typeof module !== "undefined") module.exports = SIMCORE;
