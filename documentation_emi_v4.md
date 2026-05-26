# 📖 Documentation pédagogique — Outil EMI Expert v4.0

> Ce document explique **chaque section du code** de l'outil EMI, de manière accessible
> à des collègues non-développeurs. L'objectif est de comprendre ce que fait chaque partie,
> pourquoi elle existe, et comment la modifier si besoin.

---

## 🗺️ Vue d'ensemble de l'architecture

L'outil est un **fichier Python unique** (`app.py`) qui s'exécute avec Streamlit.
Il se découpe en 6 grandes parties :

```
1. IMPORTS          → les bibliothèques dont on a besoin
2. CONFIGURATION    → les sources et les modèles IA
3. HELPERS          → les petites fonctions utilitaires
4. TAVILY           → la recherche web en temps réel
5. ANALYSE IA       → l'interrogation de Groq
6. INTERFACE        → tout ce que l'utilisateur voit
```

Streamlit fonctionne ainsi : à chaque interaction de l'utilisateur (clic, saisie),
Python **relit tout le fichier de haut en bas** et reconstruit l'interface.
C'est pourquoi l'ordre du code est important.

---

## PARTIE 1 — Imports (lignes 1 à 20)

```python
"""
Outil EMI Expert — Version 4.0
...
"""
```
> Le texte entre triple guillemets est une **docstring** : une description du fichier,
> ignorée par Python mais lisible par les humains. Bonne pratique pour documenter.

```python
import re
```
> `re` = **expressions régulières**. Permet de chercher et remplacer des motifs dans
> du texte. On s'en sert pour supprimer les URLs que l'IA génère malgré l'interdiction.

```python
import json
import io
```
> `json` : format d'échange de données (non utilisé directement ici mais utile pour
> des évolutions futures). `io` : manipulation de fichiers en mémoire.

```python
from datetime import datetime
```
> Importe la gestion des dates. On s'en sert pour afficher "Nous sommes le 26 mai 2026"
> dans le prompt envoyé à l'IA.

```python
import streamlit as st
```
> **Streamlit** est le framework qui crée l'interface web. Chaque `st.quelquechose()`
> affiche un élément à l'écran (bouton, texte, champ de saisie…).
> `as st` est un alias pour écrire `st.` au lieu de `streamlit.`.

```python
from groq import Groq
```
> Importe le client officiel de **Groq**, le service qui héberge les modèles IA
> (Llama). Sans cette ligne, impossible d'interroger l'IA.

```python
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
```
> **Bloc try/except** = "essaie, et si ça échoue, fais autre chose".
> Si le package `tavily-python` est installé → `TAVILY_AVAILABLE = True`.
> S'il est absent → `TAVILY_AVAILABLE = False` et l'outil continue sans planter.
> C'est ce qu'on appelle une **dégradation gracieuse** : l'outil reste utilisable
> même sans Tavily.

---

## PARTIE 2 — Configuration (lignes 22 à 80)

### Le dictionnaire SOURCES

```python
SOURCES = {
    "Fact-checking": {
        "AFP Factuel": "https://factuel.afp.com/?query=",
        ...
    },
    ...
}
```
> Un **dictionnaire Python** (`{}`) associe des clés à des valeurs.
> Ici : chaque domaine (clé) contient lui-même un dictionnaire de sources (nom → URL de base).
>
> L'URL de base se termine toujours par `?query=` ou `?q=` : c'est le paramètre de recherche
> du site. L'outil collera automatiquement l'affirmation de l'utilisateur à la suite.
>
> **Pour ajouter une source** : il suffit d'ajouter une ligne dans le bon domaine :
> ```python
> "Mon Site": "https://monsite.fr/recherche?q=",
> ```

### Les modèles IA

```python
MODEL_SIMPLE = "llama-3.1-8b-instant"
MODEL_FULL   = "llama-3.3-70b-versatile"
COMPLEXITY_THRESHOLD = 12
```
> Deux modèles sont disponibles sur Groq gratuitement :
> - **8b** (8 milliards de paramètres) : rapide, pour les questions courtes simples.
> - **70b** (70 milliards) : plus lent mais bien meilleur sur les raisonnements complexes.
>
> `COMPLEXITY_THRESHOLD = 12` : si l'affirmation dépasse 12 mots, on utilise le 70b.
> Ce seuil est modifiable selon vos besoins.

---

## PARTIE 3 — Fonctions utilitaires / Helpers (lignes 83 à 133)

### choose_model()

