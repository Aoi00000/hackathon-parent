# MerRecを使った高度レコメンド実験

このディレクトリは、MercariのC2Cマーケットプレイス由来のMerRecデータセットを使って、ハッカソンアプリの推薦ロジックを高度化するための任意実行ツール群です。Webアプリ本体とは分離しているため、MVPを壊さずに、ローカルまたは別Cloud Runサービスで学習・推論を行えます。

MerRecは、匿名化・派生処理されたMercariの大規模C2C推薦データセットです。Hugging Faceのデータセットカードでは、5百万超のユーザー、8千万超のアイテム、10億超のイベント、2億超のセッション、80億超のアイテムタイトルtext tokenを含むと説明されています。全量は非常に大きいため、まずは1か月・数万〜数十万行のサンプルで試してください。

## 1. 環境作成

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent
python3 -m venv .venv-ml
source .venv-ml/bin/activate
pip install -U pip
pip install -r ml/requirements.txt
```

`implicit` が環境によって入らない場合は、`ml/requirements.txt` の `implicit>=0.7.2` をコメントアウトしてください。その場合も、TF-IDF + 価格/カテゴリ特徴に基づく関連商品推薦は動作します。

## 2. データ準備

Hugging Faceの `mercari-us/merrec` から、まずは1か月分のparquet shardを一部だけ取得してください。例:

```bash
mkdir -p data/merrec/20230501
# ブラウザ、huggingface-cli、git-lfsなどでparquetを数個だけ配置します。
# data/merrec/20230501/000000000000.parquet のような形を想定します。
```

公式実験コードでは、セッション推薦ではraw dataをメモリ上でsequenceへ変換できること、MTL/CTR用には `preprocess_mtl.py` が `item_view`, `item_like`, `item_add_to_cart_tap`, `offer_make`, `buy_start`, `buy_comp` などのイベントを扱うことが示されています。このスクリプトでも同じ思想で、イベント種別を重みとして使います。

## 3. 学習・モデル作成

```bash
python ml/merrec_recommender.py \
  --input data/merrec/20230501 \
  --out-json ml/merrec_artifact.json \
  --out-pkl ml/merrec_model.pkl \
  --limit 200000 \
  --topk 30
```

生成物:

- `ml/merrec_artifact.json`: Goやフロントエンドでも読みやすい軽量JSON。カテゴリ別人気、イベント重み、簡易関連商品を含みます。
- `ml/merrec_model.pkl`: Python推論サーバー用。TF-IDF、SVD、NearestNeighbors、任意のimplicit ALSモデルを含みます。

## 4. Python推論サーバー

```bash
python ml/recommender_service.py --model ml/merrec_model.pkl --port 8090
```

確認:

```bash
curl -X POST http://127.0.0.1:8090/recommend \
  -H 'Content-Type: application/json' \
  -d '{"title":"calculus textbook beginner math", "category":"Books", "price":1200, "brand":"", "session_titles":["linear algebra textbook"], "top_k":5}'
```

## 5. アプリへの組み込み方針

現状のGoバックエンド `/api/me/recommendations` は、アプリ内商品のチェックリスト数・新着順・価格帯を使って安全に動作するMVP推薦です。MerRecモデルを本番組み込みする場合は、次のどちらかがおすすめです。

1. **軽量JSON連携**: `merrec_artifact.json` からカテゴリ別人気や関連カテゴリをGoに読み込む。
2. **推論マイクロサービス**: `recommender_service.py` を別Cloud Runサービス化し、GoからHTTPで問い合わせる。

ハッカソンでは、まず1の軽量JSON連携、余裕があれば2のマイクロサービス化が安全です。
