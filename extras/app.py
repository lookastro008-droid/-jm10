from flask import Flask, render_template, request, jsonify
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
import math

# Import ALL task functions from previous code
try:
    from tasks.kalidhinam import kalidhinam_calculation
    kalidhinam_available = True
    print("✅ Kalidhinam module imported successfully")
except ImportError as e:
    kalidhinam_available = False
    print(f"❌ Kalidhinam import error: {e}")
    def kalidhinam_calculation(data):
        return f"കലിദിനം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

try:
    from tasks.kollavarsham import kollavarsham_calculation
    kollavarsham_available = True
    print("✅ Kollavarsham module imported successfully")
except ImportError as e:
    kollavarsham_available = False
    print(f"❌ Kollavarsham import error: {e}")
    def kollavarsham_calculation(data):
        return f"കൊല്ലവർഷം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

try:
    from tasks.shakavarsham import shakavarsham_calculation
    shakavarsham_available = True
    print("✅ Shakavarsham module imported successfully")
except ImportError as e:
    shakavarsham_available = False
    print(f"❌ Shakavarsham import error: {e}")
    def shakavarsham_calculation(data):
        return f"ശകവർഷം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

try:
    from tasks.nakshathra import nakshathra_calculation
    nakshathra_available = True
    print("✅ Nakshathra module imported successfully")
except ImportError as e:
    nakshathra_available = False
    print(f"❌ Nakshathra import error: {e}")
    def nakshathra_calculation(data):
        return {
            'നക്ഷത്രം': f"നക്ഷത്രം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}",
            'തിഥി': f"തിഥി: കണക്കാക്കാനായില്ല",
            'കരണം': f"കരണം: കണക്കാക്കാനായില്ല",
            'യോഗം': f"യോഗം: കണക്കാക്കാനായില്ല"
        }

try:
    from tasks.divasam import divasam_calculation
    divasam_available = True
    print("✅ Divasam module imported successfully")
except ImportError as e:
    divasam_available = False
    print(f"❌ Divasam import error: {e}")
    def divasam_calculation(data):
        return {
            'ദിവസം': f"ദിവസം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}",
            'പ്രായം': f"പ്രായം: കണക്കാക്കാനായില്ല"
        }

try:
    from tasks.livedhasha import livedhasha_calculation
    livedhasha_available = True
    print("✅ Livedhasha module imported successfully")
except ImportError as e:
    livedhasha_available = False
    print(f"❌ Livedhasha import error: {e}")
    def livedhasha_calculation(data):
        return "ദശാഫലം: കണക്കാക്കാനായില്ല"

try:
    from tasks.nazhika import nazhika_calculation
    nazhika_available = True
    print("✅ Nazhika module imported successfully")
except ImportError as e:
    nazhika_available = False
    print(f"❌ Nazhika import error: {e}")
    def nazhika_calculation(data):
        return f"ജനന സമയം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

try:
    from tasks.sunrise import sunrise
    sunrise_available = True
    print("✅ Sunrise module imported successfully")
except ImportError as e:
    sunrise_available = False
    print(f"❌ Sunrise import error: {e}")
    def sunrise(data):
        return f"ഉദയം: കണക്കാക്കാനായില്ല\nഅസ്തമയം: കണക്കാക്കാനായില്ല"

# RAHU MODULE - FIXED IMPORT
try:
    from tasks.raahu import raahu_calculation
    raahu_available = True
    print("✅ Raahu module imported successfully")
except ImportError as e:
    raahu_available = False
    print(f"❌ Raahu import error: {e}")
    def raahu_calculation(data):
        return "രാഹു കാലം: കണക്കാക്കാനായില്ല\nഗുളിക കാലം: കണക്കാക്കാനായില്ല\nയമകണ്ട കാലം: കണക്കാക്കാനായില്ല"

try:
    from tasks.shishtadhasha import shishtadhasha_calculation
    shishtadhasha_available = True
    print("✅ Shishtadhasha module imported successfully")
except ImportError as e:
    shishtadhasha_available = False
    print(f"❌ Shishtadhasha import error: {e}")
    def shishtadhasha_calculation(data):
        return f"ശിഷ്ടദശ: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

