# Volatility and Daily-Range Forecasting Models, and Options-Implied Expected Moves, as Predictors of ES HOD/LOD Distance

Research notes as of October 2026. All claims carry inline sources. Items without a source are under "Inferences" (my own reasoning or standard math) or "Gaps".

---

## 1. ATR and range-based volatility estimators (Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang): what they are and how much efficiency they add

### Takeaway
Range-based estimators use the high and low, and sometimes the open and close, so they extract several times more information per day than close-to-close returns. Commonly cited efficiencies relative to close-to-close are about 5.2x for Parkinson, about 7.4x for Garman-Klass, and up to about 14x for Yang-Zhang. The 14x figure is from a secondary source. Each estimator removes one more idealized assumption: zero drift, then no overnight gap, then both. ATR is the practitioner analogue. It is a smoothed "true range" in raw points, which makes it a direct, though crude, forecast of the points distance a system wants to predict.

### Cited Findings
- **ATR definition.** True range is the largest of: high minus low, |high minus previous close|, and |low minus previous close|. ATR is a moving average of true range, conventionally over 14 days. — [TradingView ATR Daily Levels script](https://de.tradingview.com/script/q6nrbx80-ATR-Daily-Levels); [TradingView open-source script](https://cn.tradingview.com/script/40ANMz67)
- **Parkinson (1980).** Uses only high and low. Assumes zero drift and continuous trading with no overnight gaps. Efficiency is about 5.2x close-to-close, meaning its sampling variance is about one-fifth for the same number of days. — [bookdown Financial Econometrics, OHLC measures](https://bookdown.org/jarneric/financial_econometrics/5.1-ohlc-measures.html); [Ryan O'Connell Finance](https://ryanoconnellfinance.com/?p=13589)
- **Garman-Klass.** Adds open and close. Efficiency is about 7.4x. It assumes Brownian motion with zero drift and no jumps, and it effectively treats the open as equal to the prior close. — [bookdown OHLC measures](https://bookdown.org/jarneric/financial_econometrics/5.1-ohlc-measures.html); [Ryan O'Connell Finance](https://ryanoconnellfinance.com/?p=13589)
- **Rogers-Satchell.** Drops the zero-drift assumption, so it stays unbiased when prices trend intraday. — [Ryan O'Connell Finance](https://ryanoconnellfinance.com/?p=13589); [LuxAlgo Yang-Zhang concept](https://www.luxalgo.com/library/concept/yang-zhang-estimator/)
- **Yang-Zhang (2000).** Combines three parts: overnight (close-to-open) variance, plus k times open-to-close variance, plus (1−k) times Rogers-Satchell variance. Here k = 0.34 / (1.34 + (n+1)/(n−1)). It is robust to both drift and opening jumps, and is described as minimum-variance unbiased for OHLC. Its efficiency is cited as about 14x by a secondary, non-derived source. It is sensitive to window length, short windows push k higher so the estimate leans on the noisy overnight return, and it needs clean OHLC data. — [LuxAlgo](https://www.luxalgo.com/library/concept/yang-zhang-estimator/); [MetricGate docs](https://metricgate.com/docs/yang-zhang-volatility-estimator/); [FlashAlpha Yang-Zhang vs close-to-close](https://flashalpha.com/articles/yang-zhang-vs-close-to-close-realized-volatility)
- **Realized range (intraday).** Christensen and Podolskij's realized range-based variance replaces each squared intraday return with a normalized squared intraday range. Under ideal conditions it is about 5x more precise than realized variance. Ranges from discretely sampled data are biased downward, because the true extreme is unobserved, so a bias correction is needed. — [arXiv 2601.20463](https://arxiv.org/pdf/2601.20463); [IDEAS, J. Econometrics 141(2), 2007](https://ideas.repec.org:443/a/eee/econom/v141y2007i2p323-349.html). Related: Martens and van Dijk, "Measuring volatility with the realized range," J. Econometrics 138(1), 2007 — [search listing via IDEAS](https://ideas.repec.org:443/a/eee/econom/v141y2007i2p323-349.html)
- **Range as a theoretical volatility measure.** Extreme-value theory implies the range is an efficient estimator of local volatility (Parkinson 1980). This motivates CARR. — [Chou 2005, JMCB, IDEAS](https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html)

### Inferences
- For a HOD/LOD-in-points target, Parkinson-type range or ATR is not just an input. It is the target's own unit. Under driftless Brownian motion, E[High−Low] = 2·√(2/π)·σ√T ≈ 1.596·σ√T and E[High−Open] = √(2/π)·σ√T ≈ 0.798·σ√T, a standard reflection-principle result. A σ forecast from any model can therefore be mapped into an expected points distance to the HOD and LOD, but the constants will be biased in practice by fat tails, drift, and discrete sampling.
- ES trades nearly 23 hours. The "overnight gap" that motivates Garman-Klass and Yang-Zhang depends on how the session is defined. With the full Globex session there is almost no gap. With RTH-only bars (09:30–16:00 ET) the overnight move is large. The system must choose its session definition and reference price (open, prior close, Globex open, or the 09:30 price) consistently, because ATR (which includes gaps) and Parkinson (which excludes them) measure different things.
- ATR is a simple moving average of a noisy proxy. It reacts slowly after a volatility shock and decays slowly afterward. That weakness is exactly what HAR and CARR address.

### Gaps
- I could not access the original Yang and Zhang (2000, Journal of Business) paper to verify the "~14x" efficiency figure. Treat it as indicative.
- I found no ES-specific study comparing the out-of-sample accuracy of these estimators as forecasts of next-day points range.

---

## 2. HAR-RV, CARR, and GARCH: which forecasts the daily range best?

### Takeaway
HAR-RV, estimated with OLS on daily, weekly, and monthly averages, is the standard benchmark for realized-volatility forecasting and generally beats GARCH. CARR, a GARCH-like recursion fitted directly on the high-low range, beat GARCH on S&P 500 data in Chou's original paper, but independent replications are mixed: GARCH wins in some low-volatility samples and under asymmetric loss. The practical consensus is that models fed with range or intraday information beat models fed only with closes, and that the evaluation loss function and sample regime change the rankings.

### Cited Findings
- **HAR-RV (Corsi 2009, J. Financial Econometrics 7(2):174).** Volatility is modeled as a cascade of components from heterogeneous traders on daily, weekly, and monthly horizons. The result is an AR-type regression of RV on its lagged daily value, its 5-day average, and its 22-day average. It has no true long memory, yet it reproduces long memory, fat tails, and self-similarity, and it shows "remarkably good forecasting performance." It is estimated by simple OLS. — [Oxford Academic JFEC](https://academic.oup.com/jfec/article/7/2/174/856522); [SSRN abstract](https://papers.ssrn.com/abstract=1365738)
- HAR is still the benchmark that new realized-variance forecasting methods are measured against. A 2025 paper is titled "Predicting Realized Variance Out of Sample: Can Anything Beat The Benchmark?" — [arXiv 2506.07928](https://arxiv.org/pdf/2506.07928)
- Integrated HAR (IHAR), which constrains the coefficients to sum to one, reports considerable out-of-sample gains over HAR for four assets. — [Ewha / Cho and Shin](https://pure.ewha.ac.kr/en/publications/an-integrated-heteroscedastic-autoregressive-model-for-forecastin/)
- **CARR (Chou 2005, J. Money, Credit and Banking 37(3):561–582).** The conditional expected range follows a GARCH-like recursion on past ranges, structurally like Engle and Russell's ACD model. Out-of-sample S&P 500 tests show CARR gives "sharper volatility estimates compared with a standard GARCH model." — [IDEAS](https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html); [NYCU repository](https://ir.lib.nycu.edu.tw:443/handle/11536/14403)
- **Asymmetric CARR (Chou 2006).** Separate dynamics for upward ranges (high−open) and downward ranges (open−low) produce sharper forecasts than symmetric CARR. This is directly relevant to modeling HOD and LOD distances separately. — [IDEAS, Advances in Econometrics vol. 20](https://ideas.repec.org/h/eme/aecozz/s0731-9053(05)20009-9.html)
- **CARR vs GARCH on FTSE 100 and Nikkei 225 (Chou and Wang 2006).** CARR forecasts better because it captures intraday price variation. — [JCIS 2006, DOI](https://dx.doi.org/10.2991/jcis.2006.175)
- **Replications on the S&P 500 are mixed.**
  - Miralles-Marcelo and Miralles-Quirós find GARCH outperforms CARR in two samples, especially in lower-volatility periods and under asymmetric error statistics. Replacing the raw range with the Rogers-Satchell range gives sharper estimates in low-volatility periods. — [Dialnet PDF](https://dialnet.unirioja.es/descarga/articulo/2723714.pdf)
  - Miralles-Quirós and Daza-Izquierdo (Applied Financial Economics 2013) find two range-based models beat GARCH. Parkinson-based models do better in up-trends and in high or low volatility, and CARR does better in down-trends and in mean-volatility conditions. — [IDEAS](https://ideas.repec.org/a/taf/apfiec/v23y2013i21p1635-1647.html); [IPL repository](https://repositorio.ipl.pt/entities/publication/7e1d027b-b30d-4a9b-88b5-4f3a617b8e19)
  - A composite CARR (CCARR) separates long-term and short-term range components, illustrated on the S&P 500 and FTSE 100. — [arXiv 1702.02268](https://arxiv.org/pdf/1702.02268)
- A 2014 study compares realized semivariance, squared returns, daily high-low range, realized variance, and realized range as GARCH-type inputs under several loss functions. It is relevant as a template for comparing proxies. — [ICMAIF 2014 paper](https://icmaif.soc.uoc.gr/~icmaif/Year/2014/papers/paper_3_65.pdf)
- **HAR vs implied volatility for one day ahead.** Albers (2025) finds a VIX1D adjusted for its risk premium gives more precise one-day S&P 500 volatility forecasts than HAR or HAR-VIX1D. — [IDEAS, J. Futures Markets 45(11), 2025](https://ideas.repec.org/a/wly/jfutmk/v45y2025i11p2092-2108.html)

### Inferences
- A practical stack for ES is HAR on a range-based daily measure, for example log Parkinson or a 5-minute realized range, with the 1, 5, and 22-day lags. CARR is close in spirit, since both are linear autoregressions on a range proxy. HAR is easier to fit and extend with exogenous regressors such as VIX1D, event dummies, overnight range, or the opening-gap size.
- Model in logs. Ranges are positive and right-skewed, so log-HAR keeps forecasts positive and makes errors closer to homoskedastic. Convert back to points with a bias correction.
- The evidence that rankings depend on regime and loss function means the ES system should evaluate under the loss that matches its use, for example quantile or pinball loss if it outputs bands, and report results by volatility regime.

### Gaps
- I found no paper with a head-to-head comparison of HAR-on-range, CARR, and GARCH for daily range forecasting of S&P 500 or ES futures with standard loss metrics such as MSE or QLIKE. The CARR literature is mostly 2005–2013 and partly paywalled.
- I did not find quantitative effect sizes (MSE ratios) for Chou (2005); only the qualitative "sharper" conclusion is available from the abstract.

---

## 3. Options-implied measures (VIX, VIX1D, ATM and 0DTE straddle expected move) as forecasts of the intraday range; the variance risk premium

### Takeaway
Implied volatility usually overstates subsequently realized volatility. The VIX exceeded subsequent 30-day realized volatility 83.7% of the time, with an average premium of about 3.8 vol points. VIX1D also systematically overestimates next-day volatility, but once that premium is removed it beats HAR for one-day-ahead forecasts. 0DTE straddles priced at 10:00 ET contained SPY's close 71% of the time against a 68.3% fair benchmark. No study I found measures how often the intraday high or low breaches the straddle-implied move, which is the quantity that matters for HOD/LOD. Event days (CPI, FOMC) cause VIX1D to spike the day before and collapse on announcement day.

### Cited Findings
- **VIX1D construction.** Launched April 2023 by Cboe Labs. It uses PM-settled SPXW options expiring in 0 to 1 days, priced at bid/ask midpoints, with the VIX methodology adapted to the compressed one-day horizon. — [Hedgeweek](https://www.hedgeweek.com/cboe-launches-1-day-volatility-index/); [FinanceFeeds](https://financefeeds.com/vix1d-index-cboe-launches-1-day-volatility-index-to-measure-single-trading-day-volatility/)
- A third-party description says VIX1D reflects 0DTE options at the start of the day and then time-weights in the next-day expiry as the day goes on. — [Option Alpha](https://optionalpha.com/learn/vix1d-explained-0dte-intraday-volatility). I could not confirm this from Cboe.
- **VIX1D statistics (Cboe, May 2022 – May 2023).**
  - Closing range: 9.96 to 47.14, versus 15.78 to 34.02 for the VIX.
  - Average 20-day volatility of the index itself: 372 for VIX1D versus 84 for the VIX.
  - Return correlation with the S&P 500: −0.20 for VIX1D, while three longer-dated indices were below −0.70.
  - Over 20 CPI and FOMC announcements, VIX1D rose 61.4% on average the day before (VIX +1.9%) and fell about 24.8% on announcement day.
  - Banking stress, March 8–13, 2023: VIX1D +162.7% versus VIX +38.8%.
  - — [Cboe Insights, VIX1D in 11 charts](https://www.cboe.com/insights/posts/how-the-vix-1-d-index-performance-compares-to-the-vix-index-and-other-volatility-indices-in-11-charts)
- **Albers (2025), J. Futures Markets 45(11):2092–2108.** VIX1D is generally lower and more volatile than longer VIX-family indices. It has a distinct intraday pattern with a daily upward trend. It overestimates S&P 500 volatility. A simple adjustment for the risk premium yields one-day forecasts more precise than HAR and HAR-VIX1D. — [IDEAS](https://ideas.repec.org/a/wly/jfutmk/v45y2025i11p2092-2108.html); [TU Dresden](https://fis.tu-dresden.de/portal/en/publications/a-new-star-is-born-does-the-vix1d-render-common-volatility-forecasting-models-for-the-us-equity-market-obsolete(cdf81654-bf7d-41b6-a165-af0168c8b016).html)
- **Variance risk premium (OptionMetrics; SPX 1996 onward, 7,655 days).**
  - The VIX minus realized volatility over the next 21 days was positive 83.7% of the time. The average premium was 3.82 vol points, about 19% of an average VIX of 20.15. The article also cites a mean of 4.52 without reconciling it.
  - The premium turns sharply negative in crises: about −22 in September 1998 (LTCM) and about −68.6 in the pandemic shock. The article prints this date as "02/2000", likely a typo for 2020.
  - Negative episodes typically last about 4 trading days, with the longest in 2008. The distribution is fat-left-tailed and negatively skewed.
  - — [OptionMetrics blog](https://optionmetrics.com/blog/how-accurate-is-implied-volatility/)
- **0DTE straddle as forecast (FlashAlpha; SPY; 193 Wednesdays, July 2022 – April 2026).**
  - Method: 10:00 ET ATM straddle mapped to a 1σ move, compared with the 16:00 close.
  - The close was inside the band 71.0% of the time, versus 68.3% if fairly priced. It exceeded 1σ 25.9% of the time, versus about 31.7% under fair pricing.
  - Median realized/implied was 0.589, versus 0.674 for a fair normal, so realized ran about 13% below fair. The median implied move was 0.72% of spot and the median realized |move| was 0.37%.
  - Hit rates by year: 69.2% in 2022 H2 and in 2023, 70.0% in 2024, 71.2% in 2025, and 84.6% in 2026 Q1 (13 sessions).
  - Worst day, April 9, 2025: implied 3.51%, realized +8.72%, about 2.5x.
  - FOMC-day straddles priced at roughly double neighboring weeks and were "largely respected."
  - The study explicitly does not measure intraday high/low touches. It is a vendor blog.
  - — [FlashAlpha 0DTE study](https://flashalpha.com/articles/are-0dte-straddles-overpriced-193-spy-sessions-data-study)
- **Straddle-to-σ conversion conflicts across sources.** Some sources use expected move ≈ 0.85 × ATM straddle. Others use 1σ ≈ 1.25 × straddle, from the Black-Scholes relation ATM straddle ≈ √(2/π)·σ·S·√T ≈ 0.8·σ·S·√T. — [FlashAlpha Expected Move concept](https://flashalpha.com/concepts/expected-move); [ApexVol glossary](https://apexvol.com/glossary/expected-move); [Options Analysis Suite docs](https://www.optionsanalysissuite.com/documentation/expected-move)
- The "68% inside the expected move" figure is a lognormal theoretical benchmark. Real returns have fatter tails. — [ApexVol glossary](https://apexvol.com/glossary/expected-move); [tastylive expected move article](https://www.tastylive.com/news-insights/expected-move-sanity-checking-trade-ideas)
- tastylive (Rechenthin) studied how often S&P 500 components stayed within their expected move against the 68% benchmark. The hit rates were not retrievable. — [tastylive episode page](https://www.tastylive.com/shows/the-skinny-on-options-data-science/episodes/how-often-within-expected-01-12-2017)
- **Practitioner skepticism.** An IBKR commentary questioned whether VIX1D's FOMC-eve reading "tells a useful story" and preferred the ATM SPX daily straddle as the expected move. — [IBKR Traders' Insight, "A use case for 1-day VIX"](https://www.interactivebrokers.com/campus/traders-insight/securities/macro/a-use-case-for-1-day-vix/)
- Robot Wealth proposed, but did not validate, comparing SPX straddle-implied moves with realized open-to-close moves. — [IBKR Quant / Robot Wealth](https://www.interactivebrokers.com/campus/ibkr-quant-news/trading-0dte-options-with-the-ibkr-native-api/)

### Inferences
- **Converting VIX1D to ES points.** The one-day 1σ move is about ES × (VIX1D/100)/√252. This is standard annualization, not from a cited source. Because the straddle prices the terminal move, not the path extremes, the expected distance from the reference to the HOD (or LOD) under driftless Brownian motion is about 0.8 × 1σ, and the expected full range is about 1.6 × 1σ. A straddle-implied "expected move" that contains the close about 70% of the time will be touched intraday by the high or the low much more often. Under Brownian motion, P(max excursion ≥ k·σ) = 2·P(Z ≥ k), so a ±1σ level is touched on one side about 32% of the time and on either side roughly 55–60% of the time. Do not treat the expected move as a HOD/LOD boundary.
- The two effects pull in opposite directions. The variance risk premium (implied runs 13–19% rich) shrinks realized moves, while path extremes (√(2/π) and reflection) expand them relative to the close-to-close move. Each needs its own empirical calibration on ES data. The natural approach is to regress realized (High−Ref) and (Ref−Low) in points on the implied 1σ in points and estimate the multipliers by regime.
- Implied measures are most valuable exactly where history-based models fail: on scheduled event days, when the market prices the event in advance and HAR cannot. A combined model, HAR on range plus an adjusted VIX1D or 0DTE straddle term, is the logical design. Albers' result suggests the implied term may dominate one-day forecasts.
- Timing matters. VIX1D has an intraday upward drift as the 0DTE expiry's time-to-expiry shrinks and the next-day expiry gets weighted in. Snapshot it at a fixed time, for example at the reference-price time, and use one convention consistently.

### Gaps
- I found no peer-reviewed or vendor study measuring how often the SPX or ES intraday high or low breaches the 0DTE straddle-implied move or the VIX1D-implied move. The FlashAlpha study is close-only, SPY, Wednesdays, and n=193. This must be backtested in-house.
- I could not access the Cboe VIX1D methodology document directly to verify the intraday time-weighting.
- SpotGamma's research on implied versus realized moves was not reached within the search budget.

---

## 4. Modeling the distances to the high and the low directly and separately (high/low forecasting, VECM, cointegration)

### Takeaway
Daily highs and lows are cointegrated, and the range is the stationary error-correction term. VECM and fractional-VECM models that forecast the high and the low jointly give some out-of-sample advantage for highs and lows, and the predictability is economically meaningful in trading tests. For range forecasting itself, VECM is not uniformly better than univariate range models. Asymmetric CARR, which models the up-range and down-range separately, beats symmetric CARR.

### Cited Findings
- **Cheung, Cheung and Wan (2009), J. Forecasting 28(2):103–119; CESifo WP 2387 (2008).** Data: log daily highs and lows of Nikkei 225, KOSPI, DJIA, Nasdaq Composite, and TWSE. Johansen tests reject no cointegration and find one cointegrating vector. The vector is close to (1, −1), so the range is the error-correction term. Highs and lows "move in tandem" and the gap is stable. Range dispersion is much smaller than the day-to-day changes in highs or lows. In-sample, high-low interactions matter for modeling the range. Out-of-sample, under MSFE and direction-of-change criteria, VECM high and low forecasts "offer some advantages," but VECM range forecasts are not uniformly superior, and rankings depend on criterion and variable. An extension forecasting implied volatility also shows value in modeling highs, lows, and ranges jointly. — [CESifo WP 2387 (PDF via ifo.de)](https://www.ifo.de/DocDL/cesifo1_wp2387.pdf); [CESifo listing](https://cesifo.org/en/publications/2008/working-paper/high-low-model-daily-stock-price-ranges); [HKBU scholars](https://scholars.hkbu.edu.hk/en/publications/a-high-low-model-of-daily-stock-price-ranges/)
- Cheung et al. motivate the topic as follows: the high and low cannot be recovered from the range alone, and they matter for barrier options, candlesticks, and stochastic oscillators. — [CESifo WP 2387](https://www.ifo.de/DocDL/cesifo1_wp2387.pdf)
- **Caporin, Ranaldo and Santucci de Magistris (2013), J. Banking & Finance 37(12):5132–5146.** A fractional VECM captures the high-low cointegration and the long memory of the range. US equity daily highs and lows are "largely predictable." Using the forecasts as entry and exit signals yields superior risk-adjusted trading performance. — [IDEAS](https://ideas.repec.org/a/eee/jbfina/v37y2013i12p5132-5146.html); [SNB WP 2011-11](https://www.snb.ch/it/publications/research/working-papers/2011/working_paper_2011_11); [Padova WP 136 PDF](https://economia.unipd.it/en/sites/decon.unipd.it/files/20110136.pdf)
- A thesis replicating the approach on a single Spanish stock (Bankinter) is available. — [CUNEF TFG PDF](https://biblioteca.cunef.edu/files/documentos/TFG_Marcos_Rocabert_Barroso.pdf)
- **Asymmetric CARR (Chou 2006).** Separate dynamics for upward and downward ranges give sharper forecasts than symmetric CARR. — [IDEAS](https://ideas.repec.org/h/eme/aecozz/s0731-9053(05)20009-9.html)

### Inferences
- For a reference-price system, the natural targets are U = High − Ref and D = Ref − Low, both ≥ 0, in points. They are the "up range" and "down range" of asymmetric CARR. In VECM terms, the stationary range (U + D) anchors them while their split varies with drift and skew. Modeling log U and log D separately, with a shared volatility factor such as HAR-range or implied volatility plus asymmetric terms (prior-day return sign, overnight gap direction, put skew), is consistent with all three strands of this literature.
- Much of the predictability of the "high" and "low" levels in VECM papers comes from the fact that they are anchored to the previous close or open. The genuinely forecastable part is mostly volatility, that is, the size of U + D. The split between U and D is closer to a coin flip unless there are directional signals. Expect much better skill on U + D, or on max(U, D), than on U and D individually.
- Censoring and timing: if Ref is the open, then min(U, D) is often small, because the open is frequently near one extreme. Distributions of U and D have a point mass near 0 and should be modeled with quantile methods or mixture models rather than Gaussian errors.

### Gaps
- Neither VECM paper uses S&P 500 futures or intraday reference prices other than the prior close. I found no paper that explicitly models open-to-high and open-to-low for ES.
- Quantitative out-of-sample error reductions from Cheung et al. and Caporin et al. were not extracted, only qualitative conclusions.

---

## 5. How practitioners use ATR %, expected move, and VIX1D for intraday levels

### Takeaway
Retail and prop traders project ATR fractions (±50% and ±100% of 14-day ATR) from the open or prior close as "likely extremes." They track "% of ATR used" to judge exhaustion, and they treat the straddle or VIX1D-implied move as a one-standard-deviation band. These are heuristic tools with little published validation. The quantitative evidence above suggests they are biased in predictable ways.

### Cited Findings
- A TradingView 14-day ATR script draws ±50% and ±100% ATR lines from the daily open as "a visual guide for potential price extremes." It tracks the percentage of ATR realized today to "assess if a move is near exhaustion," and cautions that conditions may prevent price from reaching the full ATR. — [TradingView script 40ANMz67](https://cn.tradingview.com/script/40ANMz67)
- Other scripts project ATR levels from the prior close, high, and low, and use them for targets, mean-reversion entries, and stops "beyond normal flows." — [TradingView ATR Daily Levels](https://de.tradingview.com/script/q6nrbx80-ATR-Daily-Levels); [TradingView Daily ATR Levels SystemAlpha](https://de.tradingview.com/script/Ljt95oYt-Daily-ATR-Daily-Levels-SystemAlpha); [TradingView ATR Daily vs Current](https://de.tradingview.com/script/JBeTkjGg-ATR-Daily-vs-Current)
- The expected move is the straddle-implied range. For example, a $2 straddle on a $100 stock implies a ±2% move. — [Market Chameleon / IBKR presentation](https://ibkrcampus.com/wp-content/uploads/2023/05/2021-WB-4202-Market-Chameleon-July-11-2023.pdf)
- SPX expected-move indicators exist on TradingView, and expected-move pages exist for SPY and XSP. — [TradingView SPX Expected Move](https://www.tradingview.com/script/kvk4QGap-SPX-Expected-Move); [Options Analysis Suite SPY](https://www.optionsanalysissuite.com/etf/spy/expected-move)
- tastylive explains VIX1D as a gauge of same-day expected moves for 0DTE traders. — [tastylive, What is VIX1D](https://www.tastylive.com/news-insights/what-is-vix1d-how-does-it-work)

### Inferences
- "±100% ATR from the open" overstates typical one-sided excursions. If ATR is about the average full range, the expected one-sided distance from the open is closer to 50–60% of ATR, with a larger share on trend days. The "% of ATR used" heuristic is effectively a conditional-range model: given the range so far, how much remains. This can be formalized as a conditional quantile of the final range given the intraday range so far and the time of day.
- ATR in points is not comparable across volatility regimes. Normalizing by price (ATR%) or by implied volatility (realized range ÷ implied 1σ) gives a stationary target that is much easier to model and calibrate across 2017-style low-volatility and 2020/2022-style high-volatility regimes.

### Gaps
- I found no rigorous published validation of ATR-fraction levels for ES, and no ES-specific typical ATR values. Initial-balance practices (the first-hour range) were not covered by retrievable sources.

---

## 6. Pitfalls: event days (FOMC, CPI), regime shifts, normalization across volatility regimes

### Takeaway
Scheduled macro events cause large, predictable shifts in implied short-dated volatility. VIX1D rises about 61% the day before and drops about 25% on the day. These events also produce known return and volatility patterns, such as the pre-FOMC drift and the roughly 45-minute post-FOMC decay in implied volatility. The variance risk premium flips sign in crises. Unconditional models therefore miscalibrate on exactly the days that matter most. Event flags, volatility normalization, and regime-aware evaluation are essential.

### Cited Findings
- VIX1D around 20 CPI and FOMC events: +61.4% the day before, about −24.8% on announcement day. Its largest single-day jumps (+153% on January 11, 2023, the day before CPI; +133% on December 11, 2022) came just before CPI or FOMC. — [Cboe Insights](https://www.cboe.com/insights/posts/how-the-vix-1-d-index-performance-compares-to-the-vix-index-and-other-volatility-indices-in-11-charts)
- The VIX and VIX futures decline significantly at the FOMC announcement, and the decline lasts about 45 minutes. A larger realized volatility spike at the announcement means a smaller implied-volatility decline. — [AUT repository, Fernandez-Perez, Frijns and Tourani-Rad, J. Empirical Finance 41 (2017)](https://openrepository.aut.ac.nz/handle/10292/9444); [OU research portal](https://research.ou.nl/en/publications/when-no-news-is-good-news-the-decrease-in-investor-fear-after-the/)
- **Pre-FOMC drift (Lucca and Moench, J. Finance 2015; sample 1994–2011).** The S&P 500 gained about 49 bp in the 24 hours before announcements, versus about 1 bp on other days. More than 80% of the annual equity premium was earned in those windows, and prices showed no significant move after the decision. — [NY Fed Liberty Street Economics](https://libertystreeteconomics.newyorkfed.org/2012/07/the-puzzling-pre-fomc-announcement-drift); [Boston Fed slides](https://www.bostonfed.org/economic/conf/Macro-Finance-2012/presentations/lucca.pdf)
- FOMC-day 0DTE SPY straddles priced at roughly double neighboring weeks and were "largely respected." — [FlashAlpha](https://flashalpha.com/articles/are-0dte-straddles-overpriced-193-spy-sessions-data-study)
- **Regime flips.** The variance risk premium was about −22 (1998) and about −68.6 (2020 shock), so implied volatility badly understated realized in crises. Tail days such as April 9, 2025 produced realized moves of about 2.5x the implied 1σ. — [OptionMetrics](https://optionmetrics.com/blog/how-accurate-is-implied-volatility/); [FlashAlpha](https://flashalpha.com/articles/are-0dte-straddles-overpriced-193-spy-sessions-data-study)
- **Regime-dependent model rankings.** GARCH beats CARR in lower-volatility samples. Parkinson-based models win in up-trends and in high or low volatility, and CARR wins in down-trends. — [Dialnet PDF](https://dialnet.unirioja.es/descarga/articulo/2723714.pdf); [IDEAS, Applied Financial Economics 2013](https://ideas.repec.org/a/taf/apfiec/v23y2013i21p1635-1647.html)
- Hit rates of 0DTE implied moves varied by year, from 69% to 85% in partial 2026. — [FlashAlpha](https://flashalpha.com/articles/are-0dte-straddles-overpriced-193-spy-sessions-data-study)

### Inferences (design lessons for an ES HOD/LOD-distance system)
1. **Target normalization.** Model the ratios U/σ̂ and D/σ̂, where σ̂ is the day's implied 1σ in points (from VIX1D or the 0DTE straddle) or the HAR-range forecast. Convert back to points at the end. This removes most regime non-stationarity and makes "the expected move multiplier" the learned object.
2. **Combine sources.** Use a HAR-on-log-range baseline, add VIX1D or the straddle-implied move (adjusted for the risk premium), add an event-calendar dummy (CPI, FOMC, NFP, OPEX, month-end), and add the overnight-session range and gap. Albers suggests the implied term carries most of the one-day information. HAR catches persistence where options are mispriced.
3. **Path vs terminal.** Calibrate empirical multipliers for path extremes rather than using 1σ directly as a HOD/LOD bound. Straddles price the close-to-close move, but HOD and LOD are path maxima.
4. **Event handling.** On event days, the timing of the move matters. The FOMC move happens at 14:00 ET plus about 45 minutes of implied-volatility decay. CPI is released at 08:30 ET, before the RTH open. A reference price set after the release, such as the 09:30 RTH open, already contains much of the CPI move. A pre-release reference does not.
5. **Tails and evaluation.** Use quantile outputs (P50, P80, P95 of U and D) and pinball loss. Report coverage separately for event and non-event days and for each volatility tercile. Expect undercoverage in crisis regimes when the variance risk premium turns negative.
6. **Leakage.** VIX1D drifts intraday, and ES trades overnight. Make sure every input is timestamped before the reference time.

### Gaps
- I found no academic study quantifying how much larger the ES or S&P 500 futures intraday range is on FOMC or CPI days than on control days. Many such studies exist in the macro-announcement literature, but none were retrieved within the search budget.
- No source evaluated the post-2022 0DTE-era change in intraday range dynamics, for example dealer gamma pinning and its effect on whether price stays within implied ranges, beyond vendor commentary.
- I did not find out-of-sample evidence that the pre-FOMC drift persisted after 2011.
