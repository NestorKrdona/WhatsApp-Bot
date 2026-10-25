import json
from loguru import logger
import re
import urllib.parse

def print_separator(char='-', length=50):
    """Imprime un separador de caracteres."""
    logger.info(char * length)
    
def sanitize_phone(number: str, default_country="57"):
    digits = re.sub(r"\D", "", str(number))
    # si tienen 10 o menos dígitos, asumir que falta código de país (colombia=57)
    if len(digits) <= 10:
        digits = default_country + digits
    return digits

def encode_text(text: str):
    return urllib.parse.quote_plus(text or "")