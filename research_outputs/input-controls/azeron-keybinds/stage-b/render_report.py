#!/usr/bin/env python3
"""Generate the Hebrew, offline Stage B viewer from the JSON design and audit."""
import html
import json
import sys
from pathlib import Path

def build(folder):
    d=json.loads((folder/"layout_candidate.json").read_text(encoding="utf-8"))
    a=json.loads((folder/"validation.json").read_text(encoding="utf-8"))
    cases=json.loads((folder/"cases.json").read_text(encoding="utf-8"))["cases"]
    def esc(s): return html.escape(str(s), quote=True)
    names={"BASIC":"בסיס","NUMBERS":"מספרים וסימנים","LETTERS":"אותיות נוספות וניווט","TOOLS":"מקשי F וניווט"}
    labels={"UNASSIGNED":"—","LAYER:TOOLS":"כלים","LAYER:NUMBERS":"מספרים","LAYER:LETTERS":"אותיות",
       "Up Arrow":"↑","Down Arrow":"↓","Left Arrow":"←","Right Arrow":"→"}
    coordinates={}
    for r in range(1,6):
        for c in range(1,5): coordinates[f"R{r}C{c}"]=(r+2,c+1)
    coordinates.update({"L3":(5,1),"R3":(5,6),"TH_U":(2,8),"TH_L":(3,7),"TH_C":(3,8),
      "TH_R":(3,9),"TH_D":(4,8),"ST_RU":(5,9),"ST_RD":(6,9),"ST_D":(7,7)})
    changed={(x["bank"],x["position"]) for x in a["mapping_changes"]}
    boards=[]
    for bank,mapping in d["maps"].items():
        cells=[]
        for p,k in mapping.items():
            r,c=coordinates[p]
            cl="key"
            if k.startswith("LAYER:"):cl+=" selector"
            elif k=="UNASSIGNED":cl+=" blank"
            elif p in d["common_positions"]:cl+=" anchor"
            if (bank,p) in changed:cl+=" changed"
            cells.append(f'<div class="{cl}" data-key="{esc(k)}" style="grid-row:{r};grid-column:{c}">'
                         f'<small dir="ltr">{p}</small><strong dir="ltr">{esc(labels.get(k,k))}</strong>'
                         f'<span>{"שונה" if (bank,p) in changed else ""}</span></div>')
        boards.append(f'<section><h2>{names[bank]} <small dir="ltr">{bank}</small></h2>'
          '<p class="muted">השורות והעמודות תואמות לסכמת התמונות שסיפקת. אלה אינם מזהי חומרה; האצבעות משויכות לעמודות לצורך בדיקה שמרנית בלבד.</p>'
          '<div class="board-scroll"><div class="board" dir="ltr">'+''.join(cells)+
          '<div class="stick" style="grid-row:5 / span 2;grid-column:7 / span 2">סטיק תנועה<br><b>W A S D</b><small>בכל ארבע השכבות המוצעות</small></div>'
          '</div></div></section>')
    source_rows=''.join(f'<tr><td>{esc(s["id"])}</td><td><a href="{esc(s["url"])}">{esc(s["type"])}</a></td><td>{esc(s["supports"])}</td><td>{esc(s["limit"])}</td></tr>' for s in d["sources"])
    status_names={"MODEL_ROUTE":"מסלול נפרד במודל","MODEL_CONFLICT":"נדרשת בדיקה / יש חפיפה","NOT_IN_BANK":"חסר בשכבה"}
    cdict={x["id"]:x for x in cases}
    case_rows=[]
    for x in a["per_case"]:
        rr=x["r3"]; old=x["r2"]; c=cdict[x["id"]]
        route='; '.join(t["key"]+' @ '+t["position"] for t in rr["route"]) if rr["route"] else rr["reason"]
        case_rows.append('<tr data-status="'+rr["status"]+'"><td dir="ltr">'+esc(x["id"])+'</td><td dir="ltr">'+
         esc(rr["bank"])+'</td><td dir="ltr">'+esc(' + '.join(rr["keys"]))+'</td><td>'+
         ('כן' if rr["movement_required"] else 'לא')+'</td><td>'+status_names[old["status"]]+'</td><td>'+
         status_names[rr["status"]]+'</td><td dir="ltr">'+esc(route)+'</td><td dir="ltr">'+esc(c["requirement_origin"])+'</td></tr>')
    changes=''.join('<tr><td dir="ltr">'+esc(x["bank"])+'</td><td dir="ltr">'+esc(x["position"])+'</td><td dir="ltr">'+esc(x["before"])+'</td><td dir="ltr">'+esc(x["after"])+'</td></tr>' for x in a["mapping_changes"])
    source_notes=json.dumps(d,ensure_ascii=False).replace("<","\\u003c")
    template="""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Azeron — שלב ב׳, טיוטת R3</title>
<style>
:root{--ink:#182c3f;--sub:#53667a;--line:#d8e1eb;--bg:#f2f5fa;--nav:#19334e;--accent:#1a6381}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 system-ui,Arial,sans-serif}
header{background:var(--nav);color:white;padding:36px max(22px,calc((100vw - 1100px)/2))}h1{line-height:1.3;font-size:32px;margin:6px 0 16px}h2{font-size:23px;line-height:1.4;margin:0 0 15px}h3{margin-bottom:6px}
header p{max-width:1000px}.eyebrow{font-size:13px;letter-spacing:.08em;color:#bfd2e1}
main{max-width:1150px;margin:auto;padding:24px 18px 50px}section{background:white;border:1px solid var(--line);border-radius:12px;padding:26px;margin-bottom:22px}
p{margin:8px 0 16px}small,.muted{color:var(--sub)}h2 small{font-size:13px;display:inline-block;margin-right:10px}
.note{padding:16px 20px;border-right:5px solid var(--accent);background:#eef5fa;margin:18px 0}.warning{border-color:#ac7631;background:#fff4de}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px 12px;vertical-align:top;border-bottom:1px solid var(--line);text-align:right}th{background:#e9eff6}td[dir=ltr]{text-align:left}tbody tr:nth-child(even){background:#fafbfd}
.scroll,.board-scroll{overflow-x:auto}a{color:#15567d}code{direction:ltr;unicode-bidi:isolate;font-family:monospace;background:#edf2f7;padding:2px 5px}
.board{display:grid;grid-template-columns:repeat(9,92px);grid-template-rows:repeat(7,70px);gap:7px;width:884px;margin:0 auto 14px}
.key{border:1.5px solid #899aac;border-radius:7px;background:#f4f7fb;display:flex;flex-direction:column;justify-content:center;align-items:center;line-height:1.25;padding:5px 3px;text-align:center}
.key small{font-size:10px;color:#536477}.key strong{font-size:15px;overflow-wrap:anywhere;max-width:100%}.key span{height:13px;font-size:10px;color:#825115}
.selector{background:#efeaff;border-color:#927ac4}.anchor{background:#e3f2f2;border-color:#58a2a4}
.blank{background:#fff;border-style:dashed;border-color:#c4cdd9;color:#8a99a9}.changed{box-shadow:inset 0 -3px 0 #b9904f}
.stick{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border:2px solid #a6b6c8;border-radius:38%;background:#edf3f8;font-size:14px}
.stick small{font-size:10px}.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}
input,select,button{font:inherit;border:1px solid #9cafc1;background:white;padding:8px 10px;border-radius:6px;margin:4px}
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.hidden{display:none}button{cursor:pointer}bdi{direction:ltr}
@media(max-width:650px){section{padding:18px}h1{font-size:27px}main{padding:16px 10px}table{min-width:730px}}
@media print{header{background:white;color:#182c3f;padding:12px}main{padding:0}section{border:0;padding:14px;break-inside:avoid}.filters{display:none}.board{transform-origin:top right;zoom:.8}.board-scroll{overflow:visible}}
</style></head><body>
<header><div class="eyebrow">STAGE B · R3 · 2026-10-10</div><h1>ארבע שכבות — עם גישה לשילובים, לא רק מקום למקשים</h1>
<p>טיוטה חדשה למפת הכפתורים, בהמשך למחקר של 94 רשומות משחק ומערכי שליטה. מספר המשחקים לא גדל בעדכון זה: העבודה מתמקדת במפה ובביקורת שלה.</p>
<p><strong>תכנון בלבד. אין לייבא את קובצי ה־JSON שבחבילה לתוכנת Azeron. הם אינם ייצוא מקורי של v2.</strong></p></header>
<main><section><h2>מה שונה מהטיוטה הקודמת</h2>
<p>בשכבות המספרים והכלים הוצאתי את הפעולות מהעמודה שמחזיקה את בורר השכבה. נשארו שם שלושה מקומות ריקים בכל שכבה משנית — בכוונה. המטרה היא לא להציג כפתורים כזמינים רק משום שאפשר לרשום עליהם אות.</p>
<p>למספרים נוספו עותקים של Ctrl ושל Shift באצבע אחרת. בשכבת הכלים, F1–F9 נמצאים עכשיו במקומות המקבילים ל־1–9. Space, Enter ו־Esc נשארים זמינים באותם מקומות בכל ארבע השכבות, יחד עם Ctrl, Shift ו־Alt הראשיים.</p>
<p>שיניתי בבסיס רק שלוש הקצאות ביחס ל־R2: החלפה בין Alt ו־G, והוספת Backspace למקום שהיה ריק. לא הזזתי את T או Z לאגודל רק כדי לגרום למבחן מסוים להצליח.</p>
<div class="note warning"><b>יש כאן פשרות:</b> שישה מבחני גישה שהצליחו במודל של R2 אינם מקבלים מסלול נפרד ב־R3. הם מוצגים למטה. זו טיוטה שמעדיפה בנקים ברורים וגישה למספרים, לא טענה שהיא עדיפה בכל שילוב אפשרי.</div>
<p><b>78 קודים שונים</b> נכללים במערכת, כולל ארבע יציאות הסטיק. Ctrl, Shift ו־Alt הם כאן שמות לוגיים; הצד השמאלי/ימני וקודי הקלט המדויקים ייקבעו מול הייצוא האמיתי. ספרות רגילות אינן מקשי לוח המספרים.</p>
<div class="legend"><span>טורקיז: קלט משותף קבוע</span><span>סגול: בורר שכבה</span><span>קו תחתון זהוב: שינוי לעומת R2</span><span>מקווקו: ריק במכוון</span></div>
</section>
__BOARDS__
<section><h2>למה יש שני Ctrl ושני Shift בשכבת המספרים?</h2>
<p>העותק הראשי של Ctrl נמצא בעמודה השנייה, והעותק הנוסף בעמודה הרביעית. Shift הראשי בעמודה השלישית, והנוסף בעמודה השנייה. בוחרים עותק שאינו משתמש באותה אצבע של המספר.</p>
<div class="scroll"><table><thead><tr><th>שילוב</th><th>מסלול מוצע לאחר כניסה לשכבת המספרים</th><th>מה עדיין לא נבדק</th></tr></thead><tbody>
<tr><td><bdi>Ctrl+1</bdi></td><td><bdi>Ctrl @ R5C4 + 1 @ R3C2</bdi></td><td>נוחות האחיזה וכיווני הלחיצה.</td></tr>
<tr><td><bdi>Shift+2</bdi></td><td><bdi>Shift @ R5C2 + 2 @ R3C3</bdi></td><td>תזמון כניסה ושחרור שכבה.</td></tr>
<tr><td><bdi>Ctrl+Shift+8</bdi></td><td><bdi>Ctrl @ R5C4 + Shift @ R5C2 + 8 @ R1C3</bdi></td><td>השילוב כולו בזמן שהזרת מחזיקה את הבורר והאגודל מזיז את הסטיק.</td></tr>
</tbody></table></div>
<p>הבדיקה מוצאת מסלולים נפרדים ל־Ctrl, Shift ו־Ctrl+Shift עם כל הספרות 0–9 בשכבה זו, לפי השערת שיוך האצבעות. היא <b>אינה</b> הופכת את המספרים האלה לפעולות ישירות בבסיס, ואינה מודדת מהירות.</p>
<p>בתחילת בדיקה פיזית יש להשתמש בעותק אחד של כל מקש שינוי, לא בשני עותקיו יחד. יש לשחרר את המספר ואת מקש השינוי לפני שחרור בורר השכבה, עד שאופן הטיפול במקשים מוחזקים אומת בתוכנה.</p></section>
<section><h2>ביקורת ששמרה גם את הכישלונות</h2>
<div class="scroll"><table><thead><tr><th>תוצאה לפי המודל השמרני</th><th>R2</th><th>R3</th></tr></thead><tbody>
<tr><td>נמצא מסלול עם אצבעות שונות</td><td>63</td><td>90</td></tr>
<tr><td>חפיפה בין אצבעות / בורר / אגודל</td><td>41</td><td>16</td></tr>
<tr><td>המקש אינו נמצא בשכבה שנבדקה</td><td>3</td><td>1</td></tr>
</tbody></table></div>
<p>אלה <b>107 מבחני גישה שהוגדרו לצורך התכנון</b>, לא 107 בדיקות במשחק ולא מדגם המייצג את כל השימושים. 33 מבחנים קיבלו מסלול חדש, ו־6 איבדו מסלול שהיה קיים. חזרות רבות על ספרות גורמות להטיה לטובת שיפור הבנק המספרי; לכן אין להמיר את הספירה לציון איכות או לאחוז שיפור בביצועים.</p>
<p>המודל מניח שעמודות 1–4 מייצגות זרת, קמיצה, אמה ואצבע מורה. בשכבה משנית הוא מניח שהזרת כבר מחזיקה את הבורר. תנועה תופסת את האגודל. שני כפתורים באותו טור מסומנים כסיכון, <b>לא כפעולה שאדם בהכרח אינו מסוגל לבצע</b>.</p>
<h3>מה עדיין דורש פתרון או בדיקה</h3>
<p>בבסיס: <bdi>Shift+C, Shift+2, Shift+4, Ctrl+1, Ctrl+3</bdi>. בשכבת המספרים: <bdi>Alt+3, Alt+6, Alt+9</bdi>. בשכבת הכלים: <bdi>Shift+F2, Shift+F5, Shift+F8, Shift+F11</bdi>. חצים שעל האגודל מתנגשים עם הדרישה להמשיך להזיז את הסטיק באותו זמן.</p>
<p>מקש 6 נמצא בשכבת המספרים, לא בבסיס. למשל, ב־Guild Wars 2 זהו מקש הריפוי המתועד: מסלול דרך שכבה אינו מספיק כדי להכריז שדרישת ריפוי מיידי נפתרה. קודם יש לבחון שינוי קטן במקשי המשחק או בסיס המיועד לסרגל יכולות.</p>
<p><b>ששת המסלולים שאבדו:</b> <bdi>Alt+6, Alt+9, Shift+F2, Shift+F5, Shift+F8, Shift+F11</bdi>. אלו מבחני מאמץ כלליים; אין לייחס את כולם כברירות מחדל למשחק מסוים.</p>
</section>
<section><h2>שני תיקוני דיוק בדרישות המשחק</h2>
<p>ב־FAIRY TAIL 2 המדריך מגדיר מיומנויות על 2, 3 ו־4, והחזקת Tab להחלפת דף מיומנויות. לכן השילוב שנגזר לצורך בדיקה הוא <bdi>Tab+2/3/4</bdi>, ולא דרישה מאומתת של Tab עם כל 1–4. בנוסף קיימים במפורש <bdi>Space+1</bdi> לשימוש בחפץ ו־<bdi>Space+2</bdi> לבריחה. <a href="https://www.koeitecmoamerica.com/manual/fairytail2/en/2400.html">המדריך הרשמי</a>.</p>
<p>ב־osu!taiko זוגות המכות הגדולות הם <bdi>X+C</bdi> ו־<bdi>Z+V</bdi>, בהתאם לצבע. X ו־V אינם הזוג שהייתי צריך לסמן כדרישת לחיצה מקבילה. שני הזוגות הנכונים כבר מקבלים מסלול נפרד במודל הבסיס הישן והחדש; לא נוצרה בגללם מפה נוספת. <a href="https://osu.ppy.sh/wiki/en/Game_mode/osu!taiko">תיעוד הפרויקט</a>.</p>
<p>השילובים של Wo Long כגון <bdi>Shift+C</bdi> ו־<bdi>Shift+V</bdi> נלקחו מהמדריך הרשמי. הדרישה לבצע אותם גם בזמן תנועת סטיק היא מבחן מאמץ שלי, לא מדידת משחק. <a href="https://www.koeitecmoeurope.com/manual/wolong/en/2040.html">המדריך הרשמי</a>.</p>
</section>
<section><h2>מתי בכל זאת להוסיף שינוי קטן?</h2>
<p><b>חצים לצד תנועה:</b> כשצריך WASD וחצים יחד, יש שינוי בסיס אופציונלי של ארבע הקצאות בלבד: <bdi>R1C2=↑, R2C2=↓, R1C3=←, R3C3=→</bdi>. הוא מחליף את העותקים הישירים של 1–4; בנק המספרים המלא נשאר. לא הותקן שינוי כזה.</p>
<p><b>סרגל יכולות צפוף:</b> מקשי 5–0 או בחירת מטרות במקשי F עשויים להיות דחופים. קודם עדיף לבדוק שינוי ממוקד במקשי המשחק; רק אם זה לא מתאים, לפתח בסיס נוסף עם אותה משפחת שכבות. אין כאן המלצה ליצור פרופיל נפרד לכל משחק.</p>
<p><b>שלוש מול ארבע שכבות:</b> במודל המופשט עם 30 מקומות, בורר ישיר לכל שכבה נוספת, וששת המקשים המשותפים ששמרתי, הגבולות לפני כפילויות ורזרבות הם 76, 94 ו־110 קודים עבור 3, 4 ו־5 שכבות בהתאמה, כולל WASD. ההבדל מהחישוב הקודם נובע מהוספת Space ו־Enter לרשימת הקבועים. ארבע שכבות מתאימות לטיוטה זו; זו אינה הוכחה שאי אפשר לבנות פתרון אחר בשלוש.</p>
</section>
<section><h2>מה נדרש לפני קובץ לייבוא?</h2>
<p><b>קובץ JSON מקורי ועדכני של אוסף פרופילי התוכנה ב־Azeron v2</bdi></b>, עם ארבע השכבות וקישורי המעבר ביניהן. הקובץ יאפשר לבדוק מזהים, פעולות לחיצה קצרה/ארוכה, יעד שכבה והגדרות הסטיק. הוא לא מוכיח לבד נוחות פיזית או תגובת המשחק.</p>
<p>לא נמצא ייצוא v2 עדכני בחיפוש הממוקד שבוצע. כלי הגישה מרחוק הציג רק Mac מקוון, לא את מחשב המשחקים. ההעדפה ההיסטורית של V בלחיצה קצרה והחזקת 150 מילישניות לשכבה נשארת בהמתנה להתאמה למצב העדכני; לא ביטלתי אותה ולא טענתי שכבר נבדקה ב־v2.</p>
<p>השלב הבא הוא ליצור עותק מועמד עם מזהים וקישורים תקינים, תוך שמירת המקור. לאחר מכן לבדוק תחילה לחיצות ושחרורים, כולל מעבר שכבה בזמן שמקש מוחזק, ורק אחר כך משחק. אין צורך להתקין תוכנה נוספת כדי להעביר את הייצוא.</p>
<div class="note warning"><b>לא נעשה:</b> התקנת פרופיל, שינוי משחק, שינוי הגדרות מערכת, הקלטת מקשים כללית, צילום מסך, בדיקת השהיה או אימות חומרה. הדוח פועל מקומית ואינו שולח מידע או שומר הקשות.</div>
</section>
<section><h2>כל מבחני הגישה</h2>
<div class="filters"><input id="q" placeholder="חיפוש מקש או בדיקה" aria-label="חיפוש בדיקות"><select id="status"><option value="">כל התוצאות</option><option value="MODEL_ROUTE">מסלול נפרד במודל</option><option value="MODEL_CONFLICT">חפיפה</option><option value="NOT_IN_BANK">חסר בשכבה</option></select><span id="count"></span></div>
<div class="scroll"><table id="tests"><thead><tr><th>בדיקה</th><th>שכבה</th><th>מקשים</th><th>גם תנועה</th><th>R2</th><th>R3</th><th>מסלול / סיבה</th><th>סוג דרישה</th></tr></thead><tbody>__CASES__</tbody></table></div></section>
<section><h2>כל שינויי המיפוי לעומת R2</h2><div class="scroll"><table><thead><tr><th>שכבה</th><th>מקום חזותי</th><th>לפני</th><th>אחרי</th></tr></thead><tbody>__CHANGES__</tbody></table></div></section>
<section><h2>מקורות וגבולות הראיות</h2><p>מקורות המשחקים שנפתחו מחדש תומכים בדרישות המסומנות בלבד. יתר קטלוג R2 לא עבר בסבב זה בדיקה מקוונת מלאה. מסמכי Azeron כלליים אינם מאמתים את הגרסה המותקנת אצלך.</p>
<div class="scroll"><table><thead><tr><th>מזהה</th><th>מקור</th><th>מה הוא תומך בו</th><th>מגבלה</th></tr></thead><tbody>__SOURCES__</tbody></table></div></section>
</main><script>
const q=document.getElementById('q'),status=document.getElementById('status');
function apply(){let n=0;document.querySelectorAll('#tests tbody tr').forEach(r=>{const ok=(!status.value||r.dataset.status===status.value)&&r.textContent.toLowerCase().includes(q.value.trim().toLowerCase());r.hidden=!ok;if(ok)n++;});document.getElementById('count').textContent=n+' בדיקות מוצגות';}
q.addEventListener('input',apply);status.addEventListener('change',apply);apply();
</script></body></html>"""
    # Keep sources and map values generated from the same JSON source.
    report=(template.replace("__BOARDS__","".join(boards)).replace("__CASES__","".join(case_rows))
                    .replace("__CHANGES__",changes).replace("__SOURCES__",source_rows))
    report=report.replace("ב־Azeron v2</bdi></b>","ב־Azeron v2</b>")
    for code,oldn,newn in [("MODEL_ROUTE",63,90),("MODEL_CONFLICT",41,16),("NOT_IN_BANK",3,1)]:
        report=report.replace(f"<td>{oldn}</td><td>{newn}</td>",
            f'<td>{a["r2_status_counts"].get(code,0)}</td><td>{a["r3_status_counts"].get(code,0)}</td>')
    report=report.replace("107 מבחני גישה",str(a["case_count"])+" מבחני גישה")
    report=report.replace("33 מבחנים קיבלו מסלול חדש",str(len(a["new_model_routes"]))+" מבחנים קיבלו מסלול חדש")
    report=report.replace("ו־6 איבדו מסלול", "ו־"+str(len(a["lost_model_routes"]))+" איבדו מסלול")
    policy="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'"
    report=report.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="'+html.escape(policy,quote=True)+'">')

    target=folder/"Azeron_Stage_B_R3_HE.html"
    target.write_text(report,encoding="utf-8")
    return target

if __name__=="__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent))
