---
name: create-plugin
description: Scaffold a complete Q-SYS plugin from scratch, creating all required Lua files with correct structure and cross-references
argument-hint: plugin description
---

# Create Q-SYS Plugin

Create a complete Q-SYS plugin based on the following description:

**$ARGUMENTS**

## File Output Format

You are running inside a web application. You do NOT have filesystem access. Do NOT ask the user for a directory path or attempt to create files on disk.

Instead, output each file using fenced code blocks with the filename on the opening fence line. Use this exact format:

```lua filename:info.lua
-- file contents here
```

```lua filename:runtime.lua
-- file contents here
```

The web app will parse these blocks and package them into a downloadable ZIP file for the user. Every file you create must use this `filename:` prefix format on the code fence line.

## Plugin Name

The user provides a plugin name in the form. Use this name for:
- `PluginInfo.Name` in `info.lua`
- `GetPrettyName()` display string in `plugin.lua`

## Connection Settings as Runtime Controls (IMPORTANT)

Device connection details like **IP addresses, port numbers, display IDs, device keys, usernames, and passwords** must be **runtime-settable controls**, NOT properties. Properties are baked in at design-time and cannot be changed without editing the design.

**Rules:**
- Create these as **Text controls** in `controls.lua` (e.g., `IPAddress`, `Port`, `DeviceID`)
- Place them on a **"Setup"** or **"Settings" page** in `layout.lua` — separate from the main control page
- In `runtime.lua`, read connection values from `Controls["IPAddress"].String`, `Controls["Port"].String`, etc.
- Use the Q-SYS reserved control names where applicable: `IPAddress`, `Username`, `Password` — these enable built-in Q-SYS features
- The plugin should have at least 2 pages: **"Control"** (main controls) and **"Setup"** (connection settings)
- Only put things in **properties** that truly need to be design-time only (e.g., number of channels, model selection, protocol type)

**Example controls.lua pattern for connection settings:**
```lua
table.insert(ctrls, {
  Name = "IPAddress",
  ControlType = "Text",
  Count = 1,
  UserPin = true,
  PinStyle = "Both"
})
table.insert(ctrls, {
  Name = "Port",
  ControlType = "Text",
  Count = 1,
  UserPin = true,
  PinStyle = "Both"
})
table.insert(ctrls, {
  Name = "Connect",
  ControlType = "Button",
  ButtonType = "Toggle",
  Count = 1,
  UserPin = true,
  PinStyle = "Both"
})
table.insert(ctrls, {
  Name = "Status",
  ControlType = "Indicator",
  IndicatorType = "Status",
  Count = 1,
  UserPin = true,
  PinStyle = "Output"
})
```

**Example runtime.lua pattern using connection controls:**
```lua
function Initialize()
  local ip = Controls["IPAddress"].String
  local port = tonumber(Controls["Port"].String) or 23
  if ip ~= "" and Controls["Connect"].Boolean then
    TCP:Connect(ip, port)
  end
end

Controls["Connect"].EventHandler = function(ctl)
  if ctl.Boolean then
    Initialize()
  else
    TCP:Disconnect()
  end
end
```

## Protocol & Command Discovery

If the plugin description involves communicating with a device (mentions TCP, UDP, Serial, HTTP, SSH, or a specific device brand/model), you **must** gather the device's control protocol details **before generating any files**. This ensures the correct commands, responses, and parsing logic are built into the plugin from the start.

### Step 1: Check for Attached Protocol Document

The user may have attached a protocol document (PDF or text file) with their request. If a protocol document is present in the conversation, use it directly — extract the command set, response format, and connection details from it.

If no document is attached, ask the user how they want to provide protocol information:

- **"I have a protocol doc"** — Ask the user to paste the protocol details in their reply, or to go back to the form and attach a document.
- **"Search the web"** — Only offer this option if you have the `web_search` tool available (the user must enable it via the checkbox on the form). Use it to search for the manufacturer's control protocol documentation (e.g., search for `"<brand> <model> RS-232 control protocol"` or `"<brand> <model> API commands TCP"`). If no reliable protocol docs are found, inform the user and fall back to manual entry. **Do not mention web search if the tool is not available.**
- **"I'll provide commands manually"** — Ask the user to describe or list the commands the plugin needs to send and the expected responses.

