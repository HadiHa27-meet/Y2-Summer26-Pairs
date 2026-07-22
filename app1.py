import os
import re
import base64
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

BASE64_START = "===BASE64_START==="
BASE64_END = "===BASE64_END==="


def extract_base64_pptx(content_blocks):
    """
    Look through bash_code_execution_tool_result blocks for stdout text
    containing our base64 markers, and return the decoded bytes.
    """
    for block in content_blocks:
        if getattr(block, "type", None) != "bash_code_execution_tool_result":
            continue

        result_content = getattr(block, "content", None)
        if not result_content:
            continue

        stdout = getattr(result_content, "stdout", "") or ""

        if BASE64_START in stdout and BASE64_END in stdout:
            match = re.search(
                re.escape(BASE64_START) + r"(.*?)" + re.escape(BASE64_END),
                stdout,
                re.DOTALL
            )
            if match:
                b64_string = match.group(1).strip()
                try:
                    return base64.b64decode(b64_string)
                except Exception as e:
                    print(f"Failed to decode base64: {e}")
                    return None
    return None


def strip_incomplete_tool_use(content_blocks):
    if content_blocks and getattr(content_blocks[-1], "type", None) == "server_tool_use":
        return content_blocks[:-1]
    return content_blocks


def run_chat(topic, history):
    turn = 1
    system_message = f"""
        You are a presentation-design agent. You turn research content into a polished PowerPoint deck using the pptx skill. Make the presentation using and revolving around the following topic/information: {topic}

        Your job each time:
        1. Organize the research you're given into the exact number of slides requested — no more, no fewer.
        2. Convert prose into concise bullet points: 3-5 bullets per slide, each under ~15 words.
        3. Choose a color palette that fits the topic's tone (don't default to any classic generic color).
        4. Keep slides simplistic so you don't burn through too many credits.
        5. Keep language factual and neutral. Do not invent statistics or sources that weren't in the research content.

        IMPORTANT — file delivery:
        After you finish creating the .pptx file with the pptx skill, do NOT upload it as a file.
        Instead, run a bash command that prints the file's base64-encoded contents to stdout,
        wrapped exactly between these two markers on their own lines:
        ===BASE64_START===
        (base64 content here)
        ===BASE64_END===

        For example, if the file is named output.pptx, run something like:
        echo "===BASE64_START===" && base64 -w0 output.pptx && echo "" && echo "===BASE64_END==="

        Do not verify or re-run the script after creation. Do not explain what you did afterward.
        """
    history.append({
        "role": "user",
        "content": f"create a presentation on the following topic/bullet points: {topic}. Use your pptx skill to generate a PowerPoint presentation, then print its base64 contents as instructed."
    })

    while True:
        response = client.beta.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=16000,  # raised significantly to fit base64 file output
            betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
            container={"skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]},
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            system=system_message,
            messages=history
        )


        file_bytes = extract_base64_pptx(response.content)



        generated_file_name = f"presentation_{turn}.pptx"

        if file_bytes:
            print("\nPresentation generated successfully! Saving file...")
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            full_download_path = os.path.join(downloads_folder, generated_file_name)

            with open(full_download_path, 'wb') as f:
                f.write(file_bytes)
            print(f"Generated file saved locally as: {full_download_path}")
            return full_download_path

        assistant_text = ""
        for block in response.content:
            if block.type == 'text':
                print(f"\nClaude: {block.text}")
                assistant_text += block.text

        if assistant_text:
            history.append({"role": "assistant", "content": assistant_text})

        turn += 1
        user_input = input(f"Turn {turn} You: ")
        if user_input.lower() in ('exit', 'quit'):
            break
        history.append({"role": "user", "content": user_input})