#!/bin/bash
# Создаёт новую папку инициативы из шаблона
# Использование: ./new-initiative.sh "продакт" "название-инициативы"

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Использование: ./new-initiative.sh \"имя-продакта\" \"название-инициативы\""
  echo "Пример:        ./new-initiative.sh ivan vk-tickets-vk-video"
  exit 1
fi

PM="$1"
NAME="$2"
BASE="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$BASE/template"
TARGET="$BASE/$PM/$NAME"

# Создаём папку продакта если нет
mkdir -p "$BASE/$PM"

if [ -d "$TARGET" ]; then
  echo "Папка '$PM/$NAME' уже существует"
  exit 1
fi

cp -r "$TEMPLATE" "$TARGET"

# Создаём симлинк ~/.claude/skills → ~/pipeline/.claude/skills (один раз)
if [ ! -e ~/.claude/skills ]; then
  ln -sf ~/pipeline/.claude/skills ~/.claude/skills
  echo "✓ Skills linked: ~/.claude/skills → ~/pipeline/.claude/skills"
fi

# Подставляем название и продакта в CONTEXT.md
sed -i '' "s/\[НАЗВАНИЕ\]/$NAME/g" "$TARGET/CONTEXT.md"
sed -i '' "s/\[ИМЯ\]/$PM/g" "$TARGET/CONTEXT.md"

# Инициализируем трекер статуса
python3 -c "
import json, sys
d = {
  'pm': sys.argv[1],
  'initiative': sys.argv[2],
  'pending': {
    'analytics_brief': None, 'survey_brief': None, 'audience_brief': None,
    'analytics_results': None, 'survey_results': None,
    'design_brief': None, 'gate1_challenge': None, 'gate2_challenge': None
  }
}
print(json.dumps(d, indent=2, ensure_ascii=False))
" "$PM" "$NAME" > "$TARGET/output/status.json"

echo "✓ Инициатива создана: $TARGET"
echo ""
echo "Дальше:"
echo "  1. Заполни $TARGET/CONTEXT.md"
echo "  2. Положи скрины CJM в $TARGET/CJM/ (формат: 01_шаг.png, 02_шаг.png...)"
echo "  3. Открой Claude Code в папке $TARGET"
echo ""
echo "Пайплайн команд:"
echo ""
echo "  ── Phase 1: Исследование проблемы + Образ решения → Gate 1 ──"
echo "  1.  /analyze-cjm             → гипотезы проблем из CJM"
echo "  2.  /synthetic-research      → синтетика или задача на реальное исследование"
echo "  3.  /competitor-research     → конкурентный анализ"
echo "  4.  /generate-research       → бриф аналитику + опрос"
echo "  5.  /create-survey-audience  → выборка для опроса"
echo "  6.  /validate-problems       → валидация гипотез по данным"
echo "  7.  /solution-hypotheses     → гипотезы решений"
echo "  8.  /sketch-solution         → образ решения + Figma"
echo "  9.  /review-design           → ревью дизайна"
echo "  10. /create-presentation     → презентация Gate 1 (.md + .pptx)"
echo ""
echo "  ── Phase 2: Проработка решения → Gate 2 ──"
echo "  11. /create-design-brief     → задача дизайнеру + UX-исследование"
echo "  12. /estimate-with-dev       → оценка с разработкой"
echo "  13. /finalize-prd            → финализация PRD"
echo "  14. /design-ab-test          → дизайн AB-теста"
echo "  15. /create-gate2-presentation → презентация Gate 2 (.md + .pptx)"
echo ""
echo "      /create-jira             → Jira тикеты (после Gate 2)"
