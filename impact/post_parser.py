import re
from dataclasses import dataclass, asdict

SECTOR_RULES = [
    (r'\b(road|roads|grading|culvert|bridge|murram|tarmac|transport|connectivity)\b', 'Roads & Connectivity'),
    (r'\b(school|classroom|laboratory|bursary|education|student|teacher)\b', 'Education'),
    (r'\b(water|borehole|tank|pipeline|irrigation|sanitation)\b', 'Water & Sanitation'),
    (r'\b(health|hospital|dispensary|clinic|maternity)\b', 'Health'),
    (r'\b(market|trade|business|enterprise|trader)\b', 'Trade & Local Economy'),
    (r'\b(electricity|street ?light|solar|power|energy)\b', 'Energy & Lighting'),
    (r'\b(sport|stadium|football|youth|talent)\b', 'Youth & Sports'),
    (r'\b(tree|climate|environment|wetland|forest|restoration)\b', 'Environment & Climate'),
]

CAMPAIGN_PATTERNS = [
    r'\bthree terms? unopposed\b', r'\bvote\b', r'\bre[- ]?elect\b', r'\breelection\b',
    r'\bkiongozi\b', r'\bteam [a-z0-9_-]+\b', r'\bkokere\s*\d*\b', r'\bpindra update\b',
]

BENEFIT_HINTS = {
    'connect': 'Improved local connectivity',
    'movement': 'Easier movement for residents',
    'market': 'Improved access to markets',
    'trade': 'Support for local trade and businesses',
    'farmer': 'Improved access for farmers',
    'economic': 'Potential to stimulate local economic activity',
    'school': 'Improved access to education services',
    'water': 'Improved access to water services',
    'health': 'Improved access to health services',
}

@dataclass
class ParsedPost:
    headline: str
    short_title: str
    ward: str
    sector: str
    intervention: str
    project_location: str
    summary: str
    impacts: list
    excluded_campaign_lines: list
    verification_status: str = 'submitted'


def _strip_emoji_noise(text: str) -> str:
    text = text.replace('\r', '')
    text = re.sub(r'[\u200d\ufe0f]', '', text)
    text = re.sub(r'^[\s\W_]+|[\s\W_]+$', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _detect_ward(text: str, ward_names):
    low = text.lower()
    for name in sorted(ward_names, key=len, reverse=True):
        if name.lower() in low:
            return name
    m = re.search(r'([A-Z][A-Za-z’\' -]{2,40})\s+Ward', text, flags=re.I)
    return _strip_emoji_noise(m.group(1)) + ' Ward' if m else ''


def _detect_sector(text: str):
    for pattern, sector in SECTOR_RULES:
        if re.search(pattern, text, flags=re.I):
            return sector
    return 'Community Development'


def _extract_route(text: str):
    # Strongest signal: a sentence containing a chain of 3+ dash-separated locations.
    candidates = re.findall(r'([A-Z][^\n.!?]{5,220}(?:–|-)[^\n.!?]{3,220})', text)
    for c in candidates:
        cleaned = _strip_emoji_noise(c)
        if sum(cleaned.count(x) for x in ['–', '-']) >= 2:
            cleaned = re.sub(r'^(the newly constructed|newly constructed)\s+', '', cleaned, flags=re.I)
            cleaned = re.sub(r'\s+Road$', '', cleaned, flags=re.I)
            return cleaned
    # Fallback to phrases after "constructed/opened" and before "road".
    m = re.search(r'(?:constructed|opening of|grading of)\s+(?:the\s+)?(?:newly\s+constructed\s+)?(.{8,220}?)\s+Road\b', text, flags=re.I|re.S)
    return _strip_emoji_noise(m.group(1)) if m else ''


def _clean_lines(text: str):
    result, excluded = [], []
    for raw in text.splitlines():
        line = _strip_emoji_noise(raw)
        if not line:
            continue
        if any(re.search(p, line, flags=re.I) for p in CAMPAIGN_PATTERNS):
            excluded.append(line)
            continue
        result.append(line)
    return result, excluded


def parse_social_post(text: str, ward_names=()):
    lines, excluded = _clean_lines(text)
    clean = '\n'.join(lines)
    ward = _detect_ward(clean, ward_names)
    sector = _detect_sector(clean)
    route = _extract_route(clean)

    headline = lines[0] if lines else 'Imported project update'
    headline = re.sub(r'\bUPDATE\b.*$', '', headline, flags=re.I).strip(' -–—:') or headline

    if route:
        short_title = route
        if len(short_title) > 155:
            short_title = short_title[:152].rstrip() + '…'
    else:
        # Choose first non-heading sentence as a stable project title.
        short_title = headline.title()[:155]

    intervention = ''
    low = clean.lower()
    if 'completely new road' in low or 'new road' in low or 'newly constructed' in low:
        intervention = 'Opening and grading of a new road connection'
    elif 'grading' in low and 'road' in low:
        intervention = 'Road grading and access improvement'
    elif sector == 'Education':
        intervention = 'Education infrastructure/support intervention'
    elif sector == 'Water & Sanitation':
        intervention = 'Water and sanitation intervention'

    # Select concise factual sentences, excluding direct political attribution/praise.
    sentences = re.split(r'(?<=[.!?])\s+', re.sub(r'\n+', ' ', clean))
    factual = []
    for s in sentences:
        s = _strip_emoji_noise(s)
        if not s:
            continue
        if re.search(r'Hon\.|together,|embrace|associated with development', s, flags=re.I):
            continue
        factual.append(s)
    summary = ' '.join(factual[:2])[:700]

    impacts = []
    low = clean.lower()
    for needle, impact in BENEFIT_HINTS.items():
        if needle in low and impact not in impacts:
            impacts.append(impact)
    impacts = impacts[:5]

    location = route or (ward if ward else '')
    return asdict(ParsedPost(
        headline=headline[:240], short_title=short_title, ward=ward, sector=sector,
        intervention=intervention, project_location=location, summary=summary,
        impacts=impacts, excluded_campaign_lines=excluded,
    ))
