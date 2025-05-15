# Основные исправления:
# 1. Добавлен отсутствующий импорт llm
# 2. Исправлены опечатки в названиях переменных (vsp -> vsp)
# 3. Улучшена обработка ошибок
# 4. Исправлена логика работы с сообщениями

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

# Инициализация модели LLM (была отсутствующая переменная llm)
llm = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key="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",
    model_name="qwen/qwen3-4b:free"
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

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
class VspDataTool:
    """Инструмент для работы с данными об отделениях банка в Москве и отзывами по каждому из них"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Инициализация инструмента для работы с данными отделений банка
        
        Args:
            data_dir: Путь к директории с данными (относительно текущей директории)
        """
        # Создаем абсолютный путь из относительного
        self.data_dir = Path(__file__).parent / data_dir
        
        # Проверяем существование директории
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Директория с данными не найдена: {self.data_dir}")
            
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
                print(f"Ошибка: Файл {self.companies_file} не найден")
                raise FileNotFoundError(f"Файл {self.companies_file} не найден")
            
            # Загрузка отзывов
            if self.reviews_file.exists():
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    self.reviews = json.load(f)
            else:
                self.reviews = []
                print(f"Ошибка: Файл {self.reviews_file} не найден")
                raise FileNotFoundError(f"Файл {self.reviews_file} не найден")
                
        except json.JSONDecodeError as e:
            print(f"Ошибка при чтении JSON файлов: {e}")
            raise
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            raise
    
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
            return 0.0
            
        ratings = [review.get('rating', 0) for review in reviews if isinstance(review.get('rating'), (int, float))]
        if not ratings:
            return 0.0
            
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
            return 0.0
            
        vsp_id = vsp.get('id')
        if not vsp_id:
            return 0.0
            
        return self.get_average_rating_by_vsp_id(vsp_id)

# Создаем экземпляр инструмента для работы с данными компаний
vsp_data_tool = VspDataTool()

