#!/usr/bin/env python3
"""
File Search Agent
Specialized agent that only searches the knowledge repository using the agents SDK.
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

# Import the Agents SDK
try:
    from agents import Agent, FileSearchTool, Runner  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Could not import your 'agents' SDK. Ensure the 'agents' package "
        "is installed and provides Agent, FileSearchTool, Runner."
    ) from e

# -----------------------------
#            POLICY
# -----------------------------
FILE_SEARCH_INSTRUCTIONS = """
You are a specialized File Search Agent for a UK audience.

POLICY:
1) Use FileSearchTool to search the knowledge repository
2) Only answer from the returned snippets - never invent information
3) If you cite, paraphrase neatly and be concise
4) If the repository lacks the answer, clearly state "Not found in repository."
5) Write in UK English (spelling, tone). Be clear and polite.
6) Focus on providing accurate, repository-based information

When using tools, pass strictly valid JSON that matches the tool schema.
"""

# -----------------------------
#        Agent + Runner
# -----------------------------

def build_file_search_agent(vector_store_ids: List[str]):
    """Build the file search agent with only file search capabilities."""
    fs_tool = FileSearchTool(max_num_results=3, vector_store_ids=vector_store_ids)
    
    agent = Agent(
        name="FileSearchAgent",
        tools=[fs_tool],
    )
    return agent

async def run_file_search(question: str, vector_store_ids: List[str]) -> str:
    """Run a file search for the given question."""
    agent = build_file_search_agent(vector_store_ids)
    full_prompt = f"{FILE_SEARCH_INSTRUCTIONS}\n\nQuestion: {question}"
    result = await Runner.run(agent, full_prompt)

    # Be flexible about result shape
    out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
    return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)

async def file_search_repl(vector_store_ids: List[str]):
    """Interactive REPL for file search agent."""
    print("File Search Agent (UK) — type 'exit' to quit.")
    agent = build_file_search_agent(vector_store_ids)
    
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

        full_prompt = f"{FILE_SEARCH_INSTRUCTIONS}\n\nQuestion: {question}"
        result = await Runner.run(agent, full_prompt)
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        try:
            print("\nFileSearchAgent:", out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2))
        except Exception:
            print("\nFileSearchAgent:", str(out))

# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="File Search Agent - specialized for repository searches.")
    parser.add_argument("question", nargs="*", help="The question to search for in the repository.")
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
        result = asyncio.run(run_file_search(user_question, args.vector_store_id))
        print(result)
    else:
        asyncio.run(file_search_repl(args.vector_store_id))
