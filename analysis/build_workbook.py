"""Collect every Kif13a result into one Excel workbook.

Raw values come from the committed tables under results/. Derived quantities
(differences, fold changes, spreads) are written as live formulas so the sheet
recalculates if a source value is corrected. Statistics produced by scipy
(p-values, effect sizes) cannot be expressed as spreadsheet formulas and are
written as values, flagged as such on the summary sheet.

Output: Kif13a_sonuclar.xlsx in the repository root.
"""
from pathlib import Path
import re

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "Kif13a_sonuclar.xlsx"

FONT = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
HDR_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(name=FONT, bold=True, size=14, color="1F3864")
SUB_FONT = Font(name=FONT, italic=True, size=9, color="595959")
BODY = Font(name=FONT, size=10)
BOLD = Font(name=FONT, size=10, bold=True)
SMALL = Font(name=FONT, size=9)
NOTE_FILL = PatternFill("solid", fgColor="FFF2CC")
HI_FILL = PatternFill("solid", fgColor="E2EFDA")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

wb = Workbook()
wb.remove(wb.active)


def header(ws, title, subtitle, ncols):
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle
    ws["A2"].font = SUB_FONT
    wide = max(ncols, 4)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=wide)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=wide)
    ws.freeze_panes = "A5"


def table(ws, df, start_row, headers=None, num_fmt=None):
    cols = list(df.columns)
    labels = headers or cols
    for j, lab in enumerate(labels, start=1):
        c = ws.cell(row=start_row, column=j, value=lab)
        c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, (_, row) in enumerate(df.iterrows(), start=start_row + 1):
        for j, col in enumerate(cols, start=1):
            v = row[col]
            c = ws.cell(row=i, column=j, value=None if pd.isna(v) else v)
            c.font, c.border = BODY, BORDER
            if num_fmt and col in num_fmt:
                c.number_format = num_fmt[col]
    return start_row + 1, start_row + len(df)


def notes(ws, row, lines, width):
    ws.cell(row=row, column=1, value="Notlar").font = BOLD
    row += 1
    for n in lines:
        c = ws.cell(row=row, column=1, value="- " + n)
        c.font = SMALL
        c.fill = NOTE_FILL
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=width)
        row += 1
    return row


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


F3 = "0.000"
F4 = "0.0000"
PCT = "0.0%"
INT = "#,##0"

# ------------------------------------------------------------------ 1. summary
ws = wb.create_sheet("Ozet")
header(ws, "KIF13A bulgulari: ozet",
       "Allen Brain Cell Atlas, surum 20260711. Hesaplamalar TRUBA uzerinde SLURM ile yapildi.", 7)

findings = [
    ("Bulgu 1", "Kif13a oligodendrosit soyuna spesifik, genel bir glia geni degil."),
    ("", "Olgun oligodendrosit 265 alt sinif icinde birinci. Astrosit ve mikroglia yaklasik 16 kat dusuk."),
    ("", "Ayrinti: Tum Beyin Siralamasi sayfasi."),
    ("", ""),
    ("Bulgu 2", "Oncul hucreler bolgesel olarak degisken, olgun hucreler duz."),
    ("", "OPC yayilimi oligodendrositin yaklasik uc kati. Korteks ve hipokampusta yuksek, serebellum ve medullada dusuk."),
    ("", "Varyans farki anlamli (Levene p < 0.0001) ve bagimsiz kohortta tekrarlaniyor (Spearman rho = +0.96)."),
    ("", "Ayrinti: Bolgesel Heterojenlik ve Kohort Tekrari sayfalari."),
    ("", ""),
    ("Bulgu 3", "Yaslanmayla artis sadece olgun oligodendrositte."),
    ("", "53 genc fare (yaklasik 2 aylik) ile 44 yasli fare (yaklasik 18 aylik) karsilastirildi."),
    ("", "Her fare tek bir gozlem sayildi, boylece ayni hayvandan gelen binlerce hucre yalanci tekrar olusturmadi."),
    ("", "Ayrinti: Yaslanma Donor Testi sayfasi."),
]
r = 4
for lab, txt in findings:
    ws.cell(row=r, column=1, value=lab).font = BOLD
    c = ws.cell(row=r, column=2, value=txt)
    c.font = BODY
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=7)
    r += 1

