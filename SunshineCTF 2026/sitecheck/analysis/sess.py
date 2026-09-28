import sys, json, re
import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://spaceship.web.2026.sunshinectf.games"
U = "h7tex_probe01"
P = "Pr0be!Passw0rd"
JAR = "session.json"


def new_session():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) SiteCheck-Probe"
    try:
        s.cookies.update(requests.utils.cookiejar_from_dict(json.load(open(JAR))))
    except Exception:
        pass
    return s


def save(s):
    json.dump({c.name: c.value for c in s.cookies}, open(JAR, "w"))


def show(r, label=""):
    print("== %s %s -> %d (%d bytes) %s" % (r.request.method, r.url, r.status_code,
                                             len(r.content), r.headers.get("content-type", "")))
    ct = r.headers.get("content-type", "")
    if "json" in ct:
        print(json.dumps(r.json(), indent=2)[:4000])
    else:
        body = r.text
        m = re.search(r"<main.*?</main>", body, re.S)
        if m:
            body = m.group(0)
        body = re.sub(r"\n\s*\n", "\n", body)
        print(body[:6000])
    print()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "register"
    s = new_session()

    if mode == "register":
        s.get(BASE + "/register")
        r = s.post(BASE + "/register", data={"username": U, "password": P}, allow_redirects=False)
        show(r, "register")
        print("Location:", r.headers.get("Location"))
        save(s)

    elif mode == "login":
        s.get(BASE + "/login")
        r = s.post(BASE + "/login", data={"username": U, "password": P}, allow_redirects=False)
        show(r, "login")
        print("Location:", r.headers.get("Location"))
        save(s)

    elif mode == "get":
        show(s.get(BASE + sys.argv[2]), "GET")
        save(s)

    elif mode == "scan":
        for i, url in enumerate(sys.argv[2:]):
            r = s.post(BASE + "/scan", data={"url": url}, timeout=90)
            show(r, "SCAN " + url)
            open("scan_%02d_%d.html" % (i, r.status_code), "w", encoding="utf-8").write(r.text)
            save(s)

    elif mode == "probe":
        import time
        for url in sys.argv[2:]:
            t0 = time.time()
            try:
                r = s.post(BASE + "/scan", data={"url": url}, timeout=90, allow_redirects=True)
            except Exception as e:
                print("ERR   %-42s %s" % (url, type(e).__name__))
                continue
            dt = time.time() - t0
            final = r.url.replace(BASE, "")
            txt = r.text
            alert = re.search(r'class="alert">(.*?)</div>', txt, re.S)
            if alert:
                print("BLOCK %-42s alert: %s" % (url, alert.group(1).strip()[:120]))
                continue

            def g(pat, t=txt):
                m = re.search(pat, t, re.S)
                return m.group(1).strip() if m else "?"
            status = g(r'Status</span><span class="v">(.*?)</span>')
            load = g(r'Load time</span><span class="v">(.*?)</span>')
            files = g(r'Files fetched</span><span class="v">(.*?)</span>')
            result = g(r'>Result</span><span class="v">(.*?)</span>')
            note = g(r'Drone note: (.*?)</div>')
            shot = re.search(r'/screenshots/([0-9a-f-]+\.png)', txt)
            print("ALLOW %-42s st=%-6s load=%-9s files=%-3s res=%-6s t=%.1fs shot=%s" %
                  (url, status, load, files, result, dt, shot.group(1) if shot else "none"))
            if note != "?":
                print("      note: " + note[:200])
            if shot:
                open("shot_" + shot.group(1), "wb").write(
                    s.get(BASE + "/screenshots/" + shot.group(1), timeout=60).content)
            save(s)
