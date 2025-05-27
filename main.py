from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
import json
from crewai.tools import tool
from striprtf.striprtf import rtf_to_text
import chardet
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv
import logging

# Добавьте необходимые импорты в начале файла
from langchain_core.messages import HumanMessage, SystemMessage

# Настройка окружения и логирования
load_dotenv()
logging.basicConfig(level=logging.INFO)



# ----------------------------
# Класс общей памяти
# ----------------------------
class SharedMemory:
    def __init__(self):
        self.memory = ConversationBufferMemory()
        self.historical_data = {}
        self.insights = {}
    
    def add_conversation(self, agent_name: str, message: str):
        self.memory.chat_memory.add_user_message(f"{agent_name}: {message}")
    
    def add_historical_data(self, key: str, data: dict):
        self.historical_data[key] = data
    
    def add_insight(self, key: str, insight: str):
        self.insights[key] = insight
    
    def get_context(self) -> str:
        history = self.memory.load_memory_variables({})['history']
        insights = "\n".join([f"{k}: {v}" for k, v in self.insights.items()])
        return f"""
        ИСТОРИЯ ДИАЛОГА:
        {history}
        
        КЛЮЧЕВЫЕ ИНСАЙТЫ:
        {insights}
        """

shared_memory = SharedMemory()

# ----------------------------
#  Инициализация LLM
# ----------------------------
llm = ChatOpenAI(
    model="openrouter/qwen/qwen3-14b:free",  # Убрали префикс "openrouter/"
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.3
)


# ----------------------------
# Инструменты с поддержкой памяти
# ----------------------------
def readJson(file_path: str) -> Dict:
    # проверка наличия данных в локальном кеше
    print(f"reading: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        shared_memory.add_historical_data("latest_comments", data)
        return data

@tool
def access_comments() -> List[Dict]:
    """Возвращает клиентские комментарии о отделениях"""
    print(f"access_comments")
    return readJson("reviews3.json")

@tool
def access_companies() -> List[Dict]:
    """Возвращает общие данные об отделениях для которых существуют комментарии"""
    print(f"access_companies")
    return readJson("companies3.json")

@tool
def save_insight(insight: str) -> str:
    """Сохраняет ключевой инсайт в память"""
    key = f"insight_{len(shared_memory.insights) + 1}"
    shared_memory.add_insight(key, insight)
    return f"Инсайт сохранен с ключом: {key}"

@tool
def access_risk_methodology() -> str:
    """Возвращает ключевые положения методологии 716-П по операционному риску"""
    return read_text_file("data/716p.txt")

@tool
def access_wrong_practices() -> str:
    """Возвращает информацию о недобросовестных практиках"""
    return read_text_file("data/wrongPractices.txt")

# ----------------------------
# Вспомогательные функции
# ----------------------------
def read_text_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_rtf(file_path: str) -> str:
    with open(file_path, 'rb') as file:
        raw_content = file.read()
        encoding = chardet.detect(raw_content)['encoding']
        try:
            decoded_content = raw_content.decode(encoding or 'cp1251')
        except UnicodeDecodeError:
            decoded_content = raw_content.decode('cp1251', errors='replace')
    return rtf_to_text(decoded_content)

def generate_plan(question: str) -> List[str]:
    # Получение контекста из памяти
    context = shared_memory.get_context()
    
    # Шаблон запроса к LLM
    prompt = [HumanMessage(content=f"""
    **Запрос пользователя**: {question}
    
    **Контекст**: 
    {context}
    
    **Доступные действия**:
    - Анализ отзывов (access_comments)
    - Оценка рисков (risk_analysis)
    - Формирование инсайтов (insights)
    - Построение отчета (report)
    - Проверка качества (critique)
    
    Сгенерируй JSON-список задач в правильном порядке. Пример:
    {{"tasks": ["risk_analysis", "insights", "report"]}}
    """)]
    # Запрос к LLM
    try:
        response = llm.invoke(prompt).content
        print(response)
        plan = json.loads(response)["tasks"]
        return plan
    except:
        return ["data_analysis", "risk_analysis", "insights", "report", "critique"]  # fallback

# ----------------------------
# Фабрика агентов с памятью
# ----------------------------
def create_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: list,
    allow_delegation: bool = False
) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        llm=llm,
        verbose=True,
        memory=True,
        system_template=f"{backstory}\n\nТекущий контекст:\n{shared_memory.get_context()}",
        allow_delegation=allow_delegation
    )

