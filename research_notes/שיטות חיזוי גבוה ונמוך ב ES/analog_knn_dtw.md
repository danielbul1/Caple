# Analog / k-NN Forecasting and DTW Pattern Matching for ES Daily High/Low Levels and Timing

Scope: how analog (k-nearest-neighbor) forecasting and Dynamic Time Warping (DTW) work; how meteorology/energy (the most mature analog field) and markets use them; evidence; pitfalls; lessons for a system that each day takes the last ~2 years of ES data up to the prior close, picks ~10 similar days, and shows where (points from a reference) and when (hour) those days' HOD/LOD formed, split by bullish/bearish bias. Research date: Oct 2026. Tool budget was limited, so several primary PDFs (Delle Monache 2013 full text, Nakagawa 2018 full text, Tsinaslanidis full texts, van den Dool 1994) were seen only as abstracts or second-hand. Gaps below say where.

## 1. Analog/k-NN mechanics: features, distance, normalization, k, weighting, overlap

### Takeaway
Every analog method has the same core: turn "today" into a feature vector, scale each feature so none dominates, measure distance to every historical vector, keep the k closest (often weighted by closeness), and treat their outcomes as a conditional sample. Normalization and feature choice matter as much as the algorithm. k is easy to overfit, and overlapping windows make agreement among neighbors look stronger than it is. I found no published, validated "standard" feature set for "similar days" in intraday index futures. Practitioner feature lists are conventions, not evidence-backed results.

