import os
import streamlit as st
import urllib.parse
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION DES SOURCES
# ==============================================================================
TRUSTED_SITES = [
    "site:factuel.afp.com",
    "site:lemonde.fr/les-decodeurs",
    "site:liberation.fr/checknews",
    "site:francetvinfo.fr/vrai-ou-fake",
    "site:factcheck.org",
    "site:fullfact.org",
    "site:snopes.com",
    "site:reuters.com/fact-check",
    "site:euvsdisinfo.eu"
]
search_query_restriction = " OR ".join(TRUSTED_SITES)

# ==============================================================================
# LOGIQUE MÉTIER TEXTE
# ==============================================================================
def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        full_query = f"({claim}) ({search_query_restriction})"
        return search.run(full_query)
    except Exception as e:
        return f"Erreur moteur de recherche : {str(e)}"

# Nouveau Template orienté Analyse Cognitive
template = """Tu es un expert en éducation aux médias (EMI). Analyse l'affirmation et les extraits fournis.

RÈGLES D'ANALYSE :
1. VERDICT : VRAI / FAUX / NUANCÉ.
2. FAITS : Quels sont les éléments factuels vérifiables ?
3. OPINIONS & RUMEURS : Identifie ce qui relève de l'interprétation, du ressenti ou de la rumeur non sourcée.
4. MÉCANISMES À L'OEUVRE : Identifie si les extraits présentent :
   - Un BIAIS COGNITIF (ex: biais de confirmation, effet de halo).
   - Une tentative d'enfermement dans une BULLE DE FILTRES (ex: ton émotionnel, polarisation).
   - Une structure de RUMEUR (ex: absence de preuve, appel à l'émotion).
5. SOURCE : Identifie le média.
6. TITRE : Donne le titre si disponible, sinon "Non disponible".

---
EXTRAITS DE PRESSE FOURNIS :
{context}
---

AFFIRMATION À ANALYSER :
{claim}

RÉPONSE :"""

prompt = PromptTemplate.from_template(template)

def executer_fact_checking(claim: str, context_sources: str) -> str:
    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        fact_check_chain = (
            {"context": RunnablePassthrough(), "claim": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return fact_check_chain.invoke({"context": context_sources, "claim": claim})
    except Exception as e:
        return f"Erreur d'analyse : {str(e)}"

# ==============================================================================
# INTERFACE UTILISATEUR
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️", layout="centered")

st.markdown('<p style="font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px;">🛡️ Outil d\'Analyse Cognitive (EMI)</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #4B5563; margin-bottom: 25px;">Décomposition des faits, biais et rumeurs</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs([
    "✍️ Vérifier un Texte", 
    "🖼️ Vérifier une Image"
])

# ONGLET 1
with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à analyser :", height=100)
    if st.button("Lancer l'analyse critique", type="primary"):
        if not user_claim.strip():
            st.warning("⚠️ Saisissez du texte.")
        else:
            with st.spinner("🔍 Recherche et analyse en cours..."):
                sources_text = search_trusted_sources(user_claim)
                resultat_analyse = executer_fact_checking(user_claim, sources_text)
            
            st.markdown('<p style="font-size:1.3rem; font-weight:bold; margin-top:20px;">⚖️ Résultats de l\'analyse EMI :</p>', unsafe_allow_html=True)
            st.write(resultat_analyse)
            st.info("💡 **Défi pédagogique :** Identifiez le mécanisme de manipulation détecté (Biais, Bulle, Rumeur) et débattez : pourquoi l'auteur a-t-il utilisé ce levier plutôt qu'un argument factuel ?")
            
            with st.expander("🔗 Voir les sources brutes"):
                st.write(sources_text)

# ONGLET 2
with tab2:
    st.markdown("### 🖼️ Traçage d'image")
    image_url = st.text_input("URL de l'image :")
    if image_url:
        col1, col2 = st.columns(2)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(image_url)}", use_container_width=True)
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={urllib.parse.quote_plus(image_url)}", use_container_width=True)
