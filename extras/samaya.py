from flask import Flask, render_template_string, request
from datetime import datetime, timedelta
import pytz
import swisseph as swe
from astral import LocationInfo
from astral.sun import sun
import math
import os

app = Flask(__name__)

PLACES = {
    'Kannur': { 'lat': 11.8745, 'lon': 75.3704, 'tz': 'Asia/Kolkata' },
    'Thiruvananthapuram': { 'lat': 8.5241, 'lon': 76.9366, 'tz': 'Asia/Kolkata' },
    'Kollam': { 'lat': 8.8932, 'lon': 76.6141, 'tz': 'Asia/Kolkata' },
    'Dubai':  { 'lat': 25.2048, 'lon': 55.2708, 'tz': 'Asia/Dubai' },
    'Melbourne': { 'lat': -37.8136, 'lon': 144.9631, 'tz': 'Australia/Melbourne' },
    'New York': { 'lat': 40.7128, 'lon': -74.0060, 'tz': 'America/New_York' }
}

TEMPLATE = '''
<!DOCTYPE html>
<html lang="ml">
<head>
    <meta charset="UTF-8">
    <!-- STRICT VIEWPORT - NO ZOOM ALLOWED -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>രാശി സമയങ്ങൾ</title>
    <style>
        /* EXTREME FONT SIZE FORCING */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-text-size-adjust: 100% !important;
            -moz-text-size-adjust: 100% !important;
            -ms-text-size-adjust: 100% !important;
            text-size-adjust: 100% !important;
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
        }
        
        /* FORCE ALL TEXT TO BE LARGE */
        html, body, div, span, applet, object, iframe,
        h1, h2, h3, h4, h5, h6, p, blockquote, pre,
        a, abbr, acronym, address, big, cite, code,
        del, dfn, em, img, ins, kbd, q, s, samp,
        small, strike, strong, sub, sup, tt, var,
        b, u, i, center,
        dl, dt, dd, ol, ul, li,
        fieldset, form, label, legend,
        table, caption, tbody, tfoot, thead, tr, th, td,
        article, aside, canvas, details, embed,
        figure, figcaption, footer, header, hgroup,
        menu, nav, output, ruby, section, summary,
        time, mark, audio, video, input, select, textarea, button {
            font-size: inherit !important;
            font-family: inherit !important;
            line-height: inherit !important;
            color: inherit !important;
        }
        
        /* EXTREMELY LARGE BASE FONT */
        html {
            font-size: 32px !important; /* VERY LARGE - ~32px base */
        }
        
        body {
            font-family: 'Manjari', 'Noto Sans Malayalam', 'Segoe UI', Tahoma, sans-serif !important;
            background: linear-gradient(145deg, #0d1b5c 0%, #1a0d5c 100%) !important;
            color: #111 !important;
            line-height: 1.3 !important;
            min-height: 100vh !important;
            padding: 10px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            font-size: 1rem !important;
            overflow-x: hidden !important;
        }
        
        /* Main container */
        .container {
            width: 100% !important;
            max-width: 100% !important;
            background: white !important;
            border-radius: 25px !important;
            box-shadow: 0 15px 60px rgba(0, 0, 0, 0.3) !important;
            overflow: hidden !important;
            margin-bottom: 15px !important;
        }
        
        /* Header - EXTRA EXTRA LARGE */
        .header {
            background: linear-gradient(135deg, #c62828 0%, #8e0000 100%) !important;
            color: white !important;
            padding: 40px 30px !important;
            text-align: center !important;
            border-bottom: 12px solid #ffca28 !important;
        }
        
        .header h1 {
            font-size: 3.2rem !important; /* ~102px */
            font-weight: 900 !important;
            margin-bottom: 20px !important;
            text-shadow: 4px 4px 8px rgba(0, 0, 0, 0.5) !important;
            letter-spacing: 1.5px !important;
            line-height: 1.1 !important;
        }
        
        .header .subtitle {
            font-size: 1.9rem !important; /* ~61px */
            opacity: 0.95 !important;
            font-weight: 800 !important;
        }
        
        /* Input Section */
        .input-section {
            padding: 40px 30px !important;
            background: #f0f0f0 !important;
            border-bottom: 8px solid #ccc !important;
        }
        
        .form-group {
            margin-bottom: 40px !important;
        }
        
        .form-label {
            display: block !important;
            font-size: 1.8rem !important; /* ~58px */
            font-weight: 900 !important;
            color: #111 !important;
            margin-bottom: 20px !important;
            padding-left: 10px !important;
        }
        
        .form-control {
            width: 100% !important;
            padding: 30px 25px !important; /* VERY LARGE padding */
            font-size: 1.7rem !important; /* ~54px */
            font-family: inherit !important;
            border: 5px solid #999 !important;
            border-radius: 20px !important;
            background: white !important;
            color: #111 !important;
            transition: all 0.3s ease !important;
            -webkit-appearance: none !important;
            appearance: none !important;
            min-height: 90px !important;
        }
        
        .form-control:focus {
            outline: none !important;
            border-color: #c62828 !important;
            box-shadow: 0 0 0 5px rgba(198, 40, 40, 0.4) !important;
        }
        
        select.form-control {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 24 24' fill='%23111'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: right 25px center !important;
            background-size: 40px !important;
            padding-right: 85px !important;
        }
        
        /* Button - HUGE */
        .btn {
            display: block !important;
            width: 100% !important;
            padding: 35px 30px !important;
            background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 20px !important;
            font-size: 2.2rem !important; /* ~70px */
            font-weight: 900 !important;
            font-family: inherit !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            text-align: center !important;
            text-decoration: none !important;
            box-shadow: 0 10px 0 #0d3c0f !important;
            margin-top: 25px !important;
            letter-spacing: 1.5px !important;
            line-height: 1.1 !important;
        }
        
        .btn:hover, .btn:active {
            background: linear-gradient(135deg, #1b5e20 0%, #0d3c0f 100%) !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 14px 0 #0d3c0f !important;
        }
        
        .btn:active {
            transform: translateY(3px) !important;
            box-shadow: 0 5px 0 #0d3c0f !important;
        }
        
        /* Results Section */
        .results-section {
            padding: 40px 30px !important;
            background: white !important;
        }
        
        .results-header {
            background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
            color: white !important;
            padding: 35px 30px !important;
            border-radius: 20px !important;
            text-align: center !important;
            margin-bottom: 40px !important;
            box-shadow: 0 10px 25px rgba(21, 101, 192, 0.5) !important;
        }
        
        .results-header h2 {
            font-size: 2.6rem !important; /* ~83px */
            font-weight: 900 !important;
            margin-bottom: 15px !important;
            line-height: 1.1 !important;
        }
        
        .results-header .place {
            font-size: 1.8rem !important; /* ~58px */
            opacity: 0.95 !important;
            font-weight: 800 !important;
        }
        
        /* Table */
        .table-responsive {
            width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            margin-bottom: 35px !important;
            border-radius: 20px !important;
            border: 5px solid #bbb !important;
        }
        
        .results-table {
            width: 100% !important;
            min-width: 500px !important;
            border-collapse: collapse !important;
            font-size: 1.5rem !important; /* ~48px */
        }
        
        .results-table thead {
            background: linear-gradient(135deg, #4e342e 0%, #3e2723 100%) !important;
        }
        
        .results-table th {
            color: white !important;
            padding: 32px 22px !important;
            text-align: center !important;
            font-size: 1.9rem !important; /* ~61px */
            font-weight: 900 !important;
            white-space: nowrap !important;
            border-right: 4px solid #795548 !important;
        }
        
        .results-table th:last-child {
            border-right: none !important;
        }
        
        .results-table td {
            padding: 28px 22px !important;
            text-align: center !important;
            border-bottom: 5px solid #e8e8e8 !important;
            font-weight: 800 !important;
        }
        
        .results-table tr:nth-child(even) {
            background-color: #f8f8f8 !important;
        }
        
        .results-table tr:hover {
            background-color: #edf5ff !important;
        }
        
        .sign-name {
            color: #c62828 !important;
            font-weight: 900 !important;
            font-size: 2rem !important; /* ~64px */
        }
        
        .time-value {
            color: #1565c0 !important;
            font-weight: 900 !important;
            font-size: 1.7rem !important; /* ~54px */
        }
        
        /* Mobile note */
        .mobile-note {
            background: #fff9c4 !important;
            border: 5px dashed #ffa000 !important;
            border-radius: 20px !important;
            padding: 30px 25px !important;
            text-align: center !important;
            margin-top: 40px !important;
            font-size: 1.5rem !important; /* ~48px */
            color: #4e342e !important;
            font-weight: 800 !important;
        }
        
        .mobile-note span {
            font-size: 2.3rem !important;
            display: block !important;
            margin-bottom: 15px !important;
        }
        
        /* FORCE FONT SIZES ON MOBILE */
        @media (max-width: 767px) {
            html {
                font-size: 30px !important; /* Still huge */
            }
            
            .header h1 {
                font-size: 2.8rem !important; /* ~84px */
            }
            
            .header .subtitle {
                font-size: 1.7rem !important; /* ~51px */
            }
            
            .form-label {
                font-size: 1.6rem !important; /* ~48px */
            }
            
            .form-control {
                font-size: 1.5rem !important; /* ~45px */
                padding: 28px 22px !important;
                min-height: 85px !important;
            }
            
            .btn {
                font-size: 2rem !important; /* ~60px */
                padding: 30px 25px !important;
            }
            
            .results-header h2 {
                font-size: 2.3rem !important; /* ~69px */
            }
            
            .results-header .place {
                font-size: 1.6rem !important; /* ~48px */
            }
            
            .results-table {
                font-size: 1.4rem !important; /* ~42px */
            }
            
            .results-table th {
                font-size: 1.7rem !important; /* ~51px */
                padding: 28px 20px !important;
            }
            
            .results-table td {
                padding: 25px 20px !important;
            }
            
            .sign-name {
                font-size: 1.8rem !important; /* ~54px */
            }
            
            .time-value {
                font-size: 1.6rem !important; /* ~48px */
            }
            
            .mobile-note {
                font-size: 1.4rem !important; /* ~42px */
                padding: 25px 22px !important;
            }
        }
        
        /* Very small phones - MINIMUM SIZES */
        @media (max-width: 360px) {
            html {
                font-size: 28px !important; /* Absolute minimum */
            }
            
            .header {
                padding: 35px 25px !important;
            }
            
            .header h1 {
                font-size: 2.5rem !important; /* ~70px */
            }
            
            .header .subtitle {
                font-size: 1.5rem !important; /* ~42px */
            }
            
            .btn {
                font-size: 1.8rem !important; /* ~50px */
                padding: 28px 22px !important;
            }
            
            .input-section, .results-section {
                padding: 35px 25px !important;
            }
        }
        
        /* Landscape mode */
        @media (orientation: landscape) {
            html {
                font-size: 26px !important;
            }
            
            body {
                padding: 5px !important;
            }
            
            .container {
                max-width: 98% !important;
            }
            
            .header {
                padding: 25px 20px !important;
            }
            
            .input-section, .results-section {
                padding: 25px 20px !important;
            }
        }
        
        /* Desktop - make even larger */
        @media (min-width: 768px) {
            html {
                font-size: 36px !important; /* EXTREMELY HUGE on desktop */
            }
            
            body {
                padding: 20px !important;
            }
            
            .container {
                max-width: 900px !important;
            }
            
            .header h1 {
                font-size: 3.5rem !important; /* ~126px */
            }
            
            .header .subtitle {
                font-size: 2.2rem !important; /* ~79px */
            }
            
            .form-control {
                font-size: 1.9rem !important; /* ~68px */
                padding: 35px 30px !important;
            }
            
            .btn {
                font-size: 2.5rem !important; /* ~90px */
                padding: 40px 35px !important;
            }
        }
        
        /* Prevent text selection */
        .btn, .form-control {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }
        
        /* Focus styles */
        *:focus {
            outline: 5px solid rgba(198, 40, 40, 0.7) !important;
            outline-offset: 4px !important;
        }
        
        /* Hide scrollbar but allow scrolling */
        .table-responsive::-webkit-scrollbar {
            height: 15px !important;
        }
        
        .table-responsive::-webkit-scrollbar-track {
            background: #f1f1f1 !important;
            border-radius: 10px !important;
        }
        
        .table-responsive::-webkit-scrollbar-thumb {
            background: #c62828 !important;
            border-radius: 10px !important;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Manjari:wght@400;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Malayalam:wght@400;700;800;900&display=swap">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>രാശി സമയങ്ങൾ</h1>
            <div class="subtitle">ഉദയ ലഗ്ന വിശകലനം</div>
        </div>
        
        <div class="input-section">
            <form method="post" id="rasiForm">
                <div class="form-group">
                    <label for="date" class="form-label">📅 ജനന തീയതി</label>
                    <input type="date" name="date" id="date" class="form-control" 
                           value="{{ default_date }}" required
                           aria-label="ജനന തീയതി തിരഞ്ഞെടുക്കുക">
                </div>
                
                <div class="form-group">
                    <label for="place_select" class="form-label">📍 സ്ഥലം തിരഞ്ഞെടുക്കുക</label>
                    <select name="place" id="place_select" class="form-control" 
                            aria-label="സ്ഥലം തിരഞ്ഞെടുക്കുക">
                        {% for p in places %}
                            <option value="{{p}}" {% if p==default_place %}selected{% endif %}>{{p}}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <button type="submit" class="btn" id="calculateBtn">
                    📊 രാശി സമയങ്ങൾ കണ്ടുപിടിക്കുക
                </button>
            </form>
        </div>
        
        {% if result %}
        <div class="results-section">
            <div class="results-header">
                <h2>രാശി സമയങ്ങൾ</h2>
                <div class="place">{{ result.place }}</div>
            </div>
            
            <div class="table-responsive">
                <table class="results-table" aria-label="രാശി സമയങ്ങളുടെ പട്ടിക">
                    <thead>
                        <tr>
                            <th scope="col">രാശി</th>
                            <th scope="col">ആരംഭ സമയം</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for r in result.signs %}
                        <tr>
                            <td class="sign-name">{{ r.sign_name }}</td>
                            <td class="time-value">{{ r.start_local }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="mobile-note">
                <span>📱</span>
                ടേബിളിൽ വലത്തോട്ട് സ്ക്രോൾ ചെയ്ത് മുഴുവൻ ഉള്ളടക്കവും കാണാം
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        // EXTREME FONT SIZE FORCING
        (function() {
            // Force font size immediately
            document.documentElement.style.fontSize = '32px';
            
            // Prevent any zoom attempts
            const preventZoom = function(e) {
                if (e.touches && e.touches.length > 1) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            };
            
            document.addEventListener('touchstart', preventZoom, { passive: false });
            document.addEventListener('touchmove', preventZoom, { passive: false });
            
            // Prevent double tap zoom
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(e) {
                const now = Date.now();
                if (now - lastTouchEnd <= 300) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                }
                lastTouchEnd = now;
            }, { passive: false, capture: true });
            
            // Prevent gesture zoom
            document.addEventListener('gesturestart', function(e) {
                e.preventDefault();
            });
            
            document.addEventListener('gesturechange', function(e) {
                e.preventDefault();
            });
            
            document.addEventListener('gestureend', function(e) {
                e.preventDefault();
            });
            
            // Form submission handler
            const form = document.getElementById('rasiForm');
            const submitBtn = document.getElementById('calculateBtn');
            
            if (form && submitBtn) {
                form.addEventListener('submit', function() {
                    submitBtn.innerHTML = '⏳ കണക്കാക്കുന്നു...';
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.6';
                });
            }
            
            // Set today's date if empty
            const dateInput = document.getElementById('date');
            if (dateInput && !dateInput.value) {
                const today = new Date();
                const yyyy = today.getFullYear();
                const mm = String(today.getMonth() + 1).padStart(2, '0');
                const dd = String(today.getDate()).padStart(2, '0');
                dateInput.value = `${yyyy}-${mm}-${dd}`;
            }
            
            // Focus on date input with delay
            setTimeout(function() {
                if (dateInput) {
                    dateInput.focus();
                    // Force font size on inputs
                    const inputs = document.querySelectorAll('input, select, button');
                    inputs.forEach(function(input) {
                        input.style.fontSize = '1.7rem';
                        input.style.webkitTextSizeAdjust = '100%';
                        input.style.mozTextSizeAdjust = '100%';
                        input.style.msTextSizeAdjust = '100%';
                        input.style.textSizeAdjust = '100%';
                    });
                }
            }, 100);
            
            // Continuously check and enforce font size
            setInterval(function() {
                const html = document.documentElement;
                const currentSize = parseFloat(window.getComputedStyle(html).fontSize);
                const targetSize = 32; // px
                
                if (currentSize < targetSize * 0.9) {
                    html.style.fontSize = targetSize + 'px';
                }
                
                // Force button font size
                if (submitBtn) {
                    submitBtn.style.fontSize = '2.2rem';
                }
            }, 500);
            
            // Add viewport meta dynamically
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (viewportMeta) {
                viewportMeta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            }
        })();
        
        // Prevent context menu on mobile
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });
    </script>
</body>
</html>
'''

