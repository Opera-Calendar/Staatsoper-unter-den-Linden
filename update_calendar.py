#!/usr/bin/env python3
"""Create a rolling opera-only calendar from Staatsoper Berlin's official pages.
Fails safely: an empty scrape never overwrites a previously published calendar.
"""
import calendar
import datetime as dt
import hashlib
import logging
import re
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm

BASE = 'https://www.staatsoper-berlin.de'
OUT = Path('staatsoper-berlin-opera.ics')
TZ = ZoneInfo('Europe/Berlin')
MONTHS_AHEAD = 18
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; OperaCalendar/1.0; calendar personal use)'}
GERMAN_MONTHS = {'januar':1, 'februar':2, 'märz':3, 'maerz':3, 'april':4, 'mai':5,
                 'juni':6, 'juli':7, 'august':8, 'september':9, 'oktober':10,
                 'november':11, 'dezember':12}
ABBR = {'jan':1, 'feb':2, 'mär':3, 'mrz':3, 'apr':4, 'mai':5, 'jun':6, 'jul':7,
        'aug':8, 'sep':9, 'okt':10, 'nov':11, 'dez':12}
DATE_RE = re.compile(r'(?P<day>\d{1,2})\.\s*(?P<month>Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(?P<year>20\d{2})\s+(?P<hour>\d{1,2})[.:](?P<minute>\d{2})\s*Uhr', re.I)
DURATION_RE = re.compile(r'Dauer:\s*(?:ca\.?\s*)?(?:(\d{1,2}):([0-5]\d)\s*h|(\d{1,2})\s*h(?:\s*(\d{1,2})\s*min)?)', re.I)
KNOWN_OPERAS = {
    'la calisto','la vestale','manon lescaut','königskinder','la forza del destino',
    'die fledermaus für kinder','ariadne auf naxos','die entführung aus dem serail',
    'die zauberflöte','la bohème','madama butterfly','la traviata','nabucco',
    'rigoletto',"l’elisir d’amore","l'elisir d'amore",'les pêcheurs de perles',
    'samson et dalila','tannhäuser','tristan und isolde','die zarenbraut',
    'idomeneo','l’incoronazione di poppea',"l'incoronazione di poppea",
    'dido & aeneas','orfeo ed euridice','tosca','der rosenkavalier',
    'il barbiere di siviglia'
}
EXCLUDE = re.compile(r'konzert|liederabend|führung|vor-führung|workshop|gespräch|matinée|apollo-salon|ballett|gastspiel in|symphon|sinfon|recital|lesung|kammermusik|salon', re.I)

session = requests.Session()
session.headers.update(HEADERS)

def soup_for(url):
    resp = session.get(url, timeout=35)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')

def monday_windows(today, months=MONTHS_AHEAD):
    first = dt.date(today.year, today.month, 1)
    end_month = first.month - 1 + months
    last_year = first.year + end_month // 12
    last_month = end_month % 12 + 1
    last = dt.date(last_year, last_month, calendar.monthrange(last_year, last_month)[1])
    current = today
    while current <= last:
        yield current
        current += dt.timedelta(days=7)

def find_productions(today):
    urls = set()
    good_pages = 0
    for day in monday_windows(today):
        url = f'{BASE}/de/spielplan/{day:%d-%m-%Y}/'
        try:
            soup = soup_for(url)
            good_pages += 1
            for a in soup.select('a[href*="/de/veranstaltungen/"]'):
                url = urljoin(BASE, a.get('href', '')).split('?')[0].split('#')[0]
                if url.startswith(BASE + '/de/veranstaltungen/'):
                    urls.add(url)
        except requests.RequestException as exc:
            logging.warning('Spielplan-Seite fehlgeschlagen %s: %s', url, exc)
    if good_pages < 5:
        raise RuntimeError(f'Nur {good_pages} Spielplan-Seiten erreichbar, Kalender bleibt unverändert')
    return sorted(urls)

def parse_date(m):
    month = GERMAN_MONTHS[m.group('month').lower()]
    return dt.datetime(int(m.group('year')),month,int(m.group('day')),
                       int(m.group('hour')),int(m.group('minute')),tzinfo=TZ)

