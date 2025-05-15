# Обновленный модуль с современным графическим интерфейсом для анализатора банковских рисков
# Стильный дизайн с темной темой, иконками и улучшенными визуальными эффектами
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import io
from pathlib import Path
import os
import json
import re
import platform

# Пытаемся импортировать дополнительные пакеты для улучшения интерфейса
try:
    from ttkthemes import ThemedTk
    THEMED_TK_AVAILABLE = True
except ImportError:
    THEMED_TK_AVAILABLE = False
    print("Для улучшенного интерфейса установите ttkthemes: pip install ttkthemes")

# Пытаемся импортировать PIL для работы с изображениями
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Для отображения иконок установите Pillow: pip install Pillow")

# Импортируем функциональность из нашего основного модуля
try:
    # Пытаемся импортировать основные компоненты из основного модуля
    from bank_analyzer import (
        VspDataTool, run_vsp_data_workflow, USE_MOCK_LLM
    )
except ImportError:
    # Если модуль не найден, выводим сообщение об ошибке и создаем заглушки для тестирования
    print("Не удалось импортировать модуль bank_analyzer.py.")
    print("Создаем заглушки для тестирования интерфейса.")
    
    # Заглушка для демонстрации интерфейса
    USE_MOCK_LLM = True
    
    class VspDataTool:
        def __init__(self, data_dir="data"):
            self.companies = [
                {"id": 1, "name": "ВСП_1", "address": "ул. Тестовая, 1"},
                {"id": 2, "name": "ВСП_2", "address": "пр. Примерный, 2"},
                {"id": 3, "name": "ВСП_3", "address": "ул. Новый Арбат, 15"},
                {"id": 4, "name": "ВСП_4", "address": "ул. Покровка, 33"},
                {"id": 5, "name": "ВСП_5", "address": "ул. Ленинская Слобода, 19"}
            ]
            
        def get_all_companies(self):
            return self.companies
            
        def get_vsp_by_name_or_address(self, search_term):
            return [company for company in self.companies 
                   if search_term.lower() in company["name"].lower() 
                   or search_term.lower() in company["address"].lower()]
    
    def run_vsp_data_workflow(vsp_name):
        # Заглушка для функции анализа с имитацией задержки
        import time
        import random
        # Имитируем время выполнения анализа
        time.sleep(2)
        
        # Генерируем разные типы рисков для демонстрации
        risk_levels = ["Низкий", "Средний", "Высокий"]
        operational_risk = random.choice(risk_levels)
        reputation_risk = random.choice(risk_levels)
        tech_risk = random.choice(risk_levels)
        
        print(f"Анализ отделения {vsp_name} завершен")
        print(f"Обнаружены риски: операционные - {operational_risk}, репутационные - {reputation_risk}")
        
        return {
            "vsp_name": vsp_name,
            "vsp_info": {"address": "Тестовый адрес", "id": 1},
            "vsp_reviews": [{"rate": 5}, {"rate": 3}, {"rate": 4}, {"rate": 2}, {"rate": 5}],
            "final_report": f"# Отчет о рисках отделения {vsp_name}\n\n"
                           f"## Резюме\n"
                           f"На основе анализа данных отделения и отзывов клиентов выявлены следующие категории рисков:\n\n"
                           f"- Операционные риски: **{operational_risk.lower()}**\n"
                           f"- Репутационные риски: **{reputation_risk.lower()}**\n"
                           f"- Технические риски: **{tech_risk.lower()}**\n\n"
                           f"## Детализация рисков\n\n"
                           f"### 1. Операционные риски\n"
                           f"* Очереди в часы пик\n"
                           f"* Недостаточное количество операционистов\n"
                           f"* Сбои в работе банкоматов\n\n"
                           f"### 2. Репутационные риски\n"
                           f"* Негативные отзывы о качестве обслуживания\n"
                           f"* Жалобы на компетентность персонала\n\n"
                           f"### 3. Технические риски\n"
                           f"* Устаревшее оборудование\n"
                           f"* Периодические сбои в системе\n\n"
                           f"## Рекомендации\n\n"
                           f"1. **Улучшение системы обслуживания клиентов**\n"
                           f"   - Внедрить систему предварительной записи\n"
                           f"   - Увеличить количество операционистов в часы пик\n"
                           f"   - Срок: 1 месяц\n\n"
                           f"2. **Обучение персонала**\n"
                           f"   - Провести тренинги по работе с клиентами\n"
                           f"   - Обучить сотрудников новым продуктам\n"
                           f"   - Срок: 2 недели\n\n"
                           f"3. **Модернизация оборудования**\n"
                           f"   - Обновить программное обеспечение\n"
                           f"   - Установить дополнительные банкоматы\n"
                           f"   - Срок: 3 месяца\n\n"
                           f"## Приоритеты действий\n\n"
                           f"1. Срочное обучение персонала (2 недели)\n"
                           f"2. Оптимизация процесса обслуживания (1 месяц)\n"
                           f"3. Обновление технической инфраструктуры (3 месяца)\n\n"
                           f"## Критические риски\n\n"
                           f"В ходе анализа критических рисков не выявлено.\n\n"
        }

# Создаем экземпляр инструмента для работы с данными
vsp_data_tool = VspDataTool()

# Определяем цветовую схему и стили
DARK_THEME = {
    "bg": "#2E3440",         # Фон
    "fg": "#ECEFF4",         # Основной текст
    "accent": "#88C0D0",     # Акцентный цвет
    "accent_dark": "#5E81AC", # Темный акцент
    "warning": "#EBCB8B",    # Предупреждения
    "error": "#BF616A",      # Ошибки
    "success": "#A3BE8C",    # Успех
    "panel": "#3B4252",      # Панели и рамки
    "highlight": "#434C5E",  # Выделение
    "text_dark": "#D8DEE9",  # Вторичный текст
    "text_disabled": "#4C566A" # Неактивный текст
}

