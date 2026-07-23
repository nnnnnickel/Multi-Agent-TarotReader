from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CARD_ALIASES = {
    "the fool": "愚者",
    "fool": "愚者",
    "愚者": "愚者",
    "the magician": "魔术师",
    "magician": "魔术师",
    "魔术师": "魔术师",
    "the high priestess": "女祭司",
    "high priestess": "女祭司",
    "女祭司": "女祭司",
    "the empress": "女皇",
    "empress": "女皇",
    "女皇": "女皇",
    "the emperor": "皇帝",
    "emperor": "皇帝",
    "皇帝": "皇帝",
    "the hierophant": "教皇",
    "hierophant": "教皇",
    "教皇": "教皇",
    "教宗": "教皇",
    "the lovers": "恋人",
    "lovers": "恋人",
    "恋人": "恋人",
    "the chariot": "战车",
    "chariot": "战车",
    "战车": "战车",
    "strength": "力量",
    "力量": "力量",
    "the hermit": "隐者",
    "hermit": "隐者",
    "隐者": "隐者",
    "隐士": "隐者",
    "wheel of fortune": "命运之轮",
    "the wheel of fortune": "命运之轮",
    "命运之轮": "命运之轮",
    "justice": "正义",
    "正义": "正义",
    "the hanged man": "倒吊人",
    "hanged man": "倒吊人",
    "倒吊人": "倒吊人",
    "倒吊者": "倒吊人",
    "吊人": "倒吊人",
    "death": "死神",
    "死神": "死神",
    "temperance": "节制",
    "节制": "节制",
    "the devil": "恶魔",
    "devil": "恶魔",
    "恶魔": "恶魔",
    "the tower": "高塔",
    "tower": "高塔",
    "高塔": "高塔",
    "the star": "星星",
    "star": "星星",
    "星星": "星星",
    "星辰": "星星",
    "the moon": "月亮",
    "moon": "月亮",
    "月亮": "月亮",
    "the sun": "太阳",
    "sun": "太阳",
    "太阳": "太阳",
    "judgement": "审判",
    "judgment": "审判",
    "审判": "审判",
    "the world": "世界",
    "world": "世界",
    "世界": "世界",
}

SUIT_ALIASES = {
    "cup": "圣杯",
    "cups": "圣杯",
    "圣杯": "圣杯",
    "wand": "权杖",
    "wands": "权杖",
    "staff": "权杖",
    "staves": "权杖",
    "权杖": "权杖",
    "sword": "宝剑",
    "swords": "宝剑",
    "宝剑": "宝剑",
    "pentacle": "星币",
    "pentacles": "星币",
    "coin": "星币",
    "coins": "星币",
    "disk": "星币",
    "disks": "星币",
    "星币": "星币",
    "钱币": "星币",
    "金币": "星币",
}

RANK_ALIASES = {
    "ace": "王牌",
    "a": "王牌",
    "1": "王牌",
    "一": "王牌",
    "王牌": "王牌",
    "two": "二",
    "2": "二",
    "二": "二",
    "three": "三",
    "3": "三",
    "三": "三",
    "four": "四",
    "4": "四",
    "四": "四",
    "five": "五",
    "5": "五",
    "五": "五",
    "six": "六",
    "6": "六",
    "六": "六",
    "seven": "七",
    "7": "七",
    "七": "七",
    "eight": "八",
    "8": "八",
    "八": "八",
    "nine": "九",
    "9": "九",
    "九": "九",
    "ten": "十",
    "10": "十",
    "十": "十",
    "page": "侍从",
    "侍从": "侍从",
    "侍者": "侍从",
    "knight": "骑士",
    "骑士": "骑士",
    "queen": "皇后",
    "皇后": "皇后",
    "王后": "皇后",
    "king": "国王",
    "国王": "国王",
}

SUIT_ELEMENTS = {"圣杯": "水", "权杖": "火", "宝剑": "风", "星币": "土"}
MAJOR_ARCANA_ELEMENTS = {
    "愚者": "风",
    "魔术师": "风",
    "女祭司": "水",
    "女皇": "土",
    "皇帝": "火",
    "教皇": "土",
    "恋人": "风",
    "战车": "水",
    "力量": "火",
    "隐者": "土",
    "命运之轮": "火",
    "正义": "风",
    "倒吊人": "水",
    "死神": "水",
    "节制": "火",
    "恶魔": "土",
    "高塔": "火",
    "星星": "风",
    "月亮": "水",
    "太阳": "火",
    "审判": "火",
    "世界": "土",
}

