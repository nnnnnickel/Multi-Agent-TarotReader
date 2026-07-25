import argparse
import json

from tarot_reader_agent import DEFAULT_SESSION_ID, TarotReaderAgentP1


def parse_cards(raw_cards: list[str] | None) -> list[str]:
    if not raw_cards:
        return []
    cards = []
    for item in raw_cards:
        for card in item.split(","):
            cleaned = card.strip()
            if cleaned:
                cards.append(cleaned)
    return cards

def print_reading(result: dict[str, object], show_json: bool = False) -> None:
    if show_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("\n=== Reading ===")
    print(result["final_response"])
    print()

def prompt_required_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty.")

def prompt_required_cards(prompt: str) -> list[str]:
    while True:
        cards = parse_cards([input(prompt).strip()])
        if cards:
            return cards
        print("Please enter at least one card. Example: The Moon, Three of Swords")

def prompt_initial_inputs(query: str | None, cards: list[str]) -> tuple[str, list[str]]:
    if not query:
        query = prompt_required_text("Enter your question: ")
    if not cards:
        cards = prompt_required_cards("Enter drawn cards, comma-separated: ")
    return query, cards

def interactive_followups(agent: TarotReaderAgentP1, session_id: str, show_json: bool = False) -> None:
    #print("当前可进入追问模式")
    #print("按 Enter 键或输入 /quit 退出。输入 /history 可查看会话历史记录。")
    while True:
        followup_query = input("Follow-up: ").strip()
        #if not followup_query or followup_query in QUIT_COMMANDS:
        if not followup_query or followup_query == "/quit":
            agent.reset_memory(session_id)
            print("Session ended.")
            return
        if followup_query == "/history":
            print(json.dumps(agent.get_memory_context(session_id), ensure_ascii=False, indent=2))
            continue
        '''
        if followup_query == "/reset":
            agent.reset_memory(session_id)
            print("Session memory has been reset. The next reading will need a new question and cards.")
            return
        '''
        raw_extra_cards = input("Optional extra cards, comma-separated. Press Enter to reuse the previous spread: ").strip()
        #result = run_followup(agent, session_id, followup_query, parse_cards([raw_extra_cards]))
        result = agent.run_pipeline(user_query=followup_query, cards=parse_cards([raw_extra_cards]), session_id=session_id)
        print_reading(result, show_json=show_json)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capstone tarot reader agent with GraphRAG, memory, daily astrology, and safety checks.")
    parser.add_argument("--query", "-q", help='First user question, e.g. "How is my love life today? I am Gemini."')
    parser.add_argument("--cards", "-c", nargs="+", help="First drawn cards. Supports repeated args or comma-separated text.")
    parser.add_argument("--followup", "-f", help="Run one follow-up question after the first reading.")
    parser.add_argument("--extra-cards", "-e", nargs="+", help="Extra cards for the follow-up.")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID, help="Conversation memory session id.")
    parser.add_argument("--json", action="store_true", help="Print full pipeline JSON instead of only final_response.")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM calls. The reader will return a call-failed message instead of a generated reading.")
    parser.add_argument("--use-skills", action="store_true", help="Enable optional Skill.md guidance.")
    parser.add_argument("--skill-path", help="Skill file path. Relative paths are resolved under Capstone Project/Skills.")
    parser.add_argument("--once", action="store_true", help="Run only the first reading unless --followup is provided.")
    parser.add_argument("--reset-session", action="store_true", help="Clear this session before running the first reading.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    cards = parse_cards(args.cards)
    query, cards = prompt_initial_inputs(args.query, cards)
    agent = TarotReaderAgentP1(use_llm=False if args.no_llm else None, use_skills=args.use_skills, skill_path=args.skill_path)
    first_result = agent.run_pipeline(user_query=query, cards=cards, session_id=args.session_id, reset_session=args.reset_session)
    print_reading(first_result, show_json=args.json)

    if args.followup:
        #followup_result = run_followup(agent, args.session_id, args.followup, parse_cards(args.extra_cards))
        followup_result = agent.run_pipeline(user_query=args.followup, cards=parse_cards([args.extra_cards]), session_id=args.session_id)
        print_reading(followup_result, show_json=args.json)
        return
    if not args.once:
        print("当前可进入追问模式")
        print("按 Enter 键或输入 /quit 退出。输入 /history 可查看会话历史记录。")
        interactive_followups(agent, args.session_id, show_json=args.json)



if __name__ == "__main__":
    main()
