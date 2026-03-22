import tkinter as tk
from tkinter import messagebox
from database import initialiser_base, inserer_produits_defaut, inserer_intrants_defaut


# Constantes visuelles — à modifier si besoin

COULEUR_FOND       = "#f5f5f0"
COULEUR_PRIMAIRE   = "#2d6a4f"
COULEUR_SECONDAIRE = "#1b4332"
POLICE_TITRE       = ("Helvetica", 28, "bold")
POLICE_NORMALE     = ("Helvetica", 11)


class Application(tk.Tk):
#fenetre principale

    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.title("AgriSmart — Gestion de cultures")
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.configure(bg=COULEUR_FOND)

        # Centrer la fenêtre à l'écran
        self._centrer_fenetre(1000, 650)

        # Écran actuellement affiché
        self.frame_actuel = None

        # Stocke l'agriculteur connecté (défini après login)
        self.agriculteur_id   = None
        self.agriculteur_nom  = None

        # Démarrer sur l'écran de login
        self.afficher_frame("login")

    def _centrer_fenetre(self, largeur: int, hauteur: int):
        """Place la fenêtre au centre de l'écran."""
        largeur_ecran  = self.winfo_screenwidth()
        hauteur_ecran  = self.winfo_screenheight()
        x = (largeur_ecran  - largeur)  // 2
        y = (hauteur_ecran  - hauteur)  // 2
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

    def afficher_frame(self, nom_frame: str, **kwargs):
        #affiche un nouveau contenu
        # Détruire l'écran actuel
        if self.frame_actuel is not None:
            self.frame_actuel.destroy()

        # Choisir la bonne classe selon le nom
        frame = self._creer_frame(nom_frame)

        # Afficher le nouvel écran
        self.frame_actuel = frame
        self.frame_actuel.pack(fill="both", expand=True)

    def _creer_frame(self, nom_frame: str) -> tk.Frame:

        # Import ici (et non en haut du fichier) pour éviter
        # les imports circulaires et accélérer le démarrage
        if nom_frame == "login":
            from login import LoginFrame
            return LoginFrame(self)

        elif nom_frame == "dashboard":
            from dashboard import DashboardFrame
            return DashboardFrame(self, self.agriculteur_id, self.agriculteur_nom)

        elif nom_frame == "parcelle":
            from parcelle import ParcellePage
            return ParcellePage(self, self.agriculteur_id)

        elif nom_frame == "culture":
            from culture import CulturePage
            return CulturePage(self, self.agriculteur_id)

        elif nom_frame == "recolte":
            from recolte import RecoltePage
            return RecoltePage(self, self.agriculteur_id)

        elif nom_frame == "vente":
            from vente import VentePage
            return VentePage(self, self.agriculteur_id)

        elif nom_frame == "analyse":
            from analyse import AnalysePage
            return AnalysePage(self, self.agriculteur_id)
        
        elif nom_frame == "depense":
            from depense import DepensePage
            return DepensePage(self, self.agriculteur_id)

        elif nom_frame == "analyse":
            from analyse import AnalysePage
            return AnalysePage(self, self.agriculteur_id)

        else:
            raise ValueError(f"Frame inconnue : '{nom_frame}'")

    def connecter(self, agriculteur_id: int, agriculteur_nom: str):
        self.agriculteur_id  = agriculteur_id
        self.agriculteur_nom = agriculteur_nom
        self.afficher_frame("dashboard")

    def deconnecter(self):
        """Réinitialise la session et retourne au login."""
        confirme = messagebox.askyesno(
            "Déconnexion",
            "Voulez-vous vraiment vous déconnecter ?"
        )
        if confirme:
            self.agriculteur_id  = None
            self.agriculteur_nom = None
            self.afficher_frame("login")


def initialiser_application():
    try:
        initialiser_base()
        inserer_produits_defaut()
        inserer_intrants_defaut()
        print(" Base de données prête.")
    except Exception as erreur:
        # Si la base échoue, on affiche une alerte et on arrête
        messagebox.showerror(
            "Erreur critique",
            f"Impossible d'initialiser la base de données :\n{erreur}"
        )
        raise SystemExit(1)


def main():
    #point d'entré
    initialiser_application()

    app = Application()
    app.mainloop()

    print("Application fermée.")


# Lancement uniquement si exécuté directement
if __name__ == "__main__":
    main()