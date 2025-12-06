from flask import render_template_string
import swisseph as swe
from datetime import datetime, timedelta
import pytz
import math


# ജ്യോതിഷ വിവരങ്ങൾ
NAKSHATRAS = [
    ("അശ്വതി", 0), ("ഭരണി", 13.3333), ("കാർത്തിക", 26.6667), ("രോഹിണി", 40.0),
    ("മകയിരം", 53.3333), ("തിരുവാതിര", 66.6667), ("പുണർതം", 80.0), ("പൂയ്യം", 93.3333),
    ("ആയില്യം", 106.6667), ("മകം", 120.0), ("പൂരം", 133.3333), ("ഉത്രം", 146.6667),
    ("അത്തം", 160.0), ("ചിതിര", 173.3333), ("ചോതി", 186.6667), ("വിശാഖം", 200.0),
    ("അനിഴം", 213.3333), ("കേട്ട", 226.6667), ("മൂലം", 240.0), ("പൂരാടം", 253.3333),
    ("ഉത്രാടം", 266.6667), ("തിരുവോണം", 280.0), ("അവിട്ടം", 293.3333), ("ചതയം", 306.6667),
    ("പൂരുരുട്ടാതി", 320.0), ("ഉത്രട്ടാതി", 333.3333), ("രേവതി", 346.6667)
]

DASHA_ORDER = [
    ("കേതു", 7), ("ശുക്രൻ", 20), ("രവി", 6), ("ചന്ദ്രൻ", 10), ("കുജൻ", 7),
    ("രാഹു", 18), ("ഗുരു", 16), ("ശനി", 19), ("ബുധൻ", 17)
]

# Sidereal year constant (days)
SIDEREAL_YEAR_DAYS = 365.258756


# --- സഹായ ഫങ്ഷനുകൾ (Helper Functions) ---

def get_nakshatra(moon_long):
    """ചന്ദ്രൻ്റെ രേഖാംശം അനുസരിച്ച് നക്ഷത്രം കണ്ടെത്തുന്നു."""
    for i, (name, start) in enumerate(NAKSHATRAS):
        end = start + 13.3333
        if start <= moon_long < end:
            return i, name, start, end
    return 0, "അശ്വതി", 0, 13.3333


def years_to_ymd_sidereal(years_float):
    """ദശാംശ വർഷത്തെ വർഷം, മാസം, ദിവസം ആക്കി മാറ്റുന്നു (സൈഡീരിയൽ വർഷം ഉപയോഗിച്ച്)."""
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


def get_current_dasha_antar_chidra(dasha_sequence, now):
    """ഇപ്പോഴത്തെ ദശ, അപഹാരം, ചിദ്രം കണ്ടെത്തുക"""
    current_dasha, current_antar, current_chidra = None, None, None
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
    """നക്ഷത്രത്തിൻ്റെ ആരംഭ സമയത്തിൽ നിന്ന് തുടർച്ചയായ ദശകൾ സൃഷ്ടിക്കുന്നു."""

    sequence = []
    cur_dt = nak_start_time
    years_accum = 0.0
    idx = lord_index
    first = True

    while years_accum < max_years:
        lord_name, lord_years = DASHA_ORDER[idx % 9]

        if first:
            use_years = dasha_full_years  # ശിഷ്ടദശയുടെ മുഴുവൻ കാലയളവ് (നക്ഷത്രാരംഭം മുതൽ)
            first = False
        else:
            use_years = lord_years

        start = cur_dt
        end = start + timedelta(days=(use_years * SIDEREAL_YEAR_DAYS))
        years_accum += use_years

        # അപഹാരങ്ങൾ (Antardashas)
        antar_list = []
        antar_cur = start
        for a_idx in range(9):
            a_lord, a_years = DASHA_ORDER[(idx + a_idx) % 9]
            antar_len_years = use_years * (a_years / 120.0)
            antar_end = antar_cur + timedelta(days=(antar_len_years * SIDEREAL_YEAR_DAYS))

            # ചിദ്രങ്ങൾ (Pratyantar/Chidra)
            praty_list = []
            praty_cur = antar_cur
            for p_idx in range(9):
                p_lord, p_years = DASHA_ORDER[((idx + a_idx) + p_idx) % 9]
                praty_len = antar_len_years * (p_years / 120.0)
                praty_end = praty_cur + timedelta(days=(praty_len * SIDEREAL_YEAR_DAYS))
                praty_list.append({
                    "lord": p_lord, "start": praty_cur, "end": praty_end
                })
                praty_cur = praty_end

            antar_list.append({
                "lord": a_lord, "start": antar_cur, "end": antar_end, "pratyantar": praty_list
            })
            antar_cur = antar_end

        sequence.append({
            "lord": lord_name, "years": use_years, "start": start, "end": end,
            "antar": antar_list
        })

        cur_dt = end
        idx += 1

        # 90 വർഷത്തിന് ശേഷം നിർത്തുക
        if (cur_dt - nak_start_time).days > max_years * SIDEREAL_YEAR_DAYS:
            break

    return sequence


