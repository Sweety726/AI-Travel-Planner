import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
import re
import time
import requests
import pandas as pd

@st.cache_data
def load_destination_data():
    return pd.read_csv("destination.csv")


destination_data = load_destination_data()




# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)


# =========================================================
# 2. LOAD GEMINI API KEY
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Gemini API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)


# =========================================================
# 3. CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #f8fbff, #eef5ff);
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

/* Main headings */

h1 {
    font-weight: 800 !important;
}

h2 {
    font-weight: 700 !important;
}

h3 {
    font-weight: 700 !important;
}


/* HERO SECTION */

.hero-section {
    text-align: center;
    padding: 3rem 2rem;
    margin-bottom: 2rem;
    border-radius: 25px;
    background: linear-gradient(135deg, #e0f2fe, #f0fdf4);
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
}

.hero-icon {
    font-size: 4rem;
    margin-bottom: 0.5rem;
}

.hero-section h1 {
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    margin: 0;
}

.hero-section p {
    font-size: 1.2rem;
    margin-top: 1rem;
    line-height: 1.6;
}

.hero-tags {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 1.5rem;
}

.hero-tags span {
    padding: 8px 15px;
    border-radius: 20px;
    background: white;
    font-size: 0.9rem;
    font-weight: 600;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}


# ============================================================
# DESTINATION DATABASE
# ============================================================

#st.divider()

#st.header("📊 Destination Database")

#st.write(
    "Explore destinations available in our travel database."
)

#st.dataframe(
    destination_data,
    use_container_width=True
)

/* SECTION CARDS */

.section-card {
    background: white;
    padding: 1.5rem;
    border-radius: 20px;
    margin: 1rem 0;
    box-shadow: 0 5px 20px rgba(0,0,0,0.06);
}


/* BUTTONS */

.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    padding: 0.6rem 1.2rem;
    transition: 0.2s;
}

.stButton > button:hover {
    transform: translateY(-2px);
}


/* INPUTS */

.stTextInput input,
.stNumberInput input {
    border-radius: 12px;
}


/* DIVIDER */

