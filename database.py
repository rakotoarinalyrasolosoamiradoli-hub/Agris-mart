import sqlite3

DB_PATH = "agrismart.db"

def get_connection() :
    """Retourne une connexion avec les clés étrangères activées"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialiser_base() :
    """Crée toutes les tables de la BD"""
    conn = get_connection()
    conn.executescript("""

         CREATE TABLE IF NOT EXISTS agriculteurs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nom          TEXT NOT NULL UNIQUE,
            prenom       TEXT NOT NULL,
            contact      TEXT,
            localisation TEXT,
            mot_de_passe TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parcelles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            agriculteur_id  INTEGER NOT NULL,
            nom             TEXT NOT NULL,
            surface_ha      REAL NOT NULL,
            type_sol        TEXT,
            region          TEXT,
            coordonnees_gps TEXT,
            FOREIGN KEY (agriculteur_id) REFERENCES agriculteurs(id)
        );

        CREATE TABLE IF NOT EXISTS produits (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nom       TEXT NOT NULL UNIQUE,
            unite     TEXT NOT NULL DEFAULT 'kg',
            categorie TEXT NOT NULL DEFAULT 'Autres'
        );

        CREATE TABLE IF NOT EXISTS cultures (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            parcelle_id     INTEGER NOT NULL,
            produit_id      INTEGER NOT NULL,
            date_debut      TEXT NOT NULL,
            date_fin_prevue TEXT,
            statut          TEXT NOT NULL DEFAULT 'en cours',
            FOREIGN KEY (parcelle_id) REFERENCES parcelles(id),
            FOREIGN KEY (produit_id)  REFERENCES produits(id)
        );

        CREATE TABLE IF NOT EXISTS intrants (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nom   TEXT NOT NULL UNIQUE,
            type  TEXT NOT NULL,
            unite TEXT NOT NULL DEFAULT 'kg'
        );

        CREATE TABLE IF NOT EXISTS culture_intrants (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id        INTEGER NOT NULL,
            intrant_id        INTEGER NOT NULL,
            quantite_utilisee REAL NOT NULL,
            date_utilisation  TEXT NOT NULL,
            FOREIGN KEY (culture_id) REFERENCES cultures(id),
            FOREIGN KEY (intrant_id) REFERENCES intrants(id)
        );

        CREATE TABLE IF NOT EXISTS recoltes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id       INTEGER NOT NULL,
            quantite_obtenue REAL NOT NULL,
            date_recolte     TEXT NOT NULL,
            unite            TEXT NOT NULL DEFAULT 'kg',
            FOREIGN KEY (culture_id) REFERENCES cultures(id)
        );

        CREATE TABLE IF NOT EXISTS ventes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            recolte_id      INTEGER NOT NULL,
            acheteur        TEXT NOT NULL,
            quantite_vendue REAL NOT NULL,
            prix_unitaire   REAL NOT NULL,
            date_vente      TEXT NOT NULL,
            FOREIGN KEY (recolte_id) REFERENCES recoltes(id)
        );
        CREATE TABLE IF NOT EXISTS depenses (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            culture_id   INTEGER NOT NULL,
            libelle      TEXT NOT NULL,
            categorie    TEXT NOT NULL DEFAULT 'Autre',
            montant      REAL NOT NULL,
            date_depense TEXT NOT NULL,
            FOREIGN KEY (culture_id) REFERENCES cultures(id)
        );

    """)  

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès")

def inserer_produits_defaut():
    """
    Pré-remplit le référentiel produits basé sur la
    Carte Agricole de Madagascar (Ministère Agriculture, Mars 2023).
    Organisé par catégorie via le champ 'unite'.
    """

    # Structure : (nom, unite, categorie)
    produits = [
        # ── Céréales & légumineuses ──
        ("Riz",          "kg", "Céréales"),
        ("Maïs",         "kg", "Céréales"),
        ("Sorgho",       "kg", "Céréales"),
        ("Blé",          "kg", "Céréales"),
        ("Haricot",      "kg", "Légumineuses"),
        ("Pois du Cap",  "kg", "Légumineuses"),
        ("Soja",         "kg", "Légumineuses"),
        ("Black Eyes",   "kg", "Légumineuses"),
        ("Arachide",     "kg", "Légumineuses"),

        # ── Tubercules ──
        ("Manioc",       "kg", "Tubercules"),
        ("Patate douce", "kg", "Tubercules"),
        ("Pomme de terre","kg","Tubercules"),

        # ── Fruits ──
        ("Mangue",       "kg", "Fruits"),
        ("Agrume",       "kg", "Fruits"),
        ("Letchi",       "kg", "Fruits"),
        ("Pomme",        "kg", "Fruits"),
        ("Fraise",       "kg", "Fruits"),
        ("Banane",       "kg", "Fruits"),

        # ── Cultures de rente ──
        ("Vanille",      "kg", "Rente"),
        ("Girofle",      "kg", "Rente"),
        ("Café",         "kg", "Rente"),
        ("Cacao",        "kg", "Rente"),
        ("Coton",        "kg", "Rente"),
        ("Canne à sucre","tonne","Rente"),
        ("Poivre",       "kg", "Rente"),
        ("Baie rose",    "kg", "Rente"),

        # ── Maraîchers ──
        ("Oignon",       "kg", "Maraîchers"),
        ("Tomate",       "kg", "Maraîchers"),
        ("Carotte",      "kg", "Maraîchers"),
        ("Culture maraîchère", "kg", "Maraîchers"),

        # ── Élevage ──
        ("Bovin",        "tête", "Élevage"),
        ("Porcin",       "tête", "Élevage"),
        ("Volaille",     "tête", "Élevage"),
        ("Poulet gasy",  "tête", "Élevage"),
        ("Poule pondeuse","tête","Élevage"),
        ("Petit ruminant","tête","Élevage"),
        ("Vache laitière","tête","Élevage"),
        ("Miel",         "kg",  "Élevage"),
    ]

    conn = get_connection()
    try:
        c = conn.cursor()
        c.executemany(
            """INSERT OR IGNORE INTO produits (nom, unite, categorie)
               VALUES (?, ?, ?)""",
            produits
        )
        conn.commit()
        print(f"✓ {len(produits)} produits malgaches insérés.")
    finally:
        conn.close()

def inserer_intrants_defaut():
    """Intrants adaptés à l'agriculture malgache."""
    intrants = [
        # Engrais
        ("NPK 11-22-16",         "engrais",   "kg"),
        ("Urée 46%",             "engrais",   "kg"),
        ("DAP",                  "engrais",   "kg"),
        ("Fumier organique",     "engrais",   "kg"),
        ("Compost",              "engrais",   "kg"),

        # Semences certifiées par culture
        ("Semences riz SEBOTA",  "semence",   "kg"),
        ("Semences maïs hybride","semence",   "kg"),
        ("Boutures manioc",      "semence",   "unité"),
        ("Semences arachide",    "semence",   "kg"),
        ("Plants vanille",       "semence",   "plant"),
        ("Plants café",          "semence",   "plant"),
        ("Plants girofle",       "semence",   "plant"),

        # Pesticides
        ("Herbicide (riz)",      "pesticide", "L"),
        ("Insecticide acridien", "pesticide", "L"),
        ("Fongicide",            "pesticide", "kg"),
        ("Nématicide",           "pesticide", "L"),

        # Matériel
        ("Irrigation (eau)",     "autre",     "m3"),
        ("Main d'oeuvre",        "autre",     "jour"),
    ]

    conn = get_connection()
    try:
        c = conn.cursor()
        c.executemany(
            "INSERT OR IGNORE INTO intrants (nom, type, unite) VALUES (?,?,?)",
            intrants
        )
        conn.commit()
    finally:
        conn.close()