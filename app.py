from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import io
import base64
import random

app = Flask(__name__)
socketio = SocketIO(app)
qr_img_base64 = None


# ------------------------------
# Настройки
# ------------------------------
HOST_PASSWORD = "radiologyadmin"
TIME_LIMIT = 15  # секунд

questions = [
    {
        "text": "Какое излучение используется при КТ?",
        "options": ["Рентгеновское", "Инфракрасное", "Ультрафиолетовое"],
        "correct": 0
    },
    {
        "text": "Что изучает маммография?",
        "options": ["Молочные железы", "Предстательную железу", "Щитовидную железу"],
        "correct": 0
    },
    {
        "text": "Какая эхогенность у структур высокой плотности?",
        "options": ["Гипоэхогенная", "Изоэхогенная", "Гиперэхогенная"],
        "correct": 2
    },
    {
        "text": "В каком сегменте легкого частая локализация туберкулеза?",
        "options": ["S7", "S9", "S6"],
        "correct": 2
    },
    {
        "text": "Как называется заращение перелома соединительной тканью после травмы?",
        "options": ["мозоль", "костная мозоль", "зарастание"],
        "correct": 1
    }
]

players = {}
current_question = -1
quiz_active = False


# ------------------------------
# Вспомогательные функции
# ------------------------------



def assign_titles(sorted_players):
    titles = []
    for idx, (name, data) in enumerate(sorted_players, start=1):
        if idx == 1:
            t = "🥇 Радиолог №1 во всём мире!"
        elif idx == 2:
            t = "🥈 Лучший диагност всех времён!"
        elif idx == 3:
            t = "🥉 Король контрастных фаз!"
        elif idx <= 5:
            t = "Мастер визуализации!"
        elif idx <= 10:
            t = "Настоящий знаток радиологии!"
        else:
            t = "Ученик великих диагностов!"
        titles.append((name, data, t))
    return titles


# ------------------------------
# Маршруты
# ------------------------------
@app.route('/')
def index():
    return redirect('/join')


@app.route('/join')
def join():
    return render_template('join.html')


@app.route('/quiz/<username>')
def quiz(username):
    return render_template('quiz.html', username=username)


@app.route('/host')
def host():
    global qr_img_base64
    url = "http://127.0.0.1:5000/join"
    if not qr_img_base64:
        qr_img_base64 = generate_qr(url)
    return render_template('host.html', join_url=url)



@app.route('/results')
def results():
    sorted_players = sorted(players.items(), key=lambda x: x[1]["score"], reverse=True)
    titles = assign_titles(sorted_players)
    return render_template('results.html', results=titles)


# ------------------------------
# Socket-события
# ------------------------------
@socketio.on('join')
def handle_join(data):
    name = data["username"]
    if name not in players:
        players[name] = {"score": 0, "answers": []}
    emit('joined', {"success": True})


@socketio.on('get_question')
def send_question(data):
    global current_question
    if 0 <= current_question < len(questions):
        emit('question', {
            "index": current_question + 1,
            "total": len(questions),
            "text": questions[current_question]["text"],
            "options": questions[current_question]["options"],
            "time": TIME_LIMIT
        })
    else:
        emit('end', {"message": "Викторина завершена!"})


@socketio.on('answer')
def handle_answer(data):
    global players
    user = data["username"]
    selected = data["answer"]
    q = questions[current_question]
    correct = q["correct"]
    if user in players:
        if selected == correct:
            players[user]["score"] += 1
            players[user]["answers"].append((q["text"], True))
        else:
            players[user]["answers"].append((q["text"], False))


@socketio.on('next_question')
def handle_next():
    global current_question, quiz_active
    current_question += 1
    if current_question < len(questions):
        quiz_active = True
        emit('new_question', broadcast=True)
    else:
        quiz_active = False
        emit('show_results', broadcast=True)


# ------------------------------
# Запуск
# ------------------------------
if __name__ == '__main__':
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)







