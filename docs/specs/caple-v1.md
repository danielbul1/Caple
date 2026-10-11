# Caple v1: אפליקציית HOD/LOD בסגנון QuantiStat מעל המנוע הקיים

## Problem Statement

אני סוחר ES ורוצה לדעת איפה צפויים ה-HOD וה-LOD של היום ומתי. הכלי שאני מכיר, QuantiStat, נותן את זה בחוויה נוחה: סרגל צד עם מודולים, טופס, כפתור Visualize ומפת חום. אבל המספרים שלו לא כנים. הוא עובד בנקודות גולמיות בלי סרגל, ולכן רמת ה-"75%" שלו הושגה ב-86% מהימים. "רצועה בהירה" אצלו היא שכיח של היסטוגרמה רועשת, ולכן בעיקר רעש. הוא נותן תשובה רק לפני הפתיחה, ואין לו שום רקורד שנרשם מראש, כך שכל צילום "פגיעה" שלו צויר בדיעבד.

אצלי כבר קיים מנוע מכויל ונבדק (רמות הגעה לפי סרגל, ימים דומים במהלך היום, "כבר נקבע"), אבל הוא מפוזר: דף אחד שמציג מודול אחד, וכל השאר סקריפטים שרצים מהטרמינל ושומרים תמונות. אין לי מוצר אחד שמרגיש כמו QuantiStat ומראה את התחזיות הכנות שלי.

## Solution

אפליקציית אינטרנט מקומית בשם **Caple**, באנגלית, עם המבנה והאווירה של QuantiStat: רקע שחור, סרגל צד עם אריחי מודולים בשתי קבוצות (HOD/LOD ו-Bias), כרטיס טופס כהה, כותרת עם מעבר צבע וכפתור Visualize. התוצאה מופיעה בתוך הדף ולא בחלון נפרד.

ארבעה מודולים: **Price Based**, **Time Based**, **Level Validator** ו-**Bias**. כולם עובדים על ES בלבד. כל מודול שמציג חיזוי מציג לידו את אחוז ההצלחה ההיסטורי שלו, שנמדד ב-walk-forward.

שלושה מצבי זמן: לפני הפתיחה, בורר שעה לכל יום בעבר ("אחרי נר 9:00"), ומצב חי להיום שמתעדכן אחרי כל נר.

ב-Price Based יש שדה Mode בטופס (לצד Symbol, End Date ו-Time) עם **מצב QuantiStat**, וב-Time Based יש מתג **מצב QuantiStat** בתוך המסך. הוא מחליף את המנוע במחקה של השיטה שלהם, כדי שאפשר יהיה להשוות על אותו יום. ההבדל היחיד בין המצבים הוא הסרגל וחלון ה-Period, ולכן כל הבדל במפה מראה מה הסרגל שווה.

## User Stories

### מעטפת וניווט

1. As a trader, I want the app to open at a local address in my browser, so that I can use it without installing anything new.
2. As a trader, I want a dark interface in the layout of QuantiStat (sidebar with module tiles, form card, Visualize button), so that it feels like the tool I'm used to.
3. As a trader, I want the app to be named Caple with its own logo, so that it is clearly my tool and not a copy of someone else's brand.
4. As a trader, I want the sidebar grouped into "HOD/LOD" (Price Based, Time Based, Level Validator) and "Bias" (Seasonal, Intraday), so that I can find each module quickly.
5. As a trader, I want the selected tile to look highlighted, so that I know which module I'm in.
6. As a trader, I want each module to show a short title and description next to the form, as QuantiStat does, so that I remember what it answers.
7. As a trader, I want the results to appear inside the page under or beside the form, so that I don't have to manage pop-up windows.
8. As a trader, I want the whole interface in English, so that it matches QuantiStat and the trading terms I use.
9. As a trader, I want the app to show only ES in this version, so that I only see forecasts that were calibrated and tested.
10. As a trader, I want the symbol to be shown on the form (fixed to ES), so that it's clear which instrument the forecast is for.

### מצבי זמן

