"""Doc 39 figure: bought-in parts per turbine (ex-works, excl. tower, foundation, site). Run after cost_m8.py logic (imports it)."""
import io, contextlib, re
with contextlib.redirect_stdout(io.StringIO()):
    import cost_m8 as C
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

items = []
for r in C.rows:
    if r["sub"].startswith(("8 ", "11", "12")): continue
    v = r["bought"] + (r["mat"] if r["pid"] == "NP1-220F" else 0)   # magnets are bought, booked as material
    if v <= 0: continue
    name = re.sub(r"\s+—.*$", "", r["name"])
    while len(name) > 46 and re.search(r"[,:(+]", name[:46]):
        name = re.split(r"\s*[,:(+][^,:(+]*$", name)[0]
    name = re.sub(r"\s*[:(]\s*[^:()]*$", "", name) if re.search(r"[:(][^)]*$", name) else name
    name = {"Converter": "Active rectifier parts (SiC, DC link)", "Blade": "Blade consumables, erosion tape, LPS",
            "Coils": "Coil insulation, wedges, sleeving", "Cabinet internals": "Base cabinet internals (SPD, RCD, heater)"}.get(name, name)[:46]
    if r["qty"] > 1 and r["unit"] == "pc": name = f"{r['qty']:g} × {name}"
    items.append((v, name, r["sub"]))
# group fasteners, cables, tooling
def grp(label, test):
    global items
    g = [i for i in items if test(i)]; items = [i for i in items if not test(i)]
    if g: items.append((sum(i[0] for i in g), label, g[0][2]))
grp("Fasteners (all bolts, nuts, kits)", lambda i: i[1].startswith(("Bolt", "HV set", "Nut", "Small fasteners")))
grp("Cables (generator, signal, yaw, brake)", lambda i: i[1].startswith("Cable"))
grp("Tooling bought-in, ÷ 50 turbines", lambda i: i[2].startswith("10"))
items.sort(reverse=True)
N = 30
top, rest = items[:N], items[N:]
top.append((sum(i[0] for i in rest), f"Other {len(rest)} bought items", ""))
total = sum(i[0] for i in items)

subs = {}
for v, n, s in items:
    if s: subs[s] = subs.get(s, 0) + v
SUBMAP = {"1 Blades": "Blades", "2 Hub and pitch": "Hub and pitch", "3 Generator": "Generator (incl. magnets)", "4 Spindle and brake": "Spindle and brake",
          "5 Nacelle and bedplate": "Nacelle", "6 Yaw": "Yaw", "7 Electrical and power electronics": "Electrical and power electronics",
          "9 Final assembly and test": "Final assembly", "10 Tooling (written off)": "Tooling (÷ 50)"}
sl = sorted(subs.items(), key=lambda kv: -kv[1])

BLUE, INK, INK2, GRID, BG = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig = plt.figure(figsize=(13, 10.5), facecolor=BG)
gs = fig.add_gridspec(2, 1, height_ratios=[len(sl), len(top)], hspace=0.22)
def bars(ax, labels, vals, title):
    ax.set_facecolor(BG)
    y = range(len(vals))[::-1]
    ax.barh(list(y), vals, color=BLUE, height=0.62, edgecolor=BG, linewidth=2)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, color=INK)
    m = max(vals)
    for yy, v in zip(y, vals):
        ax.text(v + m * 0.01, yy, f"€{v:,.0f}  ({100*v/total:.0f} %)", va="center", color=INK2, fontsize=9)
    ax.set_xlim(0, m * 1.2)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID); ax.tick_params(axis="y", length=0); ax.tick_params(axis="x", colors=INK2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"€{x/1000:.0f}k"))
    ax.set_title(title, loc="left", color=INK, fontsize=11.5, fontweight="bold")
bars(fig.add_subplot(gs[0]), [SUBMAP.get(k, k) for k, _ in sl], [v for _, v in sl], "By subsystem")
bars(fig.add_subplot(gs[1]), [n for _, n, _ in top], [v for v, _, _ in top], "Largest bought-in items")
fig.suptitle(f"12 kW M8 — bought-in parts per turbine: €{total:,.0f} (excl. tower, foundation, site)", x=0.01, ha="left", y=0.995,
             fontsize=14, fontweight="bold", color=INK)
fig.text(0.01, 0.005, "Doc 39 estimates, 2026 list-level prices, not supplier quotes. Magnets included (bought, NdFeB N45SH €150/kg). "
         "Power electronics lines = component cost only.", color=INK2, fontsize=8.5)
fig.subplots_adjust(left=0.30, right=0.97, top=0.95, bottom=0.05)
fig.savefig(C.OUT / "B01-bought-in.png", dpi=150, facecolor=BG)
print(round(total), [(round(v), n) for v, n, _ in top])
