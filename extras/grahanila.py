from flask import render_template, jsonify

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

import matplotlib.font_manager as fm

from io import BytesIO

import base64

import numpy as np

import swisseph as swe

from datetime import datetime, timedelta, timezone

from astral import LocationInfo

from astral.sun import sun

import pytz


# ഗ്രഹങ്ങളുടെ ചുരുക്കപ്പേരുകൾ (മലയാളം)

PLANET_SHORT_NAMES = {

    "ലഗ്നം": "ല",

    "സൂര്യൻ": "ര",

    "ചന്ദ്രൻ": "ച",

    "ചൊവ്വ": "കു",

    "ബുധൻ": "ബു",

    "ഗുരു": "ഗു",

    "ശുക്രൻ": "ശു",

    "ശനി": "മ",

    "രാഹു": "സ",

    "കേതു": "ശി",

    "ഗുളികൻ": "മാ"

}


# രാശി പേരുകൾ (മേടം=0 ... മീനം=11)

RASHI_NAMES = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "സിംഹം", "കന്നി",

               "തുലാം", "വൃശ്ചികം", "ധ ു", "മകരം", "കുംഭം", "മീനം"]


# Swiss Ephemeris ഗ്രഹ കോഡുകൾ

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


# ഗുളികൻ ഉദയ സമയങ്ങൾ (പകൽ) -- Python weekday(): Monday=0 ... Sunday=6

DAY_GULIKA_TIMES = {

    0: timedelta(hours=8, minutes=48),   # തിങ്കൾ (Monday)

    1: timedelta(hours=7, minutes=12),   # ചൊവ്വ (Tuesday)

    2: timedelta(hours=5, minutes=36),   # ബുധൻ (Wednesday)

    3: timedelta(hours=4, minutes=0),    # വ്യാഴം (Thursday)

    4: timedelta(hours=2, minutes=24),   # വെള്ളി (Friday)

    5: timedelta(hours=0, minutes=48),   # ശനി (Saturday)

    6: timedelta(hours=10, minutes=24),  # ഞായർ (Sunday)

}


# ഗുളികൻ ഉദയ സമയങ്ങൾ (രാത്രി) -- അസ്തമനത്തിന് ശേഷം

NIGHT_GULIKA_TIMES = {

    0: timedelta(hours=2, minutes=24),   # തിങ്കൾ (Monday)

    1: timedelta(hours=0, minutes=48),   # ചൊവ്വ (Tuesday)

    2: timedelta(hours=10, minutes=24),  # ബുധൻ (Wednesday)

    3: timedelta(hours=8, minutes=48),   # വ്യാഴം (Thursday)

    4: timedelta(hours=7, minutes=12),   # വെള്ളി (Friday)

    5: timedelta(hours=5, minutes=36),   # ശനി (Saturday)

    6: timedelta(hours=4, minutes=0),    # ഞായർ (Sunday)

}


# ദിനമാന വ്യത്യാസം ചാർട്ടുകൾ (വിനാഴികയിൽ)

DAY_CORRECTION_CHARTS = {

    6: {  # ഞായറാഴ്ച (Sunday)

        1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9,

        20: 17, 30: 26, 40: 35, 50: 43, 60: 52, 70: 64, 80: 69, 90: 78, 100: 87

    },

    0: {  # തിങ്കളാഴ്ച (Monday)

        1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 5, 8: 6, 9: 7, 10: 7,

        20: 15, 30: 22, 40: 29, 50: 37, 60: 44, 70: 51, 80: 59, 90: 66, 100: 73

    },

    1: {  # ചൊവ്വാഴ്ച (Tuesday)

        1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5, 10: 6,

        20: 12, 30: 18, 40: 24, 50: 30, 60: 36, 70: 42, 80: 48, 90: 54, 100: 60

    },

    2: {  # ബുധനാഴ്ച (Wednesday)

        1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4, 10: 5,

        20: 9, 30: 14, 40: 19, 50: 23, 60: 28, 70: 33, 80: 37, 90: 42, 100: 47

    },

    3: {  # വ്യാഴാഴ്ച (Thursday)

        1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4, 10: 5,

        20: 9, 30: 14, 40: 19, 50: 23, 60: 28, 70: 33, 80: 47, 90: 42, 100: 47

    },

    4: {  # വെള്ളിയാഴ്ച (Friday)

        1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2, 10: 2,

        20: 4, 30: 6, 40: 8, 50: 10, 60: 12, 70: 14, 80: 16, 90: 19

    },

    5: {  # ശനിയാഴ്ച (Saturday)

        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 1, 9: 1, 10: 1,

        20: 2, 30: 3, 40: 3, 50: 4, 60: 5, 70: 5, 80: 6, 90: 6, 100: 7

    }

}


