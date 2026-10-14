#Requires AutoHotkey v2.0
#SingleInstance Off
#NoTrayIcon
#Warn All, StdOut
; Native pure-fixture acceptance, not live Studio/game/input acceptance.
; Includes the inert picture module only. Never include the #SingleInstance Force host.
#Include %A_LineFile%\..\..\StudioPictureModule.ahk

PM_Acceptance().Run()

class PM_Acceptance {
    __New() {
        this.Passed := 0
        this.Failed := 0
        this.Results := []
        this.Root := A_Temp "\StudioPictureAcceptance-" DllCall("GetCurrentProcessId", "UInt") "-" A_TickCount
        if DirExist(this.Root)
            throw Error("Unique fixture directory unexpectedly exists.")
        DirCreate(this.Root)
        FileAppend("Isolated authored fixture; no live profiles or user content.`n", this.Root "\FIXTURE-ONLY.txt", "UTF-8")
    }

    Run() {
        try this.RunCases()
        catch Error as err {
            this.Failed += 1
            this.Results.Push("FAIL setup: " err.Message " @ " err.Line)
        }
        try this.Cleanup()
        catch Error as err {
            this.Failed += 1
            this.Results.Push("FAIL safe fixture cleanup: " err.Message)
        }
        for line in this.Results
            FileAppend(line "`n", "*")
        FileAppend("SUMMARY pure-fixture passed=" this.Passed " failed=" this.Failed "`n", "*")
        FileAppend("BOUNDARY No live host, hotkeys, GUI, games, native profiles or real settings exercised.`n", "*")
        ExitApp(this.Failed ? 1 : 0)
    }

