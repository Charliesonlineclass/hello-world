"""
SCORPION-OTTER Summarizer
=========================

Meeting summarization using Ollama (MARCUS) or other LLMs.
Extracts key information, action items, decisions, and generates follow-ups.

Requirements:
    pip install requests
    Ollama running locally with mistral/llama2 model
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTTER.summarizer")

# Default Ollama configuration
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "mistral")

# Summarization prompts
PROMPTS = {
    "summary": """You are an expert meeting summarizer. Analyze this meeting transcript and provide a clear, structured summary.

TRANSCRIPT:
{transcript}

Provide a summary with:
1. **Meeting Overview** (2-3 sentences about the main topic)
2. **Key Points** (bullet points of main discussion items)
3. **Conclusions** (what was decided or concluded)

Be concise and focus on the most important information.""",

    "action_items": """Extract all action items from this meeting transcript. An action item is a task that someone committed to doing.

TRANSCRIPT:
{transcript}

List each action item in this format:
- [ ] ACTION: What needs to be done
  OWNER: Who is responsible (if mentioned)
  DEADLINE: When (if mentioned)

Only include clear commitments or tasks, not general discussion topics.""",

    "decisions": """Extract all decisions made during this meeting.

TRANSCRIPT:
{transcript}

List each decision in this format:
- DECISION: What was decided
  CONTEXT: Brief context for why (if clear)
  IMPACT: Who or what is affected

Only include firm decisions, not tentative discussions.""",

    "participants": """Identify all participants mentioned in this meeting transcript.

TRANSCRIPT:
{transcript}

List each participant:
- NAME: [name or identifier]
  ROLE: [role if mentioned]
  CONTRIBUTIONS: [brief summary of their main points]

Include both speakers and people mentioned.""",

    "followup_email": """Generate a professional follow-up email based on this meeting transcript.

TRANSCRIPT:
{transcript}

TEMPLATE STYLE: {template}

Create an email with:
- Subject line
- Greeting
- Meeting summary (2-3 sentences)
- Key decisions
- Action items with owners
- Next steps
- Professional closing

Keep it concise and actionable.""",

    "executive_summary": """Create an executive summary of this meeting for senior leadership.

TRANSCRIPT:
{transcript}

Provide:
1. **Bottom Line** (1-2 sentences - what leadership needs to know)
2. **Key Decisions** (brief bullets)
3. **Risks/Concerns** (if any)
4. **Next Steps** (high-level)

Maximum 200 words. Focus on business impact."""
}


def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    host: str = OLLAMA_HOST,
    temperature: float = 0.3,
    max_tokens: int = 2000
) -> str:
    """
    Call Ollama API for text generation.

    Args:
        prompt: The prompt to send
        model: Ollama model name
        host: Ollama API host
        temperature: Generation temperature (lower = more focused)
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text response
    """
    url = f"{host}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    try:
        logger.info(f"Calling Ollama ({model})...")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {host}. "
            "Make sure Ollama is running: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama request timed out. Try a smaller model or shorter transcript.")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise


def call_openai(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    temperature: float = 0.3
) -> str:
    """
    Alternative: Call OpenAI API for summarization.

    Args:
        prompt: The prompt to send
        model: OpenAI model name
        api_key: OpenAI API key (or from OPENAI_API_KEY env)
        temperature: Generation temperature

    Returns:
        Generated text response
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


def summarize_meeting(
    transcript: str,
    model: str = DEFAULT_MODEL,
    use_openai: bool = False,
    style: str = "summary"
) -> str:
    """
    Summarize a meeting transcript.

    Args:
        transcript: Full meeting transcript text
        model: Model to use for summarization
        use_openai: Use OpenAI instead of Ollama
        style: Summary style ("summary", "executive_summary")

    Returns:
        Meeting summary text
    """
    if style not in PROMPTS:
        style = "summary"

    prompt = PROMPTS[style].format(transcript=transcript)

    if use_openai:
        return call_openai(prompt, model)
    else:
        return call_ollama(prompt, model)


