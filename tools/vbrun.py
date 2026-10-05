"""Mach3 Cypress Enable VB makrolarının kullandığımız alt kümesini Python'da çalıştırır (test için)."""
import re, math, sys, collections

KW = {"and": " and ", "or": " or ", "not": " not ", "mod": " % "}
FUNCS = {"sin": "math.sin", "cos": "math.cos", "tan": "math.tan", "sqr": "_sqr", "atn": "math.atan",
         "int": "math.floor", "abs": "abs", "clng": "round", "chr": "_chr", "right": "_right", "val": "_val", "instr": "_instr", "left": "_left", "mid": "_mid"}

def split_strings(line):
    """(kod parçası, string mi) listesi"""
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
            res += part[:part.index("'")]
            return res
        res += part
    return res

def conv_expr(e, arrays, cond=False):
    parts = split_strings(e)
    out = []
    for part, isstr in parts:
        if isstr:
            out.append(("S", "VS(" + part.replace("\\", "\\\\") + ")"))
            continue
        p = part
        p = re.sub(r"<>", " != ", p)
        if cond:
            p = re.sub(r"(?<![<>!=])=(?!=)", "==", p)
        p = p.replace("^", "**")
        def word(m):
            w = m.group(0); lw = w.lower()
            if lw in KW: return KW[lw]
            if lw in FUNCS: return FUNCS[lw]
            return "v_" + lw
        p = re.sub(r"(?<![\w.])[A-Za-z_]\w*", word, p)
        out.append(("C", p))
    s = "".join(x[1] for x in out)
    # dizi erişimi: v_name( ... ) -> v_name[ ... ]
    for a in arrays:
        while True:
            m = re.search(r"\bv_%s\(" % a, s)
            if not m: break
            i = m.end() - 1; depth = 0
            for j in range(i, len(s)):
                if s[j] == "(": depth += 1
                elif s[j] == ")":
                    depth -= 1
                    if depth == 0: break
            s = s[:i] + "[int(" + s[i + 1:j] + ")]" + s[j + 1:]
    # & -> | : VS sınıfı | ile VB tarzı birleştirme yapar (öncelik VB ile uyumlu)
    s = re.sub(r"&(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", " | ", s)
    # Dir/EOF/GetUserDRO vb. çağrılar v_ öneki ile kalır, ortamda tanımlı
    return s

def transpile(src):
    lines = src.replace("\r\n", "\n").split("\n")
    arrays = [m.group(1).lower() for m in re.finditer(r"^\s*Dim\s+(\w+)\(", src, re.M)]
    py, ind = [], 0
    I = lambda: "    " * ind
    for raw in lines:
        l = strip_comment(raw).strip()
        if not l: continue
        low = l.lower()
        m = re.match(r"dim\s+(\w+)\((\d+)\)", l, re.I)
        if m: py.append(I() + "v_%s=[0]*%d" % (m.group(1).lower(), int(m.group(2)) + 1)); continue
        m = re.match(r"if\s+(.*)\s+then$", l, re.I)
        if m: py.append(I() + "if " + conv_expr(m.group(1), arrays, True) + ":"); ind += 1; continue
        if re.match(r"if\s+.*then\s+\S", l, re.I): raise SyntaxError("tek satır If: " + l)
        if low == "else": py.append("    " * (ind - 1) + "else:"); continue
        if low == "end if": ind -= 1; continue
        m = re.match(r"for\s+(\w+)\s*=\s*(.+?)\s+to\s+(.+?)(?:\s+step\s+(.+))?$", l, re.I)
        if m:
            st = conv_expr(m.group(4), arrays) if m.group(4) else "1"
            py.append(I() + "for v_%s in _vbrange(%s,%s,%s):" % (m.group(1).lower(), conv_expr(m.group(2), arrays), conv_expr(m.group(3), arrays), st))
            ind += 1; continue
        if low.startswith("next"): ind -= 1; continue
        if low == "exit for": py.append(I() + "break"); continue
        if re.match(r"(while|wend|do|loop|select|case|sub|function)\b", low): raise SyntaxError("desteklenmeyen: " + l)
        m = re.match(r"open\s+(.+)\s+for\s+(input|output)\s+as\s+#(\d+)", l, re.I)
        if m: py.append(I() + "_open(%s,'%s',%s)" % (conv_expr(m.group(1), arrays), m.group(2).lower(), m.group(3))); continue
        m = re.match(r"close\s+#(\d+)", l, re.I)
        if m: py.append(I() + "_close(%s)" % m.group(1)); continue
        m = re.match(r"print\s+#(\d+)\s*,\s*(.+)", l, re.I)
        if m: py.append(I() + "_printf(%s,%s)" % (m.group(1), conv_expr(m.group(2), arrays))); continue
        m = re.match(r"input\s+#(\d+)\s*,\s*(\w+)$", l, re.I)
        if m: py.append(I() + "v_%s=float(_lineinput(%s))" % (m.group(2).lower(), m.group(1))); continue
        m = re.match(r"line\s+input\s+#(\d+)\s*,\s*(\w+)", l, re.I)
        if m: py.append(I() + "v_%s=_lineinput(%s)" % (m.group(2).lower(), m.group(1))); continue
        m = re.match(r"(code|message)\s+(.+)", l, re.I)
        if m and not l.lower().startswith(("code(", "message(")):
            py.append(I() + "v_%s(%s)" % (m.group(1).lower(), conv_expr(m.group(2), arrays))); continue
        m = re.match(r"(\w+)\s*=\s*(.+)$", l)
        if m:
            py.append(I() + conv_expr(m.group(1), arrays) + " = " + conv_expr(m.group(2), arrays)); continue
        m = re.match(r"(\w+)\((.+?)\)\s*=\s*(.+)$", l)
        if m and m.group(1).lower() in arrays:
            py.append(I() + "v_%s[int(%s)] = %s" % (m.group(1).lower(), conv_expr(m.group(2), arrays), conv_expr(m.group(3), arrays))); continue
        py.append(I() + conv_expr(l, arrays))
    return "\n".join(py)