# Функции для работы с компаниями в графе агента
def get_vsp_info(state: GraphState) -> GraphState:
    """Получение информации о отделения из JSON файла"""
    messages = state["messages"]
    vsp_name = state.get("vsp_name", "")
        # Добавить счетчик попыток
    attempts = state.get("attempts", 0) + 1
    if attempts > 3:
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content="Превышено количество попыток. Завершаю работу.")],
            "current_task": "end"
        }
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
        messages.append(AIMessage(content=f"Найдена информация о отделении {vsp_name}"))
        
        return {
            **state,
            "messages": messages,
            "vsp_name": vsp_name,
            "vsp_info": vsp_info,
            "current_task": "get_vsp_reviews"
        }
    else:
        messages.append(AIMessage(content=f"Отделение {vsp_name} не найдена. Попробуйте другое название."))
        
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
        messages.append(AIMessage(content=f"Получено {len(vsp_reviews)} отзывов о отделении {vsp_name}."))
        
        return {
            **state,
            "messages": messages,
            "vsp_reviews": vsp_reviews,
            "current_task": "analyze_vsp_data"
        }
    else:
        messages.append(AIMessage(content=f"Отзывы о отделении {vsp_name} не найдены. Переходим к анализу только информации о отделении."))
        
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
    Проанализируй следующую информацию о отделении банка на предмет рисков:
    
    Информация о отделении:
    {json.dumps(vsp_info, ensure_ascii=False, indent=2)}
    """
    
    if vsp_reviews:
        analysis_prompt += f"""
        
        Отзывы клиентов:
        {json.dumps(vsp_reviews[:5], ensure_ascii=False, indent=2)} 
        (показано 5 из {len(vsp_reviews)} отзывов)
        
        Определи:
        1. Операционные риски (очереди, сбои системы)
        2. Риски поведения персонала (хамство, некомпетентность)
        3. Возможные случаи мошенничества
        4. Критические риски (кража данных и т.п.)
        5. Рекомендации по устранению рисков
        """
    else:
        analysis_prompt += """
        
        Отзывы клиентов отсутствуют.
        
        Проанализируй доступную информацию на предмет:
        1. Потенциальных операционных рисков
        2. Рекомендаций по сбору обратной связи
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
    
    Сгенерируй 3-5 ключевых инсайтов о рисках для банка.
    Для каждого риска укажи:
    - Уровень серьезности (низкий, средний, высокий)
    - Рекомендуемые действия
    - Сроки реагирования
    """))
    
    response = llm.invoke(messages)
    messages.append(response)
    
    # Извлекаем рекомендации (упрощенно)
    recommendations = [line.strip() for line in response.content.split('\n') if line.strip()]
    
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
    Создай структурированный отчет о рисках на основе:
    - Анализа: {state['analysis_result']}
    - Рекомендаций: {state['recommendations']}
    
    Формат отчета:
    1. Резюме (основные риски)
    2. Детализация по каждому риску
    3. Рекомендации по устранению
    4. Приоритеты действий
    5. Критические риски (если есть)
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
# Исправленная функция should_continue
def should_continue(state: GraphState) -> str:
    """Определяет следующий шаг в графе"""
    current_task = state.get("current_task", "get_vsp_info")
    
    # Логика определения следующего шага
    if current_task == "get_vsp_info":
        # Если vsp_info уже найден, переходим к отзывам
        if state.get("vsp_info"):
            return "get_vsp_reviews"
        else:
            # Если не найден, запрашиваем у пользователя снова
            return "get_vsp_info"
    
    elif current_task == "get_vsp_reviews":
        # Всегда переходим к анализу после получения отзывов
        return "analyze_vsp_data"
    
    elif current_task == "analyze_vsp_data":
        return "generate_insights"
    
    elif current_task == "generate_insights":
        return "create_report"
    
    elif current_task == "create_report":
        return "end"
    
    else:
        return "end"

# Создание графа для работы с данными о компаниях
# Исправленные условные переходы в create_vsp_data_workflow
def create_vsp_data_workflow():
    workflow = Graph()
    
    # Добавление узлов
    workflow.add_node("get_vsp_info", get_vsp_info)
    workflow.add_node("get_vsp_reviews", get_vsp_reviews)
    workflow.add_node("analyze_vsp_data", analyze_vsp_data)
    workflow.add_node("generate_insights", generate_insights)
    workflow.add_node("create_report", create_report)
    
    # Добавление условных переходов
    workflow.add_conditional_edges(
        "get_vsp_info",
        should_continue,
        {
            "get_vsp_reviews": "get_vsp_reviews",
            "get_vsp_info": "get_vsp_info",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "get_vsp_reviews",
        should_continue,
        {
            "analyze_vsp_data": "analyze_vsp_data",  # Исправлено: было "analyze_vsp_data"
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_vsp_data",
        should_continue,
        {
            "generate_insights": "generate_insights",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "generate_insights",
        should_continue,
        {
            "create_report": "create_report",
            "end": END
        }
    )
    
    workflow.add_edge("create_report", END)
    
    # Установка начальной точки
    workflow.set_entry_point("get_vsp_info")
    
    return workflow.compile()


# Функция для запуска рабочего процесса с данными о отделения
def run_vsp_data_workflow(vsp_name=None):
    app = create_vsp_data_workflow()
    
    initial_state = {
        "messages": [],
        "current_task": "get_vsp_info",
        "vsp_name": vsp_name if vsp_name else "",
        "vsp_info": None,
        "vsp_reviews": None,
        "analysis_result": "",
        "recommendations": [],
        "final_report": ""
    }
    
    final_state = app.invoke(initial_state)
    
    print("\n=== Результаты работы ===")
    if final_state.get("vsp_info"):
        print(f"Информация о отделении: {final_state['vsp_name']}")
    else:
        print("Информация о отделении не найдена")
        
    if final_state.get("vsp_reviews"):
        print(f"Найдено отзывов: {len(final_state['vsp_reviews'])}")
    else:
        print("Отзывы не найдены")
        
    print("\n=== Итоговый отчет о рисках ===")
    print(final_state["final_report"])
    
    return final_state

if __name__ == "__main__":
    print("=== Анализатор банковских рисков ===")
    vsp_name = input("Введите название отделения (или нажмите Enter для ввода в процессе): ").strip()
    run_vsp_data_workflow(vsp_name if vsp_name else None)