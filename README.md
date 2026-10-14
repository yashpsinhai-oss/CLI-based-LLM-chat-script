# CLI-Based LLM Chat Script

A command-line chatbot built in Python using **raw LLM API calls** (no LangChain or other frameworks). The project was built in eight incremental stages to understand how LLM chat actually works under the hood: stateless API calls, loops, conversation memory, error handling, system prompts, streaming, history trimming, and tool calling.

It uses the **Groq API** (free tier) with the `openai/gpt-oss-120b` model.

---

## Features

- Interactive back-and-forth chat in the terminal
- Conversation memory (the model remembers earlier turns)
- System prompt that controls the model's behavior on every call
- Streaming replies, printed token by token as they are generated
- History trimming, so long chats don't grow without limit
- Tool calling: the model can request a live exchange-rate lookup and the current date/time (`chat_v8.py`)
- Graceful error handling for network, rate-limit, and authentication failures
- Ignores empty input and supports `exit` / `quit` (case-insensitive)
- API key kept out of source control via a `.env` file

---

## Project Structure

```
CLI-based-LLM-chat-script/
├── chat_v1.py        # Stage 1: single raw API call
├── chat_v2.py        # Stage 2: chat loop, no memory
├── chat_v3.py        # Stage 3: conversation memory
├── chat_v4.py        # Stage 4: error handling
├── chat_v5.py        # Stage 5: system prompt
├── chat_v6.py        # Stage 6: streaming
├── chat_v7.py        # Stage 7: history trimming (streaming chat)
├── chat_v8.py        # Stage 8: tool calling
├── tool_helpers.py   # tool functions used by chat_v8.py
├── requirements.txt  # Python dependencies
├── .env              # API key (NOT committed)
├── .gitignore
└── README.md
```

Each file is a runnable checkpoint, so you can diff one against the next and see exactly what changed and why.

---

## Setup

### 1. Prerequisites

