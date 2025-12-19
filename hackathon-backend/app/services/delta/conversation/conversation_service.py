"""会話ストリーミングサービス（商品分析統合版）"""
import logging
import json
from datetime import datetime
from typing import AsyncGenerator, List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.call_llm import LLMService
from app.services.delta.engine_service import make_product_engine_decision
from app.repositories.item_repository import ItemRepository
from app.services.item_service import ItemService
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# 最新のGPT-4oモデルを使用（ストリーミング対応）
STREAM_CHAT_MODEL = "gpt-4o"


async def conversation_stream(
    messages: List[Dict[str, str]],
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    商品分析統合版のストリーミング会話
    """
    try:
        # ============================================
        # 背景分析を実行
        # ============================================
        engine_decision = await make_product_engine_decision(messages)
        
        # 分析結果をログに出力（printはengine_serviceで実行済み）
        logger.debug("Conversation Service - Analysis Result")
        logger.debug(f"Action: {engine_decision.action}")
        if engine_decision.search_query:
            logger.debug(f"Search Query: {engine_decision.search_query}")
        if engine_decision.product_id:
            logger.debug(f"Product ID: {engine_decision.product_id}")
        if engine_decision.product_ids:
            logger.debug(f"Product IDs: {engine_decision.product_ids}")
        
        logger.info(
            f"Analysis result: action={engine_decision.action}, "
            f"search_query={engine_decision.search_query}, "
            f"product_id={engine_decision.product_id}, "
            f"product_ids={engine_decision.product_ids}"
        )
        
        # ============================================
        # 商品データの取得（SEARCH または PURCHASE の場合）
        # ============================================
        # 商品リストを初期化（必ず定義されるように最初に初期化）
        items: List[Dict] = []
        
        if db:
            try:
                item_repo = ItemRepository(db)
                
                if engine_decision.action == "SEARCH":
                    # SEARCH: SQL検索とベクトル検索を並行実行し、SQL検索結果を優先
                    user_repo = UserRepository(db)
                    item_service = ItemService(item_repo, user_repo)
                    
                    sql_items: List[Dict] = []
                    vector_items: List[Dict] = []
                    
                    # SQL検索を実行（limit=3）
                    try:
                        if engine_decision.search_query:
                            # 検索キーワードでSQL検索
                            search_items = await item_repo.get_items_with_details(
                                search=engine_decision.search_query,
                                status="available",
                                limit=3,
                                offset=0
                            )
                            sql_items = search_items[:3] if search_items else []
                    except Exception as sql_error:
                        logger.warning(f"SQL search failed: {sql_error}")
                        sql_items = []
                    
                    # ベクトル検索を並行実行
                    try:
                        if engine_decision.search_query:
                            vector_items = await item_service.search_items_vector(
                                query=engine_decision.search_query,
                                category=None,
                                limit=3
                            )
                    except Exception as vector_error:
                        logger.warning(f"Vector search failed: {vector_error}")
                        vector_items = []
                    
                    # SQL検索結果を優先し、ベクトル検索結果で不足分を補完
                    items = []
                    
                    # SQL検索結果を追加
                    items.extend(sql_items)
                    
                    # SQL検索結果のIDセットを作成（重複除外用）
                    sql_item_ids = {item.get("id") for item in sql_items}
                    
                    # ベクトル検索結果から重複を除外して不足分を補完
                    remaining_slots = 3 - len(items)
                    if remaining_slots > 0 and vector_items:
                        for vector_item in vector_items:
                            if len(items) >= 3:
                                break
                            if vector_item.get("id") not in sql_item_ids:
                                items.append(vector_item)
                    
                    logger.info(
                        f"Fetched {len(items)} items (SQL: {len(sql_items)}, Vector: {len([v for v in vector_items if v.get('id') not in sql_item_ids])} unique)"
                    )
                
                elif engine_decision.action == "PURCHASE" and engine_decision.product_id:
                    # PURCHASE: 商品IDから1つの商品を取得
                    item = await item_repo.get_item_with_details(engine_decision.product_id)
                    if item:
                        items = [item]
                        logger.info(f"Fetched 1 item for PURCHASE action with product_id {engine_decision.product_id}")
                    else:
                        logger.warning(f"Item not found for PURCHASE with product_id {engine_decision.product_id}")
                else:
                    logger.info(f"No items fetched for action: {engine_decision.action}")
                    
            except Exception as item_error:
                logger.error(f"Error fetching items: {item_error}", exc_info=True)
                items = []  # エラー時も空リストを保証
        
        logger.debug(f"Items fetched: {len(items)}")
        
        # メッセージ履歴を制限
        limited_messages = messages[-10:] if len(messages) > 10 else messages
        
        # システムプロンプトを構築（分析結果と商品データを反映）
        system_content = _build_system_prompt(engine_decision, items)
        
        # LLM メッセージリスト
        llm_messages = [
            {"role": "system", "content": system_content}
        ] + [
            {"role": msg["role"], "content": msg["content"]}
            for msg in limited_messages
        ]
        
        # LLM ストリーミング
        llm_service = LLMService(model=STREAM_CHAT_MODEL, temperature=0.7)
        
        # 商品データがある場合は、最初に商品データを送信
        if items and len(items) > 0:
            try:
                items_data = json.dumps({"type": "items", "items": items}, ensure_ascii=False)
                yield f"data: {items_data}\n\n"
                logger.info(f"Sent {len(items)} items to client")
            except Exception as send_error:
                logger.error(f"Error sending items data: {send_error}", exc_info=True)
        
        async for chunk in llm_service.stream_invoke(llm_messages):
            content = chunk.removeprefix("data: ").removesuffix("\n\n")
            
            # [DONE] シグナルをそのまま転送
            if content == "[DONE]":
                yield "data: [DONE]\n\n"
                continue
            
            wrapped_chunk = json.dumps({"data": content}, ensure_ascii=False)
            yield f"data: {wrapped_chunk}\n\n"
    
    except Exception as e:
        error_message = f"エラーが発生しました: {str(e)}"
        logger.error(f"Conversation error: {type(e).__name__}: {e}", exc_info=True)
        yield f"data: {json.dumps({'data': error_message}, ensure_ascii=False)}\n\n"


def _get_monthly_event_prompt() -> str:
    """現在の月に基づいたイベントプロンプトを生成"""
    now = datetime.now()
    month = now.month
    
    month_events = {
        1: "新年・お正月",
        2: "バレンタインデー",
        3: "卒業・入学シーズン",
        4: "新生活・入学シーズン",
        5: "ゴールデンウィーク・母の日",
        6: "梅雨・父の日",
        7: "夏休み・お盆",
        8: "夏休み・お盆",
        9: "新学期・敬老の日",
        10: "ハロウィン",
        11: "文化の日・七五三",
        12: "クリスマス・年末年始"
    }
    
    event = month_events.get(month, "特別なイベント")
    return f"今月は{month}月なので、{event}のためにも"


def _build_system_prompt(decision, items: List[Dict] = None) -> str:
    """分析結果を反映したシステムプロンプトを構築"""
    if items is None:
        items = []
    
    # 月のイベントプロンプトを取得
    monthly_event = _get_monthly_event_prompt()
    
    base_prompt = "あなたは商品販売をサポートする親切なAIアシスタントです。日本語で応答してください。\n\n"
    base_prompt += "【重要な指示】\n"
    base_prompt += "- おすすめの商品は目立つようにアピールしてください（絵文字🎯✨🔥💎🎁などを適切に使用）\n"
    base_prompt += "- 説明は長くなりすぎないように、簡潔で分かりやすくしてください\n"
    base_prompt += "- 商品を紹介する際は「商品番号: ID」のようにスタイリッシュに表示してください\n\n"
    
    # 最初の訴求として月のイベントを追加
    base_prompt += f"【最初の訴求】\n{monthly_event}、ゲームやイヤホンなどいかがでしょうか！\n\n"
    
    if decision.action == "SEARCH":
        base_prompt += "ユーザーは商品を探しています。\n"
        
        # 検索キーワードがある場合はプロンプトに含める
        if decision.search_query:
            base_prompt += f"検索キーワード: 「{decision.search_query}」で商品を検索しました。\n"
        
        # 取得した商品情報をプロンプトに含める
        if items and len(items) > 0:
            base_prompt += "\n以下の商品が表示されています。これらの商品について言及し、ユーザーが選択できるようにサポートしてください：\n"
            for idx, item in enumerate(items, 1):
                title = item.get("title", "商品名なし")
                price = item.get("price", 0)
                description = item.get("description", "")
                item_id = item.get("id", "")
                base_prompt += f"\n【商品{idx}】\n"
                base_prompt += f"- 商品名: {title}\n"
                base_prompt += f"- 価格: ¥{price:,.0f}\n"
                base_prompt += f"- 商品番号: {item_id}\n"
                if description:
                    desc_preview = description[:100] + "..." if len(description) > 100 else description
                    base_prompt += f"- 説明: {desc_preview}\n"
            base_prompt += "\nこれらの商品について詳しく説明し、ユーザーのニーズに合う商品を推薦してください。おすすめの商品は絵文字を使って目立つようにアピールしてください。"
            if decision.search_query:
                base_prompt += f"\n特に「{decision.search_query}」に関連する商品について重点的に説明してください。"
        else:
            base_prompt += "適切な商品を提案してください。"
            if decision.search_query:
                base_prompt += f"\n「{decision.search_query}」に関連する商品を探しましたが、見つかりませんでした。類似の商品を提案してください。"
    
    elif decision.action == "WONDER":
        base_prompt += "ユーザーは探索的に商品を見ています。興味深い商品を提案してください。"
    
    elif decision.action == "COMPARE":
        # 商品IDは含めない
        base_prompt += "ユーザーは商品を比較しています。これらの商品の詳細な説明を読み込み、違いや特徴を分かりやすく説明してください。"
    
    elif decision.action == "PURCHASE":
        # 商品IDは含めない
        if items and len(items) > 0:
            purchase_item = items[0]
            title = purchase_item.get("title", "商品名なし")
            price = purchase_item.get("price", 0)
            base_prompt += f"\nユーザーは「{title} (¥{price:,.0f})」の購入を決断しました。"
        else:
            base_prompt += "\nユーザーは購入を決断しました。"
        base_prompt += "\n購入手続きをサポートしてください。"
    
    return base_prompt
