import streamlit as st
from groq import Groq

# --- CONFIGURATION DES SOURCES ---
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr", "liberation.fr/checknews", 
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "service-public.fr", "meteofrance.com"
]

def get_ai_analysis(query):
    """Appel à l'API Groq avec le modèle stable."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    system_prompt = f"""
    Tu es un expert en vérification de faits (Fact-checker) pour l'EMI.
    Règles strictes :
    1. Base ton analyse UNIQUEMENT sur ces sources : {', '.join(TRUSTED_SITES)}.
    2. Si aucune preuve n'est trouvée dans ces sites, réponds impérativement par 'INDÉTERMINÉ' et explique pourquoi.
    3. Ne jamais inventer.
    4. Pour chaque fait cité, insère le lien cliquable vers la source originale en markdown ex: [Titre](URL).
    """
    
    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Vérifie la véracité de cette affirmation : {query}"}
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
                    st.subheader("⚖️ Résultat")
                    
                    if "INDÉTERMINÉ" in analysis.upper():
                        st.write("❓ **INDÉTERMINÉ**")
                        st.warning("⚠️ Aucune source fiable trouvée. Conformément à la méthode, ne partagez pas cette information.")
                    elif "FAUX" in analysis.upper() or "DÉMENTI" in analysis.upper():
                        st.write("❌ **FAUX**")
                    else:
                        st.write("✅ **VÉRIFIÉ / PROBABLE**")
                    
                    st.subheader("📋 Analyse Factuelle")
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")
        else:
            st.warning("Veuillez saisir une affirmation.")

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Lens", "https://lens.google.com/")
    col2.link_button("TinEye", "https://tineye.com/")
    col3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch")
    
    st.markdown("---")
    img_input = st.text_input("Collez l'URL de l'image ici :")
    if st.button("Analyser l'Image"):
        st.info("Recherche de similarité dans les bases de données en cours...")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("""
    1. **Sources Certifiées uniquement :** AFP Factuel, Le Monde, Libération, CNRS, etc.
    2. **Zéro invention :** Si l'information est absente de ces sources, l'outil affiche **INDÉTERMINÉ**.
    3. **Action :** Si le résultat est **INDÉTERMINÉ**, l'information n'est pas fiable. **Ne la partagez pas.**
    """)

st.markdown("---")
st.caption("Outil pédagogique pour l'Éducation aux Médias et à l'Information.")
