"""Графический интерфейс эмулятора на tkinter."""

import tkinter as tk
from tkinter import scrolledtext

from emulator.errors import ExitRequest

FONT = ("Consolas", 11)
BACKGROUND = "#1e1e1e"
FOREGROUND = "#d4d4d4"
ERROR_COLOR = "#f48771"
PROMPT_COLOR = "#6a9955"
ERROR_PREFIX = "error:"


class EmulatorApp:
    """Окно эмулятора: область вывода и строка ввода с приглашением."""

    def __init__(self, shell, root=None):
        """Создаёт окно и перенаправляет вывод оболочки в него."""
        self.shell = shell
        self.root = root if root is not None else tk.Tk()
        self.exit_code = 0
        self.history, self.history_pos = [], 0
        self.root.title(shell.title())
        self.root.geometry("820x520")
        self._build_widgets()
        shell.output = self.write

    def _build_widgets(self):
        """Создаёт виджеты окна."""
        self.text = scrolledtext.ScrolledText(
            self.root, state="disabled", font=FONT, wrap="word",
            bg=BACKGROUND, fg=FOREGROUND, insertbackground=FOREGROUND)
        self.text.tag_configure("error", foreground=ERROR_COLOR)
        self.text.tag_configure("prompt", foreground=PROMPT_COLOR)
        self.text.pack(fill="both", expand=True)
        bar = tk.Frame(self.root, bg=BACKGROUND)
        bar.pack(fill="x")
        self.prompt_label = tk.Label(
            bar, text=self.shell.prompt(), font=FONT,
            bg=BACKGROUND, fg=PROMPT_COLOR)
        self.prompt_label.pack(side="left")
        self.entry = tk.Entry(
            bar, font=FONT, bg=BACKGROUND, fg=FOREGROUND,
            insertbackground=FOREGROUND, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", lambda _event: self._browse(-1))
        self.entry.bind("<Down>", lambda _event: self._browse(1))
        self.entry.focus_set()

    def write(self, text="", tag=None):
        """Добавляет строку в область вывода."""
        if tag is None and str(text).startswith(ERROR_PREFIX):
            tag = "error"
        self.text.configure(state="normal")
        self.text.insert("end", f"{text}\n", tag)
        self.text.configure(state="disabled")
        self.text.see("end")

    def submit(self, line):
        """Отображает ввод как диалог и выполняет команду."""
        self.write(self.shell.prompt() + line, "prompt")
        try:
            self.shell.run_line(line)
        except ExitRequest as request:
            self.close(request.code)
            return
        self.prompt_label.configure(text=self.shell.prompt())

    def on_enter(self, _event=None):
        """Обработчик нажатия Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        if line.strip():
            self.history.append(line)
        self.history_pos = len(self.history)
        self.submit(line)
        return "break"

    def _browse(self, step):
        """Листает историю команд стрелками вверх/вниз."""
        if not self.history:
            return "break"
        last = len(self.history) - 1
        self.history_pos = max(0, min(last, self.history_pos + step))
        self.entry.delete(0, "end")
        self.entry.insert(0, self.history[self.history_pos])
        return "break"

    def close(self, code=0):
        """Закрывает окно с кодом возврата code."""
        self.exit_code = code
        self.root.destroy()

    def run(self):
        """Запускает главный цикл окна и возвращает код выхода."""
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()
        return self.exit_code
