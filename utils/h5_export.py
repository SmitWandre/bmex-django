import h5py
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

import base64

def _safe_float_array(data):
    """Safely convert Plotly dash-serialized arrays to numpy float arrays."""
    if data is None:
        return None
    
    # Handle dict structures (e.g. index-based serialization or bdata JSON components)
    if isinstance(data, dict):
        # Handle Plotly bdata typed arrays (e.g., {'dtype': 'i1', 'bdata': '...', 'shape': '3'})
        if 'bdata' in data and 'dtype' in data:
            try:
                decoded = base64.b64decode(data['bdata'])
                return np.frombuffer(decoded, dtype=data['dtype']).astype(float)
            except Exception:
                pass
                
        # Handle index-based serialization like {'0': 1.5, '1': 2.0}
        try:
            keys = sorted([int(k) for k in data.keys()])
            return np.array([data[str(k)] for k in keys], dtype=float)
        except (ValueError, TypeError):
            return np.array(list(data.values()), dtype=float)
            
    # Handle lists that may contain dict elements
    if isinstance(data, (list, tuple, np.ndarray)):
        if len(data) > 0 and isinstance(data[0], dict):
            try:
                clean_data = []
                for item in data:
                    if isinstance(item, dict):
                        if len(item) == 1:
                            clean_data.append(list(item.values())[0])
                        else:
                            clean_data.append(np.nan)
                    else:
                        clean_data.append(item)
                return np.array(clean_data, dtype=float)
            except Exception:
                pass
                
    # Standard array conversion
    try:
        return np.array(data, dtype=float)
    except Exception:
        return None


def export_figure_to_h5(figure, view_config, file_handle, group_name):
    """
    Export a Plotly figure and its configuration to an HDF5 group.

    Parameters:
    -----------
    figure : dict or go.Figure
        The Plotly figure to export
    view_config : dict
        The view configuration containing dimension, quantity, model, etc.
    file_handle : h5py.File
        Open HDF5 file handle
    group_name : str
        Name of the group to create in the HDF5 file
    """
    fig = go.Figure(figure) if isinstance(figure, dict) else figure

    # Create group for this figure
    grp = file_handle.create_group(group_name)

    # Store metadata
    grp.attrs['dimension'] = view_config.get('dimension', 'unknown')
    grp.attrs['quantity'] = view_config.get('quantity', 'unknown')
    grp.attrs['colorbar'] = view_config.get('colorbar', 'linear')
    grp.attrs['even_even'] = view_config.get('even_even', False)
    grp.attrs['export_timestamp'] = datetime.now().isoformat()

    if view_config['dimension'] == '1D':
        grp.attrs['chain'] = view_config.get('chain', 'isotopic')

    # Store colorbar range if available
    if view_config.get('colorbar_range'):
        cb_range = view_config['colorbar_range']
        if cb_range[0] is not None and cb_range[1] is not None:
            grp.attrs['colorbar_min'] = cb_range[0]
            grp.attrs['colorbar_max'] = cb_range[1]

    # Export data based on dimension type
    if view_config['dimension'] == 'landscape' or view_config['dimension'] == 'landscape_diff':
        _export_landscape_data(fig, grp, view_config)
    elif view_config['dimension'] == '1D':
        _export_1d_data(fig, grp, view_config)
    elif view_config['dimension'] == 'single':
        _export_single_data(fig, grp, view_config)


def _export_landscape_data(fig, grp, view_config):
    """Export 2D landscape/heatmap data"""
    if len(fig.data) == 0:
        return

    trace = fig.data[0]

    # Store the heatmap data
    if hasattr(trace, 'z') and trace.z is not None:
        z_data = _safe_float_array(trace.z)
        if z_data is not None:
            grp.create_dataset('values', data=z_data, compression='gzip')

    # Store x and y coordinates (neutrons and protons)
    if hasattr(trace, 'x') and trace.x is not None:
        x_data = _safe_float_array(trace.x)
        if x_data is not None:
            grp.create_dataset('neutrons', data=x_data, compression='gzip')

    if hasattr(trace, 'y') and trace.y is not None:
        y_data = _safe_float_array(trace.y)
        if y_data is not None:
            grp.create_dataset('protons', data=y_data, compression='gzip')

    # Store colorscale information
    if hasattr(trace, 'colorscale') and trace.colorscale is not None:
        colorscale_str = str(trace.colorscale)
        grp.attrs['colorscale'] = colorscale_str

    # Store zmin and zmax
    if hasattr(trace, 'zmin') and trace.zmin is not None:
        grp.attrs['zmin'] = float(trace.zmin)
    if hasattr(trace, 'zmax') and trace.zmax is not None:
        grp.attrs['zmax'] = float(trace.zmax)

    # Store text annotations if available (for estimated values markers)
    if hasattr(trace, 'text') and trace.text is not None:
        try:
            text_data = np.array(trace.text, dtype='S1')
            grp.create_dataset('annotations', data=text_data, compression='gzip')
        except:
            pass

    # Store dataset information
    if 'dataset' in view_config and len(view_config['dataset']) > 0:
        grp.attrs['model'] = view_config['dataset'][0]

    # Store wigner information
    if 'wigner' in view_config and len(view_config['wigner']) > 0:
        grp.attrs['wigner'] = view_config['wigner'][0]


