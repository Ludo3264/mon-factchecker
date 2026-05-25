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
    query = f"{claim} site:liberation.fr OR site:lemonde.fr OR site:afp.com"
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
        sources = search_trusted_sources(user_claim)
        template = """Tu es un expert en fact-checking. 
        RÈGLES : 1. VERDICT (VRAI, FAUX, NUANCÉ). 2. ANALYSE (Faits établis). 3. TRAÇABILITÉ (URLs).
        SOURCES : {context}
        AFFIRMATION : {claim}"""
        
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        resultat = chain.invoke({"context": sources, "claim": user_claim})
        
        st.markdown("### ⚖️ Résultat")
        st.write(resultat)
        
        rapport_complet = f"ANALYSE EMI\n\nAffirmation : {user_claim}\n\n{resultat}\n\nSOURCES :\n{sources}"
        st.download_button("📥 Télécharger le rapport (.txt)", rapport_complet, "analyse.txt")
        
        st.markdown("---")
        st.markdown("### 🔗 Sources utilisées")
        st.write(sources)

with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image ou d\'une photo</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Apprendre à vérifier si une image n'est pas périmée, détournée ou modifiée.")
    
    # --- OPTION A : L'IMAGE VIENT DU WEB ---
    st.markdown("---")
    st.markdown("#### 🌐 Option 1 : L'image est déjà sur Internet")
    image_url = st.text_input(
        "Collez l'URL de l'image (clic droit -> 'Copier le lien de l'image') :", 
        placeholder="https://exemple.com/image.jpg"
    )
    
    if image_url:
        try:
            st.image(image_url, caption="Image soumise via URL", width=300)
            encoded_url = urllib.parse.quote_plus(image_url)
            
            lens_url = f"https://lens.google.com/uploadbyurl?url={encoded_url}"
            tineye_url = f"https://tineye.com/search/?url={encoded_url}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("👁️ Google Lens (URL)", lens_url, type="primary", use_container_width=True)
            with col2:
                st.link_button("🤖 TinEye (URL)", tineye_url, use_container_width=True)
        except Exception:
            st.error("Impossible d'afficher cette image. Vérifiez le lien.")

    # --- OPTION B : L'IMAGE EST SUR LE TÉLÉPHONE / L'ORDINATEUR ---
    st.markdown("---")
    st.markdown("#### 📱 Option 2 : Vous avez enregistré l'image (Fichier / Galerie)")
    st.write("Si l'image est sur votre appareil, utilisez les plateformes officielles :")
    
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.link_button("📸 Uploader sur Google Lens officiel", "https://lens.google.com", use_container_width=True)
        st.caption("Utilisez l'icône appareil photo pour envoyer une image de votre galerie.")
    with col_up2:
        st.link_button("🤖 Uploader sur TinEye officiel", "https://tineye.com", use_container_width=True)
        st.caption("Cliquez sur le bouton 'Upload' (flèche) pour envoyer votre fichier.")

    st.markdown("""
    ---
    ### 💡 Astuces :
    * **Le réflexe capture d'écran :** Si une image sur Instagram ou TikTok refuse de donner son URL, faites une **capture d'écran**, utilisez l'**Option 2** et uploadez-la directement.
    """)
