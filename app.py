import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
SOURCES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords="},
    "Santé": {"INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Politique": {"Vie Publique": "https://www.vie-publique.fr/recherche?q=", "Ass. Nat.": "https://www.assemblee-nationale.fr/dyn/recherche?q="},
    "Egalite": {"HCE": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=", "Défenseur": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "Culture": {"BnF": "https://www.bnf.fr/fr/recherche?q=", "Arcom": "https://www.arcom.fr/recherche?q="},
    "Logement": {"INSEE": "https://www.insee.fr/fr/recherche?q=", "ANIL": "https://www.anil.org/recherche/?tx_indexedsearch_pi1%5Bsword%5D="},
    "Météo": {"Météo-France": "https://meteofrance.com/recherche?q=", "Keraunos": "https://www.keraunos.org/recherche.html?searchword="}
}

# --- LOGIQUE IA ---
def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime('%d %B %Y')
    system_prompt = f"""
    Nous sommes le {current_date}. Tu es un expert EMI. 
    RÈGLE 1 : Considère la date du {current_date} comme un fait établi.
    RÈGLE 2 : Analyse l'affirmation. Si elle est fausse/rumeur, déclare-la FAUSSE fermement. 
    RÈGLE 3 : Si tu ne peux pas vérifier en temps réel, renvoie vers les liens fournis.
    Structure OBLIGATOIRE :
    [VERDICT] : VRAI, FAUX ou INCERTAIN
    1. Faits observés (dates, données). 2. Biais détectés. 3. Méthodologie. 4. Sources (URL cliquables).
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant"
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
            cat = next((c for c in SOURCES if c.lower() in user_input.lower()), "Fact-checking")
            st.session_state.cat = cat
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.get('step') == 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        cols = st.columns(len(SOURCES[st.session_state.cat]))
        for i, (name, base_url) in enumerate(SOURCES[st.session_state.cat].items()):
            cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.write("---")
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :")
        
        if st.button("Comparer mon bilan avec l'expert"):
            analysis = st.session_state.analysis
            color = "#ff5252" if "[FAUX]" in analysis.upper() else "#4caf50" if "[VRAI]" in analysis.upper() else "#ff9800"
            
            c1, c2 = st.columns(2)
            c1.info(f"👤 **Votre Bilan :**\n\n{user_bilan}")
            c2.markdown(f"""<div style="background-color: {color}15; padding: 15px; border-radius: 10px; border-left: 5px solid {color};">
                <h3 style="color: {color};">🤖 Analyse de l'expert</h3>{analysis.replace('[VRAI]', '').replace('[FAUX]', '').replace('[INCERTAIN]', '')}</div>""", unsafe_allow_html=True)

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Google Lens", "https://lens.google.com/")
    c2.link_button("TinEye", "https://tineye.com/")
    c3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")

with tab3:
    st.subheader("ℹ️ Méthode : Le Doute Méthodique")
    st.markdown("""
    1. **Croisez les sources** : Une seule source ne suffit jamais pour confirmer une information.
    2. **Identifiez l'auteur** : Qui publie ? Est-ce un site officiel, un média reconnu, ou un compte anonyme ?
    3. **Analysez la tonalité** : Une information factuelle est neutre. Si le texte joue sur vos émotions (peur, colère), soyez extrêmement vigilant.
    4. **Vérifiez la date** : Une information réelle peut devenir fausse si elle est sortie de son contexte temporel.
    """)
