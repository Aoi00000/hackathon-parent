# Webコース準拠 AIフリマアプリ Starter

このスターターは、研修資料のWebコース要件に合わせて、Goバックエンド、Reactフロントエンド、MySQL、Gemini API、GCPデプロイを前提にしたMVPです。

## MVPで満たす機能

- ユーザー登録・ログイン
- 商品一覧・検索
- 商品出品
- 商品購入
- 商品に紐づくDM
- Gemini APIによる商品説明生成
- Gemini APIによる商品Q&A

## ディレクトリ

- `hackathon-backend`: Go + MySQL + Gemini API。Cloud Runにデプロイします。
- `hackathon-frontend`: React + TypeScript + Vite。静的ファイルをnginxで配信するコンテナとしてCloud Runにデプロイします。

## ローカル起動の流れ

1. MySQLで `migrations/001_init.sql` を実行する
2. `hackathon-backend/.env.example` を参考に環境変数を設定する
3. `cd hackathon-backend && go mod tidy && go run ./cmd/server`
4. `hackathon-frontend/.env.example` を `.env` にコピーする
5. `cd hackathon-frontend && npm install && npm run dev`

## GCPデプロイの流れ

1. Cloud SQL for MySQLを作成
2. 初期SQLを投入
3. Secret ManagerにDBパスワード、JWT_SECRET、GEMINI_API_KEYを登録
4. Cloud Runにバックエンドをデプロイ
5. Cloud Runにフロントエンドをデプロイ
6. `FRONTEND_ORIGIN` と `VITE_API_BASE_URL` を相互に正しく設定する
