import os
import streamlit as st
import urllib.parse
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION DES SOURCES (Un site par ligne)
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

def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        return search.run(f"({claim}) ({search_query_restriction})")
    except Exception as e:
        return f"Erreur : {str(e)}"

# ==============================================================================
# TEMPLATE D'ANALYSE (Rigueur maximale)
# ==============================================================================
template = """Tu es un expert en éducation aux médias (EMI). Analyse l'affirmation et les extraits fournis.

RÈGLES D'ANALYSE PRIORITAIRES :
1. VÉRITÉ FACTUELLE : Un fait largement documenté (ex: orientation sexuelle, fonctions officielles) DOIT être classé comme FAIT ÉTABLI et ne jamais être remis en cause.
2. VERDICT : VRAI / FAUX / NUANCÉ. Le verdict doit refléter la véracité du fait principal.
3. STRUCTURE DE RÉPONSE :
   - FAITS ÉTABLIS : Liste les points factuels indiscutables.
   - ANALYSE DES INTERPRÉTATIONS/DÉBATS : Identifie les opinions, polémiques ou rumeurs. Explique pourquoi ce ne sont pas des faits.
   - MÉCANISMES DE MANIPULATION : Détecte biais ou rumeurs uniquement sur les points polémiques.
   - SOURCE & TITRE : Cite précisément les sources et les titres.
4. Ne jamais utiliser de connaissances externes.

---
EXTRAITS : {context}
---
AFFIRMATION : {claim}
RÉPONSE :"""

def executer_fact_checking(claim: str, context_sources: str) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    chain = ({"context": RunnablePassthrough(), "claim": RunnablePassthrough()} 
             | PromptTemplate.from_template(template) | llm | StrOutputParser())
    return chain.invoke({"context": context_sources, "claim": claim})

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️")
st.title("🛡️ Outil d'Analyse Critique (EMI)")

tab1, tab2 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
    if st.button("Lancer l'analyse"):
        sources = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources)
        st.markdown("### ⚖️ Analyse rigoureuse")
        st.write(resultat)
        st.info("💡 **Note pédagogique :** Le 'Fait Établi' est votre ancrage. Tout ce qui est en dessous sert à analyser comment le débat essaie de transformer ou manipuler cette vérité.")
        with st.expander("🔗 Voir les sources brutes"):
            st.write(sources)

with tab2:
    st.write("Outils de recherche inversée :")
    img_url = st.text_input("URL de l'image :")
    if img_url:
        col1, col2 = st.columns(2)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(img_url)}")
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={urllib.parse.quote_plus(img_url)}")