### Cited Findings
- Generic kNN analog recipe (practitioner description): encode recent behavior as a vector of normalized returns, prices or indicator readings; find the k most similar historical windows, usually by Euclidean distance; average their subsequent paths or tally a directional vote — [LuxAlgo, kNN Analog Forecasting](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md)
- Same source: normalization (z-score or min-max) "matters as much as the algorithm", because raw price levels from different periods aren't comparable. Irrelevant inputs dilute the distance and degrade neighbor quality — [LuxAlgo](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md)
- Same source on k: a small k depends on a few possibly unrepresentative episodes; a large k drifts toward the unconditional mean; k is easy to overfit and should be validated out of sample. Distance-weighted votes reduce sensitivity to k. Kernel regression is the continuous-weight alternative to kNN's hard cutoff — [LuxAlgo](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md)
- Same source: adjacent windows overlap, so neighbors are rarely independent and "can exaggerate apparent agreement". Skipping overlapping windows brings analogs closer to independent. Listed pitfalls: non-stationarity, poor normalization, look-ahead leakage, overfitting k. The page gives no performance statistics and frames the output as "a set of historical scenarios, not a prediction" — [LuxAlgo](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md)
- The meteorological analog metric (Delle Monache et al.) is a weighted Euclidean distance. Each variable's squared difference is divided by that variable's historical standard deviation σ (z-scaling) and multiplied by an importance weight wᵢ. Differences are summed over a short time window ±t̃ around the target time, so the trend is matched as well as the level — [Hu, Cervone, Young, Delle Monache, arXiv 2103.04530](https://arxiv.org/pdf/2103.04530)
- Alternative metrics in practitioner kNN scripts: Lorentzian distance Σ log(1+|xᵢ−yᵢ|) is used instead of Euclidean because squaring differences makes Euclidean "extremely sensitive to outliers" — [Pineify, Lorentzian Classification guide](https://pineify.app/pine-script/indicators/lorentzian-classification); the [TradingView "Machine Learning: Lorentzian Classification"](https://www.tradingview.com/script/WhBzgfDu-Machine-Learning-Lorentzian-Classification/) script claims it is more robust to outliers and event-driven distortions
- Distance-weighting evidence (finance): in a month-ahead stock-index direction study, weighting neighbors by w(r)=1/r (inverse IDTW distance) gave "higher or the same" accuracy as equal weights on all 8 indices tested — [Cao, Okuno, Nakagawa, Shimodaira, arXiv 2112.13951](https://arxiv.org/pdf/2112.13951)
- k selection by walk-forward in the same study: k is chosen from {1..30} each month as the value with the best accuracy over the prior 24 months, training on months t−192..t−25 (rolling, so it is not frozen) — [arXiv 2112.13951](https://arxiv.org/pdf/2112.13951)
- Session definition determines the features: CME equity e-mini futures (ES) trade one session from 15:30 CT (17:00 CT Sundays/holidays) to 15:15 CT the next day. Daily highs and lows that include overnight trading differ from RTH-only extremes and timestamps — [eSignal forum](https://forum.esignal.com/forum/product-data-category/data-inquiries/24328-es-eod-vs-5-min); see also [NexusFi thread on ES ETH/RTH daily close](https://futures.io/emini-emicro-index/49305-what-intraday-bar-close-use-es-s-p-500-futures-contract-eth-rth-daily-close.html)

### Inferences
- For daily ES "similar day" vectors, the meteorological recipe carries over directly: z-score or ATR-scale every feature (prior-day range/ATR, gap/ATR, overnight range/ATR, prior close location in range, prior-day direction, ATR percentile regime, VIX level/change), set explicit importance weights wᵢ, and optionally add a ±1-day window (t̃=1) so the last 2–3 days' trajectory is matched, not just yesterday.
- Categorical features (day of week, inside/outside day, FOMC/CPI day) don't fit a Euclidean metric well. Exact-match filters or large penalty weights work better than numeric codes, which create fake distances (e.g., Monday→Friday = 4).
- Mahalanobis distance handles correlated features (prior range, overnight range and ATR are strongly collinear). Without it, the volatility "concept" gets triple-weighted. PCA before distance is another option; Junk et al. used PCA in their weight search (section 2).
- With ~500 candidate days in a 2-year window, a 1/d weighting where d→0 lets one near-duplicate dominate. Add a floor, or use a Gaussian kernel exp(−d²/h²).

### Gaps
- No peer-reviewed study found that compares feature sets (gap, overnight range, VIX, DOW, inside/outside) for intraday futures "similar day" selection. Feature lists in the wild come from practitioner convention.
- No source found that tests Mahalanobis vs Euclidean vs cosine on daily futures analogs.

## 2. Analog Ensemble (AnEn) in meteorology/energy: method, calibration, verification, what traders can borrow

### Takeaway
The AnEn (Delle Monache et al. 2013, Monthly Weather Review 141:3498–3516) turns one deterministic forecast into a probabilistic one. It finds the N past forecasts most similar to today's and uses the observations that verified for those past dates as ensemble members. It is judged with probabilistic scores (CRPS, rank histograms, spread-skill, reliability), not hit rate. Main lessons: predictor weights matter a lot; equal weights tend to give over-dispersed (too wide) ensembles; and good analogs require a large archive, which gets much larger as dimensionality grows.

### Cited Findings
- AnEn definition: for a given location and lead time, an analog is a past prediction from the same model with similar values of selected features of the current forecast. Observations paired with the best analogs form a probability distribution of the future state. Tested on 0–48 h 10-m wind and 2-m temperature at 550 US stations (Apr–Jul 2011). AnEn showed strong statistical consistency and reliability, captured flow-dependent error, and matched or beat logistic regression on either the deterministic model or the 21-member REPS ensemble — [Delle Monache et al. 2013, UCAR OpenSky record](https://opensky.library.ucar.edu/islandora/object/articles%3A12922) (abstract-level; full text not retrieved)
- Metric details: weighted, σ-normalized Euclidean distance over a short time window (t̃ "usually set to 1"). AnEn "thrives in cases where historical archives of observations and forecasts are sufficient". The main difficulty is defining the weights, which usually needs feature selection plus an extensive weight search — [arXiv 2103.04530](https://arxiv.org/pdf/2103.04530)
- Predictor weighting by CRPS minimization: Junk, Delle Monache, Alessandrini, Cervone & von Bremen (2015, Meteorologische Zeitschrift) brute-force searched predictor weights to minimize CRPS, combined with PCA. They report up to 20% improvement in AnEn performance at onshore/offshore wind-power sites — [DOAJ record](https://doaj.org/article/30ef89c3262546538765d3db32355578); [Penn State Pure](https://pure.psu.edu/en/publications/predictor-weighting-strategies-for-probabilistic-wind-power-forec/)
- Analog-based EMOS also tunes analog predictor weights by CRPS minimization (100-m wind, 6 towers) — [UCAR data record](https://data.ucar.edu/dataset/79c2b7c5-27bd-46c0-aba4-9e8f72c3c281)
- Calibration diagnostics in practice: an 11-member equally weighted AnEn for solar irradiance was "slightly over-dispersed, or under-confidence", shown by a convex rank histogram and negative missing-rate error (MRE). Using all available variables "without discrimination" makes relevant analogs hard to find and the spread too large. Weight-optimized AnEn was slightly under-dispersed. A machine-learned similarity metric gave an almost flat rank histogram for wind. Spread-error (spread-skill) diagrams test whether the ensemble spread tracks actual error. The hardest cases were abrupt regime changes — [arXiv 2103.04530](https://arxiv.org/pdf/2103.04530)
- Archive size vs dimensionality: van den Dool (1994, Tellus A) showed that for high-dimensional systems the waiting time for a good analog grows with dimension (a curse of dimensionality). That explains why Lorenz's five years of twice-daily data found no good atmospheric analogs — [arXiv 2101.10640 summarizing van den Dool](https://arxiv.org/pdf/2101.10640) (secondary source; original not retrieved)

### Inferences (what to borrow for ES)
- Treat the ~10 analogs as an ensemble and verify it probabilistically every day out of sample:
  - Rank histogram (PIT) of the realized HOD-distance (and LOD-distance, HOD hour) within the 10 analog values. With 10 members there are 11 rank bins; a flat histogram means calibrated, U-shaped means too narrow (overconfident), and dome-shaped means too wide.
  - CRPS of the analog distribution vs a "climatology" baseline of 10 random days, or all days, from the same 2-year window. The analog step adds value only if its CRPS skill score beats that baseline.
  - Spread-skill: on days when the analogs disagree a lot, realized error should be larger.
- Tune feature weights by walk-forward CRPS minimization (Junk et al. style), not by eyeballing. Expect equal-weight, many-feature versions to be over-dispersed and close to climatology.
- van den Dool's lesson scales down: with ~500 days in a 2-year archive, only a few features (roughly 3–5 effective dimensions) can be matched before the "nearest" days stop being close. More features means worse analogs, not better ones.
- An AnEn uses the realized outcome of each analog day (observations), not a model output. The ES equivalent is the realized HOD/LOD distance and time for each analog day, which is what the planned system already does.

### Gaps
- Full Delle Monache 2013 text (number of analogs used, training length, exact rank-histogram/CRPS values) not retrieved. The record says verification covered statistical consistency, reliability and skill, but exact numbers weren't confirmed.
- Davò et al. 2016 (solar AnEn) and Alessandrini et al. 2015 (wind/solar AnEn) are well-known energy follow-ups, but their details weren't retrieved.

## 3. Academic evidence for k-NN / nearest-neighbor / pattern-matching forecasting in stock and futures markets

### Takeaway
The evidence is mixed and mostly weak for return direction. Some NN trading rules beat buy-and-hold after costs in specific years (mostly 1990s–2000s working papers). Point-forecast accuracy is often no better than a random walk, though directional accuracy sometimes is. Nearest-neighbor methods look more useful for volatility/variance, which is the closest analog to forecasting daily range or HOD/LOD distance, than for direction. Statistical accuracy does not map one-to-one onto profit. I found no peer-reviewed study of k-NN analog days for intraday HOD/LOD timing in ES.

### Cited Findings
- Fernández-Rodríguez, Sosvilla-Rivero, Andrada-Félix (NYSE, FEDEA WP 2001): after transaction costs, an NN trading rule beat risk-adjusted buy-and-hold on returns and Sharpe in the 1998 and 1999 uptrend years. In flat 2000, returns were equal but buy-and-hold had a higher Sharpe — [FEDEA working paper](https://documentos.fedea.net/documento/dt-2001-16/texto). A later version covering 1997–2002 reports the NN rule beat buy-and-hold and ARIMA on returns in all years, but in 2001 ARIMA had the higher Sharpe in 36/101 cases vs 18 for NN (36 ties) — [ULPGC repository PDF](https://accedacris.ulpgc.es/bitstream/10553/1587/1/675.pdf) (working-paper versions with differing samples; final publication details unverified)
- Mechanism in that line of work: NN selects past geometric segments similar to the latest segment, chosen by level and trajectory rather than position in time — [FEDEA WP](https://documentos.fedea.net/documento/dt-2001-16/texto)
- Nikkei 225, 1986–1997: NN predictors did worse than a random walk on Theil's U (point accuracy) but beat it on directional forecasting — [IDEAS/RePEc, Fernández-Rodríguez et al.](https://ideas.repec.org/p/can/series/2004-05.html)
- FX: allowing for interest rates and transaction costs, an NN-based rule outperformed a moving-average rule — [ULPGC: Economic value of NN exchange-rate forecasts](https://dmc.ulpgc.es/other-publications/278-assesing-the-economic-value-of-nearest-neighbour-exchange-rate-forecasts.html)
- Realized variance (S&P 100): Andrada-Félix, Fernández-Rodríguez & Fuertes (IJF 2016) found NN forecasts of daily realized variance work well. "Statistical accuracy does not have a one-to-one mapping into profitability": in turbulent markets NN gave higher risk-adjusted straddle profits even though model-based (long-memory) forecasts were statistically superior, and a directional combination of NN and model forecasts was most profitable in both calm and turbulent markets — [City Research Online](https://openaccess.city.ac.uk/id/eprint/12654/)
- Month-ahead direction of 8 major indices, Jan 2005–Oct 2021 (202 test months, rolling 192-month training, walk-forward k): plain k-NN with IDTW reached 0.574 accuracy on the S&P 500 (random 0.492), 0.594 on S&P/TSX, and only 0.500–0.530 on FTSE, DAX, CAC, TOPIX and EURO STOXX. The proposed bias-corrected LRLR reached 0.649 on the S&P 500 but underperformed baselines on EURO STOXX and TOPIX. No transaction costs; the "virtual trading" is a monthly long/short switch — [arXiv 2112.13951](https://arxiv.org/pdf/2112.13951)
- Tsinaslanidis & Kugiumtzis (2014, Expert Systems with Applications): perceptually important points (PIPs) plus DTW-based analog prediction on 18 world equity indices and GBP/USD. Results supported the efficient market hypothesis for equity indices (no exploitable predictability). For the exchange rate it sometimes beat a last-price forecast, and it recovered structure in simulated chaotic series — [Canterbury repository](https://repository.canterbury.ac.uk/item/871vz/a-prediction-scheme-using-perceptually-important-points-and-dynamic-time-warping)

### Inferences
- In the arXiv 2112.13951 table, the comparison point is a 50/50 random predictor. US indices rise in most months, so a naive "always up" rule would likely score near or above k-NN's 0.574 on the S&P 500. I didn't verify the S&P 500 up-month base rate for that sample. Lesson: always compare analog outputs to the unconditional base rate, not to a coin flip.
- The volatility result (Andrada-Félix et al.) is the most relevant to this system: "how far from the reference will the HOD/LOD be" is a range/volatility question, where NN has better support than for direction. Timing (hour of HOD/LOD) is closer to a periodic intraday-seasonality question, where the unconditional distribution is a strong baseline (see section 5).
- Published positive results are concentrated in old samples and working papers. Publication bias is likely.

### Gaps
- No peer-reviewed study found on k-NN/analog days for intraday futures HOD/LOD level or timing. No out-of-sample evidence specific to ES.
- Full text of Nakagawa et al. 2018 (k*-NN with IDTW) not retrieved, so its accuracy numbers are unconfirmed. Only its abstract/description and the 2021–22 follow-up were seen.

## 4. DTW: how it works, finance papers, pitfalls

### Takeaway
DTW aligns two sequences with a non-linear time warp (dynamic programming over a cost matrix) so that similar shapes match even when shifted or stretched in time. In finance it is used to find historical price paths that "rhyme" with the current one (Nakagawa IDTW k*-NN; Tsinaslanidis PIP+DTW and subsequence/derivative DTW). Keogh's group showed that only a little warping helps: accuracy usually peaks at windows of a few percent of series length, and wide or unconstrained warping produces spurious matches. The finance evidence that DTW-matched shapes predict continuation is weak, and Tsinaslanidis found equity indices consistent with efficiency.

### Cited Findings
- DTW mechanics and constraint: the Sakoe-Chiba band ("warping window") limits how far the path can stray from the diagonal. A 0% window equals Euclidean distance; 100% is unconstrained DTW — [Ratanamahatana & Keogh, "Everything you know about DTW is wrong"](https://www.cs.ucr.edu/~eamonn/DTW_myths.pdf)
- Same paper, from experiments with more than eight billion DTW comparisons:
  - Reinterpolating different-length series to equal length produced no statistically significant accuracy difference.
  - The conventional 10% band is "actually too large for real world data mining". Best 1-NN accuracies came at very small windows (e.g., Face 96.43% at 3%, Gun 99.00% at 3%). "A little warping is a good thing, but too much warping is a bad thing."
  - The optimal window depends on database size, so tune it on realistic data sizes.
  - With lower bounding (LB_Keogh), DTW's amortized cost is essentially O(n).
  — [DTW_myths.pdf](https://www.cs.ucr.edu/~eamonn/DTW_myths.pdf)
- Nakagawa, Imamura & Yoshida (2018, New Frontiers in AI, Springer): stock price prediction from fluctuation patterns using indexing DTW (IDTW) and k*-NN on major indices. Each series is rescaled so its first element is 1 (removing level differences), then DTW is applied — [Springer Professional record](https://www.springerprofessional.de/en/stock-price-prediction-with-fluctuation-patterns-using-indexing-/15895926); IDTW definition per [arXiv 2112.13951](https://arxiv.org/pdf/2112.13951)
- Tsinaslanidis (2018, Expert Systems with Applications): DTW, subsequence DTW and derivative DTW used for bullish/bearish class predictions on NYSE stocks — [Canterbury repository](https://repository.canterbury.ac.uk/item/8867q/subsequence-dynamic-time-warping-for-charting-bullish-and-bearish-class-predictions-for-nyse-stocks); review chapter "DTW as a similarity measure: applications in finance" — [Canterbury repository](https://repository.canterbury.ac.uk/item/875vv/dynamic-time-warping-as-a-similarity-measure-applications-in-finance)
- PIP+DTW analog prediction found no predictability in 18 equity indices (consistent with EMH) — [Canterbury repository](https://repository.canterbury.ac.uk/item/871vz/a-prediction-scheme-using-perceptually-important-points-and-dynamic-time-warping)

### Inferences
- For a "similar day" system built on daily summary features (range, gap, overnight range), DTW is unnecessary: those features are already time-aligned scalars. DTW only matters if you match intraday paths, e.g., the shape of the overnight session or the first 60–90 minutes of RTH.
- If intraday paths are matched, use z-normalized (or open-indexed, IDTW-style) series with a tight Sakoe-Chiba band (~1–5% of length) and tune the band walk-forward. A large band lets a 09:45 reversal match an 11:30 one, which destroys exactly the timing information you want to forecast.
- Timing is the forecast target, so warping time in the matching step is conceptually in tension with forecasting when HOD/LOD occurs. A small band or plain Euclidean on aligned bars is the safer default.
- Pitfalls: multiple tuning parameters (window, normalization, length, k, distance-to-weight mapping) raise data-snooping risk; shapes that rhyme are not evidence of continuation (Tsinaslanidis' EMH result).

### Gaps
- No finance paper found that tests DTW window size specifically on intraday futures. No out-of-sample after-cost DTW results for ES found.

## 5. Practitioner implementations (TradingView, LuxAlgo, forums, commercial tools)

### Takeaway
Retail implementations are mostly bar-level kNN direction classifiers (Lorentzian Classification and clones), not daily "similar day" HOD/LOD tools. Their backtests are self-reported and some have had repainting bugs. The closest commercial product to the planned output is time-of-day HOD/LOD distribution reporting (e.g., Edgeful), which conditions on weekday rather than analog similarity. I found no public, documented ES "similar days → HOD/LOD time/level" tool with verified performance.

### Cited Findings
- "Machine Learning: Lorentzian Classification" (jdehorty, TradingView):
  - Method: approximate-nearest-neighbor kNN using Lorentzian distance; up to 5 features from RSI, WaveTrend, CCI and ADX; defaults tuned for 4H–12H charts.
  - Defaults: 8 neighbors, max bars back 2000; volatility and regime filters on; Nadaraya-Watson kernel smoothing.
  - Author caveats: backtest results improve as more history is added, so judge results with that in mind; the Trade Stats table "is not a substitute for proper backtesting"; standalone strategy use is not recommended.
  — [TradingView script page](https://www.tradingview.com/script/WhBzgfDu-Machine-Learning-Lorentzian-Classification/)
- The same indicator predicts direction over the next 4 bars — [Pineify guide](https://pineify.app/pine-script/indicators/lorentzian-classification). One blog's ~57% filtered win rate on SPY 4H is anecdotal, vendor-adjacent and unverified — [Pineify blog](https://pineify.app/resources/blog/lorentzian-classification-indicator-tradingview-pine-script)
- A community "Lorentzian KNN Classifier" clone said in its v2.0 notes that an earlier version had a repainting issue that inflated backtest results — [TradingView (cn mirror)](https://cn.tradingview.com/script/6zaUr2Cy-Machine-Learning-Lorentzian-KNN-Classifier-Update)
- "k-NN Lorentzian Supervised Learning" (The Quant Science) uses a 4-D feature space: log return, CLV, range width, volume change — [TradingView](https://de.tradingview.com/script/d6fBXXZa-k-NN-Lorentzian-Supervised-Learning-The-Quant-Science/)
- LuxAlgo publishes an educational "kNN Analog Forecasting" concept page (mechanics and pitfalls, no performance claims) — [LuxAlgo](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md). I didn't confirm a LuxAlgo-branded daily similar-day tool.
- Edgeful's "Intraday timing" report bins each day's high and low into 15-minute intervals to show when they tend to occur. ES NY-session examples: Monday highs most likely 9:30am–1pm ET; Friday lows most likely 9:30–11am ET. It conditions on weekday, not analog similarity — [Edgeful docs](https://docs.edgeful.com/trade-using-edgeful/price-action-reports/intraday-timing) (vendor, self-reported)

### Inferences
- The unconditional (or weekday-conditional) time-of-day histogram of HOD/LOD is the baseline the analog system must beat. If 10 analogs only reproduce "HOD/LOD cluster near the open and close", the analog step adds nothing.
- Retail kNN backtests should be treated as marketing until reproduced with bar-close, non-repainting logic and costs.

### Gaps
- NexusFi/futures.io: no thread with documented, tested "similar days" HOD/LOD methodology for ES turned up within the search budget.
- No commercial "analog day" tool with independently verified ES performance found.

## 6. Pitfalls and concrete lessons for the ES 10-analog HOD/LOD system

### Takeaway
The biggest risks are look-ahead in the bias label, tiny samples (k≈10 drawn from ~500 days), non-independent neighbors, regime change inside a 2-year window, data snooping over features, weights, k and windows, and session/timezone definitions that shift HOD/LOD times. All are manageable with strict as-of feature construction, walk-forward evaluation against a climatology baseline, and probabilistic verification borrowed from meteorology.

### Cited Findings
- Look-ahead leakage and overfitting k are named core kNN pitfalls. The recommended guard is at least an in-sample/out-of-sample split or walk-forward test — [LuxAlgo](https://www.luxalgo.com/library/concept/knn-analog-forecasting.md)
- Walk-forward hyperparameter selection with an embargo between tuning and training data (tuning months t−24..t−1, training t−192..t−25) — [arXiv 2112.13951](https://arxiv.org/pdf/2112.13951)
- Archive-size/dimensionality: good analogs need large archives as dimension grows — [arXiv 2101.10640 on van den Dool 1994](https://arxiv.org/pdf/2101.10640)
- Equal-weight, many-variable analogs are over-dispersed, and regime changes are the hardest cases for analogs — [arXiv 2103.04530](https://arxiv.org/pdf/2103.04530)
- Repainting (using information not yet available at bar close) has inflated retail kNN backtests — [TradingView Lorentzian KNN v2.0 notes](https://cn.tradingview.com/script/6zaUr2Cy-Machine-Learning-Lorentzian-KNN-Classifier-Update)
- ES daily bars that include the overnight session differ from RTH-only bars in extremes and timestamps (session 17:00 CT → 15:15 CT next day; 15:30 CT start in the cited description) — [eSignal forum](https://forum.esignal.com/forum/product-data-category/data-inquiries/24328-es-eod-vs-5-min)
- Statistical accuracy does not guarantee economic value — [Andrada-Félix et al. 2016](https://openaccess.city.ac.uk/id/eprint/12654/)

### Inferences (design lessons)

**1. Bias label leakage.** If "bullish/bearish" means the day closed up or down, it is known only after the fact. Using it to split the analogs is look-ahead for the current day. Options:
- define bias from information known at decision time (pre-open features, or the first N minutes, timestamped);
- show both conditional branches (if bullish / if bearish) with the base rate of each among the analogs, and never imply the current day's branch is known;
- in the backtest, score only the branch selectable at decision time.

**2. As-of discipline.**
- Features come from data at or before the prior session close (plus overnight data only up to a fixed cutoff, e.g., 09:29 ET, if overnight features are used).
- Candidate analogs must be fully completed days strictly before today.
- Normalization statistics (σ, ATR percentiles) must be computed from data before today, not over the whole 2-year window including today.

**3. Small k.** With 10 analogs, a 30%/70% split has a 95% interval of roughly ±28 percentage points (binomial). The hour-of-HOD histogram with 10 draws over about 7–23 hourly bins is mostly noise. Mitigations:
- report kernel-smoothed or coarser bins (open hour / mid-day / close hour);
- report medians and IQRs rather than single analogs;
- show the climatology histogram next to it;
- consider larger k with distance weights (meteorology often uses ~10–20 members; the arXiv 2103.04530 study used 11).

**4. Non-independence.** Consecutive days in a volatility cluster look alike. Several analogs from the same week or month act like one observation. Enforce a minimum spacing (e.g., at most 1 analog per 3–5 trading days, or a de-cluster rule), analogous to skipping overlapping windows.

**5. Regime.** A 2-year window can span different volatility and rate regimes. Include an ATR or VIX regime feature with high weight, or require the analogs' regime bucket to match. Monitor CRPS skill over time, because analog skill decays at regime shifts.

**6. Data snooping.** Features × weights × k × distance × window × bias definition make a large search space. Fix a small pre-registered configuration, tune weights by walk-forward CRPS (Junk et al. style), keep a final untouched holdout period, and report the number of configurations tried.

**7. Verification metrics.**
- Daily PIT/rank histogram of the realized HOD distance, LOD distance and HOD/LOD hour against the 10 analog values.
- CRPS skill vs (a) 10 random days and (b) all days from the same window.
- Hit rate of "HOD/LOD within the analog IQR" vs its nominal 50%.
- For timing, a circular or binned Brier score vs the unconditional time-of-day distribution.

**8. Sessions and timezone.**
- Fix one session definition (ETH 18:00–17:00 ET or RTH 09:30–16:00 ET) and one timezone (ET, with DST handled).
- Treat early-close days and holidays separately, and decide how to handle contract rolls (back-adjusted vs actual), because distance "from a reference" depends on it.
- Report times in exchange or ET time consistently. CT/ET or DST mismatches shift "hour of HOD" by one bucket.

**9. Reference point.** Choose a reference available at decision time (prior close, RTH open, or overnight high/low midpoint), express distances in ATR units so analogs from different volatility regimes are comparable, then convert back to points for display.

### Gaps
- No empirical study found on the optimal k, de-clustering rule, or feature weights specifically for ES daily analogs. These must be estimated in-house by walk-forward.
- No published ES-specific evidence that analog-conditioned HOD/LOD timing beats the unconditional time-of-day distribution.