```python
def choose_model(query: str) -> str:
    word_count = len(query.split())
    return MODEL_FULL if word_count >= COMPLEXITY_THRESHOLD else MODEL_SIMPLE
```
> `query.split()` découpe la phrase en liste de mots (`["Brigitte", "Macron", "est"]`).
> `len()` compte les éléments. Si ≥ 12 mots → modèle 70b, sinon → 8b.
> La notation `A if condition else B` est un raccourci Python pour "si… sinon…".

### strip_urls()

```python
def strip_urls(text: str) -> str:
    text = re.sub(r'^\s*[-*•]\s*https?://\S+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'https?://\S+', '*(lien supprimé — voir boutons)*', text)
    text = re.sub(r'\b[\w\-]+\.(fr|com|org|net|gouv|eu|info|io)\b', '*(domaine supprimé)*', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```
> Malgré l'interdiction dans le prompt, l'IA génère parfois des URLs.
> Cette fonction est un **filet de sécurité** qui nettoie le texte avant affichage.
>
> Chaque `re.sub(motif, remplacement, texte)` cherche le motif et remplace par le texte :
> - Ligne 1 : supprime les lignes de liste avec une URL (`* https://...`)
> - Ligne 2 : remplace les URLs restantes par un message explicatif
> - Ligne 3 : supprime les noms de domaine nus (`elysee.fr`, `wikipedia.org`)
> - Ligne 4 : nettoie les lignes vides en trop (max 2 retours à la ligne consécutifs)

### extract_verdict()

```python
def extract_verdict(analysis: str) -> str:
    t = re.sub(r'\*+', '', analysis.upper())
    t = re.sub(r'\[VERDICT\]', 'VERDICT', t)
    match = re.search(r'VERDICT\s*[:\-]\s*(VRAI|FAUX|INCERTAIN)', t)
    if match:
        return match.group(1)
    for label in ["FAUX", "VRAI", "INCERTAIN"]:
        if f"[{label}]" in t:
            return label
    return ""
```
> L'IA peut écrire le verdict de plusieurs façons : `[VERDICT] : FAUX`,
> `**VERDICT : FAUX**`, `[FAUX]`… Cette fonction gère toutes ces variantes.
>
> - `analysis.upper()` : met tout en majuscules pour ne pas rater "faux" vs "FAUX"
> - `re.sub(r'\*+', '', ...)` : supprime le markdown gras (`**`)
> - `re.sub(r'\[VERDICT\]', 'VERDICT', ...)` : normalise `[VERDICT]` → `VERDICT`
> - `re.search(...)` : cherche le motif "VERDICT : MOT"
> - `match.group(1)` : récupère le premier groupe capturé, ici VRAI/FAUX/INCERTAIN
> - La boucle `for` est un fallback si le premier pattern n'a rien trouvé

### verdict_color()

```python
def verdict_color(verdict: str) -> str:
    return {"VRAI": "#43a047", "FAUX": "#e53935"}.get(verdict, "#fb8c00")
```
> Renvoie un code couleur HTML selon le verdict :
> - VRAI → vert (`#43a047`)
> - FAUX → rouge (`#e53935`)
> - Tout autre cas (INCERTAIN, vide) → orange (`#fb8c00`)
>
> `.get(clé, valeur_par_défaut)` : cherche la clé dans le dictionnaire,
> retourne la valeur par défaut si elle n'existe pas.

### reset_session()

```python
def reset_session():
    for key in ["user_input", "cat", "analysis", "step", "web_context", "model_used"]:
        st.session_state.pop(key, None)
```
> Streamlit garde en mémoire les données entre les interactions via `st.session_state`
> (un dictionnaire persistant). Cette fonction efface proprement toutes les données
> de l'analyse précédente avant d'en lancer une nouvelle.
> `.pop(key, None)` : supprime la clé si elle existe, ne fait rien sinon.

### detect_lang()

```python
def detect_lang(text: str) -> str:
    fr_markers = ['est', 'les', 'des', 'que', 'une', 'pour', 'dans', 'pas', 'sur', 'avec']
    words = text.lower().split()
    fr_score = sum(1 for w in words if w in fr_markers)
    return "fr" if fr_score >= 2 else "en" if len(words) > 0 else "fr"
```
> Détecte si l'affirmation est en français ou en anglais, sans API externe.
> Méthode simple : compte les mots français très courants ("est", "les", "des"…).
> Si 2 ou plus sont trouvés → français. Sinon → anglais.
> Le résultat est transmis à l'IA pour qu'elle réponde dans la même langue.

---

## PARTIE 4 — Tavily / Recherche web (lignes 136 à 166)

