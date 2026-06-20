# Regatear ~ AI Flea Market ~

Regatear ~ AI Flea Market ~ は、通常のフリマアプリに AI による購買支援、出品支援、価格交渉支援、生活相談、販売改善通知などを組み込んだ「次世代フリマアプリ」です。登録、ログイン、出品、検索、商品詳細、コメント、非公開DM、チェックリスト、購入、発送、受け取り評価、通知、マイページ、支払い方法、残高チャージ、売上管理までを一連の流れとして動かせます。

Go バックエンド、React フロントエンド、MySQL、Gemini / Vertex AI、ローカルAIフォールバック、MerRec分析パイプラインを責務ごとに分けています。Demo Day では、初期ユーザー4名と初期商品20件を使って、出品から購入、発送、評価、売上反映までを短時間で再現できます。

「regatear」というのはスペイン語で「値切る・価格交渉をする」といった意味を持ちます。アイデアに詰まった時に相談に乗ってくれた友人がメキシコを訪れた際、日常的に行われている「regatear」を通した、出品者と購入希望者のやり取りの活発さに魅力を感じたと語ってくれました。本アプリでは、様々なユーザー支援機能により、出品者も購入希望者も快適に利用できるような開発を目指しています。特に、双方の直接的なやり取りのツールとも言える文章作成の様々な方法での支援は、交流のハードルを下げ、市場を活発にしてくれると期待しています。AI対話機能など、日常的なものからふと生まれる動機を市場に運んでくれるような工夫も凝らしてあります。友人が感じた魅力を、このアプリ上でも表現できたらいいなと思って開発に臨みました。

---

## 1. プロダクトの特徴

### フリマとしての完成度

- ユーザー登録、ログイン、ログアウト、JWT認証
- 商品一覧、商品詳細、出品、商品情報編集、出品キャンセル
- 複数画像・動画アップロード、削除、ドラッグ&ドロップ並び替え
- 画像・動画カルーセル表示、カルーセルの循環(ループ)
- キーワード、カテゴリ、状態、サイズ、色、価格帯、発送日数、タグ、販売状況などによる検索
- プルダウン選択
- 商品一覧の並べ替え
- 出品履歴、購入履歴、チェックリスト(いいね機能)
- 出品履歴とチェックリストでは Available と Sold を分けて二列表示
- 購入履歴では取引中のものと取引完了したものを分けて二列表示
- それぞれの履歴、リスト内での検索機能、並べ替えも実装
- 公開コメント、返信スレッド、出品者によるコメント削除
- 購入検討者と出品者だけが見られる非公開DM
- 購入手続き、発送、受け取り評価、出品者評価と取引実績更新の購入フロー
- 購入時に購入者残高を減算し、受け取り評価完了時に出品者売上へ反映するエスクロー風フロー
- マイページでの残高、売上額、利用額、月別収支グラフ、住所、支払い方法管理
- 支払い方法未登録時のチャージ停止と登録欄への誘導
- 通知ページ、未読通知バッジ、既読化、ボタンによる関連商品への直接遷移
- ブロック、運営へのDM、検索条件の保存
- 端末によらず快適な レスポンシブデザイン

### AI による新しいUX

- 出品文生成: 商品名、カテゴリ、状態、タグ、追加情報などから出品説明を生成
- 購入前AIチェック: 不安点、確認すべき質問、カテゴリ別注意点、価格感などを整理
- 商品Q&A: 商品詳細上で商品文脈に沿った質問回答
- 自然言語検索: 「参考書 300円 ~ 1500円」のような普段の言葉を検索条件へ変換
- おすすめ表示: MerRecデータセットの分析に基づき、おすすめ商品を提示
- AI対話スレッド: 日常レベルでの相談に対して回答、関連するおすすめ商品の一般名提示、話題ごとに保存
- 価格交渉アシスタント: 希望金額、商品情報、公開コメント、ユーザーの立場を踏まえて丁寧な交渉文を生成
- 販売改善通知: 7日以上売れ残っている商品に対して、サイズ追記、キーワード、値下げ目安などを出品者へ通知
- Gemini / Vertex AI が使えない場合も、ローカルフォールバックによりデモが止まらない

