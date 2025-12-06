from flask import Flask, render_template
from datetime import datetime
import math
import swisseph as swe
import os
import json
import re
import pytz

# മലയാളം രാശി പേരുകൾ
RASHI_NAMES_MALAYALAM = {
    1: "മേടം", 2: "ഇടവം", 3: "മിഥുനം", 4: "കർക്കിടകം",
    5: "ചിങ്ങം", 6: "കന്നി", 7: "തുലാം", 8: "വൃശ്ചികം",
    9: "ധനു", 10: "മകരം", 11: "കുംഭം", 12: "മീനം"
}

# ഗ്രഹങ്ങൾ - grahanila.py രീതി
PLANETS = {
    'sun': swe.SUN, 'moon': swe.MOON, 'mars': swe.MARS,
    'mercury': swe.MERCURY, 'jupiter': swe.JUPITER,
    'venus': swe.VENUS, 'saturn': swe.SATURN
}

# Swiss Ephemeris ഗ്രഹ കോഡുകൾ - grahanila.py രീതി
PLANET_CODES = {
    "സൂര്യൻ": swe.SUN,
    "ചന്ദ്രൻ": swe.MOON,
    "ചൊവ്വ": swe.MARS,
    "ബുധൻ": swe.MERCURY,
    "ഗുരു": swe.JUPITER,
    "ശുക്രൻ": swe.VENUS,
    "ശനി": swe.SATURN,
    "രാഹു": swe.MEAN_NODE
}

def get_coordinates_from_app_data(place_data):
    """app.py-ൽ നിന്ന് വന്ന ഡാറ്റയിൽ നിന്ന് അക്ഷാംശം, രേഖാംശം, സമയമേഖല എടുക്കുക"""
    try:
        # place_data ഒരു dictionary ആണോ string ആണോ എന്ന് പരിശോധിക്കുക
        if isinstance(place_data, dict):
            # app.py-ൽ നിന്ന് വന്ന ഫോർമാറ്റ്
            lat = place_data.get('lat')
            lng = place_data.get('lng')
            timezone = place_data.get('timezone', 'Asia/Kolkata')
            place_name = place_data.get('name', '')
        elif isinstance(place_data, str):
            # പഴയ ഫോർമാറ്റ് (string)
            place_name = place_data
            # ഡിഫോൾട്ട് values
            lat = 11.8745  # കണ്ണൂർ
            lng = 75.3704
            timezone = 'Asia/Kolkata'
        else:
            # മറ്റ് കേസുകൾ
            place_name = str(place_data)
            lat = 11.8745
            lng = 75.3704
            timezone = 'Asia/Kolkata'
       
        # പ്രധാനമായും lat, lng ഉണ്ടോ എന്ന് പരിശോധിക്കുക
        if lat is None or lng is None:
            print(f"⚠️ Warning: Missing coordinates in place data. Using defaults.")
            lat = 11.8745
            lng = 75.3704
            timezone = 'Asia/Kolkata'
       
        print(f"📍 Place data received in ashtakavargam:")
        print(f"   - Name: {place_name}")
        print(f"   - Lat: {lat}")
        print(f"   - Lng: {lng}")
        print(f"   - Timezone: {timezone}")
       
        return lat, lng, timezone
       
    except Exception as e:
        print(f"⚠️ Error getting coordinates in ashtakavargam: {e}. Using defaults.")
        # ഡിഫോൾട്ട് values
        return 11.8745, 75.3704, 'Asia/Kolkata'

# ✅ പ്രധാന തിരുത്തൽ: grahanila.py രീതിയിലുള്ള correct_to_utc() ഫംഗ്ഷൻ
def correct_to_utc(year, month, day, hour, minute, second, timezone_str='Asia/Kolkata'):
    """സമയമേഖല അനുസരിച്ച് UTC യിലേക്ക് മാറ്റുക"""
    try:
        # സമയമേഖല object സൃഷ്ടിക്കുക
        tz = pytz.timezone(timezone_str)
       
        # Local datetime സൃഷ്ടിക്കുക
        local_dt = datetime(year, month, day, hour, minute, second)
       
        # Timezone ചേർക്കുക
        localized_dt = tz.localize(local_dt)
       
        # UTC-യിലേക്ക് മാറ്റുക
        utc_dt = localized_dt.astimezone(pytz.UTC)
       
        print(f"⏰ Time conversion in ashtakavargam:")
        print(f"   Input: {year}/{month}/{day} {hour}:{minute}:{second} ({timezone_str})")
        print(f"   UTC: {utc_dt.year}/{utc_dt.month}/{utc_dt.day} {utc_dt.hour}:{utc_dt.minute}:{utc_dt.second}")
       
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second
       
    except Exception as e:
        print(f"❌ UTC conversion error in ashtakavargam: {e}")
        # Fallback: IST മാത്രം (പഴയ രീതി)
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

