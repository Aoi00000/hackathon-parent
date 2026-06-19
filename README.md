# Regatear ~ AI Flea Market ~

Regatear ~ AI Flea Market ~ は、通常のフリマアプリに AI による購買支援、出品支援、価格交渉支援、生活相談、販売改善通知を組み込んだ「次世代フリマアプリ」です。登録、ログイン、出品、検索、商品詳細、コメント、非公開DM、チェックリスト、購入、発送、受け取り評価、通知、マイページ、支払い方法、残高チャージ、売上管理までを一連の流れとして動かせます。

Go バックエンド、React フロントエンド、MySQL、Gemini / Vertex AI、ローカルAIフォールバック、MerRec分析パイプラインを責務ごとに分けています。Demo Day では、初期ユーザー4名と初期商品20件を使って、出品から購入、発送、評価、売上反映までを短時間で再現できます。

「regatear」というのはスペイン語で「値切る・価格交渉をする」といった意味を持ちます。アイデアに詰まった時に相談に乗ってくれた友人がメキシコを訪れた際、日常的に行われている「regatear」を通した、出品者と購入希望者のやり取りの活発さに魅力を感じたと語ってくれました。本アプリでは、様々なユーザー支援機能により、出品者も購入希望者も快適に利用できるような開発を目指しています。特に、双方の直接的なやり取りのツールとも言える文章作成の様々な方法での支援は、交流のハードルを下げ、市場を活発にしてくれると期待しています。AI対話機能など、日常的なものからふと生まれる動機を市場に運んでくれるような工夫も凝らしてあります。友人が感じた魅力を、このアプリ上でも表現できたらいいなと思って開発に臨みました。

---

## 1. プロダクトの特徴

### フリマとしての完成度

- ユーザー登録、ログイン、ログアウト、JWT認証
- 商品一覧、商品詳細、出品、商品情報編集、出品キャンセル
- 複数画像・動画アップロード、削除、ドラッグ&ドロップ並び替え
- 画像・動画カルーセル表示
- キーワード、カテゴリ、状態、サイズ、色、価格帯、発送日数、タグによる検索
- 出品履歴、購入履歴、チェックリスト内検索
- 公開コメント、返信スレッド、出品者によるコメント削除
- 購入検討者と出品者だけが見られる非公開DM
- 購入、発送通知、受け取り評価、出品者評価、取引実績更新
- 購入時に購入者残高を減算し、受け取り評価完了時に出品者売上へ反映するエスクロー風フロー
- マイページでの残高、売上額、利用額、月別収支グラフ、住所、支払い方法管理
- 支払い方法未登録時のチャージ停止と登録欄への誘導
- 通知ページ、未読通知バッジ、既読化、関連商品への遷移
- ブロック、運営DM、保存した検索条件
- 端末によらず快適な レスポンシブデザイン

### AI による新しいUX

- 出品文生成: 商品名、カテゴリ、状態、タグから出品説明を生成
- 購入前AIチェック: 不安点、確認すべき質問、カテゴリ別注意点、価格感を整理
- 商品Q&A: 商品詳細上で商品文脈に沿った質問回答
- 自然言語検索: 「参考書 300円 ~ 1500円」のような普段の言葉を検索条件へ変換
- AI対話スレッド: 休日、模様替え、勉強、買い物などの相談を話題ごとに保存
- 価格交渉アシスタント: 希望金額、商品情報、公開コメント、ユーザーの立場を踏まえて丁寧な交渉文を生成
- 販売改善通知: 7日以上売れ残っている商品に対して、サイズ追記、キーワード、値下げ目安を出品者へ通知
- Gemini / Vertex AI が使えない場合も、ローカルフォールバックによりデモが止まらない

### 設計上の見せどころ

