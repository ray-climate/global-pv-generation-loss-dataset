#!/usr/bin/env python3
"""Plot aerosol loss compared with new PV generation (Global only).
Fig.2b in the manuscript

Uses yearly files:
  PV_facility_generation_year_YYYY.csv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _find_column(df: pd.DataFrame, aliases: Iterable[str]) -> str:
    normalized = {_normalize(c): c for c in df.columns}
    for alias in aliases:
        key = _normalize(alias)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Could not find any of columns: {list(aliases)}")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Global aerosol-loss vs new-generation plot from yearly facility CSV files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=repo_root / "data" / "pv_generation_losses",
        help="Directory containing PV_facility_generation_year_YYYY.csv files.",
    )
    parser.add_argument("--year-start", type=int, default=2017, help="Start year.")
    parser.add_argument("--year-end", type=int, default=2023, help="End year.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "outputs" / "figures",
        help="Output directory for figure files.",
    )
    parser.add_argument(
        "--error-fraction",
        type=float,
        default=0.10,
        help="Relative uncertainty used for visual error bars.",
    )
    parser.add_argument("--dpi", type=int, default=300, help="Figure DPI.")
    return parser.parse_args()


def _load_year_data(csv_path: Path) -> tuple[float, float]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing yearly file: {csv_path}")

    df = pd.read_csv(csv_path)
    poa_col = _find_column(df, ["power_POA (kWh)", "power_POA (KWh)", "power_POA"])
    poa_clean_col = _find_column(
        df, ["power_POA_cln (kWh)", "power_POA_cln (KWh)", "power_POA_cln"]
    )

    aerosol_col: str | None = None
    try:
        aerosol_col = _find_column(df, ["aerosol_loss (kWh)", "aerosol_loss (KWh)", "aerosol_loss"])
    except KeyError:
        aerosol_col = None

    total_poa_kwh = pd.to_numeric(df[poa_col], errors="coerce").sum()
    if aerosol_col is not None:
        aerosol_loss_kwh = pd.to_numeric(df[aerosol_col], errors="coerce").sum()
    else:
        aerosol_loss_kwh = (
            pd.to_numeric(df[poa_clean_col], errors="coerce")
            - pd.to_numeric(df[poa_col], errors="coerce")
        ).sum()

    return float(total_poa_kwh), float(aerosol_loss_kwh)


def _smooth_like_original(new_generation_twh: np.ndarray) -> np.ndarray:
    out = new_generation_twh.copy()
    for i in range(len(out)):
        if (i > 0) and (i < len(out) - 1):
            out[i] = (out[i] + out[i + 1]) / 2.0
    return out


def _build_ratio_cmap() -> mcolors.Colormap:
    blue_scale = mcolors.LinearSegmentedColormap.from_list(
        "aerosol_blue", ["#e7f4fb", "#2e92ce"]
    )
    orange_scale = mcolors.LinearSegmentedColormap.from_list(
        "aerosol_orange", ["#fbe9dd", "#cd6d2e"]
    )
    greens = blue_scale(np.linspace(1, 0.3, 128))
    oranges = orange_scale(np.linspace(0.3, 1, 128))
    split = 0.3
    green_positions = np.linspace(0, split, len(greens), endpoint=False)
    orange_positions = np.linspace(split, 1, len(oranges))
    color_list = list(zip(green_positions, greens)) + list(zip(orange_positions, oranges))
    return mcolors.LinearSegmentedColormap.from_list("custom_cmap", color_list)


def main() -> None:
    args = parse_args()
    years = np.arange(args.year_start, args.year_end + 1)

    total_generation_twh: list[float] = []
    aerosol_loss_twh: list[float] = []

    for year in years:
        yearly_file = args.input_dir / f"PV_facility_generation_year_{year}.csv"
        total_kwh, loss_kwh = _load_year_data(yearly_file)
        total_generation_twh.append(total_kwh / 1e9)
        aerosol_loss_twh.append(loss_kwh / 1e9)

    total_generation_twh_arr = np.asarray(total_generation_twh, dtype=float)
    aerosol_loss_twh_arr = np.asarray(aerosol_loss_twh, dtype=float)

    new_generation_twh = np.full_like(total_generation_twh_arr, np.nan)
    new_generation_twh[1:] = np.diff(total_generation_twh_arr)
    new_generation_twh = _smooth_like_original(new_generation_twh)

    ratios = aerosol_loss_twh_arr / new_generation_twh

    args.output_dir.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(14, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.03},
    )

    ax1.errorbar(
        years,
        new_generation_twh,
        yerr=np.abs(new_generation_twh) * args.error_fraction,
        fmt="-o",
        color="#e89875",
        markerfacecolor="#e89875",
        markeredgecolor="black",
        markeredgewidth=1.2,
        markersize=7,
        ecolor="black",
        capsize=4,
        lw=2.2,
        elinewidth=1.4,
    )
    ax1.plot(years, aerosol_loss_twh_arr, color="#66aad7", lw=2.2, zorder=1)
    ax1.errorbar(
        years,
        aerosol_loss_twh_arr,
        yerr=np.abs(aerosol_loss_twh_arr) * args.error_fraction,
        fmt="o",
        color="#66aad7",
        markerfacecolor="#66aad7",
        markeredgecolor="black",
        markeredgewidth=1.2,
        markersize=7,
        ecolor="black",
        capsize=4,
        elinewidth=1.4,
        zorder=2,
    )

    ax1.text(0.02, 0.92, "Global", transform=ax1.transAxes, fontsize=14)
    ax1.set_ylabel("PV power (TWh)", fontsize=13)
    ax1.tick_params(axis="y", labelsize=11)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(False)

    cmap = _build_ratio_cmap()
    norm = mcolors.Normalize(vmin=0, vmax=1.0)
    valid = np.isfinite(ratios)
    ax2.axhline(y=0.3, color="gray", linestyle="--", lw=1)
    ax2.bar(years[valid], ratios[valid], color=cmap(norm(ratios[valid])), width=0.3)
    ax2.set_ylabel("Ratio", fontsize=12)
    ax2.set_xlabel("Year", fontsize=12)
    ax2.set_ylim(0, 1.1)
    ax2.set_yticks([])
    ax2.tick_params(axis="x", labelsize=11)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.grid(False)

    for i, v in enumerate(ratios):
        if np.isfinite(v):
            ax2.text(years[i], min(v + 0.02, 1.06), f"{v:.2%}", ha="center", fontsize=9)

    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cax = fig.add_axes([ax2.get_position().x1 + 0.01, ax2.get_position().y0, 0.012, ax2.get_position().height])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_ticks([0, 0.3, 1.0])
    cbar.ax.tick_params(labelsize=9)

    png_path = args.output_dir / "aerosol_loss_vs_new_generation_global.png"
    pdf_path = args.output_dir / "aerosol_loss_vs_new_generation_global.pdf"
    fig.savefig(png_path, dpi=args.dpi, bbox_inches="tight")
    fig.savefig(pdf_path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved figure PNG: {png_path}")
    print(f"Saved figure PDF: {pdf_path}")


if __name__ == "__main__":
    main()
