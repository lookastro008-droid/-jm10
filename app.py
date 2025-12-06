from flask import Flask, render_template, request, jsonify
import datetime
import pytz
import math
import os
import subprocess
import sys
import glob
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Cache cleaning functions
def clean_all_cache():
    """Clean all cache files"""
    try:
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    dir_path = os.path.join(root, dir_name)
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path, ignore_errors=True)
                        print(f"✅ Cleared: {dir_path}")
       
        for root, dirs, files in os.walk('.'):
            for file_name in files:
                if file_name.endswith('.pyc') or file_name.endswith('.pyo'):
                    file_path = os.path.join(root, file_name)
                    try:
                        os.remove(file_path)
                    except:
                        pass
       
        print("✅ Cache cleaning completed")
        return True
    except Exception as e:
        print(f"❌ Cache cleaning error: {e}")
        return False

def clean_flask_sessions():
    """Clean Flask session files"""
    try:
        if os.path.exists('flask_session'):
            shutil.rmtree('flask_session', ignore_errors=True)
            os.makedirs('flask_session', exist_ok=True)
            print("✅ Flask sessions cleaned")
        return True
    except Exception as e:
        print(f"❌ Flask session clean error: {e}")
        return False

# Import places data
try:
    try:
        from places.places_data import places_list
        PLACES_DATA = places_list
        print("✅ Places imported from places.places_data")
    except ImportError:
        try:
            from places.places_data import PLACES_DATA
            print("✅ Places imported from places.places_data (PLACES_DATA)")
        except ImportError:
            from places import places_list
            PLACES_DATA = places_list
            print("✅ Places imported from places")
   
    print(f"✅ Successfully imported {len(PLACES_DATA)} places")
   
except ImportError as e:
    print(f"❌ Error importing places: {e}")
    PLACES_DATA = [
        {"name": "കണ്ണൂർ", "lat": 11.8745, "lng": 75.3704, "timezone": "Asia/Kolkata"},
        {"name": "തിരുവനന്തപുരം", "lat": 8.5241, "lng": 76.9366, "timezone": "Asia/Kolkata"}
    ]

def get_proper_timezone(timezone_str):
    """Convert any timezone format to proper pytz timezone"""
    if not timezone_str:
        return 'Asia/Kolkata'
   
    if '/' in timezone_str:
        return timezone_str
   
    timezone_map = {
        '+0530': 'Asia/Kolkata',
        '+0545': 'Asia/Kathmandu',
        '+0800': 'Asia/Singapore',
        '+0900': 'Asia/Tokyo',
        '-0500': 'America/New_York',
        '-0400': 'America/New_York',
        '-0600': 'America/Chicago',
        '-0700': 'America/Denver',
        '-0800': 'America/Los_Angeles',
        '+0000': 'Europe/London',
        '+0100': 'Europe/London'
    }
   
    if timezone_str in timezone_map:
        return timezone_map[timezone_str]
   
    return 'Asia/Kolkata'

def create_localized_datetime_for_place(year, month, day, hour_24h, minute, place_data):
    """Create PROPER localized datetime for the specific place"""
    try:
        timezone_str = place_data.get('timezone', 'Asia/Kolkata')
        proper_timezone = get_proper_timezone(timezone_str)
       
        tz = pytz.timezone(proper_timezone)
        naive_dt = datetime.datetime(year, month, day, hour_24h, minute)
        localized_dt = tz.localize(naive_dt)
       
        return localized_dt
    except Exception as e:
        print(f"Error creating localized datetime: {e}")
        return datetime.datetime(year, month, day, hour_24h, minute)

# Import ALL task functions
try:
    from tasks.kalidhinam import kalidhinam_calculation
    kalidhinam_available = True
    print("✅ Kalidhinam module imported successfully")
except ImportError as e:
    kalidhinam_available = False
    print(f"❌ Kalidhinam import error: {e}")

