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
# TEMPLATE RIGUEUR FACTUELLE
# ==============================================================================
template = """Tu es un expert en fact-checking. Ta mission est d'établir la vérité factuelle.

RÈGLES D'OR :
1. VÉRITÉ FACTUELLE : Un fait documenté par les sources fournies est une VÉRITÉ ÉTABLIE. Ne jamais le qualifier de "discutable" ou "nuancé".
2. ANALYSE :
   - FAITS ÉTABLIS : Liste uniquement les faits prouvés en citant la source correspondante sous la forme.
   - DÉBATS & OPINIONS : Analyse les commentaires politiques sans les confondre avec des faits.
   - VERDICT : VRAI, FAUX ou NUANCÉ.
3. CITATIONS : Utilise impérativement le format en te basant sur les sources numérotées ci-dessous.

---
EXTRAITS SOURCES :
{context}
---
AFFIRMATION À VÉRIFIER :
{claim}

RÉPONSE :"""

def executer_fact_checking(claim: str, context_sources: str) -> str:
    # Nettoyage et structuration des sources pour forcer la citation précise
    sources_liste = context_sources.split("...") 
    sources_structurees = "\n".join([f"Source {i+1}: {s.strip()}" for i, s in enumerate(sources_liste) if len(s) > 10])
    
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    prompt = PromptTemplate.from_template(template)
    
    chain = ({"context": lambda x: sources_structurees, "claim": lambda x: claim} 
             | prompt | llm | StrOutputParser())
    
    return chain.invoke({"context": sources_structurees, "claim": claim})

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking Rigoureux", page_icon="🛡️")
st.title("🛡️ Outil de Fact-Checking (Rigueur Absolue)")

user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
if st.button("Lancer l'analyse factuelle"):
    with st.spinner("Analyse en cours..."):
        sources_brutes = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources_brutes)
        
        st.markdown("### ⚖️ Verdict et Analyse")
        st.write(resultat)
        
        with st.expander("🔗 Voir les sources brutes (pour vérification)"):
            st.write(sources_brutes)
