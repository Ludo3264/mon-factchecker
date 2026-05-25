import streamlit as st
from groq import Groq

# --- CONFIGURATION DES SOURCES ---
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr", "liberation.fr/checknews", 
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "service-public.fr", "meteofrance.com", "radiofrance.fr"
]

def get_ai_analysis(query):
    """Analyse via Groq avec instruction de forcer le verdict."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    system_prompt = f"""
    Tu es un expert en vérification de faits.
    Règles :
    1. Analyse l'affirmation en te basant uniquement sur : {', '.join(TRUSTED_SITES)}.
    2. Si l'affirmation est fausse, une rumeur, ou non confirmée, commence ta réponse par le mot FAUX ou INDÉTERMINÉ.
    3. Ne pas inventer d'informations.
    4. Cite tes sources avec des liens racines.
    """
    
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Vérifie cette affirmation : {query}"}
        ],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil d'Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Vérifier un Texte")
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")
    
    if st.button("Analyser le Texte"):
        if user_input:
            with st.spinner("Analyse rigoureuse en cours..."):
                try:
                    analysis = get_ai_analysis(user_input)
                    up_analysis = analysis.upper()
                    
                    st.subheader("⚖️ Résultat")
                    # Logique de détection prioritaire
                    if any(word in up_analysis for word in ["FAUX", "DÉMENTI", "MENSONGE"]):
                        st.error("❌ **FAUX**")
                    elif "INDÉTERMINÉ" in up_analysis:
                        st.warning("❓ **INDÉTERMINÉ**")
                    else:
                        st.success("✅ **PROBABLEMENT VRAI**")
                    
                    st.subheader("📋 Analyse Factuelle")
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"Erreur technique : {e}")
        else:
            st.warning("Veuillez saisir une affirmation.")

    st.markdown("---")
    st.write("### 🔍 Outils experts (pour vérifier vous-même) :")
    c1, c2 = st.columns(2)
    c1.link_button("Fact Check Explorer", "https://toolbox.google.com/factcheck/explorer")
    c2.link_button("CORTEX (Esprit critique)", "https://cortecs.org/")

# --- ONGLETS 2 & 3 (inchangés) ---
with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Lens", "https://lens.google.com/")
    col2.link_button("TinEye", "https://tineye.com/")
    col3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch")
    img_input = st.text_input("Collez l'URL de l'image ici :")
    if st.button("Analyser l'Image"):
        st.info("Recherche en cours...")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("1. Sources Certifiées uniquement. 2. Zéro invention. 3. Si INDÉTERMINÉ, ne pas partager.")