try:
    from tasks.sun import sun_nakshatra_calculation
    sun_nakshatra_available = True
    print("✅ Sun nakshatra module imported successfully")
except ImportError as e:
    sun_nakshatra_available = False
    print(f"❌ Sun nakshatra import error: {e}")
    def sun_nakshatra_calculation(data):
        return f"സൂര്യനക്ഷത്രം: കണക്കാക്കാനായില്ല - {data['day']}/{data['month']}/{data['year']}"

# Import ALL extras functions from previous code
try:
    from extras.grahanila import graha_nila_calculation
    graha_nila_available = True
    print("✅ Graha Nila module imported successfully")
except ImportError as e:
    graha_nila_available = False
    print(f"❌ Graha Nila import error: {e}")
    def graha_nila_calculation(data):
        return "ഗ്രഹനില: കണക്കാക്കാനായില്ല"

# Import extras functions - GRAHA DIGRI (SPHUTAM)
try:
    from extras.grahadigri import graha_sphutam_calculation
    graha_sphutam_available = True
    print("✅ Graha Sphutam (Grahadigri) module imported successfully")
except ImportError as e:
    graha_sphutam_available = False
    print(f"❌ Graha Sphutam import error: {e}")
    def graha_sphutam_calculation(data):
        return "ഗ്രഹസ്ഫുടങ്ങൾ: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - SHAD VARGA
try:
    from extras.Shadwarga import shad_varga_calculation
    shad_varga_available = True
    print("✅ Shad Varga module imported successfully")
except ImportError as e:
    shad_varga_available = False
    print(f"❌ Shad Varga import error: {e}")
    def shad_varga_calculation(data):
        return "ഷഡ് വർഗ്ഗങ്ങൾ: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - BHAVA SPHUTAM
try:
    from extras.Bhavadigri import bhavasphutam_calculation
    bhavasphutam_available = True
    print("✅ Bhavasphutam module imported successfully")
except ImportError as e:
    bhavasphutam_available = False
    print(f"❌ Bhavasphutam import error: {e}")
    def bhavasphutam_calculation(data):
        return "ഭാവസ്ഫുടങ്ങൾ: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - ASHTAKAVARGAM
try:
    from extras.ashtakavargam import ashtakavargam_calculation
    ashtakavargam_available = True
    print("✅ Ashtakavargam module imported successfully")
except ImportError as e:
    ashtakavargam_available = False
    print(f"❌ Ashtakavargam import error: {e}")
    def ashtakavargam_calculation(data):
        return "അഷ്ടകവർഗ്ഗം: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - DASAPAHARAM
try:
    from extras.apahara import dasapaharam_calculation
    dasapaharam_available = True
    print("✅ Dasapaharam module imported successfully")
except ImportError as e:
    dasapaharam_available = False
    print(f"❌ Dasapaharam import error: {e}")
    def dasapaharam_calculation(data):
        return "ദശാപഹാരങ്ങൾ: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - RASI SAMAYAM
try:
    from extras.samaya import rasi_samayam_calculation
    rasi_samayam_available = True
    print("✅ Rasi Samayam module imported successfully")
except ImportError as e:
    rasi_samayam_available = False
    print(f"❌ Rasi Samayam import error: {e}")
    def rasi_samayam_calculation(data):
        return "രാശി സമയങ്ങൾ: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - KALAHORA
try:
    from extras.kalahora import kalahora_calculation
    kalahora_available = True
    print("✅ Kalahora module imported successfully")
except ImportError as e:
    kalahora_available = False
    print(f"❌ Kalahora import error: {e}")
    def kalahora_calculation(data):
        return "കാലഹോര: കണക്കാക്കാനായില്ല"

# Import NEW extras functions - NAKSHATRADI
try:
    from extras.nakshatradi import nakshatradi_calculation
    nakshatradi_available = True
    print("✅ Nakshatradi module imported successfully")
except ImportError as e:
    nakshatradi_available = False
    print(f"❌ Nakshatradi import error: {e}")
    def nakshatradi_calculation(data):
        return "നക്ഷത്രാദി വിശേഷം: കണക്കാക്കാനായില്ല"

