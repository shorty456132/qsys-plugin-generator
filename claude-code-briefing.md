# Q-SYS Plugin Generator — Build Briefing

## What We're Building

A local web app that exposes the Q-SYS plugin scaffolding workflow (currently only available in Claude Code terminal) as a browser-based form. User fills out plugin details, clicks generate, gets back fully scaffolded plugin code via the Anthropic API.

## File Structure to Create

```
qsys-plugin-generator/
├── server.py
├── .env
├── prompts/
│   ├── CLAUDE.md          ← copy from existing project
│   └── SKILL.md           ← copy from .claude/create-plugin/SKILL.md
└── static/
    └── index.html
```

## Dependencies

```bash
pip install flask anthropic python-dotenv
```

## .env

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## server.py

```python
from flask import Flask, request, jsonify, send_from_directory
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder="static")
client = Anthropic()

def load_system_prompt():
    claude_md = open("prompts/CLAUDE.md").read()
    skill_md = open("prompts/SKILL.md").read()
    return f"{claude_md}\n\n---\n\n{skill_md}"

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json

    user_message = f"""Create a Q-SYS plugin with the following details:

Description: {data['description']}
Protocol: {data['protocol']}
Connection: {data.get('connection', 'Not specified')}
Commands: {data.get('commands', 'Not specified')}
Responses: {data.get('responses', 'Not specified')}
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8096,
        system=load_system_prompt(),
        messages=[{"role": "user", "content": user_message}]
    )

    return jsonify({"result": response.content[0].text})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

## static/index.html

Build a clean single-page form with these fields:

- **Plugin Description** (textarea) — what the plugin does and what device it controls
- **Protocol** (dropdown) — TCP, UDP, Serial, HTTP, SSH, None
- **Connection Details** (text input) — IP/port/baud rate etc.
- **Commands** (textarea) — commands to send to the device
- **Responses** (textarea) — expected responses from the device
- **Generate Button** — POSTs to `/generate`
- **Output area** — displays the raw returned text (code blocks, file contents)

Keep the UI clean and functional. No frameworks needed — plain HTML/CSS/JS is fine.

## How It Works

1. User fills out the form and clicks Generate
2. `index.html` POSTs the form fields as JSON to `/generate`
3. `server.py` loads `prompts/CLAUDE.md` + `prompts/SKILL.md` as the system prompt
4. Calls the Anthropic API (`claude-sonnet-4-20250514`) with the user message built from the form fields
5. Returns the response to the browser and displays it

## To Run

```bash
python server.py
```

Open `http://localhost:5000`

## Notes

- This is Phase 1 (single form, single API call). Phase 2 will convert this into a multi-turn chat interface where Claude can ask follow-up questions about protocol details before generating — matching the interactive behavior of the Claude Code terminal workflow.
- The `prompts/` folder is the "secret sauce" — CLAUDE.md contains Q-SYS rules and patterns, SKILL.md contains the scaffolding workflow instructions.
