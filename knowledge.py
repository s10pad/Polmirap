"""
knowledge.py — curated profiles for tickers, traders, and the scoring algorithm.
No API needed. Updated manually when needed.
"""

# ─────────────────────────────────────────────
# TICKER PROFILES
# sector, one-line description, long summary, risk level (1-5)
# ─────────────────────────────────────────────
TICKER_PROFILES = {
    'AAPL': {
        'company': 'Apple Inc.',
        'sector': 'Technology',
        'description': 'Consumer electronics, software, and services giant.',
        'summary': 'Apple is the world\'s largest company by market cap. Revenue is anchored by iPhone but increasingly driven by high-margin services (App Store, iCloud, Apple Pay). Buffett called it "probably the best business in the world." Consistent buybacks and dividend growth make it a core holding for long-term investors.',
        'risk': 2,
    },
    'MSFT': {
        'company': 'Microsoft Corp.',
        'sector': 'Technology',
        'description': 'Cloud computing, enterprise software, and AI infrastructure.',
        'summary': 'Azure is the #2 cloud platform globally and growing faster than AWS. The OpenAI partnership and Copilot integration across Office, GitHub, and Azure give Microsoft the most credible enterprise AI monetisation path of any large-cap. Strong free cash flow and recurring revenue make it a compounding machine.',
        'risk': 2,
    },
    'NVDA': {
        'company': 'NVIDIA Corp.',
        'sector': 'Semiconductors',
        'description': 'Dominant supplier of GPUs for AI training and inference.',
        'summary': 'NVIDIA controls ~80% of the AI training chip market. Data centre revenue has grown 5x in two years. The CUDA software ecosystem creates a deep moat — switching to a competitor chip requires rewriting years of code. High valuation reflects genuine scarcity of AI compute capacity at scale.',
        'risk': 3,
    },
    'AMZN': {
        'company': 'Amazon.com Inc.',
        'sector': 'Technology / Retail',
        'description': 'E-commerce, cloud computing (AWS), and advertising.',
        'summary': 'AWS is the world\'s largest cloud platform and generates the majority of Amazon\'s operating profit despite being a minority of revenue. Advertising is the fastest-growing segment. The retail business, once a loss-leader, is becoming meaningfully profitable as logistics density improves.',
        'risk': 2,
    },
    'PANW': {
        'company': 'Palo Alto Networks',
        'sector': 'Cybersecurity',
        'description': 'Enterprise cybersecurity platform across network, cloud, and endpoints.',
        'summary': 'Palo Alto is consolidating the fragmented cybersecurity market through "platformisation" — replacing dozens of point tools with one integrated stack. Pelosi has been a consistent buyer. The shift to subscription ARR from hardware makes revenue more predictable and margins structurally higher.',
        'risk': 3,
    },
    'META': {
        'company': 'Meta Platforms Inc.',
        'sector': 'Technology',
        'description': 'Social media (Facebook, Instagram, WhatsApp) and AI infrastructure.',
        'summary': 'Meta\'s ad business has recovered strongly after Apple\'s privacy changes, driven by AI-optimised ad placement. The company is investing aggressively in AI infrastructure and open-source LLMs (Llama). Mark Zuckerberg\'s "year of efficiency" in 2023 restored margin discipline after years of Metaverse overspend.',
        'risk': 3,
    },
    'GOOGL': {
        'company': 'Alphabet Inc.',
        'sector': 'Technology',
        'description': 'Search, YouTube, cloud (GCP), and AI research (DeepMind/Gemini).',
        'summary': 'Google Search remains the world\'s most profitable business per query. YouTube is the #2 streaming platform. GCP is gaining share in AI workloads, particularly in model training via TPUs. Gemini is a genuine competitor to GPT-4 in enterprise AI. Trades at a discount to Microsoft and Apple on earnings.',
        'risk': 2,
    },
    'AVGO': {
        'company': 'Broadcom Inc.',
        'sector': 'Semiconductors',
        'description': 'Custom AI chips, networking silicon, and enterprise software (VMware).',
        'summary': 'Pelosi\'s largest options position in 2024, up 97%. Broadcom makes the custom AI chips (XPUs) for Google, Meta, and ByteTik — the alternative to NVIDIA for hyperscalers that want to control their own silicon. The VMware acquisition adds a sticky enterprise software revenue stream.',
        'risk': 3,
    },
    'VST': {
        'company': 'Vistra Corp.',
        'sector': 'Energy / Utilities',
        'description': 'Power generation company pivoting to nuclear for AI data centres.',
        'summary': 'Vistra operates nuclear, natural gas, and solar generation. The AI data centre buildout has created unprecedented demand for reliable 24/7 power — exactly what nuclear delivers. Vistra\'s existing fleet of reactors is essentially impossible to replicate given NRC licensing timelines. A direct play on AI power demand.',
        'risk': 3,
    },
    'TEM': {
        'company': 'Tempus AI Inc.',
        'sector': 'Healthcare / AI',
        'description': 'AI-powered precision medicine and clinical data platform.',
        'summary': 'Tempus uses AI to analyse genomic and clinical data to guide cancer treatment decisions. Pelosi bought in Jan 2026. The company went public in 2024 and is building a proprietary dataset of de-identified patient records that becomes more valuable as the model improves — a classic data-network-effects moat.',
        'risk': 4,
    },
    'NKE': {
        'company': 'Nike Inc.',
        'sector': 'Consumer Discretionary',
        'description': 'Global athletic footwear, apparel, and equipment brand.',
        'summary': 'Nike is held by LeBron James, Michael Jordan (via Jordan Brand royalties), Cristiano Ronaldo, and Tom Brady — four of the most commercially successful athletes in history. All have personal brand equity tied to Nike\'s success. The stock has underperformed since 2021 and a new CEO is executing a turnaround with focus on wholesale and DTC balance.',
        'risk': 2,
    },
    'DKNG': {
        'company': 'DraftKings Inc.',
        'sector': 'Consumer Discretionary',
        'description': 'Online sports betting and daily fantasy sports platform.',
        'summary': 'DraftKings is the #2 US online sportsbook behind FanDuel. Jordan and Curry are both confirmed investors. Sports betting continues to legalise state-by-state; DraftKings has a first-mover advantage in most markets it enters. Still unprofitable but approaching EBITDA break-even as marketing spend matures.',
        'risk': 4,
    },
    'PFE': {
        'company': 'Pfizer Inc.',
        'sector': 'Healthcare / Pharma',
        'description': 'Global pharmaceutical company, vaccines, oncology, and antivirals.',
        'summary': 'Wyden and Collins, both on Senate health committees, bought Pfizer. The stock has fallen significantly from COVID-era highs as vaccine demand normalised. Pfizer is now pivoting to oncology via the Seagen acquisition. Trading near 10-year lows on a forward P/E under 12 — a value play on pipeline recovery.',
        'risk': 3,
    },
    'XOM': {
        'company': 'Exxon Mobil Corp.',
        'sector': 'Energy',
        'description': 'Integrated oil and gas supermajor.',
        'summary': 'Exxon is the largest US oil company and a consistent Dalio holding. The Pioneer Natural Resources acquisition in 2024 added the largest Permian Basin position of any operator. High free cash flow at current oil prices supports the dividend and buyback programme. A hedge against energy supply disruptions.',
        'risk': 2,
    },
    'LLY': {
        'company': 'Eli Lilly & Co.',
        'sector': 'Healthcare / Pharma',
        'description': 'Pharmaceutical company — leader in GLP-1 weight loss and diabetes drugs.',
        'summary': 'Lilly makes Mounjaro and Zepbound (tirzepatide) — the best-in-class GLP-1 drugs for diabetes and obesity. The addressable market is estimated at $100B+ annually. Supply constraints are the only limit on growth right now. One of the strongest earnings growth stories in the S&P 500.',
        'risk': 3,
    },
    'RTX': {
        'company': 'RTX Corp. (Raytheon)',
        'sector': 'Defence & Aerospace',
        'description': 'Missiles, radar systems, jet engines (Pratt & Whitney).',
        'summary': 'RTX is the top ITA ETF holding. European rearmament and US defence budget growth are structural tailwinds. The Pratt & Whitney GTF engine issue is being resolved. Backlog is at record levels. A direct beneficiary of geopolitical tension regardless of which party controls Washington.',
        'risk': 2,
    },
    'PLTR': {
        'company': 'Palantir Technologies',
        'sector': 'Technology / AI',
        'description': 'AI and data analytics platform for government and enterprise.',
        'summary': 'Burry\'s top holding. Palantir\'s AIP (Artificial Intelligence Platform) is winning government contracts at an accelerating pace. US commercial revenue is growing at 50%+ YoY. The company is one of the few AI software companies with a clear, recurring revenue model rather than a story.',
        'risk': 4,
    },
    'AXP': {
        'company': 'American Express Co.',
        'sector': 'Financials',
        'description': 'Premium credit card network and travel services.',
        'summary': 'Buffett\'s largest holding. AmEx earns from merchant fees (a toll on spending) and interest. Its premium customer base (high income, low default rates) means it outperforms peers in downturns. Millennial and Gen-Z adoption of the Platinum and Gold cards has surprised the market and re-accelerated growth.',
        'risk': 2,
    },
}

