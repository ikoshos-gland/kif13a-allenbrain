"""Re-derive every number in the workbook from the source tables and compare.

Reopens the saved Kif13a_sonuclar.xlsx, locates each table by its caption, and
recomputes the values independently: group means and deltas straight from the 97
donor rows, the statistics with scipy rather than from the derived file, all 13
partition values, the spread and variance tests, the Spearman coefficients, the
ranking order and totals, and the detection identity.

Prints the number of checks and any mismatch. Exits non-zero on mismatch.
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy import stats

# Windows consoles default to a legacy code page, which mangles the Turkish
# labels this script prints. Force UTF-8 where the stream supports it.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
BOOK = ROOT / "Kif13a_sonuclar.xlsx"

wb = load_workbook(BOOK, data_only=True)
fails = []
checks = 0


def chk(name, got, exp, tol=1e-6):
    global checks
    checks += 1
    if isinstance(exp, float) and isinstance(got, (int, float)):
        ok = abs(got - exp) <= tol
    else:
        ok = got == exp
    if not ok:
        fails.append("{0}: excel={1} beklenen={2}".format(name, got, exp))


def grab(sheet, caption):
    """Return the table written under a caption as a dataframe of raw values."""
    ws = wb[sheet]
    start = None
    for row in ws.iter_rows():
        for c in row:
            if c.value == caption:
                start = c.row
                break
        if start:
            break
    assert start, "caption bulunamadi: " + caption
    hdr = [c.value for c in ws[start + 1] if c.value is not None]
    rows = []
    r = start + 2
    while True:
        vals = [ws.cell(row=r, column=j).value for j in range(1, len(hdr) + 1)]
        if all(v is None for v in vals):
            break
        rows.append(vals)
        r += 1
    return pd.DataFrame(rows, columns=hdr)


SHEETS = ["Özet tablolar", "Yaşlanma sonucu", "Yaşlanma donörler", "Bölgesel 13 parça",
          "Yaşlanma bölge", "Kohort tekrarı", "Tüm beyin sıralaması",
          "Tespit vs seviye", "Veri seti"]
chk("sayfa listesi", wb.sheetnames, SHEETS)
chk("acilis sayfasi", wb.active.title, "Özet tablolar")

donors = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv")
rank = pd.read_csv(RESULTS / "derived_wholebrain_subclass_ranking.csv")

# --- aging result, recomputed from the donor rows on both sheets that carry it
for sheet in ("Özet tablolar", "Yaşlanma sonucu"):
    t = grab(sheet, "Genç ve yaşlı farelerde Kif13a, donör düzeyi")
    for label, sc in [("Olgun oligodendrosit", "327 Oligo NN"), ("OPC (öncül)", "326 OPC NN")]:
        s = donors[donors.subclass_name == sc]
        ad = s[s.donor_age_category == "adult"].mean_Kif13a
        ag = s[s.donor_age_category == "aged"].mean_Kif13a
        row = t[t["Hücre tipi"] == label].iloc[0]
        chk(f"{sheet}/{sc} genç", row["Genç ortalama (log2)"], float(ad.mean()), 1e-5)
        chk(f"{sheet}/{sc} yaşlı", row["Yaşlı ortalama (log2)"], float(ag.mean()), 1e-5)
        chk(f"{sheet}/{sc} fark", row["Fark (log2)"], float(ag.mean() - ad.mean()), 1e-5)
        chk(f"{sheet}/{sc} kat", row["Kat değişim"], float(2 ** (ag.mean() - ad.mean())), 1e-5)
        if "Mann-Whitney p" in t.columns:
            _, p = stats.mannwhitneyu(ag, ad, alternative="two-sided")
            chk(f"{sheet}/{sc} MW p", row["Mann-Whitney p"], float(p))
            _, pt = stats.ttest_ind(ag, ad, equal_var=False)
            chk(f"{sheet}/{sc} Welch p", row["Welch t p"], float(pt))
            gt = sum(x > y for x in ag for y in ad)
            lt = sum(x < y for x in ag for y in ad)
            chk(f"{sheet}/{sc} Cliff", row["Cliff delta"], (gt - lt) / (len(ag) * len(ad)))

# --- donor counts
u = donors.drop_duplicates("donor_label")
g = grab("Yaşlanma donörler", "Grupların özeti")
chk("genç fare", int(g[g.Grup == "Genç yetişkin"]["Fare sayısı"].iloc[0]),
    int((u.donor_age_category == "adult").sum()))
chk("yaşlı fare", int(g[g.Grup == "Yaşlı"]["Fare sayısı"].iloc[0]),
    int((u.donor_age_category == "aged").sum()))
for cap, cat in [("Genç yetişkin grubu, yaşa göre fare sayısı", "adult"),
                 ("Yaşlı grup, yaşa göre fare sayısı", "aged")]:
    tt = grab("Yaşlanma donörler", cap)
    n = int((u.donor_age_category == cat).sum())
    chk(f"{cat} yaş tablosu toplamı", int(tt["Fare"].sum()), n)
    chk(f"{cat} dişi+erkek", int(tt["Dişi"].sum() + tt["Erkek"].sum()), n)

# --- 13 partitions
w = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
opc = w[w.subclass == "326 OPC NN"].set_index("region").mean_Kif13a
oli = w[w.subclass == "327 Oligo NN"].set_index("region").mean_Kif13a
rt = grab("Bölgesel 13 parça", "13 parçada OPC ve olgun oligodendrosit")
chk("parça sayısı", len(rt), 13)
for _, row in rt.iterrows():
    p = row["Parça"]
    chk(f"{p} OPC", row["OPC ortalama"], float(opc[p]))
    chk(f"{p} Oligo", row["Oligo ortalama"], float(oli[p]))
    chk(f"{p} fark", row["Oligo - OPC"], float(oli[p] - opc[p]))

sp = grab("Bölgesel 13 parça", "Yayılım karşılaştırması").set_index("Ölçüt")
chk("OPC aralık", sp.loc["Aralık", "OPC"], float(opc.max() - opc.min()))
chk("Oligo aralık", sp.loc["Aralık", "Oligo"], float(oli.max() - oli.min()))
chk("OPC SD", sp.loc["Standart sapma", "OPC"], float(opc.std(ddof=1)))
chk("Oligo SD", sp.loc["Standart sapma", "Oligo"], float(oli.std(ddof=1)))
chk("SD oranı", sp.loc["Standart sapma", "Oran (OPC/Oligo)"],
    float(opc.std(ddof=1) / oli.std(ddof=1)))

F = opc.var(ddof=1) / oli.var(ddof=1)
pf = 2 * min(stats.f.cdf(F, 12, 12), 1 - stats.f.cdf(F, 12, 12))
lev = stats.levene(opc.values, oli.values, center="median")
ts = grab("Bölgesel 13 parça", "İstatistik testleri").set_index("Test")
chk("F istatistiği", round(float(ts.loc["Varyans oranı (F testi)", "İstatistik"]), 2), round(float(F), 2))
chk("F p", round(float(ts.loc["Varyans oranı (F testi)", "p değeri"]), 6), round(float(pf), 6))
chk("Levene W", round(float(ts.loc["Levene (Brown-Forsythe)", "İstatistik"]), 2),
    round(float(lev.statistic), 2))
CTX = ["HPF", "Isocortex-1", "Isocortex-2", "CTXsp", "OLF"]
HB = ["P", "MY", "CB"]
chk("OPC korteks-arka beyin p",
    round(float(ts.loc["Korteks+HPF vs arka beyin, OPC", "p değeri"]), 4),
    round(float(stats.mannwhitneyu(opc[CTX], opc[HB], alternative="greater").pvalue), 4))
chk("OPC korteks-arka beyin fark",
    round(float(ts.loc["Korteks+HPF vs arka beyin, OPC", "Fark (log2)"]), 3),
    round(float(opc[CTX].mean() - opc[HB].mean()), 3))

# --- Spearman captions
w2 = w.copy()
ag2 = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")
w2["division"] = w2.region.replace({"Isocortex-1": "Isocortex", "Isocortex-2": "Isocortex"})
w2["prod"] = w2.mean_Kif13a * w2.n_cells
wm = w2.groupby(["division", "subclass"], as_index=False).agg(prod=("prod", "sum"), n=("n_cells", "sum"))
wm["ref"] = wm["prod"] / wm["n"]
adult_reg = (ag2[ag2.donor_age_category == "adult"]
             .rename(columns={"anatomical_division_label": "division",
                              "subclass_name": "subclass", "mean_Kif13a": "aging"})
             [["division", "subclass", "aging"]])
mg = wm.merge(adult_reg, on=["division", "subclass"])
for sc, label, rho in [("326 OPC NN", "OPC", 0.964), ("327 Oligo NN", "Olgun oligodendrosit", 0.893)]:
    s = mg[mg.subclass == sc]
    got, _ = stats.spearmanr(s.ref, s.aging)
    chk(f"{label} Spearman rho", rho, round(float(got), 3))
    t = grab("Kohort tekrarı", "{0} (Spearman rho = {1:+.3f}, p = {2})".format(
        label, rho, 0.0005 if sc == "326 OPC NN" else 0.0068))
    chk(f"{label} bölge sayısı", len(t), 7)

# --- ranking and the three label tables, on both sheets that carry them
TOP = {1: "327 Oligo NN", 2: "326 OPC NN", 3: "145 MH Tac2 Glut", 10: "129 VMH Nr5a1 Glut"}
GLIA = {"Olgun oligodendrosit": "327 Oligo NN", "OPC": "326 OPC NN",
        "Astrosit (telensefalik)": "319 Astro-TE NN", "Mikroglia": "334 Microglia NN",
        "Endotel": "333 Endo NN", "Perisit": "331 Peri NN"}
LOW = {"OB Trdn Gaba": "040 OB Trdn Gaba", "OB-out Frmd7 Gaba": "042 OB-out Frmd7 Gaba",
       "OB-STR-CTX Inh IMN": "045 OB-STR-CTX Inh IMN", "OB-in Frmd7 Gaba": "041 OB-in Frmd7 Gaba",
       "Sncg Gaba (korteks)": "047 Sncg Gaba", "Vip Gaba (korteks)": "046 Vip Gaba"}

for sheet in ("Özet tablolar", "Tüm beyin sıralaması"):
    top = grab(sheet, "En yüksek 10 hücre tipi")
    chk(f"{sheet} top10 satır", len(top), 10)
    chk(f"{sheet} top10 sıra", list(top["Sıra"]), list(range(1, 11)))
    for _, row in top.iterrows():
        src = rank.iloc[int(row["Sıra"]) - 1]
        chk(f"{sheet} top10 {row['Sıra']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
        chk(f"{sheet} top10 {row['Sıra']} hücre", int(row["Hücre"]), int(src.n_cells))
    for pos, key in TOP.items():
        chk(f"{sheet} top10 sıra {pos} kimlik", rank.iloc[pos - 1].subclass, key)

    gl = grab(sheet, "Glia tipleri karşılaştırması")
    chk(f"{sheet} glia satır", len(gl), 6)
    for _, row in gl.iterrows():
        src = rank[rank.subclass == GLIA[row["Hücre tipi"]]].iloc[0]
        chk(f"{sheet} glia {row['Hücre tipi']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
        chk(f"{sheet} glia {row['Hücre tipi']} oran", row["İfade eden oran"],
            float(src.fraction_expressing), 1e-9)

    lo = grab(sheet, "En düşük hücreler")
    chk(f"{sheet} en düşük satır", len(lo), 6)
    prev = -1.0
    for _, row in lo.iterrows():
        src = rank[rank.subclass == LOW[row["Alt sınıf"]]].iloc[0]
        chk(f"{sheet} düşük {row['Alt sınıf']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
        chk(f"{sheet} düşük {row['Alt sınıf']} oran", row["İfade eden oran"],
            float(src.fraction_expressing), 1e-9)
        if row["Ortalama (log2)"] < prev:
            fails.append(f"{sheet}: en düşük tablosu artan sırada değil")
        prev = row["Ortalama (log2)"]
    chk(f"{sheet} en düşük gerçekten dip", lo.iloc[0]["Ortalama (log2)"],
        float(rank.mean_Kif13a.min()), 1e-9)

fr = grab("Tüm beyin sıralaması", "Tam sıralama, 265 alt sınıf")
chk("tam sıralama satır", len(fr), len(rank))
chk("tam sıralama toplam hücre", int(fr["Hücre"].sum()), int(rank.n_cells.sum()))
chk("tam sıralama ilk", fr.iloc[0]["Alt sınıf"], rank.iloc[0].subclass)
chk("tam sıralama son", fr.iloc[-1]["Alt sınıf"], rank.iloc[-1].subclass)

# --- detection identity: mean over all cells = fraction * mean over expressing
dv = grab("Tespit vs seviye", "Tespit oranı ile ifade seviyesinin ayrılması")
for _, row in dv.iterrows():
    recon = np.log2(row["Tespit edilende seviye (CPM)"] + 1) * row["Tespit oranı"]
    chk("{0} özdeşlik".format(row["Alt sınıf"]), round(float(recon), 2),
        round(float(row["Ortalama (log2, sıfırlar dahil)"]), 2), 0.02)

# --- dataset sheet
part = grab("Veri seti", "Parçalara göre hücre dağılımı")
chk("parça toplam hücre", int(part["Hücre"].sum()), 2341350)
chk("parça satır", len(part), 13)

# --- no mojibake anywhere
bad = 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and ("�" in c.value or "Ã" in c.value):
                bad += 1
chk("bozuk karakterli hücre", bad, 0)

print("Sayfa sayısı:", len(wb.sheetnames))
print("Kontrol sayısı:", checks)
print()
if fails:
    print("UYUŞMAZLIK:", len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("Tüm kontroller geçti, uyuşmazlık yok.")
