// Tube Studio arayüz testi (jsdom, WebGL olmadan):  node tests/studio_ui.test.js
// Önce: python tools/build_all.py   (dist/Mach3/Addons/TubeStudio/tubestudio.html)
const path = require("path"), fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");
const FILE = path.join(__dirname, "..", "dist", "Mach3", "Addons", "TubeStudio", "tubestudio.html");
let html = fs.readFileSync(FILE, "utf8").replace('<script src="wizard_state.js"></script>', "");
html = html.replace("<script>\n", `<script>
HTMLCanvasElement.prototype.getContext=function(){return new Proxy({},{get:(t,k)=>k in t?t[k]:(()=>{}),set:(t,k,v)=>{t[k]=v;return true}})};
Object.defineProperty(HTMLElement.prototype,'clientWidth',{get(){return 1000}}); Object.defineProperty(HTMLElement.prototype,'clientHeight',{get(){return 500}});
HTMLElement.prototype.getBoundingClientRect=function(){return {left:0,top:0,width:1000,height:500}};
HTMLElement.prototype.setPointerCapture=function(){}; window.ResizeObserver=class{observe(){}}; HTMLElement.prototype.scrollIntoView=function(){};
</script><script>\n`);
html = html.replace("var renderer = new THREE.WebGLRenderer({ antialias: true });", 'var renderer = {domElement:document.createElement("canvas"),setPixelRatio(){},setClearColor(){},setSize(){},render(){}};');
html = html.replace('editor.setTool("select");', 'editor.setTool("select"); window.__ed=editor; window.__H=function(){return H}; window.__C=function(){return C};');
const errs = [], vc = new VirtualConsole(); vc.on("jsdomError", e => errs.push(e.message));
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc }); const w = dom.window, d = w.document;
const wait = ms => new Promise(r => setTimeout(r, ms));
function ev(type, p) { const e = new w.MouseEvent(type, { clientX: p.px, clientY: p.py, bubbles: true, button: 0 }); e.pointerId = 1; d.getElementById("drawcv").dispatchEvent(e); }
function drag(a, b) { ev("pointerdown", a); ev("pointermove", { px: (a.px + b.px) / 2, py: (a.py + b.py) / 2 }); ev("pointermove", b); ev("pointerup", b); }
function key(k, o) { d.dispatchEvent(new w.KeyboardEvent("keydown", Object.assign({ key: k, bubbles: true }, o || {}))); }
let fail = 0; const ok = (c, m) => { console.log((c ? "  ok   " : "  HATA ") + m); if (!c) fail++; };
(async () => {
  await wait(900);
  const E = w.__ed, H = () => JSON.parse(JSON.stringify(w.__H())), P = E.P(), A0 = P / 2, S = (x, t) => E.toScreen(x, t);
  ok(d.getElementById("status").textContent === "Hazır", "açılış: M800 hatasız");
  key("c"); drag(S(100, A0), S(106, A0)); await wait(250);
  ok(H().length === 1 && H()[0].tip === 1 && H()[0].x === 100 && H()[0].l === 12 && H()[0].a === 0, "yuvarlak delik çizimi (merkez 100, Ø12, A0)");
  key("v"); drag(S(100, A0), S(150, A0)); await wait(250);
  ok(H()[0].x === 150, "sürükleyerek taşıma -> X150");
  d.getElementById("d_n").value = "2"; d.getElementById("d_dx").value = "20"; d.getElementById("e_dup").click(); await wait(250);
  ok(JSON.stringify(H().map(h => h.x)) === "[150,170,190]", "çoğaltma 2 × 20");
  key("z", { ctrlKey: true }); await wait(200); ok(H().length === 1, "geri al");
  key("y", { ctrlKey: true }); await wait(200); ok(H().length === 3, "yinele");
  [...d.querySelectorAll("#form .seg button")].find(x => x.textContent === "Dikdörtgen").click(); await wait(400);
  E.refit(); const f2 = E.faceCenter(1);
  key("r"); drag(S(40, f2 - 6), S(70, f2 + 6)); await wait(300);
  const win = H().slice(-1)[0];
  ok(win.tip === 3 && win.a === 90 && win.l === 30 && win.w === 12 && win.x === 55, "pencere çizimi yüzey 2 (30 × 12, X55)");
  const L0 = w.__C()[1017], t = S(L0, P); drag({ px: t.px, py: t.py - 18 }, { px: S(260, P).px, py: t.py - 18 }); await wait(300);
  ok(w.__C()[1017] === 260, "parça boyu tutamağı -> L 260");
  ok(/Delik/.test(d.getElementById("stats").textContent), "istatistikler güncel");
  ok(errs.length === 0, "konsol hatası yok " + (errs[0] || ""));
  console.log("\nSONUÇ:", fail ? fail + " HATA" : "BAŞARILI"); process.exit(fail ? 1 : 0);
})();
