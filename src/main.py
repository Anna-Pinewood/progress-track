import json
import os
from pathlib import Path
import streamlit as st
from datetime import date, datetime, timedelta
import database.handlers as handlers
from streamlit_extras.let_it_rain import rain
import random
from streamlit_extras.stateful_button import button
import threading
import time
from view.animations import show_achievement_animation, show_level_up_animation
from view.render import create_daily_journey_html, render_flag, render_level_progress
from view.style_and_content_consts import GROUP_COLORS
from view.utils import extract_group, get_random_quote, format_date, format_datetime

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
                # Load saved colors after login
                st.session_state.group_colors = handlers.get_group_colors(
                    user_id)
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


def generate_report_text(user_id, start_date=None):
    achievements = handlers.get_achievements(user_id)
    groups = {}

    for achievement in achievements:
        # Skip achievements that are earlier than the start_date if provided
        if start_date and achievement[3].date() < start_date:
            continue

        group_name, achievement_text = extract_group(achievement[1])
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append((achievement_text, achievement[2], achievement[3]))

    if start_date:
        text_content = f"Мои достижения с {format_date(start_date)}:\n\n"
    else:
        text_content = "Мои достижения:\n\n"

    for group_name in sorted(groups.keys()):
        group_achievements = groups[group_name]
        total_points = sum(points for _, points, _ in group_achievements)
        text_content += f"- {group_name}:\n"
        for achievement_text, points, _ in group_achievements:
            text_content += f"  - {achievement_text}\n"
        text_content += "\n"

    return text_content


def backup_report():
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:
            # Get all users and generate reports
            users = handlers.get_all_users()
            for user_id, username in users:
                report_text = generate_report_text(user_id)
                with open('/app/reports/report.txt', 'a', encoding='utf-8') as f:
                    f.write(
                        f"\n=== Report for {username} - {format_date(now.date())} ===\n")
                    f.write(report_text)
                    f.write("\n")
            time.sleep(60)  # Wait a minute to avoid multiple writes
        time.sleep(30)  # Check every 30 seconds


