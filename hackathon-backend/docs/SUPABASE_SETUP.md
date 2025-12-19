# Supabase Storage セットアップガイド

## 1. Supabaseバケットの作成

### 手順

1. **Supabaseダッシュボードにログイン**
   - https://app.supabase.com にアクセス
   - プロジェクトを選択（または新規作成）

2. **Storageページに移動**
   - 左サイドバーから「Storage」をクリック

3. **バケットを作成**
   - 「Create bucket」ボタンをクリック
   - 以下の設定を入力：

   **Bucket name**: `item-images`
   - ⚠️ **重要**: 作成後は変更できません
   - 小文字、数字、ハイフンのみ使用可能

   **Public bucket**: ✅ **チェックを入れる**
   - これにより、認証なしで画像にアクセスできます
   - 画像を公開表示するために必要です

   **Restrict file size**: （オプション）
   - 必要に応じて制限を設定（例: 5MB）
   - デフォルトでは制限なし

   **Restrict MIME types**: （オプション）
   - 画像のみ許可する場合: `image/jpeg,image/png,image/gif,image/webp`
   - デフォルトではすべてのタイプを許可

4. **「Create bucket」をクリック**

## 2. 環境変数の設定

### 2.1 Supabaseの認証情報を取得

1. **Supabaseダッシュボードで「Settings」→「API」を開く**

2. **以下の情報をコピー**:
   - **Project URL**: `https://xxxxx.supabase.co` の形式
   - **service_role key**: 「Service role」セクションの「secret」キー
     - ⚠️ **重要**: このキーは機密情報です。絶対に公開しないでください

### 2.2 環境変数ファイル（.env）の設定

プロジェクトのルートディレクトリ（`hackathon-backend/`）に`.env`ファイルを作成または編集します。

```bash
# プロジェクトディレクトリに移動
cd /Users/yuseimoriwaki/src/uttc-hackathon/curriculum_8_yusei_moriwaki/hackathon-backend
```

`.env`ファイルに以下を追加：

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-secret-key-here
SUPABASE_BUCKET_NAME=item-images
```

**実際の値の例**:
```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjAwMDAwMDAwLCJleHAiOjE5MTU1NjY0MDB9.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_BUCKET_NAME=item-images
```

### 2.3 .envファイルの場所確認

`.env`ファイルは以下の場所に配置します：

```
curriculum_8_yusei_moriwaki/
└── hackathon-backend/
    ├── .env              ← ここに配置
    ├── app/
    ├── alembic/
    └── ...
```

### 2.4 環境変数の確認

設定が正しいか確認：

```bash
# .envファイルの内容を確認（機密情報なので注意）
cat .env | grep SUPABASE
```

## 3. データベースマイグレーションの実行

### 3.1 マイグレーションの実行

```bash
# プロジェクトディレクトリに移動
cd /Users/yuseimoriwaki/src/uttc-hackathon/curriculum_8_yusei_moriwaki/hackathon-backend

# 仮想環境をアクティベート
source venv/bin/activate

# マイグレーションを実行
alembic upgrade head
```

### 3.2 マイグレーションの確認

マイグレーションが成功したか確認：

```bash
# 現在のマイグレーション状態を確認
alembic current

# マイグレーション履歴を確認
alembic history
```

## 4. APIの使用方法

### 4.1 アイテム作成時に画像をアップロード

**エンドポイント**: `POST /api/items`

**リクエスト形式**: `multipart/form-data`

**cURL例**:
```bash
curl -X POST "http://localhost:8000/api/items" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "title=テスト商品" \
  -F "description=商品の説明" \
  -F "price=1000" \
  -F "category=fashion" \
  -F "condition=Good" \
  -F "brand_name=テストブランド" \
  -F "image=@/path/to/image.jpg"
```

**Python例**:
```python
import requests

url = "http://localhost:8000/api/items"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
files = {"image": open("image.jpg", "rb")}
data = {
    "title": "テスト商品",
    "description": "商品の説明",
    "price": 1000,
    "category": "fashion",
    "condition": "Good",
    "brand_name": "テストブランド"
}

response = requests.post(url, headers=headers, files=files, data=data)
```

### 4.2 既存アイテムに画像を追加

**エンドポイント**: `PUT /api/items/{listing_id}/image`

**リクエスト形式**: `multipart/form-data`

**cURL例**:
```bash
curl -X PUT "http://localhost:8000/api/items/123/image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@/path/to/image.jpg"
```

**Python例**:
```python
import requests

url = "http://localhost:8000/api/items/123/image"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
files = {"image": open("image.jpg", "rb")}

response = requests.put(url, headers=headers, files=files)
```

## 5. バッチスクリプトの使用方法

### 5.1 JSONファイルの準備

`items.json`ファイルを作成：

```json
{
  "items": [
    {
      "item_id": 123456789,
      "title": "既存アイテムのタイトル",
      "description": "説明",
      "price": 1000.0,
      "category": "fashion",
      "condition": "Good",
      "brand_name": "ブランド名",
      "seller_user_id": 45,
      "image_path": "./images/item-123.jpg"
    },
    {
      "title": "新規アイテムのタイトル",
      "description": "説明",
      "price": 2000.0,
      "category": "electronics",
      "condition": "Excellent",
      "brand_name": "ブランド名",
      "seller_user_id": 45,
      "image_path": "./images/new-item.jpg"
    }
  ]
}
```

### 5.2 バッチスクリプトの実行

```bash
# プロジェクトディレクトリに移動
cd /Users/yuseimoriwaki/src/uttc-hackathon/curriculum_8_yusei_moriwaki/hackathon-backend

# 仮想環境をアクティベート
source venv/bin/activate

# バッチスクリプトを実行
python scripts/batch_upsert_items_with_images.py --input items.json
```

### 5.3 ディレクトリ構造の例

```
hackathon-backend/
├── scripts/
│   └── batch_upsert_items_with_images.py
├── items.json                    ← JSONファイル
└── images/                       ← 画像ファイルを配置
    ├── item-123.jpg
    └── new-item.jpg
```

## 6. トラブルシューティング

### 6.1 エラー: "Supabase is not configured"

- `.env`ファイルが正しい場所にあるか確認
- 環境変数名が正しいか確認（`SUPABASE_URL`, `SUPABASE_KEY`）
- アプリケーションを再起動

### 6.2 エラー: "Bucket not found"

- Supabaseダッシュボードでバケットが作成されているか確認
- `SUPABASE_BUCKET_NAME`がバケット名と一致しているか確認
- バケットが「Public」に設定されているか確認

### 6.3 エラー: "Permission denied"

- `SUPABASE_KEY`が「Service role key」であることを確認
- 「anon key」ではなく「service_role key」を使用

### 6.4 画像が表示されない

- バケットが「Public」に設定されているか確認
- 画像URLが正しい形式か確認
- ブラウザの開発者ツールでネットワークエラーを確認

## 7. セキュリティの注意事項

1. **Service Role Keyの取り扱い**
   - このキーはサーバーサイドでのみ使用してください
   - クライアントサイド（フロントエンド）では使用しないでください
   - `.env`ファイルをGitにコミットしないでください（`.gitignore`に追加）

2. **バケットの設定**
   - パブリックバケットは誰でも読み取り可能です
   - 機密情報を含む画像は別のプライベートバケットを使用してください

3. **ファイルサイズ制限**
   - 必要に応じてファイルサイズ制限を設定してください
   - デフォルトでは制限なしですが、大きなファイルはコストがかかります

