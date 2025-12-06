import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
import base64
import numpy as np
import swisseph as swe
from datetime import datetime, timedelta, timezone
import pytz
from flask import Flask, render_template_string, request
from astral import LocationInfo
from astral.sun import sun

app = Flask(__name__)

# ----- SHADVARGA ഫയലിൽ നിന്നും എടുത്ത ഭാഗം -----

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

# ഗ്രഹ പേരുകൾ - shadwarga.py ലെ രീതി തന്നെ
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

# ഓജ രാശികൾ
ODD_RASHIS = [0, 2, 4, 6, 8, 10]  # മേടം, മിഥുനം, ചിങ്ങം, തുലാം, ധനു, കുംഭം
# യുഗ്മ രാശികൾ
EVEN_RASHIS = [1, 3, 5, 7, 9, 11]  # ഇടവം, കർക്കടകം, കന്നി, വൃശ്ചികം, മകരം, മീനം

def get_coordinates(place_name):
    """സ്ഥലത്തിന്റെ അക്ഷാംശം, രേഖാംശം നൽകുന്നു"""
    places = {
        'കണ്ണൂർ': (11.8745, 75.3704),
        'തിരുവനന്തപുരം': (8.5241, 76.9366),
        'കൊച്ചി': (9.9312, 76.2673),
        'കോഴിക്കോട്': (11.2588, 75.7804),
        'തൃശൂർ': (10.5276, 76.2144),
        'ന്യൂയോർക്ക്': (40.7128, -74.0060)
    }
   
    # ഉപയോക്താവ് നൽകിയ സ്ഥലം കണ്ടെത്താൻ ശ്രമിക്കുക
    for name, coords in places.items():
        if place_name in name or name in place_name:
            return coords
   
    # കണ്ടില്ലെങ്കിൽ, ആദ്യത്തെ സ്ഥലത്തിന്റെ കോർഡിനേറ്റുകൾ തിരികെ നൽകുക
    return list(places.values())[0]

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
    swe.set_sid_mode(ayanamsa_mode)
   
    houses = swe.houses(jd_ut, lat, lon, b'P')
    lagna_longitude = houses[0][0]
   
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    nirayana_lagna = (lagna_longitude - ayanamsa) % 360
   
    return nirayana_lagna

def calculate_planet_degree(jd_ut, planet_code, ayanamsa_mode):
    """ഗ്രഹത്തിന്റെ ഡിഗ്രി കണക്കാക്കുക"""
    swe.set_sid_mode(ayanamsa_mode)
   
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    result = swe.calc_ut(jd_ut, planet_code, flags)
    longitude = result[0][0]
   
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    nirayana_longitude = (longitude - ayanamsa) % 360
   
    return nirayana_longitude

def calculate_planet_positions(jd_ut, lat, lon, ayanamsa_mode):
    """എല്ലാ ഗ്രഹങ്ങളുടെയും സ്ഥാനങ്ങൾ കണക്കാക്കുക - shadwarga.py ലെ രീതി തന്നെ"""
    planets = []
   
    # ലഗ്നം കണക്കാക്കുക
    lagna_degree = calculate_lagna(jd_ut, lat, lon, ayanamsa_mode)
    lagna_index = int(lagna_degree / 30)
    planets.append({"name": "ലഗ്നം", "rasi_index": lagna_index, "degree": lagna_degree})
   
    # മറ്റ് ഗ്രഹങ്ങൾ - shadwarga.py ലെ രീതി തന്നെ
    for planet_code, planet_name in PLANET_NAMES.items():
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

def create_rashi_chart(planets_data, chart_title="രാശി", is_bhava=False):
    """രാശി ചക്രം സൃഷ്ടിക്കുക"""
    # ഗ്രഹങ്ങളുടെ എണ്ണം അനുസരിച്ച് ചാർട്ട് സൈസ് നിർണ്ണയിക്കുക
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

# ----- ഗ്രഹഡിഗ്രി യുടെ യഥാർത്ഥ കോഡ് തുടരുന്നു -----

# ആയനാംശം ലഹിരി ഉപയോഗിക്കുക
swe.set_sid_mode(swe.SIDM_LAHIRI)
swe.set_ephe_path()

