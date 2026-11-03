# Swing trading: what the evidence says, and what to test first

2026-11-03. Scope: holding periods of one day to about six weeks, daily bars, US stocks and ETFs on IBKR, a small account.
Nothing here was built or backtested; it is reading. Three tests are already done and failed (SMA 200 trend, 12-1 momentum rotation, pairs; see `log.md`).

**How to read the tags.** Every claim says where it came from, because most of the web on this topic is vendor marketing.

| Tag | Meaning | Trust |
|---|---|---|
| **[P]** | A paper's own abstract or a summary of a named academic paper, retrieved by web search. I did not read the full papers. | Medium-high |
| **[L]** | Read directly in a reference repo's files in `Trading/reference/` (their results, not independently checked) | Medium |
| **[B]** | Blog, vendor page, forum | Low. Used only for direction, never for numbers. |
| **[I]** | My own inference or judgment | Mine to be challenged |

## 1. Bottom line

1. **No published swing rule for liquid US stocks and ETFs is a reliable, cost-surviving edge today.** Almost every effect found is smaller after publication, smaller after costs, and concentrated in illiquid names where a retail account cannot trade it. [P][L]
2. **Execution costs are the main unknown, and our model may be too kind.** Tempo's backtests assume 1 bp slippage. A top finance journal paper reports IBKR small market orders cost about 0.44% round trip (working-paper tables; published tables not checked). That is for the average retail trade, not SPY, but it is ten times our assumption. [P][I]
3. **There is no peer-reviewed evidence that retail swing traders as a group make money.** Studies of individual investors find losses at holding periods from one day to 140 days. The "+2.1% a year for swing traders" figure circulating online has no traceable source and should be ignored. [P][B]
4. **The best remaining candidates are narrow and cheap to test**, not clever. Ranked list in section 6.
5. **Before any result is believed, it needs a higher bar than we used:** a t-statistic above 3, an honest count of variants, and roughly a 50% haircut for decay. [P]

## 2. Idea by idea

### A. Short-term reversal (buy last week's losers, sell last week's winners)
| | |
|---|---|
| For | Real in the data. Nagel: reversal profits are what liquidity providers earn, they are forecastable by the VIX and rise sharply in turmoil (2007 to 2009). [P] mmr measured 5-day reversal at IC t=2.65, and combining it with momentum raised gross Sharpe from 0.42 to 0.52. [L] |
| Against | Avramov, Chordia, Goyal: profits sit in illiquid, high-turnover stocks and are smaller than trading costs. [P] mmr: turnover jumps from 14x to 62x and net Sharpe falls from 0.52 to 0.19 ("we capture 0.19 of a 0.52 signal"). [L] Blitz and Huij: a conventional reversal strategy earned 18 bps a month and can turn negative after costs, though a residual version stays positive in large caps after 1990. [P] Chan: reversals after moves with no news are mainly in small illiquid stocks. [P] |
| Cost fit | Poor. It is the highest-turnover idea on the list. |
| Testable now | Yes with about 100 large-cap daily histories (survivorship bias applies). |
| Prior | Likely fail net of costs. Possible small pass only with a VIX filter or a residual (industry-neutral) version. [I] |

### B. Time-series mean reversion on index ETFs (RSI(2), internal bar strength)
| | |
|---|---|
| For | A real, simple effect on SPY and QQQ historically. [B] |
| Against | The one analysis with a before/after split: Sharpe 0.97 before the book was published, 0.68 after, below buy-and-hold's 0.87 in the same years; invested only about 11% of days. [B, a Substack, not peer reviewed] Fills assumed at the close using an indicator only final at the close. Vendor pages quote 70%+ win rates with no method. [B] No independent post-cost, rolling out-of-sample test found. |
| Cost fit | Good: SPY and QQQ are the cheapest things to trade. Low exposure means low costs. |
| Testable now | Yes (needs high and low for IBS; our files hold closes only). |
| Prior | Probably a small positive Sharpe that does not beat buy-and-hold. Useful only as a low-exposure diversifier. [I] |

### C. Breakouts and 52-week highs (buy strength with a stop)
| | |
|---|---|
| For | George and Hwang 52-week-high effect, documented across many markets. [P] |
| Against | Across 20 markets, profits are no longer significant in most once costs are included; in Australia the liquid-stock version failed after costs and short-sale limits. Transaction costs erase one half to two thirds of the risk-adjusted profit in index studies. Little evidence on US recent decades; nothing found on Donchian-style channel breakouts. [P] |
| Prior | Weak. It overlaps with momentum, which already failed here. [I] |

