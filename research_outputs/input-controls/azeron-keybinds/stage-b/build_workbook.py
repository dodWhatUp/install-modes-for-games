#!/usr/bin/env python3
"""Build a derived spreadsheet with the installed artifact_tool authoring runtime.
Run the stdlib validator first. This is not a native Azeron profile writer."""
from pathlib import Path
import sys, json, runpy
from artifact_tool import Workbook, SpreadsheetFile
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
layout=json.loads((out/"layout_candidate.json").read_text(encoding="utf-8"))
baseline_path=out/"baseline_r2_for_comparison.json"
if not baseline_path.exists():
    baseline_path=out.parent/"extensions/2026-10-10-r2/STAGE_B_DRAFT_R2.json"
r2=json.loads(baseline_path.read_text(encoding="utf-8"))
r3maps=layout["maps"]; common=layout["common_positions"]
positions=list(r3maps["BASIC"])
audit=json.loads((out/"validation.json").read_text(encoding="utf-8"))
cases=json.loads((out/"cases.json").read_text(encoding="utf-8"))["cases"]
sources=layout["sources"]
ns=runpy.run_path(str(out/"validate_layout.py"))
# Author a spreadsheet companion through artifact_tool only.
wb=Workbook.create()
sheets={name:wb.worksheets.add(name) for name in ["Overview","Map","Tests","Changes","Sources"]}
def col_name(i):
    s=""
    while i: i,r=divmod(i-1,26);s=chr(65+r)+s
    return s
def put_table(sheet_name,headers,rows,widths):
    sh=sheets[sheet_name];last=len(rows)+4
    sh.get_range(f"A1:{col_name(len(headers))}{last}").format={
        "font":{"name":"Arial","size":11,"color":"#20334A"},
        "vertical_alignment":"center","row_height":29}
    sh.get_range("A1").values=[[f"Azeron Stage B R3 — {sheet_name}"]]
    sh.get_range("A1").format.font={"name":"Arial","size":17,"bold":True,"color":"#17344F"}
    sh.get_range("A2").values=[["טיוטה בלבד — לא קובץ לייבוא; בדיקת אצבעות משוערת, ללא אימות משחק או חומרה."]]
    sh.merge_cells(f"A2:{col_name(len(headers))}2")
    sh.get_range(f"A2:{col_name(len(headers))}2").format.wrap_text=True
    sh.get_range("A2").format.row_height=35
    sh.get_range(f"A4:{col_name(len(headers))}{last}").values=[headers]+rows
    sh.get_range(f"A4:{col_name(len(headers))}4").format={
        "fill":"#17344F","font":{"name":"Arial","size":11,"bold":True,"color":"#FFFFFF"},
        "wrap_text":True,"row_height":43,"vertical_alignment":"center"}
    sh.tables.add(f"A4:{col_name(len(headers))}{last}",True,f"{sheet_name}Table")
    sh.freeze_panes.freeze_rows(4); sh.freeze_panes.freeze_columns(2)
    for i,width in enumerate(widths,1):sh.get_range(f"{col_name(i)}1:{col_name(i)}{last}").format.column_width=width
    sh.get_range(f"A5:{col_name(len(headers))}{last}").format.wrap_text=True
    return sh,last
mrows=[]
for bank in r3maps:
    for p in positions:
        before=r2['maps'][bank][p];after=r3maps[bank][p]
        mrows.append([bank,p,ns['group'](p),before,after,
                      "CHANGED" if before!=after else "UNCHANGED",
                      "COMMON" if p in common else "",
                      "NOT_VERIFIED",
                      "ריק כדי לא להעמיס על האצבע שמחזיקה את הבורר." if after=="UNASSIGNED" and bank!="BASIC" else ""])
msh,mend=put_table("Map",["Bank","Visual position","Finger hypothesis","R2 output","R3 output","Change","Common anchor","Hardware ID status","Note"],mrows,[18,17,21,24,24,18,19,22,50])
trows=[]
for x in audit["per_case"]:
    c=next(t for t in cases if t["id"]==x["id"]);new=x["r3"]
    route="; ".join(t["key"]+" @ "+t["position"] for t in new["route"]) if new["route"] else ""
    trows.append([c["id"],c["bank"]," + ".join(c["keys"]),"YES" if c["movement_required"] else "NO",
                  x["r2"]["status"],new["status"],new["reason"],route,c["requirement_origin"],
                  c["source_id"] or "", "NOT_TESTED",c["notes"]])
tsh,tend=put_table("Tests",["Case","Bank","Keys","Plus movement","R2 model","R3 model","Reason","Route","Requirement origin","Source ID","Runtime","Note"],
                 trows,[31,18,26,18,26,26,53,57,48,18,19,65])
tsh.get_range(f"A5:L{tend}").format.row_height=44
changes=audit["mapping_changes"]
chsh,cend=put_table("Changes",["Bank","Visual position","Before","After"],
                   [[x[k] for k in ["bank","position","before","after"]] for x in changes],[21,23,32,32])
ssh,send=put_table("Sources",["ID","Type","Read date","Locator","Supported fact","Limit","URL"],
      [[s["id"],s["type"],s["accessed"],s["locator"],s["supports"],s["limit"],s["url"]] for s in sources],[18,24,17,49,73,75,90])
ssh.get_range(f"A5:G{send}").format.row_height=68
ov=sheets["Overview"]
ov.get_range("A1:G30").format={"font":{"name":"Arial","size":12,"color":"#20334A"},"row_height":29,"vertical_alignment":"center"}
for c,w in [("A",43),("B",22),("C",22),("D",5),("E",30),("F",24),("G",25)]:
    ov.get_range(c+"1:"+c+"30").format.column_width=w
