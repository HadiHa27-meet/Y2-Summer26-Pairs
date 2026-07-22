from duckduckgo_search import DDGS
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import re

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
def run_research():
    system_message =f"""
    # ROLE
    You are ResearchAI, an expert research assistant. You gather, verify, and synthesize credible information, then output it as structured bullet-point notes designed to be consumed by a second, downstream agent responsible for building the actual presentation. You do not design slides yourself — you produce the raw structured content that agent will use. MAKE SURE THE CONTENT IS MINIMAL, ONLY INCLUDE NEEDED INFORMATION
    
    Just to make it clear, For each slide the user asks for you should only produce 4 clean bullet points, 5 words max. In total, 20 words max per slide. No more!!! You can have less if better

    # CORE RESPONSIBILITIES
    1. Research: Identify and consult multiple credible, diverse sources on the user's topic.
    2. Synthesize: Distill findings into clean, bullet-based notes — no dense prose.
    3. Structure for handoff: Format output so a presentation-building agent can map it directly to slides without needing to re-parse or reinterpret free text.

    # OUTPUT FORMAT (REQUIRED — FOR AGENT HANDOFF)
    Output ONLY in this structure. No narrative paragraphs. Every section must be bullet-based so the second agent can parse it programmatically.

    """
    turn  = 1
    topic = input("What would you like me to reserach about for you?: ")
    history = []

    history.append({"role": "user", "content": f"Research the following topic: {topic}. Provide structured bullet-point notes for a presentation. Include sources and citations."})


    while True:
        response = client.beta.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=3000,
            betas=["files-api-2025-04-14"],
            tools=[{"type": "web_search_20260318", "name": "web_search", "allowed_callers": ["direct"]}, {"type": "web_fetch_20260318", "name": "web_fetch", "allowed_callers": ["direct"]}],
            system=system_message,
            messages=history
            )
        
        text_output = "\n".join(block.text for block in response.content if block.type == "text")

        print (f"\nResearch completed. Here are the structured bullet-point notes:\n{text_output}\n")
        text_output = re.sub(r"```.*?```", "", text_output, flags=re.DOTALL).strip()

        break

    return text_output, history
    
