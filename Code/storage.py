import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class JsonStorage:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()
    
    def _ensure_files(self):
        """Создание файлов если их нет"""
        files = ["users.json", "movies.json", "user_movies.json"]
        for file in files:
            file_path = self.storage_dir / file
            if not file_path.exists():
                file_path.write_text("[]", encoding='utf-8')
    
    def _read_file(self, filename: str) -> List[Dict[str, Any]]:
        """Чтение данных из файла"""
        file_path = self.storage_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_file(self, filename: str, data: List[Dict[str, Any]]):
        """Запись данных в файл"""
        file_path = self.storage_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_all(self, entity_type: str) -> List[Dict[str, Any]]:
        return self._read_file(f"{entity_type}.json")
    
    def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        data = self.get_all(entity_type)
        for item in data:
            if item.get("id") == entity_id:
                return item
        return None
    
    def create(self, entity_type: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        data = self.get_all(entity_type)
        data.append(entity_data)
        self._write_file(f"{entity_type}.json", data)
        return entity_data
    
    def update(self, entity_type: str, entity_id: str, entity_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = self.get_all(entity_type)
        for i, item in enumerate(data):
            if item.get("id") == entity_id:
                data[i] = entity_data
                self._write_file(f"{entity_type}.json", data)
                return entity_data
        return None
    
    def delete(self, entity_type: str, entity_id: str) -> bool:
        data = self.get_all(entity_type)
        new_data = [item for item in data if item.get("id") != entity_id]
        if len(new_data) < len(data):
            self._write_file(f"{entity_type}.json", new_data)
            return True
        return False
    
    def query(self, entity_type: str, **filters) -> List[Dict[str, Any]]:
        data = self.get_all(entity_type)
        result = []
        for item in data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result