### D. Industry and sector momentum (rotate sector ETFs monthly)
| | |
|---|---|
| For | Moskowitz and Grinblatt (1999): industry momentum remains profitable after controlling for stock momentum, size and value, strongest at a one-month horizon. Another study reports sector index momentum profitable after transaction costs. [P] ETF costs are tiny. |
| Against | A later paper says factor momentum subsumes industry momentum. Sample is 1963 to 1995 portfolios, not ETFs. No out-of-sample ETF test found. mmr found that much of its "momentum alpha" was sector momentum, concentrated, market-correlated and crowded. [P][L] |
| Cost fit | Good (monthly, about 11 ETFs). |
| Testable now | Yes, free data. |
| Prior | Our 10-ETF rotation already failed; a sector-only variant tests something narrower but is correlated with that failure. [I] |

### E. Post-earnings drift
Martineau: drift for large stocks has been essentially nonexistent since about 2006; it survives in illiquid stocks. [P] **Skip.** Cannot be traded profitably by us.

### F. High-volume return premium
Gervais, Kaniel, Mingelgrin: unusual volume over a day or week predicts higher returns; it persists longer for liquid stocks and appears in most developed markets. [P] Real but old; needs volume data we do not store. Worth one test if cheap. [I]

### G. Overnight drift (hold from the close to the next open)
| | |
|---|---|
| For | Cooper, Cliff, Gulen: for 1993 to 2006 the equity premium was earned overnight with trading-hour returns near zero; ETF evidence in SPY, QQQ, DIA. Lou, Polk, Skouras (2019) tie momentum and reversal profits to the overnight leg. A later paper says it persisted in 1998 to 2019. [P] ibkr-algo-trader's research reaches the same view. [L] |
| Against | Every source is gross of costs; nobody costed trading it daily. It needs two orders a day (market-on-close in, open out). My own check: at the cost level our model uses, commissions alone are about 0.02% a day on $10,000, so the gross spread must be larger than that. Sample 1993 to 2006 is old. I could not confirm whether the spreads quoted (0.068% for SPY) are per day or per year, so the size of the effect is unknown. [P][I] |
| Cost fit | Unknown, and that is the point of testing it. |
| Testable now | Needs open prices (our downloader stores closes only). |
| Prior | The most structural, best-replicated of the effects. The honest question is only whether costs eat it. [I] |

### H. Stops, sizing, and risk overlays (not strategies, but they decide results)
| Finding | Source |
|---|---|
| Under a random walk a simple stop-loss always lowers expected return; with momentum it can add value; a stop on a mean-reversion strategy hurts. Tight stops on mean-reversion swing trades are a mistake. | Kaminski and Lo (2014) [P] |
| A stop on a momentum strategy cut a modeled worst month from about -50% to -11%. | Han, Zhou, Zhu, via a secondary summary [P] |
| Volatility-scaled sizing reduces tail risk and drawdown, not return; the return-boost claims failed out of sample. | Cederburg et al. (2020), plus ibkr-algo-trader's review [P][L] |

### I. Not researched
Turn-of-the-month and day-of-week effects, earnings-run-up trades, options-based swing trades, leveraged ETFs.

## 3. Costs and execution (the most important section)

| Item | What we know |
|---|---|
| Commission | IBKR Canada Pro Fixed 0.005 USD a share with a 1.00 minimum and 1% cap; Tiered 0.0035 with a 0.35 minimum plus pass-through fees; no zero-commission Lite for Canadians. SEC fee 20.60 per million sold (SEC advisory). [P] |
| Slippage | **Unknown for us.** Our model assumes 1 bp. Schwarz et al. (JoF 2025) draft tables put IBKR small market orders near 0.44% round trip, the worst of the brokers listed, with near-zero price improvement for IBKR Pro. Published tables not checked. [P] A real SPY or QQQ trade is far tighter than the average retail trade, so 1 bp may hold there and be too low for stocks. [I] |
| Execution | A 5-minute-bar bot's authors concluded the only calibration source for slippage is your own fill log. Use marketable limit orders, never naked market orders. [L] |
| Closing auction | A backtest that decides at the close and fills at the close needs a market-on-close order. Cutoffs per IBKR lessons: NYSE 15:50 ET, Nasdaq 15:55 ET, and IBKR advises submitting at least 15 minutes before the close. So the signal must be computed before 15:45 on a still-forming bar. Our backtests assume the final close, which is a small look-ahead in practice. [P][I] |
| Paper fills | IBKR paper accounts simulate top-of-book fills; fills can be better than a limit. Paper P&L is an upper bound. [L][B] |
| Data | IBKR serves ARCA-listed history from 2006 but only from the transfer date for names that moved to Nasdaq (TLT, IEF, PEP). Free daily bars are survivorship-biased because delisted names are missing. [I, observed] |

## 4. Evidence standards for results

| Standard | Source |
|---|---|
| New findings should clear t > 3.0, not 2.0, because of data snooping; one third to one half of 296 published factors are likely false. | Harvey, Liu, Zhu [P] |
| Correct the Sharpe ratio for the number of variants tried, sample length and non-normality (deflated Sharpe). | Bailey and Lopez de Prado [P] |
| Expect a 26% lower return out of sample and 58% lower after publication. | McLean and Pontiff [P] |
| Backtest Sharpe explained under 3% of live outcomes across 888 strategies. | Wiecki et al., as reported in two sources [L][B] |
| mmr's own noise control showed a "significant" t of 2.07 on random data once overlapping forward returns were used; Newey-West correction fixed it. | [L] |

