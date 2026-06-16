#!/usr/bin/env python3
"""Lightweight HTTP inference server for the MerRec recommendation model."""
from __future__ import annotations

import argparse
import json
import pickle
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from merrec_model import MerRecModel, recommend_from_payload


class Handler(BaseHTTPRequestHandler):
    model: MerRecModel | None = None

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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
        except Exception as exc:  # pragma: no cover - server safety net
            self._send_json(500, {"error": "recommendation failed", "detail": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve merrec_model.MerRecModel over HTTP.")
    parser.add_argument("--model", type=Path, default=Path("ml/merrec_model.pkl"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    return parser.parse_args()


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


if __name__ == "__main__":
    main()
