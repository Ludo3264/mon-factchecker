import streamlit as st

# --- CONFIGURATION DES SOURCES ---
# Liste des sources de confiance pour restreindre la recherche
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr/les-decodeurs", "liberation.fr/checknews",
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "inserm.fr", "nasa.gov", "service-public.fr", "vie-publique.fr"
]

# --- LOGIQUE DE VERDICT CONFORME ---
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

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

# --- ONGLETS ---
tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")
    
    if st.button("Analyser"):
        if user_input:
            # PROMPT STRICT : Applique la conformité à la méthode
            system_instruction = f"""
            Tu es un analyste rigoureux pour l'Éducation aux Médias.
            1. Utilise uniquement les preuves issues de ces domaines : {', '.join(TRUSTED_SITES)}.
            2. Si l'information n'est pas confirmée par ces sources, tu DOIS répondre 'INDÉTERMINÉ'.
            3. Ne jamais inventer, ne jamais supposer. Sois honnête sur l'absence de preuves.
            4. Analyse avec une approche scientifique et neutre.
            """
            
            # Ici, l'appel API doit intégrer system_instruction pour garantir l'absence d'invention.
            # Simulation de l'analyse (remplacer par votre appel fonctionnel)
            raw_analysis = "Analyse basée sur les sources certifiées..." 
            
            st.subheader("⚖️ Résultat")
            st.write(get_verdict(raw_analysis))
            
            st.subheader("📋 Analyse Factuelle")
            st.write(raw_analysis)
            
            # Application stricte de la mise en garde de l'onglet 3
            if "INDÉTERMINÉ" in get_verdict(raw_analysis):
                st.warning("⚠️ Aucune source fiable trouvée. Conformément à la méthode, ne partagez pas cette information.")
        else:
            st.warning("Veuillez saisir une affirmation.")

with tab2:
    st.write("### 🖼️ Vérifier une Image")
    st.write("Utilisez cet espace pour analyser le contexte d'une image.")

with tab3:
    st.write("""
    ### ℹ️ Méthode : La règle du doute méthodique
    Pour garantir l'intégrité de vos recherches, cet outil suit une règle stricte :
    * **Sources Certifiées uniquement :** Nous ne consultons que des organismes experts (Fact-checkers, Institutions, Science).
    * **Absence d'invention :** Si une information n'est pas présente dans nos sources, l'outil affiche **INDÉTERMINÉ**.
    * **Verdict final :** Si le résultat est **INDÉTERMINÉ**, cela signifie que l'information n'a pas été validée par la communauté scientifique ou journalistique reconnue. **Dans ce cas, ne partagez jamais l'information.**
    """)

# --- PIED DE PAGE ---
st.markdown("---")
st.caption("Outil pédagogique pour l'Éducation aux Médias et à l'Information.")
