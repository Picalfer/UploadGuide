import threading
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable

import constants
from main import mainAction
from upload_manager.level_cache import save_last_level

MODES = {
    "DEBUG": constants.DEBUG_SERVER,
    "TEST": constants.TEST_SERVER,
    "PROD": constants.PROD_SERVER
}


class GuideUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Загрузка методички")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        self.selected_level_id = None
        self.base_url = tk.StringVar(value="DEBUG")
        self.steps = {}

        self.create_widgets()

    def set_level_id(self, level_id):
        self.selected_level_id = level_id

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill='x', anchor='ne')

        ttk.Label(top_bar, text="Режим:").pack(side='left')
        for mode in MODES.keys():
            ttk.Radiobutton(
                top_bar,
                text=mode,
                variable=self.base_url,
                value=mode
            ).pack(side='left', padx=(5, 0))

        ttk.Label(frame, text="Загрузка методички", font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))

        self.run_button = ttk.Button(frame, text="🚀 Старт", command=self.select_and_run)
        self.run_button.pack(pady=10)

        self.steps_frame = ttk.LabelFrame(frame, text="Этапы обработки")
        self.steps_frame.pack(fill='both', expand=True, pady=10)

        self.dynamic_frame = ttk.Frame(frame)
        self.dynamic_frame.pack(fill='both', expand=True)

        self.define_steps()

    def ask_level_selection(self, courses_data: Dict, on_selected: Callable[[int], None]):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.dynamic_frame, text="📚 Выберите уровень", font=("Segoe UI", 12)).pack(pady=(10, 5))

        level_map = {}  # видимый текст -> level_id

        for course in courses_data['courses']:
            for level in course['levels']:
                text = f"{course['course_title']} > {level['level_title']} (ID: {level['level_id']})"
                level_map[text] = level['level_id']

        combo = ttk.Combobox(self.dynamic_frame, values=list(level_map.keys()), state="readonly", width=60)
        combo.pack(pady=5)
        combo.set("Выберите уровень...")

        def on_confirm():
            selected = combo.get()
            if selected in level_map:
                level_id = level_map[selected]
                save_last_level(level_id)  # сохраняем как раньше
                self.mark_step_done("level_selected")
                on_selected(level_id)

        ttk.Button(self.dynamic_frame, text="✅ Подтвердить", command=on_confirm).pack(pady=5)

    def define_steps(self):
        step_defs = [
            ("word_selected", "Выбор Word файла"),
            ("images_extracted", "Извлечение изображений"),
            ("docx_compressed", "Сжатие документа"),
            ("html_converted", "Конвертация в HTML"),
            ("images_renamed", "Переименование изображений"),
            ("upload_prepared", "Подготовка архива"),
            ("uploaded", "Загрузка завершена"),
        ]
        for key, label in step_defs:
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(self.steps_frame, text=label, variable=var, state="disabled")
            cb.pack(anchor='w', pady=2)
            self.steps[key] = var

    def mark_step_done(self, step_key):
        if step_key in self.steps:
            self.steps[step_key].set(True)

    def select_and_run(self):
        selected_label = self.base_url.get()
        selected_url = MODES[selected_label]
        constants.set_base_url(selected_url)

        print(f"🌍 Сервер: {selected_label} → {constants.BASE_URL}")
        threading.Thread(target=mainAction, kwargs={"app": self}).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = GuideUploaderApp(root)
    root.mainloop()
