import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION ---
# Liste classée par pertinence pour l'EMI
SEARCH_URLS = {
    "AFP Factuel": "https://factuel.afp.com/?query=",
    "Le Monde (Décodeurs)": "https://www.lemonde.fr/recherche/?search_keywords=",
    "Libération (CheckNews)": "https://www.liberation.fr/recherche/?q=",
    "France Info (Vrai ou Fake)": "https://www.francetvinfo.fr/recherche/?search=",
    "Portail Gouv.fr": "https://www.service-public.fr/recherche?q=",
    "Site Élysée": "https://www.elysee.fr/recherche?q="
}

def get_expert_analysis(query):
    # Injection de la date réelle
    date_actuelle = datetime.now().strftime("%d %B %Y")
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    system_prompt = f"""
    Tu es un expert en fact-checking EMI. Nous sommes le {date_actuelle}.
    1. Analyse l'affirmation avec une rigueur absolue.
    2. Si l'affirmation concerne une donnée en temps réel (météo, actualité immédiate) et que tu n'as pas accès à internet en direct, dis explicitement : "Je n'ai pas accès aux données en temps réel pour cette date. Consultez les sites officiels ci-dessous."
    3. Tu DOIS citer tes sources (médias, institutions).
    4. Structure ta réponse en 4 sections obligatoires :
       - Faits observés : (avec preuves).
       - Biais détectés : (analyse critique).
       - Méthodologie de vérification : (conseils concrets).
       - Sources de référence : (liste des sources fiables).
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
    
    if 'analysis' not in st.session_state: st.session_state.analysis = None
    if 'show_verdict' not in st.session_state: st.session_state.show_verdict = False
    
    user_input = st.text_input("Affirmation à disséquer :")
    
    if st.button("Lancer l'enquête"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.show_verdict = False
    
    if st.session_state.analysis:
        st.markdown("### 🔍 1. Enquêtez par vous-même")
        cols = st.columns(3)
        for i, (name, base_url) in enumerate(SEARCH_URLS.items()):
            cols[i % 3].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
            
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
