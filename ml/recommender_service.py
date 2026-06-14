"""MerRec学習済みpickleを使う軽量HTTP推論サーバー。

依存を増やさないため、標準ライブラリのhttp.serverで実装しています。
本番ではFastAPI化してCloud Runに載せても構いません。
"""
from __future__ import annotations

import argparse
import json
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from sklearn.preprocessing import StandardScaler


def recommend(model: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    items = model["items"]
    content = model["content"]
    tfidf = content["tfidf"]
    reducer = content["reducer"]
    nn = content["nn"]
    top_k = int(payload.get("top_k", 5))
    title = str(payload.get("title", ""))
    category = str(payload.get("category", ""))
    brand = str(payload.get("brand", ""))
    price = float(payload.get("price", 0) or 0)
    session_titles = payload.get("session_titles") or []
    text = " ".join([title, category, brand, *map(str, session_titles)])
    text_x = tfidf.transform([text])
    # 学習時と同じくlog価格を弱い特徴として足します。
    log_price = np.log1p(max(price, 0))
    price_x = sparse.csr_matrix([[log_price * 0.35]])
    x = sparse.hstack([text_x, price_x], format="csr")
    vec = reducer.transform(x)
    distances, indices = nn.kneighbors(vec, n_neighbors=min(top_k, len(items)))
    recs = []
    for dist, idx in zip(distances[0], indices[0]):
        row = items.iloc[int(idx)]
        recs.append({
            "item_id": str(row["item_id"]),
            "title": str(row.get("title", "")),
            "category": str(row.get("category_path", "")),
            "price": float(row.get("price", 0) or 0),
            "score": float(1.0 - dist),
        })
    return {"reason": "MerRecのC2C行動特徴を想定したTF-IDF/価格/カテゴリ類似推薦です。", "items": recs}


class Handler(BaseHTTPRequestHandler):
    model: dict[str, Any]

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/recommend":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        result = recommend(self.model, payload)
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    with args.model.open("rb") as f:
        Handler.model = pickle.load(f)
    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"MerRec recommender service listening on :{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
