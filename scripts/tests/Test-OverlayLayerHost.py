"""Exercise the authored host's actual key-down/up methods with inert fixtures.

No host constructor, hooks, GUI, physical input, Send or native profile writes.
"""
import os, subprocess, tempfile, unittest
from pathlib import Path


@unittest.skipUnless(os.name == "nt", "Headless Windows AHK contract")
class ActualHost(unittest.TestCase):
    def test_mixed_holds_use_actual_key_handlers_without_a_hide_or_recreated_frame(self):
        root = Path(__file__).resolve().parents[2]
        source = (root/"examples/game-input/AzeronOverlayStudio.integrated.ahk").read_text(encoding="utf-8-sig")
        methods = source[source.index("    KeyDown(i, *) {"):source.index("    ShowSlot(i, resolvedSlot := 0) {")]
        fixture = (Path(__file__).with_name("Test-OverlayLayerVisibility.ahk")).read_text(encoding="utf-8-sig").split("RunLayers(image) {")[0]
        fixture = fixture.replace("    WriteLog(*) {", methods + "    WriteLog(*) {")
        fixture = fixture.replace('%A_ScriptDir%\\..\\..\\examples\\game-input\\', str(root/"examples/game-input") + "\\")
        exercise = r'''
class InertPictures {
    __New(host) {
        this.Host := host
    }
    ResolveSlot(i, unused, active) {
        return this.Host.Slots[i].Clone()
    }
}
try {
    host := LayerHost(A_Temp), route := LayerRoute(host, A_Args[1])
    host.GroupRoute := route, host.Pictures := InertPictures(host), host.TotalEvents := 0
    host.Slots[1].Key := "F24", host.Slots[1].Name := "inert", host.Slots[1].PreserveAlpha := true
    route.SetLayer(true), route.Tick()
    hides := host.Hides, shows := host.Shows, generation := host.Generation
    host.KeyDown(1)
    LayerAssert(host.Current = 1 && host.Hides = hides && host.Shows = shows && host.Generation = generation, "Actual key-down must join layer visibility without a hidden frame")
    host.KeyUp(1)
    LayerAssert(host.Current = 1 && host.Hides = hides && host.Pressed.Count = 0, "Actual key-up must keep the native layer visible")
    host.KeyDown(1), route.SetLayer(false), route.Tick()
    LayerAssert(host.Current = 1 && host.Hides = hides, "Releasing the native layer must retain actual key-down ownership")
    host.KeyUp(1)
    LayerAssert(!host.Current && host.Hides = hides + 1, "Last actual key-up hides normally")
    host.KeyDown(1)
    LayerAssert(host.Current = 1, "Dedicated key still opens from BASIC")
    host.KeyUp(1)
    LayerAssert(!host.Current, "Dedicated key alone still hides on release")
    route.Stop()
    FileAppend("PASS 6 actual-host mixed-hold checks; inert display and direct fixture calls only.`n", "*")
    ExitApp(0)
} catch as err {
    FileAppend("FAIL " err.Message " line " err.Line "`n", "**")
    ExitApp(1)
}
'''
        ahk = Path(os.environ["LOCALAPPDATA"])/"Programs/AutoHotkey/v2/AutoHotkey64.exe"
        if not ahk.is_file(): self.skipTest("AHK runtime unavailable")
        import struct,zlib
        def chunk(k,d): return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d))
        with tempfile.TemporaryDirectory(prefix="OverlayActualHost-") as tmp:
            test=Path(tmp)/"fixture.ahk"; test.write_text(fixture+exercise,encoding="utf-8-sig")
            image=Path(tmp)/"fixture.png"
            image.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\xff\xff\xff'))+chunk(b'IEND',b''))
            result=subprocess.run([str(ahk),"/ErrorStdOut",str(test),str(image)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn("PASS 6 actual-host",result.stdout)


if __name__=="__main__":unittest.main()
