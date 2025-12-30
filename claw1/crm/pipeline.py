"""
SCORPION CLAW1 - CRM Pipeline
==============================

Sales pipeline management with stage tracking and analytics.

Pipeline Stages:
1. new - Fresh lead, not contacted
2. contacted - Initial contact made
3. quoted - Quote/proposal sent
4. negotiating - In active negotiation
5. closed - Deal won
6. lost - Deal lost
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLAW1.pipeline")


class PipelineStage(Enum):
    """Sales pipeline stages."""
    NEW = "new"
    CONTACTED = "contacted"
    QUOTED = "quoted"
    NEGOTIATING = "negotiating"
    CLOSED = "closed"
    LOST = "lost"


PIPELINE_STAGES = [stage.value for stage in PipelineStage]

# Stage transition rules (from -> allowed to)
ALLOWED_TRANSITIONS = {
    "new": ["contacted", "lost"],
    "contacted": ["quoted", "lost"],
    "quoted": ["negotiating", "closed", "lost"],
    "negotiating": ["closed", "lost", "quoted"],
    "closed": [],  # Terminal state
    "lost": ["new"]  # Can restart
}

# Stage colors for UI
STAGE_COLORS = {
    "new": "#3498db",
    "contacted": "#9b59b6",
    "quoted": "#f39c12",
    "negotiating": "#e74c3c",
    "closed": "#27ae60",
    "lost": "#95a5a6"
}


@dataclass
class Deal:
    """Deal/opportunity in the pipeline."""
    id: str
    lead_id: str
    name: str
    company: str
    value: float
    stage: str = "new"
    probability: int = 10
    owner: str = ""
    notes: str = ""
    expected_close: Optional[str] = None
    actual_close: Optional[str] = None
    lost_reason: str = ""
    stage_history: List[Dict] = field(default_factory=list)
    activities: List[Dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.stage_history:
            self.stage_history = [{
                "stage": self.stage,
                "timestamp": self.created_at,
                "note": "Created"
            }]


# Default probability by stage
STAGE_PROBABILITY = {
    "new": 10,
    "contacted": 20,
    "quoted": 40,
    "negotiating": 60,
    "closed": 100,
    "lost": 0
}


class Pipeline:
    """
    CRM Pipeline manager.

    Usage:
        pipeline = Pipeline()
        deal_id = pipeline.create_deal("LEAD-001", "Smith Project", "Smith Co", 50000)
        pipeline.move_stage(deal_id, "contacted")
        stats = pipeline.get_stats()
    """

    def __init__(self, data_dir: str = "pipeline"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._deals: Dict[str, Deal] = {}
        self._counter = 0
        self._load_data()

    def _load_data(self):
        """Load deals from file."""
        deals_file = self.data_dir / "deals.json"
        if deals_file.exists():
            try:
                data = json.loads(deals_file.read_text())
                for deal_data in data:
                    deal = Deal(**deal_data)
                    self._deals[deal.id] = deal
                self._counter = len(self._deals)
            except Exception as e:
                logger.error(f"Error loading deals: {e}")

    def _save_data(self):
        """Save deals to file."""
        deals_file = self.data_dir / "deals.json"
        data = [asdict(deal) for deal in self._deals.values()]
        deals_file.write_text(json.dumps(data, indent=2))

    def _generate_id(self) -> str:
        """Generate unique deal ID."""
        self._counter += 1
        return f"DEAL-{datetime.now().strftime('%Y%m%d')}-{self._counter:04d}"

    def create_deal(
        self,
        lead_id: str,
        name: str,
        company: str,
        value: float,
        owner: str = "",
        expected_close: Optional[str] = None,
        notes: str = ""
    ) -> str:
        """
        Create a new deal from a lead.

        Args:
            lead_id: Source lead ID
            name: Deal/project name
            company: Company name
            value: Deal value
            owner: Deal owner/rep
            expected_close: Expected close date
            notes: Initial notes

        Returns:
            Deal ID
        """
        deal = Deal(
            id=self._generate_id(),
            lead_id=lead_id,
            name=name,
            company=company,
            value=value,
            owner=owner,
            expected_close=expected_close,
            notes=notes
        )

        self._deals[deal.id] = deal
        self._save_data()

        logger.info(f"Deal created: {deal.id} - {name} (${value:,.2f})")
        return deal.id

    def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get deal by ID."""
        return self._deals.get(deal_id)

    def move_stage(
        self,
        deal_id: str,
        new_stage: str,
        note: str = ""
    ) -> Tuple[bool, str]:
        """
        Move deal to a new stage.

        Args:
            deal_id: Deal ID
            new_stage: Target stage
            note: Transition note

        Returns:
            (success, message) tuple
        """
        deal = self._deals.get(deal_id)
        if not deal:
            return False, f"Deal not found: {deal_id}"

        if new_stage not in PIPELINE_STAGES:
            return False, f"Invalid stage: {new_stage}"

        # Check allowed transitions
        allowed = ALLOWED_TRANSITIONS.get(deal.stage, [])
        if new_stage not in allowed and new_stage != deal.stage:
            return False, f"Cannot move from {deal.stage} to {new_stage}. Allowed: {allowed}"

        old_stage = deal.stage
        deal.stage = new_stage
        deal.probability = STAGE_PROBABILITY.get(new_stage, 10)
        deal.updated_at = datetime.now().isoformat()

        # Record history
        deal.stage_history.append({
            "stage": new_stage,
            "from_stage": old_stage,
            "timestamp": deal.updated_at,
            "note": note
        })

        # Handle closed/lost
        if new_stage == "closed":
            deal.actual_close = datetime.now().isoformat()

        self._save_data()

        logger.info(f"Deal {deal_id}: {old_stage} -> {new_stage}")
        return True, f"Moved to {new_stage}"

    def mark_lost(self, deal_id: str, reason: str = "") -> Tuple[bool, str]:
        """Mark deal as lost with reason."""
        deal = self._deals.get(deal_id)
        if deal:
            deal.lost_reason = reason

        return self.move_stage(deal_id, "lost", f"Lost: {reason}")

    def add_activity(
        self,
        deal_id: str,
        activity_type: str,
        description: str,
        outcome: str = ""
    ) -> bool:
        """
        Log an activity on a deal.

        Args:
            deal_id: Deal ID
            activity_type: Type (call, email, meeting, note)
            description: Activity description
            outcome: Activity outcome
        """
        deal = self._deals.get(deal_id)
        if not deal:
            return False

        activity = {
            "type": activity_type,
            "description": description,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        }

        deal.activities.append(activity)
        deal.updated_at = datetime.now().isoformat()
        self._save_data()

        return True

    def get_deals_by_stage(self, stage: str) -> List[Deal]:
        """Get all deals in a stage."""
        return [d for d in self._deals.values() if d.stage == stage]

    def get_deals_by_owner(self, owner: str) -> List[Deal]:
        """Get all deals for an owner."""
        return [d for d in self._deals.values() if d.owner == owner]

    def get_active_deals(self) -> List[Deal]:
        """Get all active (non-closed, non-lost) deals."""
        return [d for d in self._deals.values()
                if d.stage not in ("closed", "lost")]

    def get_closing_soon(self, days: int = 7) -> List[Deal]:
        """Get deals expected to close soon."""
        cutoff = (datetime.now() + timedelta(days=days)).isoformat()

        return [
            d for d in self._deals.values()
            if d.expected_close and d.expected_close <= cutoff
            and d.stage not in ("closed", "lost")
        ]

    def get_stale_deals(self, days: int = 14) -> List[Deal]:
        """Get deals with no activity for X days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        stale = []
        for deal in self._deals.values():
            if deal.stage in ("closed", "lost"):
                continue

            last_activity = deal.updated_at
            if deal.activities:
                last_activity = max(a["timestamp"] for a in deal.activities)

            if last_activity < cutoff:
                stale.append(deal)

        return stale

    def get_pipeline_stats(self) -> Dict:
        """Get comprehensive pipeline statistics."""
        deals = list(self._deals.values())
        active = [d for d in deals if d.stage not in ("closed", "lost")]

        # By stage
        by_stage = {}
        value_by_stage = {}
        for stage in PIPELINE_STAGES:
            stage_deals = [d for d in deals if d.stage == stage]
            by_stage[stage] = len(stage_deals)
            value_by_stage[stage] = sum(d.value for d in stage_deals)

        # Totals
        total_value = sum(d.value for d in deals)
        active_value = sum(d.value for d in active)
        weighted_value = sum(d.value * (d.probability / 100) for d in active)

        # Win rate
        closed = [d for d in deals if d.stage == "closed"]
        lost = [d for d in deals if d.stage == "lost"]
        total_finished = len(closed) + len(lost)
        win_rate = (len(closed) / total_finished * 100) if total_finished > 0 else 0

        # Average deal value
        avg_value = total_value / len(deals) if deals else 0
        avg_won_value = sum(d.value for d in closed) / len(closed) if closed else 0

        # Cycle time (for closed deals)
        cycle_times = []
        for deal in closed:
            if deal.actual_close:
                created = datetime.fromisoformat(deal.created_at)
                closed_dt = datetime.fromisoformat(deal.actual_close)
                cycle_times.append((closed_dt - created).days)
        avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0

        return {
            "total_deals": len(deals),
            "active_deals": len(active),
            "by_stage": by_stage,
            "value_by_stage": value_by_stage,
            "total_value": round(total_value, 2),
            "active_value": round(active_value, 2),
            "weighted_pipeline": round(weighted_value, 2),
            "win_rate": round(win_rate, 1),
            "avg_deal_value": round(avg_value, 2),
            "avg_won_value": round(avg_won_value, 2),
            "avg_cycle_days": round(avg_cycle, 1),
            "stale_count": len(self.get_stale_deals()),
            "closing_soon": len(self.get_closing_soon())
        }

    def get_pipeline_view(self) -> Dict[str, List[Dict]]:
        """Get pipeline view organized by stage."""
        view = {stage: [] for stage in PIPELINE_STAGES}

        for deal in self._deals.values():
            view[deal.stage].append({
                "id": deal.id,
                "name": deal.name,
                "company": deal.company,
                "value": deal.value,
                "probability": deal.probability,
                "owner": deal.owner,
                "days_in_stage": self._days_in_stage(deal),
                "expected_close": deal.expected_close
            })

        # Sort each stage by value (highest first)
        for stage in view:
            view[stage].sort(key=lambda x: x["value"], reverse=True)

        return view

    def _days_in_stage(self, deal: Deal) -> int:
        """Calculate days in current stage."""
        if not deal.stage_history:
            return 0

        # Find when entered current stage
        for entry in reversed(deal.stage_history):
            if entry["stage"] == deal.stage:
                entered = datetime.fromisoformat(entry["timestamp"])
                return (datetime.now() - entered).days

        return 0

    def print_pipeline(self):
        """Print formatted pipeline view."""
        view = self.get_pipeline_view()
        stats = self.get_pipeline_stats()

        print("\n" + "=" * 70)
        print("SALES PIPELINE")
        print("=" * 70)

        for stage in PIPELINE_STAGES:
            deals = view[stage]
            stage_value = stats["value_by_stage"].get(stage, 0)

            print(f"\n{stage.upper()} ({len(deals)} deals - ${stage_value:,.2f})")
            print("-" * 50)

            if not deals:
                print("  (empty)")
            else:
                for deal in deals[:5]:  # Top 5
                    print(f"  • {deal['name']} ({deal['company']})")
                    print(f"    ${deal['value']:,.2f} | {deal['probability']}% | {deal['days_in_stage']}d")
                if len(deals) > 5:
                    print(f"  ... and {len(deals) - 5} more")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("-" * 70)
        print(f"  Active Pipeline: ${stats['active_value']:,.2f}")
        print(f"  Weighted Value:  ${stats['weighted_pipeline']:,.2f}")
        print(f"  Win Rate:        {stats['win_rate']}%")
        print(f"  Avg Cycle:       {stats['avg_cycle_days']} days")
        print("=" * 70 + "\n")


# Convenience functions
_pipeline: Optional[Pipeline] = None


def move_stage(deal_id: str, new_stage: str, note: str = "") -> Tuple[bool, str]:
    """Move deal stage using default pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline.move_stage(deal_id, new_stage, note)


