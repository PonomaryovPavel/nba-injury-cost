"""Построение графиков. Только статика — GitHub не рендерит интерактивные выводы."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e3e2de"
STRUCTURAL = "#2a78d6"   # категориальный слот 1
SOFT_TISSUE = "#eb6834"  # категориальный слот 2

# Структурное повреждение = нарушена целостность ткани (разрыв, перелом).
# Остальное — перегрузка, ушибы, растяжения без разрыва.
STRUCTURAL_LABELS = {
    "Разрыв ахиллова сухожилия",
    "Разрыв ПКС (ACL)",
    "Разрыв мениска",
    "Разрыв связок колена (MCL/PCL)",
    "Перелом",
}

mpl.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.labelcolor": INK_SOFT,
    "xtick.color": INK_SOFT,
    "ytick.color": INK_SOFT,
    "axes.edgecolor": GRID,
    "axes.linewidth": 0.8,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
})


def _header(fig, title, subtitle, source, top=0.90, title_size=15):
    """Единая шапка: заголовок и подзаголовок по левому краю, источник внизу."""
    fig.text(0.012, 0.975, title, ha="left", va="top",
             fontsize=title_size, fontweight="bold", color=INK)
    fig.text(0.012, 0.925, subtitle, ha="left", va="top",
             fontsize=9.5, color=INK_SOFT, linespacing=1.45)
    fig.text(0.012, 0.012, source, ha="left", va="bottom",
             fontsize=8.5, color=INK_SOFT)
    fig.subplots_adjust(top=top)


def _times(n: float) -> str:
    """«в 5 раз» / «в 2 раза» — русская форма слова после числительного."""
    n = int(round(n))
    tail = n % 10
    if n % 100 in range(11, 15) or tail in (0, 1, 5, 6, 7, 8, 9):
        return f"в {n} раз"
    return f"в {n} раза"


def _strip(ax, xgrid=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)


def median_by_injury(table: pd.DataFrame, out: Path, overall_median: float,
                     n_episodes: int) -> Path:
    """Главный график: медиана пропущенных игровых дней по типу травмы."""
    t = table.sort_values("median")
    top_label = t.index[-1]
    top_value = t["median"].iloc[-1]
    colors = [STRUCTURAL if i in STRUCTURAL_LABELS else SOFT_TISSUE for i in t.index]

    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=200)
    ax.barh(t.index, t["median"], height=0.68, color=colors)

    for y, (value, n) in enumerate(zip(t["median"], t["n"])):
        ax.text(value + 3, y, f"{value:.0f}  (n={n})", va="center",
                fontsize=9, color=INK_SOFT)

    _strip(ax)
    ax.set_xlim(0, t["median"].max() * 1.22)
    ax.set_xlabel("Медиана пропущенных игровых дней", fontsize=10, labelpad=10)
    ax.tick_params(axis="y", labelsize=10)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=STRUCTURAL),
        plt.Rectangle((0, 0), 1, 1, color=SOFT_TISSUE),
    ]
    ax.legend(handles, ["Структурное повреждение", "Мягкие ткани и перегрузка"],
              loc="lower right", frameon=False, fontsize=9.5)

    fig.tight_layout()
    _header(fig,
            f"{top_label}: {top_value:.0f} игровых дней. "
            f"Медианная травма — {overall_median:.0f}",
            "NBA, сезоны 2010/11 – 2019/20. Учтено только время активного сезона,\n"
            "межсезонье из подсчёта исключено. Категории от 20 эпизодов.",
            f"Данные: Pro Sports Transactions  ·  {n_episodes:,} эпизодов отсутствия"
            .replace(",", " "),
            top=0.885)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return out


def spread_median_p90(table: pd.DataFrame, out: Path) -> Path:
    """Разброс внутри диагноза: медиана против 90-го перцентиля."""
    t = table.sort_values("median")
    fx_med = table.loc["Перелом", "median"]
    fx_p90 = table.loc["Перелом", "p90"]

    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=200)
    for y, (_, row) in enumerate(t.iterrows()):
        ax.plot([row["median"], row["p90"]], [y, y], color=GRID, linewidth=2.5,
                solid_capstyle="round", zorder=1)
    ax.scatter(t["median"], range(len(t)), s=62, color=STRUCTURAL, zorder=3,
               edgecolor=SURFACE, linewidth=1.6, label="Медиана")
    ax.scatter(t["p90"], range(len(t)), s=62, color=SOFT_TISSUE, zorder=3,
               edgecolor=SURFACE, linewidth=1.6, label="90-й перцентиль")

    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(t.index, fontsize=10)
    _strip(ax)
    ax.set_xlim(-8, t["p90"].max() * 1.1)
    ax.set_xlabel("Пропущенные игровые дни", fontsize=10, labelpad=10)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5)

    fig.tight_layout()
    _header(fig,
            "Один и тот же диагноз — совершенно разный исход",
            f"Каждый десятый перелом держит игрока вне игры {fx_p90:.0f} дней — "
            f"{_times(fx_p90 / fx_med)} дольше\nмедианного перелома "
            f"({fx_med:.0f}). Средним значением такие травмы не описываются.",
            "Данные: Pro Sports Transactions, NBA 2010–2020",
            top=0.885)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return out


def duration_distribution(episodes: pd.DataFrame, out: Path) -> Path:
    """Форма распределения: короткие пропуски плюс длинный хвост."""
    days = episodes.loc[episodes.injury.notna() & episodes.is_injury, "days"]
    days = days[days > 0]

    share_long = (days > 90).mean() * 100

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    ax.hist(days, bins=60, color=STRUCTURAL, log=True)

    median = days.median()
    ax.axvline(median, color=SOFT_TISSUE, linewidth=2)
    ax.text(median + 8, ax.get_ylim()[1] * 0.42,
            f"медиана\n{median:.0f} дней", color=SOFT_TISSUE,
            fontsize=10, fontweight="bold", va="top")

    _strip(ax, xgrid=False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Пропущенные игровые дни", fontsize=10, labelpad=10)
    ax.set_ylabel("Число эпизодов (лог. шкала)", fontsize=10, labelpad=10)

    fig.tight_layout()
    _header(fig,
            "Большинство травм — это неделя. Проблему создаёт хвост",
            f"{share_long:.0f}% эпизодов длятся дольше 90 дней "
            f"и дают основную часть потерь лиги.",
            "Данные: Pro Sports Transactions, NBA 2010–2020",
            top=0.825)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return out
