#!/usr/bin/env python3
"""Replicate manuscript Fig.2f from 2023 facility-level CSV data.

Figure content:
- Horizontal bars: country aerosol-related PV power loss (TWh, log scale)
- Top-axis bubbles: relative PV power loss percentage
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MAX_COUNTRY_NAME_LENGTH = 14
STOPWORDS = {"of", "and", "the"}
CUSTOM_LABELS = {"United Kingdom": "UK"}
BAR_COLOR = "#ffa74f"
BAR_HEIGHT = 0.55


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _find_column(df: pd.DataFrame, aliases: Iterable[str]) -> str:
    normalized = {_normalize(c): c for c in df.columns}
    for alias in aliases:
        key = _normalize(alias)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Could not find any of columns: {list(aliases)}")


def format_country_name(name: str) -> str:
    """Return country name or acronym if label would be too long."""
    if name in CUSTOM_LABELS:
        return CUSTOM_LABELS[name]
    if len(name) <= MAX_COUNTRY_NAME_LENGTH:
        return name
    tokens = [token for token in re.split(r"[^A-Za-z]+", name) if token]
    acronym = "".join(token[0].upper() for token in tokens if token.lower() not in STOPWORDS)
    return acronym or name


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Replicate Fig.2f country aerosol-loss plot from 2023 CSV data."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=repo_root / "data" / "pv_generation_losses" / "PV_facility_generation_year_2023.csv",
        help="Input 2023 facility-level CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "outputs" / "figures",
        help="Output directory for figure files.",
    )
    parser.add_argument(
        "--table-dir",
        type=Path,
        default=repo_root / "outputs" / "tables",
        help="Output directory for summary tables.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=30,
        help="Number of countries to show.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=1200,
        help="PNG export DPI.",
    )
    return parser.parse_args()


def _safe_share(series: pd.Series, total: float, key: str) -> tuple[float, float]:
    value = float(series.get(key, np.nan))
    ratio = value / total if np.isfinite(value) and total != 0 else np.nan
    return value, ratio


def main() -> None:
    args = parse_args()
    if not args.input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {args.input_csv}")

    # Prefer manuscript style while keeping a safe fallback on systems without Helvetica.
    plt.rcParams["font.family"] = ["Helvetica", "Arial", "DejaVu Sans"]

    df = pd.read_csv(args.input_csv)
    country_col = _find_column(df, ["country"])
    aerosol_col = _find_column(df, ["aerosol_loss (kWh)", "aerosol_loss (KWh)", "aerosol_loss"])
    poa_col = _find_column(df, ["power_POA (kWh)", "power_POA (KWh)", "power_POA"])
    poa_clean_col = _find_column(
        df, ["power_POA_cln (kWh)", "power_POA_cln (KWh)", "power_POA_cln"]
    )

    country_stats = (
        df.groupby(country_col)
        .agg(
            aerosol_loss_kwh=(aerosol_col, "sum"),
            power_poa_kwh=(poa_col, "sum"),
            power_poa_cln_kwh=(poa_clean_col, "sum"),
        )
        .reset_index()
        .rename(columns={country_col: "country"})
    )
    country_stats["aerosol_loss_twh"] = country_stats["aerosol_loss_kwh"] / 1e9
    country_stats["clean_gain_ratio"] = (
        country_stats["power_poa_cln_kwh"] - country_stats["power_poa_kwh"]
    ) / country_stats["power_poa_kwh"].replace(0, np.nan)
    country_stats["clean_gain_ratio"] = country_stats["clean_gain_ratio"].fillna(0.0)

    top_countries = country_stats.sort_values("aerosol_loss_twh", ascending=False).head(args.top_n)
    gain_percent = (top_countries["clean_gain_ratio"].to_numpy(dtype=float)) * 100.0
    formatted_names = top_countries["country"].apply(format_country_name).tolist()
    indices = np.arange(len(top_countries))

    fig, ax = plt.subplots(figsize=(8, 22))
    ax.barh(
        indices,
        top_countries["aerosol_loss_twh"],
        color=BAR_COLOR,
        height=BAR_HEIGHT,
        edgecolor="black",
        linewidth=0.8,
    )
    max_loss = float(top_countries["aerosol_loss_twh"].max())
    xmax_limit = max(120.0, max_loss * 1.2)

    ax.set_xlabel("PV Power Loss (TWh)", fontsize=28)
    ax.invert_yaxis()
    ax.tick_params(axis="x", which="both", direction="in", length=8, width=2, labelsize=28)
    ax.set_yticks(indices)
    ax.set_yticklabels(formatted_names, fontsize=28)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_xscale("log")
    ax.set_xlim([0.1, xmax_limit])
    ax.set_ylim(len(top_countries), -1.0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax_top = ax.twiny()
    percent_span = max(5.0, float(gain_percent.max() - gain_percent.min()))
    buffer = percent_span * 0.08
    ax_top.set_xlim(float(gain_percent.min() - buffer), float(gain_percent.max() + buffer))
    ax_top.set_xlabel("PV Power Loss [%]", fontsize=28, labelpad=18)
    ax_top.tick_params(axis="x", which="both", direction="in", length=8, width=2, labelsize=24, pad=10)
    ax_top.spines["bottom"].set_visible(False)
    ax_top.spines["right"].set_visible(False)
    ax_top.spines["left"].set_visible(False)

    line_start = ax_top.get_xlim()[0]
    for idx, pct in zip(indices, gain_percent):
        ax_top.hlines(
            idx,
            xmin=line_start,
            xmax=float(pct),
            colors="#4991c2",
            linestyles="-",
            linewidth=0.8,
            zorder=0,
        )

    bubble_sizes = np.full_like(gain_percent, 450.0, dtype=float)
    ax_top.scatter(
        gain_percent,
        indices,
        s=bubble_sizes,
        color="#4991c2",
        alpha=0.7,
        edgecolor="black",
        linewidth=0.5,
    )

    offset = percent_span * 0.04
    for ratio_percent, idx in zip(gain_percent, indices):
        ax_top.text(
            float(ratio_percent + offset),
            int(idx),
            f"{ratio_percent:.1f}%",
            va="center",
            ha="left",
            fontsize=18,
            color="#0b1f2a",
        )

    fig.tight_layout()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.table_dir.mkdir(parents=True, exist_ok=True)

    png_path = args.output_dir / "country_aerosol_loss_bar_revise.png"
    pdf_path = args.output_dir / "country_aerosol_loss_bar_revise.pdf"
    top_table_path = args.table_dir / "country_aerosol_loss_top30_2023.csv"
    country_stats_path = args.table_dir / "country_aerosol_loss_all_2023.csv"

    fig.savefig(png_path, dpi=args.dpi, bbox_inches="tight")
    fig.savefig(pdf_path, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)

    top_countries.to_csv(top_table_path, index=False)
    country_stats.sort_values("aerosol_loss_twh", ascending=False).to_csv(country_stats_path, index=False)

    total_aerosol_loss_twh = float(country_stats["aerosol_loss_twh"].sum())
    by_country_loss = country_stats.set_index("country")["aerosol_loss_twh"]

    china_loss, china_ratio = _safe_share(by_country_loss, total_aerosol_loss_twh, "China")
    india_loss, india_ratio = _safe_share(by_country_loss, total_aerosol_loss_twh, "India")
    usa_loss, usa_ratio = _safe_share(
        by_country_loss, total_aerosol_loss_twh, "United States of America"
    )

    total_generation_twh = float(pd.to_numeric(df[poa_col], errors="coerce").sum() / 1e9)
    by_country_generation = (
        df.groupby(country_col)[poa_col].sum() / 1e9
    )
    china_gen, china_gen_ratio = _safe_share(by_country_generation, total_generation_twh, "China")
    india_gen, india_gen_ratio = _safe_share(by_country_generation, total_generation_twh, "India")
    usa_gen, _ = _safe_share(by_country_generation, total_generation_twh, "United States of America")

    print(f"Saved figure PNG: {png_path}")
    print(f"Saved figure PDF: {pdf_path}")
    print(f"Saved top-country table: {top_table_path}")
    print(f"Saved all-country table: {country_stats_path}")
    print()
    print(f"China contributes {china_ratio:.2%} of total aerosol loss ({china_loss:.2f} TWh)")
    print(f"India contributes {india_ratio:.2%} of total aerosol loss ({india_loss:.2f} TWh)")
    print(f"USA contributes {usa_ratio:.2%} of total aerosol loss ({usa_loss:.2f} TWh)")
    print(f"China contributes {china_gen_ratio:.2%} of total solar generation ({china_gen:.2f} TWh)")
    print(f"India contributes {india_gen_ratio:.2%} of total solar generation ({india_gen:.2f} TWh)")
    print(f"USA generation: {usa_gen:.2f} TWh")


if __name__ == "__main__":
    main()
