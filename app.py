import re
import streamlit as st
from groq import Groq
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURATION DES SOURCES
# ---------------------------------------------------------------------------
SOURCES = {
    "Fact-checking": {
        "AFP Factuel": "https://factuel.afp.com/?query=",
        "Le Monde Décodeurs": "https://www.lemonde.fr/les-decodeurs/recherche/?search_keywords=",
    },
    "Médias, Réseaux Sociaux & Culture": {
        "Arcom (Régulation)": "https://www.arcom.fr/recherche?q=",
        "Le Monde Culture": "https://www.lemonde.fr/culture/recherche/?search_keywords=",
    },
    "Sport": {
        "Le Monde Sport": "https://www.lemonde.fr/sport/recherche/?search_keywords=",
        "L'Équipe": "https://www.lequipe.fr/recherche/?q=",
    },
    "Environnement & Planète": {
        "Le Monde Planète": "https://www.lemonde.fr/planete/recherche/?search_keywords=",
        "Météo-France": "https://meteofrance.com/recherche?q=",
    },
    "Société, Laïcité & Genre": {
        "Vie Publique (Laïcité)": "https://www.vie-publique.fr/recherche?q=laïcité",
        "HCE (Genre/Égalité)": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=",
        "Défenseur des Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key=",
    },
    "Santé": {
        "Le Monde Sciences": "https://www.lemonde.fr/sciences/recherche/?search_keywords=",
        "INSERM": "https://www.inserm.fr/recherche/?q=",
        "OMS": "https://www.who.int/fr/search?q=",
    },
    "Éducation & École": {
        "Le Monde Éducation": "https://www.lemonde.fr/education/recherche/?search_keywords=",
        "Ministère Éd.": "https://www.education.gouv.fr/recherche?q=",
    },
    "Politique & Institutions": {
        "Le Monde Politique": "https://www.lemonde.fr/politique/recherche/?search_keywords=",
        "Vie Publique": "https://www.vie-publique.fr/recherche?q=",
    },
    "Économie & Emploi": {
        "Le Monde Éco": "https://www.lemonde.fr/economie/recherche/?search_keywords=",
        "INSEE": "https://www.insee.fr/fr/recherche?q=",
    },
    "International": {
        "Le Monde International": "https://www.lemonde.fr/international/recherche/?search_keywords=",
        "ONU Info": "https://news.un.org/fr/search/",
    },
}

