import tkinter as tk # подкл библиотеки для GUI
from tkinter import ttk

import getpass # модуль чтобы узнать имя пользователя в системе
import socket # модуль чтобы узнать имя компьютера

import argparse # для чтения аргументов команд строки
from pathlib import Path # для удобства с путями


# глобальные константы для приглашения
user = getpass.getuser()
host = socket.gethostname() 

class Terminal:
    def __init__(self, root, vfs_path: Path | None = None, script_path: Path | None = None): # конструктор сразу как создается терминал
        # root окно, ост 2 - пути от нас при запуске
        self.root = root # сслыка на окно в атрибут объекта, чтобы из др методов иметь доступ
        self.root.title(f"Эмулятор - [{user}@{host}]")

        self.vfs_path: Path | None = vfs_path # запоминаем что передали при запуске
        self.script_path: Path | None = script_path



        # многострочный вывод
        self.out = tk.Text(root, height = 14, width = 50, state = "disabled")
        # tk.Text многострочн поле, запрещено редактирование пользователем

        # размещение текста
        self.out.pack(padx=2, pady=2, fill = "both", expand= True)
        # fill растягивание -|, expand текст расширяется с окном



        # строка ввода
        self.inp = tk.Entry(root) # одностр поле ввода
        self.inp.pack(padx=2, pady=2, fill = "x", expand= True)

        self.inp.bind("<Return>", self.on_enter) # tk вызывает метод при нажатии


        # регистрация команд, имя команды -> функция 
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }


        # отладочный вывод параметров запуска
        self.print_line("параметры запуска")
        self.print_line(f"VFS: {self.vfs_path if self.vfs_path else 'не задано'}")
        self.print_line(f"script: {self.script_path if self.script_path else 'не задано'}")

        # проверка существования путей
        if self.vfs_path and not self.vfs_path.exists():
            self.print_line(f"путь VFS не найден: {self.vfs_path}")
        if self.script_path and not self.script_path.exists():
            self.print_line(f"скрипт не найден: {self.script_path}")



        # приветствие 
        self.print_line("Возможные команды: ls, cd, exit")
        self.show_begin()


        # автоматич запуск скрипта если задан
        if self.script_path and self.script_path.exists():
            self.root.after(0, self.run_start_script)




    # вспомогат методы

    # вывод строки
    # разбл текст, ввод, прокрут вниз, заблок
    def print_line(self, text = ""):
        self.out.configure(state = "normal")
        self.out.insert("end", text + "\n") # в конец
        self.out.see("end")
        self.out.configure(state = "disabled")


    # приглашение
    def show_begin(self):
        self.print_line(f"{user}@{host}:$")
        self.inp.delete(0, "end") # каждая новая строка пустая
        self.inp.focus_set() # автоматич снос курсора
        


    # выполнение одной строки
    def exec_line(self, line: str, show: bool) -> bool: # нужно ли показываьтт команду
        line = line.strip() # - лишние пробелы
        if not line:
            if show:
                self.print_line("")
            return True # пустая строка не ошибка

        if show:
            self.print_line(f"{user}@{host}:$ {line}") # вывод имя устр-в и команду

        parts = line.split() # без пробелов
        cmd, arg = parts[0], parts[1:]

        if cmd in self.commands:
            ok, output = self.commands[cmd](arg)
            if output:
                self.print_line(output)
            return ok
        else:
            self.print_line(f"{cmd}: command not found")
            return False




    # обработка нажатия пуск
    def on_enter(self, event = None):
        line = self.inp.get()
        self.print_line(f"{user}@{host}:$ {line}")
        self.exec_line(line, show=False)
        self.show_begin()


            

    # заглушки
    def cmd_ls(self, arg):
    
        text = "команда ls вызвана"
        if arg:
            text += " с аргументами: " + " ".join(arg)
        return True, text

    def cmd_cd(self, arg):
        if not arg:
            return True, "команда cd: путь не указан"
        else:
            return True, f"команда cd: перешёл в {arg[0]}"

    def cmd_exit(self, arg):
        self.root.after(100, self.root.destroy)
        return True, "конец работы"
    



    # запуск скрипта
    def run_start_script(self):
        try:
            with self.script_path.open("r", encoding="utf-8") as f: # открыть и закрыть файл
                for raw in f: # построчно
                    line = raw.strip()
                    if not line or line.startswith("#"): # пропуск комментариев
                        continue
                    ok = self.exec_line(line, show=True)
                    if not ok:
                        self.print_line(f"скрипт остановлен на команде: {line}")
                        break
        except Exception as e:
            self.print_line(f"не удалось открыть файл: {e}")




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vfs", type=Path, nargs="?", help="путь к физическому расположению VFS")
    # имя аргумента, строка в путьт, обязательный ли аргумент, текст подсказка
    parser.add_argument("script", type=Path, nargs="?", help="путь к стартовому скрипту эмулятора")
    args = parser.parse_args() # чтение аргументов терминала


    root = tk.Tk() # главное окно
    app = Terminal(root, vfs_path=args.vfs, script_path=args.script) # приложение экземпляр класса
    root.mainloop() # главынй цикл окна

if __name__ == "__main__": 
    main()