# Import ALL places data
try:
    from places.places_data import PLACES_DATA
    print("✅ Places data imported successfully")
except ImportError as e:
    print(f"❌ Places data import error: {e}")
    PLACES_DATA = [
        {"name": "കണ്ണൂർ", "lat": 11.8745, "lng": 75.3704, "timezone": "Asia/Kolkata"},
        {"name": "തിരുവനന്തപുരം", "lat": 8.5241, "lng": 76.9366, "timezone": "Asia/Kolkata"},
        {"name": "കോഴിക്കോട്", "lat": 11.2588, "lng": 75.7804, "timezone": "Asia/Kolkata"},
        {"name": "ആലപ്പുഴ", "lat": 9.4981, "lng": 76.3388, "timezone": "Asia/Kolkata"},
        {"name": "കൊല്ലം", "lat": 8.8932, "lng": 76.6141, "timezone": "Asia/Kolkata"},
        {"name": "പത്തനംതിട്ട", "lat": 9.2647, "lng": 76.7870, "timezone": "Asia/Kolkata"},
        {"name": "ഇടുക്കി", "lat": 9.8480, "lng": 76.9650, "timezone": "Asia/Kolkata"},
        {"name": "എറണാകുളം", "lat": 10.0000, "lng": 76.5000, "timezone": "Asia/Kolkata"},
        {"name": "തൃശൂർ", "lat": 10.5276, "lng": 76.2144, "timezone": "Asia/Kolkata"},
        {"name": "പാലക്കാട്", "lat": 10.7867, "lng": 76.6548, "timezone": "Asia/Kolkata"},
        {"name": "മലപ്പുറം", "lat": 11.0732, "lng": 76.0730, "timezone": "Asia/Kolkata"},
        {"name": "വയനാട്", "lat": 11.7050, "lng": 76.0833, "timezone": "Asia/Kolkata"},
        {"name": "കോട്ടയം", "lat": 9.5916, "lng": 76.5222, "timezone": "Asia/Kolkata"}
    ]

app = Flask(__name__)

# Initialize timezone finder
tf = TimezoneFinder()

def get_timezone_from_coords(lat, lng):
    """Get timezone from coordinates"""
    try:
        timezone_str = tf.timezone_at(lat=lat, lng=lng)
        if timezone_str:
            return timezone_str
        else:
            return "Asia/Kolkata"  # Default fallback
    except Exception as e:
        print(f"Error getting timezone from coords: {e}")
        return "Asia/Kolkata"

def create_localized_datetime(year, month, day, hour, minute, timezone_str):
    """Create a timezone-aware datetime object for the specified location"""
    try:
        # Create naive datetime
        naive_dt = datetime(year, month, day, hour, minute)
        
        # Localize to the specified timezone
        local_tz = pytz.timezone(timezone_str)
        localized_dt = local_tz.localize(naive_dt)
        
        return localized_dt
    except Exception as e:
        print(f"Error creating localized datetime: {e}")
        # Fallback to UTC
        return datetime(year, month, day, hour, minute).replace(tzinfo=pytz.UTC)

def convert_to_24h(hour, ampm):
    """Convert 12-hour format to 24-hour format"""
    hour = int(hour)
    if ampm == 'PM' and hour != 12:
        return hour + 12
    elif ampm == 'AM' and hour == 12:
        return 0
    else:
        return hour

