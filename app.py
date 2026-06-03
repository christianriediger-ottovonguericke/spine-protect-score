
import streamlit as st
from datetime import date, datetime
from io import BytesIO
import pandas as pd

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="Spine-PROTECT Score", page_icon="🟢", layout="wide")

def check_password():
    password = st.text_input("Passwort", type="password")
    if password == st.secrets.get("APP_PASSWORD", ""):
        return True
    if password:
        st.error("Falsches Passwort.")
    return False

if not check_password():
    st.stop()

def risiko_klasse(score):
    if score <= 4:
        return "LOW RISK", "Niedriges Risiko", "🟢", "#16A34A", "Standardpfad", "Standardisierte präoperative Aufklärung, regulärer perioperativer Behandlungspfad und routinemäßige Nachsorge."
    if score <= 8:
        return "INTERMEDIATE RISK", "Mittleres Risiko", "🟡", "#D97706", "Erweiterter Behandlungspfad", "Zusätzliche Erwartungssteuerung, schriftlicher Recovery-Plan, frühzeitige Physiotherapie, strukturierter Schmerzmittelplan und Verlaufskontrolle."
    return "HIGH RISK", "Hohes Risiko", "🔴", "#DC2626", "Enhanced Spine Pathway", "Präoperative Schmerzsprechstunde, psychosomatisches Kurzassessment, Opioidstrategie, Prehabilitation und engmaschige Nachsorge nach 2, 6 und 12 Wochen."

def phq_cat(x):
    return "unauffällig/minimal bis leicht" if x < 10 else "leichtgradig klinisch relevant" if x < 15 else "mittelgradig" if x < 20 else "schwer"

def gad_cat(x):
    return "normal bis mild" if x < 5 else "mild" if x < 10 else "mittelgradig" if x < 15 else "schwer"

def pcs_cat(x):
    return "niedrig" if x < 20 else "moderat" if x < 30 else "hoch"

def odi_cat(x):
    if x <= 20: return "minimale Funktionseinschränkung"
    if x <= 40: return "moderate Funktionseinschränkung"
    if x <= 60: return "starke Funktionseinschränkung"
    if x <= 80: return "sehr starke Funktionseinschränkung"
    return "pflegebedürftig / psychosozial extrem überlagert"

def risiko_ampel(label, emoji, color, score):
    st.markdown(f"""
    <div style="background-color:{color};color:white;padding:22px;border-radius:16px;text-align:center;font-size:28px;font-weight:800;margin-bottom:14px;">
    {emoji} {label}<br><span style="font-size:20px;">Spine-PROTECT Score: {score}/15</span>
    </div>
    """, unsafe_allow_html=True)

def befundtext(patient, vals, score, risk_de, pfad, empfehlung):
    return f"""Spine-PROTECT Screening-Befund

Patienten-/Studien-ID: {patient['Patienten-/Studien-ID']}
Datum: {patient['Datum']}
Alter: {patient['Alter']}
Geschlecht: {patient['Geschlecht']}
Indikation: {patient['Indikation']}
Geplantes Verfahren: {patient['Geplantes Verfahren']}

Der Spine-PROTECT Gesamtscore beträgt {score}/15 Punkten. Dies entspricht der Risikoklasse: {risk_de}.

Psychosoziale Befunde:
- DS14: Negative Affektivität {vals['DS14_NA']}/28, Soziale Inhibition {vals['DS14_SI']}/28, Type-D-Persönlichkeit: {'ja' if vals['Type_D'] else 'nein'}.
- PHQ-9: {vals['PHQ9']}/27 ({phq_cat(vals['PHQ9'])}).
- GAD-7: {vals['GAD7']}/21 ({gad_cat(vals['GAD7'])}).
- PCS: {vals['PCS_Total']}/52 ({pcs_cat(vals['PCS_Total'])}).
- FABQ: PA {vals['FABQ_PA']}/24, W {vals['FABQ_W']}/42; erhöhte Fear-Avoidance-Konstellation: {'ja' if vals['FABQ_erhoeht'] else 'nein'}.
- ODI: {vals['ODI_percent']}% ({odi_cat(vals['ODI_percent'])}).

Klinisch-chirurgische Faktoren:
- Beschwerdedauer: {vals['Beschwerdedauer_Monate']} Monate.
- Präoperativer Opioidgebrauch: {vals['Praeop_Opioide']}.
- Revisionseingriff: {vals['Revision']}.
- Surgical Trauma Score: {vals['Surgical_Trauma_Score']}.

Empfohlener Behandlungspfad:
{pfad}

Empfehlung:
{empfehlung}

Hinweis:
Der Spine-PROTECT Score ist ein klinisches Entscheidungsunterstützungs- und Forschungsinstrument. Er ersetzt weder die ärztliche Beurteilung noch die individuelle Operationsindikation oder eine psychologische/psychiatrische Diagnostik. Bei auffälligem PHQ-9 Item 9 ist eine unmittelbare klinische Abklärung erforderlich."""

