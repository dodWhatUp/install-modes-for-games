# Windows app access and identity

Unified Game Tools and the maintained standalone apps have stable, separate
AppUserModelIDs and authored game-controller icons. The same identity belongs
on their Desktop, included APP LAUNCHER and Start-menu shortcuts. The Python
runtime and existing stable entry paths remain shared infrastructure.

Use the **−** button to minimize the window. Click its taskbar icon or open its
APP LAUNCHER again to restore that same window and draft. Use **×** to close
through the existing app close guard. Busy operations, pending-draft prompts
and Unified Studio shutdown retain their owners. At narrow widths these extra
buttons move out of the compact header; the same named actions remain under
Tools, alongside the standard Windows title-bar controls.

The launcher's restore request does not apply settings, switch native profiles,
publish an Overlay or open a second editor. Each app/installation scope owns
its own named Windows restore event. Unified keeps its earlier mutex name for
compatibility. Opening an older already-running version requires its normal
close before the new restoration behavior can be used.

Start registration adds user shortcuts to the existing Programs directory and
does not replace the Start layout or any unrelated pins. Search for the app's
display name, for example **Unified Game Tools**. Pinning uses the normal
Windows **Pin to Start** action; record actual native acceptance separately
from shortcut file verification. A Start entry alone is not proof of a pin.

The runtime has no third-party icon or shell package dependency. Icon generation
uses Pillow only at source-authoring time; `.svg`, `.png` and multi-size `.ico`
files are included as authored UI assets. `GameToolWindowsShortcut` uses Windows
ShellLink and PropertyStore APIs, verifies target/arguments/icon/AppUserModelID,
and requires the exact baseline before changing an existing shortcut.

Microsoft documents [matching process and shortcut identities](https://learn.microsoft.com/en-us/windows/win32/shell/appids)
and the normal [Pin to Start interaction](https://learn.microsoft.com/en-us/windows/configuration/start/layout).
Keep source/fixture/native acceptance distinct; native receipts and settings
backups stay private.