def calc_dasha(dob, tob, lat, lon, tz_str):
    """ദശാഫലം കണക്കാക്കുന്നു."""
    # 1. സമയവും സ്ഥാനവും ക്രമീകരിക്കുന്നു
    tz = pytz.timezone(tz_str)
    dt_local = tz.localize(datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M"))
    dt_utc = dt_local.astimezone(pytz.utc)

    # 2. ജൂലിയൻ ഡേയും അയനാംശവും
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa(jd)

    # 3. ചന്ദ്രൻ്റെ സ്ഥാനം
    moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    moon_long_tropical = moon_pos[0] % 360
    moon_long_sidereal = (moon_long_tropical - ayanamsa) % 360

    # 4. നക്ഷത്രം, ദശാപതി
    idx, nak_name, start_long, end_long = get_nakshatra(moon_long_sidereal)
    lord_index = idx % 9
    lord_name, dasha_full_years = DASHA_ORDER[lord_index]

    # 5. ശിഷ്ടദശ (Balance Dasha) - shishtadhsha.py ലെ ഗണിതം ഉപയോഗിച്ച്
    span = 13.3333333333
    progressed = (moon_long_sidereal - start_long) % 360.0
    if progressed > span:
        progressed = span
    fraction_left = 1.0 - (progressed / span)
    balance_years = dasha_full_years * fraction_left

    # 6. നക്ഷത്രാരംഭ സമയം (Nakshatra Start Time)
    nak_duration_days = dasha_full_years * SIDEREAL_YEAR_DAYS
    nak_elapsed_days = (progressed / span) * nak_duration_days
    nak_start_time = dt_local - timedelta(days=nak_elapsed_days)

    # 7. തുടർച്ചയായ ദശകൾ സൃഷ്ടിക്കുന്നു
    dasha_sequence = generate_sequential_dashas(nak_start_time, lord_index, dasha_full_years, dt_local, max_years=90)

    # 8. ഫലം നൽകുന്നു
    return {
        "nak": nak_name,
        "current_lord": lord_name,
        "shishta": {"years_float": balance_years, "ymd": years_to_ymd_sidereal(balance_years)},
        "sequence": dasha_sequence,
        "birth_dt": dt_local,
    }


# --- HTML Template (Style മാറ്റങ്ങൾ ഉൾപ്പെടുത്തി) ---

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ജാതകം - ദശാകാലം</title>
<style>
* {
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    -webkit-touch-callout: none;
    -webkit-tap-highlight-color: transparent;
}

body {
    font-family: "Noto Sans Malayalam", "Manjari", sans-serif;
    background: #f5f5f5;
    padding: 10px;
    margin: 0;
    font-size: 18px;
    color: #333;
}

.container {
    max-width: 100%;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border: 2px solid #e0e0e0;
}

h1 {
    color: #2c3e50;
    text-align: center;
    font-size: 1.8em;
    margin-bottom: 20px;
    padding-bottom: 5px;
    border-bottom: 2px solid #3498db;
}

.result {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    line-height: 1.5;
    margin-top: 15px;
    font-size: 18px;
    border: 1px solid #e0e0e0;
}

.current-info {
    background: #ffffff;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
    border: 2px solid #bdc3c7;
    color: #2c3e50;
    font-weight: normal;
    font-size: 0.9em;
}

.dasha-btn, .antar-btn, .chidra-btn {
    display: block;
    width: 100%;
    margin: 10px 0;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #bdc3c7;
    background: #ffffff;
    cursor: pointer;
    text-align: left;
    font-size: 18px;
    font-family: inherit;
    color: #2c3e50;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.highlight-dasha {
    background: #e74c3c !important;
    border-color: #c0392b !important;
    color: white !important;
    font-weight: normal !important;
}

.highlight-antar {
    background: #e74c3c !important;
    border-color: #c0392b !important;
    color: white !important;
    font-weight: normal !important;
}

.highlight-chidra {
    background: #e74c3c !important;
    border-color: #c0392b !important;
    color: white !important;
    font-weight: normal !important;
}

.info, .small {
    font-size: 1.1em;
    color: #2c3e50;
    margin: 10px 0;
    padding: 10px;
    background: rgba(52, 152, 219, 0.1);
    border-radius: 5px;
}

.date-time-display {
    font-weight: normal;
    font-size: 1.0em;
    color: #666;
    margin-top: 5px;
}

.highlight-dasha .date-time-display,
.highlight-antar .date-time-display,
.highlight-chidra .date-time-display {
    color: white !important;
}

.back-btn {
    width: 100%;
    padding: 14px;
    background: #95a5a6;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 20px;
}

.dasha-section, .antar-section, .chidra-section {
    margin-top: 20px;
}

.click-hint {
    font-style: italic;
    color: #7f8c8d;
    font-size: 1.0em;
    margin-top: 5px;
}

/* Copy protection */
.protected-text {
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
}
</style>
</head>
<body>
<div class="container">
<h1 class="protected-text">ദശാപഹാരങ്ങൾ</h1>

<div class="result">
{% if dob %}
    <div class="info protected-text">
        <b>ജനന തീയതി:</b> {{ dob }}<br>
        <b>ജനന സമയം:</b> {{ time }}<br>
        <b>Timezone:</b> {{ tz }}<br>
        <b>അക്ഷാംശം/രേഖാംശം:</b> {{ lat }}/{{ lon }}
    </div>
{% endif %}

{{ result_html|safe }}

</div>

<script>
// Copy protection
document.addEventListener('copy', function(e) {
    e.preventDefault();
    return false;
});

document.addEventListener('cut', function(e) {
    e.preventDefault();
    return false;
});

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    return false;
});

