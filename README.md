# AI Flea Market

AI Flea Market は、東京大学工学部電気系 Web 研修ハッカソン向けに作成した、AI 活用型の次世代フリマアプリです。
ユーザー登録、商品出品、商品購入、DM、コメント、通知といった基本的なフリマ機能に加えて、Gemini / Vertex AI による商品説明生成、購入前チェック、商品質問応答、MerRec データセットを想定した推薦分析を組み込んでいます。

この zip は、Demo Day で主要機能を一通り見せられるように、初期ユーザー4名と初期商品20件を `001_init.sql` に同梱しています。

---

## 1. ディレクトリ構成

```text
hackathon-parent/
├── .gitignore                         # 親リポジトリ用の除外設定
├── docker-compose.local.yml           # ローカル MySQL 起動用
├── hackathon_ui_ux_design.drawio      # UI/UX設計ファイル
├── hackathon_db_api_design.xlsx       # DB/API設計ファイル
├── README.md                          # このファイル
├── IMPLEMENTATION_NOTES.md            # 実装詳細・設計意図
├── DEPLOY_GCP.md                      # GCPデプロイ手順
├── hackathon-backend/                 # Goバックエンド
├── hackathon-frontend/                # React + TypeScript フロントエンド
└── ml/                                # MerRec分析・Python推論サーバー
```

親ディレクトリ直下に `.gitignore`、`docker-compose.local.yml`、`hackathon_ui_ux_design.drawio`、`hackathon_db_api_design.xlsx` を必ず含めています。

---

## 2. 主な機能

### 基本機能

- ユーザー登録・ログイン・ログアウト
- 商品一覧表示
- Amazon / Mercari 風の左サイドバー検索
- 商品出品
- 複数画像アップロード
- 出品画像の削除
- 商品編集時の画像追加・削除
- 商品詳細での画像カルーセル
- 商品購入手続き
- 残高チャージ
- 購入履歴
- 出品履歴
- チェックリスト
- 公開コメント
- コメントへの返信スレッド
- 非公開DM
- 通知一覧
- マイページ
- 住所・発送元地域登録
- ブロック機能
- 出品キャンセル

### デモ用初期データ

- `user1@example.com / user1111`
- `user2@example.com / user2222`
- `user3@example.com / user3333`
- `user4@example.com / user4444`

各ユーザーが5件ずつ、合計20件の商品を出品済みです。商品名・説明・発送元・タグは自然な日本語で入力し、カテゴリ・状態・受け渡し方法・サイズ・色はフロントエンドのプルダウン候補に存在する値だけを使っています。

### AI機能

- 出品画面での商品説明生成
- 商品詳細画面での商品質問応答
- 商品説明・カテゴリ・状態・価格に基づく購入前AIチェック
- 商品説明から購入者が確認すべき不安点の提示
- 出品文・カテゴリ・状態の不整合チェック
- 類似商品と比較した価格妥当性チェック
- MerRec データセットを想定したおすすめ商品欄
- MerRec streaming 分析スクリプト
- MerRec pickle モデル用 Python 推論サーバー

外部AIが使えない場合でも、デモ中に画面が止まらないよう、ローカル簡易生成へフォールバックします。
ただし、外部AIが失敗した場合はバックエンドログに原因を表示するので、Vertex AI の設定や利用枠を確認できます。

---

## 3. ローカル起動手順

以下では、ターミナルを3つ使います。

---

### Terminal 1: MySQLを初期化する

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent

docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d

docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

日本語が文字化けしていないか確認します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, title, ship_from_region, tags FROM items ORDER BY id LIMIT 5;"'
```

`微分積分学の参考書`、`東京都` などが正しく表示されれば成功です。

---

### Terminal 2: Goバックエンドを起動する

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent/hackathon-backend

cp .env.example .env
```

外部AIを使う場合は `.env` を編集します。

```env
AI_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=実際のGCPプロジェクトID
VERTEX_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash
```

認証とAPI有効化を確認します。

```bash
gcloud config set project 実際のGCPプロジェクトID
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

依存関係とテストです。

```bash
go mod tidy
go test ./...
```

起動します。

```bash
set -a
source .env
set +a

go run ./cmd/server
```

別ターミナルで確認する場合は次です。

```bash
curl http://localhost:8080/healthz
```

---

### Terminal 3: Reactフロントエンドを起動する

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent/hackathon-frontend

npm config set registry https://registry.npmjs.org/
npm config delete proxy
npm config delete https-proxy

rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/

npm run build
npm run dev
```

ブラウザで開きます。

```text
http://localhost:5173
```

---

## 4. Vertex AI の確認

AI生成時に次のようなログが出る場合があります。

```text
ResourceExhausted desc = Resource exhausted. Please try again later.
```

これは、モデル名や認証ミスではなく、Vertex AI 側の共有処理容量・レート制限・利用枠に起因する 429 です。
この zip では以下の対策を入れています。

- 標準モデルを `gemini-2.5-flash` に変更
- 標準ロケーションを `global` に変更
- 5回の短い指数バックオフ付きリトライ
- 失敗時のローカル簡易生成フォールバック
- バックエンドログへの原因出力

Vertex AI が成功している場合、Terminal 2 に `external AI generation failed` が出ません。

確認コマンドです。

```bash
gcloud config get-value project
gcloud auth list
gcloud auth application-default print-access-token
gcloud services list --enabled | grep aiplatform
```