SIGN_NAMES = ['മേടം', 'ഇടവം', 'മിഥുനം', 'കർക്കിടകം', 'ചിങ്ങം', 'കന്നി',
              'തുലാം', 'വൃശ്ചികം', 'ധനു', 'മകരം', 'കുംഭം', 'മീനം']

def correct_ist_to_utc(year, month, day, hour, minute, second):
    """IST (UTC+5:30) നെ UTC യാക്കി മാറ്റുക - bhavadigri.py ലെ രീതി തന്നെ"""
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

# Utility: normalize degree to 0..360
def norm_deg(d):
    d = d % 360.0
    if d < 0:
        d += 360.0
    return d

# Compute julian day from UTC datetime
def jd_from_utc(dt_utc):
    # dt_utc must be timezone-aware in UTC
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

# Compute sidereal ascendant degree using bhavadigri.py method
def ascendant_deg_from_jd_sidereal(jd_ut, lat, lon, ayanamsa_mode=1):
    """കൃത്യമായ ലഗ്നം കണക്കാക്കുക - bhavadigri.py ലെ രീതി തന്നെ"""
    swe.set_sid_mode(ayanamsa_mode)
    
    houses = swe.houses(jd_ut, lat, lon, b'P')
    lagna_longitude = houses[0][0]
    
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)
    nirayana_lagna = (lagna_longitude - ayanamsa) % 360
    
    return nirayana_lagna

