from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from anthropic import Anthropic, RateLimitError
from dotenv import load_dotenv
import os, base64, uuid, re, io, zipfile, tempfile, shutil, subprocess, time, json, logging, threading
import requests as http
import database as db

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("qsys")

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------
if not os.environ.get("ANTHROPIC_API_KEY"):
    logger.error("ANTHROPIC_API_KEY is not set. The server will not be able to generate plugins.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

client = Anthropic()

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
db.init_db()

# ---------------------------------------------------------------------------
# Background cleanup thread — purge expired conversations every hour
# ---------------------------------------------------------------------------
def _cleanup_loop():
    while True:
        time.sleep(3600)
        try:
            db.cleanup_expired(ttl_hours=24)
        except Exception:
            logger.exception("Error during conversation cleanup")

_cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)
_cleanup_thread.start()

# ---------------------------------------------------------------------------
# Anthropic tools
# ---------------------------------------------------------------------------
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,
}

SDK_REFERENCE_TOOL = {
    "name": "get_sdk_reference",
    "description": (
        "Retrieve Q-SYS SDK reference documentation by topic. "
        "Use this to look up specific SDK details when generating plugin code. "
        "You can call this multiple times for different topics."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The SDK topic to retrieve documentation for.",
                "enum": [
                    "tcp", "udp", "serial", "http", "ssh",
                    "plugin_framework", "reserved_functions", "scoping",
                    "pcall", "style_guide", "reserved_controls",
                    "building_a_plugin", "crypto", "json_parsing",
                    "xml_parsing", "timer", "controls_io", "notifications",
                    "system", "log", "hex_data", "named_components",
                    "dynamic_pages", "storing_secrets",
                ],
            }
        },
        "required": ["topic"],
    },
}

