"""Mach3 Cypress VB makrosunu (kullandığımız alt küme) tarayıcıda çalışan JavaScript'e çevirir.
Çıktı: function runMacro(R) { ... }  — R: GetUserDRO/SetUserDRO/Code/Message vb. sağlayan nesne."""
import re, sys

FUNCS = {"sin": "Math.sin", "cos": "Math.cos", "tan": "Math.tan", "sqr": "R.sqr", "atn": "Math.atan",
         "int": "Math.floor", "abs": "Math.abs", "clng": "Math.round", "chr": "String.fromCharCode",
         "right": "R.right"}
API = {"getuserdro", "setuserdro", "setuserled", "setuserlabel", "getparam", "code", "message", "openteachfile",
       "closeteachfile", "loadteachfile", "savewizard", "getmainfolder", "dir", "param1", "eof", "dooembutton"}

def split_strings(line):
    out, i, buf = [], 0, ""
    while i < len(line):
        c = line[i]
        if c == '"':
            if buf: out.append((buf, False)); buf = ""
            j = line.index('"', i + 1)
            out.append((line[i:j + 1], True)); i = j + 1
        else:
            buf += c; i += 1
    if buf: out.append((buf, False))
    return out

def strip_comment(line):
    res = ""
    for part, isstr in split_strings(line):
        if not isstr and "'" in part:
            return res + part[:part.index("'")]
        res += part
    return res

class T:
    def __init__(self, src):
        self.src = src
        self.arrays = [m.group(1).lower() for m in re.finditer(r"^\s*Dim\s+(\w+)\(", src, re.M | re.I)]
        self.vars = set()
        self.loop = 0

    def expr(self, e, cond=False):
        out = []
        for part, isstr in split_strings(e):
            if isstr:
                out.append(part.replace("\\", "\\\\"))
                continue
            p = re.sub(r"<>", " != ", part)
            if cond:
                p = re.sub(r"(?<![<>!=])=(?!=)", " == ", p)
            p = p.replace("^", "**")
            def word(m):
                w = m.group(0); lw = w.lower()
                if lw == "and": return " && "
                if lw == "or": return " || "
                if lw == "not": return " !"
                if lw == "mod": return " % "
                if lw in FUNCS: return FUNCS[lw]
                if lw in API: return "R." + lw
                self.vars.add(lw)
                return "v_" + lw
            p = re.sub(r"(?<![\w.])[A-Za-z_]\w*", word, p)
            out.append(p)
        s = "".join(out)
        for a in self.arrays:
            while True:
                m = re.search(r"\bv_%s\(" % a, s)
                if not m: break
                i = m.end() - 1; depth = 0
                for j in range(i, len(s)):
                    if s[j] == "(": depth += 1
                    elif s[j] == ")":
                        depth -= 1
                        if depth == 0: break
                s = s[:i] + "[Math.round(" + s[i + 1:j] + ")]" + s[j + 1:]
        if "&" in s.replace("&&", ""):
            pieces, depth, buf, instr, k = [], 0, "", False, 0
            while k < len(s):
                ch = s[k]
                if ch == '"': instr = not instr
                if not instr and ch in "([": depth += 1
                if not instr and ch in ")]": depth -= 1
                if ch == "&" and not instr and depth == 0 and s[k:k + 2] != "&&" and s[k - 1:k + 1] != "&&":
                    pieces.append(buf); buf = ""
                else:
                    buf += ch
                k += 1
            pieces.append(buf)
            if len(pieces) > 1: s = "R.cat(" + ",".join(pieces) + ")"
        return s

    def run(self):
        js, ind = [], 1
        I = lambda: "  " * ind
        for raw in self.src.replace("\r\n", "\n").split("\n"):
            l = strip_comment(raw).strip()
            if not l: continue
            low = l.lower()
            m = re.match(r"dim\s+(\w+)\((\d+)\)", l, re.I)
            if m:
                js.append(I() + "v_%s = new Array(%d).fill(0);" % (m.group(1).lower(), int(m.group(2)) + 1)); self.vars.add(m.group(1).lower()); continue
            m = re.match(r"if\s+(.*)\s+then$", l, re.I)
            if m: js.append(I() + "if (" + self.expr(m.group(1), True) + ") {"); ind += 1; continue
            if re.match(r"if\s+.*then\s+\S", l, re.I): raise SyntaxError("tek satır If: " + l)
            if low == "else": js.append("  " * (ind - 1) + "} else {"); continue
            if low == "end if": ind -= 1; js.append(I() + "}"); continue
            m = re.match(r"for\s+(\w+)\s*=\s*(.+?)\s+to\s+(.+?)(?:\s+step\s+(.+))?$", l, re.I)
            if m:
                self.loop += 1; k = self.loop; v = "v_" + m.group(1).lower(); self.vars.add(m.group(1).lower())
                st = self.expr(m.group(4)) if m.group(4) else "1"
                js.append(I() + "for (let _e%d = (%s), _s%d = (%s), _g%d = 0, _f%d = (%s); ; ) {" % (k, self.expr(m.group(3)), k, st, k, k, self.expr(m.group(2))))
                ind += 1
                js.append(I() + "if (_g%d++ === 0) %s = _f%d; else %s += _s%d;" % (k, v, k, v, k))
                js.append(I() + "if (_s%d > 0 ? %s > _e%d + 1e-9 : %s < _e%d - 1e-9) break;" % (k, v, k, v, k))
                js.append(I() + "if (_g%d > 2000000) throw new Error('döngü sınırı');" % k)
                continue
            if low.startswith("next"): ind -= 1; js.append(I() + "}"); continue
            if low == "exit for": js.append(I() + "break;"); continue
            if re.match(r"(while|wend|do|loop|select|case|sub|function)\b", low): raise SyntaxError("desteklenmeyen: " + l)
            if re.match(r"(open|close|print\s+#|line\s+input|input\s+#)", low): js.append(I() + "/* dosya: " + l.replace("*/", "") + " */"); continue
            m = re.match(r"(code|message)\s+(?!\()(.+)", l, re.I)
            if m: js.append(I() + "R.%s(%s);" % (m.group(1).lower(), self.expr(m.group(2)))); continue
            m = re.match(r"(\w+)\s*=\s*(.+)$", l)
            if m and m.group(1).lower() not in API:
                js.append(I() + self.expr(m.group(1)) + " = " + self.expr(m.group(2)) + ";"); continue
            m = re.match(r"(\w+)\((.+?)\)\s*=\s*(.+)$", l)
            if m and m.group(1).lower() in self.arrays:
                js.append(I() + "v_%s[Math.round(%s)] = %s;" % (m.group(1).lower(), self.expr(m.group(2)), self.expr(m.group(3)))); continue
            js.append(I() + self.expr(l) + ";")
        decl = "  let " + ", ".join("v_%s = 0" % v for v in sorted(self.vars)) + ";"
        return "function runMacro(R) {\n" + decl + "\n" + "\n".join(js) + "\n}"

