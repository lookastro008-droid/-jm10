from flask import Flask, render_template_string, request
import swisseph as swe
from datetime import datetime, timedelta
import pytz
from astral import LocationInfo
from astral.sun import sun
import os

# രണ്ട് മോഡിലും പ്രവർത്തിക്കാൻ
STANDALONE_MODE = False  # True ആക്കിയാൽ standalone ആയി run ചെയ്യാം

if STANDALONE_MODE:
    app = Flask(__name__)
else:
    app = None

# ആഴ്ചയുടെ അധിപൻ ഗ്രഹങ്ങൾ
WEEKDAY_LORDS = {
    0: ("തിങ്കൾ", "ചന്ദ്രൻ"),
    1: ("ചൊവ്വ", "ചൊവ്വ"),
    2: ("ബുധൻ", "ബുധൻ"),
    3: ("വ്യാഴം", "ഗുരു"),
    4: ("വെള്ളി", "ശുക്രൻ"),
    5: ("ശനി", "ശനി"),
    6: ("ഞായർ", "സൂര്യൻ")
}

# ഹോരാ ക്രമം (ആഴ്ചയുടെ അധിപൻ മുതൽ ആരംഭിച്ച്)
HORA_SEQUENCE = ["സൂര്യൻ", "ശുക്രൻ", "ബുധൻ", "ചന്ദ്രൻ", "ശനി", "ഗുരു", "ചൊവ്വ"]

def get_coordinates(place_data):
    """സ്ഥലത്തിന്റെ അക്ഷാംശം, രേഖാംശം നൽകുന്നു"""
    # place_data ഒരു dictionary ആണ് app.py-ൽ നിന്ന് വരുന്നത്
    try:
        if isinstance(place_data, dict):
            if 'lat' in place_data and 'lng' in place_data:
                lat = float(place_data['lat'])
                lng = float(place_data['lng'])
                return lat, lng
    except Exception as e:
        print(f"Coordinates error: {e}")
    
    # Fallback coordinates
    return 11.8745, 75.3704  # കണ്ണൂർ

def calculate_sunrise_sunset(dob, place_data):
    """ഉദയം, അസ്തമയം കണക്കാക്കുക"""
    try:
        lat, lon = get_coordinates(place_data)
        
        # Place name നേടുക
        place_name = place_data.get('name', 'കണ്ണൂർ') if isinstance(place_data, dict) else 'കണ്ണൂർ'
        
        # Timezone നേടുക - പ്രോപ്പർ ഫോർമാറ്റിൽ
        timezone_str = place_data.get('timezone', 'Asia/Kolkata') if isinstance(place_data, dict) else 'Asia/Kolkata'
        
        # Timezone string ശരിയാക്കുക
        timezone_str = str(timezone_str).strip()
        
        # Common timezone corrections
        timezone_corrections = {
            'America/New_york': 'America/New_York',
            'America/new_york': 'America/New_York',
            'America/NewYork': 'America/New_York',
            'America/newyork': 'America/New_York',
            'Asia/kolkata': 'Asia/Kolkata',
            'Asia/Calcutta': 'Asia/Kolkata',
            'Europe/london': 'Europe/London',
            'Asia/dubai': 'Asia/Dubai',
            'Asia/singapore': 'Asia/Singapore',
            'Asia/tokyo': 'Asia/Tokyo',
            'Australia/sydney': 'Australia/Sydney'
        }
        
        if timezone_str in timezone_corrections:
            timezone_str = timezone_corrections[timezone_str]
        
        # പ്രോപ്പർ timezone object സൃഷ്ടിക്കുക
        try:
            tz = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"Unknown timezone: {timezone_str}, falling back to Asia/Kolkata")
            tz = pytz.timezone('Asia/Kolkata')
            timezone_str = 'Asia/Kolkata'
        
        # Astral LocationInfo ഇനത്തിന് ശരിയായ timezone string വേണം
        loc = LocationInfo(place_name, "Location", timezone_str, lat, lon)
        
        year, month, day = map(int, dob.split("-"))
        date_obj = datetime(year, month, day)
        
        # Astral-ന് tzinfo object വേണം
        s = sun(loc.observer, date=date_obj, tzinfo=tz)
        
        # ഉദയം കണക്കാക്കുക (+3 മിനിറ്റ്)
        sunrise = s['sunrise'] + timedelta(minutes=3)
        
        # അസ്തമയം കണക്കാക്കുക (-3 മിനിറ്റ്)
        sunset = s['sunset'] - timedelta(minutes=3)
        
        return sunrise, sunset
        
    except Exception as e:
        print(f"Sunrise calculation error: {e}")
        # Fallback: സ്ഥിരമായ സമയം
        fallback_date = datetime.strptime(dob, "%Y-%m-%d")
        fallback_sunrise = datetime(fallback_date.year, fallback_date.month, fallback_date.day, 6, 0, 0)
        fallback_sunset = datetime(fallback_date.year, fallback_date.month, fallback_date.day, 18, 0, 0)
        
        # Timezone ഉപയോഗിച്ച് localize ചെയ്യുക
        try:
            tz = pytz.timezone('Asia/Kolkata')
            fallback_sunrise = tz.localize(fallback_sunrise)
            fallback_sunset = tz.localize(fallback_sunset)
        except:
            pass
            
        return fallback_sunrise + timedelta(minutes=3), fallback_sunset - timedelta(minutes=3)

