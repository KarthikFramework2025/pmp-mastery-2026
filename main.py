import os
import flet as ft
import json
import random
import asyncio
from database import init_db, save_attempt, get_attempts

init_db()


def load_questions():
    with open("questions.json", "r", encoding="utf-8") as f:
        return json.load(f)



QUESTIONS = load_questions()


def main(page: ft.Page):
    page.title = "PMP Mastery 2026"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # ---------------- BRAND COLORS ----------------
    BRAND_PRIMARY = "#3F51B5"
    BRAND_LIGHT_BG = "#F4F6FA"
    BRAND_CARD_BG = "#FFFFFF"
    BRAND_DARK_BG = "#1E1F26"
    BRAND_DARK_CARD = "#2A2C36"

    page.bgcolor = BRAND_LIGHT_BG
    page.dialog = None


    # ---------------- STATE ----------------
    current_question_index = 0
    score = 0
    quiz_questions = []
    total_questions = 0
    timer_seconds = 0
    timer_running = False
    mode = "Practice"
    domain_correct = {}
    domain_total = {}
    is_pro_user = False   # <-- ADD THIS

    # ---------------- SPACING ----------------
    SPACE_SM = 16
    SPACE_MD = 24
    SPACE_LG = 32

    content_area = ft.Container(expand=True, padding=SPACE_MD, animate_opacity=300)

    # ---------------- FADE SWITCH ----------------
    def switch_content(new_content):
        content_area.opacity = 0
        page.update()

        async def fade():
            await asyncio.sleep(0.1)
            content_area.content = new_content
            content_area.opacity = 1
            page.update()

        page.run_task(fade)

    # ---------------- DARK MODE ----------------
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = BRAND_DARK_BG
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = BRAND_LIGHT_BG

        page.update()

        if navigation.selected_index == 1:
            show_results()
        elif navigation.selected_index == 2:
            show_analytics()

    theme_switch = ft.Switch(label="Dark Mode", on_change=toggle_theme)

    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("PMP Mastery 2026", size=22, weight="bold"),
                        ft.Text("Train smart. Pass confidently.", size=12)
                    ],
                    spacing=4
                ),
                theme_switch
            ],
            alignment="spaceBetween"
        ),
        padding=SPACE_SM,
        bgcolor=BRAND_PRIMARY,
    )

    # ---------------- BUTTON ----------------
    def primary_button(text, handler):
        return ft.ElevatedButton(
            text,
            on_click=handler,
            width=220,
            style=ft.ButtonStyle(
                bgcolor=BRAND_PRIMARY,
                color="white",
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )

    # =====================================================
    # ================= QUIZ SECTION ======================
    # =====================================================

    progress_text = ft.Text(weight="bold")
    timer_display = ft.Text(color="red")
    question_text = ft.Text(size=18)
    options_column = ft.Column(spacing=SPACE_SM)
    radio_group = ft.RadioGroup(content=options_column)
    explanation_container = ft.Container(visible=False)
    continue_button = ft.ElevatedButton("Continue", visible=False)

    async def update_timer():
        nonlocal timer_seconds, timer_running
        while timer_seconds > 0 and timer_running:
            mins = timer_seconds // 60
            secs = timer_seconds % 60
            timer_display.value = f"Time Left: {mins:02}:{secs:02}"
            page.update()
            await asyncio.sleep(1)
            timer_seconds -= 1
        if timer_running:
            submit_exam(None)

    def start_timer(seconds):
        nonlocal timer_seconds, timer_running
        timer_seconds = seconds
        timer_running = True
        page.run_task(update_timer)

    def show_question():
        question = quiz_questions[current_question_index]
        progress_text.value = f"{mode} | Question {current_question_index+1}/{total_questions}"
        question_text.value = question["question"]
        radio_group.value = None
        options_column.controls.clear()

        for i, option in enumerate(question["options"]):
            options_column.controls.append(
                ft.Radio(value=str(i), label=option)
            )

        page.update()

    def next_question(e):
        nonlocal score, current_question_index

        if radio_group.value is None:
            return

        selected_index = int(radio_group.value)
        current_question = quiz_questions[current_question_index]
        correct_index = current_question["correct_answer"]
        category = current_question["category"]

        # Track totals
        domain_total[category] = domain_total.get(category, 0) + 1

        if selected_index == correct_index:
            score += 1
            domain_correct[category] = domain_correct.get(category, 0) + 1
            result_text = "✅ Correct!"
            result_color = ft.Colors.GREEN
        else:
            result_text = "❌ Incorrect!"
            result_color = ft.Colors.RED

        correct_option_text = current_question["options"][correct_index]
        explanation_text = current_question.get("explanation", "No explanation provided.")

        explanation_container.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(result_text, weight="bold", color=result_color),
                    ft.Text(f"Correct Answer: {correct_option_text}", weight="bold"),
                    ft.Text(explanation_text),
                ],
                spacing=6
            ),
            padding=SPACE_SM,
            bgcolor=BRAND_CARD_BG if page.theme_mode == ft.ThemeMode.LIGHT else BRAND_DARK_CARD,
            border_radius=10
        )

        explanation_container.visible = True

        continue_button.visible = True
        continue_button.on_click = continue_to_next

        page.update()

    def continue_to_next(e):
        nonlocal current_question_index

        explanation_container.visible = False
        continue_button.visible = False
        radio_group.value = None

        current_question_index += 1

        if current_question_index < total_questions:
            show_question()
        else:
            submit_exam(None)

        page.update()


    def submit_exam(e):
        nonlocal timer_running
        timer_running = False

        percentage = (score / total_questions) * 100 if total_questions else 0

        # ---------------- FIXED DOMAIN STRUCTURE ----------------
        domain_stats = {}

        for domain in domain_total:
            correct = domain_correct.get(domain, 0)
            total = domain_total.get(domain, 0)

            domain_stats[domain] = {
                "correct": correct,
                "total": total
            }

        save_attempt(mode, score, total_questions, domain_stats)

        result_layout = ft.Column(
            [
                ft.Text(f"{mode} Result", size=22, weight="bold"),
                ft.Text(f"Score: {score}/{total_questions}", size=18, weight="bold"),
                ft.Text(f"{percentage:.2f}%"),
                ft.Container(height=SPACE_MD),
                primary_button("Back to Home", lambda e: show_home())
            ],
            horizontal_alignment="center",
            spacing=SPACE_SM
        )

        switch_content(result_layout)


    def quiz_layout():
        return ft.Column(
            [
                progress_text,
                timer_display,
                ft.Container(height=SPACE_SM),
                question_text,
                ft.Container(height=SPACE_SM),
                radio_group,
                ft.Container(height=SPACE_MD),

                ft.ElevatedButton("Submit Answer", on_click=next_question),

                explanation_container,

                ft.Container(
                    content=continue_button,
                    margin=ft.margin.only(top=SPACE_MD, bottom=SPACE_LG)
                ),
            ],
            spacing=SPACE_SM,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )





    def start_practice(e):
        nonlocal current_question_index, score, quiz_questions
        nonlocal total_questions, domain_correct, domain_total, mode
        nonlocal timer_running

        # 🔥 STOP TIMER
        timer_running = False
        timer_display.value = ""
        
        mode = "Practice"

        free_questions = [q for q in QUESTIONS if not q.get("is_pro", False)]

        quiz_questions = random.sample(
            free_questions,
            min(25, len(free_questions))
        )

        total_questions = len(quiz_questions)
        current_question_index = 0
        score = 0
        domain_correct = {}
        domain_total = {}

        timer_display.value = ""

        switch_content(quiz_layout())
        show_question()

    # 🔥 ADD THESE FUNCTIONS HERE

    def get_weakest_domain():
        attempts = get_attempts()

        if not attempts:
            return None

        latest = attempts[-1]
        domain_stats = latest.get("domain_stats", {})

        performance = {}

        for domain, stats in domain_stats.items():
            if stats["total"] > 0:
                performance[domain] = stats["correct"] / stats["total"]

        if not performance:
            return None

        return min(performance, key=performance.get)


    def generate_adaptive_mock(questions):

        weakest = get_weakest_domain()

        # Filter only Pro questions
        pro_questions = [q for q in questions if q.get("is_pro", False)]

        # Group by category dynamically
        category_groups = {}
        for q in pro_questions:
            cat = q["category"]
            category_groups.setdefault(cat, []).append(q)

        # Default: evenly distribute across categories
        total_questions = 180
        num_categories = len(category_groups)
        base_count = total_questions // num_categories

        dist = {cat: base_count for cat in category_groups}

        # Adjust remainder
        remainder = total_questions - (base_count * num_categories)
        for i, cat in enumerate(dist):
            if i < remainder:
                dist[cat] += 1

        # Boost weakest category
        if weakest and weakest in dist:
            dist[weakest] += 10

            # Reduce others slightly
            for cat in dist:
                if cat != weakest and dist[cat] > 5:
                    dist[cat] -= 1

        # Select questions
        selected = []
        for cat, count in dist.items():
            pool = category_groups[cat]
            selected += random.sample(pool, min(count, len(pool)))

        random.shuffle(selected)

        return selected

    def start_mock(e):
        nonlocal current_question_index, score, quiz_questions
        nonlocal total_questions, domain_correct, domain_total, mode
        nonlocal is_pro_user

        if not is_pro_user:
            show_upgrade_screen()
            return

        mode = "Mock"

        # Load ALL questions for Pro
        quiz_questions = generate_adaptive_mock(QUESTIONS)

        total_questions = len(quiz_questions)
        current_question_index = 0
        score = 0
        domain_correct = {}
        domain_total = {}

        timer_display.value = ""
        switch_content(quiz_layout())
        show_question()

        start_timer(10800)  # 180 minutes real PMP



    # =====================================================
    # ================= RESULTS ===========================
    # =====================================================

    def show_results():
        attempts = get_attempts()

        table_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        header_row = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Date & Time", weight="bold", expand=3),
                    ft.Text("Mode", weight="bold", expand=2),
                    ft.Text("Score", weight="bold", expand=2),
                    ft.Text("Percentage", weight="bold", expand=2),
                ]
            ),
            padding=SPACE_SM,
            bgcolor=BRAND_PRIMARY
        )

        table_column.controls.append(header_row)

        for i, attempt in enumerate(attempts):

            # Alternate row color
            if page.theme_mode == ft.ThemeMode.DARK:
                row_bg = BRAND_DARK_CARD
            else:
                row_bg = BRAND_CARD_BG if i % 2 == 0 else "#EEF1F8"

            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(str(attempt["date"]), expand=3),
                        ft.Text(str(attempt["mode"]), expand=2),
                        ft.Text(
                            f"{attempt['score']}/{attempt['total']}",
                            expand=2
                        ),
                        ft.Text(
                            f"{attempt['percentage']:.2f}%",
                            expand=2
                        ),
                    ]
                ),
                padding=SPACE_SM,
                bgcolor=row_bg
            )

            table_column.controls.append(row)

        switch_content(table_column)


    # =====================================================
    # ================= ANALYTICS =========================
    # =====================================================

    def show_analytics():
        if not is_pro_user:
            show_basic_analytics()
        else:
            show_advanced_analytics()

    def show_basic_analytics():
        all_attempts = get_attempts()

        # ---------------- FILTER ONLY PRACTICE ATTEMPTS ----------------
        attempts = [a for a in all_attempts if a["mode"] == "Practice"]

        if not attempts:
            switch_content(
                ft.Column(
                    [ft.Text("No practice attempts yet.", size=18, weight="bold")],
                    horizontal_alignment="center",
                    expand=True
                )
            )
            return

        # ---------------- BASIC METRICS ----------------
        percentages = [a["percentage"] for a in attempts]
        total_attempts = len(attempts)

        lifetime_avg = sum(percentages) / total_attempts
        best_score = max(percentages)

        last_5 = percentages[-5:]
        last_5_avg = sum(last_5) / len(last_5)

        # ---------------- THEME COLORS ----------------
        text_color = (
            ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK
            else ft.Colors.BLACK
        )

        card_bg = (
            BRAND_DARK_CARD if page.theme_mode == ft.ThemeMode.DARK
            else BRAND_CARD_BG
        )

        # ---------------- LAYOUT ----------------
        analytics_layout = ft.Column(
            [
                ft.Text(
                    "Practice Performance Overview",
                    size=20,
                    weight="bold",
                    color=text_color
                ),

                ft.Container(height=SPACE_SM),

                ft.Text(f"Lifetime Average: {lifetime_avg:.2f}%", color=text_color),
                ft.Text(f"Best Score: {best_score:.2f}%", color=text_color),
                ft.Text(f"Total Attempts: {total_attempts}", color=text_color),
                ft.Text(f"Last 5 Attempts Avg: {last_5_avg:.2f}%", color=text_color),

                ft.Container(height=SPACE_MD),

                # -------- VALUE ANCHOR CARD --------
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Unlock Advanced Analytics",
                                weight="bold",
                                color=text_color
                            ),
                            ft.Text(
                                "Get Exam Readiness Score, Domain Coverage, "
                                "Weakness Severity & Consistency Tracking.",
                                color=text_color
                            )
                        ]
                    ),
                    padding=SPACE_MD,
                    bgcolor=card_bg,
                    border_radius=10
                ),

                ft.Container(height=SPACE_SM),

                # -------- UPGRADE BUTTON --------
                ft.ElevatedButton(
                    "Unlock Advanced Analytics – ₹399",
                    on_click=lambda e: show_upgrade_screen(),
                    width=280
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=SPACE_SM
        )

        switch_content(analytics_layout)


    def show_advanced_analytics():
        all_attempts = get_attempts()

        # ---------------- FILTER ONLY MOCK ATTEMPTS ----------------
        attempts = [a for a in all_attempts if a["mode"] == "Mock"]

        if not attempts:
            switch_content(
                ft.Column(
                    [ft.Text("No mock attempts yet.", size=18, weight="bold")],
                    horizontal_alignment="center",
                    expand=True
                )
            )
            return

        # ---------------- BASIC METRICS ----------------
        percentages = [a["percentage"] for a in attempts]
        total_attempts = len(attempts)

        lifetime_avg = sum(percentages) / total_attempts
        best_score = max(percentages)

        last_5 = percentages[-5:]
        last_5_avg = sum(last_5) / len(last_5)

        total_questions_attempted = sum(a["total"] for a in attempts)

        # ---------------- DOMAIN AGGREGATION ----------------
        domain_scores = {}

        for a in attempts:
            domain_stats = a.get("domain_stats", {})

            if not isinstance(domain_stats, dict):
                continue

            for domain, stats in domain_stats.items():

                if not isinstance(stats, dict):
                    continue

                correct = stats.get("correct", 0)
                total = stats.get("total", 0)

                if total > 0:
                    percent = (correct / total) * 100
                    domain_scores.setdefault(domain, []).append(percent)

        averaged_domains = {
            d: sum(v) / len(v)
            for d, v in domain_scores.items()
            if len(v) > 0
        }

        if averaged_domains:
            strongest_domain = max(averaged_domains, key=averaged_domains.get)
            weakest_domain = min(averaged_domains, key=averaged_domains.get)
        else:
            strongest_domain = "N/A"
            weakest_domain = "N/A"

        # ---------------- DOMAIN COVERAGE ----------------
        total_possible_domains = 10
        domains_attempted = len(averaged_domains)

        # ---------------- PERFORMANCE TREND ----------------
        if last_5_avg > lifetime_avg:
            performance_pattern = "Improving 📈"
        elif last_5_avg < lifetime_avg:
            performance_pattern = "Declining 📉"
        else:
            performance_pattern = "Stable ➖"

        # ---------------- CONSISTENCY SCORE ----------------
        if len(last_5) > 1:
            mean = last_5_avg
            variance = sum((x - mean) ** 2 for x in last_5) / len(last_5)
            stability_score = max(0, 100 - variance)
        else:
            stability_score = 100

        # ---------------- EXAM READINESS SCORE ----------------
        domain_balance_score = (
            sum(averaged_domains.values()) / len(averaged_domains)
            if averaged_domains else 0
        )

        readiness_score = (
            (last_5_avg * 0.5) +
            (lifetime_avg * 0.3) +
            (domain_balance_score * 0.2)
        )

        readiness_score = min(100, readiness_score)

        # ---------------- WEAKNESS SEVERITY ----------------
        weakest_percent = averaged_domains.get(weakest_domain, 0)

        if weakest_percent < 50:
            weakness_level = "Critical Weakness"
        elif weakest_percent < 70:
            weakness_level = "Moderate Weakness"
        else:
            weakness_level = "Minor Weakness"

        # ---------------- SMART RECOMMENDATION ----------------
        if readiness_score >= 80:
            recommendation = "You are exam-ready. Focus on mock simulation endurance."
        elif readiness_score >= 60:
            recommendation = "Good progress. Strengthen weak domains and improve stability."
        else:
            recommendation = "Focus on fundamentals. Increase structured practice."

        # ---------------- DARK MODE TEXT FIX ----------------
        text_color = (
            ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK
            else ft.Colors.BLACK
        )

        card_bg = (
            BRAND_DARK_CARD if page.theme_mode == ft.ThemeMode.DARK
            else BRAND_CARD_BG
        )

        # ---------------- UI LAYOUT ----------------
        analytics_layout = ft.Column(
            [
                ft.Text(
                    "Advanced Performance Analytics",
                    size=20,
                    weight="bold",
                    color=text_color
                ),

                ft.Container(height=SPACE_SM),

                ft.Text(
                    f"Exam Readiness Score: {readiness_score:.1f} / 100",
                    weight="bold",
                    color=text_color
                ),

                ft.Container(height=SPACE_SM),

                ft.Text(f"Lifetime Average: {lifetime_avg:.2f}%", color=text_color),
                ft.Text(f"Best Score: {best_score:.2f}%", color=text_color),
                ft.Text(f"Last 5 Attempts Avg: {last_5_avg:.2f}%", color=text_color),
                ft.Text(f"Total Attempts: {total_attempts}", color=text_color),
                ft.Text(f"Total Questions Attempted: {total_questions_attempted}", color=text_color),

                ft.Container(height=SPACE_SM),

                ft.Text(
                    f"Domains Attempted: {domains_attempted} / {total_possible_domains}",
                    color=text_color
                ),

                ft.Container(height=SPACE_SM),

                ft.Text(
                    f"Strongest Domain: {strongest_domain} "
                    f"({averaged_domains.get(strongest_domain, 0):.2f}%)",
                    color=ft.Colors.GREEN
                ),

                ft.Text(
                    f"Weakest Domain: {weakest_domain} "
                    f"({weakest_percent:.2f}%) - {weakness_level}",
                    color=ft.Colors.RED
                ),

                ft.Container(height=SPACE_SM),

                ft.Text(f"Performance Trend: {performance_pattern}", color=text_color),
                ft.Text(f"Consistency Score: {stability_score:.1f} / 100", color=text_color),

                ft.Container(height=SPACE_MD),

                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Smart Recommendation",
                                weight="bold",
                                color=text_color
                            ),
                            ft.Text(
                                recommendation,
                                color=text_color
                            )
                        ]
                    ),
                    padding=SPACE_MD,
                    bgcolor=card_bg,
                    border_radius=10
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=SPACE_SM
        )

        switch_content(analytics_layout)




    # =====================================================
    # ================= HOME ==============================
    # =====================================================

    def show_home():
        messages = [
            "Consistency beats intensity.",
            "Every question builds confidence.",
            "Mock exams simulate success.",
            "Stay focused. You’re improving daily."
        ]

        home_layout = ft.Column(
            [
                ft.Text(random.choice(messages), size=16),
                ft.Container(height=SPACE_LG),
                ft.Column(
                    [
                        primary_button("Practice Mode", start_practice),
                        ft.Text("25 Questions • Free", size=12, color=ft.Colors.GREY)
                    ],
                    horizontal_alignment="center",
                    spacing=4
                ),
                ft.Container(height=SPACE_SM),
                primary_button("Mock Exam Mode", start_mock),
            ],
            horizontal_alignment="center",
            spacing=SPACE_SM
        )

        switch_content(home_layout)

