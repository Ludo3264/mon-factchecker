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
        2. HIÉRARCHIE DES FAITS : Les faits biographiques notoires sont établis. Ne les remets jamais en doute en utilisant des sources d'analyse de désinformation.
        3. TRAÇABILITÉ : Liste les sources utilisées avec leurs URLs complètes pour chaque fait.
        
        SOURCES FOURNIES : {context}
        AFFIRMATION À VÉRIFIER : {claim}"""
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        resultat = chain.invoke({"context": sources, "claim": user_claim})
        
        st.markdown("### ⚖️ Résultat")
        st.write(resultat)
        st.markdown("---")
        st.markdown("### 🔗 Sources brutes utilisées")
        st.write(sources)

with tab2:
    st.markdown("### 🖼️ Recherche d'image inversée")
    img_url = st.text_input("Collez l'URL de l'image ici :")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 1. Moteurs d'inversion")
        if img_url:
            encoded = urllib.parse.quote_plus(img_url)
            st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded}")
            st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded}")
        else:
            st.info("Veuillez saisir une URL d'image ci-dessus.")
            
    with col_b:
        st.markdown("#### 2. Sources de confiance pour contexte")
        for site in TRUSTED_SITES:
            site_name = site.split(':')[1]
            # Lien direct pour chercher l'image sur le site spécifique via Google
            query_url = f"https://www.google.com/search?q=site:{site.split(':')[1]}+image"
            st.markdown(f"- [Recherche sur {site_name}]({query_url})")
