// ===== Boru kesim simülasyonu – arayüz =====
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var D2R = Math.PI / 180;

  if (typeof TUBE_DATA === "undefined" || typeof TUBE_GCODE === "undefined") {
    $("nodata").style.display = "flex";
    return;
  }

  var D = TUBE_DATA;
  var prof = SIMCORE.profileOf(D);
  var lim = { x: +D.vx || 0, y: +D.vy || 0, z: +D.vz || 0, a: +D.va || 0 };
  var limKnown = lim.x > 0 && lim.a > 0;
  var parsed = SIMCORE.parseGcode(TUBE_GCODE, lim);
  var ZOFS = +D.zofs || 0, STOF = (+D.stof || 0) - ZOFS;   // Z0 boru üst yüzeyi
  var samples = SIMCORE.sampleMoves(parsed.moves, STOF);
  var per = SIMCORE.buildPerimeter(prof.a, prof.b, prof.r);
  var st = SIMCORE.stats(parsed, samples);
  var moves = parsed.moves, TOTAL = Math.max(parsed.total, 1e-6);

  // yüzey konumlarını (açınım) önceden hesapla
  var SHIFT = (+D.tip === 0) ? per.P / 2 : 0;
  function sw(s) { return (s + SHIFT) % per.P; }
  var unf = samples.cut.map(function (c) {
    var q0 = SIMCORE.sOf(per, c.p0.u, c.p0.v), q1 = SIMCORE.sOf(per, c.p1.u, c.p1.v);
    return { x0: c.p0.x, s0: sw(q0.s), x1: c.p1.x, s1: sw(q1.s), air: q0.d > 0.5 || q1.d > 0.5, t: c.t, lim: c.limited };
  });
  var cutTimes = samples.cut.map(function (c) { return c.t; });

  // ---------- Bilgi paneli ----------
  function fmtT(s) { s = Math.round(Math.max(0, s) * 10) / 10; var m = Math.floor(s / 60), r = s - m * 60; return m + ":" + (r < 10 ? "0" : "") + r.toFixed(1); }
  var isRound = +D.tip === 0;
  var holeCount = TUBE_GCODE.filter(function (l) { return /delik/i.test(l); }).length;
  var rows = [
    ["Profil", isRound ? "Yuvarlak Ø" + D.D : "Dikdörtgen " + D.A + " × " + D.B + (D.R > 0 ? "  R" + D.R : "")],
    ["Et kalınlığı", (D.t || 0) + " mm"],
    ["Kesim açısı", D.beta + "°"],
    ["X0 / L", D.x0 + " / " + D.L + " mm"],
    ["Adet", D.adet],
    ["Kesim şekli", isRound ? "—" : (+D.sekil === 1 ? "Tek seferde" : "Kenar kenar")],
    ["Giriş çentiği", +D.cent > 0 ? D.cent + " mm, " + (+D.ctaraf === 0 ? "ayna yönü" : "uç yönü") : "yok"],
    ["Uç şekli", +D.btip === 1 ? "Balık ağzı (" + ["uç yönü", "ayna yönü", "iki uç"][+D.buc || 0] + "), Ø" + D.bcap + ", " + D.bteta + "°" : "Gönye"],
    ["Delik sayısı", holeCount],
    ["Toplam kesim yolu", st.cutLen.toFixed(0) + " mm"],
    ["Delme sayısı", st.pierces],
    ["Kesim süresi", fmtT(st.cutTime)],
    ["Toplam süre (tahmini)", fmtT(st.total)],
    ["Eksen max hızı X / A", limKnown ? Math.round(lim.x) + " mm/dk / " + Math.round(lim.a) + " °/dk" : "bilinmiyor"]
  ];
  $("info").innerHTML = rows.map(function (r) { return "<dt>" + r[0] + "</dt><dd>" + r[1] + "</dd>"; }).join("");
  var warns = [];
  if (parsed.warn.rapidLaser > 0) warns.push("Lazer açıkken " + parsed.warn.rapidLaser + " adet G0 (rapid) hareketi var. Kesim satırlarında G1 eksik olabilir.");
  if (parsed.warn.noFeed > 0) warns.push(parsed.warn.noFeed + " kesim satırında besleme (F) yok.");
  if (!samples.cut.length) warns.push("Programda lazer açıkken yapılan kesim hareketi bulunamadı.");
  if (st.extra > 0.3) warns.push("Eksen hız limiti nedeniyle " + st.limN + " kesim satırı yavaşlıyor (toplam +" + st.extra.toFixed(1) +
     " s). Bu bölgelerde (mor) lazer tam güçte daha uzun kalır: yanık riski. Kesim hızını veya lazer gücünü düşürmeyi düşünün.");
  if (!limKnown) warns.push("Eksen hızları okunamadı; varsayılan değerlerle hesaplandı (X/Y/Z 3000 mm/dk, A 10000 °/dk).");
  $("warn").innerHTML = warns.map(function (w) { return "<li>" + w + "</li>"; }).join("");
  $("warnbox").style.display = warns.length ? "block" : "none";

  // ---------- 3B sahne ----------
  var view3d = $("view3d");
  var renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setClearColor(0x1e2329);
  view3d.appendChild(renderer.domElement);
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(40, 1, 1, 20000);
  scene.add(new THREE.HemisphereLight(0xdfe6ee, 0x30363d, 0.9));
  var dl = new THREE.DirectionalLight(0xffffff, 0.7); dl.position.set(-300, 500, 400); scene.add(dl);

  // kesim bölgesinin X aralığı
  var xmin = 1e9, xmax = -1e9;
  samples.cut.forEach(function (c) { xmin = Math.min(xmin, c.p0.x, c.p1.x); xmax = Math.max(xmax, c.p0.x, c.p1.x); });
  if (xmin > xmax) { xmin = 0; xmax = D.x0 || 100; }
  var size = Math.max(prof.a, prof.b);
  var tubeEnd = xmax + Math.max(+D.L || 0, 4 * size, 60);

  var HEADX = 0;                                   // lazer kafası X'te sabit
  var carriage = new THREE.Group(); scene.add(carriage);   // ayna X ekseninde boruyu sürer
  var tubeGroup = new THREE.Group(); carriage.add(tubeGroup);   // A ekseni
  var grid = new THREE.GridHelper(4000, 200, 0x3a434c, 0x2a3139); grid.position.y = -(size * 2.2 + 30); scene.add(grid);

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
  var outer = rrShape(prof.a, prof.b, prof.r);
  var tw = Math.min(prof.t, prof.a * 0.9, prof.b * 0.9);
  if (tw > 0.05) {
    var inner = rrShape(prof.a - tw, prof.b - tw, Math.max(0, prof.r - tw));
    outer.holes.push(new THREE.Path(inner.getPoints(64).reverse()));
  }
  var CHX = tubeEnd;                 // ayna borunun arka ucunda (X0 = boru ön ucu)
  var tubeLen = CHX + 40;
  var tubeGeo = new THREE.ExtrudeGeometry(outer, { depth: tubeLen, bevelEnabled: false, curveSegments: 48 });
  tubeGeo.rotateY(Math.PI / 2);          // şekil (u,v) → (Z=-u, Y=v), ekstrüzyon → +X
  tubeGeo.translate(0, 0, 0);        // boru ön ucu X = 0
  var tubeMat = new THREE.MeshStandardMaterial({ color: 0xb9c0c7, metalness: 0.35, roughness: 0.55, transparent: true, opacity: 1,
                                                 polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 });
  var tube = new THREE.Mesh(tubeGeo, tubeMat); tubeGroup.add(tube);

  // ayna (tüple birlikte döner)
  var chuckR = size * 1.9 + 15;
  var chuck = new THREE.Mesh(new THREE.CylinderGeometry(chuckR, chuckR, 45, 48).rotateZ(Math.PI / 2).translate(CHX + 22.5, 0, 0),
                             new THREE.MeshStandardMaterial({ color: 0x5b6570, metalness: 0.6, roughness: 0.45 }));
  tubeGroup.add(chuck);
  for (var j = 0; j < 3; j++) {
    var jaw = new THREE.Mesh(new THREE.BoxGeometry(10, chuckR - size * 1.05, 14),
                             new THREE.MeshStandardMaterial({ color: 0x3f4750, metalness: 0.6, roughness: 0.4 }));
    var ang = j * 2 * Math.PI / 3, rr = (chuckR + size * 1.05) / 2;
    jaw.position.set(CHX - 4, rr * Math.cos(ang), rr * Math.sin(ang)); jaw.rotation.x = -ang;
    tubeGroup.add(jaw);
  }

  // kesim yolları (tüp koordinatında, tüple döner): tümü soluk + ilerleme parlak
  var n = samples.cut.length, pos = new Float32Array(n * 6), colDim = new Float32Array(n * 6), colOn = new Float32Array(n * 6);
  var C_DIM = new THREE.Color(0x7a3a26), C_ON = new THREE.Color(0xff5a1f), L_DIM = new THREE.Color(0x5b3d80), L_ON = new THREE.Color(0xd68cff);
  samples.cut.forEach(function (c, i) {
    pos.set([c.p0.x, c.p0.v, -c.p0.u, c.p1.x, c.p1.v, -c.p1.u], i * 6);
    var d = c.limited ? L_DIM : C_DIM, o = c.limited ? L_ON : C_ON;
    colDim.set([d.r, d.g, d.b, d.r, d.g, d.b], i * 6); colOn.set([o.r, o.g, o.b, o.r, o.g, o.b], i * 6);
  });
  var cutGeo = new THREE.BufferGeometry(); cutGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  cutGeo.setAttribute("color", new THREE.BufferAttribute(colDim, 3));
  var doneGeo = new THREE.BufferGeometry(); doneGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  doneGeo.setAttribute("color", new THREE.BufferAttribute(colOn, 3));
  var cutAll = new THREE.LineSegments(cutGeo, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.9 }));
  var cutDone = new THREE.LineSegments(doneGeo, new THREE.LineBasicMaterial({ vertexColors: true }));
  tubeGroup.add(cutAll); tubeGroup.add(cutDone);

  // delme noktaları
  var pierceMat = new THREE.MeshBasicMaterial({ color: 0xffd23f });
  parsed.pierces.forEach(function (p) {
    var q = SIMCORE.toTube(p, STOF);
    var sp = new THREE.Mesh(new THREE.SphereGeometry(Math.max(0.8, size * 0.04), 12, 8), pierceMat);
    sp.position.set(q.x, q.v, -q.u); tubeGroup.add(sp);
  });

  // boşta hareketler (dünya koordinatında, nozul yolu)
  var rp = new Float32Array(samples.rapid.length * 6);
  samples.rapid.forEach(function (r, i) { rp.set([r.p0.x, r.p0.z + ZOFS, -r.p0.y, r.p1.x, r.p1.z + ZOFS, -r.p1.y], i * 6); });
  var rGeo = new THREE.BufferGeometry(); rGeo.setAttribute("position", new THREE.BufferAttribute(rp, 3));
  var rapidLines = new THREE.LineSegments(rGeo, new THREE.LineBasicMaterial({ color: 0x8fa3b5, transparent: true, opacity: 0.35 }));
  carriage.add(rapidLines);   // nozul yolu boruya göre (dönmeyen çerçeve)

  // nozul
  var nozzle = new THREE.Group();
  var nh = Math.max(14, size * 0.6), nr = nh * 0.33;
  var cone = new THREE.Mesh(new THREE.ConeGeometry(nr, nh, 32).rotateX(Math.PI).translate(0, nh / 2, 0),
                            new THREE.MeshStandardMaterial({ color: 0xc9a227, metalness: 0.7, roughness: 0.3 }));
  var body = new THREE.Mesh(new THREE.CylinderGeometry(nr, nr, nh * 1.6, 32).translate(0, nh + nh * 0.8, 0),
                            new THREE.MeshStandardMaterial({ color: 0x4a525b, metalness: 0.5, roughness: 0.5 }));
  nozzle.add(cone); nozzle.add(body);
  var beamGeo = new THREE.CylinderGeometry(0.35, 0.35, 1, 8).translate(0, -0.5, 0);
  var beam = new THREE.Mesh(beamGeo, new THREE.MeshBasicMaterial({ color: 0xff3b1f }));
  var glow = new THREE.Mesh(new THREE.SphereGeometry(1.4, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffb347 }));
  nozzle.add(beam); nozzle.add(glow);
  scene.add(nozzle);

  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  function resetView() {
    var span = Math.max(Math.min(xmax - xmin, 400), size * 6, 120);
    controls.target.set(HEADX, 0, 0);
    camera.position.set(HEADX - span * 0.55, span * 0.6 + size * 2, span * 0.9 + size * 3);
    camera.near = 1; camera.far = span * 50; camera.updateProjectionMatrix();
    controls.update();
  }
  resetView();

  // ---------- Açınım (2B) ----------
  var cv = $("unfold"), ctx = cv.getContext("2d");
  var P = per.P;
  var faceLabels = [];
  if (isRound) {
    [0, 90, 180, 270].forEach(function (a) { faceLabels.push({ s: sw(SIMCORE.sAtA(per, a)), txt: "A " + a + "°" }); });
  } else {
    per.faces.forEach(function (f) {
      faceLabels.push({ s: (f.s0 + f.s1) / 2, txt: "Yüzey " + f.face + "  (A " + ((f.face - 1) * 90) + "°)", s0: f.s0, s1: f.s1 });
    });
  }
  var ux0 = Math.min(xmin, xmax) - 10, ux1 = xmax + 10;

  function drawUnfold(nDone, curPt) {
    var dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#1e2329"; ctx.fillRect(0, 0, W, H);
    var ml = 130, mr = 24, mt = 20, mb = 40;
    var sc = Math.min((W - ml - mr) / Math.max(ux1 - ux0, 1), (H - mt - mb) / P);
    var ox = ml + ((W - ml - mr) - (ux1 - ux0) * sc) / 2, oy = H - mb - ((H - mt - mb) - P * sc) / 2;
    function X(x) { return ox + (x - ux0) * sc; }
    function Y(s) { return oy - s * sc; }
    // yüzey bantları
    ctx.fillStyle = "#2a3139"; ctx.fillRect(X(ux0), Y(P), (ux1 - ux0) * sc, P * sc);
    if (!isRound) {
      faceLabels.forEach(function (f) {
        ctx.fillStyle = "#313943"; ctx.fillRect(X(ux0), Y(f.s1), (ux1 - ux0) * sc, (f.s1 - f.s0) * sc);
      });
    }
    // ızgara
    var step = [5, 10, 20, 50, 100, 200].find(function (v) { return v * sc > 45; }) || 500;
    ctx.strokeStyle = "rgba(255,255,255,0.06)"; ctx.lineWidth = 1; ctx.beginPath();
    for (var gx = Math.ceil(ux0 / step) * step; gx <= ux1; gx += step) { ctx.moveTo(X(gx), Y(0)); ctx.lineTo(X(gx), Y(P)); }
    ctx.stroke();
    ctx.fillStyle = "#8a96a3"; ctx.font = "11px Segoe UI, Arial, sans-serif"; ctx.textAlign = "center";
    for (gx = Math.ceil(ux0 / step) * step; gx <= ux1; gx += step) ctx.fillText(gx, X(gx), Y(0) + 16);
    ctx.fillText("X (mm)", X((ux0 + ux1) / 2), Y(0) + 32);
    ctx.textAlign = "right"; ctx.fillStyle = "#aab5c0"; ctx.font = "12px Segoe UI, Arial, sans-serif";
    faceLabels.forEach(function (f) { ctx.fillText(f.txt, ml - 12, Y(f.s) + 4); });
    // yol
    function seg(i, col, w) {
      var u = unf[i];
      if (Math.abs(u.s1 - u.s0) > P / 2) return;   // dikiş yerinden atlama
      if (u.lim) col = col === "#7a3a26" ? "#5b3d80" : "#d68cff";
      ctx.strokeStyle = u.air ? "rgba(150,160,170,0.5)" : col; ctx.lineWidth = w;
      ctx.beginPath(); ctx.moveTo(X(u.x0), Y(u.s0)); ctx.lineTo(X(u.x1), Y(u.s1)); ctx.stroke();
    }
    ctx.lineCap = "round";
    for (var i = 0; i < unf.length; i++) seg(i, "#7a3a26", 2);
    for (i = 0; i < nDone; i++) seg(i, "#ff5a1f", 2.2);
    // delme
    ctx.fillStyle = "#ffd23f";
    parsed.pierces.forEach(function (p) {
      var q = SIMCORE.toTube(p, STOF), s = sw(SIMCORE.sOf(per, q.u, q.v).s);
      ctx.beginPath(); ctx.arc(X(q.x), Y(s), 3.2, 0, 7); ctx.fill();
    });
    if (curPt) {
      var q = SIMCORE.sOf(per, curPt.u, curPt.v);
      ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(X(curPt.x), Y(sw(q.s)), 6, 0, 7); ctx.stroke();
    }
  }

  // ---------- Zaman / animasyon ----------
  var simT = 0, playing = false, speed = 1, lastTs = null;
  function findMove(t) {
    var lo = 0, hi = moves.length - 1;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (moves[mid].t0 <= t) lo = mid; else hi = mid - 1; }
    return lo;
  }
  function countDone(t) {
    var lo = 0, hi = cutTimes.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (cutTimes[mid] <= t + 1e-9) lo = mid + 1; else hi = mid; }
    return lo;
  }
  function stateAt(t) {
    if (!moves.length) return { p: { x: 0, y: 0, z: size * 2, a: 0 }, laser: false, line: 0 };
    var mv = moves[findMove(t)], k = mv.dur > 0 ? Math.min(1, Math.max(0, (t - mv.t0) / mv.dur)) : 1;
    if (t < mv.t0) k = 0;
    return { p: SIMCORE.lerp(mv.from, mv.to, k), laser: mv.laser && mv.kind !== "rapid" || (mv.kind === "dwell" && mv.laser), line: mv.line };
  }

  function update() {
    var s = stateAt(simT), p = s.p;
    tubeGroup.rotation.x = p.a * D2R;
    carriage.position.x = HEADX - p.x;
    nozzle.position.set(HEADX, p.z + ZOFS, -p.y);
    var stof = Math.max(0.2, +D.stof || 1);
    beam.scale.set(1, stof, 1); beam.visible = s.laser;
    glow.position.set(0, -stof, 0); glow.visible = s.laser;
    var nd = countDone(simT);
    cutDone.geometry.setDrawRange(0, nd * 2);
    $("time").textContent = fmtT(simT) + " / " + fmtT(TOTAL);
    $("pos").textContent = "X (parça) " + p.x.toFixed(2) + "   Y " + p.y.toFixed(2) + "   Z " + p.z.toFixed(2) + "   A " + p.a.toFixed(1) + "°";
    $("laser").className = s.laser ? "on" : "";
    $("laser").textContent = s.laser ? "Lazer açık" : "Lazer kapalı";
    $("line").textContent = "Satır " + s.line + (TUBE_GCODE[s.line - 1] ? ":  " + TUBE_GCODE[s.line - 1] : "");
    if (!dragging) $("scrub").value = Math.round(simT / TOTAL * 1000);
    var cur = s.laser ? SIMCORE.toTube(p, STOF) : null;
    if (tab === "unfold") drawUnfold(nd, cur);
  }

  function frame(ts) {
    if (lastTs != null && playing) {
      simT += (ts - lastTs) / 1000 * speed;
      if (simT >= TOTAL) { simT = TOTAL; setPlaying(false); }
    }
    lastTs = ts;
    update();
    controls.update();
    if (tab === "3d") renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }

  function setPlaying(v) {
    playing = v;
    $("play").textContent = v ? "❚❚  Duraklat" : "▶  Oynat";
  }

  // ---------- Kontroller ----------
  var tab = "3d", dragging = false;
  function setTab(t) {
    tab = t;
    $("tab3d").classList.toggle("active", t === "3d"); $("tabUnfold").classList.toggle("active", t === "unfold");
    view3d.style.display = t === "3d" ? "block" : "none"; cv.style.display = t === "unfold" ? "block" : "none";
    resize();
  }
  $("tab3d").onclick = function () { setTab("3d"); };
  $("tabUnfold").onclick = function () { setTab("unfold"); };
  $("play").onclick = function () { if (simT >= TOTAL) simT = 0; setPlaying(!playing); };
  $("rewind").onclick = function () { simT = 0; setPlaying(false); };
  $("toEnd").onclick = function () { simT = TOTAL; setPlaying(false); };
  $("speed").onchange = function () { speed = parseFloat(this.value); };
  $("scrub").oninput = function () { dragging = true; simT = this.value / 1000 * TOTAL; };
  $("scrub").onchange = function () { dragging = false; };
  $("showRapid").onchange = function () { rapidLines.visible = this.checked; };
  $("ghost").onchange = function () { tubeMat.opacity = this.checked ? 0.45 : 1; tubeMat.depthWrite = !this.checked; };
  $("resetView").onclick = resetView;
  document.addEventListener("keydown", function (e) { if (e.code === "Space") { e.preventDefault(); $("play").click(); } });

  function resize() {
    var r = $("stage").getBoundingClientRect();
    renderer.setSize(r.width, r.height);
    camera.aspect = r.width / Math.max(1, r.height); camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  speed = parseFloat($("speed").value);
  setTab("3d");
  simT = TOTAL;               // açılışta tamamlanmış yol görünsün
  update();
  requestAnimationFrame(frame);
})();