# Sample ascendant every minute for window_hours starting at start_dt_local
def sample_asc_for_hours(start_dt_local, window_hours, tz_str, lat, lon):
    tz = pytz.timezone(tz_str)
    results = []
    total_minutes = int(window_hours * 60)
    
    for m in range(total_minutes+1):
        dt_local = start_dt_local + timedelta(minutes=m)
        dt_utc = dt_local.astimezone(pytz.UTC)
        jd = jd_from_utc(dt_utc)
        asc = ascendant_deg_from_jd_sidereal(jd, lat, lon)
        results.append((dt_local, asc))
    
    return results

# signed minimal angular diff b - a
def ang_diff(a,b):
    d = (b - a + 540.0) % 360.0 - 180.0
    return d

# Find sign boundaries likewise; unwrapping to continuous track to manage wrap-around
def find_sign_boundaries(samples):
    boundaries = [i*30.0 for i in range(13)]
    found = {}
    
    # unwrap by making continuous list
    prev_cont = samples[0][1]
    cont_list = [(samples[0][0], prev_cont)]
    
    for i in range(1, len(samples)):
        dt, asc = samples[i]
        cand = asc
        for shift in (-360,0,360):
            if abs((asc+shift) - prev_cont) < abs(cand - prev_cont):
                cand = asc+shift
        cont_list.append((dt, cand))
        prev_cont = cand
    
    # detect boundaries
    for i in range(1, len(cont_list)):
        prev_dt, prev_deg = cont_list[i-1]
        cur_dt, cur_deg = cont_list[i]
        low = min(prev_deg, cur_deg)
        high = max(prev_deg, cur_deg)
        
        for b in boundaries:
            for candidate in (b, b+360):
                if low <= candidate <= high:
                    sign_index = int((candidate/30) % 12)
                    if sign_index not in found:
                        if cur_deg != prev_deg:
                            frac = (candidate - prev_deg) / (cur_deg - prev_deg)
                        else:
                            frac = 0.0
                        cross_time = prev_dt + timedelta(seconds=frac*60)
                        found[sign_index] = {'start': cross_time}
                    else:
                        if 'end' not in found[sign_index]:
                            if cur_deg != prev_deg:
                                frac = (candidate - prev_deg) / (cur_deg - prev_deg)
                            else:
                                frac = 0.0
                            cross_time = prev_dt + timedelta(seconds=frac*60)
                            found[sign_index]['end'] = cross_time
    
    return found