### Step 2: Extract & Organize Commands

From the gathered protocol information, identify and organize:

1. **Connection details** — protocol type (TCP/UDP/Serial/HTTP), default port, baud rate, delimiter/EOL characters
2. **Command format** — structure of commands (e.g., fixed strings, hex bytes, headers/footers, checksums)
3. **Command list** — specific commands for each function the plugin needs (power on/off, input select, volume, mute, etc.)
4. **Response format** — how the device responds (acknowledgment strings, status responses, error codes)
5. **Polling** — whether the device supports status polling and what commands to use

### Step 3: Confirm with the User

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

## You Must Create ALL Files

You are responsible for creating and populating **every** `.lua` file listed below. None are pre-filled or auto-generated. You must author each one with the correct content for this specific plugin.

### Required Files

| File | Purpose |
|------|---------|
| `plugin.lua` | Main entry point that defines all Q-SYS lifecycle functions and includes all other Lua files via `#include` directives. |
| `info.lua` | Declares the `PluginInfo` table with plugin metadata: Name, Version, BuildVersion, GUID, Author, and Description. |
| `properties.lua` | Defines user-configurable properties by inserting entries into the `props` table (inserted into `GetProperties`). |
| `controls.lua` | Defines all plugin controls by inserting entries into the `ctrls` table (inserted into `GetControls`). |
| `layout.lua` | Defines visual positioning and styling of controls in Q-SYS Designer UI (inserted into `GetControlLayout`). Uses `PageNames` and `props["page_index"]` for multi-page layouts. |
| `runtime.lua` | Contains all runtime logic: component references, variables, functions, event handlers, and initialization code. Executes on the Q-SYS Core when the design is running. |
| `pages.lua` | Iterates `PageNames` to build the pages table for multi-page plugin layouts (inserted into `GetPages`). |
| `model.lua` | Defines model variants for the plugin based on `props.Model` property (inserted into `GetModel`). |
| `components.lua` | Declares embedded Q-SYS components used within the plugin (inserted into `GetComponents`). Leave empty if not needed. |
| `pins.lua` | Declares external pins on the plugin block not tied to a control (inserted into `GetPins`). Leave empty if not needed. |
| `wiring.lua` | Defines wiring connections between embedded components (inserted into `GetWiring`). Leave empty if not needed. |
| `rectify_properties.lua` | Adjusts property visibility/availability based on current property values (inserted into `RectifyProperties`). Leave empty if not needed. |

## How It Works

`plugin.lua` is the **entry point and orchestrator**. It defines every Q-SYS plugin lifecycle function and delegates each one to a separate `.lua` file using `--[[ #include "filename.lua" ]]`. At compile time, the compiler resolves these include directives and produces a monolithic `.qplug` file that Q-SYS Designer can load.

### Two Execution Phases

1. **Design-time**: Q-SYS Designer calls `GetProperties`, `GetControls`, `GetControlLayout`, etc. to render the plugin. Controls cannot be created dynamically at runtime — they must all be pre-defined.
2. **Runtime**: When deployed to a Q-SYS Core, the `if Controls then` block at the bottom of `plugin.lua` executes, which includes `runtime.lua`.

## plugin.lua Template

Use this exact structure for `plugin.lua`:

```lua
-- Plugin Name
-- by Author Name
-- Date

-- Information block for the plugin
--[[ #include "info.lua" ]]

-- Define the color of the plugin object in the design
function GetColor(props)
  return { 102, 102, 102 }
end

-- The name that will initially display when dragged into a design
function GetPrettyName(props)
  return "Plugin Display Name, version " .. PluginInfo.Version
end

-- Optional function used if plugin has multiple pages
PageNames = { "Control" }  --List the pages within the plugin
function GetPages(props)
  local pages = {}
  --[[ #include "pages.lua" ]]
  return pages
end

-- Optional function to define model if plugin supports more than one model
function GetModel(props)
  local model = {}
  --[[ #include "model.lua" ]]
 return model
end

-- Define User configurable Properties of the plugin
function GetProperties()
  local props = {}
  --[[ #include "properties.lua" ]]
  return props
end

-- Optional function to define pins on the plugin that are not connected to a Control
function GetPins(props)
  local pins = {}
  --[[ #include "pins.lua" ]]
  return pins
end

-- Optional function to update available properties when properties are altered by the user
function RectifyProperties(props)
  --[[ #include "rectify_properties.lua" ]]
  return props
end

-- Optional function to define components used within the plugin
function GetComponents(props)
  local components = {}
  --[[ #include "components.lua" ]]
  return components
end

-- Optional function to define wiring of components used within the plugin
function GetWiring(props)
  local wiring = {}
  --[[ #include "wiring.lua" ]]
  return wiring
end

-- Defines the Controls used within the plugin
function GetControls(props)
  local ctrls = {}
  --[[ #include "controls.lua" ]]
  return ctrls
end

--Layout of controls and graphics for the plugin UI to display
function GetControlLayout(props)
  local layout = {}
  local graphics = {}
  --[[ #include "layout.lua" ]]
  return layout, graphics
end

--Start event based logic
if Controls then
  --[[ #include "runtime.lua" ]]
end
```

## File Content Details

### info.lua

**IMPORTANT:** Every plugin must have a unique `Id` in UUID/GUID format. When creating `info.lua`, you MUST generate a random unique ID in the format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` where each `x` is a random hexadecimal character (0-9, a-f). Make every digit truly random — do not reuse patterns or use obvious sequences. Each plugin must get a different ID.

```lua
PluginInfo = {
  Name = "Plugin Name",
  Version = "1.0.0",
  BuildVersion = "1.0.0.0",
  Id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  -- unique random GUID per plugin
  Author = "Author Name",
  Description = "Description of what the plugin does"
}
```

### properties.lua
Insert property definitions into the `props` table. Available property types: `string`, `integer`, `double`, `boolean`, `enum`.
```lua
table.insert(props, {
  Name = "Property Name",
  Type = "enum",
  Choices = {"Option1", "Option2", "Option3"},
  Value = "Option1"  -- default value
})
```

### controls.lua
Insert control definitions into the `ctrls` table. ControlType options: `Button`, `Knob`, `Indicator`, `Text`, `Meter`, `Header`.

**Single controls:**
```lua
table.insert(ctrls, {
  Name = "My Control",
  ControlType = "Button",
  ButtonType = "Toggle",    -- Toggle, Trigger, On, Off, Custom
  Count = 1,
  UserPin = true,           -- expose as a pin
  PinStyle = "Both",        -- Input, Output, Both, None
})
```

**Arrays of controls — IMPORTANT:** Do NOT use `Count` > 1 to create multiple instances of a control. Instead, use a property-driven loop to create individually named controls. This avoids the confusing space-separated auto-numbering (`"Button 1"`, `"Button 2"`) and keeps indexing consistent across controls.lua, layout.lua, and runtime.lua.

```lua
-- First define a count property in properties.lua:
table.insert(props, {
  Name = "Channel Count",
  Type = "integer",
  Value = 4,
  Min = 1,
  Max = 32
})

-- Then in controls.lua, loop to create individual controls:
local channelCount = props["Channel Count"].Value
for i = 1, channelCount do
  table.insert(ctrls, {
    Name = "Mute" .. i,
    ControlType = "Button",
    ButtonType = "Toggle",
    Count = 1,
    UserPin = true,
    PinStyle = "Both"
  })
  table.insert(ctrls, {
    Name = "Volume" .. i,
    ControlType = "Knob",
    ControlUnit = "dB",
    Min = -100,
    Max = 20,
    Count = 1,
    UserPin = true,
    PinStyle = "Both"
  })
