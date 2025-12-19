"""決定結果の型定義"""
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class ProductEngineDecision(BaseModel):
    """商品関連の分析結果"""
    
    action: Literal["SEARCH", "WONDER", "COMPARE", "PURCHASE"] = Field(
        description="ユーザーの行動: 'SEARCH' (商品を探している), 'WONDER' (探索的検索), 'COMPARE' (商品を比較している), 'PURCHASE' (購入を決断した)"
    )
    
    search_query: Optional[str] = Field(
        None,
        description="SEARCH アクションの場合の検索キーワード。ユーザーが探している、欲しがっている商品名、ブランド名、特徴などを抽出。例: 'ナイキ', 'ノートPC', 'スニーカー', '赤いバッグ'"
    )
    
    product_ids: Optional[List[int]] = Field(
        None,
        description="COMPARE アクションの場合の比較対象商品IDリスト。COMPARE の場合のみ設定"
    )
    
    product_id: Optional[int] = Field(
        None,
        description="購入を決断した場合の商品ID。action が 'PURCHASE' の場合のみ設定"
    )

