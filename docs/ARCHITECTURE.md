# AI Flea Market アーキテクチャ整理

このドキュメントは、Demo Day とコードレビューで説明しやすいように、アプリ全体の責務分担を整理したものです。

## 全体構成

```text
hackathon-parent/
├── docker-compose.local.yml      # ローカルMySQL
├── hackathon-backend/            # Go APIサーバー
├── hackathon-frontend/           # React + TypeScript UI
├── ml/                           # MerRec分析・推論サーバー
├── README.md                     # 実行方法・機能一覧
└── IMPLEMENTATION_NOTES.md       # 実装意図・設計メモ
```

## 責務分離

### フロントエンド

- 画面表示、フォーム状態、画像プレビュー、自然言語検索UIを担当します。
- API呼び出しは `src/api/client.ts` に集約しています。
- 日付、金額、画像URL処理などの共通処理は `src/utils.ts` にまとめています。
- 英語切り替えは要件から外したため、`i18n.tsx` は日本語固定の互換レイヤーとして残しています。

### バックエンド

- HTTPハンドラは `internal/handler/handler.go` に集約しています。
- DBアクセスは `internal/repository/` に分離しています。
- AI呼び出しは `internal/ai/gemini.go` に分離し、Gemini API / Vertex AI / ローカルフォールバックの切り替えを一箇所で扱います。
- 認証は `internal/auth/`、設定は `internal/config/`、DB接続は `internal/db/` に分けています。

### ML / MerRec

- `ml/merrec_recommender.py` は MerRec を Hugging Face streaming またはローカルファイルから読み、推薦モデルを作成します。
- `ml/merrec_model.py` は pickle の `__main__` 問題を避けるための共有モデル定義です。
- `ml/recommender_service.py` は作成済みモデルをHTTP APIとして試すための軽量サーバーです。

## AI機能の方針

外部AIは便利ですが、Demo Dayではクォータ不足や429が起こる可能性があります。そのため、以下の方針にしています。

1. まず Vertex AI / Gemini を呼ぶ。
2. 成功すれば外部AIの結果を使う。
3. 失敗時はローカル簡易生成にフォールバックする。
4. フォールバック理由はバックエンドログに残し、UI上でも必要な注意文だけ表示する。

この構成により、AI利用枠が不安定でも、デモ中に画面が止まらないようにしています。