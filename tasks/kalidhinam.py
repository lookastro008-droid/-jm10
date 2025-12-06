from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz

# കലിദിനം ആരംഭിക്കുന്ന തീയതി: 2025 സെപ്റ്റംബർ 20 (കലിദിനം 1872473)
KALI_EPOCH = datetime(2025, 9, 20)
KALI_EPOCH_DAY = 1872473

def get_sunrise_time(date, latitude, longitude, timezone_str):
    """ലോക്കൽ ടൈം ഉദയം കണക്കാക്കുക"""
    try:
        # LocationInfo ക്രിയേറ്റ് ചെയ്യുക
        location = LocationInfo(
            name="Place",
            region="Region",
            timezone=timezone_str,
            latitude=latitude,
            longitude=longitude
        )
       
        # ടൈംസോൺ എടുക്കുക
        tz = pytz.timezone(timezone_str)
       
        # ദിവസം ലോക്കൽ ടൈംസോണിൽ ലോക്കലൈസ് ചെയ്യുക
        local_date = tz.localize(datetime.combine(date, datetime.min.time()))
       
        # ഉദയം കണക്കാക്കുക
        s = sun(location.observer, date=local_date)
        sunrise = s['sunrise']
       
        # ടൈംസോണിലേക്ക് മാറ്റുക
        sunrise = sunrise.astimezone(tz)
       
        print(f"🌅 Sunrise calculated: {sunrise}")
        return sunrise
       
    except Exception as e:
        print(f"❌ Error calculating sunrise: {e}")
        # എറർ ആയാൽ 6:00 AM എന്ന് എടുക്കുക, പക്ഷേ timezone ഉള്ളതാക്കുക
        tz = pytz.timezone(timezone_str)
        default_time = tz.localize(datetime.combine(date, datetime.min.time()).replace(hour=6, minute=0, second=0, microsecond=0))
        print(f"🌅 Using default sunrise: {default_time}")
        return default_time

def calculate_kali_day_with_sunrise(english_date_str, time_str, latitude, longitude, timezone_str):
    """ഉദയം കണക്കിലെടുത്ത് കലിദിനം കണക്കാക്കുക"""
    try:
        print(f"📅 Calculating kali day for: {english_date_str} {time_str}")
        print(f"📍 Location: {latitude}, {longitude}, Timezone: {timezone_str}")
       
        # ഇൻപുട്ട് തീയതിയും സമയവും പാഴ്സ് ചെയ്യുക
        input_datetime = datetime.strptime(f'{english_date_str} {time_str}', '%Y-%m-%d %H:%M')
       
        # ടൈംസോൺ എടുക്കുക ഇൻപുട്ട് datetime-ഉം timezone aware ആക്കുക
        tz = pytz.timezone(timezone_str)
        input_datetime = tz.localize(input_datetime)
       
        # ഉദയം കണക്കാക്കുക
        sunrise_time = get_sunrise_time(input_datetime.date(), latitude, longitude, timezone_str)
       
        print(f"⏰ Input time: {input_datetime}")
        print(f"🌅 Sunrise time: {sunrise_time}")
        print(f"🔍 Before sunrise: {input_datetime < sunrise_time}")
       
        # ഉദയത്തിന് മുമ്പോ ശേഷമോ എന്ന് പരിശോധിക്കുക
        if input_datetime < sunrise_time:
            # ഉദയത്തിന് മുമ്പ് - തലേ ദിവസത്തെ കലിദിനം
            previous_day = input_datetime - timedelta(days=1)
            kali_date_str = previous_day.strftime('%Y-%m-%d')
            print(f"📆 Using previous day: {kali_date_str}")
        else:
            # ഉദയത്തിന് ശേഷം - അന്നത്തെ കലിദിനം
            kali_date_str = english_date_str
            print(f"📆 Using same day: {kali_date_str}")
       
        # കലിദിനം കണക്കാക്കുക
        kali_result = calculate_kali_date(kali_date_str)
       
        if kali_result['success']:
            return {
                'success': True,
                'kali_day': kali_result['kali_day']
            }
        else:
            return {'success': False, 'error': kali_result['error']}
       
    except Exception as e:
        print(f"❌ Error in calculate_kali_day_with_sunrise: {str(e)}")
        return {'success': False, 'error': str(e)}

def calculate_kali_date(english_date):
    """ഇംഗ്ലീഷ് തീയതിയെ കലിദിനമായി മാറ്റുക"""
    try:
        # ഇൻപുട്ട് തീയതി
        input_date = datetime.strptime(english_date, '%Y-%m-%d')
       
        # 2025 സെപ്റ്റംബർ 20 മുതലുള്ള വ്യത്യാസം (ദിവസങ്ങളിൽ)
        delta_days = (input_date - KALI_EPOCH).days
       
        # കലിദിനം കണക്കാക്കുക
        kali_day = KALI_EPOCH_DAY + delta_days
       
        print(f"🔢 Kali date calculation:")
        print(f"   - Input: {english_date}")
        print(f"   - Days since epoch: {delta_days}")
        print(f"   - Kali day: {kali_day}")
       
        return {
            'success': True,
            'kali_day': kali_day
        }
       
    except Exception as e:
        print(f"❌ Error in calculate_kali_date: {str(e)}")
        return {'success': False, 'error': str(e)}

def kalidhinam_calculation(data):
    """App.py-യിൽ നിന്ന് വിളിക്കപ്പെടുന്ന പ്രധാന ഫംഗ്ഷൻ"""
    try:
        print(f"🚀 STARTING KALIDHINAM CALCULATION")
        print(f"📊 Input data: {data}")
       
        # ഡേറ്റാ വിവരങ്ങൾ എടുക്കുക
        year = data['year']
        month = data['month']
        day = data['day']
        hour_24h = data['hour_24h']
        minute = data['minute']
        latitude = data['latitude']
        longitude = data['longitude']
        timezone = data['timezone']
       
        print(f"📍 Calculation details:")
        print(f"   - Date: {day}/{month}/{year}")
        print(f"   - Time: {hour_24h}:{minute:02d}")
        print(f"   - Location: {latitude}, {longitude}")
        print(f"   - Timezone: {timezone}")
       
        # ഇംഗ്ലീഷ് ഡേറ്റ് സ്ട്രിംഗ് തയ്യാറാക്കുക
        english_date = f"{year}-{month:02d}-{day:02d}"
        time_str = f"{hour_24h:02d}:{minute:02d}"
       
        # ഉദയം കണക്കിലെടുത്ത് കലിദിനം കണക്കാക്കുക
        result = calculate_kali_day_with_sunrise(
            english_date,
            time_str,
            latitude,
            longitude,
            timezone
        )
       
        if result['success']:
            final_result = f"കലിദിനം - {result['kali_day']}"
            print(f"✅ KALIDHINAM RESULT: {final_result}")
            return final_result
        else:
            error_msg = f"കലിദിനം: കണക്കാക്കാനായില്ല - {result['error']}"
            print(f"❌ KALIDHINAM ERROR: {error_msg}")
            return error_msg
           
    except Exception as e:
        error_msg = f"കലിദിനം: കണക്കാക്കാനായില്ല - {str(e)}"
        print(f"💥 KALIDHINAM EXCEPTION: {error_msg}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return error_msg