# ─────────────────────────────────────────────
# TRADER BIOS
# For politicians, CEOs, athletes — shown in the detail panel
# ─────────────────────────────────────────────
TRADER_BIOS = {
    # POLITICIANS
    'Nancy Pelosi': {
        'role': 'Former Speaker of the House · Democrat · California',
        'track_record': '+70.9% portfolio return in 2024 (vs S&P 500 +24.9%). Called "the greatest options trader of all time" by Unusual Whales. Known for large in-the-money call options on tech stocks years before expiry.',
        'style': 'Long-dated call options on large-cap tech. Concentrated positions. High conviction.',
        'notable': 'Nvidia calls in 2020 before major AI contracts. PANW and AVGO in 2024, both up 93–97%.',
    },
    'Roger Williams': {
        'role': 'Representative · Republican · Texas',
        'track_record': '+111.2% portfolio return in 2024. Top 4 in Congress for two consecutive years.',
        'style': 'Concentrated in financial services and Texas-linked energy companies. Active trader.',
        'notable': 'Consistent outperformer across multiple market cycles.',
    },
    'Debbie Schultz': {
        'role': 'Representative · Democrat · Florida',
        'track_record': '+142.3% portfolio return in 2024. #2 in all of Congress.',
        'style': 'Tech-focused. High turnover portfolio with frequent disclosures.',
        'notable': 'Second highest return in Congress in 2024 behind Rouzer (who held ETFs).',
    },
    'Ron Wyden': {
        'role': 'Senator · Democrat · Oregon · Senate Finance Committee',
        'track_record': '+123.8% in 2024. Consistent top-10 performer.',
        'style': 'Healthcare and pharma focus, aligned with Finance Committee jurisdiction.',
        'notable': 'Pharma picks often precede or coincide with legislative developments.',
    },
    'Pete Sessions': {
        'role': 'Representative · Republican · Texas',
        'track_record': '+77.5% in 2024. Top 10 in Congress.',
        'style': 'Broad large-cap tech. High volume of disclosures, active trader.',
        'notable': 'Consistent MSFT and NVDA buyer across multiple quarters.',
    },
    'Susan Collins': {
        'role': 'Senator · Republican · Maine · Senate Appropriations Committee',
        'track_record': '+77.5% in 2024.',
        'style': 'Healthcare, pharma, and defence — aligned with Appropriations Committee oversight.',
        'notable': 'PFE and defence names recur in her disclosures.',
    },
    'Tommy Tuberville': {
        'role': 'Senator · Republican · Alabama · Senate Armed Services Committee',
        'track_record': 'Top active trader in the Senate by volume. Known for trading near Armed Services hearings.',
        'style': 'Very high frequency. Defence stocks and broad market ETFs.',
        'notable': 'Scrutinised for trading defence stocks while blocking military promotions in 2023.',
    },
    'Marjorie Taylor Greene': {
        'role': 'Representative · Republican · Georgia',
        'track_record': '+30.2% in 2024. Accelerated trading activity in H2 2024.',
        'style': 'Large-cap tech concentration. Bought heavily after election win.',
        'notable': 'Significant tech purchases in Nov–Dec 2024 after the election.',
    },
    # CEOs / SUPERINVESTORS
    'Warren Buffett': {
        'role': 'Chairman & CEO, Berkshire Hathaway',
        'track_record': '~20% annualised return over 60 years. Most successful long-term investor in history.',
        'style': 'Buy wonderful companies at fair prices and hold forever. Deep moat focus. Concentrated bets.',
        'notable': 'AmEx, Apple, Coca-Cola, Bank of America are cornerstone positions held for decades.',
    },
    'Bill Ackman': {
        'role': 'Founder & CEO, Pershing Square Capital Management',
        'track_record': '+57% in 2023. Known for bold concentrated bets and activist campaigns.',
        'style': 'Concentrated portfolio (8–10 names). Activist shareholder. Uses public pressure to unlock value.',
        'notable': 'Massive short on US rates in 2023 made $2.2B. Holds Uber, Brookfield, Alphabet.',
    },
    'Michael Burry': {
        'role': 'Founder, Scion Asset Management',
        'track_record': 'Made $800M shorting subprime in 2008 (The Big Short). Erratic but high-conviction calls.',
        'style': 'Deep value, contrarian. Concentrated. Willing to be early and wrong before being right.',
        'notable': 'Top holding is PLTR — a rare growth buy for him. Also shorted S&P 500 in 2023.',
    },
    'Ray Dalio': {
        'role': 'Founder, Bridgewater Associates (world\'s largest hedge fund)',
        'track_record': 'Built $160B AUM. "All Weather" portfolio concept. Macro-driven systematic approach.',
        'style': 'Diversified across asset classes. Macro thesis-driven. Risk parity framework.',
        'notable': 'Heavy ETF and index exposure. NVDA and GOOGL are meaningful individual stock positions.',
    },
    'David Tepper': {
        'role': 'Founder, Appaloosa Management',
        'track_record': '25%+ annualised return over 30 years. One of the best distressed debt and equity investors.',
        'style': 'Distressed situations, macro calls, and high-conviction tech growth.',
        'notable': 'Made billions buying bank stocks in 2009 when everyone was selling. Holds NVDA, AMZN, META.',
    },
    'John Paulson': {
        'role': 'Founder, Paulson & Co.',
        'track_record': 'Made $15B shorting subprime in 2007–2008 — the largest trade in hedge fund history.',
        'style': 'Event-driven. M&A arbitrage. Gold as an inflation hedge. Concentrated special situations.',
        'notable': 'Gold position via GLD was a decade-long core holding.',
    },
    'Dan Loeb': {
        'role': 'Founder & CEO, Third Point LLC',
        'track_record': '15%+ annualised return. Activist investor with strong tech and biotech track record.',
        'style': 'Activist with detailed research letters. Tech, consumer, and healthcare focus.',
        'notable': 'Early Amazon and Alphabet positions. Known for public letters pressuring management.',
    },
    # ATHLETES
    'LeBron James': {
        'role': 'NBA Player · Co-Founder, SpringHill Company · Investor',
        'track_record': 'First active athlete to become a billionaire. Estimated $1B+ investment portfolio.',
        'style': 'Brand-aligned equity stakes. Long-horizon. Media, consumer, and tech.',
        'notable': 'Early Blaze Pizza investor (sold at 10x). Nike lifetime deal worth $1B+. Fenway Sports Group co-owner.',
    },
    'Michael Jordan': {
        'role': 'NBA Legend · Majority Owner (former), Charlotte Hornets · Nike Partner',
        'track_record': 'Jordan Brand generates ~$6B/year in Nike revenue. Sold Hornets for $3B.',
        'style': 'Sports franchises, consumer brands, sports betting.',
        'notable': 'DraftKings investor and brand ambassador. Jordan Brand royalties are a perpetual income stream.',
    },
    'Serena Williams': {
        'role': 'Tennis Legend · Founder, Serena Ventures',
        'track_record': 'Serena Ventures has backed 60+ companies, 80% founded by women or people of colour.',
        'style': 'Early-stage VC. Fintech, health, and consumer. Diversity-lens investing.',
        'notable': 'Early Coinbase, Spotify, and Lyft investor. Portfolio includes 16 unicorns.',
    },
    'Stephen Curry': {
        'role': 'NBA Player · Investor · Media entrepreneur',
        'track_record': 'Active investor across tech, consumer, and media. SC30 Inc. manages his business interests.',
        'style': 'Consumer brands, sports tech, media.',
        'notable': 'DraftKings ambassador and investor. Augusta National Golf Club first Black member.',
    },
    'Kevin Durant': {
        'role': 'NBA Player · Founder, Thirty Five Ventures',
        'track_record': 'One of the most active athlete investors. 70+ portfolio companies.',
        'style': 'Early-stage tech. Media. Sports-adjacent consumer.',
        'notable': 'Early Snap investor (pre-IPO). Airbnb, Robinhood, NVDA via Thirty Five Ventures.',
    },
    'Cristiano Ronaldo': {
        'role': 'Soccer Legend · Global Brand · Hotel and Real Estate Investor',
        'track_record': 'Highest-paid athlete in history. Most followed person on social media (600M+ Instagram).',
        'style': 'Real estate, luxury brands, hotels, and name-equity deals.',
        'notable': 'Pestana CR7 hotel chain. Nike deal runs through 2034. Booking.com brand ambassador.',
    },
    'Tom Brady': {
        'role': 'NFL Legend · Investor · Co-founder, Brady Brand',
        'track_record': 'Estimated $300M net worth. Active investor post-retirement.',
        'style': 'Value investing (Berkshire follower), sports media, and consumer health.',
        'notable': 'FTX was a costly mistake. PENN Entertainment and sports betting exposure post-career.',
    },
}

