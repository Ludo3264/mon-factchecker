import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_expert_analysis(query):
    system_prompt = """
    Tu es un expert en fact-checking EMI. 
    1. Analyse l'affirmation avec rigueur. 
    2. Cite des sources institutionnelles ou médias de référence.
    3. Structure ta réponse en : 1. Faits observés, 2. Biais détectés, 3. Méthodologie de vérification.
    4. Sois détaillé. Si l'info est en temps réel, explique la méthode de vérification.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content

# --- INTERFACE ---
st.set_page_config(page_title="Outil d'Analyse Critique EMI", layout="wide")
st.title("🛡️ Outil d'Analyse Critique — EMI")

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

with tab1:
    st.subheader("✍️ Analyseur Critique — Niveau Expert")
    
    if 'analysis' not in st.session_state: st.session_state.analysis = None
    
    user_input = st.text_input("Affirmation à disséquer :")
    
    if st.button("Lancer l'analyse experte"):
        if user_input:
            with st.spinner("Analyse approfondie..."):
                st.session_state.analysis = get_expert_analysis(user_input)
    
    if st.session_state.analysis:
        st.markdown("### 🤖 Analyse de l'IA")
        st.markdown(st.session_state.analysis)
        
        st.markdown("---")
        st.subheader("📝 Bilan de ma recherche")
        user_bilan = st.text_area("Rédigez votre conclusion après avoir consulté les sources :")
        
        note = st.slider("Quelle note attribuez-vous à la pertinence de votre recherche (1 à 5) ?", 1, 5, 3)
        
        if st.button("Comparer mon bilan avec l'analyse experte"):
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("👤 Mon Bilan")
                st.info(user_bilan)
                st.write(f"Auto-évaluation : {note}/5")
            with col2:
                st.subheader("🤖 Verdict de l'IA")
                st.write(st.session_state.analysis)
            st.success("Analyse terminée : comparez vos points de divergence avec l'IA.")

with tab2:
    st.subheader("🖼️ Vérifier une Image")
    st.write("Utilisez ces outils pour effectuer une recherche inversée :")
    col1, col2, col3 = st.columns(3)
    col1.link_button("Google Lens", "https://lens.google.com/")
    col2.link_button("TinEye", "https://tineye.com/")
    col3.link_button("Bing Visual Search", "https://www.bing.com/visualsearch")
    
    st.markdown("---")
    img_input = st.text_input("Collez l'URL de l'image ici :")
    if st.button("Analyser l'Image"):
        st.info("Recherche de similarité dans les bases de données en cours...")

with tab3:
    st.subheader("ℹ️ Méthode : La règle du doute méthodique")
    st.write("""
    Face à une information douteuse, adoptez les réflexes des journalistes :
    
    1. **Croisement des sources :** Ne vous contentez jamais d'une seule source. 
    2. **Analyse de la preuve :** Une information sans source primaire est suspecte.
    3. **Le doute méthodique :** Si aucune source fiable ne confirme, considérez l'info comme INDÉTERMINÉE.
    4. **Responsabilité :** Si le résultat est FAUX, ne partagez pas.
    """)