def vbfmt(v):
    if isinstance(v, str): return v
    if isinstance(v, bool): return "True" if v else "False"
    if float(v) == int(v) and abs(v) < 1e15: return str(int(v))
    return "%.15g" % v

class VS(str):
    def __or__(self, o): return VS(str(self) + vbfmt(o))
    def __ror__(self, o): return VS(vbfmt(o) + str(self))

class Env(dict):
    def __missing__(self, k):
        if k.startswith("v_"): return 0
        raise KeyError(k)

def run(src, dros, params=None, files=None, maxlines=10 ** 7, shared=False, labels=None, leds_in=None, param1=0):
    code = transpile(src)
    out, msgs, leds, dro_out = [], [], {}, {}
    fh = {}
    files = files if files is not None else {}
    def _vbrange(a, b, s=1):
        i = a
        if s > 0:
            while i <= b + 1e-9: yield i; i += s
        else:
            while i >= b - 1e-9: yield i; i += s
    env = Env()
    env.update(dict(
        math=math, _vbrange=_vbrange, VS=VS, _chr=lambda n: VS(chr(int(n))),
        _sqr=lambda x: math.sqrt(x) if x >= 0 else (_ for _ in ()).throw(ValueError("Sqr negatif: %r" % x)),
        _right=lambda s, n: VS(s[-int(n):]), _left=lambda s, n: s[:int(n)], _mid=lambda s, n: s[int(n)-1:], _instr=lambda s, t: s.find(t)+1,
        _val=lambda s: (lambda m: float(m.group(0)) if m else 0.0)(re.match(r'\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?', s)), _cat=lambda *a: "".join(vbfmt(x) for x in a),
        v_getuserdro=lambda n: dros.get(int(n), 0), v_setuserdro=(lambda n, v: (dro_out.__setitem__(int(n), v), dros.__setitem__(int(n), v)) if shared else dro_out.__setitem__(int(n), v)),
        v_setuserlabel=lambda n, s: (labels if labels is not None else {}).__setitem__(int(n), s), v_param1=lambda: param1,
        v_setuserled=lambda n, v: (leds.__setitem__(int(n), v), (leds_in if leds_in is not None else {}).__setitem__(int(n), v)), v_getparam=lambda k: (params or {}).get(k, 0),
        v_code=lambda s: out.append(s), v_message=lambda s: msgs.append(s),
        v_openteachfile=lambda f: 1, v_closeteachfile=lambda: None, v_loadteachfile=lambda: None,
        v_savewizard=lambda: None, v_getmainfolder=lambda: VS("C:\\Mach3\\"), v_dooembutton=lambda n: None, v_shell=lambda *a: 1,
        v_dir=lambda f: f if f in files or f.endswith(".tap") else "",
        _open=lambda f, mode, n: fh.__setitem__(n, {"f": f, "mode": mode, "lines": (list(files[f]) if f in files else list(out)) if mode == "input" else [], "i": 0}),
        _close=lambda n: files.__setitem__(fh[n]["f"], fh[n]["lines"]) if fh[n]["mode"] == "output" else None,
        _printf=lambda n, s: fh[n]["lines"].append(s),
        _lineinput=lambda n: VS((fh[n].__setitem__("i", fh[n]["i"] + 1), fh[n]["lines"][fh[n]["i"] - 1])[1]),
        v_eof=lambda n: fh[n]["i"] >= len(fh[n]["lines"]),
    ))
    exec(compile(code, "M800", "exec"), env, env)
    return out, msgs, leds, dro_out, files

if __name__ == "__main__":
    print(transpile(open(sys.argv[1]).read()))
