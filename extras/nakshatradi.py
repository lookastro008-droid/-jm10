from flask import Flask, render_template_string, request, jsonify
import swisseph as swe
from datetime import datetime, timedelta
import math
import os
import pytz

# എഫിമെറിഡ് ഫയലുകളുടെ പാത് സജ്ജമാക്കുക
swe.set_ephe_path(os.path.join(os.path.dirname(__file__), '..', 'swisseph'))

# നക്ഷത്രങ്ങളുടെ ഡിഗ്രി ശ്രേണികൾ (മേടം 0° മുതൽ)
NAKSHATRAS = [
    {"name": "അശ്വതി", "start": 0.0, "end": 13.3333},
    {"name": "ഭരണി", "start": 13.3333, "end": 26.6667},
    {"name": "കാർത്തിക", "start": 26.6667, "end": 40.0},
    {"name": "രോഹിണി", "start": 40.0, "end": 53.3333},
    {"name": "മകയിരം", "start": 53.3333, "end": 66.6667},
    {"name": "തിരുവാതിര", "start": 66.6667, "end": 80.0},
    {"name": "പുണർതം", "start": 80.0, "end": 93.3333},
    {"name": "പൂയം", "start": 93.3333, "end": 106.6667},
    {"name": "ആയില്യം", "start": 106.6667, "end": 120.0},
    {"name": "മകം", "start": 120.0, "end": 133.3333},
    {"name": "പൂരം", "start": 133.3333, "end": 146.6667},
    {"name": "ഉത്രം", "start": 146.6667, "end": 160.0},
    {"name": "അത്തം", "start": 160.0, "end": 173.3333},
    {"name": "ചിത്തിര", "start": 173.3333, "end": 186.6667},
    {"name": "ചോതി", "start": 186.6667, "end": 200.0},
    {"name": "വിശാഖം", "start": 200.0, "end": 213.3333},
    {"name": "അനിഴം", "start": 213.3333, "end": 226.6667},
    {"name": "തൃക്കേട്ട", "start": 226.6667, "end": 240.0},
    {"name": "മൂലം", "start": 240.0, "end": 253.3333},
    {"name": "പൂരാടം", "start": 253.3333, "end": 266.6667},
    {"name": "ഉത്രാടം", "start": 266.6667, "end": 280.0},
    {"name": "തിരുവോണം", "start": 280.0, "end": 293.3333},
    {"name": "അവിട്ടം", "start": 293.3333, "end": 306.6667},
    {"name": "ചതയം", "start": 306.6667, "end": 320.0},
    {"name": "പൂരുരുട്ടാതി", "start": 320.0, "end": 333.3333},
    {"name": "ഉത്രട്ടാതി", "start": 333.3333, "end": 346.6667},
    {"name": "രേവതി", "start": 346.6667, "end": 360.0}
]

