import swisseph as swe

from datetime import datetime, timedelta

import pytz

# Nakshatra table (start longitudes in sidereal degrees)

NAKSHATRAS = [

    ("അശ്വതി", 0.0), ("ഭരണി", 13.3333333333), ("രോഹിണി", 26.6666666667), ("മകയിരം", 40.0),

    ("തിരുവാതിര", 53.3333333333), ("പുണർതം", 66.6666666667), ("പൂയ്യം", 80.0), ("ആയില്യം", 93.3333333333),

    ("മകം", 106.6666666667), ("പൂരുമി", 120.0), ("അർധപൂരം", 133.3333333333), ("ഉത്രം", 146.6666666667),

    ("അത്തം", 160.0), ("ചിതിര", 173.3333333333), ("ചോതി", 186.6666666667), ("വിശാഖം", 200.0),

    ("അനിഴം", 213.3333333333), ("കേട്ട", 226.6666666667), ("മൂലം", 240.0), ("പൂരാടം", 253.3333333333),

    ("ഉത്രാടം", 266.6666666667), ("തിരുവോണം", 280.0), ("അവിട്ടം", 293.3333333333), ("ചതയം", 306.6666666667),

    ("പൂരുത്താതി", 320.0), ("ഉത്രട്ടാതി", 333.3333333333), ("രേവതി", 346.6666666667)

]

# Vimshottari Dasha order — starting from Ketu as per list position mapping

DASHA_ORDER = [

    ("കേതു", 7), ("ശുക്രൻ", 20), ("രവി", 6), ("ചന്ദ്രൻ", 10), ("കുജൻ", 7),

    ("രാഹു", 18), ("ഗുരു", 16), ("ശനി", 19), ("ബുധൻ", 17)

]

# Sidereal year constant (days)

SIDEREAL_YEAR_DAYS = 365.258756


def get_nakshatra(moon_long_sid):

    span = 13.3333333333

    for i, (name, start) in enumerate(NAKSHATRAS):

        if start <= moon_long_sid < start + span:

            return i, name, start, start + span

    return 0, NAKSHATRAS[0][0], NAKSHATRAS[0][1], NAKSHATRAS[0][1] + span


def years_to_ymd_sidereal(years_float):

    total_days = years_float * SIDEREAL_YEAR_DAYS

    years = int(total_days // SIDEREAL_YEAR_DAYS)

    rem_days = total_days - (years * SIDEREAL_YEAR_DAYS)

    month_length = SIDEREAL_YEAR_DAYS / 12.0

    months = int(rem_days // month_length)

    days = rem_days - (months * month_length)

    days_int = int(round(days))

    if days_int >= int(round(month_length)):

        days_int -= int(round(month_length))

        months += 1

    if months >= 12:

        months -= 12

        years += 1

    return years, months, days_int


def shishtadhasha_calculation(data):

    try:

        year = int(data['year'])

        month = int(data['month'])

        day = int(data['day'])

        hour_24h = int(data['hour_24h'])

        minute = int(data['minute'])

        latitude = float(data['latitude'])

        longitude = float(data['longitude'])

        timezone_str = data['timezone']

        tz = pytz.timezone(timezone_str)

        dt_local = datetime(year, month, day, hour_24h, minute)

        dt_local = tz.localize(dt_local)

        dt_utc = dt_local.astimezone(pytz.utc)

        ut_hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0

        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, ut_hour)

        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        ayanamsa = swe.get_ayanamsa(jd)

        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0]

        moon_long_sidereal = (moon_pos[0] - ayanamsa) % 360.0

        idx, nak_name, start_long, end_long = get_nakshatra(moon_long_sidereal)

        lord_index = idx % 9

        lord_name, dasha_full_years = DASHA_ORDER[lord_index]

        span = 13.3333333333

        progressed = (moon_long_sidereal - start_long) % 360.0

        if progressed > span:

            progressed = span

        fraction_left = 1.0 - (progressed / span)

        balance_years = dasha_full_years * fraction_left

        y, m, d = years_to_ymd_sidereal(balance_years)

        # >>>>>>>>>> YOUR REQUESTED SIMPLE OUTPUT <<<<<<<<<<

        result = f"ശിഷ്ടദശ: {y} വർഷം {m} മാസം {d} ദിവസം  {lord_name}"

        return result

    except Exception as e:

        return f"ശിഷ്ടദശ: കണക്കുകൂട്ടൽ പിശക് - {str(e)}"


