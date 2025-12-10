# ROLE

You are **Codex** running inside the **Meta-Agent project at `C:/meta_agent`**.

Your job in THIS STAGE is to **перетворити Meta-Agent на сервіс, який вміє виконувати одну конкретну задачу з .md-файлу (task-режим)**, не ламаючи існуючий режим по `stages.yaml`.

Meta-Agent має стати зручним "ядром", яким зможе керувати Supervisor-агент:
- створювати task-файли,
- запускати Meta-Agent на один task,
- читати структурований результат (JSON-репорт).

---

# GOAL OF THIS STAGE

**Stage 1: Supervisor-ready Meta-Agent core**

Зробити так, щоб Meta-Agent:

1. Міг запускатися в режимі **"однієї задачі"**:
   - `python meta_agent.py --task tasks/S1_ai_scalper_bot.md`
2. Мав **виділене ядро** (функція `run_task(...)`), яке:
   - читає `.md`-файл із задачею,
   - будує промпт до OpenAI так само, як для звичайних стадій,
   - виконує один виклик до моделі,
   - зберігає результати змін у цільовому проєкті (ai_scalper_bot) через існуючий протокол `===FILE: ...===`,
   - формує **JSON-звіт** з підсумком роботи.
3. Писав результати у стандартизовані каталоги:
   - `tasks/` — вхідні task-файли для Supervisor,
   - `reports/` — звіти в форматах `.md` / `.json`.

Це **інфраструктурний етап**: ми не змінюємо торгового бота, не чіпаємо логіку трейдингу. Ми покращуємо саме Meta-Agent.

---

# CURRENT CONTEXT (what you should assume)

Проєкт Meta-Agent (спрощено):

- `meta_agent.py`  
  Головний скрипт, який:
  - читає `stages.yaml`,
  - по черзі виконує етапи,
  - для кожного етапу:
    - формує промпт,
    - викликає Codex через `codex_client.py`,
    - зберігає згенеровані файли (через file_manager).

- `codex_client.py`  
  Обгортка навколо OpenAI-клієнта (chat.completions.create).

- `prompt_builder.py`  
  Збирає повний промпт:
  - HEADER / інструкції,
  - текст етапу з `.md` у `prompts/`,
  - контекст проєкту (файли ai_scalper_bot).