- フロントエンド、バックエンド、ML分析をディレクトリ単位で分離
- API呼び出しは `src/api/client.ts`、DB処理は `internal/repository/`、AI処理は `internal/ai/` に集約
- 購入、発送、受け取り評価、支払い方法変更など、複数テーブルを更新する処理はトランザクションで整合性を確保
- 画像・動画は旧 `image_url` 列との互換性を保ちながら、JSON配列として複数メディアを管理
- AI対話は `ai_chat_threads` と `ai_chat_messages` に保存し、ページを開き直しても履歴を確認可能
- MerRec 分析は `ml/` に分離し、本体デモの安定性と発展性を両立

---

## 2. ディレクトリ構成

```text
hackathon-parent/
├── .gitignore                         # 親リポジトリ全体の除外設定
├── docker-compose.local.yml           # ローカルMySQL起動用Compose
├── hackathon_ui_ux_design.drawio      # 画面遷移・ワイヤーフレーム設計
├── hackathon_db_api_design.xlsx       # DB/API/UI/タスク設計仕様書
├── README.md                          # 完成物の概要、機能一覧、実行手順
├── IMPLEMENTATION_NOTES.md            # 実装意図・保守メモ
├── DEPLOY_GCP.md                      # GCPデプロイ手順
├── docs/
│   ├── ARCHITECTURE.md                # アーキテクチャ整理
│   └── DEMO_SCRIPT.md                 # Demo Day 用の見せ方
├── hackathon-backend/
│   ├── cmd/server/main.go             # Go APIサーバー起動点、ルーティング、定期通知生成
│   ├── internal/ai/gemini.go          # Gemini / Vertex AI / ローカルフォールバック
│   ├── internal/auth/                 # JWT認証
│   ├── internal/config/               # 環境変数読み込み
│   ├── internal/db/                   # MySQL接続
│   ├── internal/handler/handler.go    # HTTPハンドラ、入力検証、JSONレスポンス
│   ├── internal/models/models.go      # API/DB共有モデル
│   ├── internal/repository/           # DBアクセス層
│   └── migrations/001_init.sql        # 初期DBスキーマとデモデータ
├── hackathon-frontend/
│   ├── src/App.tsx                    # 画面ルーティングとヘッダー
│   ├── src/api/client.ts              # APIクライアント
│   ├── src/components/                # 共通コンポーネント
│   ├── src/pages/                     # 各ページ
│   ├── src/styles.css                 # 全体スタイル
│   └── src/types.ts                   # TypeScript型
└── ml/
    ├── merrec_recommender.py          # MerRec学習/分析
    ├── recommender_service.py         # 軽量推薦API
    ├── sample_merrec.csv              # サンプルデータ
    └── README.md                      # ML側説明
```

---

## 3. 画面別の機能

### 商品一覧

商品カードを一覧表示し、キーワード、カテゴリ、状態、サイズ、色、価格帯、タグ、発送までの日数、販売状況などで絞り込めます。検索条件は保存でき、マイページから再利用・削除できます。自然言語検索では、普段の言葉をAIまたはローカル規則で検索条件JSONに変換して検索に利用します。MerRec分析に基づくおすすめ商品も表示されます。

### 商品詳細

画像・動画カルーセル、商品情報、チェックリスト追加(いいね機能と同等)数などを表示します。購入前AIチェック、商品Q&A、公開コメント、価格交渉アシスタント、非公開DMを同じ画面にまとめ、購入前の不安解消とコミュニケーションを支援します。チェックリストへの追加、購入手続きへの移行、出品者のブロックもできます。

価格交渉アシスタントでは、希望金額を入力すると、商品価格、商品説明、カテゴリ、状態、公開コメント、現在ユーザーが購入検討者か出品者かを踏まえ、角が立ちにくい交渉文を生成します。購入検討者には丁寧な値下げ依頼文、出品者には承諾・代替案・お断りのテンプレートを提示します。

### 出品する / 商品情報編集

商品名、カテゴリ、状態、価格、説明、受け渡し方法、発送までの日数、発送元地域、サイズ、色、タグを入力します。画像だけでなく動画も複数アップロードでき、削除とドラッグ&ドロップ並び替えに対応します。先頭メディアは一覧や詳細の代表表示として使われるため、出品者が見せ方を調整できます。

