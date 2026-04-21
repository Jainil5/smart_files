import requests
import json

BASE_URL = "http://127.0.0.1:8000"


# ------------------ HELPERS ------------------ #

def pretty_print(title, data):
    print("\n" + "=" * 50)
    print(f"{title}")
    print("=" * 50)
    print(json.dumps(data, indent=2))
    print("=" * 50 + "\n")


# ------------------ TEST UPLOAD ------------------ #

def test_upload(path: str):
    url = f"{BASE_URL}/upload"

    payload = {
        "path": path
    }

    try:
        response = requests.post(url, json=payload)

        pretty_print("UPLOAD RESPONSE", response.json())

        return response.json()

    except Exception as e:
        print("Upload Error:", str(e))


# ------------------ TEST QUERY ------------------ #

def test_query(query: str):
    url = f"{BASE_URL}/query"

    payload = {
        "query": query
    }

    try:
        response = requests.post(url, json=payload)

        pretty_print("QUERY RESPONSE", response.json())

        return response.json()

    except Exception as e:
        print("Query Error:", str(e))


# ------------------ MAIN TEST RUN ------------------ #

if __name__ == "__main__":

    print("\n🚀 STARTING API TESTS\n")

    # -------- TEST 1: UPLOAD -------- #
    test_upload("/Users/jainil/Documents/development/smart_files/app/test/password.txt")


    # -------- TEST 3: QUERY -------- #
    test_query("Find me a file related to leave policy")

    test_query("Explain maternity leave policy")

    test_query("Find total revenue for female customers")

    test_query("What's the weather in Mumbai?")




# ==================================================
# UPLOAD RESPONSE
# ==================================================
# {
#   "status": "success",
#   "type": "upload",
#   "data": {
#     "file_id": "25bdc97e-fc4b-4628-8a74-2acb98004d24",
#     "file_name": "password.txt",
#     "file_type": "txt",
#     "platform": "local",
#     "local_path": "data/documents/password.txt",
#     "hosted_link": "mongo://69e65c5927cde3d31e79b3ef"
#   },
#   "message": ""
# }
# ==================================================


# ==================================================
# QUERY RESPONSE
# ==================================================
# {
#   "status": "success",
#   "type": "direct",
#   "data": {
#     "response": "{}"
#   },
#   "message": ""
# }
# ==================================================


# ==================================================
# QUERY RESPONSE
# ==================================================
# {
#   "status": "success",
#   "type": "direct",
#   "data": {
#     "response": "Maternity leave typically allows a new mother to take a set period of unpaid or partially paid time off around the birth or adoption of a child. The exact duration, pay rate, eligibility requirements, and benefits vary by country, employer policy, and sometimes by gender or parental role."
#   },
#   "message": ""
# }
# ==================================================


# ==================================================
# QUERY RESPONSE
# ==================================================
# {
#   "status": "success",
#   "type": "direct",
#   "data": {
#     "response": "SELECT SUM(\"Revenue\") AS total_female_revenue FROM clothing_sales_combined WHERE gender = 'Female';"
#   },
#   "message": ""
# }
# ==================================================


