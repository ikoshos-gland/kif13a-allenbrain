import pandas as pd, numpy as np
from openpyxl import load_workbook
from scipy import stats
from pathlib import Path
R = Path("results")
wb = load_workbook("Kif13a_sonuclar.xlsx", data_only=True)
fails = []


def grab(sheet, caption):
    """Return the table under a caption as a dataframe of raw cell values."""
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


checks = 0


def chk(name, got, exp, tol=1e-6):
    global checks
    checks += 1
    ok = abs(got - exp) <= tol if isinstance(exp, float) else got == exp
    if not ok:
        fails.append(f"{name}: excel={got} beklenen={exp}")
    return ok


# 1. aging main result, recomputed from the donor table, not from the derived file
dl = pd.read_csv(R / "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv")
t = grab("Yaslanma sonucu", "Genc ve yasli farelerde Kif13a, donor duzeyi")
for xl_name, sc in [("Olgun oligodendrosit", "327 Oligo NN"), ("OPC (oncul)", "326 OPC NN")]:
    s = dl[dl.subclass_name == sc]
    ad = s[s.donor_age_category == "adult"].mean_Kif13a
    ag = s[s.donor_age_category == "aged"].mean_Kif13a
    row = t[t["Hucre tipi"] == xl_name].iloc[0]
    chk(f"{sc} genc ort", row["Genc ortalama (log2)"], float(ad.mean()), 1e-5)
    chk(f"{sc} yasli ort", row["Yasli ortalama (log2)"], float(ag.mean()), 1e-5)
    chk(f"{sc} fark", row["Fark (log2)"], float(ag.mean() - ad.mean()), 1e-5)
    chk(f"{sc} kat", row["Kat degisim"], float(2 ** (ag.mean() - ad.mean())), 1e-5)
    _, p = stats.mannwhitneyu(ag, ad, alternative="two-sided")
    chk(f"{sc} MW p", row["Mann-Whitney p"], float(p), 1e-6)
    _, pt = stats.ttest_ind(ag, ad, equal_var=False)
    chk(f"{sc} Welch p", row["Welch t p"], float(pt), 1e-6)
    gt = sum(x > y for x in ag for y in ad); lt = sum(x < y for x in ag for y in ad)
    chk(f"{sc} Cliff", row["Cliff delta"], (gt - lt) / (len(ag) * len(ad)), 1e-6)

# 2. donor counts
u = dl.drop_duplicates("donor_label")
g = grab("Yaslanma donorler", "Gruplarin ozeti")
chk("genc fare", int(g[g.Grup == "Genc yetiskin"]["Fare sayisi"].iloc[0]),
    int((u.donor_age_category == "adult").sum()))
chk("yasli fare", int(g[g.Grup == "Yasli"]["Fare sayisi"].iloc[0]),
    int((u.donor_age_category == "aged").sum()))
for cap, cat in [("Genc yetiskin grubu, yasa gore fare sayisi", "adult"),
                 ("Yasli grup, yasa gore fare sayisi", "aged")]:
    tt = grab("Yaslanma donorler", cap)
    chk(f"{cat} yas tablosu toplami", int(tt["Fare"].sum()),
        int((u.donor_age_category == cat).sum()))
    chk(f"{cat} D+E toplami", int(tt["Disi"].sum() + tt["Erkek"].sum()),
        int((u.donor_age_category == cat).sum()))

