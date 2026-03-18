# Tips and Tricks for Working with LLMs in Production

Practical lessons from building the Q-SYS Plugin Generator — a web app that uses Claude to generate complete Lua-based plugins through multi-turn conversations.

---

## 1. Prompt Composition: The Agent/Skill Pattern

Instead of one giant system prompt, break it into composable layers:

```
Base knowledge (CLAUDE.md)          — domain fundamentals, always loaded
  + SDK topics note                 — tells the model what docs it can look up
  + Agent instructions (create.md)  — workflow for this specific mode
  + Skill modules (9-10 files)      — specific capabilities (layout, controls, etc.)
```

**Why this works:**
- Each layer is independently maintainable
- You can swap agents (create vs. modify) while keeping skills shared
- Skills can be reordered or added without touching the base prompt
- Easier to debug — you know which layer caused an issue

**Key insight:** Your system prompt is code. Treat it like code — modularize, version, and test it.

---

## 2. Tool-Based Documentation Retrieval

Don't stuff 7MB of SDK docs into the system prompt. Instead, give the model a tool to fetch docs on demand:

```python
SDK_REFERENCE_TOOL = {
    "name": "get_sdk_reference",
    "description": "Retrieve Q-SYS SDK reference documentation by topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "enum": ["tcp", "udp", "serial", "http", ...]
            }
        }
    }
}
```

**Benefits:**
- Only loads docs the model actually needs (often 2-3 topics out of 25+)
- Saves thousands of input tokens per request
- The model learns to self-serve — it fetches what it needs based on the user's request
- You can update documentation files without changing any code

**Implementation tip:** List available topics in the system prompt with short descriptions so the model knows what to ask for. Include guidance like "always fetch `timer` when the plugin needs polling."

---

## 3. Prompt Caching

Use Anthropic's prompt caching for large, repeated system prompts:

```python
response = client.messages.create(
    system=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"}
    }],
    ...
)
```

**Impact:** ~90% cost reduction on input tokens for the system prompt across requests that share the same cached prefix. Since the Q-SYS base prompt is ~15K tokens, this saves significantly on every API call.

**Gotcha:** Cache is keyed on exact prefix match. If you prepend dynamic content before the cached portion, the cache misses. Put dynamic content (like user-specific details) after the cached block, or in the user message.

---

## 4. Token Management: Conversation Trimming

Long multi-turn conversations will eventually hit the context window. Trim older messages while preserving context:

```python
def trim_messages_for_api(messages):
    """Replace code blocks in older messages with short placeholders."""
    code_block_re = re.compile(r"```(?:\w+\s+)?filename:([^\n]+)\n.*?```", re.DOTALL)

    for older_messages:
        # Replace full code with: [code: info.lua — included in plugin files]
        text = code_block_re.sub(replacer, text)
```

**Strategy:**
- Keep the last 2 exchanges (most recent user + assistant) intact — the model needs full context for its latest work
- Replace code blocks in older messages with filename-only placeholders
- The model still knows which files exist, just not the full content
- If it needs to reference old code, it can generate it again or ask the user

**Why not just truncate?** Dropping messages entirely loses context about decisions made earlier. Placeholders preserve the conversation flow while dramatically reducing tokens.

---

## 5. Rate Limiting & Retry Strategy

### Server-side (protecting your API key)

```python
# flask-limiter example
limiter = Limiter(app=app, key_func=get_remote_address)

@app.route("/generate", methods=["POST"])
@limiter.limit("10/hour")
def generate():
    ...
```

Set different limits per endpoint based on cost:
- `/generate` (expensive — new conversation + tool loops): 10/hour
- `/reply` (medium — continuation): 30/hour
- `/download` (cheap — no API call): 20/hour

### Client-side (handling Anthropic rate limits)

```python
for attempt in range(max_retries):
    try:
        response = client.messages.create(...)
        break
    except RateLimitError as e:
        retry_after = float(e.response.headers.get("retry-after", 30))
        time.sleep(retry_after)
```

**Always respect `retry-after` headers** — don't use fixed delays. The API tells you exactly how long to wait.

---

## 6. Cost Optimization

Ordered by impact:

1. **Prompt caching** — ~90% savings on repeated system prompts (biggest win)
2. **Tool-based docs** — load 2-3 topics instead of all 25+ (saves ~50K tokens per request)
3. **Conversation trimming** — keeps multi-turn costs from growing linearly
4. **Model selection** — Use Sonnet for code generation (good quality/cost balance). Reserve Opus for complex reasoning tasks
5. **Max tokens** — Set `max_tokens` appropriately (16K for code gen, not 100K). Prevents runaway responses

