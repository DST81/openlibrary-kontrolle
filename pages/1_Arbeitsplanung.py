import streamlit as st
import json
from github import Github
from datetime import date, timedelta
from streamlit_calendar import calendar
from github.GithubException import GithubException

#Repo-Infos
GITHUB_USER="DST81"
REPO_NAME="openlibrary-kontrolle"
BRANCH= "main"
FILE_PATH = "kontrollen.json"

token=st.secrets['github_token']
g=Github(token)
repo= g.get_user(GITHUB_USER).get_repo(REPO_NAME)

# === Hilfsfunktionen ===
def load_kontrollen():
    try:
        contents = repo.get_contents(FILE_PATH, ref=BRANCH)
        data = json.loads(contents.decoded_content.decode())
        return data, contents.sha
    except Exception:
        return {}, None

def save_kontrollen(data_dict, sha):
    new_content = json.dumps(data_dict, indent=2, ensure_ascii=False)
    commit_message = f"Update Kontrollen/Planung am {date.today().isoformat()}"
    try:
        if sha:
            repo.update_file(FILE_PATH, commit_message, new_content, sha, branch=BRANCH)
        else:
            repo.create_file(FILE_PATH, commit_message, new_content, branch=BRANCH)
    except GithubException as e:
        if e.status == 422 and "already exists" in str(e):
            contents = repo.get_contents(FILE_PATH, ref=BRANCH)
            repo.update_file(FILE_PATH, commit_message, new_content, contents.sha, branch=BRANCH)
        else:
            raise
    contents = repo.get_contents(FILE_PATH, ref=BRANCH)
    return contents.sha

def migrate_kontrollen_if_needed(raw_data):
    # Falls schon alles vorhanden ist
    if all(k in raw_data for k in ["kontrollen", "wochenverantwortung", "planung"]):
        return raw_data
    kontrollen = raw_data.get("kontrollen", {})
    wochenverantwortung = raw_data.get("wochenverantwortung", {})
    planung = raw_data.get("planung", {})
    # Falls alte Struktur (nur Datumsschlüssel) → migrieren
    if not kontrollen and any(k for k in raw_data.keys() if "-" in k):
        for key, value in raw_data.items():
            try:
                date.fromisoformat(key)
                kontrollen[key] = value
            except ValueError:
                pass
    return {
        "kontrollen": kontrollen,
        "wochenverantwortung": wochenverantwortung,
        "planung": planung
    }

# === Mitarbeiter-Avatare ===
avatars = {
    "Aniko": "avatars/aniko.png",
    "Daniela": "avatars/daniela.png",
    "Debora": "avatars/debora.png",
    "Janine": "avatars/janine.png",
    "Sarah": "avatars/sarah.png",
    "Susanne": "avatars/susanne.png"
}

st.set_page_config(page_title='Arbeitsplanung & Termine', page_icon='📅', layout='wide')

raw_data,sha  = load_kontrollen()
raw_data = migrate_kontrollen_if_needed(raw_data)
kontrollen = raw_data['kontrollen']
wochenverantwortung = raw_data["wochenverantwortung"]
planung = raw_data["planung"]

events=[]
for tag, details in planung.items():
  if 'oeffnungszeiten' in details and details['oeffnungszeiten']:
    avatar_html=' '.join([f'<img src="{avatars[p]}" width="30" height="30">' 
                                for p in details["oeffnungszeiten"] if p in avatars])
    events.append({
      'title':avatar_html,
      'start':tag
    })
    if "klassenbesuch" in details and details["klassenbesuch"]:
      events.append({
          "title": "Klassenbesuch: " + details["klassenbesuch"],
          "start": tag
      })
  if "bemerkung" in details and details["bemerkung"]:
      events.append({
          "title": "Bemerkung: " + details["bemerkung"],
          "start": tag
      })  

calendar_options = {
    "initialView": "timeGridWeek",
    "locale": "de",
    "events": events
}

calendar(events=events, options=calendar_options)

# === Neues Event hinzufügen ===
st.subheader("📌 Termin hinzufügen")
datum = st.date_input("Datum", date.today())
oeffnungszeiten = st.multiselect("Wer übernimmt die Öffnungszeit?", list(avatars.keys()))
klassenbesuch = st.text_input("Klassenbesuch (optional)")
bemerkung = st.text_area("Bemerkung (optional)")

if st.button("💾 Speichern"):
    planung[str(datum)] = {
        "oeffnungszeiten": oeffnungszeiten if oeffnungszeiten else None,
        "klassenbesuch": klassenbesuch if klassenbesuch else None,
        "bemerkung": bemerkung if bemerkung else None
    }
    sha = save_kontrollen({
        "kontrollen": kontrollen,
        "wochenverantwortung": wochenverantwortung,
        "planung": planung
    }, sha)
    st.success("Termin gespeichert ✅")
