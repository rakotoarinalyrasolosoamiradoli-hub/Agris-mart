import tkinter as tk
from tkinter import ttk
import os
from database import get_connection


# ── Statistiques rapides ─────────────────────────────────

def stats_rapides(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM parcelles WHERE agriculteur_id = ?",
                  (agriculteur_id,))
        nb_parcelles = c.fetchone()[0]

        c.execute("""
            SELECT COUNT(*) FROM cultures cu
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ? AND cu.statut = 'en cours'
        """, (agriculteur_id,))
        nb_cultures = c.fetchone()[0]

        c.execute("""
            SELECT COALESCE(SUM(ve.quantite_vendue * ve.prix_unitaire), 0)
            FROM ventes ve
            JOIN recoltes re ON ve.recolte_id = re.id
            JOIN cultures cu ON re.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_revenus = c.fetchone()[0]

        c.execute("""
            SELECT COALESCE(SUM(re.quantite_obtenue), 0)
            FROM recoltes re
            JOIN cultures cu ON re.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_recoltes = c.fetchone()[0]

        c.execute("""
            SELECT COALESCE(SUM(de.montant), 0)
            FROM depenses de
            JOIN cultures cu ON de.culture_id = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            WHERE pa.agriculteur_id = ?
        """, (agriculteur_id,))
        total_depenses = c.fetchone()[0]

        return {
            "nb_parcelles":   nb_parcelles,
            "nb_cultures":    nb_cultures,
            "total_revenus":  total_revenus,
            "total_recoltes": total_recoltes,
            "total_depenses": total_depenses,
            "benefice":       total_revenus - total_depenses,
        }
    finally:
        conn.close()


#Dashboard 

class DashboardFrame(tk.Frame):

    def __init__(self, master, agriculteur_id, agriculteur_nom):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id  = agriculteur_id
        self.agriculteur_nom = agriculteur_nom

        self.logo_ispm = None
        self._charger_logo()
        self._construire_interface()

    def _charger_logo(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chemin   = os.path.join(base_dir, "logo_ispm.png")
        if not os.path.exists(chemin):
            return
        try:
            img     = tk.PhotoImage(file=chemin)
            facteur = max(1, min(img.width(), img.height()) // 40)
            self.logo_ispm = img.subsample(facteur, facteur)
        except Exception as e:
            print(f"[Dashboard] Logo : {e}")

    def _construire_interface(self):

        # BARRE SUPÉRIEURE
        topbar = tk.Frame(self, bg="#1B4332", height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # Logo + nom app à gauche
        gauche = tk.Frame(topbar, bg="#1B4332")
        gauche.pack(side="left", padx=20)

        tk.Label(gauche, text="Agri-Smart",
                 font=("Helvetica", 18, "bold"),
                 bg="#1B4332", fg="white").pack(side="left")

        tk.Label(gauche, text="  |  Gestion agricole intelligente",
                 font=("Helvetica", 10),
                 bg="#1B4332", fg="#9FE1CB").pack(side="left")

        # Logo ISPM + nom utilisateur à droite
        droite = tk.Frame(topbar, bg="#1B4332")
        droite.pack(side="right", padx=20)

        if self.logo_ispm:
            tk.Label(droite, image=self.logo_ispm,
                     bg="#1B4332").pack(side="right", padx=(8, 0))

        cadre_user = tk.Frame(droite, bg="#1B4332")
        cadre_user.pack(side="right")

        tk.Label(cadre_user,
                 text=self.agriculteur_nom,
                 font=("Helvetica", 11, "bold"),
                 bg="#1B4332", fg="white").pack(anchor="e")

        tk.Label(cadre_user,
                 text="Agriculteur connecté",
                 font=("Helvetica", 8),
                 bg="#1B4332", fg="#9FE1CB").pack(anchor="e")

        # CORPS PRINCIPAL
        corps = tk.Frame(self, bg="#F0F4F0")
        corps.pack(fill="both", expand=True)

        # ── Sidebar gauche ──
        self._construire_sidebar(corps)

        # ── Contenu principal ──
        self._construire_contenu(corps)

    def _construire_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg="#1B4332", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg="#2D6A4F", height=1).pack(
            fill="x", padx=16, pady=(16, 0))

        menus = [
            ("Parcelles", "parcelle", "#52B788"),
            ("Cultures",  "culture",  "#52B788"),
            ("Dépenses",  "depense",  "#52B788"),
            ("Récoltes",  "recolte",  "#52B788"),
            ("Ventes",    "vente",    "#52B788"),
            ("Analyses",  "analyse",  "#52B788"),
        ]

        tk.Label(sidebar, text="NAVIGATION",
                 font=("Helvetica", 8, "bold"),
                 bg="#1B4332", fg="#52B788").pack(
            anchor="w", padx=20, pady=(12, 4))

        for texte, frame_nom, _ in menus:
            self._bouton_sidebar(sidebar, texte, frame_nom)

        # Déconnexion
        tk.Frame(sidebar, bg="#2D6A4F", height=1).pack(
            fill="x", padx=16, side="bottom", pady=(0, 12))

        tk.Button(
            sidebar,
            text="Déconnexion",
            font=("Helvetica", 10),
            bg="#C62828", fg="white",
            relief="flat", pady=10,
            cursor="hand2",
            activebackground="#B71C1C",
            command=self.master.deconnecter
        ).pack(side="bottom", fill="x", padx=16, pady=(0, 8))

    def _bouton_sidebar(self, parent, texte, frame_nom):
        cadre = tk.Frame(parent, bg="#1B4332")
        cadre.pack(fill="x", pady=1)

        indicateur = tk.Frame(cadre, bg="#1B4332", width=4)
        indicateur.pack(side="left", fill="y")

        btn = tk.Button(
            cadre,
            text=texte,
            font=("Helvetica", 11),
            bg="#1B4332", fg="#D8F3DC",
            relief="flat",
            pady=11, padx=16,
            anchor="w",
            cursor="hand2",
            activebackground="#2D6A4F",
            activeforeground="white",
            command=lambda: self.master.afficher_frame(frame_nom)
        )
        btn.pack(fill="x")

        def on_enter(e):
            btn.config(bg="#2D6A4F", fg="white")
            indicateur.config(bg="#52B788")

        def on_leave(e):
            btn.config(bg="#1B4332", fg="#D8F3DC")
            indicateur.config(bg="#1B4332")

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        cadre.bind("<Enter>", on_enter)
        cadre.bind("<Leave>", on_leave)

    def _construire_contenu(self, parent):
        contenu = tk.Frame(parent, bg="#F0F4F0")
        contenu.pack(side="right", fill="both", expand=True)

        # Scrollable
        canvas = tk.Canvas(contenu, bg="#F0F4F0",
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenu, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#F0F4F0")
        fenetre_canvas = canvas.create_window(
            (0, 0), window=inner, anchor="nw"
        )

        def on_resize(e):
            canvas.itemconfig(fenetre_canvas, width=e.width)
        canvas.bind("<Configure>", on_resize)

        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))

        # ── Titre de bienvenue ──
        entete = tk.Frame(inner, bg="#F0F4F0")
        entete.pack(fill="x", padx=24, pady=(24, 0))

        tk.Label(entete,
                 text=f"Bonjour, {self.agriculteur_nom.split()[0]} !",
                 font=("Helvetica", 22, "bold"),
                 bg="#F0F4F0", fg="#1B4332").pack(anchor="w")

        tk.Label(entete,
                 text="Voici le résumé de votre exploitation agricole",
                 font=("Helvetica", 11),
                 bg="#F0F4F0", fg="#888888").pack(anchor="w", pady=(2, 0))

        # Ligne séparatrice
        tk.Frame(inner, bg="#D8F3DC", height=2).pack(
            fill="x", padx=24, pady=12)

        # ── Cartes statistiques ──
        self._construire_cartes_stats(inner)

        # ── Séparateur ──
        tk.Frame(inner, bg="#D8F3DC", height=2).pack(
            fill="x", padx=24, pady=12)

        # ── Accès rapide ──
        self._construire_acces_rapide(inner)

        # ── Footer ──
        tk.Label(inner,
                 text="AgriSmart © 2025 — ISPM  |  Aide à la décision pour petit agriculteur",
                 font=("Helvetica", 8),
                 bg="#F0F4F0", fg="#AAAAAA").pack(pady=(24, 16))

    def _construire_cartes_stats(self, parent):
        tk.Label(parent, text="Vue d'ensemble",
                 font=("Helvetica", 13, "bold"),
                 bg="#F0F4F0", fg="#1B4332").pack(
            anchor="w", padx=24, pady=(0, 10))

        grille = tk.Frame(parent, bg="#F0F4F0")
        grille.pack(fill="x", padx=24)

        stats = stats_rapides(self.agriculteur_id)

        cartes = [
            ("Parcelles",       str(stats["nb_parcelles"]),
             "#2D6A4F", "terrain(s) enregistré(s)"),
            ("Cultures actives", str(stats["nb_cultures"]),
             "#1565C0", "culture(s) en cours"),
            ("Récoltes (kg)",   f"{stats['total_recoltes']:,.1f}",
             "#E65100", "kg récoltés au total"),
            ("Revenus",         f"{stats['total_revenus']:,.0f} Ar",
             "#2E7D32", "Ariary de revenus"),
            ("Dépenses",        f"{stats['total_depenses']:,.0f} Ar",
             "#C62828", "Ariary de dépenses"),
            ("Bénéfice net",    f"{stats['benefice']:,.0f} Ar",
             "#6A1B9A" if stats["benefice"] >= 0 else "#C62828",
             "Ariary de bénéfice"),
        ]

        for i, (titre, valeur, couleur, sous_titre) in enumerate(cartes):
            col = i % 3
            row = i // 3

            carte = tk.Frame(grille, bg="white",
                             relief="flat", bd=0)
            carte.grid(row=row, column=col,
                       padx=8, pady=8, sticky="ew")
            grille.columnconfigure(col, weight=1)

            # Bande colorée gauche
            tk.Frame(carte, bg=couleur, width=6).pack(
                side="left", fill="y")

            contenu = tk.Frame(carte, bg="white",
                               padx=16, pady=14)
            contenu.pack(side="left", fill="both", expand=True)

            tk.Label(contenu, text=titre,
                     font=("Helvetica", 9, "bold"),
                     bg="white", fg="#888888").pack(anchor="w")

            tk.Label(contenu, text=valeur,
                     font=("Helvetica", 20, "bold"),
                     bg="white", fg=couleur).pack(anchor="w")

            tk.Label(contenu, text=sous_titre,
                     font=("Helvetica", 8),
                     bg="white", fg="#AAAAAA").pack(anchor="w")

    def _construire_acces_rapide(self, parent):
        tk.Label(parent, text="Accès rapide",
                 font=("Helvetica", 13, "bold"),
                 bg="#F0F4F0", fg="#1B4332").pack(
            anchor="w", padx=24, pady=(0, 10))

        grille = tk.Frame(parent, bg="#F0F4F0")
        grille.pack(fill="x", padx=24, pady=(0, 8))

        actions = [
            ("+ Nouvelle parcelle", "parcelle", "#2D6A4F"),
            ("+ Nouvelle culture",  "culture",  "#1565C0"),
            ("+ Enregistrer dépense","depense", "#C62828"),
            ("+ Enregistrer récolte","recolte", "#E65100"),
            ("+ Enregistrer vente",  "vente",   "#6A1B9A"),
            ("  Voir analyses",      "analyse", "#00695C"),
        ]

        for i, (texte, frame_nom, couleur) in enumerate(actions):
            col = i % 3
            row = i // 3

            btn = tk.Button(
                grille,
                text=texte,
                font=("Helvetica", 10, "bold"),
                bg=couleur, fg="white",
                relief="flat",
                pady=14, padx=10,
                cursor="hand2",
                activebackground="#1B4332",
                activeforeground="white",
                command=lambda f=frame_nom: self.master.afficher_frame(f)
            )
            btn.grid(row=row, column=col,
                     padx=8, pady=6, sticky="ew")
            grille.columnconfigure(col, weight=1)

            btn.bind("<Enter>", lambda e, b=btn, c=couleur: b.config(
                bg=self._assombrir(c)))
            btn.bind("<Leave>", lambda e, b=btn, c=couleur: b.config(bg=c))

    def _assombrir(self, couleur_hex):
        """Assombrit légèrement une couleur hex pour l'effet hover."""
        r = int(couleur_hex[1:3], 16)
        g = int(couleur_hex[3:5], 16)
        b = int(couleur_hex[5:7], 16)
        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"