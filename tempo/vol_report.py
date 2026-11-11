"""Is there a volatility premium in SPY and QQQ, from IBKR's own free series saved by tempo.option_snapshot?

Usage: python -m tempo.vol_report

Premium on day t = implied volatility on t (30-day) minus the historical volatility measured 21 trading days later, i.e.
what the option market charged for the next month minus what the stock then actually did. Positive on average means sellers
of volatility were paid. This is DESCRIPTIVE: it ignores option bid-ask costs, margin and crashes (negative skew), so it
says whether a premium exists, not whether a strategy would have made money. Nothing here is traded.
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERIES = ROOT / "data" / "snapshots" / "vol_series"
LAG = 21


def read_series(path: Path) -> dict[str, float]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "date,value":
        raise ValueError(f"{path}: unexpected header")
    return {d: float(v) for d, v in (ln.split(",") for ln in lines[1:] if ln.strip())}


def premiums(iv: dict[str, float], hv: dict[str, float], lag: int = LAG) -> list[tuple[str, float]]:
    """(date, IV(date) - HV(lag trading days later)) for every date where both exist, oldest first."""
    hv_dates = sorted(hv)
    out = []
    for i, d in enumerate(hv_dates):
        if d in iv and i + lag < len(hv_dates):
            out.append((d, iv[d] - hv[hv_dates[i + lag]]))
    return out


def summarize(pairs: list[tuple[str, float]]) -> dict[str, float]:
    values = [v for _, v in pairs]
    if len(values) < 30:
        return {"n": float(len(values))}
    return {"n": float(len(values)), "mean": statistics.fmean(values), "median": statistics.median(values),
            "share_positive": sum(v > 0 for v in values) / len(values), "worst": min(values), "best": max(values)}


def main() -> int:  # pragma: no cover - entry point
    for name in ("SPY", "QQQ"):
        iv, hv = read_series(SERIES / f"{name}_IV.csv"), read_series(SERIES / f"{name}_HV.csv")
        s = summarize(premiums(iv, hv))
        if "mean" not in s:
            print(f"{name}: too few overlapping days ({int(s['n'])})")
            continue
        print(f"{name}: {int(s['n'])} days, mean premium {s['mean']:+.1%} vol points, median {s['median']:+.1%}, "
              f"IV above later realised vol on {s['share_positive']:.0%} of days, worst {s['worst']:+.1%}, best {s['best']:+.1%}; "
              f"latest IV {iv[max(iv)]:.1%}, latest HV {hv[max(hv)]:.1%}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
