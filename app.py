import streamlit as st

# --- CONFIGURATION DES SOURCES ---
TRUSTED_SITES = [
    "site:factuel.afp.com", "site:lemonde.fr/les-decodeurs", "site:liberation.fr/checknews",
    "site:francetvinfo.fr/vrai-ou-fake", "site:snopes.com", "site:cnrs.fr", 
    "site:inserm.fr", "site:nasa.gov", "site:service-public.fr", "site:vie-publique.fr"
]

# --- LOGIQUE DE VERDICT ---
def get_verdict(analysis):
    analysis_lower = analysis.lower()
    if any(word in analysis_lower for word in ["faux", "démenti", "rumeur", "infondé", "désinformation"]):
        return "❌ FAUX"
    elif any(word in analysis_lower for word in ["vrai", "confirmé", "avéré", "exact"]):
        return "✅ VRAI"
    elif "nuancé" in analysis_lower:
        return "⚖️ NUANCÉ"
    else:
        return "❓ INDÉTERMINÉ"

# --- INTERFACE ---
st.set_page_config(page_title="Outil d'Analyse Critique", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")
    
    if st.button("Analyser"):
        if user_input:
            # Ici viendrait votre logique d'appel API réelle (Groq, etc.)
            # Pour l'exemple, nous simulons une réponse
            raw_analysis = "Cette rumeur sur Brigitte Macron est infondée et a été démentie par des sources comme Snopes et StreetPress."
            
            st.subheader("⚖️ Résultat")
            st.write(get_verdict(raw_analysis))
            
            st.subheader("📋 Analyse Factuelle")
            st.write(raw_analysis)
            
            st.subheader("⚠️ Mise en garde")
            st.info("Le partage d'une rumeur, même par curiosité, contribue à sa diffusion. Vérifiez toujours avant de cliquer.")
            
            st.subheader("🔗 Voir les sources")
            st.markdown("[Snopes - False rumor](https://www.snopes.com/news/2025/02/24/false-trans-rumor-brigitte-macron/)")
        else:
            st.warning("Veuillez saisir une affirmation.")

with tab2:
    st.write("### 🖼️ Vérifier une Image")
    st.write("Utilisez cet espace pour analyser le contexte d'une image.")
    # Ajoutez ici votre logique spécifique pour l'image

with tab3:
    st.write("""
    ### ℹ️ Méthode
    Cet outil croise vos recherches avec des sites experts et vérifiés :
    * **Fact-checkers :** AFP Factuel, Les Décodeurs, Snopes.
    * **Institutions :** CNRS, NASA, Service-public.fr.
    
    **Règle d'or :** Si l'outil affiche 'INDÉTERMINÉ', ne partagez pas l'information avant de l'avoir recouper vous-même avec un média fiable.
    """)

# --- PIED DE PAGE ---
st.markdown("---")
st.caption("Outil pédagogique pour l'Éducation aux Médias et à l'Information.")
