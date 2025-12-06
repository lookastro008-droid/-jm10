from datetime import datetime, timedelta
import math
import swisseph as swe


def kollavarsham_calculation(data):
    """
    Calculate Kollavarsham date based on precise Sun position using Swiss Ephemeris
    with ayanamsa correction and sunrise calculation
    """
    try:
        # Extract data
        year = data['year']
        month = data['month']
        day = data['day']
        hour_24h = data['hour_24h']
        minute = data['minute']
        
        # ALWAYS USE KANNUR COORDINATES - Ignore provided location
        latitude = 11.8745  # Kannur latitude
        longitude = 75.3704  # Kannur longitude
        timezone = 'Asia/Kolkata'  # Kannur timezone
        
        print(f"🔍 Kollavarsham calculation started for {day}/{month}/{year} (ALWAYS USING KANNUR)")
        
        # Create datetime object for calculation
        calc_datetime = datetime(year, month, day, hour_24h, minute)
        
        # Calculate precise sunrise time using Swiss Ephemeris for KANNUR
        sunrise_time = calculate_swisseph_sunrise(year, month, day, latitude, longitude)
        
        # Check if current time is before sunrise
        is_before_sunrise = calc_datetime < sunrise_time
        print(f"🌅 Precise sunrise time in KANNUR: {sunrise_time}, Before sunrise: {is_before_sunrise}")
        
        # If before sunrise, use previous day for Kollavarsham (Udaya rule)
        if is_before_sunrise:
            prev_day = calc_datetime - timedelta(days=1)
            kolla_year, kolla_month, kolla_day = calculate_kollavarsham_from_swisseph(
                prev_day.year, prev_day.month, prev_day.day, latitude, longitude
            )
            print(f"📅 Using previous day (Udaya rule): {prev_day.day}/{prev_day.month}/{prev_day.year}")
        else:
            kolla_year, kolla_month, kolla_day = calculate_kollavarsham_from_swisseph(
                year, month, day, latitude, longitude
            )
            print(f"📅 Using current day: {day}/{month}/{year}")
        
        # Format Malayalam month names
        malayalam_months = {
            1: "ചിങ്ങം", 2: "കന്നി", 3: "തുലാം", 4: "വൃശ്ചികം",
            5: "ധനു", 6: "മകരം", 7: "കുംഭം", 8: "മീനം",
            9: "മേടം", 10: "ഇടവം", 11: "മിഥുനം", 12: "കർക്കിടകം"
        }
        
        month_name = malayalam_months.get(kolla_month, "")
        result = f"കൊല്ലവർഷം : {kolla_year} {month_name} {kolla_day}"
        
        print(f"✅ Kollavarsham result for KANNUR: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error in kollavarsham calculation: {e}")
        return f"കൊല്ലവർഷം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"


