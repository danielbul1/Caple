# חיזוי HOD/LOD של ES: Statistical Data, ‏arXiv ו-GitHub

תאריך: 2026-10-11. היקף: שלושה סוגי מקורות בלבד: (1) "Statistical Data" (מקור ה-Discord שה-README של Caple מזכיר), (2) מאמרי arXiv והקוד שלהם, (3) מאגרי GitHub.
המסמך משלים את `hod-lod-best-practices.md` ולא חוזר עליו. מרעיונות שכבר הופיעו שם (ACI, ‏HARQ, ‏yardstick אסימטרי, ‏VIX1D) מובאים כאן רק מקורות חדשים או קוד שמממש אותם.
סימון: **[לא אומת]** = לא בדקתי מול מקור ראשוני. "הערכה שלי" = שיפוט שלי, לא תוצאה שדווחה. כוכבים ותאריכים נלקחו מה-API של GitHub ב-2026-10-11.

## תקציר

- **Statistical Data: אין לו שום נוכחות ציבורית שהצלחתי למצוא.** אין אתר, אין ארגון או מאגר ב-GitHub, אין רישום בגילוי השרתים של Discord, ואין Whop או חשבון X. העקבות היחידים הם ב-Caple עצמו: ‏README ו-`forecast_bias.py` מזכירים שלושה רעיונות שנראים כמו שמות ערוצים (`markov-process`, ‏`sarimax`, ‏`bias-forecasting`). קרוב לוודאי שזה שרת Discord פרטי, ואין לי גישה לקרוא אותו. כל שלושת הרעיונות כבר נבדקו ב-Caple ב-walk-forward, וכולם הפסידו לשיעור הבסיס (טבלת `forecast_bias.py` ב-README).
- **Statistical Data, מה כן אפשר ללמוד ממנו:** לא את השיטות. אלה שיטות לכיוון היום, והכיוון לא צפוי. מה שאפשר לקחת זה פרוטוקול בדיקה לכל טענה שתגיע משם: שיעור בסיס, רווח סמך Wilson, פיצול לחצאים, ‏null של הילוך מקרי ובדיקת טאוטולוגיה. ‏po3-research ו-edge-stats (בהמשך) נותנים לזה מימוש מוכן.
- **po3-research (GitHub, ‏ES/NQ): "סולם nulls" לתזמון קיצונים.** arcsine → ‏driftless → ‏drift → ‏drift_vol → ‏shuffle. ב-ES החודשי, ‏High-Late 54.2% נראה מובהק מול uniform ‏(33.3%), ונעלם מול shuffle ‏(p=0.586). זה בדיוק המבחן שחסר ל-Time Based: לבדוק אם שעת ה-HOD מכילה מידע מעבר ל-arcsine שמעוות לפי `REMAINING`.
- **edge-stats של LuxAlgo (MIT, ‏126 כוכבים): מנוע פתוח "P(outcome | conditions)" עם presets של high-time ו-low-time.** כל מספר מוצג עם N, ‏Wilson 95%, יציבות בין שני חצאים, תצוגת recency ופירוט לפי שנה. יש לו גם adapter ל-LSE, אותו ספק נתונים של Caple. זו התבנית לתצוגה של Level Validator ושל מודול ה-bias העונתי (51%), אבל לא מודל חיזוי.
- **נתוני VIX1D ו-VIX9D ישירות מ-Cboe, בלי Yahoo.** נמצא דרך חיפוש קוד ב-GitHub. ‏`VIX9D_History.csv` מכסה מ-2011-01-04, ו-`VIX1D_History.csv` מ-2022-05-13 (1,106 שורות עד 2026-10-09). בדקתי בהורדה. זה פותח מחדש את השורה "VIX9D … dropped with Yahoo" (‏-2%, ‏t -5 בפתיחה).
- **HARQ וסמי-וריאנס, שחזור עם walk-forward (‏atirupati7/harq-volatility-forecasting).** ‏SHAR (סמי-וריאנס) נתן ‎-5.4% QLIKE על SPX ‏2002-2013. היתרון של HARQ נעלם ב-SPY ‏2014-2019, ו-MCS משאיר שם את כל המודלים. המסקנה: להוריד ציפיות מ-HARQ ולהעדיף את הגרסה האסימטרית (רעיון 2 במסמך הקודם).
- **קוד ACI מוכן:** ‏`MAPIE` (‏1,602 כוכבים, Python), ‏`AdaptiveConformal` (R: ‏ACI, ‏AgACI, ‏DtACI, ‏SAOCP), ‏conformal PID של Angelopoulos, Candès ו-Tibshirani (arXiv:2307.16895) עם קוד, ו-DtACI (arXiv:2208.08401), שנבדק על תנודתיות מניות. ‏TCP (arXiv:2507.05470) מזהיר: בהשוואת interval score, ב-42 מתוך 52 ההשוואות מודל התנודתיות ניצח את ה-conformal המתגלגל.
- **הערכה ל-Time Based:** ‏`scoringrules` (‏frazane, ‏105 כוכבים) כולל `rps_score` (Ranked Probability Score). זה כלל הניקוד הנכון לתחזית של "שעת ה-HOD", כי השעה היא משתנה סודר. הוא כולל גם Brier, ‏log score, ‏interval score ו-quantile score ל-Level Validator.

---

## 1. Statistical Data

### 1.1 מה זה, ומה ציבורי

**מה ידוע (מקור ראשוני: Caple בלבד).**
- ‏README של Caple: "`python forecast_bias.py` tests the Discord "statistical data" ideas (markov-process, sarimax, bias-forecasting)".
- ה-docstring של `forecast_bias.py`: "Walk-forward test of the Discord "statistical data" ideas (markov-process, sarimax, bias-forecasting)".
- היסטוריית git של ה-clone: ‏`87e2a17` ‏(2026-10-10) "Test a 2nd-order Markov chain as a daily bias rule", ‏`bbf2e90` ‏(2026-10-10) "Walk-forward test of Markov, SARIMAX and ML daily bias forecasts".
- הכתיב עם מקפים (`markov-process`, ‏`bias-forecasting`) תואם את מוסכמת שמות הערוצים ב-Discord. מכאן ההשערה שאלה שמות ערוצים בשרת בשם "Statistical Data" **[לא אומת: הסקה מהכתיב]**.

