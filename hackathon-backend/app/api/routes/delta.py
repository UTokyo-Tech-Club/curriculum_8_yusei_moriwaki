from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.delta.conversation.conversation_service import conversation_stream
from app.dependencies import get_db

router = APIRouter(prefix="/api/delta", tags=["delta"])


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ConversationStreamRequest(BaseModel):
    messages: List[Message]  # メッセージ履歴をクライアントから受け取る
    # thread_id は不要


@router.post("/conversations/stream")
async def stream_conversation(
    request: ConversationStreamRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    DB を使わないストリーミング会話API
    メッセージ履歴はクライアントから受け取り、DB には保存しない
    """
    # Validate messages
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required")
    
    # Convert Pydantic models to dict for service
    messages_dict: List[Dict[str, str]] = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
        if msg.role and msg.content
    ]
    
    if not messages_dict:
        raise HTTPException(status_code=400, detail="All messages must have role and content")
    
    # ストリーミングレスポンス
    return StreamingResponse(
        conversation_stream(messages=messages_dict, db=db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

