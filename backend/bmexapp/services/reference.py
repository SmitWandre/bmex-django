"""
Reference data loader service - ports logic from utils/bmex.py

This module handles loading and querying nuclear mass data from HDF5 files.
Maps to the original utils/bmex.py functions:
- QuanValue -> get_quantity_value
- Landscape -> get_landscape_data
- IsotopicChain -> get_isotopic_chain
- IsotonicChain -> get_isotonic_chain
- IsobaricChain -> get_isobaric_chain
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Element symbol lookup table (Z -> symbol)
ELEMENT_SYMBOLS = {
    0: 'n', 1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
    11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca',
    21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn',
    31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr',
    41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
    51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd',
    61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb',
    71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg',
    81: 'Tl', 82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
    91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es', 100: 'Fm',
    101: 'Md', 102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg', 107: 'Bh', 108: 'Hs', 109: 'Mt',
    110: 'Ds', 111: 'Rg', 112: 'Cn', 113: 'Nh', 114: 'Fl', 115: 'Mc', 116: 'Lv', 117: 'Ts', 118: 'Og'
}


class DataLoader:
    """
    Data loader for BMEX reference data.
    Singleton pattern with caching for performance.
    """

    MODELS = [
        'AME2020', 'SKMS', 'SKP', 'SLY4', 'SV',
        'UNEDF0', 'UNEDF1', 'UNEDF2',
        'ME2', 'MEdelta', 'PC1', 'NL3S',
        'FRDM12', 'HFB24', 'BCPM', 'D1M'
    ]

    # Wigner energy column suffixes
    WIGNER_SUFFIXES = {0: '', 1: '_W1', 2: '_W2', 3: '_W_avg'}

    # Quantity labels and units
    QUANTITY_INFO = {
        "BE": {"label": "Binding Energy", "unit": "MeV"},
        "MassExcess": {"label": "Mass Excess", "unit": "MeV"},
        "OneNSE": {"label": "One Neutron Separation Energy", "unit": "MeV"},
        "OnePSE": {"label": "One Proton Separation Energy", "unit": "MeV"},
        "TwoNSE": {"label": "Two Neutron Separation Energy", "unit": "MeV"},
        "TwoPSE": {"label": "Two Proton Separation Energy", "unit": "MeV"},
        "AlphaSE": {"label": "Alpha Separation Energy", "unit": "MeV"},
        "BetaMinusDecay": {"label": "Beta Minus Decay Q-Value", "unit": "MeV"},
        "BetaPlusDecay": {"label": "Beta Plus Decay Q-Value", "unit": "MeV"},
        "ElectronCaptureQValue": {"label": "Electron Capture Q-Value", "unit": "MeV"},
        "AlphaDecayQValue": {"label": "Alpha Decay Q-Value", "unit": "MeV"},
        "TwoNSGap": {"label": "Two Neutron Shell Gap", "unit": "MeV"},
        "TwoPSGap": {"label": "Two Proton Shell Gap", "unit": "MeV"},
        "DoubleMDiff": {"label": "Double Mass Difference", "unit": "MeV"},
        "N3PointOED": {"label": "Neutron 3-Point Odd-Even Binding Energy Difference", "unit": "MeV"},
        "P3PointOED": {"label": "Proton 3-Point Odd-Even Binding Energy Difference", "unit": "MeV"},
        "SNESplitting": {"label": "Single-Neutron Shell Gap", "unit": "MeV"},
        "SPESplitting": {"label": "Single-Proton Shell Gap", "unit": "MeV"},
        "WignerEC": {"label": "Wigner Energy Coefficient", "unit": "MeV"},
        "BEperA": {"label": "Binding Energy per Nucleon", "unit": "MeV"},
        "QDB2t": {"label": "Quadrupole Deformation Beta2", "unit": ""},
        "QDB2n": {"label": "Quadrupole Deformation Beta2 N", "unit": ""},
        "QDB2p": {"label": "Quadrupole Deformation Beta2 P", "unit": ""},
        "QDB4t": {"label": "Quadrupole Deformation Beta4", "unit": ""},
        "QDB4n": {"label": "Quadrupole Deformation Beta4 N", "unit": ""},
        "QDB4p": {"label": "Quadrupole Deformation Beta4 P", "unit": ""},
        "FermiN": {"label": "Fermi Energy N", "unit": "MeV"},
        "FermiP": {"label": "Fermi Energy P", "unit": "MeV"},
        "PEn": {"label": "Pairing Energy N", "unit": "MeV"},
        "PEp": {"label": "Pairing Energy P", "unit": "MeV"},
        "PGn": {"label": "Pairing Gap N", "unit": "MeV"},
        "PGp": {"label": "Pairing Gap P", "unit": "MeV"},
        "CPn": {"label": "Chemical Potential N", "unit": "MeV"},
        "CPp": {"label": "Chemical Potential P", "unit": "MeV"},
        "RMSradT": {"label": "RMS Radius Total", "unit": "fm"},
        "RMSradN": {"label": "RMS Radius N", "unit": "fm"},
        "RMSradP": {"label": "RMS Radius P", "unit": "fm"},
        "MRadN": {"label": "Mass Radius N", "unit": "fm"},
        "MRadP": {"label": "Mass Radius P", "unit": "fm"},
        "ChRad": {"label": "Charge Radius", "unit": "fm"},
        "NSkin": {"label": "Neutron Skin", "unit": "fm"},
        "QMQ2t": {"label": "Quad Moment Q2 Total", "unit": "fm²"},
        "QMQ2n": {"label": "Quad Moment Q2 N", "unit": "fm²"},
        "QMQ2p": {"label": "Quad Moment Q2 P", "unit": "fm²"},
    }

    _instance = None
    _data_cache: Dict[str, pd.DataFrame] = {}

    def __init__(self):
        """Initialize data loader with path to HDF5 file."""
        self.data_path = Path(settings.BMEX_DATA_PATH)
        self.db_file = self.data_path / '2-27-25.h5'

        if not self.db_file.exists():
            logger.warning(f"HDF5 file not found: {self.db_file}")
            # Try parent directory data path
            alt_path = Path(settings.BASE_DIR).parent / 'data' / '2-27-25.h5'
            if alt_path.exists():
                self.db_file = alt_path
                logger.info(f"Using alternate data path: {self.db_file}")
            else:
                logger.error(f"Could not locate HDF5 data file")

    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @lru_cache(maxsize=32)
    def load_model_data(self, model: str) -> pd.DataFrame:
        """
        Load model data from HDF5 file with caching.
        Maps to original bmex.py data loading.
        """
        cache_key = f'model_data_{model}'
        df = cache.get(cache_key)

        if df is not None:
            return df

        try:
            df = pd.read_hdf(str(self.db_file), model)
            cache.set(cache_key, df, timeout=3600)  # Cache for 1 hour
            logger.info(f"Loaded model {model} with {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to load model {model}: {e}")
            return pd.DataFrame(columns=['Z', 'N'])

    def get_quantity_value(
        self, Z: int, N: int, model: str, quantity: str,
        W: int = 0, uncertainty: bool = False
    ) -> Tuple[Optional[float], Optional[float], Optional[int]]:
        """
        Get single quantity value for a nucleus.
        Maps to original QuanValue function in bmex.py

        Returns: (value, uncertainty, estimated_flag)
        """
        df = self.load_model_data(model)

        try:
            wstring = self.WIGNER_SUFFIXES.get(W, '')
            row = df[(df["N"] == N) & (df["Z"] == Z)]

            if row.empty:
                return None, None, None

            value = np.round(row[quantity + wstring].values[0], 6)

            if uncertainty and model == 'AME2020':
                try:
                    u = np.round(row[f'u{quantity}'].values[0], 6)
                except:
                    u = None

                try:
                    e = int(row[f'e{quantity}'].values[0])
                except:
                    e = 0

                return value, u, e

            return value, None, None

        except Exception as e:
            logger.debug(f"Value not found for Z={Z}, N={N}, model={model}, quantity={quantity}: {e}")
            return None, None, None

    def get_landscape_data(
        self, model: str, quantity: str, W: int = 0,
        step: int = 1, SPS_adj: Optional[str] = None
    ) -> Tuple[pd.DataFrame, np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get 2D landscape array for heatmap visualization.
        Maps to original Landscape function in bmex.py

        Returns: (dataframe, 2d_array, uncertainties, estimated_flags)
        """
        df = self.load_model_data(model)
        df = df[df["N"] % step == 0]
        df = df[df["Z"] % step == 0]
        df = df.dropna(subset=[quantity])

        wstring = self.WIGNER_SUFFIXES.get(W, '')

        # Apply SPS adjustment if needed
        if SPS_adj == 'N':
            factor = 41 * (df['N'] + df['Z'])**(-1/3) * (1 + (df['N'] - df['Z']) / (3 * (df['N'] + df['Z'])))
            for w in [0, 1, 2]:
                col = quantity + self.WIGNER_SUFFIXES[w]
                if col in df.columns:
                    df[col] = df[col] / factor
        elif SPS_adj == 'P':
            factor = 41 * (df['N'] + df['Z'])**(-1/3) * (1 - (df['N'] - df['Z']) / (3 * (df['N'] + df['Z'])))
            for w in [0, 1, 2]:
                col = quantity + self.WIGNER_SUFFIXES[w]
                if col in df.columns:
                    df[col] = df[col] / factor

        # Build 2D array
        max_z = int(df['Z'].max() // step + 1)
        max_n = int(df['N'].max() // step + 1)
        arr2d = np.full((max_z, max_n), None, dtype=object)

        for idx in df.index:
            try:
                z_idx = int(df.loc[idx, 'Z'] // step)
                n_idx = int(df.loc[idx, 'N'] // step)

                if W == 3:  # Average W1 and W2
                    w1_col = quantity + self.WIGNER_SUFFIXES[1]
                    w2_col = quantity + self.WIGNER_SUFFIXES[2]
                    if w1_col in df.columns and w2_col in df.columns:
                        arr2d[z_idx, n_idx] = np.round(
                            (df.loc[idx, w1_col] + df.loc[idx, w2_col]) / 2, 6
                        )
                else:
                    col = quantity + wstring
                    if col in df.columns:
                        arr2d[z_idx, n_idx] = np.round(df.loc[idx, col], 6)
            except Exception as e:
                logger.debug(f"Error processing landscape point: {e}")
                continue

        # Handle AME2020 uncertainties and estimated flags
        uncertainties, estimated = None, None
        if model == 'AME2020':
            uncertainties = np.full((max_z, max_n), None, dtype=object)
            estimated = np.full((max_z, max_n), 0, dtype=int)

            for idx in df.index:
                try:
                    z_idx = int(df.loc[idx, 'Z'] // step)
                    n_idx = int(df.loc[idx, 'N'] // step)

                    u_col = f'u{quantity}'
                    if u_col in df.columns:
                        uncertainties[z_idx, n_idx] = np.round(df.loc[idx, u_col], 6)

                    e_col = f'e{quantity}'
                    if e_col in df.columns:
                        estimated[z_idx, n_idx] = int(df.loc[idx, e_col])
                except:
                    pass

        return df, arr2d, uncertainties, estimated

    def get_isotopic_chain(
        self, Z: int, model: str, quantity: str, W: int = 0
    ) -> pd.DataFrame:
        """
        Get isotopic chain (constant Z, varying N).
        Maps to original IsotopicChain function in bmex.py
        """
        df = self.load_model_data(model)
        df = df[df["Z"] == Z]
        df = df.dropna(subset=[quantity])

        wstring = self.WIGNER_SUFFIXES.get(W, '')

        if model == 'AME2020':
            cols = ["N", quantity + wstring, f"u{quantity}", f"e{quantity}"]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result
        else:
            cols = ["N", quantity + wstring]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result

    def get_isotonic_chain(
        self, N: int, model: str, quantity: str, W: int = 0
    ) -> pd.DataFrame:
        """
        Get isotonic chain (constant N, varying Z).
        Maps to original IsotonicChain function in bmex.py
        """
        df = self.load_model_data(model)
        df = df[df["N"] == N]
        df = df.dropna(subset=[quantity])

        wstring = self.WIGNER_SUFFIXES.get(W, '')

        if model == 'AME2020':
            cols = ["Z", quantity + wstring, f"u{quantity}", f"e{quantity}"]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result
        else:
            cols = ["Z", quantity + wstring]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result

    def get_isobaric_chain(
        self, A: int, model: str, quantity: str, W: int = 0
    ) -> pd.DataFrame:
        """
        Get isobaric chain (constant A=Z+N, varying Z).
        Maps to original IsobaricChain function in bmex.py
        """
        df = self.load_model_data(model)
        df = df[df["Z"] + df["N"] == A]
        df = df.dropna(subset=[quantity])

        wstring = self.WIGNER_SUFFIXES.get(W, '')

        if model == 'AME2020':
            cols = ["Z", quantity + wstring, f"u{quantity}", f"e{quantity}"]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result
        else:
            cols = ["Z", quantity + wstring]
            cols = [c for c in cols if c in df.columns]
            result = df[cols].copy()

            if W == 3 and quantity + '_W1' in df.columns and quantity + '_W2' in df.columns:
                result[quantity + wstring] = (
                    df[quantity + '_W1'] + df[quantity + '_W2']
                ) / 2

            return result

    def filter_masses(
        self, model: str = 'AME2020', z_min: Optional[int] = None,
        z_max: Optional[int] = None, n_min: Optional[int] = None,
        n_max: Optional[int] = None, element: Optional[str] = None,
        quantity: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Filter mass data with pagination.
        Returns: (records, total_count)
        """
        df = self.load_model_data(model)

        # Apply filters
        if z_min is not None:
            df = df[df['Z'] >= z_min]
        if z_max is not None:
            df = df[df['Z'] <= z_max]
        if n_min is not None:
            df = df[df['N'] >= n_min]
        if n_max is not None:
            df = df[df['N'] <= n_max]
        if element:
            # Convert element symbol to Z
            element_upper = element.upper()
            z_values = [z for z, sym in ELEMENT_SYMBOLS.items() if sym.upper() == element_upper]
            if z_values:
                df = df[df['Z'].isin(z_values)]
        if quantity:
            df = df.dropna(subset=[quantity])

        total_count = len(df)

        # Apply pagination
        df = df.iloc[offset:offset + limit]

        # Convert to records
        records = []
        for _, row in df.iterrows():
            record = {
                'Z': int(row['Z']),
                'N': int(row['N']),
                'A': int(row['Z'] + row['N']),
                'element': ELEMENT_SYMBOLS.get(int(row['Z']), ''),
                'model': model,
            }

            if quantity and quantity in row.index:
                record['quantity'] = quantity
                record['value'] = float(row[quantity]) if pd.notna(row[quantity]) else None
                record['unit'] = self.QUANTITY_INFO.get(quantity, {}).get('unit', '')

                # Add uncertainty for AME2020
                if model == 'AME2020':
                    u_col = f'u{quantity}'
                    e_col = f'e{quantity}'
                    if u_col in row.index:
                        record['uncertainty'] = float(row[u_col]) if pd.notna(row[u_col]) else None
                    if e_col in row.index:
                        record['is_estimated'] = bool(row[e_col])

            records.append(record)

        return records, total_count

    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available theoretical models."""
        return [
            {
                'name': model,
                'full_name': model,
                'description': f'{model} theoretical nuclear model',
                'version': '2025'
            }
            for model in self.MODELS
        ]

    def get_element_symbol(self, z: int) -> str:
        """Get element symbol for proton number."""
        return ELEMENT_SYMBOLS.get(z, '')

    def get_quantity_info(self, quantity: str) -> Dict[str, str]:
        """Get quantity metadata (label, unit)."""
        return self.QUANTITY_INFO.get(quantity, {'label': quantity, 'unit': ''})


def get_data_loader() -> DataLoader:
    """Get data loader singleton instance."""
    return DataLoader.get_instance()
