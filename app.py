"""
Outil EMI Expert — Version 4.2
Mise à jour modèle : llama-3.1-8b-instant → openai/gpt-oss-20b
"""

import re
import json
import io
from datetime import datetime

import streamlit as st
from groq import Groq

# ── Tavily (optionnel : si la clé est absente, on dégrade gracieusement) ──
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# ===========================================================================
# CONFIGURATION DES SOURCES
# ===========================================================================
SOURCES = {
    "Fact-checking": {
        "AFP Factuel": "https://factuel.afp.com/?query=",
        "Le Monde Décodeurs": "https://www.lemonde.fr/les-decodeurs/recherche/?search_keywords=",
        "CheckNews (Libé)": "https://www.liberation.fr/checknews/recherche/?q=",
        "Les Surligneurs": "https://www.lessurligneurs.eu/?s=",
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
        "Our World in Data": "https://ourworldindata.org/search?q=",
    },
    "Société, Laïcité & Genre": {
        "Vie Publique": "https://www.vie-publique.fr/recherche?q=",
        "HCE (Genre/Égalité)": "https://www.haut-conseil-egalite.gouv.fr/spip.php?page=recherche&recherche=",
        "Défenseur des Droits": "https://www.defenseurdesdroits.fr/fr/recherche?key=",
    },
    "Santé": {
        "Le Monde Sciences": "https://www.lemonde.fr/sciences/recherche/?search_keywords=",
        "INSERM": "https://www.inserm.fr/recherche/?q=",
        "OMS": "https://www.who.int/fr/search?q=",
        "Vidal (médicaments)": "https://www.vidal.fr/recherche/?q=",
    },
    "Éducation & École": {
        "Le Monde Éducation": "https://www.lemonde.fr/education/recherche/?search_keywords=",
        "Ministère Éd.": "https://www.education.gouv.fr/recherche?q=",
    },
    "Politique & Institutions": {
        "Le Monde Politique": "https://www.lemonde.fr/politique/recherche/?search_keywords=",
        "Vie Publique": "https://www.vie-publique.fr/recherche?q=",
        "Sénat": "https://www.senat.fr/recherche/index.html?query=",
    },
    "Économie & Emploi": {
        "Le Monde Éco": "https://www.lemonde.fr/economie/recherche/?search_keywords=",
        "INSEE": "https://www.insee.fr/fr/recherche?q=",
        "Banque de France": "https://www.banque-france.fr/fr/recherche?q=",
    },
    "International": {
        "Le Monde International": "https://www.lemonde.fr/international/recherche/?search_keywords=",
        "ONU Info": "https://news.un.org/fr/search/",
        "BBC Afrique": "https://www.bbc.com/afrique/search?q=",
    },
}

# Mots-clés courts → modèle léger ; questions complexes → modèle lourd
MODEL_SIMPLE = "openai/gpt-oss-20b"
MODEL_FULL   = "llama-3.3-70b-versatile"
COMPLEXITY_THRESHOLD = 12  # nombre de mots au-delà duquel on passe au 70b


# ===========================================================================
# HELPERS
# ===========================================================================

def choose_model(query: str) -> str:
    """Sélectionne le modèle selon la complexité estimée de la requête."""
    word_count = len(query.split())
    return MODEL_FULL if word_count >= COMPLEXITY_THRESHOLD else MODEL_SIMPLE