def get_coordinates(place):

    """സ്ഥലത്തിന്റെ അക്ഷാംശം, രേഖാംശം നൽകുന്നു"""

    places = {

        'കണ്ണൂർ': (11.8745, 75.3704),

        'തിരുവനന്തപുരം': (8.5241, 76.9366),

        'കൊച്ചി': (9.9312, 76.2673),

        'കോഴിക്കോട്': (11.2588, 75.7804),

        'തൃശൂർ': (10.5276, 76.2144)

    }

    return places.get(place, (11.8745, 75.3704))  # കണ്ണൂർ ഡിഫോൾട്ട്


def calculate_sunrise_sunset(date_obj, place):

    """ഉദയം, അസ്തമയം കണക്കാക്കുന്നു (കേരളീയ ശൈലി - ഉദയം +3min, അസ്തമയം -3min)"""

    try:

        lat, lon = get_coordinates(place)

        loc = LocationInfo(place, "India", "Asia/Kolkata", lat, lon)

        s = sun(loc.observer, date=date_obj, tzinfo=loc.timezone)

        # sunrise +3 minutes, sunset -3 minutes (കേരളീയ ശൈലി)

        sunrise_time = s['sunrise'] + timedelta(minutes=3)

        sunset_time = s['sunset'] - timedelta(minutes=3)

        return sunrise_time, sunset_time

    except Exception as e:

        raise Exception(f"ഉദയം/അസ്തമയം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")


def minutes_to_vinazhika(minutes):

    """മിനിറ്റുകളെ വിനാഴികയാക്കി മാറ്റുന്നു"""

    return int(minutes * 2.5)  # 1 മിനിറ്റ് = 2.5 വിനാഴിക


def vinazhika_to_minutes(vinazhika):

    """വിനാഴികയെ മിനിറ്റുകളാക്കി മാറ്റുന്നു"""

    return vinazhika / 2.5  # 1 വിനാഴിക = 0.4 മിനിറ്റ്


def get_night_chart_weekday(weekday):

    """രാത്രി ഗുളികന് അഞ്ചാമത്തെ ദിവസത്തിന്റെ ചാർട്ട് ഉപയോഗിക്കുന്നു"""

    # രാത്രി അഞ്ചാമത്തെ ദിവസം മാപ്പിംഗ്

    night_chart_mapping = {

        6: 3,  # ഞായർ -> വ്യാഴം

        0: 4,  # തിങ്കൾ -> വെള്ളി

        1: 5,  # ചൊവ്വ -> ശനി

        2: 6,  # ബുധൻ -> ഞായർ

        3: 0,  # വ്യാഴം -> തിങ്കൾ

        4: 1,  # വെള്ളി -> ചൊവ്വ

        5: 2   # ശനി -> ബുധൻ

    }

    return night_chart_mapping.get(weekday, weekday)


def get_correction_from_chart(weekday, vinazhika_value, is_day=True):

    """ചാർട്ടിൽ നിന്ന് തിരുത്തൽ വിനാഴിക കണ്ടെത്തുന്നു"""

    # രാത്രി ഗുളികന് അഞ്ചാമത്തെ ദിവസത്തിന്റെ ചാർട്ട് ഉപയോഗിക്കുക

    if not is_day:

        weekday = get_night_chart_weekday(weekday)


    chart = DAY_CORRECTION_CHARTS.get(weekday, {})


    # ചാർട്ടിൽ ഉള്ള ഏറ്റവും അടുത്തുള്ള മൂല്യം കണ്ടെത്തുക

    if not chart:  # ചാർട്ട് ശൂന്യമാണെങ്കിൽ

        return 0


    closest_key = min(chart.keys(), key=lambda x: abs(x - vinazhika_value))

    return chart[closest_key]


def calculate_day_duration_difference(sunrise, sunset):

    """ദിനമാനത്തിന്റെ വ്യത്യാസം 12 മണിക്കൂറിൽ നിന്നും എത്ര മിനിറ്റ് കൂടി/കുറഞ്ഞു എന്ന് കണക്കാക്കുന്നു"""

    day_duration = sunset - sunrise

    twelve_hours = timedelta(hours=12)

    difference = day_duration - twelve_hours

    return difference.total_seconds() / 60  # മിനിറ്റുകളിൽ


