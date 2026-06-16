# AI Flea Market

AI Flea Market は、東京大学工学部電気系 Web 研修ハッカソン向けに作成した、AI 活用型の次世代フリマアプリです。
通常のフリマアプリに必要な「登録・出品・購入・DM・通知」に加え、Gemini / Vertex AI、ローカルAIフォールバック、MerRecデータセット分析、自然言語検索、購入前AIチェックを組み込んでいます。

Demo Day ですぐ見せられるように、初期ユーザー4名と初期商品20件を `hackathon-backend/migrations/001_init.sql` に同梱しています。

---

## 1. ディレクトリ構成

```text
hackathon-parent/
├── .gitignore                         # 親リポジトリ全体の除外設定
├── docker-compose.local.yml           # ローカルMySQL起動用Compose
├── hackathon_ui_ux_design.drawio      # UI/UX設計ファイル
├── hackathon_db_api_design.xlsx       # DB/API設計ファイル
├── README.md                          # 実行手順・機能一覧
├── IMPLEMENTATION_NOTES.md            # 実装意図・細かい設計メモ
├── DEPLOY_GCP.md                      # GCPデプロイ手順
├── docs/
│   ├── ARCHITECTURE.md                # アーキテクチャ整理
│   └── DEMO_SCRIPT.md                 # Demo Day 用の見せ方
├── hackathon-backend/                 # Goバックエンド
├── hackathon-frontend/                # React + TypeScriptフロントエンド
└── ml/                                # MerRec分析・Python推論サーバー
```

---

## 2. 実装済みの基本機能

- ユーザー登録、ログイン、ログアウト
- JWT認証
- 商品一覧表示
- Amazon / Mercari 風の左サイドバー検索
- キーワード、カテゴリ、状態、サイズ、色、販売状況、発送日数、価格帯、タグ検索
- 検索条件保存と再利用
- 商品出品
- 商品編集
- 出品キャンセル
- 複数画像アップロード
- 画像削除
- 商品詳細画像カルーセル
- 商品購入フロー
- 残高チャージ
- 購入履歴
- 出品履歴
- 発送通知
- 受け取り評価
- 出品者評価
- 取引実績
- チェックリスト
- 公開コメント
- コメント返信スレッド
- 非公開DM
- 通知ページ
- 未読通知バッジ
- マイページ
- 発送元地域・お届け先住所登録
- ブロック機能
- 運営DM

---

## 3. AI / 発展機能

### Gemini / Vertex AI

- 出品画面で商品説明を生成
- 商品詳細画面で商品について質問
- 自然言語検索文を検索条件JSONに変換
- Vertex AI の429やクォータ不足時はローカル生成へ自動フォールバック

### 購入前AIチェック

商品詳細画面で以下を提示します。

- 商品説明から見える不安点
- 購入前に質問すべき内容
- 出品文・カテゴリ・状態の不整合
- 類似カテゴリ商品の価格感
- カテゴリ別に購入者が気にしやすい点

### 自然言語検索

商品一覧トップ右側の入力欄に、普段の言葉で条件を入力できます。

例:

```text
参考書 300円 ~ 1500円
```

この例では、ローカル規則またはGemini / Vertex AIにより、次のような検索条件に変換されます。

```json
{
  "q": "参考書",
  "category": "本・教材",
  "minPrice": "300",
  "maxPrice": "1500",
  "status": "available",
  "sort": "recommended"
}
```

### MerRec分析

`ml/` 配下では、Hugging Face の `mercari-us/merrec` を streaming で読み込み、TF-IDF + SVD + NearestNeighbors による関連商品推薦モデルを作成できます。

アプリ本体の商品一覧に出るおすすめ商品は、画面に必ず表示できるようにアプリDB内の商品だけを対象にしています。一方で、MerRec実データは、C2Cマーケットプレイスの行動傾向・カテゴリ傾向を分析するための独立したMLパイプラインとして保持しています。

---