def strip_urls(text: str) -> str:
    """Supprime toutes les URLs / domaines nus générés malgré le prompt."""
    text = re.sub(r'^\s*[-*•]\s*https?://\S+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'https?://\S+', '*(lien supprimé — voir boutons)*', text)
    text = re.sub(
        r'\b[\w\-]+\.(fr|com|org|net|gouv|eu|info|io)\b',
        '*(domaine supprimé)*',
        text,
    )
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_verdict(analysis: str) -> str:
    """Extrait VRAI / FAUX / INCERTAIN quelle que soit la mise en forme du LLM."""
    t = re.sub(r'\*+', '', analysis.upper())
    t = re.sub(r'\[VERDICT\]', 'VERDICT', t)
    match = re.search(r'VERDICT\s*[:\-]\s*(VRAI|FAUX|INCERTAIN)', t)
    if match:
        return match.group(1)
    for label in ["FAUX", "VRAI", "INCERTAIN"]:
        if f"[{label}]" in t:
            return label
    return ""


def verdict_color(verdict: str) -> str:
    return {"VRAI": "#43a047", "FAUX": "#e53935"}.get(verdict, "#fb8c00")


def reset_session():
    for key in ["user_input", "cat", "analysis", "step", "web_context", "model_used"]:
        st.session_state.pop(key, None)


def detect_lang(text: str) -> str:
    """Détection heuristique très légère FR / EN / autre."""
    fr_markers = ['est', 'les', 'des', 'que', 'une', 'pour', 'dans', 'pas', 'sur', 'avec']
    words = text.lower().split()
    fr_score = sum(1 for w in words if w in fr_markers)
    return "fr" if fr_score >= 2 else "en" if len(words) > 0 else "fr"


# ===========================================================================
# TAVILY — RECHERCHE WEB TEMPS RÉEL
# ===========================================================================

def fetch_web_context(query: str) -> tuple[str, list[dict]]:
    """
    Interroge Tavily pour obtenir des faits récents.
    Retourne (résumé_texte, liste_sources).
    """
    if not TAVILY_AVAILABLE:
        return "", []
    tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    if not tavily_key:
        return "", []
    try:
        client = TavilyClient(api_key=tavily_key)
        resp = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
        answer = resp.get("answer", "") or ""
        sources = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "score": r.get("score", 0)}
            for r in resp.get("results", [])
            if r.get("url")
        ]
        return answer, sources
    except Exception as e:
        return f"[Tavily indisponible : {e}]", []


# ===========================================================================
# ANALYSE IA
# ===========================================================================

def get_expert_analysis(query: str, web_context: str = "", lang: str = "fr") -> tuple[str, str]:
    """
    Interroge Groq et retourne (analyse_brute, modèle_utilisé).
    """
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime("%d %B %Y")
    model = choose_model(query)

    lang_instruction = (
        "Réponds en français." if lang == "fr"
        else "Answer in English."
    )

    web_block = ""
    if web_context:
        web_block = f"""
CONTEXTE WEB RÉCUPÉRÉ EN TEMPS RÉEL (source : Tavily) :
---
{web_context}
---
Utilise ces informations factuelles pour enrichir ton analyse.
Ne mentionne pas Tavily dans ta réponse — présente les faits directement.
"""

    system_prompt = f"""
Nous sommes le {current_date}. Tu es un expert en Éducation aux Médias et à l'Information (EMI).
Tu adoptes la rigueur méthodologique des journalistes des 'Décodeurs' du Monde.
{lang_instruction}

{web_block}

CONTRAINTES ABSOLUES :
1. INTERDICTION TOTALE de générer des URLs, liens, ou noms de domaine
   (même sous forme de texte brut). Cite les sources par leur NOM uniquement.
   Les liens sont gérés par l'interface.
2. Si tu n'es pas certain d'un fait, dis-le explicitement.
3. Pour un événement des 48 dernières heures sans contexte web fourni,
   signale que tu n'as pas accès aux flux en temps réel.
4. Ton rôle est MÉTHODOLOGIQUE : structurer le raisonnement, pas remplacer la vérification.

STRUCTURE OBLIGATOIRE (exactement ces 4 blocs, dans cet ordre) :

[VERDICT] : VRAI / FAUX / INCERTAIN

1. Faits observés
(Max 5 lignes. Faits établis uniquement, sans opinion.)

2. Biais et signaux d'alerte
(Rhétoriques, omissions, cadrages suspects dans la formulation.)

3. Méthodologie de vérification
(Comment un journaliste vérifierait concrètement. Pédagogique.)

4. Limites de cette analyse
(Ce que tu ne peux pas vérifier et pourquoi. Sois honnête.)
"""

    completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        model=model,
        temperature=0.15,
        max_tokens=900,
    )
    return completion.choices[0].message.content, model


# ===========================================================================
# HISTORIQUE DE SESSION
# ===========================================================================