def calculate_corrected_gulika_time(sunrise, sunset, weekday, is_day=True):

    """തിരുത്തിയ ഗുളിക സമയം കണക്കാക്കുന്നു"""

    try:

        # ദിനമാന വ്യത്യാസം കണക്കാക്കുക

        day_duration_diff_minutes = calculate_day_duration_difference(sunrise, sunset)


        # വ്യത്യാസത്തെ വിനാഴികയാക്കി മാറ്റുക

        diff_vinazhika = minutes_to_vinazhika(abs(day_duration_diff_minutes))


        # ചാർട്ടിൽ നിന്ന് തിരുത്തൽ വിനാഴിക എടുക്കുക (രാത്രി ആണെങ്കിൽ അഞ്ചാമത്തെ ദിവസത്തിന്റെ ചാർട്ട്)

        correction_vinazhika = get_correction_from_chart(weekday, diff_vinazhika, is_day)


        # തിരുത്തൽ വിനാഴികയെ മിനിറ്റുകളാക്കി മാറ്റുക

        correction_minutes = vinazhika_to_minutes(correction_vinazhika)


        if is_day:

            # പകൽ ഗുളികൻ

            base_gulika_time = sunrise + DAY_GULIKA_TIMES[weekday]


            if day_duration_diff_minutes > 0:  # പകൽ കൂടുതൽ

                corrected_gulika_time = base_gulika_time + timedelta(minutes=correction_minutes)

            else:  # പകൽ കുറവ്

                corrected_gulika_time = base_gulika_time - timedelta(minutes=correction_minutes)

        else:

            # രാത്രി ഗുളികൻ

            base_gulika_time = sunset + NIGHT_GULIKA_TIMES[weekday]


            if day_duration_diff_minutes > 0:  # പകൽ കൂടുതൽ = രാത്രി കുറവ്

                corrected_gulika_time = base_gulika_time - timedelta(minutes=correction_minutes)

            else:  # പകൽ കുറവ് = രാത്രി കൂടുതൽ

                corrected_gulika_time = base_gulika_time + timedelta(minutes=correction_minutes)


        return corrected_gulika_time, day_duration_diff_minutes, correction_vinazhika



    except Exception as e:

        raise Exception(f"തിരുത്തിയ ഗുളിക സമയം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")


def calculate_planet_position(datetime_obj, ayanamsa, place):

    """ലഗ്നം (ascendant) പോലെ ഗുളിക ഡിഗ്രി കണക്കാക്കാം"""

    try:

        # ensure tz-aware; if naive, assume Asia/Kolkata

        if datetime_obj.tzinfo is None:

            local_tz = pytz.timezone('Asia/Kolkata')

            datetime_obj = local_tz.localize(datetime_obj)

        # convert to UTC for julian day / swe

        utc_dt = datetime_obj.astimezone(pytz.UTC)

        # Julian Day in UT

        jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,

                         utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)

        # get lat, lon

        lat, lon = get_coordinates(place)

        # get tropical ascendant using swe.houses

        cusps, ascmc = swe.houses(jd_ut, lat, lon)

        tropical_asc = ascmc[0] % 360.0


        # set sidereal mode per user choice and get ayanamsa (degrees)

        swe.set_sid_mode(int(ayanamsa))

        ayanamsa_deg = swe.get_ayanamsa(jd_ut)


        # convert to sidereal ascendant by subtracting ayanamsa

        sidereal_asc = (tropical_asc - ayanamsa_deg) % 360.0


        # break into sign/deg/min/sec

        sign = int(sidereal_asc / 30) % 12

        degrees_in_sign = sidereal_asc % 30

        degrees = int(degrees_in_sign)

        minutes = int((degrees_in_sign - degrees) * 60)

        seconds = int((((degrees_in_sign - degrees) * 60) - minutes) * 60)

        semi_degrees = seconds // 30


        sign_names = [

            "മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം",

            "ചിങ്ങം", "കന്നി", "തുലാം", "വൃശ്ചികം",

            "ധനു", "മകരം", "കുംഭം", "മീനം"

        ]


        return {

            'sign': sign_names[sign],

            'degrees': degrees,

            'minutes': minutes,

            'seconds': seconds,

            'semi_degrees': semi_degrees,

            'longitude': sidereal_asc,

            'rasi_index': sign

        }

    except Exception as e:

        raise Exception(f"ഗ്രഹ/ലഗ്നം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")


def make_timezone_aware(dt, timezone_str='Asia/Kolkata'):

    """Datetime object-നെ timezone-aware ആക്കുന്നു"""

    if dt.tzinfo is None:

        return pytz.timezone(timezone_str).localize(dt)

    return dt


