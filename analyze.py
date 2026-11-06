"""Analyse the Duck Hunt database: SQL extracts, pandas metrics, charts and a Markdown report.

Usage: uv run python analyze.py path/to/duck_hunt.db [--min-intra-id 275000]
Writes report/README.md and report/*.png. No login ever leaves the SQL layer.
"""

import argparse
import sqlite3
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).parent
SQL = ROOT / "sql"
OUT = ROOT / "report"

INK, MUTED, GRID, BAR = "#1d2430", "#5b6573", "#e3e7ea", "#0f6e7a"
STEPS = [  # (column, label) in game order
    ("started", "Started"),
    ("riddle_done", "Riddle"),
    ("game_done", "Logic game"),
    ("exam_done", "C exam"),
    ("oral_done", "Oral"),
    ("memory_done", "Memory game"),
]


def query(con: sqlite3.Connection, name: str, **params) -> pd.DataFrame:
    return pd.read_sql_query((SQL / f"{name}.sql").read_text(), con, params=params)


def style(ax: plt.Axes) -> None:
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def funnel_chart(funnel: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=160)
    labels = funnel["trial"][::-1]
    values = funnel["players"][::-1]
    ax.barh(labels, values, color=BAR, height=0.62)
    start = funnel["players"].iloc[0]
    for y, v in enumerate(values):
        ax.text(v + 0.25, y, f"{v}  ({v / start:.0%})", va="center", color=INK, fontsize=9)
    style(ax)
    ax.set_xlim(0, start * 1.25)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.tick_params(axis="y", colors=INK)
    ax.set_title("Piscine players who cleared each trial", loc="left", color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def duration_chart(durations: pd.Series, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.0), dpi=160)
    ax.barh(durations.index[::-1], durations.values[::-1], color=BAR, height=0.62)
    for y, v in enumerate(durations.values[::-1]):
        ax.text(v + durations.max() * 0.02, y, f"{v:.0f} min", va="center", color=INK, fontsize=9)
    style(ax)
    ax.set_xlim(0, durations.max() * 1.2)
    ax.tick_params(axis="y", colors=INK)
    ax.set_title("Median minutes spent on each trial", loc="left", color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db", type=Path)
    parser.add_argument("--min-intra-id", type=int, default=275000,
                        help="intra ids created for this piscine start here")
    args = parser.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    p = {"min_intra_id": args.min_intra_id}
    players = query(con, "players", **p)
    funnel = query(con, "funnel", **p)
    stand = query(con, "stand")
    con.close()

    # Time spent on each trial = time between clearing the previous step and this one.
    minutes = pd.DataFrame(index=players.index)
    for (prev, _), (col, label) in zip(STEPS, STEPS[1:]):
        minutes[label] = (players[col] - players[prev]) / 60
    durations = minutes.median().dropna().round()
    total_h = ((players["finished"] - players["started"]) / 3600).dropna()

    funnel["% of starters"] = (funnel["players"] / funnel["players"].iloc[0] * 100).round().astype(int)
    funnel["lost at this step"] = (-funnel["players"].diff()).fillna(0).astype(int)
    hardest = funnel.iloc[1:].sort_values("lost at this step", ascending=False).iloc[0]
    attempts = players.loc[players["riddle_done"].notna(), "riddle_attempts"]

    OUT.mkdir(exist_ok=True)
    funnel_chart(funnel, OUT / "funnel.png")
    duration_chart(durations, OUT / "durations.png")

    n, done = len(players), int(players["finished"].notna().sum())
    report = f"""# Duck Hunt — what the data says

Escape game for the 42 Luxembourg piscine (October 2026). Data: production SQLite
database, read-only. Lifeguards and older students who tested the game are excluded;
players are anonymised in SQL (`sql/players.sql`).

## Key figures

- **{n} piscine players** started the hunt; **{done} finished it ({done / n:.0%})**.
- Biggest drop: **{hardest['trial']}**, where {hardest['lost at this step']} players stopped.
- Riddle: {attempts.mean():.1f} wrong answers on average before solving it (max {attempts.max()}).
- Finishers took a median of **{total_h.median():.0f} h** from login to the last trial
  (fastest {total_h.min():.0f} h).

## Funnel

![Funnel](funnel.png)

{funnel[['trial', 'players', '% of starters', 'lost at this step']].to_markdown(index=False)}

## Time per trial

![Durations](durations.png)

Median minutes between clearing the previous step and clearing this one
(includes waiting for a lifeguard for the oral).

## Student fair demo

{stand.to_markdown(index=False)}

## What I would change next piscine

- **{hardest['trial']}** is where players give up: add a hint or an easier first test there.
- The longest step is **{durations.idxmax()}** ({durations.max():.0f} min median): shorten it or split it.
"""
    (OUT / "README.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
