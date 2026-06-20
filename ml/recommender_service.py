#!/usr/bin/env python3
"""
ファイル概要: ml/recommender_service.py

役割:
学習済みMerRecモデルをローカルHTTP APIとして公開し、バックエンドから推薦結果を受け取れるようにします。

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

import argparse
import json
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from merrec_model import MerRecModel, recommend_from_payload


# 【詳細コメント】このクラスは、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
class Handler(BaseHTTPRequestHandler):
    model: MerRecModel | None = None

    # 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            loaded = Handler.model is not None
            self._send_json(200, {"status": "ok", "model_loaded": loaded})
            return
        if self.path == "/category-insights":
            if Handler.model is None:
                self._send_json(500, {"error": "model is not loaded"})
                return
            self._send_json(200, {"category_insights": Handler.model.category_insights})
            return
        self._send_json(404, {"error": "not found"})

    # 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/recommend":
            self._send_json(404, {"error": "not found"})
            return
        if Handler.model is None:
            self._send_json(500, {"error": "model is not loaded"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            result = recommend_from_payload(Handler.model, payload)
            self._send_json(200, result)
        except Exception as exc:  # pragma: no cover - 外部環境依存なのでテスト対象外 - server safety net
            self._send_json(500, {"error": "recommendation failed", "detail": str(exc)})


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve merrec_model.MerRecModel over HTTP.")
    parser.add_argument("--model", type=Path, default=Path("ml/merrec_model.pkl"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    return parser.parse_args()


# 【詳細コメント】この関数は、MerRecデータの前処理・特徴量生成・推薦推論の流れを小さな単位に分けるための要素です。入出力のDataFrame列や辞書キーを確認すると役割が分かりやすくなります。
def main() -> None:
    args = parse_args()
    with args.model.open("rb") as f:
        model = pickle.load(f)

    if not isinstance(model, MerRecModel):
        raise TypeError(
            "This service expects a merrec_model.MerRecModel pickle. "
            "Please recreate it with the cleaned ml/merrec_recommender.py."
        )

    Handler.model = model
    server = HTTPServer((args.host, args.port), Handler)
    print(f"MerRec recommender service listening on http://{args.host}:{args.port}")
    print("healthz:")
    print(f"  curl http://{args.host}:{args.port}/healthz")
    print("recommend example:")
    print(
        f"  curl -X POST http://{args.host}:{args.port}/recommend "
        "-H 'Content-Type: application/json' "
        "-d '{\"title\":\"calculus textbook beginner math\",\"category\":\"Books\",\"price\":1200,\"top_k\":5}'"
    )
    server.serve_forever()


# 【実行入口】このファイルを直接実行したときだけmain処理を走らせ、import時には副作用を起こさないようにします。
if __name__ == "__main__":
    main()