def calculate_gulika_degree(dob_datetime, place, ayanamsa):

    """DOB അനുസരിച്ച് ഗുളിക ഡിഗ്രി കണക്കാക്കുക"""

    try:

        # datetime object-നെ timezone-aware ആക്കുക

        dob_datetime = make_timezone_aware(dob_datetime)


        # weekday as per Python: Monday=0 ... Sunday=6

        weekday = dob_datetime.weekday()

        # sunrise, sunset from astral (tz-aware)

        sunrise, sunset = calculate_sunrise_sunset(dob_datetime.date(), place)

        # Check if DOB is during day or night - ഇപ്പോൾ എല്ലാം timezone-aware ആണ്

        is_day_time = sunrise <= dob_datetime <= sunset


        if is_day_time:

            # പകൽ ഗുളികൻ

            day_gulika_time, day_duration_diff, day_correction_vinazhika = calculate_corrected_gulika_time(

                sunrise, sunset, weekday, is_day=True)

            gulika_position = calculate_planet_position(day_gulika_time, ayanamsa, place)

            gulika_type = "പകൽ ഗുളികൻ"

        else:

            # രാത്രി ഗുളികൻ

            night_gulika_time, night_duration_diff, night_correction_vinazhika = calculate_corrected_gulika_time(

                sunrise, sunset, weekday, is_day=False)

            gulika_position = calculate_planet_position(night_gulika_time, ayanamsa, place)

            gulika_type = "രാത്രി ഗുളികൻ"


        gulika_position['name'] = "ഗുളികൻ"

        gulika_position['type'] = gulika_type


        return gulika_position


    except Exception as e:

        raise Exception(f"ഗുളിക ഡിഗ്രി കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")


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


        print(f"⏰ സമയം പരിവർത്തനം:")

        print(f"   ഇൻപുട്ട്: {year}/{month}/{day} {hour}:{minute}:{second} ({timezone_str})")

        print(f"   UTC: {utc_dt.year}/{utc_dt.month}/{utc_dt.day} {utc_dt.hour}:{utc_dt.minute}:{utc_dt.second}")


        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second



    except Exception as e:

        print(f"❌ UTC പരിവർത്തന പിശക്: {e}")

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


    # മറ്റ് ഗ്രഹങ്ങൾ

    for planet_name, planet_code in PLANET_CODES.items():

        degree = calculate_planet_degree(jd_ut, planet_code, ayanamsa_mode)

        rasi_index = int(degree / 30)

        planets.append({"name": planet_name, "rasi_index": rasi_index, "degree": degree})


    # കേതു കണക്കാക്കുക

    rahu_degree = planets[-1]["degree"]  # രാഹുവിന്റെ ഡിഗ്രി

    ketu_degree = (rahu_degree + 180) % 360

    ketu_index = int(ketu_degree / 30)

    planets.append({"name": "കേതു", "rasi_index": ketu_index, "degree": ketu_degree})


    return {"planets": planets}


def _get_malayalam_font_prop():

    """Noto Sans Malayalam കിട്ടിയില്ലെങ്കിൽ fallback DejaVu Sans"""

    preferred = ['Noto Sans Malayalam', 'NotoSansMalayalam', 'Noto-Malayalam']

    for fam in preferred:

        try:

            fp_try = fm.FontProperties(family=fam)

            font_path = fm.findfont(fp_try)

            if font_path and 'DejaVu' not in font_path:

                return fm.FontProperties(fname=font_path)

        except Exception:

            pass


    try:

        for p in fm.findSystemFonts(fontpaths=None, fontext='ttf'):

            low = p.lower()

            if 'noto' in low and 'malay' in low:

                return fm.FontProperties(fname=p)

    except Exception:

        pass


    default_path = fm.findfont(fm.FontProperties(family='DejaVu Sans'))

    return fm.FontProperties(fname=default_path)


def degree_to_rashi_details(degree):

    """ഡിഗ്രിയെ രാശി, ഡിഗ്രി, സെമി ഡിഗ്രിയാക്കി മാറ്റുക"""

    rashi_index = int(degree / 30)

    degree_in_rashi = degree % 30

    degrees = int(degree_in_rashi)

    minutes = int((degree_in_rashi - degrees) * 60)


    return rashi_index, degrees, minutes