def get_pipeline_stats() -> Dict:
    """Get stats from default pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline.get_pipeline_stats()


if __name__ == "__main__":
    print("CLAW1 Pipeline - Demo")
    print("=" * 40)

    pipeline = Pipeline()

    # Create sample deals
    deal1 = pipeline.create_deal(
        lead_id="LEAD-001",
        name="Smith Kitchen Remodel",
        company="Smith Residence",
        value=45000,
        owner="John",
        expected_close="2024-02-15"
    )

    deal2 = pipeline.create_deal(
        lead_id="LEAD-002",
        name="Corporate Office Build",
        company="TechCorp Inc",
        value=250000,
        owner="John"
    )

    deal3 = pipeline.create_deal(
        lead_id="LEAD-003",
        name="Deck Addition",
        company="Johnson Family",
        value=15000,
        owner="Mike"
    )

    # Move stages
    pipeline.move_stage(deal1, "contacted", "Initial call made")
    pipeline.move_stage(deal1, "quoted", "Quote sent $45,000")
    pipeline.move_stage(deal2, "contacted")
    pipeline.move_stage(deal3, "contacted")
    pipeline.move_stage(deal3, "quoted")
    pipeline.move_stage(deal3, "negotiating", "Customer wants discount")

    # Add activity
    pipeline.add_activity(deal1, "call", "Follow-up call", "Customer reviewing quote")

    # Print pipeline
    pipeline.print_pipeline()
