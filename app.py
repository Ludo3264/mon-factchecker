import streamlit as st
import urllib.parse
import re
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TRUSTED_SITES = [
    "site:factuel.afp.com", "site:lemonde.fr/les-decodeurs", "site:liberation.fr/checknews",
    "site:francetvinfo.fr/vrai-ou-fake", "site:factcheck.org", "site:fullfact.org",
    "site:snopes.com", "site:reuters.com/fact-check", "site:euvsdisinfo.eu"
]

def search_trusted_sources(claim: str) -> tuple[list[dict], str]:
    query_sites = " OR ".join(TRUSTED_SITES)
    # Suppression du filtre -filetype:pdf pour inclure les rapports officiels
    search_query = f"{claim} ({query_sites})"
    
    try:
        search = GoogleSerperAPIWrapper(
            serper_api_key=st.secrets["SERPER_API_KEY"],
            gl="fr", hl="fr"
        )
        results = search.results(search_query)
    except Exception as e:
        st.error(f"❌ Erreur Serper : {e}")
        return [], "Aucune source disponible."

    sources_list, formatted = [], []
    for res in results.get("organic", [])[:4]:
        title, link, snippet = res.get("title", "Sans titre"), res.get("link", ""), res.get("snippet", "")
        sources_list.append({"title": title, "link": link, "snippet": snippet})
        formatted.append(f"- {title}\n  URL : {link}\n  Extrait : {snippet}")
    context_str = "\n\n".join(formatted) if formatted else "Aucune source pertinente trouvée."
    return sources_list, context_str

# Template mis à jour pour hiérarchiser les PDF comme preuves documentaires
ANALYSIS_TEMPLATE = """Tu es un assistant pédagogique spécialisé en Éducation aux Médias et à l'Information (EMI).

RÈGLES IMPÉRATIVES :
1. ANALYSE CRITIQUE : Utilise UNIQUEMENT les sources fournies. 
   - Si tu identifies des documents PDF parmi les sources, traite-les comme des rapports officiels ou des études de référence et donne-leur un poids important dans l'évaluation.
   - Si une source est trop technique ou hors sujet, écarte-la explicitement.
2. DISTINCTION : Si une source contredit l'autre, expose clairement la contradiction.
3. CONNAISSANCE EXTERNE : Si tu utilises une info hors sources, précise "Connaissance externe".

SOURCES VÉRIFIÉES :
{context}

AFFIRMATION ANALYSÉE : {claim}

## 🔎 ÉVALUATION PRÉLIMINAIRE
Commence par : VRAI / FAUX / NUANCÉ / INDÉTERMINÉ (en majuscules), suivi d'une justification courte.

## 📋 ANALYSE FACTUELLE
Analyse le contenu des sites ET des documents (PDF). Mentionne si un document officiel apporte une preuve définitive ou une nuance.

## ❓ QUESTIONS À SE POSER
3 à 5 questions critiques pour l'utilisateur.

## 🧭 PISTE DE VÉRIFICATION PERSONNELLE
Démarche concrète que l'utilisateur peut faire.

## ⚠️ MISE EN GARDE
Risques d'hallucination ou sujets sensibles."""

def analyze_claim(claim: str, context: str) -> str:
    try:
        llm = ChatGroq(api_key=st.secrets["GROQ_API_KEY"], model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(ANALYSIS_TEMPLATE) | llm | StrOutputParser()
        return chain.invoke({"context": context, "claim": claim})
    except Exception as e:
        return f"❌ Erreur LLM : {e}"

# (Les fonctions detect_verdict, display_verdict_badge et la suite de l'interface restent identiques à votre code précédent)
