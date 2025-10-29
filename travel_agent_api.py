"""
AI Travel Planning Agent - Real Version
Uses Claude AI to generate custom travel itineraries based on user input
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "AI Travel Planning Agent",
        "version": "1.0",
        "endpoints": {
            "plan_trip": "/api/plan-trip"
        }
    })

@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    """
    Generate a custom travel itinerary using Claude AI
    
    Expected JSON body:
    {
        "destination": "Greece",
        "travelers": "Family of 4 (2 adults, 2 young adults)",
        "duration": "7 days",
        "dates": "June 15-22, 2026",
        "budget": "$8,000-10,000",
        "departureCity": "Austin, Texas",
        "interests": ["history", "food", "beaches"],
        "pace": "relaxed",
        "specialRequests": "Family-friendly, love culture"
    }
    """
    
    # Validate request
    if not request.is_json:
        return jsonify({
            "error": True,
            "message": "Content-Type must be application/json",
            "statusCode": 400
        }), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['destination', 'travelers', 'duration']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            "error": True,
            "message": f"Missing required fields: {', '.join(missing_fields)}",
            "statusCode": 400
        }), 400
    
    # Extract data with defaults
    destination = data.get('destination')
    travelers = data.get('travelers')
    duration = data.get('duration')
    dates = data.get('dates', 'Flexible')
    budget = data.get('budget', 'Moderate budget')
    departure_city = data.get('departureCity', 'United States')
    interests = ', '.join(data.get('interests', ['sightseeing', 'culture', 'food']))
    pace = data.get('pace', 'moderate')
    special_requests = data.get('specialRequests', '')
    
    # Build the system prompt
    system_prompt = """You are an expert travel planning AI agent with 20+ years of experience in creating personalized travel itineraries. You have deep knowledge of destinations worldwide, cultural insights, logistics optimization, and budget management.

Your approach is:
- Thorough and detail-oriented
- Culturally sensitive and authentic
- Budget-conscious while maximizing value
- Focused on creating memorable experiences
- Practical with realistic timing and logistics

You create comprehensive travel plans that include:
- Flight recommendations with specific airlines and routes
- Accommodation suggestions with pricing
- Day-by-day detailed itineraries
- Restaurant and dining recommendations
- Activity bookings and timing
- Transportation logistics
- Budget breakdown
- Pro tips and local insights"""
    
    # Build the user prompt
    user_prompt = f"""Create a comprehensive, personalized travel itinerary with the following parameters:

**Trip Overview:**
- Destination: {destination}
- Travelers: {travelers}
- Duration: {duration}
- Travel Dates: {dates}
- Budget: {budget}
- Departing From: {departure_city}
- Interests: {interests}
- Preferred Pace: {pace}
{f"- Special Requests: {special_requests}" if special_requests else ""}

**Required Deliverables:**

1. **EXECUTIVE SUMMARY** (2-3 paragraphs)
   - Trip overview and highlights
   - What makes this itinerary special
   - Budget summary

2. **FLIGHTS & TRANSPORTATION**
   - Specific flight recommendations (airline, route, approximate pricing)
   - Airport transfers
   - Local transportation options
   - Inter-city travel if applicable

3. **ACCOMMODATIONS**
   - Hotel/lodging recommendations for each location
   - Why each is a good fit
   - Approximate nightly rates and total
   - Booking tips

4. **DETAILED DAY-BY-DAY ITINERARY**
   For EACH day include:
   - Day number and date
   - Morning activities (with times)
   - Lunch recommendations
   - Afternoon activities
   - Dinner suggestions
   - Evening options
   - Approximate costs per activity
   - Pro tips and insider advice

5. **RESTAURANT & DINING GUIDE**
   - 10-15 restaurant recommendations
   - Cuisine type, price range, why recommended
   - Reservation requirements

6. **ACTIVITIES & EXPERIENCES**
   - Must-do attractions with timing and cost
   - Hidden gems
   - Cultural experiences
   - Family-friendly options
   - Booking requirements

7. **BUDGET BREAKDOWN**
   - Flights: $X
   - Accommodations: $X
   - Activities: $X
   - Meals: $X
   - Transportation: $X
   - Contingency: $X
   - **Total: $X**

8. **PRACTICAL TIPS**
   - Best time to visit attractions (avoid crowds)
   - What to pack
   - Cultural etiquette
   - Money-saving tips
   - Safety considerations
   - Phone/internet recommendations

9. **BOOKING CHECKLIST & TIMELINE**
   - What to book immediately
   - What to book 1-2 months before
   - What to book upon arrival
   - Required reservations

10. **CALENDAR EXPORT READY**
    - Format the itinerary so it can be easily added to digital calendars
    - Include specific times and locations

**Style Guidelines:**
- Be specific with names, prices, and timing
- Use real hotel/restaurant names when possible
- Include approximate costs in USD
- Write in a friendly, enthusiastic tone
- Make it practical and actionable
- Include pro tips that show local knowledge

Generate a complete, professional travel plan that someone could actually use to book and enjoy this trip!"""
    
    try:
        # Call Claude API with extended timeout
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,  # Longer for detailed itinerary
            temperature=0.8,  # Slightly creative for variety
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        # Extract itinerary text
        itinerary = message.content[0].text
        
        # Calculate cost
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        estimated_cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
        
        # Build response
        response = {
            "success": True,
            "destination": destination,
            "itinerary": itinerary,
            "summary": {
                "travelers": travelers,
                "duration": duration,
                "dates": dates,
                "budget": budget,
                "interests": interests
            },
            "metadata": {
                "generatedAt": datetime.utcnow().isoformat() + "Z",
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "estimatedCost": f"${estimated_cost:.4f}",
                "model": "claude-sonnet-4-5-20250929"
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Error generating itinerary: {str(e)}",
            "statusCode": 500
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": True,
        "message": "Endpoint not found. Use POST /api/plan-trip",
        "statusCode": 404
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "error": True,
        "message": "Method not allowed. Use POST request.",
        "statusCode": 405
    }), 405

if __name__ == '__main__':
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY environment variable not set!")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