def estimate_duration(text):
    match = DURATION_RE.search(text)
    if not match:
        return dt.timedelta(hours=3), False
    if match.group(1):
        minutes = int(match.group(1))*60 + int(match.group(2))
    else:
        minutes = int(match.group(3))*60 + int(match.group(4) or 0)
    return dt.timedelta(minutes=minutes), True

def is_opera(title, text):
    norm = ' '.join(title.casefold().split())
    if EXCLUDE.search(norm):
        return False
    if norm in KNOWN_OPERAS:
        return True
    # On event detail pages the opera genre is usually stated in the intro.
    intro = text[:1800].casefold()
    positive = ('oper in ', 'operette in ', 'dramma per musica', 'opera seria',
                'melodramma', 'musikdrama', 'singspiel in ', 'musik von ',
                'opéra comique', 'tragédie lyrique', 'bühnenwerk')
    return any(p in intro for p in positive) and not re.search(r'\b(konzert|ballett|tanzabend|liederabend)\b', intro[:400])

def collect_events(today):
    found = {}
    urls = find_productions(today)
    logging.info('Entdeckte Veranstaltungsseiten: %s',len(urls))
    for url in urls:
        try:
            soup = soup_for(url)
        except requests.RequestException as exc:
            logging.warning('Eventseite fehlgeschlagen %s: %s',url,exc)
            continue
        heading = soup.find('h1')
        if not heading:
            continue
        title = heading.get_text(' ',strip=True)
        text = soup.get_text(' ',strip=True)
        if not is_opera(title,text):
            continue
        # Dates are visible for each performance; restrict to the actual Berlin opera house.
        # Date list at top can include a stale season, so use the per-performance date blocks
        # when possible, and keep only performances in the rolling future period.
        full = soup.get_text('\n',strip=True)
        matches = list(DATE_RE.finditer(full))
        if not matches:
            logging.warning('Keine Termine erkannt: %s',url)
            continue
        duration, verified = estimate_duration(text)
        for match in matches:
            start = parse_date(match)
            if start.date() < today or start.date() > today + dt.timedelta(days=570):
                continue
            # Verify location near per-performance date; top date-navigation does not state it.
            trailing = full[match.end():match.end()+250]
            if 'Staatsoper Unter den Linden' not in trailing:
                continue
            key = (title,start.isoformat())
            found[key] = dict(title=title,start=start,end=start+duration,url=url,
                              duration_verified=verified)
    return sorted(found.values(),key=lambda x:x['start'])

def write_ics(items):
    cal = Calendar()
    cal.add('prodid','-//Opera Schedules//Staatsoper Unter den Linden//DE')
    cal.add('version','2.0')
    cal.add('calscale','GREGORIAN')
    cal.add('method','PUBLISH')
    cal.add('x-wr-calname','Staatsoper Unter den Linden – Opern')
    cal.add('x-wr-timezone','Europe/Berlin')
    stamp = dt.datetime.now(dt.timezone.utc)
    for item in items:
        ev = Event()
        ev.add('uid',hashlib.sha256(f"{item['url']}|{item['start'].isoformat()}".encode()).hexdigest()[:32]+'@opera-schedules')
        ev.add('dtstamp',stamp)
        ev.add('dtstart',item['start'])
        ev.add('dtend',item['end'])
        ev.add('summary',item['title'])
        ev.add('location','Staatsoper Unter den Linden, Unter den Linden 7, 10117 Berlin')
        status = 'Offizielle Dauer' if item['duration_verified'] else 'Dauer nicht publiziert; 3 Stunden Platzhalter'
        ev.add('description',f"Opernvorstellung\n{status}\nQuelle: {item['url']}")
        ev.add('url',item['url'])
        for days in (90,30,7,1):
            alarm = Alarm()
            alarm.add('action','DISPLAY')
            alarm.add('description',f"{item['title']} – Staatsoper Berlin")
            alarm.add('trigger',dt.timedelta(days=-days))
            ev.add_component(alarm)
        cal.add_component(ev)
    OUT.write_bytes(cal.to_ical())

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,format='%(levelname)s %(message)s')
    today = dt.datetime.now(TZ).date()
    items = collect_events(today)
    if len(items)<5:
        raise RuntimeError(f'Nur {len(items)} Aufführungen erkannt; keine Kalenderüberschreibung')
    write_ics(items)
    print(f'Kalender erstellt: {len(items)} Aufführungen -> {OUT}')
