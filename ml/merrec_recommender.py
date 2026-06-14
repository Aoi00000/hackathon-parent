"""MerRecを使った実用寄りレコメンドモデル作成スクリプト。

目的:
- Mercari由来のC2C行動データから、ハッカソン用フリマアプリに取り込みやすい
  関連商品推薦モデルを作る。
- アプリ本体とは分離し、重い学習はPython側で行う。
- 推論時はpickleモデルをPythonマイクロサービスで使うか、軽量JSONをGoへ読み込む。

実装する推薦:
1. カテゴリーベース関連商品推薦
   - title / category階層 / brand / price を特徴量化
   - scikit-learnのTF-IDF + TruncatedSVD + NearestNeighborsで類似商品検索
2. セッション内閲覧パターンから次に見る商品を予測
   - session_idごとに時刻順にitemを並べ、隣接遷移を集計
3. 任意の協調フィルタリング
   - implicitが入っていれば、イベント重みつき user-item 行列でALSを学習

MerRecの列名は実験用データや公開バージョンで変わる可能性があるため、
このスクリプトでは候補列名を複数試し、存在する列だけで動くようにしています。
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import pickle
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer, StandardScaler

try:  # implicitは任意依存。入らない環境でもTF-IDF推薦は使える。
    import implicit  # type: ignore
except Exception:  # pragma: no cover
    implicit = None


EVENT_WEIGHTS = {
    "item_view": 1.0,
    "item_like": 3.0,
    "item_add_to_cart_tap": 5.0,
    "offer_make": 6.0,
    "buy_start": 8.0,
    "buy_comp": 12.0,
}


def first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """候補列名のうち、実際にDataFrameに存在する最初の列名を返します。"""
    for name in candidates:
        if name in df.columns:
            return name
    return None


def read_table(path: Path, limit: int | None) -> pd.DataFrame:
    """parquet/jsonl/csvを読み込みます。ディレクトリならparquetを結合します。"""
    if path.is_dir():
        frames: list[pd.DataFrame] = []
        total = 0
        for file in sorted(path.glob("*.parquet")):
            frame = pd.read_parquet(file)
            if limit is not None:
                remaining = max(limit - total, 0)
                frame = frame.head(remaining)
            frames.append(frame)
            total += len(frame)
            if limit is not None and total >= limit:
                break
        if not frames:
            raise FileNotFoundError(f"No parquet files found in {path}")
        return pd.concat(frames, ignore_index=True)
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
        return df.head(limit) if limit else df
    if path.suffixes[-2:] == [".jsonl", ".gz"] or path.suffix == ".jsonl":
        opener = gzip.open if path.suffix == ".gz" else open
        rows = []
        with opener(path, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                rows.append(json.loads(line))
        return pd.DataFrame(rows)
    if path.suffix == ".csv":
        return pd.read_csv(path, nrows=limit)
    raise ValueError(f"Unsupported input: {path}")


def normalize_items(raw: pd.DataFrame) -> pd.DataFrame:
    """MerRecの列をアプリ用の共通列へ寄せます。"""
    id_col = first_existing(raw, ["item_id", "product_id", "id"])
    title_col = first_existing(raw, ["title", "item_title", "name", "item_name"])
    price_col = first_existing(raw, ["price", "item_price", "price_yen"])
    brand_col = first_existing(raw, ["brand", "brand_name", "brand_id"])
    session_col = first_existing(raw, ["session_id", "sequence_id"])
    user_col = first_existing(raw, ["user_id", "buyer_id"])
    event_col = first_existing(raw, ["event_type", "event_name", "action_type", "event"])
    time_col = first_existing(raw, ["stime", "timestamp", "event_time", "created_at"])
    # カテゴリ階層は名称またはIDのどちらでも特徴として使えます。
    cat_cols = [c for c in [
        first_existing(raw, ["c0_name", "category", "category_name", "category0", "c0"]),
        first_existing(raw, ["c1_name", "subcategory", "category1", "c1"]),
        first_existing(raw, ["c2_name", "category2", "c2"]),
    ] if c]
    if id_col is None:
        raise ValueError("item_id/product_id/id のいずれかが必要です")
    out = pd.DataFrame()
    out["item_id"] = raw[id_col].astype(str)
    out["title"] = raw[title_col].fillna("").astype(str) if title_col else ""
    out["price"] = pd.to_numeric(raw[price_col], errors="coerce").fillna(0.0) if price_col else 0.0
    out["brand"] = raw[brand_col].fillna("").astype(str) if brand_col else ""
    out["session_id"] = raw[session_col].fillna("").astype(str) if session_col else ""
    out["user_id"] = raw[user_col].fillna("").astype(str) if user_col else ""
    out["event_type"] = raw[event_col].fillna("item_view").astype(str) if event_col else "item_view"
    out["timestamp"] = pd.to_datetime(raw[time_col], errors="coerce") if time_col else pd.NaT
    for i, c in enumerate(cat_cols):
        out[f"category_{i}"] = raw[c].fillna("").astype(str)
    if "category_0" not in out.columns:
        out["category_0"] = ""
    out["category_path"] = out[[c for c in out.columns if c.startswith("category_")]].agg(" > ".join, axis=1).str.strip(" >")
    return out


def build_item_table(events: pd.DataFrame) -> pd.DataFrame:
    """イベント行からitem単位の特徴表を作ります。"""
    # 同じitemが複数イベントに出るので、最初に見つかったtitle/category/brandを代表値にします。
    item = events.sort_values("timestamp", na_position="last").groupby("item_id", as_index=False).agg({
        "title": "first",
        "category_path": "first",
        "category_0": "first",
        "price": "median",
        "brand": "first",
    })
    # 価格が極端な外れ値の影響を受けにくいようlog価格も持たせます。
    item["log_price"] = np.log1p(item["price"].clip(lower=0))
    item["feature_text"] = (
        item["title"].fillna("") + " " +
        item["category_path"].fillna("") + " " +
        item["brand"].fillna("")
    )
    return item


def build_content_model(item_table: pd.DataFrame, topk: int) -> dict[str, Any]:
    """TF-IDF + 価格特徴 + NearestNeighborsのコンテンツ推薦モデルを作ります。"""
    tfidf = TfidfVectorizer(min_df=2, max_features=120_000, ngram_range=(1, 2))
    text_x = tfidf.fit_transform(item_table["feature_text"].fillna(""))
    price_x = StandardScaler(with_mean=False).fit_transform(item_table[["log_price"]])
    x = sparse.hstack([text_x, price_x.multiply(0.35)], format="csr")
    n_components = min(128, max(2, min(x.shape) - 1))
    reducer = make_pipeline(TruncatedSVD(n_components=n_components, random_state=42), Normalizer(copy=False))
    dense_x = reducer.fit_transform(x)
    n_neighbors = min(topk + 1, len(item_table))
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    nn.fit(dense_x)
    return {"tfidf": tfidf, "reducer": reducer, "nn": nn, "vectors": dense_x}


def build_transitions(events: pd.DataFrame, topk: int) -> dict[str, list[dict[str, Any]]]:
    """セッション内で次に見られやすい商品遷移を集計します。"""
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    if "session_id" not in events or events["session_id"].eq("").all():
        return {}
    ordered = events.sort_values(["session_id", "timestamp"], na_position="last")
    for _, group in ordered.groupby("session_id"):
        ids = group["item_id"].astype(str).tolist()
        for a, b in zip(ids, ids[1:]):
            if a != b:
                transitions[a][b] += 1
    return {
        src: [{"item_id": dst, "score": int(score)} for dst, score in cnt.most_common(topk)]
        for src, cnt in transitions.items()
    }


def build_implicit_als(events: pd.DataFrame) -> Any | None:
    """implicitが入っていれば、イベント重み付きALSモデルを学習します。"""
    if implicit is None or events["user_id"].eq("").all():
        return None
    user_codes, user_index = pd.factorize(events["user_id"].astype(str))
    item_codes, item_index = pd.factorize(events["item_id"].astype(str))
    weights = events["event_type"].map(EVENT_WEIGHTS).fillna(1.0).astype(float).to_numpy()
    mat = sparse.coo_matrix((weights, (item_codes, user_codes)), shape=(len(item_index), len(user_index))).tocsr()
    model = implicit.als.AlternatingLeastSquares(factors=64, regularization=0.05, iterations=12, random_state=42)
    model.fit(mat)
    return {"model": model, "item_index": item_index.tolist(), "user_index": user_index.tolist(), "item_user_matrix": mat}


def make_json_artifact(item_table: pd.DataFrame, content_model: dict[str, Any], transitions: dict[str, Any], topk: int) -> dict[str, Any]:
    """Goやフロントエンドからも読みやすい軽量JSONを作ります。"""
    vectors = content_model["vectors"]
    distances, indices = content_model["nn"].kneighbors(vectors)
    related: dict[str, list[dict[str, Any]]] = {}
    ids = item_table["item_id"].astype(str).tolist()
    for row_idx, item_id in enumerate(ids):
        rows = []
        for dist, idx in zip(distances[row_idx][1:topk+1], indices[row_idx][1:topk+1]):
            rows.append({"item_id": ids[int(idx)], "score": float(1.0 - dist)})
        related[item_id] = rows
    popular_by_category = {}
    for cat, group in item_table.groupby("category_0"):
        popular_by_category[str(cat)] = group.sort_values("price").head(topk)[["item_id", "title", "price"]].to_dict(orient="records")
    return {
        "version": 1,
        "description": "MerRec-derived lightweight recommendation artifact for C2C marketplace experiments.",
        "event_weights": EVENT_WEIGHTS,
        "popular_by_category": popular_by_category,
        "related_items": related,
        "session_transitions": transitions,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="MerRec parquet directory/file, CSV, or JSONL")
    p.add_argument("--out-json", type=Path, default=Path("ml/merrec_artifact.json"))
    p.add_argument("--out-pkl", type=Path, default=Path("ml/merrec_model.pkl"))
    p.add_argument("--limit", type=int, default=200_000, help="読み込み上限。全量は巨大なので最初は小さくしてください。")
    p.add_argument("--topk", type=int, default=30)
    p.add_argument("--with-als", action="store_true", help="implicitが入っていればALS協調フィルタリングも学習します。")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    raw = read_table(args.input, args.limit)
    events = normalize_items(raw)
    item_table = build_item_table(events)
    if len(item_table) < 2:
        raise ValueError("推薦モデルを作るには少なくとも2商品が必要です")
    content_model = build_content_model(item_table, args.topk)
    transitions = build_transitions(events, args.topk)
    als = build_implicit_als(events) if args.with_als else None
    artifact = make_json_artifact(item_table, content_model, transitions, args.topk)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_pkl.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.out_pkl.open("wb") as f:
        pickle.dump({"items": item_table, "content": content_model, "als": als, "artifact": artifact}, f)
    print(f"saved: {args.out_json}")
    print(f"saved: {args.out_pkl}")
    print(f"items: {len(item_table):,}, events: {len(events):,}, transitions: {len(transitions):,}")


if __name__ == "__main__":
    main()