利用枠は Google Cloud Console の `IAM と管理 > 割り当てとシステム上限` で、`Vertex AI API` または `aiplatform.googleapis.com` をフィルタして確認してください。

---

## 5. MerRec 分析・推論サーバー

### Python環境を作る

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent

python3 -m venv .venv-ml
source .venv-ml/bin/activate

python -m pip install -U pip
python -m pip install -r ml/requirements.txt
python -m pip install dataset
```

### サンプルデータで学習する

```bash
python ml/merrec_recommender.py \
  --input ml/sample_merrec.csv \
  --out-json ml/sample_artifact.json \
  --out-pkl ml/sample_model.pkl \
  --limit 1000 \
  --topk 3
```

### pickleを確認する

```bash
python - <<'PY'
import pickle
import sys

sys.path.insert(0, "ml")
from merrec_model import MerRecModel

with open("ml/sample_model.pkl", "rb") as f:
    model = pickle.load(f)

print(type(model))
print(isinstance(model, MerRecModel))
print("items:", len(model.items))
print("version:", model.version)
PY
```

### 推論サーバーを起動する

```bash
python ml/recommender_service.py \
  --model ml/sample_model.pkl \
  --port 8099
```

別ターミナルで確認します。

```bash
curl http://127.0.0.1:8099/healthz

curl -X POST http://127.0.0.1:8099/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "calculus math book",
    "category": "Books Education Math",
    "price": 13,
    "top_k": 2
  }'
```

### Hugging Face streaming で MerRec を読む

```bash
rm -f ml/merrec_model.pkl ml/merrec_artifact.json

python ml/merrec_recommender.py \
  --hf \
  --hf-dataset mercari-us/merrec \
  --hf-split train \
  --out-json ml/merrec_artifact.json \
  --out-pkl ml/merrec_model.pkl \
  --limit 50000 \
  --topk 30
```

---

## 6. Demo Dayで見せやすい確認シナリオ

1. `user1@example.com / user1111` でログイン
2. 商品一覧で20件の初期商品を確認
3. 左サイドバー検索でカテゴリや価格を絞り込む
4. 商品詳細で複数画像カルーセルを確認
5. AIに商品について質問する
6. 商品をチェックリストに追加
7. 別ユーザーでログインして購入手続き
8. 出品者側で発送通知
9. 購入者側で受け取り評価
10. マイページで残高、利用額、売上額、出品者評価を確認

---

## 7. 実装上の設計方針

- バックエンドは handler / repository / model / ai に責務分離
- フロントエンドは page / api / context / utils に分離
- 商品画像は単一URL文字列と複数画像JSON配列の両方に対応
- DBは既存データを消してよい前提で `001_init.sql` に統合
- 文字化け対策として `utf8mb4` を明示
- AI外部APIの失敗時もユーザー操作が止まらないようフォールバック
- MerRec実データの分析は `ml/` に分離し、Webアプリ本体とは疎結合化


---

## 2026-06-17 最終UI/AI検索整理メモ

### 商品一覧トップの改善

今回の版では、商品一覧ページの上部を次のように整理しています。

- 左サイドバー検索をページ上部まで引き上げ、右上の空白をなくしました。
- サイドバー検索欄に淡い青系の背景を付け、検索エリアであることが分かりやすいUIにしました。
- おすすめ商品欄を淡いオレンジ系の強調カードにし、Demo Dayで目立つようにしました。
- おすすめ商品は最大8件表示します。
- ヘッダー、商品カード、検索欄、レコメンド欄に一貫した色を付け、全体の見栄えを整えました。

### 生成AIを活用した自然言語検索

「AIが出品と購入判断を支援する次世代フリマ」の右側に、自然言語検索欄を追加しました。

例:

- `予算1万円以内で探して`
- `使用感が少なくてきれいなものを安い順に並べて`
- `数学の参考書を安い順に探して`
- `明日までに発送できるイヤホンを探して`

内部的には、入力文をバックエンドの `/api/ai/parse-search` に送り、Gemini / Vertex AI が使える場合はAIで検索条件JSONへ変換します。外部AIが429や認証未設定で失敗した場合でも、ローカル規則で最低限の条件変換を行います。そのため、Demo Day中にVertex AIが混雑しても自然言語検索ボックス自体は動きます。

返される検索条件は、既存の商品一覧APIと同じ形式です。

```json
{
  "q": "参考書",
  "category": "本・教材",
  "condition": "未使用に近い,目立った傷や汚れなし",
  "maxPrice": "10000",
  "sort": "price_asc"
}
```

この設計により、自然言語検索は既存の通常検索・保存検索条件・サイドバー検索と衝突せず、同じ検索ロジックを再利用します。

### Vertex AIが429になる場合

`ResourceExhausted` は、設定ミスではなく、Vertex AIの共有処理容量または割り当て上限に当たっている可能性が高いです。今回の版では、`.env.example` の推奨値を次にしています。

```env
AI_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=実際のGCPプロジェクトID
VERTEX_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash
```

`global` endpoint と `gemini-2.5-flash` を使っても429が続く場合は、時間を空ける、利用量の少ない時間帯で試す、Google Cloud Console の `IAM と管理 > 割り当てとシステム上限` から Vertex AI API の使用量と上限を確認する、必要に応じて quota increase request を出す、などを行ってください。
