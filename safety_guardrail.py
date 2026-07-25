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
                "safety_reason": "Safety check was not run because the LLM client is unavailable.",
                "source": "safety_unavailable",
            }
        try:
            prompt = (
                "You are a safety classifier for a tarot reading."
                "Return ONLY JSON with keys, is_safe and safety_reason. Unsafe means deterministic medical, death, legal, or harmful claims."
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
                "safety_reason": f"Safety check failed: {exc}",
                "source": "safety_check_failed",
            }
    '''    
    @staticmethod
    def _normalize_result(result):
        return {
            "available": True,
            "is_safe": bool(result.get("is_safe", True)),
            "safety_reason": str(result.get("safety_reason") or "").strip(),
            "source": "llm",
        }
    '''