### 出品履歴

画面幅を広く使い、左側に `Available` の商品を更新時刻が古い順で表示し、右側に `SOLD` の商品を更新時刻が新しい順で表示します。検索対象は左右両方の全商品で、商品概要をクリックすると商品情報詳細ページへ遷移します。販売中の商品は編集・キャンセルでき、購入済みの商品では発送通知を送れます。

### 購入履歴

左側に受け取り評価前の未完了取引を更新時刻が古い順で表示し、右側に取引完了済みの商品を新しい順で表示します。どちらの列も検索対象で、商品概要から商品情報詳細ページへ遷移できます。発送済みの商品には評価入力欄が表示され、評価完了をもって取引が完了し、出品者の売上が確定します。

### チェックリスト

左側に `Available` の商品、右側に `SOLD` の商品を分けて表示します。検索後も状態別に整理され、商品概要クリックで詳細へ移動できます。気になる商品が売り切れたかどうかを一目で確認できます。チェックリスト内の商品情報に値下げなどの変更があった場合に通知が届くようになっています。

### AI対話

画面幅を広く使い、左上から話題リストを縦に表示し、中央から右側を選択中の話題の会話領域として使います。話題ごとの履歴をDBに保存します。回答末尾には、フリマで探しやすいおすすめグッズを一般名で提示することで、日常のふとしたきっかけから、意外な商品に対しても購買意欲を掻き立てます。

### マイページ

残高、今月の売上額、今月の利用額、累計売上額、累計利用額、出品者評価、取引実績などを表示します。月別の売上額と利用額を1つの棒グラフ内で比較できるため、お金の出入りを把握しやすくなっています。他にも、残高チャージ、支払い方法の登録、ブロックリストの確認、保存した検索条件の確認、運営に対するDMなどの機能も備えています。支払い方法は複数登録でき、既定支払い方法を選びます。登録、既定変更、削除、チャージ、住所保存、運営へのDM送信などの重要操作は通知されます。

### 通知

購入、購入完了、発送、受け取り評価、チェックリスト内の商品情報更新、出品キャンセル、コメント、DM、支払い方法登録、住所登録、残高チャージ、販売改善提案などに関する通知を一覧表示します。未読通知はヘッダーにバッジ表示され、確認後は既読化できます。ボタンにより通知内容に該当するページに直接遷移することができます。

---

## 4. DB/API の主要仕様

### 主なDBテーブル

- `users`: 残高、売上、住所、評価、取引実績を管理
- `items`: 商品情報、販売状態、複数画像・動画JSON文字列、検索用属性を管理
- `purchases`: 購入、発送、受け取り評価、取引完了を管理
- `messages`: 公開コメントと返信を管理
- `private_messages`: 非公開DMと返信を管理
- `notifications`: 関連商品付き通知、未読状態を管理
- `payment_methods`: 支払い方法の表示用情報と既定フラグを管理
- `ai_chat_threads`: AI対話の話題スレッドを管理
- `ai_chat_messages`: AI対話のユーザー発言とAI回答を保存
- `saved_searches`: 保存した検索条件を管理
- `user_blocks`: ブロック関係を管理

### 代表的なAPI

```text
GET    /healthz
POST   /api/auth/register
POST   /api/auth/login
GET    /api/me
PUT    /api/me
POST   /api/me/charge
GET    /api/me/payment-methods
POST   /api/me/payment-methods
POST   /api/me/payment-methods/{id}/default
DELETE /api/me/payment-methods/{id}
GET    /api/items
GET    /api/items/{id}
POST   /api/items
PUT    /api/items/{id}
POST   /api/items/{id}/purchase
POST   /api/items/{id}/ship
POST   /api/items/{id}/complete
GET    /api/me/items
GET    /api/me/purchases
GET    /api/me/checklist
GET    /api/me/notifications
POST   /api/items/{id}/messages
DELETE /api/items/{id}/messages/{messageId}
GET    /api/items/{id}/private-messages
POST   /api/items/{id}/private-messages
POST   /api/ai/generate-description
POST   /api/items/{id}/ask
POST   /api/items/{id}/negotiation-assist
POST   /api/ai/parse-search
GET    /api/me/ai-chat-threads
POST   /api/me/ai-chat-threads
GET    /api/me/ai-chat-threads/{id}/messages
POST   /api/me/ai-chat-threads/{id}/messages
DELETE /api/me/ai-chat-threads/{id}
```

