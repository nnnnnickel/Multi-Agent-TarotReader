import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tarot_reader_agent import DEFAULT_SESSION_ID, TarotReaderAgentP1

import sys
sys.dont_write_bytecode = True

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_REQUEST_BYTES = 64 * 1024


class TarotWebHandler(BaseHTTPRequestHandler):
    """为中文塔罗网页提供静态资源与本地 JSON 接口。"""

    server_version = "TarotReaderWeb/1.0"

    def do_GET(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html")
            return
        requested = unquote(request_path).lstrip("/")
        self._send_file(STATIC_DIR / requested)

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            request_path = urlsplit(self.path).path
            if request_path == "/api/reading":
                self._send_json(self._run_reading(payload))
                return
            if request_path == "/api/exit":
                session_id = self._session_id(payload)
                TarotReaderAgentP1().reset_memory(session_id)
                self._send_json(
                    {
                        "status": "success",
                        "message": "会话已结束，记忆已清空。",
                        "session_id": session_id,
                    }
                )
                return
            self._send_json({"error": "接口不存在。"}, status=HTTPStatus.NOT_FOUND)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "请求内容不是有效的 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json(
                {"error": f"服务器处理失败：{exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def log_message(self, format: str, *args: object) -> None:
        print(f"[tarot-web] {self.address_string()} - {format % args}")

    def _run_reading(self, payload: dict[str, object]) -> dict[str, object]:
        question = str(payload.get("question") or "").strip()
        cards_value = payload.get("cards") or ""
        cards = parse_cards(cards_value)
        session_id = self._session_id(payload)
        is_followup = bool(payload.get("followup"))

        if not question:
            raise ValueError("请输入想要咨询的问题。")
        if not is_followup and not cards:
            raise ValueError("第一次解读请至少抽取或输入一张牌。")

        agent = TarotReaderAgentP1(use_skills=bool(payload.get("use_skills", True)))
        result = agent.run_pipeline(
            user_query=question,
            cards=cards,
            session_id=session_id,
            reset_session=bool(payload.get("reset_session", False)),
        )
        return {
            "question": question,
            "answer": result.get("final_response", ""),
            "cards": result.get("drawn_cards", cards),
            "turn_mode": result.get("turn_mode", ""),
            "topic": result.get("topic", ""),
            "session_id": session_id,
            "runtime": result.get("runtime", {}),
        }

    def _session_id(self, payload: dict[str, object]) -> str:
        session_id = str(payload.get("session_id") or DEFAULT_SESSION_ID).strip()
        return session_id or DEFAULT_SESSION_ID

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError as exc:
            raise ValueError("Content-Length 无效。") from exc
        if length > MAX_REQUEST_BYTES:
            raise ValueError("请求内容过大。")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("请求内容必须是 JSON 对象。")
        return data

    def _send_file(self, path: Path) -> None:
        try:
            resolved = path.resolve()
            static_root = STATIC_DIR.resolve()
            if static_root not in resolved.parents or not resolved.is_file():
                raise FileNotFoundError
            content = resolved.read_bytes()
            content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {
                "application/javascript",
                "application/json",
            }:
                content_type = f"{content_type}; charset=utf-8"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self._send_json({"error": "页面不存在。"}, status=HTTPStatus.NOT_FOUND)

    def _send_json(
        self,
        payload: dict[str, object],
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)


def parse_cards(raw_cards: object) -> list[str]:
    """解析逗号、中文逗号、分号或换行分隔的牌名。"""
    if isinstance(raw_cards, list):
        return [str(item).strip() for item in raw_cards if str(item).strip()]
    normalized = (
        str(raw_cards)
        .replace("，", ",")
        .replace("；", ",")
        .replace(";", ",")
        .replace("\n", ",")
    )
    return [item.strip() for item in normalized.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动 Agentic Tarot 中文网页")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=7860, help="监听端口")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), TarotWebHandler)
    print(f"Agentic Tarot 中文网页已启动：http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n网页服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