# നക്ഷത്ര വിശദാംശങ്ങൾ
NAKSHATRA_DETAILS = {
    "അശ്വതി": {
        "ഗണം": "ദേവഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "അശ്വിനി ദേവത",
        "ഭൂതം": "ഭൂമി",
        "മൃഗം": "കുതിര",
        "പക്ഷി": "പുള്ള്",
        "വൃക്ഷം": "കാഞ്ഞിരം"
    },
    "ഭരണി": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "യമൻ",
        "ഭൂതം": "ഭൂമി",
        "മൃഗം": "ആന",
        "പക്ഷി": "പുള്ള്",
        "വൃക്ഷം": "നെല്ലി"
    },
    "കാർത്തിക": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "അഗ്നി",
        "ഭൂതം": "ഭൂമി",
        "മൃഗം": "ആട്",
        "പക്ഷി": "പുള്ള്",
        "വൃക്ഷം": "അത്തി"
    },
    "രോഹിണി": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ബ്രഹ്മാവ്",
        "ഭൂതം": "ഭൂമി",
        "മൃഗം": "പാമ്പ്",
        "പക്ഷി": "പുള്ള്",
        "വൃക്ഷം": "ഞാവൽ"
    },
    "മകയിരം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ചന്ദ്രൻ",
        "ഭൂതം": "ഭൂമി",
        "മൃഗം": "പാമ്പ്",
        "പക്ഷി": "പുള്ള്",
        "വൃക്ഷം": "കരിങ്ങാലി"
    },
    "തിരുവാതിര": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ശിവൻ",
        "ഭൂതം": "ജലം",
        "മൃഗം": "വിഷ്ടി",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "കരിമരം"
    },
    "പുണർതം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ആദിതി",
        "ഭൂതം": "ജലം",
        "മൃഗം": "പൂച്ച",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "മുള"
    },
    "പൂയം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "ബൃഹസ്പതി",
        "ഭൂതം": "ജലം",
        "മൃഗം": "ആട്",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "ആരയാൽ"
    },
    "ആയില്യം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "സർപ്പങ്ങൾ",
        "ഭൂതം": "ജലം",
        "മൃഗം": "കരിമ്പൂച്ച",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "നാകം"
    },
    "മകം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "പിതൃക്കൾ",
        "ഭൂതം": "ജലം",
        "മൃഗം": "എലി",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "പേരാൽ"
    },
    "പൂരം": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ആര്യമാവ്",
        "ഭൂതം": "ജലം",
        "മൃഗം": "ചുണ്ടെലി",
        "പക്ഷി": "ചകോരം",
        "വൃക്ഷം": "പ്ലാശ്"
    },
    "ഉത്രം": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "ഭഗൻ",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "ഒട്ടകം",
        "പക്ഷി": "കാകൻ",
        "വൃക്ഷം": "ഇത്തി"
    },
    "അത്തം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ആദിത്യൻ",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "പോത്ത്",
        "പക്ഷി": "കാകൻ",
        "വൃക്ഷം": "അമ്പഴം"
    },
    "ചിത്തിര": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ത്വഷ്ടാവ്",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "ആൾപുലി",
        "പക്ഷി": "കാകൻ",
        "വൃക്ഷം": "കൂവളം"
    },
    "ചോതി": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "വായു",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "മഹിഷം",
        "പക്ഷി": "കാക്ക",
        "വൃക്ഷം": "നീർമരൂത്"
    },
    "വിശാഖം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "ഇന്ദ്രാണി",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "സിംഹം",
        "പക്ഷി": "കാക്ക",
        "വൃക്ഷം": "വയ്യങ്കതവു"
    },
    "അനിഴം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "മൈത്രൻ",
        "ഭൂതം": "അഗ്നി",
        "മൃഗം": "മാൻ",
        "പക്ഷി": "കാക്ക",
        "വൃക്ഷം": "ഇലഞ്ഞി"
    },
    "തൃക്കേട്ട": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "ഇന്ദ്രൻ",
        "ഭൂതം": "വായു",
        "മൃഗം": "കേഴമാൻ",
        "പക്ഷി": "കോഴി",
        "വൃക്ഷം": "വെട്ടി"
    },
    "മൂലം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "നിര്യതി",
        "ഭൂതം": "വായു",
        "മൃഗം": "ശ്വാവ്",
        "പക്ഷി": "കോഴി",
        "വൃക്ഷം": "പയിന"
    },
    "പൂരാടം": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "വരുണൻ",
        "ഭൂതം": "വായു",
        "മൃഗം": "കപി",
        "പക്ഷി": "കോഴി",
        "വൃക്ഷം": "വഞ്ഞി"
    },
    "ഉത്രാടം": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "വിശ്വ ദേവതകൾ",
        "ഭൂതം": "വായു",
        "മൃഗം": "കാള",
        "പക്ഷി": "കോഴി",
        "വൃക്ഷം": "പിലാവ്"
    },
    "തിരുവോണം": {
        "ഗണം": "ദേവ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "വിഷ്ണു",
        "ഭൂതം": "വായു",
        "മൃഗം": "വാനരം",
        "പക്ഷി": "കോഴി",
        "വൃക്ഷം": "എരുക്ക്"
    },
    "അവിട്ടം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "വാസുക്കൾ",
        "ഭൂതം": "ആകാശം",
        "മൃഗം": "നല്ലാൾ",
        "പക്ഷി": "മയിൽ",
        "വൃക്ഷം": "വന്നി"
    },
    "ചതയം": {
        "ഗണം": "അസുര ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "വരുണൻ",
        "ഭൂതം": "ആകാശം",
        "മൃഗം": "കുതിര",
        "പക്ഷി": "മയിൽ",
        "വൃക്ഷം": "കടമ്പ്"
    },
    "പൂരുരുട്ടാതി": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "പുരുഷ യോനി",
        "ദേവത": "അജൈകപാത്",
        "ഭൂതം": "ആകാശം",
        "മൃഗം": "നരൻ",
        "പക്ഷി": "മയിൽ",
        "വൃക്ഷം": "തേൻമാവ്"
    },
    "ഉത്രട്ടാതി": {
        "ഗണം": "മനുഷ്യ ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "ആഹിർബുധ്നി",
        "ഭൂതം": "ആകാശം",
        "മൃഗം": "പശു",
        "പക്ഷി": "മയിൽ",
        "വൃക്ഷം": "കരിമ്പന"
    },
    "രേവതി": {
        "ഗണം": "ദേവഗണം ഗണം",
        "യോനി": "സ്ത്രീ യോനി",
        "ദേവത": "പുഷാവ്",
        "ഭൂതം": "ആകാശം",
        "മൃഗം": "ആന",
        "പക്ഷി": "മയിൽ",
        "വൃക്ഷം": "ഇരിപ്പ"
    }
}

