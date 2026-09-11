"""Write the numeric tables from the analysis into a plain Excel workbook.

One sheet per topic, tables stacked with a blank row between them. Values only,
no formulas and no commentary. Output: Kif13a_sonuclar.xlsx in the repo root.
"""
from pathlib import Path
import re

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "Kif13a_sonuclar.xlsx"

FONT = "Arial"
HDR_FONT = Font(name=FONT, bold=True, size=10, color="FFFFFF")
HDR_FILL = PatternFill("solid", fgColor="44546A")
BODY = Font(name=FONT, size=10)
CAPTION = Font(name=FONT, bold=True, size=11)

F3 = "0.000"
F4 = "0.0000"
PCT = "0.0%"
INT = "#,##0"

wb = Workbook()
wb.remove(wb.active)


def put(ws, row, caption, df, fmt=None):
    """Write one captioned table. Returns the next free row."""
    ws.cell(row=row, column=1, value=caption).font = CAPTION
    row += 1
    for j, col in enumerate(df.columns, start=1):
        c = ws.cell(row=row, column=j, value=col)
        c.font, c.fill = HDR_FONT, HDR_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for _, rec in df.iterrows():
        row += 1
        for j, col in enumerate(df.columns, start=1):
            v = rec[col]
            c = ws.cell(row=row, column=j, value=None if pd.isna(v) else v)
            c.font = BODY
            if fmt and col in fmt:
                c.number_format = fmt[col]
    return row + 2


def autofit(ws, cap=44):
    for col in ws.columns:
        letter = None
        best = 0
        for c in col:
            if letter is None:
                letter = c.column_letter
            if c.value is not None:
                best = max(best, len(str(c.value)))
        if letter:
            ws.column_dimensions[letter].width = min(max(best + 2, 9), cap)


# ---------------------------------------------------------------- aging result
ws = wb.create_sheet("Yaslanma sonucu")
d = pd.read_csv(RESULTS / "derived_donor_level_age_test.csv")
d = d.set_index("subclass").reindex(["327 Oligo NN", "326 OPC NN"]).reset_index()
main = pd.DataFrame({
    "Hucre tipi": ["Olgun oligodendrosit", "OPC (oncul)"],
    "Genc ortalama (log2)": d.mean_adult.values,
    "Yasli ortalama (log2)": d.mean_aged.values,
    "Fark (log2)": d.delta_log2.values,
    "Kat degisim": d.fold_change.values,
    "Mann-Whitney p": d.mannwhitney_p.values,
    "Welch t p": d.welch_t_p.values,
    "Cliff delta": d.cliffs_delta.values,
})
r = put(ws, 1, "Genc ve yasli farelerde Kif13a, donor duzeyi", main,
        {"Genc ortalama (log2)": F3, "Yasli ortalama (log2)": F3, "Fark (log2)": "+0.000;-0.000",
         "Kat degisim": F3, "Mann-Whitney p": F4, "Welch t p": F4, "Cliff delta": "+0.000;-0.000"})

conv = pd.DataFrame({
    "Olcum": ["Oligodendrosit, genc", "Oligodendrosit, yasli", "OPC, genc", "OPC, yasli"],
    "Ortanca (log2)": [8.456, 8.717, 7.830, 7.808],
})
conv["CPM karsiligi"] = (2 ** conv["Ortanca (log2)"] - 1).round(0)
r = put(ws, r, "log2 degerlerinin CPM karsiligi (ortanca uzerinden)", conv,
        {"Ortanca (log2)": F3, "CPM karsiligi": INT})

ag = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_summary.csv")
ag = ag[["donor_age_category", "subclass_name", "n_cells", "n_donors",
         "mean_Kif13a", "median_Kif13a", "fraction_expressing"]]
ag.columns = ["Yas grubu", "Alt sinif", "Hucre", "Fare", "Ortalama (log2)",
              "Ortanca (log2)", "Ifade eden oran"]
put(ws, r, "Hucreler havuzlanmis ozet", ag,
    {"Hucre": INT, "Ortalama (log2)": F3, "Ortanca (log2)": F3, "Ifade eden oran": PCT})
autofit(ws)

# ---------------------------------------------------------------- donors
ws = wb.create_sheet("Yaslanma donorler")
dl = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv")
u = dl.drop_duplicates("donor_label").copy()


