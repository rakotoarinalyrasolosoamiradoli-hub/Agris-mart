import tkinter as tk
from tkinter import ttk
from database import get_connection
from widgets import BarreNavigation


# ═══════════════════════════════════════════════════════
# FONCTIONS DB
# ═══════════════════════════════════════════════════════

def stats_generales(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()

        # Nombre de parcelles
        c.execute("""
            SELECT COUNT(*) AS total
            FROM parcelles
            WHERE agriculteur_id = ?
        """, (agriculteur_id,))
        nb_parcelles = c.fetchone()["total"]

        # Nombre de cultures actives
        c.execute("""
            SELECT COUNT(*) AS total
            FROM cultures cu
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
            AND cu.statut = 'en cours'
        """, (agriculteur_id,))
        nb_cultures = c.fetchone()["total"]

        # Total récoltes en kg
        c.execute("""
            SELECT COALESCE(SUM(re.quantite_obtenue), 0) AS total
            FROM recoltes re
            JOIN cultures cu ON re.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_recoltes = c.fetchone()["total"]

        # Total revenus ventes
        c.execute("""
            SELECT COALESCE(SUM(ve.quantite_vendue * ve.prix_unitaire), 0)
            AS total
            FROM ventes ve
            JOIN recoltes re ON ve.recolte_id = re.id
            JOIN cultures cu ON re.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_revenus = c.fetchone()["total"]

        # Total dépenses
        c.execute("""
            SELECT COALESCE(SUM(de.montant), 0) AS total
            FROM depenses de
            JOIN cultures cu ON de.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_depenses = c.fetchone()["total"]

        return {
            "nb_parcelles":   nb_parcelles,
            "nb_cultures":    nb_cultures,
            "total_recoltes": total_recoltes,
            "total_revenus":  total_revenus,
            "total_depenses": total_depenses,
            "benefice":       total_revenus - total_depenses,
        }
    finally:
        conn.close()


def bilan_par_culture(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                pr.nom                                          AS produit,
                pa.nom                                          AS parcelle,
                cu.date_debut,
                cu.statut,
                COALESCE(SUM(DISTINCT re.quantite_obtenue), 0) AS total_recolte,
                COALESCE(
                    SUM(ve.quantite_vendue * ve.prix_unitaire), 0
                )                                               AS total_revenus,
                COALESCE(SUM(DISTINCT de.montant), 0)           AS total_depenses
            FROM cultures cu
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            JOIN produits  pr ON cu.produit_id  = pr.id
            LEFT JOIN recoltes re ON re.culture_id = cu.id
            LEFT JOIN ventes   ve ON ve.recolte_id = re.id
            LEFT JOIN depenses de ON de.culture_id = cu.id
            WHERE pa.agriculteur_id = ?
            GROUP BY cu.id
            ORDER BY cu.date_debut DESC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def bilan_par_parcelle(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                pa.nom                                        AS parcelle,
                pa.region,
                pa.surface_ha,
                COUNT(DISTINCT cu.id)                         AS nb_cultures,
                COALESCE(SUM(re.quantite_obtenue), 0)         AS total_recolte,
                COALESCE(
                    SUM(ve.quantite_vendue * ve.prix_unitaire), 0
                )                                             AS total_revenus,
                COALESCE(SUM(de.montant), 0)                  AS total_depenses
            FROM parcelles pa
            LEFT JOIN cultures  cu ON cu.parcelle_id = pa.id
            LEFT JOIN recoltes  re ON re.culture_id  = cu.id
            LEFT JOIN ventes    ve ON ve.recolte_id  = re.id
            LEFT JOIN depenses  de ON de.culture_id  = cu.id
            WHERE pa.agriculteur_id = ?
            GROUP BY pa.id
            ORDER BY pa.nom ASC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
# PAGE ANALYSE
# ═══════════════════════════════════════════════════════

class AnalysePage(tk.Frame):

    def __init__(self, master, agriculteur_id):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id = agriculteur_id
        self._construire_interface()
        self._charger_donnees()

    def _construire_interface(self):
        BarreNavigation(self, "Analyses & Bilans", self.master).pack(fill="x")

        # Onglets
        self.onglets = ttk.Notebook(self)
        self.onglets.pack(fill="both", expand=True, padx=16, pady=12)

        self.tab_general  = tk.Frame(self.onglets, bg="#F0F4F0")
        self.tab_culture  = tk.Frame(self.onglets, bg="#F0F4F0")
        self.tab_parcelle = tk.Frame(self.onglets, bg="#F0F4F0")

        self.onglets.add(self.tab_general,  text="  Vue générale  ")
        self.onglets.add(self.tab_culture,  text="  Par culture   ")
        self.onglets.add(self.tab_parcelle, text="  Par parcelle  ")

        self._construire_tab_general()
        self._construire_tab_culture()
        self._construire_tab_parcelle()

    def _construire_tab_general(self):
        p = self.tab_general

        tk.Label(p, text="Tableau de bord",
                 font=("Helvetica", 14, "bold"),
                 bg="#F0F4F0", fg="#1B4332").pack(pady=(16, 12))

        # Grille de cartes
        grille = tk.Frame(p, bg="#F0F4F0")
        grille.pack(padx=20)

        self.cartes = {}
        infos = [
            ("nb_parcelles",   "Parcelles",         "#2D6A4F"),
            ("nb_cultures",    "Cultures actives",   "#1565C0"),
            ("total_recoltes", "Récoltes (kg)",      "#E65100"),
            ("total_revenus",  "Revenus (Ar)",       "#2E7D32"),
            ("total_depenses", "Dépenses (Ar)",      "#C62828"),
            ("benefice",       "Bénéfice net (Ar)",  "#6A1B9A"),
        ]

        for i, (cle, titre, couleur) in enumerate(infos):
            ligne = i // 3
            col   = i % 3

            carte = tk.Frame(grille, bg=couleur,
                             padx=24, pady=16, width=180)
            carte.grid(row=ligne, column=col, padx=8, pady=8)
            carte.grid_propagate(False)

            tk.Label(carte, text=titre,
                     font=("Helvetica", 9),
                     bg=couleur, fg="white").pack()

            lbl_val = tk.Label(carte, text="—",
                               font=("Helvetica", 18, "bold"),
                               bg=couleur, fg="white")
            lbl_val.pack(pady=(4, 0))

            self.cartes[cle] = lbl_val

    def _construire_tab_culture(self):
        cadre = tk.Frame(self.tab_culture, bg="#F0F4F0")
        cadre.pack(fill="both", expand=True, padx=12, pady=12)

        colonnes = [
            ("produit",        120, "Produit"),
            ("parcelle",       120, "Parcelle"),
            ("date_debut",     100, "Début"),
            ("statut",          90, "Statut"),
            ("total_recolte",  110, "Récolte (kg)"),
            ("total_revenus",  120, "Revenus (Ar)"),
            ("total_depenses", 120, "Dépenses (Ar)"),
            ("benefice",       120, "Bénéfice (Ar)"),
        ]

        self.tableau_culture = ttk.Treeview(
            cadre,
            columns=[col[0] for col in colonnes],
            show="headings",
            selectmode="browse"
        )
        for col_id, largeur, titre in colonnes:
            self.tableau_culture.heading(col_id, text=titre, anchor="w")
            self.tableau_culture.column(col_id, width=largeur,
                                        anchor="w", minwidth=60)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau_culture.yview)
        self.tableau_culture.configure(yscrollcommand=scrollbar.set)
        self.tableau_culture.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tags couleur bénéfice
        self.tableau_culture.tag_configure("positif", background="#E8F5E9")
        self.tableau_culture.tag_configure("negatif", background="#FFEBEE")

    def _construire_tab_parcelle(self):
        cadre = tk.Frame(self.tab_parcelle, bg="#F0F4F0")
        cadre.pack(fill="both", expand=True, padx=12, pady=12)

        colonnes = [
            ("parcelle",       130, "Parcelle"),
            ("region",         120, "Région"),
            ("surface_ha",      80, "Surface"),
            ("nb_cultures",     80, "Cultures"),
            ("total_recolte",  110, "Récolte (kg)"),
            ("total_revenus",  120, "Revenus (Ar)"),
            ("total_depenses", 120, "Dépenses (Ar)"),
            ("benefice",       120, "Bénéfice (Ar)"),
        ]

        self.tableau_parcelle = ttk.Treeview(
            cadre,
            columns=[col[0] for col in colonnes],
            show="headings",
            selectmode="browse"
        )
        for col_id, largeur, titre in colonnes:
            self.tableau_parcelle.heading(col_id, text=titre, anchor="w")
            self.tableau_parcelle.column(col_id, width=largeur,
                                         anchor="w", minwidth=60)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau_parcelle.yview)
        self.tableau_parcelle.configure(yscrollcommand=scrollbar.set)
        self.tableau_parcelle.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tableau_parcelle.tag_configure("positif", background="#E8F5E9")
        self.tableau_parcelle.tag_configure("negatif", background="#FFEBEE")

    def _charger_donnees(self):
        self._charger_general()
        self._charger_culture()
        self._charger_parcelle()

    def _charger_general(self):
        stats = stats_generales(self.agriculteur_id)

        self.cartes["nb_parcelles"].config(
            text=str(stats["nb_parcelles"]))
        self.cartes["nb_cultures"].config(
            text=str(stats["nb_cultures"]))
        self.cartes["total_recoltes"].config(
            text=f"{stats['total_recoltes']:,.1f}")
        self.cartes["total_revenus"].config(
            text=f"{stats['total_revenus']:,.0f}")
        self.cartes["total_depenses"].config(
            text=f"{stats['total_depenses']:,.0f}")

        benefice = stats["benefice"]
        self.cartes["benefice"].config(
            text=f"{benefice:,.0f}",
            fg="#AAFFAA" if benefice >= 0 else "#FFAAAA"
        )

    def _charger_culture(self):
        for ligne in self.tableau_culture.get_children():
            self.tableau_culture.delete(ligne)

        bilans = bilan_par_culture(self.agriculteur_id)

        for b in bilans:
            benefice = b["total_revenus"] - b["total_depenses"]
            tag = "positif" if benefice >= 0 else "negatif"
            self.tableau_culture.insert("", "end", values=(
                b["produit"],
                b["parcelle"],
                b["date_debut"],
                b["statut"],
                f"{b['total_recolte']:,.1f}",
                f"{b['total_revenus']:,.0f}",
                f"{b['total_depenses']:,.0f}",
                f"{benefice:,.0f}",
            ), tags=(tag,))

        if not bilans:
            self.tableau_culture.insert("", "end",
                                        values=("Aucune donnée",
                                                "", "", "", "", "", "", ""))

    def _charger_parcelle(self):
        for ligne in self.tableau_parcelle.get_children():
            self.tableau_parcelle.delete(ligne)

        bilans = bilan_par_parcelle(self.agriculteur_id)

        for b in bilans:
            benefice = b["total_revenus"] - b["total_depenses"]
            tag = "positif" if benefice >= 0 else "negatif"
            self.tableau_parcelle.insert("", "end", values=(
                b["parcelle"],
                b["region"] or "—",
                f"{b['surface_ha']} ha",
                b["nb_cultures"],
                f"{b['total_recolte']:,.1f}",
                f"{b['total_revenus']:,.0f}",
                f"{b['total_depenses']:,.0f}",
                f"{benefice:,.0f}",
            ), tags=(tag,))

        if not bilans:
            self.tableau_parcelle.insert("", "end",
                                         values=("Aucune donnée",
                                                 "", "", "", "", "", "", ""))