## 4. 初期デモユーザー

| 表示名 | メールアドレス | パスワード |
|---|---|---|
| user1 | user1@example.com | user1111 |
| user2 | user2@example.com | user2222 |
| user3 | user3@example.com | user3333 |
| user4 | user4@example.com | user4444 |

各ユーザーは5商品ずつ、合計20商品を出品済みです。カテゴリが偏らないよう、本・教材、スマホ・PC周辺機器、日用品、音楽・楽器、食品、ファッション、ガジェット、ハンドメイドなどを分散させています。

---

## 5. Terminal 1: DB初期化

日本語文字化けを防ぐため、必ず `--default-character-set=utf8mb4` を付けて初期化します。

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent

docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d

docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

確認します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, title, ship_from_region, tags FROM items ORDER BY id LIMIT 5;"'
```

---

## 6. Terminal 2: バックエンド起動

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent/hackathon-backend

cp .env.example .env
```

`.env` はまず以下を推奨します。

```env
AI_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=実際のGCPプロジェクトID
VERTEX_LOCATION=global
GEMINI_MODEL=gemini-2.5-flash
```

Vertex AIを使う場合は認証とAPI有効化を行います。

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

疎通確認です。

```bash
curl http://localhost:8080/healthz
```

自然言語検索APIだけを確認する場合です。

```bash
curl -X POST http://localhost:8080/api/ai/parse-search \
  -H 'Content-Type: application/json' \
  -d '{"query":"参考書 300円 ~ 1500円"}'
```

---

## 7. Terminal 3: フロントエンド起動

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

確認ポイントです。

- 商品一覧に初期20商品が表示される
- 左サイドバー検索が上部から見やすく表示される
- おすすめ商品が最大8件表示される
- 自然言語検索に `参考書 300円 ~ 1500円` を入れると、本・教材かつ300〜1500円に絞られる
- 商品出品で複数画像を追加・削除できる
- 商品詳細で画像を巡回表示できる
- 購入、発送、受け取り評価、通知が一通り動く
- マイページの金額表記が `¥` で統一されている

---

## 8. Terminal 4: MerRec分析

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent

python3 -m venv .venv-ml
source .venv-ml/bin/activate

python -m pip install -U pip
python -m pip install -r ml/requirements.txt
python -m pip install dataset
```

まずサンプルで確認します。

```bash
python ml/merrec_recommender.py \
  --input ml/sample_merrec.csv \
  --out-json ml/sample_artifact.json \
  --out-pkl ml/sample_model.pkl \
  --limit 1000 \
  --topk 3
```

推論サーバーを起動します。

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
  -d '{"title":"calculus math book","category":"Books Education Math","price":13,"top_k":2}'
```

実MerRecを使う場合です。

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

## 9. Vertex AI 429 の扱い

`ResourceExhausted` が出る場合、設定ミスではなく共有リソースまたは利用枠に当たっていることがあります。このアプリでは、デモ中に止まらないようにローカル簡易生成へフォールバックします。

確認すべきもの:

```bash
gcloud config get-value project
gcloud auth list
gcloud auth application-default print-access-token
gcloud services list --enabled | grep aiplatform
```

Google Cloud Consoleでは、`IAM と管理 > 割り当てとシステム上限` で `Vertex AI API` を確認してください。

---

## 10. 評価項目との対応

- **必須機能**: 登録、出品、購入、DM、AI説明生成、デプロイ構成を実装。
- **UX**: サイドバー検索、画像カルーセル、通知バッジ、自然言語検索、おすすめ欄で操作性を高めた。
- **AI活用**: 説明生成、質問応答、購入前チェック、自然言語検索、MerRec分析を実装。
- **独創性**: C2C取引の不安点抽出、自然言語検索、フォールバック付きAI、MerRec分析を組み合わせた。
- **デモ完成度**: 初期ユーザー・初期商品・画像・通知フローを用意し、Demo Dayで一通り見せやすい構成にした。