- `project_scanner.py`  
  Читає цільовий проєкт (наприклад, `../ai_scalper_bot`) і додає в промпт файли у форматі:
  ```text
  ===FILE: relative/path/to/file.py===
  <file content>
file_manager.py
Розбирає відповідь моделі, знаходить блоки:

text
Копіювати код
===FILE: relative/path/to/file.py===
<new content>
та записує їх у цільовий проєкт.

stages.yaml
Список етапів:

yaml
Копіювати код
- name: "Some stage"
  prompt: "prompts/stage_01_something.md"
prompts/
.md-файли з інструкціями для кожного етапу (тих, що зараз запускаються Meta-Agent’ом).

Також є новий GUI (Tkinter), який вміє:

створювати нові .md у prompts/,

дописувати stages.yaml.

GUI чіпати в цьому етапі не потрібно.

WHAT TO IMPLEMENT IN THIS STAGE
1. Новий модуль meta_core.py з функцією run_task
Створи новий файл meta_core.py (або аналогічний за назвою), який міститиме основну функцію:

python
Копіювати код
def run_task(task_path: str) -> dict:
    """
    Виконує один task (.md-файл) через Meta-Agent.

    Кроки:
    1) Читає task-файл і розбирає його зміст.
    2) Формує повний промпт до OpenAI:
       - HEADER / системні інструкції (як у поточному meta_agent.py).
       - Текст із task-файлу.
       - Контекст проєкту (через project_scanner).
    3) Викликає Codex через codex_client.
    4) Передає відповідь у file_manager для застосування змін до цільового проєкту.
    5) Збирає підсумкову інформацію:
       - які файли створені/змінені,
       - чи були помилки,
       - короткий summary (якщо можливо).
    6) Пише JSON-репорт у каталог reports/.
    7) Повертає dict зі структурованими даними (опис нижче).
    """
Формат повернення run_task
run_task має повертати приблизно таку структуру:

python
Копіювати код
{
    "task_id": "S1_ai_scalper_bot",    # з імені файлу або HEADER-а
    "task_path": "tasks/S1_ai_scalper_bot.md",
    "status": "ok" or "error",
    "error_message": None or "<text>",
    "changed_files": [
        "bot/core/execution.py",
        "bot/risk/position_sizing.py",
    ],
    "report_md_path": "reports/S1_ai_scalper_bot_report.md",
    "report_json_path": "reports/S1_ai_scalper_bot_report.json",
}
Якщо щось пішло не так (виняток, помилка при збереженні файлів, некоректна відповідь моделі), запиши status: "error" та змістовний error_message.

JSON-репорт
Створи окрему допоміжну функцію в meta_core.py, наприклад:

python
Копіювати код
def write_json_report(result: dict) -> str:
    """
    Приймає результат run_task, записує його як JSON у reports/.
    Повертає шлях до JSON-файлу.
    """
Формат JSON може бути таким:

json
Копіювати код
{
  "task_id": "S1_ai_scalper_bot",
  "status": "ok",
  "summary": "Короткий опис, що було зроблено",
  "changed_files": ["..."],
  "risks": [],
  "notes": [],
  "meta": {
    "started_at": "...",
    "finished_at": "...",
    "model": "gpt-5.1-code-large"
  }
}
Мінімум: task_id, status, changed_files і таймінги.

2. Розширити meta_agent.py CLI-режимом
Доопрацюй meta_agent.py, щоб він умів працювати в двох режимах:

Старий режим (за замовчуванням) — як зараз:

якщо НЕ передано --task, читає stages.yaml і виконує всі етапи по черзі.

Новий режим однієї задачі:

якщо передано --task PATH:

не використовує stages.yaml,

просто викликає run_task(task_path=PATH) з meta_core,

виводить коротке summary в консоль,

завершує роботу.

Набір аргументів командного рядка (через argparse):

text
Копіювати код
--mode stages|task     (опційно, для явного вибору; за замовчуванням auto)
--task PATH            (шлях до .md task-файлу)
--task-id ID           (опційно: якщо хочемо обробити tasks/ID.md)
Логіка:

Якщо передано --task або --task-id → режим task.

Якщо ні — режим stages як зараз.

ВАЖЛИВО: не ламай поточний сценарій запуску без аргументів:

bash
Копіювати код
python meta_agent.py
має працювати так само, як до змін.

3. Стандартизовані каталоги tasks/ і reports/
Додай просту константу/конфіг у Meta-Agent:

TASKS_DIR = os.path.join(BASE_DIR, "tasks")

REPORTS_DIR = os.path.join(BASE_DIR, "reports")

run_task має:

приймати task_path (абсолютний або відносний),

писати звіти в REPORTS_DIR за шаблоном:

reports/<task_id>_report.md

reports/<task_id>_report.json

Для task_id можна брати:

ім’я файлу без розширення (S1_ai_scalper_bot),

або явно з першого рядка task-файлу, якщо він починається з:

text
Копіювати код
TASK_ID: S1_ai_scalper_bot
Якщо є і HEADER, і ім’я файлу — можна зробити просту евристику (взяти HEADER, а ім’я — fallback).

4. Мінімальні зміни в file_manager.py (якщо потрібно)
Якщо зараз file_manager НЕ повертає список змінених файлів, додай зручний спосіб отримати цю інформацію:

або змінити існуючу функцію, щоб вона повертала list[str] із шляхами змінених файлів;

або додати нову функцію/обгортку, яку використовуватиме meta_core.run_task.

Ціль: run_task має знати, які файли були змінені, щоб включити їх у JSON-звіт.

Не змінюй протоколи формату ===FILE: ...=== у відповідях моделі.

CONSTRAINTS / DO NOT
Не змінювати логіку торгового бота (папка ../ai_scalper_bot) по суті.
Ти можеш торкатись її тільки через стандартний механізм ===FILE: ...=== у відповіді моделі — це робиться не в цьому етапі.

Не видаляти існуючі функції Meta-Agent, не ламати поточний режим роботи по stages.yaml.

Не додавати автокоміти / git-пуші / зміну секретів.
Жодних змін до .env, ключів, файлів конфігурації без прямого завдання.

Не змінювати GUI у цьому етапі.
GUI може бути розширений пізніше, вже поверх run_task(...).

Пиши код з коментарями та docstring, де це покращує розуміння:

як використовувати run_task,

які поля в JSON-репорті,

як працюють нові CLI-прапорці.

OUTPUT REQUIREMENTS
У відповідь ти маєш:

Надати конкретні фрагменти коду для нових файлів:

meta_core.py (повний файл).

Показати зміни для існуючих файлів:

meta_agent.py (оновлений повний файл або чітко виділені блоки, які треба додати/замінити),

file_manager.py (якщо змінюється; показати повну модифіковану функцію/клас).

Формат виводу:

text
Копіювати код
===FILE: meta_core.py===
<повний вміст файлу>

===FILE: meta_agent.py===
<оновлений вміст або чітко відредагована версія>

===FILE: file_manager.py===
<оновлений вміст ключових частин, якщо були зміни>
Не використовуй дифи/patch-синтаксис.
Записуй файли повністю, щоб file-manager міг просто перезаписати їх у файловій системі.
