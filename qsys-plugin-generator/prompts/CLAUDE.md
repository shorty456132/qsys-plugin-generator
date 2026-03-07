# Q-SYS Plugin Development

This project builds Q-SYS custom plugins for professional audio/video control systems using a modular Lua file structure. Individual `.lua` files are compiled into a single `.qplug` file by resolving `--[[ #include ]]` directives.

## Critical Q-SYS Constraints

### Design-Time vs Runtime
- `GetControls()`, `GetProperties()`, `GetControlLayout()`, and all other lifecycle functions execute at **design-time** in Q-SYS Designer, not at runtime.
- You **cannot** dynamically create controls at runtime. All controls must be pre-defined in `controls.lua`.
- Use `IsInvisible` on pre-generated controls to simulate dynamic UI behavior.
- Design-time functions run in strict order and are **case-sensitive**.
- The `Controls` object only exists at runtime — never reference it in design-time functions.

### Control Indexing & Control Arrays
- Control values are **floats** — convert for string concatenation: `tostring(value)`
- Access control properties: `.Value` (float), `.String` (text), `.Boolean` (bool)
- **Do NOT use `Count` > 1** to create arrays of controls. The `Count` property creates controls with space-separated auto-numbered names (`"Button 1"`, `"Button 2"`) which causes indexing confusion and bugs.
- **Instead, use a property-driven loop** to create individually named controls in `controls.lua`:
```lua
-- In properties.lua: define a property for the count
table.insert(props, {
  Name = "NumIO",
  Type = "integer",
  Value = 2,
  Min = 1,
  Max = 100
})

-- In controls.lua: loop to create individual controls
local NumOfIO = props["NumIO"].Value
for i = 1, NumOfIO do
  table.insert(ctrls, {
    Name = "Input" .. i,
    ControlType = "Button",
    ButtonType = "Trigger",
    Count = 1,
    UserPin = true,
    PinStyle = "Input"
  })
end

-- In layout.lua: loop to position each control
for i = 1, NumOfIO do
  layout["Input" .. i] = {
    PrettyName = string.format("Input %i", i),
    Style = "Button",
    Position = { 25, (30 * i) + 40 },
    Size = { 50, 30 }
  }
end

-- In runtime.lua: loop to set up event handlers
local NumOfIO = Properties["NumIO"].Value
for i = 1, NumOfIO do
  Controls["Input" .. i].EventHandler = function()
    print("Input " .. i .. " triggered")
  end
end
```
- This pattern keeps control names simple (`"Input1"`, `"Input2"`) and consistent across controls.lua, layout.lua, and runtime.lua

### Runtime Environment
- Lua 5.3 runtime with most standard libraries
- Control engine processes at 30 FPS (every 33ms)
- Audio engine processes at 3000 FPS
- Network operations use Q-SYS `TcpSocket` / `UdpSocket` / `HttpClient` / `Ssh` APIs
- Targets Q-SYS Designer 10.1.1+
- `System.IsEmulating` — boolean to detect emulation mode

### Properties
- Properties are **read-only at runtime**: `Properties["My Prop"].Value`
- Types: `string`, `integer`, `double`, `boolean`, `enum`
- `enum` requires a `Choices` array
- Use `RectifyProperties(props)` to show/hide properties dynamically via `IsHidden`
- `Header` and `Comment` fields supported (QDS 9.10+)
- **Do NOT put connection details in properties** — IP addresses, port numbers, device IDs, usernames, and passwords must be runtime-settable Text controls on a Setup page. Properties cannot be changed without editing the design.

## Code Patterns

### EventHandler Setup
```lua
Controls["MyButton"].EventHandler = function(ctl)
  print("Button pressed, value:", ctl.Value)
end
```

### Control Visibility
```lua
Controls["MyControl"].IsInvisible = not shouldShow
```

### Dispatch Tables Over Metatables
Prefer dispatch table patterns for cleaner separation of concerns. Use metatables only when inheritance is truly needed.

### Loop Variable Capture
Always capture loop variables in local variables before using them in closures/EventHandlers:
```lua
for i = 1, count do
  local idx = i  -- capture
  Controls["Button " .. idx].EventHandler = function()
    print("Button " .. idx .. " pressed")
  end
end
```

### TCP Socket
```lua
TCP = TcpSocket.New()
TCP.ReadTimeout = 0   -- disabled; only set non-zero for TCP servers
TCP.WriteTimeout = 0  -- disabled; only set non-zero for TCP servers
TCP.ReconnectTimeout = 5

TCP.Connected = function()
  print("Connected")
end

TCP.Reconnect = function()
  print("Reconnecting...")
end

TCP.Data = function()
  local data = TCP:ReadLine(TcpSocket.EOL.Custom, "\r\n")
  while data do
    ParseResponse(data)
    data = TCP:ReadLine(TcpSocket.EOL.Custom, "\r\n")
  end
end

TCP.Closed = function()
  print("Socket closed")
end

TCP.Error = function(sock, err)
  print("Socket error:", err)
end

TCP.Timeout = function()
  print("Socket timeout")
end

TCP:Connect(host, port)
```