def extract_action_items(
    transcript: str,
    model: str = DEFAULT_MODEL,
    use_openai: bool = False
) -> List[Dict]:
    """
    Extract action items from transcript.

    Args:
        transcript: Full meeting transcript
        model: Model to use
        use_openai: Use OpenAI instead of Ollama

    Returns:
        List of action item dictionaries with action, owner, deadline
    """
    prompt = PROMPTS["action_items"].format(transcript=transcript)

    if use_openai:
        response = call_openai(prompt, model)
    else:
        response = call_ollama(prompt, model)

    # Parse the response into structured format
    action_items = []
    current_item = {}

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('- [ ]') or line.startswith('- [x]'):
            if current_item:
                action_items.append(current_item)
            # Extract action text
            action_text = line[5:].strip()
            if action_text.startswith('ACTION:'):
                action_text = action_text[7:].strip()
            current_item = {
                'action': action_text,
                'owner': None,
                'deadline': None,
                'completed': line.startswith('- [x]')
            }
        elif line.startswith('OWNER:'):
            if current_item:
                current_item['owner'] = line[6:].strip()
        elif line.startswith('DEADLINE:'):
            if current_item:
                current_item['deadline'] = line[9:].strip()

    if current_item:
        action_items.append(current_item)

    # If parsing failed, return raw response as single item
    if not action_items and response:
        action_items = [{'action': response, 'owner': None, 'deadline': None}]

    return action_items


def extract_decisions(
    transcript: str,
    model: str = DEFAULT_MODEL,
    use_openai: bool = False
) -> List[Dict]:
    """
    Extract decisions from transcript.

    Args:
        transcript: Full meeting transcript
        model: Model to use
        use_openai: Use OpenAI instead of Ollama

    Returns:
        List of decision dictionaries
    """
    prompt = PROMPTS["decisions"].format(transcript=transcript)

    if use_openai:
        response = call_openai(prompt, model)
    else:
        response = call_ollama(prompt, model)

    # Parse decisions
    decisions = []
    current_decision = {}

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('- DECISION:') or line.startswith('DECISION:'):
            if current_decision:
                decisions.append(current_decision)
            decision_text = line.split('DECISION:', 1)[-1].strip()
            current_decision = {
                'decision': decision_text,
                'context': None,
                'impact': None
            }
        elif line.startswith('CONTEXT:'):
            if current_decision:
                current_decision['context'] = line[8:].strip()
        elif line.startswith('IMPACT:'):
            if current_decision:
                current_decision['impact'] = line[7:].strip()

    if current_decision:
        decisions.append(current_decision)

    return decisions


def extract_participants(
    transcript: str,
    model: str = DEFAULT_MODEL,
    use_openai: bool = False
) -> List[Dict]:
    """
    Extract participant information from transcript.

    Args:
        transcript: Full meeting transcript
        model: Model to use
        use_openai: Use OpenAI instead of Ollama

    Returns:
        List of participant dictionaries
    """
    prompt = PROMPTS["participants"].format(transcript=transcript)

    if use_openai:
        response = call_openai(prompt, model)
    else:
        response = call_ollama(prompt, model)

    # Parse participants
    participants = []
    current_participant = {}

    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('- NAME:') or line.startswith('NAME:'):
            if current_participant:
                participants.append(current_participant)
            name = line.split('NAME:', 1)[-1].strip()
            current_participant = {
                'name': name,
                'role': None,
                'contributions': None
            }
        elif line.startswith('ROLE:'):
            if current_participant:
                current_participant['role'] = line[5:].strip()
        elif line.startswith('CONTRIBUTIONS:'):
            if current_participant:
                current_participant['contributions'] = line[14:].strip()

    if current_participant:
        participants.append(current_participant)

    return participants


