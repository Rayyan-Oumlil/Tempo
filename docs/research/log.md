# Research log

Append-only. Add new dated entries at the bottom. If an earlier entry turns out wrong, write the correction **underneath it** and leave the original: the reasoning that produced a wrong answer is usually the more useful record.

## 2026-11-02: costs, fees and the first probe

- **Commission is real, in USD, and depends on size.** BUY is 0.005 USD per share with a 1.00 minimum; SELL adds about 0.0157 USD per share at a price near 760 (about 20.6 USD per million sold; likely the SEC fee, inferred). Measured with 1, 10, 100 and 300 share orders. A 300-share round trip cost 7.70 USD.
- **No visible CAD-to-USD markup.** A 300-share round trip's CAD cash change was -18.09 against a net of -12.95 USD at USD.CAD 1.3967 (implied 1.3970). Paper account only; a real account may charge for conversion or interest on a USD debit.
- **Correction (same day):** I first reported market-order latency of about 50 ms. That was wrong. Without an explicit `tif`, ib_async briefly marks the order `Cancelled` (error 10349 notice), so `isDone()` was true before the fill. All Tempo orders now set `tif`.
- **Correction (same day):** I first told the user the day's loss was "a few dollars". After the probes it was 74.70 CAD (about 53 USD), all commissions and spread across about 40 one-to-300 share round trips.
- **Bracket probe:** cancelling the take-profit leg of an OCA pair cancelled the stop too and left the position unprotected. Tempo's bracket tool therefore never cancels one leg.

## 2026-11-02: evidence harness, first run (SPY, 2006-11-07 to 2026-11-02, 19.9 years)

Setup: signal at close t, fill at close t+1; costs 0.005 USD per share (min 1.00), sell fee 20.6 per million, slippage 1 bp (assumed). ADJUSTED_LAST daily bars. One variant tried (SMA window 200, fixed up front by convention, not tuned): **variants tried = 1**.

| Strategy | Total | CAGR | Sharpe | Max drawdown | Orders | Costs (USD) |
|---|---|---|---|---|---|---|
| Flat | 0% | 0% | 0.00 | 0% | 0 | 0 |
| Buy and hold | 679.8% | 10.8% | 0.63 | -55.4% | 1 | 15 |
| SMA 200 trend | 359.6% | 7.9% | 0.72 | -23.6% | 107 | 2,666 |

Negative control (200 shuffled-order versions of the same daily returns): real SMA Sharpe 0.72, shuffled mean 0.47, shuffled best 0.76; the real run beats 99% of shuffles.

**What this does and does not say**
- The trend rule earned **less** than buy and hold (7.9% against 10.8% a year) with a **smaller** drawdown (-23.6% against -55.4%) and a slightly higher Sharpe. It does not beat the market; it trades return for lower risk, a well-known property of trend rules.
- Costs were 2,666 USD on 107 orders against 15 USD for one order, so costs matter for anything that trades often.
- Beating 99% of shuffles is **not** evidence of an edge. Shuffling also removes volatility clustering, and a trend rule benefits from avoiding the big crashes without predicting anything. The gate asks for 95+ as a necessary check, not a sufficient one.
- This is one instrument over one history. Nothing here is a reason to trade money. The harness exists so the next idea is judged by the same rules before it is believed.