def calculate_navamsa(rasi_index, degree):

    """നവാംശകം കണക്കാക്കുക"""

    # ഒരു നവാംശകം = 3°20' = 3.3333 ഡിഗ്രി

    navamsa_size = 3.3333


    # ഗ്രഹത്തിന്റെ രാശിയിലെ ഡിഗ്രി

    degree_in_rasi = degree % 30


    # രാശി തരങ്ങൾ

    chara_rashis = [0, 3, 6, 9]   # മേടം, കർക്കടകം, തുലാം, മകരം

    sthira_rashis = [1, 4, 7, 10] # ഇടവം, ചിങ്ങം, വൃശ്ചികം, കുംഭം

    ubhaya_rashis = [2, 5, 8, 11] # മിഥുനം, കന്നി, ധനു, മീനം


    if rasi_index in chara_rashis:

        # ചരരാശികൾ - ആ രാശിയിൽ നിന്ന് തുടങ്ങി 3°20' വച്ച് എണ്ണുക

        navamsa_count = int(degree_in_rasi / navamsa_size)

        navamsa_rashi = (rasi_index + navamsa_count) % 12


    elif rasi_index in sthira_rashis:

        # സ്ഥിരരാശികൾ - ഒൻപതാം രാശിയിൽ നിന്ന് തുടങ്ങി 3°20' വച്ച് എണ്ണുക

        navamsa_count = int(degree_in_rasi / navamsa_size)

        navamsa_rashi = ((rasi_index + 8) % 12 + navamsa_count) % 12


    else:  # ubhaya_rashis

        # ഉഭയരാശികൾ - അഞ്ചാം രാശിയിൽ നിന്ന് തുടങ്ങി 3°20' വച്ച് എണ്ണുക

        navamsa_count = int(degree_in_rasi / navamsa_size)

        navamsa_rashi = ((rasi_index + 4) % 12 + navamsa_count) % 12


    return navamsa_rashi


def calculate_font_size_and_chart_size(planets_data):

    """ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ഫോണ്ട് സൈസും ചാർട്ട് സൈസും കണക്കാക്കുക"""

    max_planets_in_rashi = 0

    rashi_planets = {i: [] for i in range(12)}


    for planet in planets_data:

        rashi_index = planet.get('rasi_index', 0)

        rashi_planets[rashi_index].append(planet['name'])

        max_planets_in_rashi = max(max_planets_in_rashi, len(rashi_planets[rashi_index]))


    # ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ഫോണ്ട് സൈസ് നിർണ്ണയിക്കുക - വളരെ വലുതാക്കി

    if max_planets_in_rashi <= 2:

        font_size = 52  # വളരെ വലുതാക്കി (മുമ്പ് 48 ആയിരുന്നു)

        chart_size = 16

    elif max_planets_in_rashi == 3:

        font_size = 46  # വളരെ വലുതാക്കി (മുമ്പ് 42 ആയിരുന്നു)

        chart_size = 16

    elif max_planets_in_rashi == 4:

        font_size = 40  # വളരെ വലുതാക്കി (മുമ്പ് 36 ആയിരുന്നു)

        chart_size = 18

    else:

        font_size = 36  # വളരെ വലുതാക്കി (മുമ്പ് 32 ആയിരുന്നു)

        chart_size = 20


    return font_size, chart_size


def calculate_bhava_margins(lagna_degree):

    """ഭാവ മാർജിൻ കണക്കാക്കുക"""

    # Step 1: ലഗ്ന ഡിഗ്രിയിൽ നിന്ന് 15 ഡിഗ്രി കുറക്കുക

    bhava_start_margin = (lagna_degree - 15) % 360


    # Step 2: ലഗ്ന ഡിഗ്രിയിൽ നിന്ന് 15 ഡിഗ്രി കൂട്ടുക

    bhava_end_margin = (lagna_degree + 15) % 360


    return bhava_start_margin, bhava_end_margin


def calculate_bhava_rasi_ranges(lagna_degree):

    """എല്ലാ രാശികൾക്കും ഭാവ ആരംഭ-അവസാന ഡിഗ്രികൾ കണക്കാക്കുക"""

    bhava_ranges = {}


    # ഭാവം തുടങ്ങുന്നത് ലഗ്ന രാശിയിൽ നിന്ന് 15 ഡിഗ്രി മുമ്പ്

    bhava_start_degree = (lagna_degree - 15) % 360

    bhava_start_rashi = int(bhava_start_degree / 30)


    # എല്ലാ രാശികൾക്കും ഭാവ ആരംഭ-അവസാനം

    for i in range(12):

        current_rashi = (bhava_start_rashi + i) % 12

        start_degree = (bhava_start_degree + i * 30) % 360

        end_degree = (start_degree + 30) % 360


        bhava_ranges[current_rashi] = {

            'start_degree': start_degree,

            'end_degree': end_degree

        }


    return bhava_ranges