# സ്ഥലങ്ങളുടെ ഡാറ്റ (ഇപ്പോൾ ഉപയോഗിക്കില്ല, കണ്ണൂർ മാത്രം)
PLACES = {
    'Kannur': {
        'lat': 11.8745,
        'lon': 75.3704,
        'timezone': 'Asia/Kolkata'
    },
    'Thiruvananthapuram': {
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


# --- Base correction and year ---
BASE_ENGLISH_DATE = datetime(2000, 8, 17)  # 17/8/2000 - ചിങ്ങം 1
BASE_KOLLAVARSHAM = 1176  # 2000-ലെ കൊല്ലവർഷം
BASE_CORRECTION = -0.7566
AYANAMSA_PER_YEAR = 0.014
SINGLE_ADJUSTMENT = 0.50 # 0 ഡിഗ്രി 52 സെമി ഡിഗ്രി കൂട്ടുന്നു 


# മലയാളം മാസങ്ങൾ
MALAYALAM_MONTHS = [
    (0, 30, 'മേടം'),
    (30, 60, 'ഇടവം'),
    (60, 90, 'മിഥുനം'),
    (90, 120, 'കർക്കടകം'),
    (120, 150, 'ചിങ്ങം'),
    (150, 180, 'കന്നി'),
    (180, 210, 'തുലാം'),
    (210, 240, 'വൃശ്ചികം'),
    (240, 270, 'ധനു'),
    (270, 300, 'മകരം'),
    (300, 330, 'കുംഭം'),
    (330, 360, 'മീനം')
]


def get_dynamic_correction(year):
    """വർഷം അനുസരിച്ച് അയനാംശം കറക്ഷൻ കണക്കാക്കുന്നു"""
    year_diff = year - BASE_ENGLISH_DATE.year
    return BASE_CORRECTION + (year_diff * AYANAMSA_PER_YEAR)


def calculate_swisseph_sunrise(year, month, day, lat, lng):
    """
    Calculate precise sunrise time using Swiss Ephemeris
    """
    try:
        # Convert to UTC (for India timezone +5:30)
        utc_offset = 5.5
        jd_noon = swe.julday(year, month, day, 12 - utc_offset)
        
        # Calculate sunrise
        rise_jd = swe.rise_trans(jd_noon, swe.SUN, rsmi = swe.CALC_RISE,
                                geopos = (lng, lat, 0), atpress=1013.25, attemp=15)
        
        if rise_jd[0] == 0:  # Success
            sunrise_jd = rise_jd[1][0]
            # Convert JD to datetime
            year_int, month_int, day_int, hour_frac = swe.revjul(sunrise_jd, swe.GREG_CAL)
            hour = int(hour_frac)
            minute = int((hour_frac - hour) * 60)
            sunrise_time = datetime(year_int, month_int, day_int, hour, minute)
            
            # Add 3 minutes adjustment as in original code
            sunrise_time += timedelta(minutes=3)
        else:
            # Fallback: 6:15 AM local time
            sunrise_time = datetime(year, month, day, 6, 15)
            
        print(f"🌅 Calculated sunrise for KANNUR: {sunrise_time}")
        return sunrise_time
        
    except Exception as e:
        print(f"❌ Error in Swiss Ephemeris sunrise calculation: {e}")
        # Fallback to simple calculation
        return datetime(year, month, day, 6, 15)


def get_sun_longitude_at_sunrise(year, month, day, lat, lng):
    """ഉദയസമയത്തെ സൂര്യ ഡിഗ്രി കണക്കാക്കുന്നു (0 ഡിഗ്രി 52 സെമി ഡിഗ്രി കൂട്ടുന്നു)"""
    try:
        # ഉദയസമയം കണ്ടെത്തുന്നു
        sunrise_time = calculate_swisseph_sunrise(year, month, day, lat, lng)
        
        # ഉദയസമയത്തിന്റെ JD കണക്കാക്കുന്നു
        jd = swe.julday(sunrise_time.year, sunrise_time.month, sunrise_time.day,
                        sunrise_time.hour + sunrise_time.minute/60.0 + sunrise_time.second/3600.0)
        
        swe.set_topo(lng, lat, 0)
        
        flags = swe.FLG_SWIEPH
        sun_pos = swe.calc_ut(jd, swe.SUN, flags)[0]
        
        ayanamsa = swe.get_ayanamsa(jd)
        correction = get_dynamic_correction(year)
        corrected_ayanamsa = ayanamsa + correction
        
        # 0 ഡിഗ്രി 52 സെമി ഡിഗ്രി manually കൂട്ടുന്നു
        nirayana_longitude = (sun_pos[0] - corrected_ayanamsa + SINGLE_ADJUSTMENT) % 360
        
        return nirayana_longitude, sunrise_time
        
    except Exception as e:
        raise e


def find_chingam_1_date(year, lat, lng):
    """വർഷത്തിലെ ചിങ്ങം 1 തീയതി കണ്ടുപിടിക്കുന്നു"""
    # 2000-ൽ ചിങ്ങം 1 ഓഗസ്റ്റ് 17 ആണ് എന്ന് നമുക്ക് അറിയാം
    if year == 2000:
        return datetime(2000, 8, 17)
    
    # മറ്റ് വർഷങ്ങൾക്ക് ഏകദേശം ഓഗസ്റ്റ് മധ്യം
    approx_date = datetime(year, 8, 15)
    
    # 15 ദിവസത്തിനുള്ളിൽ ശരിയായ തീയതി കണ്ടുപിടിക്കുന്നു
    for day_offset in range(-7, 8):
        date_candidate = approx_date + timedelta(days=day_offset)
        
        try:
            # ഉദയസമയത്തെ സൂര്യ ഡിഗ്രി കണക്കാക്കുന്നു
            sun_long, sunrise_time = get_sun_longitude_at_sunrise(date_candidate.year, date_candidate.month, date_candidate.day, lat, lng)
            
            # സൂര്യൻ 120 ഡിഗ്രിയിൽ എത്തിയാൽ അത് ചിങ്ങം 1 ആണ്
            if sun_long >= 120 and sun_long < 121:
                return date_candidate
               
        except Exception as e:
            continue
    
    # കണ്ടെത്തിയില്ലെങ്കിൽ ഏകദേശം തീയതി തിരികെ നൽകുന്നു
    return approx_date


def get_kollavarsham_year(date_obj, lat, lng):
    """ഇംഗ്ലീഷ് തീയതിയിൽ നിന്ന് കൊല്ലവർഷം കണക്കാക്കുന്നു - ശരിയായ ലോജിക്"""
    try:
        # നിലവിലെ വർഷത്തിലെ ചിങ്ങം 1
        current_year_chingam_1 = find_chingam_1_date(date_obj.year, lat, lng)
        
        # നിലവിലെ തീയതി ചിങ്ങം 1 ന് മുമ്പാണോ ശേഷമാണോ എന്ന് പരിശോധിക്കുന്നു
        if date_obj >= current_year_chingam_1:
            # ചിങ്ങം 1 ന് ശേഷമാണ് - നിലവിലെ വർഷത്തിന്റെ കൊല്ലവർഷം
            kollavarsham = BASE_KOLLAVARSHAM + (date_obj.year - BASE_ENGLISH_DATE.year)
        else:
            # ചിങ്ങം 1 ന് മുമ്പാണ് - മുൻവർഷത്തിന്റെ കൊല്ലവർഷം
            kollavarsham = BASE_KOLLAVARSHAM + (date_obj.year - BASE_ENGLISH_DATE.year - 1)
            
        return kollavarsham
        
    except Exception as e:
        # എറർ കേസിൽ ഏപ്രോക്സിമേറ്റ് കണക്ക്
        return BASE_KOLLAVARSHAM + (date_obj.year - BASE_ENGLISH_DATE.year)


def check_meenam_special_rule(date_obj, lat, lng, sun_longitude):
    """മീനം അവസാന ദിവസത്തെ സ്പെഷ്യൽ നിയമം പരിശോധിക്കുന്നു"""
    try:
        # മീനം മാസത്തിൽ ആണോ എന്ന് പരിശോധിക്കുന്നു (330-360 ഡിഗ്രി)
        if 330 <= sun_longitude < 360:
            # മീനത്തിൽ 359.46 ഡിഗ്രിയോ അതിന് മുകളിലോ ആണോ എന്ന് പരിശോധിക്കുന്നു
            if sun_longitude >= 359.46:  # 359 ഡിഗ്രി + 46 സെമി
                # അന്ന് തന്നെ മേടം 1 ആയി എഴുതുന്നു
                return 9, 1  # മേടം 1
        
        return None, None
    except Exception as e:
        return None, None


def get_kollavarsham_date_details(date_obj, lat, lng):
    """ഒരു തീയതിക്ക് അനുയോജ്യമായ കൊല്ലവർഷം, മാസം, ദിവസം കണക്കാക്കുന്നു (0 ഡിഗ്രി 52 സെമി ഡിഗ്രി കൂട്ടിയത്)"""
    try:
        # ഉദയസമയത്തെ സൂര്യ ഡിഗ്രി കണക്കാക്കുന്നു (0 ഡിഗ്രി 52 സെമി ഡിഗ്രി കൂട്ടിയത്)
        sun_longitude, sunrise_time = get_sun_longitude_at_sunrise(date_obj.year, date_obj.month, date_obj.day, lat, lng)
        
        # മീനം സ്പെഷ്യൽ നിയമം പരിശോധിക്കുന്നു
        special_month, special_day = check_meenam_special_rule(date_obj, lat, lng, sun_longitude)
        
        if special_month and special_day:
            # സ്പെഷ്യൽ നിയമം ബാധകമാണെങ്കിൽ
            current_month = special_month
            day_of_month = special_day
        else:
            # സാധാരണ രീതിയിൽ മാസവും ദിവസവും കണ്ടുപിടിക്കുന്നു
            current_month = None
            day_of_month = 1
            
            for start, end, month_name in MALAYALAM_MONTHS:
                if start <= sun_longitude < end:
                    current_month = month_name
                    # 1 ദിവസം = 1 ഡിഗ്രി എന്ന നിരക്കിൽ ദിവസം കണക്കാക്കുന്നു
                    # 0-1° = day 1, 1-2° = day 2, 10-11° = day 11
                    day_of_month = int(sun_longitude - start) + 1
                    break
        
        # കൊല്ലവർഷം കണക്കാക്കുന്നു
        kollavarsham = get_kollavarsham_year(date_obj, lat, lng)

        # Convert month name to number for consistency
        month_name_to_number = {
            'മേടം': 9, 'ഇടവം': 10, 'മിഥുനം': 11, 'കർക്കടകം': 12,
            'ചിങ്ങം': 1, 'കന്നി': 2, 'തുലാം': 3, 'വൃശ്ചികം': 4,
            'ധനു': 5, 'മകരം': 6, 'കുംഭം': 7, 'മീനം': 8
        }
        
        month_number = month_name_to_number.get(current_month, 1)

        return kollavarsham, month_number, day_of_month, sun_longitude
        
    except Exception as e:
        raise e


def calculate_kollavarsham_from_swisseph(year, month, day, lat, lng):
    """
    Calculate Kollavarsham date using Swiss Ephemeris Sun position
    with proper year calculation and special rules
    """
    try:
        print(f"📊 Calculating Kollavarsham for {day}/{month}/{year} using Swiss Ephemeris (KANNUR)")
        
        current_date = datetime(year, month, day)
        
        # കൊല്ലവർഷം, മാസം, ദിവസം കണക്കാക്കുന്നു (0 ഡിഗ്രി 52 സെമി ഡിഗ്രി കൂട്ടിയത്)
        kollavarsham, current_month, day_of_month, sun_longitude = get_kollavarsham_date_details(current_date, lat, lng)

        print(f"📅 Final Kollavarsham for KANNUR: {kollavarsham}-{current_month}-{day_of_month}")
        return kollavarsham, current_month, day_of_month
        
    except Exception as e:
        print(f"❌ Error in Kollavarsham calculation: {e}")
        return 1200, 1, 1


def test_kollavarsham():
    """
    Test function to verify calculation for various dates
    """
    print("🧪 Starting Kollavarsham tests...")
    
    # Test case for today - ALWAYS USES KANNUR
    test_data = {
        'year': 2024,
        'month': 11,
        'day': 15,
        'hour_24h': 12,
        'minute': 0,
        'latitude': 8.5241,  # This will be ignored - Kannur used instead
        'longitude': 76.9366,  # This will be ignored - Kannur used instead
        'timezone': 'Asia/Kolkata'
    }
    
    result = kollavarsham_calculation(test_data)
    print(f"🧪 Test result (ALWAYS KANNUR): {result}")
    
    return result


if __name__ == "__main__":
    # Initialize swisseph
    swe.set_ephe_path()
    test_kollavarsham()