r += 1
ws.cell(row=r, column=1, value="Ana sayisal sonuc").font = Font(name=FONT, bold=True, size=12, color="1F3864")
r += 1
key = pd.DataFrame({
    "Hucre tipi": ["Olgun oligodendrosit", "OPC (oncul)"],
    "Genc ortalama (log2)": [7.867824, 6.923194 - 0.130622],
    "Yasli ortalama (log2)": [8.117736, 6.923194],
})
head_row = r
first, last = table(ws, key, head_row,
                    num_fmt={"Genc ortalama (log2)": F3, "Yasli ortalama (log2)": F3})
extra = ["Fark (log2)", "Kat degisim", "Mann-Whitney p", "Cliff delta"]
for j, lab in enumerate(extra, start=4):
    c = ws.cell(row=head_row, column=j, value=lab)
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
stats_vals = [(0.000242, 0.434820), (0.219357, 0.145798)]
for i, (pv, cd) in zip(range(first, last + 1), stats_vals):
    ws.cell(row=i, column=4, value="=C{0}-B{0}".format(i)).number_format = "+0.000;-0.000"
    ws.cell(row=i, column=5, value="=POWER(2,D{0})".format(i)).number_format = F3
    ws.cell(row=i, column=6, value=pv).number_format = F4
    ws.cell(row=i, column=7, value=cd).number_format = "+0.000;-0.000"
    for j in range(4, 8):
        ws.cell(row=i, column=j).font = BODY
        ws.cell(row=i, column=j).border = BORDER
ws.cell(row=first, column=6).fill = HI_FILL

r = notes(ws, last + 2, [
    "Olcum birimi log2(CPM + 1). Olculen sey mRNA'dir, protein degildir.",
    "Fark ve kat degisim sutunlari canli formuldur. p degerleri ve Cliff delta scipy ile hesaplandi, deger olarak yazildi.",
    "Kif13a, Allen'in yayimlanmis yasa bagli farkli ifade tablosunda yer almiyor, yani etki gercek ama mutevazi.",
    "Yaslanma kohortu 13 bolgenin sadece 7'sini kapsiyor. Serebellum, medulla, talamus, olfaktor ve CTXsp disarida.",
    "Kaynak kod: github.com/ikoshos-gland/kif13a-allenbrain",
], 7)
widths(ws, {"A": 22, "B": 21, "C": 21, "D": 13, "E": 13, "F": 16, "G": 13})

# ------------------------------------------------------------------ 2. datasets
ws = wb.create_sheet("Veri Seti")
header(ws, "Veri seti kunyesi",
       "Allen Brain Cell Atlas, abc-atlas-access ile indirildi, surum 20260711.", 3)
ds = pd.DataFrame({
    "Ozellik": ["Ad", "Hucre sayisi", "Parca / bolge", "Fare sayisi", "Gen sayisi",
                "Ifade matrisi (disk)", "Yontem", "Deger birimi", "Metadata surumu"],
    "Referans atlas": ["WMB-10Xv3", "2.341.350", "13 parca", "cikarilmadi", "32.285",
                       "yaklasik 95 GB", "10x Genomics Chromium v3", "log2(CPM+1)", "20241115"],
    "Yaslanma kohortu": ["Zeng Aging Mouse 10Xv3", "1.162.565", "7 anatomik bolge",
                         "108 (64 genc, 44 yasli)", "32.285", "yaklasik 13 GB",
                         "10x Genomics Chromium v3", "log2(CPM+1)", "20250131"],
})
table(ws, ds, 4)
r = 4 + len(ds) + 2
ws.cell(row=r, column=1, value="Ortak taksonomi").font = BOLD
tax = pd.DataFrame({
    "Duzey": ["Sinif (class)", "Alt sinif (subclass)", "Supertip (supertype)",
              "Kume (cluster)", "Notrotransmitter tipi"],
    "Sayi": [34, 338, 1201, 5322, 10],
})
table(ws, tax, r + 1, num_fmt={"Sayi": INT})
r = notes(ws, r + 1 + len(tax) + 2, [
    "Gen kimligi: Kif13a = ENSMUSG00000021375.",
    "Yaslanma kohortu kapsami: izokorteks, hipokampus, orta beyin, pallidum, hipotalamus, pons, striatum.",
    "Kapsam disi: serebellum, medulla, talamus, olfaktor alan, kortikal subplate.",
    "Atlas onbellegi 103 GB. Depoya dahil edilmedi, script'ler ilk calistirmada indiriyor.",
], 5)
widths(ws, {"A": 26, "B": 30, "C": 34, "D": 12, "E": 12})

