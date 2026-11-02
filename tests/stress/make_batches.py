"""Synthetic deliveries for the ingest stress test (ported from the 2026-11-02 stress run; deterministic, seeded).

build_pack(target) copies the data pack (base files and updates/2026-10-28) into `target` and writes, under
target/updates/:

  2026-10-29  a realistic next day: issuers, instruments, ownership, ratings, one book's positions plus an
              unentitled book, three research notes (one unlabelled, one with a label nobody holds), desk lines
  2026-10-30  a re-delivery: the 10-29 ratings again, the 10-28 note again, EM_MACRO positions only, and the
              issuer an instrument of 10-29 was waiting for
  2026-11-01  Excel export of an instruments file (UTF-8 BOM, CRLF): accepted
  2026-11-02 .. 2026-11-08  one malformed input each: rejected, the batch rolled back, file (and line) named
  2026-11-09  a note naming entities as "&amp;" and dotted abbreviations
  2026-11-10  volume: VOLUME issuers, instruments, positions per book, ratings, notes (descriptions repeat)

Run as a script to write a pack for inspection: python -I tests/stress/make_batches.py <target dir>
"""
from __future__ import annotations

import random
import shutil
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
SEED = 7
VOLUME = {"issuers": 60, "instruments": 300, "positions_per_book": 250, "ratings": 120, "notes": 20}

INS_HDR = ("instrument_id,isin,ticker,description,instrument_type,issuer_name,guarantor_name,currency,coupon,"
           "maturity,underlying_curve,source_system\n")
ISS_HDR = "issuer_id,legal_name,short_name,lei,country_of_incorporation,issuer_type,sector,source_system,last_updated\n"
POS_HDR = "book,instrument_ref,ref_type,quantity,notional_ccy,as_of_date\n"
RAT_HDR = "entity,agency,rating,outlook,action_date,source\n"
OWN_HDR = "owner,owned_entity,stake_pct,as_of_date,source,notes\n"


