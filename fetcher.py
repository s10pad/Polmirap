import requests
import json
import re
import time
from datetime import datetime, timezone

HEADERS = {'User-Agent': 'MirrorAI arnaudpkengni@2gmail.com'}

INVESTORS_13F = {
    'buffett': {'cik': '0001067983', 'cik_int': 1067983,  'name': 'Warren Buffett'},
    'ackman':  {'cik': '0001336528', 'cik_int': 1336528,  'name': 'Bill Ackman'},
    'burry':   {'cik': '0001649339', 'cik_int': 1649339,  'name': 'Michael Burry'},
    'dalio':   {'cik': '0001350694', 'cik_int': 1350694,  'name': 'Ray Dalio'},
}

def parse_xml_holdings(xml_content):
    # handle both plain tags and ns1: namespaced tags
    def findall(tag):
        results = re.findall(rf'<(?:ns1:)?{tag}>(.*?)</(?:ns1:)?{tag}>', xml_content, re.DOTALL)
        return [r.strip() for r in results]

    names  = findall('nameOfIssuer')
    values = findall('value')
    shares = findall('sshPrnamt')
    cusips = findall('cusip')

    holdings = []
    for i in range(min(len(names), len(values))):
        val = values[i].replace(',', '').strip()
        shr = shares[i].replace(',', '').strip() if i < len(shares) else '0'
        holdings.append({
            'name':   names[i],
            'cusip':  cusips[i] if i < len(cusips) else '',
            'value':  int(val) if val.isdigit() else 0,
            'shares': int(shr) if shr.isdigit() else 0,
        })
    holdings.sort(key=lambda x: x['value'], reverse=True)
    return holdings


def fetch_13f(key, cik, cik_int, name):
    print(f"Fetching 13F for {name}...")
    subs = requests.get(f'https://data.sec.gov/submissions/CIK{cik}.json', headers=HEADERS).json()
    recent = subs['filings']['recent']

    accession = filing_date = None
    for i, form in enumerate(recent['form']):
        if form == '13F-HR':
            accession   = recent['accessionNumber'][i].replace('-', '')
            filing_date = recent['filingDate'][i]
            break

    if not accession:
        print(f"  No 13F found")
        return []

    print(f"  Filing date: {filing_date}")
    idx = requests.get(f'https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/', headers=HEADERS)
    xml_files = re.findall(r'href="(/Archives/edgar/data/[^"]+\.xml)"', idx.text)

    info_xml = None
    for xf in xml_files:
        if 'primary_doc' not in xf.lower():
            info_xml = 'https://www.sec.gov' + xf
            break

    if not info_xml:
        print(f"  No info table XML found")
        return []

    print(f"  Parsing: {info_xml.split('/')[-1]}")
    xml = requests.get(info_xml, headers=HEADERS).text
    holdings = parse_xml_holdings(xml)
    print(f"  Parsed {len(holdings)} holdings")
    time.sleep(0.6)
    return holdings[:25]


def fetch_ark_wood():
    print("Fetching ARK holdings for Cathie Wood...")
    r = requests.get('https://arkfunds.io/api/v2/etf/holdings?symbol=ARKK', headers=HEADERS)
    if r.status_code != 200:
        print(f"  arkfunds.io failed: {r.status_code}")
        return []
    data = r.json()
    holdings = []
    for h in data.get('holdings', [])[:25]:
        holdings.append({
            'name':   h.get('company', ''),
            'ticker': h.get('ticker', ''),
            'value':  int(float(h.get('market_value', 0))),
            'shares': int(float(h.get('shares', 0))),
            'weight': h.get('weight', 0),
        })
    print(f"  Parsed {len(holdings)} holdings")
    return holdings


def fetch_pelosi_congress():
    print("Fetching Congress trades from EDGAR full-text search...")
    # Pelosi files Form 4 and periodic transaction reports via eFD
    # We search EDGAR for her directly and also pull
    # recent congressional stock act filings from SEC EDGAR search
    trades = []

    # Search for Pelosi in EDGAR
    r = requests.get(
        'https://efts.sec.gov/LATEST/search-index?q=%22Nancy+Pelosi%22&forms=4&dateRange=custom&startdt=2023-01-01',
        headers=HEADERS
    )
    if r.status_code == 200:
        hits = r.json().get('hits', {}).get('hits', [])
        print(f"  Found {len(hits)} EDGAR filings mentioning Pelosi")
        for h in hits[:10]:
            src = h.get('_source', {})
            trades.append({
                'date':   src.get('period_of_report', ''),
                'entity': src.get('entity_name', ''),
                'form':   src.get('form_type', ''),
                'file':   src.get('file_num', ''),
            })

    # Also extract tickers visible in Capitol Trades page
    # even though JS renders the table, ticker symbols are in the HTML
    r2 = requests.get(
        'https://www.capitoltrades.com/trades?politician=P000197&per_page=96',
        headers=HEADERS
    )
    # extract tickers that appear near buy/sell context
    known_tickers = re.findall(
        r'\b(GOOGL|AMZN|AAPL|NVDA|MSFT|TSLA|META|JPM|UNH|JNJ|PG|NFLX|AMD|'
        r'INTC|CRM|PYPL|DIS|BA|GS|MS|V|MA|HD|WMT|CVX|XOM|BAC)\b',
        r2.text
    )
    from collections import Counter
    ticker_counts = Counter(known_tickers).most_common(15)
    print(f"  Extracted {len(ticker_counts)} tickers from Capitol Trades page")
    for ticker, count in ticker_counts:
        trades.append({
            'ticker':     ticker,
            'politician': 'Nancy Pelosi',
            'mentions':   count,
            'source':     'capitoltrades_html',
        })

    return trades


def fetch_musk_form4():
    print("Fetching Form 4 filings for Elon Musk...")
    r = requests.get('https://data.sec.gov/submissions/CIK0001494730.json', headers=HEADERS).json()
    recent = r['filings']['recent']
    trades = []
    for i, form in enumerate(recent['form']):
        if form == '4':
            trades.append({
                'date':      recent['filingDate'][i],
                'accession': recent['accessionNumber'][i],
            })
            if len(trades) >= 10:
                break
    print(f"  Found {len(trades)} Form 4 filings")
    return trades


if __name__ == '__main__':
    results = {}

    for key, inv in INVESTORS_13F.items():
        print(f"\n{'='*45}")
        holdings = fetch_13f(key, inv['cik'], inv['cik_int'], inv['name'])
        results[key] = holdings
        if holdings:
            print(f"  Top 3:")
            for h in holdings[:3]:
                print(f"    {h['name']}: ${h['value']:,}k")

    print(f"\n{'='*45}")
    results['wood'] = fetch_ark_wood()
    if results['wood']:
        print(f"  Top 3:")
        for h in results['wood'][:3]:
            print(f"    {h['name']}: ${h['value']:,}")

    print(f"\n{'='*45}")
    results['pelosi'] = fetch_pelosi_congress()

    print(f"\n{'='*45}")
    results['musk'] = fetch_musk_form4()

    print(f"\n{'='*45}")
    with open('/home/ubuntu/holdings.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved to holdings.json")

    print("\nSummary:")
    for k, v in results.items():
        print(f"  {k:10s}: {len(v)} records")
EOF

python3 /home/ubuntu/fetcher.py
