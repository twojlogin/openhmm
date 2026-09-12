#!/usr/bin/env python3
"""
i_na_chuj_mi_to.py — odpowiada na najważniejsze pytanie laika.
Użycie: ./i_na_chuj_mi_to.py [nazwa_rzeczy]
Bez argumentu: tłumaczy wszystko.
"""
import sys

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
    if not args:
        print("Pytasz 'i na chuj mi to?' — słusznie. Oto cały OpenHMM:\n")
        for k, v in WYJAŚNIENIA.items():
            print(f"  {k:12} → {v}")
        print("\nJak dalej nie wiesz — odpal ./status i patrz co wypluje.")
        return
    for a in args:
        k = a.lower().strip()
        print(f"  {k:12} → {WYJAŚNIENIA.get(k, 'Tego to ja sam nie wiem po co. Spytaj Arka.')}")
    print("\nA tak serio: jak coś jest w repo, to znaczy że kiedyś było potrzebne. Chyba.")

if __name__ == "__main__":
    main()
