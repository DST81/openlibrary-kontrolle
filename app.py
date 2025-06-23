import streamlit as st
import json
import os
from datetime import date, timedelta
import math
from babel.dates import format_date

DATE_FORMAT = "%Y-%m-%d"
JSON_FILE = "kontrollen.json"
st.set_page_config(page_title="OpenLibrary Ferienkontrolle 🧹", page_icon="📚")

#CSS für Karten
st.markdown(
    """
    <style>
    .stImage img {
        border-radius: 50%;
        width: 40px !important;
        height: 40px !important;
        object-fit: cover;
    }
    .card{
        padding: 1rem;
        border-radius: 10px;
        box-shadow:0 0 10px rgba(0,0,0,0.1);
        margin-bottom:1rem;
    }
    .green{ background: #d4edda;} /*kontrolliert*/
    .orange{ background: #fff3cd; } /* in der Nähe einer Kontrolle */
    .red { background: #f8d7da; }    /* nicht kontrolliert */
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📚 OpenLibrary Kontrolle 📚 ")

# Avatare
avatars = {
    "Aniko": "avatars/aniko.png",
    "Daniela": "avatars/daniela.png",
    "Debora": "avatars/debora.png",
    "Janine": "avatars/janine.png",
    "Sarah": "avatars/sarah.png",
    "Susanne": "avatars/susanne.png"
}

# Mitarbeiter auswählen
mitarbeiter_name = st.selectbox(
    "Bitte auswählen, wer du bist:",
    list(avatars.keys())
)

#Bemerkung schreiben
bemerkung =st.text_area(
    "Bemerkung zur Kontrolle"
)

# JSON laden oder neu erstellen
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        kontrollen = json.load(f)
else:
    kontrollen = {}  

# Check-In
heute = date.today().isoformat()
if st.button(f"{mitarbeiter_name} hat heute OpenLibrary kontrolliert"):
    kontrollen[heute] = {
        "mitarbeiter": mitarbeiter_name,
        "bemerkung": bemerkung
        }
    with open("kontrollen.json", "w") as f:
        json.dump(kontrollen, f, indent=2)
    st.success(f"Danke, {mitarbeiter_name}! – Kontrolle erledigt!")

st.markdown("---")

#Editiermodus-Stauts
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None

# Ferienzeitraum (hier anpassen)
ferien_start =date(2025,6,10)
ferien_ende =date(2025,8,31)


#Alle Tage der Ferien iterieren
days_count = (ferien_ende-ferien_start).days+1
days= [ferien_start+timedelta(days=i) for i in range(days_count)]
today=date.today()
days=[d for d in days if d <=today]
weeks=[days[i:i+7] for i in range(0, len(days), 7)]
weeks.reverse()
controlled_days= {date.fromisoformat(t) for t in kontrollen.keys()}

# Diese Woche
st.markdown("### Kontrollierte Tage")
today = date.today()
monday = today - timedelta(days=today.weekday())
current_week_days = [monday + timedelta(days=i) for i in range(7)]

# Tage in Wochenblöcken
for week_days in weeks:
    cols = st.columns(7)  # 7 Spalten für die Woche
    for col, tag_date in zip(cols, week_days):
        tag = tag_date.isoformat()

        # Farbe der Karte berechnen
        if tag_date in controlled_days:
            color_class = "green"
        elif any((tag_date + timedelta(days=d)) in controlled_days for d in range(-2, 3) if d != 0):
            color_class = "orange"
        else:
            color_class = "red"

        with col:
            st.markdown(f'<div class="card {color_class}">', unsafe_allow_html=True)
            st.markdown(f"**{fromat_date(tag_date, format='EEE', locale='de)} {tag_date.strftime('%d.%m')}**")

            if tag in kontrollen:
                checked_by = kontrollen[tag]["mitarbeiter"]
                note = kontrollen[tag].get("bemerkung", "")
                st.image(avatars[checked_by])
                st.markdown(f"**{checked_by}**")

                if st.session_state.edit_mode == tag:
                    new_note = st.text_area(
                        f"Bearbeite Bemerkung:",
                        value=note,
                        key=f"note_input_{tag}"
                    )
                    cols_btn = st.columns(2)
                    with cols_btn[0]:
                        if st.button("💾", key=f"save_{tag}"):
                            kontrollen[tag]["bemerkung"] = new_note
                            with open("kontrollen.json", "w") as f:
                                json.dump(kontrollen, f, indent=2)
                            st.session_state.edit_mode = None
                            st.rerun()
                    with cols_btn[1]:
                        if st.button("❌", key=f"cancel_{tag}"):
                            st.session_state.edit_mode = None
                            st.rerun()
                else:
                    if note:
                        st.caption(f"💬 {note}")
                    cols_btn = st.columns([1, 1])
                    with cols_btn[0]:
                        if st.button("✏️", key=f"edit_{tag}"):
                            st.session_state.edit_mode = tag
                            st.rerun()
                    with cols_btn[1]:
                        if st.button("🗑️", key=f"delete_{tag}"):
                            del kontrollen[tag]
                            with open("kontrollen.json", "w") as f:
                                json.dump(kontrollen, f, indent=2)
                            st.rerun()
            else:
                st.markdown("❌ nicht kontrolliert")
            st.markdown("</div>", unsafe_allow_html=True)

#Kontrolle und Bemerkung
st.markdown('### Kontrolle nachtragen')
kontroll_tag=st.selectbox(
    "Wähle den Tag aus:",
    options= days,
    format_func=lambda d: d.strftime('%a %d.%m.%Y'),
)
mitarbeiter= st.selectbox('Mitarbeiterin auswählen', list(avatars.keys()))
bemerkung = st.text_area('Bemerkung')
if st.button('✅ Kontrolle speichern'):
    if not mitarbeiter.strip():
        st.error('Bitte deinen Namen eingeben!')
    else:
        tag_str=kontroll_tag.strftime(DATE_FORMAT)
        kontrollen[tag_str]={
            "mitarbeiter":mitarbeiter.strip(),
            "bemerkung": bemerkung.strip(),
        }
        with open(JSON_FILE, "w") as f:
            json.dump(kontrollen, f, indent=4)
    st.success(
        f"Kontrolle am {kontroll_tag.strftime('%a %d.%m.%Y')} von {mitarbeiter} gespeichert!\nBemerkung: {bemerkung}"
    )