# ------------------------------------------------------- 3. aging donor-level test
ws = wb.create_sheet("Yaslanma Donor Testi")
header(ws, "Yaslanma: donor duzeyi test",
       "Her fare tek gozlem. 53 genc ve 44 yasli farenin ortalamalari karsilastirildi.", 8)
d = pd.read_csv(RESULTS / "derived_donor_level_age_test.csv")
d = d[["subclass", "n_adult", "n_aged", "mean_adult", "mean_aged",
       "mannwhitney_p", "welch_t_p", "cliffs_delta"]]
hdr = ["Alt sinif", "Genc fare", "Yasli fare", "Genc ortalama (log2)",
       "Yasli ortalama (log2)", "Mann-Whitney p", "Welch t p", "Cliff delta"]
head_row = 4
first, last = table(ws, d, head_row, headers=hdr,
                    num_fmt={"mean_adult": F3, "mean_aged": F3,
                             "mannwhitney_p": F4, "welch_t_p": F4, "cliffs_delta": "+0.000;-0.000"})
for j, lab in enumerate(["Fark (log2)", "Kat degisim", "Anlamli mi"], start=9):
    c = ws.cell(row=head_row, column=j, value=lab)
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for i in range(first, last + 1):
    ws.cell(row=i, column=9, value="=E{0}-D{0}".format(i)).number_format = "+0.000;-0.000"
    ws.cell(row=i, column=10, value="=POWER(2,I{0})".format(i)).number_format = F3
    ws.cell(row=i, column=11, value='=IF(F{0}<0.05,"evet","hayir")'.format(i))
    for j in range(9, 12):
        ws.cell(row=i, column=j).font = BODY
        ws.cell(row=i, column=j).border = BORDER
r = notes(ws, last + 2, [
    "Orijinal SLURM pipeline hic istatistik testi yapmiyor, sadece betimsel ortalama uretiyor. Bu sayfadaki testler sonradan eklendi.",
    "Hucre duzeyinde test yapilsaydi ayni fareden gelen binlerce hucre bagimsiz gozlem sayilir ve p degeri yapay olarak kucululurdu.",
    "Cliff delta parametrik olmayan etki buyuklugu. 0.147 kucuk, 0.435 orta buyuklukte kabul edilir.",
    "Ifade eden hucre orani her iki grupta da yaklasik yuzde 95, yani daha fazla hucre geni acmiyor.",
], 11)
widths(ws, {"A": 17, "B": 11, "C": 11, "D": 19, "E": 19, "F": 16, "G": 13, "H": 12, "I": 13, "J": 13, "K": 12})

# ------------------------------------------------------- 4. aging by subclass
ws = wb.create_sheet("Yaslanma Alt Sinif")
header(ws, "Yaslanma: alt sinif ozeti (hucreler havuzlanmis)",
       "Donor duzeyi duzeltmesi yok. Anlamlilik icin Yaslanma Donor Testi sayfasina bakin.", 8)
a = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_summary.csv")
a = a[["donor_age_category", "subclass_name", "n_cells", "n_donors",
       "mean_Kif13a", "median_Kif13a", "fraction_expressing"]]
table(ws, a, 4,
      headers=["Yas grubu", "Alt sinif", "Hucre", "Fare", "Ortalama (log2)",
               "Ortanca (log2)", "Ifade eden oran"],
      num_fmt={"n_cells": INT, "mean_Kif13a": F3, "median_Kif13a": F3, "fraction_expressing": PCT})
r = 4 + len(a) + 2
ws.cell(row=r, column=1, value="Genc - yasli farklari").font = BOLD
dv = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_adult_vs_aged.csv")
keep = ["subclass_name", "mean_Kif13a_adult", "mean_Kif13a_aged",
        "median_Kif13a_adult", "median_Kif13a_aged",
        "fraction_expressing_adult", "fraction_expressing_aged"]
dv = dv[[c for c in keep if c in dv.columns]]
hr = r + 1
first, last = table(ws, dv, hr,
                    headers=["Alt sinif", "Genc ortalama", "Yasli ortalama", "Genc ortanca",
                             "Yasli ortanca", "Genc ifade oran", "Yasli ifade oran"],
                    num_fmt={c: (PCT if "fraction" in c else F3) for c in dv.columns if c != "subclass_name"})
