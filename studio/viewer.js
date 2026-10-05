// ===== Boru kesim görüntüleyici (Tube Studio önizleme) =====
// createTubeViewer({ stage, view3d, canvas, el: {time, pos, laser, line, scrub, play} })
//   .load(D, G)  -> TUBE_DATA benzeri nesne + G-kod satırları; istatistik döndürür
function createTubeViewer(opt) {
  var D2R = Math.PI / 180;
  var el = opt.el || {};
  function setText(e, t) { if (e) e.textContent = t; }
  function fmtT(s) { s = Math.round(Math.max(0, s) * 10) / 10; var m = Math.floor(s / 60), r = s - m * 60; return m + ":" + (r < 10 ? "0" : "") + r.toFixed(1); }

  // ---------- kalıcı sahne ----------
  var renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setClearColor(0x1e2329);
  opt.view3d.appendChild(renderer.domElement);
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(40, 1, 1, 20000);
  scene.add(new THREE.HemisphereLight(0xdfe6ee, 0x30363d, 0.9));
  var dl = new THREE.DirectionalLight(0xffffff, 0.7); dl.position.set(-300, 500, 400); scene.add(dl);
  var grid = new THREE.GridHelper(4000, 200, 0x3a434c, 0x2a3139); scene.add(grid);
  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  var HEADX = 0;
  var ctx = opt.canvas.getContext("2d");

  var S = null;              // yüklü programın durumu
  var content = null, nozzle = null;
  var tab = "3d", simT = 0, playing = false, speed = 1, lastTs = null, dragging = false;
  var showRapid = true, ghost = false;

  function rrShape(a, b, r) {
    var s = new THREE.Shape();
    r = Math.max(0, Math.min(r, a, b));
    s.moveTo(-(a - r), b);
    s.lineTo(a - r, b); if (r > 0) s.absarc(a - r, b - r, r, Math.PI / 2, 0, true);
    s.lineTo(a, -(b - r)); if (r > 0) s.absarc(a - r, -(b - r), r, 0, -Math.PI / 2, true);
    s.lineTo(-(a - r), -b); if (r > 0) s.absarc(-(a - r), -(b - r), r, -Math.PI / 2, -Math.PI, true);
    s.lineTo(-a, b - r); if (r > 0) s.absarc(-(a - r), b - r, r, Math.PI, Math.PI / 2, true);
    return s;
  }
  function disposeTree(o) {
    o.traverse(function (c) {
      if (c.geometry) c.geometry.dispose();
      if (c.material) (Array.isArray(c.material) ? c.material : [c.material]).forEach(function (m) { m.dispose(); });
    });
  }

  function load(D, G) {
    if (content) { scene.remove(content); disposeTree(content); content = null; }
    if (nozzle) { scene.remove(nozzle); disposeTree(nozzle); nozzle = null; }
    var prof = SIMCORE.profileOf(D);
    var lim = { x: +D.vx || 0, y: +D.vy || 0, z: +D.vz || 0, a: +D.va || 0 };
    var parsed = SIMCORE.parseGcode(G, lim);
    var ZOFS = +D.zofs || 0, STOF = (+D.stof || 0) - ZOFS;
    var samples = SIMCORE.sampleMoves(parsed.moves, STOF);
    var per = SIMCORE.buildPerimeter(prof.a, prof.b, prof.r);
    var st = SIMCORE.stats(parsed, samples);
    var isRound = +D.tip === 0;
    var SHIFT = isRound ? per.P / 2 : 0;
    function sw(s) { return (s + SHIFT) % per.P; }
    var unf = samples.cut.map(function (c) {
      var q0 = SIMCORE.sOf(per, c.p0.u, c.p0.v), q1 = SIMCORE.sOf(per, c.p1.u, c.p1.v);
      return { x0: c.p0.x, s0: sw(q0.s), x1: c.p1.x, s1: sw(q1.s), air: q0.d > 0.5 || q1.d > 0.5, lim: c.limited };
    });
    var pierceS = parsed.pierces.map(function (p) { var q = SIMCORE.toTube(p, STOF); return { x: q.x, s: sw(SIMCORE.sOf(per, q.u, q.v).s) }; });
    var xmin = 1e9, xmax = -1e9;
    samples.cut.forEach(function (c) { xmin = Math.min(xmin, c.p0.x, c.p1.x); xmax = Math.max(xmax, c.p0.x, c.p1.x); });
    if (xmin > xmax) { xmin = 0; xmax = (+D.x0 || 0) + (+D.L || 100); }
    var size = Math.max(prof.a, prof.b, 1);
    var CHX = xmax + Math.max(+D.L || 0, 4 * size, 60);

    content = new THREE.Group(); scene.add(content);
    var carriage = new THREE.Group(); content.add(carriage);
    var tubeGroup = new THREE.Group(); carriage.add(tubeGroup);
    grid.position.y = -(size * 2.2 + 30);

    var outer = rrShape(prof.a, prof.b, prof.r);
    var tw = Math.min(prof.t, prof.a * 0.9, prof.b * 0.9);
    if (tw > 0.05) outer.holes.push(new THREE.Path(rrShape(prof.a - tw, prof.b - tw, Math.max(0, prof.r - tw)).getPoints(64).reverse()));
    var tubeGeo = new THREE.ExtrudeGeometry(outer, { depth: CHX + 40, bevelEnabled: false, curveSegments: 48 });
    tubeGeo.rotateY(Math.PI / 2);
    var tubeMat = new THREE.MeshStandardMaterial({ color: 0xb9c0c7, metalness: 0.35, roughness: 0.55, transparent: true,
      opacity: ghost ? 0.45 : 1, depthWrite: !ghost, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
    tubeGroup.add(new THREE.Mesh(tubeGeo, tubeMat));
    var chuckR = size * 1.9 + 15;
    tubeGroup.add(new THREE.Mesh(new THREE.CylinderGeometry(chuckR, chuckR, 45, 48).rotateZ(Math.PI / 2).translate(CHX + 22.5, 0, 0),
                                 new THREE.MeshStandardMaterial({ color: 0x5b6570, metalness: 0.6, roughness: 0.45 })));
    for (var j = 0; j < 3; j++) {
      var jaw = new THREE.Mesh(new THREE.BoxGeometry(10, chuckR - size * 1.05, 14), new THREE.MeshStandardMaterial({ color: 0x3f4750, metalness: 0.6, roughness: 0.4 }));
      var ang = j * 2 * Math.PI / 3, rr = (chuckR + size * 1.05) / 2;
      jaw.position.set(CHX - 4, rr * Math.cos(ang), rr * Math.sin(ang)); jaw.rotation.x = -ang;
      tubeGroup.add(jaw);
    }
    var n = samples.cut.length, pos = new Float32Array(n * 6), colDim = new Float32Array(n * 6), colOn = new Float32Array(n * 6);
    var C_DIM = new THREE.Color(0x7a3a26), C_ON = new THREE.Color(0xff5a1f), L_DIM = new THREE.Color(0x5b3d80), L_ON = new THREE.Color(0xd68cff);
    samples.cut.forEach(function (c, i) {
      pos.set([c.p0.x, c.p0.v, -c.p0.u, c.p1.x, c.p1.v, -c.p1.u], i * 6);
      var d = c.limited ? L_DIM : C_DIM, o = c.limited ? L_ON : C_ON;
      colDim.set([d.r, d.g, d.b, d.r, d.g, d.b], i * 6); colOn.set([o.r, o.g, o.b, o.r, o.g, o.b], i * 6);
    });
    var g1 = new THREE.BufferGeometry(); g1.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g1.setAttribute("color", new THREE.BufferAttribute(colDim, 3));
    var g2 = new THREE.BufferGeometry(); g2.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g2.setAttribute("color", new THREE.BufferAttribute(colOn, 3));
    tubeGroup.add(new THREE.LineSegments(g1, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.9 })));
    var cutDone = new THREE.LineSegments(g2, new THREE.LineBasicMaterial({ vertexColors: true })); tubeGroup.add(cutDone);
    var pm = new THREE.MeshBasicMaterial({ color: 0xffd23f });
    parsed.pierces.forEach(function (p) {
      var q = SIMCORE.toTube(p, STOF), sp = new THREE.Mesh(new THREE.SphereGeometry(Math.max(0.8, size * 0.04), 12, 8), pm);
      sp.position.set(q.x, q.v, -q.u); tubeGroup.add(sp);
    });
    var rp = new Float32Array(samples.rapid.length * 6);
    samples.rapid.forEach(function (r, i) { rp.set([r.p0.x, r.p0.z + ZOFS, -r.p0.y, r.p1.x, r.p1.z + ZOFS, -r.p1.y], i * 6); });
    var rg = new THREE.BufferGeometry(); rg.setAttribute("position", new THREE.BufferAttribute(rp, 3));
    var rapidLines = new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: 0x8fa3b5, transparent: true, opacity: 0.35 }));
    rapidLines.visible = showRapid; carriage.add(rapidLines);

    nozzle = new THREE.Group();
    var nh = Math.max(14, size * 0.6), nr = nh * 0.33;
    nozzle.add(new THREE.Mesh(new THREE.ConeGeometry(nr, nh, 32).rotateX(Math.PI).translate(0, nh / 2, 0), new THREE.MeshStandardMaterial({ color: 0xc9a227, metalness: 0.7, roughness: 0.3 })));
    nozzle.add(new THREE.Mesh(new THREE.CylinderGeometry(nr, nr, nh * 1.6, 32).translate(0, nh + nh * 0.8, 0), new THREE.MeshStandardMaterial({ color: 0x4a525b, metalness: 0.5, roughness: 0.5 })));
    var beam = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 1, 8).translate(0, -0.5, 0), new THREE.MeshBasicMaterial({ color: 0xff3b1f }));
    var glow = new THREE.Mesh(new THREE.SphereGeometry(1.4, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffb347 }));
    nozzle.add(beam); nozzle.add(glow); scene.add(nozzle);

    var faceLabels = [];
    if (isRound) [0, 90, 180, 270].forEach(function (a) { faceLabels.push({ s: sw(SIMCORE.sAtA(per, a)), txt: "A " + a + "°" }); });
    else per.faces.forEach(function (f) { faceLabels.push({ s: (f.s0 + f.s1) / 2, txt: "Yüzey " + f.face + "  (A " + ((f.face - 1) * 90) + "°)", s0: f.s0, s1: f.s1 }); });

    var firstLoad = !S;
    S = { D: D, G: G, parsed: parsed, moves: parsed.moves, TOTAL: Math.max(parsed.total, 1e-6), ZOFS: ZOFS, STOF: STOF,
          per: per, unf: unf, pierceS: pierceS, cutTimes: samples.cut.map(function (c) { return c.t; }), faceLabels: faceLabels,
          isRound: isRound, size: size, xmin: xmin, xmax: xmax, ux0: xmin - 10, ux1: xmax + 10,
          carriage: carriage, tubeGroup: tubeGroup, tubeMat: tubeMat, cutDone: cutDone, rapidLines: rapidLines, beam: beam, glow: glow };
    simT = S.TOTAL; setPlaying(false);
    if (firstLoad) resetView();
    update();
    return { stats: st, parsed: parsed, isRound: isRound };
  }

  function resetView() {
    if (!S) return;
    var span = Math.max(Math.min(S.xmax - S.xmin, 400), S.size * 6, 120);
    controls.target.set(HEADX, 0, 0);
    camera.position.set(HEADX - span * 0.55, span * 0.6 + S.size * 2, span * 0.9 + S.size * 3);
    camera.near = 1; camera.far = span * 50; camera.updateProjectionMatrix(); controls.update();
  }

  function drawUnfold(nDone, curPt) {
    var cv = opt.canvas, dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
    if (!W || !H) return;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#1e2329"; ctx.fillRect(0, 0, W, H);
    if (!S) return;
    var P = S.per.P, ux0 = S.ux0, ux1 = S.ux1, ml = 130, mr = 24, mt = 20, mb = 40;
    var sc = Math.min((W - ml - mr) / Math.max(ux1 - ux0, 1), (H - mt - mb) / P);
    var ox = ml + ((W - ml - mr) - (ux1 - ux0) * sc) / 2, oy = H - mb - ((H - mt - mb) - P * sc) / 2;
    function X(x) { return ox + (x - ux0) * sc; }
    function Y(s) { return oy - s * sc; }
    ctx.fillStyle = "#2a3139"; ctx.fillRect(X(ux0), Y(P), (ux1 - ux0) * sc, P * sc);
    if (!S.isRound) S.faceLabels.forEach(function (f) { ctx.fillStyle = "#313943"; ctx.fillRect(X(ux0), Y(f.s1), (ux1 - ux0) * sc, (f.s1 - f.s0) * sc); });
    var step = [5, 10, 20, 50, 100, 200].find(function (v) { return v * sc > 45; }) || 500;
    ctx.strokeStyle = "rgba(255,255,255,0.06)"; ctx.lineWidth = 1; ctx.beginPath();
    for (var gx = Math.ceil(ux0 / step) * step; gx <= ux1; gx += step) { ctx.moveTo(X(gx), Y(0)); ctx.lineTo(X(gx), Y(P)); }
    ctx.stroke();
    ctx.fillStyle = "#8a96a3"; ctx.font = "11px Segoe UI, Arial, sans-serif"; ctx.textAlign = "center";
    for (gx = Math.ceil(ux0 / step) * step; gx <= ux1; gx += step) ctx.fillText(gx, X(gx), Y(0) + 16);
    ctx.fillText("X (mm, boru ucundan)", X((ux0 + ux1) / 2), Y(0) + 32);
    ctx.textAlign = "right"; ctx.fillStyle = "#aab5c0"; ctx.font = "12px Segoe UI, Arial, sans-serif";
    S.faceLabels.forEach(function (f) { ctx.fillText(f.txt, ml - 12, Y(f.s) + 4); });
    ctx.lineCap = "round";
    function seg(i, col, w) {
      var u = S.unf[i];
      if (Math.abs(u.s1 - u.s0) > P / 2) return;
      if (u.lim) col = col === "#7a3a26" ? "#5b3d80" : "#d68cff";
      ctx.strokeStyle = u.air ? "rgba(150,160,170,0.5)" : col; ctx.lineWidth = w;
      ctx.beginPath(); ctx.moveTo(X(u.x0), Y(u.s0)); ctx.lineTo(X(u.x1), Y(u.s1)); ctx.stroke();
    }
    for (var i = 0; i < S.unf.length; i++) seg(i, "#7a3a26", 2);
    for (i = 0; i < nDone; i++) seg(i, "#ff5a1f", 2.2);
    ctx.fillStyle = "#ffd23f";
    S.pierceS.forEach(function (p) { ctx.beginPath(); ctx.arc(X(p.x), Y(p.s), 3.2, 0, 7); ctx.fill(); });
    if (curPt) {
      var q = SIMCORE.sOf(S.per, curPt.u, curPt.v);
      ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(X(curPt.x), Y((q.s + (S.isRound ? S.per.P / 2 : 0)) % S.per.P), 6, 0, 7); ctx.stroke();
    }
  }

  function findMove(t) {
    var m = S.moves, lo = 0, hi = m.length - 1;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (m[mid].t0 <= t) lo = mid; else hi = mid - 1; }
    return lo;
  }
  function countDone(t) {
    var c = S.cutTimes, lo = 0, hi = c.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (c[mid] <= t + 1e-9) lo = mid + 1; else hi = mid; }
    return lo;
  }
  function stateAt(t) {
    if (!S.moves.length) return { p: { x: 0, y: 0, z: S.size * 2, a: 0 }, laser: false, line: 0 };
    var mv = S.moves[findMove(t)], k = mv.dur > 0 ? Math.min(1, Math.max(0, (t - mv.t0) / mv.dur)) : 1;
    if (t < mv.t0) k = 0;
    return { p: SIMCORE.lerp(mv.from, mv.to, k), laser: mv.laser && mv.kind !== "rapid" || (mv.kind === "dwell" && mv.laser), line: mv.line };
  }
  function update() {
    if (!S) return;
    var s = stateAt(simT), p = s.p;
    S.tubeGroup.rotation.x = p.a * D2R;
    S.carriage.position.x = HEADX - p.x;
    nozzle.position.set(HEADX, p.z + S.ZOFS, -p.y);
    var stof = Math.max(0.2, +S.D.stof || 1);
    S.beam.scale.set(1, stof, 1); S.beam.visible = s.laser;
    S.glow.position.set(0, -stof, 0); S.glow.visible = s.laser;
    var nd = countDone(simT);
    S.cutDone.geometry.setDrawRange(0, nd * 2);
    setText(el.time, fmtT(simT) + " / " + fmtT(S.TOTAL));
    setText(el.pos, "X (parça) " + p.x.toFixed(2) + "   Y " + p.y.toFixed(2) + "   Z " + p.z.toFixed(2) + "   A " + p.a.toFixed(1) + "°");
    if (el.laser) { el.laser.className = s.laser ? "on" : ""; el.laser.textContent = s.laser ? "Lazer açık" : "Lazer kapalı"; }
    setText(el.line, s.line ? "Satır " + s.line + ":  " + (S.G[s.line - 1] || "") : "");
    if (el.scrub && !dragging) el.scrub.value = Math.round(simT / S.TOTAL * 1000);
    if (tab === "unfold") drawUnfold(nd, s.laser ? SIMCORE.toTube(p, S.STOF) : null);
  }
  function setPlaying(v) { playing = v; if (el.play) el.play.textContent = v ? "❚❚  Duraklat" : "▶  Oynat"; }
  function frame(ts) {
    if (S && lastTs != null && playing) {
      simT += (ts - lastTs) / 1000 * speed;
      if (simT >= S.TOTAL) { simT = S.TOTAL; setPlaying(false); }
    }
    lastTs = ts;
    update(); controls.update();
    if (tab === "3d") renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  function resize() {
    var r = opt.stage.getBoundingClientRect();
    renderer.setSize(r.width, r.height);
    camera.aspect = r.width / Math.max(1, r.height); camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(frame);

  return {
    load: load, resize: resize, resetView: resetView,
    setTab: function (t) { tab = t; opt.view3d.style.display = t === "3d" ? "block" : "none"; opt.canvas.style.display = t === "unfold" ? "block" : "none"; resize(); },
    togglePlay: function () { if (!S) return; if (simT >= S.TOTAL) simT = 0; setPlaying(!playing); },
    rewind: function () { simT = 0; setPlaying(false); },
    toEnd: function () { if (S) simT = S.TOTAL; setPlaying(false); },
    setSpeed: function (v) { speed = v; },
    scrub: function (f) { dragging = true; if (S) simT = f * S.TOTAL; },
    scrubEnd: function () { dragging = false; },
    setRapid: function (v) { showRapid = v; if (S) S.rapidLines.visible = v; },
    setGhost: function (v) { ghost = v; if (S) { S.tubeMat.opacity = v ? 0.45 : 1; S.tubeMat.depthWrite = !v; } }
  };
}
