"""決定結果の型定義"""
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class ProductEngineDecision(BaseModel):
    """商品関連の意思決定結果"""
    
    action: Literal["SEARCH", "WONDER", "COMPARE", "PURCHASE"] = Field(
        description="ユーザーの行動: 'SEARCH' (商品を探している), 'WONDER' (探索的検索), 'COMPARE' (商品を比較している), 'PURCHASE' (購入を決断した)"
    )
    
    category: Optional[str] = Field(
        None,
        description="SEARCH アクションの場合の商品カテゴリー (fashion, electronics, books, sports, home, other)"
    )
    
    search_query: Optional[str] = Field(
        None,
        description="SEARCH アクションの場合の検索キーワード。ユーザーが言及した商品名、ブランド名など。例: 'ナイキ', 'ノートPC', 'スニーカー'"
    )
    
    product_ids: Optional[List[int]] = Field(
        None,
        description="COMPARE アクションの場合の比較対象商品IDリスト。COMPARE の場合のみ設定"
    )
    
    product_id: Optional[int] = Field(
        None,
        description="購入を決断した場合の商品ID。action が 'PURCHASE' の場合のみ設定"
    )

