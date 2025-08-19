#!/usr/bin/env python3
"""
IT Help Agent (UK):
- Answers from FileSearch first.
- Falls back to WebSearch with a clear prefix if the repo lacks the answer.
- Can create ServiceNow incidents via a FunctionTool (with confirmation, redaction, retries).

Usage:
  python it_help_agent.py "Why won't my laptop power on?"
  # or: python it_help_agent.py   (starts REPL)

Env:
  OPENAI_API_KEY  = <OpenAI API key>
  SN_INSTANCE     = dev12345                  # ServiceNow instance (no protocol)
  SN_USER         = api.integration           # ServiceNow integration user
  SN_PASS         = ********                  # its password
"""

import os
import re
import sys
import json
import time
import hashlib
from typing import Optional, Literal, Any, Dict

# --- Optional .env loader (safe if python-dotenv isn't installed) ---
try:
    if os.path.exists(".env"):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass

import requests
from pydantic import BaseModel, Field

# ------------------------------------------------------------
# Import the Agents SDK you are using (the 'agents' package)
# ------------------------------------------------------------
try:
    from agents import Agent, FileSearchTool, Runner, WebSearchTool  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Could not import your 'agents' SDK. Ensure the 'agents' package "
        "is installed and provides Agent, FileSearchTool, Runner, WebSearchTool."
    ) from e

# FunctionTool import (two common locations)
try:
    from agents import FunctionTool  # type: ignore
except Exception:
    try:
        from agents.tools import FunctionTool  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Your 'agents' SDK does not expose FunctionTool. Please upgrade "
            "to a version that includes FunctionTool."
        ) from e


# -----------------------------
#            POLICY
# -----------------------------
STRICT_INSTRUCTIONS = """
You are an IT help assistant for a UK audience.

CRITICAL: ALWAYS check for ticket creation requests FIRST before doing anything else.

POLICY:
1) TICKET CREATION DETECTION: If user mentions ANY of these keywords, treat as ticket request:
   - "create a ticket", "create ticket", "make a ticket", "open a ticket"
   - "laptop not working", "computer not working", "system not working"
   - "need help", "need support", "steps didn't work"
   - "report issue", "report problem", "submit ticket"
   
   RESPONSE: Immediately ask for ticket details (skip FileSearch/WebSearch):
   - short_description (one line)
   - description (2–4 lines max) 
   - impact (1=High, 2=Medium, 3=Low)
   - urgency (1=High, 2=Medium, 3=Low)
   
   Then call 'create_servicenow_incident' tool when details provided.

2) For all other questions: Use FileSearchTool FIRST, then WebSearchTool if needed.

3) Never invent details. If information is missing, ask ONE concise follow-up question to fill it.

4) Redact any secrets (passwords, keys, tokens) in your replies AND in any ticket descriptions.

5) Write in UK English (spelling, tone). Be clear and polite.

When using tools, pass strictly valid JSON that matches the tool schema.
"""

# -----------------------------
#       ServiceNow tool
# -----------------------------

def _redact_secrets(text: str) -> str:
    """Basic redaction for obvious secrets."""
    if not text:
        return text
    patterns = [
        r"(?i)(password|pass|secret|api[_\- ]?key|token)\s*[:=]\s*[^\s,;]+",
        r"(?i)(bearer\s+[a-z0-9\.\-_]+)",
        r"(?i)(ssh-rsa\s+[a-z0-9\+\/=]+)",
    ]
    redacted = text
    for pat in patterns:
        redacted = re.sub(pat, lambda m: re.sub(r"\S", "•", m.group(0)), redacted)
    return redacted


def _idempotency_tag(caller: Optional[str], short_description: str) -> str:
    """Create a lightweight idempotency tag to help de-duplicate downstream."""
    h = hashlib.sha256()
    base = (caller or "unknown") + "|" + short_description.strip()
    h.update(base.encode("utf-8"))
    return h.hexdigest()[:12]


class CreateIncidentArgs(BaseModel):
    short_description: str = Field(..., max_length=200)
    description: str
    urgency: Literal["1", "2", "3"] = "3"   # 1=High, 2=Med, 3=Low
    impact:  Literal["1", "2", "3"] = "3"
    caller: Optional[str] = None            # email or sys_id preferred
    assignment_group: Optional[str] = None  # name or sys_id
    category: Optional[str] = None          # e.g., "Hardware", "Software"


