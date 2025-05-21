import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_gigachat import GigaChat
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import Tool
from langchain_core.messages import SystemMessage

# Загрузка переменных окружения
load_dotenv()

# Загрузка данных
def load_companies() -> List[Dict[str, Any]]:
    with open('data/companies.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_reviews() -> List[Dict[str, Any]]:
    with open('data/reviews_small.json', 'r', encoding='utf-8') as f:
        return json.load(f)

companies = load_companies()
reviews = load_reviews()

# Модель для ответа со списком компаний
class CompanyListResponse(BaseModel):
    companies: List[Dict[str, Any]] = Field(description="Список компаний с их основными данными")

# Модель для анализа компании
class CompanyAnalysisResponse(BaseModel):
    name: str = Field(description="Название компании")
    address: str = Field(description="Адрес компании")
    average_rating: float = Field(description="Средний рейтинг")
    risks: List[str] = Field(description="Список основных рисков")

# Инструмент для получения списка компаний
def get_companies(anyParm: str) -> str:
    """Возвращает список всех отделений/организаций в формате: ID Название Адрес"""
    # Формируем список в нужном формате
    companies_list = [
        f"{company['id']} {company['name']} {company['address']}"
        for company in companies
    ]
    # Возвращаем как строку с переносами
    return "\n".join(companies_list)

# Инструмент для анализа компании`
def analyze_company(company_id: str) -> str:
    """Анализирует компанию по её ID и возвращает результаты анализа"""
    orgId: int = int(company_id)
    company_reviews = [r for r in reviews if r['orgId'] == orgId]
    company = next((c for c in companies if c['id'] == orgId), {})

    if not company_reviews:
        return CompanyAnalysisResponse(
            name=company.get('name', 'Unknown'),
            address=company.get('address', 'Unknown'),
            average_rating=0,
            risks=["Нет данных об отзывах"]
        ).json()

    avg_rating = sum(r['rate'] for r in company_reviews) / len(company_reviews)
    negative_reviews = [r for r in company_reviews if r['rate'] <= 2]

    risks = list(set(
        r['comment'].split('.')[0].strip()
        for r in negative_reviews
    ))[:3] if negative_reviews else ["Не обнаружено значительных рисков"]

    return CompanyAnalysisResponse(
        name=company.get('name', 'Unknown'),
        address=company.get('address', 'Unknown'),
        average_rating=round(avg_rating, 2),
        risks=risks
    ).json()

# Создаем инструменты
tools = [
    Tool(
        name="get_companies",
        func=get_companies,
        description="Используется для получения списка всех отделений в формате: ID name address. Принимает любую строку как параметр."
    ),
    Tool(
        name="analyze_company",
        func=analyze_company,
        description="Используется для анализа конкретного отделения. Принимает ID компании как вход (целое число)."
    )
]

# Инициализация GigaChat
giga = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"),
    model="GigaChat-Max",
    verify_ssl_certs=False
)

# Настройка промпта
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""Ты - управляющий директор компании, анализирующий мнение клиентов. 
У тебя есть доступ к данным о компаниях и их отзывах. Отвечай профессионально и по делу.
при запросе информации об отделении форматируй ответ с переносом строки, например:
- id 
- name 
- address
Средний рейтинг этого отделения составляет 1.0
В числе рисков отмечается недовольство клиентов качеством обслуживания, выраженное в комментарии "Сбер банк стал самым ужасным банком".


"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Создание агента
agent = create_openai_tools_agent(
    llm=giga,
    tools=tools,
    prompt=prompt
)

# Настройка исполнителя агента
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Основной цикл
def main():
    print("Приветствую! Я ваш виртуальный помощник для анализа отзывов о отделениях.")
    print("Вы можете запросить список всех отделений или аналитику по конкретному отделению.")
    print("Для выхода введите 'выход' или 'exit'.")

    while True:
        user_input = input("\nВаш запрос: ").strip()

        if user_input.lower() in ['выход', 'exit', 'quit']:
            print("До свидания!")
            break

        try:
            response = agent_executor.invoke({"input": user_input})
            print("\nОтвет:", response['output'])
        except Exception as e:
            print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()