Tempo already pre-registers criteria, counts variants and runs shuffled-data controls. Not yet done: a t-statistic bar and a deflated Sharpe. Adding both to the report runner is small.

## 5. What retail swing traders actually earn
No peer-reviewed study isolates retail swing traders. The nearest evidence is on individuals: Barber and Odean style analyses find economically large losses at horizons from one day to 140 trading days; Fong et al. find losses to institutions that are statistically significant even over a 10-day holding period. [P] Anything better is vendor material. [B]

## 6. Ranked test queue (each would be pre-registered before data, like the last three)

| # | Test | Why | Needs | Expected |
|---|---|---|---|---|
| 1 | **Overnight drift on SPY and QQQ** (buy the close, sell the open) | Most structural effect; fast, binary; settles the cost question for the cheapest instruments | Open prices (small change to the downloader) | Gross positive, net uncertain |
| 2 | **Low-exposure mean reversion on SPY and QQQ** (IBS and RSI(2), long only, exit on strength) | Cheap, low turnover, tests decay with a proper pre-post split | High and low prices | Small positive Sharpe, below buy-and-hold |
| 3 | **Large-cap short-term reversal with a VIX filter** | Best-documented swing effect; Nagel's conditioning is the one idea that might rescue net returns | About 100 stock histories | Probably fail net |
| 4 | **Sector-ETF one-month momentum** | Narrower than the failed rotation | Free ETF data | Probably fail |
| 5 | **High-volume return premium** | Liquid-stock persistence reported | Volume column | Unknown |

Skip: post-earnings drift, 52-week breakouts on their own, intraday anything.

## 7. What I would build once, regardless of which test wins
- **A fill and slippage log** (decision-time quote, signal price, fill price, time to fill) on the paper account, adopted from ibkr-algo-trader's plan. It is the only way to replace the assumed 1 bp with a measured number. [L]
- **The t-statistic and deflated-Sharpe lines** in the report runners.
- **A conservative paper-fill rule:** a resting limit counts as filled only if price trades through it by a tick. [L]

## 8. What would change this view
- A measured round-trip cost on SPY or QQQ well below or above 1 bp from our own fills.
- A cost-net, post-2010, US large-cap study of any idea above that I could not find.
- An idea whose edge comes from information we do not use yet (fundamentals, earnings text), not from price patterns.

## Sources
- [Nagel, Evaporating Liquidity (NBER)](https://www.nber.org/system/files/working_papers/w17653/w17653.pdf)
- [Avramov, Chordia, Goyal, Liquidity and Autocorrelations (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=555968)
- [Blitz et al., Short-Term Residual Reversal](https://www.efmaefm.org/0EFMSYMPOSIUM/2012/papers/017_update.pdf)
- [Chan, Stock price reaction to news and no-news](https://academicnewsletter.sufe.edu.cn/info/357702)
- [Gervais, Kaniel, Mingelgrin, The High-Volume Return Premium](https://ideas.repec.org/p/fth/pennfi/01-99.html)
- [Moskowitz and Grinblatt, Do industries explain momentum (JF 1999)](https://ideas.repec.org/a/bla/jfinan/v54y1999i4p1249-1290.html)
- [Martineau, Rest in Peace Post-Earnings Announcement Drift](https://econpapers.repec.org/article/nowjnlcfr/104.00000122.htm)
- [Lou, Polk, Skouras, A Tug of War (LSE)](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- [Overnight returns follow-up (arXiv 2507.04481)](https://arxiv.org/html/2507.04481v1)
- [Kaminski and Lo, When do stop-loss rules stop losses (MIT)](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)
- [Schwarz et al., The Actual Retail Price of Equity Trades (JF 2025)](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467)
- [Harvey, Liu, Zhu factor zoo summary (CXO Advisory)](https://www.cxoadvisory.com/big-ideas/taming-the-factor-zoo/)
- [Bailey and Lopez de Prado, Deflated Sharpe Ratio (SSRN)](https://papers.ssrn.com/abstract=2460551)
- [Barber, Just how much do individual investors lose by trading](https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/justhowmuchdoindividualinvestorslose_rfs_2009.pdf)
- [Fong et al., Who wins and who loses among individual investors](https://www.uts.edu.au/globalassets/sites/default/files/PaperGallagherDavid.pdf)
- [IBKR Market-on-Close order page](https://interactivebrokers.co.uk/en/trading/orders/moc.php)
- [RSI(2) before and after publication (Empirica Lab, Substack)](https://empiricalab.substack.com/p/connors-rsi2-spy)
- Local: `reference/mmr/docs/RESEARCH_LOG.md`, `reference/mmr/docs/STRATEGY_EVALUATION.md`, `reference/ibkr-algo-trader/RESEARCH.md`
