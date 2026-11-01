#!/usr/bin/env python3
"""Valida um relatório de code review no formato da turma.

Formato esperado (tabela markdown, uma linha por achado):

| # | Arquivo | Linha | Severidade | Categoria | Evidência | Sugestão |

- Arquivo: caminho relativo (ex.: app/db.py)
- Linha: inteiro ou intervalo (ex.: 42 ou 42-45)
- Severidade: crítico | alto | médio | baixo
- Categoria: correção | segurança | desempenho | dados/dinheiro | concorrência | manutenibilidade
- Evidência: trecho do código ou explicação concreta (mínimo 10 caracteres)
- Sugestão: como corrigir

Uso: python scripts/validate_report.py reports/meu-relatorio.md
Sai com código 1 se houver qualquer achado inválido.
"""
import json
import re
import sys
from pathlib import Path

import unicodedata

SEVERIDADES = {"critico", "critica", "alto", "alta", "medio", "media", "baixo", "baixa"}
CATEGORIAS = {"correcao", "seguranca", "desempenho", "performance", "dados/dinheiro", "dinheiro",
              "dados", "concorrencia", "manutenibilidade"}
LINHA_RE = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$")
_SEV_CANON = {"critica": "critico", "alta": "alto", "media": "medio", "baixa": "baixo"}
_CAT_CANON = {"dinheiro": "dados/dinheiro", "dados": "dados/dinheiro", "performance": "desempenho"}


def norm(s: str) -> str:
    """Minúsculas, sem acentos, sem espaços nas pontas: 'Segurança' -> 'seguranca'."""
    s = unicodedata.normalize("NFKD", s.strip().lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def canon_sev(s: str) -> str:
    n = norm(s)
    return _SEV_CANON.get(n, n)


def canon_cat(s: str) -> str:
    n = norm(s)
    return _CAT_CANON.get(n, n)


def parse_report(text: str) -> list[dict]:
    """Extrai as linhas de tabela que têm 7 colunas (com a coluna #) ou 6 (sem)."""
    findings = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 7:
            cells = cells[1:]
        if len(cells) != 6:
            continue
        if set(cells[0]) <= {"-", ":", " "}:          # linha separadora
            continue
        if norm(cells[0]) in {"arquivo", "file"}:      # cabeçalho
            continue
        findings.append(dict(zip(["arquivo", "linha", "severidade", "categoria", "evidencia", "sugestao"], cells)))
    return findings


def validate(findings: list[dict]) -> list[str]:
    errors = []
    for i, f in enumerate(findings, 1):
        pre = f"achado {i} ({f['arquivo']}:{f['linha']})"
        if not f["arquivo"] or " " in f["arquivo"] or not f["arquivo"].endswith((".py", ".sh", ".md", ".json", ".ini", ".txt")):
            errors.append(f"{pre}: arquivo inválido '{f['arquivo']}'")
        if not LINHA_RE.match(f["linha"]):
            errors.append(f"{pre}: linha ausente ou inválida '{f['linha']}' (use 42 ou 42-45)")
        if norm(f["severidade"]) not in SEVERIDADES:
            errors.append(f"{pre}: severidade inválida '{f['severidade']}'")
        if norm(f["categoria"]) not in CATEGORIAS:
            errors.append(f"{pre}: categoria inválida '{f['categoria']}'")
        if len(f["evidencia"]) < 10:
            errors.append(f"{pre}: evidência vazia ou curta demais")
        if len(f["sugestao"]) < 5:
            errors.append(f"{pre}: sugestão ausente")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    findings = parse_report(text)
    if not findings:
        print("ERRO: nenhum achado encontrado. O relatório precisa de uma tabela com 6 colunas.")
        return 1
    errors = validate(findings)
    print(json.dumps({"achados": len(findings), "erros": len(errors)}, ensure_ascii=False))
    for e in errors:
        print(" -", e)
    if errors:
        return 1
    print("OK: relatório válido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