def add_to_history(query: str, cat: str, verdict: str, analysis: str, model: str):
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({
        "ts": datetime.now().strftime("%H:%M"),
        "query": query,
        "cat": cat,
        "verdict": verdict,
        "analysis": analysis,
        "model": model,
    })


def export_history_txt() -> str:
    """Génère un export texte de l'historique."""
    lines = [f"=== ATELIER EMI — Export {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n"]
    for i, h in enumerate(st.session_state.get("history", []), 1):
        lines.append(f"\n── Analyse #{i} ({h['ts']}) ──")
        lines.append(f"Domaine : {h['cat']}")
        lines.append(f"Affirmation : {h['query']}")
        lines.append(f"Verdict : {h['verdict'] or 'NON DÉTERMINÉ'}")
        lines.append(f"Modèle : {h['model']}")
        lines.append(f"\n{h['analysis']}\n")
    return "\n".join(lines)


# ===========================================================================
# INTERFACE
# ===========================================================================
st.set_page_config(page_title="Outil EMI Expert", layout="wide", page_icon="🛡️")

# ── Barre latérale ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")

    # Mode animateur
    mode_animateur = st.toggle("🎓 Mode animateur", value=False,
        help="Affiche l'historique complet de toutes les analyses en bas de page.")

    # Tavily status
    tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    if TAVILY_AVAILABLE and tavily_key:
        st.success("🌐 Recherche web : **activée** (Tavily)")
    else:
        st.warning("🌐 Recherche web : **désactivée**\nAjoutez `TAVILY_API_KEY` dans vos secrets Streamlit pour activer.")

    st.markdown("---")

    # Historique sidebar
    st.markdown("### 📋 Analyses de la session")
    history = st.session_state.get("history", [])
    if not history:
        st.caption("Aucune analyse pour l'instant.")
    else:
        for i, h in enumerate(history, 1):
            color = verdict_color(h["verdict"])
            st.markdown(
                f"**#{i}** `{h['ts']}` "
                f"<span style='color:{color};font-weight:700'>{h['verdict'] or '?'}</span> "
                f"— *{h['query'][:40]}{'…' if len(h['query'])>40 else ''}*",
                unsafe_allow_html=True,
            )
        st.markdown("---")
        export_txt = export_history_txt()
        st.download_button(
            "📥 Exporter la session (.txt)",
            data=export_txt.encode("utf-8"),
            file_name=f"atelier_emi_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.history = []
            st.rerun()

    st.markdown("---")
    st.caption("v4.2 · Groq + Tavily · EMI")


# ── Titre principal ──────────────────────────────────────────────────────────
st.title("🛡️ Outil d'Analyse Critique — EMI")
st.caption(
    "Vérifiez une affirmation, consultez les sources, rédigez votre bilan, "
    "puis comparez avec l'IA. L'outil entraîne votre jugement, il ne le remplace pas."
)

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])


