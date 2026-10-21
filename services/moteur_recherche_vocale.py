"""
Recherche vocale intelligente AYYOU.
Transforme une phrase dictée (« je veux un thiéboudienne pas cher à Médina ») en filtres de recherche :
spécialités, budget, quartier, tri par prix, restaurants ouverts.
"""

import re
import unicodedata
from typing import Dict, List, Optional

try:
    from ..schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
    from .moteur_chatbot import extraire_budget_depuis_texte
except (ImportError, ValueError):
    try:
        from schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
        from services.moteur_chatbot import extraire_budget_depuis_texte
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
        from ayyouServiceIA.services.moteur_chatbot import extraire_budget_depuis_texte


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni ponctuation : « Thiéboudienne ! » -> « thieboudienne »."""
    sans_accents = unicodedata.normalize("NFD", texte.lower())
    sans_accents = "".join(c for c in sans_accents if unicodedata.category(c) != "Mn")
    sans_accents = re.sub(r"[’'\-]", " ", sans_accents)
    sans_accents = re.sub(r"[^a-z0-9 ]", " ", sans_accents)
    return re.sub(r"\s+", " ", sans_accents).strip()


# Spécialité -> façons de la dire ou de l'écrire (déjà normalisées).
# La reconnaissance vocale écrit souvent les plats sénégalais de plusieurs manières.
SPECIALITES: Dict[str, List[str]] = {
    "thieb": ["thieb", "thiep", "tieb", "tiep", "thieboudienne", "thiebou dieune", "thieboudieune",
              "tieboudienne", "ceebu jen", "ceebu jeun", "ceebu", "riz au poisson"],
    "yassa": ["yassa", "yasa"],
    "mafe": ["mafe", "maafe", "mafeh"],
    "dibi": ["dibi", "dibiterie", "viande grillee"],
    "domoda": ["domoda"],
    "soupou kandia": ["soupou kandia", "soupe kandia", "kandia"],
    "thiou": ["thiou", "tiou"],
    "couscous": ["couscous", "thiere", "cere"],
    "lakh": ["lakh", "lakhou bissap"],
    "ndambe": ["ndambe"],
    "pastels": ["pastel", "pastels"],
    "fataya": ["fataya", "fatayas"],
    "nems": ["nem", "nems"],
    "burger": ["burger", "burgers", "hamburger", "hamburgers", "cheeseburger"],
    "pizza": ["pizza", "pizzas"],
    "chawarma": ["chawarma", "shawarma", "chawarmas", "shawarmas"],
    "sandwich": ["sandwich", "sandwichs", "sandwiches"],
    "frites": ["frites", "frite"],
    "poulet": ["poulet", "poulets", "chicken"],
    "poisson": ["poisson", "poissons", "thiof", "capitaine"],
    "crevettes": ["crevette", "crevettes"],
    "brochettes": ["brochette", "brochettes"],
    "grillades": ["grillade", "grillades", "barbecue", "braise"],
    "salade": ["salade", "salades"],
    "jus": ["jus", "boisson", "boissons"],
    "bissap": ["bissap"],
    "bouye": ["bouye", "bouy", "pain de singe"],
    "gingembre": ["gingembre"],
    "cafe touba": ["cafe touba"],
    "dessert": ["dessert", "desserts", "gateau", "gateaux", "patisserie", "patisseries", "glace", "glaces"],
}

EXPRESSIONS_PRIX = ["pas cher", "pas chere", "moins cher", "petit prix", "petits prix", "economique", "bon marche"]
EXPRESSIONS_OUVERT = ["ouvert maintenant", "ouverts maintenant", "encore ouvert", "qui est ouvert", "qui sont ouverts"]

# Mots sans valeur pour la recherche (formules de politesse, verbes de demande, articles...)
MOTS_VIDES = set("""
je j veux voudrais aimerais souhaite cherche recherche trouve trouver trouvez montre montrez donne donnez
moi me m nous on il y a avoir est sont un une des du de d la le les l au aux a en et ou avec sans pour par
sur dans chez pres proche cote autour quelque chose quel quelle quels quelles qui que quoi ou
manger mange bouffer commander commande livrer livre livraison faim plat plats repas resto restaurant restaurants
s il te vous plait stp svp merci bonjour salut salam ayyou ce cette ces mon ma mes ton ta tes
bon bonne bons bonnes tres super vraiment aujourd hui ce soir midi maintenant vite rapidement
pas cher chere moins prix petit petits economique marche budget francs franc fcfa cfa f frs maximum max
ouvert ouverts encore
""".split())


def extraire_budget(texte_normalise: str) -> Optional[int]:
    """« moins de 3 000 francs » -> 3000. Accepte aussi « francs », que la dictée écrit souvent en entier."""
    texte = re.sub(r"(\d)\s+(\d{3})\b", r"\1\2", texte_normalise)  # « 3 000 » -> « 3000 »
    match = re.search(r"(\d+)\s*(?:francs?|balles)\b", texte)
    if match and 500 <= int(match.group(1)) <= 100000:
        return int(match.group(1))
    return extraire_budget_depuis_texte(texte)


def analyser_recherche_vocale(requete: RequeteRechercheVocale) -> ReponseRechercheVocale:
    texte = normaliser(requete.texte)
    reste = f" {texte} "

    budget = extraire_budget(texte)
    tri = "PRIX" if any(f" {e} " in reste for e in EXPRESSIONS_PRIX) else None
    ouvert_seulement = any(f" {e} " in reste for e in EXPRESSIONS_OUVERT)

    # Quartier : uniquement parmi les quartiers où AYYOU a vraiment des restaurants
    quartier = None
    for nom in sorted(requete.quartiers_connus, key=len, reverse=True):
        nom_normalise = normaliser(nom)
        if nom_normalise and f" {nom_normalise} " in reste:
            quartier = nom
            reste = reste.replace(f" {nom_normalise} ", " ")
            break

    # Spécialités : les expressions les plus longues d'abord (« ceebu jen » avant « ceebu »)
    specialites: List[str] = []
    termes: List[str] = []
    variantes = sorted(
        ((variante, specialite) for specialite, liste in SPECIALITES.items() for variante in liste),
        key=lambda paire: len(paire[0]),
        reverse=True,
    )
    for variante, specialite in variantes:
        if f" {variante} " in reste:
            reste = reste.replace(f" {variante} ", " ")
            if specialite not in specialites:
                specialites.append(specialite)
                termes.extend(SPECIALITES[specialite])

    mots_libres = [
        mot for mot in reste.split()
        if len(mot) >= 3 and mot not in MOTS_VIDES and not mot.isdigit()
    ]

    return ReponseRechercheVocale(
        texte_normalise=texte,
        specialites=specialites,
        termes_recherche=termes,
        mots_libres=mots_libres,
        budget_max_fcfa=budget,
        quartier=quartier,
        tri=tri,
        ouvert_seulement=ouvert_seulement,
    )