for j, lab in enumerate(["Ortalama farki", "Ortanca farki", "Oran farki"], start=8):
    c = ws.cell(row=hr, column=j, value=lab)
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for i in range(first, last + 1):
    ws.cell(row=i, column=8, value="=C{0}-B{0}".format(i)).number_format = "+0.000;-0.000"
    ws.cell(row=i, column=9, value="=E{0}-D{0}".format(i)).number_format = "+0.000;-0.000"
    ws.cell(row=i, column=10, value="=G{0}-F{0}".format(i)).number_format = "+0.0%;-0.0%"
    for j in range(8, 11):
        ws.cell(row=i, column=j).font = BODY
        ws.cell(row=i, column=j).border = BORDER
notes(ws, last + 2, [
    "Bu sayfadaki sayilar tum hucreler havuzlanarak hesaplandi, fare kimligi dikkate alinmadi.",
    "Yasli farelerin fare basina daha cok hucre vermesi bu havuzlanmis ortalamalari etkileyebilir.",
], 10)
widths(ws, {"A": 16, "B": 17, "C": 16, "D": 11, "E": 16, "F": 16, "G": 16, "H": 15, "I": 15, "J": 13})

# ------------------------------------------------------- 5. aging by region
ws = wb.create_sheet("Yaslanma Bolge")
header(ws, "Yaslanma: bolgeye gore kirilim",
       "Yaslanma kohortunun kapsadigi 7 anatomik bolge. Oligodendrositte artis 7 bolgenin 7'sinde de var.", 8)
ar = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")
ar = ar[["anatomical_division_label", "donor_age_category", "subclass_name",
         "n_cells", "n_donors", "mean_Kif13a", "median_Kif13a", "fraction_expressing"]]
ar = ar.sort_values(["subclass_name", "anatomical_division_label", "donor_age_category"])
table(ws, ar, 4,
      headers=["Bolge", "Yas grubu", "Alt sinif", "Hucre", "Fare",
               "Ortalama (log2)", "Ortanca (log2)", "Ifade eden oran"],
      num_fmt={"n_cells": INT, "mean_Kif13a": F3, "median_Kif13a": F3, "fraction_expressing": PCT})
notes(ws, 4 + len(ar) + 2, [
    "Oligodendrositte yasli ortalamasi 7 bolgenin 7'sinde de genc ortalamasinin uzerinde. OPC'de yon karisik, 4 bolgede artis 3 bolgede azalis.",
    "Bu asimetri oligodendrosit sinyalinin gercek olduguna dair ikinci bir kanit.",
], 8)
widths(ws, {"A": 13, "B": 12, "C": 16, "D": 11, "E": 9, "F": 16, "G": 16, "H": 15})

# ------------------------------------------------------- 6. donor list
ws = wb.create_sheet("Yaslanma Donor Listesi")
header(ws, "Yaslanma: fare bazinda tablo",
       "Analize giren 97 farenin her biri, her alt sinif icin bir satir.", 10)
dl = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_donor_summary.csv")
dl = dl[["donor_label", "donor_age_category", "donor_age", "donor_sex", "subclass_name",
         "n_cells", "mean_Kif13a", "median_Kif13a", "fraction_expressing"]]
dl = dl.sort_values(["subclass_name", "donor_age_category", "donor_label"])
first, last = table(ws, dl, 4,
                    headers=["Fare", "Yas grubu", "Yas", "Cinsiyet", "Alt sinif",
                             "Hucre", "Ortalama (log2)", "Ortanca (log2)", "Ifade eden oran"],
                    num_fmt={"n_cells": INT, "mean_Kif13a": F3, "median_Kif13a": F3,
                             "fraction_expressing": PCT})
ws.auto_filter.ref = "A4:I{0}".format(last)
notes(ws, last + 2, [
    "Genc grup P53 ile P69 gunleri arasinda, ortanca 61 gun. Yasli grup P540 ile P553 arasinda, ortanca 543,5 gun.",
    "18M etiketi ile P540 ayni yasi gosteriyor, metadata iki farkli etiketleme semasi kullaniyor.",
    "Veri setinin tamaminda 108 fare var. 11 genc fare hic OPC veya oligodendrosit hucresi vermedigi icin analize girmedi.",
    "Bes farenin OPC hucre sayisi ellinin altinda. Ucu genc ikisi yasli grupta, yani sistematik bir yanlilik yok.",
], 9)
widths(ws, {"A": 20, "B": 12, "C": 9, "D": 10, "E": 16, "F": 10, "G": 16, "H": 16, "I": 15})