try:
    from tasks.kollavarsham import kollavarsham_calculation
    kollavarsham_available = True
    print("✅ Kollavarsham module imported successfully")
except ImportError as e:
    kollavarsham_available = False
    print(f"❌ Kollavarsham import error: {e}")

try:
    from tasks.shakavarsham import shakavarsham_calculation
    shakavarsham_available = True
    print("✅ Shakavarsham module imported successfully")
except ImportError as e:
    shakavarsham_available = False
    print(f"❌ Shakavarsham import error: {e}")

try:
    from tasks.nakshathra import nakshathra_calculation
    nakshathra_available = True
    print("✅ Nakshathra module imported successfully")
except ImportError as e:
    nakshathra_available = False
    print(f"❌ Nakshathra import error: {e}")

try:
    from tasks.divasam import divasam_calculation
    divasam_available = True
    print("✅ Divasam module imported successfully")
except ImportError as e:
    divasam_available = False
    print(f"❌ Divasam import error: {e}")

try:
    from tasks.livedhasha import livedhasha_calculation
    livedhasha_available = True
    print("✅ Livedhasha module imported successfully")
except ImportError as e:
    livedhasha_available = False
    print(f"❌ Livedhasha import error: {e}")

try:
    from tasks.nazhika import nazhika_calculation
    nazhika_available = True
    print("✅ Nazhika module imported successfully")
except ImportError as e:
    nazhika_available = False
    print(f"❌ Nazhika import error: {e}")

try:
    from tasks.sunrise import sunrise
    sunrise_available = True
    print("✅ Sunrise module imported successfully")
except ImportError as e:
    sunrise_available = False
    print(f"❌ Sunrise import error: {e}")

try:
    from tasks.raahu import raahu_calculation
    raahu_available = True
    print("✅ Raahu module imported successfully")
except ImportError as e:
    raahu_available = False
    print(f"❌ Raahu import error: {e}")

try:
    from tasks.shishtadhasha import shishtadhasha_calculation
    shishtadhasha_available = True
    print("✅ Shishtadhasha module imported successfully")
except ImportError as e:
    shishtadhasha_available = False
    print(f"❌ Shishtadhasha import error: {e}")

try:
    from tasks.sun import sun_nakshatra_calculation
    sun_nakshatra_available = True
    print("✅ Sun nakshatra module imported successfully")
except ImportError as e:
    sun_nakshatra_available = False
    print(f"❌ Sun nakshatra import error: {e}")

# Import ALL extras functions
try:
    from extras.grahanila import graha_nila_calculation
    graha_nila_available = True
    print("✅ Graha Nila module imported successfully")
except ImportError as e:
    graha_nila_available = False
    print(f"❌ Graha Nila import error: {e}")

try:
    from extras.grahadigri import graha_sphutam_calculation
    graha_sphutam_available = True
    print("✅ Grahadigri module imported successfully")
except ImportError as e:
    graha_sphutam_available = False
    print(f"❌ Grahadigri import error: {e}")

try:
    from extras.Shadwarga import shad_varga_calculation
    shad_varga_available = True
    print("✅ Shadwarga module imported successfully")
except ImportError as e:
    shad_varga_available = False
    print(f"❌ Shadwarga import error: {e}")

try:
    from extras.Bhavadigri import bhavasphutam_calculation
    bhavadigri_available = True
    print("✅ Bhavadigri module imported successfully")
except ImportError as e:
    bhavadigri_available = False
    print(f"❌ Bhavadigri import error: {e}")

try:
    from extras.ashtakavargam import ashtakavargam_calculation
    ashtakavargam_available = True
    print("✅ Ashtakavargam module imported successfully")
except ImportError as e:
    ashtakavargam_available = False
    print(f"❌ Ashtakavargam import error: {e}")

try:
    from extras.apahara import dasapaharam_calculation
    dasapaharam_available = True
    print("✅ Apahara module imported successfully")
except ImportError as e:
    dasapaharam_available = False
    print(f"❌ Apahara import error: {e}")

