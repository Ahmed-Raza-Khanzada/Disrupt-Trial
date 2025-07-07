# from pymongo import MongoClient
# from datetime import datetime

# from pymongo import MongoClient
##Connecttion issue with mongodb
# # client = MongoClient()
# client = MongoClient("mongodb+srv://ahmed:)
# db = client["chat_db"]

# conversations = db["conversations"]

# def get_or_create_conversation(session_id):
#     conv = conversations.find_one({"session_id": session_id})
#     if not conv:
#         conversations.insert_one({"session_id": session_id, "messages": []})

# def add_message(session_id, sender, text):
#     msg = {
#         "sender": sender,
#         "text": text,
#         "timestamp": datetime.utcnow()
#     }
#     conversations.update_one(
#         {"session_id": session_id},
#         {"$push": {"messages": msg}}
#     )
#     return msg

# def get_messages(session_id):
#     conv = conversations.find_one({"session_id": session_id})
#     return conv.get("messages", []) if conv else []



##Connecttion issue with mongodb
#thats why using sql alchemy for database operations
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///chat.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('conversations.session_id'))
    sender = Column(String)
    text = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


Base.metadata.create_all(engine)

def get_or_create_conversation(session_id):
    conv = db.query(Conversation).filter_by(session_id=session_id).first()
    if not conv:
        conv = Conversation(session_id=session_id)
        db.add(conv)
        db.commit()

def add_message(session_id, sender, text):
    msg = Message(session_id=session_id, sender=sender, text=text)
    db.add(msg)
    db.commit()
    return {"sender": sender, "text": text, "timestamp": msg.timestamp}

def get_messages(session_id):
    return [
        {
            "sender": msg.sender,
            "text": msg.text,
            "timestamp": msg.timestamp
        }
        for msg in db.query(Message).filter_by(session_id=session_id).order_by(Message.timestamp).all()
    ]




def get_all_sessions():
    conv = db.query(Conversation).filter_by(session_id=session_id).first()
    if not conv:
        conv = Conversation(session_id=session_id)
        db.add(conv)
        db.commit()
