from flask import Flask, render_template, request, jsonify, session
import os
import json
from datetime import datetime
import hashlib
import csv
from query_engine import ZoningQueryEngine

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
query_engine = ZoningQueryEngine()

# Track usage for counties
usage_log = []

# Audit log for government tracking
audit_log = []

# Mock parcel database
parcel_database = {
    '123-45-6789': {
        'address': '42100 Raspberry Drive, Ashburn, VA 20148',
        'base_zoning': 'AR-1 (Agricultural Rural-1)',
        'overlays': 'Limestone Overlay District',
        'special_districts': 'None',
        'previous_permits': 'SUP-2023-001: Home Business approved'
    },
    '234-56-7890': {
        'address': '123 Main Street, Leesburg, VA 20176',
        'base_zoning': 'TR-10 (Transitional Residential-10)',
        'overlays': 'None',
        'special_districts': 'Historic District',
        'previous_permits': 'None'
    },
    '345-67-8901': {
        'address': '5000 Commerce Center Dr, Dulles, VA 20166',
        'base_zoning': 'PD-CC (Planned Development-Commercial Center)',
        'overlays': 'None',
        'special_districts': 'None',
        'previous_permits': 'SP-2022-005: Sign variance approved'
    }
}

@app.route('/')
def index():
    # Redirect to staff portal for government use
    return render_template('staff_portal.html')

@app.route('/public')
def public_interface():
    # Keep the original public interface for reference
    return render_template('index.html')

@app.route('/audit')
def audit_log_viewer():
    # Audit log viewer for administrators
    return render_template('audit_log.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question')
        county = data.get('county', 'loudoun')
        metadata = data.get('metadata', {})

        # Log the query for analytics
        usage_log.append({
            'question': question,
            'county': county,
            'timestamp': datetime.now().isoformat()
        })

        # Create audit entry for government tracking
        if metadata:
            audit_entry = {
                'session_id': metadata.get('sessionId'),
                'staff_id': metadata.get('staffId'),
                'parcel_id': metadata.get('parcelId'),
                'category': metadata.get('category'),
                'case_reference': metadata.get('caseReference'),
                'question': question,
                'timestamp': metadata.get('timestamp', datetime.now().isoformat())
            }

        # Get answer with enhanced context
        result = query_engine.answer_question(question, county)
        
        # Add parcel context to response if available
        parcel_id = metadata.get('parcelId') if metadata else None
        if parcel_id and parcel_id in parcel_database:
            result['parcel_context'] = parcel_database[parcel_id]
        
        # Complete audit entry with response
        if metadata:
            audit_entry['response'] = result.get('answer', 'No response generated')
            audit_entry['citations'] = result.get('citations', [])
            audit_log.append(audit_entry)
            
            # Save audit log to file (in production, this would go to a database)
            save_audit_log(audit_entry)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'queries_processed': len(usage_log),
        'audit_entries': len(audit_log)
    })

@app.route('/api/parcel/<parcel_id>', methods=['GET'])
def get_parcel_info(parcel_id):
    """API endpoint to get parcel information"""
    if parcel_id in parcel_database:
        return jsonify(parcel_database[parcel_id])
    else:
        return jsonify({'error': 'Parcel not found'}), 404

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data for dashboard"""
    # Calculate statistics
    today = datetime.now().date()
    today_queries = [q for q in usage_log if datetime.fromisoformat(q['timestamp']).date() == today]
    
    # Mock data for demo - in production, this would be calculated from real data
    analytics = {
        'queries_today': len(today_queries) + 47,  # Mock baseline + actual
        'avg_time_saved': '~12 min',
        'total_time_saved': f'{(len(today_queries) + 47) * 12 / 60:.1f} hrs',
        'top_sections': [
            {'section': 'Section 5-600: Setback Requirements', 'count': 12},
            {'section': 'Section 3-102: Permitted Uses in AR-1', 'count': 9},
            {'section': 'Section 7-200: Special Exception Procedures', 'count': 7},
            {'section': 'Section 4-1500: Limestone Overlay District', 'count': 6},
            {'section': 'Section 5-900: Height Regulations', 'count': 5}
        ]
    }
    
    return jsonify(analytics)

@app.route('/api/audit', methods=['GET'])
def get_audit_log():
    """Get audit log entries - restricted to authorized staff"""
    # In production, this would have authentication/authorization
    return jsonify(audit_log[-100:])  # Return last 100 entries

@app.route('/api/export', methods=['POST'])
def export_response():
    """Export response as PDF (placeholder)"""
    data = request.json
    # In production, this would generate an actual PDF
    return jsonify({
        'status': 'success',
        'message': 'PDF export functionality will be implemented',
        'session_id': data.get('session_id')
    })

def save_audit_log(entry):
    """Save audit log entry to file (in production, use database)"""
    try:
        # Create audit_logs directory if it doesn't exist
        os.makedirs('audit_logs', exist_ok=True)
        
        # Save to daily audit file
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f'audit_logs/audit_{date_str}.json'
        
        # Append to file
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(entry)
        
        with open(filename, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error saving audit log: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)