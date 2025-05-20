# Основные исправления:
# 1. Доработана логика условных переходов для избежания KeyError: analyze_vsp_data
# 2. Исправлены опечатки и несоответствия в переменных
# 3. Добавлена более надежная обработка ошибок
# 4. Улучшена работа с отзывами и рейтингами
# 5. Добавлены комментарии для лучшей читаемости

import langgraph
from langgraph.graph import Graph, END
from langchain_community.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json
import os
from pathlib import Path
import traceback
import time

# Флаг для использования мок-режима (без использования API)
USE_MOCK_LLM = False

# Создаем имитацию LLM-модели для тестирования без API ключа
class MockLLM:
    """Мок-класс для имитации работы LLM-модели"""
    
    def invoke(self, messages):
        """Имитация ответа от LLM"""
        # Анализируем последнее сообщение
        last_message = messages[-1].content if messages else ""
        
        # Имитация задержки для реалистичности
        time.sleep(0.5)
        
        # Возвращаем заглушку ответа в зависимости от контекста запроса
        if "название отделения" in last_message:
            return AIMessage(content="ВСП_1")
        elif "информацию о отделении" in last_message:
            return AIMessage(content="На основе анализа информации о отделении ВСП_1 могу выделить следующие риски: операционные риски связаны с возможными очередями из-за расположения в центре города. Рекомендую улучшить систему электронной очереди и увеличить количество операционистов в часы пик.")
        elif "инсайтов о рисках" in last_message:
            return AIMessage(content="1. Операционный риск: очереди (Уровень: средний)\n- Рекомендация: Внедрить систему предварительной записи\n- Срок: 1 месяц\n\n2. Репутационный риск: негативные отзывы (Уровень: высокий)\n- Рекомендация: Обучение персонала, работа с обратной связью\n- Срок: 2 недели")
        elif "отчет о рисках" in last_message:
            return AIMessage(content="# Отчет о рисках отделения ВСП_1\n\n## Резюме\nОтделение демонстрирует средний уровень операционных рисков и высокий уровень репутационных рисков.\n\n## Детализация рисков\n1. Операционный риск: очереди в часы пик\n2. Репутационный риск: негативные отзывы клиентов\n\n## Рекомендации\n- Внедрить систему предварительной записи\n- Провести обучение персонала по работе с клиентами\n\n## Приоритеты\n1. Срочное обучение персонала (2 недели)\n2. Доработка системы электронной очереди (1 месяц)")
        else:
            return AIMessage(content="Понял ваш запрос. Продолжаем анализ.")

# Инициализация модели LLM
try:
    # Пробуем инициализировать реальную модель, если не в мок-режиме
    if not USE_MOCK_LLM:
        # Эти API ключи уже не действительны, замените на свои
        # или используйте переменные окружения для безопасности
        from openai import OpenAI
        import os
        
        # Считываем ключ API из переменной окружения или используем резервный ключ
        api_key = "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" #os.environ.get("OPENROUTER_API_KEY", "")

        llm = ChatOpenAI(
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            model_name="qwen/qwen3-4b:free"
        )
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        print("Инициализирована реальная LLM модель")
    else:
        # Используем мок-модель для тестирования
        llm = MockLLM()
        client = None
        print("Инициализирована мок-модель LLM для тестирования")
        
