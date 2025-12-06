from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import math

def nazhika_calculation(data):
    """സമയം നാഴിക-വിനാഴികയായി മാറ്റുക"""
    try:
        # ഡാറ്റ എക്സ്ട്രാക്റ്റ് ചെയ്യുക
        year = data['year']
        month = data['month']
        day = data['day']
        hour_24h = data['hour_24h']
        minute = data['minute']
        place = data['place']
        
        # datetime object സൃഷ്ടിക്കുക
        dt = datetime(year, month, day, hour_24h, minute)
        
        # സ്ഥലം എക്സ്ട്രാക്റ്റ് ചെയ്യുക
        place_name = place['name']
        lat = place['lat']
        lon = place['lng']
        tz = place['timezone']
        
        # ഉദയം-അസ്തമയം കണക്കാക്കുക
        loc = LocationInfo(place_name, "India", tz, lat, lon)
        s = sun(loc.observer, date=dt.date(), tzinfo=tz)
        
        sunrise = s['sunrise'].replace(tzinfo=None) + timedelta(minutes=3)
        sunset = s['sunset'].replace(tzinfo=None) - timedelta(minutes=3)
        
        # സമയം നാഴിക-വിനാഴികയായി മാറ്റുക
        nazhika, vinazhika, period = convert_to_nazhika_vinazhika(dt, sunrise, sunset)
        
        # ഫോർമാറ്റ് ചെയ്ത റിസൾട്ട് തിരികെ നൽകുക
        if nazhika == 0:
            result_text = f"{period} {vinazhika} വിനാഴിക"
        else:
            result_text = f"{period} {nazhika} നാഴിക {vinazhika} വിനാഴിക"
            
        return f"ജനന സമയം: {result_text}"
        
    except Exception as e:
        print(f"❌ Error in nazhika calculation: {str(e)}")
        return f"ജനന സമയം: കണക്കാക്കാനായില്ല"

def convert_to_nazhika_vinazhika(dt, sunrise, sunset):
    """സമയം നാഴിക-വിനാഴികയായി മാറ്റുക"""
    # സെക്കൻഡുകളിൽ സമയ വ്യത്യാസം കണക്കാക്കുക
    total_seconds = 0
    period = ""
    
    if sunrise <= dt <= sunset:  # പകൽ സമയം
        time_diff = dt - sunrise
        total_seconds = time_diff.total_seconds()
        period = "ഉദയാൽപരം"
        
        # 4 PM ന് ശേഷം അസ്തമയത്തിന് മുമ്പ്
        if dt.time().hour >= 16 and dt < sunset:
            time_diff = sunset - dt
            total_seconds = time_diff.total_seconds()
            period = "അസ്തമനാൽപൂർവ്വം"
    else:  # രാത്രി സമയം
        if dt < sunrise:  # ഉദയത്തിന് മുമ്പ്
            time_diff = sunrise - dt
            total_seconds = time_diff.total_seconds()
            period = "ഉദയാൽപൂർവ്വം"
        else:  # അസ്തമയത്തിന് ശേഷം
            time_diff = dt - sunset
            total_seconds = time_diff.total_seconds()
            period = "അസ്തമനാൽപരം"
    
    # സെക്കൻഡുകളെ നാഴിക-വിനാഴികയാക്കി മാറ്റുക
    # 1 നാഴിക = 24 മിനിറ്റ് = 1440 സെക്കൻഡ്
    # 1 വിനാഴിക = 24 സെക്കൻഡ്
    total_nazhika = total_seconds / 1440
    nazhika = int(total_nazhika)
    remaining_seconds = total_seconds - (nazhika * 1440)
    vinazhika = int(remaining_seconds / 24)
    
    # കല (12 സെക്കൻഡ്) വന്നാൽ വിനാഴിക ഒന്ന് കൂട്ടുക
    if (remaining_seconds - (vinazhika * 24)) >= 12:
        vinazhika += 1
        if vinazhika >= 60:
            nazhika += 1
            vinazhika = 0
    
    return nazhika, vinazhika, period
