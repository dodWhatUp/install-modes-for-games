"""Exact inactive diagnostics and deferred host logs; no actual input/GUI."""
from pathlib import Path
import configparser,importlib.util,os,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
spec=importlib.util.spec_from_file_location('overlay_fixture',Path(__file__).with_name('Test-GameToolOverlay.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class LiveDiagnostics(unittest.TestCase):
    def test_inactive_relay_explains_reason_without_arming_or_extending_ttl(self):
        with tempfile.TemporaryDirectory(prefix='OverlayInactiveFixture-') as tmp:
            root=Path(tmp);_,manifest=fixture.fixture(root);store=api.Store(root/'store')
            store.import_manifest(manifest,'absent')
            api.relay(store,{'render':False,'reason':'Native observation Stale; refusing action map'},root/'relay',now=100)
            config=configparser.ConfigParser();config.read(root/'relay/overlay-selection.ini');row=config['Overlay']
            self.assertEqual(row['Active'],'0');self.assertEqual(row['ExpiresUnixMs'],'101000')
            self.assertEqual(row['StatusReason'],'Native observation Stale; refusing action map')
            self.assertNotIn('File',row)

    def test_reason_is_bounded_single_line(self):
        with tempfile.TemporaryDirectory(prefix='OverlayInactiveFixture-') as tmp:
            root=Path(tmp);_,manifest=fixture.fixture(root);store=api.Store(root/'store');store.import_manifest(manifest,'absent')
            api.relay(store,{'render':False,'reason':'reason\n\r'+'x'*300},root/'relay',now=100)
            config=configparser.ConfigParser();config.read(root/'relay/overlay-selection.ini');reason=config['Overlay']['StatusReason']
            self.assertEqual(len(reason),200);self.assertNotIn('\n',reason);self.assertNotIn('\r',reason)

    @unittest.skipUnless(os.name=='nt','Headless Windows AHK')
    def test_actual_host_log_defers_widget_updates_and_keeps_bounded_events(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/'examples/game-input/AzeronOverlayStudio.integrated.ahk').read_text(encoding='utf-8-sig')
        methods=source[source.index('    WriteLog(message) {'):source.index('    CopyDiagnostics(*) {')]
        fixture_source='''#Requires AutoHotkey v2.0
#SingleInstance Off
class LogFixture {
    __New() {
        this.LogLines:=[],this.Gui:=true,this.Writes:=0
        this.LogEdit:={}
    }
'''+methods+'''
}
RunLog() {
    h:=LogFixture()
    Critical("On")
    Loop 80
        h.WriteLog("overlay event " A_Index)
    Critical("Off")
    if h.LogLines.Length!=70 || !h.LogDirty || h.LogEdit.HasOwnProp("Value")
        throw Error("Hotkey log performed a synchronous widget update or lost its bound")
    if !RegExMatch(h.LogLines[1],"^\\[[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{3}\\]")
        throw Error("Millisecond event timestamp absent")
    h.RefreshLogField()
    if h.LogDirty || !InStr(h.LogEdit.Value,"overlay event 80")
        throw Error("Explicit status refresh lost latest events")
    FileAppend("PASS deferred actual-host log checks`n","*")
    ExitApp(0)
}
try RunLog()
catch as issue {
    FileAppend("FAIL " issue.Message " line " issue.Line,"*")
    ExitApp(1)
}
'''
        with tempfile.TemporaryDirectory(prefix='OverlayLogFixture-') as tmp:
            script=Path(tmp)/'log.ahk';script.write_text(fixture_source,encoding='utf-8-sig')
            ahk=Path(os.environ['LOCALAPPDATA'])/'Programs/AutoHotkey/v2/AutoHotkey64.exe'
            result=subprocess.run([str(ahk),'/ErrorStdOut=UTF-8',str(script)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('PASS deferred',result.stdout)

if __name__=='__main__':unittest.main()
