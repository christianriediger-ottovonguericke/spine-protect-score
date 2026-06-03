# Spine-PROTECT Score v1.1

Deutschsprachige Streamlit-App für psychosozial erweiterte präoperative Risikostratifizierung vor elektiver Wirbelsäulenoperation.

## Funktionen

- Passwortschutz über Streamlit Secrets
- Deutsche Oberfläche
- DS14, PHQ-9, GAD-7, PCS, FABQ und ODI
- Klinisch-chirurgische Faktoren
- Surgical Trauma Score
- Risikoampel
- Automatischer Befundtext
- Einzelfall-CSV
- Sitzungsbasierte Studien-Datenbank als CSV
- PDF-Bericht

## Secrets

APP_PASSWORD = "SpineProtect2026"

## Start lokal

pip install -r requirements.txt
streamlit run app.py
