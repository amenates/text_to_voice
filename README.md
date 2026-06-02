### Виртуальное окружение
```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
venv\Scripts\activate

# Деактивация виртуального окружения
venv\Scripts\deactivate
```

### Зависимости проекта
```bash
# Установка зависимостей из файла requirements.txt
pip install -r requirements.txt

# Обновление файла requirements.txt
pip freeze > requirements.txt
```