### 設計上の工夫

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
├── .gitignore                                      # 親リポジトリ全体の除外設定
├── .gitmodules                                     # フロントエンド・バックエンドをサブモジュール管理する場合の設定
├── DEPLOY_GCP.md                                   # GCP / Vercel / Cloud Run / Cloud SQL へのデプロイ手順
├── IMPLEMENTATION_NOTES.md                         # 実装意図、設計判断、保守時の注意点
├── README.md                                       # 完成物の概要、機能一覧、ローカル実行手順、デモ手順
├── docker-compose.local.yml                        # ローカル開発用MySQLを起動するDocker Compose設定
├── hackathon_db_api_design.xlsx                    # DB/API/UI/タスク設計仕様書
│
├── docs/
│   ├── ARCHITECTURE.md                             # 全体アーキテクチャ、責務分離、処理フローの整理
│   ├── DEMO_SCRIPT.md                              # Demo Dayでの説明順、見せ場、操作手順
│   ├── ER_dbml.pdf                                 # dbdiagram.io / DBML からPDFエクスポートしたER図
│   ├── er_diagram.dbml                             # dbdiagram.io 用ER定義
│   ├── er_diagram.drawio                           # draw.io形式のER図
│   ├── hackathon_ui_ux_design.drawio               # 総合UI/UX設計図面
│   ├── screen_transition.drawio                    # 画面遷移図
│   └── wireframe.drawio                            # 主要画面のワイヤーフレーム
│
├── hackathon-backend/
│   ├── .env                                        # ローカル開発用のバックエンド環境変数
│   ├── .env.example                                # バックエンド環境変数の記入例
│   ├── .git                                        # サブモジュール参照情報、またはGit管理情報
│   ├── .gitignore                                  # バックエンド側の除外設定
│   ├── Dockerfile                                  # Cloud Run向けGo APIコンテナ定義
│   ├── Makefile                                    # よく使うGoコマンドの補助
│   ├── README.md                                   # バックエンド単体の説明
│   ├── go.mod                                      # Goモジュール定義
│   ├── go.sum                                      # Go依存関係のチェックサム
│   │
│   ├── cmd/
│   │   └── server/
│   │       └── main.go                             # APIサーバー起動点、ルーティング、CORS、定期AI販売改善通知
│   │
│   ├── internal/
│   │   ├── ai/
│   │   │   └── gemini.go                           # Gemini / Vertex AI / ローカルフォールバックによるAI応答生成
│   │   │
│   │   ├── auth/
│   │   │   └── jwt.go                              # JWT生成、JWT検証、認証ミドルウェア
│   │   │
│   │   ├── config/
│   │   │   └── config.go                           # DB接続情報、AI設定、CORS設定などの環境変数読み込み
│   │   │
│   │   ├── db/
│   │   │   └── db.go                               # MySQL接続、接続プール設定、疎通確認
│   │   │
│   │   ├── handler/
│   │   │   └── handler.go                          # HTTPハンドラ、入力検証、認証ユーザー取得、JSONレスポンス
│   │   │
│   │   ├── httpx/
│   │   │   └── json.go                             # JSONエラー応答・成功応答の共通ユーティリティ
│   │   │
│   │   ├── models/
│   │   │   └── models.go                           # APIリクエスト/レスポンス、DB取得結果、共有モデル定義
│   │   │
│   │   └── repository/
│   │       ├── ai_chat_repository.go               # AI対話スレッド・AI対話メッセージのDB永続化
│   │       ├── item_repository.go                  # 商品、購入、出品履歴、購入履歴、チェックリスト、販売改善通知のDB処理
│   │       ├── message_repository.go               # 公開コメント、非公開DM、コメント削除のDB処理
│   │       └── user_repository.go                  # ユーザー、残高、売上、支払い方法、通知、評価のDB処理
│   │
│   └── migrations/
│       └── 001_init.sql                            # 初期DBスキーマ、外部キー、インデックス、デモユーザー、デモ商品
│
├── hackathon-frontend/
│   ├── .env                                        # ローカル開発用フロントエンド環境変数
│   ├── .env.example                                # フロントエンド環境変数の記入例
│   ├── .git                                        # サブモジュール参照情報、またはGit管理情報
│   ├── .gitignore                                  # フロントエンド側の除外設定
│   ├── Dockerfile                                  # フロントエンド配信用コンテナ定義
│   ├── README.md                                   # フロントエンド単体の説明
│   ├── cloudbuild.frontend.yaml                    # Cloud Buildでフロントエンドをビルドする設定
│   ├── index.html                                  # ViteアプリのHTMLエントリ
│   ├── nginx.conf                                  # コンテナ配信時のNginx設定
│   ├── package-lock.json                           # npm依存関係の固定
│   ├── package.json                                # npm scripts、React/Vite/TypeScript依存関係
│   ├── tsconfig.app.json                           # アプリ本体向けTypeScript設定
│   ├── tsconfig.json                               # TypeScriptプロジェクト参照設定
│   ├── tsconfig.node.json                          # Vite設定ファイル向けTypeScript設定
│   ├── tsconfig.tsbuildinfo                        # TypeScript増分ビルド情報
│   ├── vite.config.ts                              # Viteビルド設定、開発サーバー設定
│   │
│   └── src/
│       ├── App.tsx                                 # 画面ルーティング、ヘッダー、ログイン状態に応じたナビゲーション
│       ├── ErrorBoundary.tsx                       # React実行時エラーを画面全体で受け止める安全装置
│       ├── TranslatedText.tsx                      # 日本語固定表示の互換コンポーネント
│       ├── formOptions.ts                          # カテゴリ、状態、配送方法など出品フォーム選択肢
│       ├── i18n.tsx                                # 英語切替削除後も既存実装を壊さない日本語固定互換レイヤー
│       ├── imageUpload.ts                          # 画像・動画アップロード、Data URL化、メディア種別判定
│       ├── main.tsx                                # Reactアプリ起動点、DOMマウント処理
│       ├── savedSearch.ts                          # 検索条件保存・復元用ユーティリティ
│       ├── searchUtils.ts                          # 商品一覧、履歴、チェックリストで使う検索・絞り込み処理
│       ├── styles.css                              # 全体スタイル、レスポンシブ、カード、2列履歴、AI対話、マイページ装飾
│       ├── types.ts                                # フロントエンド全体で共有するTypeScript型定義
│       ├── utils.ts                                # 日時、金額、JST表示、メディア配列、表示補助の共通処理
│       ├── vite-env.d.ts                           # Vite用の型宣言
│       │
│       ├── api/
│       │   └── client.ts                           # REST APIクライアント、認証ヘッダー付与、各API呼び出し関数
│       │
│       ├── components/
│       │   └── ImageReorderGrid.tsx                # 画像・動画の追加、削除、ドラッグ&ドロップ並び替えUI
│       │
│       ├── context/
│       │   └── AuthContext.tsx                     # ログイン状態、JWT、現在ユーザー、ログイン/ログアウト処理
│       │
│       └── pages/
│           ├── AIChatPage.tsx                      # スレッド型AI対話ページ、話題リスト、会話履歴、AI応答表示
│           ├── ChecklistPage.tsx                   # チェックリスト画面、Available/SOLDの2列表示、検索対応
│           ├── CreateItemPage.tsx                  # 出品画面、商品情報入力、画像・動画アップロード、AI説明生成
│           ├── ItemDetailPage.tsx                  # 商品詳細、購入導線、公開コメント、価格交渉AI、非公開DM
│           ├── ItemListPage.tsx                    # 商品一覧、検索、検索条件保存、AIおすすめ、自然言語検索
│           ├── LoginPage.tsx                       # ログイン画面
│           ├── MyItemsPage.tsx                     # 出品履歴、Available/SOLDの2列表示、商品編集導線
│           ├── MyPage.tsx                          # マイページ、残高、売上/利用額、月別グラフ、支払い方法登録
│           ├── NotificationsPage.tsx               # 通知一覧、既読管理、販売改善通知、取引通知、支払い方法通知
│           ├── PurchaseFlowPage.tsx                # 購入手続き、残高確認、支払い方法確認、購入確定
│           ├── PurchaseHistoryPage.tsx             # 購入履歴、未完了/取引完了の2列表示、受け取り評価導線
│           └── RegisterPage.tsx                    # 新規登録画面
│
└── ml/
    ├── README.md                                   # ML側の概要、MerRec分析、推薦APIの説明
    ├── merrec_artifact.json                        # MerRec分析結果・推薦用成果物JSON
    ├── merrec_model.pkl                            # 学習済み推薦モデルのpickleファイル
    ├── merrec_model.py                             # MerRec由来データの前処理、特徴量化、モデル部品
    ├── merrec_recommender.py                       # MerRec学習/分析、TF-IDF、SVD、近傍探索、推薦生成
    ├── recommender_service.py                      # 軽量推薦API、商品推薦・販売改善提案の補助
    ├── requirements.txt                            # ML側Python依存関係
    └── sample_merrec.csv                           # 推薦処理確認用のサンプルMerRecデータ
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

