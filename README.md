# AI Flea Market

AI Flea Market は、Web 研修ハッカソン向けに作成した、AI 活用型の次世代フリマアプリです。
通常のフリマアプリに必要な「登録・出品・購入・DM・通知」などに加え、Gemini / Vertex AI、ローカルAIフォールバック、MerRecデータセット分析、自然言語検索、購入前AIチェックなどを組み込んでいます。

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
- 左サイドバー検索
- キーワード、カテゴリ、状態、サイズ、色、販売状況、発送日数、価格帯、タグ、販売状況検索
- 漢字・カタカナ・ひらがな互換対応、あいまい検索
- 検索条件保存と再利用
- 商品出品
- 出品時入力必須項目チェック
- 複数画像アップロード
- 画像削除
- 商品詳細画像カルーセル
- 商品情報再編集可能
- 出品キャンセル
- 商品購入フロー
- 内部通貨を用いたお金のやり取り表現
- 残高チャージ
- 購入履歴、履歴内検索
- 出品履歴、履歴内検索
- チェックリスト、リスト内検索
- 商品のチェックリスト追加(いいね機能)、追加数表示
- 発送通知
- 受け取り評価
- 出品者評価
- 取引実績表示
- 公開コメント
- コメント返信スレッド
- 非公開DM
- 通知ページ(出品、購入、コメント、DM、残高チャージ、マイページ設定、商品情報変更など)
- 未読通知バッジ(件数表示)
- 通知内容該当部への直接遷移
- マイページ
- 残高、売上額、利用額表示
- 発送元地域・お届け先住所登録、出品・購入時自動反映
- ブロック機能
- 対運営DM
- レスポンシブデザイン

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

## 5. 確認ポイント

### user0で新規登録
- 新規登録ができる
- 商品一覧に初期20商品が正しく表示される
- 左サイドバー検索が正しく表示される
- おすすめ商品が最大8件表示される
- 自然言語検索に `参考書 300円 ~ 1500円` などを入力して検索すると、キーワード「参考書」、カテゴリ「本・教材」価格「300〜1500円」という条件に絞られる
- 検索条件を保存、適用できる
- マイページに残高、今月の売上額、今月の利用額、累計売上額、累計利用額、出品者評価が表示される
- マイページで 残高のチャージができる、残高に反映される
- 住所を登録できる
- 保存した検索条件を削除できる
- 運営にテストDMを送ることができる
- マイページでの情報登録などによる通知を確認できる、新着通知数が表示される
- 通知から該当部分に直接遷移できる

### user1の出品商品の商品情報詳細を見る
- 商品詳細で画像を巡回表示できる、商品情報が正しく表示される
- 購入前AIチェックが表示される
- チェックリストに商品を追加できる
- いいね数(ハートマークの隣に表示される数)が増える
- チェックリストから商品詳細に直接遷移できる
- チェックリストの追加、削除はトグルボタンで変更できる
- AIに商品情報についての質問ができる、適切な回答が得られる
- 商品に対して公開コメントができる
- 出品者と購入検討者で非公開DMができる
- コメント、DMは更新時刻で並び替えられる
- 出品者のブロックができる
- ブロックした出品者の商品は商品一覧で表示されなくなり、自分の出品商品も相手に表示されなくなる
- ブロック状態は商品詳細情報ページのトグルボタンで変更できる
- ブロック状態はマイページからも確認、解除できる
- ブロックしている出品者の商品であっても、購入履歴、チェックリストからは辿ることができる

### user0で出品
- 商品出品でプルダウンが正しく動作する
- 出品用の複数画像を追加・削除できる
- マイページにて住所登録済みの場合、出品画面の地域欄に反映されている
- AIによる商品説明が正しく生成される
- 未入力の必須項目がある場合は警告が出て出品できない
- 出品完了通知が届く、通知から出品履歴に直接遷移できる
- 商品一覧に商品が反映されている
- ログアウトができる

