import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objs as go
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    # Fallback or error handling if needed, but for now we rely on .env
    print("Warning: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

class CatalystEngine:
    def __init__(self, df):
        self.df = df
        self.report = {
            "rows": 0,
            "clean_score": 100,
            "missing_values": 0,
            "analysis_sections": {
                "univariate": [],
                "bivariate": [],
                "multivariate": []
            }
        }

    def run(self):
        """Main execution pipeline."""
        self._clean_data()
        self._engineer_features()
        self._generate_visualizations()
        return self.report

    def _clean_data(self):
        """
        Cleans the data:
        - Drops duplicates
        - Fills missing values (Mean for numeric, Mode for categorical)
        - Calculates 'Clean Score' based on initial missingness
        """
        initial_rows = len(self.df)
        missing_count = self.df.isnull().sum().sum()
        total_cells = self.df.size
        
        # Calculate score before cleaning
        if total_cells > 0:
            self.report['clean_score'] = int(100 - (missing_count / total_cells * 100))
        
        self.report['missing_values'] = int(missing_count)

        # Drop duplicates
        self.df.drop_duplicates(inplace=True)

        # Fill missing values
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                self.df[col] = self.df[col].fillna(self.df[col].mean())
            else:
                self.df[col] = self.df[col].fillna(self.df[col].mode()[0] if not self.df[col].mode().empty else "Unknown")
        
        self.report['rows'] = len(self.df)

    def _engineer_features(self):
        """
        Adds smart features:
        - Extracts Month/Year/Day from Datetime columns
        - Text length for string columns
        """
        for col in self.df.columns:
            # Convert to datetime if possible (heuristic)
            if self.df[col].dtype == 'object':
                try:
                    self.df[col] = pd.to_datetime(self.df[col])
                except (ValueError, TypeError):
                    pass
            
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                self.df[f'{col}_Year'] = self.df[col].dt.year
                self.df[f'{col}_Month'] = self.df[col].dt.month_name()
            
            elif pd.api.types.is_string_dtype(self.df[col]):
                # Only if average length is substantial (avoiding categorical codes)
                avg_len = self.df[col].astype(str).map(len).mean()
                if avg_len > 10:
                    self.df[f'{col}_Length'] = self.df[col].astype(str).map(len)

    def _get_gemini_suggestions(self):
        """
        Uses Gemini AI to decide which visualizations are best for this dataset.
        """
        try:
            # Prepare metadata for the prompt
            dtypes = self.df.dtypes.to_string()
            head = self.df.head(5).to_string()
            columns = list(self.df.columns)
            
            prompt = f"""
            You are an expert Data Scientist. I have a dataset with the following columns: {columns}.
            
            Data Types:
            {dtypes}
            
            Sample Data:
            {head}
            
            Analyze this data and generate a comprehensive set of visualizations (aim for 10-15 distinct charts).
            Explore ALL meaningful relationships, distributions, and trends. Do not limit yourself.
            
            Consider these types: 
            - "histogram" (for distributions)
            - "count_plot" (for categorical frequency)
            - "kde" (use "violin" type for density estimation)
            - "time_series" (if date columns exist)
            - "pie" (for composition)
            - "scatter" (for correlations)
            - "box" (for outliers)
            - "heatmap" (for correlations or density)
            - "bar" (for comparisons)

            For each suggestion, provide a JSON object with:
            - "title": A catchy, professional title.
            - "type": One of ["bar", "line", "scatter", "histogram", "box", "violin", "pie", "heatmap"].
            - "x": Column name for X-axis.
            - "y": Column name for Y-axis (optional).
            - "color": Column name for color grouping (optional).
            - "section": One of ["univariate", "bivariate", "multivariate"].
            - "insight": A detailed explanation of what the chart shows (2-3 sentences).
            - "suggestion": Actionable business advice or next steps based on this insight.
            
            Return ONLY a valid JSON array of these objects.
            """
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            # Clean response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text)
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return [] # Fallback to empty list (could implement fallback logic here)

    def _generate_visualizations(self):
        """
        Generates a massive set of visualizations using a Hybrid approach:
        1. Standard Suite: Rule-based generation for ALL columns.
        2. AI Suite: Gemini-powered deep dive for complex insights.
        """
        
        # --- 1. STANDARD SUITE (Guaranteed Volume) ---
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = self.df.select_dtypes(include=['datetime']).columns.tolist()

        # A. Descriptive Stats
        if numeric_cols:
            desc = self.df[numeric_cols].describe().reset_index()
            desc = desc.round(2)
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(desc.columns), fill_color='#1E1E1E', font=dict(color='white', size=12), align='left'),
                cells=dict(values=[desc[k].tolist() for k in desc.columns], fill_color='#f0f0f0', font=dict(color='#1E1E1E', size=11), align='left'))
            ])
            self._add_viz("Descriptive Statistics", fig, "table", "univariate", "Summary statistics for all numerical variables.")

        # B. Correlation Matrix (Multivariate)
        if len(numeric_cols) > 1:
            corr = self.df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, color_continuous_scale='Viridis', title="Feature Correlation")
            self._add_viz("Correlation Matrix", fig, "heatmap", "multivariate", "<b>Standard Analysis:</b> Correlation heatmap showing relationships between all numerical variables.")

        # C. Distributions (Univariate) - Generate for ALL numeric columns
        for col in numeric_cols:
            # Histogram
            fig_hist = px.histogram(self.df, x=col, title=f"Distribution: {col}", color_discrete_sequence=['#39FF14'])
            self._add_viz(f"Dist: {col}", fig_hist, "histogram", "univariate", f"<b>Standard Analysis:</b> Frequency distribution of {col}.")
            
            # Box Plot
            fig_box = px.box(self.df, y=col, title=f"Outliers: {col}", color_discrete_sequence=['#39FF14'])
            self._add_viz(f"Box: {col}", fig_box, "box", "univariate", f"<b>Standard Analysis:</b> Box plot identifying outliers in {col}.")

        # D. Categorical Counts (Univariate) - Generate for ALL categorical columns
        for col in categorical_cols:
            if self.df[col].nunique() < 50: # Skip high cardinality
                fig = px.histogram(self.df, x=col, title=f"Count: {col}", color_discrete_sequence=['#1E1E1E'])
                self._add_viz(f"Count: {col}", fig, "bar", "univariate", f"<b>Standard Analysis:</b> Count plot for {col}.")

        # E. Time Series (Bivariate)
        if datetime_cols and numeric_cols:
            date_col = datetime_cols[0]
            for val_col in numeric_cols[:3]: # Top 3 numeric vs Date
                data = self.df.sort_values(date_col)
                fig = px.line(data, x=date_col, y=val_col, title=f"{val_col} over Time", color_discrete_sequence=['#1E1E1E'])
                self._add_viz(f"Trend: {val_col}", fig, "line", "bivariate", f"<b>Standard Analysis:</b> Time series trend of {val_col}.")

        # --- 2. AI SUITE (Smart Insights) ---
        suggestions = self._get_gemini_suggestions()
        
        if suggestions:
            for item in suggestions:
                try:
                    fig = None
                    title = item.get('title', 'Untitled Chart')
                    viz_type = item.get('type', 'bar')
                    x_col = item.get('x')
                    y_col = item.get('y')
                    color_col = item.get('color')
                    section = item.get('section', 'univariate')
                    
                    # Combine Insight and Suggestion into HTML description
                    insight_text = item.get('insight', '')
                    suggestion_text = item.get('suggestion', '')
                    desc = f"<b>🤖 AI Insight:</b> {insight_text}<br><br><b>🚀 Suggestion:</b> {suggestion_text}"

                    # Validate columns exist
                    if x_col and x_col not in self.df.columns: continue
                    if y_col and y_col not in self.df.columns: continue
                    if color_col and color_col not in self.df.columns: color_col = None

                    # Generate Plotly Figure
                    if viz_type == 'bar' or viz_type == 'count_plot':
                        if y_col:
                            if self.df[x_col].nunique() > 20:
                                data = self.df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(20)
                                fig = px.bar(data, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                            else:
                                fig = px.bar(self.df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                        else:
                            fig = px.histogram(self.df, x=x_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                            fig.update_layout(yaxis_title="Count")
                    
                    elif viz_type == 'line' or viz_type == 'time_series':
                        data = self.df.sort_values(x_col)
                        fig = px.line(data, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=['#1E1E1E'])
                    
                    elif viz_type == 'scatter':
                        fig = px.scatter(self.df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                    
                    elif viz_type == 'histogram':
                        fig = px.histogram(self.df, x=x_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                    
                    elif viz_type == 'box':
                        fig = px.box(self.df, x=x_col, y=y_col, color=color_col, title=title, color_discrete_sequence=['#39FF14'])
                    
                    elif viz_type == 'violin' or viz_type == 'kde':
                        fig = px.violin(self.df, x=x_col, y=y_col, color=color_col, box=True, points='all', title=title, color_discrete_sequence=['#39FF14'])
                    
                    elif viz_type == 'heatmap':
                        if x_col and y_col:
                            fig = px.density_heatmap(self.df, x=x_col, y=y_col, title=title, color_continuous_scale='Viridis')
                        else:
                            corr = self.df.select_dtypes(include=[np.number]).corr()
                            fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale='Viridis')

                    elif viz_type == 'pie':
                        fig = px.pie(self.df, names=x_col, values=y_col, title=title, color_discrete_sequence=px.colors.qualitative.Set3)

                    if fig:
                        self._add_viz(title, fig, viz_type, section, desc)

                except Exception as e:
                    print(f"Error generating chart {item.get('title')}: {e}")
                    continue

    def _add_viz(self, title, fig, type, section, description=""):
        """Helper to format and append visualization."""
        # Apply Neobrutalism styling to Plotly
        fig.update_layout(
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#f0f0f0',
            font=dict(family='Courier New, monospace', color='#1E1E1E'),
            title_font=dict(size=20, family='Inter, sans-serif', color='#1E1E1E'),
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(showgrid=True, gridcolor='#1E1E1E', gridwidth=1, linecolor='#1E1E1E', linewidth=2),
            yaxis=dict(showgrid=True, gridcolor='#1E1E1E', gridwidth=1, linecolor='#1E1E1E', linewidth=2),
        )
        if type not in ['heatmap', 'table', 'pie']:
            fig.update_traces(marker_line_width=2, marker_line_color='#1E1E1E')
        
        # Ensure section exists
        if section not in self.report['analysis_sections']:
            section = 'univariate'

        self.report['analysis_sections'][section].append({
            "title": title,
            "type": type,
            "description": description,
            "json": json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        })
