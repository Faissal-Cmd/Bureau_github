import sys
import gurobipy as gp
from gurobipy import GRB

def lire_fichier_entree(fichier_entree):
    """
    Lire le fichier d'entrée et organiser les photos en horizontales ou verticales.
    """
    with open(fichier_entree, "r") as fichier:
        lignes = fichier.read().strip().split("\n")

    N = int(lignes[0])  # Nombre de photos
    photos_horizontales = []
    photos_verticales = []

    for i in range(1, N + 1):
        donnees = lignes[i].split()
        orientation = donnees[0]
        etiquettes = set(donnees[2:])

        if orientation == "H":
            photos_horizontales.append({"id": i - 1, "sens": orientation, "etiquettes": etiquettes})
        elif orientation == "V":
            photos_verticales.append({"id": i - 1, "sens": orientation, "etiquettes": etiquettes})

    return photos_horizontales, photos_verticales

def calculer_facteur_interet(etiquettes1, etiquettes2):
    """
    Calculer le facteur d'intérêt entre deux ensembles d'étiquettes.
    """
    etiquettes_communes = len(etiquettes1.intersection(etiquettes2))
    etiquettes_uniques_1 = len(etiquettes1 - etiquettes2)
    etiquettes_uniques_2 = len(etiquettes2 - etiquettes1)
    return min(etiquettes_communes, etiquettes_uniques_1, etiquettes_uniques_2)

def optimiser_diaporama(diapositives):
    """
    Optimisation du diaporama avec Gurobi en maximisant l'intérêt total.
    """
    modele = gp.Model("Diaporama")
    n_diapositives = len(diapositives)
    
    U = modele.addVars(n_diapositives, vtype=GRB.BINARY, name="U")
    # Variables binaires : Z[i, j] indique si la diapositive i est suivie de la diapositive j
    Z = modele.addVars(n_diapositives, n_diapositives, vtype=GRB.BINARY, name="Z")

    # ** Contrainte : Chaque diapositive a un unique successeur et un unique prédécesseur**
    for i in range(n_diapositives):
        modele.addConstr(gp.quicksum(Z[i, j] for j in range(n_diapositives) if i != j) == 1)
        modele.addConstr(gp.quicksum(Z[j, i] for j in range(n_diapositives) if i != j) == 1)

    # ** Empêcher les auto-références (éviter que i pointe vers lui-même)**
    for i in range(n_diapositives):
        modele.addConstr(Z[i, i] == 0)

    for i in range(n_diapositives):
        for j in range(n_diapositives):
            if i != j:
                modele.addConstr(Z[i, j] + Z[j, i] <= 1, name=f"AntiCycle_{i}_{j}")
    
    # Préparation des termes de la somme pour affichage
    termes_objectif = []

    for i in range(n_diapositives):
        for j in range(n_diapositives):
            if  j == i+1 :  # Exclure les cas i == j
                facteur_interet = calculer_facteur_interet(diapositives[i]["etiquettes"], diapositives[j]["etiquettes"])
                termes_objectif.append((i, j, facteur_interet))

    
    # Définition de l'objectif dans Gurobi
    modele.setObjective(
        gp.quicksum(
            facteur_interet * Z[i, j]
            for i, j, facteur_interet in termes_objectif
        ),
        GRB.MAXIMIZE
    )

    # ** Résolution du modèle**
    modele.optimize()

    ordre = []
    if modele.Status == GRB.OPTIMAL:
        print("\n Solution optimale trouvée !")
        print(f" Objectif optimal : {modele.ObjVal}")

        # Récupération des valeurs optimales pour O[i]
        order_values = {i: U[i].x for i in range(n_diapositives)}

        # Trier les diapositives selon leur ordre dans le chemin
        sorted_order = sorted(order_values.keys(), key=lambda x: order_values[x])

        # Construire la séquence ordonnée
        for i in range(len(sorted_order) - 1):
            ordre.append((sorted_order[i], sorted_order[i + 1]))

    else:
        print("\n Aucune solution optimale trouvée.")

    return ordre

