import json
import random
import streamlit as st


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


def get_level_emoji(level):
    # Update next_emoji_level if we reached it
    if level >= st.session_state.next_emoji_level:
        emojis = ["⭐", "🚲", "🎨", "⛰️", "🗻", "🌋", "🎆",
                  "🎯", "🎮", "🏔️", "🏄‍♀️", "🤸", "👱🏻‍♀️"]
        st.session_state.current_emoji = random.choice(emojis)
        # Set next change 5-10 levels from now
        st.session_state.next_emoji_level = level + random.randint(5, 10)

    return st.session_state.current_emoji


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
                            time.textContent = item.created_at;  // Use the string directly
                            g.appendChild(time);

                            // Add circle
                            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                            circle.setAttribute('cx', CENTER_X);
                            circle.setAttribute('cy', item.y);
                            circle.setAttribute('r', item.radius);
                            circle.setAttribute('fill', item.color);  // Use the color from achievement data
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
