import os
import streamlit as st
import urllib.parse
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION DES SOURCES (Strictement identique à votre code)
# ==============================================================================
TRUSTED_SITES = [
    # --- FRANCE (Les piliers certifiés) ---
    "site:factuel.afp.com",              # AFP Factuel (International & France)
    "site:lemonde.fr/les-decodeurs",     # Les Décodeurs (Le Monde)
    "site:liberation.fr/checknews",      # CheckNews (Libération)
    "site:francetvinfo.fr/vrai-ou-fake", # Vrai ou Fake (France Info)
    
    # --- EUROPE & INTERNATIONAL (Bases de données globales) ---
    "site:factcheck.org",                # Référence mondiale indépendante
    "site:fullfact.org",                 # Référence Europe / UK
    "site:snopes.com",                   # Le plus grand site mondial historique
    "site:reuters.com/fact-check",       # Reuters Fact Check (Monde entier)
    "site:euvsdisinfo.eu"                # Base officielle de l'Union Européenne contre la désinformation
]
search_query_restriction = " OR ".join(TRUSTED_SITES)

# ==============================================================================
# LOGIQUE MÉTIER TEXTE (Strictement identique à votre code)
# ==============================================================================
def search_trusted_sources(claim: str) -> str:
    try:
        search = GoogleSerperAPIWrapper(gl="fr", hl="fr")
        full_query = f"({claim}) ({search_query_restriction})"
        return search.run(full_query)
    except Exception as e:
        return f"Erreur moteur de recherche : {str(e)}"

template = """Tu es un expert en fact-checking de niveau international.
Ton rôle unique est de vérifier l'affirmation d'un utilisateur en te basant EXCLUSIVEMENT sur les extraits de presse fournis ci-dessous.

RÈGLES CRITIQUES :
1. Si les extraits de presse ne permettent pas de prouver si l'info est vraie ou fausse, réponds EXACTEMENT : 
   "Je ne trouve aucune vérification de cette information dans les sources officielles de fact-checking."
2. Interdiction d'utiliser tes propres connaissances si les extraits n'en parlent pas.
3. Si la réponse y est, commence par le verdict (VRAI, FAUX, ou NUANCÉ) et cite le média source (ex: AFP, Reuters, Snopes).
4. Traduis ou résume en français si la source trouvée est en anglais.

---
EXTRAITS DE PRESSE SÉLECTIONNÉS :
{context}
---

AFFIRMATION À ANALYSER :
{claim}

VERDICT :"""

prompt = PromptTemplate.from_template(template)

