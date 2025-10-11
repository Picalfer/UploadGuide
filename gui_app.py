import threading
import customtkinter as ctk
from typing import Dict, Callable
import tkinter as tk
from tkinter import messagebox
import sys
import io
from datetime import datetime

import constants
from main import mainAction
from upload_manager.level_cache import save_last_level, load_next_order
from utils import Status

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

MODES = {
    "DEBUG": constants.DEBUG_SERVER,
    "TEST": constants.TEST_SERVER,
    "PROD": constants.PROD_SERVER
}


class ConsoleRedirector(io.TextIOBase):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert("end", message)
        self.text_widget.see("end")
        self.text_widget.update_idletasks()

    def flush(self):
        pass


class ModernGuideUploaderApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.status = Status.START.value
        self.root.title("Guide Uploader")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.selected_level_id = None
        self.base_url = ctk.StringVar(value="DEBUG")
        self.steps = {}

        self.setup_ui()
        self.setup_console()

    def setup_console(self):
        sys.stdout = ConsoleRedirector(self.console_text)
        sys.stderr = ConsoleRedirector(self.console_text)

    def set_level_id(self, level_id):
        self.selected_level_id = level_id

    def update_status(self, new_status):
        self.status = new_status
        self.status_label.configure(text=new_status.value)
        progress_value = list(Status).index(new_status) / (len(Status) - 1)
        self.progress_bar.set(progress_value)

    def update_detailed_status(self, status: Status, description: str = ""):
        self.status = status
        status_text = status.value
        if description:
            status_text += f" | {description}"
        self.status_label.configure(text=status_text)
        progress_value = list(Status).index(status) / (len(Status) - 1)
        self.progress_bar.set(progress_value)

    def setup_ui(self):
        # Настраиваем сетку окна
        self.root.rowconfigure(0, weight=0)  # хедер фиксированный
        self.root.rowconfigure(1, weight=1)  # основное содержимое растягивается
        self.root.columnconfigure(0, weight=1)

        # Хедер
        self.header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)
        self.create_header()

        # Основная часть (sidebar + content + console)
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        # layout внутри main_frame — через pack
        self.create_sidebar()
        self.create_main_content()
        #self.create_console()

    def create_header(self):
        title_label = ctk.CTkLabel(
            self.header_frame,
            text="📚 Guide Uploader",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side='left', padx=30, pady=20)

        mode_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        mode_frame.pack(side='right', padx=30, pady=20)

        ctk.CTkLabel(mode_frame, text="Mode:", font=ctk.CTkFont(weight="bold")).pack(side='left', padx=(0, 10))

        for mode in MODES.keys():
            ctk.CTkRadioButton(
                mode_frame,
                text=mode,
                variable=self.base_url,
                value=mode
            ).pack(side='left', padx=(0, 15))

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.main_frame, width=250, corner_radius=12)
        self.sidebar.pack(side='left', fill='y', padx=(0, 15), pady=15)
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="Progress",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))

        self.progress_bar = ctk.CTkProgressBar(self.sidebar, height=8, corner_radius=4)
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 20))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text=self.status,
            font=ctk.CTkFont(size=13),
            wraplength=200
        )
        self.status_label.pack(pady=(0, 20))

        self.run_button = ctk.CTkButton(
            self.sidebar,
            text="🚀 Start Upload",
            command=self.select_and_run,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10
        )
        self.run_button.pack(side='bottom', fill='x', padx=20, pady=20)

        self.create_steps_list()

    def create_steps_list(self):
        steps_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        steps_container.pack(fill='both', expand=True, padx=10, pady=10)

        step_defs = [
            ("word_selected", "📄 Select Word File"),
            ("images_extracted", "🖼️ Extract Images"),
            ("docx_compressed", "📦 Compress Document"),
            ("html_converted", "🌐 Convert to HTML"),
            ("images_renamed", "🏷️ Rename Images"),
            ("upload_prepared", "📤 Prepare Archive"),
            ("uploaded", "✅ Upload Complete"),
        ]

        for key, label in step_defs:
            step_frame = ctk.CTkFrame(steps_container, height=40, corner_radius=8)
            step_frame.pack(fill='x', pady=3)
            step_frame.pack_propagate(False)

            var = ctk.BooleanVar(value=False)

            checkbox = ctk.CTkCheckBox(
                step_frame,
                text="",
                variable=var,
                state="disabled",
                width=20,
                height=20
            )
            checkbox.pack(side='left', padx=15)

            label_widget = ctk.CTkLabel(
                step_frame,
                text=label,
                font=ctk.CTkFont(size=12)
            )
            label_widget.pack(side='left', padx=(0, 10))

            self.steps[key] = {
                'var': var,
                'checkbox': checkbox,
                'label': label_widget,
                'frame': step_frame
            }

    def create_main_content(self):
        # Создаём правую часть (контент + консоль)
        self.right_frame = ctk.CTkFrame(self.main_frame, corner_radius=12)
        self.right_frame.pack(side='left', fill='both', expand=True, padx=(0, 15), pady=15)

        # Верхняя часть — динамическое содержимое
        self.dynamic_frame = ctk.CTkScrollableFrame(self.right_frame, corner_radius=8)
        self.dynamic_frame.pack(fill='both', expand=True, padx=20, pady=(20, 10))

        # Нижняя часть — консоль
        self.console_container = ctk.CTkFrame(self.right_frame, height=200, corner_radius=12)
        self.console_container.pack(fill='x', padx=20, pady=(0, 20))
        self.console_container.pack_propagate(False)

        console_header = ctk.CTkFrame(self.console_container, fg_color="transparent", height=40)
        console_header.pack(fill='x', padx=15, pady=5)
        console_header.pack_propagate(False)

        ctk.CTkLabel(
            console_header,
            text="📝 Console Output",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left')

        clear_btn = ctk.CTkButton(
            console_header,
            text="Clear",
            command=self.clear_console,
            width=60,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        clear_btn.pack(side='right')

        self.console_text = ctk.CTkTextbox(
            self.console_container,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
            fg_color="#1a1a1a",
            text_color="#00ff00"
        )
        self.console_text.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        self.console_text.insert("1.0", "🚀 Guide Uploader started...\n")
        self.console_text.insert("end", "=" * 50 + "\n")

    def create_console(self):
        console_container = ctk.CTkFrame(self.main_frame, height=200, corner_radius=12)
        console_container.pack(side='bottom', fill='x', pady=(15, 0))
        console_container.pack_propagate(False)

        console_header = ctk.CTkFrame(console_container, fg_color="transparent", height=40)
        console_header.pack(fill='x', padx=15, pady=5)
        console_header.pack_propagate(False)

        ctk.CTkLabel(
            console_header,
            text="📝 Console Output",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side='left')

        clear_btn = ctk.CTkButton(
            console_header,
            text="Clear",
            command=self.clear_console,
            width=60,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        clear_btn.pack(side='right')

        self.console_text = ctk.CTkTextbox(
            console_container,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
            fg_color="#1a1a1a",
            text_color="#00ff00"
        )
        self.console_text.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        self.console_text.insert("1.0", "🚀 Guide Uploader started...\n")
        self.console_text.insert("end", "=" * 50 + "\n")

    def clear_console(self):
        self.console_text.delete("1.0", "end")
        self.console_text.insert("1.0", "Console cleared\n")
        self.console_text.insert("end", "=" * 50 + "\n")

    def ask_level_selection(self, courses_data: Dict, on_selected: Callable[[int], None]):
        self.update_status(Status.SELECTING)
        self.clear_dynamic_frame()

        ctk.CTkLabel(
            self.dynamic_frame,
            text="Select Level",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))

        level_map = {}
        level_options = []

        for course in courses_data['courses']:
            for level in course['levels']:
                text = f"{course['course_title']} → {level['level_title']}"
                level_map[text] = level['level_id']
                level_options.append(text)

        self.level_combo = ctk.CTkComboBox(
            self.dynamic_frame,
            values=level_options,
            state="readonly",
            width=400,
            height=45,
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=13)
        )
        self.level_combo.pack(pady=10)
        self.level_combo.set("Choose level...")

        ctk.CTkButton(
            self.dynamic_frame,
            text="Confirm Selection",
            command=lambda: self.confirm_level_selection(level_map, on_selected),
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20)

    def confirm_level_selection(self, level_map, on_selected):
        selected = self.level_combo.get()
        if selected in level_map:
            level_id = level_map[selected]
            save_last_level(level_id)
            self.mark_step_done("level_selected")
            print(f"✅ Selected level: {selected} (ID: {level_id})")
            on_selected(level_id)
        else:
            messagebox.showwarning("Warning", "Please select a level from the list")

    def ask_order_selection(self, guides_data: Dict, level_id: int, on_selected: Callable[[int], None]):
        self.clear_dynamic_frame()

        ctk.CTkLabel(
            self.dynamic_frame,
            text=f"Guides in {guides_data['level_title']}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))

        guides_frame = ctk.CTkFrame(self.dynamic_frame)
        guides_frame.pack(fill='x', pady=(0, 20))

        textbox = ctk.CTkTextbox(guides_frame, height=150, font=ctk.CTkFont(size=12))
        textbox.pack(fill='x', padx=10, pady=10)

        for guide in guides_data['guides']:
            textbox.insert("end", f"#{guide['order']}: {guide['title']}\n")
        textbox.configure(state="disabled")

        input_frame = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        input_frame.pack(fill='x', pady=10)

        max_order = max([g['order'] for g in guides_data['guides']] or [0])
        next_order = load_next_order()

        ctk.CTkLabel(input_frame, text="Order number:", font=ctk.CTkFont(size=14)).pack(side='left')

        order_var = ctk.StringVar(value=str(next_order or max_order + 1))
        self.order_entry = ctk.CTkEntry(
            input_frame,
            textvariable=order_var,
            width=80,
            height=40,
            font=ctk.CTkFont(size=14),
            justify='center'
        )
        self.order_entry.pack(side='left', padx=10)

        ctk.CTkLabel(
            input_frame,
            text=f"Range: 1-{max_order + 1}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side='left')

        ctk.CTkButton(
            self.dynamic_frame,
            text="Start Upload",
            command=lambda: self.confirm_order_selection(level_id, on_selected, max_order),
            height=50,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838"
        ).pack(pady=20)

    def confirm_order_selection(self, level_id, on_selected, max_order):
        value = self.order_entry.get().strip()
        if value.isdigit():
            order = int(value)
            if 1 <= order <= max_order + 1:
                save_last_level(level_id, order)
                self.mark_step_done("order_selected")
                print(f"✅ Selected order: {order}")
                on_selected(order)
                return

        messagebox.showerror("Error", f"Enter number from 1 to {max_order + 1}")

    def clear_dynamic_frame(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

    def mark_step_done(self, step_key):
        if step_key in self.steps:
            self.steps[step_key]['var'].set(True)
            self.steps[step_key]['frame'].configure(fg_color="#1e3a28")
            self.steps[step_key]['label'].configure(
                text_color="#28a745",
                font=ctk.CTkFont(size=12, weight="bold")
            )

    def setup(self):
        self.clear_dynamic_frame()

        for step_data in self.steps.values():
            step_data['var'].set(False)
            step_data['frame'].configure(fg_color=["#3B8ED0", "#1F6AA5"])
            step_data['label'].configure(
                text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"],
                font=ctk.CTkFont(size=12)
            )

    def select_and_run(self):
        self.setup()
        self.run_button.configure(state="disabled")

        selected_server = self.base_url.get()
        selected_url = MODES[selected_server]
        constants.set_base_url(selected_url)

        print(f"🌍 Server: {selected_server} → {constants.BASE_URL}")

        thread = threading.Thread(target=mainAction, kwargs={"app": self})
        thread.daemon = True
        thread.start()

        self.root.after(2000, lambda: self.run_button.configure(state="normal"))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ModernGuideUploaderApp()
    app.run()