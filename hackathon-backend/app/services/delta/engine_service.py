"""商品関連の意思決定分析（最小版）"""
import logging
from typing import List, Dict

from app.services.llm.call_llm import LLMService
from .models.engine_decision import ProductEngineDecision

logger = logging.getLogger(__name__)

ENGINE_SYSTEM_PROMPT = """あなたはユーザーの商品関連の行動を分析するAIです。

会話履歴から、ユーザーが以下のどの状態かを判断してください：

1. **SEARCH**: ユーザーが商品を探している
   - 「ナイキのスニーカー探してる」「ノートPCが欲しい」「赤いバッグ」など
   - 商品について質問しているが、特定の商品はまだ決めていない
   - **検索キーワード抽出**: ユーザーが探している、欲しがっている商品名、ブランド名、特徴などを search_query に設定
     - 例: 「ナイキのスニーカー探してる」→ search_query: "ナイキ スニーカー"
     - 例: 「ノートPCが欲しい」→ search_query: "ノートPC"
     - 例: 「赤いバッグ」→ search_query: "赤い バッグ"
     - 検索キーワードがない場合は search_query は null

2. **WONDER**: ユーザーが探索的に商品を見ている
   - 「何かおすすめは？」「面白い商品ある？」「何がいいかわからない」など
   - 特定の意図がない探索的検索

3. **COMPARE**: ユーザーが提示された複数の商品を比較している
   - 「AとBどっちがいい？」「違いは？」「比較したい」など
   - 複数の商品IDが提示されていて、それらを比較検討している
   - product_ids フィールドに比較対象の商品IDリストを設定

4. **PURCHASE**: ユーザーが購入を決断した
   - 「これにする」「買います」「購入します」「決めました」など
   - 明確に購入意思を示している
   - 商品IDが特定できる場合のみ product_id を設定

**重要**:
- action が "SEARCH" の場合のみ search_query を設定
- search_query はユーザーが探している、欲しがっている商品に関するキーワード（商品名、ブランド名、特徴など）
- action が "COMPARE" の場合のみ product_ids を設定（リスト）
- action が "PURCHASE" の場合のみ product_id を設定（単一）
- 商品IDが特定できない場合は該当フィールドは null
- 曖昧な場合は "WONDER" を選択

出力はJSONのみ。説明は不要です。
"""


async def make_product_engine_decision(
    messages: List[Dict[str, str]]
) -> ProductEngineDecision:
    """
    メッセージ履歴から商品関連の意思決定を行う
    
    Args:
        messages: メッセージ履歴 [{"role": "user", "content": "..."}, ...]
    
    Returns:
        ProductEngineDecision: 分析結果
    """
    if not messages:
        return ProductEngineDecision(action="WONDER")
    
    # 最後の数件のメッセージを使用（最大6件）
    recent_messages = messages[-6:] if len(messages) > 6 else messages
    
    # LLM で意思決定
    llm_messages = [
        {"role": "system", "content": ENGINE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"会話履歴:\n" + "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in recent_messages
            ])
        }
    ]
    
    try:
        llm_service = LLMService(model="gpt-4o", temperature=0.3)
        decision = await llm_service.structured_invoke(
            llm_messages,
            ProductEngineDecision
        )
        # 分析結果をログとprintで出力
        print("=" * 60)
        print("【商品分析結果】")
        print(f"Action: {decision.action}")
        if decision.search_query:
            print(f"Search Query: {decision.search_query}")
        if decision.product_id:
            print(f"Product ID: {decision.product_id}")
        if decision.product_ids:
            print(f"Product IDs: {decision.product_ids}")
        print("=" * 60)
        
        logger.debug("Product Analysis Decision")
        logger.debug(f"Action: {decision.action}")
        if decision.search_query:
            logger.debug(f"Search Query: {decision.search_query}")
        if decision.product_id:
            logger.debug(f"Product ID: {decision.product_id}")
        if decision.product_ids:
            logger.debug(f"Product IDs: {decision.product_ids}")
        
        logger.info(
            f"Product analysis: action={decision.action}, "
            f"search_query={decision.search_query}, "
            f"product_id={decision.product_id}, "
            f"product_ids={decision.product_ids}"
        )
        return decision
    except Exception as e:
        logger.error(f"Error making product analysis: {e}")
        print(f"【エラー】商品分析中にエラーが発生: {e}")
        return ProductEngineDecision(action="WONDER")