def prepare_calculation_data(date_data, place, calculation_type='manual'):
    """Prepare calculation data with proper timezone handling"""
    try:
        # Extract date and time components
        year = int(date_data['year'])
        month = int(date_data['month'])
        day = int(date_data['day'])
        
        # Handle time input (could be 12h or 24h format)
        if 'hour_24h' in date_data:
            hour_24h = int(date_data['hour_24h'])
        else:
            hour_24h = convert_to_24h(date_data['hour'], date_data['ampm'])
        
        minute = int(date_data['minute'])
        
        # Get timezone from place or calculate from coordinates
        if 'timezone' in place:
            timezone_str = place['timezone']
        else:
            timezone_str = get_timezone_from_coords(place['lat'], place['lng'])
        
        # Create localized datetime
        localized_dt = create_localized_datetime(year, month, day, hour_24h, minute, timezone_str)
        
        # Convert to UTC for internal calculations
        utc_dt = localized_dt.astimezone(pytz.UTC)
        
        # Prepare data for calculation functions
        calculation_data = {
            # Original date components
            'year': year,
            'month': month,
            'day': day,
            'hour_24h': hour_24h,
            'minute': minute,
            
            # Timezone information
            'timezone': timezone_str,
            'localized_datetime': localized_dt,
            'utc_datetime': utc_dt,
            
            # Location information
            'place': place,
            'latitude': place['lat'],
            'longitude': place['lng'],
            
            # Calculation metadata
            'calculation_type': calculation_type,
            'time_source': 'localized'
        }
        
        # Add 12h format if available
        if 'hour' in date_data and 'ampm' in date_data:
            calculation_data['hour_12h'] = date_data['hour']
            calculation_data['ampm'] = date_data['ampm']
        
        print(f"📍 Prepared calculation data for {place['name']}:")
        print(f"   - Local time: {localized_dt.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"   - UTC time: {utc_dt.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"   - Timezone: {timezone_str}")
        print(f"   - Coordinates: {place['lat']}, {place['lng']}")
        
        return calculation_data
        
    except Exception as e:
        print(f"Error preparing calculation data: {e}")
        # Fallback to simple data preparation
        return {
            'year': int(date_data['year']),
            'month': int(date_data['month']),
            'day': int(date_data['day']),
            'hour_24h': int(date_data.get('hour_24h', convert_to_24h(date_data['hour'], date_data['ampm']))),
            'minute': int(date_data['minute']),
            'place': place,
            'latitude': place['lat'],
            'longitude': place['lng'],
            'timezone': place.get('timezone', 'Asia/Kolkata'),
            'calculation_type': calculation_type,
            'time_source': 'fallback'
        }

@app.route('/')
def index():
    current_year = datetime.utcnow().year
    # Get current date and time for default display
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    default_place = PLACES_DATA[0]
    timezone_str = default_place.get('timezone', get_timezone_from_coords(default_place['lat'], default_place['lng']))
    local_tz = pytz.timezone(timezone_str)
    local_time = utc_now.astimezone(local_tz)
    
    return render_template('base.html', 
                         current_year=current_year,
                         places_data=PLACES_DATA,
                         default_place=default_place,
                         current_date=local_time.strftime('%Y-%m-%d'),
                         current_time=local_time.strftime('%I:%M %p'))

@app.route('/search_places')
def search_places():
    query = request.args.get('q', '').lower()
    if query:
        results = [place for place in PLACES_DATA if query in place['name'].lower()]
    else:
        results = PLACES_DATA
    return jsonify(results)

@app.route('/get_current_time', methods=['POST'])
def get_current_time():
    """Get current date and time for selected place - NEW ROUTE FOR DEFAULT DOB"""
    try:
        data = request.json
        place = data.get('place', PLACES_DATA[0])
        
        # Get current UTC time
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        
        # Convert to local timezone of the selected place
        timezone_str = place.get('timezone', get_timezone_from_coords(place['lat'], place['lng']))
        local_tz = pytz.timezone(timezone_str)
        local_time = utc_now.astimezone(local_tz)
        
        hour_12 = local_time.strftime('%I').lstrip('0')
        if hour_12 == '': hour_12 = '12'
        
        return jsonify({
            'success': True,
            'year': local_time.year,
            'month': local_time.month,
            'day': local_time.day,
            'hour': hour_12,
            'minute': local_time.minute,
            'ampm': local_time.strftime('%p'),
            'timezone': timezone_str,
            'local_time_display': local_time.strftime('%Y-%m-%d %H:%M %Z')
        })
        
    except Exception as e:
        print(f"Error in get_current_time: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/auto_calculate', methods=['POST'])
def auto_calculate():
    """Auto calculate with current SERVER time based on selected location"""
    try:
        data = request.json
        place = data.get('place', PLACES_DATA[0])
        
        print(f"🔍 Auto calculate called with place: {place['name']}")
        
        # Get current UTC time
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        
        # Convert to local timezone of the selected place
        timezone_str = place.get('timezone', get_timezone_from_coords(place['lat'], place['lng']))
        local_tz = pytz.timezone(timezone_str)
        local_time = utc_now.astimezone(local_tz)
        
        # Prepare date data for calculation
        date_data = {
            'year': local_time.year,
            'month': local_time.month,
            'day': local_time.day,
            'hour_24h': local_time.hour,
            'minute': local_time.minute
        }
        
        # Prepare calculation data with proper timezone
        calculation_data = prepare_calculation_data(date_data, place, 'auto')
        
        print(f"📊 Calling task functions with LOCALIZED time")
        print(f"   - Local Date: {calculation_data['day']}/{calculation_data['month']}/{calculation_data['year']}")
        print(f"   - Local Time: {local_time.strftime('%H:%M')} ({timezone_str})")
        print(f"   - Location: {calculation_data['place']['name']}")
        
        # Call calculation functions with error handling
        results = call_calculation_functions(calculation_data)
        
        return jsonify({
            'success': True, 
            'calculations': results, 
            'location_used': place,
            'local_time': {
                'year': local_time.year,
                'month': local_time.month,
                'day': local_time.day,
                'hour_24h': local_time.hour,
                'minute': local_time.minute,
                'timezone': timezone_str,
                'local_time_display': local_time.strftime('%Y-%m-%d %H:%M %Z')
            },
            'time_source': 'localized'
        })
        
    except Exception as e:
        print(f"❌ Error in auto_calculate: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/calculate', methods=['POST'])
def calculate():
    """Calculate horoscope based on form data with proper timezone handling"""
    try:
        data = request.json
        print(f"🔍 Calculate called with form data")
        print(f"   - Date: {data.get('day')}/{data.get('month')}/{data.get('year')}")
        print(f"   - Time: {data.get('hour')}:{data.get('minute')} {data.get('ampm')}")
        
        # Extract form data
        day = data.get('day')
        month = data.get('month')
        year = data.get('year')
        hour = data.get('hour')
        minute = data.get('minute')
        ampm = data.get('ampm')
        place = data.get('place', PLACES_DATA[0])
        
        if not all([day, month, year, hour, minute, ampm]):
            return jsonify({'success': False, 'error': 'എല്ലാ ഫീൽഡുകളും ആവശ്യമാണ്'})
        
        # Prepare date data
        date_data = {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'ampm': ampm
        }
        
        # Prepare calculation data with proper timezone
        calculation_data = prepare_calculation_data(date_data, place, 'manual')
        
        print(f"📊 Calling task functions with MANUAL data")
        print(f"   - Manual Date: {day}/{month}/{year}")
        print(f"   - Manual Time: {hour}:{minute} {ampm}")
        print(f"   - Location: {calculation_data['place']['name']}")
        print(f"   - Timezone: {calculation_data['timezone']}")
        
        # Call calculation functions with error handling
        results = call_calculation_functions(calculation_data)
        
        return jsonify({
            'success': True, 
            'calculations': results, 
            'location_used': place,
            'time_source': 'localized'
        })
        
    except Exception as e:
        print(f"❌ Error in calculate: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def call_calculation_functions(calculation_data):
    """Call all calculation functions with proper error handling"""
    results = {}
    
    # Define ALL calculation functions to call (from previous code)
    calculations = [
        ('കൊല്ലവർഷം', kollavarsham_calculation),
        ('ശകവർഷം', shakavarsham_calculation),
        ('കലിദിനം', kalidhinam_calculation),
        ('നക്ഷത്രം', nakshathra_calculation),
        ('ദിവസം', divasam_calculation),
        ('ശിഷ്ടദശ', shishtadhasha_calculation),
        ('ദശാഫലം', livedhasha_calculation),
        ('ജനന സമയം', nazhika_calculation),
        ('ഉദയം', sunrise),
        ('രാഹു കാലം', raahu_calculation),
        ('സൂര്യനക്ഷത്രം', sun_nakshatra_calculation)
    ]
    
    # Call individual functions
    for name, func in calculations:
        try:
            if func == nakshathra_calculation:
                # Special handling for nakshathra which returns multiple values
                nakshathra_results = func(calculation_data)
                results['നക്ഷത്രം'] = nakshathra_results.get('നക്ഷത്രം', 'കണക്കാക്കാനായില്ല')
                results['തിഥി'] = nakshathra_results.get('തിഥി', 'കണക്കാക്കാനായില്ല')
                results['കരണം'] = nakshathra_results.get('കരണം', 'കണക്കാക്കാനായില്ല')
                results['യോഗം'] = nakshathra_results.get('യോഗം', 'കണക്കാക്കാനായില്ല')
            elif func == divasam_calculation:
                # Special handling for divasam which returns multiple values
                divasam_results = func(calculation_data)
                results['ദിവസം'] = divasam_results.get('ദിവസം', 'കണക്കാക്കാനായില്ല')
                results['പ്രായം'] = divasam_results.get('പ്രായം', 'കണക്കാക്കാനായില്ല')
            else:
                result = func(calculation_data)
                results[name] = result
        except Exception as e:
            error_msg = f"{name}: പിശക് - {str(e)}"
            results[name] = error_msg
            print(f"❌ {name} calculation error: {e}")
    
    return results

@app.route('/extras_calculate', methods=['POST'])
def extras_calculate():
    """Calculate extras based on dropdown selection with proper timezone handling"""
    try:
        data = request.json
        selection = data.get('selection')
        place = data.get('place', PLACES_DATA[0])
        
        print(f"🔍 Extras calculate called with selection: {selection}")
        print(f"   - Place: {place['name']}")
        
        # Prepare calculation data based on input type
        if data.get('day') and data.get('month') and data.get('year') and data.get('hour_24h') is not None:
            # Use manual form data
            date_data = {
                'year': data.get('year'),
                'month': data.get('month'),
                'day': data.get('day'),
                'hour_24h': data.get('hour_24h'),
                'minute': data.get('minute')
            }
            calculation_data = prepare_calculation_data(date_data, place, 'manual')
            print(f"   - 📝 Using MANUAL data with timezone: {calculation_data['timezone']}")
        else:
            # Use current time for the selected location
            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            timezone_str = place.get('timezone', get_timezone_from_coords(place['lat'], place['lng']))
            local_tz = pytz.timezone(timezone_str)
            local_time = utc_now.astimezone(local_tz)
            
            date_data = {
                'year': local_time.year,
                'month': local_time.month,
                'day': local_time.day,
                'hour_24h': local_time.hour,
                'minute': local_time.minute
            }
            calculation_data = prepare_calculation_data(date_data, place, 'auto')
            print(f"   - 🔄 Using AUTO data with timezone: {calculation_data['timezone']}")
        
        # Call the appropriate extras function
        result = call_extras_function(selection, calculation_data)
        
        return jsonify({
            'success': True,
            'result': result,
            'selection': selection,
            'location_used': place,
            'calculation_data': {
                'year': calculation_data['year'],
                'month': calculation_data['month'],
                'day': calculation_data['day'],
                'hour_24h': calculation_data['hour_24h'],
                'minute': calculation_data['minute'],
                'timezone': calculation_data['timezone'],
                'latitude': calculation_data['latitude'],
                'longitude': calculation_data['longitude']
            }
        })
        
    except Exception as e:
        print(f"❌ Error in extras_calculate: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def call_extras_function(selection, calculation_data):
    """Call the appropriate extras calculation function"""
    try:
        if selection == 'graha_nila':
            return graha_nila_calculation(calculation_data)
        elif selection == 'graha_sphutam':
            return graha_sphutam_calculation(calculation_data)
        elif selection == 'shad_varga':
            return shad_varga_calculation(calculation_data)
        elif selection == 'ashtakavargam':
            return ashtakavargam_calculation(calculation_data)
        elif selection == 'bhavasphutam':
            return bhavasphutam_calculation(calculation_data)
        elif selection == 'dasapaharam':
            return dasapaharam_calculation(calculation_data)
        elif selection == 'rasi_samayam':
            return rasi_samayam_calculation(calculation_data)
        elif selection == 'kalahora':
            return kalahora_calculation(calculation_data)
        elif selection == 'nakshatradi':
            return nakshatradi_calculation(calculation_data)
        else:
            return f"അജ്ഞാതമായ ഗണിതം: {selection}"
    except Exception as e:
        error_msg = f"പിശക്: {str(e)}"
        print(f"❌ Extras calculation error for {selection}: {e}")
        return error_msg

@app.route('/extras_result/<selection>')
def extras_result(selection):
    """Render individual extras result page with proper timezone handling"""
    try:
        # Get parameters from URL
        place_name = request.args.get('place', 'കണ്ണൂർ')
        place = next((p for p in PLACES_DATA if p['name'] == place_name), PLACES_DATA[0])
        
        # Get date and time from URL parameters
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        hour_24h = request.args.get('hour_24h')
        minute = request.args.get('minute')
        
        if year and month and day and hour_24h and minute:
            # Use provided manual data
            date_data = {
                'year': int(year),
                'month': int(month),
                'day': int(day),
                'hour_24h': int(hour_24h),
                'minute': int(minute)
            }
            calculation_data = prepare_calculation_data(date_data, place, 'manual')
            print(f"📝 Extras result with MANUAL data: {calculation_data}")
        else:
            # Use current time for the location
            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            timezone_str = place.get('timezone', get_timezone_from_coords(place['lat'], place['lng']))
            local_tz = pytz.timezone(timezone_str)
            local_time = utc_now.astimezone(local_tz)
            
            date_data = {
                'year': local_time.year,
                'month': local_time.month,
                'day': local_time.day,
                'hour_24h': local_time.hour,
                'minute': local_time.minute
            }
            calculation_data = prepare_calculation_data(date_data, place, 'auto')
            print(f"🔄 Extras result with AUTO data: {calculation_data}")
        
        # Call the appropriate calculation function
        result = call_extras_function(selection, calculation_data)
        return result
        
    except Exception as e:
        print(f"❌ Error in extras_result: {str(e)}")
        return f"പിശക്: {str(e)}"

if __name__ == '__main__':
    print("🚀 Starting Horoscope App...")
    print("🔄 COMPLETELY REWRITTEN: Timezone handling system")
    print("📍 NEW: Automatic timezone detection from coordinates")
    print("🌍 NEW: Proper localized datetime calculations")
    print("⏰ ALL calculations now use LOCAL timezone of the specified place")
    print("📊 Module availability status:")
    print(f"   - Kollavarsham: {kollavarsham_available}")
    print(f"   - Shakavarsham: {shakavarsham_available}")
    print(f"   - Kalidhinam: {kalidhinam_available}")
    print(f"   - Nakshathra: {nakshathra_available}")
    print(f"   - Divasam: {divasam_available}")
    print(f"   - Livedhasha: {livedhasha_available}")
    print(f"   - Nazhika: {nazhika_available}")
    print(f"   - Sunrise: {sunrise_available}")
    print(f"   - Raahu: {raahu_available}")
    print(f"   - Shishtadhasha: {shishtadhasha_available}")
    print(f"   - Sun nakshatra: {sun_nakshatra_available}")
    print("📁 Extras modules available:")
    print(f"   - Graha Nila: {graha_nila_available}")
    print(f"   - Graha Sphutam: {graha_sphutam_available}")
    print(f"   - Shad Varga: {shad_varga_available}")
    print(f"   - Ashtakavargam: {ashtakavargam_available}")
    print(f"   - Bhavasphutam: {bhavasphutam_available}")
    print(f"   - Dasapaharam: {dasapaharam_available}")
    print(f"   - Rasi Samayam: {rasi_samayam_available}")
    print(f"   - Kalahora: {kalahora_available}")
    print(f"   - Nakshatradi: {nakshatradi_available}")
    print("✅ READY: All calculations now properly use local timezone")
    print("🎯 NEW: Default DOB section added to base.html")
    print("🔄 NEW: /get_current_time route for default DOB functionality")
    print("📈 ENHANCED: All previous modules and routes preserved")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