end
```

This creates controls named `"Mute1"`, `"Mute2"`, `"Volume1"`, `"Volume2"`, etc. — simple concatenated names with no spaces before the index number.

### layout.lua
Position controls using a `layout` table keyed by control name. Uses `props["page_index"]` for multi-page support.

**Visual Design Requirements — Every plugin layout MUST follow these rules:**

1. **Include the build version in the bottom left of each plugin**
1. **Use a dark background GroupBox** as the plugin canvas (first graphic, lowest ZOrder)
2. **Group related controls** inside lighter GroupBox sections with descriptive titles
3. **Use Header graphics** to label major sections
4. **Use Label graphics** next to every control so users know what each control does
5. **Ensure text contrast** — use light text (`{255,255,255}` or `{221,221,221}`) on dark backgrounds, dark text (`{0,0,0}`) on light backgrounds
6. **Color buttons meaningfully** — e.g., green for connect/enable, red for disconnect/stop, blue for actions, gray for settings
7. **Use `UnlinkOffColor`** on toggle buttons so on/off states are visually distinct (e.g., green on, dark gray off)
8. **Set `ButtonVisualStyle = "Flat"`** for a modern, clean look
9. **Set `CornerRadius`** on buttons (4–8px) and GroupBoxes (8px) for rounded edges
10. **Use consistent spacing** — align controls on a grid, use uniform padding (10px from GroupBox edges, 5px between controls)
11. **Set `FontSize`** appropriately — 14+ for headers, 11–12 for labels, 10 for small status text
12. **Use the `Legend` property** on buttons to label them instead of relying on separate text labels
13. **Use `Icon` on buttons** when applicable — e.g., `Icon = "Power"` for power buttons in the control definition (`controls.lua`)
14. **Status indicators** should use LED style with colored on/off states
15. **Size controls appropriately** — buttons at least `{80, 24}`, text fields at least `{150, 24}`, LEDs `{16, 16}`

**Available layout Style values:** `"Fader"`, `"Knob"`, `"Button"`, `"Text"`, `"Meter"`, `"Led"`, `"ListBox"`, `"ComboBox"`, `"Media"`, `"None"`

**Available graphic Type values:** `"Label"`, `"GroupBox"`, `"Header"`, `"Image"`, `"Svg"`

**Available fonts:** `"Roboto"` (default), `"Montserrat"`, `"Open Sans"`, `"Lato"`, `"Poppins"`, `"Roboto Mono"` (monospace), `"Noto Serif"`, `"Roboto Slab"`

**Example of a well-styled layout:**
```lua
local CurrentPage = PageNames[props["page_index"].Value]

if CurrentPage == "Control" then
  -- Plugin background
  table.insert(graphics, {
    Type = "GroupBox",
    Fill = { 35, 35, 35 },
    StrokeColor = { 35, 35, 35 },
    StrokeWidth = 0,
    CornerRadius = 0,
    Position = { 0, 0 },
    Size = { 400, 300 },
    ZOrder = -10
  })

  -- Connection section group
  table.insert(graphics, {
    Type = "GroupBox",
    Text = "Connection",
    Fill = { 55, 55, 55 },
    Color = { 221, 221, 221 },
    StrokeColor = { 80, 80, 80 },
    StrokeWidth = 1,
    CornerRadius = 8,
    Font = "Roboto",
    FontSize = 11,
    Position = { 10, 10 },
    Size = { 380, 80 },
    ZOrder = -5
  })

  -- IP Address label
  table.insert(graphics, {
    Type = "Label",
    Text = "IP Address",
    Color = { 200, 200, 200 },
    FontSize = 11,
    Font = "Roboto",
    HTextAlign = "Right",
    Position = { 20, 35 },
    Size = { 80, 24 }
  })

  -- IP Address text field
  layout["IPAddress"] = {
    PrettyName = "Connection~IP Address",
    Style = "Text",
    Position = { 105, 35 },
    Size = { 150, 24 },
    FontSize = 11,
    Color = { 255, 255, 255 },
    CornerRadius = 4
  }

  -- Connect button (green on, dark off)
  layout["Connect"] = {
    PrettyName = "Connection~Connect",
    Style = "Button",
    ButtonStyle = "Toggle",
    ButtonVisualStyle = "Flat",
    Position = { 270, 35 },
    Size = { 100, 24 },
    Color = { 0, 180, 80 },
    OffColor = { 80, 80, 80 },
    UnlinkOffColor = true,
    Legend = "Connect",
    FontSize = 12,
    CornerRadius = 4
  }

  -- Status LED
  layout["Status"] = {
    PrettyName = "Connection~Status",
    Style = "Led",
    Position = { 20, 60 },
    Size = { 16, 16 },
    Color = { 0, 255, 0 },
    OffColor = { 100, 0, 0 },
    UnlinkOffColor = true
  }

  -- Section header
  table.insert(graphics, {
    Type = "Header",
    Text = "Controls",
    Color = { 221, 221, 221 },
    Font = "Roboto",
    FontSize = 14,
    FontStyle = "Bold",
    HTextAlign = "Left",
    Position = { 10, 100 },
    Size = { 380, 20 }
  })
