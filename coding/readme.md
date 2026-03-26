# 🧠 Coding Agent with Tool Use (Groq API)

This project implements an **interactive terminal-based coding agent** powered by an LLM (via Groq API) to solve programming tasks.

The agent can:

* read files 📄
* explore directories 📁
* edit files ✏️
* autonomously decide when to use these tools

---

## 🚀 Features

* 🔧 Modular tool system (easy to extend)
* 🧠 LLM integration (`openai/gpt-oss-120b`)
* 💬 Interactive CLI loop
* 📂 Controlled filesystem access
* 🧩 Clean architecture with separated concerns

---

## 📁 Project Structure

```
project/
│
├── main.py              # Entry point
├── config.py           # Configuration (API, colors)
├── utils.py            # Generic utilities
│
├── agent.py            # Main agent loop
├── llm.py              # LLM API calls
├── parser.py           # Tool invocation parsing
├── prompt.py           # System prompt construction
│
├── tools/
│   ├── __init__.py
│   ├── file_tools.py   # Filesystem tools
│   └── registry.py     # Tool registry
│
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd project
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Main dependencies:

* `groq`
* `python-dotenv`
* `chardet`

---

### 4. Configure environment variables

Create a `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

---

## ▶️ Usage

Run the agent:

```bash
python main.py
```

You will see an interactive prompt:

```
You:
```

Example inputs:

* `read the file main.py`
* `list files in the current directory`
* `add a function to this file`

The agent will:

1. Analyze your request
2. Decide whether to use a tool
3. Execute the tool
4. Continue reasoning until producing a final answer

---

## 🛠️ Available Tools

### 📄 `read_file`

Reads the content of a file.

```python
read_file(filename: str)
```

---

### 📁 `list_files`

Lists files in a directory.

```python
list_files(path: str)
```

---

### ✏️ `edit_file`

Edits or creates a file.

```python
edit_file(path: str, old_str: str, new_str: str)
```

* If `old_str == ""` → creates/overwrites the file
* Otherwise → replaces the first occurrence

---

## 🧠 How It Works

### 1. Prompting

The system builds a **dynamic system prompt** including all available tools.

---

### 2. Tool Invocation

The model must respond using this format:

```
tool: TOOL_NAME({"arg": "value"})
```

---

### 3. Parsing

The parser:

* detects tool calls
* extracts function name and arguments
* supports fallback JSON format

---

### 4. Execution Loop

Agent workflow:

```
User → LLM → Tool → LLM → Final Output
```

---

## ➕ Adding New Tools

1. Define the function inside `tools/`
2. Register it in `tools/registry.py`

```python
TOOL_REGISTRY["tool_name"] = function
```

Done ✅ (automatically included in the prompt)

---

## 🧪 Possible Improvements

* Advanced logging
* Better error handling
* Streaming responses
* Filesystem sandboxing
* CLI enhancements (argparse / typer)
* Persistent memory

---

## ⚠️ Notes

* The model can access local files → use carefully
* Do not run on sensitive directories
* Always validate inputs in production environments

---

## 📄 License

Cristian Lepore

---

## 👤 Author

Built as an experiment in LLM agents with tool usage.

---

