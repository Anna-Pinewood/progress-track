import json
import os
from pathlib import Path
import streamlit as st
from datetime import datetime
from datetime import date
import database.handlers as handlers
from streamlit_extras.let_it_rain import rain
import random
from streamlit_extras.stateful_button import button
import time

st.set_page_config(page_title="Трекер достижений")

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0
if 'expanded_groups' not in st.session_state:
    st.session_state.expanded_groups = set()
if 'show_animation' not in st.session_state:
    st.session_state.show_animation = None
if 'group_colors' not in st.session_state:
    st.session_state.group_colors = {}
if 'last_level' not in st.session_state:
    st.session_state.last_level = None
if 'next_emoji_level' not in st.session_state:
    st.session_state.next_emoji_level = random.randint(5, 10)
if 'current_emoji' not in st.session_state:
    st.session_state.current_emoji = "🏆"

# Update the color palette with new colors
GROUP_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', 
                '#FFA07A', '#FF69B4', '#DDA0DD']  # Added orange, pink, and purple

def get_level_emoji(level):
    # Update next_emoji_level if we reached it
    if level >= st.session_state.next_emoji_level:
        emojis = ["⭐", "🚲", "🎨", "⛰️", "🗻", "🌋", "🎆", "🎯", "🎮", "🏔️"]
        st.session_state.current_emoji = random.choice(emojis)
        # Set next change 5-10 levels from now
        st.session_state.next_emoji_level = level + random.randint(5, 10)
    
    return st.session_state.current_emoji

def extract_group(description):
    if ":" in description and description.split(":")[0].strip().isupper():
        return description.split(":")[0].strip(), description.split(":", 1)[1].strip()
    return "ДРУГОЕ", description

def render_flag(points, color):
    base_height = 40
    pole_height = base_height + points
    return f"""
        <div style="position: relative; width: 30px; height: {pole_height}px; margin: 5px;">
            <div style="position: absolute; left: 15px; top: 0; width: 2px; height: {pole_height}px; background-color: #666;">
            </div>
            <div style="position: absolute; left: 17px; top: 5px; width: 0; height: 0;
                        border-left: {20}px solid {color};
                        border-top: 10px solid transparent;
                        border-bottom: 10px solid transparent;">
            </div>
        </div>
    """

MOTIVATION_MESSAGES = {
    'small': [  # for points <= 15
        "Так держать! Где фокус – там и рост.",
        "Отличный шаг вперед! Путь в тысячу ли начинается с первого шага.",
        "Молодец! Постоянство – ключ к совершенству.",
        "Хороший результат! Маленькие победы создают большой успех.",
        "Продолжай в том же духе! Капля за каплей формирует океан."
    ],
    'medium': [  # for points <= 30
        "Впечатляющий результат! Успех – это лестница, по которой не взойдешь, держа руки в карманах.",
        "Замечательная работа! Дисциплина – мост между целями и достижениями.",
        "Отличное достижение! Твоя настойчивость вдохновляет.",
        "Прекрасный прогресс! Каждый день – новая возможность стать лучше.",
        "Великолепно! Успех приходит к тем, кто действует."
    ],
    'large': [  # for points > 30
        "Выдающееся достижение! Мечты не работают, пока не работаешь ты.",
        "Потрясающий результат! Твой потенциал безграничен.",
        "Невероятная работа! Сложности – это возможности в рабочей одежде.",
        "Грандиозно! Большие достижения состоят из маленьких побед.",
        "Феноменально! Ты доказываешь, что невозможное возможно."
    ]
}

def show_achievement_animation(points):
    if points <= 15:
        st.balloons()
        message = random.choice(MOTIVATION_MESSAGES['small'])
        st.success(message)
    elif points <= 30:
        st.balloons()
        message = random.choice(MOTIVATION_MESSAGES['medium'])
        rain(emoji="💎", font_size=54, falling_speed=2, animation_length=1)
        st.success(message)
    else:
        st.balloons()
        message = random.choice(MOTIVATION_MESSAGES['large'])
        rain(emoji="💎", font_size=54, falling_speed=2, animation_length=1)
        st.success(message)