end
```

**Looped control layout — when using control arrays:**
```lua
local channelCount = props["Channel Count"].Value
for i = 1, channelCount do
  layout["Volume" .. i] = {
    PrettyName = string.format("Channel~Volume %i", i),
    Style = "Fader",
    Position = { 20 + (60 * (i - 1)), 50 },
    Size = { 50, 200 }
  }
  layout["Mute" .. i] = {
    PrettyName = string.format("Channel~Mute %i", i),
    Style = "Button",
    Position = { 20 + (60 * (i - 1)), 260 },
    Size = { 50, 24 }
  }
end
```

### runtime.lua

#### TCP/UDP/Serial Recommended Practices

When a plugin communicates with a device via TCP, UDP, or Serial, follow these recommended practices:

- **TCP Client**: Set `TCP.ReadTimeout = 0` and `TCP.WriteTimeout = 0` (disabled) by default. Only set non-zero timeout values for TCP servers. Use `TCP.ReconnectTimeout = 5` for auto-reconnect. Always define all event handlers: `.Connected`, `.Reconnect`, `.Data`, `.Closed`, `.Error`, `.Timeout`.
- **UDP**: UDP has no built-in buffer — implement manual buffering if messages can arrive incomplete. Use `UdpSocket.New()` and open with `UDP:Open(nil, port)`.
- **Serial**: Always delay serial port open with `Timer.CallAfter(fn, 1)` and wrap in `pcall`. Define `.Connected`, `.Data`, `.Error` handlers.

#### Using Gathered Protocol Information

If protocol discovery was performed (see "Protocol & Command Discovery" section), use the confirmed command set to generate:
- **Command functions** — dedicated `Send` functions or a command dispatch table using the exact command strings/bytes from the protocol spec
- **Response parsing** — parse handlers that match the device's actual response format (delimiters, acknowledgments, status strings)
- **Polling logic** — use the correct status query commands identified during discovery
- **Error handling** — handle device-specific error codes or NAK responses

Do **not** guess or invent commands. Use only what was confirmed by the user or found in the protocol documentation.

#### Control Array Event Handlers

When the plugin uses looped control arrays (created via property-driven loops in controls.lua), set up event handlers with matching loops in runtime.lua:
```lua
local numChannels = Properties["Channel Count"].Value
for i = 1, numChannels do
  Controls["Mute" .. i].EventHandler = function(ctl)
    print("Mute " .. i .. " = " .. tostring(ctl.Boolean))
    Send("MUTE " .. i .. " " .. (ctl.Boolean and "1" or "0") .. "\r")
  end
  Controls["Volume" .. i].EventHandler = function(ctl)
    print("Volume " .. i .. " = " .. tostring(ctl.Value))
    Send("VOL " .. i .. " " .. tostring(math.floor(ctl.Value)) .. "\r")
  end
end
```

The control names (`"Mute1"`, `"Volume1"`, etc.) must match exactly between controls.lua, layout.lua, and runtime.lua.

Structure your runtime logic with clear sections:
```lua
--[[ Description
    Describe the plugin's runtime behavior
]]

--------------------
-- Components ------
--------------------
-- End Components --

--------------------
-- Variables -------
--------------------
-- End Variables ---

--------------------
-- Functions -------
--------------------
-- End Functions ---

--------------------
-- EventHandlers ---
--------------------
--End Eventhandlers-