11. As a trader, I want to pick an End Date (the day before the day I want to forecast), so that I can look at any day in the past or today.
12. As a trader, I want a calendar picker for the End Date, so that I can choose a date easily.
13. As a trader, I want to choose "before the open" or "after the H:00 candle" for any day, so that I can see what the engine knew at each hour.
14. As a trader, I want a live mode for today that refreshes on its own after every candle, so that I can follow the day without pressing anything.
15. As a trader, I want the live mode to show only candles that LSE has already closed, so that I never see a forecast built from incomplete data.
16. As a trader, I want the hour picker to use only data known up to that hour, so that I can't fool myself with hindsight when looking at the past.
17. As a trader, I want QuantiStat mode to offer only "before the open", so that the comparison matches what QuantiStat actually does.

### Price Based

18. As a trader, I want a heatmap of where the HOD and LOD of similar past days ended, measured in points from the 00:00 open, so that I can see the shape of today's likely high and low.
19. As a trader, I want HOD above 0 and LOD below 0 on the same chart, so that I read it the same way as QuantiStat.
20. As a trader, I want the heatmap in 1-point cells, so that it matches the points axis.
21. As a trader, I want brighter and thicker lines where more days ended, so that repeated levels stand out.
22. As a trader, I want adjacent bright cells to look like one band, so that I can read a band the way I do in QuantiStat.
23. As a trader, I want cells with a single day hidden, so that the map isn't buried in noise.
24. As a trader, I want a color scale showing how many days each color means, so that I can tell 2 days from 10.
25. As a trader, I want the map clean, without computed lines drawn on it, so that I read it by eye as I'm used to.
26. As a trader, I want hovering over the map to show only the distance in points from the open, as QuantiStat does, so that the view stays simple.
27. As a trader, I want, in the default mode, each past day's distance measured in its own yardstick and converted to today's points, so that days from calm and wild periods and from different price levels are comparable.
28. As a trader, I want the default mode to use all the history up to the End Date, so that the map rests on as many days as possible.
29. As a trader, I want, after an hourly candle, the heatmap to show where similar days that went past the high/low so far ended, so that the map updates with what the day has already done.
30. As a trader, I want the high/low so far and the open marked on the map during the day, so that I can see where the day stands.
31. As a trader, I want a Mode field (Default / QuantiStat) next to Symbol, End Date and Time in the Price Based form, so that I can compare the two methods on the same day.
32. As a trader, I want QuantiStat mode to use raw points with no yardstick, so that the map looks like theirs.
33. As a trader, I want QuantiStat mode to show the Period field (3mo/6mo/1y/2y/ytd/max) with 2y as default, so that I can reproduce their settings.
34. As a trader, I want the Period window measured back from the End Date, not from today, so that the same input always gives the same map.
35. As a trader, I want the Period field hidden when QuantiStat mode is off, so that I'm not tempted to pick a window that makes the forecast worse.
36. As a trader, I want both modes to use 00:00 New York as the day boundary and 1-point cells, so that the only difference I see is the yardstick and the window.

### Time Based