# 3. regional table
w = pd.read_csv(R / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
opc = w[w.subclass == "326 OPC NN"].set_index("region").mean_Kif13a
oli = w[w.subclass == "327 Oligo NN"].set_index("region").mean_Kif13a
rt = grab("Bolgesel 13 parca", "13 parcada OPC ve olgun oligodendrosit")
chk("parca sayisi", len(rt), 13)
for _, row in rt.iterrows():
    p = row["Parca"]
    chk(f"{p} OPC", row["OPC ortalama"], float(opc[p]), 1e-6)
    chk(f"{p} Oligo", row["Oligo ortalama"], float(oli[p]), 1e-6)
    chk(f"{p} fark", row["Oligo - OPC"], float(oli[p] - opc[p]), 1e-6)
sp = grab("Bolgesel 13 parca", "Yayilim karsilastirmasi").set_index("Olcut")
chk("OPC aralik", sp.loc["Aralik", "OPC"], float(opc.max() - opc.min()), 1e-6)
chk("Oligo aralik", sp.loc["Aralik", "Oligo"], float(oli.max() - oli.min()), 1e-6)
chk("OPC SD", sp.loc["Standart sapma", "OPC"], float(opc.std(ddof=1)), 1e-6)
chk("Oligo SD", sp.loc["Standart sapma", "Oligo"], float(oli.std(ddof=1)), 1e-6)
chk("SD orani", sp.loc["Standart sapma", "Oran (OPC/Oligo)"],
    float(opc.std(ddof=1) / oli.std(ddof=1)), 1e-6)
F = opc.var(ddof=1) / oli.var(ddof=1)
pf = 2 * min(stats.f.cdf(F, 12, 12), 1 - stats.f.cdf(F, 12, 12))
ts = grab("Bolgesel 13 parca", "Istatistik testleri").set_index("Test")
chk("F istatistigi", round(float(ts.loc["Varyans orani (F testi)", "Istatistik"]), 2), round(float(F), 2))
chk("F p", round(float(ts.loc["Varyans orani (F testi)", "p degeri"]), 6), round(float(pf), 6))
lev = stats.levene(opc.values, oli.values, center="median")
chk("Levene W", round(float(ts.loc["Levene (Brown-Forsythe)", "Istatistik"]), 2), round(float(lev.statistic), 2))
CTX = ["HPF", "Isocortex-1", "Isocortex-2", "CTXsp", "OLF"]; HB = ["P", "MY", "CB"]
chk("OPC ctx-hb p", round(float(ts.loc["Korteks+HPF vs arka beyin, OPC", "p degeri"]), 4),
    round(float(stats.mannwhitneyu(opc[CTX], opc[HB], alternative="greater").pvalue), 4))
chk("OPC ctx-hb fark", round(float(ts.loc["Korteks+HPF vs arka beyin, OPC", "Fark (log2)"]), 3),
    round(float(opc[CTX].mean() - opc[HB].mean()), 3))

# 4. ranking
rk = pd.read_csv(R / "derived_wholebrain_subclass_ranking.csv")
fr = grab("Tum beyin siralamasi", "Tam siralama, 265 alt sinif")
chk("siralama satir", len(fr), len(rk))
chk("1. sira", fr.iloc[0]["Alt sinif"], rk.iloc[0].subclass)
chk("1. sira ort", fr.iloc[0]["Ortalama (log2)"], float(rk.iloc[0].mean_Kif13a), 1e-6)
chk("son sira", fr.iloc[-1]["Alt sinif"], rk.iloc[-1].subclass)
chk("toplam hucre", int(fr["Hucre"].sum()), int(rk.n_cells.sum()))
top = grab("Tum beyin siralamasi", "En yuksek 10 hucre tipi")
chk("top10 satir", len(top), 10)
for _, row in top.iterrows():
    src = rk.iloc[int(row["Sira"]) - 1]
    chk(f"top10 sira {row['Sira']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
    chk(f"top10 sira {row['Sira']} hucre", int(row["Hucre"]), int(src.n_cells))
chk("top10 sira artan", list(top["Sira"]), list(range(1, 11)))

GLIA = {"Olgun oligodendrosit": "327 Oligo NN", "OPC": "326 OPC NN",
        "Astrosit (telensefalik)": "319 Astro-TE NN", "Mikroglia": "334 Microglia NN",
        "Endotel": "333 Endo NN", "Perisit": "331 Peri NN"}
gl = grab("Tum beyin siralamasi", "Glia tipleri karsilastirmasi")
chk("glia satir", len(gl), 6)
for _, row in gl.iterrows():
    src = rk[rk.subclass == GLIA[row["Hucre tipi"]]].iloc[0]
    chk(f"glia {row['Hucre tipi']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
    chk(f"glia {row['Hucre tipi']} oran", row["Ifade eden oran"], float(src.fraction_expressing), 1e-9)

LOW = {"OB Trdn Gaba": "040 OB Trdn Gaba", "OB-out Frmd7 Gaba": "042 OB-out Frmd7 Gaba",
       "OB-STR-CTX Inh IMN": "045 OB-STR-CTX Inh IMN", "OB-in Frmd7 Gaba": "041 OB-in Frmd7 Gaba",
       "Sncg Gaba (korteks)": "047 Sncg Gaba", "Vip Gaba (korteks)": "046 Vip Gaba"}
lo = grab("Tum beyin siralamasi", "En dusuk hucreler")
chk("en dusuk satir", len(lo), 6)
prev = -1.0
for _, row in lo.iterrows():
    src = rk[rk.subclass == LOW[row["Alt sinif"]]].iloc[0]
    chk(f"dusuk {row['Alt sinif']} ort", row["Ortalama (log2)"], float(src.mean_Kif13a), 1e-9)
    chk(f"dusuk {row['Alt sinif']} oran", row["Ifade eden oran"], float(src.fraction_expressing), 1e-9)
    if row["Ortalama (log2)"] < prev:
        fails.append("en dusuk tablosu artan sirada degil")
    prev = row["Ortalama (log2)"]
chk("en dusuk gercekten en dip", lo.iloc[0]["Ortalama (log2)"], float(rk.mean_Kif13a.min()), 1e-9)

# 5. detection vs level identity
dv = grab("Tespit vs seviye", "Tespit orani ile ifade seviyesinin ayrilmasi")
for _, row in dv.iterrows():
    lvl = row["Tespit edilende seviye (CPM)"]
    recon = np.log2(lvl + 1) * row["Tespit orani"]
    chk(f"{row['Alt sinif']} ozdeslik", round(float(recon), 2),
        round(float(row["Ortalama (log2, sifirlar dahil)"]), 2), 0.02)

# 6. dataset cell total
part = grab("Veri seti", "Parcalara gore hucre dagilimi")
chk("parca toplam hucre", int(part["Hucre"].sum()), 2341350)
chk("parca sayisi (veri seti)", len(part), 13)

print("SAYFA:", wb.sheetnames)
print("KONTROL SAYISI:", checks)
print()
if fails:
    print("!!! UYUSMAZLIK:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("TUM KONTROLLER GECTI, uyusmazlik yok.")
