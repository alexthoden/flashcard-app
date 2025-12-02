import json
import random
import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Load questions
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

answered_file = "answeredQuestions.json"

# Load already answered questions
answered_correctly = set()
if os.path.exists(answered_file):
    with open(answered_file, "r", encoding="utf-8") as f:
        try:
            saved = json.load(f)
            answered_correctly = {q["question_number"] for q in saved}
        except json.JSONDecodeError:
            answered_correctly = set()

# Track history and index
question_history = []
current_index = -1

def get_random_question():
    remaining = [q for q in questions if q["question_number"] not in answered_correctly]
    if not remaining:
        return None
    return random.choice(remaining)

def save_correct_question(question):
    if os.path.exists(answered_file):
        with open(answered_file, "r", encoding="utf-8") as f:
            try:
                saved = json.load(f)
            except json.JSONDecodeError:
                saved = []
    else:
        saved = []
    if not any(q["question_number"] == question["question_number"] for q in saved):
        saved.append(question)
        with open(answered_file, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2)

def reset_progress():
    global answered_correctly, question_history, current_index
    answered_correctly = set()
    question_history = []
    current_index = -1
    if os.path.exists(answered_file):
        os.remove(answered_file)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Quizlet-Style Flashcards"

app.layout = dbc.Container([
    html.H2("Flashcard Quiz", className="text-center my-4 fw-bold"),

    dbc.Progress(id="progress-bar", value=0, striped=True, animated=True, className="mb-4"),

    dbc.Card([
        dbc.CardBody([
            html.Div(id="question-text", className="h4 mb-4 text-center fw-semibold"),
            dcc.RadioItems(id="options", options=[], value=None,
                           className="d-flex flex-column align-items-start mb-4",
                           inputStyle={"margin-right": "10px", "margin-bottom": "10px"}),
            dbc.Button("Submit", id="submit-btn", color="primary", className="w-100 mb-3"),
            # Navigation buttons inside the card
            dbc.Row([
                dbc.Col(dbc.Button("⬅ Back", id="back-btn", color="secondary", className="w-100"), width=6),
                dbc.Col(dbc.Button("➡ Next", id="next-btn", color="info", className="w-100"), width=6),
            ], className="mb-3"),
            html.Div(id="feedback", className="mt-3 text-center fw-bold fs-5"),
            dcc.Interval(id="feedback-timer", interval=2000, n_intervals=0, disabled=True)
        ])
    ], className="shadow-lg p-4 mb-5 bg-white rounded", style={"maxWidth": "600px", "margin": "auto"}),

    # Smaller reset button below card
    html.Div(dbc.Button("Reset Progress", id="reset-btn", color="danger", size="sm", className="mt-2"),
             className="text-center"),

    html.Div(id="status-indicator", className="text-center mt-4 fw-bold fs-5")
], fluid=True)


user_answers = {}

@app.callback(
    [Output("question-text", "children"),
     Output("options", "options"),
     Output("options", "value"),
     Output("feedback", "children"),
     Output("feedback-timer", "disabled"),
     Output("progress-bar", "value"),
     Output("status-indicator", "children")],
    [Input("submit-btn", "n_clicks"),
     Input("feedback-timer", "n_intervals"),
     Input("next-btn", "n_clicks"),
     Input("back-btn", "n_clicks"),
     Input("reset-btn", "n_clicks")],
    [State("options", "value"),
     State("question-text", "children")]
)
def update_question(submit_clicks, timer_tick, next_clicks, back_clicks, reset_clicks, selected_option, current_text):
    global current_index

    ctx = dash.callback_context
    total_questions = len(questions)
    progress = int(len(answered_correctly) / total_questions * 100)
    status_text = f"{len(answered_correctly)} of {total_questions} correct"

    # Reset
    if ctx.triggered and "reset-btn" in ctx.triggered[0]["prop_id"]:
        reset_progress()
        user_answers.clear()
        q = get_random_question()
        if q:
            question_history.append(q)
            current_index = 0
            return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], None, "Progress reset!", True, 0, f"0 of {total_questions} correct"
        else:
            return "No questions available", [], None, "", True, 0, "0 of 0 correct"

    # Back
    if ctx.triggered and "back-btn" in ctx.triggered[0]["prop_id"]:
        if current_index > 0:
            current_index -= 1
            q = question_history[current_index]
            # Restore saved answer if exists
            saved_value = user_answers.get(q["question_number"], None)
            return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], saved_value, "", True, progress, status_text
        else:
            raise PreventUpdate

    # Next
    if ctx.triggered and "next-btn" in ctx.triggered[0]["prop_id"]:
        q = get_random_question()
        if q:
            question_history.append(q)
            current_index = len(question_history) - 1
            # New random question → no saved selection
            return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], None, "", True, progress, status_text
        else:
            return "🎉 All questions answered correctly!", [], None, "", True, 100, status_text

    # Submit
    if ctx.triggered and "submit-btn" in ctx.triggered[0]["prop_id"]:
        if not selected_option:
            raise PreventUpdate
        q = next(q for q in questions if q["question"] == current_text)
        # Save user’s selection
        user_answers[q["question_number"]] = selected_option
        if selected_option == q["correct_answer"]:
            answered_correctly.add(q["question_number"])
            save_correct_question(q)
            feedback = "✅ Correct!"
        else:
            feedback = "❌ Wrong!"
        if current_index == -1 or question_history[current_index]["question_number"] != q["question_number"]:
            question_history.append(q)
            current_index = len(question_history) - 1
        status_text = f"{len(answered_correctly)} of {total_questions} correct"
        return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], selected_option, feedback, True, progress, status_text

    # Timer auto-advance
    if ctx.triggered and "feedback-timer" in ctx.triggered[0]["prop_id"]:
        q = get_random_question()
        if q:
            question_history.append(q)
            current_index = len(question_history) - 1
            # New random question → no saved selection
            return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], None, "", True, progress, status_text
        else:
            return "🎉 All questions answered correctly!", [], None, "", True, 100, status_text

    # Initial load
    if not question_history:
        q = get_random_question()
        if q:
            question_history.append(q)
            current_index = 0
            return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], None, "", True, progress, status_text
        else:
            return "No questions available", [], None, "", True, 0, "0 of 0 correct"

    q = question_history[current_index]
    saved_value = user_answers.get(q["question_number"], None)
    return q["question"], [{"label": f"{k}: {v}", "value": k} for k, v in q["options"].items()], saved_value, "", True, progress, status_text


if __name__ == "__main__":
    app.run(debug=True)