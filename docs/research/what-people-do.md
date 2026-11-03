# What people actually do, and what survives: a wider look beyond price patterns

2026-11-03. Follows `swing-trading-research.md` and five failed pre-registered tests (see `log.md`). Question asked: keep hunting, see what people do.
About 20 more searches across three rounds. I read abstracts, summaries and vendor pages, not the full papers, so every claim carries a tag.

| Tag | Meaning | Trust |
|---|---|---|
| **[P]** | A named paper's abstract or a summary of it, via web search | Medium-high; "[P2]" means I only saw it second-hand (a blog citing a paper) |
| **[O]** | An official source (SEC, Cboe factsheet) via search | High |
| **[B]** | Blog, vendor page, forum, unaudited statistic | Low: direction only |
| **[L]** | Read in a reference repo under `Trading/reference/` | Medium |
| **[I]** | My own inference | Mine to be challenged |

## 1. What the evidence says about people, not ideas

| Finding | Source |
|---|---|
| Across 888 real algorithms on Quantopian with at least six months of live data, backtest Sharpe ratio explained under 3% of out-of-sample results (R² < 0.025), and the more a developer had backtested a strategy the larger the gap between backtest and live. | Wiecki et al., "All That Glitters Is Not Gold" [P] |
| The systematic families retail people say they run are trend following, mean reversion, arbitrage and market making. I found **no survey** of what profitable retail algo traders run, and no audited track-record data. | education and vendor pages [B] |
| Prop firm "funded trader" challenges: pass rates are usually quoted at 5 to 15%; one analysis of over 300,000 accounts across 10 firms says 14% passed and 7% of all traders ever reached a payout, with average payouts near 4% of the funded account. None of it is audited, and the model depends on challenge fees from the many who fail. | industry blogs [B] |
| Studies of individual investors keep finding losses (see `swing-trading-research.md` section 5). | [P] |

Honest reading: nobody has published credible, audited evidence of a retail account that systematically beats the index with a repeatable rule. What exists is mostly marketing, survivors who post, and strategies that look good in a backtest. [I]

## 2. The approaches people use, one by one

### A. Tactical asset allocation (Faber-style: hold each asset class only above its 10-month average) 
The most common simple systematic approach, with ready-made IBKR automation code published by one vendor.
| | |
|---|---|
| Original result | 1972 to 2005: Sharpe 0.81, CAGR 11.7%, max drawdown 9.5% (monthly) [B] |
| Out of sample | 2006 to March 2025, same rule, no re-tuning: Sharpe 0.68, CAGR 6.05%, max drawdown 11.7% (Concretum Group) [B] |
| Against | A Monte Carlo review argues the original backtest oversold the result and that the sample was favourable [B]. One 60/40 comparison found less volatility with a moderately higher return [B]. The page gives no buy-and-hold figure and mentions no costs. |
| Reading | A real risk-reducer, a worse *return* than owning stocks, consistent with our own SMA and rotation tests. Low turnover, so it is cheap to run. [I] |

### B. Managed futures and trend following
Subpar since early 2009, still diversifying over long periods; slightly behind US stocks since 1990 but ahead of bonds and commodities [B]. A stand-alone per-market Sharpe near 0.15 is quoted as the realistic expectation, so a useful trend result comes from breadth across many markets, which a small account cannot reach with futures. [B][L]

### C. Selling options for premium (the "wheel", put writing, covered calls)
Cboe's own index factsheet through September 2025, measured from January 2007: PUT index Sharpe 0.49 against 0.60 for the S&P 500 total return, annual return 6.7% against 10.7%, max drawdown -32.7% against -50.9% [O]. Older Cboe material using a longer window favours the put-writing indexes [B]. Gross of trading costs in one study, with a higher turnover than the index itself [P]. Negative skew, so Sharpe flatters it. Reading: a different risk shape, not extra money. [I]

### D. Small-cap value tilts
One tracker shows AVUV roughly tied with SPY since late 2019 (16.35% vs 16.25% a year) with deeper drawdowns [B]. The size premium averaged 30 bps a month in 1926 to 1981 and 8 bps in 1982 to 2017 (earlier note, [P]).

