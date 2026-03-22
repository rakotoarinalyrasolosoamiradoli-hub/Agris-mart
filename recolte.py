import tkinter as tk
from tkinter import ttk, messagebox
import re
from database import get_connection
from widgets import BarreNavigation

PATRON_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

UNITES = ["kg", "tonne", "sac", "litre", "unité"]


# ═══════════════════════════════════════════════════════
# FONCTIONS DB
# ═══════════════════════════════════════════════════════

def lister_recoltes(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                re.id,
                pr.nom   AS produit_nom,
                pa.nom   AS parcelle_nom,
                re.quantite_obtenue,
                re.unite,
                re.date_recolte
            FROM recoltes  re
            JOIN cultures  cu ON re.culture_id  = cu.id
            JOIN parcelles pa ON cu.parcelle_id = pa.id
            JOIN produits  pr ON cu.produit_id  = pr.id
            WHERE pa.agriculteur_id = ?
            ORDER BY re.date_recolte DESC
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
            AND   cu.statut = 'en cours'
            ORDER BY pa.nom, pr.nom ASC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def ajouter_recolte(culture_id, quantite_obtenue, date_recolte, unite):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO recoltes
                (culture_id, quantite_obtenue, date_recolte, unite)
            VALUES (?, ?, ?, ?)
        """, (culture_id, quantite_obtenue, date_recolte, unite))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def modifier_recolte(recolte_id, culture_id,
                     quantite_obtenue, date_recolte, unite):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE recoltes
            SET culture_id       = ?,
                quantite_obtenue = ?,
                date_recolte     = ?,
                unite            = ?
            WHERE id = ?
        """, (culture_id, quantite_obtenue,
              date_recolte, unite, recolte_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_recolte(recolte_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM recoltes WHERE id = ?", (recolte_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def recolte_a_des_ventes(recolte_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM ventes WHERE recolte_id = ?",
            (recolte_id,)
        )
        return c.fetchone()[0] > 0
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
# PAGE RÉCOLTE
# ═══════════════════════════════════════════════════════

class RecoltePage(tk.Frame):

    COLONNES = [
        ("produit_nom",      140, "Produit"),
        ("parcelle_nom",     140, "Parcelle"),
        ("quantite_obtenue", 110, "Quantité"),
        ("unite",             70, "Unité"),
        ("date_recolte",     110, "Date récolte"),
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
        BarreNavigation(self, "Gestion des Récoltes", self.master).pack(fill="x")
        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=16, pady=12)
        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 12))

        style = ttk.Style()
        style.configure("Recolte.Treeview",
                        font=("Helvetica", 10), rowheight=30)
        style.configure("Recolte.Treeview.Heading",
                        font=("Helvetica", 10, "bold"),
                        background="#E8F4ED", foreground="#1B4332")
        style.map("Recolte.Treeview",
                  background=[("selected", "#2D6A4F")],
                  foreground=[("selected", "white")])

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            style="Recolte.Treeview",
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

        self.label_compteur = tk.Label(cadre, text="0 récolte(s)",
                                       font=("Helvetica", 9),
                                       bg="#F0F4F0", fg="#888888")
        self.label_compteur.pack(anchor="w", pady=(4, 0))

        self.label_total = tk.Label(cadre, text="Total récolté : 0 kg",
                                    font=("Helvetica", 10, "bold"),
                                    bg="#F0F4F0", fg="#1B4332")
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

        self.label_mode = tk.Label(cadre, text="Ajouter une récolte",
                                   font=("Helvetica", 13, "bold"),
                                   bg="white", fg="#1B4332")
        self.label_mode.pack(anchor="w", pady=(0, 12))

        # Combobox culture
        tk.Label(cadre, text="Culture * (en cours)",
                 font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_culture = ttk.Combobox(cadre, state="readonly",
                                          width=27, font=("Helvetica", 10))
        self.combo_culture.pack(fill="x", pady=(0, 8))

        # Quantité
        self.champs = {}
        self.champs["quantite"] = ChampFormulaire(
            cadre, "Quantité obtenue *", width=28)
        self.champs["quantite"].pack(fill="x", pady=(0, 8))

        # Combobox unité
        tk.Label(cadre, text="Unité *",
                 font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_unite = ttk.Combobox(cadre, values=UNITES,
                                        state="readonly", width=27,
                                        font=("Helvetica", 10))
        self.combo_unite.current(0)
        self.combo_unite.pack(fill="x", pady=(0, 8))

        # Date
        self.champs["date"] = ChampFormulaire(
            cadre, "Date récolte * (AAAA-MM-JJ)", width=28)
        self.champs["date"].pack(fill="x", pady=(0, 16))

        self.btn_principal = tk.Button(
            cadre, text="Enregistrer la récolte",
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

        recoltes = lister_recoltes(self.agriculteur_id)
        total    = 0.0

        for r in recoltes:
            self.tableau.insert("", "end", iid=r["id"], values=(
                r["produit_nom"],
                r["parcelle_nom"],
                r["quantite_obtenue"],
                r["unite"],
                r["date_recolte"],
            ))
            # Additionner uniquement les kg pour le total
            if r["unite"] == "kg":
                total += r["quantite_obtenue"]

        n = len(recoltes)
        self.label_compteur.config(text=f"{n} récolte(s) enregistrée(s)")
        self.label_total.config(text=f"Total récolté : {total:,.1f} kg")

        if not recoltes:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucune récolte enregistrée",
                                        "", "", "", ""))
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
            if cu["produit_nom"] == valeurs[0] and \
               cu["parcelle_nom"] == valeurs[1]:
                self.combo_culture.current(i)
                break

        self.champs["quantite"].set(str(valeurs[2]))

        unite = valeurs[3]
        if unite in UNITES:
            self.combo_unite.current(UNITES.index(unite))

        self.champs["date"].set(valeurs[4])

        self.label_mode.config(text="Modifier la récolte")
        self.btn_principal.config(text="Enregistrer les modifications",
                                  bg="#1565C0")
        self.btn_annuler.pack(fill="x", pady=(0, 4))

    def _valider_et_collecter(self):
        culture_id = self._get_culture_id()
        quantite   = self.champs["quantite"].get().strip()
        unite      = self.combo_unite.get()
        date       = self.champs["date"].get().strip()

        if not culture_id:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez une culture.")
            return None

        try:
            quantite = float(quantite)
            if quantite <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Quantité invalide",
                                 "La quantité doit être un nombre positif.")
            return None

        if not PATRON_DATE.match(date):
            messagebox.showerror("Format invalide",
                                 "Date invalide.\nFormat : AAAA-MM-JJ")
            return None

        return {
            "culture_id": culture_id,
            "quantite":   quantite,
            "unite":      unite,
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
            ajouter_recolte(data["culture_id"], data["quantite"],
                            data["date"], data["unite"])
            messagebox.showinfo("Succès", "Récolte enregistrée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _modifier(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une récolte.")

    def _modifier_enregistrer(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            modifier_recolte(self.id_selectionne, data["culture_id"],
                             data["quantite"], data["date"], data["unite"])
            messagebox.showinfo("Succès", "Récolte modifiée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une récolte.")
            return

        if recolte_a_des_ventes(self.id_selectionne):
            messagebox.showerror(
                "Suppression impossible",
                "Cette récolte a des ventes liées.\n"
                "Supprimez d'abord les ventes associées."
            )
            return

        if not messagebox.askyesno("Confirmer",
                                   "Supprimer cette récolte définitivement ?"):
            return

        try:
            supprimer_recolte(self.id_selectionne)
            messagebox.showinfo("Supprimé", "Récolte supprimée.")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    def _reinitialiser(self):
        for champ in self.champs.values():
            champ.vider()
        self.id_selectionne = None
        self.combo_unite.current(0)
        if self._cultures:
            self.combo_culture.current(0)
        self.label_mode.config(text="Ajouter une récolte")
        self.btn_principal.config(text="Enregistrer la récolte",
                                  bg="#2D6A4F")
        self.btn_annuler.pack_forget()
        self.tableau.selection_remove(self.tableau.selection())