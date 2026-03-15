# Connection Settings as Runtime Controls (IMPORTANT)

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