-- Initialize --
```

#### Debug Logging

Every plugin that communicates with a device (TCP, UDP, Serial, HTTP, SSH) **must** include debug print statements. This is essential for troubleshooting in the field. Add prints for:

1. **Commands sent** — print what is being transmitted to the device
2. **Responses received** — print what comes back from the device
3. **Errors** — print any error conditions (socket errors, parse failures, timeouts, pcall failures)
4. **Connection state changes** — print connect, disconnect, reconnect events

```lua
-- In socket/serial data handlers:
function ParseResponse(data)
  print("RX: " .. data)
  -- parsing logic...
end

-- When sending commands:
function Send(cmd)
  print("TX: " .. cmd)
  TCP:Write(cmd .. "\r\n")
end

-- In error/state handlers:
TCP.Connected = function()
  print("Connected to " .. Properties["IP Address"].Value)
end

TCP.Error = function(sock, err)
  print("Socket Error: " .. err)
end

TCP.Timeout = function()
  print("Socket Timeout")
end

TCP.Closed = function()
  print("Socket Closed")
end

-- Wrap risky operations:
local ok, err = pcall(function() TCP:Connect(host, port) end)
if not ok then
  print("Connection Error: " .. err)
end
```

Keep logging concise — no verbose dumps of every variable, just enough to trace command flow and diagnose issues.

### pages.lua
```lua
for ix,name in ipairs(PageNames) do
  table.insert(pages, {name = PageNames[ix]})
end
```

### model.lua
```lua
if props.Model ~= nil and props.Model.Value ~= "" then
  table.insert(model, { props.Model.Value } )
else
  table.insert(model, { "Base Model" } )
end
```

### rectify_properties.lua
```lua
-- Example: hide Debug Print property when not needed
if props.plugin_show_debug.Value == false then
  props["Debug Print"].IsHidden = true
end
```

## Creation Order

Follow this order to ensure dependencies are satisfied:

0. **Protocol discovery** — Gather device commands/responses if the plugin communicates with a device (see "Protocol & Command Discovery" section above)
1. **info.lua** — Plugin metadata (no dependencies)
2. **properties.lua** — Properties (no dependencies)
3. **controls.lua** — Controls (may reference property names for Count)
4. **pages.lua** — Page definitions (references `PageNames` from plugin.lua)
5. **layout.lua** — Layout (references control names from controls.lua, page names from plugin.lua)
6. **runtime.lua** — Runtime logic (references control names from controls.lua, property names from properties.lua)
7. **model.lua** — Model variants (usually static)
8. **plugin.lua** — Orchestrator (references `PageNames`, includes all files)
9. **components.lua**, **pins.lua**, **wiring.lua**, **rectify_properties.lua** — Supporting files as needed

## Consistency Checklist

Before finishing, verify:

- [ ] Every `Controls["..."]` reference in `runtime.lua` has a matching entry in `controls.lua`
- [ ] Every control defined in `controls.lua` has a layout entry in `layout.lua`
- [ ] Every `Properties["..."]` or `props["..."]` reference has a matching definition in `properties.lua`
- [ ] `PageNames` in `plugin.lua` matches the pages handled in `layout.lua`
- [ ] No Q-SYS reserved control names or function names are used
- [ ] All `table.insert` calls target the correct local variable (`ctrls`, `props`, `pages`, etc.)
- [ ] Control arrays use property-driven loops (not `Count` > 1) with matching names across controls.lua, layout.lua, and runtime.lua
- [ ] Looped control names are consistent (e.g., `"Mute" .. i` produces `"Mute1"`, `"Mute2"` — same pattern in all files)

## Output Summary (IMPORTANT)

**Code blocks are hidden from the user in the chat.** The user will only see your plain text. Code blocks are still captured by the server for ZIP packaging, but the user cannot see them.

After outputting all files, you MUST provide a clear summary that includes:

1. **Plugin name** and brief description
2. **Files created** — list each `.lua` file
3. **Key features** — controls, pages, and functionality implemented
4. **Connection details** — protocol, default port, delimiter, etc.
5. **Controls summary** — list the main controls (buttons, knobs, indicators, text fields)
6. **How to use** — brief instructions for loading in Q-SYS Designer

Keep the summary concise but informative. This is the only thing the user sees in the chat — make it count.

The ZIP download will include all source files and a compiled `.qplug` file ready for Q-SYS Designer. The server compiles the plugin automatically.
