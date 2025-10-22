# pretty_la_permits.py
import os, sys, time, argparse, json, textwrap, requests
from dotenv import load_dotenv

BASE_URL = "https://data.lacity.org/resource/pi9x-tg5x.json"
FIELDS = ["permit_nbr","issue_date","status_desc","permit_type","valuation","primary_address","apn","zone"]

def get_token():
    tok = os.getenv("SOCRATA_APP_TOKEN")
    if not tok:
        print("Missing SOCRATA_APP_TOKEN in .env", file=sys.stderr)
        sys.exit(1)
    return tok

def fetch(address, zip_code, limit, raw=False):
    params = {"$limit": limit, "$order": "issue_date DESC"}
    if address:
        params["$q"] = address
    if zip_code:
        params["$where"] = f"zip_code = '{zip_code}'"

    headers = {"X-App-Token": get_token(), "Accept": "application/json", "User-Agent": "LA-Permits-Pretty/1.0"}

    # simple retry for 429/5xx
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            if raw:
                return r  # caller prints text as-is
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            code = getattr(e.response, "status_code", None)
            if code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            print(f"HTTP {code}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Request failed: {e}", file=sys.stderr)
            sys.exit(1)

def fmt_val(v):
    try:
        return f"{int(float(v)):,}"
    except Exception:
        return v if v not in (None, "", "0") else "—"

def pretty_print(records, title):
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        console = Console()
        console.print(Text(title, style="bold"))
        if not records:
            console.print("No permits found.")
            return
        table = Table(box=box.MINIMAL)
        for col in ["Permit #","Issue Date","Status","Type","Valuation","Address","APN","Zone"]:
            table.add_column(col, overflow="fold")
        for rec in records:
            row = [
                rec.get("permit_nbr","—"),
                (rec.get("issue_date","") or "—").split("T")[0],
                rec.get("status_desc","—"),
                rec.get("permit_type","—"),
                fmt_val(rec.get("valuation")),
                rec.get("primary_address","—"),
                rec.get("apn","—"),
                rec.get("zone","—"),
            ]
            table.add_row(*row)
        console.print(table)
        # wrapped work_desc blocks
        for rec in records:
            desc = rec.get("work_desc") or rec.get("work_description") or ""
            if desc:
                short = (desc[:200] + "…") if len(desc) > 200 else desc
                console.print(Panel(short, title=f"Work Description • {rec.get('permit_nbr','')}", expand=False))
    except Exception:
        # Fallback: plain text
        print(title)
        if not records:
            print("No permits found.")
            return
        header = ["PERMIT #","DATE","STATUS","TYPE","VAL","ADDRESS","APN","ZONE"]
        print(" | ".join(header))
        print("-"*100)
        for rec in records:
            row = [
                rec.get("permit_nbr","—"),
                (rec.get("issue_date","") or "—").split("T")[0],
                rec.get("status_desc","—"),
                rec.get("permit_type","—"),
                fmt_val(rec.get("valuation")),
                rec.get("primary_address","—"),
                rec.get("apn","—"),
                rec.get("zone","—"),
            ]
            print(" | ".join(str(x) for x in row))
            desc = rec.get("work_desc") or rec.get("work_description") or ""
            if desc:
                wrapped = textwrap.fill(desc, width=96, subsequent_indent="  ")
                print("  " + wrapped)
            print("-"*100)

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Pretty-print LA LADBS permits")
    ap.add_argument("--address", default="5020 Noble", help='Search text for $q (default: "5020 Noble")')
    ap.add_argument("--zip", help="ZIP filter (exact match on zip_code)")
    ap.add_argument("--limit", type=int, default=50, help="Max rows (default: 50)")
    ap.add_argument("--raw", action="store_true", help="Print raw JSON body from API and exit")
    args = ap.parse_args()

    if args.raw:
        r = fetch(args.address, args.zip, args.limit, raw=True)
        print(r.text)
        sys.exit(0)

    data = fetch(args.address, args.zip, args.limit)
    title = f"LA Permits — {args.address}" + (f" [{args.zip}]" if args.zip else "") + f" ({len(data)} results)"
    pretty_print(data, title)

if __name__ == "__main__":
    main()
