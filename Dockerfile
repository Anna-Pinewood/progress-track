FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем только src директорию
COPY src/ /app/src/

EXPOSE 8501

# Команда по умолчанию (может быть переопределена в docker-compose)
CMD ["streamlit", "run", "src/main.py"]