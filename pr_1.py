import tkinter as tk # подкл библиотеки для GUI
from tkinter import ttk

import getpass # модуль чтобы узнать имя пользователя в системе
import socket # модуль чтобы узнать имя компьютера

import argparse # для чтения аргументов команд строки
from pathlib import Path # для удобства с путями

import csv # таблицы
import base64 
import hashlib # для SHA-256
from pathlib import PurePosixPath # для аккуратного склеиваня путей внутри vfs

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


        # структура для хранения vfs
        self.vfs = {} # путь - описание 
        self.vfs_sha = None
        self.cwd = PurePosixPath("/") # текущая директория 

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
            "vfs-info": self.cmd_vfs_info,
            "echo": self.cmd_echo,
            "rev": self.cmd_rev
        }


        # отладочный вывод параметров запуска
        self.print_line("параметры запуска")
        self.print_line(f"VFS: {self.vfs_path if self.vfs_path else 'не задано'}")
        self.print_line(f"script: {self.script_path if self.script_path else 'не задано'}")

        # проверка существования путей
        if self.vfs_path and not self.vfs_path.exists():
            self.print_line(f"путь vfs не найден: {self.vfs_path}")
        if self.script_path and not self.script_path.exists():
            self.print_line(f"скрипт не найден: {self.script_path}")

        # загружаеме пути в памяь
        if self.vfs_path:
            ok = self.load_vfs(self.vfs_path)
            if ok:
                self.print_line(f"загружено: {self.vfs_path.name}")
            else:
                self.print_line("загрузка не удалась")



        # приветствие 
        self.print_line("возможные команды: ls, cd, exit, vfs-info")
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


            
    # команда ls показать содержимое папки
    def cmd_ls(self, arg):
        # без арг содержимое тек папки
        # пуь на файл имя и размер
        # путь на папку непоср дети

        # арг или тек папка
        target = arg[0] if arg else "."

        ap = str(self._abs_path(target))

        node = self.vfs.get(ap)
        if not node:
            return False, f"ls: нет такого пути: {ap}"

        # файл
        if node["type"] == "file":
            name = PurePosixPath(ap).name
            size = len(node["content"])
            return True, f"{name}\t{size} B"

        # папка
        prefix = "" if ap == "/" else ap
        items = []
        for path, meta in self.vfs.items():
            if path == ap:
                continue
            if path.startswith(prefix + "/"):
                tail = path[len(prefix) + 1:] 
                if "/" not in tail:           # только прямые дети
                    items.append(tail + ("/" if meta["type"] == "dir" else ""))

        items.sort()
        return True, ("\n".join(items) if items else "(пусто)")




    # команда cd перейти в др дир
    def cmd_cd(self, arg):
        # без арг домой
        if not arg:
            self.cwd = PurePosixPath("/")
            return True, "cd: /"

        ap = self._abs_path(arg[0])
        meta = self.vfs.get(str(ap))

        if not meta:
            return False, f"cd: нет такого пути: {ap}"
        if meta["type"] != "dir":
            return False, f"cd: не папка: {ap}"

        self.cwd = ap
        return True, f"cd: {ap}"

        
    # команда exit
    def cmd_exit(self, arg):
        self.root.after(100, self.root.destroy)
        return True, "конец работы"
    
    # команда echo простой вывод что передано
    def cmd_echo(self, arg):
        return True, " ".join(arg)
        
    # команда rev переворот строки
    def cmd_rev(self, arg):
        if not arg:
            return True, ""
        return True, " ".join(word[::-1] for word in arg)


    # реализация команды vfs -info
    def cmd_vfs_info(self, arg):
        if not self.vfs_sha or not self.vfs_path:
            return True, "vfs не загружен"
        # сколько узлов, сколько файлов/папок
        total = len(self.vfs)
        files = sum(1 for v in self.vfs.values() if v["type"] == "file")
        dirs  = sum(1 for v in self.vfs.values() if v["type"] == "dir")
        info = [
            f"VFS файл: {self.vfs_path}",
            f"SHA-256: {self.vfs_sha}",
            f"Объектов: {total} (файлов: {files}, папок: {dirs})",
        ]
        return True, "\n".join(info)



    # нормализация путей vfs
    def _abs_path(self, raw: str) -> PurePosixPath: #(в стиле позикс с /)
        p = PurePosixPath(raw)
        if not p.is_absolute():      # относительный, абсолютный путь с  /
            p = self.cwd / p        # приклеили к тек директории
        s = "/" + str(p).lstrip("/") # все ведущ / удаляем и один доб в нач
        return PurePosixPath(s)



    # чтение vfs из csv
    def load_vfs(self, csv_path: Path) -> bool:
        # сброс предсостояния
        self.vfs.clear()
        self.vfs_sha = None
        self.cwd = PurePosixPath("/")

        # читаем как байты
        try:
            raw = csv_path.read_bytes()
        except FileNotFoundError:
            self.print_line(f"vfs файл не найден: {csv_path}")
            return False
        except Exception as e:
            self.print_line(f"не удалось прочитать vfs: {e}")
            return False
        # счет sha по байтам
        self.vfs_sha = hashlib.sha256(raw).hexdigest()


        # декодируем в текст
        text = raw.decode("utf-8")

        # разбор csv в словари
        reader = csv.DictReader(text.splitlines()) # каждая строка в солварь
        need = {"type", "path", "info"} # обязатеьные колонки
        if not need.issubset(set(reader.fieldnames or [])): # все ли эл-ты внутри имен
            self.print_line(f"не тот формат csv")
            return False

        try:
            for i, row in enumerate(reader, start = 2):  # 1 строка заголовок
                t = (row.get("type") or "").strip().lower()
                p = (row.get("path") or "").strip()
                inf = row.get("info") or ""

                if t not in {"dir", "file"} or not p:
                    self.print_line(f"пустой path/type / неизвестный тип='{t}'")
                    return False

                # абсолютный позикс
                ap = str(self._abs_path(p))

                if t == "dir":
                    self.vfs[ap] = {"type": "dir"}
                else:
                    # base64 / обычный текст, в self.vfs всегда биты
                    try:
                        data = base64.b64decode(inf, validate=True)  # если base64 декодируем
                        
                    except Exception:
                        data = inf.encode("utf-8", errors="replace")
                    self.vfs[ap] = {"type": "file", "content": data}

            # корень / как папка
            self.vfs.setdefault("/", {"type": "dir"})

            return True
        
        except Exception as e:
            self.print_line(f"ошибка csv: {e}")
            return False




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
