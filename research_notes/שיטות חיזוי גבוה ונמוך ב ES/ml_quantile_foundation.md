# ML, Quantile, Conformal and Foundation-Model Approaches for Forecasting ES Daily High/Low Distance and HOD/LOD Timing

Context: the existing system uses about 10 analog (similar) days to show high-of-day (HOD) and low-of-day (LOD) distance levels and hour histograms. These notes cover methods that could replace or wrap that system. Research is current as of October 8, 2026. Where a source was a search snippet and not a fetched primary page, these notes say so.

## 1. Quantile regression, quantile random forests, and LightGBM/XGBoost with pinball loss for open-to-high and open-to-low distance

### Takeaway
I found no published study that applies quantile GBMs or quantile forests to ES "open-to-high" or "open-to-low" distance. The closest established work treats the daily high-low range as a volatility proxy (the CARR and Parkinson line of research), and there the range-based models beat GARCH on the S&P 500. The practical recipe is to build a separate quantile model for each distance (upside and downside), normalize the target by recent volatility, fix any crossing quantiles, and then calibrate the result with conformal methods (section 2).

### Cited Findings
- **How it works, in plain terms.** Quantile LightGBM usually fits one model per quantile, with defaults of 0.1, 0.5 and 0.9, and stacks the results into a band — [spotforecast2 quantile LGBM factory docs](https://www.gm.th-koeln.de/~bartz/spotforecast2-safe/docs/reference/multitask.factories.quantile_lgbm_forecaster_factory.html)
- **Crossing quantiles.** Because each quantile is trained on its own, the predicted quantiles can cross. A common fix is to sort them per row after prediction so that p10 ≤ p50 ≤ p90 — [climagrid forecasting models source](https://climagrid.readthedocs.io/en/latest/_modules/climagrid/forecasting/models.html)
- **Reading a quantile pair as a range.** A 0.1/0.9 pair defines a range that covers the central 80% of outcomes. That is the same logic you would use for a band of HOD/LOD distances — [Optimizing Quantile-based Trading Strategies in Electricity Arbitrage, arXiv 2406.13851](https://arxiv.org/pdf/2406.13851)
- **Range-based volatility evidence.**
  - Chou's CARR model (JMCB, 2005) models the daily high-low range dynamically, in a GARCH/ACD-like way. Out of sample on the S&P 500, it gave sharper volatility estimates than GARCH. Its basis is that the range is an efficient estimator of local volatility (Parkinson, 1980) — [IDEAS/RePEc: Chou 2005](https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html)
  - On the FTSE 100 and Nikkei 225, CARR beat GARCH because it uses the intraday high/low information — [Using CARR to Forecast Volatility of Stock Indices](https://dx.doi.org/10.2991/jcis.2006.175)
  - Which model wins depends on the regime. Parkinson did better in up-trends and at extreme volatility levels, while CARR did better in down-trends and at average volatility — [Applied Financial Economics 2013 (RePEc)](https://ideas.repec.org/a/taf/apfiec/v23y2013i21p1635-1647.html)
- **Direct quantile modelling of the range.** A 2015 seminar by Jennifer Chan proposed regressing directly on the quantiles of the intraday high-low range inside a CARR framework, using generalized beta-2 and generalized-t families. It was applied to the All Ordinaries index to produce VaR forecasts. This is a seminar abstract only; I found no peer-reviewed version — [USyd seminar abstract](https://ssh.maths.usyd.edu.au/s/scnitm/jormerod-StatisticsSeminar-Jennife)
- **Predicting daily highs instead of closes.** A 2016 Quantitative Finance paper predicted next-day highs of S&P 500 stocks with classifiers. Its argument was that closes are noisier because of volatility near the close — [IDEAS/RePEc QF 2016](https://ideas.repec.org/a/taf/quantf/v16y2016i5p793-826.html)
- **Classifying S&P 500 open-to-close returns.** A 2019 International Journal of Forecasting paper used random-forest classification with four classes. Most of the trading value came from the strong-up and strong-down classes — [IDEAS/RePEc IJF 2019](https://ideas.repec.org/a/eee/intfor/v35y2019i1p390-407.html)
- **GBMs on return data.** In finance return forecasting, strong GBM ensembles (CatBoost, LightGBM) beat zero-shot foundation models. Rahimikia et al. report this for daily excess returns; I saw it as summarized in search results — [FinText HF org](https://huggingface.co/FinText)

### Inferences
- **What to model.** The natural targets are U = (High − Open) / σ and D = (Open − Low) / σ, where σ is a volatility scale such as an ATR, a HAR realized-volatility forecast, or the VIX/VVIX level. Normalizing this way makes the problem roughly stationary across regimes.
- **Fitting.** Fit pinball-loss LightGBM, or a quantile regression forest, at τ = 0.1, 0.25, 0.5, 0.75 and 0.9. Useful features include the overnight (Globex) range, the gap, prior-day range, realized-volatility lags in HAR form (1, 5 and 22 days), VIX and its term structure, the day of week, and event flags (FOMC, CPI, NFP, OPEX).
- **Relation to the analog method.** The 10-analog-day method is essentially a k-nearest-neighbour conditional quantile estimator with k = 10. That is very noisy for tail quantiles: 10 samples cannot pin down a p90 reliably. A QRF is a smoothed, learned-similarity generalization of the same idea, so it is the most natural upgrade.
- **Baseline.** The CARR/Parkinson literature suggests a cheap baseline: a HAR model on log range, plus an empirical residual distribution.

### Gaps
- I found no paper that applies LightGBM, XGBoost or QRF quantile models directly to open-to-high and open-to-low distances for ES or other index futures.
- I did not verify a primary URL for the zillow `quantile-forest` package (JOSS 2024). It was mentioned only in a search summary.

## 2. Conformal prediction for calibrated intervals (split conformal, ACI, EnbPI, conformal PID)

### Takeaway
Conformal methods turn any point or quantile forecaster, including the analog-day method, into intervals with an empirical coverage guarantee. For financial time series that are not exchangeable, the online variants (ACI, DtACI, conformal PID, EnbPI) are the relevant ones. All of them guarantee only long-run marginal coverage, not coverage conditional on the current regime. ACI's own showcase example is market volatility.

### Cited Findings
- **ACI (Gibbs & Candès, 2021).**
  - ACI updates the miscoverage level online so that long-run coverage stays near the target under distribution shift.
  - The paper's worked example is volatility: squared daily returns as the target, GARCH(1,1) forecasts refit on a rolling window of about 5 years, and relative error as the conformity score.
  - The authors note that shifting market dynamics make GARCH predictions inaccurate over long periods.
  - [arXiv 2106.00170](https://arxiv.org/pdf/2106.00170)
- **EnbPI (Xu & Xie, ICML 2021).**
  - EnbPI wraps an ensemble of bootstrap models. It does not require exchangeability, and it has approximately valid marginal coverage for time series with strongly mixing errors.
  - It needs no data splitting and no retraining. Leave-one-out bootstrap residuals serve as the calibration scores, and a sliding window of residuals lets it adapt.
  - Sources: [arXiv 2010.09107](https://arxiv.org/pdf/2010.09107); [ICML 2021 poster](https://icml.cc/virtual/2021/poster/10469); an implementation in AWS Fortuna, [Fortuna EnbPI source](https://aws-fortuna.readthedocs.io/en/latest/_modules/fortuna/conformal/regression/enbpi.html)
- **Conformal PID control.** This frames quantile tracking as P control. The I term accumulates past miscoverage, and the D term is a "scorecaster" that forecasts the next score's quantile — [arXiv 2307.16895](https://arxiv.org/pdf/2307.16895). The authorship (Angelopoulos, Candès, Tibshirani) was not verified on the page.
- **Market-implied conformal volatility intervals (Cañete, 2023).** Option-implied volatility is used as the point forecast of realized volatility, and online conformal methods add the interval around it. The study evaluates rolling coverage and width over 15 years of daily data and concludes that this works — [PMLR v204](https://proceedings.mlr.press/v204/canete23a.html)
- **Online NoVaS conformal volatility.** A related variant — [PMLR v204 canete23b](https://proceedings.mlr.press/v204/canete23b.html)
- **Conformal VaR.** At 95%, DtACI produced consistently narrower intervals than AgACI, with up to a 33% reduction in median width at nominal coverage. The intervals widened during COVID and the 2022 shocks. This is a working paper — [Conformal prediction VaR PDF](https://khuong.uk/Papers/Conformal_prediction_VaR.pdf)
- **Stock-return intervals compared.** Inductive (split) conformal gave robust coverage but wider intervals, while the adaptive methods traded reliability for efficiency. This is a master's thesis, not peer-reviewed — [Tampere thesis](https://trepo.tuni.fi/handle/10024/232978)
- **ACI coverage caveat.** ACI guarantees only marginal coverage, and its thresholds fluctuate. Multivalid conformal methods target group-conditional validity and were tested on stock data — [arXiv 2206.01067](https://arxiv.org/pdf/2206.01067)
- **Further reading.** A recent tutorial: [Gentle Introduction to Conformal Time Series Forecasting, arXiv 2511.13608](https://arxiv.org/pdf/2511.13608). A benchmark of these methods: [Conformal Prediction Algorithms for Time Series Forecasting: Methods and Benchmarking, arXiv 2601.18509](https://arxiv.org/pdf/2601.18509)
- **Conformal methods inside a commercial foundation model.** Nixtla TimeGPT produces its quantiles with conformal prediction — [nixtlar quantiles vignette](https://nixtla.r-universe.dev/nixtlar/doc/quantiles.html)

### Inferences
- **Applying this to HOD/LOD distance.**
  - Use conformalized quantile regression: the scores are max(q_lo − y, y − q_hi), taken from the LightGBM or QRF quantiles.
  - Alternatively, use the analog-day empirical quantiles as the base and let ACI or PID adjust α each day. That would fix the systematic under- or over-coverage of a k = 10 empirical band without changing the analog logic.
- **Coverage by regime.** Use Mondrian (group-wise) conformal by regime, for example VIX tercile or event day versus normal day. Otherwise the coverage guarantee can hold on average while failing on high-volatility days.
- **Choosing a variant.** Expect a trade-off between ACI or DtACI (adaptive, with noisier width) and static split conformal (stable, but it breaks under drift).

### Gaps
- I found no paper that applies conformal methods specifically to the daily high-low range or to open-to-extreme distances for index futures.

## 3. Classifying the hour of HOD/LOD (multiclass) or survival/hazard models for "has the high been set yet"

### Takeaway
Very little research targets the timing of daily extremes directly. The main academic reference (Panas, 2005) finds that the time to the first maximum or minimum follows a U-shape, with extremes clustered near the open and close. I found no ML study, and no survival or hazard study, of ES HOD/LOD timing. This area is open, so methods have to be borrowed: multiclass classification with calibrated probabilities, or discrete-time hazard models.

### Cited Findings
- **Panas (2005, Applied Economics).**
  - Models the *first* time of the day at which the maximum or minimum occurs, using one-minute data from the Athens Stock Exchange.
  - Fits a generalized beta distribution to the time to the first max or min, which turns out U-shaped, consistent with the U-shaped intraday curves.
  - [IDEAS/RePEc](https://ideas.repec.org/a/taf/applec/v37y2005i2p191-199.html)
- **The intraday "U effect" in volatility.** Volatility is high after the open, reaches its minimum around lunch, and rises into the close. This was documented for the CAC 40 — [arXiv 1009.4785 (vanity mirror)](https://www.arxiv-vanity.com/papers/1009.4785/)
- **U-shaped returns and volatility on the Athens General Index.** The pattern also differs between bull and bear markets — [Surrey open research](https://openresearch.surrey.ac.uk/esploro/outputs/preprint/Intraday-Stock-Returns-Patterns-Revisited-A/99928617502346)
- **Early classification of session direction.** On the Ibex 35, session direction could be classified with acceptable accuracy about 24 minutes after the open. I saw this only via a search summary — [rio.upo.es record](https://rio.upo.es/entities/publication/948853b7-d131-41f3-bcc4-1423800b49d8)
- **Intraday regimes.** SPY intraday regimes were identified with clustering and HMMs, then fed into deep forecasters — [Princeton DataSpace](https://dataspace.princeton.edu/handle/88435/dsp01t722hd139)
- **Low predictability of intraday index-futures returns.** Opening- and closing-hour returns of index futures showed generally low predictability, with some economic significance — [Tinbergen event page](https://tinbergen.nl/event/2020/08/31/11075/intraday-price-patterns)

### Inferences
- **Multiclass approach.** Predict the hour bucket of the HOD and the LOD (for example the RTH hours 9:30–16:00 ET, plus overnight) with a multinomial LightGBM. Evaluate with log-loss or the multiclass Brier score against the unconditional U-shaped histogram as the baseline. Calibrate the probabilities (isotonic or temperature scaling). A k = 10 analog histogram is extremely noisy, since about 7 hourly bins hold only 10 samples. Smoothing it toward the unconditional prior, for example with a Dirichlet prior, is a quick win.
- **Survival/hazard approach for "has the high been set yet".**
  - Treat each intraday bar as a discrete time step and model the probability that the running high at time t is the final daily high, conditioned on the current state: distance from the open relative to the predicted quantiles, time of day, and realized range so far.
  - This is a discrete-time hazard, or logistic per-bar, model. It updates naturally during the day, which suits a live dashboard.
- **A link worth exploiting.** If the morning has already exceeded the predicted p75 upside distance, the conditional probability that the HOD is already in should rise. A hazard model with "distance versus forecast quantile" as a feature captures this.

### Gaps
- I found no published survival or hazard study of HOD/LOD timing for any index or futures market.
- I found no published tabulation of the ES HOD/LOD hour distribution with a verified source. It would need to be computed in-house.

## 4. Time-series foundation models (TimesFM, Chronos, Moirai, TimeGPT, Granite TTM): quantile outputs, covariates, access, and evidence on financial data

### Takeaway
Current versions as of October 2026:
- **TimesFM 3.0** (Aug 2026). It has native covariates and multivariate forecasting. Its weights are non-commercial when self-hosted, and commercial use is through BigQuery ML.
- **TimesFM 2.5** (Sept 2025). It has 200M parameters, a 16k context and a quantile head. Covariates are supported via XReg, and the weights are Apache-2.0.
- **Chronos-2** (Oct 2025). It has 120M parameters, native past and future covariates, quantile outputs, and an Apache-2.0 license.
- **Moirai 2.0.** A decoder-only model with quantile loss.
- **TimeGPT.** Quantiles are produced via conformal prediction, and exogenous variables are supported.
- **Granite TTM r2.** Tiny, Apache-2.0.

On financial data, zero-shot TSFMs are weak for returns. For realized volatility they are roughly on par with Log-HAR, with TTM the only model that wins narrowly. Fine-tuning or finance-specific pretraining (PFN, FinText) is what produces gains.

### Cited Findings
**TimesFM (Google)** — [GitHub google-research/timesfm](https://github.com/google-research/timesfm)
- **2.5 (released Sept 15, 2025).**
  - Smaller and longer-context than 2.0: 200M parameters (down from 500M) and a 16k context (up from 2048).
  - An optional 30M quantile head gives continuous quantiles up to a 1k horizon.
  - The frequency indicator was removed.
  - Covariate support was restored via XReg on Oct 29, 2025.
- **3.0 (released Aug 2026).**
  - Native multivariate forecasting, plus past-only and past-and-future covariates.
  - Returns a point forecast plus 9 quantiles (0.1–0.9).
  - The repo claims rank #1 among foundation models on fev-bench, TIME and GIFT-Eval.
  - Rollout to BigQuery ML finished in Sept 2026.
- **Licensing.** The weights up to 2.5 are Apache-2.0. The 3.0 weights are under `timesfm-non-commercial-license-v1.0`; commercial use goes through Google Cloud (BigQuery ML).
- **Install and checkpoints.**
  - `pip install timesfm[torch]`; PyPI is at `timesfm==2.0.2`, updated July 2, 2026.
  - The 3.0 checkpoint is `google/timesfm-3.0-pytorch` on Hugging Face.
  - A LoRA fine-tuning example (HF Transformers + PEFT) was added on Apr 9, 2026.
  - The repo states that this is not an officially supported Google product.
- **BigQuery `AI.FORECAST`.**
  - `confidence_level` sets the prediction interval (default 0.95, valid range [0, 1)).
  - Other parameters are `context_window`, `forecast_end_timestamp` and `output_historical_time_series` — [BigQuery AI.FORECAST docs](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast)
  - A third-party guide says the selectable models are TimesFM 2.0 and 2.5 with 2.0 as the default, and gives context limits of 64–2048 (2.0) and 64–15360 (2.5). The official page did not confirm these, and they may be outdated given the 3.0 rollout — [fdaytalk guide](https://www.fdaytalk.com/ai-forecast-bigquery/)

**Chronos-2 (Amazon)**
- **Design and covariates.**
  - 120M parameters, encoder-only.
  - Natively supports past-only and known-future covariates, both real and categorical. Group attention gives in-context learning across related series and covariates.
  - Older Chronos and Chronos-Bolt lack native support for future covariates and need external regressors.
- **Outputs and limits.**
  - Multi-step quantile forecasts via `quantile_levels`.
  - Maximum context 8192; maximum prediction length 1024.
  - Apache-2.0 license.
- **Install and deployment.** `pip install "chronos-forecasting>=2.0"`, then use `Chronos2Pipeline`. A June 5, 2026 update added deployment via AutoGluon-Cloud — [HF amazon/chronos-2](https://huggingface.co/amazon/chronos-2); [autogluon/chronos-2 README](https://huggingface.co/autogluon/chronos-2/blob/main/README.md)
- **Announcement date.** The Amazon Science announcement was Oct 20, 2025 — [AWS Japan blog](https://aws.amazon.com/jp/blogs/news/introducing-chronos-2/)

**Moirai 2.0 (Salesforce)**
- **Design.** Decoder-only, trained on 36M series, with quantile loss and multi-token prediction — [arXiv 2511.11698](https://arxiv.org/pdf/2511.11698)
- **GIFT-Eval rank.** Salesforce claimed it was #1 by MASE among non-leaking models at launch — [Salesforce blog](https://www.salesforce.com/blog/moirai-2-0/). Under the paper's stricter filter (30 models), it ranks 5th on MASE and 6th on CRPS — [arXiv 2511.11698](https://arxiv.org/pdf/2511.11698)

**GIFT-Eval**
- Scores are normalized by seasonal naive and aggregated by geometric mean, covering MASE (point) and CRPS (probabilistic) — [arXiv 2511.11698](https://arxiv.org/pdf/2511.11698); [GIFT-Eval paper arXiv 2410.10393](https://arxiv.org/pdf/2410.10393)

**Nixtla TimeGPT**
- **Uncertainty.** Uses either `quantiles` or `level`, not both, and the quantiles come from conformal prediction. Python output columns are named like `TimeGPT-q-10` — [Nixtla quantile tutorial](https://nixtlaverse.nixtla.io/nixtla/docs/tutorials/10_uncertainty_quantification_with_quantile_forecasts); [nixtlar vignette](https://nixtla.r-universe.dev/nixtlar/doc/quantiles.html)
- **Exogenous variables.** Both historic and future exogenous variables are supported — [nixtlar articles](https://nixtla.r-universe.dev/articles)

**IBM Granite TTM**
- `ibm-granite/granite-timeseries-ttm-r2` is Apache-2.0 and based on the TinyTimeMixer paper (arXiv 2401.03955) — [HF commit page](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2/commit/7f5a40f6d0a198694d854f0ff3b974157c6f1fa0)

**Evidence on financial data**
- **Brini (arXiv 2607.05291, July 6, 2026).** Compared 9 zero-shot TSFMs (including Chronos-Bolt, TimesFM 2.5, Moirai, Lag-Llama, Toto, Sundial and TTM) against 8 econometric models on realized volatility for 50 assets (equities, FX and futures, from the VOLARE dataset) at 3 horizons.
  - Pooled losses favour the TSFMs, but outlier assets drive that result. Averaging each asset's loss ratio to Log-HAR, only TTM beats Log-HAR, narrowly, at every horizon.
  - Mincer–Zarnowitz recalibration shows the short-horizon gains come mostly from better scaling. A real informational gain appears only at the monthly horizon.
  - An equal-weight TTM + Log-HAR average enters the Model Confidence Set for 98–100% of assets.
  - Choosing the right architecture matters more than choosing foundation over econometric models.
  - [arXiv 2607.05291](https://arxiv.org/abs/2607.05291)
- **Goel, Pasricha, Magris & Kanniainen (arXiv 2505.11163, May 2025).** Zero-shot TimesFM is a reasonable baseline for realized volatility, but incremental fine-tuning was needed to beat the econometric benchmarks, significant under Diebold-Mariano and Giacomini-White tests — [arXiv 2505.11163](https://arxiv.org/abs/2505.11163v1)
- **Fu, Hirano & Imajo (Preferred Networks; arXiv 2412.09880, Dec 2024).**
  - TimesFM does poorly on raw prices. Continual pretraining on about 100M financial time points (hourly and daily) improved accuracy and mock-trading metrics: returns, Sharpe ratio, max drawdown and cost.
  - The training and evaluation data were cut at the end of 2022 to avoid look-ahead.
  - [arXiv 2412.09880](https://arxiv.org/abs/2412.09880); [PFN tech blog](https://www.preferred.jp/en/blog/tech/timesfm)
- **FinText (Rahimikia, Ni & Wang, 2025).**
  - 613 finance-pretrained TSFMs, Chronos and TimesFM variants, released under Apache-2.0.
  - Off-the-shelf TSFMs underperform zero-shot, while finance-pretrained ones give large gains.
  - Models are released per year vintage, for example `TimesFM_8M_2022_Augmented`.
  - [HF FinText](https://huggingface.co/FinText); [model card example](https://huggingface.co/FinText/TimesFM_8M_2022_Augmented/blob/main/README.md)
- **Fine-tuned TimesFM for VaR.** On S&P 100 daily returns over 19 years, the fine-tuned model ranked best or near-best. I saw this only as a search summary; the primary URL was not verified.

### Inferences
- **Fit to the ES problem.**
  - The ES daily-range problem is close to the realized-volatility setting, which is positive, mean-reverting and long-memory, rather than to return prediction. That is where TSFMs are most competitive.
  - Even there, the best evidence shows only parity or a small edge over Log-HAR, and the edge comes from combining the two.
- **Practical setup.**
  - Feed the TSFM the series of daily log(High − Open) and log(Open − Low), or log range. Take its quantiles, ensemble them with a HAR or LightGBM quantile model, and conformalize.
  - Use Chronos-2 or TimesFM 2.5 (both Apache-2.0) for self-hosting, with covariates such as VIX, the overnight range and event flags.
  - TimesFM 3.0 is cleanest via BigQuery for commercial use.
- **HOD/LOD timing.** TSFMs do not directly forecast "which hour". At most, they can forecast intraday volatility paths that a separate classifier then uses.
- **Licensing.** If the project is commercial, avoid self-hosting the TimesFM 3.0 weights.

### Gaps
- I did not verify a Chronos-Bolt-specific page or its release date.
- I found no information on TimeGPT-2, Moirai-MoE or the latest TTM versions.
- The current GIFT-Eval leaderboard snapshot was not retrieved.
- I found no TSFM study on daily high/low range or open-to-extreme distance specifically.

## 5. Retrieval-augmented forecasting (RAF, TimeRAF, and "When Does Retrieval Help?")

### Takeaway
RAF formalizes what the analog-day system already does. It retrieves similar past windows and feeds them, along with their continuations, as extra context to a foundation model, instead of averaging their outcomes. The 2026 critique shows that the gains depend heavily on regime. They show up mostly for periodic data with a recoverable phase, and a simple "lookup" provides most of the benefit. That is a warning for non-seasonal, noisy financial series.

### Cited Findings
- **Tire, Taga, Ildiz & Oymak, "Retrieval Augmented Time Series Forecasting" (arXiv 2411.08249; v1 Nov 2024, v2 Apr 6, 2026).**
  - RAF retrieves related time-series examples and places them in the TSFM's context, such as Chronos.
  - It improves accuracy across domains, and the gains grow with TSFM size.
  - [arXiv 2411.08249](https://arxiv.org/abs/2411.08249)
  - The fetched abstract did not give the similarity metric or the fusion details. My understanding from training data is that RAF concatenates the retrieved best-matching history and its future to the query context; the fetched page did not confirm this.
- **Han et al., "Retrieval Augmented Time Series Forecasting" (arXiv 2505.04163, ICML 2025).** A different paper with the same name. alphaXiv's summary reports an 86% win ratio across 10 benchmarks, especially on rare patterns — [arXiv 2505.04163](https://arxiv.org/pdf/2505.04163); [alphaXiv overview](https://alphaxiv.org/overview/2505.04163v1)
- **Cakiroglu, Buxton, Dalkilic & Kurban, "When Does Retrieval Help Time-Series Forecasting?" (arXiv 2609.20193, submitted July 29, 2026).**
  - **Operating point.** Retrieval's benefit depends on the ratio of the lookback window S to the dominant seasonal period L, which standard protocols never vary.
  - **A simple baseline is often enough.** At S = 12, repeating the last observed period beats six backbones on 4 of 7 benchmarks, with 8–44% lower MSE. It is up to 25% worse on datasets without a concentrated shared period.
  - **Period drives the benefit.** In a synthetic sweep, the benefit boundary tracks the seasonal period (correlation +0.71), not the horizon (−0.23).
  - **The lookup does the work.** Exact lookup matches graph diffusion, so the gain comes from consulting stored records.
  - **Zero-shot TSFMs on periodic data.** They trail trained backbones by 22–50% on periodic benchmarks.
  - **Screening.** Two statistics, a trend test and a staleness rate, predict the sign of the benefit with 0.76 accuracy, against a 0.69 majority-rule baseline.
  - [arXiv 2609.20193](https://arxiv.org/abs/2609.20193)

### Inferences
- **The analog system is a retrieval module.** Upgrade paths, in order of complexity:
  - (a) Keep the retrieval, but weight the analogs by similarity and enlarge k with kernel weights.
  - (b) Use the analogs' outcomes as features (their mean, quantiles and hour histogram) in a LightGBM quantile model.
  - (c) RAF-style: prepend the analog windows and their outcomes to a TSFM context.
- **Expected benefit for ES.** The 2026 paper suggests retrieval helps most when there is strong periodic structure. Daily ES ranges have weak periodicity beyond weekly and event calendars, so expect a modest benefit. Test it explicitly against "no retrieval" and "unconditional histogram" baselines.

### Gaps
- No TimeRAF details were retrieved; it was not verified in this session.
- I found no RAF study on financial or volatility data.

## 6. Evaluation (walk-forward, pinball loss, coverage, CRPS, baselines) and pitfalls (overfitting, look-ahead, leakage, nonstationarity)

### Takeaway
Judge every model with expanding- or rolling-window walk-forward testing. Use pinball loss per quantile, CRPS overall, empirical coverage and width for intervals, and log-loss or Brier for hour classes. Compare against seasonal-naive, Log-HAR or CARR, and the unconditional historical distribution, using DM, GW and MCS tests. The main risks are look-ahead through foundation-model pretraining data, regime drift, and small-sample noise in k = 10 analogs.

### Cited Findings
- **Probabilistic scoring and normalization.** GIFT-Eval uses CRPS for probabilistic accuracy and MASE for point accuracy, normalized by seasonal naive and aggregated by geometric mean — [arXiv 2511.11698](https://arxiv.org/pdf/2511.11698); [arXiv 2410.10393](https://arxiv.org/pdf/2410.10393)
- **Pinball (quantile) loss as the training objective.** Moirai 2.0 switched to quantile loss — [arXiv 2511.11698](https://arxiv.org/pdf/2511.11698)
- **Testing practice in the volatility-TSFM literature.**
  - Diebold-Mariano and Giacomini-White tests — [arXiv 2505.11163](https://arxiv.org/abs/2505.11163v1)
  - Model Confidence Set, Mincer–Zarnowitz recalibration, and per-asset averaged loss ratios to avoid outlier domination — [arXiv 2607.05291](https://arxiv.org/abs/2607.05291)
- **Rolling refit and coverage.** Rolling refits are needed because market dynamics shift. Coverage should be checked over rolling windows — [ACI arXiv 2106.00170](https://arxiv.org/pdf/2106.00170); [Cañete PMLR](https://proceedings.mlr.press/v204/canete23a.html)
- **Look-ahead through pretraining.**
  - PFN cut its data at the end of 2022 specifically to avoid look-ahead bias — [PFN blog](https://www.preferred.jp/en/blog/tech/timesfm)
  - FinText publishes year-vintage models, e.g. data through 2022 versus 2023 — [HF FinText](https://huggingface.co/FinText)
- **Test-data leakage on benchmarks.** GIFT-Eval comparisons explicitly separate "non test data leaking" models — [Salesforce blog](https://www.salesforce.com/blog/moirai-2-0/)
- **Pooled metrics can mislead.** A few outlier assets can drive aggregate wins — [arXiv 2607.05291](https://arxiv.org/abs/2607.05291)
- **Naive baselines can win.** Simple baselines beat sophisticated retrieval models in some regimes — [arXiv 2609.20193](https://arxiv.org/abs/2609.20193)
- **Low intraday predictability.** Intraday index-futures predictability is generally low, so expect modest gains — [Tinbergen](https://tinbergen.nl/event/2020/08/31/11075/intraday-price-patterns)

### Inferences
- **Walk-forward protocol for ES.**
  - Train on [start, t), predict day t, and roll forward.
  - Refit monthly, and keep a purge or embargo for any multi-day features.
  - Pick the analog days only from dates before t.
  - Compute features at the forecast timestamp, e.g. at 9:30 ET with the Globex session known. Never use the full-day VIX close or the RTH range in a pre-open forecast.
- **What to report for distances.**
  - Pinball loss per τ.
  - CRPS, approximated from the quantile grid.
  - Empirical coverage of the [p10, p90] band (target 80%) and its mean width, broken out by VIX regime and by event days.
- **What to report for hours.** Multiclass log-loss and Brier against the unconditional hour histogram, plus a reliability diagram.
- **Leakage and continuity checks.**
  - Contract-roll handling: use back-adjusted continuous ES carefully. Distances in points are fine, but percentages need the adjusted price base.
  - Session definition: RTH versus Globex.
  - DST shifts in hour bins: use exchange local time, ET.
  - Holidays and half-days.
- **TSFM look-ahead.** A zero-shot TSFM may have seen ES or SPX history in pretraining, which biases backtests over that period. Only out-of-sample periods after the model's training cutoff are clean.
- **Small samples.** With k = 10 analogs, the standard error of an empirical p90 is huge. Bootstrap the analog quantiles to show this, and use it to justify larger k with kernel weights, or model-based quantiles.

### Gaps
- I found no source that gives ES-specific walk-forward results for any of these methods.
- No pinball-loss or coverage benchmark for daily range forecasting of index futures was found.