try:
    from extras.samaya import rasi_samayam_calculation
    rasi_samayam_available = True
    print("✅ Samaya module imported successfully")
except ImportError as e:
    rasi_samayam_available = False
    print(f"❌ Samaya import error: {e}")

try:
    from extras.kalahora import kalahora_calculation
    kalahora_available = True
    print("✅ Kalahora module imported successfully")
except ImportError as e:
    kalahora_available = False
    print(f"❌ Kalahora import error: {e}")

try:
    from extras.nakshatradi import nakshatradi_calculation
    nakshatradi_available = True
    print("✅ Nakshatradi module imported successfully")
except ImportError as e:
    nakshatradi_available = False
    print(f"❌ Nakshatradi import error: {e}")

def get_local_time(place_data):
    """Get current local time for a specific place"""
    try:
        timezone_str = place_data.get('timezone', 'Asia/Kolkata')
        proper_timezone = get_proper_timezone(timezone_str)
       
        tz = pytz.timezone(proper_timezone)
        local_time = datetime.datetime.now(tz)
       
        hour_12 = local_time.strftime('%I').lstrip('0')
        if hour_12 == '': hour_12 = '12'
        minute = local_time.strftime('%M')
        am_pm = local_time.strftime('%p')
       
        return {
            'year': local_time.year,
            'month': local_time.month,
            'day': local_time.day,
            'hour_24h': local_time.hour,
            'minute': local_time.minute,
            'hour_12h': int(hour_12),
            'ampm': am_pm,
            'local_time_12h': f"{hour_12}:{minute} {am_pm}",
            'timezone': proper_timezone,
            'local_datetime': local_time
        }
    except Exception as e:
        print(f"Error getting local time: {e}")
        tz = pytz.timezone('Asia/Kolkata')
        local_time = datetime.datetime.now(tz)
        hour_12 = local_time.strftime('%I').lstrip('0')
        if hour_12 == '': hour_12 = '12'
        return {
            'year': local_time.year,
            'month': local_time.month,
            'day': local_time.day,
            'hour_24h': local_time.hour,
            'minute': local_time.minute,
            'hour_12h': int(hour_12),
            'ampm': local_time.strftime('%p'),
            'local_time_12h': f"{hour_12}:{local_time.strftime('%M')} {local_time.strftime('%p')}",
            'timezone': 'Asia/Kolkata'
        }

def convert_to_24h(hour, ampm):
    """Convert 12-hour format to 24-hour format"""
    hour = int(hour)
    if ampm == 'PM' and hour != 12:
        return hour + 12
    elif ampm == 'AM' and hour == 12:
        return 0
    else:
        return hour

def find_place_by_name(place_name):
    """Find place by name"""
    if not place_name:
        return PLACES_DATA[0] if PLACES_DATA else None
   
    for place in PLACES_DATA:
        if place['name'] == place_name:
            return place
   
    return PLACES_DATA[0] if PLACES_DATA else None

def correct_timezone_in_results(results, calc_data):
    """
    ഫലങ്ങളിൽ നിന്ന് IST റഫറൻസ് നീക്കംചെയ്യുക
    """
    try:
        place_data = calc_data['place']
        timezone_str = place_data.get('timezone', 'Asia/Kolkata')
        proper_timezone = get_proper_timezone(timezone_str)
       
        if proper_timezone != 'Asia/Kolkata':
            corrected_results = {}
           
            for key, value in results.items():
                if isinstance(value, str):
                    value = value.replace('(IST)', f'({proper_timezone})')
                    value = value.replace('IST', proper_timezone)
                    value = value.replace('Indian Standard Time', proper_timezone)
                    value = value.replace('ഇന്ത്യൻ സ്റ്റാൻഡേർഡ് സമയം', proper_timezone)
                   
                    if '°' in value or 'രാശി' in value or 'ഭാഗം' in value:
                        lines = value.split('\n')
                        new_lines = []
                        timezone_added = False
                       
                        for i, line in enumerate(lines):
                            if ('°' in line or 'രാശി' in line or 'ഭാഗം' in line) and not timezone_added:
                                if 'സമയമേഖല' not in line and 'timezone' not in line.lower():
                                    line = f"{line} [{proper_timezone}]"
                                    timezone_added = True
                            new_lines.append(line)
                       
                        if not timezone_added:
                            new_lines.append(f"\nസമയമേഖല: {proper_timezone}")
                       
                        value = '\n'.join(new_lines)
               
                corrected_results[key] = value
           
            print(f"✅ ഫലങ്ങൾ തിരുത്തി: {proper_timezone}")
            return corrected_results
        else:
            print(f"✅ ഇന്ത്യയാണ്, മാറ്റമില്ല: {proper_timezone}")
            return results
       
    except Exception as e:
        print(f"❌ ഫലങ്ങൾ തിരുത്തുന്നതിൽ പിശക്: {e}")
        return results

