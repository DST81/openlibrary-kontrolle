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

st.set_page_config(page_title='Arbeitsplanung & Termine version 2', page_icon='📅', layout='wide')

raw_data,sha  = load_kontrollen()
raw_data = migrate_kontrollen_if_needed(raw_data)
kontrollen = raw_data['kontrollen']
wochenverantwortung = raw_data["wochenverantwortung"]
planung = raw_data["planung"]

st.title('Arbeitsplanung - Termine')

start_date= date(2025, 8, 11)
days =[start_date + timedelta(days=i) for i in range(7)]

cols=st.columns(7)
for col, tag in zip(cols,days):
  tag_str = tag.isoformat()
  if tag_str in planung and 'oeffnungszeiten' in planung[tag_str]:
    for p in planung[tag_str]['oeffnungszeiten']:
      if p in avatars:
        col.image(avatars[p],width=40)
cols=st.columns(7)
for col, tag in zip(cols,days):
  tag_str=tag.isoformat()
  if tag_str in planung:
    details=planung[tag_str]
    if 'klassenbesuch' in details:
      col.write(f"📝 {details['klassenbesuch']}")
    if 'bemerkung' in details:
      col.write(f"💡 {details['bemerkung']}")
        
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
