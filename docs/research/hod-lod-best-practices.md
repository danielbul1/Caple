# חיזוי HOD/LOD של ES: מה עוד אפשר לשפר סטטיסטית

תאריך: 2026-10-11. היקף: שיטות סטטיסטיות לחיזוי הגבוה והנמוך של היום ולהתפלגות שלהם. נושאי מבנה שוק ומוצרים מסחריים מופיעים רק כהערה קצרה בסוף (לפי שינוי ההיקף).
נקודת המוצא היא Caple כפי שמתואר ב-README: yardstick של HAR על תנודתיות Parkinson שעתית, שילוב של חמישיות-טווח ו-k-NN (k=150) ביחס 50/50 קבוע, "already in" שהוא ממוצע 50/50 עם הילוך מקרי (reflection principle), וציון לפי pinball על הרמות 25/50/75.
סימון: **[לא אומת]** = טענה שלא מצאתי לה מקור ראשוני. "הערכה שלי" = שיפוט שלי ולא תוצאה מדווחת.

## תקציר

- **Yardstick אסימטרי ל-HOD ול-LOD.** היום אותו סקאלה משמשת לשני הצדדים. ב-Patton & Sheppard 2015 התנודתיות העתידית עוקבת יותר אחרי semivariance שלילית, ו-Chou 2006 מציג CARR אסימטרי לטווח העליון ולטווח התחתון. לא נבדק ב-Caple, וזול לבדוק.
- **VIX1D במקום VIX9D.** VIX9D כבר נתן -2% בפתיחה (שורה בטבלת README), ו-VIX1D בנוי במיוחד לטווח של היום הנוכחי. Albers 2025 מדווח ש-VIX1D מתוקן לפרמיית סיכון חזה טוב יותר מ-HAR ומ-HAR-VIX1D. החסם הוא מקור הנתונים, לא השיטה.
- **מדד ממומש טוב יותר ל-yardstick.** realized range מנרות 5 דקות (Martens & van Dijk 2007), ‏HARQ (Bollerslev, Patton & Quaedvlieg 2016) ו-HAR-CJ (Andersen, Bollerslev & Diebold 2007). קובץ 5m כבר קיים ב-legs.py.
- **ללמוד את משקלות השילוב במקום 50/50.** ממוצע של תחזיות מכוילות אינו מכויל (Ranjan & Gneiting 2010); ‏beta-transformed linear pool ל-"already in", ובדיקה של מיצוע quantiles מול מיצוע הסתברויות (Lichtendahl et al. 2013) לשילוב חמישיות ו-k-NN.
- **כיול מקוון (ACI/AgACI).** Gibbs & Candès 2021 ו-Zaffran et al. 2022 מתקנים את רמת ה-quantile בזמן אמת כך שהכיסוי נשמר תחת שינוי התפלגות. ה-journal מראה in-band בין 44% ל-55%, כלומר הכיסוי זז.
- **הילוך מקרי עם אי-ודאות בתנודתיות.** `rw_done` מניח שה-yardstick ידוע בדיוק. ערבוב על פני שגיאת ה-HAR מעבה את הזנבות, וייתכן שיהפוך את רמות ההילוך המקרי לשימושיות בשילוב.
- **קשיחות בהערכה.** CRPS על הרבה quantiles במקום שלושה, Diebold-Mariano עם Newey-West, מבחן Christoffersen לכיסוי מותנה ו-Model Confidence Set. כ-20 רעיונות כבר נבדקו, ולכן תוצאה עם t≈-2 אינה הוכחה (Harvey, Liu & Zhu 2016).
- **החלקה במדגמים קטנים.** ספירת 2-4 ימים בתא של 2 נקודות היא רעש בעיקר. סימולציה שלי מראה שגם כשההתפלגות האמיתית חלקה ויורדת, ה"קו הבהיר ביותר" נודד בין 3 ל-17 נקודות כשיש 24 ימים.

---

## 1. Yardstick אסימטרי (סקאלה נפרדת לעלייה ולירידה)