    RunCases() {
        this.FirstImage := this.WriteBmp(this.Root "\one.bmp")
        this.SameImage := this.Root "\one-copy.bmp"
        FileCopy(this.FirstImage, this.SameImage)
        this.OtherImage := this.WriteBmp(this.Root "\two.bmp", "00FF0000")
        this.LegacyPath := this.Root "\settings.ini"
        FileAppend("[General]`nSlotCount=2`n[Slot1]`nKey=F7`nEnabled=1`n[Slot2]`nKey=F15`nEnabled=0`n", this.LegacyPath, "UTF-8")
        this.LegacyBytes := FileRead(this.LegacyPath, "RAW")
        first := this.LegacySlot(), first.File := this.FirstImage
        second := this.LegacySlot("Disabled picture", "F15"), second.File := this.OtherImage, second.Enabled := 0
        this.Host := {Slots: [first, second], Dir: this.Root, Config: this.LegacyPath}
        this.BeforeSlots := this.SlotSnapshot(this.Host.Slots)
        this.Module := this.NewModule()
        this.BaseValuesFixture := this.Module.BaseValues(1)

        this.Test("constructor has no sidecar or asset directory effects", () => this.CheckInert())
        this.Test("base resolution preserves legacy values and returns a detached slot", () => this.CheckBase())
        this.Test("unsaved legacy draft resolves without applying or saving", () => this.CheckDraft())
        this.Test("clone recursively detaches maps arrays and objects", () => this.CheckClone())
        this.Test("appearance field list excludes trigger source pass and enable ownership", () => this.CheckFieldOwnership())

        this.Test("pixel sizing preserves aspect ratio", () => this.SizeCase("Pixels", 800, 1600, 900, 1920, 1080, 800, 450))
        this.Test("screen-width percentage", () => this.SizeCase("Screen width %", 50, 1600, 900, 1920, 1080, 960, 540))
        this.Test("screen-height percentage", () => this.SizeCase("Screen height %", 50, 1600, 900, 1920, 1080, 960, 540))
        this.Test("original-image percentage", () => this.SizeCase("Original %", 25, 1600, 900, 1920, 1080, 400, 225))
        this.Test("oversize image is fitted inside monitor margin", () => this.SizeCase("Pixels", 8000, 1000, 1000, 1920, 1080, 1048, 1048))
        this.Test("tiny positive size is clamped to one pixel", () => this.SizeCase("Pixels", 0.1, 1600, 900, 1920, 1080, 1, 1))
        this.Test("zero source dimensions are rejected", () => this.Throws(() => PM_Model.SizeFor("Pixels", 800, 0, 900, 1920, 1080)))
        this.Test("negative size is rejected", () => this.Throws(() => PM_Model.SizeFor("Pixels", -1, 1600, 900, 1920, 1080)))
        this.Test("monitor without usable margin is rejected", () => this.Throws(() => PM_Model.SizeFor("Pixels", 800, 1600, 900, 32, 1080)))
        this.Test("unknown sizing mode is rejected", () => this.Throws(() => PM_Model.SizeFor("Unknown", 800, 1600, 900, 1920, 1080)))
        this.Test("default image reader decodes the authored bitmap without GUI", () => this.CheckDefaultImageReader())
        this.Test("monitor geometry retains negative coordinates and offsets", () => this.CheckGeometry())
        this.Test("monitor geometry centers in selected bounds", () => this.CheckCenter())
        this.Test("disconnected monitor fails closed", () => this.CheckDisconnected())

        this.Test("variant inherits parent values and own overrides", () => this.CheckInheritance())
        this.Test("Own off restores parent inheritance", () => this.CheckOwnOff())
        this.Test("missing inheritance parent is rejected", () => this.Throws(() => this.ResolveMissing()))
        this.Test("self inheritance cycle is rejected", () => this.Throws(() => this.ResolveSelfCycle()))
        this.Test("multi-node inheritance cycle is rejected", () => this.Throws(() => this.ResolveMultiCycle()))
        this.Test("bounded inheritance accepts sixteen levels and rejects seventeen", () => this.CheckInheritanceDepth())
        this.Test("trigger key cannot be overridden", () => this.Throws(() => this.Module.SetOverride(1, "base", "Key", "F8")))
        this.Test("unknown appearance field is rejected by pure resolver", () => this.Throws(() => this.ResolveUnknownField()))
        this.Test("invalid numeric opacity cannot resolve", () => this.CheckInvalidOpacity())
        this.Test("invalid duration cannot resolve", () => this.CheckInvalidDuration())
        this.Test("invalid metadata control character is rejected", () => this.Throws(() => PM_Model.Text("name`nInjected=value")))
        this.Test("oversized metadata text is rejected", () => this.Throws(() => PM_Model.Text("abcd", 3)))
        this.Test("encoded metadata preserves Unicode whitespace semicolons and quotes", () => this.CheckEncodedText())
        this.Test("malformed metadata encoding is rejected", () => this.Throws(() => PM_Model.Decode("hex:xyz")))
        this.Test("noncanonical override field cannot become an invisible map key", () => this.Throws(() => this.Module.SetOverride(1, "base", "opacity", 50)))

        this.Test("content-equivalent images deduplicate managed storage", () => this.CheckDedup())
        this.Test("asset imports are explicit but do not save sidecar", () => this.True(!FileExist(this.Module.Path)))
        this.Test("managed file hash equals selected source", () => this.Eq(PM_Model.Sha256(this.Module.AssetPath(this.ImageId)), PM_Model.Sha256(this.FirstImage)))
        this.Test("linked asset remains linked and original unchanged", () => this.CheckLinked())
        this.Test("missing linked image may relink only identical bytes", () => this.CheckRelink())
        this.Test("different bytes cannot replace shared linked asset", () => this.Throws(() => this.Module.RelinkAsset(this.LinkedId, this.FirstImage)))
        this.Test("linked asset promotion deduplicates and verifies managed copy", () => this.CheckPromotion())
        this.Test("profile attachment is opaque data and not executed", () => this.CheckProfile())
        this.Test("wrong asset kind cannot be used as an image or profile", () => this.CheckWrongKind())
        this.Test("executable attachment is rejected", () => this.CheckExecutableAttachment())
        this.Test("metadata filters match case-insensitively", () => this.CheckFilter())
        this.Test("profile metadata precedes image metadata", () => this.CheckMetadataPrecedence())
        this.Test("individual metadata pin blocks inheritance", () => this.CheckMetadataPin())
        this.Test("FollowAsset off pins all metadata", () => this.CheckMetadataOff())
        this.Test("explicit own metadata overrides asset followers", () => this.CheckMetadataOwn())
        this.Test("view grouping cannot modify game routing metadata", () => this.CheckViewOnly())
        this.Test("all own references protect unused inherited assets", () => this.CheckUsage())
        this.Test("managed linked used and unused library filters are distinct", () => this.CheckStorageUsageFilters())
        this.Test("missing linked data is visible in the Missing library filter", () => this.CheckMissingFilter())
        this.Test("Used first sort places shared references before unused assets", () => this.CheckUsedFirstSort())
        this.Test("in-use asset removal is refused", () => this.Throws(() => this.Module.RemoveAsset(this.ImageId)))
        this.Test("unused asset removal retains managed recovery bytes", () => this.CheckRemoval())

        this.Test("exact executable match is case-insensitive", () => this.True(PM_Model.MatchesExe("SkyrimSE.exe;Cyberpunk2077.exe", "skyrimse.exe")))
        this.Test("executable substring is not a match", () => this.True(!PM_Model.MatchesExe("SkyrimSE.exe", "NotSkyrimSE.exe")))
        this.Test("Unknown required context cannot choose a constrained variant", () => this.CheckUnknownContext())
        this.Test("unique explicit context can select a help variant", () => this.CheckUniqueContext())
        this.Test("equal context matches remain ambiguous", () => this.CheckAmbiguousContext())
        this.Test("explicit preferred help variant can resolve equal matches", () => this.CheckPreferredContext())
        this.Test("view-only asset grouping does not influence context selection", () => this.CheckGroupRouting())

        this.Test("explicit isolated sidecar save reloads variants and metadata", () => this.CheckRoundTrip())
        this.Test("second explicit save creates byte-identical recovery checkpoint", () => this.CheckSaveBackup())
        this.Test("legacy identity mismatch falls back without retargeting", () => this.CheckIdentityMismatch())
        this.Test("reindex orphans advanced records without changing legacy slots", () => this.CheckReindex())
        this.Test("orphaned removed-slot definitions remain saveable and retained", () => this.CheckRemovedSlotSave())
        this.Test("malformed sidecar load blocks writes and leaves original intact", () => this.CheckMalformedLoad())
        this.Test("external sidecar change blocks overwrite and retains both revisions", () => this.CheckExternalChange())
        this.Test("legacy INI hash change leaves advanced records inactive", () => this.CheckLegacyHashChange())
        this.Test("legal twelve-slot long-path layout can save advanced metadata", () => this.CheckLongLayout())
        this.Test("legacy settings and slot profiles remain identical", () => this.CheckPreservation())
    }