# Start backup thread when app starts
backup_thread = threading.Thread(target=backup_report, daemon=True)
backup_thread.start()


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
        description = st.text_area(
            "Ваш вклад в ваши цели", key=f"desc_{st.session_state.form_key}", height=70)

        points = st.slider("Оценка вклада", min_value=5, max_value=50,
                           value=15, key=f"points_{st.session_state.form_key}")
        submitted = st.form_submit_button("Добавить достижение")

    if submitted and description:
        # Extract group name if available
        group_name = None
        if description:
            group_name, _ = extract_group(description)

        # If this is a new group, assign a random color
        if group_name and group_name not in st.session_state.group_colors:
            available_colors = set(GROUP_COLORS) - \
                set(st.session_state.group_colors.values())
            new_color = random.choice(
                list(available_colors) if available_colors else GROUP_COLORS)
            st.session_state.group_colors[group_name] = new_color
            handlers.save_group_color(
                st.session_state.user_id, group_name, new_color)

        handlers.add_achievement(description, points, st.session_state.user_id)
        st.session_state.show_animation = points
        st.session_state.form_key += 1
        st.rerun()

    # Add Group Color Management section
    existing_groups = set()
    achievements = handlers.get_achievements(st.session_state.user_id)
    for achievement in achievements:
        group_name, _ = extract_group(achievement[1])
        existing_groups.add(group_name)

    if existing_groups:
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_group = st.selectbox(
                "Выберите группу", sorted(existing_groups))
        with col2:
            current_color = st.session_state.group_colors.get(
                selected_group, GROUP_COLORS[0])
            new_color = st.color_picker("Выберите цвет", current_color)

        if new_color != current_color:
            st.session_state.group_colors[selected_group] = new_color
            # Save color to database
            handlers.save_group_color(
                st.session_state.user_id, selected_group, new_color)
            st.rerun()
    else:
        st.info("Добавьте достижения чтобы управлять цветами групп")

    # Show animation if needed
    if st.session_state.show_animation is not None:
        show_achievement_animation(st.session_state.show_animation)
        st.session_state.show_animation = None

    col1, col2 = st.columns(2)
    with col1:
        # Add confirmation state to session if not exists
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False

        if not st.session_state.confirm_delete:
            if st.button("Удалить все достижения"):
                st.session_state.confirm_delete = True
                st.rerun()
        else:
            st.warning("Вы уверены, что хотите удалить все достижения?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Да, удалить"):
                    handlers.delete_all_achievements(st.session_state.user_id)
                    st.session_state.confirm_delete = False
                    st.session_state.expanded_groups = set()
                    st.rerun()
            with col2:
                if st.button("Отмена"):
                    st.session_state.confirm_delete = False
                    st.rerun()

    # Move the report generation under the delete section (outside both columns)
    st.subheader("Генерация отчёта")
    report_col1, report_col2 = st.columns([3, 1])

    with report_col1:
        report_start_date = st.date_input(
            "С даты (опционально)",
            value=None,
            key="report_start_date",
            help="Оставьте пустым для всей истории"
        )

    with report_col2:
        generate_report = st.button("📄 Сгенерировать отчёт")

    if generate_report:
        # Pass the selected start date (or None if not selected)
        text_content = generate_report_text(st.session_state.user_id, report_start_date)
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
                    st.write(f"{text}")
                    st.caption(f"Добавлено: {format_datetime(created_at)}")
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
                "created_at": created_at.strftime("%H:%M"),
                "color": st.session_state.group_colors.get(extract_group(desc)[0], '#4CAF50')
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

    # Daily Report Section
    st.subheader("📋 Daily Report")

    # Date navigation
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("◀"):
            if 'report_date' in st.session_state:
                st.session_state.report_date = st.session_state.report_date - timedelta(days=1)
            else:
                st.session_state.report_date = date.today() - timedelta(days=1)

    with col2:
        if 'report_date' not in st.session_state:
            st.session_state.report_date = date.today()
        report_date = st.date_input(
            "Select date to view achievements",
            value=st.session_state.report_date,
            key="report_date_input"
        )
        st.session_state.report_date = report_date

    with col3:
        if st.button("▶"):
            st.session_state.report_date = st.session_state.report_date + timedelta(days=1)

    # Get achievements for selected date
    daily_achievements = [
        achievement for achievement in achievements
        if achievement[3].date() == st.session_state.report_date
    ]

    if not daily_achievements:
        st.info(f"No achievements recorded on {format_date(st.session_state.report_date)}")
    else:
        # Generate report text for selected date
        report_text = f"Achievements for {format_date(st.session_state.report_date)}:\n\n"
        groups = {}

        for achievement in daily_achievements:
            group_name, achievement_text = extract_group(achievement[1])
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append((achievement_text, achievement[2]))

        for group_name in sorted(groups.keys()):
            group_achievements = groups[group_name]
            total_points = sum(points for _, points in group_achievements)
            report_text += f"- {group_name}:\n"
            for achievement_text, points in group_achievements:
                report_text += f"  - {achievement_text}\n"
            report_text += "\n"

        with st.expander("View Report", expanded=True):
            # Apply text wrapping using CSS
            st.markdown(
                """
                <style>
                    .stCode {
                        white-space: pre-wrap !important;
                        word-wrap: break-word !important;
                    }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.code(report_text, language=None)
            if st.button("📋 Copy Report", key="copy_daily_report"):
                st.write(
                    f'<script>navigator.clipboard.writeText(`{report_text}`)</script>',
                    unsafe_allow_html=True
                )
                st.success("Report copied to clipboard!")

    # Update "To sum up" section
    st.subheader("To sum up")
    achievements = handlers.get_achievements(st.session_state.user_id)
    today = date.today()

    # Add date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From date", value=today)
    with col2:
        end_date = st.date_input("To date", value=today)

    # Filter achievements by date range
    filtered_achievements = [
        achievement for achievement in achievements
        if start_date <= achievement[3].date() <= end_date
    ]

    categories = list(set(extract_group(achievement[1])[0]
                          for achievement in filtered_achievements))

    if categories:
        selected_category = st.selectbox("Select category", categories)

        # Display filtered achievements for selected category
        category_achievements = [
            achievement for achievement in filtered_achievements
            if extract_group(achievement[1])[0] == selected_category
        ]

        # Calculate total points for the category
        total_points = sum(ach[2] for ach in category_achievements)
        st.write(f"Total points for {selected_category}: {total_points}")

        # Display achievements with flags
        for achievement_id, text, points, created_at in category_achievements:
            _, achievement_text = extract_group(text)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{achievement_text}**")
                st.caption(f"Added: {format_datetime(created_at)}")
            with col2:
                color = st.session_state.group_colors.get(
                    selected_category, '#4CAF50')
                st.markdown(render_flag(points, color), unsafe_allow_html=True)

        # Add summary input field below the achievements list
        summary_text = st.text_area("Write your summary")

        if st.button("Sum up"):
            if selected_category and summary_text:
                # Split text into individual achievements
                summary_items = [item.strip()
                                 for item in summary_text.split('\n') if item.strip()]

                if summary_items:
                    # Delete old achievements in the category for selected date range
                    handlers.delete_achievements_by_category(
                        selected_category, st.session_state.user_id, start_date, end_date)

                    # Distribute points evenly among new items
                    points_per_item = total_points // len(summary_items)
                    remaining_points = total_points % len(summary_items)

                    # Add new achievements with today's date
                    for i, item in summary_items:
                        item_points = points_per_item + \
                            (remaining_points if i == 0 else 0)
                        handlers.add_achievement(
                            f"{selected_category}: {item}", item_points, st.session_state.user_id)

                    st.success("Summary added successfully!")
                    st.rerun()
    else:
        st.info("No achievements found in selected date range!")


# Main flow
if st.session_state.user_id is None:
    login_form()
else:
    main_app()
