# Consistency Checklist

Before finishing, verify:

- [ ] Every `Controls["..."]` reference in `runtime.lua` has a matching entry in `controls.lua`
- [ ] Every control defined in `controls.lua` has a layout entry in `layout.lua`
- [ ] Every `Properties["..."]` or `props["..."]` reference has a matching definition in `properties.lua`
- [ ] `PageNames` in `plugin.lua` matches the pages handled in `layout.lua`
- [ ] No Q-SYS reserved control names or function names are used incorrectly
- [ ] All `table.insert` calls target the correct local variable (`ctrls`, `props`, `pages`, etc.)
- [ ] Control arrays use property-driven loops (not `Count` > 1) with matching names across controls.lua, layout.lua, and runtime.lua
- [ ] Looped control names are consistent (e.g., `"Mute" .. i` produces `"Mute1"`, `"Mute2"` — same pattern in all files)
- [ ] Control names are consistent across controls.lua, layout.lua, and runtime.lua