def to_days(a):
    a = str(a)
    if a.endswith("wks"):
        return int(a.split()[0]) * 7
    if a.endswith("M"):
        return int(a[:-1]) * 30
    return int(a[1:])


u["gun"] = u.donor_age.map(to_days)
grp = pd.DataFrame({
    "Grup": ["Genc yetiskin", "Yasli"],
    "Fare sayisi": [(u.donor_age_category == "adult").sum(), (u.donor_age_category == "aged").sum()],
    "En kucuk yas (gun)": [u[u.donor_age_category == "adult"].gun.min(), u[u.donor_age_category == "aged"].gun.min()],
    "En buyuk yas (gun)": [u[u.donor_age_category == "adult"].gun.max(), u[u.donor_age_category == "aged"].gun.max()],
    "Ortanca yas (gun)": [u[u.donor_age_category == "adult"].gun.median(), u[u.donor_age_category == "aged"].gun.median()],
    "Disi": [((u.donor_age_category == "adult") & (u.donor_sex == "F")).sum(),
             ((u.donor_age_category == "aged") & (u.donor_sex == "F")).sum()],
    "Erkek": [((u.donor_age_category == "adult") & (u.donor_sex == "M")).sum(),
              ((u.donor_age_category == "aged") & (u.donor_sex == "M")).sum()],
})
r = put(ws, 1, "Gruplarin ozeti", grp)

for cat, label in [("adult", "Genc yetiskin grubu, yasa gore fare sayisi"),
                   ("aged", "Yasli grup, yasa gore fare sayisi")]:
    s = u[u.donor_age_category == cat]
    t = (s.groupby(["donor_age", "gun"])
           .agg(**{"Fare": ("donor_label", "nunique"),
                   "Disi": ("donor_sex", lambda x: (x == "F").sum()),
                   "Erkek": ("donor_sex", lambda x: (x == "M").sum())})
           .reset_index().sort_values("gun"))
    t = t.rename(columns={"donor_age": "Yas etiketi", "gun": "Gun"})
    r = put(ws, r, label, t)

cells = (dl.groupby(["donor_age_category", "subclass_name"])
           .agg(**{"Fare": ("donor_label", "nunique"), "Toplam hucre": ("n_cells", "sum"),
                   "Fare basi ortanca": ("n_cells", "median"),
                   "En az": ("n_cells", "min"), "En cok": ("n_cells", "max")})
           .reset_index()
           .rename(columns={"donor_age_category": "Yas grubu", "subclass_name": "Alt sinif"}))
put(ws, r, "Fare basina hucre katkisi", cells,
    {"Toplam hucre": INT, "Fare basi ortanca": INT, "En az": INT, "En cok": INT})
autofit(ws)

# ---------------------------------------------------------------- regional
ws = wb.create_sheet("Bolgesel 13 parca")
w = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
opc = w[w.subclass == "326 OPC NN"].set_index("region")
oli = w[w.subclass == "327 Oligo NN"].set_index("region").reindex(opc.index)
reg = pd.DataFrame({
    "Parca": opc.index,
    "OPC ortalama": opc.mean_Kif13a.values,
    "Oligo ortalama": oli.mean_Kif13a.values,
    "Oligo - OPC": oli.mean_Kif13a.values - opc.mean_Kif13a.values,
    "OPC ifade oran": opc.fraction_expressing.values,
    "Oligo ifade oran": oli.fraction_expressing.values,
}).sort_values("OPC ortalama", ascending=False)
r = put(ws, 1, "13 parcada OPC ve olgun oligodendrosit", reg,
        {"OPC ortalama": F3, "Oligo ortalama": F3, "Oligo - OPC": "+0.000;-0.000",
         "OPC ifade oran": PCT, "Oligo ifade oran": PCT})

a_, b_ = reg["OPC ortalama"], reg["Oligo ortalama"]
fo, fl = reg["OPC ifade oran"], reg["Oligo ifade oran"]
spread = pd.DataFrame({
    "Olcut": ["En dusuk", "En yuksek", "Aralik", "Standart sapma",
              "Degisim katsayisi (%)", "Ifade eden oran araligi"],
    "OPC": [a_.min(), a_.max(), a_.max() - a_.min(), a_.std(ddof=1),
            100 * a_.std(ddof=1) / a_.mean(), fo.max() - fo.min()],
    "Oligo": [b_.min(), b_.max(), b_.max() - b_.min(), b_.std(ddof=1),
              100 * b_.std(ddof=1) / b_.mean(), fl.max() - fl.min()],
})
spread["Oran (OPC/Oligo)"] = spread["OPC"] / spread["Oligo"]
r = put(ws, r, "Yayilim karsilastirmasi", spread,
        {"OPC": F3, "Oligo": F3, "Oran (OPC/Oligo)": "0.00"})

