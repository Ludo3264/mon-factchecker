import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION DES SOURCES (Modifiable facilement ici)
# ==============================================================================
# Si vous voulez ajouter ou enlever un site de fact-checking, modifiez simplement cette liste :
TRUSTED_SITES = [
    "site:afp.com/fr/infos/fact-checking",
    "site:lemonde.fr/les-decodeurs",
    "site:liberation.fr/checknews",
    "site:20minutes.fr/fact-checking",
    "site:francetvinfo.fr/vrai-ou-fake"
]
search_query_restriction = " OR ".join(TRUSTED_SITES)

# ==============================================================================
# LOGIQUE MÉTIER
# ==============================================================================
def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        full_query = f"({claim}) ({search_query_restriction})"
        return search.run(full_query)
    except Exception as e:
        return f"Erreur moteur de recherche : {str(e)}"

template = """Tu es un expert en fact-checking de niveau international.
Ton rôle unique est de vérifier l'affirmation d'un utilisateur en te basant EXCLUSIVEMENT sur les extraits de presse fournis ci-dessous.

RÈGLES CRITIQUES :
1. Si les extraits de presse ne permettent pas de prouver si l'info est vraie ou fausse, réponds EXACTEMENT : 
   "Je ne trouve aucune vérification de cette information dans les sources officielles de fact-checking."
2. Interdiction d'utiliser tes propres connaissances si les extraits n'en parlent pas.
3. Si la réponse y est, commence par le verdict (VRAI, FAUX, ou NUANCÉ) et cite le média (ex: AFP, Les Décodeurs).

---
EXTRAITS DE PRESSE SÉLECTIONNÉS :
{context}
---

AFFIRMATION À ANALYSER :
{claim}

VERDICT :"""

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
st.set_page_config(page_title="Fact-Checking Cloud", page_icon="🛡️", layout="centered")

st.markdown('<p style="font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px;">🛡️ Outil de Fact-Checking Automatisé</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #4B5563; margin-bottom: 25px;">Version Cloud (Propulsée par Groq & Llama 3.1)</p>', unsafe_allow_html=True)

user_claim = st.text_area("Saisissez l'affirmation à vérifier :", placeholder="Exemple : Le gouvernement a annoncé...", height=100)

if st.button("Lancer la vérification", type="primary"):
    if not user_claim.strip():
        st.warning("⚠️ Saisissez du texte avant de lancer.")
    else:
        with st.spinner("🔍 Recherche sur les sites certifiés..."):
            sources_text = search_trusted_sources(user_claim)
        with st.spinner("🤖 Analyse critique par l'IA..."):
            resultat_verdict = executer_fact_checking(user_claim, sources_text)
            
        st.markdown('<p style="font-size:1.3rem; font-weight:bold; margin-top:20px;">⚖️ Analyse et conclusions :</p>', unsafe_allow_html=True)
        if "Je ne trouve aucune vérification" in resultat_verdict:
            st.info(resultat_verdict)
        else:
            st.success(resultat_verdict)
            
        with st.expander("🔗 Consulter les extraits de presse bruts"):
            st.write(sources_text)
