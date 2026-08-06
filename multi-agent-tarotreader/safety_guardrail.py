import json

from langchain_core.messages import HumanMessage, SystemMessage


class SafetyGuardrail:
    """LLM safety classifier for deterministic or high-risk tarot claims."""

    def __init__(self, llm = None):
        self.llm = llm

    def check(self, user_query, draft_reading, topic = "general"):
        if not self.llm:
            return {
                "available": False,
                "is_safe": True,
                "safety_reason": "Safety Guardrail不可用，安全性检查未进行",
                "source": "safety_unavailable",
            }
        try:
            prompt = (
                "你的任务是分析一段塔罗解读的安全性，“不安全”指确定性过强的医疗、生死、法律相关结论"
                "仅返回包含键 is_safe 和 safety_reason 的 JSON 数据"
            )
            payload = {"user_query": user_query, "draft_reading": draft_reading, "topic": topic}
            response = self.llm.invoke([SystemMessage(content=prompt), HumanMessage(content=json.dumps(payload, ensure_ascii=False))])   
            response_result = json.loads(response.content)
            check_result = {
                "available": True,
                "is_safe": bool(response_result.get("is_safe", True)),
                "safety_reason": str(response_result.get("safety_reason") or "").strip(),
                "source": "llm",
            }
            return check_result
            #return self._normalize_result(json.loads(response.content))
        except Exception as exc:
            return {
                "available": False,
                "is_safe": True,
                "safety_reason": f"安全性检查失败: {exc}",
                "source": "safety_check_failed",
            }
