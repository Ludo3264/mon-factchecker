import streamlit as st
from groq import Groq

# --- CONFIGURATION DES SOURCES ---
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr", "liberation.fr/checknews", 
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "service-public.fr", "meteofrance.com", "radiofrance.fr"
]

def get_ai_analysis(query):
    """Analyse via Groq avec instruction de recherche forcée."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Prompt optimisé pour forcer la recherche dans les sources listées
    system_prompt = f"""
    Tu es un expert en fact-checking. 
    Règles strictes :
    1. Analyse l'affirmation en recherchant activement si elle a été traitée, confirmée ou démentie par : {', '.join(TRUSTED_SITES)}.
    2. Si un article existe sur ces sites, cite explicitement le titre de l'article et le lien direct vers celui-ci.
    3. Si l'information est fausse ou une rumeur, commence ta réponse par 'FAUX' et explique brièvement les faits.
    4. NE CITE AUCUNE SOURCE HORS DE CETTE LISTE.
    5. Si après vérification dans ces sites tu ne trouves rien, réponds 'INDÉTERMINÉ' en expliquant que les sources de référence n'ont pas traité ce sujet.
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
            with st.spinner("Recherche active dans les sources de confiance..."):
                try:
                    analysis = get_ai_analysis(user_input)
                    up_analysis = analysis.upper()
                    
                    st.subheader("⚖️ Résultat")
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
    Face à une information douteuse, adoptez les réflexes des journalistes :
    
    1. **Croisement des sources :** Ne vous contentez jamais d'une seule source. Vérifiez si l'information est reprise par nos sites de référence (AFP, Le Monde, Libération, etc.).
    2. **Analyse de la preuve :** Une information sans source primaire ou lien vers un document officiel est suspecte.
    3. **Le doute méthodique :** Si, après vérification, aucune source fiable ne confirme l'information, considérez-la comme **INDÉTERMINÉE**.
    4. **Responsabilité :** Si le résultat est **INDÉTERMINÉ** ou **FAUX**, ne partagez pas l'information sur les réseaux sociaux. La désinformation se nourrit de notre impulsivité.
    
    *« Le doute est un hommage rendu à la vérité. »*
    """)

st.markdown("---")
st.caption("Outil pédagogique pour l'Éducation aux Médias et à l'Information.")