class RedirectOutput:
    """Класс для перенаправления стандартного вывода в виджет Text"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = io.StringIO()
    
    def write(self, string):
        self.buffer.write(string)
        # Обновляем виджет в безопасном режиме для потоков
        self.text_widget.after(0, self.update_text_widget)
    
    def update_text_widget(self):
        text = self.buffer.getvalue()
        if text:
            # Добавляем цветовую маркировку для разных типов сообщений
            for line in text.splitlines():
                if "ошибка" in line.lower() or "error" in line.lower():
                    self.text_widget.insert(tk.END, line + "\n", "error")
                elif "предупреждение" in line.lower() or "warning" in line.lower():
                    self.text_widget.insert(tk.END, line + "\n", "warning")
                elif "успех" in line.lower() or "завершен" in line.lower():
                    self.text_widget.insert(tk.END, line + "\n", "success")
                else:
                    self.text_widget.insert(tk.END, line + "\n", "normal")
            
            self.text_widget.see(tk.END)  # Прокрутка к концу текста
            self.buffer = io.StringIO()  # Очищаем буфер
    
    def flush(self):
        pass

class ModernUI:
    """Класс для создания современных UI-элементов на основе ttk"""
    
    @staticmethod
    def create_styled_button(parent, text, command, width=None, icon=None, **kwargs):
        """Создает стилизованный кнопку с иконкой"""
        button_frame = ttk.Frame(parent)
        
        # Создаем кнопку
        button = ttk.Button(button_frame, text=text, command=command, width=width, **kwargs)
        
        # Если есть иконка и доступен PIL, добавляем ее
        if icon and PIL_AVAILABLE:
            try:
                # Получаем путь к папке с иконками
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", f"{icon}.png")
                
                # Если файл иконки существует, добавляем ее на кнопку
                if os.path.exists(icon_path):
                    img = Image.open(icon_path)
                    img = img.resize((16, 16), Image.LANCZOS)
                    icon_img = ImageTk.PhotoImage(img)
                    
                    # Сохраняем ссылку на изображение, чтобы сборщик мусора не удалил его
                    button.image = icon_img
                    button.configure(image=icon_img, compound=tk.LEFT)
            except Exception as e:
                print(f"Ошибка загрузки иконки {icon}: {e}")
        
        button.pack(fill=tk.BOTH, expand=True)
        return button_frame
    
    @staticmethod
    def create_search_entry(parent, command=None):
        """Создает современное поле поиска с кнопкой"""
        frame = ttk.Frame(parent)
        
        # Создаем поле ввода
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Добавляем кнопку поиска
        search_button = ttk.Button(frame, text="🔍", width=3)
        if command:
            search_button.configure(command=lambda: command(entry.get()))
        search_button.pack(side=tk.LEFT, padx=(2, 0))
        
        # Привязываем Enter к функции поиска
        if command:
            entry.bind("<Return>", lambda event: command(entry.get()))
        
        # Создаем метод для доступа к значению поля
        frame.get = entry.get
        
        # Метод для установки значения
        def set_value(value):
            entry.delete(0, tk.END)
            entry.insert(0, value)
        frame.set = set_value
        
        return frame

    @staticmethod
    def apply_markdown_formatting(text_widget):
        """Применяет форматирование Markdown к тексту в виджете"""
        # Получаем весь текст
        content = text_widget.get(1.0, tk.END)
        
        # Очищаем все существующие теги
        for tag in text_widget.tag_names():
            if tag != "sel":  # Не трогаем тег выделения
                text_widget.tag_remove(tag, "1.0", tk.END)
        
        # Применяем форматирование для заголовков
        header_patterns = [
            (r"^# (.+)$", "h1"),
            (r"^## (.+)$", "h2"),
            (r"^### (.+)$", "h3"),
        ]
        
        for pattern, tag in header_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                text_widget.tag_add(tag, start_idx, end_idx)
        
        # Форматирование для жирного текста
        bold_matches = re.finditer(r"\*\*(.+?)\*\*", content)
        for match in bold_matches:
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            text_widget.tag_add("bold", start_idx, end_idx)
        
        # Форматирование для курсива
        italic_matches = re.finditer(r"\*(.+?)\*", content)
        for match in italic_matches:
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            text_widget.tag_add("italic", start_idx, end_idx)
        
        # Форматирование для маркированных списков
        bullet_matches = re.finditer(r"^(\s*)[*\-+] (.+)$", content, re.MULTILINE)
        for match in bullet_matches:
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            text_widget.tag_add("bullet", start_idx, end_idx)
        
        # Форматирование для нумерованных списков
        number_matches = re.finditer(r"^(\s*)\d+\. (.+)$", content, re.MULTILINE)
        for match in number_matches:
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            text_widget.tag_add("number", start_idx, end_idx)

class LoadingIndicator:
    """Класс для отображения анимированного индикатора загрузки"""
    def __init__(self, parent, message="Загрузка..."):
        self.parent = parent
        self.message = message
        self.frame = None
        self.animation_id = None
        self.dots = 0
        
    def show(self):
        """Показывает индикатор загрузки"""
        if self.frame:
            return
        
        self.frame = ttk.Frame(self.parent)
        self.frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Добавляем текст с сообщением
        self.label = ttk.Label(self.frame, text=self.message)
        self.label.pack(padx=20, pady=20)
        
        # Запускаем анимацию
        self.animate()
    
    def animate(self):
        """Анимирует индикатор загрузки"""
        if not self.frame:
            return
        
        self.dots = (self.dots + 1) % 4
        self.label.configure(text=f"{self.message}{'.' * self.dots}")
        
        # Планируем следующую анимацию
        self.animation_id = self.parent.after(300, self.animate)
    
    def hide(self):
        """Скрывает индикатор загрузки"""
        if not self.frame:
            return
        
        if self.animation_id:
            self.parent.after_cancel(self.animation_id)
            self.animation_id = None
        
        self.frame.destroy()
        self.frame = None

class BankAnalyzerApp:
    """Современный интерфейс приложения для анализа банковских рисков"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор банковских рисков")
        self.root.geometry("1000x750")  # Увеличенное окно для более комфортной работы
        
        # Настройка иконки приложения, если доступен PIL
        if PIL_AVAILABLE:
            try:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "app_icon.png")
                if os.path.exists(icon_path):
                    if platform.system() == "Windows":
                        self.root.iconbitmap(icon_path.replace(".png", ".ico"))
                    else:  # Для Linux и macOS
                        icon = ImageTk.PhotoImage(file=icon_path)
                        self.root.iconphoto(True, icon)
            except Exception as e:
                print(f"Не удалось установить иконку приложения: {e}")
        
        # Создаем и настраиваем стили
        self.setup_styles()
        
        # Настройка пользовательского интерфейса
        self.setup_ui()
        
        # Создаем индикатор загрузки
        self.loading_indicator = LoadingIndicator(self.root)
        
        # Заполняем combobox при запуске
        self.root.after(100, self.load_vsps)
    
    def setup_styles(self):
        """Настройка стилей для элементов интерфейса"""
        style = ttk.Style()
        
        # Настраиваем стиль кнопок
        style.configure("Accent.TButton", 
                        background=DARK_THEME["accent"],
                        foreground=DARK_THEME["bg"])
        
        style.map("Accent.TButton",
                 background=[("active", DARK_THEME["accent_dark"])],
                 foreground=[("active", DARK_THEME["fg"])])
        
        # Стиль для кнопок действий
        style.configure("Action.TButton", 
                        font=("Segoe UI", 10, "bold"))
        
        # Стиль для заголовков
        style.configure("Header.TLabel", 
                        font=("Segoe UI", 14, "bold"),
                        foreground=DARK_THEME["accent"])
        
        # Стиль для подзаголовков
        style.configure("Subheader.TLabel", 
                        font=("Segoe UI", 12),
                        foreground=DARK_THEME["text_dark"])
        
        # Стиль для рамок
        style.configure("Card.TFrame", 
                        background=DARK_THEME["panel"],
                        relief=tk.RAISED)
    
    def setup_ui(self):
        """Настройка современного пользовательского интерфейса"""
        # Основной frame с отступами
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок приложения
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="Анализатор банковских рисков", 
                 style="Header.TLabel").pack(side=tk.LEFT)
        
        # Кнопка для запуска демо-режима
        demo_button = ModernUI.create_styled_button(
            header_frame, "Демо режим", self.run_demo, 
            icon="play", style="Accent.TButton"
        )
        demo_button.pack(side=tk.RIGHT)
        
        # Верхняя панель - поиск и выбор отделения
        search_card = ttk.LabelFrame(main_frame, text="Поиск и выбор отделения", padding="10")
        search_card.pack(fill=tk.X, padx=5, pady=5)
        
        # Верхний ряд - поиск
        search_row = ttk.Frame(search_card)
        search_row.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_row, text="Поиск:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Создаем поле поиска с кнопкой
        self.search_entry = ModernUI.create_search_entry(search_row, self.search_vsps)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Второй ряд - выбор отделения и кнопка анализа
        select_row = ttk.Frame(search_card)
        select_row.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_row, text="Отделение:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Выпадающий список с отделениями - улучшенный стиль
        self.vsp_combobox = ttk.Combobox(select_row, width=50, state="readonly")
        self.vsp_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Кнопка анализа с иконкой
        analyze_button = ModernUI.create_styled_button(
            select_row, "Анализировать", self.analyze_vsp, 
            icon="analyze", style="Accent.TButton"
        )
        analyze_button.pack(side=tk.RIGHT)
        
        # Создаем вкладки для вывода - с улучшенным стилем
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        # Вкладка для отображения отчета
        self.report_tab = ttk.Frame(tab_control)
        tab_control.add(self.report_tab, text="Отчет")
        
        # Вкладка для отображения логов
        self.log_tab = ttk.Frame(tab_control)
        tab_control.add(self.log_tab, text="Логи")
        
        # Настраиваем вкладку отчета
        self.setup_report_tab()
        
        # Настраиваем вкладку логов
        self.setup_log_tab()
        
        # Статусная строка в современном стиле
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, padding=(5, 2))
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Добавляем индикатор прогресса, скрытый по умолчанию
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=100)
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.pack_forget()  # Скрываем до нужного момента
        
        # Перенаправляем стандартный вывод в текстовое поле логов
        self.redirect = RedirectOutput(self.log_text)
        sys.stdout = self.redirect
    
    def setup_report_tab(self):
        """Настройка вкладки отчета"""
        report_frame = ttk.Frame(self.report_tab, padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем заголовок
        header_frame = ttk.Frame(report_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.report_title = ttk.Label(header_frame, text="Отчет о рисках", style="Header.TLabel")
        self.report_title.pack(side=tk.LEFT)
        
        # Добавляем кнопки для экспорта отчета
        export_button = ModernUI.create_styled_button(
            header_frame, "Экспорт в PDF", self.export_report, 
            icon="export", width=15
        )
        export_button.pack(side=tk.RIGHT, padx=5)
        
        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text, 1)
    
    def redirect_output(self):
        """Перенаправление стандартного вывода в текстовое поле логов"""
        self.redirector = OutputRedirector(self.log_text)
        sys.stdout = self.redirector
        print("Приложение запущено. Готово к работе.")
    
    def load_vsps(self):
        """Загрузка списка отделений"""
        try:
            companies = vsp_data_tool.get_all_companies()
            self.vsp_combo.clear()
            
            # Добавляем отделения в комбобокс
            for company in companies:
                self.vsp_combo.addItem(f"{company['name']} - {company['address']}", company)
            
            print(f"Загружено {len(companies)} отделений")
            self.statusbar.showMessage(f"Загружено {len(companies)} отделений")
        except Exception as e:
            print(f"Ошибка при загрузке списка отделений: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список отделений: {e}")
    
    def search_vsps(self):
        """Поиск отделений по названию или адресу"""
        search_term = self.search_edit.text().strip()
        if not search_term:
            QMessageBox.information(self, "Информация", "Введите название или адрес отделения для поиска")
            return
        
        try:
            # Показываем индикатор загрузки
            self.start_progress("Поиск отделений...")
            
            matching_vsps = vsp_data_tool.get_vsp_by_name_or_address(search_term)
            self.vsp_combo.clear()
            
            if matching_vsps:
                # Добавляем найденные отделения в комбобокс
                for company in matching_vsps:
                    self.vsp_combo.addItem(f"{company['name']} - {company['address']}", company)
                
                print(f"Найдено {len(matching_vsps)} отделений по запросу '{search_term}'")
                self.statusbar.showMessage(f"Найдено {len(matching_vsps)} отделений")
                
                # Анимация подсветки комбобокса
                self.highlight_combobox()
            else:
                print(f"Не найдено отделений по запросу '{search_term}'")
                self.statusbar.showMessage("Отделения не найдены")
                QMessageBox.information(self, "Результаты поиска", f"Не найдено отделений по запросу '{search_term}'")
                
                # Загружаем обратно все отделения
                self.load_vsps()
            
            self.stop_progress()
        except Exception as e:
            self.stop_progress()
            print(f"Ошибка при поиске отделений: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске отделений: {e}")
    
    def highlight_combobox(self):
        """Анимация для привлечения внимания к combobox"""
        original_style = self.vsp_combo.styleSheet()
        
        # Устанавливаем подсветку
        self.vsp_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid """ + MATERIAL_COLORS["secondary"] + """;
                background-color: """ + MATERIAL_COLORS["secondary_light"] + """;
            }
        """)
        
        # Возвращаем обратно через 1 секунду
        QTimer.singleShot(1000, lambda: self.vsp_combo.setStyleSheet(original_style))
    
    def analyze_vsp(self):
        """Анализ выбранного отделения"""
        if self.vsp_combo.count() == 0:
            QMessageBox.information(self, "Информация", "Нет доступных отделений для анализа")
            return
        
        selected_index = self.vsp_combo.currentIndex()
        if selected_index < 0:
            QMessageBox.information(self, "Информация", "Выберите отделение для анализа")
            return
        
        # Получаем данные выбранного отделения
        selected_item = self.vsp_combo.currentText()
        vsp_name = selected_item.split(" - ")[0]
        
        # Показываем сообщение о запуске анализа
        if WEB_VIEW_AVAILABLE:
            self.report_view.setHtml(f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; text-align: center; }}
                        .loader {{ 
                            border: 16px solid #f3f3f3;
                            border-top: 16px solid {MATERIAL_COLORS["primary"]};
                            border-radius: 50%;
                            width: 120px;
                            height: 120px;
                            animation: spin 2s linear infinite;
                            margin: 30px auto;
                        }}
                        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                    </style>
                </head>
                <body>
                    <h2>Выполняется анализ отделения {vsp_name}</h2>
                    <p>Пожалуйста, подождите. Это может занять некоторое время...</p>
                    <div class="loader"></div>
                </body>
                </html>
            """)
        else:
            self.report_text.clear()
            self.report_text.append(f"Выполняется анализ отделения {vsp_name}...\nПожалуйста, подождите.")
        
        # Переключаемся на вкладку отчета
        self.tab_widget.setCurrentIndex(0)
        
        # Запускаем анализ в отдельном потоке
        self.start_progress(f"Анализ отделения {vsp_name}...")
        
        # Создаем и запускаем поток
        self.worker = AnalysisWorker(vsp_name)
        self.worker.finished.connect(self.update_report)
        self.worker.error.connect(self.handle_analysis_error)
        self.worker.start()
    
    def update_report(self, result):
        """Обновление отчета после завершения анализа"""
        vsp_name = result.get("vsp_name", "")
        
        # Обновляем заголовок
        self.report_title.setText(f"Отчет о рисках: {vsp_name}")
        
        # Обновляем отчет
        report_content = result.get("final_report", "Отчет не сгенерирован")
        
        if WEB_VIEW_AVAILABLE:
            # Преобразуем Markdown в HTML для WebView
            try:
                import markdown
                html_content = markdown.markdown(report_content)
                
                # Оборачиваем в HTML с CSS стилями
                styled_html = f"""
                <html>
                <head>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            margin: 20px;
                            color: {MATERIAL_COLORS["text_primary"]};
                            line-height: 1.5;
                        }}
                        h1, h2, h3, h4, h5, h6 {{ color: {MATERIAL_COLORS["primary"]}; }}
                        h1 {{ font-size: 24px; border-bottom: 1px solid {MATERIAL_COLORS["primary_light"]}; padding-bottom: 10px; }}
                        h2 {{ font-size: 20px; margin-top: 25px; }}
                        h3 {{ font-size: 16px; }}
                        ul, ol {{ padding-left: 25px; }}
                        li {{ margin-bottom: 5px; }}
                        strong {{ color: {MATERIAL_COLORS["secondary"]}; }}
                        code {{ background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
                        blockquote {{ 
                            border-left: 4px solid {MATERIAL_COLORS["primary_light"]}; 
                            padding-left: 15px; 
                            margin-left: 0;
                            color: {MATERIAL_COLORS["text_secondary"]};
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                self.report_view.setHtml(styled_html)
            except ImportError:
                # Если модуль markdown недоступен, показываем простой текст в HTML
                styled_html = f"""
                <html>
                <head>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            margin: 20px;
                            white-space: pre-wrap;
                            color: {MATERIAL_COLORS["text_primary"]};
                        }}
                    </style>
                </head>
                <body>
                    <pre>{report_content}</pre>
                </body>
                </html>
                """
                self.report_view.setHtml(styled_html)
                print("Для форматирования Markdown в HTML установите модуль markdown: pip install markdown")
        else:
            # Обновляем текстовый виджет
            self.report_text.clear()
            self.report_text.append(report_content)
        
        # Обновляем графики, если доступны
        if GRAPH_AVAILABLE:
            self.update_charts(result)
        
        # Скрываем индикатор загрузки
        self.stop_progress()
        
        # Обновляем статус
        self.statusbar.showMessage(f"Анализ отделения '{vsp_name}' успешно завершен")
        print(f"Анализ отделения '{vsp_name}' успешно завершен")
    
    def update_charts(self, result):
        """Обновление графиков на основе результатов анализа"""
        if not GRAPH_AVAILABLE:
            return
            
        vsp_reviews = result.get("vsp_reviews", [])
        risk_data = result.get("risk_data", {})
        rating_trend = result.get("rating_trend", [])
        
        # Очищаем графики
        self.risk_chart.clear()
        self.rating_chart.clear()
        self.tone_chart.clear()
        self.rating_dist_chart.clear()
        
        # Круговая диаграмма рисков
        if risk_data:
            # В pyqtgraph нет прямой поддержки круговых диаграмм,
            # поэтому используем полосовую диаграмму в качестве альтернативы
            labels = list(risk_data.keys())
            values = list(risk_data.values())
            
            # Создаем полосовую диаграмму
            bg = pg.BarGraphItem(
                x=range(len(values)), 
                height=values, 
                width=0.6, 
                brush=[MATERIAL_COLORS["chart1"], 
                       MATERIAL_COLORS["chart2"],
                       MATERIAL_COLORS["chart3"],
                       MATERIAL_COLORS["chart4"],
                       MATERIAL_COLORS["chart5"]]
            )
            self.risk_chart.addItem(bg)
            
            # Настраиваем оси
            self.risk_chart.setTitle("Распределение рисков")
            axis = self.risk_chart.getAxis('bottom')
            axis.setTicks([[(i, label) for i, label in enumerate(labels)]])
            
            self.risk_chart.showGrid(x=True, y=True)
        
        # График динамики рейтингов
        if rating_trend:
            months = [item["month"] for item in rating_trend]
            ratings = [item["rating"] for item in rating_trend]
            
            plot = self.rating_chart.plot(months, ratings, pen=pg.mkPen(MATERIAL_COLORS["primary"], width=3), symbolBrush=MATERIAL_COLORS["primary"], symbolPen='w', symbol='o', symbolSize=8)
            
            self.rating_chart.setTitle("Динамика рейтингов по месяцам")
            self.rating_chart.setLabel('left', 'Рейтинг')
            self.rating_chart.setLabel('bottom', 'Месяц')
            self.rating_chart.showGrid(x=True, y=True)
            
            # Ограничиваем диапазон оси Y от 0 до 5 (для рейтингов)
            self.rating_chart.setYRange(0, 5)
        
        # Распределение отзывов по тональности
        if vsp_reviews:
            tone_counts = {}
            for review in vsp_reviews:
                tone = review.get('tone', 'Не указано')
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
            
            # Сортируем по количеству
            tones = sorted(tone_counts.items(), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in tones]
            counts = [item[1] for item in tones]
            
            # Создаем цвета для тональностей
            tone_colors = {
                'Позитивный': MATERIAL_COLORS["success"],
                'Негативный': MATERIAL_COLORS["error"],
                'Нейтральный': MATERIAL_COLORS["info"],
                'Смешанный': MATERIAL_COLORS["warning"],
                'Не указано': MATERIAL_COLORS["text_hint"]
            }
            
            # Выбираем цвета для каждой тональности
            colors = [tone_colors.get(tone, MATERIAL_COLORS["chart1"]) for tone in labels]
            
            # Создаем полосовую диаграмму
            bg = pg.BarGraphItem(
                x=range(len(counts)), 
                height=counts, 
                width=0.6, 
                brush=colors
            )
            self.tone_chart.addItem(bg)
            
            # Настраиваем оси
            self.tone_chart.setTitle("Распределение отзывов по тональности")
            axis = self.tone_chart.getAxis('bottom')
            axis.setTicks([[(i, label) for i, label in enumerate(labels)]])
            
            self.tone_chart.showGrid(x=True, y=True)
            
            # Распределение отзывов по рейтингу
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in vsp_reviews:
                rating = review.get('rate', 0)
                if isinstance(rating, (int, float)) and 1 <= rating <= 5:
                    rating_counts[int(rating)] = rating_counts.get(int(rating), 0) + 1
            
            # Подготавливаем данные
            ratings = sorted(rating_counts.keys())
            counts = [rating_counts[rating] for rating in ratings]
            
            # Цвета для рейтингов
            rating_colors = [
                MATERIAL_COLORS["error"],        # 1 - красный
                MATERIAL_COLORS["warning"],      # 2 - оранжевый
                MATERIAL_COLORS["info"],         # 3 - синий
                MATERIAL_COLORS["chart3"],       # 4 - желтый
                MATERIAL_COLORS["success"]       # 5 - зеленый
            ]
            
            # Создаем полосовую диаграмму
            bg = pg.BarGraphItem(
                x=ratings, 
                height=counts, 
                width=0.6, 
                brush=rating_colors
            )
            self.rating_dist_chart.addItem(bg)
            
            # Настраиваем оси
            self.rating_dist_chart.setTitle("Распределение отзывов по рейтингу")
            self.rating_dist_chart.setLabel('left', 'Количество')
            self.rating_dist_chart.setLabel('bottom', 'Рейтинг')
            
            # Ограничиваем диапазон оси X от 0.5 до 5.5
            self.rating_dist_chart.setXRange(0.5, 5.5)
            self.rating_dist_chart.showGrid(x=True, y=True)
            
        # Переключаемся на вкладку графиков
        self.tab_widget.setCurrentIndex(1)
    
    def handle_analysis_error(self, error_message):
        """Обработка ошибок анализа"""
        self.stop_progress()
        print(f"Ошибка при выполнении анализа: {error_message}")
        QMessageBox.critical(self, "Ошибка", f"Ошибка при выполнении анализа: {error_message}")
        
        # Отображаем сообщение об ошибке в отчете
        if WEB_VIEW_AVAILABLE:
            self.report_view.setHtml(f"""
                <html>
                <head>
                    <style>
                        body {{ 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            margin: 20px; 
                            color: {MATERIAL_COLORS["text_primary"]};
                        }}
                        .error {{ 
                            color: {MATERIAL_COLORS["error"]}; 
                            font-weight: bold;
                            margin-bottom: 20px;
                        }}
                    </style>
                </head>
                <body>
                    <h2 class="error">Ошибка при выполнении анализа</h2>
                    <p>{error_message}</p>
                    <p>Пожалуйста, проверьте журнал работы для получения дополнительной информации.</p>
                </body>
                </html>
            """)
        else:
            self.report_text.clear()
            self.report_text.append(f"Ошибка при выполнении анализа: {error_message}")
            self.report_text.append("\nПожалуйста, проверьте журнал работы для получения дополнительной информации.")
    
    def run_demo(self):
        """Запуск демонстрационного режима"""
        try:
            global USE_MOCK_LLM
            USE_MOCK_LLM = True
            
            companies = vsp_data_tool.get_all_companies()
            if companies:
                vsp_name = companies[0]["name"]
                print(f"Запуск демонстрации на примере отделения: {vsp_name}")
                
                # Выбираем первое отделение в комбобоксе
                self.vsp_combo.setCurrentIndex(0)
                
                # Запускаем демо-анализ
                self.analyze_vsp()
            else:
                print("Не найдены данные об отделениях для демонстрации")
                QMessageBox.information(self, "Демо", "Не найдены данные об отделениях для демонстрации")
        except Exception as e:
            print(f"Ошибка при запуске демо-режима: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске демо-режима: {e}")
    
    def export_report(self):
        """Экспорт отчета в PDF файл"""
        # Проверяем, есть ли содержимое для экспорта
        if WEB_VIEW_AVAILABLE:
            html = self.report_view.page().mainFrame().toHtml() if hasattr(self.report_view.page(), 'mainFrame') else ""
            if "<h1>" not in html and "<h2>" not in html:
                QMessageBox.information(self, "Информация", "Сначала выполните анализ отделения, чтобы сгенерировать отчет")
                return
        else:
            report_content = self.report_text.toPlainText()
            if not report_content or "Выберите отделение и нажмите 'Анализировать'" in report_content:
                QMessageBox.information(self, "Информация", "Сначала выполните анализ отделения, чтобы сгенерировать отчет")
                return
        
        # Пытаемся создать PDF файл
        try:
            # Проверяем наличие необходимых библиотек
            try:
                import reportlab
            except ImportError:
                print("Для экспорта в PDF требуется установить reportlab: pip install reportlab")
                QMessageBox.information(self, "Информация", "Для экспорта в PDF требуется установить библиотеку reportlab.\nУстановите ее командой: pip install reportlab")
                return
            
            # Получаем имя файла для сохранения
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить отчет как", "", "PDF файлы (*.pdf);;Все файлы (*)"
            )
            
            if not filename:
                return  # Пользователь отменил сохранение
            
            # Добавляем расширение .pdf если отсутствует
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            # Показываем индикатор прогресса
            self.start_progress("Создание PDF...")
            
            # Получаем название отделения
            vsp_name = self.report_title.text().replace("Отчет о рисках: ", "")
            
            # Создаем PDF документ
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            # Определяем стили
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Title',
                parent=styles['Title'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor(MATERIAL_COLORS["primary"].replace("#", "#"))
            ))
            styles.add(ParagraphStyle(
                name='Heading1',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=10,
                textColor=colors.HexColor(MATERIAL_COLORS["primary"].replace("#", "#"))
            ))
            styles.add(ParagraphStyle(
                name='Heading2',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=8,
                textColor=colors.HexColor(MATERIAL_COLORS["primary"].replace("#", "#"))
            ))
            styles.add(ParagraphStyle(
                name='Normal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ))
            
            # Создаем документ
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                title=f"Отчет о рисках: {vsp_name}",
                author="Анализатор банковских рисков"
            )
            
            # Получаем текст отчета
            if WEB_VIEW_AVAILABLE:
                report_content = self.report_view.page().toHtml() if hasattr(self.report_view.page(), 'toHtml') else ""
                
                # Извлекаем текст из HTML
                import re
                report_content = re.sub('<[^<]+?>', '', report_content)
            else:
                report_content = self.report_text.toPlainText()
            
            # Разбиваем на строки
            report_lines = report_content.split('\n')
            
            # Создаем элементы документа
            elements = []
            
            # Добавляем заголовок
            elements.append(Paragraph(f"Отчет о рисках: {vsp_name}", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Обрабатываем строки отчета
            for line in report_lines:
                if line.startswith('# '):
                    elements.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    elements.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    elements.append(Paragraph(line[4:], styles['Heading2']))
                elif line.startswith('- ') or line.startswith('* '):
                    elements.append(Paragraph('• ' + line[2:], styles['Normal']))
                elif line.strip() == '':
                    elements.append(Spacer(1, 6))
                else:
                    # Заменяем Markdown-разметку
                    formatted_line = line.replace('**', '<b>').replace('**', '</b>')
                    formatted_line = formatted_line.replace('*', '<i>').replace('*', '</i>')
                    elements.append(Paragraph(formatted_line, styles['Normal']))
            
            # Строим документ
            doc.build(elements)
            
            # Скрываем индикатор прогресса
            self.stop_progress()
            
            print(f"Отчет успешно экспортирован в {filename}")
            QMessageBox.information(self, "Экспорт завершен", f"Отчет успешно сохранен в файл:\n{filename}")
            
            # Пытаемся открыть файл в стандартном приложении
            try:
                import os
                import platform
                if platform.system() == 'Windows':
                    os.startfile(filename)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{filename}"')
                else:  # Linux
                    os.system(f'xdg-open "{filename}"')
            except Exception as e:
                print(f"Не удалось автоматически открыть файл: {e}")
                
        except Exception as e:
            self.stop_progress()
            print(f"Ошибка при экспорте отчета: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать отчет: {e}")
    
    def clear_logs(self):
        """Очистка журнала работы"""
        self.log_text.clear()
        print("Журнал работы очищен")
    
    def start_progress(self, message="Загрузка..."):
        """Запуск индикатора прогресса и обновление статуса"""
        self.statusbar.showMessage(message)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
    
    def stop_progress(self):
        """Остановка индикатора прогресса"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        QTimer.singleShot(500, self.progress_bar.hide)

