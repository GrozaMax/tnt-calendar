"""
Менеджер локализации
"""
import json
from pathlib import Path
from typing import Dict, Any


class LocaleManager:
    """Менеджер для работы с переводами"""
    
    def __init__(self):
        self.locales: Dict[str, Dict[str, Any]] = {}
        self.locales_dir = Path(__file__).parent
        self._load_locales()
    
    def _load_locales(self):
        """Загрузка всех файлов локализации"""
        for locale_file in self.locales_dir.glob('*.json'):
            lang_code = locale_file.stem
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.locales[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading locale {lang_code}: {e}")
    
    def get(self, key: str, lang: str = 'ru', **kwargs) -> str:
        """
        Получить перевод по ключу.
        
        Args:
            key: Ключ перевода в формате 'section.subsection.key'
            lang: Код языка
            **kwargs: Параметры для форматирования
        
        Returns:
            Переведённый текст
        
        Example:
            get('menu.main', 'ru')
            get('booking.success', 'en', name='John')
        """
        # Если язык не найден, используем русский
        if lang not in self.locales:
            lang = 'ru'
        
        # Навигация по вложенным ключам
        keys = key.split('.')
        value = self.locales.get(lang, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                return key
        
        # Форматирование с параметрами
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        
        return value if isinstance(value, str) else key


# Глобальный экземпляр
_locale_manager = LocaleManager()


def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
    """
    Удобная функция для получения перевода.
    
    Args:
        key: Ключ перевода
        lang: Код языка
        **kwargs: Параметры для форматирования
    """
    return _locale_manager.get(key, lang, **kwargs)

