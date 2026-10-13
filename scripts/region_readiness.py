#!/usr/bin/env python3
"""Amazon Connect Region Readiness check.

Deterministic lookup: given a customer's requirements (features, phone numbers,
outbound destinations, agent locations, residency constraints) it evaluates
every Amazon Connect home Region against the bundled AWS source snapshot
(references/region-data/connect-region-data.json) and returns a per-Region
verdict, REG-xxx findings with citations, and a recommendation.

Standard library only; runs fully offline.

IMPORTANT — this script reads the BUNDLED SNAPSHOT only; it does NOT fetch live
AWS pages. It is the offline fallback / fast multi-Region scorer. The default,
current-data path is the Region Readiness agent, which fetches the live AWS page
per question and uses this snapshot only when a live fetch isn't possible. Output
from this script is a point-in-time self-prep draft, not a live or committed
answer; it stamps every report with its snapshot date and age.

    python3 scripts/region_readiness.py --input requirements.json            # Markdown report
    python3 scripts/region_readiness.py --input requirements.json --format json
    python3 scripts/region_readiness.py --list-features
    python3 scripts/region_readiness.py --country "South Africa"             # telephony lookup
    python3 scripts/region_readiness.py --template                           # blank input file

Verdicts: SUPPORTED, CONDITIONAL (possible, with a prerequisite/caveat),
NOT_SUPPORTED (blocker per the cited source), UNKNOWN (sources silent).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "references", "region-data", "connect-region-data.json")
STALE_DAYS = 90
ORDER = {"NOT_SUPPORTED": 0, "UNKNOWN": 1, "CONDITIONAL": 2, "SUPPORTED": 3}

FINDINGS = {
    "REG-001": "Feature not available in Region",
    "REG-002": "Phone number country/type not claimable in Region",
    "REG-003": "Telephony capability gap for the number (outbound / porting / multi-carrier / caller ID)",
    "REG-004": "Number offering not GA (Beta / Preview / Testing / via partner)",
    "REG-005": "Regulatory (KYC) documents or agent-location rule for the number",
    "REG-006": "Outbound destination not callable by default (allow-list request needed)",
    "REG-007": "Outbound campaigns cannot dial this destination from this Region",
    "REG-008": "Global Resiliency (ACGR) not available / pairing constraint",
    "REG-009": "Latency anchoring risk (neither agents nor numbers near the Region)",
    "REG-010": "Agent-location isolation guidance (India / South Korea / South Africa)",
    "REG-011": "AWS sources disagree - confirm with AWS before committing",
    "REG-012": "Excluded by data-residency / allowed-Region constraint",
    "REG-013": "Not evaluated - no Region data published",
}
TYPE_MAP = {  # input type -> Telecoms Coverage Guide service type(s)
    "DID": ["DID"], "TOLL_FREE": ["Toll-free"], "UIFN": ["UIFN"], "DID_MOBILE": ["DID (mobile)"],
    "SHARED": ["Shared Cost"], "SHARED_COST": ["Shared Cost"], "REPRESENTATIVE": ["Representative"],
    "MOBILE": ["DID (mobile)"], "TOLLFREE": ["Toll-free"], "TFN": ["Toll-free"], "LOCAL": ["DID"],
}
NEED_COLS = {
    "national_outbound": "national_outbound", "international_outbound": "international_outbound",
    "porting": "porting", "multi_carrier": "multi_carrier", "custom_caller_id": "custom_caller_id",
}
YELLOW_MEANING = {
    "number_availability": "use-case criteria checks apply (yellow tick)",
    "national_outbound": "supported, but delivery of the caller ID to the called party is not guaranteed (yellow tick)",
    "porting": "porting limited to certain numbers (yellow tick)",
    "international_outbound": "restricted (yellow tick) - see footnote",
}
TEMPLATE = {
    "_comment": "Fill in what you know; omit what you don't. Countries: ISO2 (GB) or name (United Kingdom).",
    "allowed_regions": [],
    "features": ["conversational_analytics.post_call_analytics", "agent_assist", "outbound_campaigns"],
    "phone_numbers": [
        {"country": "GB", "type": "DID", "needs": ["inbound", "national_outbound", "porting"]},
        {"country": "GB", "type": "TOLL_FREE", "needs": ["inbound"]},
    ],
    "outbound_destinations": ["GB", "IE"],
    "campaign_destinations": ["GB"],
    "agent_countries": ["GB"],
    "global_resiliency": False,
    "fips": False,
}


def load():
    with open(DATA) as f:
        return json.load(f)


class Ctx:
    def __init__(self, d):
        self.d = d
        self.by_iso = {v["iso2"]: k for k, v in d["countries"].items()}
        self.by_name = {k.lower(): k for k in d["countries"]}
        self.names = d["region_names"]

    ALIASES = {"uk": "United Kingdom", "great britain": "United Kingdom", "britain": "United Kingdom",
               "england": "United Kingdom", "usa": "United States", "united states of america": "United States",
               "america": "United States", "uae": "United Arab Emirates", "korea": "South Korea",
               "republic of korea": "South Korea", "holland": "Netherlands", "czechia": "Czech Republic",
               "turkiye": "Turkey", "türkiye": "Turkey", "north macedonia": "Macedonia",
               "cote d'ivoire": "Ivory Coast", "côte d'ivoire": "Ivory Coast", "ksa": "Saudi Arabia"}

    def country(self, x):
        x = str(x).strip()
        lx = x.lower()
        if lx in self.ALIASES:
            return self.ALIASES[lx]
        if x.upper() in self.by_iso:
            return self.by_iso[x.upper()]
        if lx in self.by_name:
            return self.by_name[lx]
        hits = [k for k in self.by_name if k.startswith(lx)] if len(lx) >= 4 else []
        return self.by_name[hits[0]] if len(hits) == 1 else None

    def iso(self, name):
        return self.d["countries"][name]["iso2"]

    def rname(self, r):
        return "%s (%s)" % (self.names.get(r, r), r)

    def src(self, key):
        return self.d["sources"][key]["url"]


def item(verdict, reg, req, detail, source, notes=None, region_independent=False):
    """One evaluated requirement. region_independent=True marks a blocker that no
    choice of Region fixes (e.g. a capability the number never has) - it is
    reported as a design blocker and excluded from Region ranking."""
    return {"verdict": verdict, "finding": reg, "requirement": req, "detail": detail,
            "source": source, "notes": notes or [], "region_independent": region_independent}


# --------------------------------------------------------------- feature checks
def resolve_feature(ctx, f):
    f0 = f.strip()
    key = f0.lower().replace(" ", "_") if f0 not in ctx.d["features"] else f0
    if key in ctx.d["features"]:
        return key
    al = ctx.d["feature_aliases"].get(f0.lower())
    if al:
        return al
    for k in ctx.d["features"]:  # sub-feature short names, e.g. "post_call_analytics"
        if k.endswith("." + key):
            return k
    return None


def check_feature(ctx, region, f):
    d = ctx.d
    key = resolve_feature(ctx, f)
    if key is None:
        if f.lower() in d["unlisted_features"]:
            return item("UNKNOWN", "REG-013", "Feature: %s" % f, d["unlisted_features"][f.lower()], ctx.src("regions"))
        return item("UNKNOWN", "REG-013", "Feature: %s" % f,
                    "Not a recognised feature key (run --list-features). Not evaluated.", ctx.src("regions"))
    fe = d["features"][key]
    req = "Feature: %s" % fe["label"]
    if key == "voice_id" or key.startswith("voice_id."):
        return item("NOT_SUPPORTED", "REG-001", req, fe["deprecated"]["quote"], fe["deprecated"]["source"],
                    region_independent=True)
    if key == "global_resiliency":
        return check_gr(ctx, region)
    if region not in fe["regions"]:
        return item("NOT_SUPPORTED", "REG-001", req, "%s is not listed for %s." % (fe["label"], ctx.rname(region)),
                    fe["section_url"])
    raw = fe.get("values", {}).get(region)
    notes = []
    if raw and raw not in ("Yes",):
        notes.append("Source cell reads %r." % raw + (" The page publishes no footnote for '*'." if "*" in raw else ""))
    for n in fe.get("notes", []):
        notes.append(n)
    return item("SUPPORTED", None, req, "Listed for %s." % ctx.rname(region), fe["section_url"], notes)


def check_gr(ctx, region):
    gr = ctx.d["global_resiliency"]
    req = "Global Resiliency (ACGR) replica"
    partners = [p["replica"] for p in gr["pairs"] if p["source"] == region] + \
               [p["source"] for p in gr["pairs"] if p["replica"] == region and p["bidirectional"]]
    reqs = gr.get("requirements", [])
    pre = [r for r in reqs if re.search(r"Enterprise Support|SAML|Port all phone numbers", r)]
    if not partners:
        return item("NOT_SUPPORTED", "REG-008", req,
                    "No permitted replica Region for a source instance in %s. %s" % (ctx.rname(region), " ".join(p["quote"] for p in gr["pairs"])),
                    ctx.src("gr_replica"))
    return item("CONDITIONAL", "REG-008", req,
                "Replica Region: %s. Prerequisites: %s" % (", ".join(ctx.rname(p) for p in partners), " | ".join(pre)),
                ctx.src("gr_replica") + " ; " + ctx.src("gr_requirements"))


def check_fips(ctx, region):
    fr = ctx.d["fips_regions"].get("connect", [])
    if region in fr:
        return item("SUPPORTED", None, "FIPS endpoint", "connect-fips endpoint published for %s." % region, ctx.src("regions"))
    return item("NOT_SUPPORTED", "REG-001", "FIPS endpoint", "No connect-fips endpoint published for %s." % region,
                ctx.src("regions"))


# ------------------------------------------------------------- telephony checks
def region_in(spec, region, commercial):
    if spec == "ALL":
        return True
    if spec == "ALL_COMMERCIAL":
        return region in commercial
    if isinstance(spec, list):
        return region in spec
    return None


def check_number(ctx, region, num, agent_countries):
    d = ctx.d
    cname = ctx.country(num.get("country", ""))
    ntype = str(num.get("type", "DID")).upper().replace("-", "_").replace(" ", "_")
    needs = [n.lower() for n in num.get("needs", ["inbound"])]
    label = "%s %s number" % (cname or num.get("country"), ntype)
    if not cname:
        return [item("UNKNOWN", "REG-013", label, "Country not recognised.", ctx.src("telecoms_pdf"))]
    iso = ctx.iso(cname)
    stypes = TYPE_MAP.get(ntype)
    if not stypes:
        return [item("UNKNOWN", "REG-013", label, "Unknown number type %r (use DID, TOLL_FREE, UIFN, DID_MOBILE, SHARED)." % ntype,
                     ctx.src("telecoms_pdf"))]
    rows = [t for t in d["telecoms"] if t["iso2"] == iso and t["service_type"] in stypes]
    pdf = ctx.src("telecoms_pdf")
    if not rows:
        offered = sorted({t["service_type"] for t in d["telecoms"] if t["iso2"] == iso})
        return [item("NOT_SUPPORTED", "REG-002", label,
                     "The Telecoms Coverage Guide does not offer %s numbers for %s. Offered: %s." % (
                         "/".join(stypes), cname, ", ".join(offered) or "none (country not listed)"), pdf)]
    commercial = d["commercial_regions"]
    out = []
    ok_rows = [r for r in rows if region_in(r["region_availability"], region, commercial)]
    other = [r for r in rows if r not in ok_rows]
    if not ok_rows:
        where = "; ".join(fmt_regions(r["region_availability"]) for r in rows)
        out.append(item("NOT_SUPPORTED", "REG-002", label,
                        "%s %s numbers can be claimed only in: %s." % (cname, "/".join(stypes), where), pdf))
        return out
    row = ok_rows[0]
    notes = []
    if other:
        notes.append("Another %s offering for %s is limited to %s (e.g. specific prefixes)." % (
            row["service_type"], cname, "; ".join(fmt_regions(r["region_availability"]) for r in other)))
    notes += ["Guide footnote: " + f for f in row.get("footnotes", [])]
    verdict, reg, detail = "SUPPORTED", None, "Claimable in %s per the Telecoms Coverage Guide (status %s)." % (
        ctx.rname(region), row["status"])
    na = row["number_availability"]
    if na and na["value"] == "conditional":
        verdict, reg = "CONDITIONAL", "REG-003"
        detail += " Number availability: " + YELLOW_MEANING["number_availability"] + "."
    out.append(item(verdict, reg, label, detail, pdf, notes))

    # status
    st = row["status"] or ""
    if st != "GA":
        meaning = {
            "Partner BETA": "BETA - customers can request early access; production traffic is not recommended",
            "Preview": "Preview - not GA",
            "Testing": "Test - testing only",
            "GA - Via Partner": "GA through a telephony partner - contact your AWS account team to onboard",
            "Partner GA": "GA through a telephony partner - contact your AWS account team to onboard",
        }.get(st, st)
        out.append(item("CONDITIONAL", "REG-004", label + " - status", meaning + ".", pdf))

    # capabilities the customer needs
    for n in needs:
        col = NEED_COLS.get(n)
        if not col:
            continue
        v = row.get(col) or {}
        human = n.replace("_", " ")
        if v.get("value") == "no":
            out.append(item("NOT_SUPPORTED", "REG-003", label + " - " + human,
                            "The guide marks %s as not available for %s %s." % (human, cname, row["service_type"]), pdf,
                            region_independent=True))
        elif v.get("value") == "conditional":
            out.append(item("CONDITIONAL", "REG-003", label + " - " + human,
                            "%s: %s." % (human.capitalize(), YELLOW_MEANING.get(col, "conditional (yellow tick)")), pdf,
                            ["Guide footnote: " + f for f in row.get("footnotes", [])]))
    if "campaigns" in needs:
        cr = row.get("campaign_regions")
        if not (isinstance(cr, list) and region in cr):
            out.append(item("NOT_SUPPORTED", "REG-007", label + " - outbound campaigns",
                            "The guide's Outbound Campaign Regions column for %s %s is %s." % (
                                cname, row["service_type"], fmt_regions(cr) if cr else "empty"), pdf))

    # regulatory page (ordering / porting regions, agent location, documents)
    out += check_number_requirements(ctx, region, cname, iso, ntype, needs, agent_countries, label)
    return out


def check_number_requirements(ctx, region, cname, iso, ntype, needs, agent_countries, label):
    d = ctx.d
    nr = d["number_requirements"]
    src = ctx.src("number_requirements")
    c = nr["countries"].get(iso)
    want = {"TOLL_FREE": "TOLL_FREE", "TOLLFREE": "TOLL_FREE", "TFN": "TOLL_FREE", "UIFN": "UIFN",
            "DID_MOBILE": "DID_MOBILE", "MOBILE": "DID_MOBILE", "SHARED": "SHARED", "SHARED_COST": "SHARED"}.get(ntype, "DID")
    out = []
    if c is None:
        if region in nr["default_excluded_regions"] and want != "UIFN" and iso != "US":
            out.append(item("CONDITIONAL", "REG-011", label + " - ordering Region",
                            "The Telecoms guide allows this Region, but the phone-number requirements page states: \"%s\". "
                            "%s has no country section there. Confirm with AWS." % (nr["default_rule_quote"], cname), src))
        return out
    rows = [o for o in c["order"] if o.get("type") == want] or ([o for o in c["order"] if o.get("type") == "DID"] if want == "DID_MOBILE" else [])
    restricted = [o for o in rows if isinstance(o.get("supported_regions"), list)]
    open_rows = [o for o in rows if o.get("supported_regions") == "ALL" or o.get("supported_regions") is None]
    if rows and restricted and not open_rows and not any(region in o["supported_regions"] for o in restricted):
        out.append(item("NOT_SUPPORTED", "REG-002", label + " - ordering Region",
                        "Phone-number requirements page lists ordering Regions for %s %s as: %s." % (
                            cname, want, "; ".join("%s → %s" % (o["number_text"][:50], ", ".join(o["supported_regions"])) for o in restricted)), src))
    elif rows and not restricted and region in nr["default_excluded_regions"] and not any(o.get("supported_regions") == "ALL" for o in rows):
        out.append(item("CONDITIONAL", "REG-011", label + " - ordering Region",
                        "Default rule on the requirements page: \"%s\". The Telecoms guide lists the number as claimable here. Confirm with AWS." % nr["default_rule_quote"], src))
    elif restricted and open_rows:
        out.append(item("SUPPORTED", None, label + " - ordering Region",
                        "Some prefixes are Region-restricted: %s. Other prefixes are available in all Regions." % (
                            "; ".join("%s → %s" % (o["number_text"][:50], ", ".join(o["supported_regions"])) for o in restricted)), src))
    for o in rows:
        if o.get("agent_location"):
            agents = [ctx.country(a) for a in agent_countries]
            outside = [a for a in agents if a and a != cname]
            if not agent_countries:
                out.append(item("CONDITIONAL", "REG-005", label + " - agent location",
                                o["agent_location"] + " (agent locations not provided).", src))
            elif outside:
                out.append(item("NOT_SUPPORTED", "REG-005", label + " - agent location",
                                "%s Agents also located in: %s." % (o["agent_location"], ", ".join(outside)), src,
                                region_independent=True))
            else:
                out.append(item("SUPPORTED", None, label + " - agent location", o["agent_location"], src))
            break
    docs = [o for o in rows if str(o.get("id_required", "")).lower().startswith("yes")]
    if docs:
        out.append(item("CONDITIONAL", "REG-005", label + " - regulatory documents",
                        "ID/KYC documents are required to order: %s" % docs[0].get("identification", "")[:300], src))
    if "porting" in needs and c.get("porting_supported") is False:
        out.append(item("NOT_SUPPORTED", "REG-003", label + " - porting",
                        "Phone-number requirements page: porting is not supported for %s." % cname, src,
                        region_independent=True))
    for n in c.get("notes", [])[:3]:
        if re.search(r"takes longer|preview|onboarding takes|physically", n, re.I):
            out.append(item("CONDITIONAL", "REG-005", label + " - lead time", n[:400], src))
            break
    return out


def fmt_regions(spec):
    if spec == "ALL":
        return "all Regions"
    if spec == "ALL_COMMERCIAL":
        return "all commercial Regions"
    if isinstance(spec, list):
        return ", ".join(spec) if spec else "none"
    return str(spec)


def check_outbound(ctx, region, dest):
    d = ctx.d
    cname = ctx.country(dest)
    label = "Outbound calls to %s" % (cname or dest)
    if not cname:
        return item("UNKNOWN", "REG-013", label, "Country not recognised.", ctx.src("default_outbound"))
    iso = ctx.iso(cname)
    default = d["default_outbound"].get(region, [])
    notes = [n for n in d["default_outbound_prefix_notes"] if (iso == "GB" and n.startswith("UK")) or (iso == "JP" and n.startswith("Japan"))]
    if iso in default:
        return item("SUPPORTED", None, label, "Callable by default from %s." % ctx.rname(region), ctx.src("default_outbound"), notes)
    q = d["curated"]["outbound_default_deny"]["quote"]
    return item("CONDITIONAL", "REG-006", label,
                "Not in the default list for %s. %s Raise a 'Country Allowlisting for Outbound Calls' support case." % (ctx.rname(region), q),
                ctx.src("default_outbound"), notes)


def check_campaign(ctx, region, dest):
    d = ctx.d
    cname = ctx.country(dest)
    label = "Outbound campaign to %s" % (cname or dest)
    if not cname:
        return item("UNKNOWN", "REG-013", label, "Country not recognised.", ctx.src("regions"))
    iso = ctx.iso(cname)
    if region not in d["features"]["outbound_campaigns"]["regions"]:
        return item("NOT_SUPPORTED", "REG-001", label, "Outbound campaigns is not available in %s." % ctx.rname(region), ctx.src("regions"))
    page = iso in d["campaign_destinations"].get(region, [])
    pdf = any(isinstance(t["campaign_regions"], list) and region in t["campaign_regions"]
              for t in d["telecoms"] if t["iso2"] == iso)
    src = ctx.src("regions") + "#campaigns_region ; " + ctx.src("telecoms_pdf")
    if page and pdf:
        return item("SUPPORTED", None, label, "Both the Regions page and the Telecoms guide allow %s → %s." % (region, cname), src)
    if page or pdf:
        which = "Telecoms guide (updated %s)" % d["sources"]["telecoms_pdf"].get("last_updated") if pdf else "Regions page"
        return item("CONDITIONAL", "REG-011", label,
                    "Only the %s lists %s → %s. Confirm with AWS before you plan dialling volume." % (which, region, cname), src)
    return item("NOT_SUPPORTED", "REG-007", label,
                "Neither source allows campaign calls from %s to %s. \"%s\"" % (
                    ctx.rname(region), cname, " ".join(d.get("campaign_notes", [])[-1:])), src)


def check_agents(ctx, region, agent_countries):
    d = ctx.d
    out = []
    iso_list = [ctx.country(a) for a in agent_countries]
    special = [a for a in iso_list if a in ("India", "South Korea", "South Africa")]
    if special:
        c = d["curated"]["agent_isolation"]
        out.append(item("CONDITIONAL", "REG-010", "Agents in " + ", ".join(special),
                        "AWS architecture guidance: \"%s\" Plan a dedicated instance for these agents." % c["quote"], c["source"]))
    return out


def check_latency(ctx, region, agent_countries, number_countries):
    d = ctx.d
    geo = d["region_geo"].get(region, {})
    cont = lambda n: d["countries"][n]["continent"] if n in d["countries"] else None
    agents = [ctx.country(a) for a in agent_countries if ctx.country(a)]
    nums = [ctx.country(n) for n in number_countries if ctx.country(n)]
    if not agents and not nums:
        return []
    a_near = [a for a in agents if cont(a) == geo.get("continent")]
    n_near = [n for n in nums if cont(n) == geo.get("continent")]
    far_a = sorted(set(agents) - set(a_near))
    far_n = sorted(set(nums) - set(n_near))
    q = d["curated"]
    if not far_a and not far_n:
        return [item("SUPPORTED", None, "Latency anchoring",
                     "Agents and numbers are on the same continent as %s (heuristic)." % ctx.rname(region), q["latency_anchor"]["source"])]
    both_far = sorted(set(far_a) & set(far_n))
    if (agents and not a_near) and (nums and not n_near):
        return [item("CONDITIONAL", "REG-009", "Latency anchoring",
                     "Neither agents (%s) nor numbers (%s) are on the same continent as %s. AWS: \"%s\" \"%s\" Measure with the Endpoint Test Utility before committing." % (
                         ", ".join(far_a), ", ".join(far_n), ctx.rname(region), q["latency_500"]["quote"], q["latency_900"]["quote"]),
                     q["latency_500"]["source"], ["Continent match is a heuristic; the Endpoint Test Utility measurement is authoritative."])]
    return [item("CONDITIONAL", "REG-009", "Latency anchoring",
                 "Partly anchored: off-continent agents %s; off-continent numbers %s. AWS: \"%s\" Measure from each location." % (
                     ", ".join(far_a) or "none", ", ".join(far_n) or "none", q["latency_anchor"]["quote"]),
                 q["latency_anchor"]["source"], ["Continent match is a heuristic."] + (
                     ["Both agents and numbers in %s are far from this Region." % ", ".join(both_far)] if both_far else []))]


# ----------------------------------------------------------------- orchestration
def evaluate(d, req):
    ctx = Ctx(d)
    allowed = req.get("allowed_regions") or []
    homes = d["home_regions"]
    agents = req.get("agent_countries", [])
    num_countries = [n.get("country") for n in req.get("phone_numbers", [])]
    results = {}
    for r in homes:
        items = []
        if allowed and r not in allowed:
            items.append(item("NOT_SUPPORTED", "REG-012", "Allowed Regions",
                              "%s is outside the allowed set (%s)." % (r, ", ".join(allowed)), "customer input"))
        if "-gov-" in r and not req.get("include_govcloud"):
            items.append(item("CONDITIONAL", "REG-012", "GovCloud", "AWS GovCloud (US-West) runs in a separate AWS GovCloud (US) account. Set include_govcloud=true if that is an option for you.", d["sources"]["regions"]["url"]))
        for f in req.get("features", []):
            items.append(check_feature(ctx, r, f))
        if req.get("global_resiliency"):
            items.append(check_gr(ctx, r))
        if req.get("fips"):
            items.append(check_fips(ctx, r))
        for n in req.get("phone_numbers", []):
            items += check_number(ctx, r, n, agents)
        for o in req.get("outbound_destinations", []):
            items.append(check_outbound(ctx, r, o))
        for c in req.get("campaign_destinations", []):
            items.append(check_campaign(ctx, r, c))
        items += check_agents(ctx, r, agents)
        items += check_latency(ctx, r, agents, num_countries)
        items = dedupe(items)
        blockers = [i for i in items if i["verdict"] == "NOT_SUPPORTED" and not i["region_independent"]]
        design = [i for i in items if i["verdict"] == "NOT_SUPPORTED" and i["region_independent"]]
        conds = [i for i in items if i["verdict"] in ("CONDITIONAL", "UNKNOWN")]
        overall = "NOT_SUPPORTED" if blockers else "CONDITIONAL" if conds or design else "SUPPORTED"
        results[r] = {"overall": overall, "blockers": len(blockers), "design_blockers": len(design),
                      "conditions": len(conds), "items": items}
    ranked = sorted(homes, key=lambda r: (results[r]["blockers"], "-gov-" in r, results[r]["conditions"], r))
    rec = recommend(ctx, results, ranked, allowed, req.get("include_govcloud"))
    return {"generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "data_snapshot": d["generated"], "telecoms_guide_last_updated": d["sources"]["telecoms_pdf"].get("last_updated"),
            "stale": staleness(d), "input": req, "ranking": ranked, "regions": results, "recommendation": rec,
            "design_blockers": design_blockers(results),
            "not_evaluated": [v for k, v in d["unlisted_features"].items() if k == "languages"]}


def recommend(ctx, results, ranked, allowed, include_gov=False):
    cands = [r for r in ranked if (not allowed or r in allowed) and (include_gov or "-gov-" not in r)]
    clean = [r for r in cands if results[r]["blockers"] == 0]
    if clean:
        best = clean[0]
        return {"type": "single_region", "region": best, "alternatives": clean[1:4],
                "summary": "%s meets every Region-dependent requirement (%d condition(s) to action%s)." % (
                    ctx.rname(best), results[best]["conditions"],
                    "; %d design blocker(s) remain whatever Region you choose - see below" % results[best]["design_blockers"]
                    if results[best]["design_blockers"] else "")}
    if not cands:
        return {"type": "none", "plan": [], "unachievable_in_any_region": [],
                "summary": "No candidate Region left after the allowed-Region constraint."}
    # No single Region: a requirement is blocked in a Region only if that Region has a
    # NOT_SUPPORTED item for it (requirements that produce no item there are met).
    blocked = {r: {i["requirement"] for i in results[r]["items"]
                   if i["verdict"] == "NOT_SUPPORTED" and i["finding"] != "REG-012" and not i["region_independent"]}
               for r in cands}
    primary = cands[0]
    unmet = set(blocked[primary])
    impossible = sorted(k for k in unmet if all(k in blocked[r] for r in cands))
    unmet -= set(impossible)
    plan = [{"region": primary, "role": "primary",
             "covers": ["everything except: " + "; ".join(sorted(blocked[primary]))]}]
    while unmet:
        r = max((c for c in cands if c not in [p["region"] for p in plan]),
                key=lambda c: sum(1 for k in unmet if k not in blocked[c]), default=None)
        cov = {k for k in unmet if r and k not in blocked[r]}
        if not cov:
            break
        # Every Region that covers the same gap is an equal option - don't pretend to
        # know which is nearer; the customer picks by measured latency.
        same = [c for c in cands if c not in [p["region"] for p in plan] and all(k not in blocked[c] for k in cov)]
        plan.append({"region": r, "role": "additional instance", "covers": sorted(cov),
                     "equivalent_regions": [c for c in same if c != r]})
        unmet -= cov
    return {"type": "multi_region" if len(plan) > 1 else "best_effort", "plan": plan,
            "unachievable_in_any_region": impossible + sorted(unmet),
            "summary": "No single Region meets every requirement. Closest: %s with %d blocker(s)." % (
                ctx.rname(primary), results[primary]["blockers"])}


def design_blockers(results):
    seen, out = set(), []
    for r in results.values():
        for i in r["items"]:
            if i["verdict"] == "NOT_SUPPORTED" and i["region_independent"] and i["requirement"] not in seen:
                seen.add(i["requirement"])
                out.append(i)
    return out


def dedupe(items):
    """Keep one item per (requirement, verdict, finding) - two sources can flag the same gap."""
    seen, out = {}, []
    for i in items:
        k = (i["requirement"], i["verdict"], i["finding"])
        if k in seen:
            prev = seen[k]
            if i["source"] not in prev["source"]:
                prev["source"] += " ; " + i["source"]
            continue
        seen[k] = i
        out.append(i)
    return out


def staleness(d):
    try:
        age = (dt.date.today() - dt.date.fromisoformat(d["generated"])).days
    except ValueError:
        return None
    return {"age_days": age, "stale": age > STALE_DAYS}


# ------------------------------------------------------------------- rendering
ICON = {"SUPPORTED": "✅", "CONDITIONAL": "⚠️", "NOT_SUPPORTED": "❌", "UNKNOWN": "❔"}


def render_md(res, d, top=3):
    ctx = Ctx(d)
    L = []
    A = L.append
    A("# Amazon Connect Region Readiness Report")
    A("")
    A("- Generated: %s · Data snapshot: %s · Telecoms Coverage Guide last updated: %s" % (
        res["generated"], res["data_snapshot"], res["telecoms_guide_last_updated"]))
    A("- **Data source: BUNDLED SNAPSHOT (offline).** This script does not fetch live AWS pages — it evaluates the "
      "point-in-time snapshot above. For current data, ask the Region Readiness agent, which fetches the live AWS "
      "page per question by default and uses this snapshot only as a fallback. Treat these results as a self-prep "
      "draft, not a live or committed answer.")
    if res["stale"] and res["stale"]["stale"]:
        A("- ⚠️ **Snapshot is %d days old (over %d-day freshness limit)** — do not rely on it; refresh with "
          "`scripts/build_region_data.py` or ask the agent for a live-fetched answer." % (res["stale"]["age_days"], STALE_DAYS))
    A("- A ✅ means the cited AWS document *lists* the item for that Region. It is NOT a guarantee of number stock, "
      "regulatory (KYC) approval, porting slots, or eligibility — confirm those via an AWS support case or your account team.")
    A("- Point-in-time copy of AWS documentation. Re-check the live pages before you commit (they change without notice).")
    A("")
    rec = res["recommendation"]
    A("## Recommendation")
    A("")
    A(rec["summary"])
    if rec["type"] == "single_region":
        if rec["alternatives"]:
            A("")
            A("Also viable: " + ", ".join(ctx.rname(r) for r in rec["alternatives"]) + ".")
    else:
        A("")
        for p in rec.get("plan", []):
            if p.get("equivalent_regions"):
                A("- **Additional instance** in any of %s — %s. Pick by Endpoint Test Utility latency from the users of that instance." % (
                    ", ".join("`%s`" % r for r in [p["region"]] + p["equivalent_regions"]), "; ".join(p["covers"])))
            else:
                A("- **%s** (%s) — %s" % (ctx.rname(p["region"]), p["role"], "; ".join(p["covers"])))
        if len(rec.get("plan", [])) > 1:
            A("")
            A("Each additional instance is a separate Connect instance (own users, flows, numbers, reporting, quotas). "
              "A feature on another instance only serves the contacts routed to that instance. The alternatives are to "
              "move those contacts, or to descope the requirement in the primary Region.")
        if rec.get("unachievable_in_any_region"):
            A("")
            A("Not achievable in any Region per the sources: " + "; ".join(rec["unachievable_in_any_region"]))
    A("")
    if res["design_blockers"]:
        A("## Design blockers — no Region choice fixes these")
        A("")
        for it in res["design_blockers"]:
            A("- ❌ **%s** %s — %s" % (it["finding"], it["requirement"], it["detail"]))
            A("  - Source: %s" % it["source"])
        A("")
    A("## Region scorecard")
    A("")
    A("| Rank | Region | Verdict | Region blockers | Design blockers | Conditions |")
    A("|---|---|---|---|---|---|")
    for i, r in enumerate(res["ranking"], 1):
        x = res["regions"][r]
        A("| %d | %s | %s %s | %d | %d | %d |" % (i, ctx.rname(r), ICON[x["overall"]], x["overall"], x["blockers"],
                                              x["design_blockers"], x["conditions"]))
    A("")
    shown = res["ranking"][:top]
    A("## Requirement × Region matrix (top %d)" % len(shown))
    A("")
    reqs = []
    for r in shown:
        for it in res["regions"][r]["items"]:
            if it["requirement"] not in reqs:
                reqs.append(it["requirement"])
    A("| Requirement | " + " | ".join("`%s`" % r for r in shown) + " |")
    A("|---|" + "---|" * len(shown))
    for q in reqs:
        cells = []
        for r in shown:
            v = [it for it in res["regions"][r]["items"] if it["requirement"] == q]
            cells.append(" ".join(sorted({ICON[x["verdict"]] + (" " + x["finding"] if x["finding"] else "") for x in v})) if v else "—")
        A("| %s | %s |" % (q, " | ".join(cells)))
    A("")
    for r in shown:
        x = res["regions"][r]
        A("## Findings — %s" % ctx.rname(r))
        A("")
        fs = [it for it in x["items"] if it["verdict"] != "SUPPORTED" and not it["region_independent"]]
        if not fs:
            A("No blockers or conditions.")
            A("")
            continue
        fs.sort(key=lambda it: ORDER[it["verdict"]])
        for it in fs:
            A("- %s **%s** %s — %s" % (ICON[it["verdict"]], it["finding"] or "", it["requirement"], it["detail"]))
            for n in it["notes"]:
                A("  - %s" % n)
            A("  - Source: %s" % it["source"])
        A("")
    if res["not_evaluated"]:
        A("## Not evaluated")
        A("")
        for n in res["not_evaluated"]:
            A("- " + n)
        A("")
    A("## Finding catalog")
    A("")
    for k, v in FINDINGS.items():
        A("- `%s` %s" % (k, v))
    A("")
    return "\n".join(L)


def list_features(d):
    homes = d["home_regions"]
    print("%-70s %s" % ("feature key", "regions"))
    for k, f in sorted(d["features"].items()):
        rs = f["regions"]
        print("%-70s %s" % (k, "all %d" % len(homes) if set(homes) <= set(rs) else ", ".join(rs) or "-"))
    print("\naliases: " + ", ".join("%s→%s" % kv for kv in sorted(d["feature_aliases"].items())))
    print("not in regions page: " + ", ".join(d["unlisted_features"]))


def country_lookup(d, name):
    ctx = Ctx(d)
    c = ctx.country(name)
    if not c:
        sys.exit("Country %r not recognised." % name)
    iso = ctx.iso(c)
    rows = [t for t in d["telecoms"] if t["iso2"] == iso]
    st = staleness(d)
    out = {"_provenance": "BUNDLED SNAPSHOT (offline) — not a live fetch. Snapshot %s (age %s days). "
                          "For current data ask the Region Readiness agent (live-first); this script is the offline fallback. "
                          "Listing a number/type here is not a guarantee of stock, KYC approval, or porting slots — "
                          "confirm via an AWS support case or your account team." % (
                              d["generated"], st["age_days"] if st else "unknown"),
           "country": c, "iso2": iso, "telecoms_guide": rows,
           "number_requirements": d["number_requirements"]["countries"].get(iso),
           "default_outbound_from": sorted(r for r, cs in d["default_outbound"].items() if iso in cs),
           "campaigns_from_regions_page": sorted(r for r, cs in d["campaign_destinations"].items() if iso in cs)}
    print(json.dumps(out, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="requirements JSON file ('-' for stdin)")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--top", type=int, default=3, help="Regions to detail in the Markdown report")
    ap.add_argument("--list-features", action="store_true")
    ap.add_argument("--country")
    ap.add_argument("--template", action="store_true")
    a = ap.parse_args()
    d = load()
    if a.template:
        print(json.dumps(TEMPLATE, indent=1))
        return
    if a.list_features:
        list_features(d)
        return
    if a.country:
        country_lookup(d, a.country)
        return
    if not a.input:
        ap.error("--input is required (or use --template / --list-features / --country)")
    req = json.load(sys.stdin if a.input == "-" else open(a.input))
    res = evaluate(d, req)
    if a.format == "json":
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        print(render_md(res, d, a.top))


if __name__ == "__main__":
    main()
