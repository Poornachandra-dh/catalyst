# Catalyst - AI-Powered Data Analysis Dashboard

Catalyst is a modern, Flask-based SaaS MVP designed to democratize data analysis. It transforms raw datasets into actionable insights using advanced statistical methods and AI-driven visualization.

## 🚀 Features

*   **Smart Data Cleaning**: Automatically handles missing values and duplicates.
*   **AI-Powered Insights**: Integrates **Google Gemini AI** to generate intelligent visualizations and business suggestions.
*   **Hybrid Visualization Engine**:
    *   **Standard Suite**: Guarantees histograms, box plots, and bar charts for all columns.
    *   **AI Suite**: Generates deep-dive charts (KDE, Time Series, Heatmaps) based on data context.
*   **Neobrutalism UI**: A bold, high-contrast design system for a modern user experience.
*   **Interactive Dashboard**: Built with Plotly.js for dynamic, responsive charts.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask
*   **Data Processing**: Pandas, NumPy
*   **AI/LLM**: Google Gemini (via `google-generativeai`)
*   **Visualization**: Plotly (Python & JS)
*   **Frontend**: HTML5, CSS3 (Neobrutalism), JavaScript

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Poornachandra-dh/catalyst.git
    cd catalyst
    ```

2.  **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables**:
    *   Create a `.env` file in the root directory.
    *   Add your Gemini API key:
        ```
        GEMINI_API_KEY=your_api_key_here
        ```

## 🏃‍♂️ Usage

1.  **Run the application**:
    ```bash
    python app.py
    ```

2.  **Open your browser**:
    Navigate to `http://127.0.0.1:5000`

3.  **Upload a CSV file**:
    *   The system will clean the data.
    *   It will generate a comprehensive report with standard and AI-suggested charts.
    *   Explore the "Univariate", "Bivariate", and "Multivariate" sections.

## 📂 Project Structure

```
catalyst/
├── static/
│   ├── style.css        # Neobrutalism styles
│   └── script.js        # Dashboard logic
├── templates/
│   └── index.html       # Main dashboard template
├── analysis_engine.py   # Core logic (Data cleaning, Feature Eng., AI integration)
├── app.py               # Flask server
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.


