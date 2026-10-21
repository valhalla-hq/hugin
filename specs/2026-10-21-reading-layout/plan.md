# Approach

Keep native Tk/SoftButton and existing branding. Render the reading panel on one
bounded canvas surface; composite each button over its actual gradient crop and
inset native text/scroll controls inside a rounded text area. Clip the owned
native window to rounded geometry with explicit GDI region ownership.

ReadingPanel owns session coordinates and header drag state. PanelPlacement owns
native no-activation moves and monitor selection from a supplied rectangle,
falling back to the foreground only before the first placement. A pure geometry
function clamps the remembered position and size to the selected work area.
Keep redraw/region creation tied to changed size, not pointer motion.
If native region transfer and deletion both fail, keep the untransferred handle
on PanelPlacement and retry at explicit window cleanup; do not discard ownership.

Move the existing visibility control into the main reading card, reserve a third
row and rebalance compact hero/minimum scaling to preserve the text area. Reuse
the existing optional-panel failure boundary for drag errors. No storage migration.

The live 9d6273f pilot and a7404d8 worker source remain frozen. Work in an exclusive
worktree; save/review/check/merge before a normal user-controlled restart. The
original Whispering/PipPal return shortcuts and retained source are the return path.