def create_compatible_data(calc_data):
    """Create data format compatible with ALL task modules"""
    place_data = calc_data['place']
    timezone_str = place_data.get('timezone', 'Asia/Kolkata')
    proper_timezone = get_proper_timezone(timezone_str)
   
    compatible_data = {
        'year': calc_data['year'],
        'month': calc_data['month'],
        'day': calc_data['day'],
        'hour': calc_data.get('hour_12h', 12),
        'hour_12h': calc_data.get('hour_12h', 12),
        'hours_12h': calc_data.get('hour_12h', 12),
        'hour_24h': calc_data['hour_24h'],
        'hours_24h': calc_data['hour_24h'],
        'minute': calc_data['minute'],
        'ampm': calc_data.get('ampm', 'AM'),
       
        'place': place_data,
        'latitude': place_data['lat'],
        'lat': place_data['lat'],
        'lattitude': place_data['lat'],
        'longitude': place_data['lng'],
        'lng': place_data['lng'],
        'timezone': proper_timezone,
       
        'location': place_data['name'],
        'calculation_type': calc_data.get('calculation_type', 'auto')
    }
   
    print(f"📍 Calculation for: {place_data['name']}")
    print(f"   Date: {calc_data['day']}/{calc_data['month']}/{calc_data['year']}")
    print(f"   Time: {calc_data['hour_24h']}:{calc_data['minute']}")
    print(f"   Timezone: {timezone_str} -> {proper_timezone}")
   
    return compatible_data

def call_calculation_functions(calculation_data):
    """Call all calculation functions with ACTUAL place data"""
    results = {}
   
    compatible_data = create_compatible_data(calculation_data)
   
    task_functions = [
        ('കലിദിനം', kalidhinam_calculation, kalidhinam_available),
        ('കൊല്ലവർഷം', kollavarsham_calculation, kollavarsham_available),
        ('ശകവർഷം', shakavarsham_calculation, shakavarsham_available),
        ('ദശാഫലം', livedhasha_calculation, livedhasha_available),
        ('ജനന സമയം', nazhika_calculation, nazhika_available),
        ('ഉദയം', sunrise, sunrise_available),
        ('രാഹു കാലം', raahu_calculation, raahu_available),
        ('ശിഷ്ടദശ', shishtadhasha_calculation, shishtadhasha_available),
        ('സൂര്യനക്ഷത്രം', sun_nakshatra_calculation, sun_nakshatra_available),
    ]
   
    for name, func, available in task_functions:
        if available:
            try:
                result = func(compatible_data)
                results[name] = result
                print(f"✅ {name}: Success for {compatible_data['location']}")
            except Exception as e:
                results[name] = f"{name}: പിശക് - {str(e)}"
                print(f"❌ {name} error: {e}")
   
    if nakshathra_available:
        try:
            nakshathra_results = nakshathra_calculation(compatible_data)
            if isinstance(nakshathra_results, dict):
                results.update(nakshathra_results)
            print("✅ നക്ഷത്രം: Success")
        except Exception as e:
            results['നക്ഷത്രം'] = f"നക്ഷത്രം: പിശക് - {str(e)}"
   
    if divasam_available:
        try:
            divasam_results = divasam_calculation(compatible_data)
            if isinstance(divasam_results, dict):
                results.update(divasam_results)
            print("✅ ദിവസം: Success")
        except Exception as e:
            results['ദിവസം'] = f"ദിവസം: പിശക് - {str(e)}"
   
    corrected_results = correct_timezone_in_results(results, calculation_data)
   
    return corrected_results

