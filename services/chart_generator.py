import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from typing import Dict, Any, List, Tuple

class ChartGenerator:
    """Generates interactive charts using Plotly"""

    def __init__(self):
        self.chart_functions = {
            'bar': self._create_bar_chart,
            'line': self._create_line_chart,
            'scatter': self._create_scatter_chart,
            'pie': self._create_pie_chart,
            'heatmap': self._create_heatmap,
            'area': self._create_area_chart,
            'histogram': self._create_histogram,
            'box': self._create_box_chart,
        }

    def _prepare_data(self, df: pd.DataFrame, columns_needed: List[str], numeric_only: bool = False) -> pd.DataFrame:
        """
        Safely prepare dataframe for Plotly by:
        1. Selecting only needed columns
        2. Removing rows with all NaN
        3. Converting types if needed
        4. Removing completely empty columns
        """
        # Validate columns exist
        cols_available = [col for col in columns_needed if col in df.columns]
        if not cols_available:
            raise ValueError(f"None of the required columns {columns_needed} found in data. Available: {list(df.columns)}")
        
        # Select only needed columns
        df_prep = df[cols_available].copy()
        
        # Remove completely empty columns
        df_prep = df_prep.dropna(axis=1, how='all')
        
        # Remove rows where all values are NaN
        df_prep = df_prep.dropna(how='all')
        
        if numeric_only:
            # Keep only numeric columns
            df_prep = df_prep.select_dtypes(include=['number'])
            if df_prep.empty:
                raise ValueError(f"No numeric columns found in {cols_available}")
        
        if df_prep.empty:
            raise ValueError("Data is empty after preparation")
        
        return df_prep

    def _ensure_numeric(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Safely convert a column to numeric, dropping NaN values
        """
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        
        df = df.copy()
        if df[column].dtype != 'object' and df[column].dtype != 'string':
            return df
        
        try:
            df[column] = pd.to_numeric(df[column], errors='coerce')
            original_len = len(df)
            df = df.dropna(subset=[column])
            dropped = original_len - len(df)
            if dropped > 0:
                print(f"Warning: Dropped {dropped} rows with non-numeric values in '{column}'")
            if df.empty:
                raise ValueError(f"Column '{column}' contains no valid numeric values")
            return df
        except Exception as e:
            raise ValueError(f"Cannot convert column '{column}' to numeric: {str(e)}")

    def _get_columns_for_chart(self, spec: Dict[str, Any]) -> List[str]:
        """
        Extract all columns needed for a chart from spec
        """
        cols = []
        if spec.get('x_axis'):
            cols.append(spec['x_axis'])
        if spec.get('y_axis'):
            cols.append(spec['y_axis'])
        if spec.get('color_by'):
            cols.append(spec['color_by'])
        return cols

    async def generate_chart(self, df: pd.DataFrame, chart_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart based on specification"""
        try:
            chart_type = chart_spec.get('chart_type', '').lower()

            if chart_type not in self.chart_functions:
                raise ValueError(f"Unsupported chart type: {chart_type}. Supported: {list(self.chart_functions.keys())}")

            if df.empty:
                raise ValueError("Input dataframe is empty")

            # Apply filters if specified
            filtered_df = df.copy()
            if chart_spec.get('filters'):
                for filter_item in chart_spec['filters']:
                    column = filter_item.get('column')
                    operator = filter_item.get('operator')
                    value = filter_item.get('value')

                    if not column or column not in filtered_df.columns:
                        continue
                    
                    if operator == '==':
                        filtered_df = filtered_df[filtered_df[column] == value]

            if filtered_df.empty:
                raise ValueError("No data matches the specified filters")

            # Apply aggregation if requested and y_axis provided
            agg = chart_spec.get('aggregation', 'none')
            x_axis = chart_spec.get('x_axis')
            y_axis = chart_spec.get('y_axis')
            color_by = chart_spec.get('color_by')

            if agg and agg != 'none' and y_axis and x_axis:
                try:
                    filtered_df = self._apply_aggregation(filtered_df, agg, x_axis, y_axis, color_by)
                except Exception as e:
                    print(f"Warning: Aggregation failed ({str(e)}), proceeding without aggregation")

            # Get columns needed for chart
            cols_needed = self._get_columns_for_chart(chart_spec)
            
            # Prepare data - select only needed columns
            if cols_needed:
                filtered_df = self._prepare_data(filtered_df, cols_needed)

            # Generate the appropriate chart
            chart_function = self.chart_functions[chart_type]
            fig = chart_function(filtered_df, chart_spec)

            # Apply customizations
            customization = chart_spec.get('customization', {})
            fig = self._apply_customizations(fig, customization)

            # Return chart in multiple formats
            return {
                'chart_spec': chart_spec,
                'chart_html': fig.to_html(include_plotlyjs='cdn'),
                'chart_json': json.loads(fig.to_json()),
            }
        except Exception as e:
            raise Exception(f"Error generating {chart_spec.get('chart_type', 'unknown')} chart: {str(e)}")

    def _apply_aggregation(self, df: pd.DataFrame, agg: str, x_axis: str, y_axis: str, color_by: str = None) -> pd.DataFrame:
        """Apply aggregation to dataframe"""
        agg_map = {
            'sum': 'sum',
            'mean': 'mean',
            'count': 'count',
            'min': 'min',
            'max': 'max'
        }
        func = agg_map.get(agg)
        if func is None:
            raise ValueError(f"Unsupported aggregation: {agg}")

        # Validate columns exist
        if x_axis not in df.columns:
            raise ValueError(f"X-axis column '{x_axis}' not found")
        if y_axis not in df.columns:
            raise ValueError(f"Y-axis column '{y_axis}' not found")

        # If color_by present, aggregate per (x_axis, color_by)
        if color_by and color_by in df.columns:
            grouped = df.groupby([x_axis, color_by])[y_axis]
            if func == 'count':
                agg_df = grouped.size().reset_index(name=y_axis)
            else:
                agg_df = grouped.aggregate(func).reset_index()
        else:
            grouped = df.groupby(x_axis)[y_axis]
            if func == 'count':
                agg_df = grouped.size().reset_index(name=y_axis)
            else:
                agg_df = grouped.aggregate(func).reset_index()

        return agg_df

    def _create_bar_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create bar chart"""
        x_axis = spec.get('x_axis')
        y_axis = spec.get('y_axis')
        color_by = spec.get('color_by')

        if not x_axis:
            raise ValueError("Bar chart requires x_axis")

        try:
            if y_axis:
                # Numeric bar chart
                plot_df = self._prepare_data(df, [x_axis, y_axis])
                fig = px.bar(
                    plot_df,
                    x=x_axis,
                    y=y_axis,
                    color=color_by if color_by and color_by in plot_df.columns else None,
                    title=spec.get('title', 'Bar Chart'),
                    labels={x_axis: spec.get('x_label', x_axis)}
                )
            else:
                # Count bar chart
                plot_df = self._prepare_data(df, [x_axis])
                counts = plot_df[x_axis].value_counts().reset_index()
                counts.columns = [x_axis, 'count']
                fig = px.bar(
                    counts,
                    x='count',
                    y=x_axis,
                    orientation='h',
                    title=spec.get('title', 'Bar Chart'),
                )
        except Exception as e:
            raise ValueError(f"Error creating bar chart: {str(e)}")

        return fig

    def _create_line_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create line chart"""
        x_axis = spec.get('x_axis')
        y_axis = spec.get('y_axis')
        color_by = spec.get('color_by')

        if not x_axis or not y_axis:
            raise ValueError("Line chart requires both x_axis and y_axis")

        try:
            cols_needed = [x_axis, y_axis]
            if color_by:
                cols_needed.append(color_by)
            
            plot_df = self._prepare_data(df, cols_needed)
            
            fig = px.line(
                plot_df,
                x=x_axis,
                y=y_axis,
                color=color_by if color_by and color_by in plot_df.columns else None,
                title=spec.get('title', 'Line Chart'),
                markers=True
            )
        except Exception as e:
            raise ValueError(f"Error creating line chart: {str(e)}")

        return fig

    def _create_scatter_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create scatter plot"""
        x_axis = spec.get('x_axis')
        y_axis = spec.get('y_axis')
        color_by = spec.get('color_by')

        if not x_axis or not y_axis:
            raise ValueError("Scatter chart requires both x_axis and y_axis")

        try:
            cols_needed = [x_axis, y_axis]
            if color_by:
                cols_needed.append(color_by)
            
            plot_df = self._prepare_data(df, cols_needed)
            
            fig = px.scatter(
                plot_df,
                x=x_axis,
                y=y_axis,
                color=color_by if color_by and color_by in plot_df.columns else None,
                title=spec.get('title', 'Scatter Plot'),
            )
        except Exception as e:
            raise ValueError(f"Error creating scatter chart: {str(e)}")

        return fig

    def _create_pie_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create pie chart"""
        x_axis = spec.get('x_axis')

        if not x_axis:
            raise ValueError("Pie chart requires x_axis")

        try:
            plot_df = self._prepare_data(df, [x_axis])
            pie_data = plot_df.groupby(x_axis).size().reset_index(name='count')
            
            fig = px.pie(
                pie_data,
                names=x_axis,
                values='count',
                title=spec.get('title', 'Pie Chart'),
            )
        except Exception as e:
            raise ValueError(f"Error creating pie chart: {str(e)}")

        return fig

    def _create_heatmap(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create heatmap (correlation matrix of numeric columns)"""
        try:
            # Select only numeric columns for heatmap
            numeric_df = self._prepare_data(df, df.columns.tolist(), numeric_only=True)
            
            if numeric_df.shape[1] < 2:
                raise ValueError("Heatmap requires at least 2 numeric columns")

            correlation_matrix = numeric_df.corr()

            fig = px.imshow(
                correlation_matrix,
                title=spec.get('title', 'Correlation Heatmap'),
                labels=dict(color='Correlation'),
                color_continuous_scale='RdBu'
            )
        except Exception as e:
            raise ValueError(f"Error creating heatmap: {str(e)}")

        return fig

    def _create_area_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create area chart"""
        x_axis = spec.get('x_axis')
        y_axis = spec.get('y_axis')

        if not x_axis or not y_axis:
            raise ValueError("Area chart requires both x_axis and y_axis")

        try:
            plot_df = self._prepare_data(df, [x_axis, y_axis])
            
            fig = px.area(
                plot_df,
                x=x_axis,
                y=y_axis,
                title=spec.get('title', 'Area Chart'),
            )
        except Exception as e:
            raise ValueError(f"Error creating area chart: {str(e)}")

        return fig

    def _create_histogram(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create histogram"""
        x_axis = spec.get('x_axis')

        if not x_axis:
            raise ValueError("Histogram requires x_axis")

        try:
            plot_df = self._prepare_data(df, [x_axis])
            
            # Check if column is numeric, if not try to convert
            if plot_df[x_axis].dtype == 'object' or plot_df[x_axis].dtype == 'string':
                # Try to convert to numeric
                plot_df = self._ensure_numeric(plot_df, x_axis)
            
            # If still not numeric after all attempts, find first numeric column
            if plot_df[x_axis].dtype not in ['int64', 'int32', 'float64', 'float32', 'int', 'float']:
                numeric_cols = plot_df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    print(f"Warning: Column '{x_axis}' is not numeric. Using '{numeric_cols[0]}' instead")
                    x_axis = numeric_cols[0]
                else:
                    raise ValueError(f"Column '{x_axis}' is not numeric and no numeric columns found in data")
            
            fig = px.histogram(
                plot_df,
                x=x_axis,
                nbins=20,
                title=spec.get('title', 'Histogram'),
            )
        except Exception as e:
            raise ValueError(f"Error creating histogram: {str(e)}")

        return fig

    def _create_box_chart(self, df: pd.DataFrame, spec: Dict[str, Any]) -> go.Figure:
        """Create box plot"""
        x_axis = spec.get('color_by')
        y_axis = spec.get('y_axis')

        if not y_axis:
            raise ValueError("Box chart requires y_axis")

        try:
            cols_needed = [y_axis]
            if x_axis:
                cols_needed.append(x_axis)
            
            plot_df = self._prepare_data(df, cols_needed)
            
            fig = px.box(
                plot_df,
                x=x_axis if x_axis and x_axis in plot_df.columns else None,
                y=y_axis,
                title=spec.get('title', 'Box Plot'),
            )
        except Exception as e:
            raise ValueError(f"Error creating box chart: {str(e)}")

        return fig

    def _apply_customizations(self, fig: go.Figure, customization: Dict[str, Any]) -> go.Figure:
        """Apply visual customizations"""
        if customization.get('color_scheme'):
            # Map allowed customization names to Plotly colorscales.
            # 'default' means use Plotly's default styling (do not set colorscale).
            cs = customization['color_scheme']
            colorscale_map = {
                'default': None,
                'viridis': 'viridis',
                'plasma': 'plasma',
                'coolwarm': 'RdBu',
            }
            plotly_colorscale = colorscale_map.get(cs, cs)
            if plotly_colorscale:
                fig.update_traces(marker=dict(colorscale=plotly_colorscale))

        if not customization.get('show_legend', True):
            fig.update_layout(showlegend=False)

        if customization.get('data_labels'):
            fig.update_traces(textposition='auto', texttemplate='%{y}')

        # Improve layout
        fig.update_layout(
            hovermode='x unified',
            template='plotly_white',
            height=500,
        )

        return fig

# Singleton instance
chart_generator = ChartGenerator()
