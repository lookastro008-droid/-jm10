from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
import math
import os
import pytz

# എഫിമെറിഡ് ഫയലുകളുടെ പാത് സജ്ജമാക്കുക
swe.set_ephe_path(os.path.join(os.path.dirname(__file__), '..', 'swisseph'))

# നക്ഷത്രങ്ങളുടെ ഡിഗ്രി ശ്രേണികൾ (മേടം 0° മുതൽ)
NAKSHATRAS = [
    {"name": "അശ്വതി", "start": 0.0, "end": 13.3333},
    {"name": "ഭരണി", "start": 13.3333, "end": 26.6667},
    {"name": "കാർത്തിക", "start": 26.6667, "end": 40.0},
    {"name": "രോഹിണി", "start": 40.0, "end": 53.3333},
    {"name": "മകയിരം", "start": 53.3333, "end": 66.6667},
    {"name": "തിരുവാതിര", "start": 66.6667, "end": 80.0},
    {"name": "പുണർതം", "start": 80.0, "end": 93.3333},
    {"name": "പൂയം", "start": 93.3333, "end": 106.6667},
    {"name": "ആയില്യം", "start": 106.6667, "end": 120.0},
    {"name": "മകം", "start": 120.0, "end": 133.3333},
    {"name": "പൂരം", "start": 133.3333, "end": 146.6667},
    {"name": "ഉത്രം", "start": 146.6667, "end": 160.0},
    {"name": "അത്തം", "start": 160.0, "end": 173.3333},
    {"name": "ചിത്തിര", "start": 173.3333, "end": 186.6667},
    {"name": "ചോതി", "start": 186.6667, "end": 200.0},
    {"name": "വിശാഖം", "start": 200.0, "end": 213.3333},
    {"name": "അനിഴം", "start": 213.3333, "end": 226.6667},
    {"name": "തൃക്കേട്ട", "start": 226.6667, "end": 240.0},
    {"name": "മൂലം", "start": 240.0, "end": 253.3333},
    {"name": "പൂരാടം", "start": 253.3333, "end": 266.6667},
    {"name": "ഉത്രാടം", "start": 266.6667, "end": 280.0},
    {"name": "തിരുവോണം", "start": 280.0, "end": 293.3333},
    {"name": "അവിട്ടം", "start": 293.3333, "end": 306.6667},
    {"name": "ചതയം", "start": 306.6667, "end": 320.0},
    {"name": "പൂരുരുട്ടാതി", "start": 320.0, "end": 333.3333},
    {"name": "ഉത്രട്ടാതി", "start": 333.3333, "end": 346.6667},
    {"name": "രേവതി", "start": 346.6667, "end": 360.0}
]

# രാശികളുടെ പട്ടിക
RASHIS = [
    "മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം",
    "ചിങ്ങം", "കന്നി", "തുലാം", "വൃശ്ചികം",
    "ധനു", "മകരം", "കുംഭം", "മീനം"
]

# തിഥികളുടെ പട്ടിക
THITHIS = [
    "പ്രതിപദം", "ദ്വിതീയ", "തൃതീയ", "ചതുർത്ഥി",
    "പഞ്ചമി", "ഷഷ്ഠി", "സപ്തമി", "അഷ്ടമി",
    "നവമി", "ദശമി", "ഏകാദശി", "ദ്വാദശി",
    "ത്രയോദശി", "ചതുര്ദശി", "പൗർണ്ണമി", "അമാവാസി"
]

# കരണങ്ങളുടെ പട്ടിക
SHUKLA_PAKSHA_KARANAS = {
    1: ['പുഴു', 'സിംഹം'],
    2: ['പുലി', 'പന്നി'],
    3: ['കഴുത', 'ആന'],
    4: ['പശു', 'വിഷ്ടി'],
    5: ['സിംഹം', 'പുലി'],
    6: ['പന്നി', 'കഴുത'],
    7: ['ആന', 'സുരഭി'],
    8: ['വിഷ്ടി', 'സിംഹം'],
    9: ['പുലി', 'പന്നി'],
    10: ['കഴുത', 'ആന'],
    11: ['പശു', 'വിഷ്ടി'],
    12: ['സിംഹം', 'പുലി'],
    13: ['പന്നി', 'കഴുത'],
    14: ['ആന', 'പശു'],
    15: ['വിഷ്ടി', 'സിംഹം']
}

