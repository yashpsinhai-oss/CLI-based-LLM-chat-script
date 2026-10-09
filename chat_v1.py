#single raw API call
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client= Groq(api_key=os.getenv("GROQ_API_KEY"))
response=client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What is the capital of France?"}] 
)
print(response.choices[0].message.content)
# response = requests.post("https://api.openai.com/v1/completions", 
#                          headers={"Authorization": f"Bearer {API_KEY}"}, 
#                          json={
#                              "prompt": "What is the capital of France?",
#                              "max_tokens": 1024,
#                              "n": 1,
#                              "temperature": 0.5
#                          })