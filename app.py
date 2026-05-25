import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Ass. Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Egalite": {"HCE": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

# --- LOGIQUE IA ---
def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = f"""
    Nous sommes le {datetime.now().strftime('%d %B %Y')}. 
    Tu es un expert EMI. Analyse l'affirmation avec une fermeté absolue face aux fake news.
    Si l'affirmation est une rumeur démontée par des médias (ex: AFP Factuel), déclare-la FAUSSE sans ambiguïté.
    Structure :
    1. Faits observés : Données biographiques ou scientifiques incontestables.
    2. Biais détectés : Identifie le type de désinformation (ex: rumeur, manipulation).
    3. Méthodologie : Comment vérifier par soi-même (sites sources).
    4. Sources : Cite nommément les médias ou institutions de référence.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique")
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            # Détection automatique de catégorie
            cat = next((c for c in CATEGORIES if c.lower() in user_input.lower()), "Fact-checking")
            st.session_state.cat = cat
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.get('step') == 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        cols = st.columns(4) # Colonnes fixes pour éviter la dispersion
        for i, (name, base_url) in enumerate(CATEGORIES[st.session_state.cat].items()):
            cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.markdown("---")
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :")
        
        if st.button("Comparer mon bilan avec l'analyse experte"):
            col1, col2 = st.columns(2)
            col1.info(f"**👤 Votre Bilan :**\n\n{user_bilan}")
            col2.write(f"**🤖 Analyse de l'expert :**\n\n{st.session_state.analysis}")

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Google Lens", "https://lens.google.com/")
    c2.link_button("TinEye", "https://tineye.com/")
    c3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")
    if st.text_input("URL Image"): st.info("Analyse en cours...")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("Croisez les sources, analysez la preuve, ne partagez jamais sans vérification.")
