from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz

def raahu_calculation(data):
    """
    Calculate Rahu Kalam, Gulika Kalam, Yamagandam, Abhijit Muhurtham and Hora
    """
    try:
        # Extract data like other task files
        year = data['year']
        month = data['month']
        day = data['day']
        place_name = data['place']['name']
        hour_24h = data['hour_24h']
        minute = data['minute']
       
        # Get location data
        place_data = get_place_data(place_name)
        lat = place_data['lat']
        lon = place_data['lon']
        timezone_str = place_data['timezone']
       
        # Create date object
        date_obj = datetime(year, month, day)
       
        # Calculate sunrise and sunset using astral
        loc = LocationInfo(place_name, "India", timezone_str, lat, lon)
        tz = pytz.timezone(timezone_str)
        s = sun(loc.observer, date=date_obj, tzinfo=tz)
       
        # sunrise +3 minutes, sunset -3 minutes (ജ്യോതിഷ പ്രകാരം)
        sunrise_time = s['sunrise'] + timedelta(minutes=3)
        sunset_time = s['sunset'] - timedelta(minutes=3)
        
        # Calculate next day sunrise for night calculations
        next_day = date_obj + timedelta(days=1)
        s_next = sun(loc.observer, date=next_day, tzinfo=tz)
        next_sunrise_time = s_next['sunrise'] + timedelta(minutes=3)
       
        # Check if current time is after sunset (night time)
        current_time = datetime(year, month, day, hour_24h, minute)
        is_night_time = current_time >= sunset_time.replace(tzinfo=None)
       
        # Check if it's Wednesday (ബുധനാഴ്ച)
        weekday = date_obj.weekday()  # 0=തിങ്കൾ, 1=ചൊവ്വ, 2=ബുധൻ, 3=വ്യാഴം, 4=വെള്ളി, 5=ശനി, 6=ഞായർ
        is_wednesday = (weekday == 2)
       
        # ദിവസത്തിന്റെ ആകെ സമയം (സെക്കൻഡുകളിൽ)
        day_duration = (sunset_time - sunrise_time).total_seconds()
        night_duration = (next_sunrise_time - sunset_time).total_seconds()  # അസ്തമയം മുതൽ പിറ്റേന്ന് ഉദയം വരെ
       
        # ദിവസം എടുക്കുന്ന സമയം (പകല്‍ സമയം) 8 ഭാഗങ്ങളായി വിഭജിക്കുക
        part_duration = day_duration / 8
        night_part_duration = night_duration / 8  # രാത്രിയുടെ ഭാഗ ദൈർഘ്യം
       
        # Format times in 12-hour format
        def format_time(time_obj):
            time_str = time_obj.strftime('%I:%M %p').lstrip('0')
            if time_str.startswith(':'):
                time_str = '12' + time_str
            return time_str

        # Create result string
        result_lines = []

        if is_night_time:
            # രാത്രി സമയം - ഗുളിക കാലം, ഹോര മാത്രം കാണിക്കുക
           
            # രാത്രി ഗുളിക കാലം കണക്കാക്കൽ (അസ്തമയം മുതൽ)
            gulika_parts = [6, 5, 4, 3, 2, 7, 1]
            gulika_part = gulika_parts[weekday]
            gulika_start = sunset_time + timedelta(seconds=(gulika_part-1) * night_part_duration)
            gulika_end = gulika_start + timedelta(seconds=night_part_duration)
           
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>രാത്രി ഗുളിക കാലം: {format_time(gulika_start)} to {format_time(gulika_end)}</div>")
           
            # നിലവിലെ സമയത്തിന്റെ ഹോര കണക്കാക്കൽ
            current_hora = calculate_current_hora(weekday, sunrise_time, current_time)
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>ഹോര: {current_hora}</div>")

        else:
            # പകൽ സമയം - എല്ലാം കാണിക്കുക
           
            # പകൽ ഗുളിക കാലം കണക്കാക്കൽ (ഉദയം മുതൽ)
            gulika_parts = [6, 5, 4, 3, 2, 7, 1]
            gulika_part = gulika_parts[weekday]
            gulika_start = sunrise_time + timedelta(seconds=(gulika_part-1) * part_duration)
            gulika_end = gulika_start + timedelta(seconds=part_duration)

            # Rahu Kalam (correct mapping)
            rahu_parts = [2, 7, 5, 6, 4, 3, 8]
            rahu_part = rahu_parts[weekday]
            rahu_start = sunrise_time + timedelta(seconds=(rahu_part-1) * part_duration)
            rahu_end = rahu_start + timedelta(seconds=part_duration)
           
            # Yamagandam - പഞ്ചാംഗ പ്രകാരമുള്ള നാഴിക അനുസരിച്ച് (1 നാഴിക = 24 മിനിറ്റ്)
            yamagandam_result = calculate_yamagandam_panchanga(weekday, sunrise_time, day_duration)
           
            # അഭിജിത് മുഹൂർത്തം കണക്കാക്കൽ
            midday = sunrise_time + timedelta(seconds=day_duration/2)
            abhijit_start = midday - timedelta(minutes=24)
            abhijit_end = midday + timedelta(minutes=24)
           
            # നിലവിലെ സമയത്തിന്റെ ഹോര കണക്കാക്കൽ
            current_hora = calculate_current_hora(weekday, sunrise_time, current_time)
           
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>രാഹു കാലം: {format_time(rahu_start)} to {format_time(rahu_end)}</div>")
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>പകൽ ഗുളിക കാലം: {format_time(gulika_start)} to {format_time(gulika_end)}</div>")
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>{yamagandam_result}</div>")
           
            # ബുധനാഴ്ച അഭിജിത് മുഹൂർത്തം പരിഗണിക്കാതിരിക്കൽ
            if is_wednesday:
                result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>അഭിജിത് മുഹൂർത്തം: {format_time(abhijit_start)} to {format_time(abhijit_end)} (അഭിജിത് മുഹൂർത്തം ഇന്ന് പരിഗണനീയമല്ല)</div>")
            else:
                result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>അഭിജിത് മുഹൂർത്തം: {format_time(abhijit_start)} to {format_time(abhijit_end)}</div>")
           
            result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>ഹോര: {current_hora}</div>")
       
        return "".join(result_lines)
       
    except Exception as e:
        print(f"Error in raahu calculation: {e}")
        error_lines = [
            "<div style='padding: 8px 0; border-bottom: 2px solid #333;'>രാഹു കാലം: കണക്കാക്കാനായില്ല</div>",
            "<div style='padding: 8px 0; border-bottom: 2px solid #333;'>ഗുളിക കാലം: കണക്കാക്കാനായില്ല</div>",
            "<div style='padding: 8px 0; border-bottom: 2px solid #333;'>യമകണ്ട കാലം: കണക്കാക്കാനായില്ല</div>",
            "<div style='padding: 8px 0; border-bottom: 2px solid #333;'>അഭിജിത് മുഹൂർത്തം: കണക്കാക്കാനായില്ല</div>",
            "<div style='padding: 8px 0; border-bottom: 2px solid #333;'>ഹോര: കണക്കാക്കാനായില്ല</div>"
        ]
        return "".join(error_lines)

