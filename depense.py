import tkinter as tk
from tkinter import ttk, messagebox
import re
from database import get_connection
from widgets import BarreNavigation

PATRON_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CATEGORIES_DEPENSE = [
    "Semences", "Engrais", "Pesticides", "Main d'oeuvre",
    "Matériel", "Transport", "Irrigation", "Autre"
]


# ═══════════════════════════════════════════════════════
# FONCTIONS DB
# ═══════════════════════════════════════════════════════

def lister_depenses(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                de.id,
                pr.nom   AS produit_nom,
                pa.nom   AS parcelle_nom,
                de.libelle,
                de.categorie,
                de.montant,
                de.date_depense
            FROM depenses  de
            JOIN cultures  cu ON de.culture_id  = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            JOIN produits  pr ON cu.produit_id  = pr.id
            WHERE pa.agriculteur_id = ?
            ORDER BY de.date_depense DESC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def lister_cultures_combo(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                cu.id,
                pr.nom AS produit_nom,
                pa.nom AS parcelle_nom
            FROM cultures  cu
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            JOIN produits  pr ON cu.produit_id  = pr.id
            WHERE pa.agriculteur_id = ?
            ORDER BY pa.nom, pr.nom ASC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def ajouter_depense(culture_id, libelle, categorie, montant, date_depense):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO depenses
                (culture_id, libelle, categorie, montant, date_depense)
            VALUES (?, ?, ?, ?, ?)
        """, (culture_id, libelle, categorie, montant, date_depense))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def modifier_depense(depense_id, culture_id, libelle,
                     categorie, montant, date_depense):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE depenses
            SET culture_id  = ?,
                libelle     = ?,
                categorie   = ?,
                montant     = ?,
                date_depense = ?
            WHERE id = ?
        """, (culture_id, libelle, categorie,
              montant, date_depense, depense_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_depense(depense_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM depenses WHERE id = ?", (depense_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════
# WIDGET CHAMP STYLISÉ
# ═══════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════
# PAGE DÉPENSE
# ═══════════════════════════════════════════════════════

class DepensePage(tk.Frame):

    COLONNES = [
        ("produit_nom",  120, "Produit"),
        ("parcelle_nom", 120, "Parcelle"),
        ("libelle",      150, "Libellé"),
        ("categorie",    110, "Catégorie"),
        ("montant",      110, "Montant (Ar)"),
        ("date_depense", 100, "Date"),
    ]

    def __init__(self, master, agriculteur_id):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id = agriculteur_id
        self.id_selectionne = None
        self._cultures      = []
        self._construire_interface()
        self._charger_combo()
        self._charger_tableau()

    def _construire_interface(self):
        BarreNavigation(self, "Gestion des Dépenses", self.master).pack(fill="x")
        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=16, pady=12)
        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 12))

        style = ttk.Style()
        style.configure("Depense.Treeview",
                        font=("Helvetica", 10), rowheight=30)
        style.configure("Depense.Treeview.Heading",
                        font=("Helvetica", 10, "bold"),
                        background="#E8F4ED", foreground="#1B4332")
        style.map("Depense.Treeview",
                  background=[("selected", "#2D6A4F")],
                  foreground=[("selected", "white")])

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            style="Depense.Treeview",
            selectmode="browse"
        )
        for col_id, largeur, titre in self.COLONNES:
            self.tableau.heading(col_id, text=titre, anchor="w")
            self.tableau.column(col_id, width=largeur,
                                anchor="w", minwidth=60)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<<TreeviewSelect>>", self._on_selection)

        self.label_compteur = tk.Label(cadre, text="0 dépense(s)",
                                       font=("Helvetica", 9),
                                       bg="#F0F4F0", fg="#888888")
        self.label_compteur.pack(anchor="w", pady=(4, 0))

        self.label_total = tk.Label(cadre, text="Total : 0 Ar",
                                    font=("Helvetica", 10, "bold"),
                                    bg="#F0F4F0", fg="#C62828")
        self.label_total.pack(anchor="w", pady=(2, 0))

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

        self.label_mode = tk.Label(cadre, text="Ajouter une dépense",
                                   font=("Helvetica", 13, "bold"),
                                   bg="white", fg="#1B4332")
        self.label_mode.pack(anchor="w", pady=(0, 12))

        # Combobox culture
        tk.Label(cadre, text="Culture *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_culture = ttk.Combobox(cadre, state="readonly",
                                          width=27, font=("Helvetica", 10))
        self.combo_culture.pack(fill="x", pady=(0, 8))

        # Champ libellé
        self.champs = {}
        self.champs["libelle"] = ChampFormulaire(
            cadre, "Libellé * (ex: Achat engrais NPK)", width=28)
        self.champs["libelle"].pack(fill="x", pady=(0, 8))

        # Combobox catégorie
        tk.Label(cadre, text="Catégorie *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_categorie = ttk.Combobox(
            cadre, values=CATEGORIES_DEPENSE,
            state="readonly", width=27, font=("Helvetica", 10))
        self.combo_categorie.current(0)
        self.combo_categorie.pack(fill="x", pady=(0, 8))

        # Montant et date
        for cle, label in [
            ("montant",      "Montant * (Ar)"),
            ("date_depense", "Date * (AAAA-MM-JJ)"),
        ]:
            self.champs[cle] = ChampFormulaire(cadre, label, width=28)
            self.champs[cle].pack(fill="x", pady=(0, 8))

        self.btn_principal = tk.Button(
            cadre, text="Enregistrer la dépense",
            font=("Helvetica", 11, "bold"),
            bg="#C62828", fg="white",
            relief="flat", pady=10, cursor="hand2",
            command=self._soumettre)
        self.btn_principal.pack(fill="x", pady=(8, 6))

        self.btn_annuler = tk.Button(
            cadre, text="Annuler la modification",
            font=("Helvetica", 10),
            bg="#EEEEEE", fg="#555555",
            relief="flat", pady=8, cursor="hand2",
            command=self._reinitialiser)

    def _charger_combo(self):
        self._cultures = lister_cultures_combo(self.agriculteur_id)
        self.combo_culture["values"] = [
            f"{cu['produit_nom']} — {cu['parcelle_nom']}"
            for cu in self._cultures
        ]
        if self._cultures:
            self.combo_culture.current(0)

    def _charger_tableau(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        depenses = lister_depenses(self.agriculteur_id)
        total = 0.0

        for d in depenses:
            self.tableau.insert("", "end", iid=d["id"], values=(
                d["produit_nom"],
                d["parcelle_nom"],
                d["libelle"],
                d["categorie"],
                f"{d['montant']:,.0f} Ar",
                d["date_depense"],
            ))
            total += d["montant"]

        n = len(depenses)
        self.label_compteur.config(text=f"{n} dépense(s) enregistrée(s)")
        self.label_total.config(text=f"Total : {total:,.0f} Ar")

        if not depenses:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucune dépense enregistrée",
                                        "", "", "", "", ""))
            self.tableau.tag_configure("placeholder",
                                       foreground="#AAAAAA",
                                       font=("Helvetica", 10, "italic"))

    def _get_culture_id(self):
        idx = self.combo_culture.current()
        if idx < 0 or idx >= len(self._cultures):
            return None
        return self._cultures[idx]["id"]

    def _on_selection(self, event):
        selection = self.tableau.selection()
        if not selection:
            return
        try:
            self.id_selectionne = int(selection[0])
        except ValueError:
            return

        valeurs = self.tableau.item(selection[0])["values"]

        for i, cu in enumerate(self._cultures):
            label = f"{cu['produit_nom']} — {cu['parcelle_nom']}"
            if cu["produit_nom"] == valeurs[0] and \
               cu["parcelle_nom"] == valeurs[1]:
                self.combo_culture.current(i)
                break

        self.champs["libelle"].set(valeurs[2])

        categorie = valeurs[3]
        if categorie in CATEGORIES_DEPENSE:
            self.combo_categorie.current(
                CATEGORIES_DEPENSE.index(categorie))

        montant_brut = str(valeurs[4]).replace(" Ar", "").replace(",", "").strip()
        self.champs["montant"].set(montant_brut)
        self.champs["date_depense"].set(valeurs[5])

        self.label_mode.config(text="Modifier la dépense")
        self.btn_principal.config(text="Enregistrer les modifications",
                                  bg="#1565C0")
        self.btn_annuler.pack(fill="x", pady=(0, 4))

    def _valider_et_collecter(self):
        culture_id = self._get_culture_id()
        libelle    = self.champs["libelle"].get().strip()
        categorie  = self.combo_categorie.get()
        montant    = self.champs["montant"].get().strip()
        date       = self.champs["date_depense"].get().strip()

        if not culture_id:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez une culture.")
            return None

        if not libelle:
            messagebox.showwarning("Champ manquant",
                                   "Le libellé est obligatoire.")
            return None

        try:
            montant = float(montant)
            if montant <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Montant invalide",
                                 "Le montant doit être un nombre positif.")
            return None

        if not PATRON_DATE.match(date):
            messagebox.showerror("Format invalide",
                                 "Date invalide.\nFormat : AAAA-MM-JJ")
            return None

        return {
            "culture_id": culture_id,
            "libelle":    libelle,
            "categorie":  categorie,
            "montant":    montant,
            "date":       date,
        }

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
            ajouter_depense(data["culture_id"], data["libelle"],
                            data["categorie"], data["montant"],
                            data["date"])
            messagebox.showinfo("Succès", "Dépense enregistrée !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _modifier(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une dépense.")

    def _modifier_enregistrer(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            modifier_depense(self.id_selectionne, data["culture_id"],
                             data["libelle"], data["categorie"],
                             data["montant"], data["date"])
            messagebox.showinfo("Succès", "Dépense modifiée !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une dépense.")
            return
        if not messagebox.askyesno("Confirmer",
                                   "Supprimer cette dépense définitivement ?"):
            return
        try:
            supprimer_depense(self.id_selectionne)
            messagebox.showinfo("Supprimé", "Dépense supprimée.")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    def _reinitialiser(self):
        for champ in self.champs.values():
            champ.vider()
        self.id_selectionne = None
        self.combo_categorie.current(0)
        if self._cultures:
            self.combo_culture.current(0)
        self.label_mode.config(text="Ajouter une dépense")
        self.btn_principal.config(text="Enregistrer la dépense",
                                  bg="#C62828")
        self.btn_annuler.pack_forget()
        self.tableau.selection_remove(self.tableau.selection())