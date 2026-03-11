# PM Pipeline

Репозиторий содержит шаблоны и скилы для работы над продуктовыми инициативами в Claude Code.

## Структура

```
pipeline/
├── .claude/skills/          ← скилы (симлинк: ~/.claude/skills → эта папка)
│   ├── consulting-problem-solving/
│   │   ├── SKILL.md
│   │   └── references/
│   └── <skill-name>/
│       └── SKILL.md
├── template/                ← шаблон новой инициативы
│   ├── CLAUDE.md            ← инструкции пайплайна (копируется в инициативу)
│   ├── CONTEXT.md           ← контекст инициативы (заполняет продакт)
│   ├── CJM/                 ← материалы CJM
│   ├── research/            ← исследования
│   ├── output/              ← артефакты (PRD, гипотезы, презентации)
│   └── slides/              ← шаблоны слайдов Gate 1 / Gate 2
└── tools/
    └── scripts/
        ├── new-initiative.sh   ← создаёт папку инициативы из шаблона
        ├── generate-pptx.py    ← генерирует .pptx из presentation.md
        └── dashboard.py        ← дашборд по инициативам
```

## Начало работы

Создать новую инициативу:
```bash
~/pipeline/tools/scripts/new-initiative.sh <имя-продакта> <название-инициативы>
```

Затем заполнить `CONTEXT.md` и открыть Claude Code в папке инициативы.

## Скилы

Скилы доступны через `~/.claude/skills/` (симлинк создаётся автоматически при первом запуске `new-initiative.sh`).

Каждый скил: `~/.claude/skills/<название>/SKILL.md`
