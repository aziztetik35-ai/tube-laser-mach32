// ===== Tube Studio – açınım çizim editörü =====
// Parçanın açınımı (X: parça başından, dikey: çevre boyunca) üzerinde delik çizme / taşıma / boyutlandırma.
// host: { getC(), getH(), setH(H), commit(label), getOutline(), onSelect(i), onStatus(text), maxHoles }
function createHoleEditor(canvas, host) {
  var ctx = canvas.getContext("2d");
  var view = { sc: 2, ox: 80, oy: 40 };          // ekran = ox + x*sc, oy + (P - t)*sc
  var tool = "select", sel = -1, drag = null, hover = -1, guides = [], cursor = null;
  var snap = { grid: true, step: 1, center: true, edge: true, align: true, ortho: false };
  var undo = [], redo = [];
  var dpr = window.devicePixelRatio || 1;
  var fitted = false;

  // ---------- geometri yardımcıları ----------
  function G() {
    var C = host.getC(), o = host.getOutline() || {};
    var rect = +C[1000] === 1;
    var a = rect ? C[1002] / 2 : C[1001] / 2, b = rect ? C[1003] / 2 : C[1001] / 2, r = rect ? Math.max(0, Math.min(+C[1005] || 0, a, b)) : a;
    var per = SIMCORE.buildPerimeter(a, b, r);
    var P = per.P, R = C[1001] / 2;
    var faces = rect ? per.faces.map(function (f, k) { return { k: k, s0: f.s0, s1: f.s1, c: (f.s0 + f.s1) / 2, half: (f.s1 - f.s0) / 2 }; }) : [];
    return { C: C, rect: rect, P: P, R: R, faces: faces, L: +C[1017] || 0, o: o, per: per };
  }
  // delik <-> editör koordinatı (x: parça başından, t: çevre konumu, ekranda alttan yukarı)
  function holeT(h, g) {
    if (g.rect) {
      var k = Math.round((((h.a % 360) + 360) % 360) / 90) % 4;
      return g.faces[k].c + (+h.y || 0);
    }
    var s = g.R * (h.a * Math.PI / 180) + (+h.y || 0);
    return (((s + g.P / 2) % g.P) + g.P) % g.P;           // dikiş A = 180°
  }
  function setHoleT(h, t, g) {
    if (g.rect) {
      var best = 0, bd = 1e9;
      g.faces.forEach(function (f) {
        var d = t < f.s0 ? f.s0 - t : t > f.s1 ? t - f.s1 : 0;
        if (d < bd || (d === bd && Math.abs(t - f.c) < Math.abs(t - g.faces[best].c))) { bd = d; best = f.k; }
      });
      h.a = best * 90; h.y = round2(t - g.faces[best].c);
    } else {
      var s = t - g.P / 2, a = s / g.R * 180 / Math.PI;
      a = round1(((a % 360) + 360) % 360); if (a >= 360) a -= 360;
      h.a = a; h.y = 0;
    }
  }
  function dims(h) {                               // (boy X, en çevre, köşe r)
    if (h.tip === 1) return { L: h.l, W: h.l, r: h.l / 2 };
    if (h.tip === 2) return { L: h.l, W: h.w, r: Math.min(h.l, h.w) / 2 };
    return { L: h.l, W: h.w, r: Math.max(0, Math.min(h.r || 0, h.l / 2, h.w / 2)) };
  }
  function round2(v) { return Math.round(v * 100) / 100; }
  function round1(v) { return Math.round(v * 10) / 10; }
  function X(x) { return view.ox + x * view.sc; }
  function Y(t, g) { return view.oy + (g.P - t) * view.sc; }
  function wx(px) { return (px - view.ox) / view.sc; }
  function wt(py, g) { return g.P - (py - view.oy) / view.sc; }

  function fit() {
    var g = G(), W = canvas.clientWidth, Hh = canvas.clientHeight;
    if (!W || !Hh) return;
    var ml = 120, mr = 30, mt = 30, mb = 46;
    var x0 = -Math.max(15, g.L * 0.06), x1 = g.L + Math.max(15, g.L * 0.06);
    view.sc = Math.min((W - ml - mr) / (x1 - x0), (Hh - mt - mb) / g.P);
    view.ox = ml + ((W - ml - mr) - (x1 - x0) * view.sc) / 2 - x0 * view.sc;
    view.oy = mt + ((Hh - mt - mb) - g.P * view.sc) / 2;
    fitted = true; draw();
  }

  // ---------- çizim ----------
  function rrPath(cx, cy, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    var x = cx - w / 2, y = cy - h / 2;
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.arcTo(x + w, y, x + w, y + r, r);
    ctx.lineTo(x + w, y + h - r); ctx.arcTo(x + w, y + h, x + w - r, y + h, r); ctx.lineTo(x + r, y + h);
    ctx.arcTo(x, y + h, x, y + h - r, r); ctx.lineTo(x, y + r); ctx.arcTo(x, y, x + r, y, r); ctx.closePath();
  }
  function draw() {
    var W = canvas.clientWidth, Hh = canvas.clientHeight;
    if (!W || !Hh) return;
    if (canvas.width !== Math.round(W * dpr) || canvas.height !== Math.round(Hh * dpr)) { canvas.width = Math.round(W * dpr); canvas.height = Math.round(Hh * dpr); }
    if (!fitted) { fit(); return; }
    var g = G(), H = host.getH();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#1e2329"; ctx.fillRect(0, 0, W, Hh);
    var xa = wx(0), xb = wx(W);
    // bantlar
    ctx.fillStyle = "#262d35"; ctx.fillRect(0, Y(g.P, g), W, g.P * view.sc);
    if (g.rect) g.faces.forEach(function (f) { ctx.fillStyle = "#2f3741"; ctx.fillRect(0, Y(f.s1, g), W, (f.s1 - f.s0) * view.sc); });
    // ızgara
    var gs = snap.step;
    while (gs * view.sc < 8) gs *= 5;
    var major = gs * 10;
    ctx.lineWidth = 1;
    for (var gx = Math.ceil(xa / gs) * gs; gx <= xb; gx += gs) {
      ctx.strokeStyle = Math.abs(gx / major - Math.round(gx / major)) < 1e-6 ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.035)";
      ctx.beginPath(); ctx.moveTo(X(gx), Y(g.P, g)); ctx.lineTo(X(gx), Y(0, g)); ctx.stroke();
    }
    for (var gt = 0; gt <= g.P + 1e-9; gt += gs) {
      ctx.strokeStyle = "rgba(255,255,255,0.035)";
      ctx.beginPath(); ctx.moveTo(0, Y(gt, g)); ctx.lineTo(W, Y(gt, g)); ctx.stroke();
    }
    // yüzey orta çizgileri ve etiketler
    ctx.font = "12px Segoe UI, Arial, sans-serif"; ctx.textAlign = "right";
    if (g.rect) g.faces.forEach(function (f) {
      ctx.strokeStyle = "rgba(120,170,220,0.35)"; ctx.setLineDash([6, 6]);
      ctx.beginPath(); ctx.moveTo(0, Y(f.c, g)); ctx.lineTo(W, Y(f.c, g)); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "#aab5c0"; ctx.fillText("Yüzey " + (f.k + 1) + "  (A " + f.k * 90 + "°)", 110, Y(f.c, g) + 4);
    });
    else [0, 90, 180, 270].forEach(function (a) {
      var t = (((g.R * a * Math.PI / 180 + g.P / 2) % g.P) + g.P) % g.P;
      ctx.strokeStyle = "rgba(120,170,220,0.25)"; ctx.setLineDash([6, 6]);
      ctx.beginPath(); ctx.moveTo(0, Y(t, g)); ctx.lineTo(W, Y(t, g)); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "#aab5c0"; ctx.fillText("A " + a + "°", 110, Y(t, g) + 4);
    });
    // parça sınırları (uç kesimleri, M800 çıktısından)
    var o = g.o;
    ctx.fillStyle = "rgba(10,12,15,0.55)";
    if (o.front && o.front.length) shadeOutside(o.front, true, g);
    if (o.back && o.back.length) shadeOutside(o.back, false, g);
    [o.front, o.back].forEach(function (pl) {
      if (!pl || !pl.length) return;
      ctx.strokeStyle = "#ff7a3d"; ctx.lineWidth = 2; ctx.beginPath();
      for (var i = 0; i < pl.length; i++) {
        var p = pl[i], q = pl[i - 1];
        if (i === 0 || Math.abs(p[1] - q[1]) > g.P / 2) ctx.moveTo(X(p[0]), Y(p[1], g)); else ctx.lineTo(X(p[0]), Y(p[1], g));
      }
      ctx.stroke();
    });
    // parça boyu tutamağı
    ctx.strokeStyle = "rgba(255,200,120,0.6)"; ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(X(g.L), Y(g.P, g) - 14); ctx.lineTo(X(g.L), Y(0, g) + 14); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = drag && drag.kind === "len" ? "#ffd27a" : "#e0a95a";
    ctx.fillRect(X(g.L) - 7, Y(g.P, g) - 24, 14, 12);
    ctx.fillStyle = "#cfd6dd"; ctx.textAlign = "center"; ctx.font = "12px Segoe UI, Arial, sans-serif";
    ctx.fillText("L = " + round2(g.L) + " mm", X(g.L), Y(g.P, g) - 28);
    ctx.fillText("0", X(0), Y(0, g) + 16);
    // X cetveli
    var rs = [5, 10, 20, 25, 50, 100, 200].find(function (v) { return v * view.sc > 60; }) || 500;
    ctx.fillStyle = "#8a96a3"; ctx.font = "11px Segoe UI, Arial, sans-serif";
    for (var rx = Math.ceil(xa / rs) * rs; rx <= xb; rx += rs) if (Math.abs(rx) > 1e-9) ctx.fillText(rx, X(rx), Y(0, g) + 16);
    ctx.fillText("X (mm, parça başından)", X(g.L / 2), Y(0, g) + 34);
    // delikler
    H.forEach(function (h, i) {
      var d = dims(h), t = holeT(h, g), cx = X(h.x), cy = Y(t, g);
      var bad = isBad(h, g);
      rrPath(cx, cy, d.L * view.sc, d.W * view.sc, d.r * view.sc);
      ctx.fillStyle = i === sel ? "rgba(90,170,255,0.25)" : (i === hover ? "rgba(255,255,255,0.10)" : "rgba(255,90,31,0.10)");
      ctx.fill();
      ctx.lineWidth = i === sel ? 2.4 : 1.8;
      ctx.strokeStyle = bad ? "#ff4d4d" : (i === sel ? "#5aaaff" : "#ff7a3d");
      ctx.stroke();
      ctx.fillStyle = "#cfd6dd"; ctx.font = "11px Segoe UI, Arial, sans-serif"; ctx.textAlign = "center";
      ctx.fillText(String(i + 1), cx, cy - d.W * view.sc / 2 - 5);
      // merkez artı
      ctx.strokeStyle = "rgba(255,255,255,0.5)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx - 4, cy); ctx.lineTo(cx + 4, cy); ctx.moveTo(cx, cy - 4); ctx.lineTo(cx, cy + 4); ctx.stroke();
      if (i === sel) handles(h, g).forEach(function (hd) { ctx.fillStyle = "#fff"; ctx.strokeStyle = "#2f5d8a"; ctx.fillRect(hd.px - 4, hd.py - 4, 8, 8); ctx.strokeRect(hd.px - 4, hd.py - 4, 8, 8); });
    });
    // yeni çizim kutusu
    if (drag && drag.kind === "draw" && drag.box) {
      var bx = drag.box;
      rrPath(X((bx.x0 + bx.x1) / 2), Y((bx.t0 + bx.t1) / 2, g), Math.abs(bx.x1 - bx.x0) * view.sc, Math.abs(bx.t1 - bx.t0) * view.sc,
             tool === "round" ? Math.min(Math.abs(bx.x1 - bx.x0), Math.abs(bx.t1 - bx.t0)) * view.sc / 2 : tool === "oval" ? Math.min(Math.abs(bx.x1 - bx.x0), Math.abs(bx.t1 - bx.t0)) * view.sc / 2 : 0);
      ctx.strokeStyle = "#5aaaff"; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.5; ctx.stroke(); ctx.setLineDash([]);
    }
    // yakalama kılavuzları
    ctx.strokeStyle = "rgba(90,220,140,0.8)"; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
    guides.forEach(function (gd) {
      ctx.beginPath();
      if (gd.x != null) { ctx.moveTo(X(gd.x), Y(g.P, g)); ctx.lineTo(X(gd.x), Y(0, g)); }
      else { ctx.moveTo(0, Y(gd.t, g)); ctx.lineTo(W, Y(gd.t, g)); }
      ctx.stroke();
    });
    ctx.setLineDash([]);
    // imleç bilgisi
    if (cursor) {
      ctx.fillStyle = "rgba(20,24,28,0.85)"; ctx.fillRect(W - 250, Hh - 26, 246, 22);
      ctx.fillStyle = "#cfd6dd"; ctx.textAlign = "left"; ctx.font = "12px Consolas, monospace";
      ctx.fillText(cursor, W - 244, Hh - 11);
    }
  }
  function shadeOutside(pl, front, g) {
    // ön uçta eğrinin solu, arka uçta sağı karartılır
    var W = canvas.clientWidth;
    ctx.beginPath();
    var pts = pl.slice().sort(function (p, q) { return p[1] - q[1]; });
    ctx.moveTo(front ? 0 : W, Y(pts[0][1], g));
    pts.forEach(function (p) { ctx.lineTo(X(p[0]), Y(p[1], g)); });
    ctx.lineTo(front ? 0 : W, Y(pts[pts.length - 1][1], g));
    ctx.closePath(); ctx.fill();
  }
  function isBad(h, g) {
    var bad = host.badHoles && host.badHoles();
    if (bad && bad[host.getH().indexOf(h)]) return true;
    if (g.rect) {
      var d = dims(h), k = Math.round((((h.a % 360) + 360) % 360) / 90) % 4;
      if (Math.abs(h.y || 0) + d.W / 2 > g.faces[k].half + 1e-6) return true;
    }
    return false;
  }
  function handles(h, g) {
    var d = dims(h), cx = X(h.x), cy = Y(holeT(h, g), g), hw = d.L * view.sc / 2, hh = d.W * view.sc / 2;
    var list = [];
    [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (s) {
      if (h.tip === 1 && (s[0] === 0 || s[1] === 0)) return;
      list.push({ sx: s[0], sy: s[1], px: cx + s[0] * hw, py: cy + s[1] * hh });
    });
    return list;
  }

  // ---------- yakalama ----------
  function snapPoint(x, t, g, ignore, wantX, wantT) {
    guides = [];
    var tol = 7 / view.sc, H = host.getH();
    var bx = null, bt = null, dx = tol, dt = tol;
    function cx(v) { var d = Math.abs(v - x); if (wantX !== false && d < dx) { dx = d; bx = v; } }
    function ct(v) { var d = Math.abs(v - t); if (wantT !== false && d < dt) { dt = d; bt = v; } }
    if (snap.center) { cx(g.L / 2); if (g.rect) g.faces.forEach(function (f) { ct(f.c); }); else [0, 90, 180, 270].forEach(function (a) { ct((((g.R * a * Math.PI / 180 + g.P / 2) % g.P) + g.P) % g.P); }); }
    if (snap.edge) { cx(0); cx(g.L); if (g.rect) g.faces.forEach(function (f) { ct(f.s0); ct(f.s1); }); }
    if (snap.align) H.forEach(function (h, i) { if (i === ignore) return; cx(h.x); ct(holeT(h, g)); });
    var outX = bx != null ? bx : x, outT = bt != null ? bt : t;
    if (bx != null) guides.push({ x: bx });
    if (bt != null) guides.push({ t: bt });
    if (snap.grid) {
      if (bx == null) outX = Math.round(x / snap.step) * snap.step;
      if (bt == null) {
        if (g.rect) {      // ızgara yüzey merkezine göre
          var f = nearestFace(t, g); outT = f.c + Math.round((t - f.c) / snap.step) * snap.step;
        } else outT = g.P / 2 + Math.round((t - g.P / 2) / snap.step) * snap.step;   // A = 0 çizgisine hizalı
      }
    }
    return { x: round2(outX), t: outT };
  }
  function nearestFace(t, g) { var b = g.faces[0]; g.faces.forEach(function (f) { if (Math.abs(t - f.c) < Math.abs(t - b.c)) b = f; }); return b; }
  function snapLen(v) { return snap.grid ? Math.max(snap.step, Math.round(v / snap.step) * snap.step) : Math.max(0.5, round2(v)); }

  // ---------- olaylar ----------
  function pos(e) { var r = canvas.getBoundingClientRect(); return { px: e.clientX - r.left, py: e.clientY - r.top }; }
  function hitHole(px, py, g) {
    var H = host.getH();
    for (var i = H.length - 1; i >= 0; i--) {
      var h = H[i], d = dims(h), cx = X(h.x), cy = Y(holeT(h, g), g);
      if (Math.abs(px - cx) <= d.L * view.sc / 2 + 3 && Math.abs(py - cy) <= d.W * view.sc / 2 + 3) return i;
    }
    return -1;
  }
  function snapshot() { return JSON.stringify(host.getH()); }
  function pushUndo() { undo.push(snapshot()); if (undo.length > 100) undo.shift(); redo = []; }

  canvas.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  canvas.addEventListener("wheel", function (e) {
    e.preventDefault();
    var p = pos(e), f = Math.exp(-e.deltaY * 0.0015);
    var x = wx(p.px), y = (p.py - view.oy) / view.sc;
    view.sc = Math.max(0.2, Math.min(80, view.sc * f));
    view.ox = p.px - x * view.sc; view.oy = p.py - y * view.sc; draw();
  }, { passive: false });
  canvas.addEventListener("pointerdown", function (e) {
    canvas.setPointerCapture(e.pointerId);
    var p = pos(e), g = G();
    if (e.button === 1 || e.button === 2 || e.altKey) { drag = { kind: "pan", px: p.px, py: p.py, ox: view.ox, oy: view.oy }; return; }
    // parça boyu tutamağı
    if (Math.abs(p.px - X(g.L)) < 9 && p.py < Y(g.P, g) - 4 && p.py > Y(g.P, g) - 30) { drag = { kind: "len", before: +host.getC()[1017] }; return; }
    var H = host.getH();
    if (sel >= 0 && H[sel]) {
      var hs = handles(H[sel], g);
      for (var k = 0; k < hs.length; k++) if (Math.abs(p.px - hs[k].px) <= 6 && Math.abs(p.py - hs[k].py) <= 6) {
        pushUndo(); drag = { kind: "resize", i: sel, sx: hs[k].sx, sy: hs[k].sy, h0: JSON.parse(JSON.stringify(H[sel])), t0: holeT(H[sel], g) };
        return;
      }
    }
    var hit = hitHole(p.px, p.py, g);
    if (hit >= 0) {                                   // her araçta: deliğe tıklayınca seç ve taşı
      setSel(hit); pushUndo();
      drag = { kind: "move", i: hit, gx: wx(p.px) - H[hit].x, gt: wt(p.py, g) - holeT(H[hit], g), x0: H[hit].x, t0: holeT(H[hit], g) };
      draw(); return;
    }
    if (tool === "select") { setSel(-1); draw(); return; }
    if (H.length >= host.maxHoles) { host.onStatus("En fazla " + host.maxHoles + " delik."); return; }
    var s = snapPoint(wx(p.px), wt(p.py, g), g, -1);
    drag = { kind: "draw", cx: s.x, ct: s.t, box: { x0: s.x, t0: s.t, x1: s.x, t1: s.t } };
  });
  canvas.addEventListener("pointermove", function (e) {
    var p = pos(e), g = G(), H = host.getH();
    var mx = wx(p.px), mt = wt(p.py, g);
    cursor = "X " + mx.toFixed(1) + "   " + (g.rect ? (function () { var f = nearestFace(mt, g); return "Yüzey " + (f.k + 1) + "  ofset " + (mt - f.c).toFixed(1); })() :
             "A " + ((((mt - g.P / 2) / g.R * 180 / Math.PI) % 360 + 360) % 360).toFixed(1) + "°");
    if (!drag) {
      var hv = hitHole(p.px, p.py, g); if (hv !== hover) { hover = hv; }
      var onLen = Math.abs(p.px - X(g.L)) < 9 && p.py < Y(g.P, g) - 4 && p.py > Y(g.P, g) - 30;
      canvas.style.cursor = onLen ? "ew-resize" : hv >= 0 ? "move" : tool === "select" ? "default" : "crosshair";
      draw(); return;
    }
    if (drag.kind === "pan") { view.ox = drag.ox + p.px - drag.px; view.oy = drag.oy + p.py - drag.py; draw(); return; }
    if (drag.kind === "len") {
      var Lv = snapLen(mx); host.getC()[1017] = Lv; guides = []; host.onStatus("Parça boyu L = " + Lv + " mm"); host.liveUpdate(); draw(); return;
    }
    if (drag.kind === "draw") {
      var s = snapPoint(mx, mt, g, -1);
      var b = drag.box;
      if (tool === "round") {                        // merkezden yarıçap
        var rr = Math.max(Math.abs(s.x - drag.cx), Math.abs(s.t - drag.ct));
        b.x0 = drag.cx - rr; b.x1 = drag.cx + rr; b.t0 = drag.ct - rr; b.t1 = drag.ct + rr;
        guides.push({ x: drag.cx }, { t: drag.ct });
      } else { b.x1 = s.x; b.t1 = s.t; }
      host.onStatus((tool === "round" ? "Çap " : "Boy × En ") + Math.abs(b.x1 - b.x0).toFixed(1) + (tool === "round" ? "" : " × " + Math.abs(b.t1 - b.t0).toFixed(1)) + " mm");
      draw(); return;
    }
    var h = H[drag.i];
    if (drag.kind === "move") {
      var nx = mx - drag.gx, nt = mt - drag.gt;
      if (snap.ortho || e.shiftKey) { if (Math.abs(nx - drag.x0) > Math.abs(nt - drag.t0)) nt = drag.t0; else nx = drag.x0; }
      var sp = snapPoint(nx, nt, g, drag.i, !(snap.ortho || e.shiftKey) || nx !== drag.x0, !(snap.ortho || e.shiftKey) || nt !== drag.t0);
      h.x = sp.x; setHoleT(h, sp.t, g);
      host.onStatus("Delik " + (drag.i + 1) + ":  X " + h.x + (g.rect ? "  ·  Yüzey " + (Math.round(h.a / 90) % 4 + 1) + "  ofset " + h.y : "  ·  A " + h.a + "°"));
      host.liveUpdate(drag.i); draw(); return;
    }
    if (drag.kind === "resize") {
      var h0 = drag.h0, d0 = dims(h0);
      var ex = Math.abs(mx - h0.x), et = Math.abs(mt - drag.t0);
      if (h.tip === 1) { h.l = snapLen(2 * Math.max(ex, et)); }
      else {
        if (drag.sx !== 0) h.l = snapLen(2 * ex);
        if (drag.sy !== 0) h.w = snapLen(2 * et);
        if (h.tip === 3) h.r = Math.min(h.r || 0, h.l / 2, h.w / 2);
      }
      guides = [];
      host.onStatus("Delik " + (drag.i + 1) + ":  " + (h.tip === 1 ? "Ø" + h.l : h.l + " × " + h.w) + " mm");
      host.liveUpdate(drag.i); draw(); return;
    }
  });
  canvas.addEventListener("pointerup", function (e) {
    if (!drag) return;
    var g = G(), d = drag; drag = null; guides = [];
    if (d.kind === "draw") {
      var b = d.box, L = Math.abs(b.x1 - b.x0), W = Math.abs(b.t1 - b.t0);
      if (L < 0.5 && W < 0.5) {                     // tıklama: varsayılan ölçüde yerleştir
        L = tool === "round" ? 10 : tool === "oval" ? 20 : 30; W = tool === "round" ? 10 : tool === "oval" ? 8 : 15;
        b.x1 = b.x0 + L / 2; b.x0 -= L / 2; b.t1 = b.t0 + W / 2; b.t0 -= W / 2;
      }
      if (L >= 0.5 && W >= 0.5) {
        pushUndo();
        var h = { tip: tool === "round" ? 1 : tool === "oval" ? 2 : 3, x: round2((b.x0 + b.x1) / 2), a: 0, y: 0,
                  l: snapLen(tool === "round" ? Math.max(L, W) : L), w: tool === "round" ? 0 : snapLen(W), r: tool === "window" ? 2 : 0 };
        setHoleT(h, (b.t0 + b.t1) / 2, g);
        var H = host.getH(); H.push(h); setSel(H.length - 1);
        host.commit("Delik " + H.length + " eklendi");
      }
    } else if (d.kind === "move" || d.kind === "resize") {
      host.commit("Delik " + (d.i + 1) + " güncellendi");
    } else if (d.kind === "len") {
      host.commit("Parça boyu " + host.getC()[1017] + " mm");
    }
    draw();
  });
  canvas.addEventListener("pointerleave", function () { cursor = null; hover = -1; draw(); });

  function setSel(i) { sel = i; host.onSelect(i); }
  function onKey(e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return false;
    var H = host.getH(), g = G();
    var k = e.key.toLowerCase();
    if ((e.ctrlKey || e.metaKey) && k === "z") { doUndo(); return true; }
    if ((e.ctrlKey || e.metaKey) && (k === "y" || (e.shiftKey && k === "z"))) { doRedo(); return true; }
    if ((e.ctrlKey || e.metaKey) && k === "d") { duplicate(); return true; }
    if (k === "delete" || k === "backspace") { if (sel >= 0) { pushUndo(); H.splice(sel, 1); setSel(-1); host.commit("Delik silindi"); draw(); } return true; }
    if (k === "escape") { drag = null; setSel(-1); setTool("select"); draw(); return true; }
    if (k === "v") { setTool("select"); return true; }
    if (k === "c") { setTool("round"); return true; }
    if (k === "o") { setTool("oval"); return true; }
    if (k === "r") { setTool("window"); return true; }
    if (k === "f") { fit(); return true; }
    if (sel >= 0 && H[sel] && /^arrow/.test(k)) {
      var st = e.shiftKey ? 10 : snap.step, h = H[sel];
      pushUndo();
      if (k === "arrowleft") h.x = round2(h.x - st);
      if (k === "arrowright") h.x = round2(h.x + st);
      if (k === "arrowup") setHoleT(h, holeT(h, g) + st, g);
      if (k === "arrowdown") setHoleT(h, holeT(h, g) - st, g);
      host.commit("Delik " + (sel + 1) + " taşındı"); draw(); return true;
    }
    return false;
  }
  function doUndo() { if (!undo.length) return; redo.push(snapshot()); host.setH(JSON.parse(undo.pop())); sel = -1; host.onSelect(-1); host.commit("Geri alındı"); draw(); }
  function doRedo() { if (!redo.length) return; undo.push(snapshot()); host.setH(JSON.parse(redo.pop())); sel = -1; host.onSelect(-1); host.commit("Yinelendi"); draw(); }
  function duplicate(n, dx, dt) {
    var H = host.getH(), g = G();
    if (sel < 0 || !H[sel]) { host.onStatus("Önce bir delik seçin."); return; }
    n = n || 1; dx = dx != null ? dx : 20; dt = dt || 0;
    if (H.length + n > host.maxHoles) { host.onStatus("En fazla " + host.maxHoles + " delik; " + (host.maxHoles - H.length) + " kopya yapılabilir."); return; }
    pushUndo();
    var base = H[sel], t0 = holeT(base, g);
    for (var i = 1; i <= n; i++) {
      var c = JSON.parse(JSON.stringify(base)); c.x = round2(base.x + dx * i); setHoleT(c, t0 + dt * i, g); H.push(c);
    }
    setSel(H.length - 1); host.commit(n + " kopya eklendi"); draw();
  }
  function setTool(t) { tool = t; host.onTool && host.onTool(t); canvas.style.cursor = t === "select" ? "default" : "crosshair"; }

  return {
    draw: draw, fit: fit, setTool: setTool, onKey: onKey, undo: doUndo, redo: doRedo, duplicate: duplicate,
    select: function (i) { sel = i; draw(); }, getSel: function () { return sel; },
    snap: snap, refit: function () { fitted = false; draw(); },
    toScreen: function (x, t) { var g = G(); return { px: X(x), py: Y(t, g) }; }, faceCenter: function (k) { return G().faces[k].c; }, P: function () { return G().P; }
  };
}
