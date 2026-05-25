import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
# J'ai uniformisé les clés sans ponctuation pour éviter les erreurs de détection
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Assemblée Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Egalite": {"HCE": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

# --- LOGIQUE IA ---
def analyze_query_category(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    cat_list = ", ".join(CATEGORIES.keys())
    prompt = f"Analyse cette phrase : '{query}'. Réponds uniquement par l'un de ces mots exacts : {cat_list}."
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
    return completion.choices[0].message.content.strip()

# --- INTERFACE ---
st.set_page_config(page_title="Outil EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique")
    if 'step' not in st.session_state: st.session_state.step = 0

    user_input = st.text_input("Saisissez l'affirmation à vérifier :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            # Sécurité : on récupère la catégorie
            detected_cat = analyze_query_category(user_input)
            st.session_state.cat = detected_cat if detected_cat in CATEGORIES else "Fact-checking"
            st.session_state.step = 1

    if st.session_state.step >= 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        sources = CATEGORIES.get(st.session_state.cat, {})
        
        # Sécurité : on vérifie que 'sources' n'est pas vide avant de créer les colonnes
        if sources:
            cols = st.columns(len(sources))
            for i, (name, base_url) in enumerate(sources.items()):
                cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.markdown("---")
        # ... suite du code (Bilan, etc.)