# ---------------------------------------------------------------------------
# LOGIQUE IA — prompt recentré sur la méthode, sans génération d'URL
# ---------------------------------------------------------------------------
def get_expert_analysis(query: str) -> str:
    """
    Interroge le modèle et retourne l'analyse structurée.
    Lève une exception en cas d'erreur API (géré dans l'interface).
    """
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime("%d %B %Y")

    system_prompt = f"""
Nous sommes le {current_date}. Tu es un expert en Éducation aux Médias et à l'Information (EMI).
Tu adoptes la rigueur méthodologique des journalistes des 'Décodeurs' du Monde.

CONTRAINTES ABSOLUES :
1. INTERDICTION TOTALE de générer des URLs, liens hypertexte, ou noms de domaine
   (même sous forme de texte brut comme 'elysee.fr', 'wikipedia.org', etc.).
   Si tu identifies une source pertinente, cite uniquement son NOM en clair
   (ex : "le site officiel de l'Élysée", "l'encyclopédie Wikipédia", "le journal Le Monde").
   Les liens sont entièrement gérés par l'interface — ne jamais en générer.
2. Si tu n'es pas certain d'un fait, dis-le explicitement plutôt que d'inventer.
3. Si la question porte sur un événement des 48 dernières heures, signale-le clairement :
   tu n'as pas accès aux flux d'actualité en temps réel.
4. Ton rôle est MÉTHODOLOGIQUE : aider à raisonner, pas à remplacer la vérification humaine.

STRUCTURE OBLIGATOIRE (respecte ces 4 rubriques, dans cet ordre) :

[VERDICT] : VRAI / FAUX / INCERTAIN  
(Choisis l'une des trois options. Si tu manques d'information fiable, choisis INCERTAIN.)

1. Faits observés  
Synthèse sobre des éléments factuels connus sur la question. Ne dépasse pas 5 lignes.

2. Biais et signaux d'alerte  
Identifie les rhétoriques, omissions ou cadrages suspects dans la formulation de l'affirmation.

3. Méthodologie de vérification  
Explique concrètement comment un journaliste vérifierait cette affirmation (type de sources à consulter,
croisement de données, vérification d'images, etc.). Sois pédagogique : l'utilisateur apprend.

4. Limites de cette analyse  
Dis honnêtement ce que tu ne peux pas vérifier et pourquoi.
"""

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        model="llama-3.3-70b-versatile",  # Modèle plus capable pour le fact-checking
        temperature=0.2,                   # Réponses plus factuelles, moins créatives
        max_tokens=800,
    )
    return completion.choices[0].message.content


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def strip_urls(text: str) -> str:
    """
    Filet de sécurité post-traitement : supprime toutes les URLs et noms de domaine
    que le LLM aurait générés malgré l'instruction dans le prompt.
    """
    # Supprimer les lignes de liste contenant une URL (ex: "* https://..." ou "- http://...")
    text = re.sub(r'^\s*[-*•]\s*https?://\S+.*$', '', text, flags=re.MULTILINE)
    # Supprimer les URLs inline restantes
    text = re.sub(
        r'https?://\S+',
        '*(lien supprimé — utilisez les boutons de sources ci-dessus)*',
        text,
    )
    # Supprimer les noms de domaine nus (ex: "elysee.fr", "wikipedia.org")
    text = re.sub(
        r'\b[\w\-]+\.(fr|com|org|net|gouv|eu|info|io)\b',
        '*(domaine supprimé)*',
        text,
    )
    # Nettoyer les lignes vides consécutives laissées par les suppressions
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def reset_session():
    """Réinitialise proprement l'état de session entre deux analyses."""
    for key in ["user_input", "cat", "analysis", "step"]:
        st.session_state.pop(key, None)


def verdict_color(analysis: str) -> str:
    text = analysis.upper()
    if "[FAUX]" in text:
        return "#e53935"
    if "[VRAI]" in text:
        return "#43a047"
    return "#fb8c00"  # INCERTAIN


# ---------------------------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Outil EMI Expert", layout="wide", page_icon="🛡️")

st.title("🛡️ Outil d'Analyse Critique — EMI")
st.caption(
    "Vérifiez une affirmation, consultez les sources, puis comparez votre raisonnement "
    "avec celui de l'IA. L'outil ne remplace pas votre jugement — il l'entraîne."
)

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])


