#!/usr/bin/env python3
"""Interpret the global PV facility inventory Parquet dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]

    # Local test example (commented out for shared code):
    # default_input = repo_root / "data" / "global_pv_facility_inventory.parquet"

    # Shared-code default: load directly from Zenodo.
    default_input = (
        "https://zenodo.org/records/18794231/files/"
        "global_pv_facility_inventory.parquet?download=1"
    )

    parser = argparse.ArgumentParser(
        description="Interpret global_pv_facility_inventory.parquet from local file or Zenodo."
    )
    parser.add_argument(
        "--input-parquet",
        default=default_input,
        help="Local parquet path or Zenodo URL.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=15,
        help="Top N countries by facility count.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "outputs" / "tables",
        help="Directory for output summary CSV files.",
    )
    parser.add_argument(
        "--output-figure",
        type=Path,
        default=repo_root / "outputs" / "figures" / "parquet_inventory_summary.png",
        help="Output figure path (country ranking + installation years).",
    )
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save summary CSV outputs and summary figure.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Read only tabular columns so this runs with pandas + pyarrow (no geopandas needed).
    cols = ["PV_ID", "latitude", "longitude", "country", "year", "area_m2"]
    df = pd.read_parquet(args.input_parquet, columns=cols)

    required = set(cols)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")

    print("=== Parquet Inventory Overview ===")
    print(f"Source: {args.input_parquet}")
    print(f"Rows: {len(df):,}")
    print(f"Unique facilities: {df['PV_ID'].nunique():,}")
    print(f"Countries: {df['country'].nunique():,}")
    print(f"Year range: {int(df['year'].min())} to {int(df['year'].max())}")
    print(f"Total area (m2): {df['area_m2'].sum():,.2f}")
    print()

    by_country = (
        df.groupby("country", as_index=False)
        .agg(facility_count=("PV_ID", "count"), total_area_m2=("area_m2", "sum"))
        .sort_values("facility_count", ascending=False)
    )
    by_year = (
        df.groupby("year", as_index=False)
        .agg(facility_count=("PV_ID", "count"), total_area_m2=("area_m2", "sum"))
        .sort_values("year")
    )

    print(f"=== Top {args.top_n} Countries ===")
    print(by_country.head(args.top_n).to_string(index=False))
    print()
    print("=== Facilities by Year ===")
    print(by_year.to_string(index=False))

    if args.save_output:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        args.output_figure.parent.mkdir(parents=True, exist_ok=True)
        by_country.to_csv(args.output_dir / "parquet_inventory_by_country.csv", index=False)
        by_year.to_csv(args.output_dir / "parquet_inventory_by_year.csv", index=False)

        top = by_country.head(args.top_n).copy()
        top = top.iloc[::-1]  # plot largest at top
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))

        axes[0].barh(top["country"], top["facility_count"])
        axes[0].set_title(f"Top {args.top_n} Countries by Facility Count")
        axes[0].set_xlabel("Facility count")

        axes[1].plot(by_year["year"], by_year["facility_count"], marker="o")
        axes[1].set_title("Facilities by Installation Year")
        axes[1].set_xlabel("Installation year")
        axes[1].set_ylabel("Facility count")
        axes[1].grid(alpha=0.3)

        fig.tight_layout()
        fig.savefig(args.output_figure, dpi=200)
        plt.close(fig)

        print(f"\nSaved output tables to: {args.output_dir}")
        print(f"Saved output figure: {args.output_figure}")


if __name__ == "__main__":
    main()
