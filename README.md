# AI Flea Market

React + Go + MySQL + Gemini / Vertex AI によるWebコース準拠の次世代フリマアプリです。

## 主な機能

- ユーザー登録・ログイン
- 商品出品・購入・取引状態管理
- 公開コメント / 非公開DM
- チェックリスト
- 通知一覧
- 残高チャージと仮想通貨決済
- 商品一覧のAmazon風サイドバー検索
- 曖昧検索
- AI商品説明生成
- AI質問応答
- AI購入アシスト
- 購入前AIチェック
- 日本語 / English 表示切り替え
- MerRec を使ったMLレコメンド実験環境

## 注意

`package-lock.json` は配布zipに含めていません。利用環境の public npm registry で再生成してください。

```bash
cd hackathon-frontend
npm config set registry https://registry.npmjs.org/
rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmjs.org/
npm run build
```
