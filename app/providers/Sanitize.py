import re

def contains_invisible_characters(text):
    return bool(re.search(r'[\u200B\u200C\u200D\u200E\u200F\u202A-\u202E\u2060\u2061\u2062\u2063\u2064\u2066-\u2069\uFEFF]', text))