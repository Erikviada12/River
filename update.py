import json, os, urllib.request
from datetime import datetime, timezone, timedelta

KEY = os.environ["API_FOOTBALL_KEY"]
TEAM, LEAGUE, SEASON = 435, 128, 2026  # River Plate, Liga Profesional, temporada
BASE = "https://v3.football.api-sports.io"
DIAS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]

def api(path):
    req = urllib.request.Request(BASE + path, headers={"x-apisports-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

try:
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {}

fx = api(f"/fixtures?team={TEAM}&season={SEASON}&league={LEAGUE}")["response"]
if not fx:
    raise SystemExit("La API no devolvió partidos; se deja data.json como estaba.")

ar = timezone(timedelta(hours=-3))
done = sorted([x for x in fx if x["fixture"]["status"]["short"] in ("FT","AET","PEN")],
              key=lambda x: x["fixture"]["timestamp"], reverse=True)
todo = sorted([x for x in fx if x["fixture"]["status"]["short"] in ("NS","TBD","PST")],
              key=lambda x: x["fixture"]["timestamp"])

res = []
for x in done[:5]:
    home = x["teams"]["home"]["id"] == TEAM
    gh, ga = x["goals"]["home"], x["goals"]["away"]
    mine, theirs = (gh, ga) if home else (ga, gh)
    rival = x["teams"]["away" if home else "home"]["name"]
    d = datetime.fromtimestamp(x["fixture"]["timestamp"], ar)
    res.append({"f": d.strftime("%d/%m"), "rival": f"{rival} ({'L' if home else 'V'})",
                "marcador": f"{mine}-{theirs}", "r": "G" if mine > theirs else "E" if mine == theirs else "P"})
data["resultados"] = res

if todo:
    x = todo[0]
    d = datetime.fromtimestamp(x["fixture"]["timestamp"], ar)
    h, a = x["teams"]["home"]["name"], x["teams"]["away"]["name"]
    data["proximo"] = {"titulo": f"{h} vs. {a}",
        "info": f"{x['league']['round']} · {x['fixture']['venue'].get('name') or ''} · {DIAS[d.weekday()]} {d.strftime('%d/%m')} a las {d.strftime('%H:%M')}"}
else:
    data["proximo"] = {"titulo": "Sin partidos programados", "info": ""}

try:
    st = api(f"/standings?league={LEAGUE}&season={SEASON}")["response"][0]["league"]["standings"]
    rows = [r for g in st for r in g if r["team"]["id"] == TEAM]
    if rows:
        r = rows[-1]
        a = r["all"]
        data["pos"] = {"puesto": f"{r['rank']}.º", "pts": r["points"], "pj": a["played"], "dg": f"{r['goalsDiff']:+d}"}
        data["posNota"] = f"{a['win']} ganados, {a['draw']} empatados y {a['lose']} perdidos."
except Exception as e:
    print("No se pudo actualizar la tabla:", e)

data["actualizado"] = datetime.now(ar).strftime("%d/%m/%Y")
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("data.json actualizado")
