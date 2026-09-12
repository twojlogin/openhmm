#!/usr/bin/env python3
"""openhmm CLI — szybki odczyt sprzętu w terminalu. PL domyślnie, --lang en."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys_reader

def load_lang(lang):
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", f"{lang}.json")
    try:
        with open(base, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def max_cpu_temp(sensors):
    m = 0.0
    for s in sensors.values():
        for v in s.get("temperatures", {}).values():
            try:
                m = max(m, float(v))
            except Exception:
                pass
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="pl", choices=["pl", "en"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sec", action="store_true",
                    help="Dołącz read-only raporty security-rocket (preflight/system/report). Nic nie zmienia w systemie.")
    a = ap.parse_args()
    L = load_lang(a.lang)
    d = sys_reader.get_all()
    m = d["machine"]

    sup = L.get("supported", "wspierany") if m["supported"] else L.get("unsupported", "niewspierany")
    print(f"{m['vendor']} -> {m['model']} [{m['product_code']}] {sup}")
    print(f"BIOS {m['bios_version']} ({m['bios_date']})")
    print(f"CPU: {d['cpu']['model']} ({d['cpu']['cores']}C/{d['cpu']['threads']}T)")
    print(f"\n-- {L.get('sensors', 'Temperatury')} --")
    for name, s in d["sensors"].items():
        for lbl, val in s["temperatures"].items():
            print(f"  {name}/{lbl}: {val}C")

    tmax = max_cpu_temp(d["sensors"])
    print("" if tmax <= 85 else L.get("temp_warn", "HOT"), end="")
    if tmax <= 85:
        print(L.get("temp_ok", "OK"))
    else:
        print()

    fan = d["fan"]
    print(f"\n-- {L.get('fan', 'Wentylator')}: {L.get('level','Poziom')}={fan['level']} {L.get('speed','Obroty')}={fan['speed']} RPM")
    print(L.get("fan_ok", "OK") if fan["enabled"] else L.get("fan_warn", "WARN"))
    print(f"\n-- {L.get('battery', 'Bateria')} --")
    for bn, bi in d["battery"].items():
        print(f"  {bn}: {bi.get('capacity','?')}% status={bi.get('status','?')}")
    if a.sec:
        import sec_bridge
        print(f"\n-- {L.get('tab_security', 'Bezpieczeństwo')} (read-only, security-rocket) --")
        for key, res in sec_bridge.run_all().items():
            mark = "✅" if res["ok"] else "⚠️"
            print(f"\n[{mark} {key}]")
            print(res["output"][:3000])
        d["security_note"] = "read-only bridge; modifying scripts are blocked"
    if a.json:
        print(json.dumps(d, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
