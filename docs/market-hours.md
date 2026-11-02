# Market hours (Eastern Time)

Sources: IBKR overnight-trading disclosure and news ([IBKR](https://www.interactivebrokers.com/en/trading/etf-overnight-trading.php), [Finance Magnates](https://www.financemagnates.com/forex/interactive-brokers-brings-overnight-trading-to-10k-us-stocks-and-efts/amp/)); holidays from [Kiplinger](https://www.kiplinger.com/investing/stock-market-holidays) and [Fidelity](https://www.fidelity.com/learning-center/smart-money/stock-market-holidays). Check the NYSE calendar before relying on dates. The 04:00 pre-market start is not stated on an IBKR page I could read.

## A normal week (US stocks and ETFs through IBKR)

| Time (ET) | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
|---|---|---|---|---|---|---|---|
| 00:00 to 03:50 | closed | overnight | overnight | overnight | overnight | overnight | closed |
| 03:50 to 04:00 | closed | break | break | break | break | break | closed |
| 04:00 to 09:30 | closed | pre-market | pre-market | pre-market | pre-market | pre-market | closed |
| **09:30 to 16:00** | closed | **regular** | **regular** | **regular** | **regular** | **regular** | closed |
| 16:00 to 20:00 | closed | after-hours | after-hours | after-hours | after-hours | after-hours | closed |
| 20:00 to 24:00 | overnight | overnight | overnight | overnight | overnight | closed | closed |

- **Overnight session:** five nightly sessions, Sunday 20:00 to Friday 03:50, on IBKR's own venue. No Friday-night or Saturday session ("24/6").
- **Rules:** overnight is limit orders only (market orders get error 387). Outside regular hours, use a limit order with `outsideRth=True`. Liquidity is thin, and in our paper test a sell never filled. See [ibkr-gotchas.md](ibkr-gotchas.md).
- **Forex (USD.CAD):** roughly Sunday 17:00 to Friday 17:00 ET (from memory, not verified).
- **TSX:** 09:30 to 16:00 ET, but IBKR may block API orders on Canadian-listed stocks for Canadian residents (per an old note).
- **Gateway:** logs out at 23:45 by default; set Auto restart in Configure, Lock and Exit for overnight work.

## Holidays left in 2026

```
        November 2026                      December 2026
 Su  Mo  Tu  We  Th  Fr  Sa         Su  Mo  Tu  We  Th  Fr  Sa
  1   2   3   4   5   6   7                  1   2   3   4   5
  8   9  10  11  12  13  14          6   7   8   9  10  11  12
 15  16  17  18  19  20  21         13  14  15  16  17  18  19
 22  23  24  25 [26X][27E] 28        20  21  22  23 [24E][25X] 26
 29  30                              27  28  29  30  31

 X = closed all day         E = early close at 13:00
```

| Date | What happens |
|---|---|
| Thu Nov 26 | Closed (Thanksgiving) |
| Fri Nov 27 | Closes at 13:00 |
| Thu Dec 24 | Closes at 13:00 |
| Fri Dec 25 | Closed (Christmas) |
| Fri Jan 1, 2027 | Expected closed (not checked) |

Behaviour of pre-market, after-hours and overnight on holidays is unknown.
