# la_property_bundle.py
import os, sys, time, argparse, requests, textwrap
from dotenv import load_dotenv

HOST = "data.lacity.org"
DATASETS = {
    # dataset_id : {title, columns for table, description-like fields to show below}
    "pi9x-tg5x": {  # Building Permits Issued (2020+)
        "title": "LADBS Permits (Issued)",
        "cols": ["permit_nbr","issue_date","status_desc","permit_type","valuation","primary_address","apn","zone"],
        "desc_keys": ["work_desc","work_description"],
        "date_keys": ["issue_date","status_date"],
    "zip_fields": [("zip_code", "eq")],
    },
    "9w5z-rg2h": {  # Inspections
        "title": "LADBS Inspections",
        "cols": ["address","inspection_date","inspection","inspection_result","permit","inspector_name"],
        "desc_keys": ["inspection_comments","description","result_description"],
        "date_keys": ["inspection_date"],
        "zip_fields": [],
    },
    "3f9m-afei": {  # Certificates of Occupancy
        "title": "Certificates of Occupancy",
        "cols": ["cofo_number","cofo_issue_date","latest_status","status_date","address","use","units"],
        "desc_keys": ["remarks","description"],
        "date_keys": ["cofo_issue_date","status_date"],
    "zip_fields": [("zip_code", "eq_numeric")],
    },
    "u82d-eh7z": {  # Code Enforcement (Open)
        "title": "Code Enforcement (Open)",
        "cols": ["case_no","address","case_open_date","violation_type","status","census_tract","council_district"],
        "desc_keys": ["violation_desc","description","actions"],
        "date_keys": ["case_open_date","status_date"],
    "zip_fields": [("zip", "like_prefix")],
    },
    "rken-a55j": {  # Code Enforcement (Closed)
        "title": "Code Enforcement (Closed)",
        "cols": ["case_no","address","case_open_date","case_closed_date","violation_type","disposition","council_district"],
        "desc_keys": ["violation_desc","description","actions"],
        "date_keys": ["case_open_date","case_closed_date"],
    "zip_fields": [("zip", "like_prefix")],
    },
}

def get_token() -> str:
    tok = os.getenv("SOCRATA_APP_TOKEN")
    if not tok:
        print("Missing SOCRATA_APP_TOKEN in .env", file=sys.stderr)
        sys.exit(1)
    return tok

def socrata_get(dataset_id: str, q: str, zip_code: str | None, limit: int, retries: int = 2):
    cfg = DATASETS[dataset_id]
    url = f"https://{HOST}/resource/{dataset_id}.json"
    params = {"$limit": limit}
    if q:
        params["$q"] = q
    if zip_code:
        escaped = zip_code.replace("'", "''")
        clauses = []
        for field_spec in cfg.get("zip_fields", []):
            if not field_spec:
                continue
            if isinstance(field_spec, tuple):
                field_name, mode = field_spec
            elif isinstance(field_spec, dict):
                field_name = field_spec.get("field")
                mode = field_spec.get("mode", "like_prefix")
            else:
                field_name = field_spec
                mode = "like_prefix"

            if not field_name:
                continue

            if mode == "eq_numeric":
                clauses.append(f"{field_name} = {escaped}")
            elif mode == "eq":
                clauses.append(f"{field_name} = '{escaped}'")
            else:  # default like prefix
                clauses.append(f"{field_name} like '{escaped}%\'")

        if clauses:
            params["$where"] = " OR ".join(clauses)
    headers = {"X-App-Token": get_token(), "Accept": "application/json", "User-Agent": "LA-Property-Bundle/1.0"}

    for attempt in range(retries + 1):
        r = requests.get(url, headers=headers, params=params, timeout=30)
        try:
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            code = getattr(e.response, "status_code", None)
            if code in (429,500,502,503,504) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            print(f"[{dataset_id}] HTTP {code}: {e}", file=sys.stderr)
            return []

def fmt_date(s: str | None) -> str:
    if not s: return "—"
    return s.split("T")[0] if "T" in s else s

def fmt_val(v):
    try:
        return f"{int(float(v)):,}"
    except Exception:
        return v if v not in (None, "", "0") else "—"

def pick(rec: dict, keys: list[str]) -> str:
    for k in keys:
        v = rec.get(k)
        if v not in (None, ""):
            return str(v)
    return "—"

def rich_available():
    try:
        import rich  # noqa
        return True
    except Exception:
        return False

def pretty_table(dataset_id: str, title: str, rows: list[dict]):
    cfg = DATASETS[dataset_id]
    cols = [c for c in cfg["cols"] if rows and c in rows[0]] or (list(rows[0].keys())[:8] if rows else cfg["cols"])
    desc_keys = cfg["desc_keys"]

    if rich_available():
        from rich import box
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        console = Console()
        console.print(f"[bold]{title}[/bold]")
        if not rows:
            console.print("No rows.")
            return
        t = Table(box=box.MINIMAL)
        # pretty column headers
        for c in cols:
            t.add_column(c.replace("_"," ").title(), overflow="fold")
        for rec in rows:
            rendered = []
            for c in cols:
                v = rec.get(c, "—")
                if c.endswith("_date"):
                    v = fmt_date(v)
                elif c in ("valuation",):
                    v = fmt_val(v)
                rendered.append(str(v if v not in (None, "") else "—"))
            t.add_row(*rendered)
        console.print(t)
        # description panels
        for rec in rows:
            desc = pick(rec, desc_keys)
            if desc != "—":
                short = (desc[:240] + "…") if len(desc) > 240 else desc
                console.print(Panel(short, title="Details", expand=False))
    else:
        print(title)
        if not rows:
            print("No rows.")
            return
        head = [c.upper() for c in cols]
        print(" | ".join(head))
        print("-" * 100)
        for rec in rows:
            rendered = []
            for c in cols:
                v = rec.get(c, "—")
                if c.endswith("_date"):
                    v = fmt_date(v)
                elif c in ("valuation",):
                    v = fmt_val(v)
                rendered.append(str(v if v not in (None, "") else "—"))
            print(" | ".join(rendered))
            desc = pick(rec, desc_keys)
            if desc != "—":
                print("  " + textwrap.fill(desc, width=96, subsequent_indent="  "))
            print("-" * 100)

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Pretty-print all LADBS datasets for an address (LA Open Data)")
    ap.add_argument("--address", default="4506 Tobias", help='Search text for $q (default: "4506 Tobias")')
    ap.add_argument("--zip", default="91403", help="ZIP filter (tries zip_code/zip) (default: 91403)")
    ap.add_argument("--limit", type=int, default=50, help="Max rows per dataset")
    ap.add_argument("--raw", action="store_true", help="Print raw JSON per dataset after header (no tables)")
    args = ap.parse_args()

    for dsid, cfg in DATASETS.items():
        rows = socrata_get(dsid, args.address, args.zip, args.limit)
        header = f"{cfg['title']} — {args.address} [{args.zip}] ({len(rows)} results)"
        if args.raw:
            print("\n" + "=" * 80)
            print(header)
            print("=" * 80)
            import json
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            print()
            pretty_table(dsid, header, rows)

if __name__ == "__main__":
    main()
