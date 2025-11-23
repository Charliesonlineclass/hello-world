#!/usr/bin/env python3
"""J3 Interior Design - REST API Server"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from decimal import Decimal
import os
import json

from lead_qualifier import LeadQualifier, LeadRepository, LeadPriority, LeadStatus, create_lead_from_form

app = Flask(__name__)
CORS(app)

lead_qualifier = LeadQualifier()
lead_repository = LeadRepository()

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal): return float(obj)
        if isinstance(obj, datetime): return obj.isoformat()
        if hasattr(obj, 'value'): return obj.value
        return super().default(obj)

app.json_encoder = CustomEncoder

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'J3 API', 'timestamp': datetime.now().isoformat()})

@app.route('/api/leads', methods=['POST'])
def create_lead():
    data = request.get_json()
    if not data: return jsonify({'error': 'No data'}), 400

    lead = create_lead_from_form(data)
    lead = lead_repository.save(lead)
    lead = lead_qualifier.qualify_lead(lead)
    routing = lead_qualifier.get_routing_action(lead)

    return jsonify({
        'success': True, 'lead_id': lead.id, 'score': lead.score.total_score,
        'priority': lead.score.priority.value, 'message': routing.get('customer_response')
    }), 201

@app.route('/api/leads')
def get_leads():
    leads = lead_repository.get_all()
    return jsonify({'success': True, 'count': len(leads), 'leads': [
        {'id': l.id, 'name': l.contact.full_name, 'project': l.project.project_type,
         'score': l.score.total_score, 'priority': l.score.priority.value} for l in leads
    ]})

@app.route('/api/dashboard/stats')
def dashboard_stats():
    leads = lead_repository.get_all()
    return jsonify({
        'success': True,
        'stats': {
            'total_leads': len(leads),
            'hot_leads': len([l for l in leads if l.score.priority == LeadPriority.HOT]),
            'warm_leads': len([l for l in leads if l.score.priority == LeadPriority.WARM]),
            'estimated_pipeline': sum(lead_qualifier.BUDGET_MIDPOINTS.get(l.project.budget_range, 15000)
                                     for l in leads if l.score.priority in [LeadPriority.HOT, LeadPriority.WARM])
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').lower()

    if any(g in message for g in ['hi', 'hello', 'hey']):
        response = "Hello! Welcome to J3 Interior Design. What type of project are you considering?"
    elif 'kitchen' in message:
        response = "Kitchen remodels are our specialty! Are you thinking full renovation or cabinet refacing?"
    elif 'bathroom' in message:
        response = "Bathroom renovations transform your daily routine. Full remodel or tub-to-shower conversion?"
    elif any(w in message for w in ['cost', 'price', 'budget']):
        response = "Kitchens: $15k-$75k. Bathrooms: $8k-$35k. Flooring: $5k-$30k. What's your budget range?"
    else:
        response = "I can help! Tell me about your project or ask about pricing, timeline, or scheduling."

    return jsonify({'success': True, 'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG', 'true') == 'true')
