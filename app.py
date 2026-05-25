import streamlit as st
import urllib.parse
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
    search_query = f"{claim} ({query_sites})"
    
    try:
        search = GoogleSerperAPIWrapper(
            serper_api_key=st.secrets["SERPER_API_KEY"],
            gl="fr", hl="fr"
        )
        results = search.results(search_query)
    except Exception as e:
        return [], f"Erreur lors de la recherche : {e}"

    sources_list, formatted = [], []
    for res in results.get("organic", [])[:4]:
        title, link, snippet = res.get("title", "Sans titre"), res.get("link", ""), res.get("snippet", "")
        sources_list.append({"title": title, "link": link, "snippet": snippet})
        formatted.append(f"- {title}\n  URL : {link}\n  Extrait : {snippet}")
    context_str = "\n\n".join(formatted) if formatted else "Aucune source trouvée."
    return sources_list, context_str

# ==============================================================================
# LOGIQUE D'ANALYSE (LLM)
# ==============================================================================
ANALYSIS_TEMPLATE = """Tu es un assistant pédagogique en Éducation aux Médias (EMI).
RÈGLES :
1. Analyse les sources fournies (sites web ET documents PDF).
2. Si une info est absente, ne l'invente pas. 
3. Sois transparent : si tu utilises tes propres connaissances, précise "Connaissance externe".
4. S'il y a des contradictions entre sources, expose-les.

SOURCES : {context}
AFFIRMATION : {claim}

RÉPONDRE SELON CE PLAN :
## 🔎 ÉVALUATION PRÉLIMINAIRE
Commence par : VRAI, FAUX, NUANCÉ ou INDÉTERMINÉ (en majuscules), suivi de 2 lignes de justification.
## 📋 ANALYSE FACTUELLE
Détaille les preuves trouvées dans les sources (inclus les PDF).
## ❓ QUESTIONS À SE POSER
3 à 5 questions critiques pour l'élève.
## 🧭 PISTE DE VÉRIFICATION
Démarche concrète de vérification.
## ⚠️ MISE EN GARDE
Risques d'hallucination ou sensibilité du sujet."""

def analyze_claim(claim: str, context: str) -> str:
    llm = ChatGroq(api_key=st.secrets["GROQ_API_KEY"], model="llama-3.1-8b-instant", temperature=0)
    chain = PromptTemplate.from_template(ANALYSIS_TEMPLATE) | llm | StrOutputParser()
    return chain.invoke({"context": context, "claim": claim})

def display_verdict(text: str):
    verdict = next((v for v in ["VRAI", "FAUX", "NUANCÉ", "INDÉTERMINÉ"] if v in text[:50].upper()), "INDÉTERMINÉ")
    cfg = {"VRAI": ("#d1fae5", "#065f46"), "FAUX": ("#fee2e2", "#991b1b"), "NUANCÉ": ("#fef3c7", "#92400e"), "INDÉTERMINÉ": ("#e0e7ff", "#3730a3")}
    bg, fg = cfg.get(verdict, ("#f3f4f6", "#374151"))
    st.markdown(f'<div style="background:{bg};color:{fg};padding:10px;border-radius:5px;font-weight:bold;">{verdict}</div>', unsafe_allow_html=True)

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️")
st.title("🛡️ Outil d'Analyse Critique — EMI")

user_claim = st.text_area("Saisissez l'affirmation à vérifier :")

if st.button("🔍 Lancer l'analyse"):
    if not user_claim:
        st.warning("Veuillez entrer un texte.")
    else:
        with st.spinner("Analyse en cours..."):
            sources_list, context_str = search_trusted_sources(user_claim)
            resultat = analyze_claim(user_claim, context_str)
            
            st.markdown("### ⚖️ Résultat")
            display_verdict(resultat)
            st.markdown(resultat)
            
            with st.expander("🔗 Voir les sources"):
                for s in sources_list:
                    st.write(f"**{s['title']}**: {s['link']}")
            
            st.download_button("📥 Télécharger le rapport", resultat, "analyse.txt")