# ── ONGLET 1 ─────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("✍️ Analyseur Critique")

    col_form, col_info = st.columns([3, 1])

    with col_form:
        cat_selection = st.selectbox("Domaine :", list(SOURCES.keys()))
        user_input = st.text_area(
            "Saisissez ou collez l'affirmation à vérifier :",
            height=100,
            placeholder="Ex : « Les vaccins contiennent des puces électroniques »",
        )

    with col_info:
        st.markdown("##### 🤖 Modèle sélectionné")
        if user_input.strip():
            m = choose_model(user_input)
            label = "70b — Analyse complète" if m == MODEL_FULL else "GPT OSS 20B — Analyse rapide"
            st.info(label)
        else:
            st.caption("Saisissez une affirmation pour voir le modèle.")
        st.markdown("##### 📊 Session")
        st.metric("Analyses effectuées", len(st.session_state.get("history", [])))

    launch = st.button("🔍 Lancer l'analyse", type="primary")

    if launch:
        if not user_input.strip():
            st.warning("Merci de saisir une affirmation avant de lancer l'analyse.")
        else:
            reset_session()
            lang = detect_lang(user_input)

            # Étape 1 : recherche web Tavily
            web_context = ""
            web_sources = []
            if TAVILY_AVAILABLE and tavily_key:
                with st.spinner("🌐 Recherche web en temps réel…"):
                    web_context, web_sources = fetch_web_context(user_input)

            # Étape 2 : analyse IA
            with st.spinner("🤖 Analyse en cours…"):
                try:
                    analysis_raw, model_used = get_expert_analysis(
                        user_input, web_context=web_context, lang=lang
                    )
                    analysis = strip_urls(analysis_raw)
                    verdict = extract_verdict(analysis)
                    add_to_history(user_input, cat_selection, verdict, analysis, model_used)
                    st.session_state.update({
                        "user_input": user_input,
                        "cat": cat_selection,
                        "analysis": analysis,
                        "step": 1,
                        "web_context": web_context,
                        "web_sources": web_sources,
                        "model_used": model_used,
                    })
                except Exception as e:
                    st.error(
                        f"❌ Impossible de contacter le service d'analyse : {e}\n\n"
                        "Vérifiez votre clé API ou réessayez. "
                        "Vous pouvez consulter les sources manuellement ci-dessous."
                    )

    # ── Résultats ──
    if st.session_state.get("step") == 1:

        model_used = st.session_state.get("model_used", "")
        st.caption(f"Modèle utilisé : `{model_used}`")

        # Sources web Tavily (si disponibles)
        web_sources = st.session_state.get("web_sources", [])
        if web_sources:
            with st.expander("🌐 Sources web récupérées en temps réel (Tavily)", expanded=False):
                for s in web_sources:
                    score_pct = int(s.get("score", 0) * 100)
                    st.markdown(f"- **{s['title']}** — [Ouvrir]({s['url']}) *(pertinence : {score_pct}%)*")

        st.info(
            "💡 **Astuce Vie Privée** : Faites un **clic-droit** sur les boutons "
            "→ *Ouvrir dans une fenêtre de navigation privée*."
        )

        # Sources institutionnelles
        st.markdown(f"### 🔗 Sources institutionnelles — *{st.session_state.cat}*")
        st.caption(
            "ℹ️ Ces sources fournissent le **cadre légal et institutionnel** du domaine. "
            "Pour fact-checker une affirmation précise, utilisez DuckDuckGo ou Qwant ci-dessous."
        )
        sources_cat = SOURCES[st.session_state.cat]
        cols = st.columns(len(sources_cat))
        encoded_q = st.session_state.user_input.replace(" ", "+")
        for i, (name, base_url) in enumerate(sources_cat.items()):
            cols[i].link_button(name, f"{base_url}{encoded_q}")

        # Moteurs vie privée
        st.markdown("---")
        st.markdown("#### 🌐 Recherche libre (moteurs respectueux de la vie privée)")
        c1, c2, c3 = st.columns(3)
        c1.link_button("DuckDuckGo", f"https://duckduckgo.com/?q={encoded_q}")
        c2.link_button("Qwant", f"https://www.qwant.com/?q={encoded_q}")
        c3.link_button("Brave Search", f"https://search.brave.com/search?q={encoded_q}")

        # Bilan apprenant
        st.markdown("---")
        st.subheader("📝 Votre bilan (avant de voir l'analyse IA)")
        st.caption(
            "Consultez d'abord les sources, puis rédigez votre conclusion. "
            "L'objectif est d'exercer votre jugement *avant* de voir celui de l'IA."
        )
        user_bilan = st.text_area(
            "Votre conclusion :",
            height=120,
            placeholder="Après consultation des sources, je pense que… parce que…",
        )

        if st.button("⚖️ Comparer avec l'analyse experte"):
            if not user_bilan.strip():
                st.warning("Rédigez d'abord votre bilan — c'est l'étape la plus importante !")
            else:
                analysis = st.session_state.analysis
                verdict = extract_verdict(analysis)
                color = verdict_color(verdict)

                clean = re.sub(
                    r'\[?VERDICT\]?\s*[:\-]\s*(VRAI|FAUX|INCERTAIN)\s*',
                    '', analysis, flags=re.IGNORECASE,
                ).strip()
                for label in ["VRAI", "FAUX", "INCERTAIN"]:
                    clean = clean.replace(f"[{label}]", "").replace(f"[{label.lower()}]", "")

                st.markdown(
                    f"""<div style="background:{color}20;border-left:6px solid {color};
                    padding:12px 18px;border-radius:8px;margin-bottom:16px;
                    font-size:1.25rem;font-weight:700;color:{color};">
                    Verdict IA : {verdict or "NON DÉTERMINÉ"}
                    </div>""",
                    unsafe_allow_html=True,
                )

                c1, c2 = st.columns(2)
                c1.markdown(
                    f"""<div style="background:#e3f2fd;padding:16px;border-radius:10px;
                    border-left:5px solid #2196f3;">
                    <h4 style="color:#1565c0;">👤 Votre bilan</h4>
                    <p style="white-space:pre-wrap;">{user_bilan}</p></div>""",
                    unsafe_allow_html=True,
                )
                c2.markdown(
                    f"""<div style="background:{color}12;padding:16px;border-radius:10px;
                    border-left:5px solid {color};">
                    <h4 style="color:{color};">🤖 Analyse méthodologique (IA)</h4>
                    <p style="white-space:pre-wrap;font-size:0.92rem;">{clean.strip()}</p></div>""",
                    unsafe_allow_html=True,
                )

                st.warning(
                    "⚠️ Cette analyse IA est un **guide méthodologique**, pas une vérité absolue. "
                    "Croisez toujours avec les sources institutionnelles consultées ci-dessus."
                )

                export_single = (
                    f"Affirmation : {st.session_state.user_input}\n"
                    f"Verdict IA : {verdict or 'NON DÉTERMINÉ'}\n"
                    f"Votre bilan : {user_bilan}\n\n"
                    f"--- Analyse IA ---\n{clean.strip()}"
                )
                st.download_button(
                    "📥 Télécharger cette analyse (.txt)",
                    data=export_single.encode("utf-8"),
                    file_name=f"analyse_emi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                )


# ── ONGLET 2 ─────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("🖼️ Vérifier une Image — Méthode TRACE")

    st.markdown("""
Avant de lancer une recherche inversée, posez-vous ces **5 questions** :

| Lettre | Question | Ce que vous cherchez |
|--------|----------|----------------------|
| **T** — Texte | Le texte associé correspond-il à ce qu'on voit réellement ? | Discordances, exagérations |
| **R** — Référence | D'où vient cette image selon celui qui la partage ? | Source primaire vérifiable |
| **A** — Auteur | Qui l'a prise ? Est-ce revendiqué et vérifiable ? | Profil, portfolio, crédits |
| **C** — Contexte | Quand et où a-t-elle été prise à l'origine ? | Date EXIF, géolocalisation |
| **E** — Émotion | Cherche-t-elle à provoquer une réaction forte ? | Peur, indignation, choc |
""")

    st.markdown("---")
    st.markdown("#### 🔎 Recherche inversée d'image")
    st.caption("Glissez-déposez l'image ou collez son URL dans chaque outil.")
    c1, c2, c3, c4 = st.columns(4)
    c1.link_button("🔍 Google Lens", "https://lens.google.com/")
    c2.link_button("🔍 TinEye", "https://tineye.com/")
    c3.link_button("🔍 Bing Visual", "https://www.bing.com/visualsearch/")
    c4.link_button("🔍 InVID / WeVerify", "https://www.invid-project.eu/tools-and-services/invid-verification-plugin/")

    st.markdown("---")
    st.markdown("#### 📅 Analyser les métadonnées")
    c1, c2, c3 = st.columns(3)
    c1.link_button("ExifData (date/GPS)", "https://exifdata.com/")
    c2.link_button("FotoForensics", "https://fotoforensics.com/")
    c3.link_button("Fake Image Detector", "https://www.fakeimagedetector.com/")

    st.markdown("---")
    st.markdown("#### 🤖 Détecter une image IA générée")
    c1, c2 = st.columns(2)
    c1.link_button("AI or Not", "https://www.aiornot.com/")
    c2.link_button("Hive Moderation", "https://hivemoderation.com/ai-generated-content-detection")

    st.info(
        "💡 **Rappel** : une image peut être authentique mais utilisée hors contexte. "
        "La recherche inversée confirme l'image, pas le récit qui l'accompagne."
    )


# ── ONGLET 3 ─────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("ℹ️ Méthode : Le Doute Méthodique")
    st.markdown("""
### Pourquoi cet outil ?

Cet outil est conçu pour des **ateliers EMI** : il ne remplace pas votre jugement,
il l'entraîne. La séquence est volontairement construite pour que vous consultiez
les sources *avant* de voir l'analyse IA.

---

### Les 4 principes de l'atelier

**1. Formulez d'abord votre propre hypothèse**  
Avant de cliquer sur quoi que ce soit, qu'est-ce qui vous rend méfiant(e) ?

**2. Consultez les sources institutionnelles**  
Les boutons renvoient vers des médias de référence et des institutions
(INSEE, OMS, INSERM…). Ils fournissent le contexte légal et factuel du domaine.

**3. Rédigez votre bilan avant de voir l'IA**  
C'est l'étape la plus importante. L'IA structure le raisonnement, elle ne pense pas à votre place.

**4. Comparez et discutez**  
Là où votre bilan et l'analyse IA divergent : c'est exactement là que se trouve l'apprentissage.

---

### Architecture technique

| Composant | Rôle | Gratuit |
|-----------|------|---------|
| **Groq** (GPT OSS 20B) | Analyse rapide (requêtes courtes) | ✅ 14 400 req/jour |
| **Groq** (llama-3.3-70b) | Analyse complète (requêtes complexes) | ✅ Idem |
| **Tavily** | Recherche web temps réel | ✅ 1 000 req/mois |

Le modèle est sélectionné automatiquement selon la complexité de l'affirmation.

---

### Limites de l'IA

- Date de coupure : l'IA ne connaît pas les événements très récents sans Tavily.
- Elle peut se tromper sur des faits précis — la rigueur vient des **sources humaines**.
- Les verdicts sont des **orientations**, pas des jugements définitifs.

---

### Confidentialité

- Clic-droit → navigation privée pour vos recherches.
- DuckDuckGo, Qwant, Brave Search limitent le profilage.
- Les affirmations ne sont **pas stockées** entre les sessions.
""")

    st.markdown("---")
    st.markdown("### 🧠 Pour aller plus loin : Kit Esprit Critique")
    st.caption(
        "Cet outil se concentre sur la vérification d'une affirmation précise. "
        "Le **Kit Esprit Critique** (Les RochDur) va plus loin : 15 applications ludiques "
        "pour travailler les biais cognitifs, les sophismes, la hiérarchie des preuves et "
        "la posture face à l'information — idéal en prolongement d'atelier."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🕵️ L'Académie des détectives**")
        st.caption("Repérer les biais cognitifs")
        st.link_button("Lancer", "https://kit-esprit-critique.vercel.app/apps/academie-detective.html")
    with c2:
        st.markdown("**⚖️ Toutes les preuves ne se valent pas**")
        st.caption("Hiérarchiser anecdote, étude, consensus…")
        st.link_button("Lancer", "https://kit-esprit-critique.vercel.app/apps/toutes-les-preuves.html")
    with c3:
        st.markdown("**🎯 Logic Quest**")
        st.caption("Débusquer les sophismes")
        st.link_button("Lancer", "https://kit-esprit-critique.vercel.app/apps/logic-quest.html")

    st.link_button(
        "🔗 Accéder au kit complet (15 applications)",
        "https://kit-esprit-critique.vercel.app",
        use_container_width=True,
    )


# ── MODE ANIMATEUR ────────────────────────────────────────────────────────────
if mode_animateur:
    history = st.session_state.get("history", [])
    st.markdown("---")
    st.markdown("## 🎓 Vue Animateur — Toutes les analyses de la session")
    if not history:
        st.info("Aucune analyse effectuée pour l'instant.")
    else:
        for i, h in enumerate(history, 1):
            color = verdict_color(h["verdict"])
            with st.expander(
                f"#{i} · {h['ts']} · **{h['verdict'] or '?'}** — {h['query'][:60]}",
                expanded=False,
            ):
                st.markdown(
                    f"<span style='color:{color};font-size:1.1rem;font-weight:700;'>"
                    f"Verdict : {h['verdict'] or 'NON DÉTERMINÉ'}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Domaine : {h['cat']} · Modèle : `{h['model']}`")
                st.markdown(h["analysis"])
