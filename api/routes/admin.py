"""
SCORPION AI - Admin API Routes
Handle admin dashboard endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crm.database import get_connection, backup_database, get_database_stats
from crm.leads import LeadManager
from crm.clients import ClientManager
from crm.projects import ProjectManager
from crm.communications import CommunicationManager

router = APIRouter()
lead_manager = LeadManager()
client_manager = ClientManager()
project_manager = ProjectManager()
comm_manager = CommunicationManager()


@router.get("/dashboard")
async def get_dashboard():
    """Get overview dashboard statistics"""
    lead_stats = lead_manager.get_pipeline_stats()
    client_stats = client_manager.get_client_stats()
    project_stats = project_manager.get_project_stats()
    db_stats = get_database_stats()

    # Get recent activity
    recent_activity = comm_manager.get_recent_activity(10)

    # Get top clients by revenue
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, company, tier, balance_paid
            FROM clients
            ORDER BY balance_paid DESC
            LIMIT 5
        """)
        top_clients = [dict(row) for row in cursor.fetchall()]

    return {
        "overview": {
            "total_leads": lead_stats['total'],
            "active_clients": client_stats['active'],
            "active_projects": project_stats['by_status'].get('active', 0),
            "total_revenue": client_stats['total_revenue']
        },
        "leads": {
            "total": lead_stats['total'],
            "by_status": lead_stats['by_status'],
            "conversion_rate": lead_stats['conversion_rate']
        },
        "clients": {
            "total": client_stats['total'],
            "by_tier": client_stats['by_tier'],
            "fully_owned": client_stats['fully_owned']
        },
        "projects": {
            "total": project_stats['total'],
            "by_status": project_stats['by_status'],
            "overdue": project_stats['overdue_count']
        },
        "recent_activity": recent_activity[:10],
        "top_clients": top_clients
    }


@router.get("/revenue")
async def get_revenue_metrics():
    """Get revenue metrics and projections"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Total revenue
        cursor.execute("SELECT SUM(balance_paid) FROM clients")
        total_revenue = cursor.fetchone()[0] or 0

        # Monthly recurring revenue (active clients * monthly rate)
        cursor.execute("""
            SELECT SUM(monthly_rate) FROM clients
            WHERE is_active = 1 AND months_paid < 12
        """)
        mrr = cursor.fetchone()[0] or 0

        # Revenue by tier
        cursor.execute("""
            SELECT tier, SUM(balance_paid) as revenue
            FROM clients
            GROUP BY tier
        """)
        by_tier = {row['tier']: row['revenue'] for row in cursor.fetchall()}

        # Revenue by month (simplified - based on months_paid)
        cursor.execute("""
            SELECT
                strftime('%Y-%m', start_date) as month,
                SUM(monthly_rate) as revenue
            FROM clients
            WHERE start_date IS NOT NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT 6
        """)
        monthly = [dict(row) for row in cursor.fetchall()]

        # Projected revenue (remaining payments from active clients)
        cursor.execute("""
            SELECT SUM((12 - months_paid) * monthly_rate) FROM clients
            WHERE is_active = 1 AND months_paid < 12
        """)
        projected = cursor.fetchone()[0] or 0

        return {
            "total_revenue": total_revenue,
            "monthly_recurring": mrr,
            "by_tier": by_tier,
            "monthly_history": monthly,
            "projected_remaining": projected,
            "avg_client_value": total_revenue / max(1, client_manager.get_client_stats()['total'])
        }


@router.get("/leads/sources")
async def get_lead_sources():
    """Get lead source breakdown"""
    stats = lead_manager.get_pipeline_stats()
    return {
        "sources": stats['by_source'],
        "total": stats['total']
    }


@router.get("/clients/tiers")
async def get_client_tiers():
    """Get client tier breakdown"""
    stats = client_manager.get_client_stats()

    # Calculate revenue by tier
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tier, COUNT(*) as count, SUM(balance_paid) as revenue
            FROM clients
            GROUP BY tier
        """)
        tier_data = {}
        for row in cursor.fetchall():
            tier_data[row['tier']] = {
                'count': row['count'],
                'revenue': row['revenue'] or 0
            }

    return {
        "tiers": tier_data,
        "total_clients": stats['total'],
        "fully_owned": stats['fully_owned']
    }


@router.get("/projects/overdue")
async def get_overdue_projects():
    """Get list of overdue projects"""
    overdue = project_manager.get_overdue_projects()
    return {
        "overdue": [p.to_dict() for p in overdue],
        "count": len(overdue)
    }


@router.get("/activity")
async def get_recent_activity(limit: int = 20):
    """Get recent activity feed"""
    activity = comm_manager.get_recent_activity(limit)
    return {
        "activity": activity,
        "count": len(activity)
    }


@router.post("/backup")
async def trigger_backup():
    """Trigger a database backup"""
    try:
        backup_path = backup_database()
        return {
            "success": True,
            "message": "Backup created",
            "path": str(backup_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/stats")
async def get_full_stats():
    """Get comprehensive database statistics"""
    return get_database_stats()


@router.get("/ownership/summary")
async def get_ownership_summary():
    """Get ownership status summary across all clients"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Clients by ownership status
        cursor.execute("""
            SELECT
                CASE
                    WHEN months_paid >= 12 THEN 'owned'
                    WHEN months_paid >= 9 THEN 'near_ownership'
                    WHEN months_paid >= 6 THEN 'halfway'
                    WHEN months_paid >= 3 THEN 'early'
                    ELSE 'new'
                END as status,
                COUNT(*) as count
            FROM clients
            WHERE is_active = 1
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}

        # Average ownership percentage
        cursor.execute("""
            SELECT AVG(CAST(months_paid AS FLOAT) / 12 * 100) as avg_ownership
            FROM clients
            WHERE is_active = 1
        """)
        avg_ownership = cursor.fetchone()['avg_ownership'] or 0

        # Total equity held by clients
        cursor.execute("""
            SELECT SUM(balance_paid) as total_equity
            FROM clients
            WHERE is_active = 1
        """)
        total_equity = cursor.fetchone()['total_equity'] or 0

        # Upcoming milestones (clients about to reach ownership)
        cursor.execute("""
            SELECT id, name, company, months_paid, monthly_rate, tier
            FROM clients
            WHERE is_active = 1 AND months_paid >= 10 AND months_paid < 12
            ORDER BY months_paid DESC
        """)
        near_ownership = [dict(row) for row in cursor.fetchall()]

        return {
            "by_status": by_status,
            "avg_ownership_percent": round(avg_ownership, 1),
            "total_equity": total_equity,
            "near_ownership": near_ownership
        }


@router.get("/babies/usage")
async def get_baby_usage():
    """Get AI baby usage statistics"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT baby_assigned, COUNT(*) as count, tier
            FROM clients
            WHERE baby_assigned != ''
            GROUP BY baby_assigned
        """)
        usage = {}
        for row in cursor.fetchall():
            if row['baby_assigned'] not in usage:
                usage[row['baby_assigned']] = 0
            usage[row['baby_assigned']] += row['count']

        return {
            "babies": usage,
            "total_assigned": sum(usage.values())
        }