# ------------------------------------------------------- 7. whole-brain ranking
ws = wb.create_sheet("Tum Beyin Siralamasi")
header(ws, "Tum beyin: alt siniflarin Kif13a siralamasi",
       "13 parca havuzlandi, hucre sayisiyla agirliklandirildi. En az 500 hucreli alt siniflar.", 8)
rk = pd.read_csv(RESULTS / "derived_wholebrain_subclass_ranking.csv")
rk = rk[["subclass", "cell_class", "neurotransmitter", "n_cells",
         "mean_Kif13a", "fraction_expressing", "n_partitions"]]
rk.insert(0, "Sira", range(1, len(rk) + 1))
first, last = table(ws, rk, 4,
                    headers=["Sira", "Alt sinif", "Sinif", "Notrotransmitter", "Hucre",
                             "Ortalama (log2)", "Ifade eden oran", "Parca sayisi"],
                    num_fmt={"n_cells": INT, "mean_Kif13a": F3, "fraction_expressing": PCT})
for i in range(first, min(first + 2, last + 1)):
    for j in range(1, 9):
        ws.cell(row=i, column=j).fill = HI_FILL
ws.auto_filter.ref = "A4:H{0}".format(last)
notes(ws, last + 2, [
    "Ilk iki satir yesil: olgun oligodendrosit ve onculu. Ucuncu sirada medial habenulanin kolinerjik Tac2 noronlari var ama sadece 4.662 hucre.",
    "Astrosit, mikroglia ve endotel 3,7 ile 3,9 arasinda, yani oligodendrositin yaklasik onaltida biri. Kif13a genel bir glia geni degil.",
    "En dusuk degerler olfaktor bulbusun inhibitor internoronlarinda.",
    "Ortancalar parca ortancalarindan havuzlanamaz, bu yuzden siralama ortalama uzerinden. Hucreler havuzlanmis, donor duzeyi duzeltmesi yok, siralama betimseldir.",
], 8)
widths(ws, {"A": 7, "B": 34, "C": 20, "D": 17, "E": 11, "F": 16, "G": 15, "H": 12})

# ------------------------------------------------------- 8. regional heterogeneity
ws = wb.create_sheet("Bolgesel Heterojenlik")
header(ws, "Bolgesel heterojenlik: OPC ve oligodendrosit",
       "Referans atlasin 13 parcasi. Olgun hucre her parcada onculun uzerinde.", 6)
w = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
opc = w[w.subclass == "326 OPC NN"].set_index("region")
oli = w[w.subclass == "327 Oligo NN"].set_index("region")
reg = pd.DataFrame({
    "Parca": opc.index,
    "OPC ortalama": opc.mean_Kif13a.values,
    "Oligo ortalama": oli.reindex(opc.index).mean_Kif13a.values,
    "OPC ifade oran": opc.fraction_expressing.values,
    "Oligo ifade oran": oli.reindex(opc.index).fraction_expressing.values,
}).sort_values("OPC ortalama", ascending=False)
head_row = 4
first, last = table(ws, reg, head_row,
                    num_fmt={"OPC ortalama": F3, "Oligo ortalama": F3,
                             "OPC ifade oran": PCT, "Oligo ifade oran": PCT})
c = ws.cell(row=head_row, column=6, value="Oligo - OPC")
c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for i in range(first, last + 1):
    cc = ws.cell(row=i, column=6, value="=C{0}-B{0}".format(i))
    cc.number_format = "+0.000;-0.000"
    cc.font, cc.border = BODY, BORDER

r = last + 2
ws.cell(row=r, column=1, value="Yayilim karsilastirmasi").font = BOLD
r += 1
spread_hdr = ["Olcut", "OPC", "Oligo", "Oran (OPC/Oligo)"]
for j, lab in enumerate(spread_hdr, start=1):
    c = ws.cell(row=r, column=j, value=lab)
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
    c.alignment = Alignment(horizontal="center", wrap_text=True)
def col_range(col):
    """Full A1 range for one column of the data block, e.g. B5:B17."""
    return "{0}{1}:{0}{2}".format(col, first, last)