ASTRO_TERM = {
    "MOON",
    "SUN",
    "MERCURY",
    "VENUS",
    "MARS",
    "JUPITER",
    "SATURN",
    "ARIES",
    "TAURUS",
    "GEMINI",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "SCORPIO",
    "SAGITTARIUS",
    "CAPRICORN",
    "AQUARIUS",
    "PISCES",
    "天王星",
    "海王星",
    "冥王星",
    "水星",
    "金星",
    "火星",
    "木星",
    "土星",
    "月球",
    "太阳（天体）",
    "白羊座",
    "金牛座",
    "双子座",
    "巨蟹座",
    "狮子座",
    "处女座",
    "天秤座",
    "天蝎座",
    "射手座",
    "摩羯座",
    "水瓶座",
    "双鱼座",
}

ELEMENTS = ("火", "水", "风", "土")


@dataclass
class GraphRAGResult:
    #GraphRAG检索结果
    card_meanings: list[dict[str, Any]]
    element_analysis: dict[str, Any]
    astro_associations: list[dict[str, Any]]
    graph_chains: list[str]
    retrieval_meta: dict[str, Any]

    def to_dict(self):
        #GraphRAGResult转换为字典
        return asdict(self)


class GraphRAGTool:
    """Read GraphRAG parquet output and return compact evidence for the reader."""

    def __init__(self, graphrag_project_path = None):
        #graphrag_project_path 为str或Path对象，未传入则使用default路径
        self.base_dir = Path(__file__).resolve().parent
        #使用default路径
        default_source = self.base_dir / "graphrag"
        self.graphrag_project_path = Path(graphrag_project_path) if graphrag_project_path else default_source
        #self.output_path = self.graphrag_project_path / "output"
        self.output_path = self.graphrag_project_path
        self.entities = None
        self.relationships = None
        self.community_reports = None
        self.load_error = ""
        self._load_tables() #加载parquet

    def retrieve(self, cards, topic = "general") -> dict[str, Any]:
        
        """
        检索入口
        If GraphRAG is unavailable, report the failure explicitly.
        Input: 
            cards: list[str]
            topic: str, 默认为"general"
        Output:
            检索结果 dict
        """
        if self.entities is None or self.relationships is None:
            return self._failed_result(cards, topic, self.load_error or "GraphRAG parquet tables are unavailable.").to_dict()
        return self._retrieve_from_tables(cards, topic).to_dict()

    def _load_tables(self):
        #加载parquet
        try:
            import pandas as pd

            entities_path = self.output_path / "entities.parquet"
            relationships_path = self.output_path / "relationships.parquet"
            reports_path = self.output_path / "community_reports.parquet"
            if not entities_path.exists() or not relationships_path.exists():
                self.load_error = f"Missing parquet files under {self.output_path}."
                return
            self.entities = pd.read_parquet(entities_path)
            self.relationships = pd.read_parquet(relationships_path)
            if reports_path.exists():
                self.community_reports = pd.read_parquet(reports_path)
        except Exception as exc:  # import/parquet errors are reported, not hidden.
            self.entities = None
            self.relationships = None
            self.community_reports = None
            self.load_error = str(exc)

    def _retrieve_from_tables(self, cards, topic):
        #检索
        """
        Input: 
            cards: list[str]
            topic: str
        Output:
            检索结果 GraphRAGResult        
        """
        entity_by_title = {str(row["title"]).upper(): row 
                           for row in self.entities.to_dict("records") 
                           if row.get("title")
                           }
        #title → 整行entitiy
        element_counter: Counter[str] = Counter() #元素计数器
        card_meanings = []
        astro_associations = []
        graph_chains = []
        matched = 0

        for idx, raw_card in enumerate(cards):
            #获取序号及输入的牌
            title = self._normalize_card_name(raw_card) #标准化牌名
            entity = entity_by_title.get(title)
            if not entity:
                #未找到entitiy时
                card_meanings.append(self._missing_card(raw_card, f"card_{idx + 1}"))
                continue
            matched += 1
            description = str(entity.get("description") or "")
            themes = self._extract_themes(description) 
            element = self._infer_element(title, description)
            if element != "未知":
                element_counter[element] += 1
            one_hop = self._relationships_for(title)
            graph_chains.extend(self._two_hop_chains(title, one_hop)[:3])
            astro_associations.extend(self._astro_links(raw_card, title, one_hop))
            card_meanings.append(
                {
                    "position": f"card_{idx + 1}",
                    "card": raw_card,
                    "normalized_card": title,
                    "meaning": description,
                    "themes": themes,
                    "element": element,
                    "one_hop_relations": one_hop[:5],
                    "community_reports": self._community_summaries_for(title),
                }
            )
            

        return GraphRAGResult(
            card_meanings=card_meanings,
            element_analysis=self._element_analysis(element_counter, len(cards)),
            astro_associations=astro_associations[:8],
            graph_chains=graph_chains[:10],
            retrieval_meta={
                "status": "ok",
                "source": "graphrag_parquet",
                "project_path": str(self.graphrag_project_path),
                "topic": topic,
                "requested_cards": cards,
                "matched_cards": matched,
            },
        )

    def _normalize_card_name(self, card):
        clean = self._strip_card_orientation(card)
        lowered = clean.lower()
        if lowered in CARD_ALIASES:
            return CARD_ALIASES[lowered]

        match = re.fullmatch(
            r"(ace|a|[1-9]|10|page|knight|queen|king|two|three|four|five|six|seven|eight|nine|ten)"
            r"\s+of\s+(.+)",
            lowered,
        )
        if match:
            rank, suit = match.groups()
            normalized_suit = SUIT_ALIASES.get(suit.strip())
            normalized_rank = RANK_ALIASES.get(rank)
            if normalized_suit and normalized_rank:
                return f"{normalized_suit}{normalized_rank}"

        compact = re.sub(r"\s+", "", lowered)
        match = re.fullmatch(
            r"(圣杯|权杖|宝剑|星币|钱币|金币)(?:牌)?(?:之)?"
            r"(王牌|ace|a|[1-9]|10|[一二三四五六七八九十]|page|侍从|侍者|knight|骑士|queen|皇后|王后|king|国王)",
            compact,
        )
        if match:
            suit, rank = match.groups()
            normalized_suit = SUIT_ALIASES.get(suit)
            normalized_rank = RANK_ALIASES.get(rank)
            if normalized_suit and normalized_rank:
                return f"{normalized_suit}{normalized_rank}"

        return clean.upper() if clean.isascii() else clean

    @staticmethod
    def _strip_card_orientation(card):
        clean = str(card).strip()
        orientation = r"(?:reversed|reverse|rev|upright|\u9006\u4f4d|\u6b63\u4f4d)"
        clean = re.sub(rf"\s*[\(\[\uff08]\s*{orientation}\s*[\)\]\uff09]\s*", " ", clean, flags=re.I)
        clean = re.sub(rf"^\s*{orientation}\s*[:\uff1a\-]?\s+", "", clean, flags=re.I)
        clean = re.sub(rf"(?:\s*[-:\uff1a]\s*|\s+|(?<=[\u4e00-\u9fff])){orientation}\s*$", "", clean, flags=re.I)
        return re.sub(r"\s+", " ", clean).strip()

    def _relationships_for(self, title):
        """
        查找
        source == 当前title
        or
        target == 当前title
        返回list[dict]
        """
        rows = self.relationships[
            (self.relationships["source"].astype(str).str.upper() == title)
            | (self.relationships["target"].astype(str).str.upper() == title)
        ].sort_values("weight", ascending=False)
        return rows.head(12).to_dict("records")

    def _two_hop_chains(self, title: str, one_hop: list[dict[str, Any]]):
        """
        获取links
        Input:
            title: str
            one_hop: list[dict] 用于获取中间节点
        Output:
            list[2-hop路径]
        """
        chains = []
        for rel in one_hop[:5]:
            middle = rel["target"] if str(rel["source"]).upper() == title else rel["source"]
            next_rows = self.relationships[
                (self.relationships["source"].astype(str).str.upper() == str(middle).upper())
                | (self.relationships["target"].astype(str).str.upper() == str(middle).upper())
            ].sort_values("weight", ascending=False)
            for next_rel in next_rows.head(2).to_dict("records"):
                end = next_rel["target"] if str(next_rel["source"]).upper() == str(middle).upper() else next_rel["source"]
                if str(end).upper() != title:
                    #环结构×
                    chains.append(f"{title} -> {middle} -> {end}")
        return chains

    def _community_summaries_for(self, title):
        #根据输入title获取community content的list[dict]
        if self.community_reports is None:
            return []
        pretty_title = title.title()
        matches = self.community_reports[
            self.community_reports["full_content"].astype(str).str.contains(pretty_title, case=False, na=False)
            | self.community_reports["title"].astype(str).str.contains(pretty_title, case=False, na=False)
        ]
        #保留community中的title和full_content
        return matches[["title", "summary"]].head(2).to_dict("records")

    @staticmethod
    def _extract_themes(description):
        #正则表达式提取关键词的list，或从candidates中直接匹配
        keyword_match = re.search(r"(?:关键词|keywords?)\s*[:：]\s*([^。\n]+)", description, flags=re.I)
        if keyword_match:
            keywords = [
                keyword.strip()
                for keyword in re.split(r"[,，、;；|]", keyword_match.group(1))
                if keyword.strip()
            ]
            if keywords:
                return keywords[:6]

        candidates = [
            "冲突",
            "行动",
            "稳定",
            "沟通",
            "选择",
            "过渡",
            "转变",
        ]
        found = [theme for theme in candidates if theme in description]
        return found[:4] or ["综合解读"]

    @staticmethod
    def _infer_element(title, description):
        #根据牌名字对应元素
        if title in MAJOR_ARCANA_ELEMENTS:
            return MAJOR_ARCANA_ELEMENTS[title]
        for suit, element in SUIT_ELEMENTS.items():
            if suit in title:
                return element
        """
        element_terms = {
            "水": ("水元素", "water"),
            "火": ("火元素", "fire"),
            "风": ("风元素", "空气元素", "air"),
            "土": ("土元素", "earth"),
        }
        lower = description.lower()
        for element, terms in element_terms.items():
            if any(term in lower for term in terms):
                return element
        """
        return "未知"

    def _astro_links(self, raw_card, title, one_hop):
        """
        从one-hop关系中获取占星对应
        Input:
            raw_card: str, #可能有(reversed)信息，此处保留原输入
            title: str,
            one_hop: list[dict]
        Output:
            list[dict]
        """
        links = []
        for rel in one_hop:
            source = str(rel.get("source", ""))
            target = str(rel.get("target", ""))
            description = str(rel.get("description", ""))
            if self._looks_astro(source, target, description):
                links.append(
                    {
                        "card": raw_card,
                        "target": target if source.upper() == title else source,
                        "description": description,
                        "weight": rel.get("weight", 0),
                    }
                )
        return links

    @staticmethod
    def _looks_astro(source, target, description):
        #判断是否存在占星实体，返回bool
        del description
        return source.upper() in ASTRO_TERM or target.upper() in ASTRO_TERM

    def _element_analysis(self, counter: Counter[str], total_cards: int) -> dict[str, Any]:
        """
        dominant & missing elements
        Input:
            counter: Counter[str], #已识别元素的计数器
            total_cards: int
        Output:
            分析结果dict
        """
        #dominant = counter.most_common(1)[0][0] if counter else None
        dominant= [
            key for key, count in counter.items()
            if count == max(counter.values())
        ] if counter else []        
        missing = [element for element in ELEMENTS if counter[element] == 0]
        if not dominant:
            interpretation = "没有匹配到牌面，暂时无法分析元素平衡。"
        else:
            missing_text = "、".join(missing) if missing else "无"
            interpretation = f"{total_cards} 张牌中以{'、'.join(dominant)}元素最突出；缺失元素：{missing_text}。"
        return {"counts": dict(counter), "dominant": dominant, "missing": missing, "interpretation": interpretation}

    def _missing_card(self, card, position):
        #card_meanings 失败处理，避免因为缺牌/缺含义等而发生异常
        #返回一个与正常牌结果结构相同的dict
        return {
            "position": position,
            "card": card,
            "normalized_card": self._normalize_card_name(card),
            "meaning": "",
            "themes": [],
            "element": "未知",
            "one_hop_relations": [],
            "community_reports": [],
            "status": "not_found",
            "message": "GraphRAG 中未找到与该牌名完全匹配的实体。",
        }

    def _failed_result(self, cards, topic, error):
        #GraphRAG 失败处理，用于parquet加载失败的情况，返回GraphRAGResult类型
        #在retrieval_meta记录错误类型
        return GraphRAGResult(
            card_meanings=[self._missing_card(card, f"card_{idx + 1}") for idx, card in enumerate(cards)],
            element_analysis=self._element_analysis(Counter(), len(cards)),
            astro_associations=[],
            graph_chains=[],
            retrieval_meta={
                "status": "failed",
                "source": "graphrag_parquet",
                "project_path": str(self.graphrag_project_path),
                "topic": topic,
                "requested_cards": cards,
                "matched_cards": 0,
                "error": error,
            },
        )
