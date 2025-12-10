import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import yaml

# Шляхи відносно каталогу meta_agent
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STAGES_PATH = os.path.join(BASE_DIR, "stages.yaml")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")


def slugify(text: str) -> str:
    """
    Проста "очистка" назви для файлу:
    - обрізаємо пробіли
    - замінюємо пробіли на _
    - видаляємо небезпечні символи для імені файлу
    (кирилиця лишається, Windows її нормально переварює)
    """
    text = text.strip()
    text = text.replace(" ", "_")
    for ch in r'\/:*?"<>|':
        text = text.replace(ch, "")
    if not text:
        text = "task"
    return text


def load_stages():
    if not os.path.exists(STAGES_PATH):
        return []

    with open(STAGES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    if isinstance(data, list):
        return data
    else:
        # На всякий випадок, якщо формат зламають вручну
        return []


def save_stages(stages):
    with open(STAGES_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            stages,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )


def on_start():
    task_name = entry_name.get().strip()
    task_body = text_prompt.get("1.0", tk.END).strip()

    if not task_name:
        messagebox.showerror("Помилка", "Заповни поле 'Назва завдання'.")
        return

    if not task_body:
        messagebox.showerror("Помилка", "Текст завдання порожній.")
        return

    # Завантажуємо існуючі стадії
    stages = load_stages()
    next_idx = len(stages) + 1

    slug = slugify(task_name)
    filename = f"stage_{next_idx:02d}_{slug}.md"

    # Шлях до файлу prompt
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    md_path = os.path.join(PROMPTS_DIR, filename)

    try:
        # 1) Пишемо .md з тим, що ввів користувач
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(task_body + "\n")

        # 2) Додаємо запис у stages.yaml
        rel_prompt_path = f"prompts/{filename}"
        stages.append(
            {
                "name": task_name,
                "prompt": rel_prompt_path,
            }
        )
        save_stages(stages)

    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося зберегти файли:\n{e}")
        return

    messagebox.showinfo(
        "Готово",
        f"Створено файл:\n  {filename}\n"
        f"і додано новий етап у stages.yaml.",
    )

    # Очищаємо поля
    # (якщо хочеш, можна цього не робити)
    # entry_name.delete(0, tk.END)
    # text_prompt.delete("1.0", tk.END)


def main():
    global entry_name, text_prompt

    root = tk.Tk()
    root.title("Meta-Agent GUI — новий етап")

    # Трохи падінгу
    root.geometry("700x500")

    # Рядок з назвою задачі
    frame_top = tk.Frame(root)
    frame_top.pack(fill=tk.X, padx=10, pady=10)

    lbl_name = tk.Label(frame_top, text="Назва завдання:")
    lbl_name.pack(side=tk.LEFT)

    entry_name = tk.Entry(frame_top)
    entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    # Великий текстовий блок (як чат)
    lbl_prompt = tk.Label(root, text="Текст завдання / промпт (.md):")
    lbl_prompt.pack(anchor="w", padx=10)

    text_prompt = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    text_prompt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # Кнопка Start
    btn_start = tk.Button(root, text="Start", command=on_start)
    btn_start.pack(pady=(0, 10))

    root.mainloop()


if __name__ == "__main__":
    main()
