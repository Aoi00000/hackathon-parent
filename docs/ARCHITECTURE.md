# AI Flea Market アーキテクチャ整理

このドキュメントは、AI Flea Market を完成物として説明するためのアーキテクチャメモです。評価項目である「拡張性・保守性」「コード品質」「完成度」「AI活用価値」を説明できるように、画面、API、DB、AI、ML分析の責務を整理しています。

## 1. 全体構成

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

## 2. レイヤーごとの責務

### フロントエンド

- `src/pages/*` が画面単位のUIを担当する。
- `src/api/client.ts` がAPI呼び出しを一元管理する。
- `src/types.ts` がGoのJSONレスポンスと対応するTypeScript型を定義する。
- `src/utils.ts` がメディアURL配列、日付、金額、評価表示などの共通処理を担当する。
- `src/imageUpload.ts` が画像圧縮と動画サイズ確認を担当する。
- `src/components/ImageReorderGrid.tsx` が複数画像・動画の追加、削除、ドラッグ&ドロップ並び替えを担当する。
- 英語切替は最終仕様から外しており、`i18n.tsx` と `TranslatedText.tsx` は日本語固定の互換レイヤーとして残している。

### バックエンド

- `cmd/server/main.go` は設定読み込み、DB接続、HTTPルーティング、CORS、販売改善通知の定期起動を担当する。
- `internal/handler/handler.go` はHTTP入力検証、Repository呼び出し、AIプロンプト生成、JSONレスポンス生成を担当する。
- `internal/repository/` はDBアクセスを担当する。
- `internal/ai/gemini.go` はGemini API / Vertex AI / ローカルフォールバックを担当する。
- `internal/auth/` はJWT認証を担当する。
- `internal/config/` は環境変数読み込みを担当する。

### DB

- `users` は残高、売上、住所、評価、取引実績を持つ。
- `items` は商品情報と複数画像・動画JSON文字列を持つ。
- `purchases` は購入、発送、受け取り評価、取引完了を管理する。
- `messages` は公開コメントと返信スレッドを管理する。
- `private_messages` は非公開DMと返信スレッドを管理する。
- `notifications` は購入、発送、評価、支払い方法登録、商品更新、販売改善提案などの通知を管理する。
- `payment_methods` はチャージ用支払い方法を管理する。
- `ai_chat_threads` と `ai_chat_messages` はAI対話ページの話題別履歴を管理する。

## 3. 主要な設計ポイント

### 3.1 複数画像・動画の扱い

DB列名は既存実装との互換性を保つため `items.image_url` のままにしている。ただし中身は単一URL、旧画像URL、JSON配列のどれでも読めるようにしている。フロント側では `parseImageUrls()` と `stringifyImageUrls()` に変換処理を集約し、画面ごとに分岐を書かない設計にしている。

動画はData URLとして保存できるが、サイズ上限を設けている。ハッカソンデモではCloud Storage設定なしで完結できる一方、本番運用ではCloud Storageへアップロードし、DBにはURLを保存する構成へ置き換えやすい。

### 3.2 AI対話スレッド

AI対話ページは、DBに保存されるスレッド形式である。ユーザーは「休日の遊び」「模様替え」「勉強集中」など、話題ごとにスレッドを分けて履歴を残せる。

処理の流れは次の通りである。

1. フロントエンドが `GET /api/me/ai-chat-threads` でスレッド一覧を取得する。
2. スレッドを選ぶと `GET /api/me/ai-chat-threads/{id}/messages` で履歴を取得する。
3. 送信時は `POST /api/me/ai-chat-threads/{id}/messages` へユーザー発言を送る。
4. バックエンドがユーザー発言を保存する。
5. 直近履歴を含めたプロンプトでGemini / Vertex AIを呼ぶ。
6. 外部AIが失敗した場合はローカルフォールバック回答を作る。
7. AI回答もDBに保存し、ユーザー発言とAI回答の2件をまとめて返す。

