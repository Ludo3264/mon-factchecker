import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
TRUSTED_SITES = ["AFP Factuel", "Le Monde", "Libération", "France Info"]
SEARCH_URLS = {
    "AFP Factuel": "https://factuel.afp.com/search?query=",
    "Le Monde": "https://www.lemonde.fr/recherche/?search_keywords=",
    "Libération": "https://www.liberation.fr/recherche/?q=",
    "France Info": "https://www.francetvinfo.fr/recherche/?search="
}

def get_ai_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    system_prompt = f"""
    Tu es un expert en fact-checking pour l'EMI.
    Règles :
    1. Si tu peux confirmer ou infirmer avec certitude via tes sources, donne le verdict (VRAI/FAUX) avec la source précise.
    2. Si tu n'as pas de preuve formelle dans tes données, réponds impérativement par 'INDÉTERMINÉ'.
    3. Ne cherche pas à interpréter : soit tu as la source, soit tu n'as rien.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.title("🛡️ Outil d'Analyse Critique — EMI")
user_input = st.text_input("Saisissez l'affirmation à vérifier :")

if st.button("Analyser"):
    with st.spinner("Analyse en cours..."):
        analysis = get_ai_analysis(user_input)
        
        # Affichage du Verdict
        if "FAUX" in analysis.upper():
            st.error("❌ Verdict : FAUX")
        elif "VRAI" in analysis.upper():
            st.success("✅ Verdict : VRAI")
        else:
            st.warning("❓ INDÉTERMINÉ")
            
        st.markdown(f"### Analyse de l'IA :\n{analysis}")
        
        # Section Recherche pour l'élève
        st.markdown("---")
        st.subheader("🔍 Poursuivez votre enquête (Recherche manuelle) :")
        st.write("L'IA n'a pas pu confirmer ? Vérifiez directement sur les moteurs de recherche des médias :")
        cols = st.columns(len(SEARCH_URLS))
        for i, (name, base_url) in enumerate(SEARCH_URLS.items()):
            cols[i].link_button(name, f"{base_url}{user_input.replace(' ', '+')}")

        # Section Bilan
        st.markdown("---")
        st.subheader("📝 Bilan de ma recherche")
        st.text_area("Après avoir consulté les liens, que pouvez-vous conclure ?")
