"""Shared MerRec model definitions and inference helpers.

This module is intentionally imported by both:
- merrec_recommender.py, which trains and pickles MerRecModel
- recommender_service.py, which unpickles and serves MerRecModel

Putting MerRecModel in this stable module avoids the common pickle error where a
class saved as __main__.MerRecModel cannot be found when another script loads it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse


@dataclass
class MerRecModel:
    """Pickle-safe container for the MerRec recommendation model.

    The class lives in merrec_model.py, not in __main__.  Therefore a pickle made
    by merrec_recommender.py can be loaded by recommender_service.py as long as
    both scripts can import this module.
    """

    version: int
    items: list[dict[str, Any]]
    vectorizer: Any
    price_scaler: Any
    reducer: Any
    nn: Any
    transitions: dict[str, list[dict[str, Any]]]
    category_insights: dict[str, list[str]]
    artifact: dict[str, Any]


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value such as price to float safely."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    text = str(value).replace(",", "").replace("¥", "").replace("$", "").strip()
    try:
        return float(text)
    except ValueError:
        return default


def price_bucket(price: float) -> str:
    """Coarse price bucket used as a text token during training/inference."""
    if price <= 0:
        return "price_unknown"
    if price < 10:
        return "price_under_10"
    if price < 30:
        return "price_10_30"
    if price < 100:
        return "price_30_100"
    if price < 300:
        return "price_100_300"
    if price < 1000:
        return "price_300_1000"
    return "price_over_1000"


def build_feature_text(
    title: Any = "",
    category: Any = "",
    brand: Any = "",
    description: Any = "",
    price: Any = 0,
    session_titles: list[Any] | None = None,
) -> str:
    """Build a text feature in the same style for training and inference."""
    price_value = safe_float(price, 0.0)
    parts = [
        str(title or ""),
        str(category or ""),
        str(brand or ""),
        str(description or "")[:500],
        price_bucket(price_value),
    ]
    if session_titles:
        parts.extend(str(v or "") for v in session_titles)
    return " ".join(part for part in parts if part).strip() or "unknown item"


def build_query_vector(model: MerRecModel, payload: dict[str, Any]) -> Any:
    """Convert a request payload to the same vector space as trained items."""
    price = safe_float(payload.get("price"), 0.0)
    feature_text = build_feature_text(
        title=payload.get("title", ""),
        category=payload.get("category", ""),
        brand=payload.get("brand", ""),
        description=payload.get("description", ""),
        price=price,
        session_titles=payload.get("session_titles") or [],
    )

    text_x = model.vectorizer.transform([feature_text])
    log_price = np.array([[math.log1p(max(price, 0.0))]], dtype=float)
    price_x = model.price_scaler.transform(log_price)
    x = sparse.hstack([text_x, sparse.csr_matrix(price_x).multiply(0.35)], format="csr")
    return model.reducer.transform(x)


def recommend_from_payload(model: MerRecModel, payload: dict[str, Any]) -> dict[str, Any]:
    """Return related items for a title/category/brand/price query."""
    if model.nn is None or not model.items:
        return {
            "reason": "推薦モデルに十分な商品がありません。",
            "items": [],
        }

    top_k = int(payload.get("top_k") or 5)
    top_k = max(1, min(top_k, 30, len(model.items)))

    query_vector = build_query_vector(model, payload)
    distances, indices = model.nn.kneighbors(query_vector, n_neighbors=top_k)

    recs: list[dict[str, Any]] = []
    for distance, index in zip(distances[0], indices[0]):
        item = model.items[int(index)]
        recs.append(
            {
                "item_id": str(item.get("item_id", "")),
                "title": str(item.get("title", "")),
                "category": str(item.get("category_path", item.get("category", ""))),
                "brand": str(item.get("brand", "")),
                "price": safe_float(item.get("price"), 0.0),
                "score": round(float(1.0 - distance), 6),
                "reason": "商品名・カテゴリ・ブランド・価格帯が近い商品です。",
            }
        )

    return {
        "reason": "MerRecのC2C取引データを参考に、商品名・カテゴリ・ブランド・価格帯の近さから推薦しています。",
        "items": recs,
    }
