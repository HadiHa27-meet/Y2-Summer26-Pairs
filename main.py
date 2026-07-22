
import app1
import app2
"""
while True:
    bot_choice = input("Which bot would you like to use? (1 for presentation bot, 2 for research bot): ")
    if bot_choice == "1":
        app1.run_chat()
        break
    elif bot_choice == "2":
        app2.run_research()
        break
    else:
        print("Invalid choice. Please select 1 or 2.")
        continue
"""
from duckduckgo_search import DDGS
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import re

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
def run_united_bots():
    text_result, history = app2.run_research()
    app1.run_chat(text_result, history)

run_united_bots()