### E. Capacity-limited niches (what institutions cannot or will not trade)
| Niche | Evidence | Fit for us |
|---|---|---|
| Merger arbitrage | 0.6 to 0.9% a month in 1981 to 1996, attributed to limits on arbitrageurs [P]. A practitioner guide says small deals are skipped by institutions but small investors have little edge beyond luck on the large, well-arbitraged ones [B]. | Needs deal data and judgment; no recent evidence found |
| Microcaps | Manager marketing pieces say capacity limits create an edge [B]; machine-learning anomaly returns shrink sharply or vanish once microcaps and distressed stocks are excluded (Avramov, Cheng, Metzker, via summaries) [P2] | Costs and liquidity are the problem |
| Share buybacks | The long-run abnormal return found in 1985 to 2002 disappeared in 2003 to 2010 (Fu and Huang, via a summary) [P2] | Skip |
| Spin-offs | Mixed, small-sample, mostly theses: positive for the spun-off entity in some Nordic and European samples, negative or nil in others [P2] | Skip |
| Insider purchases | Opportunistic insiders' trades earned 82 bps a month value-weighted in Cohen, Malloy, Pomorski (2012; sample ending 2007) [P]. Recent work says returns vanish and turn negative when the dollar amount per signal is capped at a reasonable size and correlate negatively with liquidity (Oenschlager and Mollenhoff 2025, as cited) [P2]. A 2020 to 2025 sample of 47,458 purchases found a placebo shifted six months forward gave a similar result, which undermines the benchmark [B]. | Free data exists (see section 3); evidence has decayed |