def show_level_up_animation(new_level):
    with st.empty():
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; align-items: center; height: 200px;">
                <div style="text-align: center; background: linear-gradient(45deg, #FFD700, #FFA500); 
                           padding: 20px; border-radius: 10px; box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);">
                    <h1 style="color: white; font-size: 2.5em; margin-bottom: 10px;">🎉 НОВЫЙ УРОВЕНЬ! 🎉</h1>
                    <h2 style="color: white; font-size: 3em;">{new_level}</h2>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        rain(emoji="⭐", font_size=54, falling_speed=5, animation_length="2s")
        time.sleep(2)

def render_level_progress(level_info):
    progress = level_info['points_in_level'] / 60
    return f"""
        <div style="position: fixed; top: 70px; right: 10px; background: white; 
                    padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000;">
            <div style="text-align: center; margin-bottom: 10px;">
                <span style="font-size: 2em; font-weight: bold; color: #4CAF50;">{get_level_emoji(level_info['level'])} {level_info['level']}</span>
                <br/>
                <span style="font-size: 0.9em; color: #666;">уровень</span>
            </div>
            <div style="width: 150px; height: 10px; background: #eee; border-radius: 5px; overflow: hidden;">
                <div style="width: {progress * 100}%; height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); 
                            transition: width 0.5s ease-in-out;">
                </div>
            </div>
            <div style="text-align: center; margin-top: 5px; font-size: 0.9em; color: #666;">
                {level_info['points_in_level']}/60 очков
            </div>
        </div>
    """