KRISHNA_PAKSHA_KARANAS = {
    1: ['പുലി', 'പന്നി'],
    2: ['കഴുത', 'ആന'],
    3: ['പശു', 'വിഷ്ടി'],
    4: ['സിംഹം', 'പുലി'],
    5: ['പന്നി', 'കഴുത'],
    6: ['ആന', 'സുരഭി'],
    7: ['വിഷ്ടി', 'സിംഹം'],
    8: ['പുലി', 'പന്നി'],
    9: ['കഴുത', 'ആന'],
    10: ['പശു', 'വിഷ്ടി'],
    11: ['സിംഹം', 'പുലി'],
    12: ['പന്നി', 'കഴുത'],
    13: ['ആന', 'സുരഭി'],
    14: ['വിഷ്ടി', 'പുള്ള്'],
    15: ['ചതുഷ്പാത്', 'നാഗം']
}

# നിത്യയോഗങ്ങളുടെ പട്ടിക
YOGAS = [
    {"name": "വിഷ്കുംഭം", "start": 0.0, "end": 13.3333},
    {"name": "പ്രീതി", "start": 13.3333, "end": 26.6667},
    {"name": "ആയുഷ്മാൻ", "start": 26.6667, "end": 40.0},
    {"name": "സൗഭാഗ്യ", "start": 40.0, "end": 53.3333},
    {"name": "ശോഭനം", "start": 53.3333, "end": 66.6667},
    {"name": "അതിഗണ്ഡം", "start": 66.6667, "end": 80.0},
    {"name": "സുകർമ്മ", "start": 80.0, "end": 93.3333},
    {"name": "ധൃതി", "start": 93.3333, "end": 106.6667},
    {"name": "ശൂല", "start": 106.6667, "end": 120.0},
    {"name": "ഗണ്ഡവം", "start": 120.0, "end": 133.3333},
    {"name": "വൃദ്ധി", "start": 133.3333, "end": 146.6667},
    {"name": "ധ്രുവം", "start": 146.6667, "end": 160.0},
    {"name": "വ്യാഘാതം", "start": 160.0, "end": 173.3333},
    {"name": "ഹർഷണം", "start": 173.3333, "end": 186.6667},
    {"name": "വജ്ജ്രം", "start": 186.6667, "end": 200.0},
    {"name": "സിദ്ധി", "start": 200.0, "end": 213.3333},
    {"name": "വ്യതിപാതം", "start": 213.3333, "end": 226.6667},
    {"name": "വരിയാൻ", "start": 226.6667, "end": 240.0},
    {"name": "പരിഘം", "start": 240.0, "end": 253.3333},
    {"name": "ശിവ", "start": 253.3333, "end": 266.6667},
    {"name": "സിദ്ധ", "start": 266.6667, "end": 280.0},
    {"name": "സാദ്ധ്യ", "start": 280.0, "end": 293.3333},
    {"name": "ശുഭ", "start": 293.3333, "end": 306.6667},
    {"name": "ശുഭ്ര", "start": 306.6667, "end": 320.0},
    {"name": "ബ്രാഹ്മ", "start": 320.0, "end": 333.3333},
    {"name": "മാഹേന്ദ്ര", "start": 333.3333, "end": 346.6667},
    {"name": "വൈധൃതി", "start": 346.6667, "end": 360.0}
]

# ചെറിയ epsilon ഒഴിവാക്കാൻ
EPS = 1e-8

