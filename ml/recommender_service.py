#!/usr/bin/env python3
"""
ファイル概要: ml/recommender_service.py

役割:
学習済みMerRecモデルをローカルHTTP APIとして公開し、バックエンドから推薦結果を受け取れるようにします。

機械学習面の背景:
MerRecのような行動ログでは、閲覧、いいね、購入開始、購入完了などのイベント強度が異なります。
そのため、単純な文字列類似だけでなく、イベント重み、TF-IDF、次元削減、近傍探索を組み合わせることで、
ハッカソンの短時間実装でも「フリマらしい推薦」を再現しやすくしています。

"""
# 実装詳細メモ:
# pickle化したMerRecModelをHTTPで呼び出せる軽量推論サーバーです。
# Goバックエンドから独立させることで、Pythonの機械学習依存関係をWeb API本体へ持ち込まない構成にしています。

from __future__ import annotations

import argparse
import json
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from merrec_model import MerRecModel, recommend_from_payload


# Handler は、標準ライブラリ http.server でMerRec推論APIを公開するリクエスト処理クラスです。
# Goバックエンドとは別プロセスにすることで、Pythonの機械学習依存関係をWeb API本体へ混ぜずに運用できます。
class Handler(BaseHTTPRequestHandler):
    # model は全リクエストで共有する学習済みMerRecModelです。
    # リクエストごとにpickleを読み直すと遅いため、起動時に1回だけ読み込み、クラス変数として保持します。
    model: MerRecModel | None = None

    # _send_json は、HTTPステータスとJSON本文を書き出す共通処理です。
    # Content-TypeとContent-Lengthを明示し、Goバックエンドやcurlから扱いやすいHTTPレスポンスにします。
    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    # do_GET は、ヘルスチェックとカテゴリ別インサイト取得のGETリクエストを処理します。
    # BaseHTTPRequestHandlerの命名規則に合わせる必要があるため、Pythonでは珍しい大文字メソッド名になっています。
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
    # do_POST は、/recommend に送られた商品条件を推薦結果へ変換します。
    # JSON本文を読み取り、recommend_from_payloadへ渡し、Goバックエンドがそのまま返せる辞書形式に整えます。
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
# parse_args は、推論サーバーのモデルファイル、ホスト、ポートをCLIから受け取ります。
# ローカル開発では127.0.0.1、コンテナや別ホスト公開では0.0.0.0のように実行環境に合わせて変更できます。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve merrec_model.MerRecModel over HTTP.")
    parser.add_argument("--model", type=Path, default=Path("ml/merrec_model.pkl"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    return parser.parse_args()
# main は、pickle化されたMerRecModelを読み込み、HTTPServerを起動します。
# pickle内のクラスが想定通り merrec_model.MerRecModel かを確認し、古い形式のモデルを誤って使う事故を防ぎます。
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


# 推論サーバーとして起動された場合だけHTTPServerを立ち上げます。
# テストや別プロセスからHandlerだけimportするときに、ポート待受けの副作用が起きないようにするためです。
if __name__ == "__main__":
    main()
