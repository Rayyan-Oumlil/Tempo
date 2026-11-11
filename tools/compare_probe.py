"""Read-only comparison probe. No order functions are called; placeOrder is blocked. Prints no account ids."""
import sys, time
from ib_async import IB, Stock

PORT = int(sys.argv[1])
STRICT = "--strict" in sys.argv   # strict: no real-time quote request at all (delayed only), no history/contract lookups

def refuse(*a, **k): raise RuntimeError("no orders")

def new_ib(cid):
    ib = IB(); ib.placeOrder = refuse; ib.cancelOrder = refuse; ib.reqGlobalCancel = refuse
    errs = []
    ib.errorEvent += lambda reqId, code, msg, c=None: errs.append(code)
    ib.connect("127.0.0.1", PORT, clientId=cid, timeout=20, readonly=True)
    return ib, errs

known = lambda v: v == v and abs(v) < 1e300

ib, errs = new_ib(85)
print("== account")
vals = ib.accountValues()
print("  base-currency entries for NetLiquidation:", sorted({v.currency for v in vals if v.tag == "NetLiquidation"}))
print("  DayTradesRemaining:", next((v.value for v in vals if v.tag == "DayTradesRemaining"), "n/a"))
print("  AccountType:", next((v.value for v in vals if v.tag == "AccountType"), "n/a"))

print("== market data (SPY, streaming 4s, real-time requested first)")
spy = Stock("SPY", "SMART", "USD"); ib.qualifyContracts(spy)
for mdt, label in (((3, "delayed"),) if STRICT else ((1, "real-time"), (3, "delayed"))):
    errs.clear(); ib.reqMarketDataType(mdt)
    t = ib.reqMktData(spy, "", False, False); ib.sleep(4)
    got = {"type": t.marketDataType, "last": t.last if known(t.last) else None, "bid": t.bid if known(t.bid) else None,
           "ask": t.ask if known(t.ask) else None, "delayedLast": getattr(t, "delayedLast", None) if known(getattr(t, "delayedLast", float("nan"))) else None}
    print(f"  asked {label}: got marketDataType={got['type']} last={got['last']} bid={got['bid']} ask={got['ask']} delayedLast={got['delayedLast']} errors={sorted(set(errs))}")
    ib.cancelMktData(spy)

print("== contracts / history")
for sym in (() if STRICT else ("LBTY", "TRAD", "TRTX", "SPY")):
    errs.clear()
    c = Stock(sym, "SMART", "USD")
    det = ib.reqContractDetails(c)
    bars = []
    if det:
        bars = ib.reqHistoricalData(det[0].contract, "", "5 D", "1 day", "TRADES", useRTH=True, formatDate=1)
    print(f"  {sym:<5} contract details: {len(det)} | daily bars: {len(bars)} | errors={sorted(set(errs))}")
ib.disconnect(); time.sleep(2)

print("== P&L: time to first answer on a fresh connection (cap 30s)")
for i in range(3):
    ib, _ = new_ib(85)
    acct = ib.managedAccounts()[0]
    t0 = time.time(); p = ib.reqPnL(acct)
    while time.time() - t0 < 30 and not known(p.dailyPnL): ib.sleep(0.1)
    print(f"  try {i+1}: " + (f"answered in {time.time()-t0:.1f}s" if known(p.dailyPnL) else "NO ANSWER in 30s"))
    ib.cancelPnL(acct); ib.disconnect(); time.sleep(2)