---

## 5. 初期デモユーザー

| 表示名 | メールアドレス | パスワード |
|---|---|---|
| user1 | user1@example.com | user1111 |
| user2 | user2@example.com | user2222 |
| user3 | user3@example.com | user3333 |
| user4 | user4@example.com | user4444 |

各ユーザーは5商品ずつ、合計20商品を出品済みです。カテゴリは、本・教材、スマホ・PC周辺機器、日用品、音楽・楽器、食品、ファッション、ガジェット、ハンドメイド、美容、家具、チケットなどに分散しています。

---

## 6. ローカル実行手順

以下では、ターミナルを3つに分けます。

### Terminal 1: DB起動と初期化

親ディレクトリで実行します。

```bash
cd hackathon-parent
```

MySQLコンテナを作り直して起動します。

```bash
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d
```

日本語文字化けを防ぐため、必ず `--default-character-set=utf8mb4` を付けて初期化します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

初期データを確認します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, title, status, price_yen, updated_at FROM items ORDER BY id LIMIT 8;"'
```

AI対話、支払い方法、通知テーブルを確認します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SHOW TABLES LIKE '\''ai_chat%'\''; SHOW TABLES LIKE '\''payment_methods'\''; SHOW TABLES LIKE '\''notifications'\'';"'
```

### Terminal 2: バックエンド起動

バックエンドディレクトリで実行します。

```bash
cd hackathon-parent/hackathon-backend
```

`.env` の例です。外部AIなしでデモしたい場合も、フォールバックにより主要AI機能の画面確認は可能です。

```env
PORT=8080
FRONTEND_ORIGIN=http://localhost:5173
JWT_SECRET=local-dev-secret
DB_USER=hackathon_user
DB_PASSWORD=hackathon_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=hackathon
AI_PROVIDER=vertex
GOOGLE_CLOUD_PROJECT=実際のGCPプロジェクトID
VERTEX_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

Vertex AIを使う場合は認証とAPI有効化を行います。

```bash
gcloud config set project 実際のGCPプロジェクトID
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

依存関係を取得し、テストします。

```bash
go mod tidy
go test ./...
```

バックエンドを起動します。

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

バックエンド起動時と24時間ごとに、7日以上売れ残っている商品へのAI販売改善通知が作成されます。デモデータでは確認しやすいよう、一部の販売中商品の更新日時を古くしています。

### Terminal 3: フロントエンド起動

フロントエンドディレクトリで実行します。

```bash
cd hackathon-parent/hackathon-frontend
```

初回は依存関係を入れ直します。

```bash
npm config set registry https://registry.npmjs.org/
npm config delete proxy
npm config delete https-proxy

rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/
```

型チェックとビルドを確認します。

```bash
npm run build
```

開発サーバーを起動します。

```bash
npm run dev
```

ブラウザで開きます。

```text
http://localhost:5173
```

---

### Terminal 4: MerRec分析

別ターミナルで実行します。

```bash
cd hackathon-parent

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

サーバーは以下のとおりです。

```bash
python ml/recommender_service.py \
  --model ml/merrec_model.pkl \
  --port 8090