    NewModule(path := "", host := 0, skipLoad := true) {
        return StudioPictureModule(IsObject(host) ? host : this.Host,
            {Path: path = "" ? this.Root "\advanced.ini" : path, AssetDir: this.Root "\assets", SkipLoad: skipLoad,
             ImageSize: (file) => [1600, 900], MonitorBounds: this.Bounds.Bind(this)})
    }

    Bounds(choice) {
        switch choice {
            case "Primary": return [0, 0, 1920, 1080]
            case "2": return [-1920, -200, 0, 880]
            case "Active window": return [0, 0, 1280, 1024]
            case "Mouse": return [1920, 100, 4480, 1540]
            default: throw Error("Synthetic disconnected monitor.")
        }
    }

    CheckInert() {
        this.True(!FileExist(this.Module.Path))
        this.True(!DirExist(this.Module.AssetDir))
        this.Eq(this.Module.Gui, 0), this.Eq(this.Module.PreviewGui, 0), this.Eq(this.Module.PreviewTimer, 0)
        this.Eq(this.Module.Context.Device, "Unknown"), this.Eq(this.Module.Context.Layer, "Unknown")
        this.Eq(this.SlotSnapshot(this.Host.Slots), this.BeforeSlots)
    }

    CheckBase() {
        s := this.Module.ResolveSlot(1)
        this.Eq(s.Key, "F7"), this.Eq(s.Width, 800), this.Eq(s.Opacity, 75), this.Eq(s.SizeMode, "Pixels")
        s.Key := "F8", s.Display["Game"] := "Test"
        this.Eq(this.Host.Slots[1].Key, "F7")
        this.Eq(this.Module.ResolveSlot(1).Display["Game"], "")
    }

    CheckDraft() {
        draft := PM_Model.Clone(this.Host.Slots[1])
        draft.Width := 420, draft.Opacity := 55, draft.Duration := 3
        resolved := this.Module.ResolveSlot(1, draft)
        this.Eq(resolved.Width, 420), this.Eq(resolved.SizeValue, 420), this.Eq(resolved.Opacity, 55)
        resolved.Width := 123, this.Eq(draft.Width, 420)
        this.Eq(this.SlotSnapshot(this.Host.Slots), this.BeforeSlots)
        this.True(!FileExist(this.Module.Path))
    }

    CheckClone() {
        before := Map("a", [{Value: 3}], "b", Map("Value", 2)), copy := PM_Model.Clone(before)
        copy["a"][1].Value := 9, copy["b"]["Value"] := 8
        this.Eq(before["a"][1].Value, 3), this.Eq(before["b"]["Value"], 2)
    }

    CheckFieldOwnership() {
        for field in ["Key", "Enabled", "Source", "Pass", "MicCanvas"]
            this.True(!PM_Model.Has(PM_Model.Join(PM_Model.Fields, ","), field), "Input owner field " field)
    }

    SizeCase(mode, value, iw, ih, mw, mh, ew, eh) {
        size := PM_Model.SizeFor(mode, value, iw, ih, mw, mh)
        this.Eq(size[1], ew), this.Eq(size[2], eh)
    }

