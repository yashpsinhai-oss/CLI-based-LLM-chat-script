#error handling
import os
import groq
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client=Groq(api_key=os.getenv("GROQ_API_KEY"))
messages = []
while True:
    user_input=input("User: ").strip()

    if not user_input:
        continue

    if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break

    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages
        )
    except groq.APIConnectionError:
        print("Network problem. Check your internet and try again.")
        messages.pop()   # remove the unanswered user message
        continue         # back to input(), chat stays alive
    except groq.RateLimitError:
        print("Rate limit hit. Wait a bit and try again.")
        messages.pop()
        continue
    except groq.AuthenticationError:
        print("Invalid API key. Check GROQ_API_KEY in your .env.")
        break            # retrying can't fix a bad key, so exit here
    except groq.APIStatusError as e:
        print(f"API error {e.status_code}. Try again.")
        messages.pop()
        continue

    reply=response.choices[0].message.content
    print(f"Assistant: {reply}")
    messages.append({"role": "assistant", "content": reply})