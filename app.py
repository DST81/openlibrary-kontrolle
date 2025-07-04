import streamlit as st
import json
import os
from github import Github
from datetime import date, timedelta
import math
from babel.dates import format_date

#Repo-Infos
GITHUB_USER="DST81"
REPO_NAME="openlibrary-kontrolle"
BRANCH= "main"
FILE_PATH = "kontrollen.json"

token=st.secrets['github_token']
g=Github(token)
repo= g.get_user(GITHUB_USER).get_repo(REPO_NAME)

# Kalenderwoche bestimmen
today = date.today()
year, week, _ = today.isocalendar()
kw_key = f"{year}-W{week:02d}"


#Hilfsfunktion
def load_kontrollen():
    try:
        contents = repo.get_contents(FILE_PATH, ref=BRANCH)
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except Exception:
        return {}, None
def save_kontrollen(kontrollen, sha):
    new_content = json.dumps(kontrollen, indent=2, ensure_ascii=False)
    commit_message = f"Update Kontrollen am {date.today().isoformat()}"
    if sha:
        repo.update_file(FILE_PATH, commit_message, new_content, sha, branch=BRANCH)
    else:
        repo.create_file(FILE_PATH, commit_message, new_content, branch=BRANCH)
    #Neustes sha holen für nächsten Update
    contents = repo.get_contents(FILE_PATH, ref=BRANCH)
    return contents.sha


DATE_FORMAT = "%Y-%m-%d"
JSON_FILE = kontrollen
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
    "Bemerkung"
)

# Check-In
heute = date.today().isoformat()
if st.button(f"{mitarbeiter_name} hat heute OpenLibrary kontrolliert"):
    kontrollen[heute] = {
        "mitarbeiter": mitarbeiter_name,
        "bemerkung": bemerkung
        }
    sha = save_kontrollen(kontrollen, sha)
    st.success(f"Danke, {mitarbeiter_name}! – Kontrolle am {heute} erledigt!")

st.markdown("---")

#Editiermodus-Stauts
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None

# Ferienzeitraum (hier anpassen)
ferien_start =date(2025,6,1)
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

monday = today - timedelta(days=today.weekday())
current_week_days = [monday + timedelta(days=i) for i in range(7)]

# Extrahiere Wochenverantwortung oder leere initialisieren
wochenverantwortung = kontrollen.get("wochenverantwortung", {})
aktuell_verantwortliche = wochenverantwortung.get(kw_key, None)

st.markdown(f"## 👩‍💼 Wochenverantwortliche KW {week}")

# Anzeige der aktuellen Verantwortlichen
if aktuell_verantwortliche:
    st.success(f"🧑‍💼 Aktuell zuständig: **{aktuell_verantwortliche}**")
else:
    st.warning("⚠️ Noch keine Wochenverantwortliche zugewiesen.")

# Sicherer Index für Dropdown (wenn aktuell nicht gesetzt, 0 als Default)
if aktuell_verantwortliche in avatars:
    default_index = list(avatars.keys()).index(aktuell_verantwortliche)
else:
    default_index = 0

# Auswahl über Dropdown mit sicherem Default-Index
neue_verantwortliche = st.selectbox(
    "➕ Verantwortliche Person für diese Woche zuweisen:",
    options=list(avatars.keys()),
    index=default_index,
    key="wochenverantwortung_dropdown"
)

# Speichern bei Klick
if st.button("✅ Wochenverantwortliche speichern"):
    kontrollen.setdefault("wochenverantwortung", {})[kw_key] = neue_verantwortliche
    sha = save_kontrollen(kontrollen, sha)
    st.success(f"✅ Verantwortliche für KW {week} ist jetzt: **{neue_verantwortliche}**")
    st.rerun()


st.markdown(f"## 👩‍💼 Wochenverantwortliche KW {week}")


# Speichern bei Klick
if st.button("✅ Wochenverantwortliche speichern"):
    kontrollen.setdefault("wochenverantwortung", {})[kw_key] = neue_verantwortliche
    sha = save_kontrollen(kontrollen, sha)
    st.success(f"✅ Verantwortliche für KW {week} ist jetzt: **{neue_verantwortliche}**")
    st.rerun()
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
            st.markdown(f"**{format_date(tag_date, format='EEE dd.MM', locale='de')}**")

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
                            kontrollen[tag]["bemerkung"] = new_note.strip()
                            sha=save_kontrollen(kontrollen, sha)
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
                            sha= save_kontrollen(kontrollen, sha)
                            st.rerun()
            else:
                st.markdown("❌ nicht kontrolliert")
            st.markdown("</div>", unsafe_allow_html=True)

#Kontrolle und Bemerkung nachtragen
st.markdown('### Kontrolle nachtragen')
kontroll_tag=st.selectbox(
    "Wähle den Tag aus:",
    options= days,
    format_func=lambda d: format_date(d, format='EEE dd.MM.yyyy', locale='de'),
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
        sha=save_kontrollen(kontrollen, sha)
        st.rerun()
        st.success(
            f"Kontrolle am {format_date(kontroll_tag, format='EEE dd.MM.yyyy', locale='de')} von {mitarbeiter} gespeichert!\nBemerkung: {bemerkung}"
        )
