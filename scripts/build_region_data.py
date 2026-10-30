#!/usr/bin/env python3
"""Maintainer tool: rebuild references/region-data/connect-region-data.json and
references/region-readiness-matrix.md from the official AWS sources.

NOT needed at runtime. The Region Readiness mode reads the generated JSON; this
script only regenerates it when AWS updates a source document.

Requires: Python 3.9+, pdfplumber (pip install pdfplumber), network access.

    python3 scripts/build_region_data.py            # fetch live sources, rebuild
    python3 scripts/build_region_data.py --cache /tmp/regsrc   # reuse/keep downloads

Every value in the output is extracted from a cited source. Anything that could
not be parsed is written to `parse_warnings` instead of being guessed - review
those before shipping a refresh.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

DOCS = "https://docs.aws.amazon.com/connect/latest/adminguide/"
SOURCES = {
    "regions": DOCS + "regions.html",
    "telecoms_pdf": "https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf",
    "number_requirements": DOCS + "phone-number-requirements.html",
    "default_outbound": DOCS + "country-code-allow-list.html",
    "gr_replica": DOCS + "create-replica-connect-instance.html",
    "gr_requirements": DOCS + "connect-global-resiliency-requirements.html",
    "low_latency": DOCS + "low-latency-design.html",
    "region_selection": DOCS + "operational-excellence.html",
    "single_vs_multi_instance": DOCS + "single-instance-multiple-instances.html",
    "supported_languages": DOCS + "supported-languages.html",
    "endpoint_test_utility": DOCS + "check-connectivity-tool.html",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JSON = os.path.join(ROOT, "references", "region-data", "connect-region-data.json")
OUT_MD = os.path.join(ROOT, "references", "region-readiness-matrix.md")

REGION_NAMES = {
    "US East (N. Virginia)": "us-east-1",
    "US West (Oregon)": "us-west-2",
    "Africa (Cape Town)": "af-south-1",
    "Asia Pacific (Seoul)": "ap-northeast-2",
    "Asia Pacific (Singapore)": "ap-southeast-1",
    "Asia Pacific (Sydney)": "ap-southeast-2",
    "Asia Pacific (Tokyo)": "ap-northeast-1",
    "Asia Pacific (Osaka)": "ap-northeast-3",
    "Canada (Central)": "ca-central-1",
    "Europe (Frankfurt)": "eu-central-1",
    "EU (Frankfurt)": "eu-central-1",
    "Europe (London)": "eu-west-2",
    "EU (London)": "eu-west-2",
    "AWS GovCloud (US-West)": "us-gov-west-1",
}
# Geography of each Connect home Region (used only by the latency-anchoring
# heuristic, which is labelled as a heuristic in every output).
REGION_GEO = {
    "us-east-1": ("US", "NA"), "us-west-2": ("US", "NA"), "us-gov-west-1": ("US", "NA"),
    "ca-central-1": ("CA", "NA"), "af-south-1": ("ZA", "AF"), "ap-northeast-2": ("KR", "AS"),
    "ap-southeast-1": ("SG", "AS"), "ap-southeast-2": ("AU", "OC"), "ap-northeast-1": ("JP", "AS"),
    "ap-northeast-3": ("JP", "AS"), "eu-central-1": ("DE", "EU"), "eu-west-2": ("GB", "EU"),
}

# Country name (as written in the AWS sources) -> (ISO 3166-1 alpha-2, continent).
# Continent codes: NA North America (incl. Central America & Caribbean), SA South
# America, EU Europe, AF Africa, ME Middle East, AS Asia, OC Oceania.
COUNTRIES = {
    "Albania": ("AL", "EU"), "Algeria": ("DZ", "AF"), "Angola": ("AO", "AF"), "Anguilla": ("AI", "NA"),
    "Antigua and Barbuda": ("AG", "NA"), "Argentina": ("AR", "SA"), "Armenia": ("AM", "AS"),
    "Australia": ("AU", "OC"), "Austria": ("AT", "EU"), "Azerbaijan": ("AZ", "AS"), "Bahamas": ("BS", "NA"),
    "Bahrain": ("BH", "ME"), "Bangladesh": ("BD", "AS"), "Barbados": ("BB", "NA"), "Belarus": ("BY", "EU"),
    "Belgium": ("BE", "EU"), "Belize": ("BZ", "NA"), "Benin": ("BJ", "AF"), "Bermuda": ("BM", "NA"),
    "Bolivia": ("BO", "SA"), "Bonaire": ("BQ", "NA"), "Bosnia and Herzegovina": ("BA", "EU"),
    "Botswana": ("BW", "AF"), "Brazil": ("BR", "SA"), "British Virgin Islands": ("VG", "NA"),
    "Virgin Islands (UK)": ("VG", "NA"), "Brunei": ("BN", "AS"), "Bulgaria": ("BG", "EU"),
    "Burkina Faso": ("BF", "AF"), "Cambodia": ("KH", "AS"), "Cameroon": ("CM", "AF"), "Canada": ("CA", "NA"),
    "Cayman Islands": ("KY", "NA"), "Chile": ("CL", "SA"), "China": ("CN", "AS"), "Colombia": ("CO", "SA"),
    "Costa Rica": ("CR", "NA"), "Croatia": ("HR", "EU"), "Cuba": ("CU", "NA"), "Curaçao": ("CW", "NA"),
    "Cyprus": ("CY", "EU"), "Czech Republic": ("CZ", "EU"), "Denmark": ("DK", "EU"), "Dominica": ("DM", "NA"),
    "Dominican Republic": ("DO", "NA"), "Ecuador": ("EC", "SA"), "Egypt": ("EG", "AF"),
    "El Salvador": ("SV", "NA"), "Estonia": ("EE", "EU"), "Ethiopia": ("ET", "AF"), "Fiji": ("FJ", "OC"),
    "Finland": ("FI", "EU"), "France": ("FR", "EU"), "French Guiana": ("GF", "SA"), "Georgia": ("GE", "AS"),
    "Germany": ("DE", "EU"), "Ghana": ("GH", "AF"), "Greece": ("GR", "EU"), "Grenada": ("GD", "NA"),
    "Guadeloupe": ("GP", "NA"), "Guam": ("GU", "OC"), "Guatemala": ("GT", "NA"), "Honduras": ("HN", "NA"),
    "Hong Kong": ("HK", "AS"), "Hungary": ("HU", "EU"), "Iceland": ("IS", "EU"), "India": ("IN", "AS"),
    "Indonesia": ("ID", "AS"), "Ireland": ("IE", "EU"), "Israel": ("IL", "ME"), "Italy": ("IT", "EU"),
    "Ivory Coast": ("CI", "AF"), "Jamaica": ("JM", "NA"), "Japan": ("JP", "AS"), "Jordan": ("JO", "ME"),
    "Kazakhstan": ("KZ", "AS"), "Kenya": ("KE", "AF"), "Kosovo": ("XK", "EU"), "Kuwait": ("KW", "ME"),
    "Kyrgyzstan": ("KG", "AS"), "Laos": ("LA", "AS"), "Latvia": ("LV", "EU"), "Lebanon": ("LB", "ME"),
    "Lesotho": ("LS", "AF"), "Liechtenstein": ("LI", "EU"), "Lithuania": ("LT", "EU"),
    "Luxembourg": ("LU", "EU"), "Macao": ("MO", "AS"), "Macedonia": ("MK", "EU"), "Malawi": ("MW", "AF"),
    "Malaysia": ("MY", "AS"), "Malta": ("MT", "EU"), "Martinique": ("MQ", "NA"), "Mauritius": ("MU", "AF"),
    "Mayotte": ("YT", "AF"), "Mexico": ("MX", "NA"), "Moldova": ("MD", "EU"), "Monaco": ("MC", "EU"),
    "Mongolia": ("MN", "AS"), "Montenegro": ("ME", "EU"), "Montserrat": ("MS", "NA"), "Morocco": ("MA", "AF"),
    "Mozambique": ("MZ", "AF"), "Myanmar": ("MM", "AS"), "Nepal": ("NP", "AS"), "Netherlands": ("NL", "EU"),
    "New Zealand": ("NZ", "OC"), "Nicaragua": ("NI", "NA"), "Nigeria": ("NG", "AF"),
    "Northern Mariana": ("MP", "OC"), "Norway": ("NO", "EU"), "Oman": ("OM", "ME"), "Pakistan": ("PK", "AS"),
    "Panama": ("PA", "NA"), "Papua New Guinea": ("PG", "OC"), "Paraguay": ("PY", "SA"), "Peru": ("PE", "SA"),
    "Philippines": ("PH", "AS"), "Poland": ("PL", "EU"), "Portugal": ("PT", "EU"), "Puerto Rico": ("PR", "NA"),
    "Qatar": ("QA", "ME"), "Reunion": ("RE", "AF"), "Romania": ("RO", "EU"), "Russia": ("RU", "EU"),
    "Rwanda": ("RW", "AF"), "Saba": ("BQ", "NA"), "Saint Kitts and Nevis": ("KN", "NA"),
    "Saint Lucia": ("LC", "NA"), "Saint Martin": ("MF", "NA"), "Saint Pierre and Miquelon": ("PM", "NA"),
    "Saint Vincent Grenadines": ("VC", "NA"), "Saudi Arabia": ("SA", "ME"), "Serbia": ("RS", "EU"),
    "Seychelles": ("SC", "AF"), "Sierra Leone": ("SL", "AF"), "Singapore": ("SG", "AS"),
    "Sint Eustatius": ("BQ", "NA"), "Sint Maarten": ("SX", "NA"), "Slovakia": ("SK", "EU"),
    "Slovenia": ("SI", "EU"), "South Africa": ("ZA", "AF"), "South Korea": ("KR", "AS"), "Spain": ("ES", "EU"),
    "Sri Lanka": ("LK", "AS"), "Sudan": ("SD", "AF"), "Sweden": ("SE", "EU"), "Switzerland": ("CH", "EU"),
    "Taiwan": ("TW", "AS"), "Tanzania": ("TZ", "AF"), "Thailand": ("TH", "AS"),
    "Trinidad and Tobago": ("TT", "NA"), "Tunisia": ("TN", "AF"), "Turkey": ("TR", "EU"),
    "Turks and Caicos": ("TC", "NA"), "Uganda": ("UG", "AF"), "Ukraine": ("UA", "EU"),
    "United Arab Emirates": ("AE", "ME"), "United Kingdom": ("GB", "EU"), "United States": ("US", "NA"),
    "Uruguay": ("UY", "SA"), "Uzbekistan": ("UZ", "AS"), "Venezuela": ("VE", "SA"), "Vietnam": ("VN", "AS"),
    "Virgin Islands (US)": ("VI", "NA"), "Zambia": ("ZM", "AF"), "Zimbabwe": ("ZW", "AF"),
}
COUNTRY_ALIASES = {"Korea": "South Korea", "UK": "United Kingdom", "US": "United States",
                   "Hongkong": "Hong Kong", "HongKong": "Hong Kong", "Venezuelan": "Venezuela"}

# Regions-page section id -> feature key used by the readiness script.
FEATURE_SECTIONS = {
    "amazonconnect_region": ("connect", "Amazon Connect (instance / core voice, chat)"),
    "agentworkspace_region": ("agent_workspace", "Agent workspace and step-by-step guides"),
    "agentworkspace_3p_region": ("agent_workspace_3p_apps", "Agent workspace third-party applications"),
    "q-connect_region": ("agent_assist", "Agent assist (Amazon Q in Connect / AI agents)"),
    "analytics_datalake_region": ("data_lake", "Analytics data lake"),
    "appintegrations_region": ("app_integrations", "AppIntegrations"),
    "cases_region": ("cases", "Cases"),
    "messaging-integrations_region": ("messaging", "Messaging integrations"),
    "chatwidget_region": ("communications_widget", "Communications widget"),
    "contactlens_region": ("conversational_analytics", "Conversational analytics (Contact Lens)"),
    "customerauthentication_region": ("customer_authentication", "Customer authentication"),
    "customerprofiles_region": ("customer_profiles", "Customer Profiles"),
    "customerprofiles_calculatedattributesregion": ("customer_profiles_calculated_attributes",
                                                    "Customer Profiles calculated attributes API"),
    "externaltool_region": ("external_tool", "External Tool"),
    "optimization_region": ("forecasting_scheduling", "Forecasting & agent scheduling"),
    "gv_region": ("agentic_voice", "Amazon Connect agentic voice"),
    "agentic-cx_region": ("agentic_cx_designer", "Agentic CX Designer"),
    "gr_region": ("global_resiliency", "Global Resiliency (ACGR)"),
    "inapp_region": ("inapp_web_video_calling", "In-app, web, and video calling"),
    "livemediastreaming_region": ("live_media_streaming", "Live media streaming"),
    "campaigns_region": ("outbound_campaigns", "Outbound campaigns"),
    "tasks_region": ("tasks", "Tasks"),
    "voiceid_region": ("voice_id", "Voice ID"),
}
FEATURE_ALIASES = {
    "contact lens": "conversational_analytics", "contact_lens": "conversational_analytics",
    "q in connect": "agent_assist", "amazon q in connect": "agent_assist", "q_in_connect": "agent_assist",
    "ai agents": "agent_assist", "wisdom": "agent_assist", "wfm": "forecasting_scheduling",
    "forecasting": "forecasting_scheduling", "scheduling": "forecasting_scheduling",
    "acgr": "global_resiliency", "global resiliency": "global_resiliency", "dr": "global_resiliency",
    "campaigns": "outbound_campaigns", "outbound campaigns": "outbound_campaigns",
    "sms": "messaging.sms", "whatsapp": "messaging.whatsapp_business_messaging",
    "apple messages": "messaging.apple_messages_for_business",
    "push": "messaging.push_notifications", "profiles": "customer_profiles",
    "webrtc": "inapp_web_video_calling", "video": "inapp_web_video_calling",
    "kvs": "live_media_streaming", "media streaming": "live_media_streaming",
    "step-by-step guides": "agent_workspace", "screen recording": "conversational_analytics.screen_recording",
    "evaluations": "conversational_analytics.performance_evaluations",
}

WARN = []


def warn(msg):
    WARN.append(msg)
    print("WARN:", msg, file=sys.stderr)


def fetch(key, url, cache):
    ext = ".pdf" if url.endswith(".pdf") else ".html"
    path = os.path.join(cache, key + ext) if cache else None
    if path and os.path.exists(path):
        return open(path, "rb").read()
    req = urllib.request.Request(url, headers={"User-Agent": "connect-region-readiness-builder"})
    data = urllib.request.urlopen(req, timeout=60).read()
    if path:
        open(path, "wb").write(data)
    return data


def clean(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x))).strip()


def slug(x):
    return re.sub(r"[^a-z0-9]+", "_", x.lower()).strip("_")


def region_code(name):
    n = re.sub(r"\s+", " ", name).strip()
    n = re.sub(r"\s*Region\b.*$", "", n).strip()
    n = re.sub(r"\s+-\s+.*$", "", n).strip()
    return REGION_NAMES.get(n)


def names_in(text):
    """Region codes for every Region display name that appears in `text`."""
    return sorted({code for name, code in REGION_NAMES.items() if name in text})


def country_key(name):
    n = re.sub(r"\s+", " ", name).strip()
    n = COUNTRY_ALIASES.get(n, n)
    if n in COUNTRIES:
        return n
    return None


class TableParser(HTMLParser):
    """Collects every <table> as a list of rows of {'t','rs','cs'} cells."""

    def __init__(self):
        super().__init__()
        self.tables, self.stack, self.cell, self.row = [], [], None, None

    def handle_starttag(self, t, a):
        a = dict(a)
        if t == "table":
            self.stack.append([])
        elif t == "tr" and self.stack:
            self.row = []
        elif t in ("td", "th") and self.row is not None:
            self.cell = {"t": "", "rs": int(a.get("rowspan", 1)), "cs": int(a.get("colspan", 1))}
        elif t in ("br", "p", "li", "div") and self.cell is not None:
            self.cell["t"] += " ; "

    def handle_endtag(self, t):
        if t in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(self.cell)
            self.cell = None
        elif t == "tr" and self.row is not None and self.stack:
            self.stack[-1].append(self.row)
            self.row = None
        elif t == "table" and self.stack:
            self.tables.append(self.stack.pop())

    def handle_data(self, d):
        if self.cell is not None:
            self.cell["t"] += d


def grid(rows):
    """Expand rowspan/colspan into a rectangular list-of-lists of strings."""
    out, pending = [], {}
    for r in rows:
        line, ci, k = [], 0, 0
        while k < len(r) or ci in pending:
            if ci in pending:
                txt, n = pending[ci]
                line.append(txt)
                if n > 1:
                    pending[ci] = (txt, n - 1)
                else:
                    del pending[ci]
                ci += 1
                continue
            c = r[k]
            k += 1
            txt = re.sub(r"(\s*;\s*)+", "; ", re.sub(r"\s+", " ", html.unescape(c["t"]))).strip("; ").strip()
            for _ in range(c["cs"]):
                line.append(txt)
                if c["rs"] > 1:
                    pending[ci] = (txt, c["rs"] - 1)
                ci += 1
        out.append(line)
    return out


def tables_in(fragment):
    p = TableParser()
    p.feed(fragment)
    return [grid(t) for t in p.tables]


def main_body(raw):
    s = raw.decode("utf-8", "replace")
    i = s.find('id="main-col-body"')
    j = s.find('id="main-col-footer"')
    return s[i:j if j > i else None]


def split_sections(body, tag="h2"):
    parts = re.split(r"<%s([^>]*)>(.*?)</%s>" % (tag, tag), body, flags=re.S)
    out = []
    for i in range(1, len(parts), 3):
        m = re.search(r'id="([^"]*)"', parts[i])
        out.append((m.group(1) if m else "", clean(parts[i + 1]), parts[i + 2]))
    return out


# ---------------------------------------------------------------- regions page
def parse_regions(raw):
    body = main_body(raw)
    features, fips, campaign_dest, notes = {}, {}, {}, {}
    for sid, title, frag in split_sections(body):
        if sid not in FEATURE_SECTIONS:
            if sid:
                warn("regions page: unmapped section %r (%s) - add it to FEATURE_SECTIONS" % (sid, title))
            continue
        key, label = FEATURE_SECTIONS[sid]
        regions, subs = [], {}
        tabs = tables_in(frag)
        for t in tabs:
            hdr = t[0]
            if hdr and hdr[0] == "" and len(hdr) > 1:
                hdr = hdr[1:]
                t = [r[1:] if len(r) > len(hdr) else r for r in t]
            if "Region" in hdr and "Endpoint" in hdr:  # endpoint table
                for r in t[1:]:
                    code = r[hdr.index("Region")].strip()
                    regions.append(code)
                    if "fips" in r[hdr.index("Endpoint")]:
                        fips.setdefault(key, []).append(code)
            elif hdr and hdr[0] == "Region Name":  # feature matrix
                cols = hdr[1:]
                for r in t[1:]:
                    code = region_code(r[0])
                    if not code:
                        warn("regions page %s: unknown region %r" % (sid, r[0]))
                        continue
                    for c, v in zip(cols, r[1:]):
                        sk = slug(c)
                        v = v.strip()
                        subs.setdefault(sk, {"label": c, "regions": {}})
                        subs[sk]["regions"][code] = v
            else:
                warn("regions page %s: unrecognised table header %r" % (sid, hdr))
        nontable = re.sub(r"<table.*?</table>", " ", frag, flags=re.S)
        for li in re.findall(r"<li[^>]*>(.*?)</li>", nontable, re.S):
            txt = clean(li)
            code = region_code(txt)
            if code:
                regions.append(code)
                if "replicas only" in txt:
                    notes.setdefault(key, []).append(txt)
            m = re.match(r"From instances created in (.+?) you can call (?:all )?phone numbers (?:that are )?based in (?:the )?(.+?)\.(?:\s|$)", txt)
            if m:
                srcs = [region_code(x) for x in re.split(r"\s+or\s+", m.group(1))]
                dests = [d.strip() for d in re.split(r",\s*|\s+and\s+", m.group(2)) if d.strip()]
                dests = [re.sub(r"^and\s+", "", d) for d in dests]
                for s_ in srcs:
                    if not s_:
                        warn("campaign destinations: unknown region in %r" % txt)
                        continue
                    for d in dests:
                        ck = country_key(d)
                        if not ck:
                            warn("campaign destinations: unknown country %r" % d)
                            continue
                        campaign_dest.setdefault(s_, []).append(COUNTRIES[ck][0])
                if "restrictions" in txt:
                    notes.setdefault("outbound_campaigns", []).append(txt)
            elif txt.startswith("No other combinations"):
                notes.setdefault("outbound_campaigns", []).append(txt)
        # contact-lens sub-feature table lives under an <h3> inside the section
        features[key] = {"label": label, "regions": sorted(set(regions)), "section_url": SOURCES["regions"] + "#" + sid}
        for sk, sv in subs.items():
            features[key + "." + sk] = {
                "label": label + " - " + sv["label"],
                "regions": sorted(c for c, v in sv["regions"].items() if v and v != "-" and v.lower() != "no"),
                "values": sv["regions"],
                "section_url": SOURCES["regions"] + "#" + sid,
            }
        if subs and not regions:  # parent of a matrix-only section = union of its sub-features
            features[key]["regions"] = sorted({r for k2, f2 in features.items() if k2.startswith(key + ".") for r in f2["regions"]})
        if not regions and not subs:
            warn("regions page %s: no regions parsed" % sid)
    for k in notes:
        if k in features:
            features[k]["notes"] = notes[k]
    features["voice_id"]["deprecated"] = {
        "quote": "End of support notice: On May 20, 2026, AWS will end support for Amazon Connect Customer Voice ID.",
        "source": DOCS + "voice-id.html"}
    if "Yes*" in json.dumps(features):
        warn("regions page: some cells are 'Yes*' but the page publishes no footnote for '*' - kept verbatim in `values`")
    return features, fips, {k: sorted(set(v)) for k, v in campaign_dest.items()}, notes.get("outbound_campaigns", [])


# ------------------------------------------------------- Global Resiliency pairs
def parse_gr(raw):
    t = clean(main_body(raw))
    pairs = []
    for m in re.finditer(r"You can only create a replica in (?:the )?(.+?) Region if your source is (.+?)(?:, or the other way around)?\.", t):
        a, b = region_code(m.group(1)), region_code(m.group(2))
        both = "other way around" in m.group(0)
        if not (a and b):
            warn("GR pair unparsed: %r" % m.group(0))
            continue
        pairs.append({"source": b, "replica": a, "bidirectional": both, "quote": m.group(0)})
    m = re.search(r"Global Resiliency is available only for .*? created in the following AWS Regions: (.+?)\.\s+You can only", t)
    avail = names_in(m.group(1)) if m else []
    if not pairs or not m:
        warn("GR: could not parse replica pairs / availability sentence")
    return {"pairs": pairs, "available_regions": [a for a in avail if a],
            "availability_quote": m.group(0) if m else None}


def parse_gr_requirements(raw):
    body = main_body(raw)
    items = [clean(li) for li in re.findall(r"<li[^>]*>(.*?)</li>", body, re.S)]
    return [i for i in items if i][:12]


# ------------------------------------------------- default outbound allow-list
def parse_default_outbound(raw):
    body = main_body(raw)
    out = {}
    for sid, title, frag in split_sections(body, "h2"):
        m = re.match(r"Instances created in (.+)$", title)
        if not m:
            continue
        names = re.split(r",\s*|\s+and\s+", m.group(1))
        codes = []
        for n in names:
            n = n.strip()
            if n in ("US East", "US West"):
                codes.append({"US East": "us-east-1", "US West": "us-west-2"}[n])
            else:
                c = region_code(n) or region_code(n.replace("EU (", "Europe ("))
                if c:
                    codes.append(c)
                else:
                    warn("default outbound: unknown region %r" % n)
        countries = []
        for li in re.findall(r"<li[^>]*>(.*?)</li>", frag, re.S):
            ck = country_key(clean(li))
            if ck:
                countries.append(COUNTRIES[ck][0])
            else:
                warn("default outbound: unknown country %r" % clean(li))
        for c in codes:
            out[c] = countries
    t = clean(body)
    prefix_notes = [s.strip() for s in re.findall(r"((?:UK|Japan) mobile numbers with the following prefix(?:es)? might not be allowed by default: [^.]*?)(?= If| UK| Japan|$)", t)]
    return out, prefix_notes


# ------------------------------------------------------- phone number requirements
TYPE_PATTERNS = [
    ("TOLL_FREE", r"toll[- ]?free|freephone"),
    ("UIFN", r"\buifn\b"),
    ("SHARED", r"shared[- ]cost"),
    ("DID_MOBILE", r"mobile"),
    ("DID", r"local|geographic|national|landline|voip|representative|\bdid\b"),
]


def number_type_of(txt):
    t = txt.lower()
    for k, p in TYPE_PATTERNS:
        if re.search(p, t):
            return k
    return None


def parse_number_requirements(raw):
    body = main_body(raw)
    intro = clean(body[:4000])
    m = re.search(r"All AWS Regions are supported\W+except (.+?\))\W*unless noted otherwise", intro)
    default_excl = names_in(m.group(1)) if m else []
    if not m:
        warn("number requirements: default region exclusion sentence not found")
    res = {}
    for sid, title, frag in split_sections(body):
        mm = re.match(r"(.+?) \(([A-Z]{2})\)$", title)
        if not mm:
            continue
        name, iso = mm.group(1), mm.group(2)
        entry = {"name": name, "iso2": iso, "order": [], "porting": [], "notes": []}
        for t in tables_in(frag):
            hdr = [h.lower() for h in t[0]]
            is_port = any("portab" in h for h in hdr)
            for r in t[1:]:
                row = dict(zip(hdr, r))
                rec = {}
                sr = next((row[h] for h in hdr if "supported region" in h), None)
                if sr is not None:
                    rec["supported_regions_text"] = sr
                    rec["supported_regions"] = sorted({c for c in (region_code(x) for x in re.split(r";\s*", sr)) if c})
                    if re.match(r"^\s*all\b", sr, re.I):
                        rec["supported_regions"] = "ALL"
                tn = next((row[h] for h in hdr if h.startswith("type of number")), None)
                if tn is None and is_port and sr:
                    tn = sr  # e.g. "All for Toll-free prefixes: ..."
                rec["number_text"] = tn or ""
                rec["type"] = number_type_of(tn or "") if tn else None
                al = next((row[h] for h in hdr if "agent location" in h), None)
                if al and al.upper() != "N/A":
                    rec["agent_location"] = al
                idr = next((row[h] for h in hdr if "id requirements" in h), None)
                if idr is not None:
                    rec["id_required"] = idr
                    ident = next((row[h] for h in hdr if "identification" in h), "")
                    rec["identification"] = ident[:600]
                if is_port:
                    rec["window"] = next((row[h] for h in hdr if "window" in h), "")
                (entry["porting"] if is_port else entry["order"]).append(rec)
        text = clean(re.sub(r"<table.*?</table>", " ", frag, flags=re.S))
        if re.search(r"porting is not supported|number portability\s+not supported", text, re.I) and not entry["porting"]:
            entry["porting_supported"] = False
        for sent in re.split(r"(?<=\.)\s+", text):
            if re.search(r"agent|physically|must be located|takes longer|not supported for|only|preview|partner", sent, re.I) \
                    and "UIFN numbers, supports standard" not in sent and len(sent) < 500:
                entry["notes"].append(re.sub(r"^For ordering phone numbers\s+", "", sent.strip()))
        res[iso] = entry
    return {"default_excluded_regions": [d for d in default_excl if d],
            "default_rule_quote": m.group(0) if m else None, "countries": res}


# --------------------------------------------------------------- telecoms PDF
PDF_COLS = ["country", "service_type", "number_availability", "national_outbound", "international_outbound",
            "porting", "multi_carrier", "custom_caller_id", "region_availability", "campaign_regions", "status"]
TICK_COLS = PDF_COLS[2:8]
GREEN, YELLOW = (0, 0.69, 0.314), (1, 0.753, 0)


def parse_pdf(path):
    import pdfplumber
    pdf = pdfplumber.open(path)
    first = (pdf.pages[0].extract_text() or "")
    lu = re.search(r"Last updated (.+)", first)
    rows, notes, legend = [], [], ""
    seen = set()
    for pi, p in enumerate(pdf.pages):
        txt = p.extract_text() or ""
        if pi == 1:
            legend = txt
        for t in p.find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"}):
            texts = t.extract()
            for r, tr in zip(t.rows, texts):
                key = (pi, round(r.bbox[1], 1))
                if key in seen:
                    continue  # overlapping table detections on the same page
                seen.add(key)
                cells = []
                for bb, val in zip(r.cells, tr):
                    if bb is None or val is None:
                        cells.append(None)
                        continue
                    x0, top, x1, bot = bb
                    cols = [c["non_stroking_color"] for c in p.chars if c["text"] == "✔"
                            and x0 <= (c["x0"] + c["x1"]) / 2 <= x1 and top <= (c["top"] + c["bottom"]) / 2 <= bot]
                    val = val.strip()
                    if cols:
                        c = tuple(round(x, 3) for x in cols[0])
                        val = val.replace("✔", "Y_green" if c == GREEN else "Y_yellow" if c == YELLOW else "Y_other", 1)
                    cells.append(val)
                if cells and cells[0] == "Country":
                    continue
                rows.append((pi + 1, cells))
        for line in txt.splitlines():
            mm = re.match(r"\s*\((\d+)\)\s*-\s*(.+)", line)
            if mm:
                notes.append({"page": pi + 1, "marker": mm.group(1), "text": mm.group(2).strip()})
    glyphs = {"yes": 0, "conditional": 0, "no": 0}
    for p in pdf.pages:
        for c in p.chars:
            col = tuple(round(x, 3) for x in (c["non_stroking_color"] or ()))
            if c["text"] == "✔":
                glyphs["yes" if col == GREEN else "conditional" if col == YELLOW else "other"] = \
                    glyphs.get("yes" if col == GREEN else "conditional" if col == YELLOW else "other", 0) + 1
            elif c["text"] == "X" and "Bold" in c["fontname"] and col == (1, 0, 0):
                glyphs["no"] += 1
    hist = []
    full = "\n".join((p.extract_text() or "") for p in pdf.pages[-2:])
    if "Document versions" in full:
        hist = [l for l in full.split("Document versions", 1)[1].splitlines() if l.strip()][1:]
    return rows, notes, (lu.group(1).strip() if lu else None), hist, legend, glyphs


def tick(v):
    if v is None:
        return None
    v = v.strip()
    m = re.match(r"^Y_(green|yellow|other)\s*\(?(\d)?\)?$", v)
    if m:
        return {"value": "yes" if m.group(1) == "green" else "conditional", "footnote": m.group(2)}
    if v == "X":
        return {"value": "no"}
    return None


def regions_field(v):
    if v is None:
        return None
    v = re.sub(r"-\s*\n\s*", "-", v).replace("\n", " ").strip()
    if v in ("", "-"):
        return []
    if v == "All commercial regions":
        return "ALL_COMMERCIAL"
    if v == "All regions":
        return "ALL"
    codes = [c.strip() for c in v.split(",")]
    for c in codes:
        if not re.match(r"^[a-z]{2}(-gov)?-[a-z]+-\d$", c):
            warn("PDF: unrecognised region value %r" % v)
            return v
    return codes


# Rows whose merged cells pdfplumber cannot split (verified manually against the
# rendered PDF, page 3, Belgium: DID all green; Toll-free National Outbound is the
# one yellow tick on that page). Re-check after every refresh - the build warns
# if the yellow-tick total in the PDF differs from the parsed total.
PDF_OVERRIDES = {
    ("Belgium", "DID"): ["Y_green"] * 6,
    ("Belgium", "Toll-free"): ["Y_green", "Y_yellow", "X", "Y_green", "Y_green", "X"],
}


def build_telecoms(rows, notes):
    out, cur = [], {}
    for page, c in rows:
        c = list(c) + [None] * (11 - len(c))
        if c[0]:
            name = re.sub(r"\s+", " ", c[0]).strip()
            cur = {"country": name, "region_availability": None, "campaign_regions": None, "status": None}
        if not cur:
            continue
        st = (c[1] or "").replace("\n", " ").strip()
        if not st:
            continue
        ov = PDF_OVERRIDES.get((cur["country"], st))
        if ov:
            c[2:8] = ov
        elif any(x is not None and "\n" in x for x in c[2:8]):
            warn("PDF: merged tick cells for %s/%s - add a PDF_OVERRIDES entry" % (cur["country"], st))
        if c[8] is not None:
            cur["region_availability"] = regions_field(c[8])
        if c[9] is not None:
            cur["campaign_regions"] = regions_field(c[9])
        if c[10] is not None and c[10].strip():
            cur["status"] = c[10].replace("\n", " ").strip()
        ck = country_key(cur["country"])
        if not ck:
            warn("PDF: unknown country %r - add to COUNTRIES" % cur["country"])
            continue
        rec = {"country": ck, "iso2": COUNTRIES[ck][0], "service_type": st, "page": page,
               "region_availability": cur["region_availability"], "campaign_regions": cur["campaign_regions"],
               "status": cur["status"]}
        for col, v in zip(TICK_COLS, c[2:8]):
            tv = tick(v)
            if tv is None:
                warn("PDF: unparsed tick %r for %s/%s/%s" % (v, ck, st, col))
            rec[col] = tv
        out.append(rec)
    # attach footnotes: a footnote belongs to the country its text names
    for n in notes:
        for rec in out:
            words = [rec["country"]] + [a for a, b in COUNTRY_ALIASES.items() if b == rec["country"]]
            if any(re.search(r"\b%s" % re.escape(w), n["text"]) for w in words):
                rec.setdefault("footnotes", [])
                if n["text"] not in rec["footnotes"]:
                    rec["footnotes"].append(n["text"])
    return out


# ------------------------------------------------------------ curated quotes
def curated(cache):
    """Facts that live in prose. Each is a verbatim quote plus its URL so the
    readiness report can cite it. The build verifies each quote still exists."""
    items = [
        ("region_selection", "region_selection",
         "Region selection is contingent upon data governance requirements, use case, services available in each Region, telephony costs in each Region, and latency in relation to your agents, contacts, and external transfer endpoint geography."),
        ("agent_isolation", "single_vs_multi_instance",
         "Isolation is required for agents in India, South Korea, and South Africa."),
        ("single_instance_default", "single_vs_multi_instance",
         "pair) in the absence of compelling requirements requiring multiple Regions."),
        ("latency_anchor", "low_latency",
         "Anchor either your phone numbers or agents in the same AWS Region where they are geographically located."),
        ("latency_500", "low_latency",
         "If both your phone numbers and agents are located in an AWS Region that is different from the one where your Connect Customer instance is created, call latency is extended above 500ms for network latency (WebRTC RTT)."),
        ("latency_900", "low_latency",
         "When call latency is greater than 900ms for both network and telephony latency, it leads to a significant delay between agents and customers."),
        ("latency_test", "low_latency",
         "Use the Connect Customer Endpoint Test Utility to check latency."),
        ("cross_region_numbers", "low_latency",
         "As of July 2023 we have simplified requirements to claim phone numbers that are located in countries outside of the AWS Region where your Connect Customer instance is located."),
        ("porting_lead_time", "region_selection",
         "Open a porting request as far in advance of your pending go-live date as possible."),
        ("lang_ai_regions", "supported_languages",
         "Not available in instances in the Africa (Cape Town) AWS Region and AWS GovCloud (US-West)."),
        ("lang_auto_eval_regions", "supported_languages",
         "Automated performance evaluations filled using generative AI is not available in instances in the following AWS Regions: Africa (Cape Town), Asia Pacific (Mumbai), Asia Pacific (Seoul) and AWS GovCloud (US-West)."),
        ("outbound_default_deny", "default_outbound",
         "Connect Customer country allowlisting supports a default deny model; unless you have specifically been allowed to call countries you will be blocked when attempting to call."),
    ]
    out = {}
    for key, src, quote in items:
        raw = fetch(src, SOURCES[src], cache)
        text = clean(main_body(raw))
        found = quote in text
        if not found:
            warn("curated quote %r no longer found verbatim in %s - re-check the page" % (key, SOURCES[src]))
        out[key] = {"quote": quote, "source": SOURCES[src], "verified_verbatim": found}
    return out


# ------------------------------------------------------------------ markdown
def write_markdown(d):
    homes = d["home_regions"]
    L = []
    A = L.append
    A("# Amazon Connect Region Readiness Matrix")
    A("")
    A("> **Generated file — do not edit by hand.** Regenerate with `python3 scripts/build_region_data.py`.")
    A("> Snapshot built %s. Telecoms Coverage Guide \"Last updated\": %s." % (d["generated"], d["sources"]["telecoms_pdf"]["last_updated"]))
    A("> This is a point-in-time copy of the AWS sources listed at the end. AWS changes them without notice —")
    A("> re-check the live pages before committing to a Region.")
    A("")
    A("Legend: ✅ available · ❌ not listed for that Region · `Yes*` = as printed on the AWS page (no footnote published).")
    A("")
    A("## 1. Amazon Connect home Regions")
    A("")
    A("| Region | Code | FIPS endpoint | Global Resiliency partner |")
    A("|---|---|---|---|")
    partner = {}
    for p in d["global_resiliency"]["pairs"]:
        partner.setdefault(p["source"], []).append(p["replica"])
        if p["bidirectional"]:
            partner.setdefault(p["replica"], []).append(p["source"])
    names = {v: k for k, v in REGION_NAMES.items() if not k.startswith("EU (")}
    for r in homes:
        A("| %s | `%s` | %s | %s |" % (names.get(r, r), r, "✅" if r in d["fips_regions"].get("connect", []) else "—",
                                      ", ".join("`%s`" % x for x in partner.get(r, [])) or "—"))
    A("")
    A("`ap-northeast-3` (Osaka) is a Global Resiliency **replica-only** Region — not a home Region.")
    A("")
    A("## 2. Feature availability by Region")
    A("")
    A("| Feature (key) | " + " | ".join("`%s`" % r for r in homes) + " |")
    A("|---|" + "---|" * len(homes))
    for k, f in sorted(d["features"].items()):
        if "." in k or k == "connect":
            continue
        A("| %s (`%s`) | " % (f["label"], k) + " | ".join("✅" if r in f["regions"] else "❌" for r in homes) + " |")
    A("")
    for parent in ("messaging", "conversational_analytics"):
        subs = sorted(k for k in d["features"] if k.startswith(parent + "."))
        if not subs:
            continue
        A("### %s — sub-features" % d["features"][parent]["label"])
        A("")
        A("| Sub-feature (key) | " + " | ".join("`%s`" % r for r in homes) + " |")
        A("|---|" + "---|" * len(homes))
        for k in subs:
            vals = d["features"][k].get("values", {})
            cells = []
            for r in homes:
                v = vals.get(r, "")
                cells.append("✅" if v in ("Yes",) else "❌" if v in ("", "-", "No") else v)
            A("| %s (`%s`) | " % (d["features"][k]["label"].split(" - ", 1)[-1], k) + " | ".join(cells) + " |")
        A("")
    A("## 3. Outbound campaigns — callable destinations by home Region")
    A("")
    A('> **Where the two columns differ for a home Region (marked ⚠️ `REG-011`), the AWS sources disagree: report both destination lists and flag `REG-011` — do not pick one. Tell the customer to confirm with AWS before committing. `REG-011` is in addition to, never instead of, the finding for the destination itself — an unsupported destination (e.g. Europe (London) → US) is always `REG-007`.**')
    A("")
    A("| Home Region | Destination countries (regions page) | Destination countries (Telecoms guide `Outbound Campaign Regions` column) |")
    A("|---|---|---|")
    pdf_c = {}
    for t in d["telecoms"]:
        if isinstance(t["campaign_regions"], list):
            for r in t["campaign_regions"]:
                pdf_c.setdefault(r, set()).add(t["iso2"])
    for r in homes:
        _page = ", ".join(d["campaign_destinations"].get(r, [])) or "—"
        _pdf = ", ".join(sorted(pdf_c.get(r, []))) or "—"
        _flag = " ⚠️ `REG-011`" if set(d["campaign_destinations"].get(r, [])) != set(pdf_c.get(r, [])) else ""
        A("| `%s`%s | %s | %s |" % (r, _flag, _page, _pdf))
    A("")
    for n in d.get("campaign_notes", []):
        A("- " + n)
    A("")
    A("## 4. Countries callable by default (outbound allow-list)")
    A("")
    A("| Home Region | Default countries |")
    A("|---|---|")
    for r in homes:
        A("| `%s` | %s |" % (r, ", ".join(d["default_outbound"].get(r, [])) or "—"))
    A("")
    for n in d.get("default_outbound_prefix_notes", []):
        A("- " + n)
    A("")
    A("## 5. Phone numbers by country (Telecoms Coverage Guide)")
    A("")
    A("Ticks: ✅ supported · 🟡 conditional (yellow tick in the PDF) · ❌ not supported. Region: where the number can be claimed/managed.")
    A("")
    A("| Country | Type | Avail | Nat OB | Intl OB | Port | Multi-carrier | Custom CLI | Claimable in | Campaign Regions | Status |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    sym = {"yes": "✅", "conditional": "🟡", "no": "❌", None: "?"}
    for t in d["telecoms"]:
        ra = t["region_availability"]
        ra = {"ALL_COMMERCIAL": "All commercial", "ALL": "All regions"}.get(ra, ra) if not isinstance(ra, list) else ", ".join(ra)
        cr = t["campaign_regions"]
        cr = ", ".join(cr) if isinstance(cr, list) and cr else "—"
        ticks = [sym[(t[c] or {}).get("value")] + ("(%s)" % t[c]["footnote"] if t[c] and t[c].get("footnote") else "") for c in TICK_COLS]
        A("| %s (%s) | %s | %s | %s | %s | %s |" % (t["country"], t["iso2"], t["service_type"], " | ".join(ticks), ra, cr, t["status"]))
    A("")
    A("Footnotes from the guide:")
    A("")
    for n in d["telecoms_footnotes"]:
        A("- (%s) %s" % (n["marker"], n["text"]))
    A("")
    A("## 6. Countries with Region-restricted ordering or agent-location rules (phone-number requirements page)")
    A("")
    A("Default rule: \"%s\"" % d["number_requirements"]["default_rule_quote"])
    A("")
    A("| Country | Number | Supported Regions | Agent location |")
    A("|---|---|---|---|")
    for iso, c in sorted(d["number_requirements"]["countries"].items()):
        for o in c["order"]:
            sr = o.get("supported_regions")
            if sr is None and not o.get("agent_location"):
                continue
            A("| %s (%s) | %s | %s | %s |" % (c["name"], iso, o["number_text"][:60],
                                             "All" if sr == "ALL" else ", ".join(sr or []) or "default rule",
                                             o.get("agent_location", "—")))
    A("")
    A("## Sources")
    A("")
    for k, s in d["sources"].items():
        A("- `%s` — %s (retrieved %s)" % (k, s["url"], s["retrieved"]))
    A("")
    open(OUT_MD, "w").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", help="directory to store/reuse downloaded sources")
    a = ap.parse_args()
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)
    today = dt.date.today().isoformat()
    raw = {k: fetch(k, u, a.cache) for k, u in SOURCES.items() if k != "telecoms_pdf"}
    pdf_path = os.path.join(a.cache or "/tmp", "telecoms_pdf.pdf")
    if not (a.cache and os.path.exists(pdf_path)):
        open(pdf_path, "wb").write(fetch("telecoms_pdf", SOURCES["telecoms_pdf"], None))

    features, fips, campaign_dest, campaign_notes = parse_regions(raw["regions"])
    gr = parse_gr(raw["gr_replica"])
    gr["requirements"] = parse_gr_requirements(raw["gr_requirements"])
    default_outbound, prefix_notes = parse_default_outbound(raw["default_outbound"])
    numreq = parse_number_requirements(raw["number_requirements"])
    rows, notes, last_updated, history, legend, glyphs = parse_pdf(pdf_path)
    telecoms = build_telecoms(rows, notes)
    # Integrity check: every tick/cross glyph in the PDF must land in exactly one parsed cell.
    for val, n in glyphs.items():
        parsed = sum(1 for t in telecoms for c in TICK_COLS if (t[c] or {}).get("value") == val)
        if parsed != n:
            warn("PDF: %d '%s' glyphs in the document but %d parsed - a merged cell needs a PDF_OVERRIDES entry"
                 % (n, val, parsed))

    home = features["connect"]["regions"]
    data = {
        "schema_version": 1,
        "generated": today,
        "home_regions": home,
        "commercial_regions": [r for r in home if "-gov-" not in r],
        "region_geo": {r: {"country": REGION_GEO[r][0], "continent": REGION_GEO[r][1]} for r in REGION_GEO},
        "region_names": {v: k for k, v in REGION_NAMES.items() if not k.startswith("EU (")},
        "features": features,
        "feature_aliases": FEATURE_ALIASES,
        "unlisted_features": {
            "email": "The Supported Regions page has no Email channel section. Confirm availability with AWS before relying on it.",
            "languages": "Language/locale support (Lex, Polly, conversational analytics, AI agents) is not evaluated per Region by the script. See supported-languages.html and the Lex V2 / Polly guides.",
        },
        "fips_regions": fips,
        "global_resiliency": gr,
        "campaign_destinations": campaign_dest,
        "campaign_notes": campaign_notes,
        "default_outbound": default_outbound,
        "default_outbound_prefix_notes": prefix_notes,
        "number_requirements": numreq,
        "telecoms": telecoms,
        "telecoms_footnotes": notes,
        "telecoms_legend": legend,
        "telecoms_history_tail": history[-12:],
        "countries": {k: {"iso2": v[0], "continent": v[1]} for k, v in COUNTRIES.items()},
        "curated": curated(a.cache),
        "sources": {k: {"url": u, "retrieved": today} for k, u in SOURCES.items()},
        "parse_warnings": WARN,
    }
    data["sources"]["telecoms_pdf"]["last_updated"] = last_updated
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    write_markdown(data)
    print("wrote %s (%d telecoms rows, %d features, %d warnings)" % (OUT_JSON, len(telecoms), len(features), len(WARN)))
    print("wrote %s" % OUT_MD)


if __name__ == "__main__":
    main()
