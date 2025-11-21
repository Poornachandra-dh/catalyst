from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from analysis_engine import CatalystEngine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload dir exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            # Read file based on extension
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            elif filepath.endswith('.json'):
                df = pd.read_json(filepath)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400

            # Run Catalyst Engine
            engine = CatalystEngine(df)
            report = engine.run()
            
            # Return report + preview of cleaned data (first 5 rows)
            preview = df.head(5).to_dict(orient='records')
            report['preview'] = preview
            
            return jsonify(report)

        except Exception as e:
            import traceback
            with open('error.log', 'w') as f:
                f.write(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
