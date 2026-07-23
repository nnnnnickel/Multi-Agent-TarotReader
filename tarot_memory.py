from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from memory_retriever_BM25 import BM25MemoryRetriever


DEFAULT_SESSION_ID = "default"


@dataclass
class ConversationMemory:
    """
    Small JSON-backed memory for follow-up questions.
    定义“一段对话的记忆”的数据类
    一个对话session存为一个实例
    """

    storage_path: Path | None = None
    turns: list[dict[str, Any]] = field(default_factory=list)
    session_summary: str = ""
    last_cards: list[str] = field(default_factory=list)
    original_query: str = ""
    last_topic: str = "general"

    @classmethod
    def load(cls, storage_path):
        if not storage_path.exists():
            #文件不存在则创建storage_path的空记忆，用户后续保存
            return cls(storage_path=storage_path)
        try:
            payload = json.loads(storage_path.read_text(encoding="utf-8")) #读取storage_path文件并解读json文本
        except (OSError, json.JSONDecodeError):
            #读取失败返回空记忆
            return cls(storage_path=storage_path)
        memory = cls(
            storage_path=storage_path,
            turns=payload.get("turns", []),
            session_summary=payload.get("session_summary", ""),
            last_cards=payload.get("last_cards", []),
            original_query=payload.get("original_query", ""),
            last_topic=payload.get("last_topic", payload.get("last_domain", "general")),
        )
        if memory.turns and not memory.session_summary:
            memory.session_summary = memory._summarize_recent_turns()
        return memory

    def add_turn(self, user_query, cards, topic, final_response, astro_context = None):
        """
        添加对话
        Input:
            user_query, 
            cards: list[str], 当前一轮的输入牌组list
            topic, 
            final_response,
            astro_context: dict[str, Any] or None 占星解读内容，可选
        """
        if not self.original_query:
            self.original_query = user_query
        self.last_cards = list(cards)
        self.last_topic = topic
        self.turns.append(
            {
                "user_query": user_query,
                "cards": list(cards),
                "topic": topic,
                "final_response": final_response,
                "astro_context": astro_context,
            }
        )
        self.session_summary = self._summarize_recent_turns()
        self.save()

    def as_history(self):
        #将记忆保存格式转换成main Agent使用的格式
        return [
            {
                "user": turn.get("user_query", ""),
                "assistant": turn.get("final_response", ""),
                "cards": turn.get("cards", []),
                "topic": turn.get("topic", "general"),
                "astro_context": turn.get("astro_context"),
            }
            for turn in self.turns
        ]

    def as_context(self, query = None, exclude_last = False):
        #将记忆放入上下文
        return {
            "original_query": self.original_query,
            "session_summary": self.session_summary,
            "last_cards": self.last_cards,
            "last_topic": self.last_topic,
            "recent_history": self.as_history()[-4:],
            "relevant_history": self.retrieve_relevant(query, top_k=3, exclude_last=exclude_last),
            "turn_count": len(self.turns),
        }

    def retrieve_relevant(self, query, top_k = 3, exclude_last = False):
        #使用全部已保存历史进行BM25检索；同分时由优先选择较新的轮次。
        searchable_turns = self.turns[:-1] if exclude_last else self.turns
        if not query or not searchable_turns:
            return []
        documents = [self._turn_search_text(turn) for turn in searchable_turns]
        results = BM25MemoryRetriever(documents).search(query, top_k=top_k)
        #print("BM25 result:",results)
        relevant_history = []
        for result in results:
            turn = searchable_turns[result.document_index]
            relevant_history.append(
                {
                "turn": result.document_index + 1,
                "user": turn.get("user_query", ""),
                "assistant": turn.get("final_response", ""),
                "cards": turn.get("cards", []),
                "topic": turn.get("topic", "general"),
                "relevance_score": round(result.score, 4),
                }
            )
        return relevant_history

    def save(self):
        #保存json
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            save_payload = {
                                "turns": self.turns,
                                "session_summary": self.session_summary,
                                "last_cards": self.last_cards,
                                "original_query": self.original_query,
                                "last_topic": self.last_topic,
                            }
            self.storage_path.write_text(json.dumps(save_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _summarize_recent_turns(self):
        #生成最近对话摘要，返回str
        snippets = []
        for idx, turn in enumerate(self.turns[-3:], start=max(1, len(self.turns) - 2)):
            query = self._shorten(turn.get("user_query", ""), 120)
            answer = self._shorten(turn.get("final_response", ""), 180)
            snippets.append(f"Turn {idx}: user asked {query!r}; answer focused on {answer!r}.")
        return " ".join(snippets)

    @staticmethod
    def _shorten(text, limit):
        cleaned = " ".join(str(text).split())
        return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."

    @classmethod
    def _turn_search_text(cls, turn):
        #将一轮对话拼成一个用于检索的str
        return " ".join(
            [
                str(turn.get("user_query", "")),
                str(turn.get("final_response", "")),
                " ".join(str(card) for card in turn.get("cards", [])),
                str(turn.get("topic", "")),
                str(turn.get("astro_context", "")),
            ]
        )

class FileConversationMemoryStore:
    """
    Manage one json memory file per session.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or Path(__file__).resolve().parent / "history"
        self.root.mkdir(parents=True, exist_ok=True)
        self._active_paths: set[Path] = set()

    def load(self, session_id, reset_session = False):
        #根据session_id返回对应记忆
        path = self._session_path(session_id) #session ID → 记忆存储路径
        if reset_session: #重置
            self.delete(session_id)
            self._active_paths.add(path)
            return ConversationMemory(storage_path=path)
        self._active_paths.add(path)
        return ConversationMemory.load(path)

    def delete(self, session_id):
        #删除session_id的记忆
        path = self._session_path(session_id)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass
        self._active_paths.discard(path)
    
    def cleanup(self):
        #agent活动结束时清空活跃的存储
        for path in list(self._active_paths):
            try:
                path.unlink()
            except (FileNotFoundError, OSError):
                pass
            self._active_paths.discard(path)
    
    def _session_path(self, session_id):
        safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id or DEFAULT_SESSION_ID).strip("._")
        return self.root / f"{(safe_id[:80] or DEFAULT_SESSION_ID)}.json"