### user1でログイン、コメント、DM確認、商品情報編集
- ログインができる
- 出品商品に対するコメント、DMについての通知が届いている
- 通知から対象商品の詳細情報ページに直接遷移できる`
- コメント、DMに返信ができる
- 返信が加わるとスレッド状の構造になる
- 出品者のコメントは強調される
- スレッドが複数存在する場合は、更新順に並び替えられる
- 商品詳細情報ページ、または出品履歴ページから商品情報を編集できる
- 出品履歴では履歴内検索により出品数が多くても出品した商品を探すことができる
- 出品キャンセルができる
- 出品キャンセルしたことを示す通知が届く

### user0で再ログイン、商品購入
- チェックリスト内の商品情報変更、出品キャンセルなどに対する通知が届く
- 商品購入手続きに進む
- 残高が不足している場合はその場でチャージすることもできる
- マイページで住所を登録している場合、お届け先住所に自動的に反映されている
- 購入すると購入完了通知が届く
- 購入履歴に購入した商品が表示される、表示は「available」から「sold」に変化している
- 「購入フローのどの段階にいるか (例：購入手続き完了)」と「次の段階 (例：発送待ち)」が表示される
- 発送がいつまでに行われるかが商品情報詳細に反映され表示される
- 購入履歴では履歴内検索により購入数が多くても購入した商品を探すことができる
- マイページの残高が減り、利用額が増えている

### user1で再ログイン、商品発送
- 出品した商品が購入されたことを示す通知が届く
- 通知から直接遷移して詳細を確認し、発送通知を送る
- 購入フロー表示が「発送通知送信済み」、「受け取り評価待ち」に変更される
- 発送したことを示す通知が届く

### user0で再ログイン、商品受け取り評価
- 購入した商品が発送されたことを示す通知が届く
- 通知から直接遷移して詳細を確認し、受け取り評価をする
- 購入フロー表示が「取引完了」になり、通知が届く

### user1で再ログイン、取引完了確認
- 受け取り評価、取引完了通知が届く
- 通知から直接遷移して詳細を確認し、取引完了を確認する
- マイページの残高と売上額が増えていることを確認する

### user2でログイン、公開コメントと非公開DMの表示確認
- user0が購入したuser1の商品を確認する
- 公開コメントは確認できるが非公開DMは表示されていないことを確認する

---


## 6. ローカルテスト 

### Terminal 1: DB初期化

日本語文字化けを防ぐため、必ず `--default-character-set=utf8mb4` を付けて初期化します。

```bash
cd hackathon-parent

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

### Terminal 2: バックエンド起動

```bash
cd hackathon-backend
```

`.env` については以下のとおりです。

```env
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

### Terminal 3: フロントエンド起動

```bash
cd hackathon-frontend

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

### Terminal 4: MerRec分析

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

## 7. 本番環境テスト 

### 1: Cloud Shellを開く

まずプロジェクトを確認します

```bash
gcloud config get-value project
```

`term-000000`など、自分のGCPプロジェクトIDが出ればOKです。違う場合は設定します。

```bash
gcloud config set project term-000000
```

確認します。

```bash
docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql --default-character-set=utf8mb4 -uhackathon_user hackathon -e "SELECT id, title, ship_from_region, tags FROM items ORDER BY id LIMIT 5;"'
```

---

### 2: root で Cloud SQL に接続する

データベースを削除・再作成するので、hackathon_user ではなく root で入るのが確実です。

```bash
gcloud sql connect hackathon-mysql --user=root
```

---

### 3: MySQL 内で DB を初期化、確認する

MySQLプロンプトで以下を実行します。

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
SELECT id, title, category FROM items ORDER BY id LIMIT 5;
```

`001_init.sql`のパスにはよく注意してください。

---

### 4: ブラウザ側もリセットする

DBを初期化しても、ブラウザ側にはログイン情報や古い状態が localStorage に残っている場合があります。

一番簡単なのは、シークレットウィンドウでVercel URLを開くことです。

`https://your-Vercel URL`

これにより、古いログイントークンや画面状態が消え、初期DBに対してきれいにログインできます。

---

## 8. Vertex AI 429 の扱い

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


## 9. 今後の変更方針

### 1. 全体方針

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

### 2. 修正基本手順

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

### 3. 作業開始時に必ず行うコマンド

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

### 4. backend を修正する場合

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

#### 4.1 VSCodeで開く

```bash
cd hackathon-parent
```

---

#### 4.2 ローカルDBを起動

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

#### 4.3 backend をローカル起動

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

#### 4.4 backend を push して Cloud Run へ反映

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

#### 4.5 Cloud Run のデプロイ確認

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

#### 4.6 親リポジトリの submodule ポインタ更新

backendのpush後、親リポジトリに戻ります。

```bash
cd hackathon-parent

git status
git add hackathon-backend
git commit -m "Update backend submodule pointer"
git push origin main
```

---

### 5. frontend を修正する場合

frontend修正は、例えば次のような場合です。

```
UI/UXの修正
商品一覧・検索欄・おすすめ欄の修正
マイページ表示の修正
API呼び出し処理の修正
CSSや文言の修正
```

---

#### 5.1 frontend をローカル起動

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

#### 5.2 frontend を push して Vercel へ反映

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

#### 5.3 Vercel側の確認

Vercelダッシュボードで確認します。

```
Project
→ Deployments
→ 最新Deployment
→ StatusがReadyか確認
```

本番URLを開き、動作確認します。

---

#### 5.4 親リポジトリの submodule ポインタ更新

frontendのpush後、親リポジトリに戻ります。

```bash
cd hackathon-parent

git status
git add hackathon-frontend
git commit -m "Update frontend submodule pointer"
git push origin main
```

---

### 6. backend と frontend を両方修正する場合

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

### 7. Cloud Shell の今後の扱い

Cloud Shellは、GCP上の状態確認・Cloud SQL操作・Cloud Run設定変更に使うのがよいです。主な用途は次です。

```
Cloud SQLに接続してDBを見る
Cloud Runのログを見る
Cloud Run環境変数を確認・更新する
Cloud Run URLを取得する
GCP権限やAPI有効化を確認する
```

---

### 8. Cloud Run の今後の扱い

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

### 9. Vercel の今後の扱い

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

### 10. 承認済みネットワークについて

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

