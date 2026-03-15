# Modify Q-SYS Plugin

You are modifying an existing Q-SYS plugin. The user has provided their current plugin code and a description of the changes they want.

**$ARGUMENTS**

## Workflow

### Step 1: Analyze the Existing Plugin

Before making any changes, analyze the provided plugin code and present a brief summary to the user:

1. **Plugin identity** — Name, version, author, GUID
2. **Communication protocol** — TCP, UDP, Serial, HTTP, SSH, or none
3. **Properties** — List defined properties
4. **Controls** — List all controls (buttons, knobs, indicators, text fields) and any control arrays
5. **Pages** — List page names
6. **Key runtime behavior** — Connection handling, polling, command structure, response parsing

This summary helps you and the user confirm understanding before proceeding.

### Step 2: Confirm the Changes

After your analysis, describe what changes you plan to make based on the user's request. Be specific about:
- Which files will be modified
- What controls, properties, or logic will be added/changed/removed
- Any potential impacts on existing functionality

Ask the user to confirm before generating the modified files.

### Step 3: Output ALL Files

**CRITICAL:** You must output **every** `.lua` file for the plugin — not just the ones you changed. The download ZIP must be a complete, self-contained plugin. If a file does not need changes, output it exactly as provided.

## Handling Uploaded File Formats

### Individual .lua Files
The user uploaded separate `.lua` files. Each file's content is labeled with its filename. Use these directly.

### Compiled .qplug File
The user uploaded a compiled `.qplug` file. This is a single monolithic file where all `--[[ #include "filename.lua" ]]` directives have been resolved inline. You need to:

1. **Read and understand** the compiled structure — identify where each logical section begins (PluginInfo, GetProperties, GetControls, GetControlLayout, runtime block, etc.)
2. **Output individual `.lua` files** — Break the monolith back into the standard modular file structure. The download system compiles from individual files, so you must output separate files.
3. **Maintain the `plugin.lua` template** — Use the standard `plugin.lua` with `#include` directives pointing to each file.

### ZIP of .lua Files
Same as individual `.lua` files — each file is labeled with its filename.

## Preservation Rules

When modifying a plugin, preserve the following unless the user explicitly asks to change them:

- **Plugin GUID** (`Id` in info.lua) — Never change this. It identifies the plugin across deployments.
- **Plugin name and author** — Keep as-is unless requested.
- **Version** — Bump the development version (4th digit) to indicate a modification. For example, `1.0.0.0` → `1.0.0.1`.
- **Existing controls** — Do not remove or rename controls unless the user asks. Adding new controls is fine.
- **Existing properties** — Do not remove or rename unless requested.
- **Layout structure** — Maintain existing page organization, sizing, and color scheme. New controls should follow the existing visual style.
- **Runtime patterns** — Match the existing code style (variable naming, structure, comment patterns).
- **Connection handling** — Keep the existing protocol and connection setup unless explicitly changing it.

## Modification Patterns

### Adding New Controls
1. Add the control definition in `controls.lua`
2. Add layout positioning in `layout.lua` (matching the existing visual style)
3. Add runtime logic (EventHandler, send command, response parsing) in `runtime.lua`
4. Ensure the control name is consistent across all three files

### Adding Control Arrays
Use the property-driven loop pattern (NOT `Count` > 1):
1. Add a count property in `properties.lua` if one doesn't exist
2. Loop to create individual controls in `controls.lua`
3. Loop to position controls in `layout.lua`
4. Loop to set up EventHandlers in `runtime.lua`

### Changing Protocol Behavior
- Modify command functions and response parsing in `runtime.lua`
- Update polling commands if needed
- Keep debug logging (TX/RX prints) for new commands

### Adding Pages
- Add the page name to `PageNames` in `plugin.lua`
- Add a new `elseif CurrentPage == "NewPage" then` section in `layout.lua`
- Position controls for the new page

### Fixing Bugs
- Identify the root cause in the analysis step
- Explain the fix clearly in your summary
- Apply the fix with minimal changes to surrounding code

## Additional Consistency Checks

In addition to the shared consistency checklist, verify:
- [ ] The plugin GUID has NOT been changed
- [ ] The development version has been bumped
- [ ] All original files are included in the output (not just changed ones)

## Output Summary Fields

After outputting all files, provide a summary including:

1. **What was changed** — List each modification made
2. **Files modified** — Which files were changed and what changed in each
3. **Files unchanged** — Briefly note which files were carried over as-is
4. **New version** — The updated version number
5. **Testing notes** — Anything the user should verify or test after loading the modified plugin
