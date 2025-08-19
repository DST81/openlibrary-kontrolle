import streamlit as st
import json
from github import Github
from datetime import date, timedelta
from github.GithubException import GithubException
import base64

# ----------------- Repo-Infos -----------------
GITHUB_USER = "DST81"
REPO_NAME = "openlibrary-kontrolle"
BRANCH = "main"
FILE_PATH = "kontrollen.json"

token = st.secrets['github_token']
g = Github(token)
repo = g.get_user(GITHUB_USER).get_repo(REPO_NAME)

# ----------------- Hilfsfunktionen -----------------
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
    if all(k in raw_data for k in ["kontrollen", "wochenverantwortung", "planung"]):
        return raw_data
    kontrollen = raw_data.get("kontrollen", {})
    wochenverantwortung = raw_data.get("wochenverantwortung", {})
    planung = raw_data.get("planung", {})
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

# ----------------- Mitarbeiter-Avatare -----------------
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

# ----------------- Daten laden -----------------
raw_data, sha = load_kontrollen()
raw_data = migrate_kontrollen_if_needed(raw_data)
kontrollen = raw_data['kontrollen']
wochenverantwortung = raw_data["wochenverantwortung"]
planung = raw_data["planung"]

# ----------------- Streamlit Setup -----------------
st.set_page_config(page_title='Arbeitsplanung', page_icon='📅', layout='wide')
st.title('Arbeitsplanung - Termine')

if "start_date" not in st.session_state:
    today = date.today()
    st.session_state.start_date = today - timedelta(days=today.weekday())

start_date = st.session_state.start_date
days = [start_date + timedelta(days=i) for i in range(7)]
wochentage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
zeiten = ['Morgen', 'Nachmittag', 'Abend']
slot_height = 120  # feste Höhe pro Slot

# ----------------- Wochentage anzeigen -----------------
cols = st.columns(7)
for col, tag, wd in zip(cols, days, wochentage):
    col.markdown(
        f"<div style='border:1px solid #ddd; padding:5px; text-align:center; font-weight:bold;'>"
        f"{wd} {tag.day}.{tag.month}"
        f"</div>", unsafe_allow_html=True
    )

# ----------------- Slots mit Avataren und Checkbox -----------------
always_active_slots = {
    "Tuesday": ["Nachmittag"],
    "Wednesday": ["Morgen"],
    "Thursday": ["Morgen", "Nachmittag"],
    "Friday": ["Morgen"],
    "Saturday": ["Morgen"]
}

if 'slot_overrides' not in st.session_state:
    st.session_state['slot_overrides'] = {}

cols = st.columns(7)
for col, tag in zip(cols, days):
    tag_str = tag.isoformat()
    wochentag = tag.strftime("%A")
    if tag_str not in st.session_state['slot_overrides']:
        st.session_state['slot_overrides'][tag_str] = {}

    for zeit in zeiten:
        default_active = zeit in always_active_slots.get(wochentag, [])
        override = st.session_state['slot_overrides'][tag_str].get(zeit, None)
        slot_needed = override if override is not None else default_active

        # Hintergrundfarbe
        if slot_needed and override is None:
            bg_color = "#c6f5c6"
        elif slot_needed and override:
            bg_color = "#f9e6c6"
        elif not slot_needed and override is False:
            bg_color = "#f5c6c6"
        else:
            bg_color = "#f9f9f9"

        # Slot-Box mit fester Höhe
        with col:
            st.markdown(
                f"<div style='border:1px solid #ccc; min-height:{slot_height}px; "
                f"margin-bottom:5px; padding:5px; background-color:{bg_color}; "
                f"display:flex; align-items:center;">
                f"<div style='flex:1;'><b>{zeit}</b></div>"
                f"</div>", unsafe_allow_html=True
            )

            # Checkbox + Avatare horizontal
            inner_cols = st.columns([1, 3])
            with inner_cols[0]:
                changed = st.checkbox("", value=slot_needed, key=f"override_{tag_str}_{zeit}")
                st.session_state['slot_overrides'][tag_str][zeit] = (
                    changed if changed != default_active else None
                )

            with inner_cols[1]:
                slot_personen = planung.get(tag_str, {}).get('oeffnungszeiten', {}).get(zeit, [])
                for p in slot_personen:
                    if p in avatars_b64:
                        st.image(avatars_b64[p], width=30, caption=p)

# ----------------- Klassenbesuche + Bemerkungen -----------------
cols = st.columns(7)
for col, tag in zip(cols, days):
    tag_str = tag.isoformat()
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

# ----------------- Neues Event hinzufügen -----------------
st.subheader("📌 Termin hinzufügen")

datum = st.date_input("Datum", value=st.session_state.start_date or date.today())
existing = planung.get(datum.isoformat(), {})
default_oeffnungszeiten = existing.get("oeffnungszeiten", {})
default_klassenbesuch = existing.get("klassenbesuch", "")
default_bemerkung = existing.get("bemerkung", "")

zeit_slot = st.selectbox('Zeit', zeiten)
selected_personen = default_oeffnungszeiten.get(zeit_slot, [])
oeffnungszeiten = st.multiselect("Wer übernimmt die Ausleihe?", list(avatars.keys()), default=selected_personen)
klassenbesuch = st.text_input("Klassenbesuch (optional)", value=default_klassenbesuch)
bemerkung = st.text_area("Bemerkung (optional)", value=default_bemerkung)

if st.button("💾 Speichern"):
    tag_str = str(datum)
    if tag_str not in planung:
        planung[tag_str] = {
            "oeffnungszeiten": {z: [] for z in zeiten},
            "klassenbesuch": None,
            "bemerkung": None
        }
    planung[tag_str]["oeffnungszeiten"][zeit_slot] = oeffnungszeiten
    planung[tag_str]["klassenbesuch"] = klassenbesuch or None
    planung[tag_str]["bemerkung"] = bemerkung or None

    sha = save_kontrollen({
        "kontrollen": kontrollen,
        "wochenverantwortung": wochenverantwortung,
        "planung": planung
    }, sha)
    st.success("Termin gespeichert ✅")
    st.rerun()
