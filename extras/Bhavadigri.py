from flask import Flask, render_template_string, request
import swisseph as swe
from datetime import datetime
import pytz

app = Flask(__name__)

# രാശി പേരുകൾ
RASHI_NAMES = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "സിംഹം", "കന്നി",
               "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"]

# ഗ്രഹ പേരുകൾ
PLANET_NAMES = {
    swe.SUN: "സൂര്യൻ",
    swe.MOON: "ചന്ദ്രൻ",
    swe.MARS: "ചൊവ്വ",
    swe.MERCURY: "ബുധൻ",
    swe.JUPITER: "ഗുരു",
    swe.VENUS: "ശുക്രൻ",
    swe.SATURN: "ശനി",
    swe.MEAN_NODE: "രാഹു"
}

# Swiss Ephemeris ഗ്രഹ കോഡുകൾ - grahanila.py രീതി
PLANET_CODES = {
    "സൂര്യൻ": swe.SUN,
    "ചന്ദ്രൻ": swe.MOON,
    "ചൊവ്വ": swe.MARS,
    "ബുധൻ": swe.MERCURY,
    "ഗുരു": swe.JUPITER,
    "ശുക്രൻ": swe.VENUS,
    "ശനി": swe.SATURN,
    "രാഹു": swe.MEAN_NODE
}

def get_coordinates_from_app_data(place_data):
    """app.py-ൽ നിന്ന് വന്ന ഡാറ്റയിൽ നിന്ന് അക്ഷാംശം, രേഖാംശം, സമയമേഖല എടുക്കുക"""
    try:
        # place_data ഒരു dictionary ആണോ string ആണോ എന്ന് പരിശോധിക്കുക
        if isinstance(place_data, dict):
            # app.py-ൽ നിന്ന് വന്ന ഫോർമാറ്റ്
            lat = place_data.get('lat')
            lng = place_data.get('lng')
            timezone = place_data.get('timezone', 'Asia/Kolkata')
            place_name = place_data.get('name', '')
        elif isinstance(place_data, str):
            # പഴയ ഫോർമാറ്റ് (string)
            place_name = place_data
            # ഡിഫോൾട്ട് values
            lat = 11.8745  # കണ്ണൂർ
            lng = 75.3704
            timezone = 'Asia/Kolkata'
        else:
            # മറ്റ് കേസുകൾ
            place_name = str(place_data)
            lat = 11.8745
            lng = 75.3704
            timezone = 'Asia/Kolkata'
       
        # പ്രധാനമായും lat, lng ഉണ്ടോ എന്ന് പരിശോധിക്കുക
        if lat is None or lng is None:
            print(f"⚠️ Warning: Missing coordinates in place data. Using defaults.")
            lat = 11.8745
            lng = 75.3704
            timezone = 'Asia/Kolkata'
       
        print(f"📍 Place data received in bhavadigri:")
        print(f"   - Name: {place_name}")
        print(f"   - Lat: {lat}")
        print(f"   - Lng: {lng}")
        print(f"   - Timezone: {timezone}")
       
        return lat, lng, timezone
       
    except Exception as e:
        print(f"⚠️ Error getting coordinates in bhavadigri: {e}. Using defaults.")
        # ഡിഫോൾട്ട് values
        return 11.8745, 75.3704, 'Asia/Kolkata'

# ✅ പ്രധാന തിരുത്തൽ: grahanila.py രീതിയിലുള്ള correct_to_utc() ഫംഗ്ഷൻ
def correct_to_utc(year, month, day, hour, minute, second, timezone_str='Asia/Kolkata'):
    """സമയമേഖല അനുസരിച്ച് UTC യിലേക്ക് മാറ്റുക"""
    try:
        # സമയമേഖല object സൃഷ്ടിക്കുക
        tz = pytz.timezone(timezone_str)
       
        # Local datetime സൃഷ്ടിക്കുക
        local_dt = datetime(year, month, day, hour, minute, second)
       
        # Timezone ചേർക്കുക
        localized_dt = tz.localize(local_dt)
       
        # UTC-യിലേക്ക് മാറ്റുക
        utc_dt = localized_dt.astimezone(pytz.UTC)
       
        print(f"⏰ Time conversion in bhavadigri:")
        print(f"   Input: {year}/{month}/{day} {hour}:{minute}:{second} ({timezone_str})")
        print(f"   UTC: {utc_dt.year}/{utc_dt.month}/{utc_dt.day} {utc_dt.hour}:{utc_dt.minute}:{utc_dt.second}")
       
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second
       
    except Exception as e:
        print(f"❌ UTC conversion error in bhavadigri: {e}")
        # Fallback: IST മാത്രം (പഴയ രീതി)
        total_hours = hour - 5
        total_minutes = minute - 30
       
        if total_minutes < 0:
            total_hours -= 1
            total_minutes += 60
       
        if total_hours < 0:
            day -= 1
            total_hours += 24
            if day < 1:
                month -= 1
                if month < 1:
                    year -= 1
                    month = 12
                day = 30
       
        return year, month, day, total_hours, total_minutes, second