spread_rows = [
    ("En dusuk", "=MIN({0})".format(col_range("B")), "=MIN({0})".format(col_range("C"))),
    ("En yuksek", "=MAX({0})".format(col_range("B")), "=MAX({0})".format(col_range("C"))),
    ("Aralik", None, None),
    ("Standart sapma", "=STDEV({0})".format(col_range("B")), "=STDEV({0})".format(col_range("C"))),
]
base = r + 1
for k, (lab, bf, cf) in enumerate(spread_rows):
    i = base + k
    ws.cell(row=i, column=1, value=lab).font = BODY
    if lab == "Aralik":
        ws.cell(row=i, column=2, value="=B{0}-B{1}".format(base + 1, base))
        ws.cell(row=i, column=3, value="=C{0}-C{1}".format(base + 1, base))
    else:
        ws.cell(row=i, column=2, value=bf)
        ws.cell(row=i, column=3, value=cf)
    ws.cell(row=i, column=4, value="=IF(C{0}=0,\"\",B{0}/C{0})".format(i))
    for j in range(1, 5):
        cell = ws.cell(row=i, column=j)
        cell.border = BORDER
        cell.font = BODY
        if j > 1:
            cell.number_format = F3
    if lab in ("Aralik", "Standart sapma"):
        ws.cell(row=i, column=4).fill = HI_FILL

r = base + len(spread_rows) + 1
ws.cell(row=r, column=1, value="Istatistik testleri (scipy ile hesaplandi)").font = BOLD
tests = pd.DataFrame({
    "Test": ["Varyans orani (F testi)", "Levene (Brown-Forsythe)",
             "Korteks+HPF vs arka beyin, OPC", "Korteks+HPF vs arka beyin, Oligo"],
    "Istatistik": [9.87, 24.95, None, None],
    "p degeri": [0.000372, 0.00003, 0.0179, 0.1964],
    "Yorum": ["OPC varyansi anlamli sekilde buyuk", "Ayni sonuc, medyan merkezli",
              "OPC gradyani anlamli, fark +1,335 log2", "Oligodendrositte gradyan yok"],
})
table(ws, tests, r + 1, num_fmt={"Istatistik": "0.00", "p degeri": "0.00000"})
notes(ws, r + 1 + len(tests) + 2, [
    "OPC'de en yuksek bes parca korteks ve hipokampus kokenli: HPF, Isocortex-1, Isocortex-2, CTXsp, OLF.",
    "En dusuk uc parca arka beyin kokenli: MY (medulla), CB (serebellum), P (pons).",
    "Pallidum ve talamus da dusuk siralarda, ikisi de arka beyin degil. Yani duz bir rostro-kaudal gradyan degil.",
    "Gozlenen yayilim ornekleme gurultusunun yaklasik 12 katı, dolayisiyla kucuk orneklem artefakti degil.",
], 6)
widths(ws, {"A": 30, "B": 16, "C": 16, "D": 18, "E": 17, "F": 14})

# ------------------------------------------------------- 9. cross-cohort replication
ws = wb.create_sheet("Kohort Tekrari")
header(ws, "Bagimsiz kohortta tekrarlanabilirlik",
       "Referans atlas ile yaslanma kohortunun ortak 7 bolgesi. Farkli fareler, farkli deney.", 5)
w2 = pd.read_csv(RESULTS / "Kif13a_WMB-10Xv3_all_regions_OPC_Oligo_summary.csv")
ag = pd.read_csv(RESULTS / "Kif13a_AgingMouse_OPC_Oligo_age_region_summary.csv")
w2["division"] = w2.region.replace({"Isocortex-1": "Isocortex", "Isocortex-2": "Isocortex"})
w2["prod"] = w2.mean_Kif13a * w2.n_cells
wm = w2.groupby(["division", "subclass"], as_index=False).agg(prod=("prod", "sum"), n=("n_cells", "sum"))
wm["ref"] = wm["prod"] / wm["n"]
adult = (ag[ag.donor_age_category == "adult"]
         .rename(columns={"anatomical_division_label": "division",
                          "subclass_name": "subclass", "mean_Kif13a": "aging"})
         [["division", "subclass", "aging"]])
