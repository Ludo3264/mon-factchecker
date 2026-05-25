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
st.markdown('<p style="color: #4B5563; margin-bottom: 25px;">Version Réseau International & Laboratoire d\'images (Propulsée par Groq & Llama 3.1)</p>', unsafe_allow_html=True)

# Création des onglets pour séparer les deux ateliers
tab1, tab2 = st.tabs(["✍️ Vérifier un Texte (Moteur IA d'origine)", "🖼️ Vérifier une Image (Recherche Inversée)"])

# ==============================================================================
# ONGLET 1 : VOTRE BLOC DE CODE TEXTE INITIAL (Totalement inchangé)
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
# ONGLET 2 : AJOUT DE LA RECHERCHE D'IMAGE INVERSÉE (Le laboratoire EMI)
# ==============================================================================
with tab2:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Traquer l\'origine d\'une image ou d\'une photo</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Apprendre à vérifier si une image n'est pas périmée, détournée ou modifiée.")
    
    image_url = st.text_input(
        "Collez l'URL de l'image à vérifier (clic droit sur une image du web -> 'Copier le lien de l'image') :", 
        placeholder="https://exemple.com/image.jpg"
    )
    
    if image_url:
        try:
            # Affichage visuel de la photo soumise
            st.image(image_url, caption="Image soumise à l'analyse", width=350)
            
            # Encodage propre de l'URL pour la compatibilité des liens
            encoded_url = urllib.parse.quote_plus(image_url)
            
            # Liens vers la boîte à outils universelle des fact-checkers
            lens_url = f"https://lens.google.com/uploadbyurl?url={encoded_url}"
            tineye_url = f"https://tineye.com/search/?url={encoded_url}"
            yandex_url = f"https://yandex.com/images/search?rpt=imageview&url={encoded_url}"
            
            st.markdown('<p style="font-size:1.1rem; font-weight:bold; margin-top:15px;">🔍 Outils de recherche inversée à activer :</p>', unsafe_allow_html=True)
            st.info("Le clic sur un bouton ouvrira automatiquement les résultats dans un nouvel onglet.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.link_button("👁️ Google Lens", lens_url, type="primary", use_container_width=True)
                st.caption("Idéal pour identifier des objets, monuments ou traduire du texte présent dans l'image.")
                
            with col2:
                st.link_button("🤖 TinEye", tineye_url, use_container_width=True)
                st.caption("Le meilleur pour trouver la **date d'apparition la plus ancienne** et détecter les montages.")
                
            with col3:
                st.link_button("🇷🇺 Yandex Images", yandex_url, use_container_width=True)
                st.caption("Redoutable pour la reconnaissance faciale dans une foule et les paysages extérieurs.")
                
            st.markdown("""
            ---
            ### 💡 Astuces d'animation pour l'atelier :
            * **Piste 1 (Chronologie) :** Demandez aux usagers de trier les résultats de **TinEye** par "Oldest" (Le plus ancien). C'est le moyen le plus rapide de prouver qu'une photo liée à une actualité récente circule en réalité depuis des années.
            * **Piste 2 (Comparaison) :** Faites observer que Google et Yandex ne trouvent pas la même chose, montrant ainsi qu'aucun algorithme n'est exhaustif.
            """)
            
        except Exception:
            st.error("Impossible d'afficher cette image. Assurez-vous que le lien se termine par une extension valide (.jpg, .png, .webp).")
