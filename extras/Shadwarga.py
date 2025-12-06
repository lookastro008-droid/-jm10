import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
import base64
import numpy as np
import swisseph as swe
from datetime import datetime
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
    "കേതു": "ശി"
}

# രാശി പേരുകൾ (മേടം=0 ... മീനം=11)
RASHI_NAMES = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "സിംഹം", "കന്നി",
              "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"]

# രാശി അധിപന്മാർ
RASHI_LORDS = {
    "മേടം": "ചൊവ്വ",
    "ഇടവം": "ശുക്രൻ",
    "മിഥുനം": "ബുധൻ",
    "കർക്കടകം": "ചന്ദ്രൻ",
    "സിംഹം": "സൂര്യൻ",
    "കന്നി": "ബുധൻ",
    "തുലാം": "ശുക്രൻ",
    "വൃശ്ചികം": "ചൊവ്വ",
    "ധനു": "ഗുരു",
    "മകരം": "ശനി",
    "കുംഭം": "ശനി",
    "മീനം": "ഗുരു"
}

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

# ഓജ രാശികൾ
ODD_RASHIS = [0, 2, 4, 6, 8, 10]  # മേടം, മിഥുനം, ചിങ്ങം, തുലാം, ധനു, കുംഭം
# യുഗ്മ രാശികൾ
EVEN_RASHIS = [1, 3, 5, 7, 9, 11]  # ഇടവം, കർക്കടകം, കന്നി, വൃശ്ചികം, മകരം, മീനം

# തൃംശാംശം അധിപന്മാർ - ഓജ രാശികൾക്ക്
ODD_TRIMSAMSA_LORDS = {
    (0, 5): "ചൊവ്വ",
    (5, 10): "ശനി",
    (10, 18): "ഗുരു",
    (18, 25): "ബുധൻ",
    (25, 30): "ശുക്രൻ"
}

