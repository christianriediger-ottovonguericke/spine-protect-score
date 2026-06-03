
import streamlit as st
from datetime import date
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

st.set_page_config(page_title="Spine-PROTECT Score", page_icon="🧠", layout="wide")

def risk_class(score: int):
    if score <= 4:
        return "LOW RISK", "Standard pathway", "Standard preoperative counselling, regular perioperative care and routine follow-up."
    if score <= 8:
        return "INTERMEDIATE RISK", "Enhanced counselling", "Additional expectation management, written recovery plan, early physiotherapy and structured pain-medication planning."
    return "HIGH RISK", "Enhanced Spine Pathway", "Preoperative pain consultation, psychosomatic short assessment, opioid strategy, prehabilitation and close follow-up at 2, 6 and 12 weeks."

def badge(text, color):
    st.markdown(f"""
    <div style="background-color:{color};color:white;padding:18px;border-radius:12px;
    text-align:center;font-size:26px;font-weight:700;margin-bottom:12px;">{text}</div>
    """, unsafe_allow_html=True)

def phq_category(score):
    if score < 10: return "unauffällig / minimal bis leicht"
    if score < 15: return "leichtgradig klinisch relevant"
    if score < 20: return "mittelgradig"
    return "schwer"

def gad_category(score):
    if score < 5: return "normal bis mild"
    if score < 10: return "mild"
    if score < 15: return "mittelgradig"
    return "schwer"

def pcs_category(score):
    if score < 20: return "niedrig"
    if score < 30: return "moderat"
    return "hoch"

def odi_category(score):
    if score <= 20: return "minimale Funktionseinschränkung"
    if score <= 40: return "moderate Funktionseinschränkung"
    if score <= 60: return "starke Funktionseinschränkung"
    if score <= 80: return "sehr starke Funktionseinschränkung"
    return "pflegebedürftig / psychosozial extrem überlagert"

