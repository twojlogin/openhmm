#!/usr/bin/env python3
"""
i_na_chuj_mi_to.py — odpowiada na najważniejsze pytanie laika.
Użycie: ./i_na_chuj_mi_to.py [nazwa_rzeczy]
Bez argumentu: tłumaczy wszystko.
"""
import sys

# Kolory ANSI do terminala
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_END = "\033[0m"

WYJAŚNIENIA = {
    "openhmm": "Żeby wiedzieć co boli Twój ThinkPad zanim padnie. Temperatury, fan, bateria — na tacy.",
    "sys_reader": "Czyta /sys i /proc. Bez tego dashboard nie wie nawet jaki masz model.",
    "distro": "Żeby na Fedorze nie kazać Ci klepać apt-get jak debilowi. Sam wykrywa menedżer pakietów.",
    "cli": "Jak nie chcesz przeglądarki. Szybki tekst w terminalu: co jest OK, co się pali.",
    "dashboard": "Jak wolisz klikać niż czytać terminal. Te same dane, ładniej podane.",
    "fru_db": "Żebyś kupił DOBRĄ część (właściwy FRU), a nie pierwszą z brzegu z Allegro.",
    "sec_bridge": "Żeby podejrzeć czy SSH/UFW/AppArmor żyją — bez ryzyka, tylko odczyt.",
    "venv": "Żeby syf z pip nie lał się po całym systemie. Porządek musi być.",
    "banner": "Żeby było wiadomo czyje to. Arek (H5N1). Podpis jak na murze.",
    "thinkfan": "Żeby wentylator nie wył jak odkurzacz ani nie spał gdy CPU ma 95°C.",
    "lynis": "Audytor co mówi Ci że masz 64/100 i co poprawić. Taki surowy nauczyciel.",
    "nvidia": "Na tym T440p? Do niczego. Wyłącz w BIOS i zapomnij. Serio.",
    "demo.sh": "Żeby nagrać gifa do README i wyglądać jak profesjonalny githubowiec.",
    "readme": "Żeby laik wiedział co kliknąć zanim napisze do Ciebie 'a jak to odpalić'.",
}

def main():
    args = sys.argv[1:]
    
    if args and args[0] in ["--help", "-h"]:
        print(f"Użycie: {C_GREEN}./i_na_chuj_mi_to.py{C_END} [{C_CYAN}nazwa_komponentu{C_END}]")
        print("Bez argumentu wypisuje ściągawkę ze wszystkiego.")
        return

    if not args:
        print(f"Pytasz '{C_RED}i na chuj mi to?{C_END}' — słusznie. Oto cały OpenHMM:\n")
        for k, v in WYJAŚNIENIA.items():
            # Wyróżnienie specyficznych podzespołów na czerwono/żółto dla klimatu
            color = C_RED if k in ["nvidia", "lynis"] else C_CYAN
            print(f"  {color}{k:12}{C_END} → {v}")
        print(f"\nJak dalej nie wiesz — odpal {C_GREEN}./status{C_END} i patrz co wypluje.")
        return
        
    for a in args:
        k = a.lower().strip()
        if k in WYJAŚNIENIA:
            print(f"  {C_CYAN}{k:12}{C_END} → {WYJAŚNIENIA[k]}")
        else:
            print(f"  {C_YELLOW}{k:12}{C_END} → Tego to ja sam nie wiem po co. Spytaj Arka.")
            
    print(f"\nA tak serio: jak coś jest w repo, to znaczy że {C_GREEN}kiedyś było potrzebne{C_END}. Chyba.")

if __name__ == "__main__":
    main()
