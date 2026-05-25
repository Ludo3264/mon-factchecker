import os
import streamlit as st
import urllib.parse
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION
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
# TEMPLATE RIGUEUR FACTUELLE (Zéro ambiguïté)
# ==============================================================================
template = """Tu es un expert en fact-checking. Ta mission est d'établir la vérité factuelle sur l'affirmation.

RÈGLES D'OR :
1. VÉRITÉ FACTUELLE : Un fait documenté par des sources fiables (ex: orientation sexuelle, fonctions publiques) est une VÉRITÉ ÉTABLIE. Ne jamais le qualifier de "discutable" ou "nuancé" s'il est prouvé.
2. ANALYSE :
   - FAITS ÉTABLIS : Liste uniquement les faits prouvés par les sources.
   - DÉBATS & OPINIONS : Analyse uniquement ce qui relève du commentaire ou de la polémique, en le distinguant clairement des faits.
   - VERDICT : VRAI, FAUX ou NUANCÉ (basé sur la preuve).
   - SOURCE & TITRE : Cite précisément les médias et titres présents dans les extraits.
3. Ne jamais inventer ou douter des faits prouvés par les sources.

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
st.set_page_config(page_title="Fact-Checking Rigoureux", page_icon="🛡️")
st.title("🛡️ Outil de Fact-Checking (Rigueur Absolue)")

user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
if st.button("Lancer l'analyse factuelle"):
    with st.spinner("Analyse en cours..."):
        sources = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources)
        st.markdown("### ⚖️ Verdict et Analyse")
        st.write(resultat)
        with st.expander("🔗 Voir les sources brutes"):
            st.write(sources)
