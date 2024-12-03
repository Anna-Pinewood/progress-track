FROM python:3.10-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ /app/src/

# Set proper permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py"]
