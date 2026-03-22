import tkinter as tk


class DashboardFrame(tk.Frame):
    """
    Écran principal après connexion.
    Barre latérale gauche + zone de contenu à droite.
    """

    def __init__(self, master, agriculteur_id: int, agriculteur_nom: str):
        super().__init__(master, bg="#F0F4F0")

        self.agriculteur_id  = agriculteur_id
        self.agriculteur_nom = agriculteur_nom

        self._construire_interface()

    def _construire_interface(self):

        # ── Barre latérale gauche ──
        barre = tk.Frame(self, bg="#1B4332", width=200)
        barre.pack(side="left", fill="y")
        barre.pack_propagate(False)  # fixe la largeur à 200px

        # Logo texte
        tk.Label(
            barre,
            text="AgriSmart",
            font=("Helvetica", 15, "bold"),
            bg="#1B4332", fg="white"
        ).pack(pady=(24, 4))

        tk.Label(
            barre,
            text="🌿",
            font=("Helvetica", 28),
            bg="#1B4332"
        ).pack(pady=(0, 8))

        # Séparateur
        tk.Frame(barre, bg="#52B788", height=1).pack(fill="x", padx=20)

        # Nom de l'utilisateur connecté
        tk.Label(
            barre,
            text=f"Bonjour,\n{self.agriculteur_nom}",
            font=("Helvetica", 9),
            bg="#1B4332", fg="#9FE1CB",
            justify="center"
        ).pack(pady=12)

        tk.Frame(barre, bg="#2D6A4F", height=1).pack(fill="x", padx=20, pady=(0, 12))

        # ── Boutons de navigation ──
        menus = [
            ("Parcelles", "parcelle"),
            ("Cultures",  "culture"),
            ("Dépenses",  "depense"),
            ("Récoltes",  "recolte"),
            ("Ventes",    "vente"),
            ("Analyses",  "analyse"),
            ]           

        for texte, frame_nom in menus:
            self._bouton_menu(barre, texte, frame_nom)

        # Bouton déconnexion en bas
        tk.Frame(barre, bg="#2D6A4F", height=1).pack(
            fill="x", padx=20, side="bottom", pady=(0, 8)
        )
        tk.Button(
            barre,
            text="Déconnexion",
            font=("Helvetica", 10),
            bg="#C62828", fg="white",
            relief="flat", pady=10,
            cursor="hand2",
            activebackground="#B71C1C",
            activeforeground="white",
            command=self.master.deconnecter
        ).pack(side="bottom", fill="x", padx=12, pady=(0, 12))

        # ── Zone de contenu droite ──
        self.zone_contenu = tk.Frame(self, bg="#F0F4F0")
        self.zone_contenu.pack(side="right", fill="both", expand=True)

        self._afficher_accueil()

    def _bouton_menu(self, parent, texte: str, frame_nom: str):
        """Crée un bouton de navigation dans la barre latérale."""
        btn = tk.Button(
            parent,
            text=texte,
            font=("Helvetica", 11),
            bg="#1B4332", fg="white",
            relief="flat",
            pady=12, padx=20,
            anchor="w",
            cursor="hand2",
            activebackground="#2D6A4F",
            activeforeground="white",
            command=lambda: self.master.afficher_frame(frame_nom)
        )
        btn.pack(fill="x")

        # Effet hover
        btn.bind("<Enter>", lambda e: btn.config(bg="#2D6A4F"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#1B4332"))

    def _afficher_accueil(self):
        """Affiche le message de bienvenue dans la zone de contenu."""

        for widget in self.zone_contenu.winfo_children():
            widget.destroy()

        # Centré verticalement
        cadre = tk.Frame(self.zone_contenu, bg="#F0F4F0")
        cadre.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            cadre,
            text="Bienvenue sur AgriSmart",
            font=("Helvetica", 22, "bold"),
            bg="#F0F4F0", fg="#1B4332"
        ).pack(pady=(0, 8))

        tk.Label(
            cadre,
            text=f"Connecté en tant que : {self.agriculteur_nom}",
            font=("Helvetica", 11),
            bg="#F0F4F0", fg="#555555"
        ).pack(pady=(0, 32))

        # Cartes de navigation rapide
        cartes = tk.Frame(cadre, bg="#F0F4F0")
        cartes.pack()

        infos = [
        ("Parcelles", "#2D6A4F", "parcelle"),
        ("Cultures",  "#1565C0", "culture"),
        ("Dépenses",  "#C62828", "depense"),
        ("Récoltes",  "#E65100", "recolte"),
        ("Ventes",    "#6A1B9A", "vente"),
        ("Analyses",  "#00695C", "analyse"),
            ]

        for texte, couleur, frame_nom in infos:
            carte = tk.Frame(
                cartes, bg=couleur,
                padx=24, pady=18,
                cursor="hand2"
            )
            carte.pack(side="left", padx=8)

            tk.Label(
                carte, text=texte,
                font=("Helvetica", 12, "bold"),
                bg=couleur, fg="white"
            ).pack()

            # Clic sur la carte → naviguer
            carte.bind(
                "<Button-1>",
                lambda e, f=frame_nom: self.master.afficher_frame(f)
            )