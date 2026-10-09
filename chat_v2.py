#turn our simple raw API into a loop , back and forth communication with the model
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client=Groq(api_key=os.getenv("GROQ_API_KEY"))
while True:
    user_input=input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the chat.")
        break

    response=client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": user_input}] 
)
    print(f"Assistant: {response.choices[0].message.content}")