    CheckGeometry() {
        s := this.Module.ResolveSlot(1), s.Monitor := "2", s.OffsetX := 7, s.OffsetY := -9
        g := this.Module.Geometry(s)
        this.Eq(g.w, 800), this.Eq(g.h, 450), this.Eq(g.x, -809), this.Eq(g.y, -193), this.Eq(g.monitor, "2")
    }

    CheckCenter() {
        s := this.Module.ResolveSlot(1), s.Monitor := "Mouse", s.Position := "Center"
        g := this.Module.Geometry(s)
        this.Eq(g.x, 2800), this.Eq(g.y, 595)
    }

    CheckDisconnected() {
        s := this.Module.ResolveSlot(1), s.Monitor := "99"
        this.Throws(() => this.Module.Geometry(s))
    }
    CheckDefaultImageReader() {
        m := StudioPictureModule(this.Host, {Path: this.Root "\image-reader.ini", AssetDir: this.Root "\decode-assets", SkipLoad: true,
            MonitorBounds: this.Bounds.Bind(this)})
        s := this.LegacySlot(), s.File := this.FirstImage, s.SizeMode := "Original %", s.SizeValue := 100
        g := m.Geometry(s)
        this.Eq(g.w, 1), this.Eq(g.h, 1)
    }

    CheckInheritance() {
        this.ParentId := this.Module.AddVariant(1, "Parent")
        this.ChildId := this.Module.AddVariant(1, "Child", this.ParentId)
        this.Module.SetOverride(1, this.ParentId, "Opacity", 40)
        this.Module.SetOverride(1, this.ChildId, "SizeValue", 50)
        this.Module.SetOverride(1, this.ChildId, "SizeMode", "Screen width %")
        this.Module.SetOverride(1, this.ChildId, "Opacity", 90)
        this.Module.BaseRecord(1).Selected := this.ChildId
        s := this.Module.ResolveSlot(1)
        this.Eq(s.Opacity, 90), this.Eq(s.SizeMode, "Screen width %"), this.Eq(s.SizeValue, 50), this.Eq(s.Key, "F7")
    }

    CheckOwnOff() {
        this.Module.SetOverride(1, this.ChildId, "Opacity", "", false)
        this.Eq(this.Module.ResolveSlot(1).Opacity, 40)
    }

    ResolveMissing() {
        return PM_Model.Resolve(Map("a", {Parent: "missing", Overrides: Map()}), "a", this.BaseValuesFixture)
    }
    ResolveSelfCycle() {
        return PM_Model.Resolve(Map("a", {Parent: "a", Overrides: Map()}), "a", this.BaseValuesFixture)
    }
    ResolveMultiCycle() {
        return PM_Model.Resolve(Map("a", {Parent: "b", Overrides: Map()}, "b", {Parent: "a", Overrides: Map()}), "a", this.BaseValuesFixture)
    }
    CheckInheritanceDepth() {
        variants := Map()
        Loop 16
            variants["v" A_Index] := {Parent: A_Index = 16 ? "" : "v" (A_Index + 1), Overrides: Map()}
        this.Eq(PM_Model.Resolve(variants, "v1", this.BaseValuesFixture)["Opacity"], 75)
        variants["v16"].Parent := "v17", variants["v17"] := {Parent: "", Overrides: Map()}
        this.Throws(() => PM_Model.Resolve(variants, "v1", this.BaseValuesFixture))
    }
    ResolveUnknownField() {
        return PM_Model.Resolve(Map("a", {Parent: "", Overrides: Map("SendInput", "unsafe")}), "a", this.BaseValuesFixture)
    }
    CheckInvalidOpacity() {
        m := this.NewModule()
        this.Throws(() => m.SetOverride(1, "base", "Opacity", "not-a-number"))
        this.Eq(m.ResolveValues(1)["Opacity"], 75)
    }
    CheckInvalidDuration() {
        m := this.NewModule()
        this.Throws(() => m.SetOverride(1, "base", "Duration", 0))
        this.Eq(m.ResolveValues(1)["Duration"], 2)
    }
    CheckEncodedText() {
        value := '  Label "quoted"; Azeron שלום 🎮  '
        this.Eq(PM_Model.Decode(PM_Model.Encode(value)), value)
        this.Eq(PM_Model.Decode(PM_Model.Encode("")), "")
    }

