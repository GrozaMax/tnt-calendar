# Тесты TNT Calendar

Структура тестов для проекта TNT Calendar.

## Структура

```
tests/
├── __init__.py
├── conftest.py              # Общие фикстуры и настройки
├── test_models.py           # Тесты моделей данных
├── test_repositories.py     # Тесты репозиториев
├── test_services.py         # Тесты сервисов
└── test_api.py             # Тесты веб-API
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### С покрытием кода
```bash
pytest --cov=src --cov=web --cov-report=html
```

### Конкретный файл
```bash
pytest tests/test_models.py
```

### Конкретный тест
```bash
pytest tests/test_models.py::TestUser::test_create_user
```

### С подробным выводом
```bash
pytest -v
```

### Только быстрые тесты (без медленных)
```bash
pytest -m "not slow"
```

## Категории тестов

- `unit` - Юнит-тесты (быстрые, изолированные)
- `integration` - Интеграционные тесты
- `api` - Тесты API
- `slow` - Медленные тесты

## Фикстуры

### Базовые
- `db_engine` - Тестовая БД в памяти
- `db_session` - Сессия БД для теста
- `user_repo`, `workout_repo`, `booking_repo` - Репозитории

### Тестовые данные
- `test_admin` - Тестовый администратор
- `test_trainer` - Тестовый тренер
- `test_athlete` - Тестовый атлет
- `test_workout` - Тестовая тренировка
- `test_booking` - Тестовая запись

## Покрытие кода

После запуска с `--cov-report=html` отчет будет в `htmlcov/index.html`:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Написание новых тестов

### Пример теста модели

```python
@pytest.mark.asyncio
async def test_my_feature(db_session, test_user):
    """Описание теста"""
    # Arrange
    ...
    
    # Act
    result = await some_function()
    
    # Assert
    assert result == expected
```

### Пример теста API

```python
@pytest.mark.asyncio
async def test_api_endpoint(auth_headers_admin):
    """Тест API endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/endpoint",
            headers=auth_headers_admin
        )
    
    assert response.status_code == 200
```

## CI/CD

Тесты автоматически запускаются при:
- Push в репозиторий
- Pull Request
- Перед деплоем

## Рекомендации

1. **Всегда пишите тесты** для новых фич
2. **Используйте фикстуры** для повторяющихся данных
3. **Именуйте тесты описательно** - `test_что_должно_произойти_когда_условие`
4. **Один тест = одна проверка**
5. **Используйте AAA паттерн**: Arrange, Act, Assert
6. **Покрытие кода > 80%** для критичных частей

## Отладка тестов

### Запуск с точкой останова
```bash
pytest --pdb
```

### Показать print() в тестах
```bash
pytest -s
```

### Запустить последние упавшие тесты
```bash
pytest --lf
```

## Проблемы и решения

### Тесты не находятся
- Проверьте, что файлы начинаются с `test_`
- Проверьте `pytest.ini`

### Ошибки асинхронности
- Убедитесь, что используете `@pytest.mark.asyncio`
- Проверьте `pytest-asyncio` установлен

### БД тесты падают
- Проверьте фикстуры в `conftest.py`
- Убедитесь, что `aiosqlite` установлен