class SwissEphemerisCalculator:
    def __init__(self):
        # Swiss Ephemeris ഡാറ്റാ പാത സെറ്റ് ചെയ്യുക
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ephe_path = os.path.join(current_dir, '..', 'ephe')
        if os.path.exists(ephe_path):
            swe.set_ephe_path(ephe_path)
        else:
            # ഡീഫോൾട്ട് എഫമറിസ് പാത ഉപയോഗിക്കുക
            swe.set_ephe_path()
   
    def calculate_planet_positions(self, year, month, day, hour, minute, lat, lon, timezone_str):
        try:
            print(f"🔍 Calculating planet positions in ashtakavargam:")
            print(f"   - Date: {day}/{month}/{year}")
            print(f"   - Time: {hour}:{minute}")
            print(f"   - Location: {lat}, {lon}")
            print(f"   - Timezone: {timezone_str}")
           
            # ✅ പ്രധാന തിരുത്തൽ: grahanila.py രീതിയിൽ UTC-യിലേക്ക് മാറ്റുക
            utc_year, utc_month, utc_day, utc_hour, utc_minute, utc_second = correct_to_utc(
                year, month, day, hour, minute, 0, timezone_str
            )
           
            # ജൂലിയൻ ദിവസം കണക്കാക്കുക (UTC)
            jd_utc = swe.julday(utc_year, utc_month, utc_day,
                              utc_hour + utc_minute/60.0 + utc_second/3600.0)
           
            print(f"   - Julian Day (UTC): {jd_utc}")
            print(f"   - UTC Time: {utc_hour}:{utc_minute}:{utc_second}")
           
            # Set ayanamsa mode (Lahiri)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
           
            # ആയനാംശം
            ayanamsa = swe.get_ayanamsa_ut(jd_utc)
           
            planet_degrees = {}
            planet_rashis = {}
           
            # ഓരോ ഗ്രഹത്തിന്റെയും സ്ഥാനം കണക്കാക്കുക
            for planet_name, planet_id in PLANETS.items():
                flags = swe.FLG_SWIEPH | swe.FLG_SPEED
                planet_pos, ret_flags = swe.calc_ut(jd_utc, planet_id, flags)
                longitude = planet_pos[0]
               
                # ആയനാംശം കുറച്ച് നിർയ്യാണ പദത്തിലേക്ക് മാറ്റുക
                nirayana_longitude = (longitude - ayanamsa) % 360
               
                planet_degrees[planet_name] = nirayana_longitude
                planet_rashis[planet_name] = self.get_rashi_from_degree(nirayana_longitude)
                print(f"   - {planet_name}: {nirayana_longitude:.2f}° ({planet_rashis[planet_name]})")
           
            # ലഗ്നം കണക്കാക്കുക (ശരിയായ രീതിയിൽ)
            lagna_degree = self.calculate_accurate_lagna(jd_utc, lat, lon, ayanamsa)
            planet_degrees['lagna'] = lagna_degree
            planet_rashis['lagna'] = self.get_rashi_from_degree(lagna_degree)
           
            print(f"   - Lagna: {lagna_degree:.2f}° ({planet_rashis['lagna']})")
           
            return planet_degrees, planet_rashis, ayanamsa, jd_utc
           
        except Exception as e:
            print(f"❌ Error in planet calculation in ashtakavargam: {e}")
            raise
   
    def calculate_accurate_lagna(self, jd_utc, lat, lon, ayanamsa):
        """ശരിയായ രീതിയിൽ ലഗ്നം കണക്കാക്കുക"""
        try:
            # Set ayanamsa mode first
            swe.set_sid_mode(swe.SIDM_LAHIRI)
           
            # Houses calculation using Swiss Ephemeris
            houses = swe.houses(jd_utc, lat, lon, b'P')  # Placidus house system
           
            # houses[0] contains the house cusps (1st house is ascendant)
            ascendant = houses[0][0]  # First house cusp
           
            # Subtract ayanamsa for nirayana lagna
            nirayana_lagna = (ascendant - ayanamsa) % 360
           
            return nirayana_lagna
           
        except Exception as e:
            print(f"Error in lagna calculation: {e}")
            # Fallback calculation
            sidereal_time = swe.sidtime(jd_utc)
            local_sidereal_time = (sidereal_time + lon/15.0) % 24
            lagna_degree = local_sidereal_time * 15.0
            return lagna_degree % 360
   
    def get_rashi_from_degree(self, degree):
        """ഡിഗ്രി അടിസ്ഥാനത്തിൽ രാശി കണ്ടെത്തുക"""
        rashi_num = math.floor(degree / 30) + 1
        return rashi_num if rashi_num <= 12 else 1

    def get_planet_details(self, jd_utc, planet_id):
        """ഗ്രഹത്തിന്റെ വിശദമായ വിവരങ്ങൾ ലഭിക്കുക"""
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        planet_pos, ret_flags = swe.calc_ut(jd_utc, planet_id, flags)
       
        return {
            'longitude': planet_pos[0],
            'latitude': planet_pos[1],
            'distance': planet_pos[2],
            'speed_longitude': planet_pos[3],
            'speed_latitude': planet_pos[4],
            'speed_distance': planet_pos[5]
        }

