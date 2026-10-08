# HOD/LOD timing, Opening Range / Initial Balance statistics, and Market Profile frameworks for ES futures

Research date: 2026-10-08. About 17 tool calls. Several key forum pages (nexusfi.com, futures.io) returned HTTP 403 to the fetcher, so their numbers come from search-result snippets only. They are flagged **[UNVERIFIED / forum or self-reported]** below.

## Q1. Unconditional HOD/LOD timing statistics for ES (RTH vs ETH, first 30/60/90 min, trend-up vs trend-down days)

### Takeaway
The day's extremes cluster at the open and, to a lesser degree, at the close (a U-shape). Midday is a dead zone. The most-cited ES numbers are:
- Linnsoft (1,000 RTH days to Nov 2010): HOD forms in the first 30 minutes 24.6% of the time and LOD 27%. Each 30-minute bar between 11:30 and 14:00 ET gets only about 3%.
- A NexusFi count (unverified, 1,249 days): HOD falls in the first 90 minutes on 37% of days and LOD on 50%.

A drift-free random walk would already produce a U-shape (the arcsine law). So "extremes happen at the open" is partly a mathematical artifact and only partly a market edge. No recent (2020s) ES study with published numbers was found.

### Cited Findings
- Linnsoft "Homework: HOD and LOD counts" covers 1,000 days of ES data ending 11/23/2010, using **day-session (RTH) bars only**. HOD forms in the first 30 minutes of the session 24.6% of the time and LOD 27% of the time. — [Linnsoft](https://linnsoft.com/videos/homework-hod-and-lod-counts)
- Same study: "during the 2.5 hour mid-day period beginning 11:30am ET, the HOD and LOD is rarely created (around 3% of the time for each 30-min period)." — [Linnsoft](https://linnsoft.com/videos/homework-hod-and-lod-counts)
- Same study: HOD forms in the **first 5 minutes** 11.8% of the time and LOD 11.6%. Linnsoft notes this is roughly the same probability as an entire 120-minute midday stretch. — [Linnsoft](https://linnsoft.com/videos/homework-hod-and-lod-counts)
- The full per-30-minute table (e.g., the last 30 minutes) was not in the page text; it sits in linked charts. — [Linnsoft](https://linnsoft.com/videos/homework-hod-and-lod-counts)
- **[UNVERIFIED / forum]** A NexusFi poster counted 1,249 days. HOD occurred in the first 90 minutes on 457 of 1,249 days (37%) and LOD on 621 of 1,249 days (50%). The poster credits the idea to Al Brooks's ES studies. The thread was active as of 2022; the page returned 403, so this comes from the search snippet only. — [NexusFi thread](https://nexusfi.com/showthread.php?p=813066)
- **[UNVERIFIED / secondhand attribution to Al Brooks]** Brooks's 5-minute bar-count heuristic, as summarized by a TradingView script: Bar 1 has a 20–30% chance of being the high or low of the day, Bar 12 (about 1 hour) about 50%, and Bar 18 (about 90 minutes) 80–90%. Note this is "high **or** low", i.e. at least one extreme is in, not both. — [TradingView "Brooks 18 Bars"](https://www.tradingview.com/script/3DkQZipV-Brooks-18-Bars-KintsugiTrading/)
- Brooks Trading Course forum example: Brooks judged price near HOD at Bar 18, and the HOD had printed at Bar 14. — [Brooks Trading Course forum 48D](https://brookstradingcourse.com/support-forum/48-trading-the-open/48d-how-do-one-know-that-we-are-near-the-hight-of-the-day)
- Academic, FTSE 100 futures (Acar, Lequeux & Ritz, LIFFE, 1996). This paper is the theoretical baseline:
  - Under a drift-free Brownian random walk, the time of the high or low follows an **arcsine-type law** (Feller 1951), so extremes are much likelier near the open or close than midday.
  - Empirically (Jul 1992–Sep 1995, 38-minute bars), extremes cluster at the open **more** than the random walk predicts: about 32% chance of a high and 33% chance of a low in the first segment.
  - At the close, the data roughly match the random walk.
  - The time gap between HOD and LOD peaks around 456 minutes, versus 266 under the random walk. Both extremes are usually separated by most of the session.
  — [Acar et al. PDF](https://www.financnik.cz/forum/uploads/monthly_2010_11/acar-emmanuel-timing-the-highs-and-lows-of-the-day.pdf)
- Academic: Mok, Lam & Li (2000), Rev. Quant. Fin. & Acct. They derived high/low-time distributions under a random walk. S&P 500 futures data **failed to reject** the random walk, while Hang Seng extremes were over-represented in the first 15 minutes (abstract only). — [HKBU scholars](https://scholars.hkbu.edu.hk/en/publications/using-daily-highlow-time-to-test-for-intraday-random-walk-in-two-/)
- Panas (2005, Applied Economics) fit the time to the first daily max/min with generalized beta distributions and found it U-shaped. The data were Athens stocks, not ES. — [IDEAS/RePEc](https://ideas.repec.org/a/taf/applec/v37y2005i2p191-199.html)
- Ekman's Purdue dissertation on S&P 500 futures (1983–88) found roughly U-shaped intraday patterns in trade counts and volatility. — [Purdue](https://docs.lib.purdue.edu/dissertations/AAI9018815)
- **ETH / 24h tooling:** the TradingView "HoD/LoD hourly timings" script buckets each day's HOD and LOD into hours 0–23 over the available history.
  - It supports a custom day start. Its example ran on ES1! with an **11pm New York** day start and about 920 days of history; no numeric table is published.
  - The author warns of "continuation bias": if the day boundary falls in an active period, the adjacent hours look artificially full of extremes. He suggests putting the boundary in a quiet hour.
  - Indicator and chart timezones must match.
  - About 900 days of hourly ES history are available on premium accounts.
  — [TradingView HoD/LoD hourly](https://www.tradingview.com/script/f58uWvIm-High-of-Day-Low-of-Day-hourly-timings-Statistics-Time-of-day)
- The TradingView "Daily High & Low Time Map" offers:
  - day anchors at 18:00 NY (CME), 09:30 NY (RTH), or midnight;
  - a **day-type filter (closed above vs below open)**, a direct analog of a bullish/bearish split;
  - Wilson confidence intervals, with cells dimmed below 30 days. It states that a share out of 10 days is "a number, not a finding";
  - exclusion of days below 60% bar coverage (half-days, gaps).
  It publishes no ES numbers. — [TradingView Time Map](https://www.tradingview.com/script/u0etVs4Y-Daily-High-Low-Time-Map-HOD-LOD/)

### Inferences
- In the RTH frame, a prior of about 25% per extreme in the first 30 minutes and 35–50% in the first 90 minutes (forum figure) is reasonable. A 10-day sample will swing widely around these.
- **Trend-up vs trend-down days:** the logic follows from the definitions, not from a found study.
  - On a bullish day (close > open, especially a close near the high), the LOD tends to come early and the HOD late. The reverse holds for bearish days.
  - The NexusFi asymmetry (LOD early 50% vs HOD early 37%) fits a sample with an upward drift: more up days means more early lows.
  - So splitting by bullish/bearish will mechanically produce "LOD early / HOD late" on bull days. Much of that is tautology from the label, not predictive information (see Q6).
- Under the arcsine law, even pure noise yields a U-shaped histogram. A useful system should compare its histograms to that random-walk baseline (e.g., simulate shuffled returns) before treating peaks as an edge.
- **ETH vs RTH:** with an 18:00 ET day start, a large share of ETH extremes fall overnight (Asia/London) or at the 09:30 open. ETH-anchored and RTH-anchored stats are not comparable and should never be mixed.

### Gaps
- No ES study from the 2020s with a full published per-hour table was found. Linnsoft's data end in 2010, and the NexusFi figures are unverified.
- No published ES split of HOD/LOD timing by trend-up vs trend-down day was found.
- No published ETH (18:00–17:00) hourly HOD/LOD table for ES with numbers was found; the TradingView scripts show screenshots only.
- The Al Brooks numbers are secondhand. The primary text (Brooks' books or course video 48D) was not accessed.

## Q2. Opening range breakout and Initial Balance (first hour) statistics

### Takeaway
No publicly verifiable ES-specific IB-extension percentages were found. The figures that circulate come from vendor or marketing posts on other tickers (QQQ, TSLA, YM) or sit behind paywalled tools (Edgeful). Reference sources themselves state that no dependable universal IB statistics exist. The best usable proxy for "the HOD/LOD is set in the IB" is the Brooks/NexusFi first-60/90-minute figures in Q1.

### Cited Findings
- Edgeful defines the IB as the first hour (9:30–10:30 ET for US markets). It classifies each day as breakout (only the IB high is broken), breakdown, double break, or no break, measured by close or by wick. Lookback is selectable from 1 month to 5+ years. The article reports no ES numbers. — [Edgeful IB report](https://www.edgeful.com/blog/posts/initial-balance-breakout-report)
- **[Vendor marketing, non-ES]** Edgeful reports that for QQQ over one year, single breaks occur 72% of the time and double breaks 25%. The date range on the page is internally inconsistent. Other examples:
  - TSLA, Fridays only, 6 months: one-side break 84%, both sides 4%.
  - YM: "97.4% stat on break days across 128 NY sessions".
  — [Edgeful IB strategy](https://www.edgeful.com/blog/posts/initial-balance-breakout-strategy); [Edgeful docs](https://docs.edgeful.com/trade-using-edgeful/for-day-traders/initial-balance-breakout)
- Implication of the QQQ figures: about 97% of days break the IB at least once (72% + 25%). That would mean the IB contains *both* HOD and LOD only about 3% of the time, and one extreme is usually in the IB. This is unverified for ES. — [Edgeful IB strategy](https://www.edgeful.com/blog/posts/initial-balance-breakout-strategy)
- The LuxAlgo library states "No dependable universal statistics exist" for IB breakout reliability. It calls the idea that a narrow IB extends and a wide IB holds "practitioner lore rather than measured law." Conventional extension levels are 0.5x, 1.0x, 1.5x and 2.0x the IB range. A 30-minute IB is a common variant, and in 24h markets the IB depends on a session convention. — [LuxAlgo Initial Balance](https://www.luxalgo.com/library/concept/initial-balance/)
- TradingView IB indicators plot 25/50/75/100% IB extensions and claim to track "extension hit rates", but publish no ES numbers. One claims 12 years of 1-minute NQ data (2013–2025), again without published percentages. — [TradingView IB Extensions](https://www.tradingview.com/script/lR2POs1Y-Initial-Balance-Extensions); [TradingView IB Statistical Mapping](https://de.tradingview.com/script/2iuvi66N-Initial-Balance-Statistical-Mapping)
- With 24h trading, the IB "is often now regarded as less important than in the past." — [TradingView Koalafied IB](https://www.tradingview.com/script/sIiOZTVt-Koalafied-Initial-Balance-Levels-and-Extensions)

### Inferences
- For the system, the cleanest IB feature to compute in-house is per day: (a) whether the IB broke up, down, both or neither; (b) the extension multiple = (HOD − IBH)/IB range and (IBL − LOD)/IB range. This turns "distance to HOD/LOD in points" into an IB-normalized number that is more stable across volatility regimes.
- If, as on QQQ, almost every ES day breaks the IB, then one extreme is "in the IB" on most days. The practical question becomes *which* side. That is the same question as the bullish/bearish split.

### Gaps
- No verified ES figures for IB extension frequency, single vs double break rates, or the share of days with the HOD/LOD inside the IB. They need to be computed from data (e.g., the Edgeful platform or the in-house dataset).
- Dalton's own numeric thresholds (for example, what counts as "range extension" for a Normal Variation day) were not verified from the book.

## Q3. Market Profile (Steidlmayer, Dalton): day types, value area, POC, and their use in anticipating HOD/LOD

### Takeaway
Market Profile classifies sessions by how far and how decisively price extends beyond the IB:
- **Normal**: a wide IB holds all day.
- **Normal Variation**: about a 2x IB extension on one side.
- **Trend**: a narrow IB, then relentless one-way extension with the close near the extreme.
- **Neutral / Neutral Extreme**: extension on both sides.
- **Double Distribution**: two separate value zones.

The day type maps directly to HOD/LOD timing. On Normal days both extremes sit in the IB, i.e. in the first hour. On Trend days one extreme is at the open and the other at the close. On Neutral days one extreme is in the IB and the other comes later, often in the afternoon. The type, however, is only certain in hindsight.

### Cited Findings
- Taxonomy summary (from Steidlmayer's CBOT work and Dalton's teaching):
  - Normal: wide IB contains the whole session, with two-sided rotation inside.
  - Normal variation: one-sided extension of roughly 2x the IB.
  - Trend: narrow IB, relentless one-direction extension, close near the extreme, little rotation.
  - Neutral: extension on both sides. It becomes Neutral Extreme if the close is near one extreme, and stays unresolved balance if the close is mid-range.
  - Common additions: non-trend day and double-distribution trend day.
  — [LuxAlgo day-type taxonomy](https://www.luxalgo.com/library/concept/day-type-taxonomy/)
- "Fading extremes tends to pay on normal and neutral days and to fail badly on trend days." The type "only becomes certain in hindsight", so the skill lies in reading the open, the IB width, and how extensions behave. — [LuxAlgo day-type taxonomy](https://www.luxalgo.com/library/concept/day-type-taxonomy/)
- The IB is the first two 30-minute TPO periods. Steidlmayer introduced Market Profile at CBOT in the mid-1980s, and Dalton's *Mind Over Markets* (1990) popularized IB-based day typing. — [LuxAlgo Initial Balance](https://www.luxalgo.com/library/concept/initial-balance/)
- Retail summaries of day types exist but are looser and lower quality. — [TradingView "Types of Market Days"](https://de.tradingview.com/chart/NIFTY/6vpuGuR9-The-Types-of-Market-Days-Ultimate-guide-to-trading-days)

### Inferences
- Mapping day type to HOD/LOD timing, by definition:
  - Normal: both extremes in the IB (first hour).
  - Normal Variation: one extreme in the IB, the other later in the extension direction.
  - Trend: one extreme near the open, the other near the close.
  - Neutral Extreme: one extreme in the IB, the other near the close.
  - Neutral (center close): extremes on both sides after the IB, the later one often midday or afternoon.
  
  This explains why an unconditional histogram is bimodal, and why "similar days" should ideally be matched on **IB width relative to ATR** and the **open-type** (e.g., Dalton's Open-Drive, Open-Test-Drive, Open-Rejection-Reverse, Open-Auction), not just on direction. The open-type terms come from memory of Dalton; no source was fetched (see Gaps).
- Value area and POC (the 70% volume/TPO zone and the max-volume price) act as rotation targets on balance days. On trend days price leaves value and does not return. The system could log whether HOD/LOD formed at, or rejected, the prior day's VAH/VAL. This rests on Dalton theory with no verified hit-rate statistic.

### Gaps
- No empirical frequency of each Dalton day type in ES was found (e.g., "trend days = X% of sessions").
- No published statistics on how often prior-day VAH/VAL/POC are touched or become the HOD/LOD in ES.
- Dalton's open-types and exact day-type thresholds were not verified from primary text in this pass.

## Q4. Reference levels (prior-day high/low/close, overnight high/low, VWAP, ATR) and touch frequency

### Takeaway
The only hard number found: Linnsoft (2,043 days, instrument not stated on the page, probably ES) shows the **overnight high was broken by 12:30 ET on 50.6% of days**, broken after 12:30 on about 10.8%, and **never broken in RTH on about 38.6%**. No verified ES statistics were found for touch rates of prior-day high/low, VWAP, or ATR targets; they exist only inside tools.

### Cited Findings
- Linnsoft Homework #12 (2,043 days): the ON high was broken by 12:30 pm ET on 1,033 days (50.56%), after 12:30 on 221 days, and never during the day session on 789 days. Overnight-low numbers and the instrument are not given in the page text. — [Linnsoft HW12](https://www.linnsoft.com/videos/homework-12-timing-overnight-high-and-low-breakouts)
- Edgeful's "Overnight range stats" defines the overnight session as **4:00 PM–9:29 AM ET** and reports how often RTH breaks the ON high/low. It suggests targeting the most-touched levels. No numbers are public. — [Edgeful ON range docs](https://docs.edgeful.com/trade-using-edgeful/price-action-reports/overnight-range-stats)
- A TradingView "Level survival tracker" reports, for prior-day H/L, ON H/L and OR H/L: P(test), P(break | test), and median rejection distance. Its definitions:
  - **touch**: a bar overlaps the level within a tolerance frozen at the open;
  - **break**: a confirmed close beyond the level plus tolerance, after a touch.
  — [TradingView Level survival tracker](https://kr.tradingview.com/script/uqxo7Vc2-Level-survival-tracker/)
- A premarket-levels script for ES/NQ (premarket defined as 18:00–9:30) computes the probability that the premarket high/low is touched in RTH and the average touch time. No numbers are published. — [TradingView Premarket Levels](https://it.tradingview.com/script/j9BeR2m2-Premarket-Levels)

### Inferences
- The overnight high (and by symmetry the low) is a coin-flip-plus target. About 39% of days never break the ON high, so on many down days the ON high *is* the ETH HOD. For an ETH-anchored system this matters a great deal: on those days the RTH HOD differs from the true session HOD.
- Distances in points should be supplemented with distances to these reference levels, and normalized by ATR, so that "10 similar days" from different volatility regimes are comparable.

### Gaps
- No verified ES touch rates for PDH/PDL/PDC, VWAP, VWAP bands, or ATR-multiple targets.
- The overnight-low counterpart of the Linnsoft figure was not retrieved.

## Q5. Time-zone and session-boundary issues (ES Globex 18:00–17:00 ET; Israel 23:00 = 17:00 ET)

### Takeaway
ES trades Sunday 18:00 ET to Friday 17:00 ET, with a daily 17:00–18:00 ET halt. The trade date rolls at 18:00 ET. The choice of day anchor (18:00 ET vs 09:30 ET vs midnight) changes HOD/LOD hour distributions substantially (the "continuation bias" from Q1).

### Cited Findings
- Weekly Globex: Sunday 6:00 PM ET to Friday 5:00 PM ET, with a daily 5–6 PM ET maintenance and trade-date rollover. Sources conflict on additional historical halts: 4:15–4:30 PM ET and a 3:15 PM CT pause are cited by some low-quality pages. Official confirmation should come from CME's contract page. — [Optimus Futures community](https://community.optimusfutures.com/t/what-time-does-the-futures-and-commodities-market-open/3064); [TradeAlgo](https://www.tradealgo.com/trading-guides/futures/futures-market-hours-expiration)
- Session anchors offered by a TradingView tool: 18:00 NY (CME), 09:30 NY (RTH), midnight NY, and midnight UTC. Bucket indexing follows daylight saving through the anchor timezone, and the repeated autumn DST hour is handled explicitly. — [TradingView Time Map](https://www.tradingview.com/script/u0etVs4Y-Daily-High-Low-Time-Map-HOD-LOD/)
- The day boundary should be placed in a quiet hour; otherwise the hours adjacent to the boundary are inflated. — [TradingView HoD/LoD hourly](https://www.tradingview.com/script/f58uWvIm-High-of-Day-Low-of-Day-hourly-timings-Statistics-Time-of-day)

### Inferences
- **DST mismatch:** this comes from general knowledge and is not sourced in this pass, so verify it. The US and Israel change clocks on different dates:
  - US: 2nd Sunday of March and 1st Sunday of November.
  - Israel: the Friday before the last Sunday of March, and the last Sunday of October.
  
  For a few weeks each spring and autumn, ET−Israel is 6 hours instead of 7. So "23:00 Israel = 17:00 ET" is wrong in those windows, and "16:30 Israel = 09:30 ET" shifts too. The system should store all timestamps in UTC or America/New_York and convert for display only. It should bucket hours in ET, since market events (09:30 open, 10:00 data, 14:00 FOMC, 16:00 cash close) are pinned to ET.
- The 18:00 ET anchor sits in the quiet post-reopen hour, which suits ETH stats. But the 09:30 open then becomes a mid-session event, and RTH-only stats need a separate anchor.
- Half-days (holidays) and the 17:00–18:00 gap should be excluded or flagged, as the Time Map tool does with its 60% coverage rule.

### Gaps
- The current official CME ES hours page was not fetched. Whether the 16:15–16:30 ET halt still exists (believed removed in CME's 2021 harmonization) is unverified here.

## Q6. Pitfalls: hindsight in bull/bear labels, sample size, regime change (0DTE era)

### Takeaway
There are three structural problems:
1. A bullish/bearish label known only at the close builds the timing answer in: up days mechanically have early lows and late highs.
2. 10 days is far too few. Wilson intervals on a per-hour share are about ±25–30 points.
3. Intraday dynamics have shifted since 2022–23 with 0DTE options. Studies associate 0DTE volume with higher intraday (not close-to-close) volatility, which can alter how far and when extremes form.

### Cited Findings
- Tool guidance: cells under 30 days are dimmed, and "a share out of ten days is a number, not a finding". Wilson score intervals are recommended. The tool makes no forecast; "high still ahead" is conditional on completed days. — [TradingView Time Map](https://www.tradingview.com/script/u0etVs4Y-Daily-High-Low-Time-Map-HOD-LOD/)
- Day type "only becomes certain in hindsight". — [LuxAlgo day-type taxonomy](https://www.luxalgo.com/library/concept/day-type-taxonomy/)
- A drift-free random walk alone produces extremes clustered at the open and close (arcsine law, Feller 1951). The empirical excess over that baseline at the open is modest (about 32–33% in the first of about 13 segments for FTSE futures). — [Acar et al. 1996](https://www.financnik.cz/forum/uploads/monthly_2010_11/acar-emmanuel-timing-the-highs-and-lows-of-the-day.pdf)
- S&P 500 futures in Mok, Lam & Li did **not** reject the random-walk timing distribution. — [HKBU](https://scholars.hkbu.edu.hk/en/publications/using-daily-highlow-time-to-test-for-intraday-random-walk-in-two-/)
- 0DTE regime, University of Utah study (Brogaard, Han, Won): a 1-SD rise in 0DTE volume is associated with about a 14% jump in S&P 500 daily volatility, mainly intraday. — [Yahoo/Bloomberg coverage](https://www.bnnbloomberg.ca/zero-day-options-are-reordering-the-way-the-stock-market-behaves-1.1921930) (press coverage; paper not read directly)
- Zero-day contracts reached a record 55% of S&P 500 options volume on one day (Nomura, Aug 2023). Intraday swings were "masked by muted close-to-close moves". — [Bloomberg](https://www.bloomberg.com/news/articles/2023-08-14/zero-day-options-cement-presence-in-reversal-ridden-stock-market)
- UBS: 0DTE (+1DTE) have been "instrumental in driving more intraday volatility" not captured close-to-close. In April 2025, S&P 500 intraday volatility almost doubled in a week to 44%. Causation is debated. — [NBC/CNBC](https://www.nbcdfw.com/news/business/money-report/zero-day-options-are-fueling-the-unprecedented-volatility-on-wall-street-amid-tariff-chaos/3816621/)
- JPMorgan (2023) modeled that in an extreme scenario 0DTE flows could turn a 5% intraday drop into a 25% rout. This is a simulation, not evidence. — [Yahoo/Reuters](https://www.yahoo.com/news/0dte-options-could-turn-5-214117774.html)
- The Linnsoft HOD/LOD study ends in 2010 and the overnight study is of similar vintage, i.e. pre-0DTE and pre-24h-retail. — [Linnsoft](https://linnsoft.com/videos/homework-hod-and-lod-counts)

### Inferences (lessons for the 10-similar-days HOD/LOD distance and hour-distribution system)
1. **Avoid lookahead in the bull/bear split.** If "bullish day" means close > open, the split is only usable after the fact.
   - For live use, condition on information known at decision time: overnight direction, gap vs prior close, open vs ON range, IB direction or width, price vs VWAP at 10:30.
   - Or present the split explicitly as scenarios ("if today turns out bullish, the LOD was typically at X and the HOD at Y").
   - Also show the unconditional mix and the historical base rate of bull vs bear among the similar days.
2. **Sample size.** With n = 10 (about 5 per bull/bear bucket), a single hour bucket is meaningless; 3/5 = 60% has a Wilson 95% CI of about 23–88%. Better options:
   - Aggregate to coarse windows (first 30 minutes, 09:30–11:00, midday, last hour, overnight).
   - Show CIs.
   - Blend with a long-run unconditional prior, e.g. shrinkage toward base rates from multi-year data.
3. **Normalize distances.** Report HOD/LOD distance from the open (or from the 18:00 reopen) in points **and** as multiples of ATR(14) or of the IB range. Points from 2019 and 2025 are not comparable at very different index levels and volatility.
4. **Use a random-walk baseline.** Overlay the arcsine-law expectation, or a bootstrap from shuffled 5-minute returns, to show whether the similar-days histogram differs from noise.
5. **Fix the anchor and timezone.** Store data in UTC, bucket in ET, and use one anchor (18:00 ET for ETH, or 09:30 ET for RTH) consistently. Label ETH vs RTH extremes separately, since about 39% of days never break the ON high in RTH (Linnsoft), so RTH HOD ≠ session HOD on many days.
6. **Weight regimes.** Prefer similar days from 2023 onward (the 0DTE era) or add a regime feature, because intraday volatility structure has plausibly changed. Exclude half-days and roll days, and treat FOMC/CPI days as their own class, since event times pin the extremes.
7. **Add day-type tags.** Tagging each historical day with a Dalton day type (Normal, Normal Variation, Trend, Neutral, Double Distribution) explains its HOD/LOD timing better than bull/bear alone. IB width relative to ATR is the real-time proxy.

### Gaps
- No quantitative study was found showing how 0DTE changed the *timing* (not just the magnitude) of ES HOD/LOD. One would need to compare pre-2022 and post-2023 hour histograms in-house.
- The Quantpedia (Feb 2026) note on 0DTE and volatility was seen only as a tag-page snippet. — [Quantpedia 0DTE tag](https://quantpedia.com/tag/0dte-options/)
- Not checked: Quantified Strategies, TradingStats, or a recent Edgeful ES HOD/LOD timing post. Edgeful's numeric reports are platform-gated.