// Disable text selection
document.addEventListener('mousedown', function(e) {
    if (e.detail > 1) {
        e.preventDefault();
    }
});

// --- Javascript ഫങ്ഷണാലിറ്റി ---

let currentView = 'dasha';
let currentDashaId = null;
let currentAntarId = null;

function showDashaView() {
    document.querySelectorAll('.antar-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.chidra-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.dasha-section').forEach(el => el.style.display = 'block');
    currentView = 'dasha';
    currentDashaId = null;
    currentAntarId = null;
    updateBrowserHistory('dasha');
}

function showAntarView(dashaId) {
    document.querySelectorAll('.dasha-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.antar-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.chidra-section').forEach(el => el.style.display = 'none');
    
    const antarSection = document.getElementById(`antar_${dashaId}`);
    if (antarSection) {
        antarSection.style.display = 'block';
    }
    currentView = 'antar';
    currentDashaId = dashaId;
    currentAntarId = null;
    updateBrowserHistory('antar', dashaId);
}

function showChidraView(antarId) {
    document.querySelectorAll('.dasha-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.antar-section').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.chidra-section').forEach(el => el.style.display = 'none');
    
    const chidraSection = document.getElementById(`chidra_${antarId}`);
    if (chidraSection) {
        chidraSection.style.display = 'block';
    }
    currentView = 'chidra';
    currentAntarId = antarId;
    updateBrowserHistory('chidra', antarId);
}

function goBack() {
    if (currentView === 'chidra') {
        const parentDashaId = currentAntarId.split('_').slice(0, 2).join('_');
        showAntarView(parentDashaId);
    } else if (currentView === 'antar') {
        showDashaView();
    } else if (currentView === 'dasha') {
        return;
    }
}

// Browser back button handling
function updateBrowserHistory(view, id = null) {
    const state = { view: view, id: id };
    const title = 'ദശാപഹാരങ്ങൾ';
    const url = `#${view}${id ? '-' + id : ''}`;
    
    history.pushState(state, title, url);
}

