import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
import jieba

@dataclass
class SkillDefinition:
    #Markdown文件被加载为数据类
    name: str
    description: str
    triggers: list[str]
    instructions: str
    path: Path

    def to_runtime_dict(self):
        return {"name": self.name, "description": self.description, "path": str(self.path)}


class SkillRegistry:
    """
    Load optional markdown skills from the local Skills folder.
    """

    def __init__(self, skills_dir = None, skill_path = None):
        #print(skill_path)
        #print(skills_dir)
        #从SKILL目录传入/读取指定SKILL文件
        self.base_dir = Path(__file__).resolve().parent
        self.skills_dir = Path(skills_dir) if skills_dir else self.base_dir / "Skills"
        self.skill_path = skill_path
        self.skills = self.reload()

    def reload(self):
        #读取SKILL，返回list[SkillDefinition]
        if self.skill_path:
            #path = self.resolve_skill_path(self.skill_path)
            resolved_skill_path = Path(self.skill_path)
            if resolved_skill_path.is_absolute():
                path = resolved_skill_path
            else: 
                path = self.skills_dir / resolved_skill_path
            skill = self._load_skill_file(path)
            return [skill] if skill else []
        if not self.skills_dir.exists():
            return []
        return [skill 
                for path in sorted(self.skills_dir.glob("*.md")) 
                if (skill := self._load_skill_file(path))
                ]

    def _load_skill_file(self, path):
        #加载SKILL文件
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8", errors="ignore")
        trigger_text = normalize_text(self._section_value(content, "Triggers"))
        return SkillDefinition(
            name=self._section_value(content, "Name") or path.stem,
            description=self._section_value(content, "Description"),
            triggers=[
                item.strip()
                for item in re.split(r"[,、;\n]+", trigger_text)
                if item.strip()
                ],
            instructions=self._section_value(content, "Instructions") or content.strip(),
            path=path,
        )

    @staticmethod
    def _section_value(content, heading):
        pattern = rf"(?ims)^#+\s*{re.escape(heading)}\s*$\s*(.*?)(?=^#+\s|\Z)"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""


class SkillSelector:
    """
    Keyword scorer for optional, human-authored reading guidance.
    """

    def __init__(self, registry):
        #registry为SkillRegistry类，用于访问已加载的SKILL
        self.registry = registry

    def select(self, user_query, cards = None, context = None):
        """
        Input:
            user_query,
            cards, 
            context: dict #额外的上下文信息
        Output:
            选取的SkillDefinition的list
        """
        print("-------------Skill selecting-----------------")
        search_text = self._turn_text(user_query, cards or [], context or {})
        scored = [(self._score(skill, search_text), skill) for skill in self.registry.skills]
        return [skill for score, skill in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:2]

    def build_instructions(self, skills):
        #发送SKILL给LLM
        if not skills:
            return ""
        sections = []
        for skill in skills:
            sections.append(f"Skill: {skill.name}\nDescription: {skill.description}\nInstructions:\n{shorten(skill.instructions, 1600)}")
        return "\n\n".join(sections)

    def _score(self, skill, search_text):
        tokens = self._tokens(search_text)
        score = 0
        for trigger in skill.triggers:
            if trigger and trigger in search_text:
                score += 3
        for token in self._tokens(skill.description + " " + skill.instructions):
            if token in tokens:
                score += 1
        return score

    @staticmethod
    def _turn_text(user_query, cards, context):
        parts = [
            user_query,
            *cards,
            context.get("topic", ""),
            context.get("turn_mode", ""),
        ]
        return normalize_text(" ".join("" if item is None else str(item) for item in parts))

    @staticmethod
    def _tokens(text):
        normalized = normalize_text(text)
        tokens = set(re.findall(r"[a-z0-9_]+", normalized))
        chinese_chunks = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", normalized)
        for chunk in chinese_chunks:
            tokens.update(
                token.strip()
                for token in jieba.lcut_for_search(chunk)
                if len(token.strip()) >= 2
            )
        return tokens


def normalize_text(text):
    value = "" if text is None else str(text)
    return unicodedata.normalize("NFKC", value).casefold()

def shorten(text, limit):
    cleaned = " ".join(str(text).split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."