**מה חיפשתי ולא מצאתי (2026-10-11).**

| איפה | שאילתה | תוצאה |
|---|---|---|
| חיפוש רשת כללי (2 מצבים) | `"Statistical Data" discord trading community quant futures`; ‏`"Statistical Data" discord futures trading ES NQ statistics server HOD LOD` | אין. הופיעו רק Quant Data (אופציות/GEX) ו-Quant Trading App, שאינם קשורים |
| חיפוש רשת | `"statistical data" discord markov-process sarimax bias-forecasting github` ; `"bias-forecasting" "markov-process" channel discord` | אין. רק ChainoPy (ספריית מרקוב כללית) ומדריכי SARIMAX |
| חיפוש רשת | `"statisticaldata" trading discord OR whop OR github` ; ‏`"StatisticalData" OR "Statistical_Data" … x.com` ; ‏`"Statistical Data" whop futures statistics HOD LOD` | אין חשבון X, אין חנות Whop |
| Discord server discovery | `discord.com/servers?query=statistical data` | ‏86 תוצאות, 12 הראשונות נקראו. אין שרת מסחר בשם הזה (הקרוב ביותר: Quant Data) |
| Disboard | `disboard.org/search?keyword=statistical+data` | HTTP 403, לא נקרא |
| GitHub (repos API) | `statistical data discord`, ‏`statisticaldata trading`, ‏`markov sarimax bias forecast` | בוטים של Discord לנתוני ספורט ומניות, ללא קשר. אפס תוצאות לשתי האחרונות |
| קבצי Caple המקומיים | grep על `C:\Users\user\Documents\Caple` | אין אזכור מחוץ ל-clone |

**מסקנה.** "Statistical Data" הוא כנראה שרת Discord פרטי, או שרת שאינו מופיע ברשימות הציבוריות. אין לי גישה אליו, ולכן אין לי מידע על מי מפעיל אותו, אם יש מוצר בתשלום, תיעוד או track record. לא המצאתי תוכן. אם תייצא את הערוצים (טקסט או צילומי מסך), אפשר לבדוק כל טענה לפי הפרוטוקול ב-1.3.

### 1.2 מה Caple כבר בדק מתוכו

הטבלה ב-README (`forecast_bias.py`): על 1,851 ימים (2019-2026), עם התאמה מחדש בכל ינואר, ציון Brier מול שיעור הבסיס:
- Markov על 1/2/3 ימים: ‏‎-4.6/-6.6/-14.4 (×1e-4). Markov עם big/small range: ‏‎-25.5. ‏SARIMAX(1,0,1)x(1,0,1,5): ‏‎-19.4. ‏logit: ‏‎-14.8. ‏GBM: ‏‎-48.7, גרוע מובהק. אף אחד לא עבר את סף 2 SE. הדיוק היה 52.5-54.3%, מול 54.3% של "תמיד שורי".
- גם ה-bias העונתי (`seasonal.py`) לא מנצח את "תמיד שורי": ב-2022 ואילך, 50.9% כששלושת החלונות מסכימים, מול 49.7%.

### 1.3 מה אפשר ללמוד מ-Statistical Data

1. **לא לייבא אף שיטת כיוון.** זה מה שכל הראיות אומרות: ‏`forecast_bias.py` ו-`bias.py` ב-Caple, ‏po3-research (גם אצלם "Month-state does not condition daily direction", בטווח ~2 נקודות אחוז מהבסיס), ו-arXiv:2605.04004 (אף אחת מ-14 משפחות אותות המומנטום ב-MNQ לא עברה walk-forward). את מודול ה-bias העונתי צריך להציג עם 51% ועם CI, כמו שתוכנן.
2. **מה שכן שווה לנסות מאותה משפחה הוא Markov על מצב הגודל, לא על הכיוון.** למשל מצב (טווח אתמול גדול/קטן ביחס ל-yardstick) → התפלגות ה-extras. הערכה שלי: הסיכוי נמוך, כי HAR כבר לוכד את התמדת התנודתיות. עדות חלקית: "Markov, last 2 days + big/small range" נבדק רק על כיוון. הבדיקה זולה: מוסיפים ממד בינארי ל-k-NN בפתיחה, ומשווים pinball על 2022-2026.
3. **פרוטוקול לכל טענה שתגיע מהשרת** (מבוסס על edge-stats ו-po3-research, סעיפים 3.1 ו-3.2):
   - שיעור הבסיס לצד כל אחוז, ו-N עם Wilson 95% (edge-stats: אזהרה מתחת ל-30, אין אומדן מתחת ל-10).
   - בדיקת טאוטולוגיה: האם התנאי כבר מכיל את התוצאה? ב-po3-research, ‏`Month_Return_So_Far_Pct` "נתן" פער של ~29 נקודות אחוז רק כי רץ עד הסגירה. התאום המפוגר שלו נתן 2-3.
   - null מתאים לתזמון: arcsine ו-shuffle, לא uniform.
   - פיצול train/OOS או חצאים, והסכמה בסימן.
   - במקרה של "רמה שהמחיר נמשך אליה": השוואה לשיעור ההגעה של יום אקראי (כבר נעשה ב-Caple לקווים הבהירים: ~31% מול ~31%).

---

## 2. arXiv

