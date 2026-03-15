# Plugin File Specifications

You are responsible for creating and populating **every** `.lua` file listed below. None are pre-filled or auto-generated. You must author each one with the correct content for this specific plugin.

## Required Files

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
