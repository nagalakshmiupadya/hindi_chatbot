from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS

import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=API_KEY)
app = Flask(__name__)
CORS(app)

# Simplified predefined responses in Hindi
PREDEFINED_RESPONSES = {
    "रेशम साड़ी": """
• मूल्य श्रेणी: ₹5,000 - ₹50,000
• उपलब्ध रंग: बैंगनी, लाल, हरा, नीला
• विशेष ऑफर: 20% की छूट""",
    
    "डिलीवरी और वापसी नीति": """
• डिलीवरी समय: 3-5 दिन
• ₹5,000 से अधिक के ऑर्डर पर मुफ्त डिलीवरी
• 7 दिन की वापसी नीति""",
    
    "ग्राहक सहायता": """
• फोन: +91 8123040488 
• समय: सुबह 10 - रात 8
• ईमेल: nithin.vs@saree-mahal.com"""
}

# System prompt in Hindi
SYSTEM_PROMPT = """
Instructions for AI (do not include this in response):
1. केवल हिंदी में जवाब दें
2. सीधे जवाब दें, बिना किसी प्रीफिक्स या सिस्टम मैसेज के
3. केवल 3-4 बुलेट पॉइंट्स का उपयोग करें
4. विशिष्ट, संरचित और सटीक रहें
5. केवल साड़ी महल स्टोर से संबंधित प्रश्नों का जवाब दें
6. जवाब में नियम या फॉर्मेटिंग का उल्लेख न करें
"""

# Context prompt in Hindi
CONTEXT_PROMPT = """
You are a Saree Mahal store assistant. Before answering any question, check if it's related to:
1. साड़ियां (प्रकार, कीमत, डिजाइन, सामग्री)
2. स्टोर सेवाएं (डिलीवरी, वापसी, ग्राहक सहायता)
3. स्टोर ऑफर और कलेक्शन
4. खरीदारी सहायता

If the question is NOT related to these topics, respond with:
"• क्षमा करें, मैं केवल साड़ी महल से संबंधित प्रश्नों का उत्तर दे सकता/सकती हूं"

For valid questions, proceed with the answer following the main system prompt.
"""

def get_chatbot_response(user_input):
    try:
        # Check predefined responses first
        if user_input in PREDEFINED_RESPONSES:
            return PREDEFINED_RESPONSES[user_input]

        # Add specific responses for sub-options
        specific_responses = {
            "विशेष संग्रह उपलब्ध": """
• नए डिजाइनर साड़ी कलेक्शन ₹15,000 से शुरू
• प्रत्येक साड़ी अनूठी और सीमित संस्करण
• विशेष संग्रह पर 15% की छूट उपलब्ध""",
            "ग्राहक सहायता": """
• फोन: +91 8123040488
• समय: सुबह 10 - रात 8
• ईमेल: nithin.vs@saree-mahal.com"""
        }

        if user_input in specific_responses:
            return specific_responses[user_input]

        # Check if question is relevant
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        relevance_check = model.generate_content([
            {"text": CONTEXT_PROMPT},
            {"text": f"Is this question related to Saree Mahal store: {user_input}? Respond with only 'yes' or 'no'."}
        ])

        if relevance_check.text.strip().lower() != 'yes':
            return "• क्षमा करें, मैं केवल साड़ी महल से संबंधित प्रश्नों का उत्तर दे सकता/सकती हूं"

        # Get the answer
        response = model.generate_content([
            {"text": SYSTEM_PROMPT},
            {"text": user_input}
        ])
        
        if not response.text:
            return "क्षमा करें, मैं समझ नहीं पाया"
        
        # Clean up response
        lines = [line.strip() for line in response.text.split('\n') if line.strip()]
        lines = [line for line in lines if not any(x in line.lower() for x in ['rule', 'नियम', 'according', 'अनुसार'])]
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            line = line.replace('*', '').replace('•', '').strip()
            if line:
                formatted_lines.append(f"• {line}")
        
        formatted_lines = [line.replace('साड़ी महल', '<strong>साड़ी महल</strong>') for line in formatted_lines]
        
        return '\n'.join(formatted_lines[:3])

    except Exception as e:
        print(f"Error: {str(e)}")
        return "तकनीकी त्रुटि हुई है"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"response": "कृपया कोई संदेश टाइप करें"})

        response = get_chatbot_response(user_input)
        return jsonify({"response": response})

    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({"response": "त्रुटि हुई है"})

if __name__ == '__main__':
    app.run(debug=True)