    CheckDedup() {
        this.ImageId := this.Module.ImportAsset(this.FirstImage)
        duplicate := this.Module.ImportAsset(this.SameImage)
        this.Eq(duplicate, this.ImageId), this.Eq(this.Module.Assets.Count, 1)
        count := 0
        Loop Files this.Module.AssetDir "\*", "F"
            count += 1
        this.Eq(count, 1)
        this.Eq(PM_Model.Sha256(this.FirstImage), PM_Model.Sha256(this.SameImage))
    }
    CheckLinked() {
        this.LinkedId := this.Module.ImportAsset(this.OtherImage, "Image", false)
        this.Eq(this.Module.AssetPath(this.LinkedId), this.OtherImage)
        this.Eq(this.Module.Assets[this.LinkedId].Managed, 0)
        this.Eq(PM_Model.Sha256(this.OtherImage), this.Module.Assets[this.LinkedId].Hash)
    }
    CheckRelink() {
        replacement := this.Root "\relinked.bmp"
        FileCopy(this.OtherImage, replacement)
        FileDelete(this.OtherImage)
        this.True(!FileExist(this.Module.AssetPath(this.LinkedId)))
        this.Module.RelinkAsset(this.LinkedId, replacement)
        this.Eq(this.Module.AssetPath(this.LinkedId), replacement)
    }
    CheckPromotion() {
        linked := this.Module.AssetPath(this.LinkedId), hash := PM_Model.Sha256(linked)
        this.Eq(this.Module.ImportAsset(linked, "Image", true), this.LinkedId)
        this.Eq(this.Module.Assets[this.LinkedId].Managed, 1)
        this.Eq(PM_Model.Sha256(this.Module.AssetPath(this.LinkedId)), hash)
        this.Eq(PM_Model.Sha256(linked), hash)
    }
    CheckProfile() {
        path := this.Root "\attachment.json"
        FileAppend('{"fixture":"opaque-only","mapping":"unchanged"}', path, "UTF-8")
        before := PM_Model.Sha256(path)
        this.ProfileId := this.Module.ImportAsset(path, "Profile", false)
        this.Eq(this.Module.Assets[this.ProfileId].Kind, "Profile")
        this.Eq(PM_Model.Sha256(path), before)
        this.Module.SetAssetMetadata(this.ProfileId, Map("Game", "Skyrim", "Device", "ProfileDevice", "Layer", "BASIC"))
        this.Module.SetAssetMetadata(this.ImageId, Map("Game", "Cyberpunk", "Device", "ImageDevice", "Keymap", "R6", "Exe", "SkyrimSE.exe", "LayerKey", "F18", "Tag", "Shared"))
    }
    CheckExecutableAttachment() {
        path := this.Root "\no-run.exe"
        FileAppend("not executable fixture", path)
        this.Throws(() => this.Module.ImportAsset(path, "Profile"))
    }
    CheckWrongKind() {
        this.Throws(() => this.Module.SetOverride(1, "base", "Asset", this.ProfileId))
        this.Throws(() => this.Module.SetOverride(1, "base", "Profile", this.ImageId))
        this.Eq(this.Module.BaseRecord(1).Variants["base"].Overrides.Count, 0)
    }
    CheckFilter() {
        this.Eq(this.Module.FilterAssets("cyberPUNK", "Game").Length, 1)
        this.Eq(this.Module.FilterAssets("R6", "Keymap")[1].Id, this.ImageId)
        this.Eq(this.Module.FilterAssets("not-present").Length, 0)
        this.Throws(() => this.Module.FilterAssets("", "Unknown"))
        this.Throws(() => this.Module.FilterAssets("", "All", "Unknown"))
    }
    MetadataValues() {
        values := PM_Model.Clone(this.BaseValuesFixture)
        values["Asset"] := this.ImageId, values["Profile"] := this.ProfileId
        return values
    }
    CheckMetadataPrecedence() {
        resolved := PM_Model.ResolveMetadata(this.MetadataValues(), this.Module.Assets)
        this.Eq(resolved["Game"], "Skyrim"), this.Eq(resolved["Device"], "ProfileDevice"), this.Eq(resolved["Keymap"], "R6")
    }
    CheckMetadataPin() {
        values := this.MetadataValues(), values["Pins"] := "Game,Device"
        resolved := PM_Model.ResolveMetadata(values, this.Module.Assets)
        this.Eq(resolved["Game"], ""), this.Eq(resolved["Device"], ""), this.Eq(resolved["Keymap"], "R6")
    }
    CheckMetadataOff() {
        values := this.MetadataValues(), values["FollowAsset"] := 0
        resolved := PM_Model.ResolveMetadata(values, this.Module.Assets)
        this.Eq(resolved["Game"], ""), this.Eq(resolved["Keymap"], "")
    }
    CheckMetadataOwn() {
        values := this.MetadataValues(), values["Game"] := "Explicit own"
        this.Eq(PM_Model.ResolveMetadata(values, this.Module.Assets)["Game"], "Explicit own")
    }
    CheckViewOnly() {
        game := this.Module.Assets[this.ImageId].Game
        this.Module.SetAssetMetadata(this.ImageId, Map("ViewGroup", "Reference", "Game", "Do not apply"), true)
        this.Eq(this.Module.Assets[this.ImageId].ViewGroup, "Reference")
        this.Eq(this.Module.Assets[this.ImageId].Game, game)
        this.Throws(() => this.Module.SetAssetMetadata(this.ImageId, Map("Hash", "wrong")))
    }
    CheckUsage() {
        this.Module.SetOverride(1, this.ParentId, "Asset", this.ImageId)
        this.Module.SetOverride(1, this.ChildId, "Profile", this.ProfileId)
        this.Module.SetOverride(2, "base", "Asset", this.ImageId)
        ; Parent OWN reference, child's resolved inherited reference, slot 2 base.
        ; Retain conservative protection of all three, including inactive child.
        this.Eq(this.Module.AssetUsage(this.ImageId).Length, 3)
        this.Eq(this.Module.AssetUsage(this.ProfileId).Length, 1)
        this.Eq(this.Module.ResolveSlot(1).File, this.Module.AssetPath(this.ImageId))
    }
    CheckStorageUsageFilters() {
        this.Eq(this.Module.FilterAssets("", "All", "Name", "Managed").Length, 2)
        this.Eq(this.Module.FilterAssets("", "All", "Name", "Linked").Length, 1)
        this.Eq(this.Module.FilterAssets("", "All", "Name", "All", "Used").Length, 2)
        this.Eq(this.Module.FilterAssets("", "All", "Name", "All", "Unused").Length, 1)
        this.Eq(this.Module.FilterAssets("", "All", "Name", "Missing").Length, 0)
        this.Throws(() => this.Module.FilterAssets("", "All", "Name", "Unknown"))
    }
    CheckMissingFilter() {
        path := this.Root "\missing-linked.txt"
        FileAppend("Isolated missing linked data fixture", path)
        m := this.NewModule(this.Root "\missing-index.ini")
        id := m.ImportAsset(path, "Profile", false)
        FileDelete(path)
        this.Eq(m.FilterAssets("", "All", "Name", "Missing").Length, 1)
        this.Eq(m.FilterAssets("", "All", "Name", "Missing")[1].Id, id)
    }
    CheckUsedFirstSort() {
        items := this.Module.FilterAssets("", "All", "Used first")
        this.Eq(items[1].Id, this.ImageId), this.Eq(items[2].Id, this.ProfileId), this.Eq(items[3].Id, this.LinkedId)
    }
    CheckRemoval() {
        path := this.Module.AssetPath(this.ImageId)
        this.Module.SetOverride(1, this.ParentId, "Asset", "", false)
        this.Module.SetOverride(2, "base", "Asset", "", false)
        this.Module.RemoveAsset(this.ImageId)
        this.True(FileExist(path)), this.True(!this.Module.Assets.Has(this.ImageId))
        this.ImageId := this.Module.ImportAsset(this.FirstImage)
        this.Module.SetOverride(1, this.ParentId, "Asset", this.ImageId)
    }

