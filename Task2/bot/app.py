from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import uuid

from db_models import get_or_create_conversation, add_message, get_messages
from engine import get_engine
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key'
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

@app.route("/")
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template("client.html", session_id=session['session_id'])

@socketio.on('join_client')
def handle_join_client(data):
    session_id = data.get('room') or str(uuid.uuid4())
    join_room(session_id)
    set_cookie = data.get('room') is None
    get_or_create_conversation(session_id)
    messages = get_messages(session_id)

    emit('room_assigned', {
        "room": session_id,
        "chathistory": [{"sender": m["sender"], "message": m["text"]} for m in messages]
    })

@socketio.on('client_message')
def handle_client_message(data):
    session_id = data.get('room')
    text = data.get('message')

    user_msg = add_message(session_id, 'client', text)
    emit('client_message', {"message": text, "flag": True}, room=session_id)
    messages = get_messages(session_id)
    bot_reply = call_gemini(text,messages)
    bot_msg = add_message(session_id, 'bot', bot_reply)
    emit('bot_message', {"message": bot_reply}, room=session_id)





llm = get_engine()
def call_gemini(query,messages):
    print(messages)
    all_msg = "\n".join(
        [f"{msg['sender']}: {msg['text']}" for msg in messages]
    )
    prompt = (
            f"You are an helpfull assistant you have to answer on based of conversation and given query.\n\n"
            f"Chat Context:\n{all_msg}\n\nQuestion: {query}\n\nAnswer:"
        )
    response = llm.generate_content(prompt)
    return response.text if hasattr(response, 'text') else str(response)
    

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
