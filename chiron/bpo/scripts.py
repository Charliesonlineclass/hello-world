"""
CHIRON BPO - Script Management System
Call scripts and rebuttal handling for healthcare campaigns

⚔️ Structured scripts for consistent performance
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════
# SCRIPT SECTION TYPES
# ═══════════════════════════════════════════════════════════════════════

class ScriptSection(Enum):
    """Standard script sections"""
    OPENER = "opener"
    VERIFY = "verify"
    PITCH = "pitch"
    QUALIFY = "qualify"
    OBJECTION = "objection"
    CLOSE = "close"
    CONFIRM = "confirm"


# ═══════════════════════════════════════════════════════════════════════
# SCRIPT DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Rebuttal:
    """Single objection rebuttal"""
    trigger: str              # What the customer says
    response: str             # Agent's response
    follow_up: Optional[str] = None  # Optional follow-up
    tips: List[str] = field(default_factory=list)


@dataclass
class Script:
    """Complete call script"""
    id: str
    name: str
    campaign_id: str
    sections: Dict[str, str] = field(default_factory=dict)
    rebuttals: Dict[str, Rebuttal] = field(default_factory=dict)
    variables: List[str] = field(default_factory=list)

    def get_section(self, section: ScriptSection) -> str:
        """Get script section text"""
        return self.sections.get(section.value, "")

    def get_rebuttal(self, objection_key: str) -> Optional[Rebuttal]:
        """Get rebuttal for objection"""
        return self.rebuttals.get(objection_key)

    def render(self, section: ScriptSection, variables: Dict[str, str]) -> str:
        """Render section with variables filled in"""
        text = self.get_section(section)
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", value)
        return text

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "campaign_id": self.campaign_id,
            "sections": self.sections,
            "rebuttals": {k: vars(v) for k, v in self.rebuttals.items()},
            "variables": self.variables
        }


# ═══════════════════════════════════════════════════════════════════════
# NSIPA HEALTHCARE SCRIPT
# ═══════════════════════════════════════════════════════════════════════

NSIPA_SCRIPT = Script(
    id="nsipa_wellness",
    name="NSIPA Annual Wellness Visit",
    campaign_id="nsipa",
    variables=["agent_name", "patient_name", "doctor_name", "date", "time"],
    sections={
        "opener": """Hi, this is {agent_name} calling from NSIPA Healthcare
on a recorded line. How are you doing today?""",

        "verify": """Am I speaking with {patient_name}?

[IF NO] Is {patient_name} available? I'll hold.
[IF YES] Continue to pitch.""",

        "pitch": """Great! I'm calling because you're due for your
Annual Wellness Visit with your Medicare benefits.

This is a FREE preventive care visit - it's covered 100% by Medicare
with no copay or deductible.

The visit includes:
• Review of your medical history
• Health risk assessment
• Personalized prevention plan
• Screenings and immunizations

It only takes about 30-45 minutes and helps catch any health issues early.""",

        "qualify": """To make sure we get you scheduled correctly:

1. Are you currently enrolled in Medicare Part B?
2. Has it been at least 12 months since your last wellness visit?
3. Do you have a primary care doctor, or would you like us to assign one?""",

        "close": """Perfect! I have availability on {date} at {time}.

Does that work for you, or would you prefer a different day?

[IF WORKS] Excellent! Let me confirm the details...""",

        "confirm": """Great, I have you scheduled for:

📅 Date: {date}
🕐 Time: {time}
👨‍⚕️ Doctor: {doctor_name}
📍 Location: [Confirm address]

You'll receive a confirmation call 24 hours before your appointment.
Please bring your Medicare card and a list of current medications.

Is there anything else I can help you with today?"""
    },
    rebuttals={
        "not_interested": Rebuttal(
            trigger="I'm not interested",
            response="""I completely understand. Many patients feel that way initially.

Can I ask - when was the last time you had a comprehensive check-up?
This visit is specifically designed to catch issues BEFORE they become
serious problems.

