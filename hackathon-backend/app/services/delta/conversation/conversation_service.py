"""会話ストリーミングサービス（商品エンジン統合版）"""
import logging
import json
from typing import AsyncGenerator, List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.call_llm import LLMService
from app.services.delta.engine_service import make_product_engine_decision
from app.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)

STREAM_CHAT_MODEL = "gpt-4o"


async def conversation_stream(
    messages: List[Dict[str, str]],
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    商品エンジン統合版のストリーミング会話
    """
    try:
        # ============================================
        # 背景意思決定を実行
        # ============================================
        engine_decision = await make_product_engine_decision(messages)
        
        # エンジンの決定結果をログに出力
        logger.debug("Conversation Service - Engine Decision")
        logger.debug(f"Action: {engine_decision.action}")
        if engine_decision.category:
            logger.debug(f"Category: {engine_decision.category}")
        if engine_decision.search_query:
            logger.debug(f"Search Query: {engine_decision.search_query}")
        if engine_decision.product_id:
            logger.debug(f"Product ID: {engine_decision.product_id}")
        if engine_decision.product_ids:
            logger.debug(f"Product IDs: {engine_decision.product_ids}")
        
        logger.info(
            f"Engine decision: action={engine_decision.action}, "
            f"category={engine_decision.category}, "
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
                    # SEARCH: まず検索キーワードで検索し、その後カテゴリーで絞り込む
                    if engine_decision.search_query:
                        # まず検索キーワードだけで検索（より多くの候補を取得）
                        search_items = await item_repo.get_items_with_details(
                            search=engine_decision.search_query,
                            status="available",
                            limit=10,  # より多くの候補を取得
                            offset=0
                        )
                        
                        # カテゴリーがある場合、検索結果をカテゴリーでフィルタリング
                        if engine_decision.category and search_items:
                            category_filtered = [
                                item for item in search_items
                                if item.get("category") == engine_decision.category
                            ]
                            
                            # カテゴリーで絞った結果が3件以上あればそれを使用
                            if len(category_filtered) >= 3:
                                items = category_filtered[:3]
                                logger.info(
                                    f"Fetched {len(items)} items filtered by category from search results "
                                    f"(search: {engine_decision.search_query}, category: {engine_decision.category})"
                                )
                            # カテゴリーで絞った結果が3件未満なら、元の検索結果から上から3件を使用
                            else:
                                items = search_items[:3]
                                logger.info(
                                    f"Fetched {len(items)} items from search "
                                    f"(category filter resulted in {len(category_filtered)} items, using top search results)"
                                )
                        else:
                            # カテゴリーがない場合、検索結果から上から3件
                            items = search_items[:3] if search_items else []
                            logger.info(
                                f"Fetched {len(items)} items from search without category filter "
                                f"(search: {engine_decision.search_query})"
                            )
                    elif engine_decision.category:
                        # 検索キーワードがない場合、カテゴリーのみで検索
                        category_items = await item_repo.get_items_with_details(
                            category=engine_decision.category,
                            status="available",
                            limit=3,
                            offset=0
                        )
                        items = category_items[:3] if category_items else []
                        logger.info(f"Fetched {len(items)} items for SEARCH action with category {engine_decision.category}")
                
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
        
        # システムプロンプトを構築（エンジンの決定と商品データを反映）
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


def _build_system_prompt(decision, items: List[Dict] = None) -> str:
    """エンジンの決定を反映したシステムプロンプトを構築"""
    if items is None:
        items = []
    
    base_prompt = "あなたは商品販売をサポートする親切なAIアシスタントです。日本語で応答してください。"
    
    if decision.action == "SEARCH":
        if decision.category:
            base_prompt += f"\n\nユーザーは{decision.category}カテゴリーの商品を探しています。"
        else:
            base_prompt += "\n\nユーザーは商品を探しています。"
        
        # 検索キーワードがある場合はプロンプトに含める
        if decision.search_query:
            base_prompt += f"\n検索キーワード: 「{decision.search_query}」で商品を検索しました。"
        
        # 取得した商品情報をプロンプトに含める
        if items and len(items) > 0:
            base_prompt += "\n\n以下の商品が表示されています。これらの商品について言及し、ユーザーが選択できるようにサポートしてください：\n"
            for idx, item in enumerate(items, 1):
                title = item.get("title", "商品名なし")
                price = item.get("price", 0)
                description = item.get("description", "")
                item_id = item.get("id", "")
                base_prompt += f"\n【商品{idx}】\n"
                base_prompt += f"- 商品ID: {item_id}\n"
                base_prompt += f"- 商品名: {title}\n"
                base_prompt += f"- 価格: ¥{price:,.0f}\n"
                if description:
                    desc_preview = description[:100] + "..." if len(description) > 100 else description
                    base_prompt += f"- 説明: {desc_preview}\n"
            base_prompt += "\nこれらの商品について詳しく説明し、ユーザーのニーズに合う商品を推薦してください。"
            if decision.search_query:
                base_prompt += f"\n特に「{decision.search_query}」に関連する商品について重点的に説明してください。"
        else:
            base_prompt += "適切な商品を提案してください。"
            if decision.search_query:
                base_prompt += f"\n「{decision.search_query}」に関連する商品を探しましたが、見つかりませんでした。類似の商品を提案してください。"
    
    elif decision.action == "WONDER":
        base_prompt += "\n\nユーザーは探索的に商品を見ています。興味深い商品を提案してください。"
    
    elif decision.action == "COMPARE":
        if decision.product_ids:
            base_prompt += f"\n\nユーザーは商品ID {decision.product_ids} を比較しています。これらの商品の詳細な説明を読み込み、違いや特徴を分かりやすく説明してください。"
        else:
            base_prompt += "\n\nユーザーは商品を比較しています。商品の違いや特徴を分かりやすく説明してください。"
    
    elif decision.action == "PURCHASE":
        if decision.product_id:
            # 購入する商品の情報をプロンプトに含める
            purchase_item = None
            if items and len(items) > 0:
                purchase_item = items[0]
            
            base_prompt += f"\n\nユーザーは商品ID {decision.product_id} の購入を決断しました。"
            if purchase_item:
                title = purchase_item.get("title", "商品名なし")
                price = purchase_item.get("price", 0)
                base_prompt += f"\n購入する商品: {title} (¥{price:,.0f})"
            base_prompt += "\n購入手続きをサポートしてください。"
        else:
            base_prompt += "\n\nユーザーは購入を決断しました。購入手続きをサポートしてください。"
    
    return base_prompt
