"""
ファイル概要: ml/merrec_model.py

役割:
MerRec学習結果を推論時に読み込めるよう、特徴量生成関数とモデル入れ物を定義します。

読み方の目安:
1. 前半の定数とヘルパー関数で、データ列名の揺れや欠損値への耐性を確認します。
2. 中盤では、テキスト特徴量、数値特徴量、カテゴリ特徴量を機械学習モデルへ渡す流れを確認します。
3. 後半では、学習済み成果物の保存またはHTTP推論APIとしての公開方法を確認します。

機械学習面の背景:
MerRecのような行動ログでは、閲覧、いいね、購入開始、購入完了などのイベント強度が異なります。
そのため、単純な文字列類似だけでなく、イベント重み、TF-IDF、次元削減、近傍探索を組み合わせることで、
ハッカソンの短時間実装でも「フリマらしい推薦」を再現しやすくしています。

"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse


@dataclass
# 【詳細コメント】このクラスは、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
class MerRecModel:
    """MerRec推薦モデルをpickleで安全に保存・読み込みするための入れ物です。

    学習スクリプトと推論サーバーの両方がこのクラスをimportすることで、
    __main__配下に保存されたクラスを別スクリプトから読めないというpickle特有の問題を避けます。
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


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def safe_float(value: Any, default: float = 0.0) -> float:
    """価格などの値を、欠損や文字列混入に耐えながらfloatへ変換します。"""
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


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def price_bucket(price: float) -> str:
    """価格帯を粗く分類し、学習・推論時にテキスト特徴量の1トークンとして使います。"""
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


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def build_feature_text(
    title: Any = "",
    category: Any = "",
    brand: Any = "",
    description: Any = "",
    price: Any = 0,
    session_titles: list[Any] | None = None,
) -> str:
    """学習時と推論時で同じ規則になるよう、商品情報からテキスト特徴量を組み立てます。"""
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


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def build_query_vector(model: MerRecModel, payload: dict[str, Any]) -> Any:
    """APIリクエストの内容を、学習済み商品と同じベクトル空間へ写像します。"""
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


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def recommend_from_payload(model: MerRecModel, payload: dict[str, Any]) -> dict[str, Any]:
    """商品名・カテゴリ・ブランド・価格などの条件から関連商品を返します。"""
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
