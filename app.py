from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
from query_engine import ZoningQueryEngine

app = Flask(__name__)
query_engine = ZoningQueryEngine()

# Track usage for counties
usage_log = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question')
        county = data.get('county', 'loudoun')

        # Log the query
        usage_log.append({
            'question': question,
            'county': county,
            'timestamp': datetime.now().isoformat()
        })

        # Get answer
        result = query_engine.answer_question(question, county)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'queries_processed': len(usage_log)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)