from datetime import datetime, timedelta
import pytz
import swisseph as swe

# Nakshatra table (13.3333° each)
NAKSHATRAS = [
    ("അശ്വതി", 0), ("ഭരണി", 13.3333), ("കാർത്തിക", 26.6667), ("രോഹിണി", 40.0),
    ("മകയിരം", 53.3333), ("തിരുവാതിര", 66.6667), ("പുണർതം", 80.0), ("പൂയ്യം", 93.3333),
    ("ആയില്യം", 106.6667), ("മകം", 120.0), ("പൂരം", 133.3333), ("ഉത്രം", 146.6667),
    ("അത്തം", 160.0), ("ചിതിര", 173.3333), ("ചോതി", 186.6667), ("വിശാഖം", 200.0),
    ("അനിഴം", 213.3333), ("കേട്ട", 226.6667), ("മൂലം", 240.0), ("പൂരാടം", 253.3333),
    ("ഉത്രാടം", 266.6667), ("തിരുവോണം", 280.0), ("അവിട്ടം", 293.3333), ("ചതയം", 306.6667),
    ("പൂരുറുട്ടാതി", 320.0), ("ഉത്രട്ടാതി", 333.3333), ("രേവതി", 346.6667)
]

# Vimshottari Dasha order (lord, years)
DASHA_ORDER = [
    ("കേതു", 7), ("ശുക്രൻ", 20), ("രവി", 6), ("ചന്ദ്രൻ", 10), ("കുജൻ", 7),
    ("രാഹു", 18), ("ഗുരു", 16), ("ശനി", 19), ("ബുധൻ", 17)
]

def get_nakshatra(moon_long):
    for i, (name, start) in enumerate(NAKSHATRAS):
        end = start + 13.3333
        if start <= moon_long < end:
            return i, name, start, end
    return 0, "അശ്വതി", 0, 13.3333

def years_to_ymd(years_float):
    """Convert decimal years to years, months, days (approx using 365.25 & 30-day months)."""
    total_days = int(round(years_float * 365.25))
    years = total_days // 365
    rem_days = total_days % 365
    months = rem_days // 30
    days = rem_days % 30
    return years, months, days

def get_current_dasha_antar_chidra(dasha_sequence, now):
    """ഇപ്പോഴത്തെ ദശ, അപഹാരം, ചിദ്രം കണ്ടെത്തുക"""
    current_dasha = None
    current_antar = None
    current_chidra = None
   
    for dasha in dasha_sequence:
        if dasha['start'] <= now <= dasha['end']:
            current_dasha = dasha['lord']
            for antar in dasha['antar']:
                if antar['start'] <= now <= antar['end']:
                    current_antar = antar['lord']
                    for chidra in antar['pratyantar']:
                        if chidra['start'] <= now <= chidra['end']:
                            current_chidra = chidra['lord']
                            break
                    break
            break
   
    return current_dasha, current_antar, current_chidra

def generate_sequential_dashas(nak_start_time, lord_index, dasha_full_years, birth_dt, max_years=90):
    """
    Generate sequential major dashas starting from nak_start_time (nakshatra start time).
    But for display purposes, we'll adjust the first dasha to show birth date in the button.
    """
    sequence = []
    cur_dt = nak_start_time
    years_accum = 0.0

    # We'll iterate through lords cyclically starting at lord_index
    idx = lord_index
    first = True
   
    while years_accum < max_years:
        lord_name, lord_years = DASHA_ORDER[idx % 9]
       
        # For the first dasha, use the full dasha years but calculate end from nak_start_time
        if first:
            use_years = dasha_full_years
            first = False
        else:
            use_years = lord_years

        start = cur_dt
        # keep fractional days (no int()) so segments chain exactly
        end = start + timedelta(days=(use_years * 365.25))
        years_accum += use_years

        # build antardashas proportional to 120-year base
        antar_list = []
        antar_cur = start
        for a_idx in range(9):
            a_lord, a_years = DASHA_ORDER[(idx + a_idx) % 9]
            antar_len_years = use_years * (a_years / 120.0)
            antar_end = antar_cur + timedelta(days=(antar_len_years * 365.25))

            # pratyantar (chidra)
            praty_list = []
            praty_cur = antar_cur
            for p_idx in range(9):
                p_lord, p_years = DASHA_ORDER[( (idx + a_idx) + p_idx ) % 9]
                praty_len = antar_len_years * (p_years / 120.0)
                praty_end = praty_cur + timedelta(days=(praty_len * 365.25))
                praty_list.append({
                    "lord": p_lord,
                    "start": praty_cur,
                    "end": praty_end
                })
                praty_cur = praty_end

            antar_list.append({
                "lord": a_lord,
                "start": antar_cur,
                "end": antar_end,
                "pratyantar": praty_list
            })
            antar_cur = antar_end

        sequence.append({
            "lord": lord_name,
            "years": use_years,
            "start": start,
            "end": end,
            "antar": antar_list,
            "nak_start_time": nak_start_time,
            "birth_dt": birth_dt
        })

        cur_dt = end
        idx += 1

        # safety guard: break if same start==end (zero length)
        if (end - start).days <= 0:
            break

        # if we've generated beyond max_years from initial start, stop
        if (cur_dt - nak_start_time).days > max_years * 365:
            break

    return sequence