def get_bhava_rasi_for_planet(planet_degree, bhava_ranges):

    """ഗ്രഹത്തിന്റെ ഭാവ രാശി കണ്ടെത്തുക"""

    for rashi_index, range_info in bhava_ranges.items():

        start_degree = range_info['start_degree']

        end_degree = range_info['end_degree']


        # ഡിഗ്രി രീതിയിൽ താരതമ്യം ചെയ്യുക

        if start_degree <= end_degree:

            # സാധാരണ കേസ്

            if start_degree <= planet_degree < end_degree:

                return rashi_index

        else:

            # 360° കടന്നുപോകുന്ന കേസ്

            if planet_degree >= start_degree or planet_degree < end_degree:

                return rashi_index


    # ഒന്നും കിട്ടിയില്ലെങ്കിൽ യഥാർത്ഥ രാശി തിരികെ നൽകുക

    return int(planet_degree / 30)


def calculate_bhava_positions(planets_data, lagna_degree):

    """ഭാവ ഡിഗ്രി അനുസരിച്ച് ഗ്രഹങ്ങളുടെ സ്ഥാനം കണക്കാക്കുക"""

    # ഭാവ മാർജിൻ കണക്കാക്കുക

    bhava_start_margin, bhava_end_margin = calculate_bhava_margins(lagna_degree)


    # എല്ലാ രാശികൾക്കും ഭാവ ആരംഭ-അവസാനം കണക്കാക്കുക

    bhava_ranges = calculate_bhava_rasi_ranges(lagna_degree)


    bhava_planets = []


    for planet in planets_data:

        planet_degree = planet['degree']

        original_rashi = planet['rasi_index']


        # ഭാവ രാശി കണ്ടെത്തുക

        bhava_rashi = get_bhava_rasi_for_planet(planet_degree, bhava_ranges)


        # ഭാവ ഗ്രഹം സൃഷ്ടിക്കുക

        bhava_planet = planet.copy()

        bhava_planet['rasi_index'] = bhava_rashi

        bhava_planet['original_rashi'] = original_rashi  # യഥാർത്ഥ രാശി സൂക്ഷിക്കുക


        bhava_planets.append(bhava_planet)


    return bhava_planets


def create_rashi_chart(planets_data, chart_title="രാശി", is_bhava=False):

    """രാശി ചക്രം സൃഷ്ടിക്കുക"""

    # ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ചാർട്ട് സൈസ് നിർണ്ണയിക്കുക

    font_size, chart_size = calculate_font_size_and_chart_size(planets_data)


    # ചക്രം സൃഷ്ടിക്കുക - ബാക്ക്ഗ്രൗണ്ട് ഒഴിവാക്കി

    fig, ax = plt.subplots(figsize=(chart_size, chart_size))

    fig.patch.set_facecolor('#f8f5e6')  # പുറം ബാക്ക്ഗ്രൗണ്ട് മാത്രം

    ax.set_facecolor('#f8f5e6')  # ചക്രത്തിനുള്ളിൽ ബാക്ക്ഗ്രൗണ്ട് ഒഴിവാക്കി


    mal_font_prop = _get_malayalam_font_prop()


    rashi_planets = {i: [] for i in range(12)}


    # ഭാവചക്രത്തിന് മാത്രം ക്ലോക്ക് ബേസിൽ ഷിഫ്റ്റ് കൂട്ടുക

    if is_bhava:

        RASHI_SHIFT = 2  # ഭാവചക്രത്തിന് 2 ഷിഫ്റ്റ്

    else:

        RASHI_SHIFT = 1  # സാധാരണ ചക്രങ്ങൾക്ക് 1 ഷിഫ്റ്റ്


    for planet in planets_data:

        raw_index = planet.get('rasi_index', 0)

        rashi_index = (raw_index + RASHI_SHIFT) % 12

        short_name = PLANET_SHORT_NAMES.get(planet['name'], planet['name'][0])

        rashi_planets[rashi_index].append(short_name)


    rashi_positions = [

        (0, 0), (0, 1), (0, 2), (0, 3),

        (1, 3), (2, 3), (3, 3), (3, 2),

        (3, 1), (3, 0), (2, 0), (1, 0)

    ]


    rashi_order = list(range(12))


    # ചാർട്ട് സൈസ് അനുസരിച്ച് cell_size കണക്കാക്കുക

    cell_size = chart_size / 3.0  # കൂടുതൽ സ്പേസ് ലഭിക്കാൻ ചെറുതാക്കി


    for idx, (i, j) in enumerate(rashi_positions):

        rashi_index = rashi_order[idx]

        x_center = j * cell_size + cell_size / 2

        y_center = (3 - i) * cell_size + cell_size / 2


        rect = plt.Rectangle((j * cell_size, (3 - i) * cell_size),

                          cell_size, cell_size,

                          fill=True, edgecolor='#8B4513',

                          facecolor='white', linewidth=4.0)  # കട്ടിയായ ബോർഡർ

        ax.add_patch(rect)


        planets_in_rashi = rashi_planets[rashi_index]

        if planets_in_rashi:

            # ഓരോ രാശിയിലും ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ഫോണ്ട് സൈസ് - ഇപ്പോൾ കൂടുതൽ ഫ്ലെക്സിബിൾ

            current_font_size = font_size


            # 3 ലധികം ഗ്രഹങ്ങൾ ഉള്ളപ്പോൾ മാത്രം ഫോണ്ട് സൈസ് കുറയ്ക്കുക

            if len(planets_in_rashi) > 3:

                current_font_size = max(34, font_size - 12)  # വളരെ വലുതാക്കി, പക്ഷേ കുറച്ച് കുറച്ചു

            elif len(planets_in_rashi) > 2:

                current_font_size = max(40, font_size - 6)  # വളരെ വലുതാക്കി, പക്ഷേ കുറച്ച് കുറച്ചു


            planets_text = " ".join(planets_in_rashi)

            ax.text(x_center, y_center, planets_text,

                    ha='center', va='center', fontsize=current_font_size,

                    fontweight='bold', fontproperties=mal_font_prop)


    # മധ്യത്തിലെ ടെക്സ്റ്റ്

    ax.text(2 * cell_size, 2 * cell_size, chart_title,

            ha='center', va='center', fontsize=58, fontweight='bold',  # വളരെ വലുതാക്കി (മുമ്പ് 52 ആയിരുന്നു)

            color='#8B0000', fontproperties=mal_font_prop)


    ax.set_xlim(0, 4 * cell_size)

    ax.set_ylim(0, 4 * cell_size)

    ax.set_aspect('equal')

    ax.axis('off')


    img = BytesIO()

    plt.savefig(img, format='png', dpi=150,  # ഉയർന്ന റെസല്യൂഷൻ

                bbox_inches='tight', facecolor=fig.get_facecolor(),

                transparent=False)

    img.seek(0)

    chart_url = base64.b64encode(img.getvalue()).decode('utf-8')

    plt.close()


    return chart_url