```


---


## 7. 完成品の確認手順

### 7.1 基本ログインと商品一覧

1. `user1@example.com / user1111` でログインします。
2. 商品一覧で初期商品が表示されることを確認します。
3. サイドバーでカテゴリ、価格、状態などを検索します。
4. 自然言語検索に `参考書 300円 ~ 1500円` と入力し、検索条件へ変換されることを確認します。

### 7.2 商品詳細、AI購入支援、価格交渉

1. 任意の商品詳細を開きます。
2. 画像・動画カルーセル、商品説明、出品者評価を確認します。
3. 購入前AIチェックを実行します。
4. 商品Q&Aに `初心者にも使いやすいですか？` などを入力します。
5. 価格交渉アシスタントに希望金額を入力し、購入検討者向け文面が生成されることを確認します。
6. 出品者本人で同じ商品を開くと、出品者向けの承諾・代替案・お断り文面が生成されることを確認します。

### 7.3 出品とメディア並び替え

1. 出品画面を開きます。
2. 画像または短い動画を複数アップロードします。
3. ドラッグ&ドロップで順番を入れ替えます。
4. AI商品説明生成を実行します。
5. 出品後、商品詳細で先頭メディアが代表表示されることを確認します。
6. 出品履歴の編集画面でも、画像・動画の削除、追加、並び替えができることを確認します。

### 7.4 出品履歴・購入履歴・チェックリスト

1. 出品履歴を開き、画面左に `Available`、右に `SOLD` が分かれて表示されることを確認します。
2. 左列は更新時刻が古い順、右列は新しい順であることを確認します。
3. 商品概要をクリックして商品詳細へ遷移します。
4. 購入履歴では、左に未完了取引、右に取引完了済みが分かれて表示されることを確認します。
5. チェックリストでも、販売中と売り切れが左右に分かれることを確認します。

### 7.5 AI対話スレッド

1. ヘッダーの「AI対話」を開きます。
2. 「新しい話題」を押します。
3. `休日の遊びのおすすめない？` と入力して送信します。
4. 回答の最後におすすめグッズが表示されることを確認します。
5. 別の話題を作り、`家の模様替えをしてみたいんだけどいい案ない？` と送信します。
6. 左側の話題リストで履歴が分かれることを確認します。
7. ページを移動して戻り、履歴が残っていることを確認します。

DBでも確認できます。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, user_id, title, updated_at FROM ai_chat_threads ORDER BY updated_at DESC; SELECT thread_id, role, LEFT(body, 60) AS body FROM ai_chat_messages ORDER BY id;"'
```

### 7.6 支払い方法、チャージ、通知

1. マイページを開きます。
2. 支払い方法未登録の状態でチャージしようとすると、登録が必要であることが表示されます。
3. 支払い方法登録欄で、登録名、カード番号、名義、有効期限、セキュリティコードを入力します。
4. 登録後、通知ページに支払い方法登録通知が届くことを確認します。
5. 既定支払い方法変更、支払い方法削除、チャージでも通知が届くことを確認します。

### 7.7 購入、発送、評価、売上反映

1. `user1` で商品を出品します。
2. `user2` でログインし、その商品を購入します。
3. `user2` の残高が購入時点で減ることを確認します。
4. `user1` の残高と売上額は、この時点ではまだ増えないことを確認します。
5. `user1` で発送通知を送ります。
6. `user2` で受け取り評価を行います。
7. `user1` の残高と売上額が、受け取り評価後に増えることを確認します。

SQLでも確認できます。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, name, balance_coins, sales_coins FROM users ORDER BY id; SELECT id, item_id, buyer_id, seller_id, price_yen, status, created_at, shipped_at, completed_at FROM purchases ORDER BY id DESC LIMIT 5;"'
```

### 7.8 販売改善通知

1. バックエンドを起動します。
2. 通知ページを開きます。
3. 7日以上更新されていない販売中商品がある出品者に、`AI販売改善提案` が届くことを確認します。
4. 通知本文に、サイズ追記、キーワード改善、価格調整案が含まれることを確認します。

DBで確認する場合です。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT user_id, item_id, title, body, created_at FROM notifications WHERE title = '\''AI販売改善提案'\'' ORDER BY created_at DESC LIMIT 5;"'
```

---

## 8. 本番環境テストの概要

詳細は `DEPLOY_GCP.md` も確認してください。