def make_pdf(patient, results, table_rows, text):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>Spine-PROTECT Score Bericht</b>", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph("<b>Patient / Fall</b>", styles["Heading2"]))
    t = Table([[k, str(v)] for k, v in patient.items()], colWidths=[160, 320])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E0F2F1")),("GRID",(0,0),(-1,-1),0.25,colors.grey)]))
    story += [t, Spacer(1, 12), Paragraph("<b>Auswertung</b>", styles["Heading2"])]
    t = Table([["Score", str(results["score"])], ["Risikoklasse", results["risk_de"]], ["Behandlungspfad", results["pfad"]], ["Empfehlung", results["empfehlung"]]], colWidths=[160, 320])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#DBEAFE")),("GRID",(0,0),(-1,-1),0.25,colors.grey)]))
    story += [t, Spacer(1, 12), Paragraph("<b>Score-Komponenten</b>", styles["Heading2"])]
    t = Table([["Komponente","Wert","Punkte","Interpretation"]] + table_rows, colWidths=[125,95,55,205])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0F766E")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),8)]))
    story += [t, Spacer(1, 12), Paragraph("<b>Befundtext</b>", styles["Heading2"])]
    for line in text.split("\n"):
        story.append(Paragraph(line if line else " ", styles["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer

st.sidebar.title("Spine-PROTECT")
st.sidebar.caption("Clinical Decision Tool v1.1")
st.sidebar.markdown("🏥 **OvGU / Universitätsmedizin Magdeburg**")
st.sidebar.info("Bitte für Cloud-Nutzung ausschließlich anonymisierte Studien-IDs verwenden.")
st.sidebar.write("🟢 0–4 Punkte: Low Risk")
st.sidebar.write("🟡 5–8 Punkte: Intermediate Risk")
st.sidebar.write("🔴 ≥9 Punkte: High Risk")

st.title("Spine-PROTECT Score")
st.subheader("Psychosozial erweitertes klinisches Decision-Tool vor elektiver Wirbelsäulenoperation")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["1 Patient", "2 Fragebögen", "3 Klinik / OP", "4 Auswertung", "5 Befund / Export", "6 Dokumentation"])

with tab1:
    st.header("Patienten- / Fallinformationen")
    c1, c2, c3 = st.columns(3)
    with c1:
        patient_id = st.text_input("Patienten-/Studien-ID", value="")
        datum = st.date_input("Datum", value=date.today())
    with c2:
        alter = st.number_input("Alter", 18, 100, 60)
        geschlecht = st.selectbox("Geschlecht", ["", "weiblich", "männlich", "divers"])
    with c3:
        indikation = st.text_input("Indikation", value="")
        verfahren = st.text_input("Geplantes Verfahren", value="")

with tab2:
    st.header("Psychosoziales und funktionelles Screening")
    with st.expander("DS14 – Type-D Persönlichkeit", expanded=True):
        ds_values = []
        cols = st.columns(7)
        for i in range(14):
            with cols[i % 7]:
                ds_values.append(st.number_input(f"DS14 Item {i+1}", 0, 4, 0, key=f"ds{i+1}"))
        ds_na = sum(ds_values[i-1] for i in [2,4,5,7,9,11,12])
        ds_si = sum(ds_values[i-1] for i in [1,3,6,8,10,13,14])
        type_d = ds_na >= 10 and ds_si >= 10
        st.write(f"Negative Affektivität: **{ds_na}/28**")
        st.write(f"Soziale Inhibition: **{ds_si}/28**")
        st.write(f"Type-D positiv: **{'Ja' if type_d else 'Nein'}**")

    with st.expander("PHQ-9 – Depressive Symptomatik"):
        phq = [st.slider(f"PHQ-9 Item {i+1}", 0, 3, 0, key=f"phq{i+1}") for i in range(9)]
        phq9 = sum(phq)
        st.write(f"PHQ-9 Gesamtwert: **{phq9}/27** – {phq_cat(phq9)}")
        if phq[8] > 0:
            st.error("PHQ-9 Item 9 ist positiv. Bitte unmittelbar klinisch abklären.")

    with st.expander("GAD-7 – Angstsymptomatik"):
        gad = [st.slider(f"GAD-7 Item {i+1}", 0, 3, 0, key=f"gad{i+1}") for i in range(7)]
        gad7 = sum(gad)
        st.write(f"GAD-7 Gesamtwert: **{gad7}/21** – {gad_cat(gad7)}")

    with st.expander("PCS – Pain Catastrophizing Scale"):
        pcs = [st.slider(f"PCS Item {i+1}", 0, 4, 0, key=f"pcs{i+1}") for i in range(13)]
        pcs_total = sum(pcs)
        st.write(f"PCS Gesamtwert: **{pcs_total}/52** – {pcs_cat(pcs_total)}")

    with st.expander("FABQ – Fear Avoidance Beliefs Questionnaire"):
        cols = st.columns(4)
        fabq = []
        for i in range(16):
            with cols[i % 4]:
                fabq.append(st.number_input(f"FABQ Item {i+1}", 0, 6, 0, key=f"fabq{i+1}"))
        fabq_pa = sum(fabq[i-1] for i in [2,3,4,5])
        fabq_w = sum(fabq[i-1] for i in [6,7,9,10,11,12,15])
        fabq_erh = fabq_pa > 15 or fabq_w > 34
        st.write(f"FABQ-PA: **{fabq_pa}/24**")
        st.write(f"FABQ-W: **{fabq_w}/42**")
        st.write(f"FABQ erhöht: **{'Ja' if fabq_erh else 'Nein'}**")

    with st.expander("ODI – Oswestry Disability Index"):
        cats = ["Schmerzstärke","Körperpflege","Heben","Gehen","Sitzen","Stehen","Schlafen","Sexualleben","Sozialleben","Reisen"]
        cols = st.columns(5)
        odi = []
        for i, name in enumerate(cats):
            with cols[i % 5]:
                odi.append(st.number_input(name, 0, 5, 0, key=f"odi{i+1}"))
        odi_raw = sum(odi)
        odi_percent = odi_raw * 2
        st.write(f"ODI Rohwert: **{odi_raw}/50**")
        st.write(f"ODI: **{odi_percent}%** – {odi_cat(odi_percent)}")

with tab3:
    st.header("Klinisch-chirurgische Risikofaktoren")
    c1, c2 = st.columns(2)
    with c1:
        dauer = st.number_input("Beschwerdedauer in Monaten", 0, 360, 0)
        opioide = st.radio("Präoperativer Opioidgebrauch", ["Nein", "Ja"], horizontal=True)
        revision = st.radio("Revisionseingriff", ["Nein", "Ja"], horizontal=True)
    with c2:
        trauma_label = st.selectbox("Surgical Trauma Score", [
            "1 = mikrochirurgische Dekompression",
            "2 = offene Dekompression",
            "3 = 1-Level-Fusion",
            "4 = Mehrsegment-Fusion",
            "5 = Revisions-/Deformitäten-/langstreckige Fusion"
        ])
        trauma = int(trauma_label[0])
    st.table(pd.DataFrame({
        "Score":[1,2,3,4,5],
        "Verfahren":["mikrochirurgische Dekompression","offene Dekompression","1-Level-Fusion","Mehrsegment-Fusion","Revisions-/Deformitäten-/langstreckige Fusion"],
        "Spine-PROTECT Punkte":[0,0,0,2,2]
    }))

points = {
    "Type-D": 2 if type_d else 0,
    "PHQ-9": 1 if phq9 >= 10 else 0,
    "GAD-7": 1 if gad7 >= 10 else 0,
    "PCS": 2 if pcs_total >= 30 else 1 if pcs_total >= 20 else 0,
    "FABQ": 1 if fabq_erh else 0,
    "Beschwerdedauer": 1 if dauer > 12 else 0,
    "Präop. Opioide": 2 if opioide == "Ja" else 0,
    "ODI": 1 if odi_percent >= 41 else 0,
    "Revision": 2 if revision == "Ja" else 0,
    "Surgical Trauma": 2 if trauma >= 4 else 0,
}
score = sum(points.values())
risk_en, risk_de, emoji, color, pfad, empfehlung = risiko_klasse(score)

component_table = [
    ["Type-D", f"NA {ds_na}, SI {ds_si}", points["Type-D"], "positiv" if type_d else "negativ"],
    ["PHQ-9", phq9, points["PHQ-9"], phq_cat(phq9)],
    ["GAD-7", gad7, points["GAD-7"], gad_cat(gad7)],
    ["PCS", pcs_total, points["PCS"], pcs_cat(pcs_total)],
    ["FABQ", f"PA {fabq_pa}, W {fabq_w}", points["FABQ"], "erhöht" if fabq_erh else "nicht erhöht"],
    ["Beschwerdedauer", f"{dauer} Monate", points["Beschwerdedauer"], ">12 Monate" if dauer > 12 else "≤12 Monate"],
    ["Präop. Opioide", opioide, points["Präop. Opioide"], ""],
    ["ODI", f"{odi_percent}%", points["ODI"], odi_cat(odi_percent)],
    ["Revision", revision, points["Revision"], ""],
    ["Surgical Trauma", trauma, points["Surgical Trauma"], trauma_label],
]
patient = {
    "Patienten-/Studien-ID": patient_id,
    "Datum": str(datum),
    "Alter": alter,
    "Geschlecht": geschlecht,
    "Indikation": indikation,
    "Geplantes Verfahren": verfahren,
}
vals = {
    "DS14_NA": ds_na, "DS14_SI": ds_si, "Type_D": type_d, "PHQ9": phq9, "GAD7": gad7,
    "PCS_Total": pcs_total, "FABQ_PA": fabq_pa, "FABQ_W": fabq_w, "FABQ_erhoeht": fabq_erh,
    "ODI_percent": odi_percent, "Beschwerdedauer_Monate": dauer, "Praeop_Opioide": opioide,
    "Revision": revision, "Surgical_Trauma_Score": trauma
}
text = befundtext(patient, vals, score, risk_de, pfad, empfehlung)

with tab4:
    st.header("Spine-PROTECT Auswertung")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Spine-PROTECT Score", f"{score}/15")
    with c2:
        risiko_ampel(risk_de, emoji, color, score)
        st.subheader(pfad)
        st.write(empfehlung)
    st.dataframe(pd.DataFrame(component_table, columns=["Komponente","Wert","Punkte","Interpretation"]), use_container_width=True, hide_index=True)

with tab5:
    st.header("Befundtext und Export")
    st.text_area("Automatisch generierter Befundtext", text, height=420)
    result = {**patient, **vals, "Spine_PROTECT_Score": score, "Risk_Class": risk_en, "Risikoklasse_DE": risk_de, "Behandlungspfad": pfad, "Empfehlung": empfehlung, "Timestamp": datetime.now().isoformat(timespec="seconds")}
    df_export = pd.DataFrame([result])
    st.download_button("Einzelfall als CSV herunterladen", df_export.to_csv(index=False).encode("utf-8-sig"), f"spine_protect_einzelfall_{patient_id or 'case'}.csv", "text/csv")

    if "registry" not in st.session_state:
        st.session_state["registry"] = []
    if st.button("Fall zur Studien-Datenbank hinzufügen"):
        st.session_state["registry"].append(result)
        st.success("Fall wurde zur Sitzungs-Studien-Datenbank hinzugefügt.")
    if st.session_state["registry"]:
        reg = pd.DataFrame(st.session_state["registry"])
        st.dataframe(reg, use_container_width=True, hide_index=True)
        st.download_button("Studien-Datenbank als CSV herunterladen", reg.to_csv(index=False).encode("utf-8-sig"), "spine_protect_studienregister.csv", "text/csv")

    pdf = make_pdf(patient, {"score": score, "risk_de": risk_de, "pfad": pfad, "empfehlung": empfehlung}, component_table, text)
    if pdf:
        st.download_button("PDF-Bericht herunterladen", pdf, f"spine_protect_bericht_{patient_id or 'case'}.pdf", "application/pdf")

with tab6:
    st.header("Dokumentation und Score-Logik")
    st.markdown("""
### Spine-PROTECT Score v1.1

**Psychosoziale Komponenten**
- Type-D positiv: +2
- PHQ-9 ≥10: +1
- GAD-7 ≥10: +1
- PCS 20–29: +1; PCS ≥30: +2
- FABQ-PA >15 oder FABQ-W >34: +1

**Klinisch-chirurgische Komponenten**
- Beschwerdedauer >12 Monate: +1
- Präoperativer Opioidgebrauch: +2
- ODI ≥41%: +1
- Revisionseingriff: +2
- Surgical Trauma Score 4–5: +2

**Risikoklassen**
- 🟢 0–4 Punkte: Low Risk
- 🟡 5–8 Punkte: Intermediate Risk
- 🔴 ≥9 Punkte: High Risk

**Datenschutz**
Diese öffentliche Streamlit-Version sollte nur mit anonymisierten Studien-IDs verwendet werden.
Für echte Patientendaten wird eine lokale oder klinikinterne Version empfohlen.
""")