SDK_TOPIC_FILES = {
    "tcp": [
        "documents/SDK Help/Recommended_Practices-TCP.md",
        "documents/SDK Help/Code_Examples-TCPSocket_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-TcpSocket.md",
    ],
    "udp": [
        "documents/SDK Help/Recommended_Practices-UDP.md",
        "documents/SDK Help/Code_Examples-UDPSocket_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-UdpSocket.md",
    ],
    "serial": [
        "documents/SDK Help/Recommended_Practices-Serial.md",
        "documents/SDK Help/Code_Examples-SerialPort.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-SerialPorts.md",
    ],
    "http": [
        "documents/SDK Help/Code_Examples-HTTPClient.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-HttpClient.md",
    ],
    "ssh": [
        "documents/SDK Help/Code_Examples-SSH_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Ssh.md",
    ],
    "plugin_framework": [
        "documents/SDK Help/Code_Examples-Basic_Plugin_Framework.md",
    ],
    "reserved_functions": [
        "documents/SDK Help/Standards_Definitions-Reserved_Functions.md",
    ],
    "scoping": [
        "documents/SDK Help/Recommended_Practices-LuaScoping.md",
    ],
    "pcall": [
        "documents/SDK Help/Recommended_Practices-Pcall.md",
    ],
    "style_guide": [
        "documents/SDK Help/Standards_Definitions-Style_Guide.md",
    ],
    "reserved_controls": [
        "documents/SDK Help/Standards_Definitions-Reserved_Control_Names.md",
    ],
    "building_a_plugin": [
        "documents/SDK Help/Getting_Started-Building_a_Plugin.md",
    ],
    "crypto": [
        "documents/SDK Help/Code_Examples-Crypto_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Crypto.md",
    ],
    "json_parsing": [
        "documents/SDK Help/Code_Examples-JSON_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-JSON.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-RapidJSON.md",
    ],
    "xml_parsing": [
        "documents/SDK Help/Code_Examples-XML_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-LuaXML.md",
    ],
    "timer": [
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Timer.md",
    ],
    "controls_io": [
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Controls_IO.md",
    ],
    "notifications": [
        "documents/SDK Help/Code_Examples-Notifications_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Notifications.md",
    ],
    "system": [
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-System.md",
    ],
    "log": [
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Log.md",
    ],
    "hex_data": [
        "documents/SDK Help/Code_Examples-Hex_Data_Handling.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Lua_Bitstring.md",
    ],
    "named_components": [
        "documents/SDK Help/Code_Examples-Named_Components_Example.md",
        "documents/General Help/Control_Scripting-Using_Lua_in_Q-Sys-Component.md",
    ],
    "dynamic_pages": [
        "documents/SDK Help/Code_Examples-Dynamic_Pages.md",
    ],
    "storing_secrets": [
        "documents/SDK Help/Code_Examples-Storing_Secrets_in_Plugins.md",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def serialize_content(content):
    """Convert Anthropic SDK content blocks to JSON-serializable dicts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        result = []
        for block in content:
            if isinstance(block, dict):
                result.append(block)
            elif hasattr(block, "model_dump"):
                result.append(block.model_dump())
            elif hasattr(block, "__dict__"):
                result.append(block.__dict__)
            else:
                result.append(block)
        return result
    if hasattr(content, "model_dump"):
        return content.model_dump()
    return content


def safe_filename(name):
    """Sanitize a string for use as a filename."""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '-') or "plugin"


VALID_PROTOCOLS = {"tcp", "udp", "serial", "http", "ssh", "none", ""}
VALID_MODES = {"create", "modify"}


def handle_sdk_tool(topic):
    """Read SDK documentation files for the given topic and return their content."""
    files = SDK_TOPIC_FILES.get(topic, [])
    if not files:
        return f"Unknown topic: {topic}"
    sections = []
    for path in files:
        full_path = os.path.join(BASE_DIR, path)
        if os.path.isfile(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                sections.append(f"### {os.path.basename(path)}\n\n{f.read()}")
    return "\n\n---\n\n".join(sections) if sections else f"No documentation found for topic: {topic}"


def call_claude(messages, system_prompt, tools, max_retries=3):
    """Call Claude with tools, prompt caching, retry on rate limit, and custom tool handling loop."""
    max_tool_loops = 10

    for loop in range(max_tool_loops):
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=16000,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=messages,
                    tools=tools,
                )
                break
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                retry_after = float(e.response.headers.get("retry-after", 30))
                logger.warning("Rate limited, retrying in %.0fs (attempt %d/%d)", retry_after, attempt + 1, max_retries)
                time.sleep(retry_after)

        # Check if we need to handle any custom tool calls
        tool_uses = [b for b in response.content if hasattr(b, "type") and b.type == "tool_use"]
        sdk_tool_uses = [t for t in tool_uses if t.name == "get_sdk_reference"]

        if not sdk_tool_uses or response.stop_reason == "end_turn":
            return response

        # Process SDK tool calls and continue the conversation
        logger.info("SDK tool requests: %s", [t.input.get("topic") for t in sdk_tool_uses])
        messages.append({"role": "assistant", "content": serialize_content(response.content)})

        tool_results = []
        for tool_use in sdk_tool_uses:
            topic = tool_use.input.get("topic", "")
            content = handle_sdk_tool(topic)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": content,
            })

        messages.append({"role": "user", "content": tool_results})

    return response


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------
AGENT_SKILLS = {
    "create": [
        "file-output-format", "connection-settings", "protocol-discovery",
        "file-specifications", "control-arrays", "layout-design",
        "runtime-practices", "consistency-checklist", "output-summary",
    ],
    "modify": [
        "file-output-format", "connection-settings", "file-specifications",
        "control-arrays", "layout-design", "runtime-practices",
        "consistency-checklist", "output-summary",
    ],
}


def build_sdk_topics_note(protocol=""):
    """Build the SDK reference documentation note listing available topics."""
    return (
        "# SDK Reference Documentation\n\n"
        "You have access to a `get_sdk_reference` tool to retrieve detailed Q-SYS SDK documentation on demand. "
        "Use it to look up specific topics when you need detailed API references or code examples.\n\n"
        "Available topics:\n\n"
        "**Plugin SDK (best practices & examples):**\n"
        "- `tcp` — TCP socket practices, SDK examples, and TcpSocket API reference\n"
        "- `udp` — UDP socket practices, SDK examples, and UdpSocket API reference\n"
        "- `serial` — Serial port practices, SDK examples, and SerialPorts API reference\n"
        "- `http` — HTTP client SDK examples and HttpClient API reference\n"
        "- `ssh` — SSH SDK examples and Ssh API reference\n"
        "- `plugin_framework` — Basic plugin framework example\n"
        "- `building_a_plugin` — Getting started guide\n"
        "- `reserved_functions` — All Q-SYS reserved design-time functions\n"
        "- `reserved_controls` — Reserved control names\n"
        "- `style_guide` — Code style guide\n"
        "- `scoping` — Lua scoping best practices\n"
        "- `pcall` — Error handling with pcall\n\n"
        "**Control Scripting APIs (runtime classes & utilities):**\n"
        "- `crypto` — Crypto class: Base64 encode/decode, CRC16, HMAC, MD5\n"
        "- `json_parsing` — JSON encoding/decoding with RapidJSON\n"
        "- `xml_parsing` — XML parsing with LuaXML\n"
        "- `timer` — Timer class for periodic and one-shot timers\n"
        "- `controls_io` — Controls[] table for reading/writing plugin controls at runtime\n"
        "- `notifications` — Notifications class for user-facing alerts\n"
        "- `system` — System class: platform info, design name, etc.\n"
        "- `log` — Log class for structured debug logging\n"
        "- `hex_data` — Hex data handling and Lua Bitstring library\n"
        "- `named_components` — Named Components and Component API\n"
        "- `dynamic_pages` — Dynamic page management in plugins\n"
        "- `storing_secrets` — Securely storing secrets in plugins\n\n"
        "**IMPORTANT:** Always fetch the relevant Control Scripting API docs alongside SDK docs. "
        "For example, if using TCP, fetch both `tcp` (for SDK practices) and `controls_io` (for Controls[] usage). "
        "If the protocol requires encoding (e.g., Base64, hex), fetch `crypto` or `hex_data`. "
        "Always fetch `timer` when the plugin needs polling or periodic tasks.\n\n"
        f"The user selected protocol: **{protocol}**. Fetch the relevant protocol SDK docs before generating code.\n"
    )


def load_system_prompt(protocol="", mode="create"):
    """Assemble the system prompt from CLAUDE.md + SDK topics + agent instructions + skills."""
    claude_md = open(os.path.join(BASE_DIR, "prompts/CLAUDE.md")).read()
    sdk_topics_note = build_sdk_topics_note(protocol)
    agent_md = open(os.path.join(BASE_DIR, f"prompts/agents/{mode}.md")).read()

    skill_sections = []
    for skill_name in AGENT_SKILLS.get(mode, AGENT_SKILLS["create"]):
        path = os.path.join(BASE_DIR, f"prompts/skills/{skill_name}.md")
        with open(path, "r", encoding="utf-8") as f:
            skill_sections.append(f.read())
    skills_md = "\n\n---\n\n".join(skill_sections)

    return (
        f"{claude_md}\n\n"
        f"---\n\n"
        f"{sdk_topics_note}\n\n"
        f"---\n\n"
        f"{agent_md}\n\n"
        f"---\n\n"
        f"{skills_md}"
    )


# ---------------------------------------------------------------------------
# Message trimming
# ---------------------------------------------------------------------------
def trim_messages_for_api(messages):
    """Create a trimmed copy of messages for API calls, replacing code blocks in older
    assistant messages with short placeholders to reduce token count."""
    if len(messages) <= 2:
        return messages

    code_block_re = re.compile(r"```(?:\w+\s+)?filename:([^\n]+)\n.*?```", re.DOTALL)

    def trim_text(text):
        def replacer(m):
            return f"[code: {m.group(1).strip()} — included in plugin files]"
        return code_block_re.sub(replacer, text)

    def trim_content(content):
        if isinstance(content, str):
            return trim_text(content)
        if isinstance(content, list):
            trimmed = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    trimmed.append({**block, "text": trim_text(block["text"])})
                elif hasattr(block, "type") and block.type == "text":
                    trimmed.append({"type": "text", "text": trim_text(block.text)})
                else:
                    trimmed.append(block)
            return trimmed
        return content

    trimmed = []
    for i, msg in enumerate(messages):
        if i < len(messages) - 2 and msg["role"] == "assistant":
            trimmed.append({**msg, "content": trim_content(msg["content"])})
        else:
            trimmed.append(msg)
    return trimmed


# ---------------------------------------------------------------------------
# Response / content helpers
# ---------------------------------------------------------------------------
def extract_text_from_response(response):
    """Extract all text blocks from a Claude response (skipping tool_use, search results, etc.)."""
    parts = []
    for block in response.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts)


def get_text_from_content(content):
    """Get text from a message content field (may be string, list of blocks, or block objects)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif hasattr(block, "type") and block.type == "text":
                parts.append(block.text)
        return "\n".join(parts)
    return ""


def extract_files_from_conversation(messages):
    """Parse ```filename:xxx code blocks from all assistant messages."""
    files = {}
    for msg in messages:
        if msg["role"] != "assistant":
            continue
        text = get_text_from_content(msg["content"])
        for m in re.finditer(
            r"```(?:\w+\s+)?filename:([^\n]+)\n(.*?)```",
            text,
            re.DOTALL,
        ):
            fname = m.group(1).strip()
            content = m.group(2)
            files[fname] = content
    return files


def compile_plugin_in_memory(files):
    """Write files to a temp directory, run compile.py, and return the .qplug content."""
    tmp_dir = tempfile.mkdtemp(prefix="qsys_plugin_")
    try:
        for fname, content in files.items():
            filepath = os.path.join(tmp_dir, fname)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        if "plugin.lua" not in files:
            return None, None

        compile_script = os.path.join(BASE_DIR, "compile.py")
        if not os.path.isfile(compile_script):
            return None, None

        result = subprocess.run(
            ["python", compile_script, tmp_dir, "--bump=skip"],
            capture_output=True,
            text=True,
            cwd=tmp_dir,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error("Compile error: %s", result.stderr)
            return None, None

        for f in os.listdir(tmp_dir):
            if f.endswith(".qplug"):
                qplug_path = os.path.join(tmp_dir, f)
                with open(qplug_path, "r", encoding="utf-8") as qf:
                    return f, qf.read()

        return None, None
    except Exception:
        logger.exception("Compile exception")
        return None, None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def format_chat_history_md(messages):
    """Format conversation messages as a Markdown chat history."""
    lines = ["# Plugin Generation Chat History\n"]
    for msg in messages:
        role = msg["role"]
        if role not in ("user", "assistant"):
            continue
        text = get_text_from_content(msg["content"])
        if not text:
            continue
        heading = "User" if role == "user" else "Assistant"
        lines.append(f"## {heading}\n")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _validate_conversation(conv_id, endpoint_name=""):
    """Validate a conversation ID exists. Returns (conv, None) or (None, error_response)."""
    if not conv_id:
        logger.warning("%s failed: empty conversation ID", endpoint_name)
        return None, (jsonify({"error": "Conversation not found. Please start a new generation."}), 400)
    conv = db.get_conversation(conv_id)
    if conv is None:
        logger.warning("%s failed: conversation '%s' not found", endpoint_name, conv_id)
        return None, (jsonify({"error": "Conversation not found. Please start a new generation."}), 400)
    return conv, None


def _extract_and_compile(conv, plugin_name):
    """Extract files from conversation and compile. Returns (files, qplug_name, qplug_content, safe_name) or error."""
    files = extract_files_from_conversation(conv["messages"])
    if not files:
        for msg in conv["messages"]:
            if msg["role"] == "assistant":
                text = get_text_from_content(msg["content"])
                logger.warning("No files found. Assistant text preview: %s", text[:300])
        return None, None, None, None, (jsonify({"error": "No plugin files found in the conversation yet. Continue the conversation until files are generated."}), 400)

    qplug_name, qplug_content = compile_plugin_in_memory(files)
    safe_name = safe_filename(plugin_name) if plugin_name else None
    if qplug_name and qplug_content and safe_name:
        qplug_name = f"{safe_name}.qplug"
    return files, qplug_name, qplug_content, safe_name, None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return send_from_directory("static/dist", "index.html")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("static/dist/assets", filename)


@app.route("/generate", methods=["POST"])
@limiter.limit("10/hour")
def generate():
    mode        = request.form.get("mode", "create")
    plugin_name = request.form.get("plugin_name", "").strip()
    description = request.form.get("description", "")
    protocol    = request.form.get("protocol", "").lower()
    connection  = request.form.get("connection", "").strip()
    api_doc_url = request.form.get("api_doc_url", "").strip()

    # --- Validation ---
    if mode not in VALID_MODES:
        return jsonify({"error": "Invalid mode."}), 400
    if not description:
        return jsonify({"error": "Description is required."}), 400
    if protocol not in VALID_PROTOCOLS:
        return jsonify({"error": f"Invalid protocol. Must be one of: {', '.join(VALID_PROTOCOLS - {''})}"}), 400

    message_content = []

    # --- Handle plugin file uploads for modify mode ---
    if mode == "modify":
        plugin_files = {}
        for f in request.files.getlist("plugin_files"):
            if f and f.filename:
                raw = f.read()
                fname = f.filename.lower()
                if fname.endswith(".zip"):
                    zip_data = io.BytesIO(raw)
                    try:
                        with zipfile.ZipFile(zip_data) as zf:
                            for name in zf.namelist():
                                if name.endswith(".lua") and not name.startswith("__MACOSX"):
                                    content = zf.read(name).decode("utf-8", errors="replace")
                                    plugin_files[os.path.basename(name)] = content
                    except zipfile.BadZipFile:
                        return jsonify({"error": "Invalid ZIP file."}), 400
                elif fname.endswith(".qplug"):
                    plugin_files[f.filename] = raw.decode("utf-8", errors="replace")
                elif fname.endswith(".lua"):
                    plugin_files[f.filename] = raw.decode("utf-8", errors="replace")

        if not plugin_files:
            return jsonify({"error": "Please upload at least one plugin file (.lua, .zip, or .qplug)."}), 400

        plugin_code_sections = []
        for fname, content in sorted(plugin_files.items()):
            plugin_code_sections.append(f"--- File: {fname} ---\n{content}")
        plugin_code_text = "\n\n".join(plugin_code_sections)

        user_message = f"""Here is my existing Q-SYS plugin code:

{plugin_code_text}

Please make the following modifications:

Plugin Name: {plugin_name if plugin_name else 'Not specified'}
Changes Requested: {description}
"""
    else:
        user_message = f"""Create a Q-SYS plugin with the following details:

Plugin Name: {plugin_name if plugin_name else 'Not specified'}
Description: {description}
Protocol: {protocol}
Connection: {connection if connection else 'Not specified'}
"""

    # --- API / protocol document ---
    if api_doc_url:
        try:
            resp = http.get(api_doc_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                message_content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(resp.content).decode("utf-8"),
                    },
                    "title": "API / Protocol Document",
                    "context": "This is the device API or protocol reference. Use it to determine the exact commands, responses, and communication details for the plugin.",
                })
            else:
                message_content.append({
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": resp.text[:100_000],
                    },
                    "title": "API / Protocol Document",
                    "context": "This is the device API or protocol reference. Use it to determine the exact commands, responses, and communication details for the plugin.",
                })
        except Exception as e:
            return jsonify({"error": f"Failed to fetch URL: {e}"}), 400

    elif "api_doc_file" in request.files:
        f = request.files["api_doc_file"]
        if f and f.filename:
            raw = f.read()
            if f.filename.lower().endswith(".pdf"):
                message_content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(raw).decode("utf-8"),
                    },
                    "title": f.filename,
                    "context": "This is the device API or protocol reference. Use it to determine the exact commands, responses, and communication details for the plugin.",
                })
            else:
                message_content.append({
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": raw.decode("utf-8", errors="replace")[:100_000],
                    },
                    "title": f.filename,
                    "context": "This is the device API or protocol reference. Use it to determine the exact commands, responses, and communication details for the plugin.",
                })

    message_content.append({"type": "text", "text": user_message})

    # Build tools list
    web_search_enabled = request.form.get("web_search", "") == "on"
    tools = [SDK_REFERENCE_TOOL]
    if web_search_enabled:
        tools.append(WEB_SEARCH_TOOL)

    # Create a new conversation session
    conv_id = str(uuid.uuid4())
    messages = [{"role": "user", "content": message_content}]

    logger.info("New conversation %s (mode=%s, protocol=%s)", conv_id, mode, protocol)

    try:
        response = call_claude(messages, load_system_prompt(protocol, mode), tools)
    except RateLimitError:
        return jsonify({"error": "Rate limited by the API. Please wait a minute and try again."}), 429

    assistant_text = extract_text_from_response(response)
    messages.append({"role": "assistant", "content": serialize_content(response.content)})

    conv_data = {"messages": messages, "protocol": protocol, "tools": tools, "mode": mode}
    db.save_conversation(conv_id, conv_data)

    return jsonify({"result": assistant_text, "conversation_id": conv_id})