### UDP Socket
```lua
UDP = UdpSocket.New()

UDP.EventHandler = function(udpSocket, packet)
  -- packet.Address, packet.Port, packet.Data
  print("RX from " .. packet.Address .. ": " .. packet.Data)
end

UDP:Open(nil, listenPort)  -- nil IP binds to all interfaces
UDP:Send(targetIP, targetPort, "data")
```

### Serial Port
```lua
MySerialPort = SerialPorts[1]

MySerialPort.Connected = function(port)
  print("Connected")
end

MySerialPort.Data = function(port)
  local data = port:ReadLine(SerialPorts.EOL.Custom, "\r")
  while data do
    ParseResponse(data)
    data = port:ReadLine(SerialPorts.EOL.Custom, "\r")
  end
end

MySerialPort.Error = function(port, err)
  print("Error:", err)
end

-- Delay open to ensure connection is ready
Timer.CallAfter(function()
  local ok, err = pcall(function()
    MySerialPort:Open(115200, 8, "N")
  end)
  if not ok then print("Error opening port:", err) end
end, 1)
```

### HTTP Client
```lua
function GetRequest(url)
  HttpClient.Download({
    Url = url,
    Method = "GET",
    Headers = { ["Content-Type"] = "application/json" },
    Timeout = 10,
    EventHandler = function(tbl, code, data, err, headers)
      if code == 200 then
        print("OK:", data)
      else
        print("Error:", code, err)
      end
    end
  })
end

-- Build URLs with HttpClient.CreateUrl
local url = HttpClient.CreateUrl({
  Host = "https://example.com",
  Port = 443,
  Path = "api/endpoint",
  Query = { key = "value" }
})
```

### SSH
```lua
SSH = Ssh.New()
SSH.ReadTimeout = 5
SSH.WriteTimeout = 5
SSH.ReconnectTimeout = 5

SSH.Connected = function() print("SSH connected") end
SSH.LoginFailed = function() print("SSH login failed") end
SSH.Data = function()
  local rx = SSH:Read(SSH.BufferLength)
  print("RX:", rx)
end

SSH:Connect(ip, 22, username, password)
```

### Heartbeat / Connection Health
Recommended for TCP and Serial to detect dropped connections:
```lua
HeartbeatTimer = Timer.New()
HeartbeatTimeout = 5  -- Must be > poll interval

HeartbeatTimer.EventHandler = function()
  print("Lost communication!")
  Initialize()
end

function ResetHeartbeat()
  HeartbeatTimer:Stop()
  HeartbeatTimer:Start(HeartbeatTimeout)
end

-- Call ResetHeartbeat() on every valid received message
```

### Polling Timer
```lua
PollTimer = Timer.New()
PollTimer.EventHandler = function()
  if TCP.IsConnected then
    TCP:Write("STATUS\r")
  end
end
PollTimer:Start(3)  -- Every 3 seconds
```

### Error Handling (pcall)
Use `pcall` for operations that may fail (socket/port opens, server listen):
```lua
local ok, err = pcall(function()
  server:Listen(Controls.Port.Value)
end)
if ok then
  print("Listening on port " .. tostring(math.floor(Controls.Port.Value)))
else
  print("Listen failed:", err)
end
```

### JSON Handling
```lua
rapidjson = require("rapidjson")
local data = rapidjson.decode(jsonString)
local json = rapidjson.encode(luaTable)
```

### Hex / Binary Data
```lua
-- Byte string to hex display
function BytesToHex(str)
  return str:gsub(".", function(byte)
    return string.format("%02X ", string.byte(byte))
  end)
end

-- Hex string to byte string
function HexToBytes(str)
  return str:gsub("..", function(byte)
    return string.char(tonumber(byte, 16))
  end)
end
```

### Crypto
```lua
Crypto.Base64Encode(data, withPadding)
Crypto.Base64Decode(data)
Crypto.Sha256(data)
Crypto.Hmac("SHA256", data, key)
```

### Named Components
Access existing design components by name:
```lua
local mixer = Component.New("Main Gain")
mixer["input.1.gain"].Value = -6
mixer["input.1.mute"].Boolean = true
```

### Notifications (Script-to-Script)
```lua
-- Publisher
Notifications.Publish("my-channel", dataString)

-- Subscriber
local noteId = Notifications.Subscribe("my-channel", function(id, data)
  print("Received:", data)
end)

-- Unsubscribe
Notifications.Unsubscribe(noteId)
```

### Multi-Page Plugins
```lua
PageNames = { "Control", "Setup" }

function GetPages(props)
  local pages = {}
  for _, name in ipairs(PageNames) do
    table.insert(pages, { name = name })
  end
  return pages
end

function GetControlLayout(props)
  local layout, graphics = {}, {}
  local CurrentPage = PageNames[props["page_index"].Value]

  if CurrentPage == "Control" then
    -- page 1 layout
  elseif CurrentPage == "Setup" then
    -- page 2 layout
  end
  return layout, graphics
end
```

