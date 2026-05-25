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
    query_sites = " OR ".join(TRUSTED_SITES)
    search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
    # On ajoute des mots-clés de confirmation pour aider l'IA à trouver le consensus
    query = f"{claim} confirmation fait établi {query_sites} -filetype:pdf"
    results = search.results(query)
    
    formatted = []
    for res in results.get("organic", [])[:3]:
        formatted.append(f"Source: {res.get('title')} | URL: {res.get('link')}\nExtrait: {res.get('snippet')}")
    
    return "\n\n".join(formatted) if formatted else "Aucune source pertinente trouvée."

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️")
st.title("🛡️ Outil d'Analyse Critique (EMI)")

tab1, tab2 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image"])

with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :")
    if st.button("Lancer l'analyse textuelle"):
        with st.spinner("Analyse approfondie en cours..."):
            sources = search_trusted_sources(user_claim)
            
            # Template renforcé pour la recherche de consensus factuel
            template = """Tu es un expert en fact-checking. 
            TA MISSION : Établir la réalité des faits. 
            RÈGLES :
            1. RECHERCHE DE CONSENSUS : Identifie les sources qui confirment un fait établi par les médias de référence.
            2. MISE EN PERSPECTIVE : Si des articles anciens mentionnent des débats, explique qu'il s'agissait d'un contexte passé et que le fait est désormais largement documenté et reconnu.
            3. VERDICT : VRAI (si le fait est reconnu), FAUX, ou NUANCÉ.
            4. TRAÇABILITÉ : Liste les sources.

            SOURCES DISPONIBLES : {context}
            AFFIRMATION À ANALYSER : {claim}"""
            
            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
            resultat = chain.invoke({"context": sources, "claim": user_claim})
            
            st.markdown("### ⚖️ Résultat de l'analyse")
            st.write(resultat)
            
            with st.expander("🔗 Voir les sources détaillées"):
                st.write(sources)