# ==================================================
# QUERY RESPONSE
# ==================================================
# {
#   "status": "success",
#   "type": "direct",
#   "data": {
#     "response": "{\"current_condition\": [{\"FeelsLikeC\": \"32\", \"FeelsLikeF\": \"90\", \"cloudcover\": \"25\", \"humidity\": \"79\", \"localObsDateTime\": \"2026-04-20 10:28 PM\", \"observation_time\": \"04:58 PM\", \"precipInches\": \"0.0\", \"precipMM\": \"0.0\", \"pressure\": \"1008\", \"pressureInches\": \"30\", \"temp_C\": \"29\", \"temp_F\": \"84\", \"uvIndex\": \"0\", \"visibility\": \"4\", \"visibilityMiles\": \"2\", \"weatherCode\": \"143\", \"weatherDesc\": [{\"value\": \"Mist\"}], \"weatherIconUrl\": [{\"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0006_mist.png\"}]}, {\"winddir16Point\": \"NW\", \"winddirDegree\": \"315\", \"windspeedKmph\": \"13\", \"windspeedMiles\": \"8\"}], \"nearest_area\": [{\"areaName\": [{\"value\": \"Ballard Estate\"}], \"country\": [{\"value\": \"India\"}], \"latitude\": \"18.933\", \"longitude\": \"72.833\", \"population\": \"0\", \"region\": [{\"value\": \"Maharashtra\"}], \"weatherUrl\": [{\"value\": \"https://www.worldweatheronline.com/v2/weather.aspx?q=18.933,72.833\"}]}], \"request\": [{\"query\": \"Lat 18.93 and Lon 72.83\", \"type\": \"LatLon\"}], \"weather\": [{\"astronomy\": [{\"moon_illumination\": \"9\", \"moon_phase\": \"Waxing Crescent\", \"moonrise\": \"08:22 AM\", \"moonset\": \"10:17 PM\", \"sunrise\": \"06:18 AM\", \"sunset\": \"06:57 PM\"}], \"avgtempC\": \"29\", \"avgtempF\": \"85\", \"date\": \"2026-04-20\", \"hourly\": [{\"DewPointC\": \"21\", \"DewPointF\": \"70\", \"FeelsLikeC\": \"31\", \"FeelsLikeF\": \"88\", \"HeatIndexC\": \"31\", \"HeatIndexF\": \"88\", \"WindChillC\": \"29\", \"WindChillF\": \"83\", \"WindGustKmph\": \"15\", \"WindGustMiles\": \"9\", \"chanceoffog\": \"0\", \"chanceoffrost\": \"0\", \"chanceofhightemp\": \"48\", \"chanceofovercast\": \"0\", \"chanceofrain\": \"0\", \"chanceofremdry\": \"92\", \"chanceofsnow\": \"0\", \"chanceofsunshine\": \"90\", \"chanceofthunder\": \"0\", \"chanceofwindy\": \"0\", \"cloudcover\": \"6\", \"diffRad\": \"0.0\", \"humidity\": \"64\", \"precipInches\": \"0.0\", \"precipMM\": \"0.0\", \"pressure\": \"1010\", \"pressureInches\": \"30\", \"shortRad\": \"0.0\", \"tempC\": \"29\", \"tempF\": \"84\", \"time\": \"0\", \"uvIndex\": \"0\", \"visibility\": \"10\", \"visibilityMiles\": \"6\", \"weatherCode\": \"113\", \"weatherDesc\": [{\"value\": \"Clear \"}], \"weatherIconUrl\": [{\"value\": \"https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0008_clear_sky_night.png\"}], \"winddir16Point\": \"SW\", \"winddirDegree\": \"217\", \"windspeedKmph\": \"10\", \"windspeedMiles\": \"6\"}, ...], \"maxtempC\": \"31\", \"maxtempF\": \"87\", \"mintempC\": \"28\", \"mintempF\": \"82\", \"sunHour\": \"12.0\", \"totalSnow_cm\": \"0.0\", \"uvIndex\": \"7\"}, {\"astronomy\": [{\"moon_illumination\": \"17\", \"moon_phase\": \"Waxing Crescent\", \"moonrise\": \"09:24 AM\", \"moonset\": \"11:24 PM\", \"sunrise\": \"06:17 AM\", \"sunset\": \"06:58 PM\"}], \"avgtempC\": \"29\", \"avgtempF\": \"85\", \"date\": \"2026-04-21\", ...}, {\"astronomy\": [{\"moon_illumination\": \"27\", \"moon_phase\": \"Waxing Crescent\", \"moonrise\": \"10:29 AM\", \"moonset\": \"No moonset\", \"sunrise\": \"06:17 AM\", \"sunset\": \"06:58 PM\"}], \"avgtempC\": \"30\", \"avgtempF\": \"86\", \"date\": \"2026-04-22\", ...}]\"}"
#   },
#   "message": ""
# }
# ==================================================    