@app.route('/')
def index():
    """Main page"""
    current_year = datetime.datetime.now().year
    return render_template('base.html', current_year=current_year)

# NEW ROUTE: Jathaka Fala
@app.route('/extras2/jathakafala')
def jathakafala_page():
    """Jathaka Fala page"""
    try:
        place_name = request.args.get('place', 'കണ്ണൂർ')
        place = find_place_by_name(place_name)
        
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        hour_24h = request.args.get('hour_24h')
        minute = request.args.get('minute')
        
        if year and month and day and hour_24h and minute:
            calc_data = {
                'day': int(day),
                'month': int(month),
                'year': int(year),
                'hour_24h': int(hour_24h),
                'minute': int(minute),
                'place': place
            }
        else:
            local_time = get_local_time(place)
            calc_data = {
                'day': local_time['day'],
                'month': local_time['month'],
                'year': local_time['year'],
                'hour_24h': local_time['hour_24h'],
                'minute': local_time['minute'],
                'place': place
            }
        
        # Import and run jathakafala calculation
        try:
            from extras2.jathakafala import jathakafala_calculation
            result = jathakafala_calculation(calc_data)
            return result
        except ImportError:
            return "ജാതക ഫലങ്ങൾ ഫയൽ ലഭ്യമല്ല"
        
    except Exception as e:
        return f"പിശക്: {str(e)}"

# NEW ROUTE: Vivahaporutham
@app.route('/porutha')
def porutha_page():
    """Vivahaporutham page"""
    try:
        # Import and show porutha page
        from porutha.porutha import main as porutha_main
        return porutha_main()
    except ImportError:
        return "വിവാഹപൊരുത്തം ഫയൽ ലഭ്യമല്ല"

# NEW ROUTE: Prashnam
@app.route('/extras3/mainprashna')
def prashna_page():
    """Prashnam page"""
    try:
        # Import and show mainprashna page
        from extras3.mainprashna import main as prashna_main
        return prashna_main()
    except ImportError:
        return "പ്രശ്നം ഫയൽ ലഭ്യമല്ല"

