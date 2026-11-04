# Tempo docs

| Document | What it is |
|---|---|
| [ibkr-gotchas.md](ibkr-gotchas.md) | IBKR error codes and behaviours we hit, with the fix for each. Read before debugging. |
| [market-hours.md](market-hours.md) | When US markets, overnight and forex are open, plus the rest of 2026's holidays. |
| [foundations-plan.md](foundations-plan.md) | The five-phase plan for solid foundations: order choke point, stop button, reconcile, brackets, evidence harness. |
| [research/log.md](research/log.md) | Dated findings with numbers, append-only, corrections written underneath. |
| [research/reference-audit.md](research/reference-audit.md) | What we took and skipped from each reference repo. |
| [research/swing-trading-research.md](research/swing-trading-research.md) | Deep research on swing trading: every idea, the evidence for and against, costs, and the ranked test queue. Claims tagged by source quality. |
| [research/what-people-do.md](research/what-people-do.md) | What people actually run (tactical allocation, trend, options income, insider and LLM signals, prop firms), with what survives scrutiny. Claims tagged by source quality. |
| [runbook.md](runbook.md) | How to operate everything day to day, the first live run of the paper runner, what to do when something fails, and the rules that must not be bent. |
| [plan-to-friday.md](plan-to-friday.md) | The code-quality plan for the days the Gateway is unavailable, with what is done. |
| [roadmap.md](roadmap.md) | What's built, what's next, and the gate before any real money. |
| [research/resources.md](research/resources.md) | Repos, books, courses, papers and reality checks, with what to read first. |
| [research/youtube-transcripts-analysis.md](research/youtube-transcripts-analysis.md) | What we learned from 14 YouTube videos and which claims to doubt. |
| [research/notes-claude-ibkr-trading-bot-video.md](research/notes-claude-ibkr-trading-bot-video.md) | Notes on the first video you sent (Claude + IBKR bot). |
| [research/transcripts/](research/transcripts/) | Raw transcripts (auto-generated), numbered 00 to 13. |

Pre-registered strategy tests live in `../evidence/*.json` (rules and pass criteria, written before any result) and run with `python -m tempo.<name>_report`; results are in [research/log.md](research/log.md).

Reference repos cloned for reading live **outside** this repo, in `Trading/reference/`. They are untrusted code: read, don't run.
