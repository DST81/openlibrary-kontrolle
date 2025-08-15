import streamlit as st
import json
from github import Github
from datetime import date, timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title='Arbeitsplanung', page_icon='📅')
