"""
LangGraph - библиотека для создания графов агентов
"""
import langgraph
from langgraph.graph import Graph, END
from langchain_community.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json
import os
from pathlib import Path

from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
  extra_headers={
    #"HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    #"X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  model="qwen/qwen3-4b:free",
  messages=[
    {
      "role": "user",
      "content": "Где живет дед мороз?"
    }
  ]
)

print(completion.choices[0].message.content)


# Определение состояния
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_task: str
    analysis_result: str
    recommendations: List[str]
    final_report: str
    vsp_name: str
    vsp_info: Optional[Dict[str, Any]]
    vsp_reviews: Optional[List[Dict[str, Any]]]

# Класс для работы с данными компаний
class vspDataTool:
    """Инструмент для работы с данными об отделениях банка в Москве и отзывами по каждому из них"""
    
    def __init__(self, data_dir: str = "../Downloads/hackaton/data"):
        """
        Инициализация инструмента для работы с данными отделений банка
        
        Args:
            data_dir: Путь к директории с данными
        """
        self.data_dir = Path(data_dir)
        self.companies_file = self.data_dir / "companies.json"
        self.reviews_file = self.data_dir / "reviews.json"
        
        # Загружаем данные при инициализации
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных из JSON файлов"""
        try:
            # Загрузка данных о компаниях
            if self.companies_file.exists():
                with open(self.companies_file, 'r', encoding='utf-8') as f:
                    self.companies = json.load(f)
            else:
                self.companies = []
                print(f"Предупреждение: Файл {self.companies_file} не найден")
            
            # Загрузка отзывов
            if self.reviews_file.exists():
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    self.reviews = json.load(f)
            else:
                self.reviews = []
                print(f"Предупреждение: Файл {self.reviews_file} не найден")
                
        except json.JSONDecodeError as e:
            print(f"Ошибка при чтении JSON файлов: {e}")
            self.companies = []
            self.reviews = []
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            self.companies = []
            self.reviews = []
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Получить список всех отделений"""
        return self.companies
    
    def get_vsp_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Найти отделение по адресу
        
        Args:
            name: Адрес отделение (полное или частичное)
            
        Returns:
            Информация об отделении или None, если отделение не найдено
        """
        name = name.lower()
        for vsp in self.companies:
            if name in vsp.get('name', '').lower():
                return vsp
        return None
    
    def get_vsp_by_id(self, vsp_id: str) -> Optional[Dict[str, Any]]:
        """
        Найти отделение по ID
        
        Args:
            vsp_id: ID отделения
            
        Returns:
            Информация об отделении или None, если отделение не найдено
        """
        for vsp in self.companies:
            if vsp.get('id') == vsp_id:
                return vsp
        return None
    
    def get_all_reviews(self) -> List[Dict[str, Any]]:
        """Получить список всех отзывов"""
        return self.reviews
    
    def get_reviews_by_vsp_id(self, vsp_id: str) -> List[Dict[str, Any]]:
        """
        Получить отзывы для конкретного отделения по ID
        
        Args:
            vsp_id: ID отделения
            
        Returns:
            Список отзывов для отделения
        """
        return [review for review in self.reviews if review.get('vsp_id') == vsp_id]
    
    def get_reviews_by_vsp_name(self, vsp_name: str) -> List[Dict[str, Any]]:
        """
        Получить отзывы для конкретного отделения по отзывам
        
        Args:
            vsp_name: Название отделения
            
        Returns:
            Список отзывов для отделения
        """
        # Сначала найдем компанию по имени
        vsp = self.get_vsp_by_name(vsp_name)
        if not vsp:
            return []
        
        # Затем получим отзывы по ID отделения
        vsp_id = vsp.get('id')
        if not vsp_id:
            return []
            
        return self.get_reviews_by_vsp_id(vsp_id)
    
    def get_average_rating_by_vsp_id(self, vsp_id: str) -> float:
        """
        Получить средний рейтинг отделения по ID
        
        Args:
            vsp_id: ID отделения
            
        Returns:
            Средний рейтинг отделения или 0, если отзывов нет
        """
        reviews = self.get_reviews_by_vsp_id(vsp_id)
        if not reviews:
            return 0
            
        ratings = [review.get('rating', 0) for review in reviews]
        return sum(ratings) / len(ratings)
    
    def get_average_rating_by_vsp_name(self, vsp_name: str) -> float:
        """
        Получить средний рейтинг отделения по названию
        
        Args:
            vsp_name: Название отделения
            
        Returns:
            Средний рейтинг отделения или 0, если отзывов нет
        """
        vsp = self.get_vsp_by_name(vsp_name)
        if not vsp:
            return 0
            
        vsp_id = vsp.get('id')
        if not vsp_id:
            return 0
            
        return self.get_average_rating_by_vsp_id(vsp_id)

# Создаем экземпляр инструмента для работы с данными компаний
vsp_data_tool = vspDataTool()

# Функции для работы с компаниями в графе агента

def get_vsp_info(state: GraphState) -> GraphState:
    """Получение информации о отделения из JSON файла"""
    messages = state["messages"]
    vsp_name = state.get("vsp_name", "")
    
    if not vsp_name:
        # Если имя отделения не указано, запросим его у пользователя
        messages.append(HumanMessage(content="Укажите название отделения для поиска информации"))
        response = llm.invoke(messages)
        messages.append(response)
        vsp_name = response.content.strip()
        state["vsp_name"] = vsp_name
    
    # Получаем информацию о отделения
    vsp_info = vsp_data_tool.get_vsp_by_name(vsp_name)
    
    if vsp_info:
        messages.append(HumanMessage(content=f"Найдена информация о отделения {vsp_name}"))
        messages.append(AIMessage(content=f"Информация о отделения {vsp_name} успешно получена."))
        
        return {
            **state,
            "messages": messages,
            "vsp_name": vsp_name,
            "vsp_info": vsp_info,
            "current_task": "get_vsp_reviews"
        }
    else:
        messages.append(HumanMessage(content=f"Компания {vsp_name} не найдена. Попробуйте другое название."))
        response = llm.invoke(messages)
        messages.append(response)
        
        return {
            **state,
            "messages": messages,
            "current_task": "get_vsp_info"  # Повторяем этот шаг
        }

def get_vsp_reviews(state: GraphState) -> GraphState:
    """Получение отзывов о отделения из JSON файла"""
    messages = state["messages"]
    vsp_name = state.get("vsp_name", "")
    vsp_info = state.get("vsp_info", None)
    
    if not vsp_info:
        return {
            **state,
            "messages": messages,
            "current_task": "get_vsp_info"  # Возвращаемся к получению информации о отделения
        }
    
    # Получаем отзывы о отделения
    vsp_id = vsp_info.get("id", "")
    if vsp_id:
        vsp_reviews = vsp_data_tool.get_reviews_by_vsp_id(vsp_id)
    else:
        vsp_reviews = vsp_data_tool.get_reviews_by_vsp_name(vsp_name)
    
    if vsp_reviews:
        messages.append(HumanMessage(content=f"Найдены отзывы о отделения {vsp_name}"))
        messages.append(AIMessage(content=f"Получено {len(vsp_reviews)} отзывов о отделения {vsp_name}."))
        
        return {
            **state,
            "messages": messages,
            "vsp_reviews": vsp_reviews,
            "current_task": "analyze_vsp_data"
        }
    else:
        messages.append(HumanMessage(content=f"Отзывы о отделения {vsp_name} не найдены."))
        messages.append(AIMessage(content=f"Отзывы о отделения {vsp_name} не найдены. Переходим к анализу только информации о отделения."))
        
        return {
            **state,
            "messages": messages,
            "vsp_reviews": [],
            "current_task": "analyze_vsp_data"
        }

def analyze_vsp_data(state: GraphState) -> GraphState:
    """Анализ данных о отделения и отзывов"""
    messages = state["messages"]
    vsp_info = state.get("vsp_info", {})
    vsp_reviews = state.get("vsp_reviews", [])
    
    # Запрос к LLM для анализа данных о отделения и отзывов
    analysis_prompt = f"""
    Проанализируй следующую информацию о отделения:
    
    Информация о отделения:
    {json.dumps(vsp_info, ensure_ascii=False, indent=2)}
    """
    
    if vsp_reviews:
        analysis_prompt += f"""
        
        Отзывы о отделения:
        {json.dumps(vsp_reviews, ensure_ascii=False, indent=2)}
        
        Определи:
        1. Общий рейтинг отделения на основе отзывов
        2. Основные сильные стороны отделения
        3. Основные слабые стороны отделения
        4. Рекомендации по улучшению
        """
    else:
        analysis_prompt += """
        
        Отзывы о отделения отсутствуют.
        
        Определи:
        1. Основные сильные стороны отделения на основе доступной информации
        2. Потенциальные области для развития
        3. Рекомендации для дальнейшего анализа
        """
    
    messages.append(HumanMessage(content=analysis_prompt))
    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "analysis_result": response.content,
        "current_task": "generate_insights"
    }


def generate_insights(state: GraphState) -> GraphState:
    """Генерация инсайтов"""
    messages = state["messages"]
    
    messages.append(HumanMessage(content=f"""
    На основе анализа: {state['analysis_result']}
    
    Сгенерируй 3-5 ключевых инсайтов для бизнеса.
    """))
    
    response = llm.invoke(messages)
    messages.append(response)
    
    # Извлекаем рекомендации (упрощенно)
    recommendations = response.content.split('\n')
    
    return {
        **state,
        "messages": messages,
        "recommendations": recommendations,
        "current_task": "create_report"
    }

def create_report(state: GraphState) -> GraphState:
    """Создание финального отчета"""
    messages = state["messages"]
    
    messages.append(HumanMessage(content=f"""
    Создай структурированный отчет на основе:
    - Анализа: {state['analysis_result']}
    - Рекомендаций: {', '.join(state['recommendations'])}
    
    Формат отчета:
    1. Резюме
    2. Ключевые находки
    3. Рекомендации
    4. Следующие шаги
    """))
    
    response = llm.invoke(messages)
    messages.append(response)
    
    return {
        **state,
        "messages": messages,
        "final_report": response.content,
        "current_task": "end"
    }

# Определение условной логики
def should_continue(state: GraphState) -> str:
    """Определяет следующий шаг в графе"""
    current_task = state.get("current_task", "analyze")
    
    if current_task == "analyze":
        return "analyze"
    elif current_task == "get_vsp_info":
        return "get_vsp_info"
    elif current_task == "get_vsp_reviews":
        return "get_vsp_reviews"
    elif current_task == "analyze_vsp_data":
        return "analyze_vsp_data"
    elif current_task == "generate_insights":
        return "insights"
    elif current_task == "create_report":
        return "report"
    else:
        return "end"

# Создание графа для анализа банковских данных (оригинальный пример)
def create_bank_analysis_workflow():
    workflow = Graph()
    
    # Добавление узлов
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("insights", generate_insights)
    workflow.add_node("report", create_report)
    
    # Добавление условных переходов
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "insights": "insights",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "insights",
        should_continue,
        {
            "report": "report",
            "end": END
        }
    )
    
    workflow.add_edge("report", END)
    
    # Установка начальной точки
    workflow.set_entry_point("analyze")
    
    return workflow.compile()

# Создание графа для работы с данными о компаниях
def create_vsp_data_workflow():
    workflow = Graph()
    
    # Добавление узлов
    workflow.add_node("get_vsp_info", get_vsp_info)
    workflow.add_node("get_vsp_reviews", get_vsp_reviews)
    workflow.add_node("analyze_vsp_data", analyze_vsp_data)
    workflow.add_node("insights", generate_insights)
    workflow.add_node("report", create_report)
    
    # Добавление условных переходов
    workflow.add_conditional_edges(
        "get_vsp_info",
        should_continue,
        {
            "get_vsp_reviews": "get_vsp_reviews",
            "get_vsp_info": "get_vsp_info",  # Повторная попытка при ошибке
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "get_vsp_reviews",
        should_continue,
        {
            "analyze_vsp_data": "analyze_vsp_data",
            "get_vsp_info": "get_vsp_info",  # Возврат к поиску отделения
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_vsp_data",
        should_continue,
        {
            "insights": "insights",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "insights",
        should_continue,
        {
            "report": "report",
            "end": END
        }
    )
    
    workflow.add_edge("report", END)
    
    # Установка начальной точки
    workflow.set_entry_point("get_vsp_info")
    
    return workflow.compile()

# Функция для запуска рабочего процесса с данными о отделения
def run_vsp_data_workflow(vsp_name=None):
    app = create_vsp_data_workflow()
    
    initial_state = {
        "messages": [],
        "current_task": "get_vsp_info",
        "vsp_name": vsp_name,
        "vsp_info": None,
        "vsp_reviews": None,
        "analysis_result": "",
        "recommendations": [],
        "final_report": ""
    }
    
    final_state = app.invoke(initial_state)
    
    print("\n=== Результаты работы ===")
    if final_state.get("vsp_info"):
        print(f"Информация о отделения: {final_state['vsp_name']}")
    else:
        print("Информация о отделения не найдена")
        
    if final_state.get("vsp_reviews"):
        print(f"Найдено отзывов: {len(final_state['vsp_reviews'])}")
    else:
        print("Отзывы не найдены")
        
    print("\n=== Итоговый отчет ===")
    print(final_state["final_report"])
    
    return final_state

# Запуск оригинального примера
def run_bank_analysis():
    app = create_bank_analysis_workflow()
    
    initial_state = {
        "messages": [],
        "current_task": "analyze",
        "analysis_result": "",
        "recommendations": [],
        "final_report": ""
    }
    
    final_state = app.invoke(initial_state)
    print(final_state["final_report"])
    
    return final_state

# ===== Вспомогательные функции =====

def test_lm_studio_connection():
    """Тест подключения к LM Studio"""
    import requests
    
    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [{"role": "user", "content": "Тест"}],
                "max_tokens": 10
            }
        )
        
        if response.status_code == 200:
            print("✓ Подключение к LM Studio успешно!")
            return True
        else:
            print(f"✗ Ошибка подключения: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Не удалось подключиться к LM Studio: {e}")
        print("Убедитесь, что сервер запущен на http://localhost:1234")
        return False

# Пример использования
if __name__ == "__main__":
    # Проверяем подключение к LM Studio
    if test_lm_studio_connection():
        # Запускаем рабочий процесс для получения данных о отделения
        print("\n=== Запуск рабочего процесса для получения данных о отделения ===")
        vsp_name = input("Введите название отделения (или нажмите Enter для ввода в процессе): ").strip()
        if not vsp_name:
            vsp_name = None
            
        run_vsp_data_workflow(vsp_name)
        
        # Можно также запустить оригинальный пример с анализом банковских данных
        # print("\n=== Запуск примера с анализом банковских данных ===")
        # run_bank_analysis()