def _export_1d_data(fig, grp, view_config):
    """Export 1D chain data (isotopic, isotonic, isobaric)"""
    chain = view_config.get('chain', 'isotopic')
    grp.attrs['chain_type'] = chain

    # Create subgroups for each series
    for i, trace in enumerate(fig.data):
        if trace.x is None or trace.y is None:
            continue

        series_grp = grp.create_group(f'series_{i+1}')

        # Store x and y data
        x_data = _safe_float_array(trace.x)
        y_data = _safe_float_array(trace.y)

        if x_data is None or y_data is None:
            continue

        if chain == 'isotopic':
            series_grp.create_dataset('neutrons', data=x_data, compression='gzip')
        elif chain == 'isotonic':
            series_grp.create_dataset('protons', data=x_data, compression='gzip')
        elif chain == 'isobaric':
            series_grp.create_dataset('protons', data=x_data, compression='gzip')

        series_grp.create_dataset('values', data=y_data, compression='gzip')

        # Store series name/label
        if hasattr(trace, 'name') and trace.name is not None:
            series_grp.attrs['label'] = str(trace.name)

        # Store error bars if present
        if hasattr(trace, 'error_y') and trace.error_y is not None:
            if hasattr(trace.error_y, 'array') and trace.error_y.array is not None:
                error_data = _safe_float_array(trace.error_y.array)
                if error_data is not None:
                    series_grp.create_dataset('uncertainties', data=error_data, compression='gzip')

        # Store marker information
        if hasattr(trace, 'marker'):
            if hasattr(trace.marker, 'symbol') and trace.marker.symbol is not None:
                # Handle array of symbols
                if isinstance(trace.marker.symbol, (list, np.ndarray)):
                    symbol_data = np.array(trace.marker.symbol, dtype='S10')
                    series_grp.create_dataset('marker_symbols', data=symbol_data, compression='gzip')
                else:
                    series_grp.attrs['marker_symbol'] = str(trace.marker.symbol)

        # Store custom data if available (estimated markers)
        if hasattr(trace, 'customdata') and trace.customdata is not None:
            try:
                custom_data = np.array(trace.customdata, dtype='S20')
                series_grp.create_dataset('custom_data', data=custom_data, compression='gzip')
            except:
                pass

    # Store the fixed parameter values
    if chain == 'isotopic' and 'proton' in view_config and len(view_config['proton']) > 0:
        if view_config['proton'][0] is not None:
            grp.attrs['proton_Z'] = view_config['proton'][0]
    elif chain == 'isotonic' and 'neutron' in view_config and len(view_config['neutron']) > 0:
        if view_config['neutron'][0] is not None:
            grp.attrs['neutron_N'] = view_config['neutron'][0]
    elif chain == 'isobaric' and 'nucleon' in view_config and len(view_config['nucleon']) > 0:
        if view_config['nucleon'][0] is not None:
            grp.attrs['mass_number_A'] = view_config['nucleon'][0]

    # Store dataset information for all series
    if 'dataset' in view_config:
        for i, dataset in enumerate(view_config['dataset']):
            grp.attrs[f'model_series_{i+1}'] = dataset

    # Store wigner information for all series
    if 'wigner' in view_config:
        for i, wigner in enumerate(view_config['wigner']):
            grp.attrs[f'wigner_series_{i+1}'] = wigner


def _export_single_data(fig, grp, view_config):
    """Export single nuclei data"""
    # For single nuclei, just store the configuration
    if 'proton' in view_config and len(view_config['proton']) > 0:
        if view_config['proton'][0] is not None:
            grp.attrs['proton_Z'] = view_config['proton'][0]

    if 'neutron' in view_config and len(view_config['neutron']) > 0:
        if view_config['neutron'][0] is not None:
            grp.attrs['neutron_N'] = view_config['neutron'][0]

    if 'dataset' in view_config and len(view_config['dataset']) > 0:
        grp.attrs['model'] = view_config['dataset'][0]

    if 'wigner' in view_config and len(view_config['wigner']) > 0:
        grp.attrs['wigner'] = view_config['wigner'][0]

    grp.attrs['note'] = 'Single nuclei view - refer to main interface for value display'
