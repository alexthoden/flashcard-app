# app.py
import json, os, random
from shiny import App, ui, reactive, render
# from shiny import update_radio_buttons

QUESTIONS_FILE = "questions.json"
SAVE_FILE = "correct_answers.json"

def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_correct_answers():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return set()
                return set(json.loads(content))
        except Exception:
            return set()
    return set()

def save_correct_answers(correct_set):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(correct_set), f, indent=2)

def reset_progress():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

# ---- UI ----
app_ui = ui.page_fluid(
    ui.div(
        ui.h2("Interactive Quiz"),
        class_="text-center my-4"   # center title horizontally, add spacing
    ),
    ui.output_ui("question_ui"),
    ui.div(
        ui.input_radio_buttons(
            "answer",
            "Choose:",
            choices=["Select an answer"],  # placeholder
            inline=False                   # each choice on its own line
        ),
        class_="d-flex justify-content-center my-3",  # center the container horizontally
        # style="height: 10vh;"
    ),
    # UI
    ui.div(
        ui.input_action_button("submit", "Submit", class_="btn-primary me-2"),
        ui.input_action_button("reset", "Reset progress", class_="btn-danger"),
        class_="my-3 d-flex justify-content-center"  # center buttons horizontally
    ),
    ui.output_text("feedback"),
    ui.output_text("debug"),
    ui.output_text("status"),
)



# ---- Server ----
def server(input, output, session):
    questions = load_questions()
    correct_set = reactive.Value(load_correct_answers())
    remaining = reactive.Value([])
    current = reactive.Value(None)
    
    feedback_msg = reactive.Value("")
    debug_msg = reactive.Value("Loading app...")

    # Initialize on startup
    def init_questions():
        try:
            debug_msg.set("Init: Loading questions...")
            rem = [q for q in questions if q["question_number"] not in correct_set.get()]
            random.shuffle(rem)
            remaining.set(rem)
            if rem:
                current.set(rem[0])
                remaining.set(rem[1:])
                debug_msg.set("✅ Init complete")
            else:
                current.set(None)
                debug_msg.set("⚠️ No questions loaded")
        except Exception as e:
            debug_msg.set(f"❌ Init error: {str(e)}")

    def next_question():
        try:
            rem = remaining.get()
            if rem:
                random.shuffle(rem)
                current.set(rem[0])
                remaining.set(rem[1:])
            else:
                current.set(None)
        except Exception as e:
            debug_msg.set(f"❌ next_question error: {str(e)}")

    @output
    @render.ui
    def question_ui():
        card = current.get()
        if card is None:
            return ui.div(
                ui.h4("🎉 All questions answered correctly!"),
                class_="d-flex justify-content-center align-items-center",
                style="height: 50vh;"   # vertically center in viewport
            )
        # update radio buttons dynamically
        ui.update_radio_buttons(
            "answer",
            choices=[f"{opt}) {val}" for opt, val in card["options"].items()],
            selected=None,
            inline=False   # each choice on its own line
        )
        return ui.div(
            ui.h4(f"Q{card['question_number']}: {card['question']}"),
            class_="d-flex justify-content-center align-items-center text-center",
            style="height: 10vh;"   # vertically center question block
        )

    @output
    @render.text
    def feedback():
        return feedback_msg.get()
    
    @output
    @render.text
    def debug():
        return debug_msg.get()

    @output
    @render.text
    def status():
        return f"Remaining: {len(remaining.get()) + (1 if current.get() else 0)} | Correct saved: {len(correct_set.get())}"

    @reactive.event(input.submit)
    def on_submit():
        try:
            debug_msg.set("🔍 submit button fired")
            card = current.get()
            if card is None:
                feedback_msg.set("⚠️ No more questions!")
                return
            ans = input.answer()
            debug_msg.set(f"🔍 Answer: {ans}")
            if not ans:
                feedback_msg.set("⚠️ Please select an answer.")
                return
            chosen = ans[0].upper()
            debug_msg.set(f"🔍 Chosen: {chosen}, Correct: {card['correct_answer']}")
            if chosen == card["correct_answer"]:
                feedback_msg.set("✅ Correct!")
                corr = correct_set.get().copy()
                corr.add(card["question_number"])
                correct_set.set(corr)
                save_correct_answers(corr)
                next_question()
            else:
                feedback_msg.set(f"❌ Incorrect. Correct answer: {card['correct_answer']}")
                rem = remaining.get().copy()
                rem.append(card)
                remaining.set(rem)
                next_question()
        except Exception as e:
            import traceback
            debug_msg.set(f"❌ ERROR in submit: {str(e)}")
            print(traceback.format_exc())

    @reactive.event(input.reset)
    def on_reset():
        try:
            debug_msg.set("🔍 reset button fired")
            reset_progress()
            correct_set.set(set())
            init_questions()
            feedback_msg.set("Progress reset.")
            debug_msg.set("✅ Reset complete")
        except Exception as e:
            import traceback
            debug_msg.set(f"❌ ERROR in reset: {str(e)}")
            print(traceback.format_exc())

    # Call init on startup
    init_questions()

app = App(app_ui, server, debug=True)