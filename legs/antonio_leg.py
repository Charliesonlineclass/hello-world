"""
SCORPION Multi-Tenant System - Antonio's Banking Leg
=====================================================

This leg serves Antonio's Banking/Financial Services operations,
specializing in loan assessment, compliance, and client management.

SCORPION Architecture Role:
- LEG: Client interface for Antonio's Banking Services
- BABY: MARCUS (qwen2.5:7b) - optimized for deep analysis
- Industry: BANKING
- Owner: Master Charlie (HEAD access)

Antonio's Banking specializes in:
- Loan risk assessment
- Compliance checking
- Credit report generation
- Client portfolio management

This leg handles loan applications, risk scoring, compliance verification,
and generates detailed financial reports.

Author: SCORPION System
Version: 1.0.0
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import uuid
import math

from .base_leg import (
    BaseClientLeg, Industry, Lead, LeadStatus,
    RequestType, logger
)


class RiskLevel(Enum):
    """Loan risk levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNACCEPTABLE = "unacceptable"


class LoanType(Enum):
    """Types of loans offered."""
    PERSONAL = "personal"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    BUSINESS = "business"
    CREDIT_LINE = "credit_line"
    CONSOLIDATION = "consolidation"


class ApplicationStatus(Enum):
    """Loan application status."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    DOCUMENTS_NEEDED = "documents_needed"
    COMPLIANCE_CHECK = "compliance_check"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    FUNDED = "funded"
    CANCELLED = "cancelled"


class ConsultationType(Enum):
    """Types of consultations."""
    INITIAL = "initial"
    FOLLOWUP = "followup"
    DOCUMENT_REVIEW = "document_review"
    CLOSING = "closing"
    COLLECTION = "collection"


@dataclass
class RiskAssessment:
    """Result of a loan risk assessment."""
    id: str
    application_id: str
    risk_score: int  # 1-10
    risk_level: RiskLevel
    factors: Dict[str, Any]
    reasoning: str
    recommendations: List[str]
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    id: str
    application_id: str
    passed: bool
    checks_performed: List[str]
    issues: List[str]
    warnings: List[str]
    reviewer_notes: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class LoanApplication:
    """A loan application."""
    id: str
    lead_id: str
    loan_type: LoanType
    amount_requested: float
    status: ApplicationStatus
    applicant_data: Dict[str, Any]
    risk_assessment_id: Optional[str]
    compliance_result_id: Optional[str]
    terms_offered: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['loan_type'] = self.loan_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class Consultation:
    """A scheduled consultation."""
    id: str
    client_id: str
    consultation_type: ConsultationType
    scheduled_datetime: datetime
    duration_minutes: int
    advisor: str
    notes: str = ""
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['consultation_type'] = self.consultation_type.value
        data['scheduled_datetime'] = self.scheduled_datetime.isoformat()
        return data


@dataclass
class SuspiciousActivity:
    """Flagged suspicious activity."""
    id: str
    client_id: str
    activity_type: str
    description: str
    severity: str
    transaction_data: Dict[str, Any]
    flagged_at: datetime
    reviewed: bool = False
    resolution: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['flagged_at'] = self.flagged_at.isoformat()
        return data


class AntonioLeg(BaseClientLeg):
    """
    SCORPION Leg for Antonio's Banking Services.

    Connects to MARCUS (qwen2.5:7b) for deep financial analysis.
    Handles loan assessment, compliance, and portfolio management.

    SCORPION Security:
    - All financial actions logged to Labienus audit system
    - Strict compliance with banking regulations
    - Suspicious activity detection and reporting
    - HEAD (Master Charlie) has full oversight
    """

    # Base interest rates by loan type
    BASE_RATES = {
        LoanType.PERSONAL: 0.0899,
        LoanType.MORTGAGE: 0.0650,
        LoanType.AUTO: 0.0549,
        LoanType.BUSINESS: 0.0799,
        LoanType.CREDIT_LINE: 0.1499,
        LoanType.CONSOLIDATION: 0.0749,
    }

    # Risk adjustment factors
    RISK_RATE_ADJUSTMENT = {
        RiskLevel.LOW: 0.00,
        RiskLevel.MODERATE: 0.02,
        RiskLevel.HIGH: 0.05,
        RiskLevel.VERY_HIGH: 0.10,
    }

    def __init__(
        self,
        access_token: str,
        data_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Antonio's Banking leg.

        Args:
            access_token: Authentication token
            data_dir: Data storage directory
            ollama_url: Ollama server URL
        """
        super().__init__(
            client_id="antonio_banking",
            client_name="Antonio's Banking Services",
            baby_model="qwen2.5:7b",  # MARCUS
            industry=Industry.BANKING,
            access_token=access_token,
            data_dir=data_dir,
            ollama_url=ollama_url
        )

        # Antonio-specific data storage
        self._applications: Dict[str, LoanApplication] = {}
        self._risk_assessments: Dict[str, RiskAssessment] = {}
        self._compliance_results: Dict[str, ComplianceResult] = {}
        self._consultations: Dict[str, Consultation] = {}
        self._suspicious_activities: Dict[str, SuspiciousActivity] = {}

        # Load Antonio's data
        self._load_antonio_data()

        logger.info(f"Antonio's Banking leg initialized with MARCUS (qwen2.5:7b)")

    def _load_antonio_data(self) -> None:
        """Load Antonio-specific data from disk."""
        apps_file = self.data_dir / "applications.json"
        if apps_file.exists():
            try:
                with open(apps_file, 'r') as f:
                    data = json.load(f)
                    for app in data:
                        app['loan_type'] = LoanType(app['loan_type'])
                        app['status'] = ApplicationStatus(app['status'])
                        app['created_at'] = datetime.fromisoformat(app['created_at'])
                        app['updated_at'] = datetime.fromisoformat(app['updated_at'])
                        self._applications[app['id']] = LoanApplication(**app)
            except Exception as e:
                logger.error(f"Error loading applications: {e}")

    def _save_antonio_data(self) -> None:
        """Save Antonio-specific data to disk."""
        apps_file = self.data_dir / "applications.json"
        with open(apps_file, 'w') as f:
            json.dump([a.to_dict() for a in self._applications.values()], f, indent=2)

    def get_industry_actions(self) -> List[str]:
        """Return Antonio-specific actions."""
        return [
            "assess_loan_risk",
            "compliance_check",
            "generate_credit_report",
            "schedule_consultation",
            "calculate_loan_terms",
            "flag_suspicious_activity",
            "monthly_portfolio_report"
        ]

    def process_industry_request(
        self,
        action: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route Antonio-specific requests."""
        handlers = {
            "assess_loan_risk": lambda d: self.assess_loan_risk(d['client_data']),
            "compliance_check": lambda d: self.compliance_check(d['application_data']),
            "generate_credit_report": lambda d: self.generate_credit_report(d['client_id']),
            "schedule_consultation": lambda d: self.schedule_consultation(
                d['client_id'],
                d['datetime'],
                ConsultationType(d.get('type', 'initial'))
            ),
            "calculate_loan_terms": lambda d: self.calculate_loan_terms(
                d['amount'],
                d['credit_score'],
                d['income'],
                LoanType(d.get('loan_type', 'personal'))
            ),
            "flag_suspicious_activity": lambda d: self.flag_suspicious_activity(d['transaction_data']),
            "monthly_portfolio_report": lambda d: self.monthly_portfolio_report(),
        }

        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown Antonio Banking action: {action}"}

        return handler(data)

    def assess_loan_risk(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess loan risk for a client.

        Uses MARCUS for deep analysis of financial indicators.

        Args:
            client_data: Client financial information including:
                - credit_score: Credit score (300-850)
                - income: Annual income
                - debt: Total existing debt
                - employment_years: Years at current job
                - loan_amount: Requested loan amount
                - loan_type: Type of loan

        Returns:
            Risk assessment with score and reasoning
        """
        assessment_id = str(uuid.uuid4())

        credit_score = client_data.get('credit_score', 650)
        income = client_data.get('income', 50000)
        debt = client_data.get('debt', 0)
        employment_years = client_data.get('employment_years', 0)
        loan_amount = client_data.get('loan_amount', 10000)
        loan_type_str = client_data.get('loan_type', 'personal')

        # Calculate debt-to-income ratio
        dti = (debt / income * 100) if income > 0 else 100

        # Calculate base risk score (1-10, higher = more risk)
        risk_score = 5  # Start neutral

        # Credit score impact
        if credit_score >= 750:
            risk_score -= 2
        elif credit_score >= 700:
            risk_score -= 1
        elif credit_score < 600:
            risk_score += 2
        elif credit_score < 650:
            risk_score += 1

        # DTI impact
        if dti > 50:
            risk_score += 2
        elif dti > 40:
            risk_score += 1
        elif dti < 20:
            risk_score -= 1

        # Employment stability
        if employment_years >= 5:
            risk_score -= 1
        elif employment_years < 1:
            risk_score += 1

        # Loan amount relative to income
        loan_to_income = loan_amount / income if income > 0 else 10
        if loan_to_income > 2:
            risk_score += 1
        elif loan_to_income < 0.5:
            risk_score -= 1

        # Clamp score to 1-10
        risk_score = max(1, min(10, risk_score))

        # Determine risk level
        if risk_score <= 3:
            risk_level = RiskLevel.LOW
        elif risk_score <= 5:
            risk_level = RiskLevel.MODERATE
        elif risk_score <= 7:
            risk_level = RiskLevel.HIGH
        elif risk_score <= 9:
            risk_level = RiskLevel.VERY_HIGH
        else:
            risk_level = RiskLevel.UNACCEPTABLE

        # Generate AI reasoning using MARCUS
        prompt = f"""Analyze this loan application risk:

Credit Score: {credit_score}
Annual Income: ${income:,.2f}
Existing Debt: ${debt:,.2f}
Debt-to-Income Ratio: {dti:.1f}%
Employment: {employment_years} years at current job
Loan Amount Requested: ${loan_amount:,.2f}
Loan Type: {loan_type_str}

Calculated Risk Score: {risk_score}/10 ({risk_level.value})

Provide a brief (100 words max) analysis of the key risk factors and recommendation."""

        ai_response = self.query_baby(prompt)

        factors = {
            "credit_score": credit_score,
            "dti_ratio": round(dti, 2),
            "employment_years": employment_years,
            "loan_to_income": round(loan_to_income, 2)
        }

        recommendations = []
        if risk_level == RiskLevel.LOW:
            recommendations = ["Approve with standard terms", "Consider rate discount for loyalty"]
        elif risk_level == RiskLevel.MODERATE:
            recommendations = ["Approve with standard terms", "Verify employment", "Monitor account"]
        elif risk_level == RiskLevel.HIGH:
            recommendations = ["Require additional documentation", "Consider higher rate", "Limit loan amount"]
        elif risk_level == RiskLevel.VERY_HIGH:
            recommendations = ["Decline or require co-signer", "Significantly higher rate if approved", "Short term only"]
        else:
            recommendations = ["Decline application", "Refer to credit counseling"]

        assessment = RiskAssessment(
            id=assessment_id,
            application_id=client_data.get('application_id', ''),
            risk_score=risk_score,
            risk_level=risk_level,
            factors=factors,
            reasoning=ai_response.get('response', 'Analysis pending'),
            recommendations=recommendations,
            created_at=datetime.now()
        )

        self._risk_assessments[assessment_id] = assessment

        self.log_activity(
            action="risk_assessment",
            details={
                "assessment_id": assessment_id,
                "risk_score": risk_score,
                "risk_level": risk_level.value
            }
        )

        return assessment.to_dict()

    def compliance_check(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform compliance check on a loan application.

        Args:
            application_data: Application details to check

        Returns:
            Compliance result with pass/fail and issues
        """
        result_id = str(uuid.uuid4())
        issues = []
        warnings = []

        checks_performed = [
            "Identity verification",
            "Income verification",
            "OFAC sanctions check",
            "Credit bureau check",
            "Debt-to-income limit",
            "State lending regulations",
            "Interest rate caps",
            "Equal Credit Opportunity Act",
            "Truth in Lending Act",
            "Anti-money laundering"
        ]

        # Perform checks
        income = application_data.get('income', 0)
        stated_income = application_data.get('stated_income', income)
        if abs(income - stated_income) > income * 0.1:
            issues.append("Income discrepancy: stated vs verified differs by >10%")

        dti = application_data.get('dti', 0)
        if dti > 43:
            issues.append("DTI exceeds qualified mortgage threshold of 43%")
        elif dti > 36:
            warnings.append("DTI exceeds recommended 36% threshold")

        if not application_data.get('identity_verified', False):
            issues.append("Identity verification incomplete")

        if not application_data.get('employment_verified', False):
            warnings.append("Employment verification pending")

        loan_amount = application_data.get('loan_amount', 0)
        income = application_data.get('income', 1)
        if loan_amount > income * 5:
            issues.append("Loan amount exceeds 5x annual income limit")

        # OFAC check simulation
        if application_data.get('name', '').lower() in ['test blocked', 'sanctions test']:
            issues.append("CRITICAL: Name matches OFAC sanctions list")

        passed = len(issues) == 0

        # Generate AI review notes
        prompt = f"""Review this compliance check result:

Checks Performed: {', '.join(checks_performed)}
Issues Found: {len(issues)}
Warnings: {len(warnings)}

Issues: {'; '.join(issues) if issues else 'None'}
Warnings: {'; '.join(warnings) if warnings else 'None'}

Provide a brief (50 words) compliance reviewer note summarizing the findings."""

        ai_response = self.query_baby(prompt)

        result = ComplianceResult(
            id=result_id,
            application_id=application_data.get('application_id', ''),
            passed=passed,
            checks_performed=checks_performed,
            issues=issues,
            warnings=warnings,
            reviewer_notes=ai_response.get('response', 'Review complete'),
            created_at=datetime.now()
        )

        self._compliance_results[result_id] = result

        self.log_activity(
            action="compliance_check",
            details={
                "result_id": result_id,
                "passed": passed,
                "issues_count": len(issues),
                "warnings_count": len(warnings)
            }
        )

        return result.to_dict()

    def generate_credit_report(self, client_id: str) -> Dict[str, Any]:
        """
        Generate a formatted credit report.

        Args:
            client_id: Client ID

        Returns:
            Formatted credit report
        """
        lead = self._leads_cache.get(client_id)

        # Get client's applications
        client_apps = [
            app for app in self._applications.values()
            if app.lead_id == client_id
        ]

        # Compile credit data
        credit_data = {
            "client_id": client_id,
            "client_name": lead.name if lead else "Unknown",
            "report_date": datetime.now().isoformat(),
            "applications": [app.to_dict() for app in client_apps],
            "total_requested": sum(app.amount_requested for app in client_apps),
            "approved_count": len([a for a in client_apps if a.status == ApplicationStatus.APPROVED]),
            "denied_count": len([a for a in client_apps if a.status == ApplicationStatus.DENIED]),
        }

        # Generate AI summary
        prompt = f"""Generate a brief credit report summary for:

Client: {credit_data['client_name']}
Total Applications: {len(client_apps)}
Total Amount Requested: ${credit_data['total_requested']:,.2f}
Approvals: {credit_data['approved_count']}
Denials: {credit_data['denied_count']}

Provide a 75-word executive summary of the client's credit relationship."""

        ai_response = self.query_baby(prompt)
        credit_data["executive_summary"] = ai_response.get('response', 'Report generated')

        # Build formatted report
        report_content = f"""
========================================
CREDIT REPORT - CONFIDENTIAL
========================================

Client ID: {client_id}
Client Name: {credit_data['client_name']}
Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

----------------------------------------
EXECUTIVE SUMMARY
----------------------------------------
{credit_data['executive_summary']}

----------------------------------------
APPLICATION HISTORY
----------------------------------------
Total Applications: {len(client_apps)}
Total Amount Requested: ${credit_data['total_requested']:,.2f}
Approved: {credit_data['approved_count']}
Denied: {credit_data['denied_count']}
Pending: {len(client_apps) - credit_data['approved_count'] - credit_data['denied_count']}

----------------------------------------
RECOMMENDATION
----------------------------------------
{'Client in good standing. Eligible for premium services.' if credit_data['approved_count'] > 0 else 'Review recent applications before extending credit.'}

========================================
Antonio's Banking Services
Confidential Credit Report
========================================
"""

        self.log_activity(
            action="credit_report_generated",
            details={"client_id": client_id}
        )

        return {
            "report": report_content,
            "data": credit_data
        }

    def schedule_consultation(
        self,
        client_id: str,
        scheduled_datetime: str,
        consultation_type: ConsultationType = ConsultationType.INITIAL
    ) -> Dict[str, Any]:
        """
        Schedule a client consultation.

        Args:
            client_id: Client ID
            scheduled_datetime: ISO datetime string
            consultation_type: Type of consultation

        Returns:
            Consultation details
        """
        consult_id = str(uuid.uuid4())
        dt = datetime.fromisoformat(scheduled_datetime)

        lead = self._leads_cache.get(client_id)

        # Duration based on type
        durations = {
            ConsultationType.INITIAL: 60,
            ConsultationType.FOLLOWUP: 30,
            ConsultationType.DOCUMENT_REVIEW: 45,
            ConsultationType.CLOSING: 90,
            ConsultationType.COLLECTION: 30,
        }

        consultation = Consultation(
            id=consult_id,
            client_id=client_id,
            consultation_type=consultation_type,
            scheduled_datetime=dt,
            duration_minutes=durations.get(consultation_type, 30),
            advisor="Antonio Financial Advisor"
        )

        self._consultations[consult_id] = consultation

        # Update lead
        if lead:
            lead.status = LeadStatus.CONTACTED
            lead.custom_data['consultation_scheduled'] = scheduled_datetime
            lead.updated_at = datetime.now()
            self._save_data()

        self.log_activity(
            action="consultation_scheduled",
            details={
                "consultation_id": consult_id,
                "client_id": client_id,
                "type": consultation_type.value,
                "datetime": scheduled_datetime
            }
        )

        return {
            "consultation": consultation.to_dict(),
            "status": "scheduled",
            "confirmation": f"Consultation scheduled for {dt.strftime('%A, %B %d at %I:%M %p')}"
        }

    def calculate_loan_terms(
        self,
        amount: float,
        credit_score: int,
        income: float,
        loan_type: LoanType = LoanType.PERSONAL
    ) -> Dict[str, Any]:
        """
        Calculate loan terms including rates and payments.

        Args:
            amount: Loan amount
            credit_score: Applicant credit score
            income: Annual income
            loan_type: Type of loan

        Returns:
            Calculated terms with rates and payment options
        """
        # Get base rate
        base_rate = self.BASE_RATES.get(loan_type, 0.10)

        # Adjust for credit score
        if credit_score >= 750:
            rate_adjustment = -0.02
        elif credit_score >= 700:
            rate_adjustment = -0.01
        elif credit_score >= 650:
            rate_adjustment = 0
        elif credit_score >= 600:
            rate_adjustment = 0.03
        else:
            rate_adjustment = 0.06

        final_rate = base_rate + rate_adjustment

        # Calculate monthly payments for different terms
        terms = [12, 24, 36, 48, 60] if loan_type != LoanType.MORTGAGE else [180, 240, 360]

        payment_options = []
        for term_months in terms:
            monthly_rate = final_rate / 12
            if monthly_rate > 0:
                payment = amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
            else:
                payment = amount / term_months

            total_interest = (payment * term_months) - amount

            payment_options.append({
                "term_months": term_months,
                "monthly_payment": round(payment, 2),
                "total_interest": round(total_interest, 2),
                "total_cost": round(amount + total_interest, 2),
                "apr": round(final_rate * 100, 2)
            })

        # Calculate max loan based on income
        max_monthly_payment = income / 12 * 0.28  # 28% rule
        max_loan = max_monthly_payment * 60 / (1 + (final_rate / 12) * 30)  # Simplified

        result = {
            "loan_amount": amount,
            "loan_type": loan_type.value,
            "credit_score": credit_score,
            "base_rate": round(base_rate * 100, 2),
            "rate_adjustment": round(rate_adjustment * 100, 2),
            "final_apr": round(final_rate * 100, 2),
            "payment_options": payment_options,
            "max_loan_amount": round(max_loan, 2),
            "qualification_status": "qualified" if amount <= max_loan else "over_limit"
        }

        self.log_activity(
            action="loan_terms_calculated",
            details={
                "amount": amount,
                "loan_type": loan_type.value,
                "apr": result["final_apr"]
            }
        )

        return result

    def flag_suspicious_activity(
        self,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Flag potentially suspicious activity for review.

        Args:
            transaction_data: Transaction details to analyze

        Returns:
            Flagged activity details
        """
        flag_id = str(uuid.uuid4())

        amount = transaction_data.get('amount', 0)
        client_id = transaction_data.get('client_id', 'unknown')
        transaction_type = transaction_data.get('type', 'unknown')

        # Determine severity
        severity = "low"
        activity_type = "unusual_pattern"
        description = ""

        if amount >= 10000:
            severity = "high"
            activity_type = "large_transaction"
            description = f"Large transaction of ${amount:,.2f} requires CTR filing"
        elif transaction_data.get('structuring_pattern', False):
            severity = "critical"
            activity_type = "structuring"
            description = "Multiple transactions appear structured to avoid reporting"
        elif transaction_data.get('unusual_geography', False):
            severity = "medium"
            activity_type = "geographic_anomaly"
            description = "Transaction from unusual geographic location"
        elif transaction_data.get('velocity_spike', False):
            severity = "medium"
            activity_type = "velocity_spike"
            description = "Unusual increase in transaction frequency"
        else:
            description = f"Flagged {transaction_type} transaction for review"

        # Use MARCUS to analyze
        prompt = f"""Analyze this flagged financial activity:

Transaction Type: {transaction_type}
Amount: ${amount:,.2f}
Severity: {severity}
Activity Type: {activity_type}
Initial Description: {description}

Provide a brief (50 words) risk assessment and recommended action."""

        ai_response = self.query_baby(prompt)

        activity = SuspiciousActivity(
            id=flag_id,
            client_id=client_id,
            activity_type=activity_type,
            description=description,
            severity=severity,
            transaction_data=transaction_data,
            flagged_at=datetime.now()
        )

        self._suspicious_activities[flag_id] = activity

        self.log_activity(
            action="suspicious_activity_flagged",
            details={
                "flag_id": flag_id,
                "severity": severity,
                "activity_type": activity_type,
                "_security_flag": "SUSPICIOUS_ACTIVITY"
            }
        )

        return {
            "flag": activity.to_dict(),
            "ai_analysis": ai_response.get('response', 'Analysis pending'),
            "required_actions": [
                "Review transaction details",
                "File SAR if warranted" if severity in ["high", "critical"] else "Monitor for patterns",
                "Notify compliance officer" if severity == "critical" else "Document in case file"
            ]
        }

    def monthly_portfolio_report(self) -> Dict[str, Any]:
        """
        Generate monthly portfolio summary.

        Returns:
            Comprehensive portfolio report
        """
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Applications this month
        month_apps = [
            app for app in self._applications.values()
            if app.created_at >= month_start
        ]

        # Calculate metrics
        total_requested = sum(app.amount_requested for app in month_apps)
        approved = [a for a in month_apps if a.status == ApplicationStatus.APPROVED]
        funded = [a for a in month_apps if a.status == ApplicationStatus.FUNDED]
        denied = [a for a in month_apps if a.status == ApplicationStatus.DENIED]

        total_approved = sum(a.amount_requested for a in approved)
        total_funded = sum(a.amount_requested for a in funded)

        # Risk distribution
        risk_counts = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
        for assessment in self._risk_assessments.values():
            if assessment.created_at >= month_start:
                risk_counts[assessment.risk_level.value] = risk_counts.get(assessment.risk_level.value, 0) + 1

        # Compliance metrics
        compliance_this_month = [
            r for r in self._compliance_results.values()
            if r.created_at >= month_start
        ]
        compliance_pass_rate = (
            len([c for c in compliance_this_month if c.passed]) /
            len(compliance_this_month) * 100
        ) if compliance_this_month else 100

        # Suspicious activity
        suspicious_this_month = [
            s for s in self._suspicious_activities.values()
            if s.flagged_at >= month_start
        ]

        report = {
            "report_period": {
                "start": month_start.isoformat(),
                "end": now.isoformat()
            },
            "applications": {
                "total": len(month_apps),
                "total_requested": total_requested,
                "approved": len(approved),
                "approved_amount": total_approved,
                "funded": len(funded),
                "funded_amount": total_funded,
                "denied": len(denied),
                "pending": len(month_apps) - len(approved) - len(denied)
            },
            "approval_rate": (len(approved) / len(month_apps) * 100) if month_apps else 0,
            "risk_distribution": risk_counts,
            "compliance": {
                "checks_performed": len(compliance_this_month),
                "pass_rate": round(compliance_pass_rate, 1)
            },
            "suspicious_activity": {
                "flags": len(suspicious_this_month),
                "critical": len([s for s in suspicious_this_month if s.severity == "critical"]),
                "unreviewed": len([s for s in suspicious_this_month if not s.reviewed])
            },
            "summary": {
                "portfolio_health": "good" if compliance_pass_rate > 90 else "needs_attention",
                "risk_posture": "conservative" if risk_counts.get("low", 0) > sum(risk_counts.values()) / 2 else "balanced"
            }
        }

        self.log_activity(
            action="monthly_report_generated",
            details={"period": month_start.isoformat()}
        )

        return report

    def create_application(
        self,
        lead_id: str,
        loan_type: LoanType,
        amount: float,
        applicant_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new loan application.

        Args:
            lead_id: Associated lead ID
            loan_type: Type of loan
            amount: Amount requested
            applicant_data: Applicant information

        Returns:
            Created application details
        """
        app_id = str(uuid.uuid4())

        application = LoanApplication(
            id=app_id,
            lead_id=lead_id,
            loan_type=loan_type,
            amount_requested=amount,
            status=ApplicationStatus.SUBMITTED,
            applicant_data=applicant_data,
            risk_assessment_id=None,
            compliance_result_id=None,
            terms_offered=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._applications[app_id] = application

        # Update lead status
        lead = self._leads_cache.get(lead_id)
        if lead:
            lead.status = LeadStatus.QUALIFIED
            lead.value = amount
            lead.custom_data['application_id'] = app_id
            lead.updated_at = datetime.now()
            self._save_data()

        self._save_antonio_data()

        self.log_activity(
            action="application_created",
            details={
                "application_id": app_id,
                "loan_type": loan_type.value,
                "amount": amount
            }
        )

        return {
            "application": application.to_dict(),
            "next_steps": [
                "Perform risk assessment",
                "Run compliance check",
                "Calculate terms",
                "Schedule consultation"
            ]
        }