def combiner_photos_verticales_optimise(photos_verticales):
    """
    Optimiser la combinaison des photos verticales en maximisant l'intérêt total.
    """
    modele = gp.Model("CombinaisonVerticale")
    modele.setParam('OutputFlag', 0)
    n = len(photos_verticales)

    if n < 2:
        return []

    # **Variables de décision X[i, j]** : indique si la photo i est appariée avec la photo j
    X = modele.addVars(n, n, vtype=GRB.BINARY, name="X")

    # ** Contraintes : Chaque photo verticale doit être appariée une seule fois**
    for i in range(n):
        modele.addConstr(gp.quicksum(X[i, j] for j in range(n) if i != j) == 1)
        modele.addConstr(gp.quicksum(X[j, i] for j in range(n) if i != j) == 1)

    # ** Fonction objectif : Maximiser l'intérêt des paires**
    modele.setObjective(
        gp.quicksum(
            calculer_facteur_interet(photos_verticales[i]["etiquettes"], photos_verticales[j]["etiquettes"]) * X[i, j]
            for i in range(n) for j in range(n) if i != j
        ),
        GRB.MAXIMIZE
    )

    # **Résolution du modèle**
    modele.optimize()

    # **Construction des diapositives verticales optimisées**
    diapositives = []
    used = set()
    for i in range(n):
        for j in range(n):
            if i!=j and X[i, j].x > 0.5 and i not in used and j not in used:
                etiquettes_combinees = photos_verticales[i]["etiquettes"].union(photos_verticales[j]["etiquettes"])
                diapositives.append({
                    "ids": [photos_verticales[i]["id"], photos_verticales[j]["id"]],
                    "sens": ["V"],
                    "etiquettes": etiquettes_combinees
                })
                used.add(i)
                used.add(j)
    return diapositives


def ecrire_fichier_sortie(fichier_sortie, ordre, diapositives):
    """
    Écrire le fichier de sortie au format attendu en respectant l'ordre des transitions.
    """
    with open(fichier_sortie, "w") as fichier:
        # Écrire le nombre total de diapositives
        fichier.write(f"{len(diapositives)}\n")

        # Écrire les diapositives dans l'ordre des transitions
        diapositives_utilisees = set()  # Pour éviter les doublons
        for i, j in ordre:
            diapo_i = diapositives[i]
            diapo_j = diapositives[j]

            # Écrire la diapositive i si elle n'a pas déjà été écrite
            if i not in diapositives_utilisees:
                fichier.write(" ".join(map(str, diapo_i["ids"])) + "\n")
                diapositives_utilisees.add(i)

            # Écrire la diapositive j si elle n'a pas déjà été écrite
            if j not in diapositives_utilisees:
                fichier.write(" ".join(map(str, diapo_j["ids"])) + "\n")
                diapositives_utilisees.add(j)
                
def calculer_score_diaporama(diapositives, ordre):
    """
    Calculer le score total du diaporama en fonction de l'ordre des diapositives.
    """
    score_total = 0

    for i, j in ordre:
        # Obtenir les étiquettes des diapositives i et j
        etiquettes1 = diapositives[i]["etiquettes"]
        etiquettes2 = diapositives[j]["etiquettes"]

        # Calculer le facteur d'intérêt entre les deux diapositives
        facteur_interet = calculer_facteur_interet(etiquettes1, etiquettes2)
        score_total += facteur_interet

        # Afficher les détails de la transition
        print(f"Transition {i} -> {j} :")
        print(f"  Diapositive {i} : {diapositives[i]['ids']} (étiquettes : {etiquettes1})")
        print(f"  Diapositive {j} : {diapositives[j]['ids']} (étiquettes : {etiquettes2})")
        print(f"  Facteur d'intérêt : {facteur_interet}")
        print(f"  Score total accumulé : {score_total}")
        print("-" * 40)

    return score_total

def principal():
    if len(sys.argv) != 2:
        print("Lancement: python slideshow.py <fichier_donnee>")
        sys.exit(1)

    fichier_entree = sys.argv[1]
    fichier_sortie = "slideshow2.sol"

    try:
        photos_horizontales, photos_verticales = lire_fichier_entree(fichier_entree)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        sys.exit(1)

    diapositives = []
    diapositives.extend([{ "ids": [photo["id"]], "sens": [photo["sens"]], "etiquettes": photo["etiquettes"] } for photo in photos_horizontales])
    diapositives.extend(combiner_photos_verticales_optimise(photos_verticales))

    ordre = optimiser_diaporama(diapositives)
   
    # Calculer le score en fonction de l'ordre final
    score = calculer_score_diaporama(diapositives, ordre)
    print(f"\n **Score total du diaporama : {score}**")

    ecrire_fichier_sortie(fichier_sortie, ordre, diapositives)
    print(f"Diaporama généré dans le fichier : {fichier_sortie}")

if __name__ == "__main__":
    principal()