@app.route("/reply", methods=["POST"])
@limiter.limit("30/hour")
def reply():
    data = request.get_json()
    conv_id = data.get("conversation_id", "")
    user_text = data.get("message", "").strip()

    conv, err = _validate_conversation(conv_id, "Reply")
    if err:
        return err
    if not user_text:
        return jsonify({"error": "Message cannot be empty."}), 400

    messages = conv["messages"]
    tools = conv.get("tools", [SDK_REFERENCE_TOOL])
    messages.append({"role": "user", "content": user_text})

    try:
        trimmed = trim_messages_for_api(messages)
        response = call_claude(trimmed, load_system_prompt(conv["protocol"], conv.get("mode", "create")), tools)
    except RateLimitError:
        messages.pop()
        return jsonify({"error": "Rate limited by the API. Please wait a minute and try again."}), 429

    assistant_text = extract_text_from_response(response)
    messages.append({"role": "assistant", "content": serialize_content(response.content)})
    db.save_conversation(conv_id, conv)

    return jsonify({"result": assistant_text})


@app.route("/download", methods=["POST"])
@limiter.limit("20/hour")
def download():
    """Test download: returns compiled .qplug file only (no source)."""
    data = request.get_json()
    conv_id = data.get("conversation_id", "")
    plugin_name = data.get("plugin_name", "").strip()

    conv, err = _validate_conversation(conv_id, "Download")
    if err:
        return err

    files, qplug_name, qplug_content, safe_name, err = _extract_and_compile(conv, plugin_name)
    if err:
        return err

    if not qplug_name or not qplug_content:
        return jsonify({"error": "Plugin compilation failed. Check that all required files are present."}), 400

    buf = io.BytesIO(qplug_content.encode("utf-8"))
    download_name = qplug_name if qplug_name else "plugin.qplug"
    return send_file(buf, mimetype="application/octet-stream", as_attachment=True, download_name=download_name)


