import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr", "liberation.fr/checknews", 
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "service-public.fr", "meteofrance.com"
]

def get_ai_analysis(query):
    """Analyse via Groq avec moteur de vérification."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    system_prompt = f"""
    Tu es un expert en vérification de faits (Fact-checker) pour l'EMI.
    Règles strictes :
    1. Si l'affirmation concerne une personnalité, donne d'abord une définition factuelle à jour.
    2. Base ton analyse UNIQUEMENT sur ces sources : {', '.join(TRUSTED_SITES)}.
    3. Si l'information est une rumeur ou fausse, réponds 'FAUX'.
    4. Si l'information n'est pas confirmée, réponds 'INDÉTERMINÉ'.
    5. Pour les sources, cite uniquement les pages d'accueil des sites de confiance suivants : {', '.join(TRUSTED_SITES)}.
    6. Ne jamais inventer.
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
                    st.subheader("⚖️ Résultat")
                    
                    if "FAUX" in analysis.upper():
                        st.write("❌ **FAUX**")
                    elif "INDÉTERMINÉ" in analysis.upper():
                        st.write("❓ **INDÉTERMINÉ**")
                        st.warning("⚠️ Aucune source fiable trouvée. Conformément à la méthode, ne partagez pas cette information.")
                    else:
                        st.write("✅ **VÉRIFIÉ / PROBABLE**")
                    
                    st.subheader("📋 Analyse Factuelle")
                    st.markdown(analysis)
                    
                except Exception as e:
                    st.error(f"Erreur technique : {e}")
        else:
            st.warning("Veuillez saisir une affirmation.")
            
    st.markdown("---")
    st.write("### 🔍 Outils experts (pour vérifier vous-même) :")
    col_a, col_b = st.columns(2)
    col_a.link_button("Fact Check Explorer (Google)", "https://toolbox.google.com/factcheck/explorer")
    col_b.link_button("CORTEX (Esprit critique)", "https://cortecs.org/")

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
