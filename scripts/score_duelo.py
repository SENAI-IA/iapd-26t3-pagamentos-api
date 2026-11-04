#!/usr/bin/env python3
"""Pontua o Duelo das Skills (S03 Aula 02) contra o gabarito do pagamentos-api.

Uso: python scripts/score_duelo.py --tema money relatorio-main.md relatorio-clean.md gabarito.json [--gatilho 4] [--tol 3]

Temas e bugs que contam cheio (+3): security = B03, B06, B08; correctness = B04, B09, B14;
money = B01, B02, B11. Bug de qualquer outro id do gabarito: +1 (até +2). Falso positivo na main: -2.
Qualquer achado na clean: -2. --gatilho N (0 a 5): +1 por prompt certo. Achado sem linha: não casa (zero).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import casa, linhas_do_achado  # noqa: E402
from validate_report import parse_report  # noqa: E402

TEMAS = {
    "security": ["B03", "B06", "B08"],
    "correctness": ["B04", "B09", "B14"],
    "money": ["B01", "B02", "B11"],
}


def casar(findings, gabarito, tol):
    encontrados, fp, sem_linha = {}, [], []
    for f in findings:
        rng = linhas_do_achado(f["linha"])
        if rng is None:
            sem_linha.append(f)
            continue
        arquivo = f["arquivo"].replace("\\", "/").lstrip("./")
        match = next((b for b in gabarito if b["id"] not in encontrados and b["arquivo"] == arquivo and casa(rng, b, tol)), None)
        if match:
            encontrados[match["id"]] = f
        else:
            fp.append(f)
    return encontrados, fp, sem_linha


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", choices=TEMAS, required=True)
    ap.add_argument("main_md")
    ap.add_argument("clean_md")
    ap.add_argument("gabarito")
    ap.add_argument("--gatilho", type=int, default=0, help="prompts de gatilho certos, 0 a 5")
    ap.add_argument("--tol", type=int, default=3)
    a = ap.parse_args()
    gabarito = json.loads(Path(a.gabarito).read_text(encoding="utf-8"))["bugs"]
    do_tema = set(TEMAS[a.tema])

    enc, fp_main, sl_main = casar(parse_report(Path(a.main_md).read_text(encoding="utf-8")), gabarito, a.tol)
    achados_clean = parse_report(Path(a.clean_md).read_text(encoding="utf-8"))

    tema_ok = sorted(i for i in enc if i in do_tema)
    outros = sorted(i for i in enc if i not in do_tema)
    p_tema = 3 * len(tema_ok)
    p_outros = min(2, len(outros))
    p_fp = -2 * len(fp_main)
    p_clean = -2 * len(achados_clean)
    p_gat = max(0, min(5, a.gatilho))
    total = p_tema + p_outros + p_fp + p_clean + p_gat

    print(f"Tema: {a.tema}  (bugs do tema: {', '.join(sorted(do_tema))})")
    print(f"{'bugs do tema encontrados':<32}{len(tema_ok)}/3  {p_tema:+d}  ({', '.join(tema_ok) or 'nenhum'})")
    print(f"{'bugs de outro tema':<32}{len(outros)}    {p_outros:+d}  ({', '.join(outros) or 'nenhum'})")
    print(f"{'falsos positivos na main':<32}{len(fp_main)}    {p_fp:+d}")
    print(f"{'achados sem linha (ignorados)':<32}{len(sl_main)}")
    print(f"{'achados na clean':<32}{len(achados_clean)}    {p_clean:+d}")
    print(f"{'gatilho':<32}{p_gat}/5  {p_gat:+d}")
    print("-" * 44)
    print(f"{'PONTOS (máx. 16)':<32}{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
