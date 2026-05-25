import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
SOURCES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde Décodeurs": "https://www.lemonde.fr/les-decodeurs/recherche/?search_keywords="},
    "Médias, Réseaux Sociaux & Culture": {
        "Arcom (Régulation)": "https://www.arcom.fr/recherche?q=", 
        "Le Monde Culture": "https://www.lemonde.fr/culture/recherche/?search_keywords="
    },
    "Sport": {"Le Monde Sport": "https://www.lemonde.fr/sport/recherche/?search_keywords=", "L'Équipe": "https://www.lequipe.fr/recherche/?q="},
    "Environnement & Planète": {"Le Monde Planète": "https://www.lemonde.fr/planete/recherche/?search_keywords=", "Météo-France": "https://meteofrance.com/recherche?q="},
    "Société, Laïcité & Genre": {
        "Vie Publique (Laïcité)": "https://www.vie-publique.fr/recherche?q=laïcité",
        "HCE (Genre/Égalité)": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=",
        "Défenseur des Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key="
    },
    "Santé": {"Le Monde Sciences": "https://www.lemonde.fr/sciences/recherche/?search_keywords=", "INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Éducation & École": {"Le Monde Éducation": "https://www.lemonde.fr/education/recherche/?search_keywords=", "Ministère Ed.": "https://www.education.gouv.fr/recherche?q="},
    "Politique & Institutions": {"Le Monde Politique": "https://www.lemonde.fr/politique/recherche/?search_keywords=", "Vie Publique": "https://www.vie-publique.fr/recherche?q="},
    "Économie & Emploi": {"Le Monde Éco": "https://www.lemonde.fr/economie/recherche/?search_keywords=", "INSEE": "https://www.insee.fr/fr/recherche?q="},
    "International": {"Le Monde International": "https://www.lemonde.fr/international/recherche/?search_keywords=", "ONU Info": "https://news.un.org/fr/search/"}
}

# --- LOGIQUE IA ---
def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime('%d %B %Y')
    
    system_prompt = f"""
    Nous sommes le {current_date}. Tu es un expert EMI agissant comme un journaliste des 'Décodeurs'.
    RÈGLE : Utilise une approche rigoureuse. Recherche des preuves factuelles et institutionnelles.
    Si tu confirmes une info, cite l'article source. Si c'est une rumeur, démontre pourquoi en citant des preuves.
    
    Structure OBLIGATOIRE :
    [VERDICT] : VRAI, FAUX ou INCERTAIN
    1. Faits observés : (Synthèse des données factuelles).
    2. Biais détectés : (Analyse critique).
    3. Méthodologie : (Comment croiser l'information).
    4. Sources : (Liste d'URL cliquables).
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant"
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil EMI Expert", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique")
    cat_selection = st.selectbox("Sélectionnez le domaine de votre recherche :", list(SOURCES.keys()))
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.cat = cat_selection
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
    * **Croisez** : Utilisez les rubriques spécialisées pour vérifier les faits.
    * **Identifiez** : Une information sourcée par des institutions (INSEE, Météo-France, HCE, etc.) est plus robuste.
    * **L'IA est un assistant** : Si elle répond 'Incertain', c'est à vous de mener l'enquête manuellement via les boutons proposés.
    * **Réseaux sociaux** : Soyez doublement vigilants, c'est le terrain privilégié de la désinformation.
    """)
