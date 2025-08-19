#!/usr/bin/env python3
"""
Agent Orchestrator
Coordinates between specialized agents: WebSearch, FileSearch, and TicketCreation.
"""

import os
import sys
import json
import asyncio
from typing import Optional, List

# --- Optional .env loader (safe if python-dotenv isn't installed) ---
try:
    if os.path.exists(".env"):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass

# Import the individual agents
from web_search_agent import run_web_search
from file_search_agent import run_file_search
from ticket_agent import run_ticket_creation

# -----------------------------
#            POLICY
# -----------------------------
ORCHESTRATOR_INSTRUCTIONS = """
You are an Agent Orchestrator for a UK audience.

POLICY:
1) ANALYZE the user's request to determine which specialized agent to use:
   
   TICKET CREATION: Use TicketAgent if user mentions:
   - "create a ticket", "create ticket", "make a ticket", "open a ticket"
   - "laptop not working", "computer not working", "system not working"
   - "need help", "need support", "steps didn't work"
   - "report issue", "report problem", "submit ticket"
   
   FILE SEARCH: Use FileSearchAgent for:
   - Technical questions about systems, processes, documentation
   - "How to" questions about internal procedures
   - Questions about company policies or guidelines
   
   WEB SEARCH: Use WebSearchAgent for:
   - Current events, news, external information
   - General knowledge questions not in repository
   - Technology trends, software versions, etc.

2) ROUTE to the appropriate agent and return their response
3) Write in UK English (spelling, tone). Be clear and polite.

RESPONSE FORMAT:
- For ticket creation: "ROUTE_TO_TICKET_AGENT"
- For file search: "ROUTE_TO_FILE_SEARCH_AGENT"
- For web search: "ROUTE_TO_WEB_SEARCH_AGENT"
"""

# -----------------------------
#        Orchestrator Logic
# -----------------------------

def analyze_request(user_question: str) -> str:
    """Analyze the user request to determine which agent to route to."""
    question_lower = user_question.lower()
    
    # Ticket creation keywords
    ticket_keywords = [
        "create a ticket", "create ticket", "make a ticket", "open a ticket",
        "laptop not working", "computer not working", "system not working",
        "need help", "need support", "steps didn't work",
        "report issue", "report problem", "submit ticket"
    ]
    
    # Check for ticket creation requests first
    for keyword in ticket_keywords:
        if keyword in question_lower:
            return "TICKET"
    
    # Check for file search patterns (technical/internal questions)
    file_search_patterns = [
        "how to", "procedure", "policy", "internal", "company",
        "system", "process", "documentation", "guide"
    ]
    
    for pattern in file_search_patterns:
        if pattern in question_lower:
            return "FILE_SEARCH"
    
    # Default to web search for general questions
    return "WEB_SEARCH"

async def orchestrate_request(user_question: str, vector_store_ids: List[str] = None) -> str:
    """Orchestrate the request to the appropriate agent."""
    if vector_store_ids is None:
        vector_store_ids = ["vs_689ca12932cc8191a0223ebc3a1d6116"]
    
    agent_type = analyze_request(user_question)
    
    print(f"🤖 Orchestrator: Routing to {agent_type} agent...")
    
    try:
        if agent_type == "TICKET":
            result = await run_ticket_creation(user_question)
            return f"🎫 Ticket Agent Response:\n{result}"
        
        elif agent_type == "FILE_SEARCH":
            result = await run_file_search(user_question, vector_store_ids)
            return f"📁 File Search Agent Response:\n{result}"
        
        elif agent_type == "WEB_SEARCH":
            result = await run_web_search(user_question)
            return f"🌐 Web Search Agent Response:\n{result}"
        
        else:
            return "❌ Error: Unknown agent type"
    
    except Exception as e:
        return f"❌ Error routing to {agent_type} agent: {str(e)}"

async def orchestrator_repl(vector_store_ids: List[str] = None):
    """Interactive REPL for the orchestrator."""
    if vector_store_ids is None:
        vector_store_ids = ["vs_689ca12932cc8191a0223ebc3a1d6116"]
    
    print("🤖 Agent Orchestrator (UK) — type 'exit' to quit.")
    print("Available agents: WebSearch, FileSearch, TicketCreation")
    
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Bye!")
            return

        result = await orchestrate_request(question, vector_store_ids)
        print(f"\n{result}")

# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent Orchestrator - coordinates between specialized agents.")
    parser.add_argument("question", nargs="*", help="The question to route to appropriate agent.")
    parser.add_argument(
        "--vector-store-id",
        action="append",
        default=["vs_689ca12932cc8191a0223ebc3a1d6116"],
        help="Vector store ID(s) for FileSearch (can repeat).",
    )
    args = parser.parse_args()

    user_question = " ".join(args.question).strip()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Please export it or add to .env")
        sys.exit(1)

    if user_question:
        result = asyncio.run(orchestrate_request(user_question, args.vector_store_id))
        print(result)
    else:
        asyncio.run(orchestrator_repl(args.vector_store_id))