### 2.1 ‏Conformal PID Control for Time Series Prediction
- **מקור:** arXiv:2307.16895, ‏Angelopoulos, Candès, Tibshirani, ‏2023-07-31. קוד: [aangelopoulos/conformal-time-series](https://github.com/aangelopoulos/conformal-time-series) (‏146 כוכבים, push אחרון 2023-11-30, ‏MIT).
- **מה מראים:** לפי התקציר, כיסוי מובטח לכל רצף, גם אדברסרי, בגישה של בקרה: quantile tracking (‏P), ‏integrator ו-scorecaster. ניסויים על מקרי מוות מ-COVID, ביקוש לחשמל, תשואות שוק וטמפרטורה. ‏`tests/datasets/proc/` כולל AMZN ו-GOOGL. השיפור שדווח: כיסוי טוב יותר מאנסמבל ה-CDC.
- **איכות:** online מטבעו, ולכן אין look-ahead כל עוד הציון של יום t מחושב אחרי שהיום נגמר. כל הניסויים חד-משתניים. אין ניסוי על extremes תוך-יומיים.
- **רלוונטיות:** Price Based ו-Level Validator. זו גרסה עשירה יותר של ACI (רעיון 5 במסמך הקודם). ה-integrator מתקן הטיה מתמשכת, כמו ה-"75%" הגולמי של QuantiStat שהגיע ל-86%.
- **נבדק ב-Caple?** לא (README: אין שורה כזאת. "Weight recent days more" זה דבר אחר).
- **בדיקת walk-forward:** לכל צד, שעה ו-q, מריצים `quantile` (‏P control) מתוך `core/methods.py` על ציון `y − level`, עם lr קטן. מעריכים כיסוי מתגלגל על 250 יום ו-pinball, 2022-2026, מול הגרסה הנוכחית, עם t מזווג ו-HAC.

### 2.2 ‏Conformal Inference for Online Prediction with Arbitrary Distribution Shifts (‏DtACI)
- **מקור:** arXiv:2208.08401, ‏Gibbs & Candès, ‏2022-08-17. קוד: [isgibbs/DtACI](https://github.com/isgibbs/DtACI) (‏20 כוכבים, push ‏2025-04-07, קובצי R: ‏`DtACI.R`, ‏`AgACI.R`, ותיקיית `MajorDailyReturns`).
- **מה מראים:** לפי התקציר, ACI עם כוונון אוטומטי של גודל הצעד. ה-regret קטן על כל חלון זמן מקומי, אין צורך לדעת מה קצב השינוי, והשיטה נבדקה על תנודתיות שוק המניות ועל COVID.
- **איכות:** online ובלי הנחות התפלגות. מתאים ל-Caple, שבו לכל צד ושעה יש quantile משלו.
- **רלוונטיות:** Price Based, ‏Level Validator. עוקף את בחירת γ, שהייתה החולשה של ACI במסמך הקודם.
- **נבדק ב-Caple?** לא.
- **בדיקה:** כמו 2.1, עם DtACI ‏(R, ‏או port של כ-30 שורות).

### 2.3 ‏Temporal Conformal Prediction (TCP)
- **מקור:** arXiv:2507.05470 (v7), ‏Aich, Aich, Jain, ‏2025-07-07. לא מצאתי קוד.
- **מה מראים:** לפי התקציר, 13 סדרות פיננסיות, 1,448 תאריכים משותפים, יעד של 95%. ‏TCP הגיע ל-95.23% על S&P 500. אבל בהשוואות interval score מול 4 מודלי תנודתיות, 42 מתוך 52 העדיפו את מודל התנודתיות ו-10 לא היו מובהקות (DM לא מתוקן, 5%).
- **איכות:** rolling, ללא look-ahead לפי התיאור. נזהרים בפרשנות: DM לא מתוקן לריבוי השוואות.
- **רלוונטיות:** אזהרה. conformal לבדו לא מחליף yardstick טוב, וצריך לשים אותו מעל ה-HAR, לא במקומו. אותו מוסר כמו ב-README: "The size of the day is predictable … its direction is not."
- **נבדק ב-Caple?** לא רלוונטי ישירות.

### 2.4 ‏Adaptive Conformal Predictions for Time Series (‏AgACI), הקוד
- המאמר כבר במסמך הקודם. **חדש:** הקוד ב-[mzaffran/AdaptiveConformalPredictionsTimeSeries](https://github.com/mzaffran/AdaptiveConformalPredictionsTimeSeries) (‏71 כוכבים, push ‏2022-04-07; ‏`AgACI/` ב-R, ‏EnbPI). הוא מצוין ב-arXiv:2202.07282.

### 2.5 ‏Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures
- **מקור:** arXiv:2605.04004 (v3), ‏Mathias Mesfin, ‏2026-05-05. לא מצאתי קוד.
- **מה מראים:** 14 משפחות אותות, 947 ימים של נרות 5m ‏(2021-2025), walk-forward עם חלון מתרחב וחמישה קריטריונים. אף משפחה לא עברה את כולם. ‏ORB long: ‏T=0.88. ‏gap continuation short: ‏T=1.46. שתי ביקורות חיוביות עברו (RTH Confluence: ‏T=3.11), כלומר המבחן מסוגל לזהות edge אמיתי.
- **איכות:** תכנון טוב (ביקורת חיובית, friction, פרמוטציה). מגבלות: מחבר יחיד, מדגם קצר, ‏NQ ולא ES.
- **רלוונטיות:** אישור חיצוני לטענות "הכיוון לא צפוי" ו-"turn of a leg can't be told" ב-README. לא משפר מודול ספציפי.
- **נבדק ב-Caple?** כן במובלע: ‏`legs.py` ו-`bias.py` (README: "every cutoff loses money").

### 2.6 ‏A Validated Volatility-Volume-Gap Classifier for Regime Identification in MNQ Intraday Data
- **מקור:** arXiv:2605.11423 (v3), ‏Mesfin, ‏2026-05-12.
- **מה מראים:** יום מסומן כשמתקיימים יחד gap חריג, תשואה חריגה ב-30 הדקות הראשונות ונפח חריג בנר הראשון. זה קרה ב-4.4% מהימים (40 ימים). ‏77.6% מהימים האלה חוזרים מהשיא לפני הסגירה, עם ויתור ממוצע של 11.73 נקודות. אף תצורה כיוונית לא עברה (הטובה ביותר: ‏T=1.46). ‏2024 שבר את היציבות. הספים חושבו על חלון מתרחב.
- **רלוונטיות:** נמוכה עד בינונית. "חזר מהשיא לפני הסגירה" קרוב לשאלה "האם ה-HOD כבר נקבע" בימים קיצוניים, אבל רק כ-10 ימים בשנה. ‏Caple כבר בדק gap כממד k-NN ונדחה (README: ‏+0.1%/+0.4%/+0.6%).

### 2.7 ‏VOLARE: VOLatility Archive for Realized Estimates
- **מקור:** arXiv:2602.19732, ‏Cipollini, Cruciani, Gallo, Insana, Otranto, Spagnolo, ‏2026-02-23. פלטפורמה: https://volare.unime.it (האתר דורש JS, ולא הצלחתי לקרוא אותו).
- **מה מראים:** לפי טקסט המאמר (גרסת HTML): מדדים ממומשים מסטנדרטיים מנתוני טיק, כולל Parkinson (`pr`), ‏Garman-Klass (`gkr`), ‏Realized Range (`rr5`), סמי-וריאנסים ו-realized quarticity. **ES נמצא בטבלה A.3** (יחד עם CL, ‏NG, ‏GC, ‏C). התחלה: 2009-09-28. עדכון חודשי. **[לא אומת]**: תנאי גישה ורישיון הנתונים.
- **רלוונטיות:** ה-yardstick (Price Based). מקור חיצוני ל-RR, ‏RQ ו-RS± של ES, לבדיקת רעיונות 2, 3 ו-5 מהמסמך הקודם בלי לחשב לבד מ-LSE 5m. העדכון החודשי לא מתאים לייצור, רק למחקר.
- **בדיקה:** מחשבים את אותם מדדים מ-`lse_ES.F_5m.csv`, ובודקים התאמה מול VOLARE על החפיפה. רק אם ההתאמה טובה, משתמשים בשניהם לבדיקת HARQ ו-SHAR.

### 2.8 תיאוריה של "זמן המקסימום" (רקע ל-Time Based)
- arXiv:1207.4736, ‏Baurdoux & van Schaik, ‏2012: stopping time שממזער מרחק L1 לזמן שבו תהליך Lévy מגיע לסופרמום הסופי. arXiv:1601.00175, ‏Rokhlin, ‏2016: ‏"perfect stopping times", מכירה כשהמחיר יורד בסכום שתלוי בזמן מתחת למקסימום הרץ.
- **רלוונטיות:** תיאורטית בלבד. נותנת את ה-point forecast האופטימלי ל-L1 של שעת ה-HOD (חציון התפלגות שעת ה-HOD המותנית), וזה מה שכדאי להציג אם מציגים שעה אחת. אין נתונים אמפיריים.

### 2.9 נבדק ונמצא דל רלוונטיות
- arXiv:2509.16137 (‏Tepelyan, ‏2025): חותמות זמן של H ו-L בתוך נרות 1m משפרות חיזוי VWAP. הדף לא מתאר תכנון OOS ולא מקשר לקוד. רעיון עקיף: חותמת הזמן של ה-HOD/LOD עד כה כממד k-NN ("כמה שעות עברו מאז השיא"). **[לא נבדק ב-Caple]**, והערכה שלי היא תועלת נמוכה.
- arXiv:1901.02947 (Int-GARCH ל-[low, high], ‏2019): ‏OOS לתנודתיות בלבד. החפיפה עם 1502.04740 צוינה ב-arXiv עצמו.
- arXiv:2606.06737 (Fast-excursion Heston): הסתברויות פגיעה במחסום עולות "of order 10%" כשמביאים בחשבון excursions, ב-EURUSD של חודש, בסימולציה בלבד. זה קשור רעיונית ל-`rw_done` עם σ לא ודאי (רעיון 6 במסמך הקודם): תנודתיות לא ודאית מעלה את הסיכוי להגיע לרמה.
- arXiv:2508.15922 (quantiles של תנודתיות ביטקוין מתחזיות נקודה): ‏QRS על מודלים לינאריים של log-RV הוא הטוב ביותר. זה מקביל לגישה של Caple (רמות כ-quantiles של extras מנורמלים).

---

## 3. GitHub

### 3.1 ‏thomas-quant/po3-research ‏(ES/NQ path structure)
- **קישור:** https://github.com/thomas-quant/po3-research. ‏2 כוכבים. commit אחרון ב-default branch: ‏2026-08-10, ‏push: ‏2026-10-05. ‏Python, ‏`po3_research/research.py` (3,848 שורות) עם tests, כולל `tests/test_random_walk_null.py`.
- **מה מראה (README וקוד):**
  - **סולם nulls לתזמון קיצונים** (`RW_NULL_CONTROLS = ["arcsine", "driftless", "drift", "drift_vol", "shuffle"]`, ‏`arcsine_null_shares`, ‏`_simulate_null`). ‏arcsine בצורה סגורה, ‏`F(t)=2/π·arcsin(√t)`, נותן 39.2% לכל שליש קצה ו-21.6% לשליש האמצעי. ב-ES, ‏192 חודשים, ‏High-Late=54.2%: מול driftless ‏p=0.000, מול drift ‏p=0.004, מול drift_vol ‏p=0.064, מול shuffle ‏p=0.586. המסקנה שלהם: "Monthly path structure is a drift artifact".
  - שיעור חזרה ל-midnight open ‏(ES, ‏Train): מ-09:30 עד הסגירה 65.72%, מ-13:00 עד הסגירה 38.53%.
  - "Midnight > Globex" הוא מצב מוקדם, לא תחזית: ‏Midnight→Close חיובי ב-50.69% מול בסיס של 52.29% ‏(ES, ‏OOS).
  - טווח אחר הצהריים מותנה ב**סימן** הבוקר: בוקר עולה → אחר צהריים צר בכ-30% (log ratio ‏‎-0.363 ב-Train ו-‎-0.591 ב-OOS ל-ES, עם CI זרים). בשעה האחרונה הגודל מתחיל לשחק תפקיד והסימן מפסיק.
  - ב-README יש אזהרה שהתוצאות בגלריה מיושנות (נוצרו 2026-05-11, והמתודולוגיה תוקנה מאז).
- **איכות:** טובה יחסית. פיצול קבוע (`TRAIN_END = 2023-12-31`), ספים מ-Train בלבד ("Thresholds come from train rows only"), ‏bootstrap CI, טבלת nulls, וזיהוי עצמי של טאוטולוגיות ושל שגיאת העתקה. **חולשות:** ‏(1) פיצול יחיד ולא walk-forward מתגלגל. (2) ‏driftless ו-drift מניחים שונות קבועה לכל נר, כך שה-null היומי מתעלם מפרופיל התנודתיות התוך-יומי (U-shape). ‏shuffle מערבב את התשואות התוך-יומיות ולכן הורס גם את העונתיות. ל-Caple, ה-null הנכון ברמת השעה הוא arcsine בזמן מעוות לפי `REMAINING` (הערכה שלי). (3) הרבה תאים בגריד, ו-README עצמו מציין את בעיית ריבוי ההשוואות.
- **רלוונטיות ל-Caple:**
  - **Time Based (גבוהה):** ‏benchmark מחייב. אם התחזית לשעת ה-HOD לא מנצחת את arcsine שמעוות לפי `REMAINING`, וגם לא shuffle שמותנה ב-range so far, היא לא מוסיפה מידע.
  - **Price Based (בינונית):** ממצא "טווח אחר הצהריים מותנה בסימן הבוקר" (אפקט leverage תוך-יומי) מציע ממד כיווני ל-k-NN אחרי 9:00 ו-12:00: (close−open)/r. ‏Caple בודק היום מיקום בחמישיות ומרחקים מה-high וה-low, ושני אלה מכילים חלק מהמידע הזה (הערכה שלי).
- **נבדק ב-Caple?** הסימן במובלע (מיקום בחמישיות; README: "Position in fifths … -3%/-4%"). ‏null של arcsine ושל shuffle לתזמון: לא, כי `quantistat.py` מצייר time_based בלי כיול (README).
- **בדיקת walk-forward:** (א) ל-Time Based: מחשבים לכל יום ב-2017-2026 את ההתפלגות החזויה של שעת ה-HOD מהשעה t (analog weights), ובמקביל את ה-null: arcsine על זמן מעוות, כלומר `REMAINING` ממופה לשעון שונות. מנקדים ב-RPS ‏(3.6) וב-log score, עם t מזווג ו-HAC, בשני החצאים. (ב) ל-levels: מוסיפים את (close−open)/r כממד k-NN מ-9:00 ומשווים pinball, כמו בבדיקות ה-README.

### 3.2 ‏LuxAlgo/edge-stats
- **קישור:** https://github.com/LuxAlgo/edge-stats. ‏126 כוכבים, ‏MIT, נוצר 2025-08-25, ‏commit אחרון 2026-09-24. ‏TypeScript, ‏DuckDB, ‏CLI, דשבורד ו-MCP.
- **מה זה:** מנוע לשאלות `P(outcome | conditions)` על נרות. ה-presets כוללים `high-time` ו-`low-time` ("How often the session's high printed within the first m minutes… The real payload is the attached minutes-to-high distribution"), ‏`range-vs-atr`, ‏ORB, ‏initial balance, ‏prev-high/low touch ועוד. כל תוצאה כוללת Wilson 95%, אזהרה מתחת ל-30 ימים ואין אומדן מתחת ל-10, ‏"first-half vs second-half stability split", ‏recency של 250 ימים מול כל ההיסטוריה, פירוט לפי שנה, וקישור לימים עצמם. יש **adapter ל-`lse`** (מפתח `LSE_API_KEY`), ולוח שנה של CME עם סימון ימי roll.
- **איכות:** זה כלי תדירויות היסטוריות ולא מודל חיזוי. הוא אומר במפורש: "Historical conditional frequencies with sample sizes. Not predictions". אין walk-forward ואין כיול. ההגנות הן CI, חצאים ו-recency. ה-ATR ב-`range-vs-atr` "uses strictly prior sessions", כלומר בלי look-ahead בתנאי.
- **רלוונטיות:** **Level Validator ומודול ה-bias העונתי (UX, גבוהה):** תבנית מוכנה ל"כל אחוז עם N, ‏CI, חצאים ו-recency, ו-drill-down לימים", בדיוק מה שצריך כדי להציג 51% בכנות. **Time Based (בינונית):** ה-preset `high-time` נותן התפלגות לא מותנית, ואפשר להשתמש בו כ-baseline. **כ-QuantiStat-like:** זה הכלי הפתוח הכי קרוב ל-QuantiStat שמצאתי, אבל בלי heatmap של מחירים ובלי נרמול לתנודתיות (הערכה שלי מתוך הקטלוג).
- **נבדק ב-Caple?** הרעיונות של "תת-מדגם לפי יום" נבדקו ונדחו (README: "Day-of-month / weekday samples — worse/0"). התצוגה עם CI וחצאים לא קיימת ב-Caple.
- **בדיקה:** אין מה לבדוק ב-walk-forward. אימוץ UX: לכל מספר ב-Level Validator מוסיפים N, ‏Wilson, שני חצאים ו-250 ימים אחרונים.

### 3.3 נתוני VIX1D ו-VIX9D מ-Cboe (נמצא דרך חיפוש קוד ב-GitHub)
- **מקור:** חיפוש הקוד `"VIX1D_History.csv"` החזיר בין השאר את csnyder256/shadow-options-trading-lab ‏(`scripts/refresh_vix_history.py`), ‏cobriensr/Options-Strike-Calculator ‏(`api/cron/refresh-vix1d.ts`, ‏22 כוכבים) ו-vysw5trjz6-tech/quant-spx-engine ‏(`vol1d/qa.py`). את הקבצים הורדתי ישירות:
  - `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX1D_History.csv` (מפנה ל-`cdn-api.cboe.com`, דורש User-Agent): ‏DATE,OPEN,HIGH,LOW,CLOSE, מ-05/13/2022 עד 10/09/2026, ‏1,106 שורות. בשורות הראשונות OPEN=HIGH=LOW=CLOSE. **[לא אומת]**: האם ההיסטוריה שלפני ההשקה (24.4.2023, לפי המסמך הקודם) מחושבת לאחור.
  - `…/VIX9D_History.csv`: מ-01/04/2011 עד 10/09/2026.
- **רלוונטיות:** Price Based (yardstick). זה מסיר את החסם "dropped with Yahoo". סגירת VIX של יום t−1 (16:15 ET) ידועה לפני 00:00 של יום t, כך שאין look-ahead.
- **נבדק ב-Caple?** ‏VIX9D כן: ‏‎-2% ‏(t -5) בפתיחה (שורה ראשונה בטבלה, "was; dropped with Yahoo"). ‏VIX1D לא.
- **בדיקה:** ‏HAR-X: ‏log(range) על HAR ועוד log(VIX9D) ו-log(VIX1D) מהסגירה הקודמת, עם התאמה מחדש כל ינואר. ‏VIX9D על 2018-2026, ‏VIX1D על 2022-05 עד 2026 בלבד (כ-1,100 ימים). מדד: pinball בפתיחה, ב-2:00 וב-5:00, עם t מזווג ו-HAC.

### 3.4 ‏Thanish8769/RVRP-adjusted-VIX1D
- **קישור:** https://github.com/Thanish8769/RVRP-adjusted-VIX1D. ‏0 כוכבים, ‏2024-09-19, מחברת אחת.
- **מה עושה:** מושך SPY ו-VIX1D ‏(Polygon, נרות 5m, שנה אחת), מחשב RV יומי, ובונה תחזית VIX1D מתוקנת לפרמיית סיכון: `vix1d.shift(1) − RVRP.shift(1)`, או ממוצע או חציון מתגלגל של 21 יום. זה המימוש הפתוח היחיד שמצאתי של התיקון של Albers 2025.
- **איכות:** התחזיות המתוקנות מפוגרות נכון (`shift(1)` על VIX1D ועל RVRP), כך שאין look-ahead. אבל: שנה אחת בלבד, אין השוואה ל-HAR, אין מבחן מובהקות, וההשוואה הראשונה (VIX1D מול RV של אותו יום) היא תיאורית בלבד. כלומר זה סקריפט בלי backtest רציני.
- **רלוונטיות:** תבנית קוד ל-3.3 (תיקון הפרמיה, "VIX1D_median_RVRP"). אפשר להעתיק את הרעיון, לא את התוצאות.

### 3.5 ‏atirupati7/harq-volatility-forecasting
- **קישור:** https://github.com/atirupati7/harq-volatility-forecasting. ‏0 כוכבים, ‏2026-04-23. מחברת, ‏`report.tex` ו-`report.pdf`.
- **מה מראה (report.tex):** walk-forward עם חלון מתרחב, התאמה מחדש כל חודש, חלון התחלתי של 1,000 ימים, ‏QLIKE ו-MSE, ‏DM עם Newey-West ו-MCS ‏(`arch.bootstrap.MCS`). שחזור על SP500RM ‏2002-2013: ‏SHAR ‏‎-5.40% QLIKE ‏(DM p=0.0003). ‏HARQ ‏+2.18% QLIKE אבל ‎-4.4% MSE. לפני הפרסום: HARQ-F ‏‎-14.1%. **אחרי הפרסום, SPY 2014-2019: ‏"HARQ is not uniquely better than HAR"**, ו-MCS שומר את כל המודלים. ‏NGBoost-HARQ: כיסוי 96.9% ביעד של 95%, אבל נכשל ב-Kupiec וב-Christoffersen בזנב של 1%.
- **איכות:** תכנון הערכה טוב (HAC, ‏MCS). חולשה: את אינדקס התאריכים של SP500RM "reconstructed by anchoring" לשני תאריכים, כלומר יישור תאריכים משוחזר **[סיכון ליישור שגוי]**. עבודת סטודנט, לא שפיטה.
- **רלוונטיות:** Price Based (yardstick). מוריד ציפיות מ-HARQ (רעיון 5 במסמך הקודם) ומחזק את הגרסה האסימטרית (רעיון 2, ‏SHAR). מוסר נוסף: אם בונים התפלגות ל-yardstick, צריך זנב כבד (Student-t), וזה מתחבר לרעיון 6 במסמך הקודם (σ לא ודאי ב-`rw_done`).
- **נבדק ב-Caple?** לא. רק HAR על Parkinson (README).

### 3.6 כלים לכיול ולהערכה (ספריות)
| ספרייה | מה רלוונטי | פרטים |
|---|---|---|
| [scikit-learn-contrib/MAPIE](https://github.com/scikit-learn-contrib/MAPIE) | `mapie/regression/time_series_regression.py` (‏EnbPI, ‏ACI), וקובץ ייחוס `examples/data/zaffran2022_aci_reference.csv` | ‏1,602 כוכבים, push ‏2026-10-09 |
| [herbps10/AdaptiveConformal](https://github.com/herbps10/AdaptiveConformal) | R: ‏SCP, ‏ACI, ‏AgACI, ‏DtACI, ‏SF-OGD, ‏SAOCP, עם tests | ‏18 כוכבים, ‏MIT, push ‏2024-06-13 |
| [frazane/scoringrules](https://github.com/frazane/scoringrules) | `rps_score`, ‏`brier_score`, ‏`log_score`, ‏`interval_score`, ‏`weighted_interval_score`, ‏`quantile_score`, ‏CRPS | ‏105 כוכבים, push ‏2026-07-25 |
| [bashtage/arch](https://github.com/bashtage/arch) | `HARX` (‏`arch/univariate/mean.py`), ‏`MCS`, ‏`SPA`, ‏`StepM`, ‏`RealityCheck` (‏`arch/bootstrap/multiple_comparison.py`) | ‏1,592 כוכבים, push ‏2026-10-10 |
| [CamDavidsonPilon/lifelines](https://github.com/CamDavidsonPilon/lifelines) | ניתוח הישרדות, כלומר hazard בדיד ל-"שעת ה-HOD בהינתן שעוד לא נקבע" | ‏2,615 כוכבים, push ‏2026-03-07 |

**איך מעריכים תחזית "שעת ה-HOD" (Time Based), המלצה שלי מתוך הכלים:**
1. התחזית היא התפלגות על השעות h=t+1…23 (ועוד "כבר נקבע", כלומר h≤t). **עקביות:** ‏P(h≤t) חייב להיות שווה ל-"already in" של `levels.py`, אחרת שני המודולים סותרים זה את זה בעמוד אחד.
2. ניקוד: **RPS** ‏(`scoringrules.rps_score`), כי השעה משתנה סודר וטעות בשעה אחת קלה מטעות בשש. בנוסף log score על 24 הקטגוריות. Brier ל"יקרה לפני שעה X" (זה גם ה-hit rate שמוצג למשתמש).
3. ‏baselines: (א) ההיסטוגרמה הלא מותנית (כמו `quantistat.py` ו-edge-stats `high-time`). (ב) arcsine בזמן מעוות לפי `REMAINING`, מותנה ב"עוד לא נקבע". (ג) shuffle בסגנון po3. התחזית נחשבת מוסיפה מידע רק אם היא מנצחת את (ב), ב-RPS, בשני החצאים.
4. ה-"hit rate" שמוצג: ‏reliability diagram, בנוסף לשיעור הפגיעה של השעה הסבירה ביותר מול שיעור הפגיעה של אותה שעה ב-baseline. מספר בודד בלי baseline מטעה (ראו את ה-54.2% מול 39.2% ב-po3).

**איך מעריכים "chance HOD reaches X" (Level Validator):** זו פונקציית הישרדות של max(יום) מעל המחיר הנוכחי. ב-Caple כבר יש שני מקורות: ה-analog weights (פונקציית הישרדות אמפירית של extras), ו-`rw_done` (reflection, ‏`2Φ(d/sd)−1`). את זה כדאי למדוד כ-Brier ממוצע על גריד של X, שזה CRPS בדיד, עם ACI/DtACI על הסתברות ההגעה. לא מצאתי מימוש קוד פתוח ייעודי ל-reach probability של max יומי עם הערכה, ולכן זה כנראה רכיב שצריך לכתוב בעצמנו **[לא נמצא]**.

### 3.7 מאגרים קטנים שנבדקו (ערך נמוך)
| מאגר | מה | שיפוט |
|---|---|---|
| [FunChef/volatility-based-HOD-LOD-indicator](https://github.com/FunChef/volatility-based-HOD-LOD-indicator) (0 כוכבים, ‏2026-01-27) | Pine: אזורי HOD/LOD כ-open ± מכפלות קבועות (0.15/0.85/1.05) של ATR יומי של 14 | **look-ahead**: `request.security(..., f_atr(...), lookahead=barmerge.lookahead_on)` ואחריו `dailyATR_raw[1]`. ה-`[1]` מופעל על סדרת הגרף ולא בתוך ה-security, ולכן בנרות היסטוריים הוא מחזיר את ה-ATR של היום הנוכחי (כולל טווח היום). אין הערכה. זה מקביל ל-"raw points/ATR" שנדחה ב-Caple |
| [xifan828/tradable-mind](https://github.com/xifan828/tradable-mind) `src/services/scenario/session_open_extreme.py` (2 כוכבים) | שיעור הימים שה-H/L של 24 השעות נקבע ב-London או NY open | תיאורי בלבד, אין OOS. בשוויון שיא בכמה שעות נספרת כל שעה, כך שיש ספירה כפולה |
| [jayaliyev/nq_hourly-sweep-statistics](https://github.com/jayaliyev/nq_hourly-sweep-statistics) (0 כוכבים, ‏2025-07-01) | חזרה ל-open השעתי אחרי sweep של ה-high/low השעתי הקודם, ‏NQ, ‏18 שנה | מחברת תיאורית. לפי ה-README אין פיצול OOS |
| [matthewoestreich/fmpcloud-DailyHighLowTimeFrame](https://github.com/matthewoestreich/fmpcloud-DailyHighLowTimeFrame) (0 כוכבים, ‏2021) | ספירת שעות של H/L יומי (JS) | ספירה בלבד |
| [TRiamder/Nasdaq-forecasting](https://github.com/TRiamder/Nasdaq-forecasting) (0 כוכבים, ‏MIT, ‏2025-09-22) | LR ו-XGBoost ל-high/low יומי של QQQ ומסחר על הטווח. ‏OOS 2024-01 עד 2025-08: ‏+11.12% | split יחיד, הנתונים לא ניתנים לשיתוף ולכן לא ניתן להריץ. לא תוך-יומי |
| [uga-gaim/AnalogEnsemble](https://github.com/uga-gaim/AnalogEnsemble) (18 כוכבים, push ‏2026-10-07) | ‏AnEn ב-C++/R (מטאורולוגיה) | המימוש הקנוני של מה ש-Caple כבר עושה (k-NN analogs). שימושי רק לבחירת משקלות לפי ממד (AnEn ממשקל מנבאים) |

---

## טבלה מדורגת

| # | פריט | סוג | רלוונטיות (מודול) | איכות | מאמץ |
|---|---|---|---|---|---|
| 1 | Cboe `VIX9D_History.csv` / `VIX1D_History.csv` | GitHub (חיפוש קוד) + הורדה | גבוהה (Price Based: ‏yardstick; ‏VIX9D כבר הוכח ‎-2%) | נתונים רשמיים. היסטוריית VIX1D לפני 2023 לא אומתה | נמוך |
| 2 | po3-research: סולם nulls (arcsine→shuffle) | GitHub | גבוהה (Time Based: benchmark; פרוטוקול ל-Statistical Data) | טובה, פיצול יחיד, ‏null בלי U-shape | נמוך |
| 3 | scoringrules (`rps_score` ועוד) + עקביות עם "already in" | GitHub | גבוהה (Time Based, ‏Level Validator: הערכה) | ספרייה מתוחזקת | נמוך |
| 4 | edge-stats: ‏N, ‏Wilson, חצאים, ‏recency, ‏high-time | GitHub | בינונית-גבוהה (Level Validator, ‏bias עונתי: UX; ‏baseline ל-Time Based) | כלי תדירויות, לא חיזוי. מתוחזק, ‏MIT | נמוך-בינוני |
| 5 | DtACI / Conformal PID + קוד (MAPIE, ‏AdaptiveConformal) | arXiv + GitHub | בינונית-גבוהה (Price Based, ‏Level Validator: כיול) | מאמרים חזקים, אין ניסוי על extremes | נמוך |
| 6 | HARQ/SHAR walk-forward (atirupati7) | GitHub | בינונית (yardstick: להעדיף SHAR, להוריד ציפיות מ-HARQ) | הערכה טובה, יישור תאריכים משוחזר | בינוני |
| 7 | po3: טווח אחר הצהריים מותנה בסימן הבוקר | GitHub | בינונית (Price Based מ-9:00) | ‏CI זרים ב-OOS, ‏ES ו-NQ | נמוך |
| 8 | VOLARE (ES, ‏rr5, ‏RS±, ‏RQ מ-2009) | arXiv | בינונית (אימות ה-yardstick) | אקדמי, גישה לא אומתה | בינוני |
| 9 | RVRP-adjusted VIX1D | GitHub | בינונית-נמוכה (תבנית קוד ל-#1) | סקריפט, שנה אחת, בלי HAR | נמוך |
| 10 | TCP (2507.05470) | arXiv | נמוכה (אזהרה: conformal לא מחליף yardstick) | ‏DM לא מתוקן | — |
| 11 | MNQ falsification / VVG (2605.04004, ‏2605.11423) | arXiv | נמוכה (מאשר "כיוון לא צפוי") | walk-forward, מחבר יחיד | — |
| 12 | Statistical Data | Discord פרטי | לא ניתן להערכה. השיטות הידועות (Markov/SARIMAX/bias) נבדקו ונדחו | אין מקור ציבורי | — |
| 13 | Baurdoux & van Schaik; ‏Rokhlin (זמן הסופרמום) | arXiv | נמוכה (הצגת שעה אחת = חציון) | תיאוריה | — |
| 14 | FunChef, ‏tradable-mind, ‏jayaliyev, ‏TRiamder, ‏fmpcloud | GitHub | נמוכה | תיאורי. ב-FunChef יש look-ahead | — |

---

## לא נמצא, או לא הייתה גישה

- **Statistical Data:** אין אתר, ארגון או מאגר ב-GitHub, רישום ב-Discord discovery (12 תוצאות ראשונות מתוך 86), ‏Whop או חשבון X. ‏Disboard החזיר 403. מי מפעיל אותו, מוצר, מחיר, תיעוד, track record: **לא ידוע**. התוכן של הערוצים `markov-process`, ‏`sarimax` ו-`bias-forecasting` לא נקרא. ידוע רק מה ש-Caple שחזר ובדק.
- **QuantiStat:** שני חיפושים נוספים (רשת ו-GitHub `quantistat`) לא החזירו שום מוצר או קוד. זה תואם את המסמך הקודם.
- **מאמר arXiv שחוזה שעת HOD/LOD תוך-יומית, או "is the high in", על מדד מניות:** לא נמצא. חיפשתי ב-arXiv API את המונחים: `daily high`, ‏`high and low prices`, ‏`intraday` + `high-low`, ‏`time of the maximum`/`arcsine law` ב-q-fin, ‏`opening range`/`intraday range`, ‏`interval-valued`, ‏`ultimate maximum`. העבודות האמפיריות הרלוונטיות (Mok, Lam & Li 2000; ‏Acar, "Timing the highs and lows of the day"; ‏Panas 2005; ‏Jones 2015 ב-MPRA) אינן ב-arXiv, ולכן מחוץ להיקף.
- **מימוש קוד פתוח של reach probability ל-max יומי עם הערכה out-of-sample:** לא נמצא.
- **מימוש CARR או CARR אסימטרי ב-GitHub:** חיפוש `CARR range volatility` ו-`realized range volatility` החזיר אפס תוצאות.
- **VOLARE:** האתר דורש JS ולא נקרא. תנאי גישה ורישיון לא אומתו.
- **מחוץ להיקף, אבל קיים (לא נבדק לעומק):** אינדיקטורים ב-TradingView ("Daily High & Low Time Map (HOD / LOD)" עם Wilson CI; ‏"4H HOD/LOD Checkpoint Analysis", רק NQ, 3,136 ימים, לפי המחבר), ופוסט בפורום Brooks ("81.1%" ל-HOD/LOD עד bar 18 על 4,400 ימי ES, לפי הכותב). אלה לא arXiv ולא GitHub, ולכן לא נבדקו.

## מקורות

- Caple clone: ‏`README.md`, ‏`forecast_bias.py`, ‏`levels.py`, ‏git log (`87e2a17`, ‏`bbf2e90`).
- arXiv: 2307.16895; 2208.08401; 2507.05470; 2202.07282; 2605.04004; 2605.11423; 2602.19732 (+HTML, טבלה A.3); 2509.16137; 1901.02947; 2606.06737; 2508.15922; 1207.4736; 1601.00175.
- GitHub: thomas-quant/po3-research (README, ‏`po3_research/research.py`); ‏LuxAlgo/edge-stats (README, ‏`presets/high-time.json`, ‏`presets/range-vs-atr.json`, ‏`docs/catalog.md`); ‏aangelopoulos/conformal-time-series; ‏isgibbs/DtACI; ‏mzaffran/AdaptiveConformalPredictionsTimeSeries; ‏herbps10/AdaptiveConformal; ‏scikit-learn-contrib/MAPIE; ‏frazane/scoringrules; ‏bashtage/arch; ‏CamDavidsonPilon/lifelines; ‏Thanish8769/RVRP-adjusted-VIX1D; ‏atirupati7/harq-volatility-forecasting (`report.tex`); ‏FunChef/volatility-based-HOD-LOD-indicator; ‏xifan828/tradable-mind; ‏jayaliyev/nq_hourly-sweep-statistics; ‏matthewoestreich/fmpcloud-DailyHighLowTimeFrame; ‏TRiamder/Nasdaq-forecasting; ‏uga-gaim/AnalogEnsemble; ‏csnyder256/shadow-options-trading-lab; ‏cobriensr/Options-Strike-Calculator.
- Cboe: https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX1D_History.csv; https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv (הורדו ב-2026-10-11).
