import tkinter as tk
from tkinter import messagebox
import hashlib
import os
from database import get_connection

VERT_FONCE = "#1B4332"
VERT_MED   = "#2D6A4F"
VERT_CLAIR = "#52B788"
VERT_PALE  = "#D8F3DC"
BLANC      = "#FFFFFF"
GRIS_FOND  = "#F0F4F0"
GRIS_CHAMP = "#F7FAF7"
GRIS_BRD   = "#B7D5BE"
GRIS_TEXT  = "#555555"
BLEU_BTN   = "#1565C0"
POLICE     = "Helvetica"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ── Base de données

def verifier_connexion(nom: str, mot_de_passe: str):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, nom, prenom FROM agriculteurs WHERE nom = ? AND mot_de_passe = ?",
            (nom, hash_password(mot_de_passe))
        )
        return c.fetchone()
    finally:
        conn.close()


def nom_existe(nom: str) -> bool:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM agriculteurs WHERE nom = ?", (nom,))
        return c.fetchone() is not None
    finally:
        conn.close()


def creer_agriculteur(nom, prenom, contact, localisation, mot_de_passe):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """INSERT INTO agriculteurs
               (nom, prenom, contact, localisation, mot_de_passe)
               VALUES (?, ?, ?, ?, ?)""",
            (nom, prenom, contact, localisation, hash_password(mot_de_passe))
        )
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ── Widgets 

class ChampSaisi(tk.Frame):

    def __init__(self, parent, label, secret=False, **kwargs):
        super().__init__(parent, bg=BLANC)
        tk.Label(self, text=label, font=(POLICE, 9, "bold"),
                 bg=BLANC, fg=VERT_MED, anchor="w").pack(fill="x", padx=2, pady=(0, 2))
        self.border_frame = tk.Frame(self, bg=GRIS_BRD, padx=1, pady=1)
        self.border_frame.pack(fill="x")
        self.entry = tk.Entry(self.border_frame, font=(POLICE, 11),
                              bg=GRIS_CHAMP, fg="#222222", relief="flat",
                              show="*" if secret else "",
                              insertbackground=VERT_MED, **kwargs)
        self.entry.pack(fill="x", ipady=7, padx=1)
        self.entry.bind("<FocusIn>",  self._on_focus)
        self.entry.bind("<FocusOut>", self._on_blur)

    def _on_focus(self, _):
        self.border_frame.config(bg=VERT_MED)
        self.entry.config(bg=BLANC)

    def _on_blur(self, _):
        self.border_frame.config(bg=GRIS_BRD)
        self.entry.config(bg=GRIS_CHAMP)

    def get(self):    return self.entry.get()
    def clear(self):  self.entry.delete(0, tk.END)


class BoutonStyled(tk.Button):

    def __init__(self, parent, text, command, couleur=VERT_MED, **kwargs):
        super().__init__(parent, text=text, command=command,
                         font=(POLICE, 11, "bold"), bg=couleur, fg=BLANC,
                         relief="flat", cursor="hand2",
                         activebackground=VERT_FONCE, activeforeground=BLANC,
                         pady=10, **kwargs)
        self.couleur = couleur
        self.bind("<Enter>", lambda _: self.config(bg=VERT_FONCE))
        self.bind("<Leave>", lambda _: self.config(bg=self.couleur))


# ── Page Login ───────────────────────────────────────────

