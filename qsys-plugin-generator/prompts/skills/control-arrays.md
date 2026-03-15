# Control Arrays

**IMPORTANT:** Do NOT use `Count` > 1 to create multiple instances of a control. Instead, use a property-driven loop to create individually named controls. This avoids the confusing space-separated auto-numbering (`"Button 1"`, `"Button 2"`) and keeps indexing consistent across controls.lua, layout.lua, and runtime.lua.

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

## Looped Layout Positioning

When using control arrays, position them with matching loops in layout.lua:
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

## Looped Event Handlers

Set up event handlers with matching loops in runtime.lua:
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