# ഗ്രഹങ്ങളുടെ പട്ടിക
PLANETS = {
    "ലഗ്നം": None,
    "സൂര്യൻ": swe.SUN,
    "ചന്ദ്രൻ": swe.MOON,
    "ചൊവ്വ": swe.MARS,
    "ബുധൻ": swe.MERCURY,
    "ഗുരു": swe.JUPITER,
    "ശുക്രൻ": swe.VENUS,
    "ശനി": swe.SATURN,
    "രാഹു": swe.MEAN_NODE,
    "കേതു": swe.TRUE_NODE,
}

RASHIS = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "സിംഹം", "കന്നി",
          "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"]

NAKSHATRAS = [
    "അശ്വതി", "ഭരണി", "കാർത്തിക", "രോഹിണി", "മകയിരം", "തിരുവാതിര",
    "പുണർതം", "പൂയം", "ആയില്യം", "മകം", "പൂരം", "ഉത്രം",
    "അത്തം", "ചിത്തിര", "ചോതി", "വിശാഖം", "അനിഴം", "തൃക്കേട്ട",
    "മൂലം", "പൂരാടം", "ഉത്രാടം", "തിരുവോണം", "അവിട്ടം", "ചതയം",
    "പൂരുരുട്ടാതി", "ഉത്രട്ടാതി", "രേവതി"
]

# ഗുളികൻ ഉദയ സമയങ്ങൾ (പകൽ)
DAY_GULIKA_TIMES = {
    0: timedelta(hours=8, minutes=48),   # തിങ്കൾ (Monday)
    1: timedelta(hours=7, minutes=12),   # ചൊവ്വ (Tuesday)
    2: timedelta(hours=5, minutes=36),   # ബുധൻ (Wednesday)
    3: timedelta(hours=4, minutes=0),    # വ്യാഴം (Thursday)
    4: timedelta(hours=2, minutes=24),   # വെള്ളി (Friday)
    5: timedelta(hours=0, minutes=48),   # ശനി (Saturday)
    6: timedelta(hours=10, minutes=24),  # ഞായർ (Sunday)
}

# ഗുളികൻ ഉദയ സമയങ്ങൾ (രാത്രി)
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

# മൗഢ്യം ഡിഗ്രി പരിധി
MAUDHYA_DEGREES = {
    "ചൊവ്വ": 17,
    "ബുധൻ": 13,
    "ഗുരു": 11,
    "ശുക്രൻ": 9,
    "ശനി": 15
}

# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ജ്യോതിഷ ഗണന</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Noto Sans Malayalam', 'Manjari', 'Rachana', sans-serif;
            background-color: #e8f4fd;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        input[type="date"],
        input[type="time"],
        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            background-color: #fff;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            font-weight: bold;
            margin-top: 10px;
        }
        button:hover {
            background-color: #2980b9;
        }
        @media (min-width: 768px) {
            .container {
                max-width: 600px;
                padding: 30px;
            }
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ജ്യോതിഷ ഗണന</h1>
        <form method="POST" action="/calculate">
            <div class="form-group">
                <label for="dob">ജനന തീയതി:</label>
                <input type="date" id="dob" name="dob" required>
            </div>
           
            <div class="form-group">
                <label for="tob">ജനന സമയം:</label>
                <input type="time" id="tob" name="tob" step="1" required>
            </div>
           
            <div class="form-group">
                <label for="place">സ്ഥലം:</label>
                <select id="place" name="place" required>
                    <option value="കണ്ണൂർ">കണ്ണൂർ</option>
                    <option value="തിരുവനന്തപുരം">തിരുവനന്തപുരം</option>
                    <option value="കൊച്ചി">കൊച്ചി</option>
                    <option value="കോഴിക്കോട്">കോഴിക്കോട്</option>
                    <option value="തൃശൂർ">തൃശൂർ</option>
                    <option value="ന്യൂയോർക്ക്">ന്യൂയോർക്ക്</option>
                </select>
            </div>
           
            <div class="form-group">
                <label for="lat">അക്ഷാംശം:</label>
                <input type="number" id="lat" name="lat" step="0.0001" required>
            </div>
           
            <div class="form-group">
                <label for="lon">രേഖാംശം:</label>
                <input type="number" id="lon" name="lon" step="0.0001" required>
            </div>
           
            <div class="form-group">
                <label for="tz_offset">സമയമേഖല:</label>
                <input type="text" id="tz_offset" name="tz_offset" value="+5:30" required>
            </div>
           
            <button type="submit">ഗണന നടത്തുക</button>
        </form>
    </div>
</body>
</html>
'''

RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ഗ്രഹസ്ഫുടങ്ങൾ</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Noto Sans Malayalam', 'Manjari', 'Rachana', sans-serif;
            background-color: #e8f4fd;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.8rem;
            font-weight: bold;
        }
        .result-header {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 1.1rem;
            font-weight: bold;
        }
        .planet-card {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #3498db;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .planet-name {
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .planet-details {
            font-size: 1.2rem;
            line-height: 1.8;
            font-weight: bold;
        }
        .planet-details strong {
            color: #2c3e50;
        }
        .gulika-card {
            background: linear-gradient(135deg, #fff3e0, #e8f5e8);
            border-left: 5px solid #e74c3c;
        }
        .back-button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 20px;
            background-color: #7f8c8d;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            text-align: center;
            width: 100%;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .back-button:hover {
            background-color: #636e72;
        }
        @media (min-width: 768px) {
            .container {
                max-width: 600px;
                padding: 20px;
            }
            h1 {
                font-size: 2.2rem;
            }
            .planet-name {
                font-size: 1.7rem;
            }
            .planet-details {
                font-size: 1.3rem;
            }
            .result-header {
                font-size: 1.2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ഗ്രഹസ്ഫുടങ്ങൾ</h1>
       
        <div class="result-header">
            <p><strong>ജനന വിവരങ്ങൾ:</strong></p>
            <p>തീയതി: {{ dob }} | സമയം: {{ tob }}</p>
            <p>സ്ഥലം: {{ place }}</p>
            <p>അക്ഷാംശം: {{ lat }} | രേഖാംശം: {{ lon }}</p>
        </div>

        {% for planet in planets %}
        <div class="planet-card">
            <div class="planet-name">{{ planet.name }}</div>
            <div class="planet-details">
                <strong>രാശി:</strong> {{ planet.rasi }}<br>
                <strong>ഭാഗ:</strong> {{ planet.degree }}<br>
                <strong>കല:</strong> {{ planet.minute }}<br>
                <strong>നക്ഷത്രം:</strong> {{ planet.nakshatra }} - {{ planet.pada }}<br>
                <strong>ഗതി:</strong> {{ planet.motion }}<br>
                {% if planet.maudhya is defined %}
                <strong>മൗഢ്യം:</strong> {{ planet.maudhya }}
                {% endif %}
            </div>
        </div>
        {% endfor %}

        {% if gulika_results %}
        <div class="planet-card gulika-card">
            <div class="planet-name">പകൽ ഗുളിക</div>
            <div class="planet-details">
                <strong>സമയം:</strong> {{ gulika_results.day_gulika_time }}<br>
                <strong>രാശി:</strong> {{ gulika_results.day_gulika_position.sign }}<br>
                <strong>ഭാഗ:</strong> {{ gulika_results.day_gulika_position.degrees }}<br>
                <strong>കല:</strong> {{ gulika_results.day_gulika_position.minutes }}<br>
                <strong>നക്ഷത്രം:</strong> {{ gulika_results.day_nakshatra }} - {{ gulika_results.day_pada }}
            </div>
        </div>

        <div class="planet-card gulika-card">
            <div class="planet-name">രാത്രി ഗുളിക</div>
            <div class="planet-details">
                <strong>സമയം:</strong> {{ gulika_results.night_gulika_time }}<br>
                <strong>രാശി:</strong> {{ gulika_results.night_gulika_position.sign }}<br>
                <strong>ഭാഗ:</strong> {{ gulika_results.night_gulika_position.degrees }}<br>
                <strong>കല:</strong> {{ gulika_results.night_gulika_position.minutes }}<br>
                <strong>നക്ഷത്രം:</strong> {{ gulika_results.night_nakshatra }} - {{ gulika_results.night_pada }}
            </div>
        </div>
        {% endif %}

        <a href="/" class="back-button">മുഖ്യ പേജിലേക്ക് മടങ്ങുക</a>
    </div>
</body>
</html>
'''

def degrees_to_dms(degrees):
    """ഡിഗ്രിയെ ഡിഗ്രി, മിനിറ്റ്, സെക്കൻഡ് ആക്കി മാറ്റുക"""
    degrees = abs(degrees)
    d = int(degrees)
    minutes_decimal = (degrees - d) * 60
    m = int(minutes_decimal)
    s = round((minutes_decimal - m) * 60, 2)
    return f"{d}° {m:02d}' {s:05.2f}\""

def get_nakshatra(longitude):
    """നക്ഷത്രം കണ്ടുപിടിക്കുക"""
    nakshatra_index = int(longitude / (360 / 27))
    remainder = longitude % (360 / 27)
    pada = int(remainder / (360 / 108)) + 1
    return NAKSHATRAS[nakshatra_index], pada

def correct_ist_to_utc(year, month, day, hour, minute, second):
    """IST (UTC+5:30) നെ UTC യാക്കി മാറ്റുക"""
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

def calculate_sunrise_sunset(date_obj, place):
    """ഉദയം, അസ്തമയം കണക്കാക്കുന്നു"""
    try:
        lat, lon = get_coordinates(place)
        loc = LocationInfo(place, "India", "Asia/Kolkata", lat, lon)
        s = sun(loc.observer, date=date_obj, tzinfo=loc.timezone)

        sunrise_time = s['sunrise'] + timedelta(minutes=3)
        sunset_time = s['sunset'] - timedelta(minutes=3)

        return sunrise_time, sunset_time
    except Exception as e:
        raise Exception(f"ഉദയം/അസ്തമയം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")

def minutes_to_vinazhika(minutes):
    """മിനിറ്റുകളെ വിനാഴികയാക്കി മാറ്റുന്നു"""
    return int(minutes * 2.5)

def vinazhika_to_minutes(vinazhika):
    """വിനാഴികയെ മിനിറ്റുകളാക്കി മാറ്റുന്നു"""
    return vinazhika / 2.5

def get_night_chart_weekday(weekday):
    """രാത്രി ഗുളികന് അഞ്ചാമത്തെ ദിവസത്തിന്റെ ചാർട്ട് ഉപയോഗിക്കുന്നു"""
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
    if not is_day:
        weekday = get_night_chart_weekday(weekday)
   
    chart = DAY_CORRECTION_CHARTS.get(weekday, {})
   
    if not chart:
        return 0
   
    closest_key = min(chart.keys(), key=lambda x: abs(x - vinazhika_value))
    return chart[closest_key]

def calculate_day_duration_difference(sunrise, sunset):
    """ദിനമാനത്തിന്റെ വ്യത്യാസം 12 മണിക്കൂറിൽ നിന്നും എത്ര മിനിറ്റ് കൂടി/കുറഞ്ഞു എന്ന് കണക്കാക്കുന്നു"""
    day_duration = sunset - sunrise
    twelve_hours = timedelta(hours=12)
    difference = day_duration - twelve_hours
    return difference.total_seconds() / 60

def calculate_corrected_gulika_time(sunrise, sunset, weekday, is_day=True):
    """തിരുത്തിയ ഗുളിക സമയം കണക്കാക്കുന്നു"""
    try:
        day_duration_diff_minutes = calculate_day_duration_difference(sunrise, sunset)
       
        diff_vinazhika = minutes_to_vinazhika(abs(day_duration_diff_minutes))
       
        correction_vinazhika = get_correction_from_chart(weekday, diff_vinazhika, is_day)
       
        correction_minutes = vinazhika_to_minutes(correction_vinazhika)
       
        if is_day:
            base_gulika_time = sunrise + DAY_GULIKA_TIMES[weekday]
           
            if day_duration_diff_minutes > 0:
                corrected_gulika_time = base_gulika_time + timedelta(minutes=correction_minutes)
            else:
                corrected_gulika_time = base_gulika_time - timedelta(minutes=correction_minutes)
        else:
            base_gulika_time = sunset + NIGHT_GULIKA_TIMES[weekday]
           
            if day_duration_diff_minutes > 0:
                corrected_gulika_time = base_gulika_time - timedelta(minutes=correction_minutes)
            else:
                corrected_gulika_time = base_gulika_time + timedelta(minutes=correction_minutes)
       
        return corrected_gulika_time, day_duration_diff_minutes, correction_vinazhika
       
    except Exception as e:
        raise Exception(f"തിരുത്തിയ ഗുളിക സമയം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")

def calculate_planet_position(datetime_obj, ayanamsa, place):
    """ലഗ്നം പോലെ ഗുളിക ഡിഗ്രി കണക്കാക്കാം"""
    try:
        if datetime_obj.tzinfo is None:
            local_tz = timezone(timedelta(hours=5, minutes=30))
            datetime_obj = datetime_obj.replace(tzinfo=local_tz)

        utc_dt = datetime_obj.astimezone(timezone.utc)

        jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                         utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)

        lat, lon = get_coordinates(place)

        cusps, ascmc = swe.houses(jd_ut, lat, lon)
        tropical_asc = ascmc[0] % 360.0

        swe.set_sid_mode(int(ayanamsa))
        ayanamsa_deg = swe.get_ayanamsa(jd_ut)

        sidereal_asc = (tropical_asc - ayanamsa_deg) % 360.0

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
            'longitude': sidereal_asc
        }
    except Exception as e:
        raise Exception(f"ഗ്രഹ/ലഗ്നം കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")