def calculate_lagna(jd_ut, lat, lon, ayanamsa_mode):
    """കൃത്യമായ ലഗ്നം കണക്കാക്കുക"""
    # Set ayanamsa mode first
    swe.set_sid_mode(ayanamsa_mode)
   
    # Calculate houses with sidereal mode
    houses = swe.houses(jd_ut, lat, lon, b'P')
    lagna_longitude = houses[0][0]
   
    # Get ayanamsa value
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
   
    # Calculate nirayana lagna by subtracting ayanamsa
    nirayana_lagna = (lagna_longitude - ayanamsa) % 360
   
    return nirayana_lagna

def calculate_planet_degree(jd_ut, planet_code, ayanamsa_mode):
    """ഗ്രഹത്തിന്റെ ഡിഗ്രി കണക്കാക്കുക"""
    # Set ayanamsa mode first
    swe.set_sid_mode(ayanamsa_mode)
   
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    result = swe.calc_ut(jd_ut, planet_code, flags)
    longitude = result[0][0]
   
    # Get ayanamsa value
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
   
    # Calculate nirayana longitude by subtracting ayanamsa
    nirayana_longitude = (longitude - ayanamsa) % 360
   
    return nirayana_longitude

def calculate_planet_positions(jd_ut, lat, lon, ayanamsa_mode):
    """Swiss Ephemeris ഉപയോഗിച്ച് ഗ്രഹ സ്ഥിതികൾ കണക്കാക്കുക"""
    planets = []
   
    # ലഗ്നം കണക്കാക്കുക
    lagna_degree = calculate_lagna(jd_ut, lat, lon, ayanamsa_mode)
    lagna_index = int(lagna_degree / 30)
    planets.append({"name": "ലഗ്നം", "rasi_index": lagna_index, "degree": lagna_degree})
   
    # ✅ പ്രധാന തിരുത്തൽ: PLANET_CODES ഉപയോഗിക്കുക (grahanila.py രീതി)
    for planet_name, planet_code in PLANET_CODES.items():
        degree = calculate_planet_degree(jd_ut, planet_code, ayanamsa_mode)
        rasi_index = int(degree / 30)
        planets.append({"name": planet_name, "rasi_index": rasi_index, "degree": degree})
   
    # കേതു കണക്കാക്കുക
    rahu_degree = planets[-1]["degree"]  # രാഹുവിന്റെ ഡിഗ്രി
    ketu_degree = (rahu_degree + 180) % 360
    ketu_index = int(ketu_degree / 30)
    planets.append({"name": "കേതു", "rasi_index": ketu_index, "degree": ketu_degree})
   
    return planets

def calculate_bhava_ranges(lagna_degree):
    """എല്ലാ ഭാവങ്ങൾക്കും ആരംഭ-അവസാന ഡിഗ്രികൾ കണക്കാക്കുക"""
    bhava_ranges = {}
   
    # ഭാവം തുടങ്ങുന്നത് ലഗ്ന രാശിയിൽ നിന്ന് 15 ഡിഗ്രി മുമ്പ്
    bhava_start_degree = (lagna_degree - 15) % 360
    bhava_start_rashi = int(bhava_start_degree / 30)
   
    # ലഗ്ന രാശി ഒന്നാം ഭാവമാക്കി മാറ്റുക
    # ഭാവം 1 = ലഗ്ന രാശി, ഭാവം 2 = അടുത്ത രാശി, ...
    lagna_rashi = int(lagna_degree / 30)
   
    # എല്ലാ രാശികൾക്കും ഭാവ ആരംഭ-അവസാനം
    for i in range(12):
        # ഭാവം i+1 ൻ്റെ രാശി = (ലഗ്ന രാശി + i) % 12
        current_rashi = (lagna_rashi + i) % 12
        start_degree = (bhava_start_degree + i * 30) % 360
        end_degree = (start_degree + 30) % 360
       
        bhava_ranges[current_rashi] = {
            'start_degree': start_degree,
            'end_degree': end_degree,
            'bhava_number': i + 1,
            'bhava_rashi': current_rashi  # ഭാവത്തിന്റെ രാശി
        }
   
    return bhava_ranges

