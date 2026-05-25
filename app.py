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
    # Construction dynamique : recherche sur sites de confiance, exclusion PDF
    query_sites = " OR ".join(TRUSTED_SITES)
    search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
    # Recherche souple sans guillemets stricts pour assurer la trouvaille, mais exclusion PDF
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
        with st.spinner("Analyse en cours par l'expert fact-checking..."):
            sources = search_trusted_sources(user_claim)
            template = """Tu es un expert en fact-checking. 
            RÈGLES : 
            1. VERDICT (VRAI, FAUX, NUANCÉ). 
            2. ANALYSE (Faits établis, pas de suppositions). 
            3. TRAÇABILITÉ (URLs).
            Si les sources ne permettent pas de conclure, indique explicitement : "Les preuves disponibles sont insuffisantes pour confirmer ou infirmer cette affirmation."
            SOURCES : {context}
            AFFIRMATION : {claim}"""
            
            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
            resultat = chain.invoke({"context": sources, "claim": user_claim})
            
            st.markdown("### ⚖️ Résultat")
            if "VRAI" in resultat.upper():
                st.success(resultat)
            elif "FAUX" in resultat.upper():
                st.error(resultat)
            else:
                st.warning(resultat)
            
            rapport_complet = f"ANALYSE EMI\n\nAffirmation : {user_claim}\n\n{resultat}\n\nSOURCES :\n{sources}"
            st.download_button("📥 Télécharger le rapport (.txt)", rapport_complet, "analyse.txt")
            
            with st.expander("🔗 Voir les sources détaillées"):
                st.write(sources)

with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image ou d\'une photo</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Apprendre à vérifier si une image n'est pas périmée, détournée ou modifiée.")
    
    st.markdown("---")
    st.markdown("#### 🌐 Option 1 : L'image est déjà sur Internet")
    image_url = st.text_input("Collez l'URL de l'image (clic droit -> 'Copier le lien de l'image') :")
    
    if image_url:
        try:
            st.image(image_url, caption="Image soumise via URL", width=300)
            encoded_url = urllib.parse.quote_plus(image_url)
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("👁️ Google Lens (URL)", f"https://lens.google.com/uploadbyurl?url={encoded_url}", type="primary", use_container_width=True)
            with col2:
                st.link_button("🤖 TinEye (URL)", f"https://tineye.com/search/?url={encoded_url}", use_container_width=True)
        except Exception:
            st.error("Impossible d'afficher cette image. Vérifiez le lien.")

    st.markdown("---")
    st.markdown("#### 📱 Option 2 : Vous avez enregistré l'image (Fichier / Galerie)")
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.link_button("📸 Uploader sur Google Lens officiel", "https://lens.google.com", use_container_width=True)
    with col_up2:
        st.link_button("🤖 Uploader sur TinEye officiel", "https://tineye.com", use_container_width=True)

    st.markdown("""
    ---
    ### 💡 Astuces :
    * **Le réflexe capture d'écran :** Si une image sur les réseaux sociaux refuse de donner son URL, faites une **capture d'écran** et uploadez-la directement via les boutons de l'Option 2.
    """)
