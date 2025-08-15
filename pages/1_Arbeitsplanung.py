import streamlit as st
import json
from github import Github
from datetime import date, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title='Arbeitsplanung & Termine', page_icon='📅')

raw_data, sha = load_kontrollen()
data = migrate_kontrollen_if_needed(raw_data)
kontrollen = data.get("kontrollen", {})
wochenverantwortung = data.get("wochenverantwortung", {})
planung = data.get("planung", {})

events=[]
for tag, details in planung.items():
  if 'oeffnungszeiten' in details and details['oeffnungszeiten']:
    events.append({
      'title':'Öffnungszeiten: ' +', '.join(details['oeffnungzeiten']),
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
    "initialView": "dayGridMonth",
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
