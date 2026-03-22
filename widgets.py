import tkinter as tk


class BarreNavigation(tk.Frame):

    #Barre de navigation réutilisable pour toutes les pages.
    def __init__(self, parent, titre_page: str, master_app):
        super().__init__(parent, bg="#1B4332", pady=10)

        # ── Bouton retour ──
        btn_retour = tk.Button(
            self,
            text="← Dashboard",
            font=("Helvetica", 10),
            bg="#2D6A4F", fg="white",
            relief="flat",
            padx=14, pady=6,
            cursor="hand2",
            activebackground="#52B788",
            activeforeground="white",
            command=lambda: master_app.afficher_frame("dashboard")
        )
        btn_retour.pack(side="left", padx=16)

        btn_retour.bind("<Enter>", lambda e: btn_retour.config(bg="#52B788"))
        btn_retour.bind("<Leave>", lambda e: btn_retour.config(bg="#2D6A4F"))

        # ── Titre de la page ──
        tk.Label(
            self,
            text=titre_page,
            font=("Helvetica", 14, "bold"),
            bg="#1B4332", fg="white"
        ).pack(side="left", padx=16)

        # ── Nom utilisateur à droite ──
        nom = getattr(master_app, "agriculteur_nom", "")
        tk.Label(
            self,
            text=f"Connecté : {nom}",
            font=("Helvetica", 9),
            bg="#1B4332", fg="#9FE1CB"
        ).pack(side="right", padx=16)