def rasi_samayam_calculation(data):
    """Main calculation function for app.py integration"""
    try:
        # Extract data from app.py format
        year = data['year']
        month = data['month']
        day = data['day']
        hour_24h = data['hour_24h']
        minute = data['minute']
        place_data = data['place']
        
        # Convert to required format
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        lat = place_data['lat']
        lon = place_data['lng']
        tz_name = place_data['timezone']
        place_name = place_data['name']
        
        # Compute sunrise with Astral (timezone-aware)
        loc = LocationInfo(name=place_name, region=place_name, timezone=tz_name, latitude=lat, longitude=lon)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        s = sun(loc.observer, date=date_obj, tzinfo=pytz.timezone(tz_name))
        sunrise_local = s['sunrise']  # timezone-aware local time (handles DST)
        
        # FIX: Subtract 3 minutes from sunrise time (രാശി സമയത്തിൽ 3 മിനിറ്റ് കുറച്ചെഴുതു)
        sunrise_local = sunrise_local - timedelta(minutes=3)
        
        # Convert to UTC explicitly
        sunrise_utc = sunrise_local.astimezone(pytz.UTC)
        
        # Compute sidereal ascendant at sunrise using bhavadigri.py method
        jd_ut = jd_from_utc(sunrise_utc)
        asc_udaya = ascendant_deg_from_jd_sidereal(jd_ut, lat, lon)
        
        # sample 24 hours from sunrise to find sign boundaries (1-min)
        window_hours = 24
        samples = sample_asc_for_hours(sunrise_local, window_hours, tz_name, lat, lon)
        found = find_sign_boundaries(samples)
        
        sign_list = []
        for idx in sorted(found.keys(), key=lambda x: found[x]['start']):
            rec = found[idx]
            start_local = rec.get('start')
            if start_local:
                sign_list.append({
                    'sign_name': SIGN_NAMES[idx],
                    'start_local': start_local.strftime('%Y-%m-%d %H:%M')
                })
        
        # Format result as HTML for app.py with INLINE CSS
        result_html = f"""
        <div style="
            font-family: 'Manjari', sans-serif !important;
            background: linear-gradient(145deg, #0d1b5c 0%, #1a0d5c 100%) !important;
            min-height: 100vh !important;
            padding: 15px !important;
            color: #111 !important;
            font-size: 32px !important;
        ">
            <div style="
                background: white !important;
                padding: 30px !important;
                border-radius: 25px !important;
                box-shadow: 0 15px 60px rgba(0, 0, 0, 0.3) !important;
            ">
                <div style="
                    background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
                    color: white !important;
                    padding: 35px 30px !important;
                    border-radius: 20px !important;
                    text-align: center !important;
                    margin-bottom: 35px !important;
                ">
                    <div style="font-size: 2.6rem !important; font-weight: 900 !important; margin-bottom: 15px !important;">
                        രാശി സമയങ്ങൾ - {place_name}
                    </div>
                </div>
                
                <div style="width: 100% !important; overflow-x: auto !important;">
                    <table style="
                        width: 100% !important;
                        min-width: 500px !important;
                        border-collapse: collapse !important;
                        font-size: 1.5rem !important;
                    ">
                        <thead>
                            <tr>
                                <th style="
                                    background: linear-gradient(135deg, #4e342e 0%, #3e2723 100%) !important;
                                    color: white !important;
                                    padding: 32px 22px !important;
                                    text-align: center !important;
                                    font-size: 1.9rem !important;
                                    font-weight: 900 !important;
                                ">രാശി</th>
                                <th style="
                                    background: linear-gradient(135deg, #4e342e 0%, #3e2723 100%) !important;
                                    color: white !important;
                                    padding: 32px 22px !important;
                                    text-align: center !important;
                                    font-size: 1.9rem !important;
                                    font-weight: 900 !important;
                                ">ആരംഭ സമയം</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for sign in sign_list:
            result_html += f"""
                            <tr>
                                <td style="
                                    padding: 28px 22px !important;
                                    text-align: center !important;
                                    border-bottom: 5px solid #e8e8e8 !important;
                                    color: #c62828 !important;
                                    font-weight: 900 !important;
                                    font-size: 2rem !important;
                                ">{sign['sign_name']}</td>
                                <td style="
                                    padding: 28px 22px !important;
                                    text-align: center !important;
                                    border-bottom: 5px solid #e8e8e8 !important;
                                    color: #1565c0 !important;
                                    font-weight: 900 !important;
                                    font-size: 1.7rem !important;
                                ">{sign['start_local']}</td>
                            </tr>
            """
        
        result_html += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """
        
        return result_html
        
    except Exception as e:
        return f"<div style='color: #c62828 !important; font-size: 1.7rem !important; padding: 30px !important; background: white !important; border-radius: 20px !important;'>പിശക്: {str(e)}</div>"

