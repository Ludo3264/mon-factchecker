import streamlit as st
import urllib.parse
import re
from langchain_groq import ChatGroq
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TRUSTED_SITES = [
    "site:factuel.afp.com", "site:lemonde.fr/les-decodeurs", "site:liberation.fr/checknews",
    "site:francetvinfo.fr/vrai-ou-fake", "site:factcheck.org", "site:fullfact.org",
    "site:snopes.com", "site:reuters.com/fact-check", "site:euvsdisinfo.eu"
]

def search_trusted_sources(claim: str) -> tuple[list[dict], str]:
    query_sites = " OR ".join(TRUSTED_SITES)
    try:
        search = GoogleSerperAPIWrapper(
            serper_api_key=st.secrets["SERPER_API_KEY"],
            gl="fr", hl="fr"
        )
        results = search.results(f"{claim} ({query_sites})")
    except Exception as e:
        st.error(f"❌ Erreur Serper : {e}")
        return [], "Aucune source disponible."

    sources_list, formatted = [], []
    for res in results.get("organic", [])[:4]:
        title, link, snippet = res.get("title", "Sans titre"), res.get("link", ""), res.get("snippet", "")
        sources_list.append({"title": title, "link": link, "snippet": snippet})
        formatted.append(f"- {title}\n  URL : {link}\n  Extrait : {snippet}")
    context_str = "\n\n".join(formatted) if formatted else "Aucune source pertinente trouvée."
    return sources_list, context_str

ANALYSIS_TEMPLATE = """Tu es un assistant pédagogique spécialisé en Éducation aux Médias et à l'Information (EMI).
Ton rôle est d'aider l'utilisateur à développer son esprit critique, PAS de trancher définitivement.

RÈGLES IMPÉRATIVES :
1. Ne fabrique AUCUNE URL, date ou citation. Utilise UNIQUEMENT les sources fournies.
2. Si les sources sont insuffisantes ou contradictoires, dis-le explicitement.
3. Respecte strictement le plan ci-dessous.

SOURCES VÉRIFIÉES (issues d'une recherche réelle) :
{context}

AFFIRMATION ANALYSÉE : {claim}

## 🔎 ÉVALUATION PRÉLIMINAIRE
Commence par : VRAI / FAUX / NUANCÉ / INDÉTERMINÉ (en majuscules), suivi d'une justification courte (2 lignes max).

## 📋 ANALYSE FACTUELLE
Ce que disent les sources disponibles. Mentionne explicitement les limites (manque de sources, sources datées, contexte partiel).

## ❓ QUESTIONS À SE POSER
3 à 5 questions que tout citoyen devrait poser face à cette affirmation (Qui publie ? Dans quel contexte ? Quelles preuves ?).

## 🧭 PISTE DE VÉRIFICATION PERSONNELLE
1 ou 2 démarches concrètes que l'utilisateur peut faire lui-même.

## ⚠️ MISE EN GARDE
Si le sujet est sensible, polarisant ou susceptible d'évoluer, signale-le."""

def analyze_claim(claim: str, context: str) -> str:
    try:
        llm = ChatGroq(api_key=st.secrets["GROQ_API_KEY"], model="llama-3.1-8b-instant", temperature=0)
        chain = PromptTemplate.from_template(ANALYSIS_TEMPLATE) | llm | StrOutputParser()
        return chain.invoke({"context": context, "claim": claim})
    except Exception as e:
        return f"❌ Erreur LLM : {e}"

def detect_verdict(text: str) -> str:
    zone = text[:120].upper()
    for v in ["INDÉTERMINÉ", "INDETERMINE", "NUANCÉ", "NUANCE", "FAUX", "VRAI"]:
        if v in zone:
            return v
    return "INCONNU"

def display_verdict_badge(verdict: str):
    cfg = {
        "VRAI":        ("#d1fae5", "#065f46", "✅ VRAI"),
        "FAUX":        ("#fee2e2", "#991b1b", "❌ FAUX"),
        "NUANC":       ("#fef3c7", "#92400e", "⚠️ NUANCÉ"),
        "IND":         ("#e0e7ff", "#3730a3", "❓ INDÉTERMINÉ"),
        "INCONNU":     ("#f3f4f6", "#374151", "🔍 INDÉTERMINÉ"),
    }
    key = next((k for k in cfg if verdict.startswith(k)), "INCONNU")
    bg, fg, label = cfg[key]
    st.markdown(
        f'<div style="background:{bg};color:{fg};padding:12px 20px;border-radius:8px;'
        f'font-size:1.2rem;font-weight:700;display:inline-block;margin-bottom:12px;">{label}</div>',
        unsafe_allow_html=True
    )

