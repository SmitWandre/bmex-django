#!/usr/bin/env python3
"""
Example script for plotting data from BMEX HDF5 exports

This script demonstrates how to create visualizations from exported HDF5 data.

Requirements:
    pip install h5py numpy matplotlib

Usage:
    python plot_h5_export.py <path_to_data.h5>
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
import sys


def plot_landscape(h5_file, figure_name):
    """Plot a landscape (2D heatmap) figure"""
    fig_data = h5_file[figure_name]

    # Read data
    neutrons = fig_data['neutrons'][:]
    protons = fig_data['protons'][:]
    values = fig_data['values'][:]

    # Get metadata
    quantity = fig_data.attrs.get('quantity', 'Unknown')
    model = fig_data.attrs.get('model', 'Unknown')

    # Create figure
    plt.figure(figsize=(12, 10))

    # Create meshgrid for proper plotting
    N, P = np.meshgrid(neutrons, protons)

    # Plot heatmap
    im = plt.pcolormesh(N, P, values, shading='auto', cmap='viridis')

    # Add colorbar
    cbar = plt.colorbar(im, label=quantity)

    # Labels and title
    plt.xlabel('Neutrons', fontsize=14)
    plt.ylabel('Protons', fontsize=14)
    plt.title(f'{quantity} - {model}', fontsize=16)

    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save figure
    output_filename = f'{figure_name}_landscape.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_filename}")

    plt.show()


def plot_1d_chain(h5_file, figure_name):
    """Plot 1D chain data"""
    fig_data = h5_file[figure_name]

    # Get metadata
    quantity = fig_data.attrs.get('quantity', 'Unknown')
    chain_type = fig_data.attrs.get('chain_type', 'Unknown')

    # Create figure
    plt.figure(figsize=(12, 8))

    # Plot each series
    for series_name in sorted(fig_data.keys()):
        if not series_name.startswith('series_'):
            continue

        series = fig_data[series_name]

        # Get x-axis data (neutrons or protons)
        if 'neutrons' in series:
            x = series['neutrons'][:]
            x_label = 'Neutrons'
        else:
            x = series['protons'][:]
            x_label = 'Protons'

        # Get y-axis data
        y = series['values'][:]

        # Get label
        label = series.attrs.get('label', series_name)

        # Plot with or without error bars
        if 'uncertainties' in series:
            yerr = series['uncertainties'][:]
            plt.errorbar(x, y, yerr=yerr, label=label, marker='o',
                        markersize=6, capsize=3, capthick=1)
        else:
            plt.plot(x, y, label=label, marker='o', markersize=6,
                    linestyle='-', linewidth=1.5)

    # Labels and title
    plt.xlabel(x_label, fontsize=14)
    plt.ylabel(quantity, fontsize=14)

    # Add fixed parameter to title
    title = f'{quantity} - {chain_type.capitalize()} Chain'
    if 'proton_Z' in fig_data.attrs:
        title += f' (Z={fig_data.attrs["proton_Z"]})'
    elif 'neutron_N' in fig_data.attrs:
        title += f' (N={fig_data.attrs["neutron_N"]})'
    elif 'mass_number_A' in fig_data.attrs:
        title += f' (A={fig_data.attrs["mass_number_A"]})'

    plt.title(title, fontsize=16)

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save figure
    output_filename = f'{figure_name}_1d_chain.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_filename}")

    plt.show()


def plot_all_figures(filename):
    """Plot all figures in the HDF5 file"""
    with h5py.File(filename, 'r') as f:
        print(f"Opening: {filename}")
        print(f"Export Date: {f.attrs.get('export_date', 'Unknown')}")
        print(f"Number of Figures: {f.attrs.get('num_figures', 'Unknown')}\n")

        for fig_name in sorted(f.keys()):
            if not fig_name.startswith('figure_'):
                continue

            fig = f[fig_name]
            dimension = fig.attrs.get('dimension', '')

            print(f"Plotting {fig_name} ({dimension})...")

            try:
                if dimension in ['landscape', 'landscape_diff']:
                    plot_landscape(f, fig_name)
                elif dimension == '1D':
                    plot_1d_chain(f, fig_name)
                else:
                    print(f"  Skipping {fig_name}: dimension '{dimension}' not supported for plotting")
            except Exception as e:
                print(f"  Error plotting {fig_name}: {e}")
                import traceback
                traceback.print_exc()

        print("\nAll figures processed!")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python plot_h5_export.py <path_to_data.h5>")
        print("\nExample:")
        print("  python plot_h5_export.py BMEX-Jan-15-2025_14-30-00/data.h5")
        print("\nThis will create PNG files for each figure in the HDF5 file.")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        plot_all_figures(filename)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
