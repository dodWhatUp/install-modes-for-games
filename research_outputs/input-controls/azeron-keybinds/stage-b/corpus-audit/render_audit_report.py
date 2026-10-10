#!/usr/bin/env python3
"""Render the inherited-corpus audit as an offline Hebrew report.
No keyboard listeners, network requests, input injection, or profile writes.
"""
from pathlib import Path
import html, json, sys

def render(folder: Path) -> Path:
    report=json.loads((folder/'CORPUS_AUDIT_R4.json').read_text())
    checks=json.loads((folder/'source_checks.json').read_text())
    esc=lambda x:html.escape(str(x),quote=True)
    fresh={rid:[] for c in checks['checks'] for rid in c['row_ids']}
    for c in checks['checks']:
        for rid in c['row_ids']:fresh[rid].append(c['id'])
    flags={
      'FINGER_MODEL_CONFLICT':'חפיפת אצבעות במודל',
      'NO_SINGLE_BANK':'רכיבי השילוב אינם באותה שכבה',
      'UNMAPPED_OUTPUT':'קוד פלט אינו כלול בטיוטה',
      'SYMBOL_LAYOUT_REVIEW':'סימן שתלוי בפריסת המקלדת',
      'STICK_COMMAND_ROUTE':'הסטיק מפיק פקודה שאינה תנועה',
      'MANUAL_REVIEW':'ביטוי שדורש עיון ידני',
      'LAYERED_BUTTON_ROUTE':'מסלול דרך שכבה',
      'DIRECT_BUTTON_ROUTE':'מסלול ישיר בבסיס',
      'STICK_DIRECTIONAL_ROUTE':'קלט כיווני דרך הסטיק',
      'MOUSE_ONLY':'עכבר בלבד'}
    flag_rows=[]
    for code in ['NO_SINGLE_BANK','FINGER_MODEL_CONFLICT','UNMAPPED_OUTPUT','SYMBOL_LAYOUT_REVIEW','STICK_COMMAND_ROUTE','MANUAL_REVIEW']:
        rr=[r for r in report['records'] if (r['syntax']['status']==code or any(v['isolated']['status']==code for v in r['variants']))]
        flag_rows.append([flags[code],len(rr),len({r['row']['game'] for r in rr})])
    def table(headers,rows):
        return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    source_rows=[]
    for c in checks['checks']:
        source_rows.append('<tr><td dir="ltr">'+esc(c['id'])+'</td><td>'+esc(c['source_fact'])+'</td><td>'+esc(c['limit'])+'</td><td><a href="'+esc(c['url'])+'" target="_blank" rel="noopener noreferrer">מקור</a></td></tr>')
    rows=[]
    for r in report['records']:
        codes=sorted({v['isolated']['status'] for v in r['variants']})
        if r['syntax']['status']!='PARSED':codes=['MANUAL_REVIEW']
        rows.append({'row':r['row'],'syntax':r['syntax'],'variants':r['variants'],
                     'codes':codes,'r4_recheck_ids':fresh.get(r['row']['id'],[])})
    payload=json.dumps({'rows':rows,'games':report['games'],'labels':flags},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    s=report['summary']
    text=r'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>Azeron — R4: בדיקת מפת R3 מול מיפויי המשחקים</title><style>
:root{--ink:#183147;--muted:#52677a;--line:#dbe4eb;--paper:#fff;--bg:#f2f6fa;--blue:#173c59;--warn:#fff3dc}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:16px/1.8 system-ui,Arial,sans-serif;color:var(--ink)}
header{background:var(--blue);color:white;padding:42px max(20px,calc((100vw - 1120px)/2))}header p{max-width:1000px;margin:12px 0}h1{font-size:34px;line-height:1.3;margin:10px 0 20px}h2{font-size:24px;line-height:1.4;margin:0 0 16px}h3{font-size:19px;margin:24px 0 8px}.eyebrow{font-size:13px;letter-spacing:.08em;color:#c1d7e8}
nav{background:white;padding:12px 20px;display:flex;gap:23px;flex-wrap:wrap;border-bottom:1px solid var(--line)}nav a{font-weight:650;text-decoration:none}
main{max-width:1160px;margin:auto;padding:25px 18px 60px}section{padding:28px;background:var(--paper);border:1px solid var(--line);border-radius:12px;margin-bottom:24px}p{margin:8px 0 16px}a{color:#185b86}small,.muted{color:var(--muted)}code,bdi{direction:ltr;unicode-bidi:isolate}code{font:14px/1.7 ui-monospace,Consolas,monospace;background:#eaf1f7;padding:3px 6px;border-radius:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:5px 0 22px}.stat{padding:10px 16px;border-right:3px solid #5c8da8}.stat b{display:block;font-size:30px;line-height:1.2}.stat small{display:block;font-size:13px;margin-top:7px}
.note{padding:16px 20px;background:#edf5fb;border-right:4px solid #3b7d9c;margin:18px 0}.warning{background:var(--warn);border-color:#ad7c32}
.table-scroll{overflow:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:11px 13px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}th{background:#e9f0f6}tbody tr:nth-child(even){background:#f8fafc}td[dir=ltr]{text-align:left}details{border:1px solid var(--line);padding:10px 14px;border-radius:6px;margin:12px 0}summary{font-weight:650;cursor:pointer}
.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:center}input,select,button{font:inherit;font-size:14px;padding:10px 12px;border:1px solid #a0b4c5;border-radius:6px;background:white;max-width:100%}input{flex:1;min-width:240px}button{cursor:pointer;background:#e9f1f8}#rows td:first-child{min-width:170px}#rows td:nth-child(3){min-width:145px}#rows td:nth-child(5){min-width:210px}pre{direction:ltr;text-align:left;white-space:pre-wrap;font:12px/1.6 monospace;overflow-wrap:anywhere;max-height:330px;overflow:auto;background:#edf2f6;padding:10px}footer{font-size:13px;color:var(--muted);padding:0 8px}.pill{font-size:12px;background:#e8f2f5;border-radius:4px;padding:2px 5px;display:inline-block;margin:2px}
@media(max-width:650px){h1{font-size:27px}.stats{grid-template-columns:1fr 1fr}section{padding:18px}main{padding:18px 10px}nav{gap:13px}}
@media print{nav,.filters,button{display:none}body{background:white}header{background:white;color:#183147;padding:12px}section{border:0;break-inside:avoid;padding:12px}main{padding:0}.table-scroll{overflow:visible}}
</style></head><body><header><div class="eyebrow">AZERON · CORPUS AUDIT R4 · 2026-10-10</div><h1>בדיקת מפת R3 מול מיפויי המשחקים שנאספו</h1>
<p>לא עוד סידור חדש של כפתורים: המפה נשארה ללא שינוי. הפעם נבדקו הביטויים שנשמרו בכל קטלוג R2, כדי להבחין בין בעיית תכנון שמופיעה במשחקים, מבחן מאמץ כללי ומידע שעדיין אינו ידוע.</p>
<p><strong>זהו דוח ביקורת, לא פרופיל Azeron ולא קובץ לייבוא. לא בוצע שינוי במכשיר או במשחק.</strong></p></header>
<nav><a href="#overview">התוצאה</a><a href="#findings">הממצאים החשובים</a><a href="#decision">מה עושים עם המפה</a><a href="#method">גבולות הבדיקה</a><a href="#catalogue">חיפוש במיפויים</a><a href="#next">הקלט הנדרש</a></nav><main>
<section id="overview"><div class="stats"><div class="stat"><b>__GAMES__</b><small>רשומות משחק / מהדורה / מערך</small></div><div class="stat"><b>__ROWS__</b><small>מיפויים שנכללו בבדיקה</small></div><div class="stat"><b>__PARSED__</b><small>ביטויי מקשים שפוענחו לפי הכללים</small></div><div class="stat"><b>__MANUAL__</b><small>ביטויים שנשארו לעיון ידני</small></div></div>
<h2>המסקנה: המבנה המשותף שימושי, אך עדיין צריך טיפול בחריגים</h2>
<p>ארבע השכבות הן מסגרת תכנון סבירה להמשך, לא מפה שהוכחה כמתאימה לכל המשחקים. הבדיקה מצביעה על שלושה חסמים שונים: מקש שקיים אבל קשה לשלב אותו באותה יד; רכיבים של אותו שילוב שנמצאים בשכבות שונות; וקוד שאינו מופיע בטיוטה בכלל. הוספת שכבה פותרת רק חלק מהבעיות האלה.</p>
<div class="note warning"><b>אין כאן ציון איכות או אחוז תאימות.</b> שורה יכולה לציין כמה פעולות, כמה ברירות או טווח מקשים. מציאת מסלול לקוד אינה מוכיחה שהפעולה מהירה, נוחה או שמישה במשחק. המקורות ההיסטוריים לא הפכו לעדכניים רק כי הקוד עבר עליהם.</div>
__FLAG_TABLE__
<p class="muted">הספירות בטבלה הן שורות שבהן סומן לפחות מקרה אחד, ומספר המשחקים שבהם הן מופיעות. הקבוצות עשויות לחפוף. חלופה חסרה בתוך שורה אינה בהכרח פעולה חסרה: למשל, Enter עשוי להיות זמין גם כאשר Numpad Enter אינו ממופה.</p></section>
<section id="findings"><h2>הממצאים שמשנים את דרך היישום</h2>
<h3>1. גם אות רגילה יכולה לשמש מקש החזקה של המשחק</h3>
<p>ב־Atelier Yumia המדריך מראה <bdi>C+1 / C+2 / C+3 / C+4</bdi> להחלפת דמות. האות C אינה מקש שינוי של Windows, אך מבחינת הגישה הפיזית היא ממלאת כאן תפקיד דומה. <a href="https://www.gamecity.ne.jp/manual/3Tr5Fw2Y/en/2400.html">המדריך הרשמי</a>.</p>
<p>במפת R3, C ו־2 וגם C ו־4 נמצאים באותה עמודה משוערת של האמה. העותקים הנוספים של Ctrl ו־Shift בשכבת המספרים אינם פותרים זאת, מפני שבאותה שכבה אין C. זו סיבה לבדוק את זוגות הלחיצה האמיתיים לפני שמקבעים את הבסיס.</p>
<h3>2. קיום שני מקשים במערכת אינו מבטיח שקיים שילוב</h3>
<p>ברשומה השמורה של Elden Ring מופיע <bdi>E + arrow keys</bdi> לקיצור של הנרתיק. בטיוטת R3 יש E בבסיס, והחצים נמצאים בשכבת האותיות. לכן הבדיקה אינה מוצאת שכבה אחת שמכילה את השילוב. <b>זוהי מסקנה מהרשומה הקיימת; ברירת המחדל לא אומתה מחדש במקור רשמי בסבב זה.</b></p>
<p>אין להניח שהחזקת E לפני מעבר שכבה תשאיר אותו פעיל כראוי: התנהגות המעבר והשחרור עדיין לא ידועה. הפתרון העתידי יכול להיות העתק קטן של מקש או שינוי נקודתי במשחק — לא בהכרח פרופיל נפרד.</p>
<h3>3. WASD על הסטיק אינם ארבעה כפתורי פקודות עצמאיים</h3>
<p>ב־OpenTTD, למשל, A מפעיל Autorail ו־W משמש להרמת הקרקע בכלי עיצוב הנוף; החצים משמשים להזזת המפה. אלה תפקידים שונים מתנועת דמות רגילה. <a href="https://wiki.openttd.org/en/Manual/Hotkeys">תיעוד הפרויקט</a>.</p>
<p>הסימון ״W קיים דרך הסטיק״ אינו מספיק: הפקודה עלולה לתפוס את אותו אגודל שאמור להזיז את המצלמה, או להיות פחות נוחה ללחיצה מתוזמנת. חלק מ־51 השורות שסומנו בקטלוג הן פקודות שאפשר לבצע בנחת, וחלק עשויות להצדיק בסיס פקודות אחר. השיוך הראשוני נעשה לפי שם הפעולה ודורש שיקול דעת.</p>
<h3>4. חלק מהפשרות של R3 מופיעות גם במקורות משחק ממשיים</h3>
<p>בתיעוד OpenTTD מופיעים <bdi>Shift+F2</bdi> לרשימת כלי הרכב ו־<bdi>Shift+F8</bdi> לסרגל בניית הכבישים. אלה שניים מדפוסי השילוב שאיבדו מסלול נפרד במודל של R3 לעומת R2. אין לפטור אותם כמבחנים תאורטיים בלבד.</p>
<p>ב־Wo Long מתועד גם <bdi>Shift+C</bdi>, שהבעיה שלו נמצאת בבסיס ולא בבנק המספרים. לכן ״שיפרנו את Ctrl/Shift עם הספרות״ אינו שקול לשיפור של כל צירופי ההחזקה. <a href="https://www.koeitecmoeurope.com/manual/wolong/en/2040.html">המדריך הרשמי</a>.</p>
<h3>5. מקש חסר וסימן שתלוי בפריסה הם שתי בעיות שונות</h3>
<p>קודים כמו <bdi>Numpad 1</bdi> אינם הספרה הרגילה 1 בטיוטה. לעומתם, סימנים כמו +, ~ או ? עשויים להיות מופקים באמצעות שילוב מקשים, בהתאם לפריסת המקלדת ולאופן שבו המשחק מזהה קלט. הבדיקה משאירה אותם כ״דרוש אימות פריסה״, ולא קובעת שהם בהכרח בלתי אפשריים.</p>
<p>אין צורך להוסיף בנק מקשי לוח מספרים רק כדי להעלות ספירת כיסוי. תחילה בודקים אם המשחק שבאמת צריך אותם מציע חלופה מתאימה או שינוי מקש.</p>
<h3>6. מסלול דרך שכבה אינו פתרון לדרישה של תגובה מיידית</h3>
<p>Guild Wars 2 מתעד ריפוי על 6. ב־R3 יש ל־6 מסלול בשכבת המספרים, אך אין עותק ישיר בבסיס. לכן הנגישות הלוגית עברה, והדרישה השמרנית לריפוי מיידי עדיין לא נפתרה. המדריך גם מתאר התאמת מקשי המשחק, כך שאפשר לבחון שינוי ממוקד לפני יצירת משפחת מפות חדשה. <a href="https://www.guildwars2.com/en/new-player-guide/">המדריך הרשמי</a>.</p></section>
<section id="decision"><h2>מה לעשות עם R3 בעקבות הבדיקה</h2>
<p><strong>לא לשנות שוב את כל המפה ללא בדיקה פיזית.</strong> יש לשמור את ארבעת הבנקים כטיוטת העבודה, ולתקן רק דרישות רלוונטיות שהן בעייתיות בפועל. הקטלוג מספק דוגמאות ובדיקות, לא הוראה להתאים עכשיו 94 משחקים.</p>
__DECISION_TABLE__
<p>כשהמשחק תומך בכך, שינוי נקודתי במקשי המשחק יכול לשמור את מפת ה־Azeron המשותפת. כאשר ההבדל מבני — למשל פקודות אותיות עצמאיות לצד תנועת מצלמה — בסיס כללי לסוג השליטה עשוי להיות הגיוני יותר משכבה איטית נוספת. אלה אפשרויות לבחינה, לא שינויים שבוצעו.</p></section>
<section id="method"><h2>מה הבדיקה עושה — ומה לא</h2>
<p>הקוד פענח את כל 2,195 הרשומות מתוך קובץ ה־HTML הקיים של R2, בלי להריץ את הסקריפט שבתוכו ובלי לשנות אף שדה מקורי. זהו עותק תצוגה נגזר שמכיל את הרשומות; הוא אינו שחזור של הקובץ הראשי המקורי. מפת R3 נבדקה באמצעות טביעת Git ונשארה זהה.</p>
<p>טווחים ורשימות מפורשים הורחבו ל־3,106 וריאציות קלט לצורכי בדיקה. אין להתייחס אליהן כאל 3,106 פעולות משחק נפרדות. רצף כגון <bdi>A then LMB</bdi>, מספר שלא פורט, או היקף לא ברור של מקש החזקה נשארו לעיון ידני.</p>
<p>המודל בודק שכבה אחת בכל פעם, מניח אצבע נפרדת לכל קלט שמוחזק במקביל, ומקצה את הזרת לבורר שכבה מוחזק לאחר זיהויו. המקשים שעל האגודל חולקים משאב עם הסטיק. זהירות זו יכולה להחמיר עם שני מתגים שבפועל אפשר להפעיל באותה אצבע; היא אינה הוכחת חוסר יכולת.</p>
<p>נשמרה הבחנה בין דרישה מקורית לבין מבחן נוסף בזמן תנועה. בצירופים שמציינים Left/Right Ctrl, Shift או Alt, המסלול הוא לוגי בלבד עד שנדע איזה צד מופק בייצוא המקורי. העכבר נחשב לקלט של היד האחרת, ללא בדיקת נוחות או ציוד.</p>
<div class="note"><b>מגבלה נוספת שחשוב לשמר:</b> בדיקת כל השורות אינה בדיקה של כל הקשרים בין שורות. ב־FAIRY TAIL 2, למשל, החזקת Tab להחלפת דף מיומנויות ומקשי 2/3/4 מופיעים בשורות נפרדות; השילוב ביניהם נגזר מקריאת ההקשר. תרחיש כזה נשמר בבדיקות R3 הקודמות, אך אינו מתגלה אוטומטית רק מפענוח שורה בודדת. <a href="https://www.koeitecmoamerica.com/manual/fairytail2/en/2400.html">המקור</a>.</div>
<p>נבדקו מחדש 14 רשומות ממוקדות בחמישה משחקים מול חמישה מקורות ראשוניים, ובנוסף נקרא דף היצרן על הייצוא. יתר 2,181 הרשומות לא עברו אימות מקוון מלא בסבב R4. גיל המקור, גרסת המשחק, תדירות השימוש והנוחות הפיזית נשארים צירי בדיקה נפרדים.</p></section>
<section id="catalogue"><h2>חיפוש בכל המיפויים ותוצאות הגישה</h2>
<p>בחר משחק או סוג בעיה. ״מסלול״ כאן פירושו תוצאה לוגית במודל בלבד. בכל שורה אפשר להרחיב את פירוט השילובים, התנועה והמקור. שדה ״בדיקה קודמת״ מוצג כפי שנשמר ב־R2; בדיקות R4 מסומנות בנפרד.</p>
<div class="filters"><input id="query" placeholder="שם משחק, פעולה, מקש או מזהה" aria-label="חיפוש"><select id="game" aria-label="משחק"><option value="">כל המשחקים</option></select><select id="status" aria-label="תוצאת הבדיקה"><option value="">כל התוצאות</option></select><button id="reset">ניקוי</button></div>
<p id="count" role="status" class="muted"></p><div class="table-scroll"><table id="rows"><thead><tr><th>משחק</th><th>פעולה / הקשר</th><th>ביטוי מקשים מקורי</th><th>תוצאות</th><th>מקור ופירוט</th></tr></thead><tbody></tbody></table></div><button id="more">הצג 80 נוספות</button>
<noscript>אפשר לעיין בכל התוצאות גם בקובץ CORPUS_AUDIT_R4.json שבחבילה. הסינון בדוח זקוק ל־JavaScript מקומי.</noscript></section>
<section id="next"><h2>המעבר מתכנון ליישום: נדרש ייצוא מקורי אחד</h2>
<p>לא נמצא ייצוא v2 עדכני בתיקיית ה־Azeron שנבדקה; הקבצים המקוריים הזמינים שם הם הגיבויים ההיסטוריים מ־15 בספטמבר. בחיבור המרוחק הופיע רק Mac, לא מחשב המשחקים. צילום ארבע שכבות אינו כולל את כל מזהי הפרופילים, מחוות הלחיצה וקישורי המעבר.</p>
<p><strong>יש לייצא מתוך Azeron Software v2 את אוסף פרופילי התוכנה הפעיל ל־JSON, עם כל ארבע השכבות וקישורי המעבר, ולהעלות את הקובץ המקורי לצ׳אט.</strong> היצרן מתאר גיבוי באמצעות ייצוא JSON. אין צורך לשנות או למחוק פרופיל לצורך זה. <a href="https://azeron.com/pages/software">תיעוד Azeron</a>.</p>
<p>לאחר קריאת הייצוא יהיה אפשר להתאים את המפה למזהי החומרה ולמחוות הקיימות, ליצור עותק מועמד נפרד ולבדוק קודם לחיצות ושחרורים. עד אז לא מופק קובץ לייבוא ולא מבוטלת העדפת הלחיצה הקצרה/ההחזקה ההיסטורית.</p>
<p>הבדיקות הפיזיות הראשונות יהיו ממוקדות: C עם 2/4, Shift עם C, Ctrl עם ספרה, Shift עם F2/F8, שחרור שכבה כשקלט היה מוחזק, ותנועה בזמן פעולה באזור האגודל. אין להריץ את הצירופים בתוך משחק או יישום שבו הם גורמים לפעולה לא רצויה רק כדי לבדוק נוחות.</p></section>
<section><h2>בדיקות המקור הממוקדות</h2><p>הטבלה מגדירה בדיוק מה אומת מחדש. שורות וממצאים אחרים נשענים על האיסוף השמור; הם לא קיבלו אוטומטית מעמד של ברירת מחדל עדכנית.</p><div class="table-scroll"><table><thead><tr><th>בדיקה</th><th>עובדה שנתמכת במקור</th><th>גבול האימות</th><th>קישור</th></tr></thead><tbody>__SOURCE_ROWS__</tbody></table></div></section>
<footer>R4 הוא אובייקט ביקורת נגזר של R3 ושל קטלוג R2. מפת המקור לא שונתה, AI_MASTER.json לא אוחד ולא נכתב מחדש. הדוח אינו מאזין להקשות מערכת, אינו שומר נתונים בדפדפן ואינו שולח מידע.</footer>
</main><script>
const data=__DATA__;
const $=id=>document.getElementById(id),q=$('query'),game=$('game'),status=$('status'),body=document.querySelector('#rows tbody');let limit=80;
const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function addOption(el,value,label){const o=document.createElement('option');o.value=value;o.textContent=label;el.append(o)}
data.games.forEach(g=>addOption(game,g.game,g.game));Object.entries(data.labels).forEach(([k,v])=>addOption(status,k,v));
function apply(){const term=q.value.trim().toLowerCase();const matched=data.rows.filter(x=>(!game.value||x.row.game===game.value)&&(!status.value||x.codes.includes(status.value))&&(!term||[x.row.game,x.row.action,x.row.key,x.row.id].join(' ').toLowerCase().includes(term)));
 body.innerHTML=matched.slice(0,limit).map(x=>{const r=x.row;const source=/^https:\/\//.test(r.source_url)?'<a target="_blank" rel="noopener noreferrer" href="'+esc(r.source_url)+'">מקור הרשומה</a>':'אין קישור HTTPS';return '<tr data-id="'+esc(r.id)+'"><td>'+esc(r.game)+'<br><small>'+esc(r.family)+'</small></td><td>'+esc(r.action)+'<br><small>'+esc(r.context)+'</small></td><td dir="ltr">'+esc(r.key)+'</td><td>'+x.codes.map(c=>'<span class="pill">'+esc(data.labels[c])+'</span>').join(' ')+'</td><td>'+source+'<br><small>'+esc(r.provenance_kind)+'<br>בדיקה קודמת: '+esc(r.source_recheck)+'</small><br><strong>'+ (x.r4_recheck_ids.length?'R4: נבדק במיקוד המסומן':'R4: מקור שלא נבדק מחדש')+'</strong><details><summary>פירוט ותנאים</summary><p>'+esc(r.note)+'</p><p>מחווה שנשמרה: <bdi>'+esc(r.gesture)+'</bdi></p><pre>'+esc(JSON.stringify({id:r.id,syntax:x.syntax,variants:x.variants,r4_recheck_ids:x.r4_recheck_ids},null,2))+'</pre></details></td></tr>'}).join('');
 $('count').textContent=matched.length+' רשומות מתאימות; '+Math.min(limit,matched.length)+' מוצגות.';$('more').hidden=matched.length<=limit;}
[q,game,status].forEach(el=>el.addEventListener('input',()=>{limit=80;apply()}));$('reset').addEventListener('click',()=>{q.value='';game.value='';status.value='';limit=80;apply()});$('more').addEventListener('click',()=>{limit+=80;apply()});apply();
</script></body></html>'''
    decisions=[['שילוב דחוף שקיים רק בחלקיו','בודקים העתק קטן או שינוי ממוקד במקשי המשחק. אין להניח שכניסה לשכבה תוך החזקה עובדת.'],
      ['אותיות רבות משמשות פקודות, לא תנועה','בוחנים בסיס פקודות/רשת אותיות כללי, עם תנועת מצלמה נפרדת לפי המשחק.'],
      ['מקשי לוח מספרים ייחודיים','בודקים אם נדרשים בפועל ואם קיימת חלופה לפני הוספת בנק מלא.'],
      ['פעולה איטית שנוחה גם דרך שכבה','משאירים בבנק המשפחתי; לא מקריבים עבורה כפתור בסיס דחוף.'],
      ['בעיה שמבוססת רק על השערת אותה אצבע','ממתינים לבדיקה קצרה ביד ולא מכריזים שהשילוב בלתי אפשרי.']]
    replacements={'__GAMES__':str(s['games']),'__ROWS__':f"{s['rows']:,}",'__PARSED__':f"{s['syntax_status']['PARSED']:,}",
      '__MANUAL__':str(s['syntax_status']['MANUAL_REVIEW']),'__FLAG_TABLE__':table(['סוג הדגל','רשומות','משחקים'],flag_rows),
      '__DECISION_TABLE__':table(['סוג הבעיה','כיוון הטיפול לפני התקנה'],decisions),
      '__SOURCE_ROWS__':''.join(source_rows),'__DATA__':payload}
    for a,b in replacements.items():text=text.replace(a,b)
    dest=folder/'Azeron_R4_Game_Access_Audit_HE.html';dest.write_text(text,encoding='utf-8')
    return dest
if __name__=='__main__':print(render(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent))
