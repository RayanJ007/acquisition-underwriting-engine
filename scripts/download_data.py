"""Download configured public snapshots with explicit user-agent identification."""

import argparse, json, os, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml
from source_manifest import write_manifest

ROOT = Path(__file__).resolve().parents[1]


def fetch(url: str, path: Path) -> None:
    user_agent = os.environ.get("SEC_USER_AGENT")
    if "sec.gov" in url and not user_agent:
        raise ValueError(
            "Set SEC_USER_AGENT to an identifying research name and contact before downloading SEC data."
        )
    request = urllib.request.Request(
        url, headers={"User-Agent": user_agent or "AcquisitionResearch/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    json.loads(payload)
    path.write_bytes(payload)
    path.with_suffix(".source.json").write_text(
        json.dumps(
            {"source": url, "retrieved_at": datetime.now(timezone.utc).isoformat()},
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Replace existing snapshots, including metadata",
    )
    args = parser.parse_args()
    c = yaml.safe_load((ROOT / "config/company.yaml").read_text())
    companies = [c["company"], *c["peers"]]
    date = datetime.fromisoformat(c["company"]["market_date"]).replace(
        tzinfo=timezone.utc
    )
    start = int(date.timestamp())
    end = int((date + timedelta(days=1)).timestamp())
    for item in companies:
        ticker = item["ticker"]
        cik = item["cik"]
        path = ROOT / f"data/raw/{ticker}_companyfacts.json"
        if args.refresh or not path.exists():
            fetch(
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
                path,
            )
        path = ROOT / f"data/raw/{ticker}_market.json"
        if args.refresh or not path.exists():
            fetch(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={start}&period2={end}&interval=1d",
                path,
            )
        time.sleep(0.2)
    write_manifest()