### Cloud SQL 初期化

Cloud Shellでプロジェクトを確認します。

```bash
gcloud config get-value project
```

違う場合は設定します。

```bash
gcloud config set project term-000000
```

rootでCloud SQLへ接続します。

```bash
gcloud sql connect hackathon-mysql --user=root
```

MySQLプロンプトでDBを初期化します。

```SQL
DROP DATABASE IF EXISTS hackathon;

CREATE DATABASE hackathon
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

GRANT ALL PRIVILEGES ON hackathon.* TO 'hackathon_user'@'%';

FLUSH PRIVILEGES;

USE hackathon;
SET NAMES utf8mb4;
SOURCE 001_init.sql;

SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS item_count FROM items;
SHOW TABLES LIKE 'ai_chat%';
SHOW TABLES LIKE 'payment_methods';
```

### ブラウザ側リセット

DBを初期化しても、ブラウザ側には古いログイン情報や画面状態が残る場合があります。最も簡単なのは、シークレットウィンドウでVercel URLを開くことです。

```text
https://your-vercel-url
```

これにより、古いログイントークンや画面状態が消え、初期DBに対してきれいにログインできます。

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

## 10. 開発時の基本コマンド

### 最新化

```bash
cd hackathon-parent

git status
git pull origin main
git submodule update --init --recursive
```

### バックエンド確認

```bash
cd hackathon-parent/hackathon-backend

go mod tidy
go test ./...
go run ./cmd/server
```

### フロントエンド確認

```bash
cd hackathon-parent/hackathon-frontend

rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/
npm run build
npm run dev
```

### DB再初期化

```bash
cd hackathon-parent

docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d

docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

---

## 11. 今後の変更方針

### 11.1. 全体方針

現在の構成は以下のとおりです。

```
hackathon-parent/
├── hackathon-backend/   ← Cloud Runにデプロイされる本体
├── hackathon-frontend/  ← Vercelにデプロイされる本体
├── ml/                  ← MerRec分析・発展機能。通常は本番Webには直接反映されない
├── docker-compose.local.yml
├── README.md
├── IMPLEMENTATION_NOTES.md
└── .gitignore
```

運用上の対応関係は次です。

```
backendを修正
→ hackathon-backend にcommit/push
→ Cloud Runが自動デプロイ

frontendを修正
→ hackathon-frontend にcommit/push
→ Vercelが自動デプロイ

ml, README, docker-compose.local.yml などを修正
→ hackathon-parent にcommit/push
→ Cloud Run/Vercelには直接反映されない

submoduleの中身を更新した
→ 最後にhackathon-parent側でsubmoduleポインタもcommit/push
```

---

### 11.2. 修正基本手順

現在の構成は以下のとおりです。

```
1. ローカルでpullして最新化
2. VSCodeで修正
3. ローカルで動作確認
4. 対象submodule側でcommit/push
5. Cloud RunまたはVercelのデプロイ完了を確認
6. 本番URLで動作確認
7. 親リポジトリのsubmoduleポインタをcommit/push
```

---

### 11.3. 作業開始時に必ず行うコマンド

最初は親リポジトリで最新化します。

```bash
cd hackathon-parent

git status
git pull origin main

git submodule update --init --recursive
```

submodule側も最新の main に合わせます。

```bash
cd hackathon-backend
git checkout main
git pull origin main

cd ../hackathon-frontend
git checkout main
git pull origin main

cd ..
git status
```

---

### 11.4. backend を修正する場合

backend修正は、例えば次のような場合です。

```
APIの追加・修正
DBアクセス処理の修正
AI生成処理の修正
Cloud SQL接続関連の修正
通知・購入・出品ロジックの修正
Goのモデルやリポジトリ層の修正
```

---

#### 11.4.1 VSCodeで開く

```bash
cd hackathon-parent
```

---

#### 11.4.2 ローカルDBを起動

Terminal 1 :

```bash
cd hackathon-parent

