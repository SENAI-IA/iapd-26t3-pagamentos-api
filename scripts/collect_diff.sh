#!/usr/bin/env bash
# Coleta o diff e as mensagens de commit entre duas referências git.
# Uso: scripts/collect_diff.sh [BASE] [HEAD]   (padrão: HEAD~1 HEAD)
# Saída: markdown no stdout, pronto para o revisor ler (mensagem de commit + diff).
set -euo pipefail
BASE="${1:-HEAD~1}"
HEAD_REF="${2:-HEAD}"

echo "# Diff ${BASE}..${HEAD_REF}"
echo
echo "## Mensagens de commit"
echo
git log --format='- %h %s%n%n%b' "${BASE}..${HEAD_REF}" | sed '/^$/N;/^\n$/D'
echo
echo "## Arquivos alterados"
echo
git diff --stat "${BASE}" "${HEAD_REF}"
echo
echo "## Diff"
echo
echo '```diff'
git diff "${BASE}" "${HEAD_REF}" -- . ':(exclude)*.lock'
echo '```'