def livedhasha_calculation(data):
    """
    Main function to calculate dasha periods based on birth data
    Expected data format:
    {
        'year': int, 'month': int, 'day': int,
        'hour_24h': int, 'minute': int,
        'latitude': float, 'longitude': float,
        'timezone': str
    }
    """
    # Extract data
    year = data['year']
    month = data['month']
    day = data['day']
    hour_24h = data['hour_24h']
    minute = data['minute']
    lat = data['latitude']
    lon = data['longitude']
    tz_str = data['timezone']

    # Create datetime object
    tz = pytz.timezone(tz_str)
    dt_local = tz.localize(datetime(year, month, day, hour_24h, minute))
    dt_utc = dt_local.astimezone(pytz.utc)

    # Julian Day
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                    dt_utc.hour + dt_utc.minute/60.0)

    # set sidereal (Lahiri) and get ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa(jd)

    # moon position (tropical) and convert to sidereal
    moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    moon_long_tropical = moon_pos[0] % 360
    moon_long_sidereal = (moon_long_tropical - ayanamsa) % 360

    # nakshatra and its start/end longitudes
    idx, nak_name, start_long, end_long = get_nakshatra(moon_long_sidereal)

    # dasha lord index (Vimshottari sequence starts from Ketu at 0 position)
    lord_index = idx % 9
    lord_name, dasha_full_years = DASHA_ORDER[lord_index]

    # compute fraction left (shishtadasha) using position inside nakshatra
    span = 13.3333  # നക്ഷത്രത്തിന്റെ മൊത്തം വീതി
    progressed = moon_long_sidereal - start_long  # നക്ഷത്രത്തിൽ ചന്ദ്രൻ പ്രവേശിച്ച ഡിഗ്രി
    fraction_done = progressed / span
    fraction_left = 1.0 - fraction_done
    balance_years = dasha_full_years * fraction_left

    # Calculate nakshatra start time more accurately
    nak_duration_days = dasha_full_years * 365.25
    nak_elapsed_days = fraction_done * nak_duration_days
    nak_start_time = dt_local - timedelta(days=nak_elapsed_days)

    # Generate sequential dashas starting from nakshatra start time
    dasha_sequence = generate_sequential_dashas(nak_start_time, lord_index, dasha_full_years, dt_local, max_years=90)

    # Get current time
    now = datetime.now(pytz.timezone(tz_str))

    # Find current dasha, antar, and chidra
    current_dasha, current_antar, current_chidra = get_current_dasha_antar_chidra(dasha_sequence, now)

    # Find period details
    dasha_start = dasha_end = dasha_years = None
    antar_start = antar_end = None
    chidra_start = chidra_end = None

    for d in dasha_sequence:
        if d['start'] <= now <= d['end']:
            dasha_start, dasha_end, dasha_years = d['start'], d['end'], d.get('years', None)
            for a in d['antar']:
                if a['start'] <= now <= a['end']:
                    antar_start, antar_end = a['start'], a['end']
                    for p in a['pratyantar']:
                        if p['start'] <= now <= p['end']:
                            chidra_start, chidra_end = p['start'], p['end']
                            break
                    break
            break

    # Format dates
    def fmt(dt):
        if not dt:
            return ""
        return dt.strftime("%d/%m/%Y")

    def years_label(y):
        if y is None:
            return ""
        try:
            yi = int(round(float(y)))
            return f"{yi} വർഷം"
        except:
            return f"{y} വർഷം"

    # Build result with HTML formatting and dark borders
    result_lines = []
   
    # Current Dasha
    if current_dasha:
        yrs_text = years_label(dasha_years)
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ ദശ - {current_dasha} ({yrs_text})</div>")
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>{fmt(dasha_start)} - to - {fmt(dasha_end)}</div>")
    else:
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ ദശ - -</div>")

    result_lines.append("<br>")

    # Current Antar
    if current_antar:
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ അപഹാരം - {current_antar}</div>")
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>{fmt(antar_start)} - to - {fmt(antar_end)}</div>")
    else:
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ അപഹാരം - -</div>")

    result_lines.append("<br>")

    # Current Chidra
    if current_chidra:
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ ചിദ്രം - {current_chidra}</div>")
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>{fmt(chidra_start)} - to - {fmt(chidra_end)}</div>")
    else:
        result_lines.append(f"<div style='padding: 8px 0; border-bottom: 2px solid #333;'>നിലവിലെ ചിദ്രം - -</div>")

    return "".join(result_lines)