```python
def fetch_web_context(query: str) -> tuple[str, list[dict]]:
```
> Cette fonction retourne un **tuple** : deux valeurs à la fois.
> - Premier élément : un texte résumant ce que Tavily a trouvé sur le web
> - Deuxième élément : la liste des sources (titre + URL + score de pertinence)

```python
    if not TAVILY_AVAILABLE:
        return "", []
    tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    if not tavily_key:
        return "", []
```
> Double vérification : package installé ET clé API présente.
> Si l'une des deux manque, on retourne vide sans erreur.
> `st.secrets` lit les clés depuis le fichier `secrets.toml` de Streamlit.

```python
    try:
        client = TavilyClient(api_key=tavily_key)
        resp = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
```
> Crée un client Tavily et lance une recherche :
> - `search_depth="basic"` : recherche rapide (économise le quota)
> - `max_results=5` : 5 résultats maximum
> - `include_answer=True` : demande à Tavily de générer un résumé en plus des liens

```python
        answer = resp.get("answer", "") or ""
        sources = [
            {"title": r.get("title", ""), "url": r.get("url", ""), "score": r.get("score", 0)}
            for r in resp.get("results", [])
            if r.get("url")
        ]
        return answer, sources
    except Exception as e:
        return f"[Tavily indisponible : {e}]", []
```
> Extrait le résumé (`answer`) et construit la liste de sources.
> La **list comprehension** `[... for r in ... if ...]` est un raccourci Python
> pour construire une liste en filtrant : ici, on garde seulement les résultats avec une URL.
> Le `except` attrape toute erreur réseau ou API sans faire planter l'outil.

---

## PARTIE 5 — Analyse IA / Groq (lignes 169 à 240)

