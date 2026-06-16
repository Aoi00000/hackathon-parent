#!/usr/bin/env python3
"""Build a MerRec-based recommendation artifact for the hackathon marketplace.

This script supports two input modes:
1. Hugging Face streaming mode
   Reads mercari-us/merrec with streaming=True and stops after --limit rows.
2. Local mode
   Reads parquet/csv/jsonl/jsonl.gz files already placed on disk.

The trained pickle stores merrec_model.MerRecModel, not __main__.MerRecModel.
Therefore the inference server can load it cleanly from another script.
"""
from __future__ import annotations

import argparse
import gzip
import json
import pickle
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer, StandardScaler

from merrec_model import MerRecModel, build_feature_text, safe_float

try:
    import implicit  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    implicit = None


EVENT_WEIGHTS = {
    "item_view": 1.0,
    "view": 1.0,
    "item_like": 3.0,
    "like": 3.0,
    "item_add_to_cart_tap": 5.0,
    "add_to_cart": 5.0,
    "offer_make": 6.0,
    "offer": 6.0,
    "buy_start": 8.0,
    "purchase_start": 8.0,
    "buy_comp": 12.0,
    "purchase": 12.0,
}


def first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def read_jsonl(path: Path, limit: int | None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def read_table(path: Path, limit: int | None) -> pd.DataFrame:
    """Read local parquet/csv/jsonl/jsonl.gz data."""
    if path.is_dir():
        files: list[Path] = []
        for pattern in ("*.parquet", "*.csv", "*.jsonl", "*.jsonl.gz"):
            files.extend(sorted(path.rglob(pattern)))
        if not files:
            raise FileNotFoundError(f"No supported files found in {path}")

        frames: list[pd.DataFrame] = []
        total = 0
        for file in files:
            remaining = None if limit is None else max(limit - total, 0)
            if remaining == 0:
                break
            frame = read_table(file, remaining)
            frames.append(frame)
            total += len(frame)
            if limit is not None and total >= limit:
                break
        return pd.concat(frames, ignore_index=True)

    suffixes = "".join(path.suffixes)
    if suffixes.endswith(".parquet"):
        df = pd.read_parquet(path)
        return df.head(limit) if limit else df
    if suffixes.endswith(".csv"):
        return pd.read_csv(path, nrows=limit)
    if suffixes.endswith(".jsonl") or suffixes.endswith(".jsonl.gz"):
        return read_jsonl(path, limit)
    raise ValueError(f"Unsupported input: {path}")


def read_hf_streaming(dataset_name: str, split: str, limit: int, config: str | None = None) -> pd.DataFrame:
    """Read MerRec from Hugging Face with streaming=True."""
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("datasets が必要です。pip install datasets を実行してください。") from exc

    kwargs: dict[str, Any] = {"split": split, "streaming": True}
    ds = load_dataset(dataset_name, config, **kwargs) if config else load_dataset(dataset_name, **kwargs)

    rows: list[dict[str, Any]] = []
    for i, row in enumerate(ds):
        if i >= limit:
            break
        rows.append(dict(row))
    if not rows:
        raise ValueError("Hugging Face streaming から行を取得できませんでした。split/configを確認してください。")
    return pd.DataFrame(rows)


def normalize_event(value: Any) -> str:
    return str(value or "item_view").strip().lower().replace("-", "_").replace(" ", "_")


def event_weight(value: Any) -> float:
    return EVENT_WEIGHTS.get(normalize_event(value), 1.0)


def normalize_items(raw: pd.DataFrame) -> pd.DataFrame:
    """Map MerRec/raw columns to common event columns."""
    id_col = first_existing(raw, ["item_id", "product_id", "id", "listing_id"])
    title_col = first_existing(raw, ["title", "item_title", "name", "item_name", "product_name"])
    price_col = first_existing(raw, ["price", "item_price", "price_yen", "listing_price"])
    brand_col = first_existing(raw, ["brand", "brand_name", "brand_id"])
    session_col = first_existing(raw, ["session_id", "sequence_id"])
    user_col = first_existing(raw, ["user_id", "buyer_id", "visitor_id"])
    event_col = first_existing(raw, ["event_type", "event_name", "action_type", "event", "event_id"])
    time_col = first_existing(raw, ["stime", "timestamp", "event_time", "created_at"])

    category_candidates = [
        first_existing(raw, ["c0_name", "category", "category_name", "category0", "c0"]),
        first_existing(raw, ["c1_name", "subcategory", "category1", "c1"]),
        first_existing(raw, ["c2_name", "category2", "c2"]),
    ]
    cat_cols = [c for c in category_candidates if c]

    if id_col is None:
        raise ValueError(f"item_id/product_id/id のいずれかが必要です。columns={list(raw.columns)}")

    out = pd.DataFrame()
    out["item_id"] = raw[id_col].astype(str)
    out["title"] = raw[title_col].fillna("").astype(str) if title_col else ""
    out["price"] = raw[price_col].map(safe_float).fillna(0.0) if price_col else 0.0
    out["brand"] = raw[brand_col].fillna("").astype(str) if brand_col else ""
    out["session_id"] = raw[session_col].fillna("").astype(str) if session_col else ""
    out["user_id"] = raw[user_col].fillna("").astype(str) if user_col else ""
    out["event_type"] = raw[event_col].fillna("item_view").astype(str) if event_col else "item_view"
    out["timestamp"] = pd.to_datetime(raw[time_col], errors="coerce") if time_col else pd.NaT

    for i, col in enumerate(cat_cols):
        out[f"category_{i}"] = raw[col].fillna("").astype(str)
    if "category_0" not in out.columns:
        out["category_0"] = ""

    category_cols = [c for c in out.columns if c.startswith("category_")]
    out["category_path"] = (
        out[category_cols]
        .apply(lambda row: " > ".join(str(v) for v in row if str(v).strip()), axis=1)
        .str.strip(" >")
    )
    return out


def build_item_table(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate event rows to item-level training rows."""
    item = (
        events.sort_values("timestamp", na_position="last")
        .groupby("item_id", as_index=False)
        .agg(
            {
                "title": "first",
                "category_path": "first",
                "category_0": "first",
                "price": "median",
                "brand": "first",
                "event_type": "count",
            }
        )
        .rename(columns={"event_type": "event_count"})
    )
    item["log_price"] = np.log1p(item["price"].clip(lower=0))
    item["feature_text"] = item.apply(
        lambda row: build_feature_text(
            title=row.get("title", ""),
            category=row.get("category_path", ""),
            brand=row.get("brand", ""),
            description="",
            price=row.get("price", 0),
        ),
        axis=1,
    )
    return item


def fit_content_model(item_table: pd.DataFrame, topk: int) -> tuple[TfidfVectorizer, StandardScaler, Any, NearestNeighbors, Any]:
    """Fit TF-IDF + price + SVD/Normalizer + NearestNeighbors."""
    min_df = 2 if len(item_table) >= 2000 else 1
    vectorizer = TfidfVectorizer(min_df=min_df, max_features=120_000, ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b")
    text_x = vectorizer.fit_transform(item_table["feature_text"].fillna(""))

    price_scaler = StandardScaler(with_mean=False)
    price_x = price_scaler.fit_transform(item_table[["log_price"]])
    x = sparse.hstack([text_x, sparse.csr_matrix(price_x).multiply(0.35)], format="csr")

    n_components = min(128, max(2, min(x.shape) - 1))
    reducer = make_pipeline(TruncatedSVD(n_components=n_components, random_state=42), Normalizer(copy=False))
    vectors = reducer.fit_transform(x)

    n_neighbors = min(max(topk + 1, 2), len(item_table))
    nn = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine")
    nn.fit(vectors)
    return vectorizer, price_scaler, reducer, nn, vectors


def build_transitions(events: pd.DataFrame, topk: int) -> dict[str, list[dict[str, Any]]]:
    """Count next-item transitions in each session."""
    transitions: dict[str, Counter[str]] = defaultdict(Counter)
    if "session_id" not in events.columns or events["session_id"].eq("").all():
        return {}

    ordered = events.sort_values(["session_id", "timestamp"], na_position="last")
    for _, group in ordered.groupby("session_id"):
        ids = group["item_id"].astype(str).tolist()
        weights = [event_weight(v) for v in group["event_type"].tolist()]
        for i, (src, dst) in enumerate(zip(ids, ids[1:])):
            if src and dst and src != dst:
                transitions[src][dst] += weights[i + 1]

    return {
        src: [{"item_id": dst, "score": float(score), "reason": "同じセッション内で次に閲覧されやすい商品"}
              for dst, score in counter.most_common(topk)]
        for src, counter in transitions.items()
    }


def default_insights(category: str) -> list[str]:
    c = category.lower()
    if any(k in c for k in ["book", "本", "教材", "参考書"]):
        return ["書き込み・折れ・汚れの有無", "版・年度・改訂版の違い", "付属冊子や解答の有無", "対象レベルが明確か"]
    if any(k in c for k in ["fashion", "服", "靴", "bag", "バッグ"]):
        return ["サイズ感・実寸", "汚れ・ほつれ・色あせ", "着用回数・使用感", "写真と実物の色味の差"]
    if any(k in c for k in ["electronics", "家電", "スマホ", "pc", "camera"]):
        return ["動作確認済みか", "バッテリー劣化", "付属品の有無", "型番・容量・保証の有無"]
    if any(k in c for k in ["food", "食品", "飲料"]):
        return ["賞味期限・消費期限", "未開封かどうか", "保存方法", "内容量・アレルギー表示"]
    return ["商品の状態が具体的か", "購入時期・使用回数", "付属品や欠品", "発送方法や梱包"]


def build_category_insights(item_table: pd.DataFrame) -> dict[str, list[str]]:
    insights: dict[str, list[str]] = {}
    for category, group in item_table.groupby("category_0", dropna=True):
        cat = str(category).strip()
        if not cat:
            continue
        points = default_insights(cat)
        titles = " ".join(group["title"].fillna("").astype(str).head(2000)).lower()
        if any(w in titles for w in ["size", "cm", "inch"]):
            points.append("サイズ・寸法が分かるか")
        if any(w in titles for w in ["new", "used", "condition"]):
            points.append("新品/中古や使用感が明確か")
        unique: list[str] = []
        for point in points:
            if point not in unique:
                unique.append(point)
        insights[cat] = unique[:6]
    return insights


def build_json_artifact(
    item_table: pd.DataFrame,
    vectors: Any,
    nn: NearestNeighbors,
    transitions: dict[str, Any],
    category_insights: dict[str, list[str]],
    topk: int,
) -> dict[str, Any]:
    distances, indices = nn.kneighbors(vectors)
    item_records = item_table.to_dict(orient="records")
    ids = item_table["item_id"].astype(str).tolist()
    related: dict[str, list[dict[str, Any]]] = {}

    for row_idx, item_id in enumerate(ids):
        rows = []
        for dist, idx in zip(distances[row_idx][1:topk + 1], indices[row_idx][1:topk + 1]):
            cand = item_records[int(idx)]
            rows.append(
                {
                    "item_id": str(cand["item_id"]),
                    "title": str(cand.get("title", "")),
                    "category": str(cand.get("category_path", "")),
                    "price": float(cand.get("price", 0) or 0),
                    "score": round(float(1.0 - dist), 6),
                }
            )
        related[str(item_id)] = rows

    popular_by_category: dict[str, list[dict[str, Any]]] = {}
    for cat, group in item_table.groupby("category_0"):
        popular_by_category[str(cat)] = (
            group.sort_values(["event_count", "price"], ascending=[False, True])
            .head(topk)[["item_id", "title", "category_path", "price"]]
            .to_dict(orient="records")
        )

    return {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "MerRec-derived lightweight recommendation artifact for C2C marketplace experiments.",
        "event_weights": EVENT_WEIGHTS,
        "popular_by_category": popular_by_category,
        "related_items": related,
        "session_transitions": transitions,
        "category_insights": category_insights,
    }


def build_implicit_als(events: pd.DataFrame) -> Any | None:
    if implicit is None or events["user_id"].eq("").all():
        return None
    user_codes, user_index = pd.factorize(events["user_id"].astype(str))
    item_codes, item_index = pd.factorize(events["item_id"].astype(str))
    weights = events["event_type"].map(event_weight).astype(float).to_numpy()
    mat = sparse.coo_matrix((weights, (item_codes, user_codes)), shape=(len(item_index), len(user_index))).tocsr()
    model = implicit.als.AlternatingLeastSquares(factors=64, regularization=0.05, iterations=12, random_state=42)
    model.fit(mat)
    return {"model": model, "item_index": item_index.tolist(), "user_index": user_index.tolist(), "item_user_matrix": mat}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MerRec recommendation artifacts.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="ローカルのMerRec parquet/CSV/JSONLまたはディレクトリ")
    source.add_argument("--hf", action="store_true", help="Hugging Faceのmercari-us/merrecをstreaming=Trueで読む")
    parser.add_argument("--hf-dataset", default="mercari-us/merrec", help="Hugging Face dataset名")
    parser.add_argument("--hf-config", default=None, help="必要な場合のみHugging Face config名を指定")
    parser.add_argument("--hf-split", default="train", help="Hugging Face split名")
    parser.add_argument("--out-json", type=Path, default=Path("ml/merrec_artifact.json"))
    parser.add_argument("--out-pkl", type=Path, default=Path("ml/merrec_model.pkl"))
    parser.add_argument("--limit", type=int, default=50_000, help="読み込み上限。最初は1000〜50000程度から確認してください。")
    parser.add_argument("--topk", type=int, default=30)
    parser.add_argument("--with-als", action="store_true", help="implicitが入っていればALS協調フィルタリングも学習する")
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit は1以上にしてください。")
    if args.topk <= 0:
        parser.error("--topk は1以上にしてください。")
    return args


def main() -> None:
    args = parse_args()
    if args.hf:
        print("Loading MerRec from Hugging Face with streaming=True...")
        print(f"- dataset: {args.hf_dataset}")
        print(f"- config: {args.hf_config or '(default)'}")
        print(f"- split: {args.hf_split}")
        print(f"- limit: {args.limit:,}")
        raw = read_hf_streaming(args.hf_dataset, args.hf_split, args.limit, args.hf_config)
    else:
        print("Loading MerRec from local files...")
        print(f"- input: {args.input}")
        raw = read_table(args.input, args.limit)

    print(f"Loaded rows: {len(raw):,}")
    print(f"Columns: {list(raw.columns)}")

    events = normalize_items(raw)
    item_table = build_item_table(events)
    if len(item_table) < 2:
        raise ValueError("推薦モデルを作るには少なくとも2商品が必要です。")

    vectorizer, price_scaler, reducer, nn, vectors = fit_content_model(item_table, args.topk)
    transitions = build_transitions(events, args.topk)
    category_insights = build_category_insights(item_table)
    als = build_implicit_als(events) if args.with_als else None

    artifact = build_json_artifact(item_table, vectors, nn, transitions, category_insights, args.topk)
    if als is not None:
        artifact["als_summary"] = {"enabled": True, "note": "ALS model is stored only in pickle."}
    else:
        artifact["als_summary"] = {"enabled": False, "note": "ALS was skipped."}

    items = item_table[["item_id", "title", "category_path", "category_0", "price", "brand", "event_count"]].to_dict(orient="records")
    model = MerRecModel(
        version=2,
        items=items,
        vectorizer=vectorizer,
        price_scaler=price_scaler,
        reducer=reducer,
        nn=nn,
        transitions=transitions,
        category_insights=category_insights,
        artifact=artifact,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_pkl.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.out_pkl.open("wb") as f:
        pickle.dump(model, f)

    print("MerRec artifact created.")
    print(f"- events: {len(events):,}")
    print(f"- unique items: {len(items):,}")
    print(f"- json: {args.out_json}")
    print(f"- pickle: {args.out_pkl}")
    print("- pickle class: merrec_model.MerRecModel")


if __name__ == "__main__":
    main()
