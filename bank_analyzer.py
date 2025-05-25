from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Type, Optional, Dict, List
import json
from crewai.tools import tool
from striprtf.striprtf import rtf_to_text
import chardet

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
# Исправленные инструменты (совместимый способ)
# ----------------------------

@tool
def access_comments() -> Dict:
    """Возвращает клиентские комментарии о отделениях"""
    with open("reviews3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

@tool
def access_companies() -> Dict:
    """Возвращает общие данные об отделениях для которых существуют комментарии"""
    with open("companies3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

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
# ----------------------------
# Определение агентов
# ----------------------------
senior_analyst = Agent(
    role='Старший аналитик данных',
    goal='Анализировать данные отзывов и выявлять ключевые метрики',
    backstory='Опытный аналитик с 10-летним стажем в банковской сфере',
    tools=[access_comments, access_companies],
    llm=llm,
    verbose=True
)

risk_assistant = Agent(
    role='Риск-ассистент',
    goal='Идентифицировать операционные риски и недобросовестные практики на основе отзывов клиентов',
    backstory='Специалист по управлению рисками с глубокими знаниями методологии 716-П '
              'и опытом выявления операционных инцидентов в банковской сфере.',
    tools=[access_comments, access_companies, access_risk_methodology, access_wrong_practices],
    verbose=True,
    allow_delegation=False,
    llm = llm
)

insights_agent = Agent(
    role='Агент выявления инсайтов',
    goal='Формулировать краткие выводы и ключевые особенности по каждому отделению банка',
    backstory='Эксперт по интерпретации данных, способный выделять наиболее значимые '
              'аспекты из большого объема информации и представлять их в сжатом виде.',
    verbose=True,
    allow_delegation=False,
    llm = llm
)

report_builder = Agent(
    role='Агент построения отчетов',
    goal='Создавать понятные и структурированные отчеты на основе данных от других агентов',
    backstory='Профессиональный технический писатель с опытом подготовки аналитических '
              'отчетов для высшего руководства банка.',
    verbose=True,
    allow_delegation=False,
    llm = llm
)

critic = Agent(
    role='Критик',
    goal='Оценивать качество и полноту аналитических выводов, предоставленных другими агентами',
    backstory='Независимый эксперт с критическим мышлением, отвечающий за контроль '
              'качества аналитических материалов перед их представлением руководству.',
    verbose=True,
    allow_delegation=False,
    llm = llm
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
        Профессиональный отчет в формате презентации, содержащий:
        - Ответ на исходный вопрос
        - Ключевые выводы
        - Визуализации данных
        - Рекомендации по улучшению
        """
    )

    # Задача для критика
    critique_task = Task(
        description=f"""
        Критически оцените качество аналитического отчета, подготовленного командой.
        Проверьте:
        1. Полноту ответа на вопрос: {question}
        2. Обоснованность выводов
        3. Качество визуализаций
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

def analyze_bank_reviews(question: str):
    """Запускает мультиагентный анализ с возможностью доработок"""
    max_revisions = 2  # Максимальное число доработок
    current_revision = 0
    approved = False
    final_result = None
    critique_feedback = ""

    while not approved and current_revision < max_revisions:
        print(f"\n🔧 Итерация доработки {current_revision + 1}/{max_revisions}")

        # Создаем/обновляем задачи
        tasks = create_analysis_tasks(question)

        if current_revision > 0:
            # Добавляем замечания в задачу report_builder
            tasks[3].description += f"\n\nЗАМЕЧАНИЯ К ДОРАБОТКЕ:\n{critique_feedback}"

        # Запускаем crew
        crew = Crew(
            agents=[senior_analyst, risk_assistant, insights_agent, report_builder, critic],
            tasks=tasks,
            process=Process.sequential
        )

        result = crew.kickoff()

        # Проверяем результат критика (последняя задача)
        if "APPROVED" in str(result).split("\n")[-1]:
            approved = True
            final_result = result
        else:
            critique_feedback = str(result).split("\n")[-1]
            current_revision += 1
            if current_revision < max_revisions:
                print("🔄 Отправка на доработку...")

    if not approved:
        final_result = str(result) + "\n\n⚠️ Достигнут лимит доработок. Отчет принят с замечаниями."

    return final_result




# ----------------------------
# Запуск системы
# ----------------------------
if __name__ == "__main__":
    try:

        print("🚀 Запуск анализа...")
        result = analyze_bank_reviews("Проанализируйте данные из клиентских комментариев и найдите инциденты операционного риска в отделениях")
        print("\n📊 Результат:", result)

    except Exception as e:
        print(f"❌ Ошибка: {e}")

