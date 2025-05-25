from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any
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


# Глобальный кеш в памяти для доступа к данным в tools
FILE_CACHE: Dict[str, Any] = {}

# ----------------------------
# Инициализация LLM
# ----------------------------

llm = ChatOpenAI(
    #model="openrouter/qwen/qwen3-14b:free",
    model=os.getenv("MODEL_NAME"),
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv(os.getenv("API_KEY")),
    temperature=0.3
)

def read_rtf(file_path):
    print(f"Чтение файла: {file_path}")

    # проверка наличия данных в локальном кеше
    if file_path in FILE_CACHE:
        print(f"cache hit: {file_path}")
        return FILE_CACHE[file_path]
    print(f"cache miss: {file_path}")


    with open(file_path, 'rb') as file:
        raw_content = file.read()

        encoding = chardet.detect(raw_content)['encoding']
        try:
            decoded_content = raw_content.decode(encoding or 'cp1251')
        except UnicodeDecodeError:
            decoded_content = raw_content.decode('cp1251', errors='replace')

    text = rtf_to_text(decoded_content)
    FILE_CACHE[file_path] = text
    print(f"read symbols: {len(text)}")
    return text


def read_text_file(file_path: str) -> str:
    """Читает содержимое текстового файла и возвращает его как строку

    Args:
        file_path: Путь к текстовому файлу

    Returns:
        Содержимое файла в виде строки
    """
    # проверка наличия данных в локальном кеше
    if file_path in FILE_CACHE:
        print(f"cache hit: {file_path}")
        return FILE_CACHE[file_path]
    print(f"cache miss: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        FILE_CACHE[file_path] = text
        return text

def readJson(file_path: str) -> Dict:
    # проверка наличия данных в локальном кеше
    if file_path in FILE_CACHE:
        print(f"cache hit: {file_path}")
        return FILE_CACHE[file_path]
    print(f"cache miss: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        text = json.load(f)
        FILE_CACHE[file_path] = text
        return text

@tool
def access_comments() -> Dict:
    """Возвращает клиентские комментарии о отделениях"""
    return readJson("reviews3.json")

@tool
def access_companies() -> Dict:
    """Возвращает общие данные об отделениях для которых существуют комментарии"""
    return readJson("companies3.json")

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
    goal='Анализировать данные отзывов и выявлять закономерности, тенденции, ключевые метрики, формировать выводы и рекомендации для улучшения сервиса и принятия решений бизнесом',
    backstory='Опытный аналитик с 10-летним стажем в банковской сфере, работал в крупнейших российских и международных банках, занимал позицию главного бизнес аналитика в управлении развития розничного бизнеса, кандидат экономических наук, очень ответственный и внимательный к деталям, избегает поверхностных выводов, тщательно проверяет гипотезы',
    tools=[access_comments, access_companies],
    llm=llm,
    verbose=True
)

risk_assistant = Agent(
    role='Риск-ассистент',
    goal='Провести глубокий всесторонний анализ, идентифицировать операционные риски и недобросовестные практики на основе отзывов клиентов',
    backstory='Специалист по управлению рисками с глубокими знаниями методологии 716-П  '
              'и значительным опытом выявления операционных рисков в банковской сфере. Является автором методики по выявлению и управлению операционным риском и риском поведения, бывший руководитель отдела риск-менеджмента крупнейших российских банков, выстроил систему мониторинга операционного риска, снизив потери на 30%',
    tools=[access_comments, access_companies, access_risk_methodology, access_wrong_practices],
    verbose=True,
    allow_delegation=False,
    llm = llm
)

insights_agent = Agent(
    role='Агент выявления инсайтов',
    goal='Выявлять ключевые позитивные и негативные особенности по каждому отделению банка, формулировать краткие информативные выводы',
    backstory='Эксперт по интерпретации данных, способный выделять наиболее значимые аспекты из большого объема информации и представлять их в сжатом виде, возглавлял аналитические отделы в крупных банках, имеет большой опыт в аналитике данных и выявлении причинно-следственных связей, участвовал в автоматизации алгоритма рекомендаций по принятию управленческих решений.',
    verbose=True,
    allow_delegation=False,
    llm = llm
)

report_builder = Agent(
    role='Агент построения отчетов',
    goal='На основе данных от других агентов создавать качественные, понятные и структурированные отчеты, отражающие ключевые показатели для принятия оперативных и стратегических решений',
    backstory='Профессиональный технический писатель с большим опытом подготовки аналитических отчетов для высшего руководства банка, имеет глубокие знания в области построения отчетности, высокий уровень ответственности, внимательность к деталям, был руководителем отдела разработки и внедрения отчетности в Центральном Банке',
    verbose=True,
    allow_delegation=False,
    llm = llm
)

critic = Agent(
    role='Критик',
    goal='Оценивать качество и полноту выводов, предоставленных другими агентами, проводя тщательный анализ по всем аспектам, давать проработанные развернутые оценки',
    backstory='Независимый эксперт с критическим мышлением, отвечающий за контроль качества аналитических материалов перед их представлением руководству. Имеет глубокие знания и богатый опыт в обработке и интерпретации данных и построении аналитики, отличается вниманием к деталям и глубокой проработкой сделанных выводов, возглавлял крупное аналитическое агентство',
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
        """,
        output_file = "report_output.txt"
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
    max_revisions = 3
    current_revision = 0
    approved = False
    final_report = None
    last_critique = ""
    last_report = ""

    while not approved and current_revision < max_revisions:
        print(f"\n🔧 Итерация доработки {current_revision + 1}/{max_revisions}")

        tasks = create_analysis_tasks(question)

        if current_revision > 0:
            tasks[3].description += f"\n\nЗАМЕЧАНИЯ К ДОРАБОТКЕ:\n{last_critique}"

        crew = Crew(
            agents=[senior_analyst, risk_assistant, insights_agent, report_builder, critic],
            tasks=tasks,
            process=Process.sequential
        )

        crew.kickoff()

        # Получаем отчет builder'а (предпоследняя задача)
        report_content = tasks[-2].output.raw_output if hasattr(tasks[-2].output, 'raw_output') else str(
            tasks[-2].output)
        # Получаем замечания критика (последняя задача)
        critique_result = tasks[-1].output.raw_output if hasattr(tasks[-1].output, 'raw_output') else str(
            tasks[-1].output)

        last_report = report_content
        last_critique = critique_result

        if "APPROVED" in critique_result:
            approved = True
            final_report = report_content
        else:
            current_revision += 1
            if current_revision < max_revisions:
                print("🔄 Отправка на доработку...")

    if approved:
        result_str = "📋 ФИНАЛЬНАЯ ВЕРСИЯ ОТЧЕТА:\n"
        result_str += final_report + "\n"
        return result_str
    else:
        result_str = "⚠️ Достигнут лимит доработок. Отчет принят с замечаниями.\n\n"
        result_str += "📋 ФИНАЛЬНАЯ ВЕРСИЯ ОТЧЕТА C ЗАМЕЧАНИЯМИ:\n"
        result_str += "──────────────────────────\n"
        result_str += last_report + "\n\n"
        result_str += "🔹 ЗАКЛЮЧЕНИЕ КРИТИКА:\n"
        result_str += last_critique + "\n"

        return result_str




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