docker compose -f docker-compose.local.yml up -d
```

DBを初期化し直す場合だけ、次を使います。

```bash
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d

docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

---

#### 11.4.3 backend をローカル起動

Terminal 2 :

```bash
cd hackathon-backend
```

起動します。

```bash
go mod tidy
go test ./...

set -a
source .env
set +a

go run ./cmd/server
```

---

#### 11.4.4 backend を push して Cloud Run へ反映

修正が終わったら、backend submodule内でcommit/pushします。

```bash
cd hackathon-backend

git status
git add .
git commit -m "Fix backend behavior"
git push origin main
```

Cloud Runは `hackathon-backend/main` を監視しているため、push後に自動デプロイが走ります。Cloud RunはGitHubリポジトリからCloud Build経由で継続デプロイできます。

---

#### 11.4.5 Cloud Run のデプロイ確認

Cloud Shellまたはローカルで確認します。

```bash
gcloud builds list --limit=5
```

Cloud Runログです。

```bash
gcloud run services logs read hackathon-backend \
  --region us-central1 \
  --limit 100
```

Cloud Run URLを取得します。

```bash
BACKEND_URL=$(gcloud run services describe hackathon-backend \
  --region us-central1 \
  --format="value(status.url)")

echo "$BACKEND_URL"
```

API確認です。

```bash
curl "$BACKEND_URL/api/items"

curl -X POST "$BACKEND_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"user1@example.com","password":"user1111"}'
```

Cloud Runではコンテナが PORT 環境変数で指定されたポートをlistenする必要があります。今後もし「PORT=8080でlistenしなかった」というエラーが出た場合でも、多くの場合はDB接続失敗などでサーバー起動前に落ちているので、Cloud Runログを見るのが第一です。

---

#### 11.4.6 親リポジトリの submodule ポインタ更新

backendのpush後、親リポジトリに戻ります。

```bash
cd hackathon-parent

git status
git add hackathon-backend
git commit -m "Update backend submodule pointer"
git push origin main
```

---

### 11.5. frontend を修正する場合

frontend修正は、例えば次のような場合です。

```
UI/UXの修正
商品一覧・検索欄・おすすめ欄の修正
マイページ表示の修正
API呼び出し処理の修正
CSSや文言の修正
```

---

#### 11.5.1 frontend をローカル起動

Terminal 3 :

```bash
cd hackathon-frontend
```

依存関係を整理します。

```bash
npm config set registry https://registry.npmjs.org/
npm config delete proxy
npm config delete https-proxy

rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/
```

起動します。

```bash
npm run build
npm run dev
```

ブラウザで開きます。

```
http://localhost:5173
```

---

#### 11.5.2 frontend を push して Vercel へ反映

修正が終わったら、frontend submodule内でcommit/pushします。

```bash
cd hackathon-frontend

git status
git add .
git commit -m "Fix frontend UI"
git push origin main
```

Vercelは `hackathon-frontend/main` を監視しているため、自動デプロイされます。

---

#### 11.5.3 Vercel側の確認

Vercelダッシュボードで確認します。

```
Project
→ Deployments
→ 最新Deployment
→ StatusがReadyか確認
```

本番URLを開き、動作確認します。

---

#### 11.5.4 親リポジトリの submodule ポインタ更新

frontendのpush後、親リポジトリに戻ります。

```bash
cd hackathon-parent

git status
git add hackathon-frontend
git commit -m "Update frontend submodule pointer"
git push origin main
```

---

### 11.6. backend と frontend を両方修正する場合

API仕様を変える場合などは、backendとfrontendの両方を修正することになります。

```
backendで新しいAPIを追加
frontendでそのAPIを呼ぶUIを追加
```

この場合の順番は次がおすすめです。

```
1. backendを修正
2. frontendを修正
3. ローカルでbackend + frontendを同時に起動
4. APIと画面の接続を確認
5. backendをpush
6. Cloud Runの反映を確認
7. frontendをpush
8. Vercelの反映を確認
9. 親リポジトリで両方のsubmoduleポインタを更新
```

