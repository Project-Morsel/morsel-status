"""Preview the built status page with fixture data, and screenshot it.

    pip install playwright && python -m playwright install chromium
    tools/build-site.sh
    python3 tools/preview.py site/status-page/__sapper__/export up /tmp/status-up 390 1280

Requests to status.projectmorsel.com are served from the build. GitHub's API and
raw.githubusercontent.com are answered from fixtures, so no real incident is needed.
Scenarios: up (this repository's summary), degraded, down (with an open incident), resolved
(past incidents), nohistory, apifail, ratelimit. Add -v to list requests and
--path /history/morsel-service or /incident/5 for other pages, --text200 to double the
text size, --tab to list the first keyboard stops. Prints, per width, the final
address, any horizontal overflow in pixels and page errors.
"""
import asyncio, json, sys, mimetypes, pathlib, copy, re
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

export = pathlib.Path(sys.argv[1]); scenario = sys.argv[2]; out = sys.argv[3]
args = sys.argv[4:]
path = "/"
if "--path" in args:
    i = args.index("--path"); path = args[i+1]; args = args[:i] + args[i+2:]
widths = [int(a) for a in args if a.isdigit()] or [1280, 390]
repo = pathlib.Path(__file__).resolve().parents[1]
real = json.loads((repo / "history/summary.json").read_text())

def issue(n, title, state, created, closed=None, labels=("status",), comments=1, body=""):
    return {"number": n, "title": title, "state": state, "created_at": created, "closed_at": closed,
            "comments": comments, "body": body, "html_url": f"https://github.com/Project-Morsel/morsel-status/issues/{n}",
            "labels": [{"name": l} for l in labels], "user": {"login": "upptime-bot"}, "locked": False}

summary = copy.deepcopy(real); open_issues = []; closed = []; api_fail = None
if scenario == "degraded":
    summary[0]["status"] = "degraded"
elif scenario == "down":
    summary[0]["status"] = "down"; summary[0]["uptimeDay"] = "97.90%"
    open_issues = [issue(7, "🛑 Morsel service is down", "open", "2026-11-21T13:10:00Z")]
elif scenario == "resolved":
    closed = [issue(5, "🛑 Web app is down", "closed", "2026-11-21T11:00:00Z", "2026-11-21T11:22:00Z", comments=2),
              issue(3, "⚠️ Morsel service has degraded performance", "closed", "2026-11-20T09:00:00Z", "2026-11-20T09:15:00Z")]
elif scenario == "nohistory":
    summary = []
elif scenario == "apifail":
    api_fail = 500
elif scenario == "ratelimit":
    api_fail = 403

CORS = {"content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "GET, OPTIONS"}

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        for w in widths:
            ctx = await b.new_context(viewport={"width": w, "height": 844 if w < 500 else 900}, service_workers="block")
            page = await ctx.new_page()
            errors = []
            page.on("console", lambda m: errors.append("console: " + m.text[:200]))
            page.on("requestfailed", lambda q: errors.append("failed: " + q.url[:100] + " " + str(q.failure)))
            page.on("pageerror", lambda e: errors.append(str(e) + " @ " + (e.stack or "")[:400]))
            async def route(r):
                u = urlparse(r.request.url)
                if "-v" in sys.argv: print(r.request.method, r.request.url[:140])
                if u.hostname != "status.projectmorsel.com" and r.request.method == "OPTIONS":
                    await r.fulfill(status=204, headers=CORS); return
                if u.hostname == "status.projectmorsel.com":
                    f = export / u.path.lstrip("/")
                    if f.is_dir(): f = f / "index.html"
                    if not f.exists():
                        f = export / "404.html"
                    await r.fulfill(path=str(f), content_type=mimetypes.guess_type(str(f))[0] or "text/html")
                elif u.hostname == "raw.githubusercontent.com":
                    if u.path.endswith("summary.json"):
                        await r.fulfill(headers=CORS, json=summary)
                    elif "/graphs/" in u.path:
                        f = repo / "graphs" / u.path.split("/graphs/")[1]
                        if f.exists(): await r.fulfill(path=str(f), content_type="image/png", headers={"access-control-allow-origin": "*"})
                        else: await r.fulfill(status=404, body="")
                    else:
                        await r.fulfill(status=404, body="")
                elif u.hostname == "api.github.com":
                    if api_fail:
                        msg = "API rate limit exceeded for 1.2.3.4." if api_fail == 403 else "Server Error"
                        await r.fulfill(status=api_fail, headers=CORS, json={"message": msg}); return
                    q = parse_qs(u.query)
                    if u.path.endswith("/issues"):
                        state = q.get("state", ["open"])[0]; label = q.get("labels", [""])[0]
                        if label == "maintenance": await r.fulfill(headers=CORS, json=[]); return
                        await r.fulfill(headers=CORS, json=open_issues if state == "open" else closed)
                    elif re.search(r"/issues/\d+/comments", u.path):
                        await r.fulfill(headers=CORS, json=[{"id": 1, "body": "Investigating. Records may be unavailable for a few minutes.", "created_at": "2026-11-21T13:12:00Z", "user": {"login": "hs737"}}])
                    elif re.search(r"/issues/\d+$", u.path):
                        n = int(u.path.rsplit("/", 1)[1])
                        found = [i for i in open_issues + closed if i["number"] == n]
                        await r.fulfill(headers=CORS, json=found[0] if found else {"message": "Not Found"}, status=200 if found else 404)
                    elif u.path.endswith("/commits"):
                        await r.fulfill(headers=CORS, json=[])
                    else:
                        await r.fulfill(headers=CORS, json=[])
                else:
                    await r.abort()
            await page.route("**/*", route)
            await page.goto("https://status.projectmorsel.com" + path)
            await page.wait_for_timeout(2500)
            if "--text200" in sys.argv:
                await page.evaluate("document.documentElement.style.fontSize = '200%'")
                await page.wait_for_timeout(300)
            if "--tab" in sys.argv:
                stops = []
                for _ in range(8):
                    await page.keyboard.press("Tab")
                    stops.append(await page.evaluate("(document.activeElement.textContent || document.activeElement.id || document.activeElement.tagName).trim().slice(0, 30)"))
                print("tab stops:", stops)
            over = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            await page.screenshot(path=f"{out}-{w}.png", full_page=True)
            await page.screenshot(path=f"{out}-{w}-fold.png", full_page=False)
            print(w, "url", page.url, "overflow", over, "errors", errors[:8])
            await ctx.close()
        await b.close()
asyncio.run(main())