def create_servicenow_incident(
    short_description: str,
    description: str,
    urgency: str = "3",
    impact: str = "3",
    caller: Optional[str] = None,
    assignment_group: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """POST to ServiceNow /api/now/table/incident with simple retries."""
    sn_instance = os.environ.get("SN_INSTANCE")
    sn_user = os.environ.get("SN_USER")
    sn_pass = os.environ.get("SN_PASS")

    if not all([sn_instance, sn_user, sn_pass]):
        return {"error": "ServiceNow credentials missing (SN_INSTANCE, SN_USER, SN_PASS)."}

    url = f"https://{sn_instance}.service-now.com/api/now/table/incident"

    safe_desc = _redact_secrets(description)
    safe_short = _redact_secrets(short_description)

    idem = _idempotency_tag(caller, safe_short)
    payload = {
        "short_description": safe_short,
        "description": f"{safe_desc}\n\n[idempotency:{idem}]",
        "urgency": urgency,
        "impact": impact,
    }
    if caller:
        payload["caller_id"] = caller
    if assignment_group:
        payload["assignment_group"] = assignment_group
    if category:
        payload["category"] = category

    attempts = 0
    last_error = None
    while attempts < 3:
        attempts += 1
        try:
            r = requests.post(
                url,
                json=payload,
                auth=(sn_user, sn_pass),
                headers={"Accept": "application/json"},
                timeout=15,
            )
            # retry on transient issues
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * attempts)
                continue
            r.raise_for_status()
            data = r.json().get("result", {})
            return {
                "number": data.get("number"),
                "sys_id": data.get("sys_id"),
                "url": f"https://{sn_instance}.service-now.com/nav_to.do?uri=incident.do?sys_id={data.get('sys_id')}",
                "idempotency": idem,
            }
        except Exception as ex:
            last_error = f"{type(ex).__name__}: {ex}"
            time.sleep(1.0 * attempts)

    return {"error": f"ServiceNow API failed after retries. Detail: {last_error}"}


# -----------------------------
#    Tool registration
# -----------------------------

def build_tools(vector_store_ids):
    """Return tools list as proper tool objects (no dicts)."""
    fs_tool = FileSearchTool(max_num_results=3, vector_store_ids=vector_store_ids)
    ws_tool = WebSearchTool()

    # Create FunctionTool using the correct constructor pattern
    async def on_invoke_tool(tool_context, args):
        """Wrapper to handle the function call with proper argument parsing."""
        import json
        if isinstance(args, str):
            args = json.loads(args)
        return create_servicenow_incident(**args)
    
    create_ticket_tool = FunctionTool(
        name="create_servicenow_incident",
        description="Create a ServiceNow incident (use only after user confirms).",
        params_json_schema=CreateIncidentArgs.model_json_schema(),
        on_invoke_tool=on_invoke_tool
    )

    return [ws_tool, fs_tool, create_ticket_tool]


# -----------------------------
#        Agent + Runner
# -----------------------------

def build_agent(vector_store_ids):
    tools = build_tools(vector_store_ids)
    agent = Agent(
        name="Assistant",
        tools=tools,
        # If your Agent constructor supports 'instructions', you can put the policy here:
        # instructions=STRICT_INSTRUCTIONS,
    )
    return agent


async def run_once(question: str, vector_store_ids):
    agent = build_agent(vector_store_ids)
    full_prompt = f"{STRICT_INSTRUCTIONS}\n\nQuestion: {question}"
    result = await Runner.run(agent, full_prompt)

    # Be flexible about result shape
    out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
    try:
        print(out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2))
    except Exception:
        print(str(out))


async def repl(vector_store_ids):
    print("IT Help Agent (UK) — type 'exit' to quit.")
    agent = build_agent(vector_store_ids)
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

        full_prompt = f"{STRICT_INSTRUCTIONS}\n\nQuestion: {question}"
        result = await Runner.run(agent, full_prompt)
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        try:
            print("\nAssistant:", out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2))
        except Exception:
            print("\nAssistant:", str(out))


# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="IT Help Agent with FileSearch, Web fallback, and ServiceNow ticketing.")
    parser.add_argument("question", nargs="*", help="The question to ask.")
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
        asyncio.run(run_once(user_question, args.vector_store_id))
    else:
        asyncio.run(repl(args.vector_store_id))
