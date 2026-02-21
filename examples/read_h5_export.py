#!/usr/bin/env python3
"""
Example script for reading and exploring BMEX HDF5 exports

This script demonstrates how to:
1. Open and explore an HDF5 file exported from BMEX
2. Read metadata and attributes
3. Extract numerical data
4. Create basic visualizations

Usage:
    python read_h5_export.py <path_to_data.h5>
"""

import h5py
import numpy as np
import sys


def print_separator(char='=', length=70):
    """Print a separator line"""
    print(char * length)


def explore_structure(h5_file):
    """Print the structure of the HDF5 file"""
    print_separator()
    print("HDF5 FILE STRUCTURE")
    print_separator()

    # Print root attributes
    print("\nRoot Attributes:")
    for key, value in h5_file.attrs.items():
        print(f"  {key}: {value}")

    # Print figure groups
    print("\nFigures:")
    for fig_name in sorted(h5_file.keys()):
        if fig_name.startswith('figure_'):
            print(f"\n  {fig_name}/")
            fig_group = h5_file[fig_name]

            # Print figure attributes
            print("    Attributes:")
            for key, value in fig_group.attrs.items():
                print(f"      {key}: {value}")

            # Print datasets
            datasets = []
            subgroups = []
            for item_name in fig_group.keys():
                item = fig_group[item_name]
                if isinstance(item, h5py.Dataset):
                    datasets.append(item_name)
                elif isinstance(item, h5py.Group):
                    subgroups.append(item_name)

            if datasets:
                print("    Datasets:")
                for ds_name in datasets:
                    ds = fig_group[ds_name]
                    print(f"      {ds_name}: shape={ds.shape}, dtype={ds.dtype}")

            if subgroups:
                print("    Subgroups:")
                for sg_name in subgroups:
                    print(f"      {sg_name}/")
                    sg = fig_group[sg_name]
                    for key, value in sg.attrs.items():
                        print(f"        @{key}: {value}")
                    for ds_name in sg.keys():
                        ds = sg[ds_name]
                        print(f"        {ds_name}: shape={ds.shape}")


def analyze_landscape_figure(h5_file, figure_name):
    """Analyze and summarize a landscape (2D) figure"""
    print_separator()
    print(f"LANDSCAPE FIGURE ANALYSIS: {figure_name}")
    print_separator()

    fig = h5_file[figure_name]

    # Print metadata
    print("\nMetadata:")
    print(f"  Dimension: {fig.attrs.get('dimension', 'N/A')}")
    print(f"  Quantity: {fig.attrs.get('quantity', 'N/A')}")
    print(f"  Model: {fig.attrs.get('model', 'N/A')}")
    print(f"  Colorbar: {fig.attrs.get('colorbar', 'N/A')}")
    print(f"  Wigner: {fig.attrs.get('wigner', 'N/A')}")
    print(f"  Even-Even Only: {fig.attrs.get('even_even', 'N/A')}")

    if 'zmin' in fig.attrs:
        print(f"  Z-range: [{fig.attrs['zmin']:.3f}, {fig.attrs['zmax']:.3f}]")

    # Analyze data
    if 'values' in fig and 'neutrons' in fig and 'protons' in fig:
        values = fig['values'][:]
        neutrons = fig['neutrons'][:]
        protons = fig['protons'][:]

        print("\nData Summary:")
        print(f"  Array shape: {values.shape}")
        print(f"  Neutron range: {neutrons.min():.0f} - {neutrons.max():.0f}")
        print(f"  Proton range: {protons.min():.0f} - {protons.max():.0f}")

        # Calculate statistics on valid (non-None) values
        valid_values = values[~np.isnan(values.astype(float))]
        if len(valid_values) > 0:
            print(f"  Value range: {np.nanmin(values):.3f} - {np.nanmax(values):.3f}")
            print(f"  Mean value: {np.nanmean(values):.3f}")
            print(f"  Std dev: {np.nanstd(values):.3f}")
            print(f"  Valid data points: {len(valid_values)} / {values.size}")


def analyze_1d_figure(h5_file, figure_name):
    """Analyze and summarize a 1D chain figure"""
    print_separator()
    print(f"1D CHAIN FIGURE ANALYSIS: {figure_name}")
    print_separator()

    fig = h5_file[figure_name]

    # Print metadata
    print("\nMetadata:")
    print(f"  Dimension: {fig.attrs.get('dimension', 'N/A')}")
    print(f"  Chain Type: {fig.attrs.get('chain_type', 'N/A')}")
    print(f"  Quantity: {fig.attrs.get('quantity', 'N/A')}")

    # Print fixed parameters
    if 'proton_Z' in fig.attrs:
        print(f"  Proton Z: {fig.attrs['proton_Z']}")
    if 'neutron_N' in fig.attrs:
        print(f"  Neutron N: {fig.attrs['neutron_N']}")
    if 'mass_number_A' in fig.attrs:
        print(f"  Mass Number A: {fig.attrs['mass_number_A']}")

    # Analyze each series
    series_count = 0
    for key in sorted(fig.keys()):
        if key.startswith('series_'):
            series_count += 1
            series = fig[key]

            print(f"\n  Series {series_count}:")
            if 'label' in series.attrs:
                print(f"    Label: {series.attrs['label']}")

            # Determine x-axis data
            x_name = 'neutrons' if 'neutrons' in series else 'protons'
            if x_name in series:
                x_data = series[x_name][:]
                y_data = series['values'][:]

                print(f"    {x_name.capitalize()}: {x_data.min():.0f} - {x_data.max():.0f}")
                print(f"    Number of points: {len(x_data)}")
                print(f"    Value range: {y_data.min():.3f} - {y_data.max():.3f}")

                if 'uncertainties' in series:
                    unc = series['uncertainties'][:]
                    print(f"    Has uncertainties: Yes (mean = {np.mean(unc):.3f})")
                else:
                    print(f"    Has uncertainties: No")


def quick_summary(h5_file):
    """Print a quick summary of the file contents"""
    print_separator()
    print("QUICK SUMMARY")
    print_separator()

    num_figs = h5_file.attrs.get('num_figures', 'Unknown')
    export_date = h5_file.attrs.get('export_date', 'Unknown')

    print(f"\nExport Date: {export_date}")
    print(f"Number of Figures: {num_figs}")

    print("\nFigure Types:")
    for fig_name in sorted(h5_file.keys()):
        if fig_name.startswith('figure_'):
            fig = h5_file[fig_name]
            dimension = fig.attrs.get('dimension', 'unknown')
            quantity = fig.attrs.get('quantity', 'unknown')
            print(f"  {fig_name}: {dimension} - {quantity}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python read_h5_export.py <path_to_data.h5>")
        print("\nExample:")
        print("  python read_h5_export.py BMEX-Jan-15-2025_14-30-00/data.h5")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with h5py.File(filename, 'r') as f:
            # Quick summary
            quick_summary(f)

            # Full structure
            explore_structure(f)

            # Analyze each figure
            for fig_name in sorted(f.keys()):
                if not fig_name.startswith('figure_'):
                    continue

                fig = f[fig_name]
                dimension = fig.attrs.get('dimension', '')

                if dimension in ['landscape', 'landscape_diff']:
                    analyze_landscape_figure(f, fig_name)
                elif dimension == '1D':
                    analyze_1d_figure(f, fig_name)

            print_separator()
            print("Analysis complete!")
            print_separator()

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
