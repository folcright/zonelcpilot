from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
from datetime import datetime, timedelta
import hashlib
import csv
from functools import wraps
from query_engine import ZoningQueryEngine

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
query_engine = ZoningQueryEngine()

# Track usage for counties - separated by mode
public_usage_log = []
staff_usage_log = []

# Audit log for government tracking
audit_log = []

# Mock staff credentials (in production, use proper authentication)
STAFF_CREDENTIALS = {
    'jsmith': {'password': 'planning2024', 'name': 'John Smith', 'role': 'Senior Planner'},
    'mjones': {'password': 'zoning2024', 'name': 'Mary Jones', 'role': 'Zoning Administrator'},
    'rlopez': {'password': 'staff2024', 'name': 'Robert Lopez', 'role': 'Planning Technician'},
    'admin': {'password': 'admin2024', 'name': 'Administrator', 'role': 'System Admin'}
}

# Mock parcel database
parcel_database = {
    '123-45-6789': {
        'address': '42100 Raspberry Drive, Ashburn, VA 20148',
        'base_zoning': 'AR-1 (Agricultural Rural-1)',
        'overlays': 'Limestone Overlay District',
        'special_districts': 'None',
        'previous_permits': 'SUP-2023-001: Home Business approved',
        'history': [
            {'date': '2023-03-15', 'action': 'Special Use Permit Approved', 'details': 'Home business operation'},
            {'date': '2022-11-20', 'action': 'Building Permit Issued', 'details': 'Detached garage construction'},
            {'date': '2021-06-10', 'action': 'Variance Denied', 'details': 'Setback reduction request'}
        ]
    },
    '234-56-7890': {
        'address': '123 Main Street, Leesburg, VA 20176',
        'base_zoning': 'TR-10 (Transitional Residential-10)',
        'overlays': 'None',
        'special_districts': 'Historic District',
        'previous_permits': 'None',
        'history': [
            {'date': '2023-08-01', 'action': 'Site Plan Approved', 'details': 'Single family dwelling'},
            {'date': '2023-01-15', 'action': 'Proffer Amendment', 'details': 'Modified landscaping requirements'}
        ]
    },
    '345-67-8901': {
        'address': '5000 Commerce Center Dr, Dulles, VA 20166',
        'base_zoning': 'PD-CC (Planned Development-Commercial Center)',
        'overlays': 'None',
        'special_districts': 'None',
        'previous_permits': 'SP-2022-005: Sign variance approved',
        'history': [
            {'date': '2022-09-20', 'action': 'Sign Variance Approved', 'details': 'Height variance for monument sign'},
            {'date': '2021-12-01', 'action': 'Site Plan Modification', 'details': 'Parking lot expansion'}
        ]
    }
}

# Decorator for requiring staff login
def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'staff_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main entry point with mode selection"""
    mode = session.get('mode', 'public')
    if mode == 'staff' and 'staff_id' in session:
        return render_template('staff_portal.html')
    else:
        session['mode'] = 'public'
        return render_template('public_portal.html')

@app.route('/public')
def public_interface():
    """Dedicated public access point"""
    session['mode'] = 'public'
    return render_template('public_portal.html')

