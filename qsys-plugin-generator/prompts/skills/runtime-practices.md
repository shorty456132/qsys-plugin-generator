# Runtime Practices

## TCP/UDP/Serial Recommended Practices

When a plugin communicates with a device via TCP, UDP, or Serial, follow these recommended practices:

- **TCP Client**: Set `TCP.ReadTimeout = 0` and `TCP.WriteTimeout = 0` (disabled) by default. Only set non-zero timeout values for TCP servers. Use `TCP.ReconnectTimeout = 5` for auto-reconnect. Always define all event handlers: `.Connected`, `.Reconnect`, `.Data`, `.Closed`, `.Error`, `.Timeout`.
- **UDP**: UDP has no built-in buffer — implement manual buffering if messages can arrive incomplete. Use `UdpSocket.New()` and open with `UDP:Open(nil, port)`.
- **Serial**: Always delay serial port open with `Timer.CallAfter(fn, 1)` and wrap in `pcall`. Define `.Connected`, `.Data`, `.Error` handlers.

## Using Gathered Protocol Information

If protocol discovery was performed, use the confirmed command set to generate:
- **Command functions** — dedicated `Send` functions or a command dispatch table using the exact command strings/bytes from the protocol spec
- **Response parsing** — parse handlers that match the device's actual response format (delimiters, acknowledgments, status strings)
- **Polling logic** — use the correct status query commands identified during discovery
- **Error handling** — handle device-specific error codes or NAK responses

Do **not** guess or invent commands. Use only what was confirmed by the user or found in the protocol documentation.

## Runtime File Structure

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

## Debug Logging

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
  print("Connected to " .. Controls["IPAddress"].String)
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