# ആയനാംശം പ്രയോഗിക്കുന്ന ഫംഗ്ഷൻ (കൃത്യമായ ഗണിതം)
def apply_ayanamsa(degree):
    """
    കൃത്യമായ ആയനാംശം കണക്കാക്കുന്നു
    """
    # ആയനാംശം കൃത്യമായി കണക്കാക്കുന്നു
    base_ayanamsa = 24.219444  # 24°13'10" in decimal degrees
    
    # ഡിഗ്രിയിൽ നിന്ന് ആയനാംശം കുറയ്ക്കുന്നു
    degree_with_ayanamsa = degree - base_ayanamsa
    
    # ഡിഗ്രി 0-360 ശ്രേണിയിൽ നിലനിർത്തുന്നു
    degree_with_ayanamsa %= 360.0
    if degree_with_ayanamsa < 0:
        degree_with_ayanamsa += 360.0
        
    return degree_with_ayanamsa

# നക്ഷത്രം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_nakshatra(degree):
    degree = degree % 360.0
    for nakshatra in NAKSHATRAS:
        if nakshatra['start'] <= degree < nakshatra['end']:
            return nakshatra
    # Handle case when degree is exactly 360.0
    return NAKSHATRAS[0]

# യോഗം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_yoga(degree):
    degree = degree % 360.0
    for yoga in YOGAS:
        if yoga['start'] <= degree < yoga['end']:
            return yoga
    return YOGAS[0]

# UTC-ൽ നിന്ന് സ്ഥാനീയ സമയത്തേക്ക് മാറ്റുന്ന ഫംഗ്ഷൻ
def utc_to_local(utc_time, timezone_offset):
    return utc_time + timedelta(hours=timezone_offset)

# സ്ഥാനീയ സമയത്തിൽ നിന്ന് UTC-ലേക്ക് മാറ്റുന്ന ഫംഗ്ഷൻ
def local_to_utc(local_time, timezone_offset):
    return local_time - timedelta(hours=timezone_offset)

# സ്ട്രിംഗ് timezone-നെ float-ആക്കി മാറ്റുന്ന ഫംഗ്ഷൻ
def parse_timezone(timezone_input):
    """
    സ്ട്രിംഗ് timezone-നെ float-ആക്കി മാറ്റുന്നു
    'Asia/Kolkata' -> 5.5
    """
    if isinstance(timezone_input, (int, float)):
        return float(timezone_input)
    
    if isinstance(timezone_input, str):
        # നമ്പർ സ്ട്രിംഗ് ആണെങ്കിൽ
        try:
            return float(timezone_input)
        except ValueError:
            # timezone name ആണെങ്കിൽ
            timezone_mapping = {
                'Asia/Kolkata': 5.5,
                'Asia/Calcutta': 5.5,
                'IST': 5.5,
                'UTC': 0.0,
                'GMT': 0.0
            }
            if timezone_input in timezone_mapping:
                return timezone_mapping[timezone_input]
            else:
                # ഡിഫോൾട്ട് ഇന്ത്യൻ സ്റ്റാൻഡേർഡ് ടൈം
                return 5.5
    
    # ഡിഫോൾട്ട്
    return 5.5

# ഗ്രഹ സ്ഥാനം കണക്കാക്കുന്ന ഫംഗ്ഷൻ (കൃത്യമായ ഗണിതം)
def calculate_planetary_positions(date_time_utc, coords):
    """
    കൃത്യമായ ഗ്രഹ സ്ഥാനം കണക്കാക്കുന്നു
    """
    # ജൂലിയൻ ദിനം കണക്കാക്കുന്നു
    jd = swe.julday(date_time_utc.year, date_time_utc.month, date_time_utc.day,
                   date_time_utc.hour + date_time_utc.minute/60.0 + date_time_utc.second/3600.0)
    
    # സൂര്യന്റെ സ്ഥാനം
    sun_pos, sun_flags = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    sun_degree = apply_ayanamsa(sun_pos[0] % 360.0)
    
    # ചന്ദ്രന്റെ സ്ഥാനം
    moon_pos, moon_flags = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    moon_degree = apply_ayanamsa(moon_pos[0] % 360.0)
    
    return {
        'sun': sun_degree,
        'moon': moon_degree,
        'jd': jd
    }

# പാദം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_pada(degree, nakshatra):
    nakshatra_range = nakshatra['end'] - nakshatra['start']
    position_in_nakshatra = (degree - nakshatra['start']) % 360.0
    pada = int(position_in_nakshatra / (nakshatra_range / 4)) + 1
    return min(max(pada, 1), 4)

