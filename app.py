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
    "site:francetvinfo.fr/vrai-ou-fake"
]

def search_trusted_sources(claim: str) -> str:
    search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
    # Recherche plus large mais toujours confinée aux sites de confiance
    query = f"{claim} ({' OR '.join(TRUSTED_SITES)})"
    results = search.results(query)
    
    formatted = []
    for res in results.get("organic", [])[:4]:
        formatted.append(f"Source: {res.get('title')} | URL: {res.get('link')}\nExtrait: {res.get('snippet')}")
    
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
        
        # Le template a été renforcé pour traiter les faits biographiques avec assurance
        template = """Tu es un expert en fact-checking.
        
        RÈGLES :
        1. VERDICT : Affiche VRAI, FAUX ou NUANCÉ.
        2. ANALYSE : Si les sources fournies mentionnent des faits biographiques (ex: homosexualité, fonctions), traite-les comme des faits établis et reconnus publiquement. N'hésite pas à valider ces informations si elles apparaissent dans les extraits.
        3. TRAÇABILITÉ : Cite impérativement l'URL de la source pour chaque fait cité.
        
        SOURCES FOURNIES : {context}
        AFFIRMATION : {claim}"""
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        resultat = chain.invoke({"context": sources, "claim": user_claim})
        
        st.markdown("### ⚖️ Résultat")
        st.write(resultat)
        st.markdown("---")
        st.markdown("### 🔗 Sources utilisées")
        st.write(sources)

with tab2:
    st.markdown("### 🖼️ Recherche d'image inversée")
    img_url = st.text_input("Collez l'URL de l'image ici :")
    
    st.markdown("#### 1. Moteurs d'inversion")
    if img_url:
        encoded = urllib.parse.quote_plus(img_url)
        st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded}")
        st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded}")
    else:
        st.info("Saisissez une URL pour activer les moteurs.")
            
    st.markdown("#### 2. Sources de confiance pour contexte")
    for site in TRUSTED_SITES:
        site_name = site.split(':')[1]
        query_url = f"https://www.google.com/search?q=site:{site_name}+image"
        st.link_button(f"Recherche sur {site_name}", query_url)
