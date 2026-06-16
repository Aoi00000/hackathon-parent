# IMPLEMENTATION_NOTES

このドキュメントは、AI Flea Market の実装意図、責務分離、発展的機能、Demo Day向けの見せ方をまとめたものです。

## 1. アーキテクチャ

### バックエンド

```text
hackathon-backend/
├── cmd/server/main.go              # 起動点。設定読み込み、DB接続、ルーティング登録を行う。
├── internal/config/config.go       # 環境変数をConfig構造体へ集約する。
├── internal/db/db.go               # MySQL接続を作る。
├── internal/models/models.go       # APIレスポンス・リクエスト・DBモデルを定義する。
├── internal/repository/            # DB操作を集約する。
├── internal/handler/handler.go     # HTTPリクエストを受け、repository/aiを呼び出す。
└── internal/ai/gemini.go           # Gemini / Vertex AI / フォールバック生成を扱う。
```

責務を完全に分離することで、DB、HTTP、AI、認証の修正が互いに影響しにくい構造にしています。

### フロントエンド

```text
hackathon-frontend/src/
├── api/client.ts                   # API通信を一元化する。
├── context/AuthContext.tsx         # ログイン状態を保持する。
├── pages/                          # 画面単位のReactコンポーネント。
├── utils.ts                        # 日時、金額、画像URLなどの共通処理。
├── imageUpload.ts                  # 画像ファイルをData URLへ変換する。
├── searchUtils.ts                  # 表記揺れ検索・曖昧検索。
└── styles.css                      # UI全体の一貫したデザイン。
```

## 2. AI設計

外部AI呼び出しは `internal/ai/gemini.go` に集約しています。

処理の流れは次の通りです。

1. `AI_PROVIDER` を見る
2. `vertex` の場合は Vertex AI を呼ぶ
3. `ai_studio` の場合は Google AI Studio API を呼ぶ
4. 429や認証エラーなどで失敗した場合は、ローカル簡易生成へフォールバック
5. フォールバック理由はログとAPIレスポンスに分離して返す

この構成により、外部AIの利用枠が切れていても、デモ中にアプリが止まりません。

## 3. Vertex AI 429対策

現在のコードでは以下を実装しています。

- `GEMINI_MODEL=gemini-2.5-flash`
- `VERTEX_LOCATION=global`
- 5回の短い指数バックオフ
- フォールバック時のログ表示

429 ResourceExhausted はアプリのバグではなく、Vertex AI側の割当・共有容量・一時混雑で起こります。
本番では Quota Increase Request や Provisioned Throughput の検討が必要です。

## 4. UX上の工夫

- Amazon/Mercari風の左サイドバー検索
- コンパクトな商品カード
- 複数画像カルーセル
- 出品画像の個別削除
- 出品履歴から画像を再編集
- 通知バッジ
- 既読/未読通知
- 出品キャンセル通知
- チェックリストユーザーへのキャンセル通知
- 購入履歴から受け取り評価
- 出品者評価の星表示
- マイページの残高・売上・利用額・評価サマリー

## 5. AI活用価値

単なる商品説明生成だけではなく、次の機能で「次世代フリマアプリ」らしさを出しています。

- 購入前AIチェック
- 商品説明から不安点を抽出
- 購入者が質問すべき項目を提示
- 出品文・カテゴリ・状態の不整合を検出
- 類似商品価格から価格妥当性を推定
- MerRecを想定したおすすめ欄
- MerRec streaming 分析スクリプト
- Python推論サーバー分離

## 6. データベース設計上の注意

`items.image_url` は互換性のため名前を維持していますが、中身は次の2形式に対応します。

- 旧形式: 単一URL文字列
- 新形式: JSON配列文字列

例:

```json
["data:image/svg+xml;base64,...", "data:image/svg+xml;base64,..."]
```

フロントエンドの `parseImageUrls()` が両方を解釈します。

## 7. 金額表記

DB/API内部では過去実装との互換性のため `balance_coins` や `sales_coins` という名前を残しています。
ただし、画面・通知などのユーザー向け表記はすべて `¥` に統一しています。

## 8. 文字化け対策

`001_init.sql` には `SET NAMES utf8mb4` を入れています。
初期化時にも必ず以下のように `--default-character-set=utf8mb4` を付けます。

```bash
mysql --default-character-set=utf8mb4 -uhackathon_user hackathon < 001_init.sql
```

既に文字化けしたDBはフロント側では直せないので、`docker compose down -v` でvolumeを消してから再投入してください。

---

## 2026-06-17 UI polish and natural language search

### Responsibility separation

Natural language search is implemented as a thin AI-to-filter conversion layer.

- Frontend `ItemListPage.tsx`
  - Owns the visual input box.
  - Sends the natural sentence to `aiApi.parseSearch`.
  - Applies the returned filter params to the existing sidebar state.
  - Calls the existing `itemApi.list` endpoint.

- Backend `ParseNaturalSearch`
  - Receives a plain Japanese search sentence.
  - Tries Vertex AI / Gemini first.
  - Falls back to deterministic local parsing if the external AI fails.
  - Returns the same shape as the existing search query params.

This avoids creating a second search implementation. The existing `ItemRepository.List` and `BuildFilterFromQuery` remain the single source of truth for item filtering.

### Fallback strategy

External LLM calls are useful for ambiguous expressions such as:

- 「使用感が少なくてきれい」
- 「予算1万円以内」
- 「安い順」
- 「明日までに発送」

However, Vertex AI can return 429 during demos. To keep the UX stable, the handler always returns a valid filter object. When the external call fails, the local parser handles common Japanese expressions for budget, condition, category, sort order, and shipping speed.

### UI strategy

The product listing page now has three clear zones:

1. Left sidebar search.
2. Hero + natural language search.
3. Highlighted recommendation strip + compact product grid.

This keeps the Amazon/Mercari-like density while giving the AI feature a visible, demo-friendly location.
