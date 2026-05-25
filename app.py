import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
TRUSTED_SITES_INFO = {
    "AFP Factuel": "https://factuel.afp.com/search?query=",
    "Le Monde (Décodeurs)": "https://www.lemonde.fr/recherche/?search_keywords=",
    "Libération (CheckNews)": "https://www.liberation.fr/recherche/?q=",
    "France Info (Vrai ou Fake)": "https://www.francetvinfo.fr/recherche/?search=",
    "Snopes": "https://www.snopes.com/?s="
}

def get_ai_research_plan(query):
    """L'IA analyse le sujet et propose des liens de recherche directe."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    system_prompt = f"""
    Tu es un assistant expert en Éducation aux Médias et à l'Information (EMI).
    Ton rôle est d'aider l'élève à vérifier une affirmation en lui fournissant les liens de recherche directe.
    1. Analyse brièvement l'affirmation.
    2. Ne tente pas de conclure par toi-même si tu n'es pas certain.
    3. Indique à l'élève de cliquer sur les liens ci-dessous pour effectuer la recherche sur les sites de référence.
    """
    
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Aide-moi à vérifier cette affirmation : {query}"}
        ],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil d'Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

# Tab1 : Vérification assistée
st.subheader("✍️ Vérifier une affirmation")
user_input = st.text_input("Saisissez l'affirmation à vérifier :")

if st.button("Préparer la recherche"):
    if user_input:
        # Analyse de l'IA
        analysis = get_ai_research_plan(user_input)
        st.markdown(analysis)
        
        # Génération dynamique des boutons de recherche
        st.write("### 🔍 Cliquez pour lancer la recherche sur les sites de confiance :")
        cols = st.columns(len(TRUSTED_SITES_INFO))
        for i, (name, base_url) in enumerate(TRUSTED_SITES_INFO.items()):
            search_url = f"{base_url}{user_input.replace(' ', '+')}"
            cols[i].link_button(name, search_url)
    else:
        st.warning("Veuillez saisir une affirmation.")

st.markdown("---")
st.caption("Outil pédagogique EMI : L'IA guide, l'élève vérifie.")