```python
def get_expert_analysis(query: str, web_context: str = "", lang: str = "fr") -> tuple[str, str]:
```
> Trois paramètres :
> - `query` : l'affirmation à analyser
> - `web_context` : le résumé Tavily (vide par défaut si Tavily inactif)
> - `lang` : la langue détectée ("fr" par défaut)
>
> Retourne (texte de l'analyse, nom du modèle utilisé).

```python
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    current_date = datetime.now().strftime("%d %B %Y")
    model = choose_model(query)
```
> Crée le client Groq, récupère la date du jour formatée ("26 mai 2026"),
> et choisit le modèle selon la complexité.

```python
    web_block = ""
    if web_context:
        web_block = f"""
CONTEXTE WEB RÉCUPÉRÉ EN TEMPS RÉEL :
---
{web_context}
---
Utilise ces informations. Ne mentionne pas Tavily dans ta réponse.
"""
```
> Si Tavily a trouvé quelque chose, on prépare un bloc de texte à insérer dans le prompt.
> Les `f"""..."""` sont des **f-strings** : des chaînes de caractères où `{variable}`
> est remplacé par la valeur réelle de la variable.

```python
    system_prompt = f"""
Nous sommes le {current_date}. Tu es un expert EMI...
CONTRAINTES ABSOLUES :
1. INTERDICTION TOTALE de générer des URLs...
...
STRUCTURE OBLIGATOIRE :
[VERDICT] : VRAI / FAUX / INCERTAIN
1. Faits observés
2. Biais et signaux d'alerte
3. Méthodologie de vérification
4. Limites de cette analyse
"""
```
> Le **system prompt** est l'instruction permanente donnée à l'IA avant chaque échange.
> C'est ici qu'on définit son rôle, ses contraintes et la structure de sa réponse.
> C'est la partie la plus importante à modifier si vous voulez changer le comportement de l'IA.

```python
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
```
> Envoie la requête à Groq avec deux messages :
> - `"system"` : les instructions permanentes
> - `"user"` : l'affirmation de l'utilisateur
>
> Paramètres importants :
> - `temperature=0.15` : proche de 0 = réponses factuelles et reproductibles ;
>   proche de 1 = réponses créatives et variées. Pour du fact-checking, on veut 0.
> - `max_tokens=900` : limite la longueur de la réponse (économise le quota).
>
> `.choices[0].message.content` : récupère le texte de la première (et unique) réponse.

---

## PARTIE 6 — Historique et export (lignes 243 à 270)

### add_to_history()

```python
def add_to_history(query, cat, verdict, analysis, model):
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
```
> À chaque analyse, on ajoute un enregistrement dans `st.session_state.history`
> (une liste de dictionnaires). L'heure (`ts`) permet de retrouver l'ordre des analyses.
> Cette liste persiste pendant toute la session mais disparaît à la fermeture du navigateur.

### export_history_txt()

```python
def export_history_txt() -> str:
    lines = [f"=== ATELIER EMI — Export {datetime.now().strftime('%d/%m/%Y %H:%M')} ===\n"]
    for i, h in enumerate(st.session_state.get("history", []), 1):
        lines.append(f"\n── Analyse #{i} ({h['ts']}) ──")
        ...
    return "\n".join(lines)
```
> Construit un fichier texte à partir de l'historique.
> `enumerate(..., 1)` : parcourt la liste en numérotant à partir de 1.
> `"\n".join(lines)` : assemble toutes les lignes séparées par des retours à la ligne.

---

## PARTIE 7 — Interface / Sidebar (lignes 273 à 330)

```python
st.set_page_config(page_title="Outil EMI Expert", layout="wide", page_icon="🛡️")
```
> Configure la page Streamlit : titre dans l'onglet du navigateur,
> layout "wide" = utilise toute la largeur de l'écran, icône dans l'onglet.
> **Doit être la première commande Streamlit du fichier.**

```python
with st.sidebar:
    mode_animateur = st.toggle("🎓 Mode animateur", value=False, help="...")
```
> `with st.sidebar:` : tout ce qui est dans ce bloc apparaît dans la barre latérale gauche.
> `st.toggle()` : interrupteur on/off. `value=False` = désactivé par défaut.

```python
    tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    if TAVILY_AVAILABLE and tavily_key:
        st.success("🌐 Recherche web : **activée** (Tavily)")
    else:
        st.warning("🌐 Recherche web : **désactivée**...")
```
> Affiche un bandeau vert ou orange selon l'état de Tavily.
> `st.success()` = bandeau vert, `st.warning()` = bandeau orange.

```python
    for i, h in enumerate(history, 1):
        color = verdict_color(h["verdict"])
        st.markdown(
            f"**#{i}** `{h['ts']}` "
            f"<span style='color:{color};font-weight:700'>{h['verdict'] or '?'}</span>...",
            unsafe_allow_html=True,
        )
```
> Affiche chaque analyse de l'historique avec sa couleur de verdict.
> `unsafe_allow_html=True` : autorise le HTML dans le markdown Streamlit.
> Sans ça, les balises `<span>` seraient affichées comme du texte brut.

```python
    st.download_button(
        "📥 Exporter la session (.txt)",
        data=export_txt.encode("utf-8"),
        file_name=f"atelier_emi_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
    )
```
> Crée un bouton de téléchargement. `.encode("utf-8")` convertit le texte en bytes
> (format nécessaire pour le téléchargement). `mime="text/plain"` indique au navigateur
> que c'est un fichier texte.

---

## PARTIE 8 — Onglet 1 : Analyser un texte (lignes 333 à 512)

```python
tab1, tab2, tab3 = st.tabs(["✍️ Vérifier un Texte", "🖼️ Vérifier une Image", "ℹ️ Méthode"])
```
> Crée 3 onglets et les assigne à 3 variables.
> Tout ce qui suit `with tab1:` s'affiche dans le premier onglet, etc.

```python
col_form, col_info = st.columns([3, 1])
```
> Divise l'espace en 2 colonnes. `[3, 1]` = proportions : la première fait 3/4 de largeur,
> la seconde 1/4. Permet d'afficher le formulaire et l'info modèle côte à côte.

```python
launch = st.button("🔍 Lancer l'analyse", type="primary")
if launch:
```
> `st.button()` retourne `True` quand on clique dessus, `False` sinon.
> On stocke dans `launch` pour tester ensuite. `type="primary"` = bouton bleu mis en avant.

```python
    lang = detect_lang(user_input)
    web_context, web_sources = fetch_web_context(user_input)
    analysis_raw, model_used = get_expert_analysis(user_input, web_context, lang)
    analysis = strip_urls(analysis_raw)
    verdict = extract_verdict(analysis)
    add_to_history(user_input, cat_selection, verdict, analysis, model_used)
```
> La **chaîne de traitement** complète, dans l'ordre :
> 1. Détecte la langue
> 2. Cherche des faits sur le web (Tavily)
> 3. Interroge l'IA (Groq) avec le contexte web
> 4. Nettoie les URLs générées malgré l'interdiction
> 5. Extrait le verdict
> 6. Sauvegarde dans l'historique

```python
    st.session_state.update({
        "user_input": user_input,
        "cat": cat_selection,
        "analysis": analysis,
        "step": 1,
        ...
    })
```
> Sauvegarde les résultats dans la session pour les afficher après le rechargement.
> Rappel : Streamlit relit tout le code à chaque interaction, donc sans session_state
> les données seraient perdues.

```python
if st.session_state.get("step") == 1:
```
> Condition qui contrôle l'affichage des résultats.
> Si `step` n'existe pas encore (première visite), rien ne s'affiche.
> Dès que l'analyse est lancée, `step = 1` et les résultats apparaissent.

```python
    with st.expander("🌐 Sources web récupérées en temps réel (Tavily)", expanded=False):
        for s in web_sources:
            score_pct = int(s.get("score", 0) * 100)
            st.markdown(f"- **{s['title']}** — [Ouvrir]({s['url']}) *(pertinence : {score_pct}%)*")
```
> `st.expander()` : section repliable. `expanded=False` = repliée par défaut.
> Le score Tavily est entre 0 et 1, on le convertit en pourcentage pour l'affichage.

```python
    cols = st.columns(len(sources_cat))
    for i, (name, base_url) in enumerate(sources_cat.items()):
        encoded_q = st.session_state.user_input.replace(" ", "+")
        cols[i].link_button(name, f"{base_url}{encoded_q}")
```
> Crée autant de colonnes qu'il y a de sources dans le domaine sélectionné.
> `replace(" ", "+")` : encode les espaces pour les URLs (standard web).
> `link_button()` : bouton qui ouvre un lien externe.

```python
    clean = re.sub(
        r'\[?VERDICT\]?\s*[:\-]\s*(VRAI|FAUX|INCERTAIN)\s*',
        '', analysis, flags=re.IGNORECASE,
    ).strip()
```
> Retire la ligne de verdict du corps du texte pour éviter la répétition
> (le verdict est déjà affiché dans le bandeau coloré au-dessus).

```python
    st.markdown(
        f"""<div style="background:{color}20;border-left:6px solid {color};...">
        Verdict IA : {verdict or "NON DÉTERMINÉ"}
        </div>""",
        unsafe_allow_html=True,
    )
```
> Affiche le bandeau coloré avec du HTML/CSS inline.
> `{color}20` : le `20` à la fin d'un code couleur hexadécimal définit la transparence
> (20 en hexadécimal = ~12% d'opacité). Effet "fond très léger de la même couleur".

---

## PARTIE 9 — Onglet 2 : Image (lignes 515 à 556)

La méthode **TRACE** est affichée sous forme de tableau Markdown.
Les outils sont organisés en 3 groupes :
- Recherche inversée (retrouver l'origine d'une image)
- Métadonnées EXIF (date, GPS de la prise de vue)
- Détection d'image générée par IA

Tous sont de simples `link_button()` vers des services externes gratuits.

---

## PARTIE 10 — Mode Animateur (lignes 616 à 636)

```python
if mode_animateur:
    for i, h in enumerate(history, 1):
        with st.expander(f"#{i} · {h['ts']} · **{h['verdict'] or '?'}** — {h['query'][:60]}", ...):
            st.markdown(h["analysis"])
```
> S'affiche **en dehors des onglets**, en bas de page, uniquement si le toggle
> "Mode animateur" est activé dans la sidebar.
>
> `h['query'][:60]` : affiche les 60 premiers caractères de l'affirmation
> pour que le titre de l'accordéon reste lisible.
>
> Chaque analyse passée est affichée dans un accordéon dépliable,
> avec sa couleur de verdict. Pratique pour une restitution en groupe projeté.

---

## 🔧 Guide de modification rapide

| Je veux… | Je modifie… |
|----------|-------------|
| Ajouter une source | Le dictionnaire `SOURCES`, ligne ~25 |
| Changer le seuil modèle simple/complet | `COMPLEXITY_THRESHOLD`, ligne 80 |
| Modifier les instructions de l'IA | Le `system_prompt` dans `get_expert_analysis()` |
| Ajouter un verdict possible | `extract_verdict()` et `verdict_color()` |
| Changer les couleurs des verdicts | `verdict_color()` |
| Limiter la longueur des réponses IA | `max_tokens=900` dans `get_expert_analysis()` |
| Rendre l'IA plus créative/moins factuelle | `temperature=0.15` (augmenter vers 0.5) |
| Ajouter un onglet | `st.tabs([..., "Nouvel onglet"])` et `with tab4:` |

---

## 📦 Les services externes utilisés

| Service | Rôle | Limite gratuite | Clé dans secrets.toml |
|---------|------|-----------------|----------------------|
| **Streamlit Cloud** | Hébergement de l'app | Illimité (public) | — |
| **Groq** | Modèles IA (Llama) | 14 400 req/jour | `GROQ_API_KEY` |
| **Tavily** | Recherche web temps réel | 1 000 req/mois | `TAVILY_API_KEY` |

---

*Documentation générée avec Claude (Anthropic) — Mai 2026*