### 7.1 マイページ

1. `user2@example.com / user2222` でログインする。新規登録の場合はユーザー名、メールアドレス、パスワードで登録し、JWT認証が用いられることを説明する。
2. マイページを開く。
3. 残高、今月/累計売上額、今月/累計利用額、出品者評価の表示を確認する。
4. 月別売上額と利用額の棒グラフを見せ、お金の出入りが視覚的にわかりやすく表示されることを説明する。
5. 支払い情報の登録情報を削除して残高チャージを試みて失敗する。
6. 支払い情報を登録する。複数カードを登録して既定カードを選択できることを説明する。
7. 100円の残高チャージを行い、残高に反映されることを確認する。
8. 住所を登録できること、出品時の発送元地域と購入時のお届け先に自動で反映されることを説明する。
9. 運営にテストDMを送る。トラブル対応用やご意見箱として、ユーザと運営の交流も実現できることを説明する。
10. マイページでの登録などが通知に反映されていることを示し、該当ページに直接遷移できることを説明する


### 7.2 出品

1. 出品画面を開いて商品情報を入力する。
2. 複数画像と短い動画をアップロードする。
3. ドラッグ&ドロップでメディア順を入れ替える。画像の削除も試してみる。
4. 「発送元の地域」にマイページでの登録情報が反映されていることを確認する。
6. AI商品説明生成を実行する。
5. 「発送元の地域」を空欄にして「出品する」に失敗することで必須項目のチェックを見せる。
7. 空欄を埋めて出品完了後に通知が届くことを見せる。
8. 通知から遷移した出品履歴の「Available」に現れることを確認する。
9. 出品履歴画面が左右で「Available」「SOLD」に分けて2列で表示されていること、更新日時で並び替えができることを確認する。また、出品履歴内検索が機能することも確認する。
10. 出品履歴画面から「商品情報の編集」「出品キャンセル」ができることを確認する。