def get_planet_position_in_bhava(planet_degree, bhava_start, bhava_end):
    """ഗ്രഹം ഭാവത്തിൽ എവിടെയാണെന്ന് കണ്ടെത്തുക (ആരംഭം/മധ്യം/അവസാനം)"""
    bhava_length = 30.0
    position_in_bhava = (planet_degree - bhava_start) % 360
   
    if position_in_bhava < 10:
        return "ആരംഭം"
    elif position_in_bhava < 20:
        return "മധ്യം"
    else:
        return "അവസാനം"

def get_bhava_for_planet(planet_degree, bhava_ranges):
    """ഗ്രഹത്തിന്റെ ഭാവ രാശി കണ്ടെത്തുക"""
    for rashi_index, range_info in bhava_ranges.items():
        start_degree = range_info['start_degree']
        end_degree = range_info['end_degree']
       
        # ഡിഗ്രി രീതിയിൽ താരതമ്യം ചെയ്യുക
        if start_degree <= end_degree:
            # സാധാരണ കേസ്
            if start_degree <= planet_degree < end_degree:
                return rashi_index, range_info
        else:
            # 360° കടന്നുപോകുന്ന കേസ്
            if planet_degree >= start_degree or planet_degree < end_degree:
                return rashi_index, range_info
   
    # ഒന്നും കിട്ടിയില്ലെങ്കിൽ യഥാർത്ഥ രാശി തിരികെ നൽകുക
    original_rashi = int(planet_degree / 30)
    return original_rashi, bhava_ranges.get(original_rashi, {})

def format_degree_detailed(degree):
    """ഡിഗ്രിയെ ഡിഗ്രി-മിനിറ്റ്-സെക്കൻഡ് രൂപത്തിൽ ഫോർമാറ്റ് ചെയ്യുക"""
    degree_in_rashi = degree % 30
    degrees = int(degree_in_rashi)
    minutes = int((degree_in_rashi - degrees) * 60)
    seconds = int((((degree_in_rashi - degrees) * 60) - minutes) * 60)
   
    return f"{degrees}-{minutes:02d}-{seconds:02d}"

def get_rashi_for_degree(degree):
    """ഡിഗ്രിക്ക് അനുസരിച്ച് രാശി കണ്ടെത്തുക"""
    rashi_index = int(degree / 30) % 12
    return RASHI_NAMES[rashi_index]

