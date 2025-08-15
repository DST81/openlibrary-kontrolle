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


raw_data,sha  = load_kontrollen()
raw_data = migrate_kontrollen_if_needed(raw_data)
kontrollen = raw_data['kontrollen']
wochenverantwortung = raw_data["wochenverantwortung"]
planung = raw_data["planung"]

st.set_page_config(page_title='Arbeitsplanung & Termine version 2', page_icon='📅', layout='wide')
            
st.title('Arbeitsplanung - Termine')

if "start_date" not in st.session_state:
    #aktueller Wochenanfang(Montag)
    today=date.today()
    st.session_state.start_date=today-timedelta(days=today.weekday())

col1, col2, col3 = st.columns([1,2,1])

with col2: 
    selected_date= st.date_input(
        "Springe zu Datum", 
        value=st.session_state.start_date,
        key='date_jump_input'
    )
    if selected_date != st.session_state.start_date:
        st.session_state.start_date=selected_date - timedelta(days=selected_date.weekday())

if "start_date" not in st.session_state:
    #aktueller Wochenanfang(Montag)
    today=data.today()
    st.session_state.start_date=today-timedelat(days=today.weekday())
     
start_date= st.session_state.start_date
days =[start_date + timedelta(days=i) for i in range(7)]
wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
zeiten=['Morgen','Nachmittag','Abend']


# Erste Reihe: Wochentage + Datum
cols=st.columns(7)
for col, tag, wd in zip(cols,days, wochentage):
    col.markdown(
        f"<div style='border:1px solid #ddd; padding:5px; text-align:center; font-weight:bold;'>"
        f"{wd} {tag.day}.{tag.month}"
        f"</div>", unsafe_allow_html=True
    )

#Zweite Reihe: Unterteilung in Morgen, Nachmittag und Abend mit Avatare + Namen
cols=st.columns(7)
for col, tag in zip(cols,days):
    tag_str = tag.isoformat()
    with col:
        for zeit in zeiten:
            st.markdown(
                f"<div style='border:1px solid #ddd; padding:5px; min-height:60px; text-align:center;'>"
                f"<b>{zeit}</b><br>", 
                unsafe_allow_html=True
            ) 
        oeffnungszeiten = planung.get(tag_str, {}).get('oeffnungszeiten')  # kann None sein
        if oeffnungszeiten: 
            avatar_cols=col.columns(len(oeffnungszeiten))
            for ac, p in zip(avatar_cols,oeffnungszeiten):
                if p in avatars:
                    ac.image(avatars[p],width=40)
                    ac.caption(p)
        st.markdown("</div>", unsafe_allow_html=True)

#Dritte Reihe: Klassenbesuche + Bemerkungen
cols=st.columns(7)
for col, tag in zip(cols,days):
    tag_str=tag.isoformat()
    details = planung.get(tag_str, {})
    text = ""
    if details.get("klassenbesuch"):
        text += f"📝 {details['klassenbesuch']}<br>"
    if details.get("bemerkung"):
        text += f"💡 {details['bemerkung']}<br>"
    col.markdown(
        f"<div style='border:1px solid #ddd; padding:5px; min-height:40px; text-align:left;'>{text}</div>",
        unsafe_allow_html=True
    )
    
# === Neues Event hinzufügen ===
st.subheader("📌 Termin hinzufügen")

datum = st.date_input("Datum", date.today())
oeffnungszeiten = st.multiselect("Wer übernimmt die Öffnungszeit?", list(avatars.keys()))
klassenbesuch = st.text_input("Klassenbesuch (optional)")
bemerkung = st.text_area("Bemerkung (optional)")

events=[]
for tag, details in planung.items():
  if 'oeffnungszeiten' in details and details['oeffnungszeiten']:
    events.append({
      'title':', '.join(details['oeffnungszeiten']),
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