# തിഥി ദേവതകൾ
THITHI_DEVATAS = {
    1: "അഗ്നി",
    2: "ബ്രഹ്മാവ്",
    3: "ഗൗരി",
    4: "ഗണപതി",
    5: "സർപ്പദേവത",
    6: "കാർത്തികേയൻ",
    7: "സൂര്യൻ",
    8: "ശിവൻ",
    9: "ദുർഗ്ഗ",
    10: "യമൻ",
    11: "വിശ്വേദേവകൾ",
    12: "വിഷ്ണു",
    13: "കാമദേവൻ",
    14: "ശിവൻ",
    15: "ചന്ദ്രൻ",  # പൗർണമി
    16: "പിതൃദേവതകൾ"  # അമാവാസി
}

# രാശികളുടെ പട്ടിക
RASHIS = [
    "മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം",
    "ചിങ്ങം", "കന്നി", "തുലാം", "വൃശ്ചികം",
    "ധനു", "മകരം", "കുംഭം", "മീനം"
]

# തിഥികളുടെ പട്ടിക
THITHIS = [
    "പ്രതിപദം", "ദ്വിതീയ", "തൃതീയ", "ചതുർത്ഥി",
    "പഞ്ചമി", "ഷഷ്ഠി", "സപ്തമി", "അഷ്ടമി",
    "നവമി", "ദശമി", "ഏകാദശി", "ദ്വാദശി",
    "ത്രയോദശി", "ചതുര്ദശി", "പൗർണ്ണമി", "അമാവാസി"
]

# കരണങ്ങളുടെ പട്ടിക
SHUKLA_PAKSHA_KARANAS = {
    1: ['പുഴു', 'സിംഹം'],
    2: ['പുലി', 'പന്നി'],
    3: ['കഴുത', 'ആന'],
    4: ['പശു', 'വിഷ്ടി'],
    5: ['സിംഹം', 'പുലി'],
    6: ['പന്നി', 'കഴുത'],
    7: ['ആന', 'സുരഭി'],
    8: ['വിഷ്ടി', 'സിംഹം'],
    9: ['പുലി', 'പന്നി'],
    10: ['കഴുത', 'ആന'],
    11: ['പശു', 'വിഷ്ടി'],
    12: ['സിംഹം', 'പുലി'],
    13: ['പന്നി', 'കഴുത'],
    14: ['ആന', 'പശു'],
    15: ['വിഷ്ടി', 'സിംഹം']
}

KRISHNA_PAKSHA_KARANAS = {
    1: ['പുലി', 'പന്നി'],
    2: ['കഴുത', 'ആന'],
    3: ['പശു', 'വിഷ്ടി'],
    4: ['സിംഹം', 'പുലി'],
    5: ['പന്നി', 'കഴുത'],
    6: ['ആന', 'സുരഭി'],
    7: ['വിഷ്ടി', 'സിംഹം'],
    8: ['പുലി', 'പന്നി'],
    9: ['കഴുത', 'ആന'],
    10: ['പശു', 'വിഷ്ടി'],
    11: ['സിംഹം', 'പുലി'],
    12: ['പന്നി', 'കഴുത'],
    13: ['ആന', 'സുരഭി'],
    14: ['വിഷ്ടി', 'പുള്ള്'],
    15: ['ചതുഷ്പാത്', 'നാഗം']
}