# കൃത്യമായ കരണം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ (തിരുത്തിയത്)
def find_karana(thithi_number, moon_sun_diff, thithi_progress):
    """
    കൃത്യമായ കരണം കണ്ടെത്തുന്നു - തിരുത്തിയ പതിപ്പ്
    """
    # നിർണ്ണയിക്കാം ഏത് പക്ഷം
    if moon_sun_diff < 180:  # ശുക്ല പക്ഷം
        karana_list = SHUKLA_PAKSHA_KARANAS
    else:
        karana_list = KRISHNA_PAKSHA_KARANAS
    
    # തിഥി നമ്പർ 1..15 ലേക്ക് മാപ്പ് ചെയ്യുന്നു - ശരിയായി
    mapped_thithi = ((thithi_number - 1) % 15) + 1
    
    # പ്രത്യേക 15-ആം തിഥി കൈകാര്യംചെയ്യൽ
    if mapped_thithi == 15:
        karana_pair = karana_list[mapped_thithi]
        karana_index = 0 if thithi_progress < 6 else 1
        current_karana = karana_pair[karana_index]
        return current_karana
    
    # സാധാരണ കരണ ജോടി
    if mapped_thithi in karana_list:
        karana_pair = karana_list[mapped_thithi]
        # തിഥി പുരോഗതി അടിസ്ഥാനത്തിൽ കരണം തിരഞ്ഞെടുക്കുന്നു
        # തിഥിയുടെ ആദ്യ പകുതി: ആദ്യ കരണം, രണ്ടാം പകുതി: രണ്ടാം കരണം
        karana_index = 0 if thithi_progress < 6 else 1
        current_karana = karana_pair[karana_index]
        return current_karana
    
    return "അജ്ഞാതം"

# തിഥി കണ്ടെത്തുന്ന ഫംഗ്ഷൻ (കൃത്യമായ ഗണിതം) - തിരുത്തിയത്
def find_thithi(moon_degree, sun_degree):
    """
    കൃത്യമായ തിഥി കണ്ടെത്തുന്നു - ഒന്ന് കുറവ് വരുന്ന പ്രശ്നം തിരുത്തി
    """
    moon_sun_diff = (moon_degree - sun_degree) % 360.0
    
    # തിഥി ഇൻഡെക്സ് കൃത്യമായി കണക്കാക്കുന്നു
    thithi_index = int(moon_sun_diff / 12.0)  # 0..29
    thithi_number = thithi_index + 1  # 1..30
    
    # പുരോഗതി കൃത്യമായി കണക്കാക്കുന്നു
    thithi_progress = (moon_sun_diff % 12.0)
    
    paksha = "ശുക്ല പക്ഷം" if moon_sun_diff < 180 else "കൃഷ്ണ പക്ഷം"
    
    # തിഥിയുടെ പേര് നിർണ്ണയിക്കുന്നു - ഒന്ന് കുറവ് വരുന്ന പ്രശ്നം തിരുത്തി
    if thithi_number == 15:  # 15-ആം തിഥി (പൗർണ്ണമി)
        thithi_name = "പൗർണ്ണമി"
    elif thithi_number == 30:  # 30-ആം തിഥി (അമാവാസി)
        thithi_name = "അമാവാസി"
    else:
        # സാധാരണ തിഥികൾ - ഇൻഡെക്സ് ശരിയായി ഉപയോഗിക്കുന്നു
        actual_thithi_index = (thithi_number - 1) % 15
        thithi_name = THITHIS[actual_thithi_index]
    
    return {
        'number': thithi_number,
        'name': thithi_name,
        'moon_sun_diff': moon_sun_diff,
        'progress': thithi_progress,
        'paksha': paksha
    }