**מה זה.** במקום yardstick אחד `r5`, בונים שני yardsticks: אחד מ-semivariance חיובית או מהטווח העליון (high−open), ואחד מ-semivariance שלילית או מהטווח התחתון (open−low). כל אחד מהם הוא HAR. את ה-extras של HOD מנרמלים לפי הסקאלה העליונה, ואת אלה של LOD לפי התחתונה.
**מקורות.**
- Patton & Sheppard (2015), "Good volatility, bad volatility: Signed jumps and the persistence of volatility", *Review of Economics and Statistics* 97(3):683–697. ‏[Duke](https://scholars.duke.edu/publication/1082826), [working paper](https://public.econ.duke.edu/~ap172/Patton_Sheppard_Realized_Semivariance_7oct11.pdf). מדווחים שהתנודתיות העתידית קשורה יותר לתנודתיות של תשואות שליליות בעבר, ושמודלים מבוססי semivariance משפרים מובהקות את החיזוי מחוץ למדגם (S&P 500 ו-105 מניות).
- Chou (2005), "Forecasting Financial Volatilities with Extreme Values: The CARR Model", *JMCB* 37(3):561–582 ([RePEc](https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html)). מודל דינמי לטווח, שנותן ב-S&P 500 אומדנים חדים יותר מ-GARCH מחוץ למדגם. Chou (2006), "Modeling the Asymmetry of Stock Movements Using Price Ranges", *Advances in Econometrics* 20 ([RePEc](https://ideas.repec.org/h/eme/aecozz/s0731-9053(05)20009-9.html)) מרחיב את המודל לטווח עליון ותחתון נפרדים.

**נבדק ב-Caple?** לא. השורות "HAR on daily ranges" ו-"Parkinson alone" ב-README בודקות סקאלה סימטרית בלבד.
**ערך צפוי.** ה-pinball של LOD (27-28) גבוה מזה של HOD (23-25) בכל טבלאות ה-README, כך שיש אסימטריה. הערכה שלי: שיפור של 0.5-1.5% בפתיחה וב-2:00, וכמעט אפס אחרי 9:00, כי שם המיקום בטווח שולט.
**איך לבדוק.** מחשבים מהנרות השעתיים semivariance של עלייה וירידה (סכום ריבועי תשואות log חיוביות ושליליות), או את (high−open) ו-(open−low) היומיים. מתאימים HAR לכל צד על 2016-2021, בדיוק כמו `yardstick()`. ב-`extras()` מחלקים את up ב-r_up ואת down ב-r_down, ובתחזית מכפילים בסקאלות של היום. מריצים `python levels.py backtest`, ומשווים pinball לכל צד ולכל שעה, 2022-2026, עם t מזווג.

## 2. VIX1D (תנודתיות משתמעת ליום הנוכחי)

**מה זה.** מדד של Cboe שמבוסס על אופציות SPXW שפוקעות היום ומחר. בתחילת היום כמעט כל המשקל על הפקיעה של היום, והמשקל עובר לפקיעה של מחר במהלך היום ([Cboe](https://www.cboe.com/insights/posts/what-the-vix-and-vix-1-d-indices-attempt-to-measure-and-how-they-differ)). המדד הושק ב-24.4.2023.
**מקור.** Albers (2025), "A New Star Is Born: Does the VIX1D Render Common Volatility Forecasting Models for the US Equity Market Obsolete?", *Journal of Futures Markets* 45(11):2092–2108, ‏doi:10.1002/fut.70023 ([RePEc](https://ideas.repec.org/a/wly/jfutmk/v45y2025i11p2092-2108.html)). לפי התקציר, VIX1D מגזים בתנודתיות של S&P 500 ויש לו דפוס תוך-יומי עם מגמה עולה. VIX1D מתוקן לפרמיית סיכון מדויק יותר מ-HAR ומ-HAR-VIX1D כתחזית ליום אחד, ונראה שהוא קולט את המידע של אופציות 0DTE.
**נבדק ב-Caple?** חלקית. VIX9D נבדק ונתן -2% (t -5) בפתיחה ו-1% ב-9:00. הוא ירד יחד עם Yahoo (שורה ראשונה בטבלה). VIX1D עצמו לא נבדק.
**ערך צפוי.** זה המועמד החזק ביותר לשיפור בפתיחה. הערכה שלי: 1-3% מעבר ל-HAR, כי VIX9D לבדו כבר נתן 2%. **[לא אומת]** מאיזו שנה יש היסטוריה של VIX1D ב-Cboe (נכון לפרסום יש backtest רק לתקופות מסוימות). אם יש רק היסטוריה מ-2023, מדגם הבדיקה יהיה קצר (כ-600 ימים).
**איך לבדוק.** צריך מקור נתונים יומי (CSV היסטורי של Cboe או ספק אחר), ולקחת רק את הערך האחרון לפני 00:00 NY, כדי שלא תהיה הצצה קדימה. מוסיפים log(VIX1D) כרגרסור ל-HAR (HAR-X), או מחליפים את ה-yardstick ב-VIX1D מוכפל במקדם שמותאם walk-forward (תיקון הפרמיה של Albers). בודקים pinball בפתיחה, ב-2:00 וב-5:00 על החפיפה בלבד.

## 3. מדד ממומש מדויק יותר ל-yardstick

**מה זה.** ה-yardstick היום הוא Parkinson על נרות של שעה. אפשר לבנות אותו מ-5m.
**מקורות.**
- Martens & van Dijk (2007), "Measuring volatility with the realized range", *J. Econometrics* 138(1):181–207 ([RePEc](https://ideas.repec.org:443/a/eee/econom/v138y2007i1p181-207.html)). סכום טווחי high-low תוך-יומיים, עם תיקון הטיה לחיכוכי מיקרו-מבנה. בסימולציה ה-MSE שלו נמוך מזה של realized variance. נבדק על חוזי S&P 500.
- Bollerslev, Patton & Quaedvlieg (2016), "Exploiting the errors: A simple approach for improved volatility forecasting", *J. Econometrics* 192(1):1–18 ([Maastricht](https://cris.maastrichtuniversity.nl/en/publications/exploiting-the-errors-a-simple-approach-for-improved-volatility-f/)). מקדמי HAR משתנים לפי גודל שגיאת המדידה (realized quarticity), עם שיפור מובהק ב-S&P 500 ובמניות ה-DJIA.
- Andersen, Bollerslev & Diebold (2007), "Roughing It Up", *REStat* 89(4):701–720 ([NBER](https://www.nber.org/papers/w11775)). מפרידים קפיצות מהרכיב הרציף (HAR-RV-CJ). הקפיצות דועכות מהר יותר, ההפרדה משפרת את החיזוי, ורבות מהקפיצות חלות על פרסומי מאקרו.
- רקע: Corsi (2009), HAR-RV, *J. Financial Econometrics* 7(2):174–196 (כבר מצוטט ב-README).

**נבדק ב-Caple?** לא. נבדקו רק Parkinson שעתי מול טווח יומי וטווח ערב (שורות "HAR on daily ranges" ו-"Parkinson alone").
**ערך צפוי.** הערכה שלי: 0.3-1% בפתיחה. המעבר מטווח יומי ל-Parkinson שעתי הוריד את שגיאת log-range מ-6% ל-15%, ולכן מ-5m יש עוד מה להרוויח, אבל בתשואה פוחתת.
**איך לבדוק.** מחשבים realized range יומי מקובץ `lse_ES.F_5m.csv` (סכום של (ln H/L)² חלקי 4ln2 על נרות 5m), ומחליפים את `stats.park`. מתאימים מחדש את משקלות HAR על 2016-2021. אחר כך משווים: (א) RR, (ב) RR עם רכיב קפיצה, (ג) HARQ, שבו כל מקדם מוכפל ב-(1+θ·√RQ). מדד ההצלחה: pinball בפתיחה על 2022-2026.

## 4. משקלות שילוב נלמדים במקום 50/50 קבוע

**מה זה.** Caple מוסיף 50% משקל לימים מאותה חמישית ו-50% ל-k-NN (שזה ערבוב דגימות, כלומר מיצוע הסתברויות), ועושה ממוצע של `done` עם `rw_done` ביחס 50/50.
**מקורות.**
- Ranjan & Gneiting (2010), "Combining probability forecasts", *JRSS B* 72(1):71–91 ([RePEc](https://ideas.repec.org/a/bla/jorssb/v72y2010i1p71-91.html)). הם מראים שכל ממוצע משוקלל לא טריוויאלי של שתי תחזיות מכוילות שונות אינו מכויל וחסר חדות. ההצעה שלהם היא beta-transformed linear pool (BLP), כלומר טרנספורמציית בטא על הממוצע.
- Lichtendahl, Grushka-Cockayne & Winkler (2013), "Is It Better to Average Probabilities or Quantiles?", *Management Science* 59(7):1594–1611 ([RePEc](https://ideas.repec.org/a/inm/ormnsc/v59y2013i7p1594-1611.html)). מיצוע quantiles נותן התפלגות צרה יותר מאותו ממוצע, ובנתוני SPF ניצח את מיצוע ההסתברויות. ההכרעה בפועל אמפירית.

**נבדק ב-Caple?** רק 50/50. ה-README מציין ש"averaging them [RW levels] in did not help", אבל לא נבדקו משקל אחר או BLP.
**ערך צפוי.** הערכה שלי: log loss של "already in" יורד עוד 0.5-2%, כי BLP מתקן בדיוק את חוסר הכיול שממוצע יוצר. ב-pinball צפוי 0-0.7%.
**איך לבדוק.** (א) ל-"already in": בכל ינואר מתאימים לוגיסטית על logit(done_analog), ‏logit(rw_done) ושעה, על השנים הקודמות בלבד. זו גרסה פשוטה של stacking, ו-BLP מלא דורש α, β ו-w. (ב) לרמות: מחשבים quantiles נפרדים מחמישיות ומ-k-NN ועושים להם ממוצע, ומשווים לערבוב המשקלות הנוכחי. משווים log loss ו-pinball בשני החצאים (2017-21 ו-2022-26), כמו בטבלת ה-README.

## 5. כיול מקוון: Conformal / ACI

**מה זה.** עטיפה שמעדכנת את רמת ה-quantile בפועל אחרי כל יום: אם הרמה "75%" נחצתה יותר מדי לאחרונה, מזיזים את היעד. אין הנחת exchangeability.
**מקורות.**
- Gibbs & Candès (2021), "Adaptive Conformal Inference Under Distribution Shift", NeurIPS ([arXiv:2106.00170](https://arxiv.org/abs/2106.00170v3)). פרמטר אחד שמתעדכן בצעד גרדיאנט, ומבטיח כיסוי לטווח ארוך על כל מנבא או quantile estimator.
- Zaffran et al. (2022), "Adaptive Conformal Predictions for Time Series", ICML ([PMLR](https://proceedings.mlr.press/v162/zaffran22a.html)). ‏AgACI מבטל את הצורך לכוון את קצב הלמידה בעזרת צבירת מומחים, וכולל קוד.
- Romano, Patterson & Candès (2019), "Conformalized Quantile Regression", NeurIPS ([arXiv:1905.03222](https://arxiv.org/abs/1905.03222)). מכייל quantiles קיימים (כמו של Caple) ושומר על אדפטיביות להטרוסקדסטיות.

**נבדק ב-Caple?** לא. מה שנבדק הוא משקל לימים אחרונים (half-life), וזה דבר אחר.
**ערך צפוי.** בעיקר יציבות בכיול: in-band נע היום בין 44% ל-55% לפי שעה (טבלת ה-journal), והרמה "75%" הגולמית של QuantiStat הגיעה ל-86% בגלל עליית מחירים. ב-pinball הערכה שלי היא 0-0.5%, ויותר בתקופות של שינוי משטר.
**איך לבדוק.** לכל צד, שעה ו-quantile q מחזיקים α_t. ‏α_{t+1}=α_t+γ(q−1{y_t<level_t}), עם γ קטן (למשל 0.005), או AgACI על כמה ערכי γ. מחשבים את הרמה כ-`wquantile(..., α_t)`. מעריכים כיסוי מתגלגל על 250 יום, ו-pinball מול הגרסה הקיימת.

## 6. הילוך מקרי עם תנודתיות לא ודאית

**מה זה.** `rw_done` משתמש ב-sd=RW_SIGMA·√REMAINING[hour], כלומר מניח שה-yardstick של היום הוא התנודתיות האמיתית. בפועל לשגיאת HAR יש פיזור log-normal. אינטגרציה של `rw_done` על פני התפלגות σ נותנת התפלגות עם זנבות עבים יותר, כמו t של Student.
**מקור.** ה-reflection principle וההתפלגות של מקסימום תנועה בראונית הם קלאסיים. Caple כבר מצטט את Mok, Lam & Li 2000. ש-HAR של log-RV משאיר שגיאה בפיזור מסוים עולה מ-Corsi 2009 ומ-Bollerslev et al. 2016, ששם גודל השגיאה משתנה בזמן. אין מאמר ספציפי שבדק את זה על HOD/LOD **[לא אומת]**.
**נבדק ב-Caple?** הגרסה עם σ ידוע נבדקה ונשמרה. הרמות שלה "as good as the analogs", אבל השילוב לא עזר. גרסת הערבוב לא נבדקה.
**ערך צפוי.** הערכה שלי: log loss של "already in" יורד 0.5-1.5% בשעות 2:00-9:00. ייתכן גם שהרמות הפרמטריות יעזרו בזנבות (quantiles מעבר ל-25/75).
**איך לבדוק.** מעריכים walk-forward את סטיית התקן של log(טווח בפועל/yardstick), ומחשבים E[rw_done(dist·r/σ)] על r~LogNormal(0,s²) באינטגרציה גאוס-הרמיט (7 נקודות). מחליפים ב-`rw_done` ובודקים log loss ו-calls right.

## 7. החלקה במדגמים קטנים ורעש בתאים

**מה זה.** הרמות הן `wquantile` אמפירי, וזה בסדר כשיש k=150 ועוד ימי חמישית. אבל: (א) אחרי 12:00 מעט ימים "הולכים רחוק יותר", כך שה-quantiles נשענים על מעט תצפיות. (ב) ה-heatmap סופר ימים בתאים של נקודה, כך שכל תא מקבל מעט ימים.
**מקורות.** Harrell & Davis (1982), אומדן quantile כממוצע משוקלל בטא של כל סטטיסטי הסדר, *Biometrika* 69(3):635–640 **[לא אומת מול המקור, ציטוט מהזיכרון]**. ‏Brown, Cai & DasGupta (2001), רווחי סמך לפרופורציה בינומית (Wilson וכו'), *Statistical Science* 16(2):101–133 **[לא אומת מול המקור]**.
**ראיה (סימולציה שלי, `binsim.py` ב-scratchpad).** מרחקי HOD מחצי-נורמלית (מדיאנה כ-20 נקודות, צפיפות אמיתית יורדת מ-0), בתאים של 2 נקודות, 5,000 חזרות (QuantiStat עצמו משתמש בתאים של נקודה, שבהם הספירות קטנות עוד יותר):

| ימים במדגם | ספירה בתא הבהיר ביותר (חציון / p90) | מיקום התא הבהיר (רבעונים, נקודות) |
|---|---|---|
| 24 | 3 / 4 | 3 / 9 / 17 |
| 52 (≈ אותו יום בשבוע, שנתיים) | 5 / 7 | 3 / 9 / 15 |
| 104 | 9 / 11 | 3 / 7 / 13 |
| 500 | 33 / 37 | 3 / 7 / 11 |

השכיח האמיתי הוא 0-2 נקודות, ובכל זאת התא הבהיר נודד על פני 10-15 נקודות רק בגלל רעש. זה מסביר את ממצא ה-README ש"bright heatmap lines: no better than a random day's".
**נבדק ב-Caple?** כן לגבי הקווים הבהירים (נדחו), וה-heatmap כבר מסתיר תאים של יום בודד. החלקה של quantiles לא נבדקה.
**ערך צפוי.** pinball: הערכה שלי היא 0-0.5%, בעיקר ב-15:00. התועלת העיקרית היא ב-UX: KDE עם רוחב פס שנבחר בכלל אצבע או ב-cross-validation, במקום ספירות.
**איך לבדוק.** מחליפים את `wquantile` בגרסה משוקללת של Harrell-Davis, ומשווים pinball לפי שעה, בדגש על 12:00 ו-15:00. ב-heatmap מציגים צפיפות KDE עם רצועת bootstrap.

## 8. קשיחות בהערכה ובדיקות מרובות

**מה זה.** הכלים הקיימים (pinball על 3 quantiles, t מזווג) טובים, אבל חסרים כמה דברים:
- **CRPS / pinball על הרבה quantiles.** CRPS הוא אינטגרל ה-pinball על כל ה-quantiles, ומודד גם זנבות. ‏Gneiting & Raftery (2007), "Strictly proper scoring rules, prediction, and estimation", *JASA* 102(477):359–378 ([DTIC](https://apps.dtic.mil/sti/pdfs/ADA459827.pdf)). שם מוצג גם ה-interval score, שמשלב רוחב וכיסוי.
- **PIT וחדות מותנית בכיול.** Gneiting, Balabdaoui & Raftery (2007), *JRSS B* 69(2):243–268 ([PDF](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf)).
- **כיסוי מותנה.** Christoffersen (1998), "Evaluating Interval Forecasts", *IER* 39(4):841–862 ([RePEc](https://ideas.repec.org:443/a/ier/iecrev/v39y1998i4p841-62.html)). בודקים שהחריגות מה-band לא מתקבצות בזמן (שרשרת מרקוב).
- **השוואת תחזיות.** Diebold & Mariano (1995), *JBES* 13(3):253–263, עם תיקון Harvey-Leybourne-Newbold ל-HAC. ‏Giacomini & White (2006), "Tests of Conditional Predictive Ability", *Econometrica* 74(6):1545–1578 ([Econometric Society](https://econometricsociety.org/publications/econometrica/2006/11/01/tests-conditional-predictive-ability)). הפרש ההפסד היומי מתואם סדרתית (משטרי תנודתיות), ו-t מזווג רגיל מנפח את המובהקות.
- **בדיקות מרובות.** Hansen, Lunde & Nason (2011), "The Model Confidence Set", *Econometrica* 79(2):453–497 ([RePEc](https://ideas.repec.org/a/ecm/emetrp/v79y2011i2p453-497.html)). ‏Bailey, Borwein, López de Prado & Zhu (2017), "The Probability of Backtest Overfitting", *J. Computational Finance* 20(4) ([SSRN](https://papers.ssrn.com/abstract=2326253)). ‏Harvey, Liu & Zhu (2016), *RFS* 29(1):5–68 ([NBER](https://www.nber.org/papers/w20592)): עם הרבה ניסיונות הסף הסביר הוא t>3.

**נבדק ב-Caple?** חלקית: pinball, calibration ו-t מזווג על שני חצאים. זה מנגנון הגנה טוב, אבל לא כולל HAC ולא MCS.
**ערך צפוי.** לא שיפור בדיוק, אלא הגנה מפני "שיפורים" מזויפים. דוגמה מה-README: event-day weighting עם t -2.1 ו-hour-update עם t -0.8 נדחו בצדק, ותיקון HAC עשוי להחליש עוד כמה תוצאות של t≈-3 עד -5.
**איך לבדוק.** מוסיפים ל-scorecard: (א) pinball על q=0.05..0.95, (ב) t עם Newey-West (lag≈5) על הפרש ההפסד היומי HOD+LOD, (ג) MCS על כל הווריאנטים שנשמרו, (ד) LR של Christoffersen על in-band ב-journal.csv.

## 9. מודלים של התפלגות מותנית כ-benchmark

**מקורות.** Meinshausen (2006), "Quantile Regression Forests", *JMLR* 7:983–999 ([JMLR](https://www.jmlr.org/papers/v7/meinshausen06a.html)). ‏Henzi, Ziegel & Gneiting (2021), "Isotonic distributional regression", *JRSS B* 83(5):963–993 ([arXiv:1909.03725](https://arxiv.org/abs/1909.03725)): התפלגות מכוילת בלי כוונון פרמטרים, תחת מונוטוניות במשתנים, ומוצעת כ-benchmark. ‏Delle Monache et al. (2013), Analog Ensemble, *MWR* 141:3498–3516 ([UCAR](https://opensky.library.ucar.edu/islandora/object/articles%3A12922)) הוא מה ש-Caple כבר עושה.
**נבדק ב-Caple?** כן במשפחה: LightGBM quantile נבדק ונדחה, ו-k-NN (AnEn) נשמר.
**ערך צפוי.** נמוך. QRF הוא k-NN עם מטריקה נלמדת. IDR מעניין רק כבדיקת שפיות: אם מודל בלי כוונון משתווה ל-Caple, יש סימן שאין עוד הרבה מה לסחוט.
**איך לבדוק.** IDR (חבילת `isodistrreg`, יש גם ב-Python) עם יחס סדר על (מרחק מהגבוה, מרחק מהנמוך, שעה), ב-walk-forward שנתי.

## 10. מידול משותף של high ו-low ברמה יומית

**מקורות.** Cheung, Cheung & Wan (2009), "A high-low model of daily stock price ranges", *J. Forecasting* 28(2):103–119 ([CESifo WP](https://www.cesifo.org/DocDL/cesifo1_wp2387.pdf)): ‏high ו-low מקושרים ב-cointegration, ו-VECM נותן יתרון מסוים בחיזוי high ו-low, אבל לא בחיזוי הטווח. ‏Caporin, Ranaldo & Santucci de Magistris (2013), *J. Banking & Finance* 37(12):5132–5146 ([SNB WP](https://www.snb.ch/en/mmr/papers/id/working_paper_2011_11)): ‏FVECM שמנצל cointegration וזיכרון ארוך של הטווח. ‏González-Rivera, Luo & Ruiz (2020), *J. Applied Econometrics* 35(4):373–390 ([PDF](https://faculty.ucr.edu/~ggonzale/publications/jae_ggr_luo_ruiz2020.pdf)): אזורי חיזוי משותפים ל-low/high של S&P 500 בבוטסטרפ. ‏Jones (2015), MPRA 62664 ([PDF](https://mpra.ub.uni-muenchen.de/62664/1/MPRA_paper_62664.pdf)): המיקום של הפתיחה ביחס ל-high ול-low של אתמול כמנבא (מסמך עבודה, לא שפיט).
**נבדק ב-Caple?** חלקית. overnight gap כממד k-NN נבדק ונדחה (+0.1%/+0.4%). המיקום של הפתיחה ביחס ל-high/low של אתמול לא נבדק.
**ערך צפוי.** נמוך. החלק של "high ו-low צפויים" במאמרים האלה בא בעיקר מה-cointegration עם המחיר, ש-Caple כבר מנצל בכך שהוא מודד מרחקים מהפתיחה. החלק שנשאר הוא חיזוי הטווח, וזה ה-yardstick.
**איך לבדוק.** ממד k-NN בפתיחה: (open−prevHigh)/r ו-(open−prevLow)/r. כרגע בפתיחה אין k-NN בכלל, רק כל הימים.

## 11. תזמון ה-HOD/LOD

**מקורות.** חוק ה-arcsine לזמן המקסימום של תנועה בראונית הוא קלאסי. המחקר האמפירי שמצאתי: מאמר ב-*Applied Economics* 37(2) על התפלגות בטא מוכללת לזמן ההגעה הראשונה למקסימום או למינימום, שמוצאת צורת U בבורסת אתונה ([T&F](https://www.tandfonline.com/doi/abs/10.1080/00036840412331315006)). את המאמר המלא לא קראתי. Andersen & Bollerslev (1997), "Intraday periodicity and volatility persistence", *J. Empirical Finance* 4(2–3):115–158 ([RePEc](https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html)): צריך למדל את המחזוריות התוך-יומית לפני הדינמיקה. לא מצאתי מאמר שבודק חוק arcsine מול HOD/LOD של מדד מניות **[לא אומת]**.
**נבדק ב-Caple?** כן במובלע: `REMAINING` הוא פרופיל השונות התוך-יומי. `quantistat.py` מצייר time_based בלי כיול.
**ערך צפוי.** אין השפעה על pinball. זו תוספת מוצר: תחזית מכוילת לשעת ה-HOD מתוך אותם משקלות analog, ומבחן שלה מול ה-arcsine המעוות לפי `REMAINING` (log loss על 24 שעות).

---

## טבלה מדורגת

| # | רעיון | מקור | נבדק? (שורה ב-README) | שיפור צפוי (הערכה שלי) | מאמץ |
|---|---|---|---|---|---|
| 1 | VIX1D מתוקן ב-yardstick | Albers 2025 | VIX9D: ‎-2% בפתיחה, נשמט עם Yahoo | 1-3% בפתיחה | בינוני (מקור נתונים) |
| 2 | Yardstick אסימטרי עלייה/ירידה | Patton & Sheppard 2015; Chou 2006 | לא | 0.5-1.5% בפתיחה ועד 5:00 | נמוך |
| 3 | משקלות שילוב נלמדים / BLP / מיצוע quantiles | Ranjan & Gneiting 2010; Lichtendahl et al. 2013 | רק 50/50 | log loss ‏0.5-2%, ‏pinball 0-0.7% | נמוך |
| 4 | RW עם ערבוב על אי-ודאות σ | reflection + שגיאת HAR | σ ידוע: נשמר | log loss ‏0.5-1.5% | נמוך |
| 5 | Realized range מ-5m / HARQ / HAR-CJ | Martens & van Dijk 2007; BPQ 2016; ABD 2007 | Parkinson שעתי בלבד | 0.3-1% בפתיחה | נמוך-בינוני |
| 6 | ACI/AgACI/CQR לכיול מקוון | Gibbs & Candès 2021; Zaffran 2022; Romano 2019 | לא (half-life ≠) | כיול יציב, ‏pinball 0-0.5% | נמוך |
| 7 | הערכה: CRPS, ‏HAC-DM, ‏MCS, ‏Christoffersen | Gneiting & Raftery 2007; DM 1995; HLN 2011; Christoffersen 1998 | חלקי | הגנה מפני שיפורים מזויפים | נמוך |
| 8 | החלקת quantiles ו-heatmap (Harrell-Davis, ‏KDE) | Harrell & Davis 1982 [לא אומת] | קווים בהירים: נדחו | 0-0.5% (‏15:00), ‏UX גבוה | נמוך |
| 9 | IDR / QRF כ-benchmark | Henzi et al. 2021; Meinshausen 2006 | LightGBM: נדחה | ~0 | בינוני |
| 10 | Open מול high/low של אתמול, VECM | Jones 2015; Cheung et al. 2009 | gap: נדחה | ~0-0.3% | נמוך |
| 11 | תחזית מכוילת לשעת HOD/LOD | arcsine; Andersen & Bollerslev 1997 | לא (רק תרשים) | מוצר, לא pinball | נמוך |

הכלל מה-README נשאר בתוקף: הכיוון לא צפוי, ולכן הגבול לשיפור הוא חיזוי גודל היום (1, 2, 5) והכיול (3, 4, 6). על התקרה של ידיעת ה-bias (pinball 18/22) לא ניתן לעבור דרך אף אחד מהרעיונות האלה.

## הערה קצרה: מבנה שוק

- Baltussen, Da, Lammers & Martens (2021), "Hedging Demand and Market Intraday Momentum", *JFE* 142(1):377–403 ([PDF](https://www3.nd.edu/~zda/intramom.pdf)): התשואה של שאר היום מנבאת את 30 הדקות האחרונות, ב-60+ חוזים עתידיים, ומקושרת ל-gamma hedging. בשביל Caple זה מועמד לפיצ'ר רק בבדיקת 15:00, לגבי ה-HOD/LOD בשעה שלפני הסגירה (16:00).
- המידע של 0DTE נקלט ב-VIX1D לפי Albers 2025 (רעיון 1), כך שאין צורך במודל gamma נפרד לפני שבודקים אותו.
- ABD 2007: קפיצות מתרכזות בפרסומי מאקרו. ב-Caple, משקל לימי FOMC/CPI נבדק ונדחה כרעש. גרסת HAR-CJ (רעיון 5) היא הדרך הסטטיסטית להכניס את זה.
- Opening range / initial balance: נכלל ב-Caple במובלע, דרך המיקום בטווח עד כה וה-k-NN אחרי כל שעה.

## מה ללמוד מ-QuantiStat (בכנות)

- **לא מצאתי עמוד מוצר ראשוני, תיעוד שיטה או track record מאומת** ל-QuantiStat בחיפושים (שלושה חיפושים שונים לא החזירו את המוצר). כל מה שלהלן מבוסס על מה ש-Caple שחזר ובדק (README ו-`quantistat.py`), לא על טענות היצרן **[לא אומת מול מקור ראשוני]**.
- **השיטה כפי שהיא נראית:** היסטוגרמה אמפירית של מרחקי HOD/LOD מהפתיחה, בנקודות גולמיות, על כל הימים בחלון ה-Period (ברירת מחדל שנתיים, נמדד אצלם מתאריך ההרצה; מצב QuantiStat באפליקציה מודד מה-End Date), בלי פיצול לפי bias ב-Price Based, מוצגת כ-heatmap של תאים של נקודה. סטטיסטית יש שלוש בעיות: (1) נקודות לא מנורמלות הן לא סטציונריות, והרמה "75%" הגיעה ל-86% (README, Scorecard). (2) גם ב-500 ימים התא הבהיר נודד על פני כ-8 נקודות רק בגלל רעש (טבלה בסעיף 7, בתאים של 2 נקודות; בתאים של נקודה הספירות קטנות עוד יותר). (3) "הקו הבהיר" הוא שכיח של היסטוגרמה רועשת, שנבחר כמקסימום ולכן מוטה (winner's curse), ובפועל לא טוב מיום אקראי (README). כלל "הקצה הפנימי של הרצועה הבהירה" שקול ל-quantile אמפירי שמרני (כ-83-86% הגעה), לפי הבדיקה הקודמת בסשן הזה.
- **מה כן ללמוד, ברמת המוצר:** (א) הצגה ויזואלית של התפלגות מותנית (heatmap), שסוחר קורא מהר. (ב) פיצול ל-Price Based ול-Time Based. (ג) הרעיון של "Level Validator", כלומר שאלה על רמה ספציפית שהסוחר בחר. אצל Caple אפשר לתת לשאלה הזאת תשובה מכוילת: "ההסתברות שה-HOD יגיע או לא יגיע ל-X", מתוך אותם משקלות analog ועם ACI, במקום ספירה גולמית. ה-README כבר מראה שגם כשמגיעים לרמה החציונית, המחיר ממשיך בממוצע עוד 17-38 נקודות.
- **מה לא ללמוד:** סינון לפי יום בשבוע או בחודש (נבדק ונדחה), נקודות גולמיות, וקווים בהירים כאותות.

## מקורות

- Albers, S. (2025). A New Star Is Born: Does the VIX1D Render Common Volatility Forecasting Models for the US Equity Market Obsolete? *J. Futures Markets* 45(11). https://ideas.repec.org/a/wly/jfutmk/v45y2025i11p2092-2108.html
- Andersen, T., Bollerslev, T. (1997). Intraday periodicity and volatility persistence in financial markets. *J. Empirical Finance* 4. https://ideas.repec.org:443/a/eee/empfin/v4y1997i2-3p115-158.html
- Andersen, T., Bollerslev, T., Diebold, F. (2007). Roughing It Up. *REStat* 89(4). https://www.nber.org/papers/w11775
- Bailey, D., Borwein, J., López de Prado, M., Zhu, Q. (2017). The Probability of Backtest Overfitting. *J. Comp. Finance* 20(4). https://papers.ssrn.com/abstract=2326253
- Baltussen, G., Da, Z., Lammers, S., Martens, M. (2021). Hedging Demand and Market Intraday Momentum. *JFE* 142(1). https://www3.nd.edu/~zda/intramom.pdf
- Bollerslev, T., Patton, A., Quaedvlieg, R. (2016). Exploiting the errors. *J. Econometrics* 192(1). https://cris.maastrichtuniversity.nl/en/publications/exploiting-the-errors-a-simple-approach-for-improved-volatility-f/
- Caporin, M., Ranaldo, A., Santucci de Magistris, P. (2013). On the predictability of stock prices: a case for high and low prices. *JBF* 37(12). https://www.snb.ch/en/mmr/papers/id/working_paper_2011_11
- Cboe. What the VIX and VIX1D Indices Attempt to Measure. https://www.cboe.com/insights/posts/what-the-vix-and-vix-1-d-indices-attempt-to-measure-and-how-they-differ
- Cheung, Y.-L., Cheung, Y.-W., Wan, A. (2009). A high-low model of daily stock price ranges. *J. Forecasting* 28(2). https://www.cesifo.org/DocDL/cesifo1_wp2387.pdf
- Chou, R. Y. (2005). The CARR Model. *JMCB* 37(3). https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html
- Chou, R. Y. (2006). Modeling the Asymmetry of Stock Movements Using Price Ranges. *Adv. Econometrics* 20. https://ideas.repec.org/h/eme/aecozz/s0731-9053(05)20009-9.html
- Christoffersen, P. (1998). Evaluating Interval Forecasts. *IER* 39(4). https://ideas.repec.org:443/a/ier/iecrev/v39y1998i4p841-62.html
- Delle Monache, L. et al. (2013). Probabilistic weather prediction with an analog ensemble. *MWR* 141. https://opensky.library.ucar.edu/islandora/object/articles%3A12922
- Diebold, F., Mariano, R. (1995). Comparing Predictive Accuracy. *JBES* 13(3). https://www.statsmodels.org/dev/generated/statsmodels.tsa.stattools.diebold_mariano_test.html (מימוש; המאמר עצמו לא נקרא)
- Gibbs, I., Candès, E. (2021). Adaptive Conformal Inference Under Distribution Shift. NeurIPS. https://arxiv.org/abs/2106.00170v3
- Giacomini, R., White, H. (2006). Tests of Conditional Predictive Ability. *Econometrica* 74(6). https://econometricsociety.org/publications/econometrica/2006/11/01/tests-conditional-predictive-ability
- Gneiting, T., Raftery, A. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA* 102. https://apps.dtic.mil/sti/pdfs/ADA459827.pdf
- Gneiting, T., Balabdaoui, F., Raftery, A. (2007). Probabilistic forecasts, calibration and sharpness. *JRSS B* 69(2). https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jrssb.pdf
- González-Rivera, G., Luo, Y., Ruiz, E. (2020). Prediction regions for interval-valued time series. *JAE* 35(4). https://faculty.ucr.edu/~ggonzale/publications/jae_ggr_luo_ruiz2020.pdf
- Hansen, P., Lunde, A., Nason, J. (2011). The Model Confidence Set. *Econometrica* 79(2). https://ideas.repec.org/a/ecm/emetrp/v79y2011i2p453-497.html
- Harvey, C., Liu, Y., Zhu, H. (2016). …and the Cross-Section of Expected Returns. *RFS* 29(1). https://www.nber.org/papers/w20592
- Henzi, A., Ziegel, J., Gneiting, T. (2021). Isotonic distributional regression. *JRSS B* 83(5). https://arxiv.org/abs/1909.03725
- Jones, R. (2015). MPRA Paper 62664 (proximity variables for daily high/low). https://mpra.ub.uni-muenchen.de/62664/1/MPRA_paper_62664.pdf
- Lichtendahl, K., Grushka-Cockayne, Y., Winkler, R. (2013). Is It Better to Average Probabilities or Quantiles? *Mgmt Sci* 59(7). https://ideas.repec.org/a/inm/ormnsc/v59y2013i7p1594-1611.html
- Martens, M., van Dijk, D. (2007). Measuring volatility with the realized range. *J. Econometrics* 138(1). https://ideas.repec.org:443/a/eee/econom/v138y2007i1p181-207.html
- Meinshausen, N. (2006). Quantile Regression Forests. *JMLR* 7. https://www.jmlr.org/papers/v7/meinshausen06a.html
- Patton, A., Sheppard, K. (2015). Good volatility, bad volatility. *REStat* 97(3). https://scholars.duke.edu/publication/1082826
- Ranjan, R., Gneiting, T. (2010). Combining probability forecasts. *JRSS B* 72(1). https://ideas.repec.org/a/bla/jorssb/v72y2010i1p71-91.html
- Rogers, L.C.G., Satchell, S. (1991). Estimating Variance From High, Low and Closing Prices. *Ann. Appl. Prob.* 1(4). https://projecteuclid.org/euclid.aoap/1177005835 (רקע; מומלץ אם עוברים ל-yardstick ברמת נר שמתחשב ב-drift)
- Romano, Y., Patterson, E., Candès, E. (2019). Conformalized Quantile Regression. NeurIPS. https://arxiv.org/abs/1905.03222
- Yang, D., Zhang, Q. (2000). Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices. *J. Business* 73(3). https://scholars.cityu.edu.hk/en/publications/drift-independent-volatility-estimation-based-on-high-low-open-an/ (רקע)
- Zaffran, M. et al. (2022). Adaptive Conformal Predictions for Time Series. ICML. https://proceedings.mlr.press/v162/zaffran22a.html
- ציטוטים מהזיכרון שלא אומתו בסשן הזה: Harrell & Davis 1982 (*Biometrika* 69(3)); ‏Brown, Cai & DasGupta 2001 (*Stat. Science* 16(2)); ‏Corsi 2009 (*J. Fin. Econometrics* 7(2), כבר ב-README).
