import functools

def recursive_cache_timer(show_time=False):
    """
    Décorateur qui ajoute :
    - un mécanisme de mémoïsation (cache) pour accélérer la récursion
    - un chronométrage optionnel pour mesurer le temps d’exécution
    """
    def decorator(func):
        cache = {}  # Dictionnaire servant à mémoriser les résultats déjà calculés

        @functools.wraps(func)
        def wrapper(tree, i=0, k=0):
            """
            Fonction enveloppe qui gère le cache.
            Les clés sont les couples (i, k), correspondant à la position dans l’arbre.
            """
            key = (i, k)
            if key in cache:  # Si le résultat a déjà été calculé, on le renvoie directement
                return cache[key]

            # Calcul et stockage du résultat dans le cache
            result = func(tree, i, k, cache)
            cache[key] = result
            return result

        return wrapper
    return decorator


@recursive_cache_timer(show_time=True)
def price_recursive(tree, i=0, k=0, _cache=None):
    """
    Fonction de calcul récursif du prix de l’option.
    """

    # Initialisation du cache si non fourni
    if _cache is None:
        _cache = {}

    key = (i, k)
    if key in _cache:
        return _cache[key]

    # A maturité 
    if i >= tree.N:
        idx = k + i  # Index réel du noeud dans la liste
        if 0 <= idx < len(tree.tree[i]):
            node = tree.tree[i][idx]
            val = 0.0 if node is None else tree.option.payoff(node.stock_price)
        else:
            val = 0.0
        _cache[key] = val
        return val

    # Vérification des indices valides
    idx = k + i
    if not (0 <= idx < len(tree.tree[i])):
        _cache[key] = 0.0
        return 0.0

    node = tree.tree[i][idx]
    if node is None:
        _cache[key] = 0.0
        return 0.0

    S = node.stock_price  # Prix du sous-jacent au noeud courant

    # Récupération des probabilités locales
    try:
        pD, pM, pU, kprime = tree.proba_tree[i][idx]
    except (IndexError, TypeError):
        _cache[key] = 0.0
        return 0.0

    # Encadrement du décalage k' pour rester dans les bornes de l’arbre
    kprime = max(-(i + 1), min(i + 1, kprime))

    # Appels récursifs sur les trois directions
    Vd = price_recursive(tree, i + 1, kprime - 1)  
    Vm = price_recursive(tree, i + 1, kprime)     
    Vu = price_recursive(tree, i + 1, kprime + 1)  

    hold = tree.df * (pD * Vd + pM * Vm + pU * Vu)
    exer = tree.option.payoff(S)

    val = max(hold, exer) if tree.exercise == "american" else hold

    _cache[key] = val
    return val