# തൃംശാംശം അധിപന്മാർ - യുഗ്മ രാശികൾക്ക്
EVEN_TRIMSAMSA_LORDS = {
    (0, 5): "ശുക്രൻ",
    (5, 12): "ബുധൻ",
    (12, 20): "ഗുരു",
    (20, 25): "ശനി",
    (25, 30): "ചൊവ്വ"
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
       
        print(f"📍 Place data received:")
        print(f"   - Name: {place_name}")
        print(f"   - Lat: {lat}")
        print(f"   - Lng: {lng}")
        print(f"   - Timezone: {timezone}")
       
        return lat, lng, timezone
       
    except Exception as e:
        print(f"⚠️ Error getting coordinates: {e}. Using defaults.")
        # ഡിഫോൾട്ട് values
        return 11.8745, 75.3704, 'Asia/Kolkata'

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
       
        print(f"⏰ Time conversion:")
        print(f"   Input: {year}/{month}/{day} {hour}:{minute}:{second} ({timezone_str})")
        print(f"   UTC: {utc_dt.year}/{utc_dt.month}/{utc_dt.day} {utc_dt.hour}:{utc_dt.minute}:{utc_dt.second}")
       
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second
       
    except Exception as e:
        print(f"❌ UTC conversion error: {e}")
        # Fallback: IST മാത്രം
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
   
    return planets

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

def calculate_drekkana(rasi_index, degree):
    """ദ്രേക്കാണം കണക്കാക്കുക"""
    degree_in_rasi = degree % 30
   
    # ദ്രേക്കാണം നിർണ്ണയിക്കുക (ഓരോ 10 ഡിഗ്രിയും ഒരു ദ്രേക്കാണം)
    drekkana_part = int(degree_in_rasi / 10) + 1
   
    # ദ്രേക്കാണ അധിപൻ നിർണ്ണയിക്കുക
    if drekkana_part == 1:
        # ആദ്യ ദ്രേക്കാണം - രാശിയുടെ അധിപൻ
        drekkana_lord = RASHI_LORDS[RASHI_NAMES[rasi_index]]
    elif drekkana_part == 2:
        # രണ്ടാം ദ്രേക്കാണം - അഞ്ചാം രാശിയുടെ അധിപൻ
        fifth_rashi = (rasi_index + 4) % 12
        drekkana_lord = RASHI_LORDS[RASHI_NAMES[fifth_rashi]]
    else:  # drekkana_part == 3
        # മൂന്നാം ദ്രേക്കാണം - ഒൻപതാം രാശിയുടെ അധിപൻ
        ninth_rashi = (rasi_index + 8) % 12
        drekkana_lord = RASHI_LORDS[RASHI_NAMES[ninth_rashi]]
   
    return {
        'rasi': RASHI_NAMES[rasi_index],
        'part': drekkana_part,
        'lord': drekkana_lord
    }

def calculate_dwadasamsa(rasi_index, degree):
    """ദ്വാദശാംശം കണക്കാക്കുക"""
    degree_in_rasi = degree % 30
   
    # ഓരോ രാശിയും 2.5 ഡിഗ്രി വീതം (30/12 = 2.5)
    dwadasamsa_size = 2.5
   
    # ദ്വാദശാംശ രാശി കണക്കാക്കുക
    dwadasamsa_count = int(degree_in_rasi / dwadasamsa_size)
    dwadasamsa_rashi = (rasi_index + dwadasamsa_count) % 12
   
    return {
        'rasi': RASHI_NAMES[dwadasamsa_rashi],
        'lord': RASHI_LORDS[RASHI_NAMES[dwadasamsa_rashi]]
    }

def calculate_trimsamsa(rasi_index, degree):
    """തൃംശാംശം കണക്കാക്കുക"""
    degree_in_rasi = degree % 30
   
    # ഓജ രാശിയോ യുഗ്മ രാശിയോ ആയി നോക്കുക
    if rasi_index in ODD_RASHIS:
        # ഓജ രാശികൾ
        lords_dict = ODD_TRIMSAMSA_LORDS
    else:
        # യുഗ്മ രാശികൾ
        lords_dict = EVEN_TRIMSAMSA_LORDS
   
    # ഡിഗ്രി ഏത് പരിധിയിൽ വരുന്നു എന്ന് നോക്കുക
    for (start, end), lord in lords_dict.items():
        if start <= degree_in_rasi < end:
            return lord
   
    # അവസാന പരിധി
    return list(lords_dict.values())[-1]

def calculate_hora(rasi_index, degree):
    """ഹോര കണക്കാക്കുക"""
    degree_in_rasi = degree % 30
   
    if rasi_index in ODD_RASHIS:
        # ഓജ രാശികൾ - ആദ്യ 15° സൂര്യൻ, ബാക്കി ചന്ദ്രൻ
        if degree_in_rasi < 15:
            return "സൂര്യൻ"
        else:
            return "ചന്ദ്രൻ"
    else:
        # യുഗ്മ രാശികൾ - ആദ്യ 15° ചന്ദ്രൻ, ബാക്കി സൂര്യൻ
        if degree_in_rasi < 15:
            return "ചന്ദ്രൻ"
        else:
            return "സൂര്യൻ"

def calculate_shad_varga(planets_data):
    """ഷഡ് വർഗ്ഗം കണക്കാക്കുക"""
    shad_varga_results = []
   
    for planet in planets_data:
        name = planet['name']
        rasi_index = planet['rasi_index']
        degree = planet['degree']
       
        # ക്ഷേത്രം
        kshetra = {
            'rasi': RASHI_NAMES[rasi_index],
            'lord': RASHI_LORDS[RASHI_NAMES[rasi_index]]
        }
       
        # നവാംശകം
        navamsa_rashi = calculate_navamsa(rasi_index, degree)
        navamsa = {
            'rasi': RASHI_NAMES[navamsa_rashi],
            'lord': RASHI_LORDS[RASHI_NAMES[navamsa_rashi]]
        }
       
        # ഹോര
        hora = calculate_hora(rasi_index, degree)
       
        # ദ്രേക്കാണം
        drekkana = calculate_drekkana(rasi_index, degree)
       
        # ദ്വാദശാംശം
        dwadasamsa = calculate_dwadasamsa(rasi_index, degree)
       
        # തൃംശാംശം
        trimsamsa = calculate_trimsamsa(rasi_index, degree)
       
        shad_varga_results.append({
            'planet': name,
            'kshetra': kshetra,
            'navamsa': navamsa,
            'hora': hora,
            'drekkana': drekkana,
            'dwadasamsa': dwadasamsa,
            'trimsamsa': trimsamsa,
            'degree': degree,
            'rasi_index': rasi_index
        })
   
    return shad_varga_results

def calculate_font_size_and_chart_size(planets_data):
    """ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ഫോണ്ട് സൈസും ചാർട്ട് സൈസും കണക്കാക്കുക"""
    max_planets_in_rashi = 0
    rashi_planets = {i: [] for i in range(12)}
   
    for planet in planets_data:
        rashi_index = planet.get('rasi_index', 0)
        rashi_planets[rashi_index].append(planet['name'])
        max_planets_in_rashi = max(max_planets_in_rashi, len(rashi_planets[rashi_index]))
   
    # ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ഫോണ്ട് സൈസ് നിർണ്ണയിക്കുക
    if max_planets_in_rashi <= 2:
        font_size = 52
        chart_size = 16
    elif max_planets_in_rashi == 3:
        font_size = 46
        chart_size = 16
    elif max_planets_in_rashi == 4:
        font_size = 40
        chart_size = 18
    else:
        font_size = 36
        chart_size = 20
   
    return font_size, chart_size

def create_rashi_chart(planets_data, chart_title="രാശി", is_bhava=False):
    """രാശി ചക്രം സൃഷ്ടിക്കുക"""
    # ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ചാർട്ട് സൈസ് നിർണ്ണയിക്കുക
    font_size, chart_size = calculate_font_size_and_chart_size(planets_data)

    # ചക്രം സൃഷ്ടിക്കുക
    fig, ax = plt.subplots(figsize=(chart_size, chart_size))
    fig.patch.set_facecolor('#f8f5e6')
    ax.set_facecolor('#f8f5e6')

    mal_font_prop = _get_malayalam_font_prop()

    rashi_planets = {i: [] for i in range(12)}

    # ഭാവചക്രത്തിന് മാത്രം ക്ലോക്ക് ബേസിൽ ഷിഫ്റ്റ് കൂട്ടുക
    if is_bhava:
        RASHI_SHIFT = 2
    else:
        RASHI_SHIFT = 1

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
    cell_size = chart_size / 3.0
   
    for idx, (i, j) in enumerate(rashi_positions):
        rashi_index = rashi_order[idx]
        x_center = j * cell_size + cell_size / 2
        y_center = (3 - i) * cell_size + cell_size / 2

        rect = plt.Rectangle((j * cell_size, (3 - i) * cell_size),
                          cell_size, cell_size,
                          fill=True, edgecolor='#8B4513',
                          facecolor='white', linewidth=4.0)
        ax.add_patch(rect)

        planets_in_rashi = rashi_planets[rashi_index]
        if planets_in_rashi:
            current_font_size = font_size
           
            if len(planets_in_rashi) > 3:
                current_font_size = max(34, font_size - 12)
            elif len(planets_in_rashi) > 2:
                current_font_size = max(40, font_size - 6)

            planets_text = " ".join(planets_in_rashi)
            ax.text(x_center, y_center, planets_text,
                    ha='center', va='center', fontsize=current_font_size,
                    fontweight='bold', fontproperties=mal_font_prop)

    # മധ്യത്തിലെ ടെക്സ്റ്റ്
    ax.text(2 * cell_size, 2 * cell_size, chart_title,
            ha='center', va='center', fontsize=58, fontweight='bold',
            color='#8B0000', fontproperties=mal_font_prop)

    ax.set_xlim(0, 4 * cell_size)
    ax.set_ylim(0, 4 * cell_size)
    ax.set_aspect('equal')
    ax.axis('off')

    img = BytesIO()
    plt.savefig(img, format='png', dpi=150,
                bbox_inches='tight', facecolor=fig.get_facecolor(),
                transparent=False)
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
   
    return chart_url

def create_shad_varga_display(shad_varga_data):
    """ഷഡ് വർഗ്ഗം ഡിസ്പ്ലേ ചെയ്യുക"""
    html_output = """
    <div style="background: white; padding: 20px; border-radius: 10px; margin: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    """
   
    for planet_data in shad_varga_data:
        planet_name = planet_data['planet']
        kshetra = planet_data['kshetra']
        navamsa = planet_data['navamsa']
        hora = planet_data['hora']
        drekkana = planet_data['drekkana']
        dwadasamsa = planet_data['dwadasamsa']
        trimsamsa = planet_data['trimsamsa']
       
        html_output += f"""
        <div style="border: 2px solid #8B4513; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f9f3e9;">
            <h4 style="color: #8B0000; margin: 0 0 10px 0;">{planet_name}</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div><strong>ക്ഷേത്രം:</strong> {kshetra['rasi']} ({kshetra['lord']})</div>
                <div><strong>നവാംശകം:</strong> {navamsa['rasi']} ({navamsa['lord']})</div>
                <div><strong>ഹോര:</strong> {hora}</div>
                <div><strong>ദ്രേക്കാണം:</strong> {drekkana['rasi']} ദ്രേക്കാണം {drekkana['part']} ({drekkana['lord']})</div>
                <div><strong>ദ്വാദശാംശം:</strong> {dwadasamsa['rasi']} ({dwadasamsa['lord']})</div>
                <div><strong>തൃംശാംശം:</strong> {trimsamsa}</div>
            </div>
        </div>
        """
   
    html_output += "</div>"
    return html_output

def shad_varga_calculation(data):
    """app.py-യിൽ നിന്ന് വിളിക്കപ്പെടുന്ന പ്രധാന ഫങ്ഷൻ"""
    try:
        # Extract data from app.py request
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour_24h = data.get('hour_24h')
        minute = data.get('minute')
        place_data = data.get('place', {})
       
        print(f"🔍 Shad Varga calculation started:")
        print(f"   - Date: {day}/{month}/{year}")
        print(f"   - Time: {hour_24h}:{minute}")
        print(f"   - Place data type: {type(place_data)}")
        print(f"   - Place data: {place_data}")
       
        ayanamsa_mode = 1  # Default ayanamsa
       
        # ✅ പ്രധാന തിരുത്തൽ: app.py-ൽ നിന്ന് വന്ന ഡാറ്റയിൽ നിന്ന് കോർഡിനേറ്റുകൾ എടുക്കുക
        lat, lon, timezone_str = get_coordinates_from_app_data(place_data)
       
        print(f"📍 Coordinates obtained:")
        print(f"   - Lat: {lat}")
        print(f"   - Lon: {lon}")
        print(f"   - Timezone: {timezone_str}")

        # ✅ grahanila.py രീതിയിൽ സമയമേഖല അനുസരിച്ച് UTC-യിലേക്ക് മാറ്റുക
        utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(
            year, month, day, hour_24h, minute, 0, timezone_str
        )

        jd_ut = swe.julday(utc_year, utc_month, utc_day,
                          utc_hour + utc_minute/60.0 + utc_second/3600.0)

        print(f"   - Julian Day: {jd_ut}")
        print(f"   - UTC Time: {utc_hour}:{utc_minute}:{utc_second}")

        # Calculate regular planet positions with ayanamsa mode
        planets_data = calculate_planet_positions(jd_ut, lat, lon, ayanamsa_mode)
       
        print(f"   - Planets calculated: {len(planets_data)}")
        print(f"   - Lagna: {RASHI_NAMES[planets_data[0]['rasi_index']]} ({planets_data[0]['degree']:.2f}°)")

        # Calculate Shad Varga
        shad_varga_data = calculate_shad_varga(planets_data)
        shad_varga_html = create_shad_varga_display(shad_varga_data)

        # Create Rashi Chart
        rashi_chart_url = create_rashi_chart(planets_data, "രാശി", is_bhava=False)
       
        # Create Navamsa Chart
        navamsa_planets = []
        for planet in planets_data:
            navamsa_rashi = calculate_navamsa(planet['rasi_index'], planet['degree'])
            navamsa_planets.append({
                "name": planet['name'],
                "rasi_index": navamsa_rashi,
                "degree": planet['degree']
            })
       
        navamsa_chart_url = create_rashi_chart(navamsa_planets, "നവാംശകം", is_bhava=False)

        # Get place name for display
        if isinstance(place_data, dict):
            place_name = place_data.get('name', '')
        else:
            place_name = str(place_data)

        result_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ജാതക ചക്രം</title>
            <style>
                body {{
                    font-family: 'Noto Sans Malayalam', Arial, sans-serif;
                    background: #f8f5e6;
                    padding: 15px;
                    margin: 0;
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
                .shad-varga-container {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 10px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .info-section {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid #8B0000;
                }}
                .timezone-info {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    border-left: 4px solid #1565c0;
                }}
            </style>
        </head>
        <body>
            <div style="text-align: center; margin-bottom: 20px;">
                <div class="timezone-info">
                    <h3>സമയ വിവരങ്ങൾ</h3>
                    <p><strong>തീയതി:</strong> {day}/{month}/{year}</p>
                    <p><strong>സമയം:</strong> {hour_24h}:{minute:02d}</p>
                    <p><strong>സ്ഥലം:</strong> {place_name}</p>
                    <p><strong>ലഗ്നം:</strong> {RASHI_NAMES[planets_data[0]['rasi_index']]}</p>
                </div>
            </div>
           
            <div class="chart-container">
                <h3 style="color: #8B0000;">രാശി ചക്രം</h3>
                <img src="data:image/png;base64,{rashi_chart_url}" alt="രാശി ചക്രം" class="chart-image">
            </div>
           
            <div class="chart-container">
                <h3 style="color: #8B0000;">നവാംശക ചക്രം</h3>
                <img src="data:image/png;base64,{navamsa_chart_url}" alt="നവാംശക ചക്രം" class="chart-image">
            </div>

            {shad_varga_html}
           
            <div style="text-align: center;">
                <a href="javascript:history.back()" class="back-button">മടങ്ങുക</a>
            </div>
        </body>
        </html>
        """

        print(f"✅ Shad Varga calculation completed successfully")
        return result_html

    except Exception as e:
        print(f"❌ Error in shad_varga_calculation: {str(e)}")
        import traceback
        print(f"❌ Detailed error: {traceback.format_exc()}")
        error_html = f"""
        <div style="color: red; text-align: center; padding: 20px; max-width: 600px; margin: 0 auto;">
            <h3>പിശക്:</h3>
            <p>{str(e)}</p>
            <a href="javascript:history.back()" style="background: #8B4513; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">മടങ്ങുക</a>
        </div>
        """
        return error_html

# Initialize Swiss Ephemeris
swe.set_ephe_path('')
