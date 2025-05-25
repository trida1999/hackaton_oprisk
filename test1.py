from typing import Dict, Any

if __name__ == "__main__":
    # Глобальный кеш в памяти для данных из tool
    FILE_CACHE: Dict[str, Any] = {}

    FILE_CACHE["key1"]="abc"

    print(f"in cache: {FILE_CACHE["key1"]}")