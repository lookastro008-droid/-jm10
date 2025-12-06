from datetime import datetime


def divasam_calculation(data):
    """
    Calculate day of week and age based on provided data
    Returns: Dictionary with day and age information
    """
    try:
        # Extract date information
        if 'calculation_type' in data and data['calculation_type'] == 'auto':
            # For auto calculation, use current SERVER date for day of week
            # and current date as both current date and DOB for age
            current_year = data['year']
            current_month = data['month']
            current_day = data['day']
            dob_year = current_year
            dob_month = current_month
            dob_day = current_day
            
            # Calculate day of week using SERVER date
            day_of_week = calculate_day_of_week(current_year, current_month, current_day)
            
        else:
            # For manual calculation, use provided date for day of week (DOB date)
            # and as DOB for age calculation (with current date as reference)
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            current_day = current_date.day
            
            dob_year = data['year']
            dob_month = data['month']
            dob_day = data['day']
            
            # Calculate day of week using PROVIDED DOB date
            day_of_week = calculate_day_of_week(dob_year, dob_month, dob_day)

        # Calculate age
        age_result = calculate_age(dob_year, dob_month, dob_day, current_year, current_month, current_day)

        # Apply dark blue color for age in BOTH auto and manual calculations
        age_display = f'<span style="color: #1a5276; font-weight: bold; font-size: 1.1em;">പ്രായം: {age_result}</span>'

        return {
            'ദിവസം': f"ദിവസം: {day_of_week}",
            'പ്രായം': age_display
        }
        
    except Exception as e:
        print(f"Error in divasam_calculation: {e}")
        return {
            'ദിവസം': "ദിവസം: കണക്കാക്കാനായില്ല",
            'പ്രായം': '<span style="color: #1a5276; font-weight: bold; font-size: 1.1em;">പ്രായം: 0 വ 0 മാ 0 ദി</span>'
        }


def calculate_day_of_week(year, month, day):
    """Calculate Malayalam day name for given date using calendar function"""
    try:
        date_obj = datetime(year, month, day)
        day_number = date_obj.weekday()
        
        malayalam_days = [
            "തിങ്കൾ", "ചൊവ്വ", "ബുധൻ", "വ്യാഴം",
            "വെള്ളി", "ശനി", "ഞായർ"
        ]
        
        return malayalam_days[day_number]
    except Exception as e:
        print(f"Error calculating day: {e}")
        return "കണക്കാക്കാനായില്ല"


def calculate_age(dob_year, dob_month, dob_day, current_year, current_month, current_day):
    """Calculate age in years, months and days accurately"""
    try:
        # If it's the same date, return 0
        if dob_year == current_year and dob_month == current_month and dob_day == current_day:
            return "0 വ 0 മാ 0 ദി"
        
        # Create date objects for comparison
        dob_date = datetime(dob_year, dob_month, dob_day)
        current_date = datetime(current_year, current_month, current_day)
        
        # If DOB is in the future, return 0
        if dob_date > current_date:
            return "0 വ 0 മാ 0 ദി"
        
        # Calculate years difference
        years = current_year - dob_year
        
        # Calculate months difference
        months = current_month - dob_month
        
        # Calculate days difference
        days = current_day - dob_day
        
        # Adjust for negative days
        if days < 0:
            # Get the previous month
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            # Get days in previous month
            days_in_prev_month = get_days_in_month(prev_year, prev_month)
            days = days_in_prev_month + days  # Add negative days
            months -= 1
        
        # Adjust for negative months
        if months < 0:
            months += 12
            years -= 1
        
        # If years become negative, set to 0
        if years < 0:
            years = 0
        
        # Format the result
        return f"{years} വ {months} മാ {days} ദി"
        
    except Exception as e:
        print(f"Error calculating age: {e}")
        return "0 വ 0 മാ 0 ദി"


def get_days_in_month(year, month):
    """Get number of days in a month"""
    if month == 2:
        # February - check for leap year
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        else:
            return 28
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        return 31


# Test function for direct command line testing
if __name__ == "__main__":
    print("🔍 Divasam Module Test")
    
    # Test case 1: Current date (auto calculation)
    test_data_auto = {
        'year': datetime.now().year,
        'month': datetime.now().month,
        'day': datetime.now().day,
        'calculation_type': 'auto'
    }
    
    result_auto = divasam_calculation(test_data_auto)
    print("\n📅 Auto Calculation Test:")
    print(f"   - {result_auto['ദിവസം']}")
    print(f"   - {result_auto['പ്രായം']}")
    
    # Test case 2: DOB from yesterday
    today = datetime.now()
    yesterday = today.replace(day=today.day-1) if today.day > 1 else today.replace(month=today.month-1, day=get_days_in_month(today.year, today.month-1))
    
    test_data_yesterday = {
        'year': yesterday.year,
        'month': yesterday.month,
        'day': yesterday.day,
        'calculation_type': 'manual'
    }
    
    result_yesterday = divasam_calculation(test_data_yesterday)
    print(f"\n📅 DOB Yesterday Test:")
    print(f"   - {result_yesterday['ദിവസം']}")
    print(f"   - {result_yesterday['പ്രായം']}")  # Should show dark blue color
    
    # Test case 3: Specific DOB (9/11/2025) - future date
    test_data_future = {
        'year': 2025,
        'month': 11,
        'day': 9,
        'calculation_type': 'manual'
    }
    
    result_future = divasam_calculation(test_data_future)
    print(f"\n📅 Future DOB Test (9/11/2025):")
    print(f"   - {result_future['ദിവസം']}")
    print(f"   - {result_future['പ്രായം']}")  # Should show dark blue color
    
    # Test case 4: 1 month old baby
    one_month_ago = today.replace(month=today.month-1) if today.month > 1 else today.replace(year=today.year-1, month=12)
    
    test_data_one_month = {
        'year': one_month_ago.year,
        'month': one_month_ago.month,
        'day': one_month_ago.day,
        'calculation_type': 'manual'
    }
    
    result_one_month = divasam_calculation(test_data_one_month)
    print(f"\n📅 1 Month Old Test:")
    print(f"   - {result_one_month['ദിവസം']}")
    print(f"   - {result_one_month['പ്രായം']}")  # Should show dark blue color
    
    # Test case 5: Same day as today (should be dark blue)
    test_data_same_day = {
        'year': today.year,
        'month': today.month,
        'day': today.day,
        'calculation_type': 'manual'
    }
    
    result_same_day = divasam_calculation(test_data_same_day)
    print(f"\n📅 Same Day Test:")
    print(f"   - {result_same_day['ദിവസം']}")
    print(f"   - {result_same_day['പ്രായം']}")  # Should show dark blue color
