from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Type, Optional, Dict, List
import json
from crewai.tools import tool
from striprtf.striprtf import rtf_to_text
import chardet
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

import os
from dotenv import load_dotenv

# 1. Загрузка переменных окружения
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

# ----------------------------
# Инициализация LLM
# ----------------------------

#llm = ChatOpenAI(
#    openai_api_base="https://openrouter.ai/api/v1",
#    openai_api_key="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",
#    model_name="qwen/qwen3-4b:free"
#)

llm = ChatOpenAI(
    model="openrouter/qwen/qwen3-14b:free",
    #model="openrouter/meta-llama/llama-3.3-70b-instruct",
    #model="openrouter/google/gemini-2.5-flash-preview:thinking",
    #model="openrouter/qwen/qwen2.5-vl-72b-instruct:free",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    #openai_api_key=os.getenv("GEMINI_2.5_PREVIEW_API_KEY"),
    temperature=0.3,
    headers={
        "HTTP-Referer": "",  # Укажите ваш URL
        "X-Title": ""  # Название вашего приложения
    }
)

# ----------------------------
# Общая память для агентов
# ----------------------------

class SharedMemory:
    def __init__(self):
        self.memory = ConversationBufferMemory()
        self.historical_data = {}
        self.insights = {}
    
    def add_conversation(self, agent_name: str, message: str):
        """Сохраняет диалог в память"""
        self.memory.chat_memory.add_user_message(f"{agent_name}: {message}")
    
    def add_historical_data(self, key: str, data: dict):
        """Сохраняет аналитические данные"""
        self.historical_data[key] = data
    
    def add_insight(self, key: str, insight: str):
        """Сохраняет ключевые инсайты"""
        self.insights[key] = insight
    
    def get_context(self) -> str:
        """Возвращает контекст для агентов"""
        history = self.memory.load_memory_variables({})['history']
        insights = "\n".join([f"{k}: {v}" for k, v in self.insights.items()])
        return f"""
        ИСТОРИЯ ДИАЛОГА:
        {history}
        
        КЛЮЧЕВЫЕ ИНСАЙТЫ:
        {insights}
        """

shared_memory = SharedMemory()

def analyze_bank_reviews(question: str) -> str:
    """Возвращает результат в виде строки"""
    crew_result = original_analyze_function(question)  # Ваша текущая реализация
    return str(crew_result.raw_output if hasattr(crew_result, 'raw_output') else crew_result)

def read_rtf(file_path):
    print(f"Чтение файла: {file_path}")
    with open(file_path, 'rb') as file:
        raw_content = file.read()

        encoding = chardet.detect(raw_content)['encoding']
        try:
            decoded_content = raw_content.decode(encoding or 'cp1251')
        except UnicodeDecodeError:
            decoded_content = raw_content.decode('cp1251', errors='replace')

    text = rtf_to_text(decoded_content)
    print(f"read symbols: {len(text)}");
    return text