def generate_followup_email(
    transcript: str,
    template: str = "professional",
    model: str = DEFAULT_MODEL,
    use_openai: bool = False,
    recipient_name: Optional[str] = None,
    sender_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate a follow-up email based on meeting transcript.

    Args:
        transcript: Full meeting transcript
        template: Email style (professional, casual, brief)
        model: Model to use
        use_openai: Use OpenAI instead of Ollama
        recipient_name: Name of email recipient
        sender_name: Name of sender

    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    prompt = PROMPTS["followup_email"].format(
        transcript=transcript,
        template=template
    )

    if recipient_name:
        prompt += f"\n\nAddress the email to: {recipient_name}"
    if sender_name:
        prompt += f"\nSign the email as: {sender_name}"

    if use_openai:
        response = call_openai(prompt, model)
    else:
        response = call_ollama(prompt, model)

    # Parse subject and body
    subject = "Meeting Follow-up"
    body = response

    lines = response.split('\n')
    for i, line in enumerate(lines):
        if line.lower().startswith('subject:'):
            subject = line.split(':', 1)[-1].strip()
            # Body is everything after subject line
            body = '\n'.join(lines[i+1:]).strip()
            break

    return {
        'subject': subject,
        'body': body
    }


def full_analysis(
    transcript: str,
    model: str = DEFAULT_MODEL,
    use_openai: bool = False
) -> Dict:
    """
    Perform full meeting analysis: summary, actions, decisions, participants.

    Args:
        transcript: Full meeting transcript
        model: Model to use
        use_openai: Use OpenAI instead of Ollama

    Returns:
        Complete analysis dictionary
    """
    logger.info("Starting full meeting analysis...")

    analysis = {
        'timestamp': datetime.now().isoformat(),
        'model': model,
        'summary': None,
        'action_items': [],
        'decisions': [],
        'participants': [],
        'executive_summary': None
    }

    # Run all extractions
    logger.info("Generating summary...")
    analysis['summary'] = summarize_meeting(transcript, model, use_openai)

    logger.info("Extracting action items...")
    analysis['action_items'] = extract_action_items(transcript, model, use_openai)

    logger.info("Extracting decisions...")
    analysis['decisions'] = extract_decisions(transcript, model, use_openai)

    logger.info("Identifying participants...")
    analysis['participants'] = extract_participants(transcript, model, use_openai)

    logger.info("Creating executive summary...")
    analysis['executive_summary'] = summarize_meeting(
        transcript, model, use_openai, style="executive_summary"
    )

    logger.info("Analysis complete!")
    return analysis


def save_analysis(
    analysis: Dict,
    output_path: Optional[Union[str, Path]] = None,
    meeting_name: Optional[str] = None
) -> Path:
    """
    Save meeting analysis to file.

    Args:
        analysis: Analysis dictionary from full_analysis()
        output_path: Output file path
        meeting_name: Meeting name for auto-generated filename

    Returns:
        Path to saved file
    """
    if output_path is None:
        analysis_dir = Path("meeting_analysis")
        analysis_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = meeting_name or "meeting"
        name = name.replace(" ", "_").lower()
        output_path = analysis_dir / f"{name}_{timestamp}_analysis.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)

    logger.info(f"Analysis saved: {output_path}")
    return output_path


def analysis_to_markdown(analysis: Dict) -> str:
    """
    Convert analysis to markdown format.

    Args:
        analysis: Analysis dictionary

    Returns:
        Markdown formatted string
    """
    md = [
        "# Meeting Analysis",
        f"",
        f"*Generated: {analysis.get('timestamp', 'Unknown')}*",
        f"*Model: {analysis.get('model', 'Unknown')}*",
        f"",
        "---",
        f"",
        "## Executive Summary",
        f"",
        analysis.get('executive_summary', 'Not available'),
        f"",
        "---",
        f"",
        "## Detailed Summary",
        f"",
        analysis.get('summary', 'Not available'),
        f"",
        "---",
        f"",
        "## Action Items",
        f""
    ]

    for item in analysis.get('action_items', []):
        checkbox = "[x]" if item.get('completed') else "[ ]"
        md.append(f"- {checkbox} **{item.get('action', 'Unknown action')}**")
        if item.get('owner'):
            md.append(f"  - Owner: {item['owner']}")
        if item.get('deadline'):
            md.append(f"  - Deadline: {item['deadline']}")

    md.extend([
        f"",
        "---",
        f"",
        "## Key Decisions",
        f""
    ])

    for decision in analysis.get('decisions', []):
        md.append(f"- **{decision.get('decision', 'Unknown decision')}**")
        if decision.get('context'):
            md.append(f"  - Context: {decision['context']}")
        if decision.get('impact'):
            md.append(f"  - Impact: {decision['impact']}")

    md.extend([
        f"",
        "---",
        f"",
        "## Participants",
        f""
    ])

    for participant in analysis.get('participants', []):
        md.append(f"- **{participant.get('name', 'Unknown')}**")
        if participant.get('role'):
            md.append(f"  - Role: {participant['role']}")
        if participant.get('contributions'):
            md.append(f"  - Contributions: {participant['contributions']}")

    return '\n'.join(md)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python summarizer.py <transcript_file> [model]")
        print("Example: python summarizer.py meeting.txt mistral")
        sys.exit(1)

    transcript_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL

    # Read transcript
    with open(transcript_file, 'r') as f:
        transcript = f.read()

    # Run full analysis
    print(f"\n{'='*60}")
    print(f"ANALYZING MEETING WITH {model.upper()}")
    print(f"{'='*60}\n")

    analysis = full_analysis(transcript, model)

    # Save and display
    output_path = save_analysis(analysis)
    markdown = analysis_to_markdown(analysis)

    print(markdown)
    print(f"\n{'='*60}")
    print(f"Analysis saved to: {output_path}")
    print(f"{'='*60}")
