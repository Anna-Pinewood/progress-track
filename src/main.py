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
from view.animations import show_achievement_animation, show_level_up_animation
from view.render import create_daily_journey_html, render_flag, render_level_progress
from view.style_and_content_consts import GROUP_COLORS
from view.utils import extract_group, get_random_quote

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
if 'current_quote' not in st.session_state:
    st.session_state.current_quote = get_random_quote()


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
    # Quote section
    quote_col, button_col = st.columns([5, 1])
    with quote_col:
        st.markdown(f"*{st.session_state.current_quote}*")
    with button_col:
        if st.button("🔄"):
            st.session_state.current_quote = get_random_quote()
            st.rerun()

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
        description = st.text_input(
            "Ваш вклад в ваши цели", key=f"desc_{st.session_state.form_key}")
        points = st.slider("Оценка вклада", min_value=5, max_value=50,
                           value=15, key=f"points_{st.session_state.form_key}")
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
                text_content += f"- {group_name} (Всего баллов: {total_points}):\n"
                for achievement_text, points in group_achievements:
                    text_content += f"  - {achievement_text}\n"
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
                    st.session_state.group_colors[group_name] = random.choice(
                        GROUP_COLORS)
        groups[group_name].append(
            (achievement[0], achievement_text, achievement[2], achievement[3]))

    # Clean up deleted groups from session state
    existing_groups = set(groups.keys())
    deleted_groups = set(
        st.session_state.group_colors.keys()) - existing_groups
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
                    st.markdown(render_flag(points, color),
                                unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️", key=f"delete_{achievement_id}"):
                        handlers.delete_achievement(
                            achievement_id, st.session_state.user_id)
                        remaining_achievements = [
                            a for a in group_achievements if a[0] != achievement_id]
                        if not remaining_achievements:
                            st.session_state.expanded_groups.remove(group_name)
                        st.rerun()
        else:
            st.session_state.expanded_groups.discard(group_name)

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

    # Add "To sum up" section
    st.subheader("To sum up")
    achievements = handlers.get_achievements(st.session_state.user_id)
    today = date.today()
    daily_achievements = [
        achievement for achievement in achievements if achievement[3].date() == today
    ]
    categories = list(set(extract_group(achievement[1])[
                      0] for achievement in daily_achievements))

    if categories:
        selected_category = st.selectbox("Select category", categories)
        summary_text = st.text_area("Write your summary")

        if st.button("Sum up"):
            if selected_category and summary_text:
                # Calculate total points for the category today
                total_points = sum(
                    ach[2] for ach in daily_achievements
                    if extract_group(ach[1])[0] == selected_category
                )

                # Split text into individual achievements
                summary_items = [item.strip()
                                 for item in summary_text.split('\n') if item.strip()]

                if summary_items:
                    # Delete old achievements
                    handlers.delete_achievements_by_category(
                        selected_category, st.session_state.user_id, today)

                    # Distribute points evenly among new items
                    points_per_item = total_points // len(summary_items)
                    remaining_points = total_points % len(summary_items)

                    # Add new achievements
                    for i, item in enumerate(summary_items):
                        # Add remaining points to first item
                        item_points = points_per_item + \
                            (remaining_points if i == 0 else 0)
                        handlers.add_achievement(
                            f"{selected_category}: {item}", item_points, st.session_state.user_id)

                    st.success("Summary added successfully!")
                    st.rerun()
    else:
        st.info("No achievements recorded today yet!")


# Main flow
if st.session_state.user_id is None:
    login_form()
else:
    main_app()
