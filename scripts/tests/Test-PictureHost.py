"""Source-contract checks, separate from native AHK and observed desktop acceptance."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOST = (ROOT / "examples/game-input/AzeronOverlayStudio.integrated.ahk").read_text(encoding="utf-8-sig")
ADAPTER = (ROOT / "examples/game-input/OverlayStudioGameInput.ahk").read_text(encoding="utf-8-sig")
ORIGINAL = "__New NewSlot LoadConfig SaveConfig ValidateAll IsWhole ValidCombo ComboToSend BuildGui BuildTray ShowPanel HidePanel RefreshList SelectSlot ReadSlotFields OnSourceChanged ReadCurrentSlot SaveSlot AddSlot RemoveSlot BrowsePicture RecordKey TestCapture BindAll UnbindAll KeyDown KeyUp ShowSlot ShowLocal ShowMIC HideCurrent HideAll ArmHide Expire TestSlot TogglePaused SaveMicShortcut ManualMicToggle MarkMicHidden LoadHudFields ValidateHud SaveHud StartKeyDisplay StopKeyDisplay HudDownEvent HudUpEvent AddHudEntry TestHud ClearHud DestroyHUD HudRefresh Tick RefreshStatus WriteLog RefreshLogField CopyDiagnostics OpenGuide ImportLegacy AddMicPreset Shutdown".split()


def method(name):
    start = re.search(rf"(?m)^    {re.escape(name)}\([^\n]*\) \{{", HOST)
    if not start:
        raise AssertionError(f"Missing method: {name}")
    end = re.search(r"(?m)^    }$", HOST[start.end():])
    return HOST[start.start():start.end() + end.end()]


class PictureHostContracts(unittest.TestCase):
    def test_original_methods_retained(self):
        found = set(re.findall(r"(?m)^    (\w+)\([^\n]*\) \{", HOST))
        self.assertEqual(len(ORIGINAL), 60)
        self.assertFalse(set(ORIGINAL) - found)

    def test_original_tabs_and_optional_input_retained(self):
        for label in ["1. Picture buttons", "2. Multi Image Canvas", "3. Key display", "4. Status / log", "5. Game Input"]:
            self.assertIn(label, method("BuildGui"))
        self.assertIn("this.Module := false", ADAPTER)

    def test_preview_is_detached_from_save_bind_and_mic(self):
        preview = method("TestSlot")
        self.assertIn("this.ReadCurrentSlot()", preview)
        self.assertIn("this.Pictures.RenderPreview(this.Selected, s)", preview)
        self.assertNotIn("this.SaveConfig()", preview)
        self.assertNotIn("this.BindAll()", preview)
        local_branch = preview.split("; MIC is", 1)[0]
        self.assertNotIn("this.ShowSlot", local_branch)
        self.assertNotIn("Send", local_branch)

    def test_render_and_trigger_use_resolved_appearance(self):
        for name in ["ShowSlot", "KeyDown"]:
            self.assertIn("this.Pictures.ResolveSlot(i, 0, true)", method(name))
        self.assertIn("this.Pictures.Geometry(s)", method("ShowLocal"))

    def test_routing_refuses_safely_and_resolves_once_per_down(self):
        down, show = method("KeyDown"), method("ShowSlot")
        self.assertIn("this.ShowSlot(i, s)", down)
        for body in [down, show]:
            self.assertIn("catch Error as err", body)
            self.assertIn("PICTURE ROUTING REFUSED", body)
        self.assertNotIn("ResolveSlot", method("KeyUp"))

    def test_hold_release_uses_down_snapshot(self):
        self.assertIn("{Token: token, Mode: s.Mode}", method("KeyDown"))
        self.assertIn('pressed.Mode = "Hold"', method("KeyUp"))

    def test_identity_change_notifications(self):
        self.assertIn("this.Pictures.LegacyChanged(this.Selected)", method("SaveSlot"))
        self.assertIn("this.Pictures.LegacyChanged(index, false, true)", method("AddMicPreset"))
        for name in ["RemoveSlot", "ImportLegacy"]:
            self.assertIn("this.Pictures.LegacyChanged(0, true)", method(name))

    def test_fixture_root_is_bounded_prepared_nonlinked(self):
        init = method("__New")
        for guard in ["A_Args.Length != 2", "StrLower(parent)", "^StudioPictureUiFixture-[a-f0-9]{32}$", "GetFileAttributesW", "attributes & 0x400"]:
            self.assertIn(guard, init)
        self.assertIn('this.DesktopTest := false', init)

    def test_fixture_never_activates_input_or_external_shortcuts(self):
        for name in ["BindAll", "StartKeyDisplay", "RecordKey", "ShowMIC", "ManualMicToggle"]:
            self.assertIn("this.DesktopTest", method(name))
        self.assertIn("this.Host.DesktopTest", ADAPTER)

    def test_cleanup_preview_and_module(self):
        for name in ["HideAll", "TogglePaused"]:
            self.assertIn("this.Pictures.Suspend()", method(name))
        self.assertIn("this.Pictures.Shutdown()", method("Shutdown"))
        self.assertIn("this.GameInput.StopForHost()", method("Shutdown"))

    def test_add_does_not_silently_discard_draft(self):
        self.assertIn("this.ConfirmDiscardDraft()", method("AddSlot"))


if __name__ == "__main__":
    unittest.main()