**Monitoring tip:** Log token usage from response headers to track costs:
```python
# response.usage.input_tokens, response.usage.output_tokens
```

---

## 7. Error Handling for LLM APIs

### Mixed content blocks

Claude responses can contain multiple block types — don't assume it's just text:

```python
def extract_text_from_response(response):
    parts = []
    for block in response.content:
        if hasattr(block, "text"):  # TextBlock
            parts.append(block.text)
        # Skip: ToolUseBlock, web search results, etc.
    return "\n".join(parts)
```

### Tool loops with safety limits

When the model uses tools, it needs another API call to continue. Set a maximum:

```python
max_tool_loops = 10
for loop in range(max_tool_loops):
    response = client.messages.create(...)
    tool_uses = [b for b in response.content if b.type == "tool_use"]
    if not tool_uses or response.stop_reason == "end_turn":
        return response
    # Process tools and continue...
```

Without this limit, a confused model could loop indefinitely.

### Timeout configuration

Claude API calls with tool loops can take 30-60+ seconds. Set timeouts accordingly:
- HTTP client timeout: 120s minimum
- WSGI server (gunicorn) timeout: 120s
- Reverse proxy timeout: 120s

If any layer in the chain has a shorter timeout, you'll get intermittent failures on complex generations.

---

## 8. Stateful Conversations

### UUID-based tracking (no auth needed for MVP)

```python
conv_id = str(uuid.uuid4())
conversations[conv_id] = {
    "messages": messages,
    "protocol": protocol,
    "tools": tools,
    "mode": mode
}
```

Simple, stateless from the client's perspective — the frontend just holds the UUID.

### TTL cleanup

Abandoned conversations waste memory/storage. Clean them up:

```python
def cleanup_expired(ttl_hours=24):
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)
    expired = [id for id, conv in conversations.items()
               if conv["created_at"] < cutoff]
    for id in expired:
        del conversations[id]
```

### Serialization

Anthropic SDK responses contain Pydantic model objects that aren't directly JSON-serializable. Convert them when storing:

```python
def serialize_content(content):
    if isinstance(content, list):
        return [block.model_dump() if hasattr(block, "model_dump") else block
                for block in content]
    return content
```

This lets you use JSON (or SQLite with JSON columns) instead of pickle, which is both safer and more portable.

---

## 9. File Generation: The Temp Directory Pattern

For generating files from LLM output (compiling, zipping, etc.):

```python
tmp_dir = tempfile.mkdtemp(prefix="qsys_plugin_")
try:
    # Write files
    for fname, content in files.items():
        with open(os.path.join(tmp_dir, fname), "w") as f:
            f.write(content)

    # Compile / process
    subprocess.run(["python", "compile.py", tmp_dir], timeout=30)

    # Read result
    result = open(os.path.join(tmp_dir, "output.qplug")).read()
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
```

**Key practices:**
- Always use `try/finally` — cleanup must happen even on errors
- Set subprocess `timeout` to prevent hangs
- Use unique prefixes (`qsys_plugin_`) so you can identify orphaned dirs
- Add periodic cleanup for crash recovery (scan `/tmp/qsys_plugin_*` for old dirs)

### Extracting structured output from LLM responses

Use a consistent format the model can follow and you can regex-parse:

````
```lua filename:info.lua
-- file content here
```
````

Then extract with:
```python
for m in re.finditer(r"```(?:\w+\s+)?filename:([^\n]+)\n(.*?)```", text, re.DOTALL):
    files[m.group(1).strip()] = m.group(2)
```

**Why this works well:**
- Code fences are natural for LLMs — they already know this format
- The `filename:` prefix is distinctive enough to avoid false matches
- You get both the filename and content in one pass
- The model can output multiple files in a single response

---

## 10. Production Checklist

Before going live, verify:

- [ ] Debug mode is OFF (`FLASK_DEBUG=false`)
- [ ] API keys are in environment variables, not in code
- [ ] Secret key is stable (not `os.urandom()` on every restart)
- [ ] Upload size limits are set (`MAX_CONTENT_LENGTH`)
- [ ] Rate limiting is active on expensive endpoints
- [ ] Conversation cleanup runs automatically (TTL)
- [ ] Structured logging is in place (not `print()`)
- [ ] HTTPS is enforced (handled by hosting platform)
- [ ] Subprocess calls have timeouts
- [ ] Temp directories are cleaned up in `finally` blocks
