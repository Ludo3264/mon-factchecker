import streamlit as st
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
        results = search.results(f"({claim}) ({search_query_restriction})")
        
        formatted_sources = []
        for i, res in enumerate(results.get("organic", [])[:5]):
            title = res.get("title", "Sans titre")
            link = res.get("link", "#")
            snippet = res.get("snippet", "")
            formatted_sources.append(f"Source {i+1}: {title} | URL: {link}\nExtrait: {snippet}")
            
        return "\n\n".join(formatted_sources)
    except Exception as e:
        return f"Erreur : {str(e)}"

# ==============================================================================
# TEMPLATE AVEC TRAÇABILITÉ
# ==============================================================================
template = """Tu es un expert en fact-checking. Ta mission est d'établir la vérité avec des sources traçables.

RÈGLES D'AFFICHAGE :
1. VERDICT : Affiche le verdict (VRAI, FAUX, ou NUANCÉ) tout en haut.
2. FAITS ÉTABLIS : Liste les faits en citant la [Source X] (Nom du site).
3. DÉBATS & OPINIONS : Analyse les points de vue avec la référence [Source X].
4. RÉFÉRENCES & LIENS : Liste explicitement les URLs des sources citées pour vérification.

---
SOURCES FOURNIES (Titre | URL | Extrait) :
{context}
---
AFFIRMATION À VÉRIFIER :
{claim}

RÉPONSE :"""

def executer_fact_checking(claim: str, context_sources: str) -> str:
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    prompt = PromptTemplate.from_template(template)
    
    chain = ({"context": lambda x: context_sources, "claim": lambda x: claim} 
             | prompt | llm | StrOutputParser())
    
    return chain.invoke({"context": context_sources, "claim": claim})

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking Traçable", page_icon="🛡️")
st.title("🛡️ Outil de Fact-Checking (Sources Traçables)")

user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
if st.button("Lancer l'analyse factuelle"):
    with st.spinner("Recherche et analyse en cours..."):
        sources_info = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources_info)
        
        st.markdown("### ⚖️ Verdict et Analyse")
        st.write(resultat)