def write(path: Path, text: str, eol: str = "\n", bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        f.write(text.replace("\n", eol))


def note(title: str, source: str, author: str, day: str, body: str, visibility: str | None = "external") -> str:
    vis = f"visibility: {visibility}\n" if visibility else ""
    return f"---\ntitle: {title}\nsource: {source}\nauthor: {author}\ndate: {day}\n{vis}---\n\n{body}\n"


def day_2026_10_29(u: Path) -> None:
    b = u / "2026-10-29"
    write(b / "issuers_delta.csv", ISS_HDR +
          "ISS-0011,Corvana Telecom Holdings SA,CorTel Holdings,5493CTHOLD0000000901,QC,Corporate,Telecoms,SecMaster,2026-10-29\n"
          "ISS-0012,Valdoria Ports Authority,VPA,,QV,Agency,Industrials,SecMaster,2026-10-29\n"
          "ISS-0006,First Corvana Bank,FCB,5493FIRSTCB000000507,QC,Corporate,Financials,SecMaster,2025-03-14\n"
          "ISS-0003,Corvana Power & Light plc,CPL,5493CPLPWR0000000204,QC,Corporate,Utilities,SecMaster,2026-10-29\n"
          "ISS-0008,Meridian Mining plc,Meridian,213800MERIDIAN000746,GB,Corporate,Mining,SecMaster,2026-04-30\n")
    write(b / "instruments_delta.csv", INS_HDR +
          "INS-1013,XS3011223344,CTHOLD 7 11/01/31,CorTel Holdings 7% 2031,Corporate Bond,Corvana Telecom Holdings SA,,USD,7.0,2031-11-01,,SecMaster\n"
          "INS-1014,XS3011223351,CDBANK 6.25 10/29/29,Corvana Development Bank 6.25% 2029,Agency Bond,CDB,Republic of Corvana,USD,6.25,2029-10-29,,SecMaster\n"
          "INS-1015,XS3011223369,FCB 8 11/15/28,First Corvana Bank 8% 2028,Corporate Bond,First Corvana Bank Ltd,,USD,8.0,2028-11-15,,SecMaster\n"
          "INS-1017,XS3011223385,KESTRL 9 06/30/30,Kestrel Resources 9% 2030,Corporate Bond,Kestrel Resources Ltd,,USD,9.0,2030-06-30,,SecMaster\n"
          "INS-2004,,CDBANK CDS USD SR 5Y,CDB 5Y senior CDS,CDS,Corvana Development Bank,,USD,1.0,2031-12-20,,SecMaster\n"
          "INS-1005,XS2600112234,CNOC 5.875 11/04/29,CNOC Finance 5.875% 2029,Corporate Bond,CNOC Finance B.V.,Corvana National Oil Co,USD,5.875,2030-11-04,,SecMaster\n"
          "INS-1006,XS2500445569,CORPWR 6 05/20/31,Corvana Power & Light 6% 2031,Corporate Bond,Corvana Power & Light plc,,USD,6.0,2031-05-20,,SecMaster\n")
    write(b / "ownership_delta.csv", OWN_HDR +
          "Republic of Corvana (MinFin),Corvana Power & Light plc,34,2026-10-15,CPL secondary placement notice,\n"
          "Corvana Telecom Holdings SA,Corvana Telecommunications SA,80,2026-10-29,CorTel annual report 2025,\n"
          "Republic of Corvana (MinFin),Corvana Development Bank,100,2026-10-29,MinFin press release,Sovereign guarantee withdrawn for new issuance from 2027\n"
          "Republic of Valdoria,Valdoria Ports Authority,100,2026-10-29,VPA charter,Financing vehicle for sovereign infrastructure debt\n")
    write(b / "ratings_delta.csv", RAT_HDR +
          "Corvana Development Bank,Agency A,B+,Stable,2026-10-29,RatingsFeed\n"
          "First Corvana Bank,Agency A,B,Negative,2026-10-29,RatingsFeed\n"
          "Corvana National Oil Company,Agency A,B+,Stable,2026-10-28,RatingsFeed\n"
          "Republic of Corvana,Agency A,B,Negative,2026-10-28,RatingsFeed\n"
          "Corvana Telecom Holdings SA,Agency A,B+,Stable,2026-10-29,RatingsFeed\n")
    credit = ["XS2812345672,ISIN,10000000,USD", "CNOC 5.875 11/04/29,TICKER,12000000,USD", "XS2500445569,ISIN,7500000,USD",
              "INS-1007,INTERNAL,6000000,USD", "XS2700334415,ISIN,9000000,USD", "XS2300665523,ISIN,4000000,USD",
              "INS-2001,INTERNAL,-20000000,USD", "XS2999887768,ISIN,5000000,USD", "XS3011223351,ISIN,8000000,USD",
              "XS3011223344,ISIN,3000000,USD", "INS-2004,INTERNAL,-10000000,USD", "XS3011223369,ISIN,2000000,USD",
              "XS3011223385,ISIN,1000000,USD"]
    write(b / "positions_delta.csv", POS_HDR + "".join(f"EM_CREDIT,{r},2026-10-29\n" for r in credit)
          + "EM_RATES,CVD IRS 5Y,TICKER,-300000000,CVD,2026-10-29\n")
    write(b / "research" / "2026-10-29_bank-a_cpl-placement.md", note(
        "CPL - state stake falls to 34% after secondary placement", "Bank A Research", "Utilities Credit Team",
        "2026-10-29",
        "The Ministry of Finance completed a secondary placement of Corvana Power & Light shares on 15 October, taking\n"
        "the state's stake from 51% to 34%. With the sovereign now a minority shareholder we expect Agency A to review\n"
        "CPL on a standalone basis.\n\nCorTel Holdings, the holding company that owns 80% of CorTel, has issued its first\n"
        "USD bond (CTHOLD 7 11/01/31). The bond is not guaranteed by Corvana Telecommunications."))
    write(b / "research" / "2026-10-29_rates-internal_cvd-curve.md",
          "Title: CVD curve - bear steepening after the downgrade\n"
          "Internal rates note | EM Rates team | 29 Oct 2026 | visibility: rates_internal\n\n"
          "The CVD govt curve sold off 35bp in the 10Y sector after Agency A cut the Republic to B+. CVD-OIS 5Y moved\n"
          "22bp. We keep paying CVD 5Y swaps.\n")
    write(b / "research" / "2026-10-29_bank-c_fcb-nexus.md", note(
        "First Corvana Bank - the sovereign-bank nexus tightens", "Bank C Research", "CEEMEA Banks", "2026-10-29",
        "FCB holds roughly 31% of its assets in Corvana government securities (CVGBs). After the downgrade of the\n"
        "Republic of Corvana to B+, we expect Agency A to cap FCB at the sovereign rating.", visibility=None))
    write(b / "desk_notes" / "em-credit-desk-notes.md",
          "# EM Credit desk - running notes (copied from desk chat)\n\n"
          "[2026-10-28 08:05] dk: downgrade done. CNOC moved same day, CDB still BB- on the feed - lag. sell protection on\n"
          "CDB 5Y vs CORVAN 5Y as a basis trade.\n\n"
          "[2026-10-29 10:40] j.s: CPL now 34% state owned per the placement notice. treat as standalone credit from here.\n\n"
          "[2026-10-29 15:12] dk: careful, MinFin says the CDB guarantee does NOT cover new issuance from 2027. existing 27s\n"
          "and the new 29s still covered.\n")


def day_2026_10_30(u: Path) -> None:
    b = u / "2026-10-30"
    b.mkdir(parents=True, exist_ok=True)
    shutil.copy(u / "2026-10-29" / "ratings_delta.csv", b / "ratings_delta.csv")
    (b / "research").mkdir(exist_ok=True)
    shutil.copy(u / "2026-10-28" / "research" / "2026-10-28_bank-b_corvana-downgrade.md", b / "research")
    write(b / "issuers_delta.csv", ISS_HDR +
          "ISS-0013,Kestrel Resources Ltd,Kestrel,,QC,Corporate,Materials,SecMaster,2026-10-30\n")
    macro = ["XS2812345671,ISIN,15000000,USD", "QC000CV33031,ISIN,450000000,CVD", "INS-2002,INTERNAL,25000000,USD",
             "CVD IRS 5Y,TICKER,800000000,CVD", "XS2900123451,ISIN,8000000,USD", "GB00NB123454,ISIN,5000000,GBP"]
    write(b / "positions_delta.csv", POS_HDR + "".join(f"EM_MACRO,{r},2026-10-30\n" for r in macro))


# (folder, expected: None = accepted, else (file the error must name, line or None))
MALFORMED: dict[str, tuple[str, int | None] | None] = {
    "2026-11-01": None,
    "2026-11-02": ("ratings_delta.csv", 2),
    "2026-11-03": ("research/2026-11-03_bank-b_cnoc.md", 2),
    "2026-11-04": ("research/2026-11-04_bank-a_cdb.md", 5),
    "2026-11-05": ("positions_delta.csv", 2),
    "2026-11-06": ("issuers_delta.csv", 2),
    "2026-11-07": ("prices_delta.csv", None),
    "2026-11-08": ("research/2026-11-08_bank-b_cpl.md", 1),
}


def hostile(u: Path) -> None:
    write(u / "2026-11-01" / "instruments_delta.csv", INS_HDR +
          "INS-1016,XS3011223377,CORVAN 8 11/01/36,Republic of Corvana 8% 2036,Sovereign Bond,Republic of Corvana,,USD,8.0,2036-11-01,,SecMaster\n",
          eol="\r\n", bom=True)
    write(u / "2026-11-02" / "ratings_delta.csv", RAT_HDR + "Republic of Corvana,Agency B,B1,Negative,2026-11-02,RatingsFeed\n")
    write(u / "2026-11-03" / "research" / "2026-11-03_bank-b_cnoc.md",
          "---\ntitle: CNOC: still capped at the sovereign\nsource: Bank B Research\nauthor: CEEMEA Credit Strategy\n"
          "date: 2026-11-03\nvisibility: external\n---\n\nCNOC remains capped at the sovereign.\n")
    write(u / "2026-11-04" / "research" / "2026-11-04_bank-a_cdb.md",
          "---\ntitle: CDB follows the sovereign\nsource: Bank A Research\nauthor: Agencies Team\ndate: 4 Nov 2026\n"
          "visibility: external\n---\n\nAgency A cut Corvana Development Bank to B+.\n")
    write(u / "2026-11-05" / "positions_delta.csv", POS_HDR + 'EM_CREDIT,XS2500445569,Isin,"7,500,000",USD,2026-11-05\n')
    write(u / "2026-11-06" / "issuers_delta.csv", ISS_HDR +
          "ISS-0014,Springbok Minerals Ltd,Springbok,,ZA,Corporate,Materials,SecMaster,2026-11-06\n")
    write(u / "2026-11-07" / "prices_delta.csv", "instrument_id,price\nINS-1001,88.5\n")
    write(u / "2026-11-08" / "research" / "2026-11-08_bank-b_cpl.md",
          "CPL: we move to Neutral. The 34% state stake no longer supports the rating.\n")
    write(u / "2026-11-09" / "research" / "2026-11-09_bank-a_compendium.md", note(
        "Credit compendium", "Bank A Research", "EM Strategy", "2026-11-09",
        "Corvana Power &amp; Light and C.N.O.C. are discussed below.\n\n"
        + "Spreads on the sovereign curve widened; the outlook remains Negative. " * 400))


def volume(u: Path, rnd: random.Random) -> None:
    v = u / "2026-11-10"
    words = ["Atlas", "Borealis", "Cobalt", "Delta", "Ember", "Falcon", "Granite", "Harbor", "Iris", "Juniper"]
    kinds = ["Energy", "Utilities", "Financials", "Telecoms", "Materials", "Industrials"]
    issuers = []
    for n in range(100, 100 + VOLUME["issuers"]):
        name = f"{rnd.choice(words)} {rnd.choice(words)} {rnd.choice(kinds)} {n} plc"
        issuers.append((f"ISS-{n:04d}", name, f"{name[:3].upper()}{n}", rnd.choice(["QC", "QV", "GB", "NL", "US"])))
    write(v / "issuers_delta.csv", ISS_HDR + "".join(
        f"{i},{name},{short},,{c},Corporate,{rnd.choice(kinds)},SecMaster,2026-11-10\n" for i, name, short, c in issuers))
    inst = []
    for n in range(5000, 5000 + VOLUME["instruments"]):
        i = rnd.choice(issuers)
        guarantor = "Republic of Corvana" if rnd.random() < 0.05 else ""
        inst.append((f"INS-{n}", f"XS9{n:09d}", f"{i[2]} {rnd.randint(3, 9)} {n}", i[1], guarantor))
    # descriptions repeat on purpose ("<issuer> bond"), like a RegS/144A pair: not an alias, never a collision
    write(v / "instruments_delta.csv", INS_HDR + "".join(
        f"{iid},{isin},{tick},{iname} bond,Corporate Bond,{iname},{g},USD,5.0,2032-01-01,,SecMaster\n"
        for iid, isin, tick, iname, g in inst))
    own = [(rnd.choice(["Republic of Corvana (MinFin)", "Republic of Valdoria"]), i[1], rnd.choice([20, 34, 51, 100]))
           for i in rnd.sample(issuers, VOLUME["issuers"] // 3)]
    write(v / "ownership_delta.csv", OWN_HDR + "".join(f"{o},{e},{s},2026-11-10,synthetic,\n" for o, e, s in own))
    scale = ["BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B", "B-"]
    seen, rat = set(), []
    while len(rat) < VOLUME["ratings"]:
        i, d = rnd.choice(issuers), f"2026-{rnd.randint(1, 10):02d}-{rnd.randint(1, 28):02d}"
        if (i[1], d) not in seen:
            seen.add((i[1], d))
            rat.append(f"{i[1]},Agency A,{rnd.choice(scale)},Stable,{d},RatingsFeed\n")
    write(v / "ratings_delta.csv", RAT_HDR + "".join(rat))
    rows = [f"{book},{k[1]},ISIN,{rnd.randint(-50, 50) * 100000 or 100000},USD,2026-11-10\n"
            for book in ("EM_MACRO", "EM_CREDIT") for k in rnd.sample(inst, VOLUME["positions_per_book"])]
    write(v / "positions_delta.csv", POS_HDR + "".join(rows))
    for n in range(VOLUME["notes"]):
        picks = rnd.sample(issuers, 4)
        body = " ".join(f"{p[1]} ({p[2]}) looks {rnd.choice(['cheap', 'rich', 'fair'])} versus the Republic of "
                        f"Corvana curve." for p in picks)
        write(v / "research" / f"2026-11-10_bank-z_note-{n:03d}.md", note(
            f"Synthetic note {n}", "Bank Z Research", f"Desk {n % 7}", "2026-11-10", body,
            visibility=rnd.choice(["external", "macro_internal", "credit_internal"])))


FOLDERS = ("2026-10-28", "2026-10-29", "2026-10-30", *MALFORMED, "2026-11-09", "2026-11-10")


def build_pack(target: Path, seed: int = SEED) -> Path:
    """The data pack (base and updates/2026-10-28) copied to target, plus every synthetic delivery. Returns target."""
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"{target} is not empty")
    shutil.copytree(DATA, target, dirs_exist_ok=True)
    u = target / "updates"
    day_2026_10_29(u)
    day_2026_10_30(u)
    hostile(u)
    volume(u, random.Random(seed))
    return target


if __name__ == "__main__":
    print(build_pack(Path(sys.argv[1])))