# ─── ONGLET 1 : VÉRIFIER UN TEXTE ──────────────────────────────────────────
with tab1:
    st.subheader("✍️ Analyseur Critique")

    cat_selection = st.selectbox("Domaine :", list(SOURCES.keys()))

    # text_area plutôt que text_input → accepte les paragraphes collés
    user_input = st.text_area(
        "Saisissez ou collez l'affirmation à vérifier :",
        height=100,
        placeholder="Ex : « Les vaccins contiennent des puces électroniques »",
    )

    if st.button("🔍 Lancer l'analyse", type="primary"):
        if not user_input.strip():
            st.warning("Merci de saisir une affirmation avant de lancer l'analyse.")
        else:
            reset_session()
            with st.spinner("Analyse en cours…"):
                try:
                    analysis_raw = get_expert_analysis(user_input)
                    analysis = strip_urls(analysis_raw)  # filet de sécurité anti-URLs
                    st.session_state.update(
                        {
                            "user_input": user_input,
                            "cat": cat_selection,
                            "analysis": analysis,
                            "step": 1,
                        }
                    )
                except Exception as e:
                    st.error(
                        f"❌ Impossible de contacter le service d'analyse : {e}\n\n"
                        "Vérifiez votre clé API ou réessayez dans quelques instants. "
                        "Vous pouvez toujours consulter les sources ci-dessous manuellement."
                    )

    # ── ÉTAPE 1 : affichage des sources et bilan ──
    if st.session_state.get("step") == 1:
        st.info(
            "💡 **Astuce Vie Privée** : Faites un **clic-droit** sur les boutons "
            "ci-dessous → *Ouvrir dans une fenêtre de navigation privée*."
        )

        # Sources spécialisées
        st.markdown(f"### 🔗 Sources spécialisées — *{st.session_state.cat}*")
        st.caption(
            "ℹ️ Ces sources servent à comprendre le **cadre légal et institutionnel** "
            "du domaine (lois, rapports officiels, régulation). "
            "Elles peuvent ne pas renvoyer de résultat direct sur une rumeur précise — "
            "c'est normal. Pour fact-checker une affirmation spécifique, "
            "utilisez plutôt **DuckDuckGo** ou **Qwant** avec des mots-clés ciblés."
        )
        sources_cat = SOURCES[st.session_state.cat]
        cols = st.columns(len(sources_cat))
        for i, (name, base_url) in enumerate(sources_cat.items()):
            encoded_query = st.session_state.user_input.replace(" ", "+")
            cols[i].link_button(name, f"{base_url}{encoded_query}")

        # Recherche libre
        st.markdown("---")
        st.markdown("#### 🌐 Recherche libre (moteurs respectueux de la vie privée)")
        encoded_query = st.session_state.user_input.replace(" ", "+")
        c1, c2 = st.columns(2)
        c1.link_button("DuckDuckGo", f"https://duckduckgo.com/?q={encoded_query}")
        c2.link_button("Qwant", f"https://www.qwant.com/?q={encoded_query}")

        # Bilan de l'apprenant
        st.markdown("---")
        st.subheader("📝 Votre bilan (avant de voir l'analyse IA)")
        st.caption(
            "Consultez d'abord les sources ci-dessus, puis rédigez votre conclusion. "
            "L'objectif est d'exercer votre jugement *avant* de voir celui de l'IA."
        )
        user_bilan = st.text_area(
            "Votre conclusion :",
            height=120,
            placeholder="Après consultation des sources, je pense que… parce que…",
        )

        if st.button("⚖️ Comparer avec l'analyse experte"):
            if not user_bilan.strip():
                st.warning(
                    "Rédigez d'abord votre bilan — c'est l'étape la plus importante !"
                )
            else:
                analysis = st.session_state.analysis
                color = verdict_color(analysis)

                # Extraction du verdict pour l'afficher séparément
                verdict_line = ""
                clean_analysis = analysis
                for verdict in ["[VRAI]", "[FAUX]", "[INCERTAIN]"]:
                    if verdict in analysis.upper():
                        verdict_line = verdict.replace("[", "").replace("]", "")
                        clean_analysis = analysis.replace(verdict, "").replace(
                            verdict.lower(), ""
                        )
                        break

                # Bandeau verdict
                st.markdown(
                    f"""
                    <div style="
                        background:{color}20;
                        border-left:6px solid {color};
                        padding:12px 18px;
                        border-radius:8px;
                        margin-bottom:16px;
                        font-size:1.2rem;
                        font-weight:700;
                        color:{color};
                    ">
                        Verdict IA : {verdict_line or "NON DETERMINÉ"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c1, c2 = st.columns(2)
                c1.markdown(
                    f"""
                    <div style="background:#e3f2fd;padding:16px;border-radius:10px;
                                border-left:5px solid #2196f3;height:100%;">
                        <h4 style="color:#1565c0;">👤 Votre bilan</h4>
                        <p style="white-space:pre-wrap;">{user_bilan}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f"""
                    <div style="background:{color}12;padding:16px;border-radius:10px;
                                border-left:5px solid {color};height:100%;">
                        <h4 style="color:{color};">🤖 Analyse méthodologique (IA)</h4>
                        <p style="white-space:pre-wrap;font-size:0.92rem;">{clean_analysis.strip()}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.warning(
                    "⚠️ Cette analyse IA est un **guide méthodologique**, pas une vérité absolue. "
                    "Croisez toujours avec les sources institutionnelles consultées ci-dessus."
                )


# ─── ONGLET 2 : VÉRIFIER UNE IMAGE ─────────────────────────────────────────
with tab2:
    st.subheader("🖼️ Vérifier une Image — Méthode TRACE")

    st.markdown(
        """
Avant de lancer une recherche inversée, posez-vous ces **5 questions** :

| Lettre | Question | Ce que vous cherchez |
|--------|----------|----------------------|
| **T** — Texte | Le texte qui accompagne l'image correspond-il à ce que l'on voit réellement ? | Discordances, exagérations |
| **R** — Référence | D'où vient cette image selon la personne qui la partage ? | Source primaire vérifiable |
| **A** — Auteur | Qui l'a prise ? Est-ce revendiqué et vérifiable ? | Profil, portfolio, crédits |
| **C** — Contexte | Quand et où a-t-elle été prise à l'origine ? | Date EXIF, géolocalisation |
| **E** — Émotion | Cherche-t-elle à provoquer une réaction forte ? | Peur, indignation, choc |
"""
    )

    st.markdown("---")
    st.markdown("#### 🔎 Outils de recherche inversée d'image")
    st.caption("Glissez-déposez l'image ou collez son URL dans chaque outil.")

    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("🔍 Google Lens", "https://lens.google.com/")
    c2.link_button("🔍 TinEye", "https://tineye.com/")
    c3.link_button("🔍 Bing Visual", "https://www.bing.com/visualsearch/")
    c4.link_button("🔍 InVID / WeVerify", "https://www.invid-project.eu/tools-and-services/invid-verification-plugin/")

    st.markdown("---")
    st.markdown("#### 📅 Vérifier la date d'une image")
    c1, c2 = st.columns(2)
    c1.link_button("Jeffrey's Exif Viewer", "https://exifdata.com/")
    c2.link_button("FotoForensics (métadonnées)", "https://fotoforensics.com/")

    st.info(
        "💡 **Rappel** : une image peut être authentique mais utilisée hors contexte. "
        "La recherche inversée confirme l'image, pas le récit qui l'accompagne."
    )


# ─── ONGLET 3 : MÉTHODE ─────────────────────────────────────────────────────
with tab3:
    st.subheader("ℹ️ Méthode : Le Doute Méthodique")

    st.markdown(
        """
### Pourquoi cet outil ?

Cet outil est conçu pour des **ateliers EMI** : il ne remplace pas votre jugement,
il l'entraîne. La séquence est volontairement construite pour que vous consultiez
les sources *avant* de voir l'analyse IA.

---

### Les 4 principes de l'atelier

**1. Formulez d'abord votre propre hypothèse**  
Avant de cliquer sur quoi que ce soit, qu'est-ce qui vous rend méfiant(e) ?
Notez-le mentalement.

**2. Consultez les sources institutionnelles**  
Les boutons de sources renvoient vers des médias de référence et des institutions
(INSEE, OMS, INSERM…). Privilégiez-les sur les résultats de moteur de recherche.

**3. Rédigez votre bilan avant de voir l'IA**  
C'est l'étape la plus importante. L'IA n'est qu'un miroir — elle vous aide à
structurer votre raisonnement, pas à penser à votre place.

**4. Comparez et discutez**  
Là où votre bilan et l'analyse IA divergent : c'est exactement là que se trouve
l'apprentissage.

---

### Limites de l'IA dans cet outil

- Le modèle a une **date de coupure** : il ne connaît pas les événements récents.
- Il peut se tromper sur des faits précis — la rigueur vient des **sources humaines**.
- Les verdicts VRAI/FAUX/INCERTAIN sont des **orientations méthodologiques**,
  pas des jugements définitifs.

---

### Confidentialité

- Utilisez le **clic-droit → navigation privée** pour vos recherches.
- Préférez **DuckDuckGo** ou **Qwant** à Google pour limiter le profilage.
- Les affirmations saisies ici ne sont pas stockées par cet outil.
"""
    )