この設計により、AIの活用価値が「単発の商品説明生成」から「継続的な生活・購買相談」へ拡張されている。

### 3.3 価格交渉アシスタント

価格交渉はフリマ特有の摩擦が生じやすい場面である。商品詳細では、希望金額、商品情報、公開コメント、現在ユーザーの立場をプロンプトに含め、購入検討者向け・出品者向けに異なる文面を生成する。

- 購入検討者には、失礼になりにくい値下げ依頼文を提示する。
- 出品者には、承諾、代替案、丁寧なお断りのテンプレートを提示する。
- 外部AIが失敗した場合も、ローカルテンプレートで最低限の交渉文を返す。

### 3.4 エスクロー風の取引残高フロー

購入時点では購入者の残高だけを減らす。出品者の残高と売上額は、購入者が受け取り評価を完了した時点で増やす。これにより、実際のフリマアプリに近い「商品到着確認後に売上確定」という流れになる。

```text
購入手続き完了
  -> buyer.balance_coins -= price_yen
  -> item.status = sold
  -> purchase.status = paid
  -> seller.balance_coins はまだ増えない

発送通知
  -> purchase.status = shipped
  -> buyerへ受け取り評価依頼通知

受け取り評価完了
  -> purchase.status = completed
  -> seller.balance_coins += price_yen
  -> seller.sales_coins += price_yen
  -> seller.rating_sum / rating_count / transaction_count 更新
```

### 3.5 販売改善通知

バックエンド起動時と24時間ごとに、7日以上更新されていない販売中商品を確認する。同じ商品へ同内容の通知を連続送信しないよう、直近7日以内の `AI販売改善提案` 通知を見て重複を防いでいる。

通知本文には、カテゴリ別に追記すべきサイズ・状態情報、検索に効きやすいキーワード、同カテゴリの完了取引価格を参考にした価格調整案を含める。これにより、MerRecの「過去取引傾向を販売改善へ使う」という発展性を、Web本体の通知UXへ接続している。

### 3.6 履歴系ページの2列レイアウト

出品履歴、購入履歴、チェックリストは、画面幅を広く使い、状態別に左右2列へ分けている。検索対象は全件のままにし、表示段階で状態別に分けることで、検索機能と一覧性を両立している。

- 出品履歴: 左にAvailableを古い順、右にSOLDを新しい順。
- 購入履歴: 左に未完了取引を古い順、右に完了取引を新しい順。
- チェックリスト: 左にAvailableを古い順、右にSOLDを新しい順。

## 4. 評価項目との対応

### 技術・実装

- Repository層を分け、DB処理の責務を明確化した。
- 複数テーブルを更新する購入、受け取り評価、出品キャンセル、支払い方法変更はトランザクションで扱う。
- AI呼び出しは `internal/ai` に集約し、外部AI失敗時もUIが止まらない。
- 画像・動画の変換処理を共通化し、出品画面と編集画面で同じUIを使う。

### 完成度・UX

- 出品、購入、発送、受け取り評価、通知、残高反映まで一連の取引がつながっている。
- 履歴ページを左右2列化し、取引状態を直感的に把握できるようにした。
- 複数画像・動画のドラッグ&ドロップ並び替えにより、出品体験が自然になった。
- 月別収支グラフにより、売上と利用額の動向を視覚的に把握できる。
- 支払い方法未登録時はチャージを止め、登録欄へ誘導する。

### テーマ性・独創性

- 自然言語検索、購入前AIチェック、商品Q&A、AI対話スレッド、価格交渉アシスタント、販売改善通知により、AIの使いどころを複数用意した。
- AIを単なる文章生成ではなく、検索、安心感、交渉摩擦低減、売れ残り改善に接続した。
- MerRec分析をWeb本体から分離しつつ、C2Cマーケットプレイス分析の発展性を示した。
- 取引フロー、通知、評価、ブロック、支払い方法を組み合わせ、実運用に近い次世代フリマ体験を作った。
