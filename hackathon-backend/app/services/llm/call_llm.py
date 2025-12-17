"""LLM service for OpenAI API calls."""
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.7, api_key: Optional[str] = None):
        """
        Initialize LLM Service.
        
        Args:
            model: Model name to use (default: "gpt-4o")
            temperature: Sampling temperature (default: 0.7)
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not configured")
        
        # プロキシ設定を一切指定しない（httpx エラー回避）
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            streaming=True,
            openai_api_key=self.api_key,
            # http_client の指定はしない
        )

    async def stream_invoke(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream LLM response in SSE format.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     content can be string or list (for vision)
        
        Yields:
            SSE-formatted chunks: "data: {content}\n\n"
        """
        if not self.api_key:
            error_msg = "OPENAI_API_KEY is not configured"
            logger.error(error_msg)
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        try:
            # Convert to LangChain messages
            lc_messages = []
            for msg in messages:
                content = msg["content"]
                role = msg["role"]
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    # Support both string and list content (for vision)
                    lc_messages.append(HumanMessage(content=content))
                else:  # assistant
                    lc_messages.append(AIMessage(content=content))
            
            # Stream response
            async for chunk in self.llm.astream(lc_messages):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
            
            # Send completion signal
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"LLM streaming error: {e}", exc_info=True)
            error_msg = f"LLMエラー: {str(e)}"
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"

    async def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Non-streaming invoke"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        lc_messages = [
            SystemMessage(content=msg["content"]) if msg["role"] == "system"
            else HumanMessage(content=msg["content"]) if msg["role"] == "user"
            else AIMessage(content=msg["content"])
            for msg in messages
        ]
        response = await self.llm.ainvoke(lc_messages)
        return str(response.content)
    
    async def structured_invoke(
        self,
        messages: List[Dict[str, Any]],
        response_schema: type,
        **kwargs
    ) -> Any:
        """
        Structured output invoke with Pydantic schema
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            response_schema: Pydantic model class for structured output
            **kwargs: Additional arguments
            
        Returns:
            Instance of response_schema
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        from pydantic import BaseModel as PydanticBaseModel
        
        # Convert Pydantic model to LangChain structured output
        if issubclass(response_schema, PydanticBaseModel):
            # method="json_schema" を指定（重要！）
            structured_llm = self.llm.with_structured_output(response_schema, method="json_schema")
            
            # Convert to LangChain messages
            lc_messages = []
            for msg in messages:
                content = msg["content"]
                role = msg["role"]
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                else:
                    lc_messages.append(AIMessage(content=content))
            
            response = await structured_llm.ainvoke(lc_messages)
            return response
        
        raise ValueError(f"response_schema must be a Pydantic BaseModel, got {type(response_schema)}")