37. As a trader, I want a histogram of the hour at which the HOD was set and one for the LOD, so that I know when the extremes usually come.
38. As a trader, I want, before the open, the histograms to cover all similar days, so that I see the day's general timing.
39. As a trader, I want, during the day, the chance that the HOD/LOD is already in shown first, so that I know whether there is anything left to wait for.
40. As a trader, I want, during the day, the histogram to show at which hour the HOD/LOD is likely to come if it isn't in yet, among similar days, so that I know when to watch.
41. As a trader, I want the chance that the HOD hour has already passed to equal the "already in" figure, so that Time Based and Price Based never contradict each other.
42. As a trader, I want a hit rate shown next to the Time Based forecast (how often the most likely hour, ± one hour, was right in walk-forward), so that I know how much the histogram is worth.
43. As a trader, I want that hit rate compared with a baseline (a random walk's timing and always picking the most common hour), so that I know whether the histogram beats chance.
44. As a trader, I want a QuantiStat mode toggle in Time Based that shows their four histograms (HOD/LOD if bullish/bearish bias), so that I can compare with what I used to see.

### Level Validator: יומן אמינות

45. As a trader, I want a reliability journal that shows, for each day and checkpoint, the levels as they were set before that time, so that I can see the forecast was not drawn in hindsight.
46. As a trader, I want each level marked as reached or not, and whether the HOD/LOD landed in the 75–25% band, so that I can check every call.
47. As a trader, I want a running record for a date range (for example "75% level reached on 76% of days"), so that I can see whether the levels keep their promise.
48. As a trader, I want the journal to include the days the forecast was wrong, so that the record is honest and not a highlight reel.
49. As a trader, I want a QuantiStat mode column in the journal, so that I can see both methods' record on the same days.
50. As a trader, I want to pick the date range of the journal, so that I can check recent weeks or the whole history.
51. As a trader, I want the journal to update every trading day on its own, so that I don't have to run anything.

### Level Validator: בדיקת רמה

52. As a trader, I want to type a price and get the chance that today's HOD (if above price) or LOD (if below) reaches it, so that any level I find (by eye, from a chart, from QuantiStat) becomes a number.
53. As a trader, I want the level check to use the current hour and similar days, so that the chance reflects what the day has already done.
54. As a trader, I want the level check to work for past days and hours too, so that I can study how a level looked at the time.
55. As a trader, I want a clear answer when the price is already beyond the high/low so far, so that I don't get a meaningless percentage.

### Bias: עונתי

56. As a trader, I want a seasonal chart of the average path of the month (10y, 5y, 2y) with today's day marked, in the style of market-bulls, so that I can see the chart I used to pick my bias from.
57. As a trader, I want the hit rate of each window's bias call shown next to it, with a confidence interval, so that I know how much it is worth.
58. As a trader, I want "always bullish" shown as the baseline, so that I can see the seasonal call doesn't beat it.
59. As a trader, I want a note that the 10y window holds only about 9 years of LSE data, so that I'm not misled by its name.
60. As a trader, I want the hit rate shown with the number of days and a split by year, so that I can see how stable it is.

### Bias: Intraday

61. As a trader, I want an intraday screen with the chance the day closes bullish (close above the 00:00 open) after each candle, so that I know where the day is leaning.
62. As a trader, I want the hit rate of that chance at the current hour shown next to it (for example "right on 71% of past days at 9:00"), so that I know how much to trust it.
63. As a trader, I want the seasonal and intraday hit rates visible side by side in the Bias group, so that I can see the difference between before the open and during the day.
64. As a trader, I want the bias to never change the HOD/LOD levels, so that a wrong bias can't spoil them.

### נתונים

65. As a trader, I want all data to come from LSE, so that the app runs on the same 10 years the engine was tested on.
66. As a trader, I want the data refreshed regularly during the day, so that the live mode stays current.
67. As a trader, I want the candle-table section of the old page removed from the interface while its API stays, so that the app stays focused on HOD/LOD without losing anything.

## Implementation Decisions

- **מעטפת:** הרחבה של שרת ה-Flask הקיים ושל הדף הסטטי הקיים. אין אפליקציה שולחנית ואין framework חדש. הדף מצייר את הגרפים בדפדפן (SVG, כמו מפת החום הקיימת) ולא כתמונות matplotlib.
- **ממשק:** אנגלית, משמאל לימין. השם Caple. לא משתמשים בשם, בלוגו או במיתוג של QuantiStat.
- **API:** נקודת קצה JSON אחת לכל מודול: Price Based, Time Based, Level Validator (יומן ובדיקת רמה), Bias (עונתי ו-Intraday). כל אחת מקבלת End Date, נקודת זמן (לפני הפתיחה, שעה, או חי) ומצב (רגיל או QuantiStat) כשרלוונטי. הדף רק מציג את ה-JSON. נקודת הקצה הקיימת של מפת הרמות מוחלפת או מורחבת בנקודת Price Based.
- **מצב רגיל של Price Based:** מבוסס על המנוע הקיים כמו שהוא. המרחקים נמדדים בסרגל (HAR על תנודתיות Parkinson שעתית) ומומרים לנקודות של היום. ימים דומים במהלך היום: חמישית הטווח ו-k-NN, כמו היום. כל ההיסטוריה עד ה-End Date. תאים של נקודה אחת במקום 2. תאים עם יום אחד מוסתרים.
- **מצב QuantiStat:** נקודות גולמיות בלי סרגל, כל הימים בחלון ה-Period שנמדד מה-End Date, רק לפני הפתיחה, תאים של נקודה, גבול יום של 00:00 ניו יורק. Price Based לא מפוצל לפי bias. Time Based מפוצל לפי bias (ארבע היסטוגרמות). ההנחה הקיימת בקוד שהם בוחרים "אותו יום בחודש" לא נכונה לפי השחזור, ולא משתמשים בה.
- **Time Based במצב רגיל:** לפני הפתיחה, התפלגות שעת ה-HOD/LOD על הימים הדומים. אחרי שעה מסוימת, "כבר נקבע" של המנוע, ומתחתיו התפלגות השעה בין הימים הדומים שעוד המשיכו. הסיכוי ששעת הקיצון כבר עברה חייב להיות שווה ל"כבר נקבע".
- **הערכת Time Based:** walk-forward לכל השעות, רק מימים קודמים. ציון RPS (התוצאה היא שעה, ערך מסודר), אחוז "השעה הכי סבירה ± שעה", והשוואה לחוק ה-arcsine מותאם לפרופיל השונות התוך-יומי, ולבחירה קבועה של השעה הנפוצה ביותר. התוצאה מוגשת דרך ה-API כאחוז ההצלחה של המודול.
- **Level Validator, יומן:** מבוסס על היומן הקיים (רמות מראש לפני הפתיחה ואחרי 2/5/9/12/15, מסומן אם הושג ואם נפל ברצועה). מוסיפים עמודה של מצב QuantiStat לאותם ימים, וסינון לפי טווח תאריכים.
- **Level Validator, בדיקת רמה:** מחיר נכנס, ויוצא הסיכוי שה-HOD (מחיר מעל המחיר הנוכחי) או ה-LOD (מתחת) יגיע אליו, לפי פונקציית ההישרדות של הימים הדומים בנקודת הזמן שנבחרה, משולבת עם "כבר נקבע". מחיר שכבר נחצה מחזיר תשובה מפורשת ולא אחוז. אין מצב QuantiStat.
- **Bias עונתי:** החלונות 10y, 5y, 2y מנתוני LSE היומיים (מאמצע 2016), מבוסס על הקוד העונתי הקיים. לכל חלון: אחוז הצלחה walk-forward, מספר ימים, רווח סמך Wilson, פילוח לפי שנה. "תמיד שורי" כבסיס. אין מקור נתונים נוסף.
- **Bias Intraday:** רגרסיה לוגיסטית על (מחיר עכשיו − פתיחה) / סרגל, לכל שעה, מתאימה מחדש כל ינואר על שנים קודמות בלבד. מוצגת עם אחוז ההצלחה שלה באותה שעה. נבדקה ב-scratchpad: מכוילת, 70.6% ב-9:00, 80.1% ב-12:00, 90.1% ב-15:00 (2018–2026). הבדיקה עוברת לריפו.
- **bias לא נוגע ברמות:** לא לפני הפתיחה ולא במהלך היום. נבדק: פיצול לפני הפתיחה דורש bias שצודק ב-73% (העונתי צודק ב-51%). פיצול במהלך היום מחמיר את ה-pinball ב-2–10%, כי זו ספירה כפולה.
- **סימול:** ES בלבד, אבל הסימול הוא פרמטר ולא קבוע בקוד. NQ ייכנס רק אחרי בדיקת כיול משלו.
- **הדף הקיים:** חלק טבלת הנרות ולוח השנה שלה יורדים מהממשק. נקודות הקצה של הנרות נשארות.
- **מצב חי:** משתמש ברענון הקיים (נתונים כל 2 דקות, הדף כל דקה) ובנרות ש-LSE כבר סגרה.

## Testing Decisions

- **בדיקה טובה בודקת התנהגות חיצונית בלבד:** מה ה-API מחזיר עבור נתונים ידועים, לא איך זה מחושב בפנים.
- **נקודת בדיקה אחת: ה-API של השרת**, דרך ה-test client של Flask, כשמקור הנתונים מוחלף בנרות סינתטיים ותאריך היום קבוע. זה הדפוס של בדיקות השרת הקיימות.
- **מה נבדק בכל נקודת קצה:**
  - Price Based: תאים של נקודה; הסתרת תאים של יום אחד; בנתונים שבהם רמת המחירים משתנה, מצב רגיל משווה ימים בסרגל ומצב QuantiStat בנקודות גולמיות; חלון Period נמדד מה-End Date; מצב QuantiStat מסרב לשעה שאינה "לפני הפתיחה".
  - כל נקודות הקצה: שום דבר אחרי השעה שנבחרה לא משנה את מה שמוחזר לשעה הזאת (הדפוס של הבדיקה הקיימת במנוע).
  - Time Based: הסיכוי ששעת הקיצון עברה שווה ל"כבר נקבע"; ההיסטוגרמות לפי bias במצב QuantiStat.
  - Level Validator: היומן מחזיר רמות שנבנו רק מימים קודמים, כולל עמודת QuantiStat; בדיקת רמה מחזירה סיכוי שיורד ככל שהמחיר רחוק יותר, ותשובה מפורשת למחיר שכבר נחצה.
  - Bias: החלונות העונתיים עם אחוז הצלחה, מספר ימים ורווח סמך; ה-Intraday מחזיר הסתברות ואחוז הצלחה לשעה; שינוי ה-bias לא משנה את רמות Price Based.
  - הערכות ה-walk-forward (Time Based ו-Bias Intraday) נבדקות על נתונים סינתטיים קטנים שבהם התשובה ידועה מראש.
- **לא נבדקים:** HTML, CSS והציור בדפדפן. הם רק מציגים את ה-JSON.
- **בדיקות קודמות לחקות:** בדיקות השרת (test client עם נתונים מוחלפים), ובדיקות המנוע ("שום דבר אחרי השעה לא משנה", pinball, odds).

## Out of Scope

- שיפורי מנוע: VIX1D/VIX9D מ-Cboe, סרגל אסימטרי, משקלות שילוב נלמדים, הילוך מקרי עם אי-ודאות בתנודתיות, ACI/conformal, Markov על גודל היום. מסלול נפרד, כל רעיון נכנס רק אחרי בדיקת walk-forward.
- סימולים מלבד ES (NQ ו-GC זמינים ב-LSE, אבל דורשים כיול).
- מקור נתונים יומי ארוך לחלונות עונתיים של 15y/20y.
- פיצול רמות לפי bias, בכל צורה.
- גרף נרות או טבלת נרות בממשק.
- מתג שפה, עברית, עטיפה כחלון שולחני.
- העתקה של "החלון לפי תאריך ההרצה" של QuantiStat.
- סיכוי הגעה ב-hover של מפת החום.

## Further Notes

- **הוראות הריפו לסוכנים** מורות לעבוד אוטונומית עד commit ו-push. זה סותר את הכלל של המשתמש לא לממש עד שהוא אומר. הכלל של המשתמש גובר.
- **ההנחות הקיימות בקוד ובתיעוד על QuantiStat** ("אותו יום בחודש", תאים של 2 נקודות) לא נכונות לפי השחזור, וצריך לעדכן אותן.
- **מילון מונחים:** CONTEXT.md בשורש הריפו. מחקרי רקע: התיקייה docs/research.
- **בדיקות שבוצעו במהלך התכנון (ב-scratchpad, לא בריפו):**
  - הכלל "הקצה הפנימי של הרצועה הבהירה" שקול ל-quantile שמרני (הגעה ב-81%), ולא טוב ממנו.
  - הנקודה שבה פיצול לפי bias מתחיל להשתלם: bias שצודק ב-73% מהימים.
  - bias מימים דומים לא טוב יותר מ"מחיר מול פתיחה".
  - שחזור השיטה של QuantiStat.