def calculate_planet_motion(jd_ut_current, jd_ut_previous, planet_id, ayanamsa):
    """രണ്ട് ദിവസത്തെ ഗ്രഹസ്ഥിതി താരതമ്യം ചെയ്ത് വക്രം/ക്രമം നിർണ്ണയിക്കുക"""
    try:
        # ഇന്നത്തെ ഗ്രഹസ്ഥിതി
        pos_current, retflag = swe.calc_ut(jd_ut_current, planet_id, swe.FLG_SWIEPH)
        lon_current = pos_current[0]
        nirayana_lon_current = (lon_current - ayanamsa) % 360
       
        # ഇന്നലത്തെ ഗ്രഹസ്ഥിതി
        pos_previous, retflag = swe.calc_ut(jd_ut_previous, planet_id, swe.FLG_SWIEPH)
        lon_previous = pos_previous[0]
        nirayana_lon_previous = (lon_previous - ayanamsa) % 360
       
        # ഗ്രഹം മുന്നോട്ട് പോകുന്നുണ്ടോ അതോ പിറകോട്ട് പോകുന്നുണ്ടോ എന്ന് പരിശോധിക്കുക
        diff = nirayana_lon_current - nirayana_lon_previous
       
        # 360 ഡിഗ്രി കടന്നുപോകുന്ന സാഹചര്യം കണക്കാക്കുക
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
           
        if diff > 0:
            return "ക്രമം"
        elif diff < 0:
            return "വക്രം"
        else:
            return "ക്രമം"  # സ്ഥിരം എന്നത് ക്രമം ആക്കി മാറ്റി
    except Exception as e:
        print(f"ഗ്രഹ ഗതി കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")
        return "ക്രമം"

