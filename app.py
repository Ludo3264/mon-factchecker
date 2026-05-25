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
        search = GoogleSerperAPIWrapper(serper_api_key=st.secrets["SERPER_API_KEY"], gl="fr", hl="fr")
        results = search.results(search_query)
    except Exception as e:
        return [], f"Erreur de recherche : {e}"
    
    sources_list, formatted = [], []
    for res in results.get("organic", [])[:4]:
        title, link, snippet = res.get("title", "Sans titre"), res.get("link", ""), res.get("snippet", "")
        sources_list.append({"title": title, "link": link, "snippet": snippet})
        formatted.append(f"- {title}\n  URL : {link}\n  Extrait : {snippet}")
    return sources_list, "\n\n".join(formatted) if formatted else "Aucune source trouvée."

# ==============================================================================
# LOGIQUE D'ANALYSE
# ==============================================================================
ANALYSIS_TEMPLATE = """Tu es un assistant pédagogique en Éducation aux Médias (EMI).
RÈGLES :
1. Analyse les sources (sites web et documents PDF).
2. Si une info est absente, ne l'invente pas. Précise "Connaissance externe" si nécessaire.
3. S'il y a des contradictions, expose-les clairement.

SOURCES : {context}
AFFIRMATION : {claim}

RÉPONDRE SELON CE PLAN :
## 🔎 ÉVALUATION PRÉLIMINAIRE
Commence par : VRAI, FAUX, NUANCÉ ou INDÉTERMINÉ (en majuscules), suivi de 2 lignes de justification.
## 📋 ANALYSE FACTUELLE
Détaille les preuves trouvées.
## ❓ QUESTIONS À SE POSER
3 à 5 questions critiques pour l'élève.
## 🧭 PISTE DE VÉRIFICATION
Démarche concrète de vérification.
## ⚠️ MISE EN GARDE
Risques d'hallucination ou sensibilité."""

def analyze_claim(claim: str, context: str) -> str:
    llm = ChatGroq(api_key=st.secrets["GROQ_API_KEY"], model="llama-3.1-8b-instant", temperature=0)
    chain = PromptTemplate.from_template(ANALYSIS_TEMPLATE) | llm | StrOutputParser()
    return chain.invoke({"context": context, "claim": claim})

def display_verdict(text: str):
    verdict = next((v for v in ["VRAI", "FAUX", "NUANCÉ", "INDÉTERMINÉ"] if v in text[:50].upper()), "INDÉTERMINÉ")
    cfg = {"VRAI": ("#d1fae5", "#065f46"), "FAUX": ("#fee2e2", "#991b1b"), "NUANCÉ": ("#fef3c7", "#92400e"), "INDÉTERMINÉ": ("#e0e7ff", "#3730a3")}
    bg, fg = cfg.get(verdict, ("#f3f4f6", "#374151"))
    st.markdown(f'<div style="background:{bg};color:{fg};padding:10px;border-radius:5px;font-weight:bold;display:inline-block;">{verdict}</div>', unsafe_allow_html=True)

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
    if st.button("🔍 Lancer l'analyse"):
        with st.spinner("Analyse en cours..."):
            sources_list, context_str = search_trusted_sources(user_claim)
            resultat = analyze_claim(user_claim, context_str)
            st.markdown("### ⚖️ Résultat")
            display_verdict(resultat)
            st.markdown(resultat)
            with st.expander("🔗 Voir les sources"):
                for s in sources_list: st.write(f"**{s['title']}**: {s['link']}")
            st.download_button("📥 Télécharger le rapport", resultat, "analyse.txt")

with tab2:
    st.markdown("#### Traquer l'origine d'une image")
    image_url = st.text_input("Collez l'URL de l'image :")
    if image_url:
        enc = urllib.parse.quote_plus(image_url)
        c1, c2, c3 = st.columns(3)
        with c1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={enc}", use_container_width=True)
        with c2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={enc}", use_container_width=True)
        with c3: st.link_button("🔎 Bing Visual", f"https://www.bing.com/images/search?q=imgurl:{enc}", use_container_width=True)

with tab3:
    st.markdown("#### Comment fonctionne cet outil ?")
    st.markdown("""Utilisez cet outil pour développer votre esprit critique. Il recherche des sources de confiance et propose une analyse structurée. **Rappelez-vous : l'IA est une aide à la réflexion, elle ne remplace pas votre jugement.**""")
