import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
CATEGORIES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique & Société": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Assemblée Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Égalité & Droits": {"HCE (Haut Conseil Égalité)": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur des Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture & Médias": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement & Économie": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL (Logement)": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo & Climat": {"Météo-France": "https://meteofrance.com/recherche?q=", "Copernicus": "https://climate.copernicus.eu/search?q="}
}

# --- LOGIQUE IA ---
def analyze_query_category(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    cat_list = ", ".join(CATEGORIES.keys())
    prompt = f"Analyse cette phrase : '{query}'. Réponds uniquement par l'un de ces termes : {cat_list}."
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.1-8b-instant")
    return completion.choices[0].message.content.strip()

def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = f"""
    Nous sommes le {datetime.now().strftime("%d %B %Y")}. 
    Agis en expert EMI. Ta réponse doit être structurée ainsi :
    1. Faits observés (avec preuves et sources nommées).
    2. Biais détectés (analyse critique).
    3. Méthodologie de vérification (conseils concrets).
    4. Sources de référence (liste des institutions/médias cités).
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil d'Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique")
    if 'step' not in st.session_state: st.session_state.step = 0

    user_input = st.text_input("Saisissez l'affirmation à vérifier :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.cat = analyze_query_category(user_input)
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.step >= 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        sources = CATEGORIES.get(st.session_state.cat, {})
        cols = st.columns(len(sources))
        for i, (name, base_url) in enumerate(sources.items()):
            cols[i % 5].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.markdown("---")
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :")
        
        if st.button("Comparer mon bilan avec l'analyse experte"):
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Votre Bilan")
                st.info(user_bilan)
            with col2:
                st.subheader("🤖 Analyse de l'expert")
                st.write(st.session_state.analysis)

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Lens", "https://lens.google.com/")
    col2.link_button("TinEye", "https://tineye.com/")
    col3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("Croisez les sources, analysez la preuve, et en cas de doute, considérez l'information comme indéterminée.")