# നക്ഷത്രം തുടങ്ങിയ സമയവും അവസാന സമയവും കണക്കാക്കുന്ന ഫംഗ്ഷൻ
def calculate_nakshatra_timing(moon_degree, current_time_utc, timezone):
    """
    നക്ഷത്രം തുടങ്ങിയ സമയവും അവസാന സമയവും കണക്കാക്കുന്നു
    """
    try:
        # നിലവിലെ നക്ഷത്രം
        current_nakshatra = find_nakshatra(moon_degree)
        
        # നക്ഷത്രം തുടങ്ങിയ ഡിഗ്രി
        start_degree = current_nakshatra['start']
        
        # നക്ഷത്രം അവസാനിക്കുന്ന ഡിഗ്രി  
        end_degree = current_nakshatra['end']
        
        # നിലവിലെ ചന്ദ്ര ഡിഗ്രി
        current_moon_deg = moon_degree
        
        # അടുത്ത ദിവസം ചന്ദ്ര ഡിഗ്രി കണക്കാക്കുന്നു
        next_day_utc = current_time_utc + timedelta(days=1)
        next_day_jd = swe.julday(next_day_utc.year, next_day_utc.month, next_day_utc.day,
                                next_day_utc.hour + next_day_utc.minute/60.0)
        next_moon_pos, _ = swe.calc_ut(next_day_jd, swe.MOON, swe.FLG_SWIEPH)
        next_moon_deg = apply_ayanamsa(next_moon_pos[0] % 360.0)
        
        # ചന്ദ്രന്റെ പ്രതിദിന ചലനം
        daily_movement = (next_moon_deg - current_moon_deg) % 360.0
        if daily_movement < 0:
            daily_movement += 360.0
            
        # മണിക്കൂറിൽ ചലിക്കുന്ന ഡിഗ്രി
        hourly_movement = daily_movement / 24.0
        
        # നക്ഷത്രം തുടങ്ങിയതിന് ശേഷമുള്ള സമയം കണക്കാക്കുന്നു
        if current_moon_deg >= start_degree:
            # നക്ഷത്രം ഇതിനകം തുടങ്ങി
            degrees_passed = current_moon_deg - start_degree
        else:
            # നക്ഷത്രം തുടങ്ങിയത് മുൻദിവസം
            degrees_passed = (360.0 - start_degree) + current_moon_deg
            
        hours_passed = degrees_passed / hourly_movement
        
        # നക്ഷത്രം തുടങ്ങിയ സമയം
        start_time_utc = current_time_utc - timedelta(hours=hours_passed)
        
        # നക്ഷത്രം അവസാനിക്കുന്നതിന് ബാക്കിയുള്ള സമയം
        if current_moon_deg <= end_degree:
            degrees_remaining = end_degree - current_moon_deg
        else:
            degrees_remaining = (360.0 - current_moon_deg) + end_degree
            
        hours_remaining = degrees_remaining / hourly_movement
        
        # നക്ഷത്രം അവസാനിക്കുന്ന സമയം
        end_time_utc = current_time_utc + timedelta(hours=hours_remaining)
        
        # സ്ഥാനീയ സമയത്തിലേക്ക് മാറ്റുന്നു
        start_time_local = utc_to_local(start_time_utc, timezone)
        end_time_local = utc_to_local(end_time_utc, timezone)
        
        # നാഴിക വിനാഴിക കണക്കാക്കുന്നു
        total_nakshatra_hours = (end_time_local - start_time_local).total_seconds() / 3600.0
        elapsed_hours = (current_time_utc - start_time_utc).total_seconds() / 3600.0
        
        # നാഴികയിലേക്ക് മാറ്റുന്നു (1 നാഴിക = 24 മിനിറ്റ്)
        total_nazhika = total_nakshatra_hours * (60/24)
        elapsed_nazhika = elapsed_hours * (60/24)
        
        nazhika = int(elapsed_nazhika)
        vinazhika = int((elapsed_nazhika - nazhika) * 60)
        
        return {
            'start_time': start_time_local.strftime('%d/%m/%Y %I:%M %p'),
            'end_time': end_time_local.strftime('%d/%m/%Y %I:%M %p'),
            'nazhika': nazhika,
            'vinazhika': vinazhika
        }
        
    except Exception as e:
        print(f"Error calculating nakshatra timing: {e}")
        return {
            'start_time': 'കണക്കാക്കാനായില്ല',
            'end_time': 'കണക്കാക്കാനായില്ല', 
            'nazhika': 0,
            'vinazhika': 0
        }