def calculate_yamagandam_panchanga(weekday, sunrise_time, day_duration):
    """
    പഞ്ചാംഗ പ്രകാരമുള്ള നാഴിക അനുസരിച്ച് യമകണ്ട കാലം കണക്കാക്കുക
    (1 നാഴിക = 24 മിനിറ്റ്)
    """
    try:
        # ദിവസം തോറും യമകണ്ട കാലത്തിന്റെ നാഴിക മൂല്യങ്ങൾ
        yamagandam_nazhika = {
            0: 14,  # തിങ്കൾ - 14 നാഴിക
            1: 10,  # ചൊവ്വ - 10 നാഴിക
            2: 6,   # ബുധൻ - 6 നാഴിക
            3: 2,   # വ്യാഴം - 2 നാഴിക
            4: 26,  # വെള്ളി - 26 നാഴിക
            5: 22,  # ശനി - 22 നാഴിക
            6: 18   # ഞായർ - 18 നാഴിക
        }
       
        nazhika_value = yamagandam_nazhika.get(weekday, 18)
       
        # നാഴികയെ മണിക്കൂറാക്കി മാറ്റുക (1 നാഴിക = 24 മിനിറ്റ് = 0.4 മണിക്കൂർ)
        nazhika_to_hours = nazhika_value * 0.4
       
        # യമകണ്ട കാലത്തിന്റെ ആരംഭ സമയം കണക്കാക്കുക (ഉദയം + നാഴിക)
        yamagandam_start = sunrise_time + timedelta(hours=nazhika_to_hours)
       
        # യമകണ്ട കാലം പകലിന്റെ 1/8 ഭാഗം നീണ്ടുനിൽക്കും
        yamagandam_duration = day_duration / 8
        yamagandam_end = yamagandam_start + timedelta(seconds=yamagandam_duration)
       
        # Format times in 12-hour format
        def format_time(time_obj):
            time_str = time_obj.strftime('%I:%M %p').lstrip('0')
            if time_str.startswith(':'):
                time_str = '12' + time_str
            return time_str
       
        return f"യമകണ്ട കാലം: {format_time(yamagandam_start)} to {format_time(yamagandam_end)}"
       
    except Exception as e:
        print(f"Error in yamagandam calculation: {e}")
        return "യമകണ്ട കാലം: കണക്കാക്കാനായില്ല"

