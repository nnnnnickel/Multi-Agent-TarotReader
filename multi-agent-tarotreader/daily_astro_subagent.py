import os
import json
import re
import string
from dataclasses import asdict, dataclass
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from openai import OpenAI

DEFAULT_ASTRO_MODEL = "gpt-4o-mini"
SIGNS = {
    "Aries": "白羊座",
    "Taurus": "金牛座",
    "Gemini": "双子座",
    "Cancer": "巨蟹座",
    "Leo": "狮子座",
    "Virgo": "处女座",
    "Libra": "天秤座",
    "Scorpio": "天蝎座",
    "Sagittarius": "射手座",
    "Capricorn": "摩羯座",
    "Aquarius": "水瓶座",
    "Pisces": "双鱼座",
}
SIGN_BY_TOKEN = {
    token.lower(): sign
    for sign, chinese_sign in SIGNS.items()
    for token in (sign, chinese_sign, chinese_sign[:-1])
}
USER_CUES = {
    "i",
    "im",
    "i'm",
    "me",
    "my",
    "mine",
    "myself",
    "am",
    "as",
    "我是",
    "本人是",
    "我的",
    "我的星座是",
    "本人",
    "我",
}
VALID_TOPICS = {
    "romance": "感情",
    "career": "事业",
    "finance": "财运",
    "health": "健康",
    "general": "综合运势",
}


@dataclass
class AstroSignExtraction:
    #数据类，从用户问题中提取星座的结果
    user_sign: str | None

    def to_dict(self):
        return asdict(self)


class DailyAstroSearchTool:
    """
    OpenAI web-search backed daily astrology lookup.
    """

    def __init__(self, model = None, enabled = True):
        """
        Input:
            model = None, #搜索使用的模型
            enabled = True #是否启用在线搜索, bool类型
        """
        self.model = model or os.getenv("ASTRO_SEARCH_MODEL") or os.getenv("READER_MODEL_NAME") or DEFAULT_ASTRO_MODEL
        self.enabled = enabled
        self.client = self._build_client() if enabled else None

    def search(self, sign, topic, query):
        #使用OpenAI web_search_preview tool进行线上检索，返回搜索结果dict
        print("----------------------astro sub-agent started--------------------")
        if not self.enabled:
            raise RuntimeError("Daily astrology web lookup is disabled.")
        if not self.client:
            raise RuntimeError("OpenAI client is unavailable for daily astrology lookup.")

        prompt = (
            "查询用户星座的今日每日星座运势内容。"
            "返回包含“content”和“sources”键的JSON。若存在，“sources”键相必须包含“title”和“url”。"
            "语言应具有指导性，避免过于绝对的表述。"
        )
        response = self.client.responses.create(
            model=self.model,
            tools=[{"type": "web_search_preview"}],
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "date": datetime.now().astimezone().date().isoformat(),
                            "sign": SIGNS.get(sign, sign),
                            "topic": topic,
                            "user_query": query,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        text = self._response_text(response)
        parsed = self._parse_json_text(text)
        content = str(parsed.get("content") or text).strip()
        if not content:
            raise ValueError("Daily astrology lookup returned no usable content.")
        return {
            "content": content,
            "sources": self._normalize_sources(parsed.get("sources")) or self._annotation_sources(response),
            "retrieval_method": "openai_web_search",
            "search_model": self.model,
        }

    def _build_client(self):
        #if OpenAI is None:
        #    return None
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return None
        return OpenAI(api_key=key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))

    @staticmethod
    def _response_text(response):
        text = getattr(response, "output_text", None) #读取output_text，不存在则返回None
        if text:
            return str(text).strip()
        chunks = [] #创建分块列表，从每个"content"内容块读取"text"，有值就加入chunks列表
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                value = getattr(content, "text", None)
                if value:
                    chunks.append(str(value))
        return "\n".join(chunks).strip()

    @staticmethod
    def _parse_json_text(text):
        #处理json文本，输出为dict
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _normalize_sources(raw_sources):
        #标准化模型提供的信息来源，并以dict格式输出其信息
        if not isinstance(raw_sources, list):
            return []
        sources = []
        for source in raw_sources:
            if isinstance(source, dict):
                title = str(
                    source.get("title") 
                    or source.get("name") 
                    or "").strip()
                url = str(
                    source.get("url") 
                    or source.get("link") 
                    or "").strip()
                if title or url:
                    sources.append({"title": title, "url": url})
        return sources[:6]

    @staticmethod
    def _annotation_sources(response):
        #backup来源解析
        sources = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                for annotation in getattr(content, "annotations", []) or []:
                    title = str(getattr(annotation, "title", "") or "").strip()
                    url = str(getattr(annotation, "url", "") or "").strip()
                    if title or url:
                        sources.append({"title": title, "url": url})
        return sources[:6]


