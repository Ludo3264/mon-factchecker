import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
# Liens mis à jour pour une meilleure fiabilité
SEARCH_URLS = {
    "AFP Factuel": "https://factuel.afp.com/?query=",
    "Le Monde (Décodeurs)": "https://www.lemonde.fr/recherche/?search_keywords=",
    "Libération (CheckNews)": "https://www.liberation.fr/recherche/?q=",
    "France Info (Vrai ou Fake)": "https://www.francetvinfo.fr/recherche/?search="
}

# --- LOGIQUE IA ---
def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = """
    Tu es un expert en fact-checking EMI. 
    1. Analyse l'affirmation avec une rigueur journalistique.
    2. Ne génère aucune information factuelle erronée (dates, titres, fonctions).
    3. Structure ta réponse en 3 parties obligatoires :
       - Faits observés (données biographiques ou factuelles vérifiables).
       - Biais détectés (analyse de la nature de la rumeur).
       - Méthodologie de vérification (conseils concrets pour l'élève).
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
    st.subheader("✍️ Analyseur Critique — Niveau Expert")
    
    # Initialisation des états
    if 'analysis' not in st.session_state: st.session_state.analysis = None
    if 'show_verdict' not in st.session_state: st.session_state.show_verdict = False
    if 'user_input' not in st.session_state: st.session_state.user_input = ""

    user_input = st.text_input("Affirmation à disséquer :")
    
    if st.button("Lancer l'enquête"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.show_verdict = False
    
    if st.session_state.analysis:
        st.markdown("### 🔍 1. Enquêtez par vous-même")
        cols = st.columns(len(SEARCH_URLS))
        for i, (name, base_url) in enumerate(SEARCH_URLS.items()):
            cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
            
        st.markdown("---")
        st.subheader("📝 2. Bilan de ma recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :", key="bilan_area")
        
        if st.button("Comparer mon bilan avec l'analyse experte"):
            if user_bilan:
                st.session_state.show_verdict = True
            else:
                st.warning("Veuillez rédiger votre bilan avant de comparer.")

        if st.session_state.show_verdict:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Mon Bilan")
                st.info(user_bilan)
            with col2:
                st.subheader("🤖 Analyse de l'expert (IA)")
                st.write(st.session_state.analysis)

# (Onglets 2 et 3 inchangés)
with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Lens", "https://lens.google.com/")
    col2.link_button("TinEye", "https://tineye.com/")
    col3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("Le doute est un hommage rendu à la vérité. Croisez, vérifiez, ne partagez pas sans preuve.")
