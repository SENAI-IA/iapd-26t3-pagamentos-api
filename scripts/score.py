#!/usr/bin/env python3
"""Pontua um relatório de code review contra o gabarito.

Uso: python scripts/score.py reports/grupo-v0.md gabarito/gabarito.json [--tol 3] [--json saida.json]

Regras de casamento: um achado casa com um bug do gabarito quando aponta o mesmo
arquivo e uma linha dentro de ±tol das linhas do bug. Cada bug conta uma vez.

Pontuação da disputa:
  +3 bug crítico encontrado, +2 alto, +1 médio ou baixo
  -1 por falso positivo (achado que não casa com nenhum bug)
  -2 por achado sem linha válida (não entra no casamento)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_report import LINHA_RE, canon_sev, parse_report  # noqa: E402

PONTOS = {"critico": 3, "alto": 2, "medio": 1, "baixo": 1}


def linhas_do_achado(linha: str):
    m = LINHA_RE.match(linha)
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return range(min(a, b), max(a, b) + 1)


def casa(achado_linhas: range, bug: dict, tol: int) -> bool:
    for ln in bug["linhas"]:
        if any(abs(l - ln) <= tol for l in achado_linhas):
            return True
    return False


def score(findings: list[dict], gabarito: list[dict], tol: int) -> dict:
    encontrados: dict[str, dict] = {}
    falsos_positivos, sem_linha = [], []
    for f in findings:
        rng = linhas_do_achado(f["linha"])
        if rng is None:
            sem_linha.append(f)
            continue
        arquivo = f["arquivo"].replace("\\", "/").lstrip("./")
        match = None
        for bug in gabarito:
            if bug["id"] in encontrados:
                continue
            if bug["arquivo"] == arquivo and casa(rng, bug, tol):
                match = bug
                break
        if match:
            encontrados[match["id"]] = f
        else:
            falsos_positivos.append(f)

    pontos = 0
    por_sev = {s: {"total": 0, "encontrados": 0} for s in PONTOS}
    for bug in gabarito:
        sev = canon_sev(bug["severidade"])
        por_sev[sev]["total"] += 1
        if bug["id"] in encontrados:
            por_sev[sev]["encontrados"] += 1
            pontos += PONTOS[sev]
    pontos -= len(falsos_positivos)
    pontos -= 2 * len(sem_linha)
    recall = len(encontrados) / len(gabarito) if gabarito else 0.0
    return {
        "achados": len(findings),
        "bugs_no_gabarito": len(gabarito),
        "encontrados": sorted(encontrados),
        "nao_encontrados": [b["id"] for b in gabarito if b["id"] not in encontrados],
        "falsos_positivos": len(falsos_positivos),
        "sem_linha": len(sem_linha),
        "recall": round(recall, 3),
        "recall_por_severidade": {
            s: (round(v["encontrados"] / v["total"], 3) if v["total"] else None) for s, v in por_sev.items()
        },
        "pontos": pontos,
    }


def imprime(r: dict) -> None:
    print(f"{'Métrica':<26}{'Valor':>10}")
    print("-" * 36)
    print(f"{'Achados no relatório':<26}{r['achados']:>10}")
    print(f"{'Bugs no gabarito':<26}{r['bugs_no_gabarito']:>10}")
    print(f"{'Bugs encontrados':<26}{len(r['encontrados']):>10}")
    print(f"{'Falsos positivos':<26}{r['falsos_positivos']:>10}")
    print(f"{'Achados sem linha':<26}{r['sem_linha']:>10}")
    print(f"{'Recall':<26}{r['recall']:>10.1%}")
    for s, v in r["recall_por_severidade"].items():
        print(f"{'  recall ' + s:<26}{(f'{v:.0%}' if v is not None else 'n/a'):>10}")
    print("-" * 36)
    print(f"{'PONTOS':<26}{r['pontos']:>10}")
    print("\nEncontrados:     ", ", ".join(r["encontrados"]) or "nenhum")
    print("Não encontrados: ", ", ".join(r["nao_encontrados"]) or "nenhum")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("relatorio")
    ap.add_argument("gabarito")
    ap.add_argument("--tol", type=int, default=3)
    ap.add_argument("--json", dest="saida")
    a = ap.parse_args()
    findings = parse_report(Path(a.relatorio).read_text(encoding="utf-8"))
    gabarito = json.loads(Path(a.gabarito).read_text(encoding="utf-8"))["bugs"]
    r = score(findings, gabarito, a.tol)
    imprime(r)
    if a.saida:
        Path(a.saida).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
