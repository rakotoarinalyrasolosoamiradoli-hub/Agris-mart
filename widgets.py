import tkinter as tk


class BarreNavigation(tk.Frame):
    """
    Barre de navigation réutilisable pour toutes les pages.
    Contient : bouton Retour + titre de la page + logo ISPM à droite.
    """

    # Logo chargé une seule fois pour toute l'application
    _logo_cache = None

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

        # ── Logo ISPM à droite ──
        logo = self._charger_logo(master_app)
        if logo:
            tk.Label(
                self,
                image=logo,
                bg="#1B4332"
            ).pack(side="right", padx=16)

    def _charger_logo(self, master_app):
        """
        Charge le logo une seule fois et le met en cache.
        Utilise _logo_cache pour éviter de recharger à chaque page.
        """
        # Si déjà chargé, retourner le cache
        if BarreNavigation._logo_cache is not None:
            return BarreNavigation._logo_cache

        import os

        # Chercher le logo dans le dossier du projet
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chemin   = os.path.join(base_dir, "logo_ispm.png")

        if not os.path.exists(chemin):
            print(f"[BarreNavigation] Logo introuvable : {chemin}")
            return None

        try:
            from PIL import Image, ImageDraw, ImageTk

            img    = Image.open(chemin).convert("RGBA")
            img    = img.resize((45, 45), Image.LANCZOS)

            masque = Image.new("L", (45, 45), 0)
            draw   = ImageDraw.Draw(masque)
            draw.rounded_rectangle((0, 0, 44, 44), radius=12, fill=255)

            resultat = Image.new("RGBA", (45, 45), (0, 0, 0, 0))
            resultat.paste(img, mask=masque)

            BarreNavigation._logo_cache = ImageTk.PhotoImage(resultat)
            return BarreNavigation._logo_cache
        
        except ImportError:
            img     = tk.PhotoImage(file=chemin)
            facteur = max(1, min(img.width(), img.height()) // 45)
            BarreNavigation._logo_cache = img.subsample(facteur, facteur)
            return BarreNavigation._logo_cache

        except Exception as e:
            print(f"[BarreNavigation] Erreur logo : {e}")
            return None  