import threading
import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable

from ttkthemes import ThemedTk

import constants
from main import mainAction
from upload_manager.level_cache import save_last_level, load_next_order
from utils import Status

MODES = {
    "DEBUG": constants.DEBUG_SERVER,
    "TEST": constants.TEST_SERVER,
    "PROD": constants.PROD_SERVER
}


class GuideUploaderApp:
    def __init__(self, root):
        self.status = Status.START.value
        self.root = root
        self.root.iconbitmap("icon.ico")
        self.root.title("Загрузка методички")
        self.root.geometry("1200x800")
        self.root.resizable(False, False)
        self.selected_level_id = None
        self.base_url = tk.StringVar(value="DEBUG")
        self.steps = {}

        self.create_widgets()

    def set_level_id(self, level_id):
        self.selected_level_id = level_id

    def update_status(self, new_status):
        self.status = new_status
        self.status_label.config(text=f"Статус: {self.status.value}")

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TCombobox", font=("Segoe UI", 10), padding=4)
        style.configure("TEntry", font=("Segoe UI", 10), padding=4)

        frame = ttk.Frame(self.root, padding=(30, 20, 30, 20), style="TFrame")

        frame.pack(fill='both', expand=True)

        top_bar = ttk.Frame(frame, style="TFrame")
        top_bar.pack(fill='x', anchor='ne', pady=(0, 10))

        ttk.Label(top_bar, text="Режим:", font=("Segoe UI", 10, "bold")).pack(side='left', padx=(0, 5))
        for mode in MODES.keys():
            ttk.Radiobutton(
                top_bar,
                text=mode,
                variable=self.base_url,
                value=mode,
                style="TRadiobutton"
            ).pack(side='left', padx=(5, 0))

        ttk.Label(frame, text="Загрузка методички", font=("Segoe UI", 18, "bold"), background="#f5f6fa").pack(
            pady=(10, 15))

        button_status_frame = ttk.Frame(frame)
        button_status_frame.pack(pady=(0, 15))

        self.run_button = ttk.Button(button_status_frame, text="🚀 Старт", command=self.select_and_run)
        self.run_button.pack(side='left', padx=(0, 10))

        self.status_label = ttk.Label(button_status_frame, text=f"Статус: {self.status}", width=40)
        self.status_label.pack(side='left')

        self.steps_frame = ttk.LabelFrame(frame, text="Этапы обработки", style="TLabelframe")
        self.steps_frame.pack(fill='both', expand=True, pady=10)

        self.dynamic_frame = ttk.Frame(frame, style="TFrame")
        self.dynamic_frame.pack(fill='both', expand=True, pady=(10, 0))

        self.define_steps()

    def ask_level_selection(self, courses_data: Dict, on_selected: Callable[[int], None]):
        self.update_status(Status.SELECTING)
        self.clear_dynamic_frame()

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

    def ask_order_selection(self, guides_data: Dict, level_id: int, on_selected: Callable[[int], None]):
        self.clear_dynamic_frame()

        ttk.Label(self.dynamic_frame, text=f"📝 Методички в уровне «{guides_data['level_title']}»",
                  font=("Segoe UI", 12)).pack(pady=(10, 5))

        listbox = tk.Listbox(self.dynamic_frame, height=10)
        listbox.config(borderwidth=1, relief="flat", font=("Segoe UI", 10))

        for guide in guides_data['guides']:
            listbox.insert('end', f"{guide['order']}. {guide['title']}")
        listbox.pack(fill='x', pady=(0, 10))

        max_order = max([g['order'] for g in guides_data['guides']] or [0])
        next_order = load_next_order()

        input_frame = ttk.Frame(self.dynamic_frame)
        input_frame.pack(pady=5)

        ttk.Label(input_frame, text="Порядковый номер:").pack(side='left')
        order_var = tk.StringVar(value=str(next_order or max_order + 1))
        entry = ttk.Entry(input_frame, textvariable=order_var, width=5)
        entry.pack(side='left', padx=5)

        def confirm():
            value = entry.get().strip()
            if value.isdigit():
                order = int(value)
                if 1 <= order <= max_order + 1:
                    save_last_level(level_id, order)
                    self.mark_step_done("order_selected")
                    on_selected(order)
                    return
            tk.messagebox.showerror("Ошибка", f"Введите число от 1 до {max_order + 1}")

        ttk.Button(self.dynamic_frame, text="✅ Подтвердить", command=confirm).pack(pady=5)

    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

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

    def setup(self):
        self.clear_dynamic_frame()

        # clear checkboxes
        for step in self.steps:
            self.steps[step].set(False)

    def select_and_run(self):
        self.setup()

        selected_server = self.base_url.get()
        selected_url = MODES[selected_server]
        constants.set_base_url(selected_url)

        print(f"🌍 Сервер: {selected_server} → {constants.BASE_URL}")
        threading.Thread(target=mainAction, kwargs={"app": self}).start()


if __name__ == "__main__":
    root = ThemedTk(theme="radiance")
    app = GuideUploaderApp(root)
    root.mainloop()
