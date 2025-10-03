# Note: Lab Completed 9/20/2025
# Instruction: https://github.com/MicrosoftLearning/mslearn-ai-agents/blob/main/Instructions/06-multi-remote-agents-with-a2a.md
# Use Azure AI Agent Service with the A2A protocol to create simple remote agents 
# that interact with one another. 
# These agents will assist technical writers with preparing their developer blog posts. 
# - title agent will generate a headline, 
# - outline agent will use the title to develop a concise outline for the article


""" Client code that connects to the routing agent """

import os
import asyncio
import requests
from dotenv import load_dotenv

load_dotenv()

server = os.environ["SERVER_URL"]
port = os.environ["ROUTING_AGENT_PORT"]

def send_prompt(prompt: str):
    url = f"http://{server}:{port}/message"
    payload = {"message": prompt}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "No response from agent.")
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Request failed: {e}"

async def main():
    print("Enter a prompt for the agent. Type 'quit' to exit.")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("quit", "", "exit"):
            print("Goodbye!")
            break
        response = send_prompt(user_input)
        print(f"Agent: {response}")

if __name__ == "__main__":
    asyncio.run(main())
