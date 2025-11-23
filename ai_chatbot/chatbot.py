#!/usr/bin/env python3
"""J3 Interior Design - AI Chatbot"""

import re
from typing import Tuple, Dict, Any, List

PRICING = {
    "kitchen": {"low": "$15,000-$25,000", "mid": "$25,000-$50,000", "high": "$50,000+"},
    "bathroom": {"low": "$8,000-$15,000", "mid": "$15,000-$25,000", "high": "$25,000+"},
    "flooring": {"low": "$5,000-$10,000", "mid": "$10,000-$20,000", "high": "$20,000+"},
    "storm": {"info": "Often covered by insurance - we handle claims directly"}
}

class J3ChatBot:
    def process_message(self, message: str, history: List, lead_data: Dict) -> Tuple[str, Dict]:
        msg = message.lower()
        updated = lead_data.copy()

        # Detect project type
        for project in ["kitchen", "bathroom", "flooring", "storm"]:
            if project in msg:
                updated["projectType"] = project

        # Detect budget numbers
        if match := re.search(r'\$?(\d+),?(\d{3})?k?', msg):
            try:
                amt = int(match.group(1).replace(',', '') + (match.group(2) or ''))
                if 'k' in msg.lower(): amt *= 1000
                updated["budget_estimate"] = amt
            except: pass

        # Generate response
        if any(g in msg for g in ['hi', 'hello', 'hey']):
            response = "Hello! Welcome to J3 Interior Design. What type of project are you considering? Kitchen, bathroom, flooring, or something else?"
        elif 'kitchen' in msg:
            response = f"Kitchen remodels are our specialty! Pricing ranges: {PRICING['kitchen']['low']} for updates, {PRICING['kitchen']['mid']} for mid-range, {PRICING['kitchen']['high']} for luxury. What's your vision?"
        elif 'bathroom' in msg:
            response = f"Bathroom renovations transform your daily routine! Ranges from {PRICING['bathroom']['low']} to {PRICING['bathroom']['high']}. Are you thinking full remodel or specific updates?"
        elif 'flooring' in msg:
            response = f"Flooring makes a huge impact! Hardwood, tile, or luxury vinyl? Pricing: {PRICING['flooring']['low']} to {PRICING['flooring']['high']} depending on scope."
        elif 'storm' in msg or 'damage' in msg:
            response = "I'm sorry about the damage. We specialize in storm restoration and work directly with insurance. Have you filed a claim yet?"
        elif any(w in msg for w in ['cost', 'price', 'budget', 'much']):
            response = "Kitchens: $15k-$75k. Bathrooms: $8k-$35k. Flooring: $5k-$30k. What project and budget are you considering?"
        elif any(w in msg for w in ['schedule', 'appointment', 'consult']):
            response = "I'd love to help schedule your free consultation! What's your name and phone number?"
        else:
            response = "I can help with your project! Tell me what you're considering, or ask about pricing, timeline, or scheduling. Call (713) 555-0123 anytime."

        return response, updated

if __name__ == "__main__":
    bot = J3ChatBot()
    print("J3 Chatbot Test - type 'quit' to exit")
    history, data = [], {}
    while True:
        msg = input("You: ")
        if msg.lower() == 'quit': break
        response, data = bot.process_message(msg, history, data)
        print(f"Bot: {response}\n")