ov.merge_cells("A1:G2");ov.get_range("A1").values=[["Azeron — שלב ב׳ / R3"]]
ov.get_range("A1:G2").format={"fill":"#17344F","font":{"name":"Arial","size":21,"bold":True,"color":"#FFFFFF"},"row_height":30}
ov.merge_cells("A3:G4");ov.get_range("A3").values=[["בדיקת גישה סטטית בלבד. לא נבדקו זמן תגובה, נוחות היד, חומרה או התנהגות משחק."]]
ov.get_range("A3:G4").format.wrap_text=True
ov.get_range("A6:C9").values=[["תוצאת המודל","R2","R3"],["MODEL_ROUTE",None,None],["MODEL_CONFLICT",None,None],["NOT_IN_BANK",None,None]]
for rr,st in [(7,"MODEL_ROUTE"),(8,"MODEL_CONFLICT"),(9,"NOT_IN_BANK")]:
    ov.get_range(f"B{rr}:C{rr}").formulas=[[
        f'=COUNTIF(Tests!$E$5:$E${tend},A{rr})',
        f'=COUNTIF(Tests!$F$5:$F${tend},A{rr})']]
ov.get_range("A10").values=[["סה״כ בדיקות"]]
ov.get_range("B10:C10").formulas=[["=SUM(B7:B9)","=SUM(C7:C9)"]]
ov.get_range("A12:B15").values=[["הקצאות שנבדקו",None],["שינויים בבסיס",None],["תאים ריקים בשכבות משניות",None],["יעד קודים לוגיים כולל WASD",78]]
ov.get_range("B12").formulas=[[f"=COUNTA(Map!$B$5:$B${mend})"]]
ov.get_range("B13").formulas=[[f'=COUNTIFS(Map!$A$5:$A${mend},"BASIC",Map!$F$5:$F${mend},"CHANGED")']]
ov.get_range("B14").formulas=[[f'=COUNTIFS(Map!$A$5:$A${mend},"<>BASIC",Map!$E$5:$E${mend},"UNASSIGNED")']]
ov.get_range("E6:F9").values=[["שכבות תאורטיות","גבול קיבולת"],[3,None],[4,None],[5,None]]
for rr in [7,8,9]:
    ov.get_range(f"F{rr}").formulas=[[f"=E{rr}*(30-(E{rr}-1))-6*(E{rr}-1)+4"]]
ov.merge_cells("E11:G15")
ov.get_range("E11").values=[["קיבולת לפני כפילויות ורזרבות: 30 מקומות, בורר לכל שכבה נוספת, 6 קלטים קבועים ו־4 יציאות WASD. זה אינו מדד שימושיות או הוכחת מינימום אוניברסלי."]]
ov.get_range("E11:G15").format.wrap_text=True
notes=[
"F1–F9 ו־1–9 מסודרים באותם מקומות בשתי השכבות.",
"Ctrl ו־Shift נוספים בבנק המספרים מספקים מסלולים חלופיים לפי השערת האצבעות.",
"Space, Enter, Esc והמקשים Ctrl / Shift / Alt הראשיים נשמרים בכל השכבות.",
"33 מבחנים קיבלו מסלול חדש; 6 איבדו מסלול. אין להמיר זאת לאחוז שיפור.",
"כל סימון finger hypothesis הוא השערה חזותית, לא זיהוי כפתור חומרה.",
"המאגר נשאר 94 רשומות / 2,195 מיפויים; אין כאן סריקת משחקים חדשה.",
"נדרש ייצוא JSON עדכני של פרופילי התוכנה ב־v2 לפני יצירת קובץ לייבוא.",
"אל תייבא את layout_candidate.json לתוכנת Azeron. הוא קובץ תכנון בלבד."
]
for rr,note in enumerate(notes,18):
    ov.merge_cells(f"A{rr}:G{rr}")
    ov.get_range(f"A{rr}").values=[[note]]
    ov.get_range(f"A{rr}:G{rr}").format.wrap_text=True
    ov.get_range(f"A{rr}:G{rr}").format.row_height=36
ov.get_range("A6:C6").format={"fill":"#E2ECF6","font":{"bold":True},"row_height":33}
ov.get_range("E6:F6").format={"fill":"#E2ECF6","font":{"bold":True},"row_height":33}
ov.get_range("B7:C15").set_number_format("0");ov.get_range("F7:F9").set_number_format("0")
print(wb.inspect({"kind":"table","range":"Overview!A6:C15","include":"values,formulas","table_max_rows":10,"table_max_cols":3}).ndjson)
book_path=out/"Azeron_Stage_B_R3.xlsx"
ov.unmerge_cells("E11:G15")
for rg,txt in [("E11:G12","גבול תאורטי: 30 מקומות ו־6 קלטים קבועים."),
               ("E13:G14","כולל בוררי שכבות ותנועה; לפני כפילויות ורזרבות."),
               ("E15:G15","לא מדידה של נוחות או מהירות.")]:
    ov.merge_cells(rg)
    ov.get_range(rg.split(":")[0]).values=[[txt]]
    ov.get_range(rg).format.wrap_text=True
    ov.get_range(rg).format.horizontal_alignment="right"
for rg in ["A1:G2","A3:G4","A6:A6","E6:G6","A10:A15","A18:G25"]:
    ov.get_range(rg).format.horizontal_alignment="right"
SpreadsheetFile.export_xlsx(wb).save(str(book_path))
