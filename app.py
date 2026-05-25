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
# TEMPLATE RIGUEUR FACTUELLE (Verdict en tête)
# ==============================================================================
template = """Tu es un expert en fact-checking. Ta mission est d'établir la vérité factuelle.

RÈGLES D'AFFICHAGE :
1. VERDICT : Affiche le verdict (VRAI, FAUX, ou NUANCÉ) tout en haut de ta réponse.
2. FAITS ÉTABLIS : Liste uniquement les faits prouvés en utilisant la référence [Source X] issue des extraits ci-dessous.
3. DÉBATS & OPINIONS : Analyse les commentaires sans les confondre avec des faits.
4. RÉFÉRENCES : Liste le texte des sources utilisées avec leur numéro correspondant.

---
EXTRAITS SOURCES :
{context}
---
AFFIRMATION À VÉRIFIER :
{claim}

RÉPONSE :"""

def executer_fact_checking(claim: str, context_sources: str) -> str:
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
st.title("🛡️ Outil de Fact-Checking (Verdict en Premier)")

user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
if st.button("Lancer l'analyse factuelle"):
    with st.spinner("Analyse en cours..."):
        sources_brutes = search_trusted_sources(user_claim)
        resultat = executer_fact_checking(user_claim, sources_brutes)
        
        st.markdown("### ⚖️ Verdict et Analyse")
        st.write(resultat)
        
        with st.expander("🔗 Voir les sources brutes"):
            st.write(sources_brutes)
