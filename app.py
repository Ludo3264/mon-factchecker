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

def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        results = search.results(f"{claim} ({' OR '.join(TRUSTED_SITES)})")
        formatted = [f"Titre: {res.get('title')} | URL: {res.get('link')}\nExtrait: {res.get('snippet')}" 
                     for res in results.get("organic", [])[:4]]
        return "\n\n".join(formatted) if formatted else "Aucune source pertinente trouvée."
    except Exception as e:
        return f"Erreur : {str(e)}"

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️")
st.title("🛡️ Outil d'Analyse Critique (EMI)")

tab1, tab2 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation :")
    if st.button("Lancer l'analyse"):
        sources = search_trusted_sources(user_claim)
        
        template = """Tu es un expert en fact-checking. 
        VERDICT : VRAI, FAUX, ou NUANCÉ (en haut).
        FAITS : Liste les faits avec source et URL.
        DÉBATS : Sépare les opinions des faits.
        
        SOURCES : {context}
        AFFIRMATION : {claim}"""
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        chain = ({"context": lambda x: sources, "claim": lambda x: user_claim} 
                 | PromptTemplate.from_template(template) | llm | StrOutputParser())
        
        st.markdown("### ⚖️ Verdict et Analyse")
        st.write(chain.invoke({}))

with tab2:
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    img_url = st.text_input("URL de l'image à vérifier :")
    if img_url:
        encoded_url = urllib.parse.quote_plus(img_url)
        col1, col2 = st.columns(2)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded_url}")
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded_url}")
