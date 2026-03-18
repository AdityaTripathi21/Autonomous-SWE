# AutonomousSWE

A self-correcting code generation agent built with LangGraph. Give it a task in plain English, and it writes code, generates tests, runs them, and fixes errors automatically.

## How it works

```
User input → Task planner → Engineer agent (subgraph) → README generator
                                    ↓
                            Worker (generates code)
                                    ↓
                            Test creator (generates tests)
                                    ↓
                            Test runner (runs tests)
                                    ↓
                    [pass] → END    [fail] → Bug fixer → loop back
```

The engineer agent loops up to 3 times before giving up. On each failed attempt, the bug fixer sees the error and the previous code and tries to fix it.

## Project structure

```
AutonomousSWE/
├── agent.py              # main agent logic and graph
├── tools/
│   └── file_tools.py     # read, write, list file tools
├── workspace/
│   └── src/
│       ├── __init__.py
│       └── main.py       # generated code output
├── .env                  # API keys
└── requirements.txt
```

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/AutonomousSWE.git
cd AutonomousSWE
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install langgraph langchain langchain-groq python-dotenv
```

**4. Add your API key**

Create a `.env` file in the root:
```
GROQ_API_KEY=your_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com)

**5. Create the workspace**
```bash
mkdir -p workspace/src
touch workspace/src/__init__.py
```

## Usage

Run the agent:
```bash
python3 agent.py
```

You'll be prompted to enter a task:
```
Enter task (or 'quit' to exit): Write a function that checks if a number is prime
```

The agent will:
1. Clarify the requirements
2. Generate the code
3. Write it to `workspace/src/main.py`
4. Generate and run tests
5. Fix any errors automatically

## Example output

**Input:**
```
Write merge sort in Python
```

**Output (`workspace/src/main.py`):**
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    ...
```

## Built with

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent graph framework
- [LangChain](https://github.com/langchain-ai/langchain) — LLM tooling
- [Groq](https://groq.com) — LLM inference