def main():
    # Проверяем доступность PyQt
    if not PYQT_AVAILABLE:
        print("PyQt5 не установлен. Установите его с помощью команды: pip install PyQt5")
        return
    
    # Инициализируем приложение
    app = QApplication(sys.argv)
    
    # Настраиваем шрифты для всего приложения
    app.setFont(QFont("Segoe UI", 10))
    
    # Создаем и показываем главное окно
    main_window = BankAnalyzerApp()
    main_window.show()
    
    # Запускаем главный цикл обработки событий
    sys.exit(app.exec_())

if __name__ == "__main__":
    #main() вывода отчета с прокруткой и улучшенным форматированием
        report_area = ttk.Frame(report_frame)
        report_area.pack(fill=tk.BOTH, expand=True)
        
        self.report_text = scrolledtext.ScrolledText(
            report_area, wrap=tk.WORD, font=("Segoe UI", 11)
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        # Настраиваем теги для форматирования текста
        self.report_text.tag_configure("h1", font=("Segoe UI", 16, "bold"), foreground=DARK_THEME["accent"])
        self.report_text.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground=DARK_THEME["accent"])
        self.report_text.tag_configure("h3", font=("Segoe UI", 12, "bold"), foreground=DARK_THEME["text_dark"])
        self.report_text.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.report_text.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        self.report_text.tag_configure("bullet", lmargin1=20, lmargin2=30)
        self.report_text.tag_configure("number", lmargin1=20, lmargin2=30)
        
        # Устанавливаем начальный текст
        self.report_text.insert(tk.END, "Выберите отделение и нажмите 'Анализировать' для генерации отчета о рисках.")
    
    def setup_log_tab(self):
        """Настройка вкладки логов"""
        log_frame = ttk.Frame(self.log_tab, padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем заголовок и кнопки управления
        header_frame = ttk.Frame(log_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Журнал работы", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Кнопка очистки логов
        clear_button = ModernUI.create_styled_button(
            header_frame, "Очистить", self.clear_logs, 
            icon="clear", width=10
        )
        clear_button.pack(side=tk.RIGHT)
        
        # Текстовое поле для вывода логов с прокруткой и цветовой подсветкой
        log_area = ttk.Frame(log_frame)
        log_area.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_area, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Настраиваем теги для цветов сообщений
        self.log_text.tag_configure("error", foreground=DARK_THEME["error"])
        self.log_text.tag_configure("warning", foreground=DARK_THEME["warning"])
        self.log_text.tag_configure("success", foreground=DARK_THEME["success"])
        self.log_text.tag_configure("normal", foreground=DARK_THEME["fg"])
    
    def load_vsps(self):
        """Загрузка списка отделений в combobox"""
        try:
            companies = vsp_data_tool.get_all_companies()
            vsp_list = [f"{vsp['name']} - {vsp['address']}" for vsp in companies]
            self.vsp_combobox["values"] = vsp_list
            if vsp_list:
                self.vsp_combobox.current(0)  # Выбираем первый элемент
                print(f"Загружено {len(vsp_list)} отделений")
            else:
                print("Не найдено ни одного отделения")
        except Exception as e:
            print(f"Ошибка при загрузке списка отделений: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить список отделений: {e}")
    
    def search_vsps(self, search_term=None):
        """Поиск отделений по названию или адресу"""
        if search_term is None:
            search_term = self.search_entry.get()
        
        search_term = search_term.strip()
        if not search_term:
            messagebox.showinfo("Информация", "Введите название или адрес отделения для поиска")
            return
        
        try:
            # Показываем индикатор загрузки
            self.show_progress("Поиск отделений...")
            
            matching_vsps = vsp_data_tool.get_vsp_by_name_or_address(search_term)
            if matching_vsps:
                vsp_list = [f"{vsp['name']} - {vsp['address']}" for vsp in matching_vsps]
                self.vsp_combobox["values"] = vsp_list
                self.vsp_combobox.current(0)  # Выбираем первый элемент
                print(f"Найдено {len(matching_vsps)} отделений по запросу '{search_term}'")
                
                # Добавляем анимацию для привлечения внимания
                self.highlight_combobox()
            else:
                print(f"Не найдено отделений по запросу '{search_term}'")
                messagebox.showinfo("Результаты поиска", f"Не найдено отделений по запросу '{search_term}'")
                
            self.hide_progress()
        except Exception as e:
            self.hide_progress()
            print(f"Ошибка при поиске отделений: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при поиске отделений: {e}")
    
    def highlight_combobox(self):
        """Анимация для привлечения внимания к combobox"""
        original_style = self.vsp_combobox.cget("style") or ""
        
        # Создаем временный стиль для подсветки
        style = ttk.Style()
        style.configure("Highlight.TCombobox", foreground=DARK_THEME["accent"])
        
        # Меняем стиль combobox
        self.vsp_combobox.configure(style="Highlight.TCombobox")
        
        # Возвращаем обратно через 1 секунду
        self.root.after(1000, lambda: self.vsp_combobox.configure(style=original_style))
    
    def analyze_vsp(self):
        """Анализ выбранного отделения"""
        selected_item = self.vsp_combobox.get()
        if not selected_item:
            messagebox.showinfo("Информация", "Выберите отделение для анализа")
            return
        
        # Извлекаем название отделения из выбранного элемента
        vsp_name = selected_item.split(" - ")[0]
        
        # Очищаем отчет и показываем индикатор загрузки
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "Выполняется анализ отделения...\nПожалуйста, подождите.")
        
        self.show_progress("Анализ отделения...")
        self.loading_indicator.show()
        
        # Создаем и запускаем поток для анализа
        analysis_thread = threading.Thread(target=self.run_analysis, args=(vsp_name,))
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def run_analysis(self, vsp_name):
        """Запуск анализа отделения в отдельном потоке"""
        try:
            print(f"Запуск анализа отделения '{vsp_name}'...")
            final_state = run_vsp_data_workflow(vsp_name)
            
            if final_state and final_state.get("final_report"):
                # Обновляем текст отчета в основном потоке
                self.root.after(0, lambda: self.update_report(final_state))
            else:
                self.root.after(0, lambda: self.status_var.set("Анализ завершен с ошибкой"))
                print("Анализ завершен с ошибкой, отчет не сгенерирован")
                self.root.after(0, self.hide_progress)
                self.root.after(0, self.loading_indicator.hide)
        except Exception as e:
            print(f"Ошибка при выполнении анализа: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при выполнении анализа: {e}"))
            self.root.after(0, self.hide_progress)
            self.root.after(0, self.loading_indicator.hide)
    
    def update_report(self, final_state):
        """Обновление текста отчета в интерфейсе с форматированием Markdown"""
        vsp_name = final_state.get("vsp_name", "")
        vsp_info = final_state.get("vsp_info", {})
        vsp_reviews = final_state.get("vsp_reviews", [])
        
        # Устанавливаем заголовок отчета
        self.report_title.configure(text=f"Отчет о рисках: {vsp_name}")
        
        # Очищаем текст отчета
        self.report_text.delete(1.0, tk.END)
        
        # Вставляем содержимое отчета
        self.report_text.insert(tk.END, final_state.get("final_report", "Отчет не сгенерирован"))
        
        # Применяем Markdown-форматирование
        ModernUI.apply_markdown_formatting(self.report_text)
        
        # Переключаемся на вкладку отчета
        for i, tab in enumerate(self.root.nametowidget(self.report_tab.winfo_parent()).tabs()):
            if tab == self.report_tab._w:
                self.root.nametowidget(self.report_tab.winfo_parent()).select(i)
                break
        
        # Скрываем индикаторы загрузки
        self.hide_progress()
        self.loading_indicator.hide()
        
        # Обновляем статус
        self.status_var.set(f"Анализ отделения '{vsp_name}' успешно завершен")
        print(f"Анализ отделения '{vsp_name}' успешно завершен")
    
    def run_demo(self):
        """Запуск демонстрационного режима"""
        try:
            global USE_MOCK_LLM
            USE_MOCK_LLM = True
            
            companies = vsp_data_tool.get_all_companies()
            if companies:
                vsp_name = companies[0]["name"]
                print(f"Запуск демонстрации на примере отделения: {vsp_name}")
                
                # Выбираем первое отделение в combobox
                self.vsp_combobox.current(0)
                
                # Запускаем демо-анализ
                self.analyze_vsp()
            else:
                print("Не найдены данные об отделениях для демонстрации")
                messagebox.showinfo("Демо", "Не найдены данные об отделениях для демонстрации")
        except Exception as e:
            print(f"Ошибка при запуске демо-режима: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при запуске демо-режима: {e}")
    
    def export_report(self):
        """Экспорт отчета в PDF файл"""
        # Проверяем, есть ли содержимое для экспорта
        report_content = self.report_text.get(1.0, tk.END).strip()
        if not report_content or report_content == "Выберите отделение и нажмите 'Анализировать' для генерации отчета о рисках.":
            messagebox.showinfo("Информация", "Сначала выполните анализ отделения, чтобы сгенерировать отчет")
            return
        
        # Пытаемся создать PDF файл
        try:
            # Проверяем наличие необходимых библиотек
            try:
                import reportlab
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            except ImportError:
                print("Для экспорта в PDF требуется установить reportlab: pip install reportlab")
                messagebox.showinfo("Информация", "Для экспорта в PDF требуется установить библиотеку reportlab.\nУстановите ее командой: pip install reportlab")
                return
            
            # Получаем имя файла для сохранения
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF файлы", "*.pdf"), ("Все файлы", "*.*")],
                title="Сохранить отчет как"
            )
            
            if not filename:
                return  # Пользователь отменил сохранение
            
            # Создаем PDF файл
            self.show_progress("Создание PDF...")
            
            # Извлекаем название отделения
            selected_item = self.vsp_combobox.get()
            vsp_name = selected_item.split(" - ")[0] if selected_item else "Отделение"
            
            # Создаем PDF документ
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                title=f"Отчет о рисках: {vsp_name}",
                author="Анализатор банковских рисков"
            )
            
            # Получаем текст отчета и разбиваем его на строки
            report_lines = report_content.split('\n')
            
            # Создаем стили для разных элементов отчета
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Title',
                parent=styles['Title'],
                fontSize=16,
                spaceAfter=12
            ))
            styles.add(ParagraphStyle(
                name='Heading1',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=10
            ))
            styles.add(ParagraphStyle(
                name='Heading2',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=8
            ))
            styles.add(ParagraphStyle(
                name='Normal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ))
            
            # Преобразуем Markdown в форматированный текст для PDF
            elements = []
            
            # Добавляем заголовок отчета
            elements.append(Paragraph(f"Отчет о рисках: {vsp_name}", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Обрабатываем строки отчета
            for line in report_lines:
                if line.startswith('# '):
                    elements.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    elements.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    elements.append(Paragraph(line[4:], styles['Heading2']))
                elif line.startswith('- ') or line.startswith('* '):
                    elements.append(Paragraph('• ' + line[2:], styles['Normal']))
                elif line.strip() == '':
                    elements.append(Spacer(1, 6))
                else:
                    # Заменяем Markdown-разметку на HTML для reportlab
                    formatted_line = line.replace('**', '<b>').replace('**', '</b>')
                    formatted_line = formatted_line.replace('*', '<i>').replace('*', '</i>')
                    elements.append(Paragraph(formatted_line, styles['Normal']))
            
            # Генерируем PDF
            doc.build(elements)
            
            self.hide_progress()
            print(f"Отчет успешно экспортирован в {filename}")
            messagebox.showinfo("Экспорт завершен", f"Отчет успешно сохранен в файл:\n{filename}")
            
            # Пытаемся открыть файл в стандартном приложении
            try:
                import os
                import platform
                if platform.system() == 'Windows':
                    os.startfile(filename)
                elif platform.system() == 'Darwin':  # macOS
                    os.system(f'open "{filename}"')
                else:  # Linux
                    os.system(f'xdg-open "{filename}"')
            except Exception as e:
                print(f"Не удалось автоматически открыть файл: {e}")
                
        except Exception as e:
            self.hide_progress()
            print(f"Ошибка при экспорте отчета: {e}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать отчет: {e}")
    
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        print("Журнал работы очищен")
    
    def show_progress(self, message="Загрузка..."):
        """Показывает индикатор прогресса и обновляет статус"""
        self.status_var.set(message)
        self.progress.pack(side=tk.RIGHT, padx=5)
        self.progress.start(10)
    
    def hide_progress(self):
        """Скрывает индикатор прогресса"""
        self.progress.stop()
        self.progress.pack_forget()

# Функция для создания и настройки корневого окна с темной темой
def create_themed_root():
    if THEMED_TK_AVAILABLE:
        # Создаем окно с темной темой
        root = ThemedTk(theme="equilux")  # Или другие темные темы: "black", "arc", "equilux"
        
        # Настраиваем цвета для соответствия нашей цветовой схеме
        root.configure(background=DARK_THEME["bg"])
        
        style = ttk.Style(root)
        style.configure(".", 
                        background=DARK_THEME["bg"],
                        foreground=DARK_THEME["fg"],
                        fieldbackground=DARK_THEME["panel"],
                        troughcolor=DARK_THEME["highlight"])
        
        # Настройка цветов для разных элементов
        style.configure("TLabel", background=DARK_THEME["bg"], foreground=DARK_THEME["fg"])
        style.configure("TFrame", background=DARK_THEME["bg"])
        style.configure("TLabelframe", background=DARK_THEME["bg"], foreground=DARK_THEME["fg"])
        style.configure("TLabelframe.Label", background=DARK_THEME["bg"], foreground=DARK_THEME["accent"])
        style.configure("TNotebook", background=DARK_THEME["bg"], foreground=DARK_THEME["fg"])
        style.configure("TNotebook.Tab", background=DARK_THEME["panel"], foreground=DARK_THEME["fg"])
        style.map("TNotebook.Tab",
                 background=[("selected", DARK_THEME["accent"])],
                 foreground=[("selected", DARK_THEME["bg"])])
        
        # Настройка текстовых виджетов
        root.option_add("*Text.Background", DARK_THEME["panel"])
        root.option_add("*Text.Foreground", DARK_THEME["fg"])
        root.option_add("*Text.selectBackground", DARK_THEME["accent"])
        root.option_add("*Text.selectForeground", DARK_THEME["bg"])
    else:
        # Если ttkthemes не доступен, создаем обычное окно
        root = tk.Tk()
        
        # Пробуем настроить нативную тему для текущей ОС
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")  # Более современная тема из стандартных
    
    return root

# Функция для запуска приложения
def main():
    # Создаем корневое окно с темной темой
    root = create_themed_root()
    
    # Создаем и запускаем приложение
    app = BankAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()# Основной модуль с графическим интерфейсом для анализатора банковских рисков
# Импортируем необходимые библиотеки
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import io
from pathlib import Path
import os
import json

# Импортируем функциональность из нашего основного модуля
# Предполагается, что основной код сохранен в файле bank_analyzer.py
# Если ваш файл имеет другое название, измените имя соответственно
try:
    # Пытаемся импортировать основные компоненты из основного модуля
    from bank_analyzer import (
        VspDataTool, run_vsp_data_workflow, USE_MOCK_LLM
    )
except ImportError:
    # Если модуль не найден, выводим сообщение об ошибке и создаем заглушки для тестирования
    print("Не удалось импортировать модуль bank_analyzer.py.")
    print("Создаем заглушки для тестирования интерфейса.")
    
    # Заглушка для демонстрации интерфейса
    USE_MOCK_LLM = True
    
    class VspDataTool:
        def __init__(self, data_dir="data"):
            self.companies = [
                {"id": 1, "name": "ВСП_1", "address": "ул. Тестовая, 1"},
                {"id": 2, "name": "ВСП_2", "address": "пр. Примерный, 2"}
            ]
            
        def get_all_companies(self):
            return self.companies
            
        def get_vsp_by_name_or_address(self, search_term):
            return [company for company in self.companies 
                   if search_term.lower() in company["name"].lower() 
                   or search_term.lower() in company["address"].lower()]
    
    def run_vsp_data_workflow(vsp_name):
        # Заглушка для функции анализа
        return {
            "vsp_name": vsp_name,
            "vsp_info": {"address": "Тестовый адрес"},
            "vsp_reviews": [{"rate": 5}, {"rate": 3}, {"rate": 4}],
            "final_report": f"Тестовый отчет для отделения {vsp_name}\n\n"
                           f"Это демонстрационный отчет, который показывает, как будет выглядеть "
                           f"реальный отчет о рисках для отделения.\n\n"
                           f"1. Операционные риски: средние\n"
                           f"2. Репутационные риски: низкие\n"
                           f"3. Технические риски: низкие\n\n"
                           f"Основная рекомендация: улучшить систему обслуживания клиентов."
        }

# Создаем экземпляр инструмента для работы с данными
vsp_data_tool = VspDataTool()

class RedirectOutput:
    """Класс для перенаправления стандартного вывода в виджет Text"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = io.StringIO()
    
    def write(self, string):
        self.buffer.write(string)
        # Обновляем виджет в безопасном режиме для потоков
        self.text_widget.after(0, self.update_text_widget)
    
    def update_text_widget(self):
        text = self.buffer.getvalue()
        if text:
            self.text_widget.insert(tk.END, text)
            self.text_widget.see(tk.END)  # Прокрутка к концу текста
            self.buffer = io.StringIO()  # Очищаем буфер
    
    def flush(self):
        pass

class BankAnalyzerApp:
    """Основной класс приложения для анализа банковских рисков"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор банковских рисков")
        self.root.geometry("900x700")  # Установка размера окна
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной frame с отступами
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель - поиск и выбор отделения
        search_frame = ttk.LabelFrame(main_frame, text="Поиск отделения", padding="5")
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Поле для ввода запроса поиска
        ttk.Label(search_frame, text="Название или адрес:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Button(search_frame, text="Поиск", command=self.search_vsps).grid(row=0, column=2, padx=5, pady=5)
        
        # Выпадающий список с отделениями
        ttk.Label(search_frame, text="Выберите отделение:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.vsp_combobox = ttk.Combobox(search_frame, width=40, state="readonly")
        self.vsp_combobox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Кнопки действий
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(button_frame, text="Анализировать", command=self.analyze_vsp).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Демо", command=self.run_demo).pack(side=tk.LEFT, padx=2)
        
        # Создаем вкладки для вывода
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка для отображения логов
        self.log_tab = ttk.Frame(tab_control)
        tab_control.add(self.log_tab, text="Логи")
        
        # Вкладка для отображения отчета
        self.report_tab = ttk.Frame(tab_control)
        tab_control.add(self.report_tab, text="Отчет")
        
        # Текстовое поле для вывода логов с прокруткой
        self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Текстовое поле для вывода отчета с прокруткой
        self.report_text = scrolledtext.ScrolledText(self.report_tab, wrap=tk.WORD, height=20, font=("Courier New", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Перенаправляем стандартный вывод в текстовое поле логов
        self.redirect = RedirectOutput(self.log_text)
        sys.stdout = self.redirect
        
        # Заполняем combobox при запуске
        self.load_vsps()
    
    def load_vsps(self):
        """Загрузка списка отделений в combobox"""
        try:
            companies = vsp_data_tool.get_all_companies()
            vsp_list = [f"{vsp['name']} - {vsp['address']}" for vsp in companies]
            self.vsp_combobox["values"] = vsp_list
            if vsp_list:
                self.vsp_combobox.current(0)  # Выбираем первый элемент
                print(f"Загружено {len(vsp_list)} отделений")
            else:
                print("Не найдено ни одного отделения")
        except Exception as e:
            print(f"Ошибка при загрузке списка отделений: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить список отделений: {e}")
    
    def search_vsps(self):
        """Поиск отделений по названию или адресу"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showinfo("Информация", "Введите название или адрес отделения для поиска")
            return
        
        try:
            matching_vsps = vsp_data_tool.get_vsp_by_name_or_address(search_term)
            if matching_vsps:
                vsp_list = [f"{vsp['name']} - {vsp['address']}" for vsp in matching_vsps]
                self.vsp_combobox["values"] = vsp_list
                self.vsp_combobox.current(0)  # Выбираем первый элемент
                print(f"Найдено {len(matching_vsps)} отделений по запросу '{search_term}'")
            else:
                print(f"Не найдено отделений по запросу '{search_term}'")
                messagebox.showinfo("Результаты поиска", f"Не найдено отделений по запросу '{search_term}'")
        except Exception as e:
            print(f"Ошибка при поиске отделений: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при поиске отделений: {e}")
    
    def analyze_vsp(self):
        """Анализ выбранного отделения"""
        selected_item = self.vsp_combobox.get()
        if not selected_item:
            messagebox.showinfo("Информация", "Выберите отделение для анализа")
            return
        
        # Извлекаем название отделения из выбранного элемента
        vsp_name = selected_item.split(" - ")[0]
        
        # Запускаем анализ в отдельном потоке
        self.status_var.set(f"Анализ отделения '{vsp_name}'...")
        self.report_text.delete(1.0, tk.END)  # Очищаем отчет
        
        # Создаем и запускаем поток для анализа
        analysis_thread = threading.Thread(target=self.run_analysis, args=(vsp_name,))
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def run_analysis(self, vsp_name):
        """Запуск анализа отделения в отдельном потоке"""
        try:
            print(f"Запуск анализа отделения '{vsp_name}'...")
            final_state = run_vsp_data_workflow(vsp_name)
            
            if final_state and final_state.get("final_report"):
                # Обновляем текст отчета в основном потоке
                self.root.after(0, lambda: self.update_report(final_state))
            else:
                self.root.after(0, lambda: self.status_var.set("Анализ завершен с ошибкой"))
                print("Анализ завершен с ошибкой, отчет не сгенерирован")
        except Exception as e:
            print(f"Ошибка при выполнении анализа: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Ошибка: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка при выполнении анализа: {e}"))
    
    def update_report(self, final_state):
        """Обновление текста отчета в интерфейсе"""
        vsp_name = final_state.get("vsp_name", "")
        vsp_info = final_state.get("vsp_info", {})
        vsp_reviews = final_state.get("vsp_reviews", [])
        
        # Добавляем заголовок отчета
        report_header = f"ОТЧЕТ О РИСКАХ: {vsp_name}\n"
        report_header += "=" * 50 + "\n\n"
        
        # Добавляем информацию об отделении
        report_header += f"Адрес: {vsp_info.get('address', 'Не указан')}\n"
        
        # Добавляем статистику по отзывам
        if vsp_reviews:
            ratings = [r.get('rate', 0) for r in vsp_reviews if isinstance(r.get('rate'), (int, float))]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                report_header += f"Отзывы: {len(vsp_reviews)} (Средний рейтинг: {avg_rating:.1f}/5)\n"
        
        report_header += "-" * 50 + "\n\n"
        
        # Добавляем основной отчет
        report_content = final_state.get("final_report", "Отчет не сгенерирован")
        
        # Обновляем текст отчета
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report_header + report_content)
        
        # Переключаемся на вкладку отчета
        for i, tab in enumerate(self.root.nametowidget(self.report_tab.winfo_parent()).tabs()):
            if tab == self.report_tab._w:
                self.root.nametowidget(self.report_tab.winfo_parent()).select(i)
                break
        
        self.status_var.set(f"Анализ отделения '{vsp_name}' завершен")
        print(f"Анализ отделения '{vsp_name}' успешно завершен")
    
    def run_demo(self):
        """Запуск демонстрационного режима"""
        try:
            global USE_MOCK_LLM
            USE_MOCK_LLM = True
            
            companies = vsp_data_tool.get_all_companies()
            if companies:
                vsp_name = companies[0]["name"]
                print(f"Запуск демонстрации на примере отделения: {vsp_name}")
                
                # Запускаем демо-анализ в отдельном потоке
                self.status_var.set(f"Демонстрация на примере отделения '{vsp_name}'...")
                
                # Создаем и запускаем поток для анализа
                demo_thread = threading.Thread(target=self.run_analysis, args=(vsp_name,))
                demo_thread.daemon = True
                demo_thread.start()
            else:
                print("Не найдены данные об отделениях для демонстрации")
                messagebox.showinfo("Демо", "Не найдены данные об отделениях для демонстрации")
        except Exception as e:
            print(f"Ошибка при запуске демо-режима: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при запуске демо-режима: {e}")

# Функция для запуска приложения
def main():
    root = tk.Tk()
    app = BankAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()