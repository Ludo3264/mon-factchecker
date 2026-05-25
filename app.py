import streamlit as st
from groq import Groq

# Configuration
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_ai_fact_check(query):
    # On force l'IA à devenir un assistant de recherche structuré
    system_prompt = """
    Tu es un assistant de fact-checking. 
    1. Ton rôle est de vérifier si l'affirmation est confirmée par des sources en temps réel.
    2. Si tu ne peux pas confirmer (comme pour la météo), ne dis pas "INDÉTERMINÉ" par défaut, 
       propose une requête de recherche précise pour Google/Météo France.
    3. Si l'affirmation est factuellement fausse, explique pourquoi.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# Interface
st.title("🛡️ Outil d'Analyse Critique — EMI")
user_input = st.text_input("Affirmation à vérifier :")

if st.button("Analyser"):
    if user_input:
        with st.spinner("Analyse..."):
            # L'IA génère ici une analyse qui inclut des requêtes de recherche
            result = get_ai_fact_check(user_input)
            st.session_state.analysis = result
            st.write(result)
            
            # Liens dynamiques incluant une recherche Météo France explicite
            st.markdown("### 🔍 Vérifier en temps réel :")
            col1, col2 = st.columns(2)
            col1.link_button("Vérifier sur Météo France", f"https://meteofrance.com/recherche?q={user_input.replace(' ', '+')}")
            col2.link_button("Recherche Google Actualités", f"https://news.google.com/search?q={user_input.replace(' ', '+')}")

# Bilan
if 'analysis' in st.session_state:
    st.markdown("---")
    st.text_area("Bilan de recherche (comparatif) :")
    if st.button("Valider"):
        st.success("Bilan enregistré. L'IA confirme que la vérification humaine est essentielle.")