mg = wm.merge(adult, on=["division", "subclass"])
r = 4
for sc, label, rho, pv in [("326 OPC NN", "OPC", 0.964, 0.0005),
                           ("327 Oligo NN", "Olgun oligodendrosit", 0.893, 0.0068)]:
    s = mg[mg.subclass == sc].sort_values("ref", ascending=False)
    ws.cell(row=r, column=1, value=label).font = Font(name=FONT, bold=True, size=11, color="1F3864")
    r += 1
    tb = s[["division", "ref", "aging"]].copy()
    first, last = table(ws, tb, r,
                        headers=["Bolge", "Referans atlas (log2)", "Yaslanma kohortu (log2)"],
                        num_fmt={"ref": F3, "aging": F3})
    c = ws.cell(row=r, column=4, value="Fark")
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
    c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(first, last + 1):
        cc = ws.cell(row=i, column=4, value="=C{0}-B{0}".format(i))
        cc.number_format = "+0.000;-0.000"
        cc.font, cc.border = BODY, BORDER
    r = last + 1
    ws.cell(row=r, column=1, value="Spearman rho").font = BOLD
    ws.cell(row=r, column=2, value=rho).number_format = "+0.000"
    ws.cell(row=r, column=2).fill = HI_FILL
    ws.cell(row=r, column=3, value="p = {0}".format(pv)).font = BODY
    r += 3
notes(ws, r, [
    "Iki veri seti farkli hayvanlardan ve farkli deneylerden geliyor. Bolgesel siralamanin ikisinde de ayni cikmasi, oruntununu tek bir deneyin toplu isleme artefakti olmadigini gosteriyor.",
    "Yaslanma kohortu sadece 7 bolgeyi kapsadigi icin karsilastirma bu bolgelerle sinirli.",
    "Izokorteks referans atlasta iki parcaya bolunmus. Karsilastirma icin hucre sayisiyla agirliklandirilip tek bolgede birlestirildi.",
    "Spearman rho scipy ile hesaplandi ve deger olarak yazildi.",
], 5)
widths(ws, {"A": 24, "B": 22, "C": 24, "D": 13, "E": 13})

wb.save(OUT)
print("Kaydedildi:", OUT)
print("Sayfalar:", wb.sheetnames)


# ------------------------------------------------------- cache the formula values
# openpyxl writes formulas with no cached result, so pandas, previewers and
# anything reading cached values see blanks until a spreadsheet application
# opens the file. Evaluate the formulas and embed each result next to its
# formula, which keeps the sheet recalculating while staying readable offline.
def cache_formula_values(path):
    import shutil
    import warnings
    import xml.etree.ElementTree as ET
    import zipfile

    try:
        import formulas
    except ImportError:
        print("uyari: 'formulas' kurulu degil, degerler gomulmedi "
              "(dosya yine de Excel'de acildiginda hesaplanir)")
        return

    warnings.filterwarnings("ignore")
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("", ns)

    book = __import__("openpyxl").load_workbook(path)
    order = {s.title.upper(): i + 1 for i, s in enumerate(book.worksheets)}

    solved = formulas.ExcelModel().loads(str(path)).finish().calculate()
    computed = {}
    for k, v in solved.items():
        if "]" not in k or "'!" not in k:
            continue
        sheet = k.split("]", 1)[1].split("'!", 1)[0].upper()
        coord = k.split("'!", 1)[1]
        if not re.fullmatch(r"[A-Z]+\d+", coord):
            continue
        try:
            computed[(sheet, coord)] = v.value[0, 0]
        except Exception:
            continue

    backup = str(path) + ".bak"
    shutil.copy(path, backup)
    zin = zipfile.ZipFile(backup, "r")
    items = zin.infolist()
    payload, patched = {}, 0
    for it in items:
        data = zin.read(it.filename)
        m = re.fullmatch(r"xl/worksheets/sheet(\d+)\.xml", it.filename)
        if m:
            idx = int(m.group(1))
            sheet = next((s for s, i in order.items() if i == idx), None)
            if sheet:
                root = ET.fromstring(data)
                for cell in root.iter("{%s}c" % ns):
                    if cell.find("{%s}f" % ns) is None:
                        continue
                    val = computed.get((sheet, cell.get("r")))
                    if val is None:
                        continue
                    for old in cell.findall("{%s}v" % ns):
                        cell.remove(old)
                    node = ET.SubElement(cell, "{%s}v" % ns)
                    if isinstance(val, str):
                        cell.set("t", "str")
                        node.text = val
                    else:
                        cell.attrib.pop("t", None)
                        node.text = repr(float(val))
                    patched += 1
                data = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
        payload[it.filename] = data
    zin.close()

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in items:
            zout.writestr(it, payload[it.filename])
    Path(backup).unlink(missing_ok=True)
    print("Formul degeri gomulen hucre:", patched)


cache_formula_values(OUT)
