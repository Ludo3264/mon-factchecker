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

def search_trusted_sources(claim: str) -> str:
    search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
    results = search.results(f"{claim} ({' OR '.join(TRUSTED_SITES)})")
    # Structuration pour faciliter la citation
    formatted = [f"Source {i+1} ({res.get('title')}): {res.get('link')}\nExtrait: {res.get('snippet')}" 
                 for i, res in enumerate(results.get("organic", [])[:4])]
    return "\n\n".join(formatted) if formatted else "Aucune source trouvée."

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️")
st.title("🛡️ Outil d'Analyse Critique (EMI)")

tab1, tab2 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
    if st.button("Lancer l'analyse textuelle"):
        sources = search_trusted_sources(user_claim)
        template = """Tu es un expert en fact-checking.
        
        RÈGLES STRICTES :
        1. VERDICT : Affiche VRAI, FAUX ou NUANCÉ en premier.
        2. HIÉRARCHIE DES FAITS : Les faits biographiques notoires (ex: homosexualité d'une personnalité publique, fonctions exercées) sont des faits établis. Ne les remets jamais en doute.
        3. TRAITEMENT DES SOURCES : N'utilise jamais une source documentant la désinformation (ex: euvsdisinfo.eu) pour invalider un fait biographique. Ces sources servent uniquement à expliquer comment des manipulateurs utilisent des faits.
        4. CITATIONS : Utilise exclusivement les URLs fournies dans le contexte ci-dessous pour justifier tes propos.
        
        SOURCES : {context}
        AFFIRMATION : {claim}"""
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        st.write(chain.invoke({"context": sources, "claim": user_claim}))

with tab2:
    st.markdown("### 🖼️ Recherche d'image inversée")
    img_url = st.text_input("URL de l'image :")
    if img_url:
        encoded = urllib.parse.quote_plus(img_url)
        st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded}")
        st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded}")
        st.markdown("### Sources de confiance pour le contexte :")
        for site in TRUSTED_SITES:
            site_name = site.split(':')[1]
            st.markdown(f"- [Vérifier sur {site_name}](https://www.google.com/search?q={site}+image)")