def read_text_file(file_path: str) -> str:
    """Читает содержимое текстового файла и возвращает его как строку

    Args:
        file_path: Путь к текстовому файлу

    Returns:
        Содержимое файла в виде строки
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# ----------------------------
# ----------------------------
# Инструменты с поддержкой памяти
# ----------------------------

@tool
def access_comments() -> Dict:
    """Возвращает клиентские комментарии о отделениях"""
    with open("data/reviews3.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        shared_memory.add_historical_data("latest_comments", data)
        return data

@tool
def access_companies() -> Dict:
    """Возвращает общие данные об отделениях для которых существуют комментарии"""
    with open("data/companies3.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        shared_memory.add_historical_data("companies_data", data)
        return data
    
@tool
def save_insight(insight: str) -> str:
    """Сохраняет ключевой инсайт в общую память"""
    key = f"insight_{len(shared_memory.insights) + 1}"
    shared_memory.add_insight(key, insight)
    return f"Инсайт сохранен с ключом: {key}"

@tool
def access_risk_methodology() -> str:
    """Возвращает ключевые положения методологии 716-П по операционному риску"""
    #очень большой текс документа, он не влезает в контекст 40К
    #return read_rtf('data/Положение_Банка_России_от_08_04_2020_N_716_П_ред_от_25_03_1.rtf')
    return read_text_file("data/716p.txt")

@tool
def access_wrong_practices() -> str:
    """Возвращает информацию о недобросовестных практиках"""
    return read_text_file("data/wrongPractices.txt")


def create_agent_with_memory(role: str, goal: str, backstory: str, tools: list, **kwargs):
    """Создает агента с поддержкой памяти"""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        llm=llm,
        verbose=True,
        memory=True,  # Включаем индивидуальную память
        system_template=f"""
        {backstory}
        
        Текущий контекст:
        {shared_memory.get_context()}
        
        Всегда анализируй историю диалога перед ответом!
        """,
        **kwargs
    )


# ----------------------------
# Определение агентов
# ----------------------------
senior_analyst = create_agent_with_memory(
    role='Старший аналитик данных',
    goal='Анализировать данные отзывов и выявлять ключевые метрики',
    backstory='Опытный аналитик с 10-летним стажем в банковской сфере',
    tools=[access_comments, access_companies, save_insight]
)

risk_assistant = create_agent_with_memory(
    role='Риск-ассистент',
    goal='Идентифицировать операционные риски и недобросовестные практики на основе отзывов клиентов',
    backstory='Специалист по управлению рисками с глубокими знаниями методологии 716-П '
              'и опытом выявления операционных инцидентов в банковской сфере.',
    tools=[access_comments, access_companies, access_wrong_practices, save_insight], #access_risk_methodology
    allow_delegation=False
)

insights_agent = create_agent_with_memory(
    role='Агент выявления инсайтов',
    goal='Формулировать краткие выводы и ключевые особенности по каждому отделению банка',
    backstory='Эксперт по интерпретации данных, способный выделять наиболее значимые '
              'аспекты из большого объема информации и представлять их в сжатом виде.',
    tools=[save_insight],
    allow_delegation=False
)

report_builder = create_agent_with_memory(
    role='Агент построения отчетов',
    goal='Создавать понятные и структурированные отчеты на основе данных от других агентов',
    backstory='Профессиональный технический писатель с опытом подготовки аналитических '
              'отчетов для высшего руководства банка.',
    tools=[save_insight],
    allow_delegation=False
)

critic = create_agent_with_memory(
    role='Критик',
    goal='Оценивать качество и полноту аналитических выводов, предоставленных другими агентами',
    backstory='Независимый эксперт с критическим мышлением, отвечающий за контроль '
              'качества аналитических материалов перед их представлением руководству.',
    tools=[],
    allow_delegation=False
)

# ----------------------------
# Определение задач
# ----------------------------

def create_analysis_tasks(question: str) -> List[Task]:
    """Создает список задач для анализа отзывов банковских отделений"""
    
    # Задача для старшего аналитика
    data_analysis_task = Task(
        description=f"""
        Проанализируйте данные отзывов банковских отделений и подготовьте аналитическую справку.
        Вопрос для анализа: {question}
        
        В вашем анализе должны быть:
        1. Средние рейтинги по каждому отделению
        2. Распределение тональности отзывов (позитивные, негативные, нейтральные)
        3. Динамика отзывов по времени
        4. Выявление отделений с лучшими и худшими показателями
        """,
        agent=senior_analyst,
        expected_output="""
        Детальный аналитический отчет с таблицами и графиками, показывающий:
        - Средние рейтинги по отделениям
        - Распределение тональности отзывов
        - Динамику изменения оценок с течением времени
        - Рейтинг отделений от лучшего к худшему
        """
    )

    # Задача для риск-ассистента
    risk_analysis_task = Task(
        description=f"""
        На основе отзывов клиентов идентифицируйте потенциальные операционные риски 
        и случаи недобросовестных практик в банковских отделениях.
        Вопрос для анализа: {question}
        
        Используйте методологию 716-П для классификации выявленных рисков.
        Особое внимание уделите:
        1. Жалобам на навязывание услуг
        2. Скрытым комиссиям и платежам
        3. Некомпетентности сотрудников
        4. Техническим сбоям
        """,
        agent=risk_assistant,
        expected_output="""
        Отчет о выявленных операционных рисках, содержащий:
        - Классификацию рисков по методологии 716-П
        - Список наиболее частых инцидентов
        - Отделения с наибольшим количеством жалоб
        - Рекомендации по снижению рисков
        """
    )

    # Задача для агента инсайтов
    insights_task = Task(
        description=f"""
        На основе данных аналитиков сформулируйте ключевые инсайты и выводы 
        по каждому банковскому отделению.
        Вопрос для анализа: {question}
        
        Обратите внимание на:
        1. Уникальные особенности каждого отделения
        2. Основные проблемы и преимущества
        3. Рекомендации по улучшению
        """,
        agent=insights_agent,
        expected_output="""
        Краткий отчет с ключевыми выводами по каждому отделению, содержащий:
        - Основные сильные и слабые стороны
        - Уникальные особенности работы
        - Рекомендации для руководства
        """
    )

    # Задача для построения отчетов
    report_task = Task(
        description=f"""
        На основе данных от всех аналитиков подготовьте итоговый отчет, 
        отвечающий на вопрос: {question}
        
        Отчет должен быть:
        1. Структурированным и понятным
        2. Содержать ключевые выводы
        3. Включать рекомендации для руководства
        4. Быть адаптирован для презентации топ-менеджменту
        """,
        agent=report_builder,
        expected_output="""
        Профессиональный отчет в формате Markdown, содержащий:
        - Ответ на исходный вопрос
        - Ключевые выводы
        - Рекомендации по улучшению
        """,
        output_file="report.md",  # Для сохранения в файл
        context=[data_analysis_task, risk_analysis_task]  # Зависимости
    )

    # Задача для критика
    critique_task = Task(
        description=f"""
        Критически оцените качество аналитического отчета, подготовленного командой.
        Проверьте:
        1. Полноту ответа на вопрос: {question}
        2. Обоснованность выводов
        4. Практическую применимость рекомендаций

        В ответе укажите:
        - "APPROVED" если отчет не требует доработок
        - Иначе список конкретных замечаний для исправления
        """,
        agent=critic,
        expected_output="""
        Либо строка "APPROVED", либо:
        - Список конкретных замечаний с указанием:
          * Раздела отчета
          * Сути проблемы
          * Рекомендации по исправлению
        """
    )

    return [data_analysis_task, risk_analysis_task, insights_task, report_task, critique_task]

# ----------------------------
# Функция для запуска анализа
# ----------------------------

def original_analyze_function(question: str) -> str:
    """Запускает мультиагентный анализ и возвращает готовый отчет"""
    max_revisions = 2
    current_revision = 0
    approved = False
    final_report = None
    critique_feedback = ""

    while not approved and current_revision < max_revisions:
        print(f"\n🔧 Итерация доработки {current_revision + 1}/{max_revisions}")

        tasks = create_analysis_tasks(question)

        if current_revision > 0:
            tasks[3].description += f"\n\nЗАМЕЧАНИЯ К ДОРАБОТКЕ:\n{critique_feedback}"

        crew = Crew(
            agents=[senior_analyst, risk_assistant, insights_agent, report_builder, critic],
            tasks=tasks,
            process=Process.sequential
        )

        result = crew.kickoff()

        # Извлекаем отдельно отчет и замечания критика
        if hasattr(result, 'tasks_output'):
            # Для версий CrewAI с tasks_output
            report = result.tasks_output[3]  # Отчет (4-я задача)
            critique = result.tasks_output[4]  # Критика (5-я задача)
        else:
            # Фолбэк для старых версий
            outputs = str(result).split("=== Task Output ===")
            report = outputs[3] if len(outputs) > 3 else str(result)
            critique = outputs[4] if len(outputs) > 4 else ""

        if "APPROVED" in critique:
            approved = True
            final_report = report
        else:
            critique_feedback = critique
            current_revision += 1

    return final_report if approved else f"{report}"  #\n\n⚠️ Достигнут лимит доработок. Замечания:\n{critique_feedback}

__all__ = ['analyze_bank_reviews', 'shared_memory', 'SharedMemory']
# ----------------------------
# Запуск системы
# ----------------------------
if __name__ == "__main__":
    try:
        print("🚀 Запуск анализа с улучшенной памятью...")
        shared_memory.add_conversation("System", "Инициализация анализа операционных рисков")
        
        result = analyze_bank_reviews(
            "Какие топ 5 отделений по жалобам?"
        )
        
        print("\n📊 Результат:", result)
        print("\n🧠 Контекст памяти:", shared_memory.get_context())

    except Exception as e:
        print(f"❌ Ошибка: {e}")