def bhavasphutam_calculation(data):
    """ഭാവ സ്ഫുടങ്ങൾ കണക്കാക്കുന്ന ഫങ്ഷൻ"""
    try:
        # Extract data
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour_24h = data.get('hour_24h')
        minute = data.get('minute')
        place_data = data.get('place', {})
       
        print(f"🔍 Bhavadigri calculation started:")
        print(f"   - Date: {day}/{month}/{year}")
        print(f"   - Time: {hour_24h}:{minute}")
        print(f"   - Place data type: {type(place_data)}")
        print(f"   - Place data: {place_data}")
       
        # Format date and time for display
        dob = f"{year}-{month:02d}-{day:02d}"
        tob = f"{hour_24h:02d}:{minute:02d}:00"
       
        # ✅ പ്രധാന തിരുത്തൽ: app.py-ൽ നിന്ന് വന്ന ഡാറ്റയിൽ നിന്ന് കോർഡിനേറ്റുകൾ എടുക്കുക
        lat, lon, timezone_str = get_coordinates_from_app_data(place_data)
       
        print(f"📍 Coordinates obtained in bhavadigri:")
        print(f"   - Lat: {lat}")
        print(f"   - Lon: {lon}")
        print(f"   - Timezone: {timezone_str}")
       
        ayanamsa_mode = 1  # Default to Lahiri
       
        # ✅ പ്രധാന തിരുത്തൽ: grahanila.py രീതിയിൽ സമയമേഖല അനുസരിച്ച് UTC-യിലേക്ക് മാറ്റുക
        utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(
            year, month, day, hour_24h, minute, 0, timezone_str
        )
       
        jd_ut = swe.julday(utc_year, utc_month, utc_day,
                          utc_hour + utc_minute/60.0 + utc_second/3600.0)

        print(f"   - Julian Day: {jd_ut}")
        print(f"   - UTC Time: {utc_hour}:{utc_minute}:{utc_second}")

        # Calculate planet positions
        planets = calculate_planet_positions(jd_ut, lat, lon, ayanamsa_mode)
       
        print(f"   - Planets calculated: {len(planets)}")
        print(f"   - Lagna: {RASHI_NAMES[planets[0]['rasi_index']]} ({planets[0]['degree']:.2f}°)")
       
        # Get Lagna degree
        lagna_degree = planets[0]['degree']
        lagna_rashi_index = planets[0]['rasi_index']
       
        # Calculate Bhava ranges
        bhava_ranges = calculate_bhava_ranges(lagna_degree)
       
        # Get place name for display
        if isinstance(place_data, dict):
            place_name = place_data.get('name', '')
        else:
            place_name = str(place_data)
       
        # Create result HTML
        result_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ഭാവ സ്ഫുടങ്ങൾ - ഫലം</title>
            <style>
                body {{
                    font-family: 'Noto Sans Malayalam', Arial, sans-serif;
                    background: #f8f5e6;
                    padding: 15px;
                    margin: 0;
                }}
                .result-container {{
                    background: white;
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    margin-bottom: 15px;
                }}
                .section-title {{
                    color: #8B0000;
                    border-bottom: 2px solid #8B4513;
                    padding-bottom: 8px;
                    margin: 15px 0 10px 0;
                    font-size: 1.2em;
                }}
                .bhava-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 12px 0;
                    font-size: 12px;
                }}
                .bhava-table th, .bhava-table td {{
                    border: 1px solid #8B4513;
                    padding: 6px 3px;
                    text-align: center;
                    vertical-align: middle;
                }}
                .bhava-table th {{
                    background: #8B0000;
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                }}
                .bhava-table tr:nth-child(even) {{
                    background: #f8f5e6;
                }}
                .planet-position {{
                    font-weight: bold;
                    color: #8B0000;
                }}
                .basic-info {{
                    background: #e8f5e9;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid #4caf50;
                    font-size: 14px;
                }}
                .back-button {{
                    display: block;
                    text-align: center;
                    margin: 15px auto;
                    padding: 12px 20px;
                    background: #8B4513;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    width: 150px;
                    font-weight: bold;
                }}
                .degree-display {{
                    font-family: monospace;
                    font-size: 11px;
                    font-weight: bold;
                }}
                .rashi-name {{
                    font-weight: bold;
                    color: #8B0000;
                    font-size: 11px;
                }}
                .bhava-header {{
                    background: #8B4513;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                }}
                .planet-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 12px 0;
                    font-size: 13px;
                }}
                .planet-table th, .planet-table td {{
                    border: 1px solid #8B4513;
                    padding: 8px 6px;
                    text-align: center;
                }}
                .planet-table th {{
                    background: #8B0000;
                    color: white;
                    font-weight: bold;
                }}
                @media (max-width: 480px) {{
                    body {{
                        padding: 10px;
                    }}
                    .bhava-table {{
                        font-size: 10px;
                    }}
                    .bhava-table th, .bhava-table td {{
                        padding: 4px 2px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="result-container">
                <h2 style="color: #8B0000; text-align: center;">ഭാവ സ്ഫുടങ്ങൾ</h2>
               
                <div class="basic-info">
                    <p><strong>ജനന തീയതി:</strong> {dob}</p>
                    <p><strong>ജനന സമയം:</strong> {tob}</p>
                    <p><strong>സ്ഥലം:</strong> {place_name}</p>
                </div>
        """
       
        # Add Bhava Sections Table - Corrected Format
        result_html += """
                <h3 class="section-title">ഭാവ വിഭാഗങ്ങൾ</h3>
                <table class="bhava-table">
                    <tr class="bhava-header">
                        <th>ഭാവം</th>
                        <th>ആരംഭം</th>
                        <th>മധ്യം</th>
                        <th>അവസാനം</th>
                    </tr>
        """
       
        # Sort bhava ranges by bhava number
        sorted_bhavas = sorted(bhava_ranges.items(), key=lambda x: x[1]['bhava_number'])
       
        for rashi_index, range_info in sorted_bhavas:
            start_degree = range_info['start_degree']
            bhava_number = range_info['bhava_number']
            bhava_rashi = range_info['bhava_rashi']
           
            # Calculate section start degrees
            section1_start = start_degree
            section2_start = (start_degree + 10) % 360
            section3_start = (start_degree + 20) % 360
           
            # Calculate section end degrees
            section1_end = section2_start
            section2_end = section3_start
            section3_end = (start_degree + 30) % 360
           
            # Get rashi for each section
            section1_start_rashi = get_rashi_for_degree(section1_start)
            section1_end_rashi = get_rashi_for_degree(section1_end)
            section2_start_rashi = get_rashi_for_degree(section2_start)
            section2_end_rashi = get_rashi_for_degree(section2_end)
            section3_start_rashi = get_rashi_for_degree(section3_start)
            section3_end_rashi = get_rashi_for_degree(section3_end)
           
            # Format degrees within rashi
            section1_start_in_rashi = section1_start % 30
            section1_end_in_rashi = section1_end % 30
            section2_start_in_rashi = section2_start % 30
            section2_end_in_rashi = section2_end % 30
            section3_start_in_rashi = section3_start % 30
            section3_end_in_rashi = section3_end % 30
           
            result_html += f"""
                    <tr>
                        <td class="rashi-name"><strong>{bhava_number}({RASHI_NAMES[bhava_rashi]})</strong></td>
                        <td>
                            <div class="rashi-name">{section1_start_rashi}</div>
                            <div class="degree-display">{section1_start_in_rashi:.1f}°</div>
                            <div class="rashi-name">{section1_end_rashi}</div>
                            <div class="degree-display">{section1_end_in_rashi:.1f}°</div>
                        </td>
                        <td>
                            <div class="rashi-name">{section2_start_rashi}</div>
                            <div class="degree-display">{section2_start_in_rashi:.1f}°</div>
                            <div class="rashi-name">{section2_end_rashi}</div>
                            <div class="degree-display">{section2_end_in_rashi:.1f}°</div>
                        </td>
                        <td>
                            <div class="rashi-name">{section3_start_rashi}</div>
                            <div class="degree-display">{section3_start_in_rashi:.1f}°</div>
                            <div class="rashi-name">{section3_end_rashi}</div>
                            <div class="degree-display">{section3_end_in_rashi:.1f}°</div>
                        </td>
                    </tr>
            """
       
        result_html += """
                </table>
        """
       
        # Add Planet Positions Table
        result_html += """
                <h3 class="section-title">ഗ്രഹങ്ങളുടെ ഭാവ സ്ഥാനങ്ങൾ</h3>
                <table class="planet-table">
                    <tr>
                        <th>ഗ്രഹം</th>
                        <th>രാശി</th>
                        <th>ഡിഗ്രി</th>
                        <th>ഭാവത്തിൽ</th>
                    </tr>
        """
       
        for planet in planets:
            planet_degree = planet['degree']
            original_rashi = planet['rasi_index']
           
            # Find bhava rashi and position
            bhava_rashi, bhava_range = get_bhava_for_planet(planet_degree, bhava_ranges)
            bhava_position = get_planet_position_in_bhava(planet_degree,
                                                         bhava_range['start_degree'],
                                                         bhava_range['end_degree'])
           
            formatted_degree = format_degree_detailed(planet_degree)
           
            result_html += f"""
                    <tr>
                        <td class="planet-position">{planet['name']}</td>
                        <td class="rashi-name">{RASHI_NAMES[original_rashi]}</td>
                        <td class="degree-display">{formatted_degree}</td>
                        <td><strong>{bhava_position}</strong></td>
                    </tr>
            """
       
        result_html += """
                </table>
            </div>
           
            <div style="text-align: center;">
                <a href="javascript:history.back()" class="back-button">മടങ്ങുക</a>
            </div>
        </body>
        </html>
        """
       
        print(f"✅ Bhavadigri calculation completed successfully")
        return result_html
       
    except Exception as e:
        error_message = f"ഭാവ സ്ഫുടങ്ങൾ കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}"
        print(f"❌ Error in bhavasphutam_calculation: {error_message}")
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>പിശക്</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f8f5e6;
                    padding: 20px;
                }}
                .error-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                h1 {{ color: #8B0000; }}
                .back-button {{
                    display: inline-block;
                    margin-top: 15px;
                    padding: 12px 20px;
                    background: #8B4513;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>പിശക്</h1>
                <p>{error_message}</p>
                <a href="javascript:history.back()" class="back-button">മടങ്ങുക</a>
            </div>
        </body>
        </html>
        """
        return error_html

# Initialize Swiss Ephemeris
swe.set_ephe_path('')

if __name__ == '__main__':
    print("🚀 Bhavadigri Server starting...")
    print("📊 Testing bhavadigri calculation...")
   
    # Test data
    test_data = {
        'year': 1990,
        'month': 5,
        'day': 15,
        'hour_24h': 10,
        'minute': 30,
        'place': {
            'name': 'തിരുവനന്തപുരം',
            'lat': 8.5241,
            'lng': 76.9366,
            'timezone': 'Asia/Kolkata'
        }
    }
   
    try:
        result = bhavasphutam_calculation(test_data)
        print("✅ Test completed successfully")
    except Exception as e:
        print(f"❌ Test failed: {e}")
   
    print("🌐 Server ready")