except Exception as e:
    # В случае ошибки инициализации используем мок-модель
    print(f"Ошибка при инициализации LLM: {e}")
    print("Переключаемся на мок-модель...")
    llm = MockLLM()
    client = None

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
    attempts: int  # Добавлен счетчик попыток

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
            self.data_dir.mkdir(parents=True, exist_ok=True)
            print(f"Создана директория для данных: {self.data_dir}")
        
        # Устанавливаем пути к файлам. Сначала пробуем найти их в директории скрипта,
        # затем в текущей директории, если директория с данными не существует
        self.companies_file = None
        self.reviews_file = None
        
        # Пробуем найти файлы в разных местах
        possible_paths = [
            self.data_dir / "companies.json",  # В папке data относительно скрипта
            Path("companies.json"),            # В текущей директории
            Path(__file__).parent / "companies.json"  # В директории скрипта
        ]
        
        for path in possible_paths:
            if path.exists():
                self.companies_file = path
                break
        
        possible_paths = [
            self.data_dir / "reviews.json",    # В папке data относительно скрипта
            Path("reviews.json"),              # В текущей директории
            Path(__file__).parent / "reviews.json"  # В директории скрипта
        ]
        
        for path in possible_paths:
            if path.exists():
                self.reviews_file = path
                break
        
        # Если файлы не найдены, устанавливаем пути по умолчанию
        if not self.companies_file:
            self.companies_file = self.data_dir / "companies.json"
            print(f"Файл companies.json не найден, будет использован путь: {self.companies_file}")
        
        if not self.reviews_file:
            self.reviews_file = self.data_dir / "reviews.json"
            print(f"Файл reviews.json не найден, будет использован путь: {self.reviews_file}")
        
        # Загружаем данные при инициализации
        self._load_data()
    
    def _load_data(self):
        """Загрузка данных из JSON файлов"""
        try:
            # Загрузка данных о компаниях
            if self.companies_file and self.companies_file.exists():
                with open(self.companies_file, 'r', encoding='utf-8') as f:
                    self.companies = json.load(f)
                print(f"Загружены данные о {len(self.companies)} отделениях из {self.companies_file}")
            else:
                # Данные не найдены, создаем тестовые
                print(f"Файл с отделениями не найден, создаем тестовые данные")
                self.companies = [
                    {
                        "id": 18436,
                        "number": 18436,
                        "name": "ВСП_1",
                        "address": "ул. Тверская, 12",
                        "geo_position": {
                            "latitude": 55.763305,
                            "longitude": 37.609371
                        }
                    },
                    {
                        "id": 59271,
                        "number": 59271,
                        "name": "ВСП_2",
                        "address": "пр. Мира, 25",
                        "geo_position": {
                            "latitude": 55.779155,
                            "longitude": 37.631936
                        }
                    }
                ]
                # Сохраняем тестовые данные, если возможно
                if self.companies_file:
                    try:
                        with open(self.companies_file, 'w', encoding='utf-8') as f:
                            json.dump(self.companies, f, ensure_ascii=False, indent=2)
                        print(f"Создан тестовый файл {self.companies_file}")
                    except Exception as e:
                        print(f"Не удалось создать файл компаний: {e}")
            
            # Загрузка отзывов
            if self.reviews_file and self.reviews_file.exists():
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    self.reviews = json.load(f)
                print(f"Загружены данные о {len(self.reviews)} отзывах из {self.reviews_file}")
            else:
                # Данные не найдены, создаем тестовые
                print(f"Файл с отзывами не найден, создаем тестовые данные")
                self.reviews = [
                    {
                        "date": "3/15/2025",
                        "rate": 1,
                        "comment": "Ужасное обслуживание! Очередь двигалась медленно, сотрудники грубили.",
                        "expertise": 8,
                        "tone": "Негативный",
                        "orgId": 18436
                    },
                    {
                        "date": "5/14/2025",
                        "rate": 4,
                        "comment": "Хорошее отделение, но вечно не хватает стульев в зоне ожидания.",
                        "expertise": 9,
                        "tone": "Смешанный",
                        "orgId": 18436
                    },
                    {
                        "date": "4/22/2025",
                        "rate": 5,
                        "comment": "Отличный сервис! Менеджер помог оформить кредит на выгодных условиях.",
                        "expertise": 12,
                        "tone": "Позитивный",
                        "orgId": 59271
                    }
                ]
                # Сохраняем тестовые данные, если возможно
                if self.reviews_file:
                    try:
                        with open(self.reviews_file, 'w', encoding='utf-8') as f:
                            json.dump(self.reviews, f, ensure_ascii=False, indent=2)
                        print(f"Создан тестовый файл {self.reviews_file}")
                    except Exception as e:
                        print(f"Не удалось создать файл отзывов: {e}")
                
        except json.JSONDecodeError as e:
            print(f"Ошибка при чтении JSON файлов: {e}")
            # Создаем пустые массивы в случае ошибки
            self.companies = []
            self.reviews = []
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            # Создаем пустые массивы в случае ошибки
            self.companies = []
            self.reviews = []
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Получить список всех отделений"""
        return self.companies
    
    def get_vsp_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Найти отделение по названию
        
        Args:
            name: Название отделения (полное или частичное)
            
        Returns:
            Информация об отделении или None, если отделение не найдено
        """
        if not name:
            return None
            
        name = name.lower().strip()
        for vsp in self.companies:
            if name in vsp.get('name', '').lower():
                return vsp
        return None
    
    def get_vsp_by_id(self, vsp_id: int) -> Optional[Dict[str, Any]]:
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
    
    def get_reviews_by_vsp_id(self, vsp_id: int) -> List[Dict[str, Any]]:
        """
        Получить отзывы для конкретного отделения по ID
        
        Args:
            vsp_id: ID отделения
            
        Returns:
            Список отзывов для отделения
        """
        return [review for review in self.reviews if review.get('orgId') == vsp_id]
    
    def get_reviews_by_vsp_name(self, vsp_name: str) -> List[Dict[str, Any]]:
        """
        Получить отзывы для конкретного отделения по названию
        
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
        if vsp_id is None:
            return []
            
        return self.get_reviews_by_vsp_id(vsp_id)
    
    def get_average_rating_by_vsp_id(self, vsp_id: int) -> float:
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
            
        # Исправлено: используем 'rate' вместо 'rating'
        ratings = [review.get('rate', 0) for review in reviews if isinstance(review.get('rate'), (int, float))]
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
        if vsp_id is None:
            return 0.0
            
        return self.get_average_rating_by_vsp_id(vsp_id)

# Создаем экземпляр инструмента для работы с данными компаний
vsp_data_tool = VspDataTool()

# Функции для работы с компаниями в графе агента
def get_vsp_info(state: GraphState) -> GraphState:
    """Получение информации о отделении из JSON файла"""
    messages = state["messages"]
    vsp_name = state.get("vsp_name", "")
    
    # Добавить счетчик попыток
    attempts = state.get("attempts", 0) + 1
    if attempts > 3:
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content="Превышено количество попыток. Завершаю работу.")],
            "current_task": "end",
            "attempts": attempts
        }
    
    if not vsp_name:
        # Если имя отделения не указано, запросим его у пользователя
        messages.append(HumanMessage(content="Укажите название отделения для поиска информации"))
        response = llm.invoke(messages)
        messages.append(response)
        vsp_name = response.content.strip()
        state["vsp_name"] = vsp_name
    
    # Получаем информацию о отделении
    vsp_info = vsp_data_tool.get_vsp_by_name(vsp_name)
    
    if vsp_info:
        messages.append(AIMessage(content=f"Найдена информация о отделении {vsp_name}"))
        
        return {
            **state,
            "messages": messages,
            "vsp_name": vsp_name,
            "vsp_info": vsp_info,
            "current_task": "get_vsp_reviews",
            "attempts": attempts
        }
    else:
        messages.append(AIMessage(content=f"Отделение {vsp_name} не найдено. Попробуйте другое название."))
        
        return {
            **state,
            "messages": messages,
            "current_task": "get_vsp_info",  # Повторяем этот шаг
            "attempts": attempts
        }

def get_vsp_reviews(state: GraphState) -> GraphState:
    """Получение отзывов о отделении из JSON файла"""
    messages = state["messages"]
    vsp_name = state.get("vsp_name", "")
    vsp_info = state.get("vsp_info", None)
    
    if not vsp_info:
        return {
            **state,
            "messages": messages,
            "current_task": "get_vsp_info"  # Возвращаемся к получению информации о отделении
        }
    
    # Получаем отзывы о отделении
    vsp_id = vsp_info.get("id")
    if vsp_id is not None:
        vsp_reviews = vsp_data_tool.get_reviews_by_vsp_id(vsp_id)
    else:
        vsp_reviews = vsp_data_tool.get_reviews_by_vsp_name(vsp_name)
    
    if vsp_reviews:
        # Добавляем расчет среднего рейтинга
        total_rating = sum(review.get('rate', 0) for review in vsp_reviews if isinstance(review.get('rate'), (int, float)))
        avg_rating = total_rating / len(vsp_reviews) if vsp_reviews else 0
        
        messages.append(AIMessage(content=f"Получено {len(vsp_reviews)} отзывов о отделении {vsp_name}. "
                                 f"Средний рейтинг: {avg_rating:.1f} из 5."))
        
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

def analyze_tone_distribution(reviews):
    """Анализ распределения тональности отзывов"""
    tones = {}
    for review in reviews:
        tone = review.get('tone', 'Не указано')
        tones[tone] = tones.get(tone, 0) + 1
    
    return tones

def analyze_vsp_data(state: GraphState) -> GraphState:
    """Анализ данных о отделении и отзывов"""
    messages = state["messages"]
    vsp_info = state.get("vsp_info", {})
    vsp_reviews = state.get("vsp_reviews", [])
    
    # Базовый анализ отзывов перед запросом к LLM
    summary = ""
    if vsp_reviews:
        # Средний рейтинг
        avg_rating = sum(review.get('rate', 0) for review in vsp_reviews if isinstance(review.get('rate'), (int, float))) / len(vsp_reviews)
        
        # Распределение по тональности
        tone_distribution = analyze_tone_distribution(vsp_reviews)
        
        summary = f"""
        Средний рейтинг: {avg_rating:.2f}/5
        Всего отзывов: {len(vsp_reviews)}
        
        Распределение по тональности:
        {", ".join([f"{tone}: {count}" for tone, count in tone_distribution.items()])}
        """
    
    # Запрос к LLM для анализа данных о отделении и отзывов
    analysis_prompt = f"""
    Проанализируй следующую информацию о отделении банка на предмет рисков:
    
    Информация о отделении:
    {json.dumps(vsp_info, ensure_ascii=False, indent=2)}
    """
    
    if vsp_reviews:
        analysis_prompt += f"""
        
        Краткая статистика отзывов:
        {summary}
        
        Примеры отзывов:
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
    vsp_name = state.get("vsp_name", "")
    vsp_info = state.get("vsp_info", {})
    
    messages.append(HumanMessage(content=f"""
    Создай структурированный отчет о рисках отделения "{vsp_name}" на основе:
    - Анализа: {state['analysis_result']}
    - Рекомендаций: {' '.join(state['recommendations'][:3])}
    
    Формат отчета:
    1. Резюме (основные риски)
    2. Детализация по каждому риску
    3. Рекомендации по устранению
    4. Приоритеты действий
    5. Критические риски (если есть)
    
    Пожалуйста, сделай отчет структурированным и легким для восприятия.
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
    current_task = state.get("current_task", "get_vsp_info")
    
    # Если достигнут предел попыток
    if state.get("attempts", 0) > 3:
        return "end"
    
    # Мэппинг текущей задачи на следующую
    tasks_map = {
        "get_vsp_info": "get_vsp_reviews",
        "get_vsp_reviews": "analyze_vsp_data",
        "analyze_vsp_data": "generate_insights",
        "generate_insights": "create_report",
        "create_report": "end",
        "end": "end"
    }
    
    # Логика определения следующего шага с особыми случаями
    if current_task == "get_vsp_info" and not state.get("vsp_info"):
        return "get_vsp_info"  # Если информация о отделении не найдена, повторяем запрос
    
    # Возвращаем следующую задачу из мэппинга или переходим к завершению
    return tasks_map.get(current_task, "end")

# Создание графа для работы с данными о компаниях
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
            "analyze_vsp_data": "analyze_vsp_data",
            "get_vsp_info": "get_vsp_info",
            "end": END
        }
    )
    
    # ИСПРАВЛЕНИЕ: добавлены все возможные переходы из узла analyze_vsp_data
    workflow.add_conditional_edges(
        "analyze_vsp_data",
        should_continue,
        {
            "generate_insights": "generate_insights",
            "analyze_vsp_data": "analyze_vsp_data",  # Возможность повторить анализ
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "generate_insights",
        should_continue,
        {
            "create_report": "create_report",
            "generate_insights": "generate_insights",  # Возможность повторить генерацию
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "create_report",
        should_continue,
        {
            "end": END
        }
    )
    
    # Установка начальной точки
    workflow.set_entry_point("get_vsp_info")
    
    return workflow.compile()


# Функция для запуска рабочего процесса с данными о отделении
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
        "final_report": "",
        "attempts": 0
    }
    
    try:
        # Если пользователь указал название отделения, попробуем найти его сразу
        if vsp_name:
            vsp_info = vsp_data_tool.get_vsp_by_name(vsp_name)
            if vsp_info:
                initial_state["vsp_info"] = vsp_info
                print(f"Найдена информация о отделении {vsp_name}")
            else:
                print(f"Отделение '{vsp_name}' не найдено в базе данных. Проверим другие отделения.")
        
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
    except Exception as e:
        print(f"Ошибка при выполнении рабочего процесса: {e}")
        
        # Подробный вывод стека ошибки для отладки
        traceback.print_exc()
        
        # Создаем базовый отчет даже при ошибке
        if vsp_name:
            vsp_info = vsp_data_tool.get_vsp_by_name(vsp_name)
            if vsp_info:
                vsp_reviews = vsp_data_tool.get_reviews_by_vsp_id(vsp_info.get("id", 0))
                avg_rating = 0
                if vsp_reviews:
                    ratings = [r.get('rate', 0) for r in vsp_reviews if isinstance(r.get('rate'), (int, float))]
                    avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                print("\n=== Аварийный отчет о отделении ===")
                print(f"Отделение: {vsp_name}")
                print(f"Адрес: {vsp_info.get('address', 'Не указан')}")
                print(f"Количество отзывов: {len(vsp_reviews)}")
                print(f"Средний рейтинг: {avg_rating:.1f}/5")
                
                # Анализируем тональность отзывов
                tones = {}
                for review in vsp_reviews:
                    tone = review.get('tone', 'Не указано')
                    tones[tone] = tones.get(tone, 0) + 1
                
                print("Распределение тональности отзывов:")
                for tone, count in tones.items():
                    print(f"- {tone}: {count}")
                
                # Создаем базовый отчет о рисках
                print("\n--- Базовый отчет о рисках ---")
                if avg_rating < 3:
                    print("Высокий репутационный риск: низкий средний рейтинг отзывов")
                elif avg_rating < 4:
                    print("Средний репутационный риск: средний рейтинг отзывов")
                else:
                    print("Низкий репутационный риск: высокий рейтинг отзывов")
                
                # Ищем потенциальные операционные риски в отзывах
                operational_risks = []
                for review in vsp_reviews:
                    text = review.get('comment', '').lower()
                    if any(word in text for word in ['очередь', 'долго', 'ждать']):
                        operational_risks.append("очереди")
                    if any(word in text for word in ['система', 'сбой', 'не работает']):
                        operational_risks.append("технические сбои")
                
                if operational_risks:
                    print("Обнаружены операционные риски:")
                    for risk in set(operational_risks):
                        print(f"- {risk}")
                else:
                    print("Явных операционных рисков не обнаружено")
        
        return None

if __name__ == "__main__":
    print("=== Анализатор банковских рисков ===")
    try:
        print("Доступные отделения:")
        for i, vsp in enumerate(vsp_data_tool.get_all_companies()):
            print(f"{i+1}. {vsp['name']} - {vsp['address']}")
    except Exception as e:
        print(f"Ошибка при загрузке списка отделений: {e}")
    
    print("\nВыберите опцию:")
    print("1. Ввести название отделения")
    print("2. Выбрать отделение из списка")
    print("3. Запустить в демо-режиме")
    
    choice = input("Ваш выбор (1-3): ").strip()
    
    if choice == "1":
        vsp_name = input("Введите название отделения: ").strip()
        run_vsp_data_workflow(vsp_name if vsp_name else None)
    elif choice == "2":
        try:
            idx = int(input("Введите номер отделения из списка: ").strip()) - 1
            companies = vsp_data_tool.get_all_companies()
            if 0 <= idx < len(companies):
                vsp_name = companies[idx]["name"]
                print(f"Выбрано отделение: {vsp_name}")
                run_vsp_data_workflow(vsp_name)
            else:
                print("Неверный номер отделения")
        except ValueError:
            print("Ошибка ввода. Необходимо указать номер отделения.")
        except Exception as e:
            print(f"Ошибка при выборе отделения: {e}")
    else:
        # Демо-режим - используется мок и первое доступное отделение
        print("Запуск в демо-режиме...")
        #global USE_MOCK_LLM
        USE_MOCK_LLM = True
        
        companies = vsp_data_tool.get_all_companies()
        if companies:
            vsp_name = companies[0]["name"]
            print(f"Демонстрация на примере отделения: {vsp_name}")
            run_vsp_data_workflow(vsp_name)
        else:
            print("Не найдены данные об отделениях для демонстрации")
            run_vsp_data_workflow("ВСП_1")
