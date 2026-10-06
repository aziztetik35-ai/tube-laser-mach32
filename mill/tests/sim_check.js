// Simülasyon sayfasını (tubesim.html / tubemillsim.html) jsdom'da veriyle açar, sonucu JSON yazar.
//   node mill/tests/sim_check.js <sayfa.html> <veri.js>
// WebGL yok: renderer ve canvas taklit edilir (görüntü doğrulanmaz, yalnız mantık ve hata).
const fs = require("fs");
const { JSDOM, VirtualConsole } = require("jsdom");
const [html0, data] = [fs.readFileSync(process.argv[2], "utf8"), fs.readFileSync(process.argv[3], "utf8")];
let html = html0.replace(/<script src="tube(sim|mill)_data\.js"><\/script>/, () => "<script>\n" + data + "\n</script>");
html = html.replace("<script>\n", `<script>
HTMLCanvasElement.prototype.getContext=function(){return new Proxy({},{get:(t,k)=>k in t?t[k]:(()=>{}),set:(t,k,v)=>{t[k]=v;return true}})};
Object.defineProperty(HTMLElement.prototype,'clientWidth',{get(){return 1000}}); Object.defineProperty(HTMLElement.prototype,'clientHeight',{get(){return 500}});
HTMLElement.prototype.getBoundingClientRect=function(){return {left:0,top:0,width:1000,height:500}};
</script><script>\n`);
html = html.replace("var renderer = new THREE.WebGLRenderer({ antialias: true });", 'var renderer = {domElement:document.createElement("canvas"),setPixelRatio(){},setClearColor(){},setSize(){},render(){}};');
const errs = [], vc = new VirtualConsole(); vc.on("jsdomError", e => errs.push(e.message));
const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
const d = dom.window.document;
setTimeout(() => {
  d.getElementById("tabUnfold").click();             // açınım çizimi
  d.getElementById("play").click();
  setTimeout(() => {
    console.log(JSON.stringify({ errors: errs, title: d.title, info: d.getElementById("info").textContent,
      warn: d.getElementById("warn").textContent, legend: d.querySelector(".legend").textContent, hud: d.getElementById("laser").textContent }));
    dom.window.close();
  }, 300);
}, 300);