# നിത്യയോഗങ്ങളുടെ പട്ടിക
YOGAS = [
    {"name": "വിഷ്കുംഭം", "start": 0.0, "end": 13.3333},
    {"name": "പ്രീതി", "start": 13.3333, "end": 26.6667},
    {"name": "ആയുഷ്മാൻ", "start": 26.6667, "end": 40.0},
    {"name": "സൗഭാഗ്യ", "start": 40.0, "end": 53.3333},
    {"name": "ശോഭനം", "start": 53.3333, "end": 66.6667},
    {"name": "അതിഗണ്ഡം", "start": 66.6667, "end": 80.0},
    {"name": "സുകർമ്മ", "start": 80.0, "end": 93.3333},
    {"name": "ധൃതി", "start": 93.3333, "end": 106.6667},
    {"name": "ശൂല", "start": 106.6667, "end": 120.0},
    {"name": "ഗണ്ഡവം", "start": 120.0, "end": 133.3333},
    {"name": "വൃദ്ധി", "start": 133.3333, "end": 146.6667},
    {"name": "ധ്രുവം", "start": 146.6667, "end": 160.0},
    {"name": "വ്യാഘാതം", "start": 160.0, "end": 173.3333},
    {"name": "ഹർഷണം", "start": 173.3333, "end": 186.6667},
    {"name": "വജ്ജ്രം", "start": 186.6667, "end": 200.0},
    {"name": "സിദ്ധി", "start": 200.0, "end": 213.3333},
    {"name": "വ്യതിപാതം", "start": 213.3333, "end": 226.6667},
    {"name": "വരിയാൻ", "start": 226.6667, "end": 240.0},
    {"name": "പരിഘം", "start": 240.0, "end": 253.3333},
    {"name": "ശിവ", "start": 253.3333, "end": 266.6667},
    {"name": "സിദ്ധ", "start": 266.6667, "end": 280.0},
    {"name": "സാദ്ധ്യ", "start": 280.0, "end": 293.3333},
    {"name": "ശുഭ", "start": 293.3333, "end": 306.6667},
    {"name": "ശുഭ്ര", "start": 306.6667, "end": 320.0},
    {"name": "ബ്രാഹ്മ", "start": 320.0, "end": 333.3333},
    {"name": "മാഹേന്ദ്ര", "start": 333.3333, "end": 346.6667},
    {"name": "വൈധൃതി", "start": 346.6667, "end": 360.0}
]