### 7.3 商品一覧

2. 商品一覧で初期20商品が表示されることを見せる。
3. サイドバーで検索条件を「入力」「チェックボックス」「プルダウン」などにより指定できることを説明する。
4. 自然言語検索に `参考書 300円 ~ 1500円` と入力し、検索条件へ自動変換されることを見せる。
5. 検索条件を保存、適用してみる。保存した条件はマイページで管理、削除できることを説明する。
6. MerRecデータセット分析に基づくおすすめ商品がDB内の商品から安定して表示されることを説明する。
7. 「微分積分学参考書」を選択し、商品情報詳細の説明に移る。

### 7.4. 商品詳細、購入前AI、価格交渉、コメント/DM

1. 商品情報詳細を確認する。
2. 複数画像・動画を添付できることを説明し、画像・動画カルーセル、循環を見せる。
3. AI購入アシストで商品画像や販売状況、出品者評価などに基づくコメントを表示します。
3. 購入前AIチェックで、不安点、質問候補、不整合チェック、価格感、カテゴリ別レビュー知識の情報が出ることを見せる。
4. 商品をチェックリストに追加する。チェックリストから対象商品のページに直接遷移できること、チェックリスト内の「値下げ」や「出品キャンセル」などの商品情報変更に対して通知が届くようになることなどを説明する。
5. 出品者のブロックができることを確認する。ブロックすると相互に商品が表示されなくなること、ブロックはマイページで管理できることを説明する。
6. AIに商品について質問する。(例：「初学者でも理解できますか？」)
7. 価格交渉アシスタントに希望金額を入力し、購入検討者向けの丁寧な交渉文が出ることを見せる。
8. 出品者アカウントでは、承諾、代替案、お断りの文面が出ることを説明する。
9. 公開コメントを見せる。更新時刻で並び替えが行われることを説明する。
10. 非公開DMは購入検討者自身と出品者だけが見られることを説明する。