    ContextVariants(two := false) {
        variants := Map("a", {Parent: "", Overrides: Map("Exe", "SkyrimSE.exe", "Layer", "BASIC", "Device", "Azeron")})
        if two
            variants["b"] := {Parent: "", Overrides: Map("Exe", "SkyrimSE.exe", "Layer", "BASIC", "Device", "Azeron")}
        return variants
    }
    CheckUnknownContext() {
        for ctx in [{Exe: "Unknown", Layer: "BASIC", Device: "Azeron"}, {Exe: "SkyrimSE.exe", Layer: "Unknown", Device: "Azeron"}, {Exe: "SkyrimSE.exe", Layer: "BASIC", Device: "Unknown"}]
            this.Eq(PM_Model.Pick(this.ContextVariants(), this.BaseValuesFixture, this.Module.Assets, ctx).Id, "")
    }
    CheckUniqueContext() {
        this.Eq(PM_Model.Pick(this.ContextVariants(), this.BaseValuesFixture, this.Module.Assets, {Exe: "skyrimse.exe", Layer: "BASIC", Device: "Azeron"}).Id, "a")
    }
    CheckAmbiguousContext() {
        this.Eq(PM_Model.Pick(this.ContextVariants(true), this.BaseValuesFixture, this.Module.Assets, {Exe: "SkyrimSE.exe", Layer: "BASIC", Device: "Azeron"}).Id, "")
    }
    CheckPreferredContext() {
        ctx := {Exe: "SkyrimSE.exe", Layer: "BASIC", Device: "Azeron"}
        this.Eq(PM_Model.Pick(this.ContextVariants(true), this.BaseValuesFixture, this.Module.Assets, ctx, "b").Id, "b")
        this.Eq(PM_Model.Pick(this.ContextVariants(true), this.BaseValuesFixture, this.Module.Assets, ctx, "missing").Id, "")
    }
    CheckGroupRouting() {
        values := this.MetadataValues()
        before := PM_Model.Pick(this.ContextVariants(), this.BaseValuesFixture, this.Module.Assets, {Exe: "SkyrimSE.exe", Layer: "BASIC", Device: "Azeron"}).Id
        this.Module.SetAssetMetadata(this.ImageId, Map("ViewGroup", "Different display-only group"), true)
        this.Eq(PM_Model.Pick(this.ContextVariants(), this.BaseValuesFixture, this.Module.Assets, {Exe: "SkyrimSE.exe", Layer: "BASIC", Device: "Azeron"}).Id, before)
        this.Eq(PM_Model.ResolveMetadata(values, this.Module.Assets)["Exe"], "")
    }

