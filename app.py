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
    query = f"{claim} {query_sites} -filetype:pdf"
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
    user_claim = st.text_area("Saisissez l'affirmation ou les mots-clés à vérifier :")
    if st.button("Lancer l'analyse textuelle"):
        with st.spinner("Analyse critique en cours..."):
            sources = search_trusted_sources(user_claim)
            
            # Nouveau template orienté vers l'analyse nuancée et l'esprit critique
            template = """Tu es un assistant de recherche pour l'Éducation aux Médias et à l'Information (EMI).
            TA MISSION : Aider l'utilisateur à comprendre la complexité d'une information en analysant les sources fournies.

            RÈGLES STRICTES :
            1. SYNTHÈSE : Ne conclus pas par un verdict arbitraire. Si les sources sont complexes, expose la nuance.
            2. CONTEXTUALISATION : Pour chaque source, explique brièvement le contexte (date, sujet principal de l'article).
            3. GESTION DES CONTRADICTIONS : Si les sources disent des choses différentes, expose clairement la contradiction au lieu de trancher.
            4. FIABILITÉ : Donne la priorité à la source qui traite le fait le plus directement.

            RÉPONDRE SELON CE FORMAT :
            - VERDICT : (VRAI / FAUX / NUANCÉ / À VÉRIFIER)
            - SYNTHÈSE DES FAITS : (Explique ce que disent les sources sans interprétation personnelle)
            - ANALYSE DU CONTEXTE : (Pourquoi les sources peuvent sembler contradictoires selon leur date ou leur sujet)
            - SOURCES UTILISÉES : (Liste avec liens et dates si disponibles)

            SOURCES : {context}
            AFFIRMATION À ANALYSER : {claim}"""
            
            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
            resultat = chain.invoke({"context": sources, "claim": user_claim})
            
            st.markdown("### ⚖️ Résultat de l'analyse")
            st.write(resultat)
            
            st.download_button("📥 Télécharger le rapport (.txt)", f"ANALYSE EMI\n\n{resultat}\n\nSOURCES :\n{sources}", "analyse.txt")
            
            with st.expander("🔗 Voir les sources détaillées"):
                st.write(sources)

with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image</p>', unsafe_allow_html=True)
    image_url = st.text_input("Collez l'URL de l'image :")
    if image_url:
        encoded_url = urllib.parse.quote_plus(image_url)
        col1, col2 = st.columns(2)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded_url}", use_container_width=True)
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded_url}", use_container_width=True)
    st.markdown("---")
    st.markdown("#### 📱 Option 2 : Upload fichier")
    c1, c2 = st.columns(2)
    with c1: st.link_button("📸 Google Lens", "https://lens.google.com", use_container_width=True)
    with c2: st.link_button("🤖 TinEye", "https://tineye.com", use_container_width=True)
