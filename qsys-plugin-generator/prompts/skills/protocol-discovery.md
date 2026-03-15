# Protocol & Command Discovery

If the plugin description involves communicating with a device (mentions TCP, UDP, Serial, HTTP, SSH, or a specific device brand/model), you **must** gather the device's control protocol details **before generating any files**. This ensures the correct commands, responses, and parsing logic are built into the plugin from the start.

## Step 1: Check for Attached Protocol Document

The user may have attached a protocol document (PDF or text file) with their request. If a protocol document is present in the conversation, use it directly — extract the command set, response format, and connection details from it.

If no document is attached, ask the user how they want to provide protocol information:

- **"I have a protocol doc"** — Ask the user to paste the protocol details in their reply, or to go back to the form and attach a document.
- **"Search the web"** — Only offer this option if you have the `web_search` tool available (the user must enable it via the checkbox on the form). Use it to search for the manufacturer's control protocol documentation (e.g., search for `"<brand> <model> RS-232 control protocol"` or `"<brand> <model> API commands TCP"`). If no reliable protocol docs are found, inform the user and fall back to manual entry. **Do not mention web search if the tool is not available.**
- **"I'll provide commands manually"** — Ask the user to describe or list the commands the plugin needs to send and the expected responses.

## Step 2: Extract & Organize Commands

From the gathered protocol information, identify and organize:

1. **Connection details** — protocol type (TCP/UDP/Serial/HTTP), default port, baud rate, delimiter/EOL characters
2. **Command format** — structure of commands (e.g., fixed strings, hex bytes, headers/footers, checksums)
3. **Command list** — specific commands for each function the plugin needs (power on/off, input select, volume, mute, etc.)
4. **Response format** — how the device responds (acknowledgment strings, status responses, error codes)
5. **Polling** — whether the device supports status polling and what commands to use

## Step 3: Confirm with the User

Present a summary of the discovered commands and protocol details to the user. Ask them to confirm the command set is correct or provide corrections before proceeding to file generation.

**Example summary format:**
```
Protocol: TCP, Port 23, Delimiter: \r
Commands found:
  - Power On:  "POWR 1\r"  → Response: "POWR=1\r"
  - Power Off: "POWR 0\r"  → Response: "POWR=0\r"
  - Input HDMI1: "INPT 1\r" → Response: "INPT=1\r"
  - Volume Set: "VOLM <value>\r" → Response: "VOLM=<value>\r"
  - Mute On: "AMUT 1\r" → Response: "AMUT=1\r"
  - Status Poll: "POWR?\r" → Response: "POWR=<0|1>\r"
```

If the plugin does **not** communicate with a device (e.g., a utility or logic-only plugin), skip this section entirely.