def calculate_maudhya(sun_longitude, planet_longitude, planet_name):
    """ഗ്രഹത്തിന്റെ മൗഢ്യം നിർണ്ണയിക്കുക"""
    if planet_name not in MAUDHYA_DEGREES:
        return "no"
   
    maudhya_degree = MAUDHYA_DEGREES[planet_name]
   
    # സൂര്യനും ഗ്രഹത്തിനും ഇടയിലുള്ള ഡിഗ്രി വ്യത്യാസം കണക്കാക്കുക
    diff = abs(sun_longitude - planet_longitude)
   
    # 360 ഡിഗ്രി കടന്നുപോകുന്ന സാഹചര്യം കണക്കാക്കുക
    if diff > 180:
        diff = 360 - diff
   
    if diff <= maudhya_degree:
        return "yes"
    else:
        return "no"

def calculate_planet_positions_from_shadwarga(jd_ut, lat, lon, dob, tob, tz_offset):
    """shadwarga.py യിൽ നിന്നും ഗ്രഹനില കണക്കാക്കുന്ന രീതി ഉപയോഗിക്കുക"""
    # shadwarga.py ലെ രീതി ഉപയോഗിക്കുക
    ayanamsa_mode = 1  # Default ayanamsa
   
    # യഥാർത്ഥ grahadigri.py ലെ ഫോർമാറ്റ് ഉപയോഗിച്ച് ഡാറ്റ പ്രോസസ്സ് ചെയ്യുക
    planets_data = calculate_planet_positions(jd_ut, lat, lon, ayanamsa_mode)
   
    # grahadigri.py യുടെ ഫോർമാറ്റിലേക്ക് മാറ്റുക
    planet_positions = []
   
    for planet in planets_data:
        name = planet['name']
        degree = planet['degree']
        rasi_index = planet['rasi_index']
       
        # ഡിഗ്രി മാറ്റുക
        degree_in_rasi = degree % 30
        deg = int(degree_in_rasi)
        min_val = int((degree_in_rasi - deg) * 60)
        sec_val = round(((degree_in_rasi - deg) * 60 - min_val) * 60)
       
        # നക്ഷത്രം കണക്കാക്കുക
        nakshatra, pada = get_nakshatra(degree)
       
        # ഗ്രഹ ഗതി (temporary - പിന്നീട് കണക്കാക്കാം)
        motion = "ക്രമം"
       
        planet_info = {
            'name': name,
            'rasi': RASHIS[rasi_index],
            'motion': motion,
            'nakshatra': nakshatra,
            'pada': pada,
            'rasi_index': rasi_index,
            'degree': deg,
            'minute': min_val,
            'second': sec_val,
            'longitude': degree
        }
       
        # മൗഢ്യം (ഗ്രഹങ്ങൾക്ക് മാത്രം)
        if name in MAUDHYA_DEGREES:
            # സൂര്യന്റെ ഡിഗ്രി കണ്ടെത്തുക
            sun_degree = None
            for p in planets_data:
                if p['name'] == 'സൂര്യൻ':
                    sun_degree = p['degree']
                    break
           
            if sun_degree:
                maudhya = calculate_maudhya(sun_degree, degree, name)
                planet_info['maudhya'] = maudhya
       
        planet_positions.append(planet_info)
   
    return {
        'planets': planet_positions,
        'ayanamsa': 24.0 + 12.0/60.0 + 57.0/3600.0  # Fixed ayanamsa
    }