# ==============================================================================
# INTERFACE
# ==============================================================================
st.set_page_config(page_title="Fact-Checking EMI", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
.source-card {
    background:#f8fafc;border:1px solid #e2e8f0;
    border-radius:8px;padding:12px 16px;margin-bottom:10px;
}
.source-card a { color:#2563eb;text-decoration:none;font-weight:600; }
.warning-box {
    background:#fffbeb;border-left:4px solid #f59e0b;
    padding:10px 16px;border-radius:4px;margin-bottom:16px;
    font-size:0.88rem;color:#78350f;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Outil d'Analyse Critique — EMI")
st.caption("Éducation aux Médias et à l'Information · Cet outil aide à questionner, pas à trancher définitivement.")

# Vérification des secrets
for key in ["GROQ_API_KEY", "SERPER_API_KEY"]:
    if key not in st.secrets:
        st.error(f"Clé API manquante dans les secrets : `{key}`")
        st.stop()

tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])

# --------------------------------------------------------------------------
# TAB 1 — ANALYSE TEXTUELLE
# --------------------------------------------------------------------------
with tab1:
    st.markdown(
        '<div class="warning-box">⚠️ Cet outil est une aide à la réflexion. '
        'Il ne remplace pas votre propre jugement critique. '
        'Les sources affichées proviennent d\'une recherche automatisée et doivent être vérifiées.</div>',
        unsafe_allow_html=True
    )
    user_claim = st.text_area(
        "Saisissez l'affirmation à vérifier :",
        placeholder="Ex : Les réseaux sociaux sont responsables de la hausse de l'anxiété chez les adolescents.",
        height=100
    )
    if st.button("🔍 Lancer l'analyse"):
        if not user_claim.strip():
            st.warning("Merci de saisir une affirmation avant de lancer l'analyse.")
        else:
            with st.spinner("🔎 Recherche dans les sources de confiance..."):
                sources_list, context_str = search_trusted_sources(user_claim)
            if not sources_list:
                st.warning("Aucune source trouvée — l'analyse sera limitée, interprétez avec prudence.")
            with st.spinner("🧠 Analyse critique en cours..."):
                result = analyze_claim(user_claim, context_str)

            st.markdown("### ⚖️ Résultat de l'analyse")
            display_verdict_badge(detect_verdict(result))
            st.markdown(result)
            st.markdown("---")

            st.markdown("### 🔗 Sources réelles trouvées (Serper)")
            st.caption("Ces URLs proviennent d'une recherche réelle — elles ne sont PAS générées par le LLM.")
            if sources_list:
                for s in sources_list:
                    st.markdown(
                        f'<div class="source-card">'
                        f'<a href="{s["link"]}" target="_blank">{s["title"]}</a><br>'
                        f'<small style="color:#6b7280;">{s["link"]}</small><br>'
                        f'{s["snippet"]}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Aucune source externe trouvée.")

            export_text = (
                f"AFFIRMATION :\n{user_claim}\n\n{'='*60}\nANALYSE :\n{result}\n\n{'='*60}\nSOURCES :\n"
                + "\n".join(f"- {s['title']} | {s['link']}\n  {s['snippet']}" for s in sources_list)
            )
            st.download_button("📥 Télécharger le rapport (.txt)", export_text, "analyse_emi.txt", "text/plain")

# --------------------------------------------------------------------------
# TAB 2 — VÉRIFICATION D'IMAGE
# --------------------------------------------------------------------------
with tab2:
    st.markdown("#### Traquer l'origine d'une image")
    st.markdown("Utilisez au moins deux outils et comparez les résultats.")

    image_url = st.text_input("Collez l'URL de l'image :", placeholder="https://exemple.com/image.jpg")
    if image_url:
        encoded_url = urllib.parse.quote_plus(image_url)
        st.markdown("##### 🔍 Recherche inversée par URL")
        col1, col2, col3 = st.columns(3)
        with col1: st.link_button("👁️ Google Lens", f"https://lens.google.com/uploadbyurl?url={encoded_url}", use_container_width=True)
        with col2: st.link_button("🤖 TinEye", f"https://tineye.com/search/?url={encoded_url}", use_container_width=True)
        with col3: st.link_button("🔎 Bing Visual", f"https://www.bing.com/images/search?q=imgurl:{encoded_url}&view=detailv2&iss=sbi", use_container_width=True)

    st.markdown("---")
    st.markdown("##### 📱 Depuis un fichier local")
    c1, c2, c3 = st.columns(3)
    with c1: st.link_button("📸 Google Lens", "https://lens.google.com", use_container_width=True)
    with c2: st.link_button("🤖 TinEye", "https://tineye.com", use_container_width=True)
    with c3: st.link_button("🔎 Bing Visual", "https://www.bing.com/images/", use_container_width=True)

    st.markdown("---")
    st.markdown("##### 💡 Que chercher lors d'une recherche inversée ?")
    st.markdown("""
- **Date de première apparition** : l'image est-elle plus ancienne que le contexte présenté ?
- **Contexte d'origine** : à quel événement réel est-elle liée ?
- **Modifications** : la version circulant est-elle identique à l'originale ?
- **Sources qui la relaient** : quels types de sites la partagent ?
""")

# --------------------------------------------------------------------------
# TAB 3 — MÉTHODE
# --------------------------------------------------------------------------
with tab3:
    st.markdown("#### Comment fonctionne cet outil ?")
    st.markdown("""
**1. Recherche dans des sources de confiance (Serper API)**
Requête restreinte à des sites de fact-checking reconnus (AFP Factuel, Les Décodeurs, CheckNews, Snopes…).
Les URLs retournées sont **réelles** — pas générées par une IA.

**2. Analyse par un LLM (Groq / LLaMA 3.1)**
Le modèle reçoit uniquement les extraits trouvés à l'étape 1. Il est instruit de ne pas inventer de sources
et de signaler les incertitudes. Son rôle est pédagogique : poser des questions, pas trancher.

**3. Affichage différencié**
Sources réelles (Serper) et analyse LLM sont affichées séparément.

---
#### Limites
- Les sources peuvent ne pas avoir traité le sujet → "Indéterminé" est une réponse normale et honnête.
- Le LLM peut mal interpréter les extraits.
- Un résultat "VRAI" ne dispense pas de vérifier soi-même.

---
#### Ressources EMI
- [CLEMI](https://www.clemi.fr) · [AFP Factuel](https://factuel.afp.com) · [Méthode SIFT](https://hapgood.us/2019/06/19/sift-the-four-moves/)
""")