- Python 3.10+ (developed on Python 3.14)
- A free Groq API key from [console.groq.com](https://console.groq.com) (no credit card required)

### 2. Clone and create a virtual environment

```powershell
git clone https://github.com/yashpsinhai-oss/CLI-based-LLM-chat-script
cd CLI-based-LLM-chat-script
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux, activate with `source .venv/bin/activate` instead.

> You must activate the virtual environment in every new terminal session. If you see `ModuleNotFoundError`, check that `(.venv)` appears at the start of your prompt.

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

This installs `groq` (the API client) and `python-dotenv` (loads the `.env` file), plus their dependencies.

### 4. Add your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your-key-here
```

No quotes and no spaces around the `=`. The `.gitignore` already excludes this file.

### 5. Run

```powershell
python chat_v7.py    # streaming chat with system prompt and history trimming
python chat_v8.py    # chat with tool calling (exchange rates, date and time)
```

Type `exit` or `quit` to leave the chat.

### Which Python runs the script

The packages (`groq`, `python-dotenv`) are installed **inside the virtual environment**, so the script must be run with the environment's own interpreter, `.venv\Scripts\python.exe`. Activating the environment makes the plain `python` command point to it.

You can also skip activation and call that interpreter directly:

```powershell
.\.venv\Scripts\python.exe chat_v7.py
```

### Troubleshooting

**`ModuleNotFoundError: No module named 'dotenv'` (or `groq`)**

The script ran with a different Python (usually your global install), which doesn't have the packages. Common causes:

- The terminal was not activated. Check that `(.venv)` appears at the start of the prompt.
- An editor "run" button (for example the VS Code Code Runner extension) uses its own fixed interpreter and ignores the virtual environment. Use VS Code's **Run Python File** button after selecting the `.venv` interpreter (`Ctrl+Shift+P`, then **Python: Select Interpreter**), or run the script from the activated terminal.

**"Running scripts is disabled" when activating**

Allow scripts for the current terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then run `.\.venv\Scripts\Activate.ps1` again.

---

## How It Was Built

### Stage 1: Single API call (`chat_v1.py`)

Sends one hardcoded prompt and prints the reply.

- `load_dotenv()` loads the key from `.env`
- `Groq(api_key=...)` creates the client once
- `client.chat.completions.create(model=..., messages=[...])` sends the request
- The reply text lives at `response.choices[0].message.content`

**Key idea:** an LLM API call is **stateless**. Each request is independent, and the model knows nothing beyond what you send in that request.

### Stage 2: Chat loop (`chat_v2.py`)

Wraps the call in a `while True` loop with `input()`.

- The client is created **once**, outside the loop
- The exit condition checks the **user's input**, not the model's output
- Still no memory: each turn sends only the latest message, so the model forgets your name between turns

### Stage 3: Conversation memory (`chat_v3.py`)

Adds a `messages` list that persists across turns.

1. Create the list **outside** the loop
2. Append the user message before each API call
3. Pass the **whole list** to `.create()`
4. Append the assistant's reply after each response

**Key idea:** the model has no memory. "Memory" means resending the full conversation transcript every turn, with `user` and `assistant` roles marking who said what. A side effect is that token usage grows with every turn.

### Stage 4: Error handling (`chat_v4.py`)

Wraps the API call in `try` / `except` using Groq's typed exceptions:

| Exception                  | Behavior                                                                 |
| -------------------------- | ------------------------------------------------------------------------ |
| `groq.APIConnectionError`  | Print a network message, remove the unanswered user message, continue    |
| `groq.RateLimitError`      | Print a rate-limit message, remove the unanswered user message, continue |
| `groq.AuthenticationError` | Print a bad-key message and exit (retrying cannot fix it)                |
| `groq.APIStatusError`      | Generic fallback: print the status code, continue                        |

Details that matter:

- **Specific exceptions come before general ones.** `RateLimitError` and `AuthenticationError` are subclasses of `APIStatusError`, so the general handler must be last.
- **`pop()` on failure.** The user message is appended before the call. If the call fails, it must be removed, otherwise the next turn sends two `user` messages in a row.
- **`continue` vs `break`.** `continue` skips the rest of the iteration and returns to `input()`. `break` leaves the loop entirely.
- **Empty input** (`""` or only spaces) is skipped with `.strip()` and `continue`, so nothing is sent to the API or added to history.

### Stage 5: System prompt (`chat_v5.py`)

Adds a message with the role `system` that sets the rules for the whole conversation: tone, persona, format, and limits.

- The system message is created **once**, before the loop
- It is sent **first on every call**, because the model has no memory and would otherwise forget it
- The user never sees it, but it shapes every reply

**How it was tested:** a system prompt with an obvious rule (such as a fixed reply length) was compared against the same question in `chat_v4.py`, which has no system prompt. The replies were clearly different, which shows the system message reaches the model and keeps applying across turns.

### Stage 6: Streaming (`chat_v6.py`)

Prints the reply as it is generated instead of waiting for the whole answer.

- `stream=True` makes `.create()` return an **iterator of chunks** instead of one finished response
- Each chunk's new text is in `chunk.choices[0].delta.content` (not `message.content`)
- Some chunks carry no text (`None`), so each piece is checked with `if piece:` before use
- `print(piece, end="", flush=True)` shows text immediately without line breaks
- The full reply is also built up in a string, so it can be saved to history
- The `try` block now wraps the whole streaming loop, because the connection can also drop mid-reply
- The assistant message is appended only **after** the stream completes, so a half-finished reply never reaches history
- An empty reply (for example from a reasoning model that produced no visible text) is detected, the unanswered user message is removed, and the user is asked to try again

### Stage 7: History trimming (`chat_v7.py`)

Caps how much history is resent, so long chats don't keep growing in cost and don't hit the model's context limit.

- The system message is kept **separate** from the conversation history. If it lived in the same list, a plain `[-N:]` slice would eventually drop it
- Each call sends `system_message + history`, so the system message is always first, exactly once
- After the assistant reply is appended, the history is trimmed to the last `MAX_HISTORY_LENGTH` messages
- `MAX_HISTORY_LENGTH` is an **even** number, so trimming keeps whole user/assistant pairs and the history always starts with a `user` message
- Trimming happens **after the reply**, not after appending the user message. Trimming at that point would leave an odd-length list that starts with an `assistant` message
- Because trimming only runs after a successful reply, a failed call never loses history, and `pop()` still removes the right message

---

### Stage 8: Tool calling (`chat_v8.py`, `tool_helpers.py`)

Lets the model request functions for information it cannot know on its own. Two tools are included:

- `get_exchange_rate(base_currency, target_currency)` fetches a rate from the Exchange Rate API (rates update once a day)
- `get_current_datetime()` reads the system clock, with timezone

How it works:

- The model never runs code. It replies with a **request** (`finish_reason == "tool_calls"`, `message.tool_calls`), the script runs the function, and the result goes back as a `tool` message whose `tool_call_id` matches the request
- `TOOLS` describes each function (name, description, JSON Schema parameters). The descriptions are what the model uses to decide when to call a tool
- `AVAILABLE_TOOLS` maps tool names to Python functions and acts as the **allowed list**. A name that is not in it is never executed; an error string is sent back instead
- Arguments arrive as a JSON string, so they are parsed with `json.loads` and passed with `func(**args)`. Schema property names must match the function's parameter names
- A failing tool does not crash the chat: the exception is caught and sent back as `"Error: ..."` so the model can explain the problem
- `MAX_TOOL_ROUNDS` caps how many model requests one turn may make, so a confused model cannot loop forever. A `for ... else` handles the case where the cap is reached
- A tool turn adds several messages (assistant request, tool results, final answer), so on failure the whole turn is rolled back with `del messages[turn_start:]` instead of a single `pop()`
- The tool functions use a request timeout, `raise_for_status()`, uppercase normalisation of currency codes, and return labelled dictionaries so the model can phrase accurate answers

This version does not include streaming or history trimming. Merging them is on the roadmap, because trimmed history must keep every tool message paired with its assistant request.

---

## Execution Flow (Streaming Chat, `chat_v7.py`)

1. `load_dotenv()` loads `.env`, then the Groq client, the system message, and an empty `history` list are created once.
2. The loop starts and `input("User: ").strip()` waits for input.
3. Empty input goes back to the prompt. `exit` or `quit` breaks out of the loop.
4. Otherwise the user message is appended to `history`.
5. `client.chat.completions.create(..., stream=True)` is called with `system_message + history`.
6. Chunks are printed as they arrive and accumulated into `reply`.
7. **On success:** the reply is stripped and, if non-empty, appended as an `assistant` message. Then `history` is trimmed to the last `MAX_HISTORY_LENGTH` messages and the loop repeats.
8. **On an empty reply or a recoverable error:** a clear message is printed, the unanswered user message is removed, and the chat continues.
9. **On an authentication error:** a message is printed and the program exits.

---

## Tool-Calling Flow (`chat_v8.py`)

1. The user message is appended and `turn_start` records where the turn began.
2. Round 1: the request is sent with `tools=TOOLS`. If the model wants a tool, the reply contains `tool_calls`.
3. The assistant message is appended, then for each requested call the name is checked against `AVAILABLE_TOOLS`, the arguments are parsed, the function runs, and a `tool` message with the matching id is appended.
4. Round 2: the model sees the tool results. If it needs nothing more, it returns plain text and the loop `break`s.
5. The final text is printed once and appended once as an `assistant` message.
6. If the round cap is reached, or an API error occurs, everything added during the turn is removed so the history stays valid.

---

## Testing Checklist

1. **Memory:** say "my name is Yash", then ask "what is my name". The model should answer correctly.
2. **Empty input:** press Enter or type only spaces. Nothing should be sent.
3. **Bad key:** put a wrong key in `.env`. You should see a clean message and the program exits.
4. **Network failure:** turn off Wi-Fi, send a message, turn it back on, send another. The first shows a network message, the second gets a normal reply with history intact.
5. **System prompt:** compare the same question in `chat_v4.py` and `chat_v5.py`. The replies should differ according to your system prompt.
6. **Streaming:** ask a long question. The text should appear gradually rather than all at once.
7. **Trimming:** set `MAX_HISTORY_LENGTH = 4`, tell the model your name, have two or three unrelated turns, then ask for your name. The model should no longer know it.
8. **Tool call:** in `chat_v8.py`, ask for the USD to INR rate. A `[tool]` debug line should appear, followed by the answer. Compare the number to a real source.
9. **Two tools:** ask to convert an amount and give today's date. Both tools should be used.
10. **No tool needed:** say "hi". No tool should be called.
11. **Round cap:** set `MAX_TOOL_ROUNDS = 1` and ask for an exchange rate. The cap message should appear and the turn should be rolled back.
12. **Tool failure:** temporarily break the exchange-rate URL. The model should explain the failure instead of crashing.

---

## Key Concepts Learned

- LLM APIs are stateless; conversation memory is client-side history resent each turn
- The `messages` list format and the `system`, `user`, and `assistant` roles
- Why API keys belong in environment variables, never in source code
- Typed exception handling and keeping conversation state consistent after failures
- A system prompt is resent on every call; it is instructions to the model, not part of the chat
- Streaming returns an iterator of chunks; the full reply must be rebuilt for history
- Context windows and why long histories must be trimmed
- Differences between provider SDK response shapes (Groq/OpenAI use `choices[0].message.content`; Anthropic uses `content[0].text`)
- LLMs have no live data: a model asked for something like a current exchange rate can only guess, which is the problem tool calling solves
- Tool calling: the model requests a function, your code executes it, and the result goes back with a matching `tool_call_id`
- Tool arguments are a JSON string; `json.loads` plus `func(**args)` runs the function
- Guardrails in code: an allowed-tool dictionary, a cap on tool rounds, and errors returned to the model instead of crashing
- A `finish_reason` of `tool_calls` means the model wants a tool; a normal answer means the loop can stop

---

## Roadmap

- [x] Single API call, chat loop, conversation memory, error handling
- [x] System prompt
- [x] Streaming responses
- [x] History trimming
- [ ] Detect cut-off replies using `finish_reason == "length"`
- [x] Tool calling loop with a live exchange-rate tool and a date/time tool
- [ ] Merge streaming and history trimming into the tool-calling script
- [ ] Extend into a RAG chatbot with embeddings and a vector database

---

## Tech Stack

- Python
- [Groq API](https://console.groq.com) (`groq` SDK)
- `python-dotenv`
- `requests`

---

## Credits

Exchange rates by [Exchange Rate API](https://www.exchangerate-api.com) (open access endpoint, `open.er-api.com`, updated once a day).
