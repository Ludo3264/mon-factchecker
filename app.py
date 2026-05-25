import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Science & Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Météo & Climat": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

def analyze_query(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # On demande à l'IA de nous donner uniquement la catégorie pertinente
    prompt = f"Analyse cette affirmation : '{query}'. Réponds uniquement par l'un de ces mots : 'Fact-checking', 'Science & Santé', ou 'Météo & Climat'."
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content.strip()

# --- INTERFACE ---
st.title("🛡️ Outil d'Analyse Critique — EMI")

if 'cat' not in st.session_state: st.session_state.cat = None

user_input = st.text_input("Affirmation à disséquer :")

if st.button("Lancer l'enquête"):
    if user_input:
        st.session_state.user_input = user_input
        # On détermine la catégorie dynamiquement
        st.session_state.cat = analyze_query(user_input)
        st.session_state.show_verdict = False

if st.session_state.cat:
    st.markdown(f"### 🔍 Enquêtez (Catégorie détectée : {st.session_state.cat})")
    # Affichage dynamique uniquement de la catégorie pertinente
    sources = CATEGORIES.get(st.session_state.cat, {})
    cols = st.columns(len(sources))
    for i, (name, base_url) in enumerate(sources.items()):
        cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")

    # Le reste du code (Bilan et IA) reste identique...