# ----------------------------
# Определение агентов
# ----------------------------
senior_analyst = create_agent(
    role='Старший аналитик данных',
    goal='Анализировать данные отзывов и выявлять закономерности, тенденции, ключевые метрики, формировать выводы и рекомендации для улучшения сервиса и принятия решений бизнесом',
    backstory='Опытный аналитик с 10-летним стажем в банковской сфере, работал в крупнейших российских и международных банках, занимал позицию главного бизнес аналитика в управлении развития розничного бизнеса, кандидат экономических наук, очень ответственный и внимательный к деталям, избегает поверхностных выводов, тщательно проверяет гипотезы',
    tools=[access_comments, access_companies, save_insight]
)

risk_assistant = create_agent(
    role='Риск-ассистент',
    goal='Провести глубокий всесторонний анализ, идентифицировать операционные риски и недобросовестные практики на основе отзывов клиентов',
    backstory='Специалист по управлению рисками с глубокими знаниями методологии 716-П  '
              'и значительным опытом выявления операционных рисков в банковской сфере. Является автором методики по выявлению и управлению операционным риском и риском поведения, бывший руководитель отдела риск-менеджмента крупнейших российских банков, выстроил систему мониторинга операционного риска, снизив потери на 30%',
    tools=[access_comments, access_companies, access_wrong_practices, save_insight]
)

insights_agent = create_agent(
    role='Агент выявления инсайтов',
    goal='Выявлять ключевые позитивные и негативные особенности по каждому отделению банка, формулировать краткие информативные выводы',
    backstory='Эксперт по интерпретации данных, способный выделять наиболее значимые аспекты из большого объема информации и представлять их в сжатом виде, возглавлял аналитические отделы в крупных банках, имеет большой опыт в аналитике данных и выявлении причинно-следственных связей, участвовал в автоматизации алгоритма рекомендаций по принятию управленческих решений.',
    tools=[save_insight]
)

report_builder = create_agent(
    role='Агент построения отчетов',
    goal='На основе данных от других агентов создавать качественные, понятные и структурированные отчеты, отражающие ключевые показатели для принятия оперативных и стратегических решений',
    backstory='Профессиональный технический писатель с большим опытом подготовки аналитических отчетов для высшего руководства банка, имеет глубокие знания в области построения отчетности, высокий уровень ответственности, внимательность к деталям, был руководителем отдела разработки и внедрения отчетности в Центральном Банке',
    tools=[save_insight]
)

critic = create_agent(
    role='Критик',
    goal='Оценивать качество и полноту выводов, предоставленных другими агентами, проводя тщательный анализ по всем аспектам, давать проработанные развернутые оценки',
    backstory='Независимый эксперт с критическим мышлением, отвечающий за контроль качества аналитических материалов перед их представлением руководству. Имеет глубокие знания и богатый опыт в обработке и интерпретации данных и построении аналитики, отличается вниманием к деталям и глубокой проработкой сделанных выводов, возглавлял крупное аналитическое агентство',
    tools=[]
)

planner = create_agent(
    role='Планировщик задач',
    goal='Генерировать оптимальный порядок задач для решения запроса',
    backstory='Эксперт в анализе запросов и построении рабочих процессов. Использует данные из памяти и знания предметной области.',
    tools=[access_comments, access_companies, save_insight],
    allow_delegation=False
)

