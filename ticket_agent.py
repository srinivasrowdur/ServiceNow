#!/usr/bin/env python3
"""
Ticket Creation Agent
Specialized agent that only creates ServiceNow tickets using the agents SDK.
"""

import os
import sys
import json
import time
import hashlib
import asyncio
import requests
from typing import Optional, Literal, Any, Dict

# --- Optional .env loader (safe if python-dotenv isn't installed) ---
try:
    if os.path.exists(".env"):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass

from pydantic import BaseModel, Field

# Import the Agents SDK
try:
    from agents import Agent, FunctionTool, Runner  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Could not import your 'agents' SDK. Ensure the 'agents' package "
        "is installed and provides Agent, FunctionTool, Runner."
    ) from e

# -----------------------------
#            POLICY
# -----------------------------
TICKET_CREATION_INSTRUCTIONS = """
You are a specialized Ticket Creation Agent for a UK audience.

POLICY:
1) Your ONLY job is to create ServiceNow tickets
2) When user asks to create a ticket, ask for required details:
   - short_description (one line)
   - description (2–4 lines max)
   - impact (1=High, 2=Medium, 3=Low)
   - urgency (1=High, 2=Medium, 3=Low)
3) Once details are provided, IMMEDIATELY call the 'create_servicenow_incident' tool
4) No confirmation needed - create the ticket directly
5) Write in UK English (spelling, tone). Be clear and polite.
6) Redact any secrets in ticket descriptions

When using tools, pass strictly valid JSON that matches the tool schema.
"""

# -----------------------------
#       ServiceNow tool
# -----------------------------

def _redact_secrets(text: str) -> str:
    """Basic redaction for obvious secrets."""
    if not text:
        return text
    import re
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
#        Agent + Runner
# -----------------------------

def build_ticket_agent():
    """Build the ticket creation agent with only ticket creation capabilities."""
    # Create FunctionTool using the correct constructor pattern
    async def on_invoke_tool(tool_context, args):
        """Wrapper to handle the function call with proper argument parsing."""
        import json
        if isinstance(args, str):
            args = json.loads(args)
        return create_servicenow_incident(**args)
    
    create_ticket_tool = FunctionTool(
        name="create_servicenow_incident",
        description="Create a ServiceNow incident ticket.",
        params_json_schema=CreateIncidentArgs.model_json_schema(),
        on_invoke_tool=on_invoke_tool
    )

    agent = Agent(
        name="TicketAgent",
        tools=[create_ticket_tool],
    )
    return agent

async def run_ticket_creation(question: str) -> str:
    """Run ticket creation for the given request."""
    agent = build_ticket_agent()
    full_prompt = f"{TICKET_CREATION_INSTRUCTIONS}\n\nQuestion: {question}"
    result = await Runner.run(agent, full_prompt)

    # Be flexible about result shape
    out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
    return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)

async def run_ticket_creation_streaming(question: str, stream_callback=None):
    """Run ticket creation with streaming support."""
    agent = build_ticket_agent()
    full_prompt = f"{TICKET_CREATION_INSTRUCTIONS}\n\nQuestion: {question}"
    
    if stream_callback:
        # Send initial status
        stream_callback("🎫 Processing ticket request...")
    
    try:
        result = await Runner.run(agent, full_prompt)
        
        if stream_callback:
            stream_callback("📝 Analyzing ticket details...")
        
        # Be flexible about result shape
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        final_result = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
        
        if stream_callback:
            # Stream the final result in chunks
            chunk_size = 50
            for i in range(0, len(final_result), chunk_size):
                chunk = final_result[i:i + chunk_size]
                stream_callback(chunk)
                await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        return final_result
        
    except Exception as e:
        error_msg = f"❌ Error during ticket creation: {str(e)}"
        if stream_callback:
            stream_callback(error_msg)
        return error_msg

async def ticket_creation_repl():
    """Interactive REPL for ticket creation agent."""
    print("Ticket Creation Agent (UK) — type 'exit' to quit.")
    agent = build_ticket_agent()
    
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

        full_prompt = f"{TICKET_CREATION_INSTRUCTIONS}\n\nQuestion: {question}"
        result = await Runner.run(agent, full_prompt)
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        try:
            print("\nTicketAgent:", out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2))
        except Exception:
            print("\nTicketAgent:", str(out))

# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ticket Creation Agent - specialized for ServiceNow ticket creation.")
    parser.add_argument("question", nargs="*", help="The ticket creation request.")
    args = parser.parse_args()

    user_question = " ".join(args.question).strip()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Please export it or add to .env")
        sys.exit(1)

    if user_question:
        result = asyncio.run(run_ticket_creation(user_question))
        print(result)
    else:
        asyncio.run(ticket_creation_repl())