### F. LLM and text-based signals (the Claude-adjacent frontier)
| | |
|---|---|
| Result | ChatGPT scores of news headlines predict next-day returns out of sample, more strongly for small stocks and after negative news (Lopez-Lira and Tang) [P]. GPT-4 forecasts the direction of next earnings from anonymized statements with about 60% accuracy, and strategies built on it earn a higher Sharpe than machine-learning benchmarks (Kim, Muhn, Nikolaev; Sharpe values not retrieved) [P]. |
| Central warning | **Look-ahead and memorization:** a model trained on text that includes the test period can "remember" the outcome. The authors say you must use a sample after the model's knowledge cutoff. A time-restricted-pretraining study finds positive, significant returns even without look-ahead, but it is a single follow-up [P]. |
| Decay | The authors expect predictability to fall as more people use these tools [P]. No direct recent replication measuring the decay found. |
| Reading | The one frontier where Claude has a real comparative advantage, and the one where honest backtests are hardest. A **forward test** (record the model's call now, score the outcome later) avoids both look-ahead and overfitting entirely. [I] |

### G. Machine-learning cross-sectional models
Large published long-short Sharpe ratios (Gu, Kelly, Xiu) are concentrated in microcaps; implementable versions (no microcaps, no distressed firms, with costs) lose more than half or become insignificant [P2].

### H. Discretionary swing methods (CANSLIM, Minervini)
No peer-reviewed test found. One vendor backtest on Canadian stocks over 25 years: the trend filter alone 9.6% a year vs 8.3% for the ETF with a 38% vs 47% drawdown, and adding stops lowered returns [B]. Vendor sells screeners, so treat it as promotional. [B]

## 3. What would be testable honestly with free data

| Direction | Data | Main problem | Honest test type |
|---|---|---|---|
| Tactical asset allocation on ETFs | Free IBKR daily bars for 5 to 6 ETFs from 2006 | Close to what we already ran | Pre-registered backtest, cheap |
| Insider purchases | SEC Insider Transactions Data Sets, quarterly zips from 2006, free [O] | Needs prices for delisted stocks (IBKR does not serve them) so any backtest is biased upward; evidence has decayed | Forward test only |
| LLM reading of earnings releases and filings | SEC EDGAR filings, free | Memorization in any historical test; Claude API cost per document | Forward test only |
| Options income | Needs an options data and order path | New build; reading above says no edge over the index | Skip for now |

[I] for the whole table.

## 4. Conclusions

1. **What people do** is mostly trend following, mean reversion and tactical allocation, with little verified profit data. The strategies that hold up under scrutiny are diversified and low-turnover with a Sharpe near 0.5 to 0.7, which roughly matches, not beats, stock returns. [B][P][I]
2. **Bigger published edges** live where a small account cannot trade (microcaps, hard-to-borrow shorts, speed) or have decayed since publication. [P][P2]
3. **The one place that is new and on-theme** is LLM-read text. Its historical tests are contaminated, but a forward test is clean and cheap to run. [P][I]
4. **The most valuable thing we can build once** is a signal ledger (append-only record of every call, with timestamp, rule version and inputs, later scored against realised returns). It turns "does this work?" into a question that cannot be overfitted, and it serves tactical allocation, insider signals and LLM signals equally. [I]

## 5. Proposed next steps (not started)
1. **Pre-register and run tactical asset allocation** (Faber 5-asset, 10-month average, free ETF data). Expected: lower drawdown, no more money than buy and hold. It is what real people run.
2. **Build the signal ledger** and attach two forward tests: insider cluster purchases (SEC data) and a Claude reading of earnings releases (8-K item 2.02). The Claude test has an API cost per document, which I would estimate and cap before starting.
3. **Keep the mean-reversion forward test running** (`python -m tempo.forward`).

## Sources
- [Wiecki et al., All That Glitters Is Not Gold (Quantpedia summary)](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/)
- [Wiecki et al. (CXO Advisory summary)](https://www.cxoadvisory.com/big-ideas/in-sample-vs-out-of-sample-performance-of-888-trading-strategies/)
- [Prop firm statistics 2026 (Track360)](https://track360.io/blog/prop-trading-industry-statistics-2026)
- [Only 1 in 20 pass prop firm challenges (Finance Magnates)](https://www.financemagnates.com/forex/only-1-in-20-traders-pass-prop-firm-challenges-reports-the-funded-trader/)
- [Concretum Group, Global Tactical Asset Allocation with Python and IBKR](https://concretumgroup.substack.com/p/global-tactical-asset-allocation)
- [Capital Spectator on Faber's backtest](https://capitalspectator.com/?p=7974)
- [Befriend the Trend, managed futures overview (Cambridge Associates)](https://publishedresearch.cambridgeassociates.com/befriend-the-trend-an-overview-of-managed-futures-investing/)
- [Cboe PUT Index factsheet](https://cdn.cboe.com/resources/indices/factsheet/CboeGlobalIndices_PUT-Index.pdf)
- [Cboe benchmark indexes using SPX options](https://www.cboe.com/insights/posts/key-cboe-benchmark-indexes-using-spx-options-offer-strong-risk-adjusted-returns/)
- [AVUV vs SPY tracker](https://totalrealreturns.com/n/AVUV,SPY)
- [Cohen, Malloy, Pomorski, Decoding Inside Information](https://dash.harvard.edu/bitstream/1/33785679/1/cohen,malloy,pomorski_decoding-inside-information.pdf)
- [Insider purchase signals in microcaps (arXiv 2602.06198)](https://arxiv.org/html/2602.06198v2)
- [Insider buys study (Equibles)](https://equibles.com/research/what-happens-after-an-insider-buys-evidence-from-47-458-open-market-purchases)
- [SEC Insider Transactions Data Sets](https://www.sec.gov/dera/data/form-345)
- [Merger arbitrage for small investors](https://www.researchgate.net/publication/331178119_Merger_Arbitrage_Investment_as_an_Effective_Strategy_for_High_Rollers_and_Small_Time_Investors_Evidence_from_US_Cash_Deal_Mergers)
- [Limited arbitrage in mergers and acquisitions (HBS)](https://www.hbs.edu/ris/Publication%20Files/arbitrage_af05900b-acd4-44db-8210-70a9fbc3cf6c.pdf)
- [Lopez-Lira and Tang, Can ChatGPT Forecast Stock Price Movements? (arXiv)](https://arxiv.org/pdf/2304.07619)
- [DatedGPT: lookahead bias in LLMs (arXiv)](https://arxiv.org/pdf/2603.11838)
- [Kim, Muhn, Nikolaev, Financial Statement Analysis with LLMs (arXiv)](https://arxiv.org/abs/2407.17866v3)
- [Gu, Kelly, Xiu, Empirical Asset Pricing via Machine Learning (SSRN)](https://papers.ssrn.com/abstract=3159577)
- [Minervini trend template backtest (MarketInOut, vendor)](https://www.marketinout.com/blog/minervini-trend-template-backtest-tsx)
- [Retail algorithmic trading guide (QuantInsti)](https://blog.quantinsti.com/algorithmic-trading-retail-traders/)