def calculate_gulika_degrees(dob, tob, place):
    """ഗുളിക ഡിഗ്രി കണക്കാക്കുക"""
    try:
        year, month, day = map(int, dob.split("-"))
        time_parts = tob.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
       
        selected_datetime = datetime(year, month, day, hour, minute, second)
        weekday = selected_datetime.weekday()
       
        sunrise, sunset = calculate_sunrise_sunset(selected_datetime.date(), place)
       
        day_gulika_time, day_duration_diff, day_correction_vinazhika = calculate_corrected_gulika_time(
            sunrise, sunset, weekday, is_day=True)
        night_gulika_time, night_duration_diff, night_correction_vinazhika = calculate_corrected_gulika_time(
            sunrise, sunset, weekday, is_day=False)

        day_gulika_position = calculate_planet_position(day_gulika_time, '1', place)
        night_gulika_position = calculate_planet_position(night_gulika_time, '1', place)
       
        # ഗുളികന്റെ നക്ഷത്രം കണക്കാക്കുക
        day_nakshatra, day_pada = get_nakshatra(day_gulika_position['longitude'])
        night_nakshatra, night_pada = get_nakshatra(night_gulika_position['longitude'])
       
        return {
            'day_gulika_time': day_gulika_time.strftime('%Y-%m-%d %H:%M:%S'),
            'night_gulika_time': night_gulika_time.strftime('%Y-%m-%d %H:%M:%S'),
            'day_gulika_position': day_gulika_position,
            'night_gulika_position': night_gulika_position,
            'day_nakshatra': day_nakshatra,
            'day_pada': day_pada,
            'night_nakshatra': night_nakshatra,
            'night_pada': night_pada,
            'day_duration_diff': day_duration_diff,
            'night_duration_diff': night_duration_diff
        }
    except Exception as e:
        print(f"ഗുളിക ഡിഗ്രി കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    dob = request.form['dob']
    tob = request.form['tob']
    place = request.form['place']
    lat = float(request.form['lat'])
    lon = float(request.form['lon'])
    tz_offset = request.form['tz_offset']
   
    year, month, day = map(int, dob.split("-"))
    time_parts = tob.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
    second = int(time_parts[2]) if len(time_parts) > 2 else 0
   
    # ✅ പുതിയത്: correct_to_utc() ഫംഗ്ഷൻ ഉപയോഗിക്കുക
    # സമയമേഖല കണ്ടെത്തുക (പ്ലേസ് അനുസരിച്ച്)
    timezone_str = 'Asia/Kolkata'  # ഡിഫോൾട്ട്
    if place == 'ന്യൂയോർക്ക്':
        timezone_str = 'America/New_York'
    elif place in ['കൊച്ചി', 'കോഴിക്കോട്', 'തൃശൂർ', 'കണ്ണൂർ', 'തിരുവനന്തപുരം']:
        timezone_str = 'Asia/Kolkata'
    
    utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(
        year, month, day, hour, minute, second, timezone_str
    )
   
    jd_ut = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0 + utc_second/3600.0)
   
    # shadwarga.py രീതി ഉപയോഗിച്ച് ഗ്രഹനില കണക്കാക്കുക
    results = calculate_planet_positions_from_shadwarga(jd_ut, lat, lon, dob, tob, tz_offset)
   
    gulika_results = calculate_gulika_degrees(dob, tob, place)
   
    ayanamsa_display = degrees_to_dms(results['ayanamsa'])
   
    return render_template_string(RESULT_TEMPLATE,
                                dob=dob, tob=tob, place=place,
                                lat=lat, lon=lon, tz_offset=tz_offset,
                                planets=results['planets'],
                                ayanamsa_display=ayanamsa_display,
                                gulika_results=gulika_results)