@app.route('/clean-cache')
def clean_cache_page():
    """Cache cleaning page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cache Cleaner</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .btn { display: block; width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 5px;
                   font-size: 16px; cursor: pointer; transition: background 0.3s; }
            .quick { background: #4CAF50; color: white; }
            .full { background: #2196F3; color: white; }
            .sessions { background: #ff9800; color: white; }
            .status { margin-top: 20px; padding: 15px; border-radius: 5px; display: none; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .back-btn { background: #6c757d; color: white; text-decoration: none; padding: 10px 20px;
                        border-radius: 5px; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧹 Cache Cleaner</h1>
            <p>Select cache cleaning option:</p>
           
            <button class="btn quick" onclick="cleanCache('quick')">⚡ Quick Clean</button>
            <button class="btn full" onclick="cleanCache('full')">🧹 Full Clean</button>
            <button class="btn sessions" onclick="cleanCache('sessions')">🗑️ Clean Sessions</button>
           
            <div id="status" class="status"></div>
            <a href="/" class="back-btn">← Back to App</a>
        </div>
       
        <script>
            function cleanCache(type) {
                const status = document.getElementById('status');
                status.style.display = 'block';
                status.className = 'status';
                status.innerHTML = 'Cleaning...';
               
                fetch('/clean-cache-action?type=' + type)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        status.className = 'status success';
                        status.innerHTML = '✅ ' + data.message;
                    } else {
                        status.className = 'status error';
                        status.innerHTML = '❌ ' + data.message;
                    }
                })
                .catch(error => {
                    status.className = 'status error';
                    status.innerHTML = '❌ Error: ' + error;
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/clean-cache-action')
def clean_cache_action():
    """Clean cache action endpoint"""
    try:
        clean_type = request.args.get('type', 'quick')
       
        if clean_type == 'full':
            success = clean_all_cache()
            message = "Full cache cleaned successfully!"
        elif clean_type == 'sessions':
            success = clean_flask_sessions()
            message = "Sessions cleaned successfully!"
        else:  # quick
            success = clean_all_cache()
            message = "Cache cleaned successfully!"
       
        return jsonify({
            'success': success,
            'message': message,
            'type': clean_type
        })
       
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/auto_calculate', methods=['POST'])
def auto_calculate():
    """Auto calculation with USER PROVIDED time"""
    try:
        data = request.get_json()
        place_data = data.get('place', PLACES_DATA[0])
       
        day = data.get('day')
        month = data.get('month')
        year = data.get('year')
        hour_12 = data.get('hour')
        minute = data.get('minute')
        ampm = data.get('ampm')
       
        if not all([day, month, year, hour_12, minute, ampm]):
            local_time = get_local_time(place_data)
            day = local_time['day']
            month = local_time['month']
            year = local_time['year']
            hour_12 = local_time['hour_12h']
            minute = local_time['minute']
            ampm = local_time['ampm']
            print("⚠️ No user time provided, using current time")
       
        hour_24h = convert_to_24h(hour_12, ampm)
       
        localized_dt = create_localized_datetime_for_place(year, month, day, hour_24h, minute, place_data)
       
        if hasattr(localized_dt, 'tzinfo') and localized_dt.tzinfo is not None:
            actual_local_date = localized_dt
            calc_day = actual_local_date.day
            calc_month = actual_local_date.month
            calc_year = actual_local_date.year
        else:
            calc_day = day
            calc_month = month
            calc_year = year
       
        calc_data = {
            'day': calc_day,
            'month': calc_month,
            'year': calc_year,
            'hour_24h': hour_24h,
            'minute': minute,
            'hour_12h': int(hour_12),
            'ampm': ampm,
            'place': place_data,
            'calculation_type': 'auto',
            'localized_datetime': localized_dt
        }
       
        print(f"🌍 Auto calculation for: {place_data['name']}")
        print(f"   User input: {day}/{month}/{year} {hour_12}:{minute} {ampm}")
        print(f"   Calculated: {calc_day}/{calc_month}/{calc_year} {hour_24h}:{minute}")
        print(f"   Timezone: {place_data.get('timezone', 'Asia/Kolkata')}")
       
        calculations = call_calculation_functions(calc_data)
       
        return jsonify({
            'success': True,
            'calculations': calculations,
            'location_used': place_data,
            'calculated_date': f"{calc_day}/{calc_month}/{calc_year}"
        })
       
    except Exception as e:
        print(f"❌ Auto calculate error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/calculate', methods=['POST'])
def calculate():
    """Manual calculation with ACTUAL place data"""
    try:
        data = request.get_json()
       
        day = int(data['day'])
        month = int(data['month'])
        year = int(data['year'])
        hour = int(data['hour'])
        minute = int(data['minute'])
        ampm = data['ampm']
        place_data = data['place']
       
        hour_24h = convert_to_24h(hour, ampm)
       
        localized_dt = create_localized_datetime_for_place(year, month, day, hour_24h, minute, place_data)
       
        if hasattr(localized_dt, 'tzinfo') and localized_dt.tzinfo is not None:
            actual_local_date = localized_dt
            calc_day = actual_local_date.day
            calc_month = actual_local_date.month
            calc_year = actual_local_date.year
        else:
            calc_day = day
            calc_month = month
            calc_year = year
       
        calc_data = {
            'day': calc_day,
            'month': calc_month,
            'year': calc_year,
            'hour_24h': hour_24h,
            'minute': minute,
            'hour_12h': hour,
            'ampm': ampm,
            'place': place_data,
            'calculation_type': 'manual',
            'localized_datetime': localized_dt
        }
       
        print(f"🌍 Manual calculation for ACTUAL place: {place_data['name']}")
        print(f"   Input: {day}/{month}/{year} {hour}:{minute} {ampm}")
        print(f"   Local: {calc_day}/{calc_month}/{calc_year} {hour_24h}:{minute}")
        print(f"   Timezone: {place_data.get('timezone', 'Asia/Kolkata')}")
       
        calculations = call_calculation_functions(calc_data)
       
        return jsonify({
            'success': True,
            'calculations': calculations,
            'location_used': place_data,
            'calculated_date': f"{calc_day}/{calc_month}/{calc_year}"
        })
       
    except Exception as e:
        print(f"❌ Manual calculate error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/extras_calculate', methods=['POST'])
def extras_calculate():
    """Calculate extras with ACTUAL place data"""
    try:
        data = request.get_json()
        selection = data.get('selection')
        place_data = data.get('place')
        calculation_type = data.get('calculation_type', 'auto')
       
        if calculation_type == 'manual':
            day = int(data['day'])
            month = int(data['month'])
            year = int(data['year'])
            hour_24h = int(data['hour_24h'])
            minute = int(data['minute'])
           
            localized_dt = create_localized_datetime_for_place(year, month, day, hour_24h, minute, place_data)
           
            if hasattr(localized_dt, 'tzinfo') and localized_dt.tzinfo is not None:
                actual_local_date = localized_dt
                calc_day = actual_local_date.day
                calc_month = actual_local_date.month
                calc_year = actual_local_date.year
            else:
                calc_day = day
                calc_month = month
                calc_year = year
           
            calc_data = {
                'day': calc_day,
                'month': calc_month,
                'year': calc_year,
                'hour_24h': hour_24h,
                'minute': minute,
                'place': place_data
            }
        else:
            local_time = get_local_time(place_data)
            calc_data = {
                'day': local_time['day'],
                'month': local_time['month'],
                'year': local_time['year'],
                'hour_24h': local_time['hour_24h'],
                'minute': local_time['minute'],
                'place': place_data
            }
       
        compatible_data = create_compatible_data(calc_data)
       
        result = ""
        if selection == 'graha_nila':
            result = graha_nila_calculation(compatible_data)
        elif selection == 'graha_sphutam':
            result = graha_sphutam_calculation(compatible_data)
        elif selection == 'shad_varga':
            result = shad_varga_calculation(compatible_data)
        elif selection == 'ashtakavargam':
            result = ashtakavargam_calculation(compatible_data)
        elif selection == 'bhavasphutam':
            result = bhavasphutam_calculation(compatible_data)
        elif selection == 'dasapaharam':
            result = dasapaharam_calculation(compatible_data)
        elif selection == 'rasi_samayam':
            result = rasi_samayam_calculation(compatible_data)
        elif selection == 'kalahora':
            result = kalahora_calculation(compatible_data)
        elif selection == 'nakshatradi':
            result = nakshatradi_calculation(compatible_data)
        else:
            result = f"അജ്ഞാതമായ ഗണിതം: {selection}"
       
        if isinstance(result, str):
            timezone_str = place_data.get('timezone', 'Asia/Kolkata')
            proper_timezone = get_proper_timezone(timezone_str)
           
            if proper_timezone != 'Asia/Kolkata':
                result = result.replace('(IST)', f'({proper_timezone})')
                result = result.replace('IST', proper_timezone)
                result = result.replace('Indian Standard Time', proper_timezone)
                result = result.replace('ഇന്ത്യൻ സ്റ്റാൻഡേർഡ് സമയം', proper_timezone)
               
                if 'സമയമേഖല:' not in result and 'timezone:' not in result.lower():
                    result = f"{result}\n\nസമയമേഖല: {proper_timezone}"
       
        return jsonify({
            'success': True,
            'result': result,
            'selection': selection
        })
       
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/extras_result/<selection>')
def extras_result(selection):
    """Extras result with ACTUAL place data"""
    try:
        place_name = request.args.get('place', 'കണ്ണൂർ')
        place = find_place_by_name(place_name)
       
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        hour_24h = request.args.get('hour_24h')
        minute = request.args.get('minute')
       
        if year and month and day and hour_24h and minute:
            calc_data = {
                'day': int(day),
                'month': int(month),
                'year': int(year),
                'hour_24h': int(hour_24h),
                'minute': int(minute),
                'place': place
            }
        else:
            local_time = get_local_time(place)
            calc_data = {
                'day': local_time['day'],
                'month': local_time['month'],
                'year': local_time['year'],
                'hour_24h': local_time['hour_24h'],
                'minute': local_time['minute'],
                'place': place
            }
       
        compatible_data = create_compatible_data(calc_data)
       
        if selection == 'graha_nila':
            result = graha_nila_calculation(compatible_data)
        elif selection == 'graha_sphutam':
            result = graha_sphutam_calculation(compatible_data)
        elif selection == 'shad_varga':
            result = shad_varga_calculation(compatible_data)
        elif selection == 'ashtakavargam':
            result = ashtakavargam_calculation(compatible_data)
        elif selection == 'bhavasphutam':
            result = bhavasphutam_calculation(compatible_data)
        elif selection == 'dasapaharam':
            result = dasapaharam_calculation(compatible_data)
        elif selection == 'rasi_samayam':
            result = rasi_samayam_calculation(compatible_data)
        elif selection == 'kalahora':
            result = kalahora_calculation(compatible_data)
        elif selection == 'nakshatradi':
            result = nakshatradi_calculation(compatible_data)
        else:
            result = f"അജ്ഞാതമായ ഗണിതം: {selection}"
       
        if isinstance(result, str):
            timezone_str = place.get('timezone', 'Asia/Kolkata')
            proper_timezone = get_proper_timezone(timezone_str)
           
            if proper_timezone != 'Asia/Kolkata':
                result = result.replace('(IST)', f'({proper_timezone})')
                result = result.replace('IST', proper_timezone)
                result = result.replace('Indian Standard Time', proper_timezone)
                result = result.replace('ഇന്ത്യൻ സ്റ്റാൻഡേർഡ് സമയം', proper_timezone)
               
                if 'സമയമേഖല:' not in result and 'timezone:' not in result.lower():
                    result = f"{result}\n\nസമയമേഖല: {proper_timezone}"
       
        return result
       
    except Exception as e:
        return f"പിശക്: {str(e)}"

@app.route('/search_places')
def search_places():
    """Search places"""
    query = request.args.get('q', '').lower()
   
    if query:
        results = [place for place in PLACES_DATA if query in place['name'].lower()]
    else:
        results = PLACES_DATA
   
    return jsonify(results)

if __name__ == '__main__':
    print("🚀 Starting Horoscope App...")
    print(f"📊 Loaded {len(PLACES_DATA)} places")
    print("✅ ACTUAL place calculations enabled")
    print("🌍 Features:")
    print("   - New: Compact form layout")
    print("   - New: Hide top controls when form is open")
    print("   - New: Ganitham dropdown with Malayalam options")
    print("   - New: Jathaka Fala, Vivahaporutham, Prashnam routes")
    print("   - Real local time for each place")
    print("   - Proper timezone handling")
    print("   - ✅ IST references removed from results for non-Indian timezones")
    print("   - ✅ Cache cleaning available at /clean-cache")
    print("   - ✅ Fixed syntax error in line 475")
    app.run(debug=True, host='0.0.0.0', port=5000)
