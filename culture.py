import tkinter as tk
from tkinter import ttk, messagebox
import re
from database import get_connection
from widgets import BarreNavigation

STATUTS = ["en cours", "terminé", "abandonné"]

COULEURS_STATUT = {
    "en cours":  "#E8F5E9",
    "terminé":   "#E3F2FD",
    "abandonné": "#FFEBEE",
}

PATRON_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")



# FONCTIONS DB — CULTURES

def lister_cultures(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT cu.id,
                   pa.nom       AS parcelle_nom,
                   pr.nom       AS produit_nom,
                   pr.categorie AS categorie,
                   cu.date_debut,
                   cu.date_fin_prevue,
                   cu.statut
            FROM cultures  cu
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            JOIN produits  pr ON cu.produit_id  = pr.id
            WHERE pa.agriculteur_id = ?
            ORDER BY cu.date_debut DESC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def lister_parcelles_combo(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, nom, region FROM parcelles
            WHERE agriculteur_id = ?
            ORDER BY nom ASC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def lister_categories():
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT DISTINCT categorie FROM produits ORDER BY categorie ASC")
        return ["Toutes"] + [row["categorie"] for row in c.fetchall()]
    finally:
        conn.close()


def lister_produits(categorie="Toutes"):
    conn = get_connection()
    try:
        c = conn.cursor()
        if categorie == "Toutes":
            c.execute("""
                SELECT id, nom, categorie FROM produits
                ORDER BY categorie, nom ASC
            """)
        else:
            c.execute("""
                SELECT id, nom, categorie FROM produits
                WHERE categorie = ?
                ORDER BY nom ASC
            """, (categorie,))
        return c.fetchall()
    finally:
        conn.close()


def ajouter_culture(parcelle_id, produit_id, date_debut, date_fin, statut):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO cultures
                (parcelle_id, produit_id, date_debut, date_fin_prevue, statut)
            VALUES (?, ?, ?, ?, ?)
        """, (parcelle_id, produit_id, date_debut, date_fin or None, statut))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def modifier_culture(culture_id, parcelle_id, produit_id,
                     date_debut, date_fin, statut):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE cultures
            SET parcelle_id = ?, produit_id = ?,
                date_debut = ?, date_fin_prevue = ?, statut = ?
            WHERE id = ?
        """, (parcelle_id, produit_id, date_debut,
              date_fin or None, statut, culture_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_culture(culture_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM cultures WHERE id = ?", (culture_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def culture_a_des_recoltes(culture_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM recoltes WHERE culture_id = ?",
            (culture_id,)
        )
        return c.fetchone()[0] > 0
    finally:
        conn.close()



# FONCTIONS DB — INTRANTS
def lister_intrants_culture(culture_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                ci.id,
                i.nom             AS intrant_nom,
                i.type            AS intrant_type,
                ci.quantite_utilisee,
                i.unite,
                ci.date_utilisation
            FROM culture_intrants ci
            JOIN intrants i ON ci.intrant_id = i.id
            WHERE ci.culture_id = ?
            ORDER BY ci.date_utilisation DESC
        """, (culture_id,))
        return c.fetchall()
    finally:
        conn.close()


def lister_intrants_dispo():
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, nom, type, unite
            FROM intrants
            ORDER BY type, nom ASC
        """)
        return c.fetchall()
    finally:
        conn.close()


def ajouter_intrant_culture(culture_id, intrant_id, quantite, date):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO culture_intrants
                (culture_id, intrant_id, quantite_utilisee, date_utilisation)
            VALUES (?, ?, ?, ?)
        """, (culture_id, intrant_id, quantite, date))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_intrant_culture(intrant_culture_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "DELETE FROM culture_intrants WHERE id = ?",
            (intrant_culture_id,)
        )
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# WIDGET CHAMP STYLISÉ

class ChampFormulaire(tk.Frame):

    def __init__(self, parent, label, secret=False, **kwargs):
        super().__init__(parent, bg="white")
        tk.Label(self, text=label, font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F", anchor="w").pack(fill="x", pady=(4, 2))
        self.bordure = tk.Frame(self, bg="#B7D5BE", padx=1, pady=1)
        self.bordure.pack(fill="x")
        self.entry = tk.Entry(self.bordure, font=("Helvetica", 11),
                              bg="#F7FAF7", fg="#222222", relief="flat",
                              show="*" if secret else "",
                              insertbackground="#2D6A4F", **kwargs)
        self.entry.pack(fill="x", ipady=6, padx=1)
        self.entry.bind("<FocusIn>",  lambda _: (self.bordure.config(bg="#2D6A4F"),
                                                  self.entry.config(bg="white")))
        self.entry.bind("<FocusOut>", lambda _: (self.bordure.config(bg="#B7D5BE"),
                                                  self.entry.config(bg="#F7FAF7")))

    def get(self):    return self.entry.get()
    def set(self, v): self.entry.delete(0, tk.END); self.entry.insert(0, v)
    def vider(self):  self.entry.delete(0, tk.END)



# CLASSE INTRANTS (widget secondaire)

class IntrantsCultureFrame(tk.Frame):

    COLONNES = [
        ("intrant_nom",       160, "Intrant"),
        ("intrant_type",      110, "Type"),
        ("quantite_utilisee", 100, "Quantité"),
        ("unite",              70, "Unité"),
        ("date_utilisation",  110, "Date"),
    ]

    def __init__(self, parent, culture_id, culture_nom):
        super().__init__(parent, bg="#F0F4F0")
        self.culture_id      = culture_id
        self.culture_nom     = culture_nom
        self._intrants_dispo = []
        self.id_selectionne  = None

        self._construire_interface()
        self._charger_tableau()

    def _construire_interface(self):
        entete = tk.Frame(self, bg="#2D6A4F", pady=8)
        entete.pack(fill="x")

        tk.Label(
            entete,
            text=f"Intrants — {self.culture_nom}",
            font=("Helvetica", 11, "bold"),
            bg="#2D6A4F", fg="white"
        ).pack(side="left", padx=12)

        tk.Button(
            entete, text="Fermer",
            font=("Helvetica", 9),
            bg="#1B4332", fg="white",
            relief="flat", padx=8, pady=4,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right", padx=12)

        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=12, pady=8)

        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            height=6,
            selectmode="browse"
        )
        for col_id, largeur, titre in self.COLONNES:
            self.tableau.heading(col_id, text=titre, anchor="w")
            self.tableau.column(col_id, width=largeur, anchor="w")

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<<TreeviewSelect>>", self._on_selection)

        tk.Button(
            cadre, text="Supprimer",
            font=("Helvetica", 10),
            bg="#C62828", fg="white",
            relief="flat", padx=12, pady=6,
            cursor="hand2",
            command=self._supprimer
        ).pack(anchor="w", pady=(6, 0))

    def _construire_formulaire(self, parent):
        cadre = tk.Frame(parent, bg="white", padx=16, pady=12)
        cadre.pack(side="right", fill="y")

        tk.Label(cadre, text="Ajouter un intrant",
                 font=("Helvetica", 11, "bold"),
                 bg="white", fg="#1B4332").pack(anchor="w", pady=(0, 10))

        tk.Label(cadre, text="Intrant *",
                 font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))

        self.combo_intrant = ttk.Combobox(cadre, state="readonly",
                                          width=24, font=("Helvetica", 10))
        self.combo_intrant.pack(fill="x", pady=(0, 8))

        tk.Label(cadre, text="Quantité *",
                 font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))

        self.champ_quantite = tk.Entry(cadre, font=("Helvetica", 11),
                                       relief="solid", bd=1, width=26)
        self.champ_quantite.pack(fill="x", ipady=5, pady=(0, 8))

        tk.Label(cadre, text="Date * (AAAA-MM-JJ)",
                 font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))

        self.champ_date = tk.Entry(cadre, font=("Helvetica", 11),
                                   relief="solid", bd=1, width=26)
        self.champ_date.pack(fill="x", ipady=5, pady=(0, 14))

        tk.Button(
            cadre, text="Enregistrer l'intrant",
            font=("Helvetica", 10, "bold"),
            bg="#2D6A4F", fg="white",
            relief="flat", pady=8, cursor="hand2",
            command=self._ajouter
        ).pack(fill="x")

        self._charger_combo()

    def _charger_combo(self):
        self._intrants_dispo = lister_intrants_dispo()
        self.combo_intrant["values"] = [
            f"{i['nom']} ({i['type']})" for i in self._intrants_dispo
        ]
        if self._intrants_dispo:
            self.combo_intrant.current(0)

    def _charger_tableau(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        intrants = lister_intrants_culture(self.culture_id)

        for i in intrants:
            self.tableau.insert("", "end", iid=i["id"], values=(
                i["intrant_nom"],
                i["intrant_type"],
                i["quantite_utilisee"],
                i["unite"],
                i["date_utilisation"],
            ))

        if not intrants:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucun intrant enregistré",
                                        "", "", "", ""))
            self.tableau.tag_configure("placeholder",
                                       foreground="#AAAAAA",
                                       font=("Helvetica", 10, "italic"))

    def _on_selection(self, event):
        selection = self.tableau.selection()
        if not selection:
            return
        try:
            self.id_selectionne = int(selection[0])
        except ValueError:
            self.id_selectionne = None

    def _ajouter(self):
        idx      = self.combo_intrant.current()
        quantite = self.champ_quantite.get().strip()
        date     = self.champ_date.get().strip()

        if idx < 0:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez un intrant.")
            return

        try:
            quantite = float(quantite)
            if quantite <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Quantité invalide",
                                 "La quantité doit être un nombre positif.")
            return

        if not PATRON_DATE.match(date):
            messagebox.showerror("Format invalide",
                                 "Date invalide.\nFormat : AAAA-MM-JJ\nEx: 2025-03-15")
            return

        intrant_id = self._intrants_dispo[idx]["id"]

        try:
            ajouter_intrant_culture(self.culture_id, intrant_id,
                                    quantite, date)
            messagebox.showinfo("Succès", "Intrant enregistré !")
            self.champ_quantite.delete(0, tk.END)
            self.champ_date.delete(0, tk.END)
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur un intrant.")
            return

        if not messagebox.askyesno("Confirmer",
                                   "Supprimer cet intrant ?"):
            return

        try:
            supprimer_intrant_culture(self.id_selectionne)
            self.id_selectionne = None
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")


# CLASSE PRINCIPALE CULTURE

class CulturePage(tk.Frame):

    COLONNES = [
        ("parcelle_nom",    150, "Parcelle"),
        ("produit_nom",     130, "Produit"),
        ("categorie",       110, "Catégorie"),
        ("date_debut",      100, "Début"),
        ("date_fin_prevue", 100, "Fin prévue"),
        ("statut",          100, "Statut"),
    ]

    def __init__(self, master, agriculteur_id):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id  = agriculteur_id
        self.id_selectionne  = None
        self._parcelles      = []
        self._produits       = []
        self.frame_intrants  = None
        self._construire_interface()
        self._charger_combos()
        self._charger_tableau()

    def _construire_interface(self):
        BarreNavigation(self, "Gestion des Cultures", self.master).pack(fill="x")
        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=16, pady=12)
        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 12))

        style = ttk.Style()
        style.configure("Culture.Treeview", font=("Helvetica", 10), rowheight=30)
        style.configure("Culture.Treeview.Heading",
                        font=("Helvetica", 10, "bold"),
                        background="#E8F4ED", foreground="#1B4332")
        style.map("Culture.Treeview",
                  background=[("selected", "#2D6A4F")],
                  foreground=[("selected", "white")])

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            style="Culture.Treeview",
            selectmode="browse"
        )
        for col_id, largeur, titre in self.COLONNES:
            self.tableau.heading(col_id, text=titre, anchor="w")
            self.tableau.column(col_id, width=largeur, anchor="w", minwidth=60)

        for statut, couleur in COULEURS_STATUT.items():
            self.tableau.tag_configure(statut.replace(" ", "_"),
                                       background=couleur)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<<TreeviewSelect>>", self._on_selection)

        self.label_compteur = tk.Label(cadre, text="0 culture(s)",
                                       font=("Helvetica", 9),
                                       bg="#F0F4F0", fg="#888888")
        self.label_compteur.pack(anchor="w", pady=(4, 0))

        barre = tk.Frame(cadre, bg="#F0F4F0")
        barre.pack(fill="x", pady=(6, 0))
        for texte, couleur, cmd in [
            ("Modifier",      "#1565C0", self._modifier),
            ("Supprimer",     "#C62828", self._supprimer),
            ("Tout afficher", "#555555", self._reinitialiser),
        ]:
            tk.Button(barre, text=texte, font=("Helvetica", 10),
                      bg=couleur, fg="white", relief="flat",
                      padx=12, pady=6, cursor="hand2",
                      command=cmd).pack(side="left", padx=(0, 6))

    def _construire_formulaire(self, parent):
        cadre = tk.Frame(parent, bg="white", padx=20, pady=16)
        cadre.pack(side="right", fill="y", ipadx=8)

        self.label_mode = tk.Label(cadre, text="Ajouter une culture",
                                   font=("Helvetica", 13, "bold"),
                                   bg="white", fg="#1B4332")
        self.label_mode.pack(anchor="w", pady=(0, 12))

        tk.Label(cadre, text="Parcelle *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_parcelle = ttk.Combobox(cadre, state="readonly",
                                           width=27, font=("Helvetica", 10))
        self.combo_parcelle.pack(fill="x", pady=(0, 8))

        tk.Label(cadre, text="Catégorie", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_categorie = ttk.Combobox(cadre, state="readonly",
                                            width=27, font=("Helvetica", 10))
        self.combo_categorie.pack(fill="x", pady=(0, 8))
        self.combo_categorie.bind("<<ComboboxSelected>>",
                                  self._on_categorie_change)

        tk.Label(cadre, text="Produit *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_produit = ttk.Combobox(cadre, state="readonly",
                                          width=27, font=("Helvetica", 10))
        self.combo_produit.pack(fill="x", pady=(0, 8))

        self.champs = {}
        for cle, label in [("date_debut",      "Date début * (AAAA-MM-JJ)"),
                            ("date_fin_prevue", "Date fin prévue (AAAA-MM-JJ)")]:
            self.champs[cle] = ChampFormulaire(cadre, label, width=28)
            self.champs[cle].pack(fill="x", pady=(0, 8))

        tk.Label(cadre, text="Statut *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_statut = ttk.Combobox(cadre, values=STATUTS,
                                         state="readonly", width=27,
                                         font=("Helvetica", 10))
        self.combo_statut.current(0)
        self.combo_statut.pack(fill="x", pady=(0, 14))

        self.btn_principal = tk.Button(
            cadre, text="Ajouter la culture",
            font=("Helvetica", 11, "bold"),
            bg="#2D6A4F", fg="white",
            relief="flat", pady=10, cursor="hand2",
            command=self._soumettre)
        self.btn_principal.pack(fill="x", pady=(0, 6))

        self.btn_annuler = tk.Button(
            cadre, text="Annuler la modification",
            font=("Helvetica", 10),
            bg="#EEEEEE", fg="#555555",
            relief="flat", pady=8, cursor="hand2",
            command=self._reinitialiser)

    def _charger_combos(self):
        self._parcelles = lister_parcelles_combo(self.agriculteur_id)
        self.combo_parcelle["values"] = [
            f"{p['nom']} ({p['region'] or 'N/A'})"
            for p in self._parcelles
        ]
        if self._parcelles:
            self.combo_parcelle.current(0)

        self.combo_categorie["values"] = lister_categories()
        self.combo_categorie.current(0)

        self._produits = lister_produits("Toutes")
        self.combo_produit["values"] = [p["nom"] for p in self._produits]
        if self._produits:
            self.combo_produit.current(0)

    def _charger_tableau(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        cultures = lister_cultures(self.agriculteur_id)

        for cu in cultures:
            tag = cu["statut"].replace(" ", "_")
            self.tableau.insert("", "end", iid=cu["id"], values=(
                cu["parcelle_nom"],
                cu["produit_nom"],
                cu["categorie"],
                cu["date_debut"],
                cu["date_fin_prevue"] or "—",
                cu["statut"],
            ), tags=(tag,))

        n = len(cultures)
        self.label_compteur.config(text=f"{n} culture(s) enregistrée(s)")

        if not cultures:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucune culture enregistrée",
                                        "", "", "", "", ""))
            self.tableau.tag_configure("placeholder",
                                       foreground="#AAAAAA",
                                       font=("Helvetica", 10, "italic"))

    def _on_categorie_change(self, event):
        self._produits = lister_produits(self.combo_categorie.get())
        self.combo_produit["values"] = [p["nom"] for p in self._produits]
        if self._produits:
            self.combo_produit.current(0)
        else:
            self.combo_produit.set("")

    def _on_selection(self, event):
        selection = self.tableau.selection()
        if not selection:
            return

        try:
            self.id_selectionne = int(selection[0])
        except ValueError:
            return

        valeurs = self.tableau.item(selection[0])["values"]

        for i, p in enumerate(self._parcelles):
            if p["nom"] == valeurs[0] or \
               f"{p['nom']} ({p['region'] or 'N/A'})" == valeurs[0]:
                self.combo_parcelle.current(i)
                break

        self.combo_categorie.set(valeurs[2])
        self._on_categorie_change(None)

        for i, p in enumerate(self._produits):
            if p["nom"] == valeurs[1]:
                self.combo_produit.current(i)
                break

        self.champs["date_debut"].set(valeurs[3])
        self.champs["date_fin_prevue"].set(
            "" if valeurs[4] == "—" else valeurs[4])

        if valeurs[5] in STATUTS:
            self.combo_statut.current(STATUTS.index(valeurs[5]))

        self.label_mode.config(text="Modifier la culture")
        self.btn_principal.config(text="Enregistrer les modifications",
                                  bg="#1565C0")
        self.btn_annuler.pack(fill="x", pady=(0, 4))

        # ── Afficher les intrants de cette culture ──
        if self.frame_intrants:
            self.frame_intrants.destroy()

        nom_culture = f"{valeurs[1]} sur {valeurs[0]}"
        self.frame_intrants = IntrantsCultureFrame(
            self, self.id_selectionne, nom_culture
        )
        self.frame_intrants.pack(fill="x", padx=0, pady=(8, 0))

    def _get_parcelle_id(self):
        idx = self.combo_parcelle.current()
        if idx < 0 or idx >= len(self._parcelles):
            return None
        return self._parcelles[idx]["id"]

    def _get_produit_id(self):
        idx = self.combo_produit.current()
        if idx < 0 or idx >= len(self._produits):
            return None
        return self._produits[idx]["id"]

    def _valider_et_collecter(self):
        parcelle_id = self._get_parcelle_id()
        produit_id  = self._get_produit_id()
        date_debut  = self.champs["date_debut"].get().strip()
        date_fin    = self.champs["date_fin_prevue"].get().strip()
        statut      = self.combo_statut.get()

        if not parcelle_id:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez une parcelle.")
            return None
        if not produit_id:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez un produit.")
            return None
        if not date_debut:
            messagebox.showwarning("Champ manquant",
                                   "La date de début est obligatoire.")
            return None
        if not PATRON_DATE.match(date_debut):
            messagebox.showerror("Format invalide",
                                 "Date début invalide.\nFormat : AAAA-MM-JJ")
            return None
        if date_fin and not PATRON_DATE.match(date_fin):
            messagebox.showerror("Format invalide",
                                 "Date fin invalide.\nFormat : AAAA-MM-JJ")
            return None

        return {"parcelle_id": parcelle_id, "produit_id": produit_id,
                "date_debut": date_debut, "date_fin": date_fin or None,
                "statut": statut}

    def _soumettre(self):
        if self.id_selectionne is None:
            self._ajouter()
        else:
            self._modifier_enregistrer()

    def _ajouter(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            ajouter_culture(data["parcelle_id"], data["produit_id"],
                            data["date_debut"], data["date_fin"],
                            data["statut"])
            messagebox.showinfo("Succès", "Culture ajoutée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _modifier(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une culture.")

    def _modifier_enregistrer(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            modifier_culture(self.id_selectionne, data["parcelle_id"],
                             data["produit_id"], data["date_debut"],
                             data["date_fin"], data["statut"])
            messagebox.showinfo("Succès", "Culture modifiée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une culture.")
            return
        if culture_a_des_recoltes(self.id_selectionne):
            messagebox.showerror("Suppression impossible",
                                 "Cette culture a des récoltes liées.\n"
                                 "Supprimez d'abord les récoltes.")
            return
        if not messagebox.askyesno("Confirmer",
                                   "Supprimer cette culture définitivement ?"):
            return
        try:
            supprimer_culture(self.id_selectionne)
            messagebox.showinfo("Supprimé", "Culture supprimée.")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    def _reinitialiser(self):
        for champ in self.champs.values():
            champ.vider()
        self.id_selectionne = None
        self.combo_statut.current(0)
        self.combo_categorie.current(0)
        self._on_categorie_change(None)
        if self._parcelles:
            self.combo_parcelle.current(0)
        self.label_mode.config(text="Ajouter une culture")
        self.btn_principal.config(text="Ajouter la culture", bg="#2D6A4F")
        self.btn_annuler.pack_forget()
        self.tableau.selection_remove(self.tableau.selection())

        # Fermer le frame intrants si ouvert
        if self.frame_intrants:
            self.frame_intrants.destroy()
            self.frame_intrants = None