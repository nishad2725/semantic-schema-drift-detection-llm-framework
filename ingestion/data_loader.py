"""Data loading utilities for drift detection."""
import pandas as pd
from pathlib import Path

def load_dataset(path: str) -> pd.DataFrame:
    """
    Load a dataset from various file formats.
    
    Args:
        path: Path to the dataset file
        
    Returns:
        Loaded DataFrame
        
    Raises:
        ValueError: If file format is not supported
    """
    ext = Path(path).suffix.lower()
    
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in [".xls", ".xlsx"]:
        return pd.read_excel(path)
    if ext == ".txt":
        return pd.read_csv(path, delimiter="|")
    
    raise ValueError("Unsupported file format")

