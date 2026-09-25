#!/usr/bin/env python3
import json, os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
try:
    import sys_reader
except ImportError:
    from src.core import sys_reader

app = FastAPI(title="OpenHMM — ThinkPad Przychodnia / Doctor")
BASE = os.path.dirname(os.path.abspath(__file__))

def load_lang(lang):
    p = os.path.join(BASE, "..", "data", f"{lang}.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

@app.get("/api/lang/{lang}")
def api_lang(lang: str):
    return JSONResponse(load_lang(lang if lang in ("pl", "en") else "pl"))

@app.get("/api/hardware")
def get_hardware_status():
    d = sys_reader.get_all()
    try:
        import distro as _distro
    except ImportError:
        from src.core import distro as _distro
    return {"machine": d["machine"], "sensors": d["sensors"], "fan": d["fan"],
            "battery": d["battery"], "cpu": d["cpu"], "memory": d["memory"],
            "distro": _distro.detect()}

@app.get("/api/fru/{model}")
def api_fru(model: str):
    p = os.path.join(BASE, "..", "data", "fru_db.json")
    try:
        with open(p, encoding="utf-8") as f:
            db = json.load(f)
        return JSONResponse(db.get(model, {"error": "model not in db", "models": list(db.keys())}))
    except Exception as e:
        return JSONResponse({"error": str(e)})

@app.get("/api/readme/{lang}")
def api_readme(lang: str):
    lang = lang if lang in ("pl", "en") else "pl"
    fname = "README.md" if lang == "pl" else "README.en.md"
    for cand in (os.path.join(BASE, "..", "..", fname), os.path.join(BASE, "..", fname)):
        if os.path.exists(cand):
            try:
                with open(cand, encoding="utf-8") as f:
                    return JSONResponse({"lang": lang, "file": fname, "content": f.read()})
            except Exception as e:
                return JSONResponse({"error": str(e)})
    return JSONResponse({"error": "README not found"})

@app.get("/api/inventory")
def api_inventory(show_serial: bool = False):
    try:
        import sys_reader as _sr
    except ImportError:
        from src.core import sys_reader as _sr
    return JSONResponse(_sr.get_inventory(redact=not show_serial))

@app.get("/api/health")
def api_health():
    try:
        import sys_reader as _sr
    except ImportError:
        from src.core import sys_reader as _sr
    return JSONResponse(_sr.assess_health(_sr.get_all()))

@app.get("/api/security")
def api_security():
    try:
        import sec_bridge
    except ImportError:
        from src.core import sec_bridge
    return JSONResponse(sec_bridge.run_all())

@app.get("/")
def get_dashboard():
    html = """<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><title>OpenHMM — ThinkPad Przychodnia</title>
<style>
:root{--bg:#000;--fg:#7dff7d;--bright:#c6ffc6;--box:#0a0f0a;--pre:#060906;--bd:#2a5a2a;--btn:#7dff7d;--btnfg:#000}
body.light{--bg:#f4f6f4;--fg:#0d3b0d;--bright:#000;--box:#fff;--pre:#eef3ee;--bd:#9dbf9d;--btn:#0d5c0d;--btnfg:#fff}
body{background:var(--bg);color:var(--fg);font-family:'Courier New',monospace;padding:20px;font-size:16px;line-height:1.65;max-width:1100px;margin:0 auto}
h1{color:var(--bright);font-size:26px;letter-spacing:1px}
h3{color:var(--bright);font-size:19px}
.box{border:1px solid var(--bd);padding:15px;margin-bottom:15px;background:var(--box);border-radius:6px}
button{background:var(--btn);color:var(--btnfg);border:0;padding:10px 18px;font-weight:bold;font-size:15px;cursor:pointer;margin:0 8px 8px 0;border-radius:4px}
#langbtn,#themebtn{background:transparent;color:var(--fg);border:1px solid var(--bd)}
pre{background:var(--pre);border:1px solid var(--bd);padding:12px;max-height:340px;overflow:auto;font-size:14px;line-height:1.7;white-space:pre-wrap;color:var(--fg)}
.tabs button{background:transparent;color:var(--fg);border:1px solid var(--bd)}
.tabs button.active{background:var(--btn);color:var(--btnfg)}
.small{font-size:13px;opacity:.85}
</style></head>
<body>
<h1 id="title">OpenHMM — ThinkPad Przychodnia</h1>
<div><span id="subtitle"></span> <button id="langbtn" onclick="toggleLang()">EN</button><button id="themebtn" onclick="toggleTheme()" title="Jasny / ciemny">☀/☾</button> <button onclick="fontSize(1)" title="Większa czcionka">A+</button><button onclick="fontSize(-1)" title="Mniejsza czcionka">A−</button></div>
<p><button id="checkbtn" onclick="updateStats()">Sprawdź mój komputer</button></p>
<div class="tabs"><button id="t1" class="active" onclick="tab('hw')">Sprzęt</button><button id="t2" onclick="tab('fru')">Naprawa (FRU/HMM)</button><button id="t3" onclick="tab('help')">Pomoc</button><button id="t4" onclick="tab('sec')">Bezpieczeństwo</button></div>
<div class="box" id="hw">
<div class="box" id="machine-info">...</div>
<div class="box"><h3 id="h-sens"></h3><pre id="sensor-info"></pre></div>
<div class="box"><h3 id="h-fan"></h3><pre id="fan-info"></pre></div>
<div class="box"><h3 id="h-bat"></h3><pre id="bat-info"></pre></div>
<div class="box"><h3 id="h-inv">Inwentaryzacja</h3><button onclick="loadInv()">Pokaż pełny sprzęt</button><pre id="inv-info" style="max-height:500px">Kliknij żeby załadować (GPU/dyski/RAM/sieć/USB/monitory).</pre></div>
</div>
<div class="box" id="fru" style="display:none"><h3>FRU / HMM</h3><pre id="fru-info"></pre></div>
<div class="box" id="help" style="display:none"><h3 id="h-help"></h3><pre id="help-info" style="max-height:500px"></pre></div>
<div class="box" id="sec" style="display:none"><h3 id="h-sec"></h3><div style="color:#888;font-size:11px" id="sec-note"></div><pre id="sec-info" style="max-height:500px"></pre></div>
<script>
let lang = localStorage.getItem('openhmm-lang') || 'pl';
let L = {};
async function loadLang(){
  let r = await fetch('/api/lang/' + lang); L = await r.json();
  document.documentElement.lang = lang;
  document.getElementById('title').textContent = L.title;
  document.getElementById('subtitle').textContent = L.subtitle;
  document.getElementById('checkbtn').textContent = L.check_pc;
  document.getElementById('t1').textContent = L.tab_hardware;
  document.getElementById('t2').textContent = L.tab_repair;
  document.getElementById('h-sens').textContent = L.sensors;
  document.getElementById('h-fan').textContent = L.fan;
  document.getElementById('h-bat').textContent = L.battery;
  document.getElementById('langbtn').textContent = L.lang_btn;
  document.getElementById('t3').textContent = L.tab_help || 'Pomoc';
  document.getElementById('h-help').textContent = L.tab_help || 'Pomoc';
  document.getElementById('t4').textContent = L.tab_security || 'Bezpieczeństwo';
  document.getElementById('h-sec').textContent = L.tab_security || 'Bezpieczeństwo';
  document.getElementById('sec-note').textContent = L.sec_note || '';
}
function toggleLang(){ lang = (lang === 'pl' ? 'en' : 'pl'); localStorage.setItem('openhmm-lang', lang); loadLang().then(updateStats); }
function toggleTheme(){ document.body.classList.toggle('light'); localStorage.setItem('openhmm-theme', document.body.classList.contains('light') ? 'light' : 'dark'); }
function fontSize(d){ const b = document.body; const cur = parseFloat(getComputedStyle(b).fontSize) || 16; b.style.fontSize = Math.min(22, Math.max(13, cur + d)) + 'px'; localStorage.setItem('openhmm-fs', b.style.fontSize); }
(function initView(){
  if (localStorage.getItem('openhmm-theme') === 'light') document.body.classList.add('light');
  const fs = localStorage.getItem('openhmm-fs'); if (fs) document.body.style.fontSize = fs;
})();
function tab(w){
  for (const id of ['hw','fru','help','sec']) document.getElementById(id).style.display = id === w ? 'block' : 'none';
  document.getElementById('t1').className = w === 'hw' ? 'active' : '';
  document.getElementById('t2').className = w === 'fru' ? 'active' : '';
  document.getElementById('t3').className = w === 'help' ? 'active' : '';
  document.getElementById('t4').className = w === 'sec' ? 'active' : '';
  if (w === 'help') loadHelp();
  if (w === 'sec') loadSec();
}
async function loadSec(){
  document.getElementById('sec-info').textContent = '...';
  try{
    let r = await fetch('/api/security'); let d = await r.json();
    let out = '';
    for (const k of Object.keys(d)) out += (d[k].ok ? '[OK] ' : '[WARN] ') + k + '\\n' + d[k].output.slice(0,4000) + '\\n\\n';
    document.getElementById('sec-info').textContent = out;
  }catch(e){ document.getElementById('sec-info').textContent = 'ERR ' + e; }
}
async function loadInv(){
  document.getElementById('inv-info').textContent = '...';
  try{
    let r = await fetch('/api/inventory'); let d = await r.json();
    document.getElementById('inv-info').textContent = JSON.stringify(d, null, 2);
  }catch(e){ document.getElementById('inv-info').textContent = 'ERR ' + e; }
}
async function loadHelp(){
  try{
    let r = await fetch('/api/readme/' + lang); let d = await r.json();
    document.getElementById('help-info').textContent = d.content || JSON.stringify(d);
  }catch(e){ document.getElementById('help-info').textContent = 'ERR ' + e; }
}
async function updateStats(){
  await loadLang();
  try{
    let r = await fetch('/api/hardware'); let d = await r.json();
    let sup = d.machine.supported ? L.supported : L.unsupported;
    document.getElementById('machine-info').innerHTML = '<b>'+L.device+':</b> '+d.machine.vendor+' - '+d.machine.model+' ['+d.machine.product_code+'] '+sup;
    document.getElementById('sensor-info').textContent = JSON.stringify(d.sensors, null, 2);
    document.getElementById('fan-info').textContent = L.level+': '+d.fan.level+' | '+L.speed+': '+d.fan.speed+' RPM';
    document.getElementById('bat-info').textContent = JSON.stringify(d.battery, null, 2);
    let f = await (await fetch('/api/fru/' + encodeURIComponent(d.machine.model))).json();
    document.getElementById('fru-info').textContent = JSON.stringify(f, null, 2);
  }catch(e){ console.error(e); }
}
setInterval(updateStats, 5000); updateStats();
</script></body></html>"""
    # Bez tego przeglądarka potrafi trzymać starą wersję strony (bez zakładek)
    return HTMLResponse(content=html, headers={"Cache-Control": "no-store, max-age=0"})

def serve():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5066)