# ----------------------------
# Определение задач
# ----------------------------
def create_analysis_tasks(question: str) -> List[Task]:
    
    plan = generate_plan(question)

    data_analysis_task = Task(
            description=f"Анализ данных отзывов. Вопрос: {question}. Сформируйте инсайты на основе анализа данных и сохраните их через save_insight(insight='ваш_текст')",
            agent=senior_analyst,
            expected_output="Отчет с рейтингами и динамикой оценок"
        )

    risk_analysis_task = Task(
            description=f"""На основе отзывов клиентов идентифицируйте потенциальные операционные риски 
        и случаи недобросовестных практик в банковских отделениях. Используйте строго методологию 716-П и информацию о недобросовестных практиках
          для классификации выявленных рисков. Вопрос для анализа: {question}
Сформируйте инсайты на основе анализа данных и сохраните их через save_insight(insight='ваш_текст')""",
            agent=risk_assistant,
            expected_output="Отчет о рисках с классификацией по методологии 716-П"
        )

    insights_task = Task(
            description=f"""Формулировка ключевых выводов. Обратите внимание на:
        1. Уникальные особенности отделения
        2. Основные проблемы и преимущества
        3. Рекомендации по улучшению. Вопрос: {question}
        Сформируйте инсайты на основе анализа данных и сохраните их через save_insight(insight='ваш_текст')""",
            agent=insights_agent,
            expected_output="Краткий отчет с сильными и слабыми сторонами"
        )

    report_task = Task(
            description=f"""На основе данных от всех аналитиков подготовьте итоговый отчет, 
        отвечающий на вопрос: {question}
        Отчет должен быть:
        1. Структурированным и понятным
        2. Содержать ключевые выводы
        3. Включать рекомендации для руководства
        4. Быть адаптирован для презентации топ-менеджменту""",
            agent=report_builder,
            expected_output="""Профессиональный отчет в формате Markdown для вывода в телеграм, содержащий:
        - Ответ на исходный вопрос
        - Ключевые выводы
        - Рекомендации по улучшению""",
            output_file="report.md",
            context=[data_analysis_task, risk_analysis_task]
        )

    critique_task = Task(
            description=f""" Критически оцените качество аналитического отчета, подготовленного командой.
        Проверьте:
        1. Полноту ответа на вопрос: {question}
        2. Обоснованность выводов""",
            agent=critic,
            expected_output="Либо 'APPROVED', либо список замечаний"
        )
    
    task_templates = {
        "data_analysis": data_analysis_task,
        "risk_analysis": risk_analysis_task,
        "insights": insights_task,
        "report": report_task,
        "critique": critique_task
    }
    
    # Сборка задач по плану
    tasks = []
    for task_name in plan:
        if task_name in task_templates:
            tasks.append(task_templates[task_name])

    shared_memory.add_historical_data("latest_plan", {"plan": plan, "question": question})
    
    return tasks

# ----------------------------
# Основная логика анализа
# ----------------------------
def analyze_bank_reviews(question: str) -> str:
    max_revisions = 2
    current_revision = 0
    approved = False
    final_report = None

    while not approved and current_revision < max_revisions:
        print("Создание задачи на анализ")
        tasks = create_analysis_tasks(question)
        print("create_analysis_tasks done")
        print(current_revision)
        if current_revision > 0:
            print(current_revision)
            tasks[3].description += f"\n\nЗАМЕЧАНИЯ ИЗ ПРЕДЫДУЩЕЙ ИТЕРАЦИИ:\n{shared_memory.get_context()}"
        print("crew")
        crew = Crew(
            agents=[senior_analyst, risk_assistant, insights_agent, report_builder, critic],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        print("crew.kickoff")
        result = crew.kickoff()
        print("tasks_output")
        tasks_output = getattr(result, 'tasks_output', [None] * 5)
        print("report")
        report = str(tasks_output[3]) if tasks_output[3] else ""
        critique = str(tasks_output[4]) if tasks_output[4] else ""

        if "APPROVED" in critique:
            approved = True
            final_report = report
        else:
            shared_memory.add_conversation("Critic", critique)
            current_revision += 1

    return final_report if approved else f"{report}\n\n⚠️ Достигнут лимит доработок"

# ----------------------------
# Запуск системы
# ----------------------------
if __name__ == "__main__":
    try:
        print("🚀 Запуск анализа...")
        shared_memory.add_conversation("System", "Инициализация анализа")
        result = analyze_bank_reviews("В каком отделении были инциденты операционного риска за последний месяц?")
        print("\n📊 Результат:", result)
    except Exception as e:
        print(f"❌ Ошибка: {e}")