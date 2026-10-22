import re
from typing import Optional

NOMBRES_TEXTE = {
    "cinq cents": 500,
    "cinq cent": 500,
    "cinq-cents": 500,
    "cinq-cent": 500,
    "six cents": 600,
    "sept cents": 700,
    "huit cents": 800,
    "neuf cents": 900,
    "mille": 1000,
    "mille cinq cents": 1500,
    "mille cinq cent": 1500,
    "deux mille": 2000,
    "deux mille cinq cents": 2500,
    "deux mille cinq cent": 2500,
    "trois mille": 3000,
    "trois mille cinq cents": 3500,
    "quatre mille": 4000,
    "cinq mille": 5000,
    "six mille": 6000,
    "sept mille": 7000,
    "huit mille": 8000,
    "neuf mille": 9000,
    "dix mille": 10000,
    "quinze mille": 15000,
    "vingt mille": 20000,
}


def extraire_budget_robuste(texte: str) -> Optional[int]:
    """
    Extrait avec robustesse un montant budgétaire en FCFA d'une phrase en français.
    Gère :
    - Chiffres + devises : '500 francs', '500 fcfa', '1500 cfa', '500f', '3 000 F'
    - Formulations verbales directes : 'j'ai 500', 'jai 500', 'je dispose de 1500', 'je peux mettre 2500'
    - Contraintes : 'moins de 3000', 'maximum 2500', 'max 2000', 'pas dépasser 3000', 'sous 1500'
    - Prépositions : 'pour 2000', 'avec 1500', 'de 3000', 'à 2500'
    - Mots en toutes lettres : 'cinq cents francs', 'mille cinq cents', 'deux mille'
    - Formats k/mille : '2,5 mille' -> 2500, '2.5 mille' -> 2500
    - Séparateurs d'espace et de points : '1 500', '3.000'
    """
    if not texte:
        return None
    texte_clean = texte.lower().strip()

    # 1. Nombres décimaux avec 'mille' (ex: '2,5 mille' ou '2.5 mille')
    match_k = re.search(r"(\d+(?:[,\.]\d+)?)\s*mille", texte_clean)
    if match_k:
        val_str = match_k.group(1).replace(",", ".")
        try:
            val_float = float(val_str)
            return int(val_float * 1000)
        except ValueError:
            pass

    # 2. Mots en toutes lettres ('cinq cents francs', 'deux mille', etc.)
    for nom_texte, valeur in sorted(NOMBRES_TEXTE.items(), key=lambda x: -len(x[0])):
        if nom_texte in texte_clean:
            return valeur

    # 3. Motifs regex ordonnés du plus spécifique au plus général
    motifs = [
        # Explicit currency suffix: '500 fcfa', '1 500 francs', '3000 cfa', '500f', '4500 frs'
        r"(\d+[\s\.]?\d*)\s*(?:fcfa|cfa|frs|francs?|f\b)",
        # Keywords 'budget', 'budjet', 'tarif', 'somme'
        r"(?:budget|budjet|tarif|somme)(?:\s*(?:de|max|maximum|environ|égal|egal|:|=))?\s*(\d+[\s\.]?\d*)",
        # Ceiling constraints: 'moins de 3000', 'maximum 2500', 'max 2500', 'pas dépasser 3000', 'ne pas dépasser 3000', 'sous 2000'
        r"(?:moins\s+de|maximum|max|ne\s+pas\s+dépasser|pas\s+dépasser|sous|inférieur\s+à)\s*(\d+[\s\.]?\d*)",
        # Verb phrase with possession / budget: 'j'ai 500', 'jai 500', 'je dispose de 1500', 'je peux mettre 2500', 'j ai 500'
        r"(?:j['’]?\s*ai|jai|dispose\s+de|peux\s+mettre|mettre\s+au\s+max)\s*(\d+[\s\.]?\d*)",
        # Prepositional expressions: 'pour 2000', 'avec 1500', 'de 2500', 'à moins de 3000'
        r"(?:pour|avec|de|à|a)\s*(\d+[\s\.]?\d*)\s*(?:fcfa|cfa|frs|francs?|f\b)?",
        # Standalone number if phrase is very short or clearly food search (e.g., '500 que me propose tu', 'thieb 2500')
        r"\b(\d{3,5})\b",
    ]

    for motif in motifs:
        match = re.search(motif, texte_clean)
        if match:
            chiffres = re.sub(r"[\s\.]", "", match.group(1))
            try:
                val = int(chiffres)
                # Validation du montant raisonnable pour un repas à Dakar (200 FCFA à 100 000 FCFA)
                if 200 <= val <= 100000:
                    return val
            except ValueError:
                continue

    return None


if __name__ == "__main__":
    tests = [
        ("J'ai 500 francs.", 500),
        ("jai 500 que me propose tu", 500),
        ("J'ai 500 F.", 500),
        ("Mon budget est de 500 FCFA.", 500),
        ("Je dispose de 1 500 francs.", 1500),
        ("Je veux manger pour moins de 2 000.", 2000),
        ("Je ne veux pas dépasser 3 000 francs.", 3000),
        ("Je peux mettre maximum 2 500.", 2500),
        ("J'ai cinq cents francs.", 500),
        ("J'ai 2,5 mille.", 2500),
        ("Je veux du yassa à moins de 3 000 FCFA.", 3000),
        ("Je dispose de 1 500 francs et je veux du poisson.", 1500),
        ("Je peux mettre cinq cents francs.", 500),
    ]

    succes = 0
    for phrase, attendu in tests:
        res = extraire_budget_robuste(phrase)
        assert res == attendu, f"ECHEC pour '{phrase}': attendu {attendu}, obtenu {res}"
        succes += 1
    print(f"TOUS LES {succes}/{len(tests)} TESTS DE BUDGET ONT REUSSI !")
