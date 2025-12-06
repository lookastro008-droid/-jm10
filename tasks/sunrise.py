from astral import LocationInfo
from astral.sun import sun
import datetime
import pytz

def sunrise(calculation_data):
    """
    Calculate sunrise and sunset times for a given location and date
    using the astral library.
    
    Args:
        calculation_data (dict): Contains date and location information
        
    Returns:
        str: Formatted sunrise and sunset times
    """
    try:
        # Extract location data
        place_name = calculation_data.get('location', 'Unknown')
        latitude = calculation_data.get('latitude', 
                      calculation_data.get('lat', 
                      calculation_data.get('lattitude', 0)))
        longitude = calculation_data.get('longitude', 
                       calculation_data.get('lng', 
                       calculation_data.get('longitude', 0)))
        timezone_str = calculation_data.get('timezone', 'Asia/Kolkata')
        
        # Extract date
        year = calculation_data.get('year', datetime.datetime.now().year)
        month = calculation_data.get('month', datetime.datetime.now().month)
        day = calculation_data.get('day', datetime.datetime.now().day)
        
        # Validate coordinates
        if latitude == 0 or longitude == 0:
            return "സ്ഥലത്തിന്റെ അക്ഷാംശ/രേഖാംശ വിവരങ്ങൾ ലഭ്യമല്ല"
        
        # Create date object
        date_obj = datetime.date(year, month, day)
        
        # Get timezone
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        # Create location info
        location = LocationInfo(
            name=place_name,
            region="India",
            timezone=timezone_str,
            latitude=latitude,
            longitude=longitude
        )
        
        # Calculate sun times
        s = sun(location.observer, date=date_obj, tzinfo=tz)
        
        # Extract sunrise and sunset times
        sunrise_time = s['sunrise']
        sunset_time = s['sunset']
        
        # Format times to 12-hour format with AM/PM
        def format_time(dt):
            hour = dt.hour
            minute = dt.minute
            
            # Convert to 12-hour format
            if hour == 0:
                hour_12 = 12
                period = "AM"
            elif hour < 12:
                hour_12 = hour
                period = "AM"
            elif hour == 12:
                hour_12 = 12
                period = "PM"
            else:
                hour_12 = hour - 12
                period = "PM"
            
            return f"{hour_12}-{minute:02d} {period}"
        
        sunrise_formatted = format_time(sunrise_time)
        sunset_formatted = format_time(sunset_time)
        
        # Return formatted result
        result = f"ഉദയം: {sunrise_formatted}\nഅസ്തമയം: {sunset_formatted}"
        
        print(f"🌅 Sunrise calculation for {place_name}:")
        print(f"   Date: {date_obj}")
        print(f"   Coordinates: {latitude}, {longitude}")
        print(f"   Timezone: {timezone_str}")
        print(f"   Result: {result}")
        
        return result
        
    except Exception as e:
        error_msg = f"സൂര്യോദയ കണക്കുകൂട്ടലിൽ പിശക്: {str(e)}"
        print(f"❌ Sunrise calculation error: {e}")
        return error_msg

# Test function for development
def test_sunrise():
    """Test function to verify sunrise calculation"""
    test_data = {
        'location': 'Kannur',
        'latitude': 11.8745,
        'longitude': 75.3704,
        'timezone': 'Asia/Kolkata',
        'year': 2024,
        'month': 1,
        'day': 15
    }
    
    result = sunrise(test_data)
    print("Test Result:", result)
    return result

if __name__ == "__main__":
    test_sunrise()
