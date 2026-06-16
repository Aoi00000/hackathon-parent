# MerRec 推薦分析

このディレクトリには、MercariのMerRecデータセットを用いた推薦分析用コードを置いています。

## 構成

- `merrec_model.py`
  - 学習側と推論側で共有する `MerRecModel` 定義です。
  - pickle内のクラス参照が `__main__` にならないよう、必ずこのファイルをimportします。
- `merrec_recommender.py`
  - Hugging Face streaming またはローカルファイルからデータを読み、TF-IDF + SVD + NearestNeighborsで推薦モデルを作ります。
- `recommender_service.py`
  - 作成した `merrec_model.pkl` を読み込み、HTTP API `/recommend` として提供します。
- `sample_merrec.csv`
  - ネットワークなしでも構文・推論確認ができる小さなサンプルです。

## 環境構築

```bash
cd /Users/moment/Documents/UTTC/hackathon/hackathon-parent
python3 -m venv .venv-ml
source .venv-ml/bin/activate
python -m pip install -U pip
python -m pip install -r ml/requirements.txt
# Hugging Face Datasetsとは別に、ユーザー環境で必要になる場合があるため追加します。
python -m pip install dataset
```

## サンプルデータでの最小確認

```bash
python ml/merrec_recommender.py \
  --input ml/sample_merrec.csv \
  --out-json ml/sample_artifact.json \
  --out-pkl ml/sample_model.pkl \
  --limit 1000 \
  --topk 3
```

```bash
python ml/recommender_service.py --model ml/sample_model.pkl --port 8099
```

別ターミナル:

```bash
curl http://127.0.0.1:8099/healthz
curl -X POST http://127.0.0.1:8099/recommend \
  -H 'Content-Type: application/json' \
  -d '{"title":"calculus math book","category":"Books Education Math","price":13,"top_k":2}'
```

## Hugging Face streamingでMerRecを読む

全量を一括ダウンロードせず、反復した分だけ読みます。まず1000件で試します。

```bash
rm -f ml/merrec_model.pkl ml/merrec_artifact.json
python ml/merrec_recommender.py \
  --hf \
  --hf-dataset mercari-us/merrec \
  --hf-split train \
  --out-json ml/merrec_artifact.json \
  --out-pkl ml/merrec_model.pkl \
  --limit 1000 \
  --topk 10
```

成功後、50000件へ増やします。

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

## pickle確認

```bash
python - <<'PY'
import pickle
import sys
sys.path.insert(0, "ml")
from merrec_model import MerRecModel
with open("ml/merrec_model.pkl", "rb") as f:
    model = pickle.load(f)
print(type(model))
print(isinstance(model, MerRecModel))
print("items:", len(model.items))
print("version:", model.version)
PY
```

`<class 'merrec_model.MerRecModel'>` と `True` が出れば正常です。
