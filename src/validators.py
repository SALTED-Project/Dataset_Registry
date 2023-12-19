import ipaddress
from urllib.parse import urlparse


def is_valid_hostname(hostname):
    if hostname[-1] == ".":
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]
    if len(hostname) > 253:
        return False

    labels = hostname.split(".")

    # the TLD must be not all-numeric
    if re.match(r"[0-9]+$", labels[-1]):
        return False

    allowed = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(label) for label in labels)


def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_port(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


THEMES = [
    "AGRI",
    "OP_DATPRO",
    "ENVI",
    "TRAN",
    "JUST",
    "ENER",
    "TECH",
    "INTR",
    "EDUC",
    "SOCI",
    "HEAL",
    "ECON",
    "REGI",
    "EDUC",
    "GOVE"
]


def get_theme(theme_number):
    return THEMES[theme_number]


# ISO 639-3
LANGUAGES = ["ENG", "SPA", "DEU", "FRA"]


def get_language(language_number):
    return LANGUAGES[language_number]


# ISO 639-3
ACCESS_RIGHTS = ["PUBLIC", "RESTRICTED", "PRIVATE"]


def get_access_rights(ar_number):
    return ACCESS_RIGHTS[ar_number-1]


# ISO 639-3
LOCATIONS = [
"AUT",
"BEL",
"BGR",
"HRV",
"CYP",
"CZE",
"DNK",
"EST",
"FIN",
"FRA",
"DEU",
"HUN",
"IRL",
"ITA",
"LVA",
"LTU",
"LUX",
"MLT",
"NLD",
"NOR",
"POL",
"PRT",
"ROU",
"SVK",
"SVN",
"ESP",
"SWE",
"CHE",
"GBR",
"EUROPE",
"OP_DATPRO"
]

def get_location(location_number):
    return LOCATIONS[location_number]

