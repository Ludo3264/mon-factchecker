import streamlit as st

# --- CONFIGURATION DES SOURCES ---
TRUSTED_SITES = [
    "factuel.afp.com", "lemonde.fr/les-decodeurs", "liberation.fr/checknews",
    "francetvinfo.fr/vrai-ou-fake", "snopes.com", "cnrs.fr", 
    "inserm.fr", "nasa.gov", "service-public.fr", "vie-publique.fr"
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

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

# Rétablissement des onglets originaux
tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")
    
    if st.button("Analyser"):
        if user_input:
            # Instruction système conforme à la méthode
            system_instruction = f"""
            Agis comme un vérificateur de faits rigoureux. 
            Utilise uniquement les sources suivantes : {', '.join(TRUSTED_SITES)}.
            Si l'information n'est pas présente ou confirmée, réponds impérativement 'INDÉTERMINÉ'.
            Ne jamais inventer.
            """
            
            # Ici, intégrez votre appel API réel (ex: client.chat.completions.create)
            # raw_analysis = ... 
            raw_analysis = "Analyse simulée : aucune preuve trouvée dans les sources certifiées."
            
            st.subheader("⚖️ Résultat")
            st.write(get_verdict(raw_analysis))
            
            st.subheader("📋 Analyse Factuelle")
            st.write(raw_analysis)
            
            if "INDÉTERMINÉ" in get_verdict(raw_analysis):
                st.warning("⚠️ Aucune source fiable trouvée. Conformément à la méthode, ne partagez pas cette information.")

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez cet espace pour analyser le contexte d'une image.")
    # Votre logique spécifique pour les images ici

with tab3:
    st.subheader("ℹ️ Méthode")
    st.write("""
    ### La règle du doute méthodique
    Pour garantir l'intégrité de vos recherches, cet outil suit une règle stricte :
    * **Sources Certifiées uniquement :** Nous ne consultons que des organismes experts (Fact-checkers, Institutions, Science).
    * **Absence d'invention :** Si une information n'est pas présente dans nos sources, l'outil affiche **INDÉTERMINÉ**.
    * **Verdict final :** Si le résultat est **INDÉTERMINÉ**, cela signifie que l'information n'a pas été validée par la communauté scientifique ou journalistique reconnue. **Dans ce cas, ne partagez jamais l'information.**
    """)

st.markdown("---")
st.caption("Outil pédagogique pour l'Éducation aux Médias et à l'Information.")
