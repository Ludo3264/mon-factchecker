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
    Expert EMI. Analyse l'affirmation. 
    OBLIGATOIRE : 
    1. Si l'info est vérifiable, cite des URL cliquables dans ton texte.
    2. Commence ta réponse par le verdict en majuscules : [VRAI], [FAUX] ou [INCERTAIN].
    3. Structure : Faits observés, Biais, Méthodologie, Sources avec liens.
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
    user_input = st.text_input("Saisissez l'affirmation :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.get('step') == 1:
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion :")
        
        if st.button("Comparer avec l'expert"):
            analysis = st.session_state.analysis
            # Logique de couleur dynamique
            color = "#ff5252" # Rouge (Faux)
            if "[VRAI]" in analysis: color = "#4caf50"
            elif "[INCERTAIN]" in analysis: color = "#ff9800"

            col1, col2 = st.columns(2)
            col1.info(f"👤 **Votre Bilan :**\n\n{user_bilan}")
            col2.markdown(f"""
            <div style="background-color: {color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {color};">
                <h3 style="color: {color};">🤖 Analyse Expert</h3>
                {analysis.replace('[VRAI]', '').replace('[FAUX]', '').replace('[INCERTAIN]', '')}
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.write("La méthode EMI repose sur le croisement systématique.")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Fact-checking.svg/512px-Fact-checking.svg.png", caption="Processus de vérification")
