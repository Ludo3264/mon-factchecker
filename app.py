import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION ---
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Assemblée Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Egalite": {"HCE": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

# --- LOGIQUE ---
def analyze_query_category(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    cat_list = ", ".join(CATEGORIES.keys())
    prompt = f"Analyse cette phrase : '{query}'. Réponds uniquement par l'un de ces mots exacts : {cat_list}."
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
    return completion.choices[0].message.content.strip()

def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = f"Nous sommes le {datetime.now().strftime('%d %B %Y')}. Agis en expert EMI. Structure la réponse en 4 points : Faits observés, Biais détectés, Méthodologie, Sources."
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
            detected = analyze_query_category(user_input)
            st.session_state.cat = detected if detected in CATEGORIES else "Fact-checking"
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.get('step') == 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        sources = CATEGORIES[st.session_state.cat]
        cols = st.columns(len(sources))
        for i, (name, base_url) in enumerate(sources.items()):
            cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.markdown("---")
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :")
        
        if st.button("Comparer mon bilan avec l'analyse experte"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Votre Bilan")
                st.info(user_bilan)
            with col2:
                st.subheader("🤖 Analyse de l'expert")
                st.write(st.session_state.analysis)

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Google Lens", "https://lens.google.com/")
    c2.link_button("TinEye", "https://tineye.com/")
    c3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("Croisez les sources, analysez la preuve, ne partagez pas sans vérification.")