    CheckRoundTrip() {
        this.Module.SaveExplicit()
        this.True(FileExist(this.Module.Path)), this.Eq(this.Module.Dirty, false)
        loaded := this.NewModule(this.Module.Path, this.Host, false)
        this.Eq(loaded.LoadError, ""), this.Eq(loaded.BaseRecord(1).Selected, this.ChildId)
        this.Eq(loaded.ResolveSlot(1).Opacity, 40), this.Eq(loaded.Assets.Count, this.Module.Assets.Count)
        this.Eq(loaded.Assets[this.ImageId].ViewGroup, "Different display-only group")
    }
    CheckSaveBackup() {
        hash := PM_Model.Sha256(this.Module.Path)
        this.Module.SetOverride(1, this.ParentId, "Opacity", 41)
        this.Module.SaveExplicit()
        count := 0
        Loop Files this.Module.Path ".before-*", "F" {
            count += 1
            this.Eq(PM_Model.Sha256(A_LoopFileFullPath), hash)
        }
        this.Eq(count, 1)
    }
    CheckIdentityMismatch() {
        host := PM_Model.Clone(this.Host), host.Slots[1].Key := "F8"
        loaded := this.NewModule(this.Module.Path, host, false)
        this.Eq(loaded.LoadError, ""), this.Eq(loaded.BaseRecord(1).Orphaned, 1)
        this.Eq(loaded.ResolveSlot(1).Opacity, 75), this.Eq(loaded.ResolveSlot(1).Key, "F8")
    }
    CheckReindex() {
        copy := this.NewModule(this.Module.Path, this.Host, false)
        copy.LegacyChanged(0, true)
        this.Eq(copy.BaseRecord(1).Orphaned, 1), this.Eq(copy.BaseRecord(2).Orphaned, 1)
        this.Eq(copy.ResolveSlot(1).Opacity, 75)
        this.Eq(this.SlotSnapshot(this.Host.Slots), this.BeforeSlots)
    }
    CheckRemovedSlotSave() {
        host := PM_Model.Clone(this.Host)
        host.Slots.Pop()
        copy := this.NewModule(this.Module.Path, host, false)
        this.Eq(copy.LoadError, ""), this.Eq(copy.Records["2"].Orphaned, 1)
        copy.Path := this.Root "\orphan-preserved.ini"
        copy.SourceHash := ""
        copy.SaveExplicit()
        loaded := this.NewModule(copy.Path, host, false)
        this.Eq(loaded.LoadError, ""), this.True(loaded.Records.Has("2"))
        this.Eq(loaded.Records["2"].Orphaned, 1)
    }
    CheckMalformedLoad() {
        path := this.Root "\invalid.ini"
        FileAppend("[Meta]`nSchema=999`n", path, "UTF-8")
        hash := PM_Model.Sha256(path), m := this.NewModule(path, this.Host, false)
        this.True(m.LoadError != "")
        this.Throws(() => m.SaveExplicit())
        this.Throws(() => m.ImportAsset(this.FirstImage))
        this.Eq(PM_Model.Sha256(path), hash)
    }
    CheckExternalChange() {
        path := this.Root "\concurrent.ini"
        m := this.NewModule(path), m.BaseRecord(1), m.SaveExplicit()
        saved := FileRead(path, "UTF-8")
        FileAppend("; External authored fixture update`n", path, "UTF-8")
        hash := PM_Model.Sha256(path)
        m.SetOverride(1, "base", "Opacity", 77)
        this.Throws(() => m.SaveExplicit())
        this.Eq(PM_Model.Sha256(path), hash)
        this.Eq(m.ResolveValues(1)["Opacity"], 77)
        this.True(InStr(FileRead(path, "UTF-8"), saved))
    }
    CheckLegacyHashChange() {
        config := this.Root "\changed-legacy.ini"
        FileCopy(this.LegacyPath, config)
        host := PM_Model.Clone(this.Host), host.Config := config
        path := this.Root "\legacy-hash.ini"
        m := this.NewModule(path, host), m.BaseRecord(1), m.SetOverride(1, "base", "Opacity", 50), m.SaveExplicit()
        FileAppend("; Changed only the isolated legacy fixture`n", config, "UTF-8")
        loaded := this.NewModule(path, host, false)
        this.Eq(loaded.LoadError, ""), this.Eq(loaded.BaseRecord(1).Orphaned, 1)
        this.Eq(loaded.ResolveSlot(1).Opacity, 75)
    }
    CheckLongLayout() {
        slots := [], suffix := ""
        Loop 100
            suffix .= "x"
        Loop 12 {
            slot := this.LegacySlot(suffix A_Index, "F" (12 + A_Index))
            slot.File := this.Root "\" suffix A_Index ".bmp"
            slots.Push(slot)
        }
        host := {Slots: slots, Dir: this.Root}, path := this.Root "\long-layout.ini"
        m := this.NewModule(path, host)
        Loop slots.Length
            m.BaseRecord(A_Index)
        m.SaveExplicit()
        loaded := this.NewModule(path, host, false)
        this.Eq(loaded.LoadError, ""), this.Eq(loaded.Records.Count, 12)
        this.Eq(loaded.BaseRecord(12).Orphaned, 0)
    }
    CheckPreservation() {
        this.Eq(this.SlotSnapshot(this.Host.Slots), this.BeforeSlots)
        current := FileRead(this.LegacyPath, "RAW")
        this.Eq(current.Size, this.LegacyBytes.Size)
        Loop current.Size
            this.Eq(NumGet(current, A_Index - 1, "UChar"), NumGet(this.LegacyBytes, A_Index - 1, "UChar"))
    }

