import os
import pymysql
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime

load_dotenv(dotenv_path=".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=api_key)

DB_HOST = "react-to-python-db"
DB_NAME = os.getenv("MYSQL_DATABASE")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/hello")
async def hello():
    return {"message": "Hello World!"}

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )


class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": request.question}],
    )
    answer=resp.choices[0].message.content

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO chats (question, answer) VALUES (%s, %s)"
            cursor.execute(sql, (request.question, answer))
            chat_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    return {"id": chat_id, "question": request.question, "answer": answer, "created_at": datetime.now().isoformat()}

@app.get("/chats")
async def get_chats():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM chats ORDER BY created_at ASC "
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