class DailyAstroSubagent:
    """
    Extract a user's zodiac sign
    Retrieve web context
    Summarize the retrieved context for the main reader
    """

    def __init__(self, llm = None, search_tool = None):
        self.llm = llm
        self.search_tool = search_tool or DailyAstroSearchTool()

    def extract_user_sign(self, query):
        #根据query识别用户星座，得到AstroSignExtraction类
        tokens = self._tokenize(query)
        mentions = [(SIGN_BY_TOKEN[token], idx) for idx, token in enumerate(tokens) if token in SIGN_BY_TOKEN]
        if not mentions:
            return AstroSignExtraction(user_sign=None)

        user_sign = next(
            (sign for sign, idx in mentions if idx > 0 and tokens[idx - 1] in USER_CUES),
            mentions[0][0],
        )
        return AstroSignExtraction(user_sign=user_sign)

    def read_for_query(self, sign, query, topic):
        topic = VALID_TOPICS.get(str(topic or "").strip().lower(), VALID_TOPICS["general"])
        try:
            retrieved = self.search_tool.search(sign, topic, query)
            summary = self._summarize_retrieved_horoscope(sign, topic, query, retrieved)
            return {
                "available": True,
                "sign": sign,
                "topic": topic,
                "summary": summary,
                "source": "web_daily_astro_tool",
                "retrieval_method": retrieved.get("retrieval_method"),
                "search_model": retrieved.get("search_model"),
                "sources": retrieved.get("sources", []),
                "retrieved_excerpt": shorten(retrieved.get("content", ""), 900),
            }
        except Exception as exc:
            return {
                "available": False,
                "sign": sign,
                "topic": topic,
                "summary": "",
                "source": "daily_astro_unavailable",
                "error": f"Daily astrology lookup failed: {exc}",
            }

    def _summarize_retrieved_horoscope(self, sign, topic, query, retrieved):
        #总结检索内容，返回给主agent
        if not self.llm:
            raise RuntimeError("LLM summarizer is unavailable for daily astrology context.")
        prompt = (
            "你是一名占星师助理"
            "基于输入内容，总结1-2句星座运势"
        )
        payload = {
            "sign": sign,
            "topic": topic,
            "query": query,
            "retrieved_daily_astro": shorten(retrieved.get("content", ""), 3000),
            #"sources": retrieved.get("sources", []),
        }
        #print("daily_astro_payload", payload)
        response = self.llm.invoke([SystemMessage(content=prompt), HumanMessage(content=json.dumps(payload, ensure_ascii=False))])
        return response.content.strip()

    def _tokenize(self, text):
        punctuation = string.punctuation + "，。！？；：（）【】“”‘’"
        table = str.maketrans({char: " " for char in punctuation})
        normalized = text.lower().translate(table)
        chinese_tokens = sorted(
            (token for token in set(SIGN_BY_TOKEN) | USER_CUES if not token.isascii()),
            key=len,
            reverse=True,
        )
        normalized = re.sub(f"({'|'.join(map(re.escape, chinese_tokens))})", r" \1 ", normalized)
        return normalized.split()


def shorten(text, limit):
    cleaned = " ".join(str(text).split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."
