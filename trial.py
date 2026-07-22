import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
def extract_file_id(content_blocks):
    for block in content_blocks:
        if getattr(block, "type", None) != "bash_code_execution_tool_result":
            continue
            
        result_content = getattr(block, "content", None)
        if not result_content:
            continue
 
        files = getattr(result_content, "content", None) or []
        for item in files:
            file_id = getattr(item, "file_id", None)
            print("hi")
            if file_id:
                return file_id
            return None
        
def strip_incomplete_tool_use(content_blocks):
    if content_blocks and getattr(content_blocks[-1], "type", None) == "server_tool_use":
        return content_blocks[:-1]
    return content_blocks
    


def run_chat(topic):
    history = []
    turn  = 1
    turn = 1
    history = []
    system_message =f"""
        You are a presentation-design agent. You turn research content into a polished PowerPoint deck using the pptx skill. Make the presntation using and revolving around the following topic/information: {topic}
        Your job each time:
        2. Organize the research your given into the exact number of slides requested — no more, no fewer.
        3. Convert prose into concise bullet points: 3-5 bullets per slide, each under ~15 words.
        4. Choose a color palette that fits the topic's tone (don't default to any classic generic color).
        keep slides simplistic so you dont burn through too much credits
        7. Keep language factual and neutral. Do not invent statistics or sources that weren't in the research content.

        Output only the finished presentation file. Upload that only. No need to burn through credits

        Do not verify or re-run the script after creation. Do not explain what you did afterward.
        """
    history.append({"role": "user", "content": f"create a presentation on the following topic/bullet points: {topic}. Use your pptx skill to generate a PowerPoint presentation. Please provide the presentation as a downloadable file or just download it."})

    while True:
        response = client.beta.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=3000,
            betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
            container={"skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]},
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            system=system_message,
            messages=history
            )
        print([getattr(b, "type", "?") for b in response.content])
        file_id = extract_file_id(response)
        generated_file_name = f"presentation_{turn}.pptx"


            
        if file_id:
                print("\nPresentation generated successfully! Downloading file...")
                file_content = client.beta.files.download(file_id)

                downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                full_download_path = os.path.join(downloads_folder, generated_file_name)
                print ("hi")

                with open(full_download_path, 'wb') as f:
                    f.write(file_content.content)
                print(f"Generated file saved locally as: {full_download_path}")
                return file_id, full_download_path
        assistant_text = ""
        for block in response.content:
                if block.type == 'text':
                    print(f"\nClaude: {block.text}")
                    assistant_text += block.text
                    
        if assistant_text:
                history.append({"role": "assistant", "content": assistant_text})
            
        turn += 1
        user_input = input(f"Turn {turn} You: ")
        if user_input.lower() == 'exit' or user_input.lower() == 'quit':
            break
    history.append({"role": "user", "content": user_input})
    return file_id
 