def graha_sphutam_calculation(data):
    """ഗ്രഹസ്ഫുടങ്ങൾ കണക്കാക്കുന്ന ഫങ്ഷൻ"""
    try:
        # Extract data
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour_24h = data.get('hour_24h')
        minute = data.get('minute')
        place = data.get('place')
       
        # Format date and time for grahadigri
        dob = f"{year}-{month:02d}-{day:02d}"
        tob = f"{hour_24h:02d}:{minute:02d}:00"
       
        # Prepare data for grahadigri calculation
        lat = place.get('lat', 11.8745)
        lon = place.get('lng', 75.3704)
        timezone_str = place.get('timezone', 'Asia/Kolkata')
       
        # ✅ പുതിയത്: correct_to_utc() ഫംഗ്ഷൻ ഉപയോഗിക്കുക
        utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(
            year, month, day, hour_24h, minute, 0, timezone_str
        )
       
        jd_ut = swe.julday(utc_year, utc_month, utc_day, utc_hour + utc_minute/60.0 + utc_second/3600.0)
       
        # shadwarga.py രീതി ഉപയോഗിച്ച് ഗ്രഹനില കണക്കാക്കുക
        results = calculate_planet_positions_from_shadwarga(jd_ut, lat, lon, dob, tob, timezone_str)
       
        # Calculate gulika degrees
        gulika_results = calculate_gulika_degrees(dob, tob, place.get('name', 'കണ്ണൂർ'))
       
        # Render result
        return render_template_string(RESULT_TEMPLATE,
                                    dob=dob, tob=tob, place=place.get('name', 'കണ്ണൂർ'),
                                    lat=lat, lon=lon, tz_offset=timezone_str,
                                    planets=results['planets'],
                                    ayanamsa_display=degrees_to_dms(results['ayanamsa']),
                                    gulika_results=gulika_results)
       
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>പിശക്</title></head>
        <body>
            <h1>പിശക്</h1>
            <p>ഗ്രഹസ്ഫുടങ്ങൾ കണക്കാക്കുന്നതിൽ പിശക്: {str(e)}</p>
            <a href="/">മുഖ്യ പേജിലേക്ക് മടങ്ങുക</a>
        </body>
        </html>
        """
        return error_html

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
