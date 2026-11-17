"""One command for the fast-track history verdicts (Workstream F): python -m tempo.history_report [plan]

Reads only local files: daily bars with an open price (data/history/shortvol/bars and data/history/fast/bars), SPY
(data/SPY_ohlc.csv) and the SEC Form sets (data/insider_sets). Prints one verdict per source under protocol rule 7 and saves
data/history/fast_track_report.json. `plan` lists the symbols whose bars are still missing (fetch them with tempo.history_fetch).
Everything here is deterministic: the same files give the same table.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from tempo import history_insider as hi
from tempo import history_reversal as hr
from tempo.history_core import Series, Verdict, judge, load_series
from tempo.insider_history import build_index

DATA = Path(__file__).resolve().parents[1] / "data"
SHORTVOL_BARS = DATA / "history" / "shortvol" / "bars"
FAST_BARS = DATA / "history" / "fast" / "bars"
SETS_DIR = DATA / "insider_sets"
SPY_FILE = DATA / "SPY_ohlc.csv"
REPORT = DATA / "history" / "fast_track_report.json"
FIRST_TEST_ENTRY = "2023-01-02"
BUY_QUARTERS = ["2022q4"] + [f"{y}q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]
INDEX_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def load_spy(path: Path = SPY_FILE) -> Series:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return Series([r["date"] for r in rows], [float(r["open"]) for r in rows], [float(r["close"]) for r in rows], [0.0] * len(rows))


def read_set(quarter: str, sets_dir: Path = SETS_DIR) -> bytes:
    p = sets_dir / f"{quarter}_form345.zip"
    if not p.exists():
        raise SystemExit(f"missing {p}: fetch the Form sets first (python -m tempo.history_fetch sets)")
    return p.read_bytes()


def make_bar_lookup(*dirs: Path):
    cache: dict[str, Series | None] = {}

    def get(symbol: str) -> Series | None:
        if symbol not in cache:
            cache[symbol] = next((s for d in dirs if (s := load_series(d / f"{symbol}.csv")) is not None), None)
        return cache[symbol]
    return get


def load_universe(bars_dir: Path = SHORTVOL_BARS) -> dict[str, Series]:
    out = {}
    for p in sorted(bars_dir.glob("*.csv")):
        s = load_series(p)
        if s is not None and p.stem != "SPY":
            out[p.stem] = s
    return out


def insider_inputs(spy: Series):
    buys = [b for q in BUY_QUARTERS for b in hi.buys_from_zip(read_set(q))]
    index = build_index(INDEX_YEARS, read_set)
    return hi.signals(buys, index, spy.dates, FIRST_TEST_ENTRY), len(buys)


def missing_symbols(sigs: dict[str, list[tuple[str, str]]], bars) -> list[str]:
    return sorted({sym for rows in sigs.values() for _, sym in rows if bars(sym) is None})


def render(results: dict[str, tuple[Verdict, Counter, float]]) -> str:
    lines = ["FAST-TRACK HISTORY VERDICTS (protocol rule 7; test years 2023-2025; 5-session horizon; net of the registered cost)", ""]
    for source, (v, counts, cost) in results.items():
        lines.append(f"{source}  cost {cost:.2%}   signals: {dict(counts)}")
        if v.mean_net is None or v.ci is None or v.mean_net_stress is None:
            lines.append(f"   events {v.events}  days {v.days}   {v.decision}: {'; '.join(v.reasons)}")
        else:
            t = f"{v.t:.2f}" if v.t is not None else "n/a"
            lines.append(f"   events {v.events}  days {v.days}  net mean {v.mean_net:+.2%} [{v.ci[0]:+.2%}, {v.ci[1]:+.2%}]  t {t}  "
                         f"at 1.5x cost {v.mean_net_stress:+.2%}")
            lines.append("   by year: " + "  ".join(f"{y} {m:+.2%} ({n})" for y, (n, m) in v.years.items()))
            lines.append(f"   => {v.decision}" + (": " + "; ".join(v.reasons) if v.reasons else ""))
        lines.append("")
    lines.append("Limits: today's constituents and still-listed issuers only (survivorship flatters long legs); pre-2023-04 Form sets cannot exclude")
    lines.append("10b5-1 trades; daily-bar approximation of the live 09:40 entry and 15:45 exit. FORWARD means 'worth a forward test', never real money.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:  # pragma: no cover - reads the local data
    spy = load_spy()
    fast = make_bar_lookup(FAST_BARS, SHORTVOL_BARS)
    sigs, n_buys = insider_inputs(spy)
    if argv[:1] == ["plan"]:
        missing = missing_symbols(sigs, fast)
        print(f"{n_buys} purchases rebuilt; insider signals: {({s: len(r) for s, r in sigs.items()})}")
        print(f"{len(missing)} symbols have no bars with an open price yet")
        FAST_BARS.parent.mkdir(parents=True, exist_ok=True)
        (FAST_BARS.parent.parent / "missing_symbols.json").write_text(json.dumps(missing), encoding="utf-8")
        return 0
    results: dict[str, tuple[Verdict, Counter, float]] = {}
    trades, counts = hr.reversal_trades(load_universe(), spy, FIRST_TEST_ENTRY)
    results[hr.SOURCE] = (judge(trades, hr.COST, hr.HORIZON), counts, hr.COST)
    for source, rows in sigs.items():
        trades, counts = hi.to_trades(rows, spy, fast)
        results[source] = (judge(trades, hi.SOURCES[source], hi.HORIZON), counts, hi.SOURCES[source])
    print(render(results))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({s: {"decision": v.decision, "reasons": list(v.reasons), "events": v.events, "days": v.days, "mean_net": v.mean_net,
                                      "ci": v.ci, "t": v.t, "years": v.years, "mean_net_stress": v.mean_net_stress, "signals": dict(c), "cost": cost}
                                  for s, (v, c, cost) in results.items()}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(sys.argv[1:]))
