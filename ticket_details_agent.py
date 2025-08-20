#!/usr/bin/env python3
"""
Ticket Details Agent - Uses LLM to intelligently parse and fill ticket details from natural language input.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from agents import Agent, Runner
from pydantic import BaseModel, Field

class TicketDetails(BaseModel):
    """Schema for ticket details."""
    short_description: str = Field(description="Brief one-line summary of the issue")
    description: str = Field(description="Detailed description of the problem (2-4 lines)")
    impact: str = Field(description="Impact level: 1=High, 2=Medium, 3=Low")
    urgency: str = Field(description="Urgency level: 1=High, 2=Medium, 3=Low")

TICKET_DETAILS_INSTRUCTIONS = """
You are a specialised Ticket Details Interpreter Agent for a UK audience.

Your job is to intelligently parse user input and extract or infer ticket details for IT support requests.

INPUT: User's natural language description of their IT problem
OUTPUT: Complete ticket details with intelligent assumptions for missing information

PARSING RULES:
1. **Short Description**: Extract the core issue in one line
   - "My laptop won't turn on" → "Laptop not powering on"
   - "Can't access email" → "Email access issues"
   - "Printer is broken" → "Printer malfunction"

2. **Description**: Use the full user input as description, or expand if too brief
   - If user says "laptop broken", expand to "User reports laptop is not functioning properly"

3. **Impact Assessment**: Intelligently determine business impact
   - Hardware failures (laptop, printer, monitor) → High Impact (1)
   - Software issues (email, specific apps) → Medium Impact (2) 
   - Minor issues (password reset, basic questions) → Low Impact (3)

4. **Urgency Assessment**: Determine how quickly this needs resolution
   - "Can't work", "urgent", "emergency" → High Urgency (1)
   - "Need help", "when possible" → Medium Urgency (2)
   - "When convenient", "no rush" → Low Urgency (2)

INTELLIGENT ASSUMPTIONS:
- If user mentions "broken laptop" but no impact/urgency → Assume High Impact (1), Medium Urgency (2)
- If user says "urgent" but no impact → Assume High Impact (1)
- If user provides minimal info → Make reasonable assumptions based on issue type
- Always err on the side of being helpful rather than asking for more details

RESPONSE FORMAT:
Return ONLY a valid JSON object with this exact structure:
{
    "short_description": "brief issue summary",
    "description": "detailed description", 
    "impact": "1",
    "urgency": "2"
}

Do not include any explanation text - just the JSON object.
"""

def build_ticket_details_agent() -> Agent:
    """Build the ticket details interpretation agent."""
    return Agent(
        name="ticket_details_interpreter",
        instructions=TICKET_DETAILS_INSTRUCTIONS,
        model="gpt-4o-mini"
    )

async def interpret_ticket_details(user_input: str, existing_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Use LLM to intelligently interpret user input and extract/complete ticket details.
    
    Args:
        user_input: User's natural language description
        existing_details: Any existing details to merge with
    
    Returns:
        Complete ticket details dictionary
    """
    agent = build_ticket_details_agent()
    
    # Build context-aware prompt
    context = ""
    if existing_details:
        context = f"\n\nEXISTING DETAILS: {json.dumps(existing_details, indent=2)}\n\nMerge with new information from user input."
    
    prompt = f"User Input: {user_input}{context}\n\nExtract and complete ticket details:"
    
    try:
        result = await Runner.run(agent, prompt)
        response = getattr(result, "final_output", None) or getattr(result, "output_text", None) or str(result)
        
        # Clean the response to extract JSON
        response = response.strip()
        
        # Try to find JSON in the response
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            
            # Parse the JSON
            parsed_details = json.loads(json_str)
            
            # Validate and ensure all required fields
            required_fields = ["short_description", "description", "impact", "urgency"]
            for field in required_fields:
                if field not in parsed_details or not parsed_details[field]:
                    # Provide defaults for missing fields
                    if field == "short_description":
                        parsed_details[field] = user_input[:50] + "..." if len(user_input) > 50 else user_input
                    elif field == "description":
                        parsed_details[field] = user_input
                    elif field == "impact":
                        parsed_details[field] = "2"  # Default to medium
                    elif field == "urgency":
                        parsed_details[field] = "2"  # Default to medium
            
            return parsed_details
        else:
            # Fallback if no JSON found
            return {
                "short_description": user_input[:50] + "..." if len(user_input) > 50 else user_input,
                "description": user_input,
                "impact": "2",
                "urgency": "2"
            }
            
    except Exception as e:
        print(f"Error interpreting ticket details: {e}")
        # Fallback parsing
        return {
            "short_description": user_input[:50] + "..." if len(user_input) > 50 else user_input,
            "description": user_input,
            "impact": "2",
            "urgency": "2"
        }

async def test_ticket_details_agent():
    """Test the ticket details agent with various inputs."""
    test_cases = [
        "My laptop won't turn on",
        "Can't access email, urgent",
        "Printer is broken, need it for meeting",
        "Password reset needed",
        "Laptop screen is cracked"
    ]
    
    print("🧪 Testing Ticket Details Agent...")
    for test_input in test_cases:
        print(f"\nInput: {test_input}")
        result = await interpret_ticket_details(test_input)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_ticket_details_agent())