def get_hora_sequence(starting_planet):
    """ആരംഭ ഗ്രഹത്തിൽ നിന്ന് ഹോരാ ക്രമം നിർണ്ണയിക്കുക"""
    try:
        start_index = HORA_SEQUENCE.index(starting_planet)
    except ValueError:
        start_index = 0
    
    hora_sequence = []
    for i in range(24):
        planet_index = (start_index + i) % 7
        hora_sequence.append(HORA_SEQUENCE[planet_index])
    
    return hora_sequence

def calculate_hora_chart(dob, place_data):
    """കലഹോര ചാർട്ട് കണക്കാക്കുക"""
    try:
        # ഉദയം, അസ്തമയം കണക്കാക്കുക
        sunrise, sunset = calculate_sunrise_sunset(dob, place_data)
        
        # ആഴ്ചയുടെ ദിവസം കണ്ടെത്തുക
        weekday = sunrise.weekday()
        weekday_malayalam, lord_planet = WEEKDAY_LORDS[weekday]
        
        # ഹോരാ ക്രമം നിർണ്ണയിക്കുക
        hora_sequence = get_hora_sequence(lord_planet)
        
        # ഹോരാ സമയങ്ങൾ കണക്കാക്കുക
        hora_chart = []
        current_time = sunrise
        
        for i in range(24):
            hora_start = current_time
            hora_end = hora_start + timedelta(hours=1)
            
            # Format time - മുൻപിലെ 0 നീക്കം ചെയ്യാൻ
            start_str = hora_start.strftime('%I:%M %p').lstrip('0')
            if start_str.startswith(':'):
                start_str = '12' + start_str
            
            end_str = hora_end.strftime('%I:%M %p').lstrip('0')
            if end_str.startswith(':'):
                end_str = '12' + end_str
            
            hora_chart.append({
                'planet': hora_sequence[i],
                'start_time': start_str,
                'end_time': end_str,
                'simple_format': f"{start_str} to {end_str}"
            })
            
            current_time = hora_end
        
        return {
            'hora_chart': hora_chart
        }
        
    except Exception as e:
        print(f"Hora chart calculation error: {e}")
        raise Exception(f"കലഹോര കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")