@app.route('/staff')
def staff_interface():
    """Staff portal entry point"""
    if 'staff_id' not in session:
        return redirect(url_for('login'))
    session['mode'] = 'staff'
    return render_template('staff_portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Staff login page"""
    if request.method == 'POST':
        data = request.json
        staff_id = data.get('staff_id')
        password = data.get('password')
        
        if staff_id in STAFF_CREDENTIALS and STAFF_CREDENTIALS[staff_id]['password'] == password:
            session['staff_id'] = staff_id
            session['staff_name'] = STAFF_CREDENTIALS[staff_id]['name']
            session['staff_role'] = STAFF_CREDENTIALS[staff_id]['role']
            session['mode'] = 'staff'
            session.permanent = True
            
            # Log the login
            audit_log.append({
                'event': 'staff_login',
                'staff_id': staff_id,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Staff logout"""
    if 'staff_id' in session:
        audit_log.append({
            'event': 'staff_logout',
            'staff_id': session.get('staff_id'),
            'timestamp': datetime.now().isoformat()
        })
    
    session.clear()
    return redirect(url_for('index'))

@app.route('/toggle_mode')
def toggle_mode():
    """Toggle between public and staff mode"""
    current_mode = session.get('mode', 'public')
    
    if current_mode == 'public':
        # Switching to staff mode requires login
        if 'staff_id' not in session:
            return redirect(url_for('login'))
        session['mode'] = 'staff'
        return redirect(url_for('staff_interface'))
    else:
        # Switch to public mode
        session['mode'] = 'public'
        return redirect(url_for('public_interface'))

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question')
        county = data.get('county', 'loudoun')
        metadata = data.get('metadata', {})
        mode = session.get('mode', 'public')
        
        # Differentiated logging based on mode
        if mode == 'staff':
            # Staff query - full audit logging
            staff_usage_log.append({
                'question': question,
                'county': county,
                'staff_id': session.get('staff_id'),
                'staff_name': session.get('staff_name'),
                'timestamp': datetime.now().isoformat(),
                'mode': 'staff'
            })
            
            # Create detailed audit entry
            if metadata:
                audit_entry = {
                    'session_id': metadata.get('sessionId'),
                    'staff_id': session.get('staff_id'),
                    'staff_name': session.get('staff_name'),
                    'parcel_id': metadata.get('parcelId'),
                    'category': metadata.get('category'),
                    'case_reference': metadata.get('caseReference'),
                    'question': question,
                    'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                    'mode': 'staff'
                }
        else:
            # Public query - self-service analytics
            public_usage_log.append({
                'question': question,
                'county': county,
                'timestamp': datetime.now().isoformat(),
                'mode': 'public',
                'session_id': request.headers.get('X-Session-Id', 'unknown')
            })
            
            # Simplified logging for public queries
            save_public_log({
                'question': question,
                'timestamp': datetime.now().isoformat(),
                'county': county
            })

        # Get answer with enhanced context
        result = query_engine.answer_question(question, county)
        
        # Add mode-specific enhancements
        if mode == 'staff':
            # Add parcel context for staff
            parcel_id = metadata.get('parcelId') if metadata else None
            if parcel_id and parcel_id in parcel_database:
                result['parcel_context'] = parcel_database[parcel_id]
            
            # Add precedent search capability
            result['precedents'] = search_precedents(question)
            
            # Complete audit entry with response
            if metadata:
                audit_entry['response'] = result.get('answer', 'No response generated')
                audit_entry['citations'] = result.get('citations', [])
                audit_log.append(audit_entry)
                save_audit_log(audit_entry)
        else:
            # Add disclaimer for public users
            result['disclaimer'] = "This information is for educational purposes only. For official determinations, please contact the Planning Department at (703) 777-0246 or visit us in person."
            
            # Simplify response for public
            result['simplified'] = True

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/escalate', methods=['POST'])
def escalate_to_staff():
    """Escalate a public query to staff for review"""
    data = request.json
    escalation = {
        'question': data.get('question'),
        'user_context': data.get('context'),
        'timestamp': datetime.now().isoformat(),
        'status': 'pending_review',
        'escalation_id': hashlib.md5(f"{data.get('question')}_{datetime.now()}".encode()).hexdigest()[:8]
    }
    
    # Save escalation for staff review
    save_escalation(escalation)
    
    return jsonify({
        'success': True,
        'escalation_id': escalation['escalation_id'],
        'message': 'Your query has been submitted for staff review. Reference number: ' + escalation['escalation_id']
    })

@app.route('/precedents/search', methods=['POST'])
@staff_required
def search_precedents_endpoint():
    """Search for precedent cases"""
    data = request.json
    query = data.get('query')
    precedents = search_precedents(query)
    return jsonify({'precedents': precedents})

@app.route('/health')
def health():
    mode = session.get('mode', 'public')
    return jsonify({
        'status': 'healthy',
        'mode': mode,
        'public_queries': len(public_usage_log),
        'staff_queries': len(staff_usage_log),
        'audit_entries': len(audit_log)
    })

@app.route('/api/parcel/<parcel_id>', methods=['GET'])
def get_parcel_info(parcel_id):
    """API endpoint to get parcel information"""
    if parcel_id in parcel_database:
        # Return different levels of detail based on mode
        mode = session.get('mode', 'public')
        parcel_info = parcel_database[parcel_id].copy()
        
        if mode == 'public':
            # Remove sensitive history for public users
            parcel_info.pop('history', None)
        
        return jsonify(parcel_info)
    else:
        return jsonify({'error': 'Parcel not found'}), 404

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data for dashboard"""
    today = datetime.now().date()
    
    # Calculate statistics for both modes
    today_public = [q for q in public_usage_log if datetime.fromisoformat(q['timestamp']).date() == today]
    today_staff = [q for q in staff_usage_log if datetime.fromisoformat(q['timestamp']).date() == today]
    
    # Calculate self-service deflection rate
    total_queries = len(today_public) + len(today_staff) + 100  # Mock baseline
    public_queries = len(today_public) + 73  # Mock baseline
    deflection_rate = (public_queries / total_queries * 100) if total_queries > 0 else 0
    
    analytics = {
        'queries_today': len(today_public) + len(today_staff) + 47,
        'public_queries_today': len(today_public) + 35,
        'staff_queries_today': len(today_staff) + 12,
        'deflection_rate': f'{deflection_rate:.1f}%',
        'avg_time_saved': '~12 min',
        'avg_response_time': '4 min',
        'prev_response_time': '16 min',
        'violation_rate_change': -40,
        'total_time_saved': f'{(len(today_staff) + 12) * 12 / 60:.1f} hrs',
        'top_public_queries': [
            {'query': 'Can I build a shed in my backyard?', 'count': 23},
            {'query': 'What are the setback requirements?', 'count': 18},
            {'query': 'Do I need a permit for a fence?', 'count': 15}
        ],
        'top_staff_sections': [
            {'section': 'Section 5-600: Setback Requirements', 'count': 12},
            {'section': 'Section 3-102: Permitted Uses in AR-1', 'count': 9},
            {'section': 'Section 7-200: Special Exception Procedures', 'count': 7}
        ]
    }
    
    return jsonify(analytics)

@app.route('/commissioner')
@staff_required
def commissioner_dashboard():
    """Commissioner dashboard with high-level metrics"""
    return render_template('commissioner_dashboard.html')

@app.route('/api/commissioner/metrics', methods=['GET'])
@staff_required
def get_commissioner_metrics():
    """Get metrics for commissioner dashboard"""
    # Calculate comprehensive metrics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Mock data for demonstration
    metrics = {
        'deflection_rate': 73,
        'avg_staff_response': 4,
        'prev_staff_response': 16,
        'violation_rate_change': -40,
        'weekly_trends': {
            'dates': [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)],
            'public': [45, 52, 48, 61, 55, 58, 63],
            'staff': [12, 15, 11, 14, 13, 16, 12]
        },
        'query_categories': {
            'labels': ['Setbacks', 'Permits', 'Zoning', 'Uses', 'Variances'],
            'public': [32, 28, 18, 15, 7],
            'staff': [15, 12, 25, 30, 18]
        },
        'efficiency_gains': {
            'time_saved_weekly': 84,  # hours
            'queries_deflected': 341,
            'cost_savings': 6820  # dollars
        }
    }
    
    return jsonify(metrics)

@app.route('/audit')
@staff_required
def audit_log_viewer():
    """Audit log viewer for administrators"""
    return render_template('audit_log.html')

@app.route('/api/audit', methods=['GET'])
@staff_required
def get_audit_log():
    """Get audit log entries - restricted to authorized staff"""
    return jsonify(audit_log[-100:])  # Return last 100 entries

@app.route('/api/export', methods=['POST'])
@staff_required
def export_response():
    """Export response as official determination"""
    data = request.json
    
    # Create official determination document
    determination = {
        'determination_id': hashlib.md5(f"{data.get('session_id')}_{datetime.now()}".encode()).hexdigest()[:10].upper(),
        'issued_by': session.get('staff_name'),
        'issued_date': datetime.now().isoformat(),
        'parcel_id': data.get('parcel_id'),
        'question': data.get('question'),
        'determination': data.get('response'),
        'citations': data.get('citations'),
        'disclaimer': 'This determination is based on the information provided and current zoning ordinances. Subject to change based on amendments or additional information.'
    }
    
    # In production, this would generate an actual PDF
    return jsonify({
        'status': 'success',
        'determination_id': determination['determination_id'],
        'message': 'Official determination has been generated',
        'document': determination
    })

@app.route('/api/analytics/event', methods=['POST'])
def track_analytics_event():
    """Track analytics events from the public portal"""
    data = request.json
    event_name = data.get('event')
    event_data = data.get('data', {})
    timestamp = data.get('timestamp', datetime.now().isoformat())
    session_id = data.get('sessionId')
    
    # Store analytics event
    analytics_event = {
        'event': event_name,
        'data': event_data,
        'timestamp': timestamp,
        'session_id': session_id,
        'mode': 'public'
    }
    
    # Add to public usage log for tracking
    public_usage_log.append(analytics_event)
    
    # Track specific events for metrics
    if event_name == 'wizard_started':
        # Track wizard starts by category
        pass
    elif event_name == 'compliance_check':
        # Track compliance checks
        pass
    elif event_name == 'abandoned':
        # Track abandoned flows
        pass
    
    return jsonify({'status': 'success', 'tracked': True})

def search_precedents(query):
    """Search for precedent cases (mock implementation)"""
    # Mock precedent data
    precedents = [
        {
            'case_id': 'SP-2023-045',
            'date': '2023-06-15',
            'subject': 'Setback variance for AR-1 property',
            'decision': 'Approved with conditions',
            'relevance': 0.85
        },
        {
            'case_id': 'SUP-2023-012',
            'date': '2023-03-20',
            'subject': 'Home business special use permit',
            'decision': 'Approved',
            'relevance': 0.78
        },
        {
            'case_id': 'VAR-2022-089',
            'date': '2022-11-10',
            'subject': 'Height variance for accessory structure',
            'decision': 'Denied',
            'relevance': 0.65
        }
    ]
    
    # Filter by relevance (mock implementation)
    return [p for p in precedents if p['relevance'] > 0.6]

def save_audit_log(entry):
    """Save audit log entry to file (in production, use database)"""
    try:
        os.makedirs('audit_logs', exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f'audit_logs/staff_audit_{date_str}.json'
        
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

def save_public_log(entry):
    """Save public query log for analytics"""
    try:
        os.makedirs('public_logs', exist_ok=True)
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f'public_logs/self_service_{date_str}.json'
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(entry)
        
        with open(filename, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error saving public log: {e}")

def save_escalation(escalation):
    """Save escalated query for staff review"""
    try:
        os.makedirs('escalations', exist_ok=True)
        filename = 'escalations/pending_escalations.json'
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                escalations = json.load(f)
        else:
            escalations = []
        
        escalations.append(escalation)
        
        with open(filename, 'w') as f:
            json.dump(escalations, f, indent=2)
    except Exception as e:
        print(f"Error saving escalation: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)