tests = pd.DataFrame({
    "Test": ["Varyans orani (F testi)", "Levene (Brown-Forsythe)",
             "Korteks+HPF vs arka beyin, OPC", "Korteks+HPF vs arka beyin, Oligo"],
    "Istatistik": [9.87, 24.95, None, None],
    "Fark (log2)": [None, None, 1.335, 0.107],
    "p degeri": [0.000372, 0.00003, 0.0179, 0.1964],
})
put(ws, r, "Istatistik testleri", tests,
    {"Istatistik": "0.00", "Fark (log2)": "+0.000;-0.000", "p degeri": "0.00000"})
autofit(ws)

# ---------------------------------------------------------------- aging by region
ws = wb.create_sheet("Yaslanma bolge")
ar = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")
ar = ar[["anatomical_division_label", "donor_age_category", "subclass_name",
         "n_cells", "n_donors", "mean_Kif13a", "median_Kif13a", "fraction_expressing"]]
ar.columns = ["Bolge", "Yas grubu", "Alt sinif", "Hucre", "Fare",
              "Ortalama (log2)", "Ortanca (log2)", "Ifade eden oran"]
ar = ar.sort_values(["Alt sinif", "Bolge", "Yas grubu"])
put(ws, 1, "Yaslanma kohortunun 7 bolgesi, yas grubuna gore", ar,
    {"Hucre": INT, "Ortalama (log2)": F3, "Ortanca (log2)": F3, "Ifade eden oran": PCT})
autofit(ws)

# ---------------------------------------------------------------- replication
ws = wb.create_sheet("Kohort tekrari")
w2 = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
ag2 = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")
w2["division"] = w2.region.replace({"Isocortex-1": "Isocortex", "Isocortex-2": "Isocortex"})
w2["prod"] = w2.mean_Kif13a * w2.n_cells
wm = w2.groupby(["division", "subclass"], as_index=False).agg(prod=("prod", "sum"), n=("n_cells", "sum"))
wm["ref"] = wm["prod"] / wm["n"]
adult = (ag2[ag2.donor_age_category == "adult"]
         .rename(columns={"anatomical_division_label": "division",
                          "subclass_name": "subclass", "mean_Kif13a": "aging"})
         [["division", "subclass", "aging"]])
mg = wm.merge(adult, on=["division", "subclass"])
r = 1
for sc, label, rho, pv in [("326 OPC NN", "OPC", 0.964, 0.0005),
                           ("327 Oligo NN", "Olgun oligodendrosit", 0.893, 0.0068)]:
    s = mg[mg.subclass == sc].sort_values("ref", ascending=False)
    t = pd.DataFrame({
        "Bolge": s.division.values,
        "Referans atlas (log2)": s.ref.values,
        "Yaslanma kohortu (log2)": s.aging.values,
        "Fark": s.aging.values - s.ref.values,
    })
    r = put(ws, r, "{0} (Spearman rho = {1:+.3f}, p = {2})".format(label, rho, pv), t,
            {"Referans atlas (log2)": F3, "Yaslanma kohortu (log2)": F3, "Fark": "+0.000;-0.000"})
autofit(ws)

# ---------------------------------------------------------------- whole brain
ws = wb.create_sheet("Tum beyin siralamasi")
rk = pd.read_csv(RESULTS / "derived_wholebrain_subclass_ranking.csv")
rk.insert(0, "Sira", range(1, len(rk) + 1))
full = rk[["Sira", "subclass", "cell_class", "neurotransmitter", "n_cells",
           "mean_Kif13a", "fraction_expressing", "n_partitions"]]
full.columns = ["Sira", "Alt sinif", "Sinif", "Notrotransmitter", "Hucre",
                "Ortalama (log2)", "Ifade eden oran", "Parca sayisi"]
r = put(ws, 1, "En yuksek 10 hucre tipi", full.head(10),
        {"Hucre": INT, "Ortalama (log2)": F3, "Ifade eden oran": PCT})

