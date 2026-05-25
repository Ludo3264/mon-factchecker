import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
SEARCH_URLS = {
    "AFP Factuel": "https://factuel.afp.com/search?query=",
    "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords=",
    "Libération": "https://www.liberation.fr/recherche/?q="
}

def get_ai_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = """
    Tu es un expert en fact-checking EMI. 
    1. Analyse l'affirmation de manière détaillée. 
    2. Cite les faits de manière objective.
    3. Si c'est faux/rumeur, commence par FAUX. Sinon VRAI ou INDÉTERMINÉ.
    4. Sois pédagogique et explique POURQUOI c'est vrai ou faux.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.title("🛡️ Outil d'Analyse Critique — EMI")
user_input = st.text_input("Saisissez l'affirmation à vérifier :")

# Stockage des états dans la session pour garder l'analyse en mémoire
if 'analysis' not in st.session_state:
    st.session_state.analysis = None

if st.button("Lancer l'Analyse"):
    if user_input:
        with st.spinner("Analyse en cours..."):
            st.session_state.analysis = get_ai_analysis(user_input)
            st.success("Analyse générée. Effectuez vos recherches avant de consulter le verdict.")
    else:
        st.warning("Veuillez saisir une affirmation.")

# Section Recherche (Toujours visible)
if st.session_state.analysis:
    st.markdown("### 🔍 1. Enquêtez par vous-même")
    cols = st.columns(len(SEARCH_URLS))
    for i, (name, base_url) in enumerate(SEARCH_URLS.items()):
        cols[i].link_button(name, f"{base_url}{user_input.replace(' ', '+')}")

    # Section Bilan
    st.markdown("---")
    st.subheader("📝 2. Bilan de ma recherche")
    user_bilan = st.text_area("Après avoir consulté les liens, que pouvez-vous conclure ?")
    
    # Bouton de validation pour comparer
    if st.button("Valider mon bilan et voir le verdict de l'IA"):
        if user_bilan:
            st.markdown("---")
            st.subheader("⚖️ 3. Verdict de l'IA")
            analysis = st.session_state.analysis
            up_analysis = analysis.upper()
            
            # Affichage couleur
            if any(word in up_analysis for word in ["FAUX", "DÉMENTI", "MENSONGE"]):
                st.error("❌ FAUX")
            elif "VRAI" in up_analysis:
                st.success("✅ VRAI")
            else:
                st.warning("❓ INDÉTERMINÉ")
            
            st.write(analysis)
        else:
            st.warning("Veuillez rédiger votre bilan avant de valider.")