def executer_fact_checking(claim: str, context_sources: str) -> str:
    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        fact_check_chain = (
            {"context": RunnablePassthrough(), "claim": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return fact_check_chain.invoke({"context": context_sources, "claim": claim})
    except Exception as e:
        return f"Erreur d'analyse : {str(e)}"

# ==============================================================================
# INTERFACE UTILISATEUR (Configuration de la page - Première commande obligatoire)
# ==============================================================================
st.set_page_config(page_title="Fact-Checking Global", page_icon="🛡️", layout="centered")

st.markdown('<p style="font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px;">🛡️ Outil de Fact-Checking Global & EMI</p>', unsafe_allow_html=True)
st.markdown('<p style="color: #4B5563; margin-bottom: 25px;">Version Réseau International & Laboratoires Visuels (Propulsée par Groq & Llama 3.1)</p>', unsafe_allow_html=True)

# Création des trois onglets pour séparer les ateliers
tab1, tab2, tab3 = st.tabs([
    "✍️ Vérifier un Texte (Moteur IA d'origine)", 
    "🖼️ Vérifier une Image (Recherche Inversée)",
    "📹 Vérifier une Vidéo (Analyse Visuelle)"
])

# ==============================================================================
# ONGLET 1 : BLOC DE CODE TEXTE INITIAL (Totalement inchangé)
# ==============================================================================
with tab1:
    user_claim = st.text_area("Saisissez l'affirmation à vérifier :", placeholder="Exemple : Une rumeur internationale dit que...", height=100)

    if st.button("Lancer la vérification", type="primary"):
        if not user_claim.strip():
            st.warning("⚠️ Saisissez du texte avant de lancer.")
        else:
            with st.spinner("🔍 Recherche sur le réseau international..."):
                sources_text = search_trusted_sources(user_claim)
            with st.spinner("🤖 Analyse critique multilingue par l'IA..."):
                resultat_verdict = executer_fact_checking(user_claim, sources_text)
                
            st.markdown('<p style="font-size:1.3rem; font-weight:bold; margin-top:20px;">⚖️ Analyse et conclusions :</p>', unsafe_allow_html=True)
            if "Je ne trouve aucune vérification" in resultat_verdict:
                st.info(resultat_verdict)
            else:
                st.success(resultat_verdict)
                
            with st.expander("🔗 Consulter les extraits de presse bruts (Monde)"):
                st.write(sources_text)

# ==============================================================================
# ONGLET 2 : RECHERCHE D'IMAGE INVERSÉE (Totalement inchangé)
# ==============================================================================
with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image ou d\'une photo</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Apprendre à vérifier si une image n'est pas périmée, détournée ou modifiée.")
    
    # --- OPTION A : L'IMAGE VIENT DU WEB ---
    st.markdown("---")
    st.markdown("#### 🌐 Option 1 : L'image est déjà sur Internet")
    image_url = st.text_input(
        "Collez l'URL de l'image (clic droit sur une image du web -> 'Copier le lien de l'image') :", 
        placeholder="https://exemple.com/image.jpg",
        key="url_mode"
    )
    
    if image_url:
        try:
            st.image(image_url, caption="Image soumise via URL", width=300)
            encoded_url = urllib.parse.quote_plus(image_url)
            
            lens_url = f"https://lens.google.com/uploadbyurl?url={encoded_url}"
            tineye_url = f"https://tineye.com/search/?url={encoded_url}"
            yandex_url = f"https://yandex.com/images/search?rpt=imageview&url={encoded_url}"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("👁️ Google Lens (URL)", lens_url, type="primary", use_container_width=True)
            with col2:
                st.link_button("🤖 TinEye (URL)", tineye_url, use_container_width=True)
            with col3:
                st.link_button("🇷🇺 Yandex (URL)", yandex_url, use_container_width=True)
        except Exception:
            st.error("Impossible d'afficher cette image. Vérifiez le lien.")

    # --- OPTION B : L'IMAGE EST SUR LE TÉLÉPHONE / L'ORDINATEUR ---
    st.markdown("---")
    st.markdown("#### 📱 Option 2 : Vous avez enregistré l'image (Fichier / Galerie)")
    st.write("Si l'image est enregistrée sur votre appareil (ou si vous voulez la prendre en photo en direct), utilisez les plateformes officielles :")
    
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.link_button("📸 Uploader sur Google Lens officiel", "https://lens.google.com", use_container_width=True)
        st.caption("Sur mobile, cliquez sur l'icône d'appareil photo pour envoyer une image de votre galerie ou prendre une photo en direct.")
    with col_up2:
        st.link_button("🤖 Uploader sur TinEye officiel", "https://tineye.com", use_container_width=True)
        st.caption("Cliquez sur le bouton 'Upload' (flèche) pour envoyer votre fichier image.")

    st.markdown("""
    ---
    ### 💡 Astuces :
    * **Le réflexe capture d'écran :** Si une image sur Instagram ou TikTok refuse de donner son URL, faire une **capture d'écran**, utiliser l'**Option 2** et l'uploader directement sur le Google Lens officiel.
    """)

# ==============================================================================
# ONGLET 3 : LA STATION DE FACT-CHECKING VIDÉO (Nouveau volet)
# ==============================================================================
with tab3:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Enquêter sur une vidéo suspecte (TikTok, Reels, YouTube)</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Apprendre à repérer les vidéos sorties de leur contexte, recyclées ou générées par IA (Deepfakes).")
    
    st.markdown("#### 🛠️ La boîte à outils du Fact-Checking Vidéo")
    st.write("Pour analyser une vidéo, l'astuce consiste à la découper en images fixes pour les analyser séparément.")

    col_vid1, col_vid2 = st.columns(2)
    with col_vid1:
        st.link_button("🛡️ Ouvrir l'outil mondial InVID / WeVerify", "https://www.invid-project.eu/", type="primary", use_container_width=True)
        st.caption("L'extension incontournable des journalistes. Elle permet de découper n'importe quelle vidéo du web en images clés d'un simple clic.")
    with col_vid2:
        st.link_button("🎞️ Utiliser Watch Frame by Frame", "http://www.watchframebyframe.com/", use_container_width=True)
        st.caption("Idéal pour analyser une vidéo YouTube ou Vimeo seconde par seconde (image par image) pour repérer les faux raccords ou les trucages numériques.")

    st.markdown("""
    ---
    ### 💡 Guide d'animation pour votre atelier Vidéo :
    En EMI, apprenez-leur à devenir des **détectives visuels** en analysant 4 indices clés dans une vidéo :
    1. **La météo et la végétation :** Si la vidéo prétend avoir été filmée en Ukraine en plein mois de décembre mais qu'il y a des arbres verts et des gens en T-shirt, c'est un recyclage d'images anciennes.
    2. **Les détails urbains :** Regardez les plaques d'immatriculation des voitures, la forme des panneaux publicitaires ou la langue des écritures sur les devantures des commerces.
    3. **Les anomalies physiques (Spécial Deepfake) :** Demandez aux élèves de fixer les yeux de la personne (cligne-t-elle des yeux normalement ?), l'intérieur de la bouche quand elle parle, ou les contours de son visage (y a-t-il un effet de flou bizarre autour des oreilles, du cou ou de ses cheveux ?).
    4. **La technique de la capture d'écran :** Demandez aux élèves de faire pause sur un moment marquant et net de la vidéo suspecte. Prenez une **capture d'écran** de ce moment précis, basculez sur l'**Onglet 2 (Image)** de l'application et uploadez-la sur Google Lens. Très souvent, la vidéo d'origine est retrouvée immédiatement !
    """)
