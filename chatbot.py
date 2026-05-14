# chatbot.py
# Enhanced chatbot for Blood Bank Management System
# Handles user messages with rule-based replies that query the database
# Supports real-time inventory, donor, and request information.

import re
import os
from datetime import datetime, timedelta, date

# Import database models and db instance from your project
from models import Donor, BloodInventory, BloodRequest
from database import db

# ----------------------------------------------------------------------
# Configuration (set these environment variables if using AI fallback)
AI_API_KEY = os.environ.get('AI_API_KEY', None)
AI_API_URL = os.environ.get('AI_API_URL', None)
AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
# ----------------------------------------------------------------------

LOW_STOCK_THRESHOLD = 5

def get_bot_response(user_message: str) -> str:
    """
    Main entry point: processes the user's message and returns a reply.
    """
    # Clean and normalize the message
    msg = user_message.lower().strip()
    msg = re.sub(r'[^\w\s]', '', msg)  # remove punctuation

    # 1. Try to match known intents using keywords / regex
    reply = rule_based_response(msg, user_message)
    if reply:
        return reply

    # 2. If no rule matched and an AI API is configured, use it
    if AI_API_KEY and AI_API_URL:
        return ai_fallback_response(user_message)

    # 3. Default fallback
    return ("I'm sorry, I didn't understand that. You can ask me about "
            "donor eligibility, blood type compatibility, current inventory, "
            "low stock alerts, expiring units, donor statistics, pending requests, "
            "or how to request blood.")

# ----------------------------------------------------------------------
# Rule based responses
# ----------------------------------------------------------------------