    Cleanup() {
        expectedPrefix := A_Temp "\StudioPictureAcceptance-" DllCall("GetCurrentProcessId", "UInt") "-"
        if SubStr(this.Root, 1, StrLen(expectedPrefix)) != expectedPrefix
            throw Error("Fixture target is outside the exact task prefix.")
        marker := this.Root "\FIXTURE-ONLY.txt"
        if !FileExist(marker) || FileRead(marker, "UTF-8") != "Isolated authored fixture; no live profiles or user content.`n"
            throw Error("Authored fixture marker does not match; no deletion attempted.")
        DirDelete(this.Root, true)
        this.True(!DirExist(this.Root), "Fixture cleanup did not complete.")
    }

    Test(name, callback) {
        try {
            callback.Call()
            this.Passed += 1
            this.Results.Push("PASS " name)
        } catch Error as err {
            this.Failed += 1
            this.Results.Push("FAIL " name ": " err.Message " @ " err.Line)
        }
    }

    True(value, message := "Expected true") {
        if !value
            throw Error(message)
    }

    Eq(actual, expected, message := "") {
        if actual != expected
            throw Error((message ? message ": " : "") "expected [" expected "], got [" actual "]")
    }

    Near(actual, expected, tolerance := 1, message := "") {
        if Abs(actual - expected) > tolerance
            throw Error((message ? message ": " : "") "expected " expected " +/- " tolerance ", got " actual)
    }

    Throws(callback, message := "Expected rejection") {
        rejected := false
        try callback.Call()
        catch Error
            rejected := true
        this.True(rejected, message)
    }

    WriteBmp(path, pixel := "0000FF00") {
        ; Authored 1x1 RGB BMP; image dimensions for geometry are injected separately.
        hex := "424D3A0000000000000036000000280000000100000001000000010018000000000004000000130B0000130B00000000000000000000" pixel
        bytes := Buffer(StrLen(hex) // 2)
        Loop bytes.Size
            NumPut("UChar", Integer("0x" SubStr(hex, (A_Index - 1) * 2 + 1, 2)), bytes, A_Index - 1)
        stream := FileOpen(path, "w")
        try stream.RawWrite(bytes)
        finally stream.Close()
        return path
    }

    LegacySlot(name := "Fixture picture", key := "F7") {
        return {Enabled: 1, Name: name, Key: key, Source: "Local", Mode: "Hold", File: "",
            MicCanvas: "", Width: 800, Opacity: 75, Position: "TopRight", OffsetX: 0,
            OffsetY: 0, Duration: 2, Pass: 0}
    }

    SlotSnapshot(slots) {
        value := ""
        for index, slot in slots {
            value .= "slot=" index "`n"
            for field, content in slot.OwnProps()
                value .= field "=" content "`n"
        }
        return value
    }
}
