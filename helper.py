import re
import numpy as np

def convert_percentage_to_float(str):
    p_strings = re.findall(r"\d+,\d", str)
    if len(p_strings) == 0:
        p_strings = re.findall(r"\d+", str)
    p_floats = [float(s.replace(",", ".")) for s in p_strings]
    return sum(p_floats) if not "-" in str else sum(p_floats)/2

def convert_befragte(str):

    if str == "Bundestagswahl" or "?" in str:
        return np.NaN

    s = str
    to_replace = ".~≈>"
    for r in to_replace:
        s = s.replace(r, "")

    s = re.findall(r"\d+", s)[0]

    return int(s)

months = {
    "Jan": 1,
    "Feb": 2,
    "Mrz": 3,
    "Apr": 4,
    "Mai": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Dez": 12
}

def convert_weird_date_to_date(str):
    if bool(re.match(r"\w{3}.? \d{4}", str)):
        return f"15.{months[str[:3]]}.{str[-4:]}"
    else:
        return str