from datetime import timedelta
from pathlib import Path
import random
import streamlit as st
from consts import QUOTES_FILE


def load_quotes():
    """Load quotes from the quotes.txt file"""
    quotes_path = Path(
        "/app/data") / QUOTES_FILE  # Updated path to mounted volume
    try:
        with open(quotes_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip() if line.strip()]
    except FileNotFoundError:
        return ["Файл с цитатами не найден"]


def get_random_quote():
    """Get a random quote from the loaded quotes"""
    quotes = load_quotes()
    return random.choice(quotes)


# Moscow time instead of UTC
def adjust_time(timestamp):
    return timestamp + timedelta(hours=3)


def extract_group(description):
    if ":" in description and description.split(":")[0].strip().isupper():
        return description.split(":")[0].strip(), description.split(":", 1)[1].strip()
    return "ДРУГОЕ", description


WEEKDAYS_RU = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье'
}


def format_date(date_obj):
    """Format date as DD.MM.YYYY, Weekday in Russian"""
    weekday = WEEKDAYS_RU[date_obj.weekday()]
    return f"{date_obj.strftime('%d.%m.%Y')}, {weekday}"
