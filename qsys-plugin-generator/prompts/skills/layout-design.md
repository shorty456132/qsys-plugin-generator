# Layout Design

Position controls using a `layout` table keyed by control name. Uses `props["page_index"]` for multi-page support.

## Visual Design Requirements — Every plugin layout MUST follow these rules:

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

## Available Values

**Layout Style values:** `"Fader"`, `"Knob"`, `"Button"`, `"Text"`, `"Meter"`, `"Led"`, `"ListBox"`, `"ComboBox"`, `"Media"`, `"None"`

**Graphic Type values:** `"Label"`, `"GroupBox"`, `"Header"`, `"Image"`, `"Svg"`

**Available fonts:** `"Roboto"` (default), `"Montserrat"`, `"Open Sans"`, `"Lato"`, `"Poppins"`, `"Roboto Mono"` (monospace), `"Noto Serif"`, `"Roboto Slab"`

## Example of a Well-Styled Layout

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