def get_place_data(place_name):
    """
    Get place coordinates and timezone
    """
    PLACES = {
        'കണ്ണൂർ': {
            'lat': 11.8745,
            'lon': 75.3704,
            'timezone': 'Asia/Kolkata'
        },
        'തിരുവനന്തപുരം': {
            'lat': 8.5241,
            'lon': 76.9366,
            'timezone': 'Asia/Kolkata'
        },
        'Kochi': {
            'lat': 9.9312,
            'lon': 76.2673,
            'timezone': 'Asia/Kolkata'
        },
        'Kozhikode': {
            'lat': 11.2588,
            'lon': 75.7804,
            'timezone': 'Asia/Kolkata'
        },
        'Thrissur': {
            'lat': 10.5276,
            'lon': 76.2144,
            'timezone': 'Asia/Kolkata'
        },
        'Kottayam': {
            'lat': 9.5869,
            'lon': 76.5213,
            'timezone': 'Asia/Kolkata'
        },
        'Delhi': {
            'lat': 28.6139,
            'lon': 77.2090,
            'timezone': 'Asia/Kolkata'
        },
        'Dubai': {
            'lat': 25.2048,
            'lon': 55.2708,
            'timezone': 'Asia/Dubai'
        },
        'New York': {
            'lat': 40.7128,
            'lon': -74.0060,
            'timezone': 'America/New_York'
        },
        'Melbourne': {
            'lat': -37.8136,
            'lon': 144.9631,
            'timezone': 'Australia/Melbourne'
        }
    }
   
    # Return the place data or default to Kannur
    return PLACES.get(place_name, PLACES['കണ്ണൂർ'])

def get_hora_sequence(weekday):
    """ആഴ്ചയിലെ ദിവസം അനുസരിച്ച് ഹോര ക്രമം നൽകുന്നു"""
    # ഹോര ക്രമം: ചന്ദ്രൻ, ശനി, വ്യാഴം, ചൊവ്വ, സൂര്യൻ, ശുക്രൻ, ബുധൻ
    base_sequence = ["ചന്ദ്രൻ", "ശനി", "വ്യാഴം", "ചൊവ്വ", "സൂര്യൻ", "ശുക്രൻ", "ബുധൻ"]
   
    # ദിവസം അനുസരിച്ച് ആദ്യ ഹോര
    first_hora = {
        0: "ചന്ദ്രൻ",  # തിങ്കൾ
        1: "ചൊവ്വ",   # ചൊവ്വ
        2: "ബുധൻ",    # ബുധൻ
        3: "വ്യാഴം",   # വ്യാഴം
        4: "ശുക്രൻ",   # വെള്ളി (ശുക്രൻ)
        5: "ശനി",     # ശനി
        6: "സൂര്യൻ"    # ഞായർ
    }
   
    # ആദ്യ ഹോരയുടെ സ്ഥാനം കണ്ടെത്തുക
    start_index = base_sequence.index(first_hora[weekday])
   
    # 24 ഹോരകളുടെ ക്രമം സൃഷ്ടിക്കുക
    hora_sequence = []
    for i in range(24):
        hora_sequence.append(base_sequence[(start_index + i) % 7])
   
    return hora_sequence

def calculate_current_hora(weekday, sunrise_time, current_time):
    """നിലവിലെ സമയത്തിന്റെ ഹോര കണക്കാക്കുന്ന ഫങ്ഷൻ"""
    try:
        hora_sequence = get_hora_sequence(weekday)
       
        # Format times in 12-hour format
        def format_time(time_obj):
            time_str = time_obj.strftime('%I:%M %p').lstrip('0')
            if time_str.startswith(':'):
                time_str = '12' + time_str
            return time_str
       
        # ഉദയസമയത്തിൽ നിന്നുള്ള വ്യത്യാസം കണക്കാക്കുക
        time_diff = current_time - sunrise_time.replace(tzinfo=None)
        hours_diff = time_diff.total_seconds() / 3600
       
        if hours_diff < 0:
            # ഉദയത്തിന് മുമ്പുള്ള സമയം
            hora_index = (int(hours_diff) % 24 + 24) % 24
        else:
            hora_index = int(hours_diff) % 24
       
        current_hora_name = hora_sequence[hora_index]
        hora_start = sunrise_time + timedelta(hours=hora_index)
        hora_end = hora_start + timedelta(hours=1)
       
        return f"{current_hora_name} ({format_time(hora_start)} to {format_time(hora_end)})"
       
    except Exception as e:
        print(f"Error in current hora calculation: {e}")
        return "ഹോര കണക്കാക്കാനായില്ല"
