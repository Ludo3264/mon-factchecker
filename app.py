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
    "site:factuel.afp.com", "site:lemonde.fr/les-decodeurs", "site:liberation.fr/checknews",
    "site:francetvinfo.fr/vrai-ou-fake", "site:factcheck.org", "site:fullfact.org",
    "site:snopes.com", "site:reuters.com/fact-check", "site:euvsdisinfo.eu"
]
search_query_restriction = " OR ".join(TRUSTED_SITES)

def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        return search.run(f"({claim}) ({search_query_restriction})")
    except Exception as e:
        return f"Erreur : {str(e)}"

# Template mis à jour pour isoler la désinformation parasite
template = """Tu es un expert en fact-checking. Vérifie l'affirmation en te basant EXCLUSIVEMENT sur les extraits fournis.

RÈGLES :
1. Si l'info n'est pas vérifiable, réponds : "Je ne trouve aucune vérification dans les sources."
2. Si l'info est vérifiée, structure ainsi :
   - VERDICT : VRAI / FAUX / NUANCÉ
   - EXPLICATION : Résumé factuel. Si tu détectes des informations contradictoires dans les extraits (ex: mélange de sujets), ignore les éléments hors-sujet qui ne concernent pas directement l'affirmation.
   - NOTE SUR LA FIABILITÉ : Si une partie des extraits contient des éléments de désinformation ou de confusion, précise-le clairement pour éviter toute confusion.
   - SOURCE : Identifie le média. Si non explicite, indique le domaine probable.
   - TITRE DE RÉFÉRENCE : Donne le titre si disponible, sinon "Non disponible".
3. Ne pas utiliser de connaissances externes.

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
st.set_page_config(page_title="Fact-Checking Pédagogique", page_icon="🛡️")
st.title("🛡️ Outil de Fact-Checking Pédagogique")

tab1, tab2 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
    if st.button("Lancer la vérification"):
        sources = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources)
        st.markdown("### ⚖️ Analyse et conclusions")
        st.write(resultat)
        st.info("💡 **Conseil pédagogique :** Si le verdict semble contredire des phrases présentes dans les extraits, c'est parce que le moteur de recherche a pu inclure des articles traitant d'autres rumeurs. Analysez bien la 'Note sur la fiabilité' et les extraits bruts.")
        with st.expander("🔗 Consulter les extraits de presse bruts"):
            st.write(sources)

with tab2:
    st.write("Utilisez les outils officiels pour une recherche inversée :")
    img_url = st.text_input("Collez l'URL de l'image ici :")
    if img_url:
        col1, col2 = st.columns(2)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(img_url)}")
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={urllib.parse.quote_plus(img_url)}")