def login_form():
    with st.form("login_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        col1, col2 = st.columns(2)
        with col1:
            login_submit = st.form_submit_button("Войти")
        with col2:
            register_submit = st.form_submit_button("Зарегистрироваться")

        if login_submit and username and password:
            user_id = handlers.verify_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.success("Успешный вход!")
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль")

        if register_submit and username and password:
            success, message = handlers.register_user(username, password)
            if success:
                st.success(message)
            else:
                st.error(message)

def main_app():
    st.title("Трекер достижений")

    # Get and display level info
    level_info = handlers.get_user_level_info(st.session_state.user_id)
    st.markdown(render_level_progress(level_info), unsafe_allow_html=True)

    # Check for level up
    if st.session_state.last_level is None:
        st.session_state.last_level = level_info['level']
    elif level_info['level'] > st.session_state.last_level:
        show_level_up_animation(level_info['level'])
        st.session_state.last_level = level_info['level']

    if st.button("Выйти"):
        st.session_state.user_id = None
        st.rerun()

    with st.form(f"achievement_form_{st.session_state.form_key}"):
        description = st.text_input("Ваш вклад в ваши цели", key=f"desc_{st.session_state.form_key}")
        points = st.slider("Оценка вклада", min_value=5, max_value=50, value=15, key=f"points_{st.session_state.form_key}")
        submitted = st.form_submit_button("Добавить достижение")

    if submitted and description:
        handlers.add_achievement(description, points, st.session_state.user_id)
        st.session_state.show_animation = points
        st.session_state.form_key += 1
        st.rerun()

    # Show animation if needed
    if st.session_state.show_animation is not None:
        show_achievement_animation(st.session_state.show_animation)
        st.session_state.show_animation = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Удалить все достижения"):
            handlers.delete_all_achievements(st.session_state.user_id)
            st.warning("Все достижения удалены!")
            st.session_state.expanded_groups = set()
            st.rerun()

    with col2:
        if st.button("📄 Сгенерировать отчёт"):
            achievements = handlers.get_achievements(st.session_state.user_id)
            groups = {}

            for achievement in achievements:
                group_name, achievement_text = extract_group(achievement[1])
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append((achievement_text, achievement[2]))

            text_content = "Мои достижения:\n\n"

            # Calculate total points for each group
            for group_name in sorted(groups.keys()):
                group_achievements = groups[group_name]
                total_points = sum(points for _, points in group_achievements)
                text_content += f"{group_name} (Всего баллов: {total_points}):\n"
                for achievement_text, points in group_achievements:
                    text_content += f"  - {achievement_text} ({points} pts)\n"
                text_content += "\n"

            with st.expander("Текст для копирования", expanded=True):
                st.code(text_content, language=None)
                st.button("Копировать", type="primary",
                         on_click=lambda: st.write(
                             f'<script>navigator.clipboard.writeText(`{text_content}`)</script>',
                             unsafe_allow_html=True
                         ))

    achievements = handlers.get_achievements(st.session_state.user_id)

    # Group achievements
    groups = {}
    color_index = 0
    available_colors = set(GROUP_COLORS)

    # Remove already used colors from available_colors
    for color in st.session_state.group_colors.values():
        if color in available_colors:
            available_colors.remove(color)

    for achievement in achievements:
        group_name, achievement_text = extract_group(achievement[1])
        if group_name not in groups:
            groups[group_name] = []
            # If group doesn't have a color, assign a random one from available colors
            if group_name not in st.session_state.group_colors:
                if available_colors:
                    new_color = random.choice(list(available_colors))
                    available_colors.remove(new_color)
                    st.session_state.group_colors[group_name] = new_color
                else:
                    # If no colors available, pick a random one from the full palette
                    st.session_state.group_colors[group_name] = random.choice(GROUP_COLORS)
        groups[group_name].append((achievement[0], achievement_text, achievement[2], achievement[3]))

    # Clean up deleted groups from session state
    existing_groups = set(groups.keys())
    deleted_groups = set(st.session_state.group_colors.keys()) - existing_groups
    for group in deleted_groups:
        del st.session_state.group_colors[group]

    # Display grouped achievements using stored colors
    for group_name, group_achievements in groups.items():
        color = st.session_state.group_colors[group_name]

        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            st.markdown(f"""
                <div style="width: 20px; height: 20px; background-color: {color};
                           border-radius: 50%; margin-top: 10px;">
                </div>
            """, unsafe_allow_html=True)
        with col2:
            is_expanded = st.checkbox(
                f"{group_name} ({len(group_achievements)})",
                key=f"group_{group_name}",
                value=group_name in st.session_state.expanded_groups
            )

        if is_expanded:
            st.session_state.expanded_groups.add(group_name)
            for achievement_id, text, points, created_at in group_achievements:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{text}**")
                    st.caption(f"Добавлено: {created_at}")
                with col2:
                    st.markdown(render_flag(points, color), unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️", key=f"delete_{achievement_id}"):
                        handlers.delete_achievement(achievement_id, st.session_state.user_id)
                        remaining_achievements = [a for a in group_achievements if a[0] != achievement_id]
                        if not remaining_achievements:
                            st.session_state.expanded_groups.remove(group_name)
                        st.rerun()
        else:
            st.session_state.expanded_groups.discard(group_name)

    def create_daily_journey_html(achievements):
            """Create an HTML string for the daily journey visualization."""
            html = """
            <div id="daily-journey" style="font-family: sans-serif; padding: 20px;">
                <script>
                    const achievements = ACHIEVEMENTS_PLACEHOLDER;

                    function createJourney() {
                        const container = document.getElementById('daily-journey');
                        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');

                        const CIRCLE_BASE_SIZE = 30;
                        const CIRCLE_MAX_SIZE = 60;
                        const MIN_SPACING = 120;
                        const CENTER_X = 600;
                        const TEXT_WIDTH = 400; // Maximum width for text
                        const CHARS_PER_LINE = 50; // Approximate characters per line

                        // Calculate positions and sizes
                        const journeyItems = achievements.map((achievement, index) => {
                            const radius = CIRCLE_BASE_SIZE + (achievement.points / 50) * (CIRCLE_MAX_SIZE - CIRCLE_BASE_SIZE);
                            const y = index * MIN_SPACING + radius + 40;
                            return { ...achievement, y, radius };
                        });

                        const height = journeyItems.length > 0
                            ? journeyItems[journeyItems.length - 1].y + CIRCLE_MAX_SIZE
                            : 200;

                        // Set SVG attributes
                        svg.setAttribute('width', '100%');
                        svg.setAttribute('height', height);
                        svg.style.maxWidth = '800px';

                        // Create dotted line
                        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                        line.setAttribute('x1', CENTER_X);
                        line.setAttribute('y1', '20');
                        line.setAttribute('x2', CENTER_X);
                        line.setAttribute('y2', height - 20);
                        line.setAttribute('stroke', '#e2e8f0');
                        line.setAttribute('stroke-width', '2');
                        line.setAttribute('stroke-dasharray', '6,6');
                        svg.appendChild(line);

                        // Function to wrap text
                        function wrapText(text, width) {
                            const words = text.split(' ');
                            let lines = [];
                            let currentLine = words[0];

                            for (let i = 1; i < words.length; i++) {
                                if (currentLine.length + words[i].length + 1 <= CHARS_PER_LINE) {
                                    currentLine += " " + words[i];
                                } else {
                                    lines.push(currentLine);
                                    currentLine = words[i];
                                }
                            }
                            lines.push(currentLine);
                            return lines;
                        }

                        // Create journey items
                        journeyItems.forEach(item => {
                            // Create group for each item
                            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

                            // Wrap and add text lines
                            const lines = wrapText(item.description, TEXT_WIDTH);
                            lines.forEach((line, index) => {
                                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                                text.setAttribute('x', CENTER_X - item.radius - 20);
                                text.setAttribute('y', item.y - (lines.length - 1) * 20 / 2 + index * 20);
                                text.setAttribute('text-anchor', 'end');
                                text.style.fontSize = '16px';
                                text.style.fill = '#1e293b';
                                text.textContent = line;
                                g.appendChild(text);
                            });

                            // Add time
                            const time = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                            time.setAttribute('x', CENTER_X - item.radius - 20);
                            time.setAttribute('y', item.y + lines.length * 10 + 10);
                            time.setAttribute('text-anchor', 'end');
                            time.style.fontSize = '14px';
                            time.style.fill = '#64748b';
                            time.textContent = new Date(item.created_at).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                            g.appendChild(time);

                            // Add circle
                            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                            circle.setAttribute('cx', CENTER_X);
                            circle.setAttribute('cy', item.y);
                            circle.setAttribute('r', item.radius);
                            circle.setAttribute('fill', '#60a5fa');
                            circle.setAttribute('fill-opacity', '0.9');
                            g.appendChild(circle);

                            // Add points
                            const points = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                            points.setAttribute('x', CENTER_X);
                            points.setAttribute('y', item.y);
                            points.setAttribute('text-anchor', 'middle');
                            points.setAttribute('dominant-baseline', 'middle');
                            points.style.fill = 'white';
                            points.style.fontSize = '16px';
                            points.style.fontWeight = 'bold';
                            points.textContent = item.points;
                            g.appendChild(points);

                            svg.appendChild(g);
                        });

                        container.appendChild(svg);
                    }

                    // Create visualization when the page loads
                    window.onload = createJourney;
                </script>
            </div>
            """

            # Insert the achievements data
            achievements_json = json.dumps(achievements)
            html = html.replace('ACHIEVEMENTS_PLACEHOLDER', achievements_json)

            return html

        # In your main_app function, update the daily journey button handler:
    if st.button("📅 Daily Journey"):
            achievements = handlers.get_achievements(st.session_state.user_id)
            today = date.today()
            daily_achievements = [
                {
                    "description": desc,
                    "points": points,
                    "created_at": created_at.isoformat()
                }
                for _, desc, points, created_at in achievements
                if created_at.date() == today
            ]

            if not daily_achievements:
                st.info("No achievements recorded today yet!")
            else:
                st.subheader("Your Journey Today")
                html_content = create_daily_journey_html(daily_achievements)
                st.components.v1.html(
                    html_content,
                    height=len(daily_achievements) * 120 + 100,
                    scrolling=True
                )
# Main flow
if st.session_state.user_id is None:
    login_form()
else:
    main_app()
