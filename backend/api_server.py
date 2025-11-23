#!/usr/bin/env python3
"""
J3 Interior Design - REST API Server

PRODUCTION-READY VERSION with:
- Proper imports matching lead_qualifier.py
- Full error handling
- JSON serialization for all types
- CORS support for cross-origin requests
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from decimal import Decimal
import os
import json
import traceback
import logging

from lead_qualifier import LeadQualifier, LeadRepository, Lead, LeadPriority, LeadStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('J3API')

app = Flask(__name__)
CORS(app)

# Initialize services
lead_qualifier = LeadQualifier()
lead_repository = LeadRepository(data_file='data/leads.json')

# Budget midpoints for pipeline estimation
BUDGET_MIDPOINTS = {
    'kitchen': 35000,
    'bathroom': 20000,
    'flooring': 15000,
    'storm': 25000,
    'other': 15000,
}


class CustomEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, Decimal, and enums"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'value'):  # Enum types
            return obj.value
        return super().default(obj)


app.json_encoder = CustomEncoder


def estimate_budget(lead: Lead) -> int:
    """Estimate budget from lead data"""
    if lead.budget_max > 0:
        return lead.budget_max
    if lead.budget_min > 0:
        return lead.budget_min
    return BUDGET_MIDPOINTS.get(lead.project_type.lower(), 15000)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'J3 Interior Design API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/leads', methods=['POST'])
def create_lead():
    """
    Create and qualify a new lead from form submission.

    Expected JSON body:
    {
        "name": "John Smith",
        "email": "john@email.com",
        "phone": "(713) 555-1234",
        "address": "123 Main St",
        "zip": "77002",
        "project_type": "kitchen",
        "budget": "50k",
        "timeline": "asap",
        "description": "Kitchen remodel",
        "photos": false
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Validate required fields
        required = ['name', 'email', 'phone']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400

        # Qualify the lead
        lead, score, priority = lead_qualifier.qualify_lead(data)

        # Save to repository
        lead_repository.save(lead)

        # Generate customer response based on priority
        if priority == LeadPriority.HOT:
            customer_response = f"Thank you {lead.name}! Your project is a great fit. We'll call you within 4 hours."
        elif priority == LeadPriority.WARM:
            customer_response = f"Thank you {lead.name}! We'll contact you within 24 hours to discuss your project."
        elif priority == LeadPriority.LUKEWARM:
            customer_response = f"Thank you {lead.name}! A team member will reach out within 2 business days."
        elif priority == LeadPriority.DISQUALIFIED:
            if lead.disqualification_reason == 'outside_service_area':
                customer_response = f"Thank you for your interest! Unfortunately, your location is outside our current service area (Houston + 120 miles)."
            else:
                customer_response = "Thank you for your interest! We'll review your submission and be in touch if we can help."
        else:
            customer_response = f"Thank you {lead.name}! We've received your request and will be in touch soon."

        logger.info(f"Lead created: {lead.lead_id} - Score: {score}, Priority: {priority.value}")

        return jsonify({
            'success': True,
            'lead_id': lead.lead_id,
            'score': score,
            'priority': priority.value,
            'message': customer_response,
            'details': {
                'geo_score': lead.geo_score,
                'budget_score': lead.budget_score,
                'timeline_score': lead.timeline_score,
                'clarity_score': lead.clarity_score,
                'contact_score': lead.contact_score,
                'distance_miles': lead.distance_miles
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating lead: {e}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/leads', methods=['GET'])
def get_leads():
    """Get all leads with optional filtering"""
    try:
        # Optional filters
        priority_filter = request.args.get('priority')
        status_filter = request.args.get('status')

        leads = lead_repository.get_all()

        # Apply filters
        if priority_filter:
            try:
                priority = LeadPriority(priority_filter.lower())
                leads = [l for l in leads if l.priority == priority]
            except ValueError:
                pass

        if status_filter:
            try:
                status = LeadStatus(status_filter.lower())
                leads = [l for l in leads if l.status == status]
            except ValueError:
                pass

        return jsonify({
            'success': True,
            'count': len(leads),
            'leads': [{
                'id': l.lead_id,
                'name': l.name,
                'email': l.email,
                'phone': l.phone,
                'project_type': l.project_type,
                'score': l.score,
                'priority': l.priority.value,
                'status': l.status.value,
                'budget': f"${l.budget_min:,}" + (f"-${l.budget_max:,}" if l.budget_max != l.budget_min else ""),
                'distance_miles': l.distance_miles,
                'created_at': l.created_at.isoformat(),
                'next_followup': l.next_followup.isoformat() if l.next_followup else None
            } for l in leads]
        })

    except Exception as e:
        logger.error(f"Error getting leads: {e}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/leads/<lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get a single lead by ID"""
    try:
        lead = lead_repository.get(lead_id)
        if not lead:
            return jsonify({'success': False, 'error': 'Lead not found'}), 404

        return jsonify({
            'success': True,
            'lead': {
                'id': lead.lead_id,
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'address': lead.address,
                'city': lead.city,
                'zip_code': lead.zip_code,
                'project_type': lead.project_type,
                'budget_input': lead.budget_input,
                'budget_min': lead.budget_min,
                'budget_max': lead.budget_max,
                'timeline': lead.timeline,
                'description': lead.description,
                'has_photos': lead.has_photos,
                'source': lead.source,
                'score': lead.score,
                'geo_score': lead.geo_score,
                'budget_score': lead.budget_score,
                'timeline_score': lead.timeline_score,
                'clarity_score': lead.clarity_score,
                'contact_score': lead.contact_score,
                'distance_miles': lead.distance_miles,
                'priority': lead.priority.value,
                'status': lead.status.value,
                'disqualification_reason': lead.disqualification_reason,
                'created_at': lead.created_at.isoformat(),
                'next_followup': lead.next_followup.isoformat() if lead.next_followup else None,
                'notes': lead.notes
            }
        })

    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/leads/<lead_id>/status', methods=['PUT'])
def update_lead_status(lead_id):
    """Update lead status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        note = data.get('note', '')

        if not new_status:
            return jsonify({'success': False, 'error': 'Status required'}), 400

        try:
            status = LeadStatus(new_status.lower())
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Valid values: {[s.value for s in LeadStatus]}'
            }), 400

        lead = lead_repository.update_status(lead_id, status, note)
        if not lead:
            return jsonify({'success': False, 'error': 'Lead not found'}), 404

        logger.info(f"Lead {lead_id} status updated to {status.value}")

        return jsonify({
            'success': True,
            'lead_id': lead_id,
            'status': status.value,
            'message': f'Status updated to {status.value}'
        })

    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        leads = lead_repository.get_all()

        hot_leads = [l for l in leads if l.priority == LeadPriority.HOT]
        warm_leads = [l for l in leads if l.priority == LeadPriority.WARM]
        pipeline_leads = hot_leads + warm_leads

        # Calculate pipeline value
        pipeline_value = sum(estimate_budget(l) for l in pipeline_leads)

        # Appointments (leads with consultation scheduled)
        appointments = [l for l in leads if l.status == LeadStatus.CONSULTATION_SCHEDULED]

        return jsonify({
            'success': True,
            'stats': {
                'total_leads': len(leads),
                'hot_leads': len(hot_leads),
                'warm_leads': len(warm_leads),
                'lukewarm_leads': len([l for l in leads if l.priority == LeadPriority.LUKEWARM]),
                'cold_leads': len([l for l in leads if l.priority == LeadPriority.COLD]),
                'disqualified': len([l for l in leads if l.priority == LeadPriority.DISQUALIFIED]),
                'appointments': len(appointments),
                'estimated_pipeline': pipeline_value
            }
        })

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint for website widget"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()

        # Simple keyword-based responses
        if any(g in message for g in ['hi', 'hello', 'hey']):
            response = "Hello! Welcome to J3 Interior Design. What type of project are you considering? Kitchen, bathroom, flooring, or something else?"
        elif 'kitchen' in message:
            response = "Kitchen remodels are our specialty! Pricing ranges from $15,000 for updates to $75,000+ for luxury renovations. Are you thinking full renovation or cabinet refacing?"
        elif 'bathroom' in message:
            response = "Bathroom renovations transform your daily routine! Ranges from $8,000 to $35,000+. Full remodel or tub-to-shower conversion?"
        elif 'flooring' in message:
            response = "Flooring makes a huge impact! We offer hardwood, tile, luxury vinyl, and more. Starting at $5,000 for most projects."
        elif 'storm' in message or 'damage' in message:
            response = "I'm sorry about the damage. We specialize in storm restoration and work directly with insurance companies. Have you filed a claim yet?"
        elif any(w in message for w in ['cost', 'price', 'budget', 'much']):
            response = "General ranges: Kitchens $15k-$75k, Bathrooms $8k-$35k, Flooring $5k-$30k. What project are you considering?"
        elif any(w in message for w in ['schedule', 'appointment', 'consult', 'meet']):
            response = "I'd love to help schedule your free consultation! What's your name and the best phone number to reach you?"
        elif any(w in message for w in ['time', 'long', 'duration']):
            response = "Project timelines vary: Kitchen remodels typically take 4-8 weeks, bathrooms 2-4 weeks, and flooring 1-2 weeks. We'll give you an exact timeline during your free consultation."
        else:
            response = "I can help with your project! Tell me what you're considering, or ask about pricing, timeline, or scheduling a free consultation. You can also call us at (713) 555-0123."

        return jsonify({
            'success': True,
            'response': response
        })

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({
            'success': True,
            'response': "Thanks for your message! For immediate assistance, please call (713) 555-0123."
        })


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    logger.info(f"Starting J3 API Server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