RUNTIME = r"""
// VB çalışma ortamı: sayı biçimi, dize işlemleri, Mach3 API saplamaları
function makeRuntime(dro, params) {
  var out = [], msgs = [], leds = {}, labels = {}, dset = {};
  function vf(x) {
    if (typeof x === "string") return x;
    if (typeof x === "boolean") return x ? "True" : "False";
    if (Number.isInteger(x)) return String(x);
    var s = x.toPrecision(15);
    if (s.indexOf("e") < 0 && s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s;
  }
  return {
    out: out, msgs: msgs, leds: leds, labels: labels, dset: dset,
    cat: function () { var s = ""; for (var i = 0; i < arguments.length; i++) s += vf(arguments[i]); return s; },
    sqr: function (x) { if (x < 0) throw new Error("Sqr negatif: " + x); return Math.sqrt(x); },
    right: function (s, n) { s = String(s); return s.substr(s.length - n); },
    getuserdro: function (n) { var v = dro[Math.round(n)]; return v === undefined ? 0 : +v; },
    setuserdro: function (n, v) { dro[Math.round(n)] = v; dset[Math.round(n)] = v; },
    setuserled: function (n, v) { leds[Math.round(n)] = v; },
    setuserlabel: function (n, s) { labels[Math.round(n)] = s; },
    getparam: function (k) { return (params || {})[k] || 0; },
    code: function (s) { out.push(String(s)); },
    message: function (s) { msgs.push(String(s)); },
    openteachfile: function () { return 1; }, closeteachfile: function () {}, loadteachfile: function () {},
    savewizard: function () {}, getmainfolder: function () { return "C:\\Mach3\\"; },
    dir: function () { return ""; }, eof: function () { return true; }, param1: function () { return 0; },
    dooembutton: function () {}
  };
}
function runM800(dro, params) {
  var d = {}; for (var k in dro) d[k] = dro[k];
  var R = makeRuntime(d, params);
  var err = null;
  try { runMacro(R); } catch (e) { err = String(e && e.message || e); }
  return { gcode: R.out, msgs: R.msgs, dro: d, set: R.dset, leds: R.leds, error: err };
}
if (typeof module !== "undefined") module.exports = { runM800: runM800 };
"""

if __name__ == "__main__":
    raw = open(sys.argv[1], "rb").read()
    src = raw.decode("utf-8") if sys.argv[1].endswith(".bas") else raw.decode("cp1252")
    js = "// M800.m1s'ten otomatik üretildi – elle düzenlemeyin\n" + T(src).run() + "\n" + RUNTIME
    open(sys.argv[2], "w", encoding="utf-8").write(js)
    print("yazıldı", sys.argv[2], len(js))