class AshtakavargaCalculator:
    def __init__(self, year, month, day, hour, minute, lat, lon, timezone_str):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.lat = lat
        self.lon = lon
        self.timezone_str = timezone_str
        self.swiss_ephe = SwissEphemerisCalculator()
   
    def calculate_all_ashtakavarga(self):
        planet_degrees, planet_rashis, ayanamsa, jd_utc = self.swiss_ephe.calculate_planet_positions(
            self.year, self.month, self.day, self.hour, self.minute,
            self.lat, self.lon, self.timezone_str
        )
       
        # ഗ്രഹങ്ങളുടെ വിശദ വിവരങ്ങൾ
        planet_details = {}
        for planet_name, planet_id in PLANETS.items():
            planet_details[planet_name] = self.swiss_ephe.get_planet_details(jd_utc, planet_id)
       
        results = {}
       
        # ഓരോ അഷ്ടവർഗ്ഗവും കണക്കാക്കുക
        results['sun'] = self.calculate_sun_ashtavarga(planet_rashis)
        results['moon'] = self.calculate_moon_ashtavarga(planet_rashis)
        results['mars'] = self.calculate_mars_ashtavarga(planet_rashis)
        results['mercury'] = self.calculate_mercury_ashtavarga(planet_rashis)
        results['jupiter'] = self.calculate_jupiter_ashtavarga(planet_rashis)
        results['venus'] = self.calculate_venus_ashtavarga(planet_rashis)
        results['saturn'] = self.calculate_saturn_ashtavarga(planet_rashis)
       
        # സമുദായ അഷ്ടവർഗ്ഗം
        results['total'] = self.calculate_total_ashtakavarga(results)
       
        return results, planet_rashis, ayanamsa, planet_degrees, planet_details
   
    def add_points_from_planet(self, base_rashi, points_list, rashi_points):
        for point in points_list:
            target_rashi = (base_rashi + point - 1) % 12
            if target_rashi == 0:
                target_rashi = 12
            rashi_points[target_rashi] += 1
   
    def calculate_sun_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # സൂര്യാഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [1, 2, 4, 7, 8, 9, 10, 11]
        moon_points = [3, 6, 10, 11]
        mars_points = [1, 2, 4, 7, 8, 9, 10, 11]
        mercury_points = [3, 5, 6, 9, 10, 11, 12]
        jupiter_points = [5, 6, 9, 11]
        venus_points = [6, 7, 12]
        saturn_points = [1, 2, 4, 7, 8, 9, 10, 11]
        lagna_points = [3, 4, 6, 10, 11, 12]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_moon_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # ചന്ദ്രാഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [3, 6, 7, 8, 10, 11]
        moon_points = [1, 3, 6, 7, 10, 11]
        mars_points = [2, 3, 5, 6, 9, 10, 11]
        mercury_points = [1, 3, 4, 5, 7, 8, 10, 11]
        jupiter_points = [1, 2, 4, 7, 8, 10, 11]
        venus_points = [3, 4, 5, 7, 9, 10, 11]
        saturn_points = [3, 5, 6, 11]
        lagna_points = [3, 6, 10, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_mars_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # കുജാഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [3, 5, 6, 10, 11]
        moon_points = [3, 6, 11]
        mars_points = [1, 2, 4, 7, 8, 10, 11]
        mercury_points = [3, 5, 6, 11]
        jupiter_points = [6, 10, 11, 12]
        venus_points = [6, 8, 11, 12]
        saturn_points = [1, 4, 7, 8, 9, 10, 11]
        lagna_points = [1, 3, 6, 10, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_mercury_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # ബുധാഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [5, 6, 9, 11, 12]
        moon_points = [2, 4, 6, 8, 10, 11]
        mars_points = [1, 2, 4, 7, 8, 9, 10, 11]
        mercury_points = [1, 3, 5, 6, 9, 10, 11, 12]
        jupiter_points = [6, 8, 11, 12]
        venus_points = [1, 2, 3, 4, 5, 8, 9, 11]
        saturn_points = [1, 2, 4, 7, 8, 9, 10, 11]
        lagna_points = [1, 2, 4, 6, 8, 10, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_jupiter_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # ഗുരുഅഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [1, 2, 3, 4, 7, 8, 9, 10, 11]
        moon_points = [2, 5, 7, 8, 11]
        mars_points = [1, 2, 4, 7, 8, 10, 11]
        mercury_points = [1, 2, 4, 5, 6, 9, 10, 11]
        jupiter_points = [1, 2, 3, 4, 7, 8, 10, 11]
        venus_points = [2, 5, 6, 9, 10, 11]
        saturn_points = [3, 6, 6, 12]
        lagna_points = [1, 2, 4, 5, 6, 7, 9, 10, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_venus_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # ശുക്രാഷ്ട വർഗ്ഗ നിയമങ്ങൾ
        sun_points = [8, 11, 12]
        moon_points = [1, 2, 3, 4, 5, 8, 9, 11, 12]
        mars_points = [3, 4, 6, 9, 11, 12]
        mercury_points = [3, 5, 6, 9, 11]
        jupiter_points = [5, 8, 9, 10, 11]
        venus_points = [1, 2, 3, 4, 5, 8, 9, 10, 11]
        saturn_points = [3, 4, 5, 8, 9, 10, 11]
        lagna_points = [1, 2, 3, 4, 5, 8, 9, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_saturn_ashtavarga(self, planet_rashis):
        rashi_points = {rashi: 0 for rashi in range(1, 13)}
       
        # ശനിഅഷ്ട വർഗ്ഗ നിയമങ്ങൾ (തിരുത്തിയത്)
        sun_points = [1, 2, 4, 7, 8, 10, 11]
        moon_points = [3, 6, 11]
        mars_points = [3, 5, 6, 10, 11, 12]
        mercury_points = [6, 8, 9, 10, 11, 12]
        jupiter_points = [3, 6, 11, 12]
        venus_points = [6, 11, 12]
        saturn_points = [3, 5, 6, 11]
        lagna_points = [1, 3, 4, 6, 10, 11]
       
        self.add_points_from_planet(planet_rashis['sun'], sun_points, rashi_points)
        self.add_points_from_planet(planet_rashis['moon'], moon_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mars'], mars_points, rashi_points)
        self.add_points_from_planet(planet_rashis['mercury'], mercury_points, rashi_points)
        self.add_points_from_planet(planet_rashis['jupiter'], jupiter_points, rashi_points)
        self.add_points_from_planet(planet_rashis['venus'], venus_points, rashi_points)
        self.add_points_from_planet(planet_rashis['saturn'], saturn_points, rashi_points)
        self.add_points_from_planet(planet_rashis['lagna'], lagna_points, rashi_points)
       
        return rashi_points
   
    def calculate_total_ashtakavarga(self, all_ashtavarga):
        total_points = {rashi: 0 for rashi in range(1, 13)}
       
        for planet in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']:
            if planet in all_ashtavarga:
                for rashi, points in all_ashtavarga[planet].items():
                    total_points[rashi] += points
       
        return total_points

def ashtakavargam_calculation(data):
    """Main function for Ashtakavargam calculation - called from app.py"""
    try:
        print(f"🔍 Ashtakavargam calculation started with data: {data}")
       
        # Extract data from app.py
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour_24h = data.get('hour_24h')
        minute = data.get('minute')
        place_data = data.get('place', {})
       
        if not all([year, month, day, hour_24h is not None, minute is not None]):
            return "പിശക്: എല്ലാ ഡാറ്റയും ലഭ്യമല്ല"
       
        # ✅ പ്രധാന തിരുത്തൽ: app.py-ൽ നിന്ന് വന്ന ഡാറ്റയിൽ നിന്ന് കോർഡിനേറ്റുകൾ എടുക്കുക
        lat, lon, timezone_str = get_coordinates_from_app_data(place_data)
       
        print(f"📍 Coordinates obtained in ashtakavargam:")
        print(f"   - Lat: {lat}")
        print(f"   - Lon: {lon}")
        print(f"   - Timezone: {timezone_str}")
       
        # Get place name for display
        if isinstance(place_data, dict):
            place_name = place_data.get('name', '')
        else:
            place_name = str(place_data)
       
        print(f"📅 Calculating Ashtakavargam for: {day}/{month}/{year} {hour_24h}:{minute}")
        print(f"📍 Location: {place_name} ({lat}, {lon}), Timezone: {timezone_str}")
       
        # Calculate Ashtakavargam with actual location data
        calculator = AshtakavargaCalculator(
            year=int(year), month=int(month), day=int(day),
            hour=int(hour_24h), minute=int(minute),
            lat=float(lat), lon=float(lon), timezone_str=str(timezone_str)
        )
       
        results, planet_rashis, ayanamsa, planet_degrees, planet_details = calculator.calculate_all_ashtakavarga()
       
        print(f"✅ Ashtakavargam calculation completed successfully")
        print(f"   - Lagna: {planet_degrees.get('lagna', 0):.2f}° ({planet_rashis.get('lagna', 1)})")
        print(f"   - Sun: {planet_degrees.get('sun', 0):.2f}° ({planet_rashis.get('sun', 1)})")
        print(f"   - Moon: {planet_degrees.get('moon', 0):.2f}° ({planet_rashis.get('moon', 1)})")
       
        # Format results for display
        formatted_results = {}
        for planet, planet_data in results.items():
            formatted_results[planet] = {}
            for rashi_num, points in planet_data.items():
                rashi_name = RASHI_NAMES_MALAYALAM[rashi_num]
                formatted_results[planet][rashi_name] = points
       
        # Generate HTML output with all details
        html_output = generate_ashtakavargam_html(
            formatted_results, planet_rashis, ayanamsa, data,
            planet_degrees, planet_details, {
                'name': place_name,
                'latitude': lat,
                'longitude': lon,
                'timezone': timezone_str
            }
        )
       
        return html_output
       
    except Exception as e:
        print(f"❌ Error in ashtakavargam_calculation: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<div style='color: red; padding: 20px; text-align: center;'>പിശക്: അഷ്ടവർഗ്ഗം കണക്കാക്കുന്നതിൽ പിശക് സംഭവിച്ചു: {str(e)}</div>"

def generate_ashtakavargam_html(results, planet_rashis, ayanamsa, calculation_data, planet_degrees, planet_details, place):
    """Generate HTML output for Ashtakavargam results"""
   
    PLANET_NAMES = {
        'sun': 'സൂര്യാഷ്ട വർഗ്ഗം',
        'moon': 'ചന്ദ്രാഷ്ട വർഗ്ഗം',
        'mars': 'കുജാഷ്ട വർഗ്ഗം',
        'mercury': 'ബുധാഷ്ട വർഗ്ഗം',
        'jupiter': 'ഗുരുഅഷ്ട വർഗ്ഗം',
        'venus': 'ശുക്രാഷ്ട വർഗ്ഗം',
        'saturn': 'ശനിഅഷ്ട വർഗ്ഗം',
        'total': 'സമുദായ അഷ്ടവർഗ്ഗം'
    }

    PLANET_DISPLAY_NAMES = {
        'sun': 'സൂര്യൻ', 'moon': 'ചന്ദ്രൻ', 'mars': 'കുജൻ',
        'mercury': 'ബുധൻ', 'jupiter': 'ഗുരു', 'venus': 'ശുക്രൻ',
        'saturn': 'ശനി', 'lagna': 'ലഗ്നം'
    }
   
    rashis = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കിടകം", "ചിങ്ങം", "കന്നി",
              "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"]
   
    html = f"""
    <!DOCTYPE html>
    <html lang="ml">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>അഷ്ടവർഗ്ഗം</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Noto Sans Malayalam', 'Manjari', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 10px;
                line-height: 1.5;
                color: #333;
            }}
            .container {{
                max-width: 100%;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                color: white;
                padding: 20px 15px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 24px;
                margin-bottom: 8px;
            }}
            .info-section {{
                background: #f8f9fa;
                padding: 15px;
                margin: 15px;
                border-radius: 10px;
                border-left: 4px solid #3498db;
            }}
            .location-details {{
                background: #e8f4f8;
                padding: 12px;
                margin: 10px 0;
                border-radius: 8px;
                border-left: 4px solid #2980b9;
            }}
            .planet-info {{
                background: #f8f9fa;
                padding: 15px;
                margin: 0 15px 15px 15px;
                border-radius: 10px;
                border-left: 4px solid #3498db;
            }}
            .planet-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }}
            .planet-item {{
                padding: 10px;
                background: white;
                border-radius: 8px;
                text-align: center;
                font-size: 13px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .planet-name {{
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 4px;
            }}
            .planet-rashi {{
                font-weight: bold;
                color: #e74c3c;
                font-size: 14px;
            }}
            .lagna-rashi {{
                color: #3498db;
            }}
            .planet-degree {{
                font-size: 11px;
                color: #7f8c8d;
                margin-top: 2px;
            }}
            .tabs-section {{
                background: #34495e;
                padding: 15px;
            }}
            .tabs-title {{
                color: white;
                text-align: center;
                margin-bottom: 12px;
                font-size: 16px;
                font-weight: bold;
            }}
            .tabs {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .tab {{
                padding: 14px 12px;
                background: #2c3e50;
                color: white;
                cursor: pointer;
                border-radius: 8px;
                font-size: 14px;
                text-align: center;
                flex: 1;
                min-width: 90px;
                font-weight: bold;
                transition: all 0.3s ease;
            }}
            .tab:hover {{
                background: #3a506b;
            }}
            .tab.active {{
                background: #e74c3c;
                transform: scale(1.05);
            }}
            .tab-content {{
                display: none;
                padding: 0 15px;
            }}
            .tab-content.active {{
                display: block;
            }}
            .rashi-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 20px;
            }}
            .rashi-item {{
                padding: 18px 12px;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 12px;
                text-align: center;
                border-left: 5px solid #e74c3c;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            }}
            .rashi-name {{
                font-weight: bold;
                color: #2c3e50;
                font-size: 16px;
                margin-bottom: 8px;
            }}
            .rashi-points {{
                font-size: 24px;
                font-weight: bold;
                color: #e74c3c;
            }}
            .total-summary {{
                background: #27ae60;
                color: white;
                padding: 18px;
                text-align: center;
                border-radius: 12px;
                margin: 15px;
                font-size: 18px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }}
            @media (max-width: 480px) {{
                .rashi-grid {{ grid-template-columns: repeat(2, 1fr); }}
                .planet-grid {{ grid-template-columns: repeat(3, 1fr); }}
                .tab {{ font-size: 13px; padding: 12px 8px; min-width: 85px; }}
            }}
            @media (min-width: 768px) {{
                .container {{ max-width: 700px; }}
                .rashi-grid {{ grid-template-columns: repeat(4, 1fr); }}
                .planet-grid {{ grid-template-columns: repeat(4, 1fr); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>അഷ്ടവർഗ്ഗം</h1>
            </div>
           
            <div class="info-section">
                <h3>Calculation Details:</h3>
                <p>📅 Date: {calculation_data['day']}/{calculation_data['month']}/{calculation_data['year']}</p>
                <p>⏰ Time: {calculation_data['hour_24h']}:{calculation_data['minute']:02d}</p>
                <div class="location-details">
                    <p><strong>📍 Location: {place.get('name', 'Unknown')}</strong></p>
                    <p>Latitude: {place.get('latitude')}°N</p>
                    <p>Longitude: {place.get('longitude')}°E</p>
                    <p>Timezone: {place.get('timezone')}</p>
                </div>
    """
   
    html += f"""
                <p>Ayanamsa: {ayanamsa:.6f}°</p>
            </div>
           
            <div class="planet-info">
                <h3>ഗ്രഹ നിലകൾ:</h3>
                <div class="planet-grid">
    """
   
    # Add planet positions with degrees
    for planet, rashi_num in planet_rashis.items():
        rashi_name = rashis[rashi_num - 1]
        degree = planet_degrees.get(planet, 0)
        className = 'planet-rashi lagna-rashi' if planet == 'lagna' else 'planet-rashi'
        html += f"""
                    <div class="planet-item">
                        <div class="planet-name">{PLANET_DISPLAY_NAMES[planet]}</div>
                        <div class="{className}">{rashi_name}</div>
                        <div class="planet-degree">{degree:.2f}°</div>
                    </div>
        """
   
    html += """
                </div>
            </div>
           
            <div class="tabs-section">
                <div class="tabs-title">അഷ്ടവർഗ്ഗങ്ങൾ</div>
                <div class="tabs" id="tabs">
    """
   
    # Create tabs
    planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'total']
    for i, planet in enumerate(planets):
        active = "active" if i == 0 else ""
        html += f'<div class="tab {active}" onclick="switchTab(\'{planet}\')">{PLANET_NAMES[planet]}</div>'
   
    html += """
                </div>
            </div>
           
            <div id="tabContents">
    """
   
    # Create tab contents
    for i, planet in enumerate(planets):
        active = "active" if i == 0 else ""
        html += f'<div class="tab-content {active}" id="tab-{planet}">'
       
        if planet in results:
            html += '<div class="rashi-grid">'
            for rashi in rashis:
                points = results[planet].get(rashi, 0)
                html += f"""
                    <div class="rashi-item">
                        <div class="rashi-name">{rashi}</div>
                        <div class="rashi-points">{points}</div>
                    </div>
                """
            html += '</div>'
           
            # Add total sum for total ashtakavarga
            if planet == 'total':
                total_sum = sum(results[planet].values())
                html += f'<div class="total-summary">ആകെ തുക: {total_sum}</div>'
       
        html += '</div>'
   
    html += """
            </div>
        </div>

        <script>
            function switchTab(planet) {
                // Hide all tabs and contents
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
               
                // Activate selected tab and content
                document.querySelector(`.tab:nth-child(${getTabIndex(planet) + 1})`).classList.add('active');
                document.getElementById(`tab-${planet}`).classList.add('active');
            }
           
            function getTabIndex(planet) {
                const planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'total'];
                return planets.indexOf(planet);
            }
           
            // Initialize with first tab active
            window.onload = function() {
                switchTab('sun');
            };
        </script>
    </body>
    </html>
    """
   
    return html

# Initialize Swiss Ephemeris
swe.set_ephe_path('')

if __name__ == "__main__":
    print("🚀 Ashtakavargam Server starting...")
    print("📊 Testing ashtakavargam calculation...")
   
    # Test data
    test_data = {
        'year': 1990,
        'month': 5,
        'day': 15,
        'hour_24h': 10,
        'minute': 30,
        'place': {
            'name': 'തിരുവനന്തപുരം',
            'lat': 8.5241,
            'lng': 76.9366,
            'timezone': 'Asia/Kolkata'
        }
    }
   
    try:
        result = ashtakavargam_calculation(test_data)
        print("✅ Test completed successfully")
        print("🌐 Server ready")
    except Exception as e:
        print(f"❌ Test failed: {e}")