def kalahora_calculation(data):
    """Main calculation function for app.py integration"""
    try:
        year = data['year']
        month = data['month']
        day = data['day']
        place_data = data['place']
        
        dob_str = f"{year:04d}-{month:02d}-{day:02d}"
        
        result = calculate_hora_chart(dob_str, place_data)
        
        # CSS for styling - വലിയ ഫോണ്ട്, റെഡ് കളർ, മൊബൈൽ ഫ്രണ്ട്ലി
        css = """
        <style>
        /* എല്ലാം റീസെറ്റ് */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-text-size-adjust: 100%;
        }
        
        .kalahora-result {
            background-color: #FFFFFF !important;
            padding: 25px 20px !important;
            margin: 0 !important;
            color: #FF0000 !important;
            font-size: 38px !important;
            font-family: 'Noto Sans Malayalam', 'Manjari', Arial, sans-serif !important;
            border-radius: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            min-height: 100vh !important;
            font-weight: bold !important;
            line-height: 1.6 !important;
        }
        
        .hora-line {
            padding: 25px 15px !important;
            border-bottom: 3px solid #FFCCCC !important;
            line-height: 1.8 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            background: #FFF5F5 !important;
            margin-bottom: 12px !important;
            border-radius: 15px !important;
            font-weight: 900 !important;
            box-shadow: 0 2px 5px rgba(255,0,0,0.1);
        }
        
        .hora-line:nth-child(even) {
            background: #FFFAFA !important;
        }
        
        .planet-name {
            font-weight: 900 !important;
            color: #CC0000 !important;
            font-size: 40px !important;
            min-width: 150px !important;
            text-align: left !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .time-range {
            font-family: 'Courier New', monospace !important;
            font-weight: 900 !important;
            font-size: 38px !important;
            color: #FF0000 !important;
            text-align: right !important;
            flex: 1 !important;
            margin-left: 25px !important;
            letter-spacing: 1px !important;
        }
        
        /* മൊബൈൽ ഓപ്റ്റിമൈസേഷൻ */
        @media (max-width: 768px) {
            .kalahora-result { 
                padding: 20px 15px !important; 
                font-size: 36px !important;
            }
            .planet-name {
                font-size: 38px !important;
                min-width: 140px !important;
            }
            .time-range {
                font-size: 36px !important;
            }
            .hora-line {
                padding: 22px 12px !important;
                font-size: 36px !important;
                margin-bottom: 10px !important;
            }
        }
        
        @media (max-width: 480px) {
            .kalahora-result { 
                font-size: 34px !important; 
                padding: 18px 12px !important;
                line-height: 1.7 !important;
            }
            .planet-name {
                font-size: 36px !important;
                min-width: 130px !important;
            }
            .time-range {
                font-size: 34px !important;
                margin-left: 20px !important;
            }
            .hora-line {
                padding: 20px 10px !important;
                font-size: 34px !important;
                flex-direction: row !important;
                display: flex !important;
                align-items: center !important;
            }
        }
        
        @media (max-width: 360px) {
            .kalahora-result { 
                font-size: 32px !important; 
                padding: 16px 10px !important;
            }
            .planet-name {
                font-size: 34px !important;
                min-width: 120px !important;
            }
            .time-range {
                font-size: 32px !important;
                margin-left: 15px !important;
            }
            .hora-line {
                padding: 18px 8px !important;
                font-size: 32px !important;
            }
        }
        
        /* Landscape mode */
        @media (max-height: 500px) and (orientation: landscape) {
            .kalahora-result {
                font-size: 32px !important;
                padding: 15px !important;
            }
            .hora-line {
                padding: 15px 8px !important;
                margin-bottom: 8px !important;
            }
        }
        
        /* Prevent zoom on mobile */
        @media (hover: none) and (pointer: coarse) {
            input, select, textarea {
                font-size: 16px !important;
            }
        }
        </style>
        """
        
        # Format result as HTML - header ഇല്ല, footer ഇല്ല, ലളിതമായ display
        result_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>കലഹോര ഫലം</title>
            {css}
        </head>
        <body>
            <div class="kalahora-result">
        """
        
        for hora in result['hora_chart']:
            result_html += f"""
                <div class="hora-line">
                    <span class="planet-name">{hora['planet']} :</span>
                    <span class="time-range">{hora['start_time']} to {hora['end_time']}</span>
                </div>
            """
        
        result_html += """
            </div>
        </body>
        </html>
        """
        
        return result_html
        
    except Exception as e:
        return f"""
        <div style='
            color: #FF0000 !important; 
            padding: 30px !important; 
            background: #FFF0F0 !important; 
            border: 4px solid #FF0000 !important; 
            border-radius: 15px !important; 
            margin: 20px !important; 
            font-size: 32px !important;
            font-weight: bold !important;
            font-family: "Noto Sans Malayalam", Arial !important;
            text-align: center !important;
        '>
            പിശക്: {str(e)}
        </div>
        """

# Standalone mode-ൽ മാത്രം ഈ ഭാഗങ്ങൾ ഉണ്ടാകും
if STANDALONE_MODE:
    HTML_FORM = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>കലഹോര</title>
        <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-text-size-adjust: 100%;
        }
        body { 
            background: #FFFFFF !important; 
            padding: 20px !important; 
            font-family: 'Noto Sans Malayalam', Arial !important; 
            font-size: 36px !important;
            color: #FF0000 !important;
            font-weight: bold !important;
            min-height: 100vh;
        }
        .container { 
            max-width: 100% !important; 
            margin: 0 auto !important; 
            width: 100% !important;
        }
        .form-box { 
            background: #FFF0F0 !important; 
            padding: 30px !important; 
            border-radius: 20px !important;
            border: 4px solid #FF0000 !important;
            box-shadow: 0 5px 20px rgba(255,0,0,0.1);
        }
        h2 { 
            color: #FF0000 !important; 
            text-align: center !important; 
            font-size: 42px !important; 
            margin-bottom: 35px !important;
            font-weight: 900 !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        label {
            display: block !important;
            margin: 25px 0 15px 0 !important;
            font-weight: 900 !important;
            color: #CC0000 !important;
            font-size: 38px !important;
        }
        input, select { 
            width: 100% !important; 
            padding: 25px !important; 
            margin: 5px 0 30px 0 !important; 
            font-size: 36px !important;
            border: 3px solid #FF0000 !important;
            border-radius: 15px !important;
            background: white !important;
            font-weight: bold !important;
            color: #000000 !important;
        }
        button { 
            background: #FF0000 !important; 
            color: white !important; 
            padding: 30px !important; 
            border: none !important; 
            width: 100% !important; 
            font-size: 40px !important;
            font-weight: 900 !important;
            border-radius: 15px !important;
            margin-top: 30px !important;
            cursor: pointer !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }
        @media (max-width: 768px) {
            body { padding: 15px !important; font-size: 32px !important; }
            .form-box { padding: 25px !important; }
            h2 { font-size: 38px !important; margin-bottom: 30px !important; }
            label, input, select, button { font-size: 32px !important; }
            button { padding: 25px !important; font-size: 36px !important; }
        }
        @media (max-width: 480px) {
            body { padding: 12px !important; font-size: 30px !important; }
            .form-box { padding: 20px !important; }
            h2 { font-size: 34px !important; margin-bottom: 25px !important; }
            label, input, select, button { font-size: 30px !important; }
            input, select { padding: 20px !important; }
            button { padding: 22px !important; font-size: 32px !important; }
        }
        @media (max-width: 360px) {
            body { padding: 10px !important; font-size: 28px !important; }
            .form-box { padding: 18px !important; }
            h2 { font-size: 32px !important; margin-bottom: 20px !important; }
            label, input, select, button { font-size: 28px !important; }
            button { padding: 20px !important; font-size: 30px !important; }
        }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="form-box">
                <h2>കലഹോര കണക്കുകൂട്ടൽ</h2>
                <form method="post">
                    <label>ജനന തീയതി:</label>
                    <input type="date" name="dob" required>
                    
                    <label>സ്ഥലം:</label>
                    <select name="place" required>
                        <option value='കണ്ണൂർ'>കണ്ണൂർ</option>
                        <option value='തിരുവനന്തപുരം'>തിരുവനന്തപുരം</option>
                        <option value='ന്യൂയോർക്ക്'>ന്യൂയോർക്ക്</option>
                    </select>
                    
                    <button type="submit">കണക്കാക്കുക</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    
    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            try:
                # സ്ഥലം അനുസരിച്ച് coordinates
                place_name = request.form['place']
                places_coords = {
                    'കണ്ണൂർ': {'name': 'കണ്ണൂർ', 'lat': 11.8745, 'lng': 75.3704, 'timezone': 'Asia/Kolkata'},
                    'തിരുവനന്തപുരം': {'name': 'തിരുവനന്തപുരം', 'lat': 8.5241, 'lng': 76.9366, 'timezone': 'Asia/Kolkata'},
                    'ന്യൂയോർക്ക്': {'name': 'ന്യൂയോർക്ക്', 'lat': 40.7128, 'lng': -74.0060, 'timezone': 'America/New_York'}
                }
                
                place_data = places_coords.get(place_name, places_coords['കണ്ണൂർ'])
                
                data = {
                    'year': int(request.form['dob'].split('-')[0]),
                    'month': int(request.form['dob'].split('-')[1]),
                    'day': int(request.form['dob'].split('-')[2]),
                    'place': place_data
                }
                return kalahora_calculation(data)
            except Exception as e:
                return f"<div style='color: #FF0000; padding: 30px; font-size: 32px; font-weight: bold;'>പിശക്: {str(e)}</div>"
        return HTML_FORM
    
    if __name__ == '__main__':
        print("കലഹോര സെർവർ തുടങ്ങുന്നു...")
        print("ബ്രൗസറിൽ തുറക്കുക: http://localhost:5001")
        app.run(debug=True, host='0.0.0.0', port=5001)
