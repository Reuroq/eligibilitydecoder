"""Deploy eligibilitydecoder.com — Render static site + Name.com domain. Mirrors the fleet
pattern. Secrets never printed.
Commands: recon | create_service | register | dns | render_domain | status | env | deploy"""
import sys, json, base64, urllib.request, urllib.error
from pathlib import Path

ENV = Path(r"C:\Users\dwayn\OneDrive\Desktop\workshield-product\.env.deploy")
creds = {}
for line in ENV.read_text(encoding="latin-1").splitlines():
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); creds[k.strip()] = v.strip()
RENDER_KEY = creds["RENDER_API_KEY"]
RENDER_OWNER = creds.get("RENDER_OWNER_ID", "")
NC_USER = creds["NAMECOM_USERNAME"]
NC_TOKEN = creds["NAMECOM_API_TOKEN"]

DOMAIN = "eligibilitydecoder.com"
REPO = "https://github.com/Reuroq/eligibilitydecoder"
BRANCH = "main"
APEX_IP = "216.24.57.1"
SERVICE_ID = creds.get("CLI_SERVICE_ID", "")
NAME = "eligibilitydecoder"


def req(url, method="GET", headers=None, data=None):
    h = headers or {}
    body = json.dumps(data).encode() if data is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {"error": "non-json"}
    except Exception as e:
        return 0, {"error": str(e)}


def render_h():
    return {"Authorization": f"Bearer {RENDER_KEY}", "Accept": "application/json"}


def nc_h():
    tok = base64.b64encode(f"{NC_USER}:{NC_TOKEN}".encode()).decode()
    return {"Authorization": f"Basic {tok}", "Accept": "application/json"}


NC = "https://api.name.com"


def find_service():
    st, data = req("https://api.render.com/v1/services?limit=100", headers=render_h())
    if st != 200:
        return None, (st, data)
    for item in data:
        svc = item.get("service", item)
        if NAME in svc.get("name", "").lower():
            return svc, None
    return None, "not found"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "recon"

    if cmd == "recon":
        st2, who = req("https://api.render.com/v1/services?limit=1", headers=render_h())
        svc, err = find_service()
        print(f"  render services_http={st2} | existing service: {svc.get('id') if svc else err}")
        st, data = req(f"{NC}/v4/domains:checkAvailability", method="POST", headers=nc_h(),
                       data={"domainNames": [DOMAIN]})
        if st == 200:
            for r in data.get("results", []):
                print(f"  {r.get('domainName')}: purchasable={r.get('purchasable')} price=${r.get('purchasePrice')} "
                      f"renew=${r.get('renewalPrice')} premium={r.get('premium')}")
        else:
            print(f"  check http={st} -> {json.dumps(data)[:300]}")

    elif cmd == "register":
        body = {"domain": {"domainName": DOMAIN}, "purchaseType": "registration", "years": 1}
        st, data = req(f"{NC}/v4/domains", method="POST", headers=nc_h(), data=body)
        if st in (200, 201):
            d = data.get("domain", data)
            print(f"  REGISTERED {d.get('domainName')} expires={d.get('expireDate')} ns={d.get('nameservers')}")
        else:
            print(f"  REGISTER http={st} -> {json.dumps(data)[:400]}")

    elif cmd == "create_service":
        body = {"type": "static_site", "name": NAME, "ownerId": RENDER_OWNER, "repo": REPO, "branch": BRANCH,
                "autoDeploy": "yes",
                "serviceDetails": {"buildCommand": "pip install -r requirements.txt && python build.py",
                                   "publishPath": "dist"}}
        st, data = req("https://api.render.com/v1/services", method="POST", headers=render_h(), data=body)
        svc = data.get("service", data)
        print(f"  create_service http={st} id={svc.get('id')} url={svc.get('serviceDetails', {}).get('url', '')}")
        if st not in (200, 201):
            print("  ->", json.dumps(data)[:500])

    elif cmd == "dns":
        www_target = sys.argv[2] if len(sys.argv) > 2 else f"{NAME}.onrender.com"
        for host, rtype, ans in [("", "A", APEX_IP), ("www", "CNAME", www_target)]:
            st, data = req(f"{NC}/v4/domains/{DOMAIN}/records", method="POST", headers=nc_h(),
                           data={"host": host, "type": rtype, "answer": ans, "ttl": 300})
            print(f"  {rtype} {host or '@'} -> {ans}: http={st} {'OK' if st in (200, 201) else json.dumps(data)[:200]}")

    elif cmd == "render_domain":
        sid = sys.argv[2] if len(sys.argv) > 2 else SERVICE_ID
        for name in (DOMAIN, f"www.{DOMAIN}"):
            st, data = req(f"https://api.render.com/v1/services/{sid}/custom-domains", method="POST",
                           headers=render_h(), data={"name": name})
            already = st == 409 or "already" in json.dumps(data).lower()
            print(f"  custom-domain {name}: http={st} {'OK' if st in (200, 201) else ('exists' if already else json.dumps(data)[:200])}")

    elif cmd == "status":
        sid = sys.argv[2] if len(sys.argv) > 2 else SERVICE_ID
        st, data = req(f"https://api.render.com/v1/services/{sid}/custom-domains", headers=render_h())
        for item in (data if isinstance(data, list) else []):
            cd = item.get("customDomain", item)
            print(f"  {cd.get('name')}: verified={cd.get('verificationStatus')} resolves={cd.get('domainResolves')}")

    elif cmd == "env":
        sid = sys.argv[2] if len(sys.argv) > 2 else SERVICE_ID
        ga = sys.argv[3] if len(sys.argv) > 3 else ""
        idx = sys.argv[4] if len(sys.argv) > 4 else ""
        for k, v in [("CLI_GA_ID", ga), ("CLI_INDEXNOW_KEY", idx)]:
            if not v:
                continue
            st, data = req(f"https://api.render.com/v1/services/{sid}/env-vars/{k}", method="PUT",
                           headers=render_h(), data={"value": v})
            print(f"  set {k}={v}: http={st} {'OK' if st in (200, 201) else json.dumps(data)[:200]}")

    elif cmd == "deploy":
        sid = sys.argv[2] if len(sys.argv) > 2 else SERVICE_ID
        st, data = req(f"https://api.render.com/v1/services/{sid}/deploys", method="POST",
                       headers=render_h(), data={"clearCache": "do_not_clear"})
        print(f"  deploy http={st} id={data.get('id', '')}")
