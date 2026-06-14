# 実装メモ: MerRec / AI / i18n 高度化

## 追加した機能

- 商品詳細に「購入前AIチェック」を追加
  - 商品説明から不安点を抽出
  - 購入者が出品者に確認すべき質問を提案
  - 出品文・カテゴリ・状態の不整合を検出
  - 同カテゴリ商品の価格分布から高すぎる/安すぎる可能性を提示
- 出品画面にカテゴリ別レビュー知識を表示
  - MerRec の低評価レビュー・有用票レビューを分析する前提で、カテゴリごとの購入者関心点を提示
- 日本語 / English 切り替えを再実装
  - 日本語がデフォルト
  - 英語表示では静的UIを辞書変換
  - 商品名・説明・AI回答などの動的文言は Gemini / Vertex AI 翻訳APIを利用
  - 日本語へ戻す場合は再翻訳せず、元の日本語データを表示
- MerRec を使ったMLレコメンド用 `ml/` を高度化
  - scikit-learn TF-IDF + TruncatedSVD + NearestNeighbors
  - optional: implicit ALS 協調フィルタリング
  - bought-together graph / review concern mining へ拡張しやすい構成
  - Python推論サービス例を追加
- PC / タブレット / スマートフォン向けのレスポンシブCSSを追加

## ローカル起動

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent

docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d

docker compose -f docker-compose.local.yml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -uhackathon_user hackathon' \
  < hackathon-backend/migrations/001_init.sql
```

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent/hackathon-backend
set -a
source .env
set +a
go run ./cmd/server
```

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

## MerRec ML 実行

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent
python3 -m venv .venv-ml
source .venv-ml/bin/activate
pip install -U pip
pip install -r ml/requirements.txt
```

データを `data/amazon2023/` に置いたあと、まず小さく試します。

```bash
python ml/merrec_recommender.py \
  --meta data/amazon2023/meta_Books.jsonl.gz \
  --reviews data/amazon2023/reviews_Books.jsonl.gz \
  --out ml/recommender_artifact.json \
  --pickle ml/recommender_model.pkl \
  --limit 50000 \
  --review-limit 200000 \
  --topk 20
```

Python推論サービスとして使う場合:

```bash
python ml/recommender_service.py --model ml/recommender_model.pkl --port 8090
```

```bash
curl -X POST http://127.0.0.1:8090/recommend \
  -H 'Content-Type: application/json' \
  -d '{"text":"calculus textbook beginner university entrance exam", "top_k":5}'
```
