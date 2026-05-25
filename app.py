import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION ---
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Ass. Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Egalite": {"HCE": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

# --- LOGIQUE ---
def get_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    prompt = f"Nous sommes le {datetime.now().strftime('%d %B %Y')}. Analyse cette affirmation en 4 sections : Faits, Biais, Méthodologie, Sources. Affirmation : {query}"
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="EMI Expert", layout="wide")
st.title("🛡️ Outil d'Analyse Critique")

# Gestion des états
if 'step' not in st.session_state: st.session_state.step = 0

user_input = st.text_input("Saisissez l'affirmation à vérifier :")

if st.button("Lancer l'analyse"):
    if user_input:
        st.session_state.user_input = user_input
        # Détection simple de catégorie
        cat_found = next((cat for cat in CATEGORIES if cat.lower() in user_input.lower()), "Fact-checking")
        st.session_state.cat = cat_found
        st.session_state.analysis = get_analysis(user_input)
        st.session_state.step = 1

if st.session_state.step == 1:
    st.markdown(f"### 🔍 Sources ({st.session_state.cat})")
    # Affichage compact : une seule ligne de boutons
    cols = st.columns(2) 
    sources = CATEGORIES[st.session_state.cat]
    for i, (name, base_url) in enumerate(sources.items()):
        cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
    
    st.markdown("---")
    st.subheader("📝 Bilan de votre recherche")
    user_bilan = st.text_area("Rédigez votre conclusion :")
    
    if st.button("Comparer mon bilan"):
        col1, col2 = st.columns(2)
        col1.info(f"👤 Votre bilan : {user_bilan}")
        col2.write(f"🤖 **Verdict expert :**\n\n{st.session_state.analysis}")
