# Plan

Original execution plan follows; all build/installation checks are completed.
Final checked private source integration and cleanup retain separate receipts.

Reuse the already accepted40365-file1.0.2 payload after rechecking its complete
manifest. Pin recipe/tools to the artifact source3fd3ca9 (identical to Main772bf1e
for packaging/tools). Generate an explicit Inno file list; never wildcard a live
candidate tree. Keep installer evidence separate from the historic app-only
receipt and do not modify the running payload. Avoid rebuilding identical
11.6GB runtimes/models or starting the GPU.

Compiler provisioning was denied even after explicit human consent.
Prepare all inputs and local package/setup tests; wait for a user-installed
trusted compiler in a permanent directory. Then use the existing Inno recipe,
record signatures/version/hash, compile new outputs, and verify the unchanged
source payload and installer slice hashes.

Executed: Brian installed the compiler at C:/Program Files/Inno Setup 7.
Version/signature/trusted hash pass. Compilation completed exit0 with five
hashed files and an unchanged verified payload. After normal Hugin Quit the
guarded upgrade completed exit0; state/shortcut/uninstall readback, installed
profile/input probe and two hidden normal starts pass. The exact installed
startup command is running. Compiler provisioning is no longer a dependency.

After normal Hugin Quit, run the existing installer upgrade into its own root.
Compare active-candidate versus previous-installed voice before migration;
preserve the current user choice explicitly if they differ. Verify activation,
shortcut backup and target, Start-menu/uninstall ownership and normal repeated
hidden input starts. Launch the installed app. Actual login stays untested until
Brian chooses to perform it. Bundle source evidence/checkpoints; keep CI gates
but avoid unnecessary hosted reruns within the shared quota.
