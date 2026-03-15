# Create Q-SYS Plugin

Create a complete Q-SYS plugin based on the following description:

**$ARGUMENTS**

## Plugin Name

The user provides a plugin name in the form. Use this name for:
- `PluginInfo.Name` in `info.lua`
- `GetPrettyName()` display string in `plugin.lua`

## Creation Order

Follow this order to ensure dependencies are satisfied:

0. **Protocol discovery** — Gather device commands/responses if the plugin communicates with a device (see the Protocol Discovery skill)
1. **info.lua** — Plugin metadata (no dependencies)
2. **properties.lua** — Properties (no dependencies)
3. **controls.lua** — Controls (may reference property names for Count)
4. **pages.lua** — Page definitions (references `PageNames` from plugin.lua)
5. **layout.lua** — Layout (references control names from controls.lua, page names from plugin.lua)
6. **runtime.lua** — Runtime logic (references control names from controls.lua, property names from properties.lua)
7. **model.lua** — Model variants (usually static)
8. **plugin.lua** — Orchestrator (references `PageNames`, includes all files)
9. **components.lua**, **pins.lua**, **wiring.lua**, **rectify_properties.lua** — Supporting files as needed

## Output Summary Fields

After outputting all files, provide a summary including:

1. **Plugin name** and brief description
2. **Files created** — list each `.lua` file
3. **Key features** — controls, pages, and functionality implemented
4. **Connection details** — protocol, default port, delimiter, etc.
5. **Controls summary** — list the main controls (buttons, knobs, indicators, text fields)
6. **How to use** — brief instructions for loading in Q-SYS Designer
