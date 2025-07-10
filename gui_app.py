import tkinter as tk
from tkinter import ttk

import constants
from main import main

MODES = {
    "DEBUG": constants.DEBUG_SERVER,
    "TEST": constants.TEST_SERVER,
    "PROD": constants.PROD_SERVER
}


class GuideUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Загрузка методички")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        self.base_url = tk.StringVar(value="DEBUG")

        self.create_widgets()

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

        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=10)

        self.log_text = tk.Text(frame, height=15, state='disabled', wrap='word', bg="#f7f7f7")
        self.log_text.pack(fill='both', expand=True)

    def select_and_run(self):
        selected_label = self.base_url.get()
        selected_url = MODES[selected_label]
        constants.set_base_url(selected_url)

        print(f"🌍 Сервер: {selected_label} → {constants.BASE_URL}")

        main()

    def log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.see('end')
        self.log_text.configure(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = GuideUploaderApp(root)
    root.mainloop()