glia = ["327 Oligo NN", "326 OPC NN", "334 Microglia NN", "319 Astro-TE NN",
        "333 Endo NN", "331 Peri NN"]
gl = full[full["Alt sinif"].isin(glia)].copy()
gl["_o"] = gl["Alt sinif"].map({s: i for i, s in enumerate(glia)})
gl = gl.sort_values("_o").drop(columns="_o")
r = put(ws, r, "Glia tipleri karsilastirmasi", gl,
        {"Hucre": INT, "Ortalama (log2)": F3, "Ifade eden oran": PCT})

r = put(ws, r, "En dusuk 10 hucre tipi", full.tail(10),
        {"Hucre": INT, "Ortalama (log2)": F3, "Ifade eden oran": PCT})
put(ws, r, "Tam siralama, 265 alt sinif", full,
    {"Hucre": INT, "Ortalama (log2)": F3, "Ifade eden oran": PCT})
autofit(ws)

# ---------------------------------------------------------------- detection vs level
ws = wb.create_sheet("Tespit vs seviye")
dv = pd.read_csv(RESULTS / "derived_detection_vs_level.csv")
dv = dv[["subclass", "rank_overall", "n_cells", "mean_Kif13a", "fraction_expressing",
         "cpm_among_expressing", "naive_fold", "detection_ratio", "level_ratio_among_expressing"]]
dv.columns = ["Alt sinif", "Genel sira", "Hucre", "Ortalama (log2, sifirlar dahil)",
              "Tespit orani", "Tespit edilende seviye (CPM)", "Yaniltici kat",
              "Tespit orani kati", "Seviye kati"]
put(ws, 1, "Tespit orani ile ifade seviyesinin ayrilmasi", dv,
    {"Hucre": INT, "Ortalama (log2, sifirlar dahil)": F3, "Tespit orani": PCT,
     "Tespit edilende seviye (CPM)": INT, "Yaniltici kat": "0.0",
     "Tespit orani kati": "0.00", "Seviye kati": "0.00"})
autofit(ws)

# ---------------------------------------------------------------- dataset
ws = wb.create_sheet("Veri seti")
ds = pd.DataFrame({
    "Ozellik": ["Ad", "Hucre sayisi", "Parca / bolge", "Fare sayisi", "Gen sayisi",
                "Ifade matrisi (disk)", "Yontem", "Deger birimi", "Metadata surumu"],
    "Referans atlas": ["WMB-10Xv3", "2.341.350", "13 parca", "cikarilmadi", "32.285",
                       "yaklasik 95 GB", "10x Genomics Chromium v3", "log2(CPM+1)", "20241115"],
    "Yaslanma kohortu": ["Zeng Aging Mouse 10Xv3", "1.162.565", "7 anatomik bolge",
                         "108 (64 genc, 44 yasli)", "32.285", "yaklasik 13 GB",
                         "10x Genomics Chromium v3", "log2(CPM+1)", "20250131"],
})
r = put(ws, 1, "Veri setleri", ds)

frames = []
for f in sorted(RESULTS.glob("Kif13a_WMB-10Xv3-*_subclass_summary.csv")):
    region = re.search(r"WMB-10Xv3-(.+)_subclass_summary", f.name).group(1)
    t = pd.read_csv(f, keep_default_na=False)
    t["region"] = region
    frames.append(t)
allp = pd.concat(frames, ignore_index=True)
part = (allp.groupby("region")
            .agg(**{"Hucre": ("n_cells", "sum"), "Alt sinif": ("subclass", "nunique")})
            .reset_index().rename(columns={"region": "Parca"})
            .sort_values("Hucre", ascending=False))
part["Yuzde"] = part["Hucre"] / part["Hucre"].sum()
r = put(ws, r, "Parcalara gore hucre dagilimi", part, {"Hucre": INT, "Yuzde": PCT})

tax = pd.DataFrame({
    "Duzey": ["Sinif (class)", "Alt sinif (subclass)", "Supertip (supertype)",
              "Kume (cluster)", "Notrotransmitter tipi"],
    "Sayi": [34, 338, 1201, 5322, 10],
})
put(ws, r, "Ortak taksonomi", tax, {"Sayi": INT})
autofit(ws)

wb.save(OUT)
print("Kaydedildi:", OUT)
print("Sayfalar:", wb.sheetnames)
