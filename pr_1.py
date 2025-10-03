# practice_1_part1
#Разработать эмулятор для языка оболочки ОС. Необходимо сделать работу
#эмулятора как можно более похожей на работу в командной строке UNIXподобной ОС.
#Этап 1. REPL
#Цель: создать минимальный прототип. Большинство функций в нем пока
#представляют собой заглушки, но диалог с пользователем уже поддерживается.

#Требования:
#1. Приложение должно быть реализовано в форме графического интерфейса
#(GUI).
#2. Заголовок окна должен формироваться на основе реальных данных ОС, в
#которой исполняется эмулятор. Пример: Эмулятор - [username@hostname].
#3. Реализовать простой парсер, который разделяет ввод на команду и
#аргументы по пробелам.
#4. Реализовать команды-заглушки, которые выводят свое имя и аргументы: ls, cd.
# 5. Реализовать команду exit.
# 6. Продемонстрировать работу прототипа в интерактивном режиме.
# Необходимо показать примеры работы всей реализованной
# функциональности, включая обработку ошибок.
# 7. Результат выполнения этапа сохранить в репозиторий стандартно
# оформленным коммитом.



import tkinter as tk # подкл библиотеки для GUI
from tkinter import ttk

import getpass # модуль чтобы узнать имя пользователя в системе
import socket # модуль чтобы узнать имя компьютера



# глобальные константы для приглашения
user = getpass.getuser()
host = socket.gethostname() 

class Terminal:
    def __init__(self, root): # конструктор, self ссылка на создаваемый объект
        self.root = root # сслыка на окно в атрибут объекта, чтобы из др методов иметь доступ
        root.title(f"Эмулятор - [{user}@{host}]")

        # многострочный вывод

        self.out = tk.Text(root, height = 14, width = 50, state = "disabled")
        # tk.Text многострочн поле, запрещено редактирование пользователем

        # размещение текста
        self.out.pack(padx=2, pady=2, fill = "both", expand= True)
        # fill растягивание -|, expand текст расширяется с окном


        # строка ввода

        self.inp = tk.Entry(root) # одностр поле ввода
        self.inp.pack(padx=2, pady=2, fill = "x", expand= True)

        self.inp.bind("<Return>", self.on_enter) # tk вызывает обработчик


        # регистрация команд, имя команды -> функция 
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }


        # приветствие 
        self.print_line("Возможные команды: ls, cd, exit")
        self.show_begin()





    # вспомогат методы

    # разбл текст, ввод, прокрут вниз, заблок
    def print_line(self, text = ""):
        self.out.configure(state = "normal")
        self.out.insert("end", text + "\n") # в конец
        self.out.see("end")
        self.out.configure(state = "disabled")



    def show_begin(self):
        self.print_line(user + "@" + host + ":$")
        self.inp.delete(0, "end") # каждая новая строка пустая
        self.inp.focus_set() # автоматич снос курсора
        
        
    # обработка нажатия пуск
    def on_enter(self, event = None):
        line = self.inp.get().strip() # взяли введ строку без пробелов
        if line:
            self.print_line(line)
        if not line:
            self.show_begin()
            return
        # разбить на команду и аргументы
        parts = line.split()
        cmd, arg = parts[0], parts[1:]

        if cmd in self.commands:
            output = self.commands[cmd](arg) # вызываем функцию команды
            if output: self.print_line(output) # если команда вернула строук
        else: self.print_line("{cmd}: command not found")


        self.show_begin()
            

    # заглушки
    def cmd_ls(self, arg):
        return "ls " + " ".join(arg)

    def cmd_cd(self, arg):
        return "cd " + " ".join(arg)
            
    def cmd_exit(self, arg):
        self.root.after(100, self.root.destroy)





def main():
    root = tk.Tk() # главное окно
    app = Terminal(root) # приложение экземпляр класса
    tk.mainloop() # главынй цикл окна

if __name__ == "__main__": 
    main()