def rule_based_response(msg: str, original_msg: str) -> str | None:
    """
    Check the cleaned message against known patterns.
    Returns a reply string if a pattern matches, otherwise None.
    """

    # ----- Greetings -----
    if any(word in msg for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return "Hello! How can I assist you with blood bank services today?"

    # ----- Eligibility (who can donate) -----
    if any(word in msg for word in ['eligibility', 'eligible', 'can i donate', 'who can donate']):
        return ("Generally, blood donors should:\n"
                "• Be at least 18 years old (or 16 with parental consent in some regions)\n"
                "• Weigh at least 50 kg (110 lbs)\n"
                "• Be in good health and feel well on donation day\n"
                "• Not have donated whole blood in the last 56 days\n\n"
                "Please consult our staff for a full eligibility check.")

    # ----- Blood type compatibility -----
    if any(word in msg for word in ['compatible', 'compatibility', 'match', 'can receive', 'donate to']):
        blood_type_match = extract_blood_type(original_msg)
        if blood_type_match:
            return get_compatibility_info(blood_type_match)
        else:
            return ("I can tell you which blood types are compatible. "
                    "Just mention a specific type, e.g., 'What is compatible with A+?'")

    # ----- Donor statistics -----
    if any(word in msg for word in ['total donors', 'how many donors', 'donor count', 'number of donors']):
        return get_total_donors()
    if any(word in msg for word in ['donors by blood', 'donor distribution', 'donors per type']):
        return get_donors_by_blood_type()
    if any(word in msg for word in ['recent donors', 'last donation', 'donated recently']):
        days_match = re.search(r'(\d+)\s*days?', msg)
        days = int(days_match.group(1)) if days_match else 30
        return get_recent_donors(days)

    # ----- Blood request statistics -----
    if any(word in msg for word in ['pending requests', 'how many pending', 'requests pending']):
        return get_pending_requests()
    if any(word in msg for word in ['requests by blood', 'requests per type']):
        return get_requests_by_blood_type()
    if any(word in msg for word in ['fulfilled requests', 'completed requests']):
        return get_fulfilled_requests()

    # ----- Inventory / stock (specific type) -----
    if any(word in msg for word in ['inventory', 'stock', 'how many', 'available', 'units', 'have']):
        blood_type_match = extract_blood_type(original_msg)
        if blood_type_match:
            return get_inventory_for_type(blood_type_match)
        else:
            return get_inventory_summary()

    # ----- Low stock alerts -----
    if any(word in msg for word in ['low stock', 'low on', 'shortage', 'running low', 'alert']):
        return get_low_stock_info()

    # ----- Expiring soon -----
    if any(word in msg for word in ['expiring', 'expiry', 'expire', 'soon', 'about to expire']):
        days_match = re.search(r'(\d+)\s*days?', msg)
        days = int(days_match.group(1)) if days_match else 7
        return get_expiring_soon(days)

    # ----- How to request blood -----
    if any(word in msg for word in ['request blood', 'how to request', 'need blood', 'place request']):
        return ("To request blood, please log in and go to the 'Requests' page, "
                "then click 'New Request'. You will need patient and hospital details. "
                "Alternatively, you can ask our staff for assistance.")

    # ----- How to become a donor -----
    if any(word in msg for word in ['become donor', 'register as donor', 'sign up', 'donate blood']):
        return ("Thank you for your interest in donating! Please log in and visit the "
                "'Donors' page, then click 'Add New Donor'. Our team will contact you "
                "for further steps.")

    # ----- Contact / help -----
    if any(word in msg for word in ['contact', 'phone', 'email', 'help', 'support']):
        return ("You can reach our blood bank at:\n"
                "📞 Phone: +91 1234 567 890\n"
                "📧 Email: support@bloodbank.org\n"
                "Or visit us during working hours.")

    # ----- No match -----
    return None

# ----------------------------------------------------------------------
# Helper: extract blood type from message
# ----------------------------------------------------------------------
def extract_blood_type(text: str) -> str | None:
    """
    Extract a standard blood type (e.g., A+, B-, AB+, O-) from the text.
    Returns the matched blood type or None.
    """
    # Order matters: AB+ before A+, AB- before A-, etc.
    pattern = r'(AB\+|AB-|A\+|A-|B\+|B-|O\+|O-)'
    match = re.search(pattern, text.upper())
    return match.group(0) if match else None

# ----------------------------------------------------------------------
# Database query functions
# ----------------------------------------------------------------------

def get_inventory_for_type(blood_type: str) -> str:
    """
    Query the database for total units of a specific blood type.
    """
    try:
        total = db.session.query(db.func.sum(BloodInventory.quantity)) \
                          .filter(BloodInventory.blood_type == blood_type.upper()) \
                          .scalar() or 0
        return f"We currently have **{total} units** of {blood_type.upper()} available."
    except Exception as e:
        print(f"DB error in get_inventory_for_type: {e}")
        return "Sorry, I couldn't retrieve inventory information at the moment."

def get_inventory_summary() -> str:
    """
    Return a summary of all blood types in inventory.
    """
    try:
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        summary = []
        for bt in blood_types:
            total = db.session.query(db.func.sum(BloodInventory.quantity)) \
                              .filter(BloodInventory.blood_type == bt) \
                              .scalar() or 0
            summary.append(f"{bt}: {total} units")
        return "Current inventory:\n" + "\n".join(summary)
    except Exception as e:
        print(f"DB error in get_inventory_summary: {e}")
        return "Sorry, I couldn't retrieve inventory information at the moment."

def get_low_stock_info() -> str:
    """
    Return list of blood types with quantity below LOW_STOCK_THRESHOLD.
    """
    try:
        low_items = BloodInventory.query.filter(BloodInventory.quantity < LOW_STOCK_THRESHOLD).all()
        if not low_items:
            return f"All blood types have adequate stock (≥ {LOW_STOCK_THRESHOLD} units)."
        result = "Low stock alerts:\n"
        for item in low_items:
            result += f"• {item.blood_type}: only {item.quantity} units left\n"
        return result.strip()
    except Exception as e:
        print(f"DB error in get_low_stock_info: {e}")
        return "Sorry, I couldn't retrieve low stock information."

def get_expiring_soon(days: int = 7) -> str:
    """
    Return list of inventory items expiring within 'days' from today.
    """
    try:
        expiry_threshold = date.today() + timedelta(days=days)
        expiring = BloodInventory.query.filter(BloodInventory.expiry_date <= expiry_threshold) \
                                        .filter(BloodInventory.expiry_date >= date.today()) \
                                        .all()
        if not expiring:
            return f"No blood units are expiring within the next {days} days."
        result = f"Blood units expiring within {days} days:\n"
        for item in expiring:
            days_left = (item.expiry_date - date.today()).days
            result += f"• {item.blood_type}: {item.quantity} units expire on {item.expiry_date} ({days_left} days left)\n"
        return result.strip()
    except Exception as e:
        print(f"DB error in get_expiring_soon: {e}")
        return "Sorry, I couldn't retrieve expiry information."

def get_total_donors() -> str:
    """
    Return total number of registered donors.
    """
    try:
        total = Donor.query.count()
        return f"Total registered donors: **{total}**."
    except Exception as e:
        print(f"DB error in get_total_donors: {e}")
        return "Sorry, I couldn't retrieve donor count."

def get_donors_by_blood_type() -> str:
    """
    Return donor count grouped by blood type.
    """
    try:
        stats = db.session.query(Donor.blood_type, db.func.count(Donor.id)) \
                          .group_by(Donor.blood_type).all()
        if not stats:
            return "No donors registered yet."
        result = "Donors by blood type:\n"
        for bt, cnt in stats:
            result += f"• {bt}: {cnt} donors\n"
        return result.strip()
    except Exception as e:
        print(f"DB error in get_donors_by_blood_type: {e}")
        return "Sorry, I couldn't retrieve donor distribution."

def get_recent_donors(days: int = 30) -> str:
    """
    Return number of donors who have donated within the last 'days' days.
    """
    try:
        since_date = date.today() - timedelta(days=days)
        recent = Donor.query.filter(Donor.last_donation >= since_date).count()
        return f"Number of donors who donated in the last {days} days: **{recent}**."
    except Exception as e:
        print(f"DB error in get_recent_donors: {e}")
        return "Sorry, I couldn't retrieve recent donation data."

def get_pending_requests() -> str:
    """
    Return count of pending blood requests.
    """
    try:
        pending = BloodRequest.query.filter_by(status='Pending').count()
        return f"Pending blood requests: **{pending}**."
    except Exception as e:
        print(f"DB error in get_pending_requests: {e}")
        return "Sorry, I couldn't retrieve request data."

def get_fulfilled_requests() -> str:
    """
    Return count of fulfilled blood requests.
    """
    try:
        fulfilled = BloodRequest.query.filter_by(status='Fulfilled').count()
        return f"Fulfilled blood requests: **{fulfilled}**."
    except Exception as e:
        print(f"DB error in get_fulfilled_requests: {e}")
        return "Sorry, I couldn't retrieve request data."

def get_requests_by_blood_type() -> str:
    """
    Return request counts (pending) grouped by blood type.
    """
    try:
        stats = db.session.query(BloodRequest.blood_type, db.func.count(BloodRequest.id)) \
                          .filter_by(status='Pending') \
                          .group_by(BloodRequest.blood_type).all()
        if not stats:
            return "No pending requests."
        result = "Pending requests by blood type:\n"
        for bt, cnt in stats:
            result += f"• {bt}: {cnt} requests\n"
        return result.strip()
    except Exception as e:
        print(f"DB error in get_requests_by_blood_type: {e}")
        return "Sorry, I couldn't retrieve request distribution."

def get_compatibility_info(blood_type: str) -> str:
    """
    Return compatibility information for a given blood type.
    """
    compatibility = {
        'A+':  "A+ can receive from: A+, A-, O+, O-",
        'A-':  "A- can receive from: A-, O-",
        'B+':  "B+ can receive from: B+, B-, O+, O-",
        'B-':  "B- can receive from: B-, O-",
        'AB+': "AB+ can receive from: all blood types (universal recipient)",
        'AB-': "AB- can receive from: AB-, A-, B-, O-",
        'O+':  "O+ can receive from: O+, O-",
        'O-':  "O- can receive from: O- only (universal donor)",
    }
    return compatibility.get(blood_type.upper(),
                             f"Sorry, I don't recognize '{blood_type}'. Please use standard blood types like A+, O-, etc.")

# ----------------------------------------------------------------------
# AI fallback (optional)
# ----------------------------------------------------------------------

def ai_fallback_response(user_message: str) -> str:
    """
    Send the user message to an AI API (e.g., OpenAI) and return the reply.
    Requires AI_API_KEY and AI_API_URL to be set.
    """
    if not AI_API_KEY or not AI_API_URL:
        return ("I'm not sure how to answer that. Please contact our staff for assistance.")

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for a blood bank management system. Answer politely and concisely."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        import requests
        response = requests.post(AI_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content'].strip()
        else:
            return "I received an unexpected response from the AI service."
    except Exception as e:
        print(f"AI API error: {e}")
        return "I'm having trouble connecting to my knowledge base right now. Please try again later."