# HTML ടെംപ്ലേറ്റ് - വേറെ വിൻഡോയിൽ കാണിക്കാൻ
NAKSHATRADI_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>നക്ഷത്രാദി വിശേഷം</title>
    <style>
        body {
            font-family: 'Noto Sans Malayalam', 'Manjari', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            border: 2px solid #8B4513;
        }
        .header {
            text-align: center;
            color: #8B4513;
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 30px;
            border-bottom: 3px solid #8B4513;
            padding-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .info-section {
            background: #fff8dc;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            border-left: 5px solid #8B4513;
        }
        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .result-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #8B4513;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .result-label {
            color: #8B4513;
            font-weight: bold;
            font-size: 20px;
            display: block;
            margin-bottom: 8px;
        }
        .result-value {
            color: #2c3e50;
            font-size: 22px;
            font-weight: bold;
        }
        .nakshatra-details {
            background: #e8f4f8;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #3498db;
        }
        .detail-item {
            margin: 12px 0;
            padding: 10px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        .timestamp {
            text-align: center;
            color: #7f8c8d;
            font-size: 16px;
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #bdc3c7;
        }
        .highlight {
            background: linear-gradient(135deg, #8B4513, #A0522D);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin: 25px 0;
            font-size: 24px;
            font-weight: bold;
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            .header {
                font-size: 28px;
            }
            .result-value {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">🌙 നക്ഷത്രാദി വിശേഷം 🌟</div>
        
        <div class="info-section">
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="font-size: 20px; color: #8B4513; margin-bottom: 10px;">
                    📅 തീയതി: {{ calculation_date }}<br>
                    ⏰ സമയം: {{ calculation_time }}<br>
                    📍 സ്ഥലം: {{ place_name }}
                </div>
            </div>

            <div class="highlight">
                {{ main_nakshatra }}
            </div>

            <div class="result-grid">
                <div class="result-card">
                    <span class="result-label">നക്ഷത്രം</span>
                    <div class="result-value">{{ nakshatra_name }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">പാദം</span>
                    <div class="result-value">{{ pada }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">നക്ഷത്ര നാഴിക</span>
                    <div class="result-value">{{ nakshatra_nazhika }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">തിഥി</span>
                    <div class="result-value">{{ thithi_name }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">പക്ഷം</span>
                    <div class="result-value">{{ paksha }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">തിഥി ദേവത</span>
                    <div class="result-value">{{ thithi_devata }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">കരണം</span>
                    <div class="result-value">{{ karana }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">നിത്യയോഗം</span>
                    <div class="result-value">{{ yoga }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">കൂറ്</span>
                    <div class="result-value">{{ kooru }}</div>
                </div>
                <div class="result-card">
                    <span class="result-label">ചന്ദ്രാഷ്ടമം</span>
                    <div class="result-value">{{ chandra_ashtamam }}</div>
                </div>
            </div>

            <div class="nakshatra-details">
                <h3 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">നക്ഷത്ര വിശദാംശങ്ങൾ</h3>
                <div class="detail-item">
                    <span class="result-label">ഗണം</span>
                    <div class="result-value">{{ gana }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">യോനി</span>
                    <div class="result-value">{{ yoni }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">ദേവത</span>
                    <div class="result-value">{{ nakshatra_devata }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">ഭൂതം</span>
                    <div class="result-value">{{ bhuta }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">മൃഗം</span>
                    <div class="result-value">{{ mrga }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">പക്ഷി</span>
                    <div class="result-value">{{ pakshi }}</div>
                </div>
                <div class="detail-item">
                    <span class="result-label">വൃക്ഷം</span>
                    <div class="result-value">{{ vriksha }}</div>
                </div>
            </div>
        </div>

        <div class="timestamp">
            കണക്കാക്കിയ സമയം: {{ current_timestamp }}
        </div>
    </div>
</body>
</html>
'''

# ആയനാംശം പ്രയോഗിക്കുന്ന ഫംഗ്ഷൻ
def apply_ayanamsa(degree):
    base_ayanamsa = 24.219444
    degree_with_ayanamsa = degree - base_ayanamsa
    degree_with_ayanamsa %= 360.0
    if degree_with_ayanamsa < 0:
        degree_with_ayanamsa += 360.0
    return degree_with_ayanamsa

# നക്ഷത്രം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_nakshatra(degree):
    degree = degree % 360.0
    for nakshatra in NAKSHATRAS:
        if nakshatra['start'] <= degree < nakshatra['end']:
            return nakshatra
    return NAKSHATRAS[0]

# യോഗം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_yoga(degree):
    degree = degree % 360.0
    for yoga in YOGAS:
        if yoga['start'] <= degree < yoga['end']:
            return yoga
    return YOGAS[0]

# UTC-ൽ നിന്ന് സ്ഥാനീയ സമയത്തേക്ക് മാറ്റുന്ന ഫംഗ്ഷൻ
def utc_to_local(utc_time, timezone_offset):
    return utc_time + timedelta(hours=timezone_offset)

# സ്ഥാനീയ സമയത്തിൽ നിന്ന് UTC-ലേക്ക് മാറ്റുന്ന ഫംഗ്ഷൻ
def local_to_utc(local_time, timezone_offset):
    return local_time - timedelta(hours=timezone_offset)

# സ്ട്രിംഗ് timezone-നെ float-ആക്കി മാറ്റുന്ന ഫംഗ്ഷൻ
def parse_timezone(timezone_input):
    if isinstance(timezone_input, (int, float)):
        return float(timezone_input)
   
    if isinstance(timezone_input, str):
        try:
            return float(timezone_input)
        except ValueError:
            timezone_mapping = {
                'Asia/Kolkata': 5.5,
                'Asia/Calcutta': 5.5,
                'IST': 5.5,
                'UTC': 0.0,
                'GMT': 0.0
            }
            if timezone_input in timezone_mapping:
                return timezone_mapping[timezone_input]
            else:
                return 5.5
   
    return 5.5

# ചന്ദ്രാഷ്ടമം കണക്കാക്കുന്ന ഫംഗ്ഷൻ (ശരിയായ രീതി)
def calculate_chandra_ashtamam(moon_rashi_index):
    # ചന്ദ്രൻ നിൽക്കുന്ന രാശിയിൽ നിന്നും എട്ടാമത്തെ രാശി
    ashtama_rashi = (moon_rashi_index + 8) % 12
    return RASHIS[ashtama_rashi]

# ഗ്രഹ സ്ഥാനം കണക്കാക്കുന്ന ഫംഗ്ഷൻ
def calculate_planetary_positions(date_time_utc, coords):
    jd = swe.julday(date_time_utc.year, date_time_utc.month, date_time_utc.day,
                   date_time_utc.hour + date_time_utc.minute/60.0 + date_time_utc.second/3600.0)
   
    # സൂര്യന്റെ സ്ഥാനം
    sun_pos, sun_flags = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    sun_degree = apply_ayanamsa(sun_pos[0] % 360.0)
   
    # ചന്ദ്രന്റെ സ്ഥാനം
    moon_pos, moon_flags = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    moon_degree = apply_ayanamsa(moon_pos[0] % 360.0)
   
    return {
        'sun': sun_degree,
        'moon': moon_degree,
        'jd': jd
    }

# പാദം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_pada(degree, nakshatra):
    nakshatra_range = nakshatra['end'] - nakshatra['start']
    position_in_nakshatra = (degree - nakshatra['start']) % 360.0
    pada = int(position_in_nakshatra / (nakshatra_range / 4)) + 1
    return min(max(pada, 1), 4)

# കൃത്യമായ കരണം കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_karana(thithi_number, moon_sun_diff, thithi_progress):
    if moon_sun_diff < 180:
        karana_list = SHUKLA_PAKSHA_KARANAS
    else:
        karana_list = KRISHNA_PAKSHA_KARANAS
   
    mapped_thithi = ((thithi_number - 1) % 15) + 1
   
    if mapped_thithi == 15:
        karana_pair = karana_list[mapped_thithi]
        karana_index = 0 if thithi_progress < 6 else 1
        current_karana = karana_pair[karana_index]
        return current_karana
   
    if mapped_thithi in karana_list:
        karana_pair = karana_list[mapped_thithi]
        karana_index = 0 if thithi_progress < 6 else 1
        current_karana = karana_pair[karana_index]
        return current_karana
   
    return "അജ്ഞാതം"

# തിഥി കണ്ടെത്തുന്ന ഫംഗ്ഷൻ
def find_thithi(moon_degree, sun_degree):
    moon_sun_diff = (moon_degree - sun_degree) % 360.0
    thithi_index = int(moon_sun_diff / 12.0)
    thithi_number = thithi_index + 1
    thithi_progress = (moon_sun_diff % 12.0)
   
    paksha = "ശുക്ല പക്ഷം" if moon_sun_diff < 180 else "കൃഷ്ണ പക്ഷം"
   
    if thithi_number == 15:
        thithi_name = "പൗർണ്ണമി"
    elif thithi_number == 30:
        thithi_name = "അമാവാസി"
    else:
        actual_thithi_index = (thithi_number - 1) % 15
        thithi_name = THITHIS[actual_thithi_index]
   
    return {
        'number': thithi_number,
        'name': thithi_name,
        'moon_sun_diff': moon_sun_diff,
        'progress': thithi_progress,
        'paksha': paksha
    }

# നക്ഷത്ര നാഴിക കണക്കാക്കുന്ന ഫംഗ്ഷൻ (ശരിയായ രീതി)
def calculate_nakshatra_nazhika(current_dt_utc, timezone, current_moon_deg, nakshatra_start):
    try:
        # നാളത്തെ ഇതേ സമയത്തെ ചന്ദ്ര ഡിഗ്രി കണക്കാക്കുന്നു
        next_day_dt_utc = current_dt_utc + timedelta(days=1)
        next_day_positions = calculate_planetary_positions(next_day_dt_utc, {})
        next_day_moon_deg = next_day_positions['moon']
       
        # ചന്ദ്രന്റെ ഒരു ദിവസത്തെ സഞ്ചരണ വേഗത
        moon_speed_per_day = (next_day_moon_deg - current_moon_deg) % 360.0
        if moon_speed_per_day < 0:
            moon_speed_per_day += 360.0
           
        # ഒരു മണിക്കൂറിൽ ചന്ദ്രൻ സഞ്ചരിക്കുന്ന ഡിഗ്രി
        moon_speed_per_hour = moon_speed_per_day / 24.0
       
        # നിലവിലെ ചന്ദ്ര ഡിഗ്രിയിൽ നിന്ന് നക്ഷത്രം തുടങ്ങിയ ഡിഗ്രിയിലേക്കുള്ള ദൂരം
        distance_to_start = (current_moon_deg - nakshatra_start) % 360.0
       
        # ഈ ദൂരം സഞ്ചരിക്കാൻ എടുക്കുന്ന സമയം (മണിക്കൂറിൽ)
        time_to_start_hours = distance_to_start / moon_speed_per_hour
       
        # നക്ഷത്രം തുടങ്ങിയ സമയം
        nakshatra_start_time_utc = current_dt_utc - timedelta(hours=time_to_start_hours)
       
        # നക്ഷത്രം തുടങ്ങിയ സമയം മുതൽ നിലവിലെ സമയം വരെ എടുത്ത സമയം
        elapsed_time = current_dt_utc - nakshatra_start_time_utc
        elapsed_hours = elapsed_time.total_seconds() / 3600.0
       
        # മണിക്കൂറിനെ നാഴിക വിനാഴികയിലേക്ക് മാറ്റുന്നു
        # 1 നാഴിക = 24 മിനിറ്റ്, 1 വിനാഴിക = 24 സെക്കൻഡ്
        total_nazhikas = elapsed_hours * (60.0 / 24.0)  # 1 മണിക്കൂർ = 2.5 നാഴിക
        nazhikas = int(total_nazhikas)
        vinazhikas = (total_nazhikas - nazhikas) * 60.0  # 1 നാഴിക = 60 വിനാഴിക
       
        return f"{nazhikas} നാഴിക {vinazhikas:.1f} വിനാഴിക"
       
    except Exception as e:
        print(f"നക്ഷത്ര നാഴിക കണക്കാക്കുന്നതിൽ പിശക്: {e}")
        return "കണക്കാക്കാനായില്ല"

# പ്രധാന കണക്കുകൂട്ടൽ ഫംഗ്ഷൻ - app.py-ൽ നിന്ന് വിവരങ്ങൾ എടുക്കുന്നു
def nakshatradi_calculation(data):
    try:
        # app.py-ൽ നിന്ന് വിവരങ്ങൾ എടുക്കുന്നു
        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        hour_24h = int(data.get('hour_24h', 12))
        minute = int(data.get('minute', 0))
        place = data.get('place', {})
       
        # സ്ഥലം അനുസരിച്ച് കോർഡിനേറ്റുകൾ
        place_name = place.get('name', 'കണ്ണൂർ')
        lat = place.get('lat', 11.8745)
        lon = place.get('lng', 75.3704)
        timezone_input = place.get('timezone', 'Asia/Kolkata')
       
        timezone = parse_timezone(timezone_input)

        # സ്ഥാനീയ സമയം
        local_dt = datetime(year, month, day, hour_24h, minute, 0)
       
        # UTC സമയത്തിലേക്ക് മാറ്റുന്നു
        utc_dt = local_to_utc(local_dt, timezone)

        coords = {'lat': lat, 'lon': lon, 'timezone': timezone}

        # ഗ്രഹ സ്ഥാനം കണക്കാക്കുന്നു
        positions = calculate_planetary_positions(utc_dt, coords)
        sun_deg = positions['sun']
        moon_deg = positions['moon']
        jd = positions['jd']

        # നക്ഷത്രം കണ്ടെത്തുന്നു
        nak = find_nakshatra(moon_deg)
        pada = find_pada(moon_deg, nak)

        # തിഥി കണ്ടെത്തുന്നു
        thithi = find_thithi(moon_deg, sun_deg)

        # കരണം കണ്ടെത്തുന്നു
        karana = find_karana(thithi['number'], thithi['moon_sun_diff'], thithi['progress'])

        # യോഗം കണ്ടെത്തുന്നു
        yoga_degree = (sun_deg + moon_deg) % 360.0
        yoga = find_yoga(yoga_degree)

        # നക്ഷത്ര നാഴിക കണക്കാക്കുന്നു (ശരിയായ രീതി)
        nakshatra_nazhika = calculate_nakshatra_nazhika(utc_dt, timezone, moon_deg, nak['start'])

        # തിഥി ദേവത
        thithi_devata_number = thithi['number'] if thithi['number'] <= 15 else 16
        thithi_devata = THITHI_DEVATAS.get(thithi_devata_number, "അജ്ഞാതം")

        # കൂറ് (ചന്ദ്ര രാശി)
        moon_rashi_index = int(moon_deg / 30.0)
        kooru = RASHIS[moon_rashi_index % 12]

        # ചന്ദ്രാഷ്ടമം (ശരിയായ രീതി)
        chandra_ashtamam = calculate_chandra_ashtamam(moon_rashi_index)

        # നക്ഷത്ര വിശദാംശങ്ങൾ
        nakshatra_details = NAKSHATRA_DETAILS.get(nak['name'], {})
       
        # HTML റിസൾട്ട് രൂപപ്പെടുത്തുന്നു
        calculation_date = f"{day:02d}/{month:02d}/{year}"
        calculation_time = f"{hour_24h:02d}:{minute:02d}"
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
        html_result = render_template_string(
            NAKSHATRADI_HTML_TEMPLATE,
            calculation_date=calculation_date,
            calculation_time=calculation_time,
            place_name=place_name,
            main_nakshatra=f"🌙 {nak['name']} - പാദം {pada} 🌟",
            nakshatra_name=nak['name'],
            pada=f"പാദം {pada}",
            nakshatra_nazhika=nakshatra_nazhika,
            thithi_name=thithi['name'],
            paksha=thithi['paksha'],
            thithi_devata=thithi_devata,
            karana=karana,
            yoga=yoga['name'],
            kooru=kooru,
            chandra_ashtamam=chandra_ashtamam,
            gana=nakshatra_details.get('ഗണം', 'അജ്ഞാതം'),
            yoni=nakshatra_details.get('യോനി', 'അജ്ഞാതം'),
            nakshatra_devata=nakshatra_details.get('ദേവത', 'അജ്ഞാതം'),
            bhuta=nakshatra_details.get('ഭൂതം', 'അജ്ഞാതം'),
            mrga=nakshatra_details.get('മൃഗം', 'അജ്ഞാതം'),
            pakshi=nakshatra_details.get('പക്ഷി', 'അജ്ഞാതം'),
            vriksha=nakshatra_details.get('വൃക്ഷം', 'അജ്ഞാതം'),
            current_timestamp=current_timestamp
        )

        return html_result

    except Exception as e:
        print(f"❌ Error in nakshatradi_calculation: {str(e)}")
        error_html = f"""
        <div style="padding: 20px; background: #ffebee; border: 2px solid #f44336; border-radius: 10px; text-align: center;">
            <h2 style="color: #d32f2f;">പിശക്!</h2>
            <p style="color: #b71c1c; font-size: 18px;">നക്ഷത്രാദി വിശേഷം കണക്കാക്കാനായില്ല: {str(e)}</p>
        </div>
        """
        return error_html

# Flask app സൃഷ്ടിക്കുന്നു (വേറെ വിൻഡോയിൽ കാണിക്കാൻ)
app = Flask(__name__)

@app.route('/nakshatradi')
def nakshatradi_page():
    """നക്ഷത്രാദി വിശേഷം വേറെ വിൻഡോയിൽ കാണിക്കാൻ"""
    try:
        # URL പാരാമീറ്ററുകൾ എടുക്കുന്നു
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        day = request.args.get('day', type=int)
        hour_24h = request.args.get('hour_24h', 12, type=int)
        minute = request.args.get('minute', 0, type=int)
        place_name = request.args.get('place', 'കണ്ണൂർ')
       
        # സ്ഥലം അനുസരിച്ച് കോർഡിനേറ്റുകൾ
        place_data = {
            'name': place_name,
            'lat': 11.8745 if place_name == 'കണ്ണൂർ' else 8.5241,
            'lng': 75.3704 if place_name == 'കണ്ണൂർ' else 76.9366,
            'timezone': 'Asia/Kolkata'
        }
       
        calculation_data = {
            'year': year,
            'month': month,
            'day': day,
            'hour_24h': hour_24h,
            'minute': minute,
            'place': place_data
        }
       
        return nakshatradi_calculation(calculation_data)
       
    except Exception as e:
        error_html = f"""
        <div style="padding: 20px; background: #ffebee; border: 2px solid #f44336; border-radius: 10px; text-align: center;">
            <h2 style="color: #d32f2f;">പിശക്!</h2>
            <p style="color: #b71c1c; font-size: 18px;">വിവരങ്ങൾ ലഭ്യമല്ല: {str(e)}</p>
        </div>
        """
        return error_html

if __name__ == '__main__':
    print("🚀 Starting Nakshatradi Module...")
    app.run(host='0.0.0.0', port=5001, debug=True)
