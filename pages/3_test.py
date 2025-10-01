import streamlit as st
import json
from github import Github
from datetime import date, timedelta
from streamlit_calendar import calendar
from github.GithubException import GithubException
import base64

#Repo-Infos
GITHUB_USER="DST81"
REPO_NAME="openlibrary-kontrolle"
BRANCH= "main"
FILE_PATH = "arbeitsplan.json"

token=st.secrets['github_token']
g=Github(token)
repo= g.get_user(GITHUB_USER).get_repo(REPO_NAME)

import json, base64
from datetime import date, timedelta
import streamlit as st
from github import GithubException

# Pfad zur neuen Datei
FILE_PATH_ARBEITSPLAN = "arbeitsplan.json"

# === Laden & Speichern für Arbeitsplan ===
def load_planung():
    try:
        contents = repo.get_contents(FILE_PATH_ARBEITSPLAN, ref=BRANCH)
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except Exception:
        return {}, None   # leere Planung beim ersten Start

def save_planung(planung, sha):
    new_content = json.dumps(planung, indent=2, ensure_ascii=False)
    commit_message = f"Update Arbeitsplan am {date.today().isoformat()}"
    try:
        if sha:
            repo.update_file(FILE_PATH_ARBEITSPLAN, commit_message, new_content, sha, branch=BRANCH)
        else:
            repo.create_file(FILE_PATH_ARBEITSPLAN, commit_message, new_content, branch=BRANCH)
    except GithubException as e:
        if e.status == 422 and "already exists" in str(e):
            contents = repo.get_contents(FILE_PATH_ARBEITSPLAN, ref=BRANCH)
            repo.update_file(FILE_PATH_ARBEITSPLAN, commit_message, new_content, contents.sha, branch=BRANCH)
        else:
            raise
    contents = repo.get_contents(FILE_PATH_ARBEITSPLAN, ref=BRANCH)
    return contents.sha

# === Mitarbeiter-Avatare ===
avatars = {
    "Aniko": "avatars/aniko.png",
    "Daniela": "avatars/daniela.png",
    "Debora": "avatars/debora.png",
    "Janine": "avatars/janine.png",
    "Sarah": "avatars/sarah.png",
    "Susanne": "avatars/susanne.png"
}

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

avatars_b64 = {name: img_to_base64(path) for name, path in avatars.items()}

# === Daten laden ===
planung, sha = load_planung()

# === UI Setup ===
st.set_page_config(page_title='Arbeitsplanung', page_icon='📅', layout='wide')
st.title('Arbeitsplanung - Termine')

# Startdatum = Montag dieser Woche
if "start_date" not in st.session_state:
    today = date.today()
    st.session_state.start_date = today - timedelta(days=today.weekday())

start_date = st.session_state.start_date
days = [start_date + timedelta(days=i) for i in range(7)]
wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
zeiten = ['Morgen', 'Nachmittag']

# === Tabelle mit Slots ===
cols = st.columns(7)
for col, tag, wd in zip(cols, days, wochentage):
    tag_str = tag.isoformat()
    eintrag = planung.get(tag_str, {"oeffnungszeiten": {z: [] for z in zeiten}, "klassenbesuch": None, "bemerkung": ""})

    col.markdown(f"### {wd} {tag.day}.{tag.month}")
    
    # Öffnungszeiten anzeigen
    for zeit in zeiten:
        personen = eintrag["oeffnungszeiten"].get(zeit, [])
        col.write(f"**{zeit}:**")
        for p in personen:
            if p in avatars_b64:
                col.markdown(
                    f"<img src='data:image/png;base64,{avatars_b64[p]}' width='30' style='border-radius:50%;'> {p}",
                    unsafe_allow_html=True
                )

    # Klassenbesuch / Bemerkung
    if eintrag.get("klassenbesuch"):
        col.info(f"📝 {eintrag['klassenbesuch']}")
    if eintrag.get("bemerkung"):
        col.caption(f"💡 {eintrag['bemerkung']}")

# === Formular für neuen Eintrag ===
st.subheader("📌 Termin hinzufügen")

datum = st.date_input("Datum", value=start_date)
zeit_slot = st.selectbox("Zeit", zeiten)
oeffnungszeiten = st.multiselect("Wer übernimmt die Ausleihe?", list(avatars.keys()))
klassenbesuch = st.text_input("Klassenbesuch (optional)")
bemerkung = st.text_area("Bemerkung (optional)")

if st.button("💾 Speichern"):
    tag_str = datum.isoformat()
    if tag_str not in planung:
        planung[tag_str] = {
            "oeffnungszeiten": {z: [] for z in zeiten},
            "klassenbesuch": None,
            "bemerkung": ""
        }
    planung[tag_str]["oeffnungszeiten"][zeit_slot] = oeffnungszeiten
    planung[tag_str]["klassenbesuch"] = klassenbesuch if klassenbesuch else None
    planung[tag_str]["bemerkung"] = bemerkung if bemerkung else ""
    
    sha = save_planung(planung, sha)
    st.success(f"Termin für {datum.strftime('%d.%m.%Y')} gespeichert ✅")
    st.rerun()