And remember, it's completely FREE with your Medicare benefits.
You've already paid for it through your premiums.""",
            tips=["Stay calm and curious", "Emphasize the FREE aspect", "Don't push too hard"]
        ),

        "already_have_doctor": Rebuttal(
            trigger="I already have a doctor",
            response="""That's wonderful! This visit can actually be done WITH
your existing doctor. We're not trying to change your care -
we're helping you USE the Medicare benefits you're entitled to.

Has your doctor mentioned scheduling your Annual Wellness Visit?""",
            tips=["Validate their relationship", "Position as enhancement not replacement"]
        ),

        "call_back": Rebuttal(
            trigger="Can you call me back later?",
            response="""Of course! I want to make sure I reach you at a
convenient time.

What day and time works best for you? I'll make a note
and call you back then.

[BOOK SPECIFIC CALLBACK - date and time]""",
            tips=["Always get a specific time", "Confirm phone number", "Set reminder"]
        ),

        "too_busy": Rebuttal(
            trigger="I'm too busy right now",
            response="""I completely understand - I'll be brief.

This is just a quick call to schedule your FREE Medicare wellness visit.
It only takes about 30 seconds to book.

Do you have your calendar handy?""",
            tips=["Acknowledge their time", "Be concise", "Create urgency"]
        ),

        "send_info": Rebuttal(
            trigger="Can you send me information?",
            response="""Absolutely! I can send you details right away.

While I have you, let me ask - if the information looks good,
would you be open to scheduling? That way I can tentatively
hold a spot for you.

What's the best email address to send this to?""",
            tips=["Get email for follow-up", "Try to soft-close"]
        ),

        "spouse_decide": Rebuttal(
            trigger="I need to talk to my spouse first",
            response="""That makes perfect sense - it's always good to discuss
health decisions together.

Actually, is your spouse also on Medicare? They may be eligible
for their own wellness visit too. We could schedule you both
on the same day!

When would be a good time to call back after you've spoken?""",
            tips=["Turn objection into opportunity", "Book callback"]
        ),

        "feeling_fine": Rebuttal(
            trigger="I feel fine, I don't need a checkup",
            response="""I'm so glad to hear you're feeling well!

The purpose of this wellness visit is actually to KEEP you
feeling that way. It's preventive care - we check for things
that might not show symptoms yet.

Many conditions like high blood pressure or early diabetes
have no symptoms until they become serious. This visit can
catch those early when they're easiest to manage.""",
            tips=["Validate their health", "Educate on prevention", "Use gentle fear"]
        ),

        "medicare_question": Rebuttal(
            trigger="Is this covered by Medicare?",
            response="""Yes, 100%! This is one of the benefits of your
Medicare Part B coverage.

There's no copay, no deductible - it's completely FREE to you.
You've already paid for this benefit through your Medicare
premiums, so we want to make sure you're using it.""",
            tips=["Be emphatic about FREE", "Explain they've already paid"]
        )
    }
)


# ═══════════════════════════════════════════════════════════════════════
# SCRIPT REPOSITORY
# ═══════════════════════════════════════════════════════════════════════

class ScriptRepository:
    """Manages all call scripts"""

    def __init__(self):
        self.scripts: Dict[str, Script] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default scripts"""
        self.scripts["nsipa_wellness"] = NSIPA_SCRIPT

    def get_script(self, script_id: str) -> Optional[Script]:
        """Get script by ID"""
        return self.scripts.get(script_id)

    def get_scripts_for_campaign(self, campaign_id: str) -> List[Script]:
        """Get all scripts for a campaign"""
        return [s for s in self.scripts.values() if s.campaign_id == campaign_id]

    def add_script(self, script: Script) -> None:
        """Add a new script"""
        self.scripts[script.id] = script

    def list_rebuttals(self, script_id: str) -> Dict[str, str]:
        """Get quick reference of all rebuttals"""
        script = self.get_script(script_id)
        if not script:
            return {}
        return {k: v.trigger for k, v in script.rebuttals.items()}


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════

_repository: Optional[ScriptRepository] = None

def get_script_repository() -> ScriptRepository:
    """Get or create script repository singleton"""
    global _repository
    if _repository is None:
        _repository = ScriptRepository()
    return _repository