hr {
    margin: 2rem 0;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. HERO SECTION
# =========================================================

st.markdown("""
<div class="hero-section">

<div class="hero-icon">✈️</div>

<h1>AI Travel Planner</h1>

<p>
        Plan smarter. Travel better. 🌍<br>
        Create personalized trips with the power of Artificial Intelligence.
</p>

<div class="hero-tags">
        <span>🤖 AI Powered</span>
        <span>🌦️ Live Weather</span>
        <span>💰 Smart Budget</span>
        <span>🎒 Packing Assistant</span>
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# 5. SESSION STATE
# =========================================================

if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

if "travel_plan" not in st.session_state:
    st.session_state.travel_plan = None

if "estimated_cost" not in st.session_state:
    st.session_state.estimated_cost = None

if "packing_checklist" not in st.session_state:
    st.session_state.packing_checklist = None

if "budget_breakdown" not in st.session_state:
    st.session_state.budget_breakdown = None

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


# =========================================================
# 6. GEMINI FUNCTION
# =========================================================

def ask_gemini(prompt):

    models = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]

    last_error = None

    for model_name in models:

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if response and response.text:
                    return response.text

            except Exception as e:

                last_error = e

                time.sleep(2 ** attempt)

    st.error(
        f"❌ Gemini could not generate a response.\n\n"
        f"Error: {last_error}"
    )

    return None


# =========================================================
# 7. DESTINATION RECOMMENDATIONS
# =========================================================

def recommend_destinations(days, budget, interests):

    prompt = f"""
You are an expert travel planner.

Recommend 5 suitable travel destinations in India.

Trip duration: {days} days
Total budget: ₹{budget}
Interests: {", ".join(interests)}

For every destination provide:

1. Destination name
2. Why it is suitable
3. Approximate budget
4. Best activities

Keep the recommendations practical for the given budget.
"""

    return ask_gemini(prompt)


# =========================================================
# 8. COMPLETE TRAVEL PLAN
# =========================================================

def generate_travel_plan(
    destination,
    days,
    budget,
    travelers,
    interests
):

    prompt = f"""
You are an expert AI travel planner.

Create a detailed but practical travel plan.

Destination: {destination}
Number of days: {days}
Budget: ₹{budget}
Number of travelers: {travelers}
Interests: {", ".join(interests)}

Include:

# Trip Overview

# Day-by-Day Itinerary

For every day include:
- Morning
- Afternoon
- Evening
- Suggested activities
- Food suggestions

# Accommodation Suggestions

# Transportation

# Places to Visit

# Local Food

# Travel Tips

# Estimated Budget

Break the budget into:
- Transportation
- Accommodation
- Food
- Activities & Sightseeing
- Shopping
- Miscellaneous

At the end write exactly:

TOTAL_TRIP_COST: <number>

Make the plan realistic and budget-friendly.
"""

    return ask_gemini(prompt)


# =========================================================
# 9. EXTRACT ESTIMATED COST
# =========================================================

def extract_estimated_cost(text):

    if not text:
        return None

    match = re.search(
        r"TOTAL_TRIP_COST\s*:\s*₹?\s*([\d,]+)",
        text,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1).replace(",", ""))

    return None


# =========================================================
# 10. BUDGET SAVING SUGGESTIONS
# =========================================================

def generate_budget_suggestions(
    budget,
    estimated_cost,
    destination
):

    prompt = f"""
You are a travel budget expert.

Destination: {destination}
User budget: ₹{budget}
Estimated trip cost: ₹{estimated_cost}

Give 5 practical ways to reduce the trip cost.

Focus on:
- transportation
- accommodation
- food
- activities
- shopping

Keep suggestions short and useful.
"""

    return ask_gemini(prompt)

# CSV DISPLAY
st.divider()

with st.expander("📊 Explore Destination Database"):

    st.write(
        "Explore destinations available in our travel database."
    )

    st.dataframe(
        destination_data,
        use_container_width=True
    )

# =========================================================
# 11. PACKING CHECKLIST
# =========================================================

def generate_packing_checklist(
    destination,
    days,
    season,
    interests
):

    prompt = f"""
You are an expert travel assistant.

Create a personalized packing checklist.

Destination: {destination}
Trip duration: {days} days
Season: {season}
Interests: {", ".join(interests)}

Organize the checklist into:

1. Clothing
2. Footwear
3. Personal Care
4. Health & Medicines
5. Electronics
6. Important Documents
7. Travel Essentials
8. Destination-specific Items

Use simple bullet points.
"""

    return ask_gemini(prompt)


# =========================================================
# 12. WEATHER FUNCTIONS
# =========================================================

def weather_code_to_text(code):

    weather_codes = {

        0: "Clear sky",

        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing rime fog",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",

        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",

        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",

        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",

        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    return weather_codes.get(
        code,
        "Unknown weather condition"
    )


def get_weather(city):

    try:

        # Geocoding

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return None

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        # Weather

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
        )

        weather_params = {

            "latitude": latitude,

            "longitude": longitude,

            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),

            "timezone": "auto"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        return {
            "location": location,
            "current": weather_data.get(
                "current",
                {}
            )
        }

    except requests.RequestException:

        return None



def get_coordinates(place):

    try:
        place = place.strip()

        if not place:
            return None

        url = "https://geocoding-api.open-meteo.com/v1/search"

        params = {
            "name": place,
            "count": 10,
            "language": "en",
            "format": "json",
            "countryCode": "IN"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        # Prefer actual cities/towns
        city_results = [
            r for r in results
            if r.get("feature_code", "").startswith("PPL")
        ]

        if city_results:
            results = city_results

        # Prefer highly populated locations
        results.sort(
            key=lambda r: r.get("population", 0),
            reverse=True
        )

        result = results[0]

        return {
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "name": result.get("name", place),
            "state": result.get("admin1", ""),
            "country": result.get("country", "")
        }

    except requests.RequestException:
        return None
    
from math import radians, sin, cos, sqrt, atan2


def calculate_distance(place1, place2):

    location1 = get_coordinates(place1)
    location2 = get_coordinates(place2)

    if not location1 or not location2:
        return None

    lat1 = location1["latitude"]
    lon1 = location1["longitude"]

    lat2 = location2["latitude"]
    lon2 = location2["longitude"]

    earth_radius = 6371

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    difference_lat = radians(lat2 - lat1)
    difference_lon = radians(lon2 - lon1)

    a = (
        sin(difference_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(difference_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c

def calculate_travel_cost(distance, travel_mode, travelers):

    rates = {
        "Train": 2.0,
        "Bus": 2.5,
        "Car": 8.0,
        "Flight": 7.0
    }

    cost_per_km = rates[travel_mode]

    total_cost = distance * cost_per_km * travelers

    return round(total_cost)

# =========================================================
# 13. TRIP DETAILS
# =========================================================

st.divider()
st.markdown("""
<div class="section-intro">
    <h2>🌍 Tell us about your trip</h2>
    <p>Enter a few details and let AI create a personalized travel experience for you.</p>
</div>
""", unsafe_allow_html=True)

# your existing destination, days, budget, travelers inputs...

current_location = st.text_input(
    "📍 Current Location",
    placeholder="e.g. Haldia"
)

destination = st.text_input(
    "📍 Enter a destination",
    placeholder="Example: Goa"
)

travel_mode = st.selectbox(
    "🚆 Travel Mode",
    ["Train", "Bus", "Car", "Flight"]
)

days = st.number_input(
    "📅 Number of days",
    min_value=1,
    max_value=30,
    value=3
)

budget = st.number_input(
    "💰 Your total budget (₹)",
    min_value=1000,
    value=10000,
    step=1000
)

travelers = st.number_input(
    "👥 Number of travelers",
    min_value=1,
    max_value=20,
    value=1
)


if st.button("💰 Calculate Travelling Expense"):

    if not current_location or not destination:
        st.warning(
            "Please enter both current location and destination."
        )

    else:

        with st.spinner("Calculating travel distance..."):

            distance = calculate_distance(
                current_location,
                destination
            )

        if distance:

            travel_cost = calculate_travel_cost(
                distance,
                travel_mode,
                travelers
            )

            st.session_state.travel_distance = distance
            st.session_state.travel_cost = travel_cost

            st.success("Travel expense calculated!")

            col1, col2 = st.columns(2)

            col1.metric(
                "📏 Approx. Straight-Line Distance",
                f"{distance:.1f} km"
 
            )

            col2.metric(
                "💰 Estimated Travel Cost",
                f"₹{travel_cost:,}"
            )

        else:

            st.error(
    f"Could not find the locations: "
    f"{current_location} → {destination}. "
    "Please enter specific city names, such as "
    "'Gaya, Bihar' or 'Bhubaneswar, Odisha'."
)
interests = st.multiselect(
    "❤️ What are your interests?",
    [
        "Nature",
        "Adventure",
        "History",
        "Food",
        "Shopping",
        "Beaches",
        "Culture",
        "Nightlife",
        "Relaxation"
    ]
)

travel_season = st.selectbox(
    "🌤️ Travel Season",
    [
        "Summer",
        "Monsoon",
        "Winter",
        "Spring",
        "Autumn"
    ]
)


# =========================================================
# 14. DESTINATION RECOMMENDATIONS
# =========================================================

st.divider()

st.header("🤖 AI Destination Recommendations")

if st.button("✨ Recommend Destinations"):

    if not interests:
        st.warning(
            "Please select at least one interest."
        )

    else:

        with st.spinner(
            "🤖 AI is finding suitable destinations..."
        ):

            recommendations = recommend_destinations(
                days,
                budget,
                interests
            )

        if recommendations:

            st.session_state.recommendations = recommendations

if st.session_state.recommendations:

    st.markdown(
        st.session_state.recommendations
    )


# =========================================================
# 15. SELECT DESTINATION
# =========================================================

selected_destination = destination

if destination:

    st.divider()

    st.subheader("📍 Choose Your Destination")

    destination_options = [destination]

    selected_destination = st.selectbox(
        "Select a destination",
        destination_options
    )

else:

    st.info(
        "Please enter a destination above."
    )



# =========================================================
# 16. WEATHER
# =========================================================

st.divider()

st.header("🌦️ Current Weather")

weather_city = (
    selected_destination
    if selected_destination
    else destination
)

if st.button("🌤️ Check Weather"):

    if not weather_city:

        st.warning(
            "Please enter a destination first."
        )

    else:

        with st.spinner(
            "Fetching current weather..."
        ):

            weather_data = get_weather(
                weather_city
            )

        if weather_data:

            current = weather_data["current"]

            location = weather_data["location"]

            st.subheader(
                f"📍 {location['name']}, "
                f"{location.get('country', '')}"
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "🌡️ Temperature",
                f"{current.get('temperature_2m', 'N/A')} °C"
            )

            col2.metric(
                "🤗 Feels Like",
                f"{current.get('apparent_temperature', 'N/A')} °C"
            )

            col3.metric(
                "💧 Humidity",
                f"{current.get('relative_humidity_2m', 'N/A')} %"
            )

            weather_code = current.get(
                "weather_code"
            )

            st.write(
                f"🌤️ **Condition:** "
                f"{weather_code_to_text(weather_code)}"
            )

            st.write(
                f"💨 **Wind Speed:** "
                f"{current.get('wind_speed_10m', 'N/A')} km/h"
            )

            st.write(
                f"🌧️ **Precipitation:** "
                f"{current.get('precipitation', 'N/A')} mm"
            )

        else:

            st.error(
                "❌ Could not fetch weather. "
                "Please check the destination name."
            )


# =========================================================
# 17. COMPLETE TRAVEL PLAN
# =========================================================

st.divider()

st.header("🗺️ Create Your Complete Travel Plan")

if st.button("✨ Generate Travel Plan"):

    if not selected_destination:

        st.warning(
            "Please enter or select a destination."
        )

    elif not interests:

        st.warning(
            "Please select at least one interest."
        )

    else:

        prompt_destination = selected_destination

        with st.spinner(
            "🤖 AI is creating your personalized travel plan..."
        ):

            travel_plan = generate_travel_plan(
                prompt_destination,
                days,
                budget,
                travelers,
                interests
            )

        if travel_plan:

            st.session_state.travel_plan = (
                travel_plan
            )

            estimated_cost = (
                extract_estimated_cost(
                    travel_plan
                )
            )

            st.session_state.estimated_cost = (
                estimated_cost
            )

            st.success(
                "🗺️ Your travel plan is ready!"
            )


# =========================================================
# 18. DISPLAY TRAVEL PLAN
# =========================================================

if st.session_state.travel_plan:

    st.subheader(
        "📖 Your AI-Generated Travel Plan"
    )

    st.markdown(
        st.session_state.travel_plan
    )


# =========================================================
# 19. BUDGET CHECK
# =========================================================

if (
    st.session_state.estimated_cost
    is not None
):

    st.divider()

    st.header("💰 Smart Budget Check")

    estimated_cost = (
        st.session_state.estimated_cost
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Your Budget",
        f"₹{budget:,}"
    )

    col2.metric(
        "Estimated Cost",
        f"₹{estimated_cost:,}"
    )

    difference = budget - estimated_cost

    col3.metric(
        "Difference",
        f"₹{difference:,}"
    )

    if estimated_cost <= budget:

        st.success(
            "✅ Your estimated trip cost is "
            "within your budget!"
        )

    else:

        st.warning(
            "⚠️ The estimated trip cost is "
            "higher than your budget."
        )


# =========================================================
# 20. AI BUDGET SAVING SUGGESTIONS
# =========================================================

if (
    st.session_state.estimated_cost
    is not None
    and selected_destination
):

    st.divider()

    st.header("💡 AI Budget Saving Suggestions")

    if st.button(
        "💰 Generate Saving Suggestions"
    ):

        with st.spinner(
            "🤖 AI is finding ways to save money..."
        ):

            suggestions = (
                generate_budget_suggestions(
                    budget,
                    st.session_state.estimated_cost,
                    selected_destination
                )
            )

        if suggestions:

            st.markdown(
                suggestions
            )


# =========================================================
# 21. AI BUDGET BREAKDOWN
# =========================================================

st.divider()

st.header("📊 AI Budget Breakdown")

st.write(
    "Get an AI-generated category-wise "
    "estimate for your trip."
)

if st.button(
    "📊 Generate Budget Breakdown"
):

    if not selected_destination:

        st.warning(
            "Please enter a destination first."
        )

    else:

        budget_prompt = f"""
Create a realistic budget breakdown for a trip.

Destination: {selected_destination}
Days: {days}
Travelers: {travelers}
Total budget: ₹{budget}

Return exactly these categories:

Transportation: ₹amount
Accommodation: ₹amount
Food: ₹amount
Activities & Sightseeing: ₹amount
Shopping: ₹amount
Miscellaneous: ₹amount

Make sure the amounts are realistic.
"""

        with st.spinner(
            "🤖 AI is preparing the budget breakdown..."
        ):

            breakdown = ask_gemini(
                budget_prompt
            )

        if breakdown:

            st.session_state.budget_breakdown = (
                breakdown
            )

if st.session_state.budget_breakdown:

    st.subheader(
        "💰 Expense Details"
    )

    breakdown_text = (
        st.session_state.budget_breakdown
    )

    categories = [
        "Transportation",
        "Accommodation",
        "Food",
        "Activities & Sightseeing",
        "Shopping",
        "Miscellaneous"
    ]

    chart_data = {}

    for category in categories:

        pattern = (
            rf"{re.escape(category)}"
            rf"\s*:\s*₹?\s*([\d,]+)"
        )

        match = re.search(
            pattern,
            breakdown_text,
            re.IGNORECASE
        )

        if match:

            amount = int(
                match.group(1).replace(",", "")
            )

            chart_data[category] = amount

            st.write(
                f"**{category}:** ₹{amount:,}"
            )

    if chart_data:

        st.subheader(
            "📈 Expense Distribution"
        )

        st.bar_chart(
            chart_data
        )


# =========================================================
# 22. PACKING CHECKLIST
# =========================================================

st.divider()

st.header("🎒 AI Packing Checklist")

st.write(
    "Get a personalized packing checklist based "
    "on your destination, trip duration, season "
    "and interests."
)

if st.button(
    "🎒 Generate Packing Checklist"
):

    if not selected_destination:

        st.warning(
            "Please enter a destination first."
        )

    else:

        with st.spinner(
            "AI is preparing your packing checklist..."
        ):

            packing_checklist = (
                generate_packing_checklist(
                    selected_destination,
                    days,
                    travel_season,
                    interests
                )
            )

        if packing_checklist:

            st.session_state.packing_checklist = (
                packing_checklist
            )

if st.session_state.packing_checklist:

    st.subheader(
        "🧳 Your Personalized Packing List"
    )

    st.markdown(
        st.session_state.packing_checklist
    )


# =========================================================
# 23. DOWNLOAD TRAVEL PLAN
# =========================================================

if st.session_state.travel_plan:

    st.divider()

    st.header("📥 Download Your Travel Plan")

    st.download_button(
        label="📥 Download Travel Plan",
        data=st.session_state.travel_plan,
        file_name="AI_Travel_Plan.txt",
        mime="text/plain"
    )


# =========================================================
# 24. AI TRAVEL ASSISTANT CHATBOT
# =========================================================

st.divider()

st.header("🤖 AI Travel Assistant")

st.write(
    "Ask me anything about your trip, destination, "
    "budget, activities, food, packing, or travel tips."
)


# Display previous messages

for message in st.session_state.chat_messages:

    if message["role"] == "user":

        st.chat_message(
            "user"
        ).write(
            message["content"]
        )

    else:

        st.chat_message(
            "assistant"
        ).write(
            message["content"]
        )


# Chat input

user_question = st.chat_input(
    "Ask your AI Travel Assistant..."
)


if user_question:

    # Display user message

    st.chat_message(
        "user"
    ).write(
        user_question
    )

    # Save user message

    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": user_question
        }
    )


    # Create conversation history

    conversation_history = ""

    for message in st.session_state.chat_messages:

        conversation_history += (
            f"{message['role'].upper()}: "
            f"{message['content']}\n"
        )


    # Current trip context

    selected_place = (
        selected_destination
        if selected_destination
        else destination
    )

    chatbot_prompt = f"""
You are an AI Travel Assistant.

The user is planning a trip.

Current trip information:

Destination: {selected_place}
Number of days: {days}
Budget: ₹{budget}
Travelers: {travelers}
Interests: {", ".join(interests)}

Previous conversation:

{conversation_history}

Current user question:

{user_question}

Use the trip information and previous conversation
to understand the user's context.

Answer clearly, practically and concisely.

Focus mainly on travel-related questions.

If the user has not selected a destination,
help them decide based on their budget and interests.
"""


    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "🤖 Thinking..."
        ):

            chatbot_response = ask_gemini(
                chatbot_prompt
            )

        if chatbot_response:

            st.markdown(
                chatbot_response
            )

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": chatbot_response
                }
            )