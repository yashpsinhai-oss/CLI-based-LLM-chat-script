# CLI-Based LLM Chat Script

A command-line chatbot built in Python using **raw LLM API calls** (no LangChain or other frameworks). The project was built in four incremental stages to understand how LLM chat actually works under the hood: stateless API calls, loops, conversation memory, and error handling.

It uses the **Groq API** (free tier) with the `openai/gpt-oss-120b` model.

---

## Features

- Interactive back-and-forth chat in the terminal
- Conversation memory (the model remembers earlier turns)
- Graceful error handling for network, rate-limit, and authentication failures
- Ignores empty input and supports `exit` / `quit` (case-insensitive)
- API key kept out of source control via a `.env` file

---

## Project Structure

```
CLI-based-LLM-chat-script/
├── chat_v1.py      # Stage 1: single raw API call
├── chat_v2.py      # Stage 2: chat loop, no memory
├── chat_v3.py      # Stage 3: conversation memory
├── chat_v4.py      # Stage 4: error handling (final version)
├── .env            # API key (NOT committed)
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
pip install groq python-dotenv
```

### 4. Add your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your-key-here
```

No quotes and no spaces around the `=`. The `.gitignore` already excludes this file.

### 5. Run

```powershell
python chat_v4.py
```

Type `exit` or `quit` to leave the chat.

### Which Python runs the script

The packages (`groq`, `python-dotenv`) are installed **inside the virtual environment**, so the script must be run with the environment's own interpreter, `.venv\Scripts\python.exe`. Activating the environment makes the plain `python` command point to it.

You can also skip activation and call that interpreter directly:

```powershell
.\.venv\Scripts\python.exe chat_v4.py
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

1. Create `messages = []` **outside** the loop
2. Append the user message before each API call
3. Pass the **whole list** as `messages=messages`
4. Append the assistant's reply after each response

**Key idea:** the model has no memory. "Memory" means resending the full conversation transcript every turn, with `user` and `assistant` roles marking who said what. A side effect is that token usage grows with every turn.

### Stage 4: Error handling (`chat_v4.py`)

Wraps the API call in `try` / `except` using Groq's typed exceptions:

| Exception | Behavior |
|---|---|
| `groq.APIConnectionError` | Print a network message, remove the unanswered user message, continue |
| `groq.RateLimitError` | Print a rate-limit message, remove the unanswered user message, continue |
| `groq.AuthenticationError` | Print a bad-key message and exit (retrying cannot fix it) |
| `groq.APIStatusError` | Generic fallback: print the status code, continue |

Details that matter:

- **Specific exceptions come before general ones.** `RateLimitError` and `AuthenticationError` are subclasses of `APIStatusError`, so the general handler must be last.
- **`messages.pop()` on failure.** The user message is appended before the call. If the call fails, it must be removed, otherwise the next turn sends two `user` messages in a row.
- **`continue` vs `break`.** `continue` skips the rest of the iteration and returns to `input()`. `break` leaves the loop entirely.
- **Empty input** (`""` or only spaces) is skipped with `.strip()` and `continue`, so nothing is sent to the API or added to history.

---

## Execution Flow (Final Version)

1. `load_dotenv()` loads `.env`, then the Groq client and an empty `messages` list are created once.
2. The loop starts and `input("User: ").strip()` waits for input.
3. Empty input goes back to the prompt. `exit` or `quit` breaks out of the loop.
4. Otherwise the user message is appended to `messages`.
5. `client.chat.completions.create(...)` sends the full history to the model.
6. **On success:** the reply is printed and appended as an `assistant` message, then the loop repeats.
7. **On a recoverable error:** a clear message is printed, the unanswered user message is removed, and the chat continues.
8. **On an authentication error:** a message is printed and the program exits.

---

## Testing Checklist

1. **Memory:** say "my name is Yash", then ask "what is my name". The model should answer correctly.
2. **Empty input:** press Enter or type only spaces. Nothing should be sent.
3. **Bad key:** put a wrong key in `.env`. You should see a clean message and the program exits.
4. **Network failure:** turn off Wi-Fi, send a message, turn it back on, send another. The first shows a network message, the second gets a normal reply with history intact.

---

## Key Concepts Learned

- LLM APIs are stateless; conversation memory is client-side history resent each turn
- The `messages` list format and the `system`, `user`, and `assistant` roles
- Why API keys belong in environment variables, never in source code
- Typed exception handling and keeping conversation state consistent after failures
- Differences between provider SDK response shapes (Groq/OpenAI use `choices[0].message.content`; Anthropic uses `content[0].text`)

---

## Roadmap

- [ ] System prompt to control model behavior
- [ ] Streaming responses (print tokens as they arrive)
- [ ] History trimming to cap token usage in long chats
- [ ] Tool calling loop (`finish_reason == "tool_calls"`)
- [ ] Extend into a RAG chatbot with embeddings and a vector database

---

## Tech Stack

- Python
- [Groq API](https://console.groq.com) (`groq` SDK)
- `python-dotenv`
