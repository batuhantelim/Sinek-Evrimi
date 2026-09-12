#!/usr/bin/env python3
"""FAZ 4 adim 1 — dogal avci: 2x2 tasarim ve uc soru.

Tasarim (her seed icin DORT kosum):

                      gercek etiket      karistirma kontrolu
    avci VAR          faz4_avci          faz4_avci_kontrol
    avci YOK          faz4_avcisiz       faz4_avcisiz_kontrol

Neden dort: ayrimcilik (kin_bias_adj) MUTLAK degil, kendi eslesmis
kontrolune karsi okunur. Iki kolu kiyaslamak icin once her kolun kendi
t degeri hesaplanir, sonra t'ler kiyaslanir.

Uc soru:
  S1  Avci DIS-GRUP DUSMANLIGI uretiyor mu?  -> atk_t(avci) vs atk_t(avcisiz)
  S2  Avci IN-GRUP ISBIRLIGINI guclendiriyor mu? -> share_t, in-grup paylasim
      orani ve `clustering` (surulesme = dilution'in davranissal izi)
  S3  EN ILGINCI: avci altinda fedakarlik ile dusmanlik BIRLIKTE mi geliyor?
      -> donem-donem in-grup paylasim egrisi ile dis-grup saldiri egrisinin
         Pearson r'si. Faz 3'te bu ikisi ayrilabiliyordu.

Yeni mekanik EKLENMEZ: kollar arasindaki tek fark `rules.predator.enabled`
ve `rules.kinship.control`. `tests/test_tools.py` bunu sabitler.

    python tools/predator_sweep.py --seeds 42 --out runs/faz4/sonuc.jsonl
    python tools/predator_sweep.py --summary runs/faz4/sonuc.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from seed_sweep import CELLS, SEED_POP, run, series, welch_t  # noqa: E402

#: Kollarin rejime dokunma izni olan TEK anahtari.
PREDATOR_KEY = "rules.predator.enabled"

ARMS = {
    "avci": [f"{PREDATOR_KEY}=true"],
    "avcisiz": [f"{PREDATOR_KEY}=false"],
}

#: Faz 3 adim 2 / saglamlik taramasinin taban degerleri — yeni sonuc bunlara
#: karsi okunur. (docs/faz3/adim2_parochial.md, adim2_seed_taramasi.md)
FAZ3_HOSTILITY = 0.0442        # taban rejimde saldiri orani
FAZ3_SHARE_ADJ = 0.2802        # kin_bias_adj asil, 5 seed ortalamasi


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 3 or a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def read_rows(run_dir: str) -> list[dict]:
    """Hazir bir kosum klasorunden nesil/donem satirlarini oku."""
    path = run_dir if run_dir.endswith(".csv") else os.path.join(run_dir, "generations.csv")
    if not os.path.exists(path):
        raise SystemExit(f"bulunamadi: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _arm_from_rows(main: list[dict], ctrl: list[dict]) -> dict:
    """Tek kol: asil kosum + KENDI karistirma kontrolu (satirlar hazir).

    Iki kosum farkli uzunluktaysa (kontrol tukenip erken bitmis olabilir)
    ORTAK donem penceresine kirpilir: yoksa "son yari" iki kolda farkli
    zaman araliklarini gosterir ve t degeri anlamsizlasir. Kirpma olduysa
    `ctrl_short` bayragi rapora dusurulur — eslesmis kontrolu tukenmis bir
    kosumdan cikan ayrimcilik olcusu ZATEN guvenilir degildir.
    """
    if not main or not ctrl:
        raise SystemExit("kosum bos — koloni tukendi mi?")
    epochs_main, epochs_ctrl = len(main), len(ctrl)
    n = min(epochs_main, epochs_ctrl)
    main_w, ctrl_w = main[:n], ctrl[:n]

    share_t = welch_t(series(main_w, "kin_bias_adj"), series(ctrl_w, "kin_bias_adj"))
    attack_t = welch_t(
        series(main_w, "attack_kin_bias_adj"), series(ctrl_w, "attack_kin_bias_adj")
    )

    # S3: fedakarlik ve dusmanlik BIRLIKTE mi hareket ediyor?
    coup = pearson(series(main, "coop_in_group", 1.0), series(main, "attack_out_group", 1.0))
    coup_c = pearson(series(ctrl, "coop_in_group", 1.0), series(ctrl, "attack_out_group", 1.0))

    def m(rows, key, frac=0.5):
        return float(series(rows, key, frac).mean())

    out = {
        "share_adj_main": m(main, "kin_bias_adj"),
        "share_adj_ctrl": m(ctrl, "kin_bias_adj"),
        "share_t": share_t,
        "attack_adj_main": m(main, "attack_kin_bias_adj"),
        "attack_adj_ctrl": m(ctrl, "attack_kin_bias_adj"),
        "attack_t": attack_t,
        "coupling": coup,
        "coupling_ctrl": coup_c,
        # dort hucre — son ceyrek, firsata kosullu
        **{f"q_{k}": m(main, k, 0.25) for k in CELLS},
        **{f"qc_{k}": m(ctrl, k, 0.25) for k in CELLS},
        # seviye ayri, yon ayri raporlanir (eksen B dersi)
        "hostility": m(main, "hostility_rate", 0.25),
        "cooperation": m(main, "cooperation_rate", 0.25),
        # yan etkiler: avcinin ne DEGISTIRDIGINI olcmeden yorum yapilmaz
        "assortment": m(main, "kin_assortment"),
        "lineage_eff": m(main, "lineage_effective"),
        "clustering": m(main, "clustering"),
        "clustering_ctrl": m(ctrl, "clustering"),
        "food_fill": m(main, "food_fill"),
        "population": m(main, "population"),
        "opp_kin": m(main, "opp_kin"),
        "opp_nonkin": m(main, "opp_nonkin"),
        "epochs_main": epochs_main,
        "epochs_ctrl": epochs_ctrl,
        "ctrl_short": epochs_ctrl < epochs_main,
        # avlanma baskisi ve koloni sagligi (D/C ayrimi buna bakar)
        "deaths": m(main, "deaths"),
        "death_predator": m(main, "death_predator"),
        "predator_kills": m(main, "predator_kills"),
        "epochs": len(main),
    }
    out["pred_death_share"] = out["death_predator"] / max(1e-9, out["deaths"])
    out["out_share"] = out["opp_nonkin"] / max(1e-9, out["opp_kin"] + out["opp_nonkin"])
    return out


def _arm(seed: int, steps: int, extra: list[str], seed_pop: str | None) -> dict:
    return _arm_from_rows(
        run(seed, steps, False, seed_pop, extra),
        run(seed, steps, True, seed_pop, extra),
    )


def classify(pred: dict, base: dict) -> tuple[str, str]:
    """D (dusmanlik) / C (caresizlik) / belirsiz — eksen B'deki disiplin.

    COKME once kontrol edilir: aclik yuzunden herkesin herkese saldirdigi bir
    koloni "dusmanlik" degildir. Saldiri artmadiysa soru zaten dusmez, ama
    YON yine de raporlanir (eksen B'de 'artmadi' dalinin yonu gizlemesi hataydi).
    """
    hostility, base_h = pred["hostility"], base["hostility"]
    ratio = pred["q_attack_out_group"] / max(1e-9, pred["q_attack_in_group"])
    targeted = pred["attack_t"] < -2.0        # negatif t = yabanciya yoneliyor
    blind = abs(pred["attack_t"]) < 2.0
    # cokme: avcisiz kola gore populasyon ucte bir eridiyse
    collapse = pred["population"] < 0.67 * base["population"]

    if hostility < 1.5 * base_h:
        return "artmadi", (
            f"saldiri %{hostility * 100:.2f}, avcisiz kolda %{base_h * 100:.2f} "
            f"(D/C sorusu dusmuyor); ama YON: dis/ic {ratio:.2f}x, atk_t {pred['attack_t']:+.2f}"
        )
    if collapse:
        return "C", (
            f"populasyon {pred['population']:.0f} vs avcisiz {base['population']:.0f} "
            f"(-%{(1 - pred['population'] / max(1e-9, base['population'])) * 100:.0f}): "
            "saldiri artisi koloni cokusuyle birlikte geliyor"
        )
    if targeted and not blind:
        return "D", (
            f"saldiri %{base_h * 100:.2f} -> %{hostility * 100:.2f} ve YABANCIYA yoneldi "
            f"(atk_t {pred['attack_t']:+.2f}, dis/ic {ratio:.2f}x), koloni saglikli"
        )
    if blind:
        return "C", (
            f"saldiri arttı (%{hostility * 100:.2f}) ama akrabaliga KOR "
            f"(atk_t {pred['attack_t']:+.2f}): hedef ayrimi yok, ayrim gutmeyen bir artis"
        )
    return "belirsiz", f"atk_t {pred['attack_t']:+.2f}, dis/ic {ratio:.2f}x"


def _record(seed: int, steps: int, arms: dict, seconds: float) -> dict:
    verdict, why = classify(arms["avci"], arms["avcisiz"])
    return {
        "seed": seed,
        "steps": steps,
        "seconds": round(seconds, 1),
        "arms": arms,
        "dc_verdict": verdict,
        "dc_reason": why,
    }


def evaluate(seed: int, steps: int, seed_pop: str | None) -> dict:
    t0 = time.time()
    arms = {name: _arm(seed, steps, extra, seed_pop) for name, extra in ARMS.items()}
    return _record(seed, steps, arms, time.time() - t0)


def evaluate_dirs(seed: int, dirs: dict[str, str]) -> dict:
    """Dort kosum klasorunden ayni kaydi uretir (run.py ile paralel kosulunca).

    dirs: {"avci": yol, "avci_kontrol": yol, "avcisiz": yol,
           "avcisiz_kontrol": yol}
    """
    rows = {k: read_rows(v) for k, v in dirs.items()}
    arms = {
        "avci": _arm_from_rows(rows["avci"], rows["avci_kontrol"]),
        "avcisiz": _arm_from_rows(rows["avcisiz"], rows["avcisiz_kontrol"]),
    }
    steps = int(rows["avci"][-1]["step"]) if rows["avci"] else 0
    return _record(seed, steps, arms, 0.0)


# ------------------------------------------------------------------ rapor
def _row(label: str, a: dict) -> str:
    return (
        f"  {label:10s} {a['q_coop_in_group'] * 100:8.2f}% {a['q_coop_out_group'] * 100:9.2f}% "
        f"{a['q_attack_in_group'] * 100:8.2f}% {a['q_attack_out_group'] * 100:9.2f}% "
        f"| {a['share_adj_main'] * 100:+7.2f} {a['share_t']:+6.2f} "
        f"| {a['attack_adj_main'] * 100:+7.2f} {a['attack_t']:+6.2f} "
        f"| {a['coupling']:+5.2f} {a['coupling_ctrl']:+5.2f}"
    )


HEADER = (
    f"  {'kol':10s} {'pay ic':>9} {'pay dis':>10} {'sal ic':>9} {'sal dis':>10} "
    f"| {'kin_adj':>7} {'t':>6} | {'atk_adj':>7} {'t':>6} | {'r':>5} {'rk':>5}"
)


def print_detail(r: dict) -> None:
    print(f"\nseed {r['seed']}  ({r['seconds']:.0f} sn)")
    print(HEADER)
    for name in ("avci", "avcisiz"):
        print(_row(name, r["arms"][name]))
    p, b = r["arms"]["avci"], r["arms"]["avcisiz"]
    print(
        f"    yan etki : assortment {b['assortment']:.3f} -> {p['assortment']:.3f}"
        f" | kumelenme {b['clustering']:+.3f} -> {p['clustering']:+.3f}"
        f" | doluluk {b['food_fill']:.3f} -> {p['food_fill']:.3f}"
        f" | pop {b['population']:.0f} -> {p['population']:.0f}"
    )
    print(
        f"    ornek    : opp_kin {b['opp_kin']:.0f}->{p['opp_kin']:.0f}, "
        f"opp_dis {b['opp_nonkin']:.0f}->{p['opp_nonkin']:.0f} "
        f"(dis pay %{b['out_share'] * 100:.1f}->%{p['out_share'] * 100:.1f}), "
        f"etkin soy {b['lineage_eff']:.1f}->{p['lineage_eff']:.1f}"
    )
    print(
        f"    avlanma  : olumlerin %{p['pred_death_share'] * 100:.1f}'i avciya "
        f"(donem basina {p['predator_kills']:.0f} oldurme)"
    )
    print(f"    D/C      : {r['dc_verdict'].upper()} — {r['dc_reason']}")
    for name, a in r["arms"].items():
        if a.get("ctrl_short"):
            print(
                f"    ⚠ {name}: karistirma kontrolu ERKEN BITTI "
                f"({a['epochs_ctrl']} donem, asil {a['epochs_main']}) — koloni tukenmis. "
                "t degeri ortak pencerede hesaplandi ama bu kol OKUNMAZ."
            )
        if a["out_share"] < 0.10:
            print(
                f"    ⚠ {name}: dis-grup firsat payi %{a['out_share'] * 100:.1f} "
                f"(opp_dis {a['opp_nonkin']:.0f}) — in/out orani GURULTU."
            )


def summarize(path: str) -> None:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    if not rows:
        raise SystemExit(f"bos: {path}")
    rows.sort(key=lambda r: r["seed"])

    print("=" * 104)
    print(f"FAZ 4 ADIM 1 — AVCI 2x2 ({len(rows)} seed; her kol KENDI karistirma kontroluyle)")
    print("  dort hucre: son ceyrek, firsata kosullu | kin_adj/atk_adj: son yari, yuzde puan")
    print("  r: in-grup paylasim x dis-grup saldiri (donem-donem); rk ayni sey KONTROLDE")
    print("=" * 104)
    for r in rows:
        print_detail(r)

    print()
    print("=" * 104)
    print("UC SORU")
    print("=" * 104)
    at_p = np.array([r["arms"]["avci"]["attack_t"] for r in rows])
    at_b = np.array([r["arms"]["avcisiz"]["attack_t"] for r in rows])
    sh_p = np.array([r["arms"]["avci"]["share_t"] for r in rows])
    sh_b = np.array([r["arms"]["avcisiz"]["share_t"] for r in rows])
    cl_p = np.array([r["arms"]["avci"]["clustering"] for r in rows])
    cl_b = np.array([r["arms"]["avcisiz"]["clustering"] for r in rows])
    cp_p = np.array([r["arms"]["avci"]["coupling"] for r in rows])
    cp_b = np.array([r["arms"]["avcisiz"]["coupling"] for r in rows])

    def verdicts(ts):
        return {
            "yabanciya": int((ts < -2.0).sum()),
            "akrabaya": int((ts > 2.0).sum()),
            "kor": int((np.abs(ts) <= 2.0).sum()),
        }

    print(f"  S1 dis-grup dusmanlik  : atk_t avcili {at_p.mean():+.2f}, "
          f"avcisiz {at_b.mean():+.2f} (fark {at_p.mean() - at_b.mean():+.2f})")
    print(f"       kararlar avcili   : {verdicts(at_p)}")
    print(f"       kararlar avcisiz  : {verdicts(at_b)}")
    print(f"  S2 in-grup isbirligi   : share_t avcili {sh_p.mean():+.2f}, "
          f"avcisiz {sh_b.mean():+.2f} (fark {sh_p.mean() - sh_b.mean():+.2f})")
    print(f"       kumelenme         : {cl_b.mean():+.3f} -> {cl_p.mean():+.3f} "
          f"(fark {cl_p.mean() - cl_b.mean():+.3f})")
    print(f"  S3 fedakarlik x dusmanlik birlikte mi: r avcili {cp_p.mean():+.2f}, "
          f"avcisiz {cp_b.mean():+.2f}")
    print(f"       kontrolde (yapaylik sinamasi): avcili "
          f"{np.mean([r['arms']['avci']['coupling_ctrl'] for r in rows]):+.2f}")
    print()
    print(f"  taban (Faz 3 adim 2): saldiri %{FAZ3_HOSTILITY * 100:.2f}, "
          f"kin_bias_adj {FAZ3_SHARE_ADJ * 100:+.2f} puan")
    if len(rows) < 2:
        print("  ⚠ TEK SEED SONUC DEGILDIR — yon umut veriyorsa 2-3 seed'de teyit edin.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faz 4 adim 1: avci 2x2 taramasi")
    ap.add_argument("--seeds", nargs="*", type=int, default=[])
    ap.add_argument("--steps", type=int, default=12000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-seed-pop", action="store_true")
    ap.add_argument("--summary", default=None)
    ap.add_argument(
        "--from-runs",
        nargs=4,
        metavar=("AVCI", "AVCI_KONTROL", "AVCISIZ", "AVCISIZ_KONTROL"),
        default=None,
        help="dort hazir kosum klasoru (run.py ile paralel kosuldugunda)",
    )
    ap.add_argument("--seed-label", type=int, default=0, help="--from-runs icin seed etiketi")
    args = ap.parse_args(argv)

    if args.summary:
        summarize(args.summary)
        return 0
    if args.from_runs:
        names = ("avci", "avci_kontrol", "avcisiz", "avcisiz_kontrol")
        rec = evaluate_dirs(args.seed_label, dict(zip(names, args.from_runs)))
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        print_detail(rec)
        return 0
    if not args.seeds:
        raise SystemExit("--seeds, --from-runs ya da --summary verin")

    pop = None if args.no_seed_pop else os.path.join(ROOT, SEED_POP)
    out = None
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        out = open(args.out, "a", encoding="utf-8")
    for seed in args.seeds:
        r = evaluate(seed, args.steps, pop)
        print_detail(r)
        if out:
            out.write(json.dumps(r) + "\n")
            out.flush()
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