# നിങ്ങളുടെ nakshathra_calculation ഫംഗ്ഷൻ - പുതിയ ഫീച്ചറുകളോടെ
def nakshathra_calculation(data):
    try:
        # ഇൻപുട്ട് ഡാറ്റാ വായിക്കുന്നു
        day = int(data.get('day'))
        month = int(data.get('month'))
        year = int(data.get('year'))
        hour_24h = int(data.get('hour_24h', 12))
        minute = int(data.get('minute', 0))
        lat = float(data.get('latitude', 11.8745))
        lon = float(data.get('longitude', 75.3704))
        timezone_input = data.get('timezone', 'Asia/Kolkata')
        
        # timezone പാഴ്സ് ചെയ്യുന്നു
        timezone = parse_timezone(timezone_input)

        # സ്ഥാനീയ സമയം
        local_dt = datetime(year, month, day, hour_24h, minute, 0)
        
        # UTC സമയത്തിലേക്ക് മാറ്റുന്നു
        utc_dt = local_to_utc(local_dt, timezone)

        coords = {'lat': lat, 'lon': lon, 'timezone': timezone}

        # ഗ്രഹ സ്ഥാനം കണക്കാക്കുന്നു
        positions = calculate_planetary_positions(utc_dt, coords)
        sun_deg = positions['sun']
        moon_deg = positions['moon']
        jd = positions['jd']

        # നക്ഷത്രം കണ്ടെത്തുന്നു
        nak = find_nakshatra(moon_deg)
        pada = find_pada(moon_deg, nak)

        # തിഥി കണ്ടെത്തുന്നു
        thithi = find_thithi(moon_deg, sun_deg)

        # കരണം കണ്ടെത്തുന്നു - ഒരു കരണം മാത്രം റിട്ടേൺ ചെയ്യുന്നു
        karana = find_karana(thithi['number'], thithi['moon_sun_diff'], thithi['progress'])

        # യോഗം കണ്ടെത്തുന്നു
        yoga_degree = (sun_deg + moon_deg) % 360.0
        yoga = find_yoga(yoga_degree)

        # നക്ഷത്ര സമയം കണക്കാക്കുന്നു
        nakshatra_timing = calculate_nakshatra_timing(moon_deg, utc_dt, timezone)

        # ഫലങ്ങൾ രൂപപ്പെടുത്തുന്നു - പുതിയ ഡിസ്പ്ലേ ഫോർമാറ്റ്
        return {
            'നക്ഷത്രം': f"നക്ഷത്രം : {nak['name']} പാദം {pada}",
            'തിഥി': f"തിഥി : {thithi['name']} ({thithi['paksha']})", 
            'കരണം': f"കരണം: {karana}",
            'യോഗം': f"നിത്യയോഗം: {yoga['name']}",
            'നക്ഷത്ര_സമയം': f"തുടക്കം: {nakshatra_timing['start_time']} | അവസാനം: {nakshatra_timing['end_time']}",
            'നക്ഷത്ര_ദൈർഘ്യം': f"നക്ഷത്രത്തിൽ ചെന്ന നാഴിക: {nakshatra_timing['nazhika']} നാഴിക {nakshatra_timing['vinazhika']} വിനാഴിക"
        }

    except Exception as e:
        print(f"❌ Error in nakshathra_calculation: {str(e)}")
        return {
            'നക്ഷത്രം': f"നക്ഷത്രം : കണക്കാക്കാനായില്ല ({e})",
            'തിഥി': "തിഥി : കണക്കാക്കാനായില്ല",
            'കരണം': "കരണം: കണക്കാക്കാനായില്ല", 
            'യോഗം': "നിത്യയോഗം: കണക്കാക്കാനായില്ല",
            'നക്ഷത്ര_സമയം': "തുടക്കം: കണക്കാക്കാനായില്ല | അവസാനം: കണക്കാക്കാനായില്ല",
            'നക്ഷത്ര_ദൈർഘ്യം': "നക്ഷത്രത്തിൽ ചെന്ന നാഴിക: കണക്കാക്കാനായില്ല"
        }
