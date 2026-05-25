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

template = """Tu es un expert en fact-checking. Ton rôle est de vérifier l'affirmation en te basant EXCLUSIVEMENT sur les extraits fournis.

RÈGLES DE HIÉRARCHIE :
1. Priorise les faits établis sur les opinions, commentaires ou arguments de défense.
2. Si l'affirmation est vérifiée, le VERDICT doit être VRAI.
3. Structure la réponse comme suit :
   - VERDICT : VRAI / FAUX / NUANCÉ
   - FAIT ÉTABLI : Résumé du point vérifiable sans interprétation.
   - ANALYSE DES OPINIONS/DÉBATS : Identifie et sépare les avis, polémiques ou interprétations présents dans les sources qui ne constituent pas un fait.
   - SOURCE : Identifie le nom du média en te basant sur le contexte. Si non explicite, indique le domaine probable.
   - TITRE DE RÉFÉRENCE : Donne le TITRE de l'article trouvé dans le texte si disponible, sinon "Non disponible".
4. Ne jamais utiliser de connaissances externes.
5. Si les sources sont en anglais, traduis le résultat en français.

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
st.set_page_config(page_title="Fact-Checking Global", page_icon="🛡️", layout="centered")

st.markdown('<p style="font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px;">🛡️ Outil de Fact-Checking</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #4B5563; margin-bottom: 25px;">Version spécialisée (Texte & Image)</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs([
    "✍️ Vérifier un Texte", 
    "🖼️ Vérifier une Image (Recherche Inversée)"
])

# ONGLET 1
with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :", placeholder="Exemple : Une rumeur internationale dit que...", height=100)
    if st.button("Lancer la vérification", type="primary"):
        if not user_claim.strip():
            st.warning("⚠️ Saisissez du texte avant de lancer.")
        else:
            with st.spinner("🔍 Recherche sur le réseau international..."):
                sources_text = search_trusted_sources(user_claim)
            with st.spinner("🤖 Analyse critique multilingue par l'IA..."):
                resultat_verdict = executer_fact_checking(user_claim, sources_text)
            
            st.markdown('<p style="font-size:1.3rem; font-weight:bold; margin-top:20px;">⚖️ Analyse et conclusions :</p>', unsafe_allow_html=True)
            st.write(resultat_verdict)
            st.info("💡 **Conseil pédagogique :** Observez comment l'outil sépare le 'Fait établi' de l' 'Analyse des opinions'. C'est la base du travail de journaliste : ne jamais confondre ce qui est prouvé avec ce qui est dit ou pensé.")
            
            with st.expander("🔗 Consulter les extraits de presse bruts (Monde)"):
                st.write(sources_text)

# ONGLET 2
with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image</p>', unsafe_allow_html=True)
    image_url = st.text_input("Collez l'URL de l'image :", placeholder="https://exemple.com/image.jpg", key="url_mode")
    if image_url:
        try:
            st.image(image_url, caption="Image soumise via URL", width=300)
            encoded_url = urllib.parse.quote_plus(image_url)
            col1, col2 = st.columns(2)
            with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded_url}", type="primary", use_container_width=True)
            with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded_url}", use_container_width=True)
        except Exception:
            st.error("Impossible d'afficher cette image.")
    st.markdown("---")
    st.markdown("#### 📱 Option : Vous avez enregistré l'image sur votre appareil")
    col_up1, col_up2 = st.columns(2)
    with col_up1: st.link_button("📸 Uploader sur Google Lens officiel", "https://lens.google.com", use_container_width=True)
    with col_up2: st.link_button("🤖 Uploader sur TinEye officiel", "https://tineye.com", use_container_width=True)
