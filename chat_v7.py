#history trimming
import groq
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client=Groq(api_key=os.getenv("GROQ_API_KEY"))
MAX_HISTORY_LENGTH=4  # maximum number of messages to keep in history, even number so that they stay in pairs of user/assistant messages
system_message = [{"role": "system", "content": "Always answer as if you are a teacher explaining to a student" }] #seperate from the message list which contains user and assistant messages, can be a system message dict or a list of system messages, to be prepended to the last N messages in history
history=[]
while True:
    user_input=input("User: ").strip()

    if not user_input:
        continue

    if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break

    history.append({"role": "user", "content": user_input})
    reply=""
    try:
        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=system_message + history,  # send whole history, not to trim after the new user message is added , such trim will start history from assistant message, so the user message will be lost, instead trim after the assistant message is added
            stream=True
        )

        print("Assistant: ", end="", flush=True)
        for chunk in stream:
             piece=chunk.choices[0].delta.content
             if piece:
                 print(piece, end="", flush=True)
                 reply+=piece
        print()
    except groq.APIConnectionError:
        print()
        print("Network problem. Check your internet and try again.")
        history.pop()   # remove the unanswered user message
        continue         # back to input(), chat stays alive
    except groq.RateLimitError:
        print()
        print("Rate limit hit. Wait a bit and try again.")
        history.pop()
        continue
    except groq.AuthenticationError:
        print("Invalid API key. Check GROQ_API_KEY in your .env.")
        break            # retrying can't fix a bad key, so exit here
    except groq.APIStatusError as e:
        print()
        print(f"API error {e.status_code}. Try again.")
        history.pop()
        continue

    reply=reply.strip()
    if not reply:
        print("(No reply received. Try again.)")
        history.pop()   # remove the unanswered user message
        continue
    
    history.append({"role": "assistant", "content": reply})
    history=history[-MAX_HISTORY_LENGTH:]  # trim history to the last MAX_HISTORY_LENGTH messages