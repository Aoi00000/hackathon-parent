"""
ファイル概要: ml/merrec_model.py

役割:
MerRec学習結果を推論時に読み込めるよう、特徴量生成関数とモデル入れ物を定義します。

機械学習面の背景:
MerRecのような行動ログでは、閲覧、いいね、購入開始、購入完了などのイベント強度が異なります。
そのため、単純な文字列類似だけでなく、イベント重み、TF-IDF、次元削減、近傍探索を組み合わせることで、
ハッカソンの短時間実装でも「フリマらしい推薦」を再現しやすくしています。

"""
# 実装詳細メモ:
# 学習スクリプトと推論サーバーの両方からimportされる、推薦モデルの共通定義です。
# TF-IDF、価格スケーリング、次元削減、近傍探索を同じ順序で使い、学習時と推論時の特徴量空間を一致させます。

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse


# MerRecModel は、学習済み推薦モデルを1つのpickleにまとめるためのデータクラスです。
# vectorizerやreducerなどの機械学習部品と、推薦候補の商品メタデータを同じ単位で保存することで、
# 推論サーバーはこのオブジェクトを読み込むだけで「入力テキストを同じ特徴量空間へ変換し、近い商品を探す」処理を再現できます。
@dataclass
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
# safe_float は、価格データに混ざりやすい欠損値・文字列・通貨記号をfloatへ正規化します。
# 機械学習の特徴量は数値である必要があり、NaNや「¥1,200」のような表記をそのまま渡すと変換や学習が失敗します。
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
# price_bucket は、連続値の価格を「安い/中間/高い」のような粗いカテゴリトークンへ変換します。
# TF-IDFは文字列特徴量を扱うため、価格帯を単語として混ぜることで「同じジャンルでも価格帯が近い商品」を拾いやすくします。
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
# build_feature_text は、商品タイトル・カテゴリ・ブランド・説明・価格帯を1本の学習用テキストにまとめます。
# 学習時と推論時でこの組み立て規則がずれると、同じ商品でも別の特徴量空間に入ってしまうため、共通関数として定義しています。
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
# build_query_vector は、APIから受け取った検索/推薦条件を学習済み商品のベクトルと同じ形式へ変換します。
# TF-IDFの語彙、価格スケーラー、SVD次元削減器は学習済みのものを再利用し、新しい入力だけを同じ空間へ写像します。
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
# recommend_from_payload は、変換済みクエリベクトルに対して近傍探索を行い、関連商品をAPI向けJSONに整えます。
# 近傍探索ではコサイン距離が小さい商品ほど内容・価格帯が近いとみなし、scoreには直感的に読める類似度へ変換した値を入れます。
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
