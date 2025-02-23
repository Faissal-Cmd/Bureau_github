def calculer_facteur_interet(etiquettes1, etiquettes2):
    """
    Calculer le facteur d'intérêt entre deux ensembles d'étiquettes.
    """
    etiquettes_communes = len(etiquettes1.intersection(etiquettes2))
    etiquettes_uniques_1 = len(etiquettes1 - etiquettes2)
    etiquettes_uniques_2 = len(etiquettes2 - etiquettes1)
    return min(etiquettes_communes, etiquettes_uniques_1, etiquettes_uniques_2)

def lire_fichier_entree(fichier_entree):
    """
    Lire le fichier d'entrée et organiser les photos en horizontales ou verticales.
    """
    with open(fichier_entree, "r") as fichier:
        lignes = fichier.read().strip().split("\n")

    N = int(lignes[0])  # Nombre de photos
    photos = []

    for i in range(1, N + 1):
        donnees = lignes[i].split()
        orientation = donnees[0]
        etiquettes = set(donnees[2:])
        photos.append({"id": i - 1, "sens": orientation, "etiquettes": etiquettes})

    return photos

def lire_fichier_solution(fichier_solution):
    """
    Lire le fichier de solution et retourner l'ordre des diapositives.
    """
    with open(fichier_solution, "r") as fichier:
        lignes = fichier.read().strip().split("\n")

    # La première ligne est le nombre de diapositives
    S = int(lignes[0])

    # Les lignes suivantes décrivent les diapositives
    diapositives = []
    for ligne in lignes[1:]:
        ids = list(map(int, ligne.split()))
        diapositives.append(ids)

    return diapositives

def calculer_score_diaporama(photos, diapositives):
    """
    Calculer le score total du diaporama en fonction de l'ordre des diapositives.
    """
    score_total = 0

    for i in range(len(diapositives) - 1):
        # Obtenir les étiquettes des diapositives i et i+1
        diapo1 = diapositives[i]
        diapo2 = diapositives[i + 1]

        # Si la diapositive contient une seule photo (horizontale)
        if len(diapo1) == 1:
            etiquettes1 = photos[diapo1[0]]["etiquettes"]
        else:
            # Si la diapositive contient deux photos (verticales)
            etiquettes1 = photos[diapo1[0]]["etiquettes"].union(photos[diapo1[1]]["etiquettes"])

        if len(diapo2) == 1:
            etiquettes2 = photos[diapo2[0]]["etiquettes"]
        else:
            etiquettes2 = photos[diapo2[0]]["etiquettes"].union(photos[diapo2[1]]["etiquettes"])

        # Calculer le facteur d'intérêt entre les deux diapositives
        score_transition = calculer_facteur_interet(etiquettes1, etiquettes2)
        score_total += score_transition
        print(f"Transition {i} -> {i + 1} : {score_transition}")

    return score_total

def principal(fichier_entree, fichier_solution):
    """
    Fonction principale pour calculer le score d'un diaporama.
    """
    # Lire les photos à partir du fichier d'entrée
    photos = lire_fichier_entree(fichier_entree)

    # Lire l'ordre des diapositives à partir du fichier de solution
    diapositives = lire_fichier_solution(fichier_solution)
    print(diapositives)
    # Calculer le score du diaporama
    score = calculer_score_diaporama(photos, diapositives)
    print(f"\n🎯 **Score total du diaporama : {score}**")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Utilisation: python verify.py <fichier_entree> <fichier_solution>")
        sys.exit(1)

    fichier_entree = sys.argv[1]
    fichier_solution = sys.argv[2]

    principal(fichier_entree, fichier_solution)