class LoginFrame(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bg=GRIS_FOND)

        self.logo_agrismart  = None
        self.logo_ispm       = None
        self.frame_connexion   = None
        self.frame_inscription = None

        self._charger_logos()       # ← charge les deux logos
        self._construire_layout()
        self._show_connexion()

    def _charger_logos(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # ── Logo AgriSmart principal (JPEG) ──
        chemin = os.path.join(base_dir, "téléchargement.jpg")
        if os.path.exists(chemin):
            try:
                from PIL import Image, ImageTk, ImageDraw
                img = Image.open(chemin).convert("RGBA")
                img = img.resize((130, 130), Image.LANCZOS)
                masque = Image.new("L",(50,50), 0)
                draw = ImageDraw.Draw(masque)
                rayon = 15
                draw.rounded_rectangle((0,0,49,49), radius=rayon, fill=255)
                resultat = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
                resultat.paste(img, mask=masque)
                self.logo_agrismart = ImageTk.PhotoImage(resultat)
                print("[Logo AgriSmart] OK")
            except ImportError:
                print("[Logo AgriSmart] Pillow absent → pip install Pillow")
            except Exception as e:
                print(f"[Logo AgriSmart] Erreur : {e}")
        else:
            print(f"[Logo AgriSmart] Introuvable : {chemin}")

        # ── Logo ISPM secondaire (PNG natif) ──
        chemin_ispm = os.path.join(base_dir, "logo_ispm.png")
        if os.path.exists(chemin_ispm):
            try:
                img2 = tk.PhotoImage(file=chemin_ispm)
                facteur = max(1, min(img2.width(), img2.height()) // 55)
                self.logo_ispm = img2.subsample(facteur, facteur)
                print(f"[Logo ISPM] OK — {self.logo_ispm.width()}x{self.logo_ispm.height()}")
            except Exception as e:
                print(f"[Logo ISPM] Erreur : {e}")
        else:
            print(f"[Logo ISPM] Introuvable : {chemin_ispm}")

    def _construire_layout(self):
        self.panneau_gauche = tk.Frame(self, bg=VERT_FONCE, width=230)
        self.panneau_gauche.pack(side="left", fill="y")
        self.panneau_gauche.pack_propagate(False)
        self._construire_panneau_gauche()

        self.panneau_droit = tk.Frame(self, bg=BLANC)
        self.panneau_droit.pack(side="right", fill="both", expand=True)

    def _construire_panneau_gauche(self):
        p = self.panneau_gauche

        tk.Frame(p, bg=VERT_FONCE, height=30).pack()

        # ── Logo AgriSmart principal ──
        if self.logo_agrismart:
            tk.Label(p, image=self.logo_agrismart,
                     bg=VERT_FONCE).pack(pady=(0, 8))
        else:
            tk.Label(p, text="AS", font=(POLICE, 36, "bold"),
                     bg=VERT_FONCE, fg=VERT_CLAIR).pack(pady=(10, 8))

        # Nom application
        tk.Label(p, text="Agri-Smart",
                 font=(POLICE, 17, "bold"),
                 bg=VERT_FONCE, fg=BLANC).pack()

        # Séparateur
        tk.Frame(p, bg=VERT_CLAIR, height=2, width=120).pack(pady=8)

        # Slogan
        tk.Label(p,
                 text="Aide à la décision\npour petit agriculteur",
                 font=(POLICE, 9),
                 bg=VERT_FONCE, fg=VERT_PALE,
                 justify="center").pack(pady=(0, 16))

        # Fonctionnalités
        for texte in ("   Cultures & parcelles",
                      "   Analyses & bilans",
                      "   Ventes & recoltes"):
            tk.Label(p, text=texte, font=(POLICE, 9),
                     bg=VERT_FONCE, fg="#9FE1CB",
                     anchor="w").pack(fill="x", pady=2)

        # ── Footer : logo ISPM + copyright ──
        footer = tk.Frame(p, bg=VERT_FONCE)
        footer.pack(side="bottom", fill="x", pady=12, padx=12)

        if self.logo_ispm:
            tk.Label(footer, image=self.logo_ispm,
                     bg=VERT_FONCE).pack(side="right", padx=(6, 0))

        tk.Label(footer, text="ISPM\n© 2025",
                 font=(POLICE, 8),
                 bg=VERT_FONCE, fg="#6B9E7A",
                 justify="left").pack(side="right")

    # ─────────────────────────────────────────────
    # FORMULAIRES
    # ─────────────────────────────────────────────

    def _build_connexion(self):
        f = tk.Frame(self.panneau_droit, bg=BLANC, padx=50)
        f.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(f, text="Bienvenue !",
                 font=(POLICE, 22, "bold"),
                 bg=BLANC, fg=VERT_FONCE).pack(anchor="w")
        tk.Label(f, text="Connectez-vous à votre espace",
                 font=(POLICE, 10),
                 bg=BLANC, fg=GRIS_TEXT).pack(anchor="w", pady=(2, 24))

        self.nom_login = ChampSaisi(f, "Nom d'utilisateur *", width=28)
        self.nom_login.pack(fill="x", pady=(0, 14))

        self.mdp_login = ChampSaisi(f, "Mot de passe *", secret=True, width=28)
        self.mdp_login.pack(fill="x", pady=(0, 24))

        BoutonStyled(f, "Se connecter →", self._connecter).pack(fill="x")

        tk.Frame(f, bg=GRIS_BRD, height=1).pack(fill="x", pady=20)

        lien_frame = tk.Frame(f, bg=BLANC)
        lien_frame.pack()
        tk.Label(lien_frame, text="Pas encore de compte ?",
                 font=(POLICE, 9), bg=BLANC, fg=GRIS_TEXT).pack(side="left")
        lien = tk.Label(lien_frame, text="  S'inscrire",
                        font=(POLICE, 9, "bold", "underline"),
                        bg=BLANC, fg=VERT_MED, cursor="hand2")
        lien.pack(side="left")
        lien.bind("<Button-1>", lambda e: self._show_inscription())

        return f

    def _build_inscription(self):
        outer = tk.Frame(self.panneau_droit, bg=BLANC)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        f = tk.Frame(outer, bg=BLANC, padx=50)
        f.pack()

        tk.Label(f, text="Créer un compte",
                 font=(POLICE, 22, "bold"),
                 bg=BLANC, fg=VERT_FONCE).pack(anchor="w")
        tk.Label(f, text="Remplissez les informations ci-dessous",
                 font=(POLICE, 10),
                 bg=BLANC, fg=GRIS_TEXT).pack(anchor="w", pady=(2, 18))

        # Nom + Prénom côte à côte
        ligne1 = tk.Frame(f, bg=BLANC)
        ligne1.pack(fill="x", pady=(0, 14))
        col_nom = tk.Frame(ligne1, bg=BLANC)
        col_nom.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self.nom_reg = ChampSaisi(col_nom, "Nom *", width=14)
        self.nom_reg.pack(fill="x")
        col_pre = tk.Frame(ligne1, bg=BLANC)
        col_pre.pack(side="right", expand=True, fill="x", padx=(8, 0))
        self.prenom_reg = ChampSaisi(col_pre, "Prénom *", width=14)
        self.prenom_reg.pack(fill="x")

        # Contact + Localisation côte à côte
        ligne2 = tk.Frame(f, bg=BLANC)
        ligne2.pack(fill="x", pady=(0, 14))
        col_con = tk.Frame(ligne2, bg=BLANC)
        col_con.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self.contact_reg = ChampSaisi(col_con, "Contact (optionnel)", width=14)
        self.contact_reg.pack(fill="x")
        col_loc = tk.Frame(ligne2, bg=BLANC)
        col_loc.pack(side="right", expand=True, fill="x", padx=(8, 0))
        self.localisation_reg = ChampSaisi(col_loc, "Localisation (optionnel)", width=14)
        self.localisation_reg.pack(fill="x")

        self.mdp_reg = ChampSaisi(f, "Mot de passe * (min. 6 caractères)",
                                  secret=True, width=28)
        self.mdp_reg.pack(fill="x", pady=(0, 14))

        self.confirm_mdp = ChampSaisi(f, "Confirmer le mot de passe *",
                                      secret=True, width=28)
        self.confirm_mdp.pack(fill="x", pady=(0, 22))

        BoutonStyled(f, "Créer mon compte →",
                     self._inscrire, couleur=BLEU_BTN).pack(fill="x")

        tk.Frame(f, bg=GRIS_BRD, height=1).pack(fill="x", pady=16)

        lien_frame = tk.Frame(f, bg=BLANC)
        lien_frame.pack()
        tk.Label(lien_frame, text="Déjà un compte ?",
                 font=(POLICE, 9), bg=BLANC, fg=GRIS_TEXT).pack(side="left")
        lien = tk.Label(lien_frame, text="  Se connecter",
                        font=(POLICE, 9, "bold", "underline"),
                        bg=BLANC, fg=VERT_MED, cursor="hand2")
        lien.pack(side="left")
        lien.bind("<Button-1>", lambda e: self._show_connexion())

        return outer

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _connecter(self):
        nom = self.nom_login.get().strip()
        mdp = self.mdp_login.get()

        if not nom or not mdp:
            messagebox.showerror("Erreur",
                "Champs vides\nVeuillez remplir nom et mot de passe.")
            return

        agriculteur = verifier_connexion(nom, mdp)
        if agriculteur:
            self.master.connecter(
                agriculteur["id"],
                f"{agriculteur['prenom']} {agriculteur['nom']}"
            )
        else:
            messagebox.showerror("Identifiants incorrects",
                "Nom d'utilisateur ou mot de passe invalide.")

    def _inscrire(self):
        nom          = self.nom_reg.get().strip()
        prenom       = self.prenom_reg.get().strip()
        contact      = self.contact_reg.get().strip()
        localisation = self.localisation_reg.get().strip()
        mdp          = self.mdp_reg.get()
        confirm      = self.confirm_mdp.get()

        if not nom or not prenom or not mdp:
            messagebox.showerror("Erreur",
                "Les champs obligatoires (nom, prénom, mot de passe) sont vides.")
            return
        if len(mdp) < 6:
            messagebox.showerror("Erreur",
                "Le mot de passe doit contenir au moins 6 caractères.")
            return
        if mdp != confirm:
            messagebox.showerror("Erreur",
                "Les deux mots de passe ne correspondent pas.")
            return
        if nom_existe(nom):
            messagebox.showerror("Erreur",
                f"Le nom '{nom}' existe déjà dans la base.")
            return

        try:
            creer_agriculteur(nom, prenom, contact, localisation, mdp)
            messagebox.showinfo("Compte créé !",
                f"Bienvenue {prenom} !\nCompte créé avec succès.\n"
                "Vous pouvez maintenant vous connecter.")
            for champ in (self.nom_reg, self.prenom_reg, self.contact_reg,
                          self.localisation_reg, self.mdp_reg, self.confirm_mdp):
                champ.clear()
            self._show_connexion()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le compte :\n{e}")

    # ─────────────────────────────────────────────
    # NAVIGATION INTERNE
    # ─────────────────────────────────────────────

    def _show_connexion(self):
        if self.frame_inscription:
            self.frame_inscription.place_forget()
        if self.frame_connexion:
            self.frame_connexion.place_forget()
        self.frame_connexion = self._build_connexion()

    def _show_inscription(self):
        if self.frame_connexion:
            self.frame_connexion.place_forget()
        if self.frame_inscription:
            self.frame_inscription.place_forget()
        self.frame_inscription = self._build_inscription()