コマンド例です。

```bash
# backend
cd hackathon-backend
git add .
git commit -m "Add backend API"
git push origin main

# frontend
cd ../hackathon-frontend
git add .
git commit -m "Use new backend API"
git push origin main

# parent
cd ..
git add hackathon-backend hackathon-frontend
git commit -m "Update app submodules"
git push origin main
```

---

### 11.7. Cloud Shell の今後の扱い

Cloud Shellは、GCP上の状態確認・Cloud SQL操作・Cloud Run設定変更に使うのがよいです。主な用途は次です。

```
Cloud SQLに接続してDBを見る
Cloud Runのログを見る
Cloud Run環境変数を確認・更新する
Cloud Run URLを取得する
GCP権限やAPI有効化を確認する
```

---

### 11.8. Cloud Run の今後の扱い

Cloud Runは、基本的に backendの本番実行環境です。

今後触る場所は主に3つです。

```
1. Deployments / Revisions
2. Logs
3. Environment variables / Cloud SQL connection
```

よく見るポイント

```
最新リビジョンがReadyか
トラフィックが最新リビジョンに100%向いているか
Cloud SQL接続が付いているか
FRONTEND_ORIGINがVercel本番URLになっているか
```

Cloud RunからCloud SQLへ接続するには、Cloud RunサービスにCloud SQL接続を追加して /cloudsql/INSTANCE_CONNECTION_NAME を使う構成にします。

---

### 11.9. Vercel の今後の扱い

Vercelは、frontendの本番実行環境です。

見る場所は主に次です。

```
Deployments
Build Logs
Settings → Environment Variables
Domains
```

重要な環境変数はこれです。
```env
VITE_API_BASE_URL=https://hackathon-backend-xxxxx-uc.a.run.app
```

Vercelの環境変数は、設定後に再デプロイしないとビルド済みフロントエンドに反映されません。Vercelでは環境変数をプロジェクト設定から管理できます。

VercelでAPI URLを変えた場合

```
Vercel
→ Project
→ Settings
→ Environment Variables
→ VITE_API_BASE_URL を修正
→ Deployments
→ Redeploy
```

その後、ブラウザで動作確認します。

---

### 11.10. 承認済みネットワークについて

自宅でCloud SQLにMacから直接SSL接続するために、自宅のグローバルIPをCloud SQLの「承認済みネットワーク」に登録していました。

他の場所ではグローバルIPが変わるため、Macから直接Cloud SQLへ接続する場合は、その場所のの現在のIPを追加する必要があります。

```bash
curl ifconfig.me
```

出たIPをCloud SQLに追加します。

```
Cloud SQL
→ hackathon-mysql
→ 接続
→ ネットワーキング
→ 承認済みネットワーク
→ 大学のIP/32 を追加
```

VercelからCloud Runへアクセスする構成、Cloud RunからCloud SQLへ接続する構成は、あなたの現在地のIPには依存しません。

つまり、別の場所に移動しても以下は基本的に変えなくてよいです。

```
VercelのVITE_API_BASE_URL
Cloud RunのMYSQL_HOST
Cloud RunのCloud SQL接続
Cloud RunのFRONTEND_ORIGIN
```

変える必要があるのは、自分のMacからCloud SQLへ直接接続したい場合の承認済みネットワークだけです。

---

## 12. Demo Dayで強調すること

1. フリマとしての基本機能が一通り動く。
2. 画像だけでなく動画も扱えるため、商品の状態や雰囲気を伝えやすい。
3. AIは説明生成だけでなく、検索、購入前チェック、商品Q&A、価格交渉、生活相談、販売改善通知に広がっている。
4. 購入時に出品者へ即時入金しないため、実際のフリマサービスに近い安心感がある。
5. AI対話や価格交渉など、既存フリマアプリでは弱い「相談」と「摩擦低減」を体験として組み込んでいる。
6. 外部AIが不安定でもフォールバックでデモが止まらない。