@app.route('/', methods=['GET','POST'])
def index():
    default_place = 'Kannur'
    p = PLACES[default_place]
    default_date = datetime.now().date().isoformat()
    result = None
    
    if request.method == 'POST':
        date_str = request.form['date']
        place = request.form['place']
        lat = PLACES[place]['lat']
        lon = PLACES[place]['lon']
        tz_name = PLACES[place]['tz']
        
        # Compute sunrise with Astral (timezone-aware)
        loc = LocationInfo(name=place, region=place, timezone=tz_name, latitude=lat, longitude=lon)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        s = sun(loc.observer, date=date_obj, tzinfo=pytz.timezone(tz_name))
        sunrise_local = s['sunrise']
        
        # FIX: Subtract 3 minutes from sunrise time
        sunrise_local = sunrise_local - timedelta(minutes=3)
        
        # Convert to UTC explicitly
        sunrise_utc = sunrise_local.astimezone(pytz.UTC)
        
        # Compute sidereal ascendant at sunrise using bhavadigri.py method
        jd_ut = jd_from_utc(sunrise_utc)
        asc_udaya = ascendant_deg_from_jd_sidereal(jd_ut, lat, lon)
        
        # sample 24 hours from sunrise to find sign boundaries (1-min)
        window_hours = 24
        samples = sample_asc_for_hours(sunrise_local, window_hours, tz_name, lat, lon)
        found = find_sign_boundaries(samples)
        
        sign_list = []
        for idx in sorted(found.keys(), key=lambda x: found[x]['start']):
            rec = found[idx]
            start_local = rec.get('start')
            if start_local:
                sign_list.append({
                    'sign_name': SIGN_NAMES[idx],
                    'start_local': start_local.strftime('%Y-%m-%d %H:%M')
                })
        
        result = {
            'place': place,
            'lat': lat,
            'lon': lon,
            'tz': tz_name,
            'signs': sign_list,
        }
    
    return render_template_string(TEMPLATE,
                                  places=PLACES.keys(),
                                  default_place=default_place,
                                  default_lat=p['lat'],
                                  default_lon=p['lon'],
                                  default_tz=p['tz'],
                                  default_date=default_date,
                                  result=result,
                                  places_json=PLACES)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