# =====================================================
# ================= MONETIZATION ======================
# =====================================================

    def close_dialog(dialog):
        dialog.open = False
        page.update()


    def activate_pro(dialog):
        nonlocal is_pro_user
        is_pro_user = True
        dialog.open = False
        page.update()


    def show_upgrade_screen():
        upgrade_layout = ft.Column(
            [
                ft.Text("Upgrade to PMP Pro", size=22, weight="bold"),

                ft.Container(height=SPACE_MD),

                ft.Text("What You Get:", weight="bold"),

                ft.Column(
                    [
                        ft.Text("• Full 500+ Question Bank"),
                        ft.Text("• 180-Question Realistic Mock Exam"),
                        ft.Text("• 3-Hour Real Exam Simulation"),
                        ft.Text("• Detailed Answer Explanations"),
                        ft.Text("• Advanced Performance Analytics"),
                        ft.Text("• Domain-Level Mastery Tracking"),
                    ],
                    spacing=6
                ),

                ft.Container(height=SPACE_MD),

                ft.Text("Free Version Includes:", weight="bold"),

                ft.Column(
                    [
                        ft.Text("• 25 Practice Questions"),
                        ft.Text("• Basic Analytics"),
                        ft.Text("• Limited Question Pool"),
                    ],
                    spacing=6
                ),

                ft.Container(height=SPACE_LG),

                ft.ElevatedButton(
                    "Unlock Pro – ₹399",
                    on_click=lambda e: activate_pro_from_screen(),
                    width=220
                ),

                ft.Text(
                    "One-Time Payment • Lifetime Access • No Subscription",
                    size=12,
                    color=ft.Colors.GREY
                ),

                ft.TextButton(
                    "Maybe Later",
                    on_click=lambda e: show_home()
                )
            ],
            spacing=SPACE_SM,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment="center"
        )

        switch_content(upgrade_layout)

    def activate_pro_from_screen():
        nonlocal is_pro_user
        is_pro_user = True
        show_home()




    # =====================================================
    # ================= NAVIGATION ========================
    # =====================================================

    def on_tab_change(e):
        if e.control.selected_index == 0:
            show_home()
        elif e.control.selected_index == 1:
            show_results()
        elif e.control.selected_index == 2:
            show_analytics()

    navigation = ft.NavigationBar(
        selected_index=0,
        on_change=on_tab_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Results"),
            ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS, label="Analytics"),
        ],
    )

    # ---------------- SPLASH ----------------
    splash = ft.Container(
        content=ft.Column(
            [
                ft.Text("PMP Mastery 2026", size=32, weight="bold", color=BRAND_PRIMARY),
                ft.Text("Train smart. Pass confidently.", size=16),
            ],
            horizontal_alignment="center",
            alignment="center"
        ),
        expand=True,
        alignment=ft.Alignment.CENTER
    )

    page.add(splash)

    async def load_app():
        await asyncio.sleep(1.5)
        page.controls.clear()
        page.add(ft.Column([header, content_area, navigation], expand=True))
        show_home()

    page.run_task(load_app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=main, port=port)