### 7.5 出品者側の表示確認

1. 出品者として `user1@example.com / user1111` でログインする。
2. 出品した商品へのコメントについての通知が届いていることを確認する。
3. 公開コメントに返信するとスレッド状になることを示す。出品者のコメントは色で強調されることを説明する。
4. 出品者は自分の商品についた公開コメントを削除できることを説明する。
5. 価格交渉アシスタントに希望金額を入力し、出品者向けの丁寧な交渉文が出ることを見せる。
6. 「出品履歴で編集する」から「商品情報を編集」で価格を「1150」に変更する。


### 7.6 商品購入

1. 購入者として `user2@example.com / user2222` で再ログインする。
2. チェックリストに入れていた商品の値下げ通知が届いたことを確認する。
3. 購入手続きに進む
4. 残高が不足しているのでその場でチャージする。
5. お届け先住所にマイページで登録した住所が反映されていることを確認する。
6. 購入手続きを完了すると、通知が届くことや、購入履歴の「取引中」欄に反映されることを確認する。購入フローが表示されていることも確認する。
7. マイページに移り、残高が減って利用額が増えていることを確認する。グラフに反映されていることも確認する。


### 7.7. 商品発送

1. 出品者として `user1@example.com / user1111` で再ログインする。
2. 購入手続きが完了した旨の通知が届いていることを確認し、直接遷移して発送する。
3. 発送完了通知が届くことを確認し、マイページに移動する。この段階ではまだ残高・売上額ともに増えていないことを確認して、受け取り評価完了後に売上に反映されることを説明する。


### 7.8 受け取り評価

1. 購入者として `user2@example.com / user2222` でログインする。
2. 発送が完了した旨の通知が届いていることを確認し、直接遷移して受け取り評価をする。
3. 取引完了通知が届くことを確認し、購入履歴に移動する。商品が「取引完了」の位置に表示されることを確認する。


### 7.9 取引完了、残高反映

1. 出品者として `user1@example.com / user1111` でログインする。
2. 取引完了通知が届いたことを確認し、出品履歴に移動する。商品が「SOLD」の位置に表示されることを確認する。
3. マイページの残高と売上額、グラフに反映されていることを確認する。出品者評価の件数が増え、評価値も反映されていることを確認する。


### 7.10. 改めて、履歴、チェックリストページのUXの確認

1. 出品履歴を開き、左にAvailable、右にSOLDが分かれて表示されることを見せる。
2. Availableは古い順で、長く売れ残っている商品を上から確認できることを説明する。
3. SOLDは新しい順で、直近の取引を確認しやすいことを説明する。
4. 購入履歴では、未完了取引と取引完了済みが左右に分かれることを見せる。
5. チェックリストでは、気になる商品の販売中/売り切れを左右に分けて確認できることを見せる。
6. いずれも検索対象であり、商品概要クリックで詳細へ遷移できることを見せる。
7. いずれについても並び替えが古い順、新しい順で選択できることを説明する。

### 7.11. AI対話スレッド

1. ヘッダーからAI対話ページを開く。
2. 「新しい話題」を作る。
3. 例文 `休日の遊びのおすすめない？` を送信する。
4. 回答の最後に「おすすめグッズ」が一般名で出ることを見せる。
5. 別の話題として `家の模様替えをしてみたいんだけどいい案ない？` を送信する。
6. 左側のスレッドリストで話題ごとに履歴が分かれていることを見せる。
7. ページを移動して戻っても履歴が残ることを説明する。
8. スレッドを削除できることを確認する。


### 7.12. 販売改善通知

1. 通知ページに `AI販売改善提案` が表示されることを見せる。
2. 7日以上売れ残っている商品に対して、サイズ追記、キーワード、価格調整のヒントが出ることを説明する。
3. MerRec分析の考え方を、売れ残り改善・価格調整・検索キーワード提案へ接続していることを説明する。

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