#tool calling
from tool_helpers import get_exchange_rate, get_current_datetime
import json
import groq
import os
from dotenv import load_dotenv
from groq import Groq

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate between two currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "The currency code to convert from (e.g., 'USD').",
                    },
                    "target_currency": {
                        "type": "string",
                        "description": "The currency code to convert to (e.g., 'INR').",
                    },
                },
                "required": ["base_currency", "target_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time in the system's local timezone.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]
AVAILABLE_TOOLS={"get_exchange_rate":get_exchange_rate,"get_current_datetime":get_current_datetime}
MAX_TOOL_ROUNDS=5

load_dotenv()
client=Groq(api_key=os.getenv("GROQ_API_KEY"))
# a system prompt that tells the model when to use tools; replace with your own wording if you like
messages = [{"role": "system", "content": "You are a helpful assistant. Use the provided tools for live information such as exchange rates or the current date and time. Keep answers concise."}]
while True:
    user_input=input("User: ").strip()

    if not user_input:
        continue

    if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break

    turn_start=len(messages)
    messages.append({"role": "user", "content": user_input})

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=TOOLS
            )
            message = response.choices[0].message    # the model's reply object

            if not message.tool_calls:           # None or empty: no tool wanted, so this is the final answer
                break

            messages.append(message)             # keep the assistant's tool request BEFORE the tool results

            for tool_call in message.tool_calls:         # the model may ask for several tools at once
                name = tool_call.function.name           # which tool it wants
                if name not in AVAILABLE_TOOLS:          # allowed-list check: never run an unknown name
                    result = f"Error: tool '{name}' is not available."
                else:
                    try:
                        args = json.loads(tool_call.function.arguments)      # JSON string -> dict
                        result = json.dumps(AVAILABLE_TOOLS[name](**args))   # run the function, make the result a string
                    except Exception as e:       # any tool failure goes back to the model, not a crash
                        result = f"Error: {e}"

                print(f"[tool] {name}({tool_call.function.arguments}) -> {result}")   # debug line
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,    # must match the id in the model's request
                    "content": result,               # must be a string
                })        
        else:
            # the for loop used all its rounds without a final answer
            print("Too many tool rounds. Stopping.")
            del messages[turn_start:]            # drop everything this turn added
            continue

    except groq.APIConnectionError:
        print("Network problem. Check your internet and try again.")
        del messages[turn_start:]                # roll back the whole turn, not one message
        continue
    except groq.RateLimitError:
        print("Rate limit hit. Wait a bit and try again.")
        del messages[turn_start:]
        continue
    except groq.AuthenticationError:
        print("Invalid API key. Check GROQ_API_KEY in your .env.")
        break
    except groq.APIStatusError as e:
        print(f"API error {e.status_code}. Try again.")
        del messages[turn_start:]
        continue

    reply = (message.content or "").strip()      # the final text answer from the last round
    if not reply:
        print("(No reply received. Try again.)")
        del messages[turn_start:]
        continue

    print(f"Assistant: {reply}")
    messages.append({"role": "assistant", "content": reply})   # saved once, after the loop