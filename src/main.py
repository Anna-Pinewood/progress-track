# src/main.py
import streamlit as st
from datetime import datetime
import os
import database.handlers as handlers
from streamlit_extras.let_it_rain import rain


st.set_page_config(page_title="Трекер достижений")

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

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
    
    # Logout button
    if st.button("Выйти"):
        st.session_state.user_id = None
        st.rerun()
    
    # Achievement input form
    with st.form("achievement_form"):
        description = st.text_input("Ваш вклад в ваши цели")
        points = st.slider("Оценка вклада", min_value=5, max_value=50, value=15)
        submitted = st.form_submit_button("Добавить достижение")

    if submitted and description:

        handlers.add_achievement(description, points, st.session_state.user_id)
        balloon_count = max(1, points // 10)
        if points <= 15:
            for _ in range(balloon_count):
                st.balloons()
                st.success("Молодец, так держать!")
        elif points <= 30:
            for _ in range(balloon_count):
                st.balloons()
                rain(emoji="🥇", font_size=54, falling_speed=2, animation_length=1)
                st.success("Отличное достижение!")
        else:
            for _ in range(balloon_count):
                st.balloons()
                rain(emoji="💎", font_size=54, falling_speed=2, animation_length=1)
            st.success("Выдающееся достижение!")
            
        st.session_state.description = ""
        st.session_state.points = 15
    # Delete all achievements button
    if st.button("Удалить все достижения"):
        handlers.delete_all_achievements(st.session_state.user_id)
        st.warning("Все достижения удалены!")

    # Export to txt
    if st.button("📄 txt сводка"):
        text_content = "Мои достижения:\n\n"
        for achievement in handlers.get_achievements(st.session_state.user_id):
            text_content += f"• {achievement[1]} ({achievement[2]} pts)\n"
        
        with st.expander("Текст для копирования", expanded=True):
            st.code(text_content, language=None)
            st.button("Копировать", type="primary", 
                     on_click=lambda: st.write(
                         f'<script>navigator.clipboard.writeText(`{text_content}`)</script>', 
                         unsafe_allow_html=True
                     ))

    # Display achievements
    with st.expander("Показать все достижения", expanded=True):
        achievements = handlers.get_achievements(st.session_state.user_id)
        for achievement in achievements:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{achievement[1]}**")
                st.caption(f"Добавлено: {achievement[3]}")
            with col2:
                size = achievement[2] * 2
                st.markdown(f"""
                    <div style="
                        width: {size}px;
                        height: {size}px;
                        background-color: #fea03d;
                        margin: 5px;
                    "></div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                    <style>
                    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(3) button {
                        padding: 0px 5px;
                        font-size: 12px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete_{achievement[0]}"):
                    handlers.delete_achievement(achievement[0], st.session_state.user_id)
                    st.rerun()

# Main flow
if st.session_state.user_id is None:
    login_form()
else:
    main_app()