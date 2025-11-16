import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from io import BytesIO

class DataHandler:
    """Handles data ingestion and validation"""

    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xlsx']

    async def load_data(self, file_content: bytes, file_type: str) -> pd.DataFrame:
        """Load data from uploaded file"""
        try:
            if file_type == 'csv':
                return pd.read_csv(BytesIO(file_content))
            elif file_type == 'json':
                return pd.read_json(BytesIO(file_content))
            elif file_type == 'xlsx':
                return pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate data structure and size"""
        # Check row count
        if len(df) < 2:
            return False, "Data must have at least 2 rows"

        if len(df) > 100000:
            return False, "Data exceeds maximum limit of 100,000 rows"

        # Check for empty dataframe
        if df.empty:
            return False, "Data cannot be empty"

        # Check for all null columns
        if df.isnull().all().all():
            return False, "All data is null"

        return True, "Data validated successfully"

    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data types and structure for chart selection"""
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        metadata = {
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'numerical_columns': numerical_cols,
            'categorical_columns': categorical_cols,
            'datetime_columns': datetime_cols,
            'row_count': len(df),
            'column_count': len(df.columns),
            'summary_stats': df.describe().to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
        }
        return metadata

    def apply_filters(self, df: pd.DataFrame, filters: list) -> pd.DataFrame:
        """Apply data filters to dataframe"""
        if not filters:
            return df

        filtered_df = df.copy()

        for filter_spec in filters:
            column = filter_spec.column
            operator = filter_spec.operator
            value = filter_spec.value

            if column not in filtered_df.columns:
                raise ValueError(f"Column {column} not found")

            try:
                if operator == '==':
                    filtered_df = filtered_df[filtered_df[column] == value]
                elif operator == '>':
                    filtered_df = filtered_df[filtered_df[column] > value]
                elif operator == '<':
                    filtered_df = filtered_df[filtered_df[column] < value]
                elif operator == '>=':
                    filtered_df = filtered_df[filtered_df[column] >= value]
                elif operator == '<=':
                    filtered_df = filtered_df[filtered_df[column] <= value]
                elif operator == '!=':
                    filtered_df = filtered_df[filtered_df[column] != value]
                else:
                    raise ValueError(f"Unsupported operator: {operator}")
            except Exception as e:
                raise ValueError(f"Error applying filter: {str(e)}")

        return filtered_df

    def get_column_sample(self, df: pd.DataFrame, column: str, sample_size: int = 5) -> list:
        """Get sample values from a column"""
        if column not in df.columns:
            return []
        return df[column].dropna().unique()[:sample_size].tolist()

# Singleton instance
data_handler = DataHandler()