# ─────────────────────────────────────────────
# SCORING EXPLAINER
# Plain-English logic shown to the user in the detail panel
# ─────────────────────────────────────────────
SCORING_EXPLAINER = {
    'politicians': (
        "MIRROR AI scans the official STOCK Act trade disclosures filed by the top 8 "
        "politicians ranked by portfolio returns. When a politician files a BUY disclosure "
        "for a ticker, it adds weight to that ticker's score — proportional to that politician's "
        "historical return rate (Pelosi at 1.6x, Williams at 1.4x, etc.). "
        "If multiple politicians buy the same stock, the score gets a conviction multiplier "
        "(1.2x for 2 politicians, 1.5x for 3+). Politicians on powerful committees "
        "(Finance, Armed Services, Appropriations) have asymmetric information access — "
        "their trades are the closest thing to a legal insider signal in the US market."
    ),
    'ceos': (
        "MIRROR AI pulls the most recent SEC 13F quarterly filings for 7 of the world's "
        "best fund managers. Each holding is scored by its weight in the portfolio "
        "(position size as % of total holdings), rank position (top holdings score higher), "
        "and the manager's historical return weight. Stocks held by multiple managers "
        "receive a conviction multiplier. 13F data is quarterly — these are positions "
        "held at least 90 days, meaning high-conviction bets rather than short-term trades."
    ),
    'athletes': (
        "MIRROR AI tracks the publicly confirmed equity holdings of 7 elite athlete-investors "
        "based on SEC filings, company registrations, public interviews, and investment announcements. "
        "Athletes with the strongest investment track records (LeBron, Jordan, Serena) carry "
        "higher weight. When multiple athletes hold the same ticker, conviction multipliers apply. "
        "A news scraper checks Sportico and Boardroom for fresh investment mentions each day."
    ),
    'sectors': (
        "MIRROR AI scores the top holdings of 7 flagship sector ETFs (QQQ for AI, ITA for Defence, "
        "XLE for Energy, XLV for Healthcare, IBB for Biotech, XLF for Financials, PAVE for Infrastructure). "
        "Each ETF's top 10 holdings are weighted by their rank position and the sector's growth outlook. "
        "Critically, stocks that appear across multiple sectors get a cross-sector conviction multiplier — "
        "NVDA appearing in AI, Defence, and Biotech simultaneously is a much stronger signal than a "
        "single-sector appearance."
    ),
}

# ─────────────────────────────────────────────
# CONFIDENCE LABELS
# Derived from conviction count and score
# ─────────────────────────────────────────────
def confidence_label(conviction, total, score):
    pct = conviction / total
    if pct >= 0.5 or score > 5:
        return 'HIGH', '#00e87a'
    elif pct >= 0.25 or score > 2:
        return 'MEDIUM', '#f5a623'
    else:
        return 'LOW', '#6e6e90'