### PrettyName Hierarchy
Use `~` to create nested groups in UCI/pin views:
```lua
layout["Volume 1"] = {
  PrettyName = "Audio~Inputs~Volume 1",
  -- ...
}
```

## Naming Conventions

- **Globals, functions, objects**: PascalCase — `MySocket`, `ParseResponse`
- **Local variables**: camelCase — `myLocalVar`, `bufferData`
- **Control names**: PascalCase with spaces — `"Send Button"`, `"Status Indicator"`
- **Lua is case-sensitive** — `"string"` and `"String"` are different

## Scoping Rules

- **Never declare sockets, timers, or serial ports as `local`** — they will be garbage collected
- Top-level plugin variables should be global (no `local` keyword)
- Use `local` only for temporary variables inside functions and loop iterators
- Socket parameters from `TcpSocketServer.EventHandler()` must be stored globally
- Runtime code lives inside `if Controls then ... end`

## Reserved Control Names

These names have special meaning in Q-SYS and enable built-in features when used:
- `Status` — connection status indicator
- `IPAddress` — IP address input
- `Username` / `Password` — credential inputs
- `MACAddress`, `DeviceName`, `SerialNumber`, `DeviceFirmware` — device info displays

## Reserved Design-Time Functions

All receive `props` parameter (except `GetProperties`):
- `GetColor(props)` — returns `{ R, G, B }` (0–255)
- `GetPrettyName(props)` — display name string
- `GetProperties()` — property definitions table
- `RectifyProperties(props)` — adapt properties dynamically
- `GetPages(props)` — page name table
- `GetControls(props)` — control definitions table
- `GetControlLayout(props)` — returns `layout, graphics` tables
- `GetPins(props)` — audio/serial pin definitions
- `GetComponents(props)` — embedded component definitions
- `GetWiring(props)` — component wiring table

## Control Types Reference

| Type | Required Field | Values |
|------|---------------|--------|
| Button | `ButtonType` | `"Toggle"`, `"Momentary"`, `"Trigger"` |
| Knob | `ControlUnit` | `"dB"`, `"Hz"`, `"Float"`, `"Integer"`, `"Pan"`, `"Percent"`, `"Position"`, `"Seconds"` |
| Indicator | `IndicatorType` | `"Led"`, `"Meter"`, `"Text"`, `"Status"` |
| Text | — | Style set in layout: `"Text"`, `"ComboBox"`, `"ListBox"` |

## Debug Logging

Every plugin that communicates with a device must include debug prints:
- **TX**: Print commands sent to devices — `print("TX: " .. cmd)`
- **RX**: Print responses received — `print("RX: " .. data)`
- **Errors**: Print socket errors, timeouts, parse failures, pcall errors
- **State changes**: Print connect, disconnect, reconnect events

Keep logging concise — trace command flow and diagnose issues, not verbose variable dumps.

## Versioning

- `Version` field uses 3-part format: `"1.0.0"` (Major.Minor.Fix)
- `BuildVersion` field uses 4-part format: `"1.0.0.0"` (Major.Minor.Fix.Development)
- The compiler updates both fields when bumping versions

## Common Pitfalls

1. **Don't create controls at runtime** — pre-generate them in `controls.lua`
2. **Capture loop variables in closures** — use local captures for EventHandlers
3. **Check protocol variations** — TCP vs UDP, manufacturer-specific differences
4. **Validate control references** — ensure controls exist before accessing
5. **Don't use reserved names** — check Q-SYS reserved control names and function names
6. **Never declare sockets/timers as `local`** — they get garbage collected and stop working
7. **UDP has no buffer** — implement manual buffering for incomplete messages
8. **Delay serial port open** — use `Timer.CallAfter(fn, 1)` to ensure connection is ready
9. **Always check `.IsConnected` / `.IsOpen`** before writing to sockets/ports
10. **Wrap risky operations in `pcall`** — socket opens, server listen, port opens
11. **Properties are read-only at runtime** — use `RectifyProperties` for design-time changes only
12. **Dynamic pages require calling helper in both `GetPages` and `GetControlLayout`**

## Documentation Reference

### SDK Help Files
SDK plugin development documentation (API reference, code examples, recommended practices) is located at:
`documents/SDK Help/`

Files are named by category: `Getting_Started-*.md`, `Standards_Definitions-*.md`, `Code_Examples-*.md`, `Recommended_Practices-*.md`, `Development_Tools-*.md`

### General Q-SYS Help Files
Comprehensive Q-SYS platform documentation (hardware, components, networking, schematic library, control scripting, external control APIs, etc.) is located at:
`documents/General Help/`

This includes documentation on all Q-SYS components and features. Key categories include:
- `Schematic_Library-*.md` — All Q-SYS Designer schematic components (mixers, routers, DSP, video, etc.)
- `Control_Scripting-*.md` — Lua scripting API reference for runtime control
- `External_Control_APIs-*.md` — External control protocol references
- `Hardware-*.md` — Q-SYS hardware specifications and capabilities
- `Networking-*.md` — Network configuration and protocols
- `Application_Integration-*.md` — Integration guides for conferencing, AEC, GPIO, etc.