function handlePopState(event) {
    if (event.state) {
        const state = event.state;
        if (state.view === 'dasha') {
            showDashaView();
        } else if (state.view === 'antar' && state.id) {
            showAntarView(state.id);
        } else if (state.view === 'chidra' && state.id) {
            showChidraView(state.id);
        }
    } else {
        showDashaView();
    }
}

// Attach event listeners after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    showDashaView();
    
    window.addEventListener('popstate', handlePopState);
    
    document.querySelectorAll('.dasha-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const dashaId = btn.dataset.dashaid;
            showAntarView(dashaId);
        });
    });
    
    document.querySelectorAll('.antar-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const antarId = btn.dataset.antarid;
            showChidraView(antarId);
        });
    });
    
    document.querySelectorAll('.back-btn').forEach(btn => {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            goBack();
        });
    });
});

window.addEventListener('beforeunload', function (e) {
    // Optional confirmation
});
</script>

</div>
</body>
</html>
"""


# --- പ്രധാന ഫംഗ്ഷൻ (Main Function) ---

def dasapaharam_calculation(data):
    """
    app.py-യിൽ നിന്ന് ലഭിക്കുന്ന ഡാറ്റ ഉപയോഗിച്ച് ദശാപഹാരം കണക്കാക്കി HTML നൽകുന്നു.
    """
    try:
        # app.py ൽ നിന്ന് dob വിവരങ്ങൾ എടുക്കുന്നു
        year = data['year']
        month = data['month']
        day = data['day']
        hour_24h = data['hour_24h']
        minute = data['minute']
        
        # സ്ഥല വിവരങ്ങൾ എടുക്കുന്നു
        place = data['place']
        lat = float(place.get('lat', 11.8745))
        lon = float(place.get('lng', 75.3704))
        tz_str = place.get('timezone', 'Asia/Kolkata')
        
        # കണക്കുകൂട്ടലിനായി തീയതിയും സമയവും സ്ട്രിംഗാക്കുന്നു
        dob = f"{year:04d}-{month:02d}-{day:02d}"
        tob = f"{hour_24h:02d}:{minute:02d}"
        
        # ദശാഫലം കണക്കാക്കുന്നു
        out = calc_dasha(dob, tob, lat, lon, tz_str)
        
        # ഇപ്പോഴത്തെ സമയം (ഇപ്പോൾ ബ്രൗസറിൽ നിന്ന് എടുക്കുന്നതിനു പകരം സെർവർ ടൈം ഉപയോഗിക്കുന്നു)
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        
        # --- റിസൾട്ട് HTML ഉണ്ടാക്കുന്നു ---
        html = []
        
        # നിലവിലെ ദശ, അപഹാരം, ചിദ്രം കണ്ടെത്തുന്നു
        current_dasha, current_antar, current_chidra = get_current_dasha_antar_chidra(out['sequence'], now)
        
        # നിലവിലെ ദശ വിവരങ്ങൾ
        html.append(f"<div class='current-info protected-text'>")
        html.append(f"<b>നിലവിലെ ദശപതി:</b> {current_dasha if current_dasha else 'കണ്ടെത്താനായില്ല'}<br>")
        html.append(f"<b>നിലവിലെ അപഹാരം:</b> {current_antar if current_antar else 'കണ്ടെത്താനായില്ല'}<br>")
        html.append(f"<b>നിലവിലെ ചിദ്രം:</b> {current_chidra if current_chidra else 'കണ്ടെത്താനായില്ല'}")
        html.append(f"</div>")
        
        # ശിഷ്ടദശ - shishtadhsha.py ലെ ഗണിതം ഉപയോഗിച്ച്
        y, m, d = out['shishta']['ymd']
        html.append(f"<div class='small protected-text'><b>ശിഷ്ടദശ:</b> {out['current_lord']} - {y} വർഷം {m} മാസം {d} ദിവസം</div>")
        
        # DASHA VIEW (ദശ)
        html.append("<div class='dasha-section section'>")
        html.append("<h3 class='protected-text'>ദശകൾ</h3>")
        html.append("<div class='click-hint protected-text'>ക്ലിക്ക് ചെയ്ത് അപഹാരം കാണുക</div>")
        
        seq = out['sequence']
        for i, d in enumerate(seq):
            d_id = f"dasha_{i}"
            cls = "dasha-btn protected-text"
            if d['start'] <= now <= d['end']:
                cls += " highlight-dasha"
            
            # ജനന തീയതി മുതൽ തുടങ്ങുന്ന ദശയ്ക്കുള്ള പ്രത്യേക ലേബൽ
            if i == 0:
                display_start = out['birth_dt'].strftime('%d/%m/%Y %H:%M')
                display_end = d['end'].strftime('%d/%m/%Y')
                years_label = f"({display_start} → {display_end}) (ശിഷ്ടദശ)"
            else:
                years_label = f"({d['years']:.4g} വർഷം) &nbsp; {d['start'].strftime('%d/%m/%Y')} → {d['end'].strftime('%d/%m/%Y')}"
            
            html.append(f"<div><button type='button' class='{cls}' data-dashaid='{d_id}'>")
            html.append(f"{d['lord']} ദശ")
            html.append(f"<div class='date-time-display protected-text'>{years_label}</div>")
            html.append(f"</button></div>")
            
        html.append("</div>") # end dasha-section
        
        # ANTAR VIEWS (അപഹാരം)
        for i, d in enumerate(seq):
            d_id = f"dasha_{i}"
            html.append(f"<div id='antar_{d_id}' class='antar-section section' style='display:none;'>")
            html.append(f"<h3 class='protected-text'>{d['lord']} ദശ - അപഹാരങ്ങൾ</h3>")
            html.append("<div class='click-hint protected-text'>ക്ലിക്ക് ചെയ്ത് ചിദ്രം കാണുക</div>")
            
            for j, a in enumerate(d['antar']):
                a_id = f"{d_id}_antar_{j}"
                cls2 = "antar-btn protected-text"
                if a['start'] <= now <= a['end']:
                    cls2 += " highlight-antar"
                
                antar_label = f"{a['start'].strftime('%d/%m/%Y %H:%M')} → {a['end'].strftime('%d/%m/%Y %H:%M')}"
                
                html.append(f"<div><button type='button' class='{cls2}' data-antarid='{a_id}'>")
                html.append(f"{a['lord']} അപഹാരം")
                html.append(f"<div class='date-time-display protected-text'>{antar_label}</div>")
                html.append(f"</button></div>")
            
            html.append(f"<button class='back-btn protected-text' data-dashaid='{d_id}'>← ദശയിലേക്ക് മടങ്ങുക</button>")
            html.append("</div>") # end antar-section
            
            # CHIDRA VIEWS (ചിദ്രം)
            for j, a in enumerate(d['antar']):
                a_id = f"{d_id}_antar_{j}"
                html.append(f"<div id='chidra_{a_id}' class='chidra-section section' style='display:none;'>")
                html.append(f"<h3 class='protected-text'>{d['lord']} - {a['lord']} അപഹാരം - ചിദ്രങ്ങൾ</h3>")
                
                for k, p in enumerate(a['pratyantar']):
                    cls3 = "chidra-btn protected-text"
                    if p['start'] <= now <= p['end']:
                        cls3 += " highlight-chidra"
                    
                    chidra_label = f"{p['start'].strftime('%d/%m/%Y %H:%M')} → {p['end'].strftime('%d/%m/%Y %H:%M')}"
                    
                    html.append(f"<div><button type='button' class='{cls3}'>")
                    html.append(f"{p['lord']} ചിദ്രം")
                    html.append(f"<div class='date-time-display protected-text'>{chidra_label}</div>")
                    html.append(f"</button></div>")
                
                html.append(f"<button class='back-btn protected-text' data-antarid='{a_id}'>← അപഹാരത്തിലേക്ക് മടങ്ങുക</button>")
                html.append("</div>") # end chidra-section

        result_html = "\n".join(html)

        # Template-ലേക്ക് ഡാറ്റ കൈമാറുന്നു
        return render_template_string(
            HTML_TEMPLATE,
            result_html=result_html,
            dob=dob,
            time=tob,
            lat=lat,
            lon=lon,
            tz=tz_str
        )

    except Exception as e:
        print(f"❌ Error in dasapaharam_calculation: {e}")
        return f"<div class='result'><h3>പിശക് സംഭവിച്ചു:</h3> ദശാപഹാരം കണക്കാക്കാനായില്ല. നൽകിയ വിവരങ്ങൾ ശരിയാണോയെന്ന് പരിശോധിക്കുക.<br><br>പിശക്: {str(e)}</div>"
