from datetime import datetime, timedelta, date
import astral
from astral.sun import sun
import pytz

# (imports & root function name unchanged as requested)

# NOTE: We'll still keep an epoch constant for any fallback but primary logic will
# base Chaitra-1 on the Gregorian year (official Saka rule).
SHAKA_EPOCH = datetime(78, 3, 21)

# Shaka months template (Chaithra length will be adjusted per Gregorian leap)
SHAKA_MONTHS = [
    (30, 'ചൈത്രം'),
    (31, 'വൈശാഖം'),
    (31, 'ജ്യേഷ്ഠം'),
    (31, 'ആഷാഢം'),
    (31, 'ശ്രാവണം'),
    (31, 'ഭാദ്രപദം'),
    (30, 'ആശ്വിനം'),
    (30, 'കാർത്തികം'),
    (30, 'മാർഗശീർഷം'),
    (30, 'പൗഷം'),
    (30, 'മാഘം'),
    (30, 'ഫാൽഗുനം')
]

def is_gregorian_leap(gy):
    """Gregorian leap-year with century rules."""
    return (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)

def get_sunrise_time(latitude, longitude, timezone_str, date_):
    try:
        tz = pytz.timezone(timezone_str)
        obs = astral.Observer(latitude=latitude, longitude=longitude)
        s = sun(obs, date=date_, tzinfo=tz)
        return s['sunrise']
    except Exception as e:
        print(f"Error calculating sunrise: {e}")
        return None

def adjust_date_by_sunrise(latitude, longitude, timezone_str, input_date, input_time):
    try:
        tz = pytz.timezone(timezone_str)
        input_datetime = datetime.combine(input_date, input_time)
        local_datetime = tz.localize(input_datetime)
        sunrise_time = get_sunrise_time(latitude, longitude, timezone_str, input_date)

        if sunrise_time and local_datetime < sunrise_time:
            return input_date - timedelta(days=1)
        else:
            return input_date
    except Exception as e:
        print(f"Error adjusting date by sunrise: {e}")
        return input_date

def shakavarsham_calculation(data):
    """ശകവർഷം കണക്കാക്കുന്നു - app.py-യ്ക്കായി റൂട്ട് (imports & name unchanged)"""
    try:
        # parse inputs
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour_12h = int(data['hour_12h'])
        minute = int(data['minute'])
        ampm = str(data['ampm']).upper()
        place_data = data['place']
        latitude = place_data['lat']
        longitude = place_data['lng']
        timezone_str = place_data['timezone']

        # 12h -> 24h
        if ampm == 'PM' and hour_12h != 12:
            hour_24h = hour_12h + 12
        elif ampm == 'AM' and hour_12h == 12:
            hour_24h = 0
        else:
            hour_24h = hour_12h

        input_date = datetime.strptime(f"{year}-{month:02d}-{day:02d}", '%Y-%m-%d').date()
        time_obj = datetime.strptime(f"{hour_24h:02d}:{minute:02d}", '%H:%M').time()

        # apply sunrise-before adjustment
        adjusted_date = adjust_date_by_sunrise(latitude, longitude, timezone_str, input_date, time_obj)

        # Primary logic: determine Chaitra-1 for the relevant Gregorian year
        g_year = adjusted_date.year

        # Decide Chaitra1 for current Gregorian year (March 21 if leap, else March 22)
        if is_gregorian_leap(g_year):
            chaitra1 = date(g_year, 3, 21)
        else:
            chaitra1 = date(g_year, 3, 22)

        # If adjusted_date is on/after chaitra1 -> same Saka year = g_year - 78
        # else, use previous Gregorian year
        if adjusted_date >= chaitra1:
            saka_year = g_year - 78
            start_of_saka = chaitra1
            # chaitra_month_is_31 if current gregorian year is leap
            chaitra_is_31 = is_gregorian_leap(g_year)
        else:
            prev_g = g_year - 1
            if is_gregorian_leap(prev_g):
                chaitra1_prev = date(prev_g, 3, 21)
            else:
                chaitra1_prev = date(prev_g, 3, 22)
            saka_year = g_year - 79
            start_of_saka = chaitra1_prev
            chaitra_is_31 = is_gregorian_leap(prev_g)

        # day offset within Saka year (0-based)
        day_in_year = (adjusted_date - start_of_saka).days
        if day_in_year < 0:
            # safety fallback (shouldn't happen)
            day_in_year = 0

        # build months with Chaithra length adjusted
        months = SHAKA_MONTHS.copy()
        if chaitra_is_31:
            months[0] = (31, 'ചൈത്രം')
        else:
            months[0] = (30, 'ചൈത്രം')

        # find month index and day
        month_index = 0
        remaining = day_in_year
        for dm, name in months:
            if remaining < dm:
                break
            remaining -= dm
            month_index += 1

        # wrap safety
        if month_index >= len(months):
            # move into next saka year (rare edge)
            month_index = 0
            saka_year += 1
            remaining = 0

        shaka_month = months[month_index][1]
        shaka_day = remaining + 1

        # Final result
        return f"ശകവർഷം: {saka_year} {shaka_month} {shaka_day}"

    except Exception as e:
        return f"Error: {str(e)}"