@app.route("/complete", methods=["POST"])
@limiter.limit("20/hour")
def complete():
    """Final download: returns full ZIP with source, compiled .qplug, and chat history. Deletes conversation."""
    data = request.get_json()
    conv_id = data.get("conversation_id", "")
    plugin_name = data.get("plugin_name", "").strip()

    conv, err = _validate_conversation(conv_id, "Complete")
    if err:
        return err

    files, qplug_name, qplug_content, safe_name, err = _extract_and_compile(conv, plugin_name)
    if err:
        return err

    chat_history = format_chat_history_md(conv["messages"])

    zip_filename = f"{safe_name}-complete.zip" if safe_name else "plugin-complete.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
        if qplug_name and qplug_content:
            zf.writestr(qplug_name, qplug_content)
        zf.writestr("chat-history.md", chat_history)
    buf.seek(0)

    db.delete_conversation(conv_id)
    logger.info("Conversation %s completed and deleted", conv_id)

    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=zip_filename)


@app.route("/delete-conversation", methods=["POST"])
def delete_conversation():
    """Delete a conversation (used by Start Over)."""
    data = request.get_json()
    conv_id = data.get("conversation_id", "")
    if conv_id:
        db.delete_conversation(conv_id)
        logger.info("Conversation %s deleted", conv_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug, port=port)
