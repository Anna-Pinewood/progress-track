import random
from streamlit_extras.let_it_rain import rain
import streamlit as st
import time

from view.style_and_content_consts import MOTIVATION_MESSAGES


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
