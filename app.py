# ==============================================================================
# ONGLET 3 : LA STATION DE FACT-CHECKING VIDÉO (Corrigé avec outil technique)
# ==============================================================================
with tab3:
    st.markdown('<p style="font-size:1.3rem; font-weight:bold; color: #1E3A8A; margin-top:10px;">Enquêter sur une vidéo suspecte</p>', unsafe_allow_html=True)
    st.write("**Objectif pédagogique :** Analyser les vidéos détournées ou manipulées.")
    
    col_vid1, col_vid2 = st.columns(2)
    with col_vid1:
        st.link_button("📥 Extension InVID (Debunker)", "https://chromewebstore.google.com/detail/fake-news-debunker-invid/mhccpoafgdgbhnjfhkcmgknndkeenfhe?hl=fr", type="primary", use_container_width=True)
    with col_vid2:
        # Lien vers la Sandbox officielle de vérification (outil technique propre)
        st.link_button("🛠️ Vidéo Verification Sandbox", "https://reveal-mklab.iti.gr/reveal/", use_container_width=True)
    
    st.markdown("""
    ---
    ### 💡 Guide d'animation pour vos élèves :
    1. **InVID :** Utilisez l'extension pour extraire les images clés d'une vidéo.
    2. **Analyse Technique :** La *Vidéo Verification Sandbox* permet d'analyser les méta-données et de tester la cohérence visuelle des vidéos.
    3. **Vérification Inversée :** Uploadez les images extraites dans l'**Onglet 2** de notre application pour voir si elles ont été détournées d'un reportage antérieur.
    """)
