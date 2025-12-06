import swisseph as swe
from datetime import datetime
import pytz

# നക്ഷത്രങ്ങളുടെ ചാർട്ട്
NAKSHATRA_CHART = [
    {"name": "അശ്വതി", "start": 0, "end": 13.3333},
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
    {"name": "ചിത്ര", "start": 173.3333, "end": 186.6667},
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

def sun_nakshatra_calculation(data):
    """
    സൂര്യനക്ഷത്രം കണക്കാക്കുന്ന ഫംഗ്ഷൻ
    """
    try:
        # ഡാറ്റ വിശകലനം ചെയ്യുക
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour_24h = data['hour_24h']
        minute = int(data['minute'])
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        timezone_str = data['timezone']
        
        # സ്വിസ്സെഫ് സെറ്റപ്പ്
        swe.set_ephe_path('/usr/share/swisseph:/var/lib/swisseph')
        
        # ലോക്കൽ ടൈം യുടിസിയായി മാറ്റുക
        local_tz = pytz.timezone(timezone_str)
        local_dt = local_tz.localize(datetime(year, month, day, hour_24h, minute))
        utc_dt = local_dt.astimezone(pytz.utc)
        
        # ജൂലിയൻ ദിവസം കണക്കാക്കുക
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, 
                        utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
        
        # സൂര്യന്റെ സ്ഥാനം കണ്ടുപിടിക്കുക
        sun_position = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
        sun_longitude = sun_position[0][0]  # ദൈർഘ്യരേഖ
        
        # അയനാംശം കുറയ്ക്കുക (ലഹരി അയനാംശം)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        sun_longitude_nira = sun_longitude - ayanamsa
        
        # 360 ഡിഗ്രിക്കുള്ളിൽ എടുക്കുക
        if sun_longitude_nira < 0:
            sun_longitude_nira += 360.0
        if sun_longitude_nira >= 360.0:
            sun_longitude_nira -= 360.0
        
        # നക്ഷത്രം കണ്ടുപിടിക്കുക
        nakshatra_name = "അശ്വതി"  # ഡിഫോൾട്ട്
        for nakshatra in NAKSHATRA_CHART:
            if nakshatra['start'] <= sun_longitude_nira < nakshatra['end']:
                nakshatra_name = nakshatra['name']
                break
            # 360 ഡിഗ്രിക്ക് മുകളിലുള്ളവർക്ക്
            elif sun_longitude_nira >= 346.6667 and sun_longitude_nira < 360.0:
                nakshatra_name = "രേവതി"
                break
        
        result = f"സൂര്യനക്ഷത്രം (ഞാറ്റുവേല) : {nakshatra_name}"
        return result
        
    except Exception as e:
        print(f"❌ Error in sun_nakshatra_calculation: {str(e)}")
        return f"സൂര്യനക്ഷത്രം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"
