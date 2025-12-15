import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set"
        )
    return OpenAI(api_key=api_key)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    client = get_openai_client()

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": request.question}],
    )

    answer = resp.choices[0].message.content
    return {"answer": answer}