def graha_nila_calculation(data):

    """പ്രധാന ഗണിത ഫങ്ഷൻ - app.py-ൽ നിന്ന് വിവരങ്ങൾ സ്വീകരിക്കുന്നു"""

    try:

        print(f"🔍 Graha Nila calculation called with data: {data}")


        # Extract data from app.py calculation

        year = data.get('year')

        month = data.get('month')

        day = data.get('day')

        hour_24h = data.get('hour_24h')

        minute = data.get('minute')

        place = data.get('place', {'name': 'കണ്ണൂർ', 'lat': 11.8745, 'lng': 75.3704})

        calculation_type = data.get('calculation_type', 'auto')

        timezone_str = data.get('timezone', 'Asia/Kolkata')  # ✅ പുതിയത്: സമയമേഖല

        ayanamsa_mode = 1  # Default ayanamsa


        print(f"   - Calculation type: {calculation_type}")

        print(f"   - Date: {day}/{month}/{year}")

        print(f"   - Time: {hour_24h}:{minute}")

        print(f"   - Place: {place['name']}")

        print(f"   - Timezone: {timezone_str}")  # ✅ പുതിയത്


        # Create datetime object

        dob_datetime = datetime(year, month, day, hour_24h, minute, 0)


        # ✅ പുതിയത്: സമയമേഖല അനുസരിച്ച് UTC-യിലേക്ക് മാറ്റുക

        utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(

            year, month, day, hour_24h, minute, 0, timezone_str  # ✅ timezone_str ചേർത്തു

        )


        jd_ut = swe.julday(utc_year, utc_month, utc_day,

                         utc_hour + utc_minute/60.0 + utc_second/3600.0)


        # Calculate regular planet positions with ayanamsa mode

        results = calculate_planet_positions(jd_ut, place['lat'], place['lng'], ayanamsa_mode)


        # Calculate Gulika degree

        gulika_position = calculate_gulika_degree(dob_datetime, place['name'], str(ayanamsa_mode))


        # Add Gulika to the planets list

        results['planets'].append({

            "name": "ഗുളികൻ",

            "rasi_index": gulika_position['rasi_index'],

            "degree": gulika_position['longitude'],

            "type": gulika_position['type']

        })


        # Calculate Navamsa positions for all planets

        navamsa_planets = []

        for planet in results['planets']:

            navamsa_rashi = calculate_navamsa(planet['rasi_index'], planet['degree'])

            navamsa_planets.append({

                "name": planet['name'],

                "rasi_index": navamsa_rashi,

                "degree": planet['degree']

            })


        # Calculate Bhava positions for all planets

        lagna_degree = results['planets'][0]['degree']  # ലഗ്നത്തിന്റെ ഡിഗ്രി

        bhava_planets = calculate_bhava_positions(results['planets'], lagna_degree)


        # Create Rashi Chart

        rashi_chart_url = create_rashi_chart(results['planets'], "രാശി", is_bhava=False)


        # Create Navamsa Chart

        navamsa_chart_url = create_rashi_chart(navamsa_planets, "നവാംശകം", is_bhava=False)


        # Create Bhava Chart

        bhava_chart_url = create_rashi_chart(bhava_planets, "ഭാവം", is_bhava=True)


        # Create detailed result HTML - സമയമേഖല ചേർക്കുക

        result_html = f"""

        <!DOCTYPE html>

        <html>

        <head>

            <meta charset="UTF-8">

            <meta name="viewport" content="width=device-width, initial-scale=1.0">

            <title>ഗ്രഹനില - ജാതക ചക്രം</title>

            <style>

                body {{

                    font-family: 'Noto Sans Malayalam', Arial, sans-serif;

                    background: #f8f5e6;

                    padding: 15px;

                    margin: 0;

                }}

                .info-section {{

                    background: white;

                    padding: 20px;

                    border-radius: 10px;

                    margin-bottom: 20px;

                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);

                }}

                .chart-container {{

                    text-align: center;

                    max-width: 100%;

                    margin: 0 auto;

                    background: white;

                    padding: 10px;

                    border-radius: 10px;

                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);

                    margin-bottom: 10px;

                }}

                .chart-image {{

                    max-width: 100%;

                    height: auto;

                    border: 2px solid #8B4513;

                    border-radius: 8px;

                }}

                .planet-details {{

                    display: grid;

                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));

                    gap: 15px;

                    margin-top: 20px;

                }}

                .planet-item {{

                    background: #f5f5f5;

                    padding: 15px;

                    border-radius: 8px;

                    border-left: 4px solid #8B0000;

                }}

                .back-button {{

                    display: block;

                    text-align: center;

                    margin: 15px auto;

                    padding: 12px 24px;

                    background: #8B4513;

                    color: white;

                    text-decoration: none;

                    border-radius: 5px;

                    width: 200px;

                }}

            </style>

        </head>

        <body>

            <div class="info-section">

                <h2>ജാതക വിവരങ്ങൾ</h2>

                <p><strong>തീയതി:</strong> {day}/{month}/{year}</p>

                <p><strong>സമയം:</strong> {hour_24h}:{minute:02d}</p>

                <p><strong>സ്ഥലം:</strong> {place['name']}</p>

            </div>

            

            <div class="chart-container">

                <h2>രാശി ചക്രം</h2>

                <img src="data:image/png;base64,{rashi_chart_url}" alt="രാശി ചക്രം" class="chart-image">

            </div>

            

            <div class="chart-container">

                <h2>നവാംശക ചക്രം</h2>

                <img src="data:image/png;base64,{navamsa_chart_url}" alt="നവാംശക ചക്രം" class="chart-image">

            </div>


            <div class="chart-container">

                <h2>ഭാവ ചക്രം</h2>

                <img src="data:image/png;base64,{bhava_chart_url}" alt="ഭാവ ചക്രം" class="chart-image">

            </div>

            

            <div class="info-section">

                <h2>ഗ്രഹ സ്ഥിതികൾ</h2>

                <div class="planet-details">

        """


        # Add planet details

        for planet in results['planets']:

            rashi_index, degrees, minutes = degree_to_rashi_details(planet['degree'])

            result_html += f"""

                    <div class="planet-item">

                        <strong>{planet['name']}</strong><br>

                        രാശി: {RASHI_NAMES[rashi_index]}<br>

                        ഡിഗ്രി: {degrees}° {minutes}'

                        {f"<br>തരം: {planet['type']}" if planet.get('type') else ""}

                    </div>

            """


        result_html += """

                </div>

            </div>

            

            <div style="text-align: center;">

                <a href="javascript:history.back()" class="back-button">മടങ്ങുക</a>

            </div>

        </body>

        </html>

        """


        return result_html


    except Exception as e:

        error_message = f"ഗ്രഹനില കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}"

        print(f"❌ Error in graha_nila_calculation: {error_message}")

        return f"""

        <div style='color: red; text-align: center; padding: 20px; max-width: 600px; margin: 0 auto;'>

            <h3>പിശക്:</h3>

            <p>{error_message}</p>

            <a href='javascript:history.back()' style='background: #8B4513; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>മടങ്ങുക</a>

        </div>

        """