def make_pdf(patient, results, component_table):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph("<b>Spine-PROTECT Score Report</b>", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph("<b>Patient / Case Information</b>", styles["Heading2"]))
    t = Table([[k, str(v)] for k, v in patient.items()], colWidths=[150, 330])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E0F2F1")),("GRID",(0,0),(-1,-1),0.25,colors.grey)]))
    story += [t, Spacer(1, 14), Paragraph("<b>Result</b>", styles["Heading2"])]
    result_rows = [["Spine-PROTECT Score", str(results["score"])],["Risk class", results["risk"]],["Pathway", results["pathway"]],["Recommendation", results["recommendation"]]]
    t = Table(result_rows, colWidths=[150, 330])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#DBEAFE")),("GRID",(0,0),(-1,-1),0.25,colors.grey)]))
    story += [t, Spacer(1, 14), Paragraph("<b>Score Components</b>", styles["Heading2"])]
    rows = [["Component","Value","Points","Interpretation"]] + component_table
    t = Table(rows, colWidths=[130, 90, 60, 200])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0F766E")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),8)]))
    story += [t, Spacer(1, 14)]
    story.append(Paragraph("Note: This tool is intended for structured clinical risk stratification and research use. It does not replace medical judgment, surgical indication, psychiatric diagnosis or emergency assessment.", styles["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer

st.sidebar.title("Spine-PROTECT")
st.sidebar.caption("Clinical Decision Tool v1.0")
st.sidebar.info("Use anonymized study IDs for research or cloud deployment.")
st.sidebar.markdown("**Thresholds:** 0–4 Low, 5–8 Intermediate, ≥9 High")

st.title("Spine-PROTECT Score")
st.subheader("Psychosocially enhanced clinical decision tool for elective spine surgery")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 Patient", "2 Questionnaires", "3 Clinical / Surgery", "4 Result", "5 Documentation"])

with tab1:
    st.header("Patient / Case Information")
    c1, c2, c3 = st.columns(3)
    with c1:
        patient_id = st.text_input("Study / Patient ID", value="")
        exam_date = st.date_input("Date", value=date.today())
    with c2:
        age = st.number_input("Age", min_value=18, max_value=100, value=60)
        sex = st.selectbox("Sex", ["", "Female", "Male", "Diverse"])
    with c3:
        indication = st.text_input("Indication", value="")
        planned_surgery = st.text_input("Planned surgery", value="")

with tab2:
    st.header("Psychosocial Screening")
    with st.expander("DS14 – Type-D Personality", expanded=True):
        st.caption("Enter the 14 DS14 item scores according to the official validated questionnaire. Scale: 0–4.")
        ds_cols = st.columns(7)
        ds_values = []
        for i in range(14):
            with ds_cols[i % 7]:
                ds_values.append(st.number_input(f"DS14 item {i+1}", 0, 4, 0, key=f"ds{i+1}"))
        ds_na = sum(ds_values[i-1] for i in [2,4,5,7,9,11,12])
        ds_si = sum(ds_values[i-1] for i in [1,3,6,8,10,13,14])
        type_d_positive = ds_na >= 10 and ds_si >= 10
        st.write(f"Negative Affectivity: **{ds_na}/28**")
        st.write(f"Social Inhibition: **{ds_si}/28**")
        st.write(f"Type-D positive: **{'Yes' if type_d_positive else 'No'}**")

    with st.expander("PHQ-9 – Depressive symptoms"):
        phq_values = [st.slider(f"PHQ-9 item {i+1}", 0, 3, 0, key=f"phq{i+1}") for i in range(9)]
        phq9 = sum(phq_values)
        st.write(f"PHQ-9 total: **{phq9}/27** – {phq_category(phq9)}")
        if phq_values[8] > 0:
            st.error("PHQ-9 item 9 is positive. This requires immediate clinical evaluation according to local procedures.")

    with st.expander("GAD-7 – Anxiety symptoms"):
        gad_values = [st.slider(f"GAD-7 item {i+1}", 0, 3, 0, key=f"gad{i+1}") for i in range(7)]
        gad7 = sum(gad_values)
        st.write(f"GAD-7 total: **{gad7}/21** – {gad_category(gad7)}")

    with st.expander("PCS – Pain Catastrophizing Scale"):
        pcs_values = [st.slider(f"PCS item {i+1}", 0, 4, 0, key=f"pcs{i+1}") for i in range(13)]
        pcs_total = sum(pcs_values)
        pcs_helplessness = sum(pcs_values[i-1] for i in [1,2,3,4,5,12])
        pcs_magnification = sum(pcs_values[i-1] for i in [6,7,13])
        pcs_rumination = sum(pcs_values[i-1] for i in [8,9,10,11])
        st.write(f"PCS total: **{pcs_total}/52** – {pcs_category(pcs_total)}")
        st.write(f"Helplessness: {pcs_helplessness}; Magnification: {pcs_magnification}; Rumination: {pcs_rumination}")

    with st.expander("FABQ – Fear Avoidance Beliefs Questionnaire"):
        fabq_cols = st.columns(4)
        fabq_values = []
        for i in range(16):
            with fabq_cols[i % 4]:
                fabq_values.append(st.number_input(f"FABQ item {i+1}", 0, 6, 0, key=f"fabq{i+1}"))
        fabq_pa = sum(fabq_values[i-1] for i in [2,3,4,5])
        fabq_w = sum(fabq_values[i-1] for i in [6,7,9,10,11,12,15])
        fabq_elevated = fabq_pa > 15 or fabq_w > 34
        st.write(f"FABQ-PA: **{fabq_pa}/24**")
        st.write(f"FABQ-W: **{fabq_w}/42**")
        st.write(f"FABQ elevated: **{'Yes' if fabq_elevated else 'No'}**")

    with st.expander("ODI – Oswestry Disability Index"):
        odi_categories = ["Pain intensity","Personal care","Lifting","Walking","Sitting","Standing","Sleeping","Sex life","Social life","Traveling"]
        odi_cols = st.columns(5)
        odi_values = []
        for i, name in enumerate(odi_categories):
            with odi_cols[i % 5]:
                odi_values.append(st.number_input(name, 0, 5, 0, key=f"odi{i+1}"))
        odi_raw = sum(odi_values)
        odi_percent = odi_raw * 2
        st.write(f"ODI raw score: **{odi_raw}/50**")
        st.write(f"ODI: **{odi_percent}%** – {odi_category(odi_percent)}")

with tab3:
    st.header("Clinical and Surgical Risk Factors")
    c1, c2 = st.columns(2)
    with c1:
        symptoms_months = st.number_input("Symptom duration in months", 0, 360, 0)
        preop_opioids = st.radio("Preoperative opioid use", ["No", "Yes"], horizontal=True)
        revision = st.radio("Revision procedure", ["No", "Yes"], horizontal=True)
    with c2:
        surgical_trauma_label = st.selectbox("Surgical Trauma Score", [
            "1 = microsurgical decompression",
            "2 = open decompression",
            "3 = one-level fusion",
            "4 = multisegment fusion",
            "5 = revision / deformity / long-segment fusion"
        ])
        surgical_trauma_score = int(surgical_trauma_label[0])
    st.table(pd.DataFrame({"Score":[1,2,3,4,5],"Procedure":["microsurgical decompression","open decompression","one-level fusion","multisegment fusion","revision / deformity / long-segment fusion"],"Spine-PROTECT points":[0,0,0,2,2]}))

points_type_d = 2 if type_d_positive else 0
points_phq9 = 1 if phq9 >= 10 else 0
points_gad7 = 1 if gad7 >= 10 else 0
points_pcs = 2 if pcs_total >= 30 else 1 if pcs_total >= 20 else 0
points_fabq = 1 if fabq_elevated else 0
points_symptoms = 1 if symptoms_months > 12 else 0
points_opioids = 2 if preop_opioids == "Yes" else 0
points_odi = 1 if odi_percent >= 41 else 0
points_revision = 2 if revision == "Yes" else 0
points_trauma = 2 if surgical_trauma_score >= 4 else 0

total_score = sum([points_type_d, points_phq9, points_gad7, points_pcs, points_fabq, points_symptoms, points_opioids, points_odi, points_revision, points_trauma])
risk, pathway, recommendation = risk_class(total_score)

component_table = [
    ["Type-D", f"NA {ds_na}, SI {ds_si}", points_type_d, "positive" if type_d_positive else "negative"],
    ["PHQ-9", phq9, points_phq9, phq_category(phq9)],
    ["GAD-7", gad7, points_gad7, gad_category(gad7)],
    ["PCS", pcs_total, points_pcs, pcs_category(pcs_total)],
    ["FABQ", f"PA {fabq_pa}, W {fabq_w}", points_fabq, "elevated" if fabq_elevated else "not elevated"],
    ["Symptom duration", f"{symptoms_months} months", points_symptoms, ">12 months" if symptoms_months > 12 else "≤12 months"],
    ["Preop opioids", preop_opioids, points_opioids, ""],
    ["ODI", f"{odi_percent}%", points_odi, odi_category(odi_percent)],
    ["Revision", revision, points_revision, ""],
    ["Surgical trauma", surgical_trauma_score, points_trauma, surgical_trauma_label],
]

with tab4:
    st.header("Spine-PROTECT Result")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.metric("Spine-PROTECT Score", f"{total_score}/15")
    with c2:
        badge(risk, "#16A34A" if risk == "LOW RISK" else "#D97706" if risk == "INTERMEDIATE RISK" else "#DC2626")
    with c3:
        st.subheader(pathway)
        st.write(recommendation)

    st.dataframe(pd.DataFrame(component_table, columns=["Component","Value","Points","Interpretation"]), use_container_width=True, hide_index=True)

    patient_info = {"Study / Patient ID": patient_id, "Date": str(exam_date), "Age": age, "Sex": sex, "Indication": indication, "Planned surgery": planned_surgery}
    result_info = {"score": total_score, "risk": risk, "pathway": pathway, "recommendation": recommendation}

    df_export = pd.DataFrame([{**patient_info, "DS14_NA": ds_na, "DS14_SI": ds_si, "Type_D": type_d_positive, "PHQ9": phq9, "GAD7": gad7, "PCS_Total": pcs_total, "FABQ_PA": fabq_pa, "FABQ_W": fabq_w, "ODI_percent": odi_percent, "Symptoms_months": symptoms_months, "Preop_opioids": preop_opioids, "Revision": revision, "Surgical_Trauma_Score": surgical_trauma_score, "Spine_PROTECT_Score": total_score, "Risk_Class": risk, "Recommendation": recommendation}])
    st.download_button("Download result as CSV", data=df_export.to_csv(index=False).encode("utf-8"), file_name=f"spine_protect_result_{patient_id or 'case'}.csv", mime="text/csv")

    pdf = make_pdf(patient_info, result_info, component_table)
    if pdf:
        st.download_button("Download PDF report", data=pdf, file_name=f"spine_protect_report_{patient_id or 'case'}.pdf", mime="application/pdf")

with tab5:
    st.header("Documentation")
    st.markdown("""
### Spine-PROTECT Score v1.0

**Psychosocial components**
- Type-D positive: +2
- PHQ-9 ≥10: +1
- GAD-7 ≥10: +1
- PCS 20–29: +1; PCS ≥30: +2
- FABQ-PA >15 or FABQ-W >34: +1

**Clinical-surgical components**
- Symptom duration >12 months: +1
- Preoperative opioid use: +2
- ODI ≥41%: +1
- Revision procedure: +2
- Surgical Trauma Score 4–5: +2

**Risk classes**
- 0–4: Low Risk
- 5–8: Intermediate Risk
- ≥9: High Risk

This app is a research and clinical decision-support prototype.
It does not replace clinical judgment, surgical indication, psychological assessment or emergency evaluation.
""")
