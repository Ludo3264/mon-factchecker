import streamlit as st
from groq import Groq
from datetime import datetime

# --- CONFIGURATION ÉTENDUE (Inspirée des rubriques de presse) ---
SOURCES = {
    "Fact-checking": {"AFP Factuel": "https://factuel.afp.com/?query=", "Le Monde Décodeurs": "https://www.lemonde.fr/les-decodeurs/recherche/?search_keywords="},
    "Sport": {"Le Monde Sport": "https://www.lemonde.fr/sport/recherche/?search_keywords=", "L'Équipe": "https://www.lequipe.fr/recherche/?q="},
    "Planète (Climat/Météo)": {"Le Monde Planète": "https://www.lemonde.fr/planete/recherche/?search_keywords=", "Météo-France": "https://meteofrance.com/recherche?q=", "Keraunos": "https://www.keraunos.org/recherche.html?searchword="},
    "Politique": {"Le Monde Politique": "https://www.lemonde.fr/politique/recherche/?search_keywords=", "Vie Publique": "https://www.vie-publique.fr/recherche?q="},
    "Sciences & Santé": {"Le Monde Sciences": "https://www.lemonde.fr/sciences/recherche/?search_keywords=", "INSERM": "https://www.inserm.fr/recherche/?q=", "OMS": "https://www.who.int/fr/search?q="},
    "Économie": {"Le Monde Éco": "https://www.lemonde.fr/economie/recherche/?search_keywords=", "INSEE": "https://www.insee.fr/fr/recherche?q="},
    "Société": {"Le Monde Société": "https://www.lemonde.fr/societe/recherche/?search_keywords=", "Défenseur Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key="},
    "International": {"Le Monde International": "https://www.lemonde.fr/international/recherche/?search_keywords=", "ONU Info": "https://news.un.org/fr/search/"}
}

# --- LOGIQUE IA ---
def get_expert_analysis(query):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime('%d %B %Y')
    
    system_prompt = f"""
    Nous sommes le {current_date}. Tu es un expert EMI agissant comme un journaliste des 'Décodeurs'.
    RÈGLE : Utilise une approche rigoureuse. Si le sujet concerne le sport, la santé, le climat ou la politique, cherche des preuves factuelles.
    Si tu confirmes une info, cite l'article source. Si c'est une rumeur, démontre pourquoi en citant des preuves.
    
    Structure OBLIGATOIRE :
    [VERDICT] : VRAI, FAUX ou INCERTAIN
    1. Faits observés : (Synthèse des données factuelles).
    2. Biais détectés : (Analyse critique).
    3. Méthodologie : (Comment croiser l'information).
    4. Sources : (Liste d'URL cliquables vers les rubriques spécialisées).
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant"
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil EMI Expert", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique")
    user_input = st.text_input("Saisissez l'affirmation à vérifier :")

    if st.button("Lancer l'analyse"):
        if user_input:
            st.session_state.user_input = user_input
            # Détection automatique de la catégorie
            cat = next((c for c in SOURCES if c.lower() in user_input.lower()), "Fact-checking")
            st.session_state.cat = cat
            st.session_state.analysis = get_expert_analysis(user_input)
            st.session_state.step = 1

    if st.session_state.get('step') == 1:
        st.markdown(f"### 🔍 Sources suggérées ({st.session_state.cat})")
        cols = st.columns(len(SOURCES[st.session_state.cat]))
        for i, (name, base_url) in enumerate(SOURCES[st.session_state.cat].items()):
            cols[i].link_button(name, f"{base_url}{st.session_state.user_input.replace(' ', '+')}")
        
        st.markdown("---")
        st.subheader("📝 Bilan de votre recherche")
        user_bilan = st.text_area("Rédigez votre conclusion :")
        
        if st.button("Comparer avec l'analyse experte"):
            analysis = st.session_state.analysis
            color = "#ff5252" if "[FAUX]" in analysis.upper() else "#4caf50" if "[VRAI]" in analysis.upper() else "#ff9800"
            c1, c2 = st.columns(2)
            c1.info(f"👤 **Votre Bilan :**\n\n{user_bilan}")
            c2.markdown(f"""<div style="background-color: {color}15; padding: 15px; border-radius: 10px; border-left: 5px solid {color};">
                <h3 style="color: {color};">🤖 Analyse de l'expert</h3>{analysis.replace('[VRAI]', '').replace('[FAUX]', '').replace('[INCERTAIN]', '')}</div>""", unsafe_allow_html=True)

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Google Lens", "https://lens.google.com/")
    c2.link_button("TinEye", "https://tineye.com/")
    c3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch/")

with tab3:
    st.subheader("ℹ️ Méthode : Le Doute Méthodique")
    st.write("L'information est un écosystème complexe. Pour ne pas se laisser tromper :")
    st.write("1. **Croisez** : Utilisez les rubriques spécialisées (Sport, Santé, Planète) pour vérifier les faits.")
    st.write("2. **Identifiez** : Qui publie ? Une information sportive vérifiée est une information sourcée (ex: L'Équipe, Le Monde).")
    st.write("3. **Analysez** : Apprenez à distinguer le fait (ce qui s'est passé) de l'opinion (ce que j'en pense).")
