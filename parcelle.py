import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection
from widgets import BarreNavigation

REGIONS_MADAGASCAR = [
    "Analamanga", "Vakinankaratra", "Itasy", "Bongolava",
    "Matsiatra Ambony", "Amoron'i Mania", "Vatovavy", "Ihorombe",
    "Atsimo Atsinanana", "Atsinanana", "Analanjirofo", "Alaotra Mangoro",
    "Boeny", "Sofia", "Betsiboka", "Melaky",
    "Atsimo Andrefana", "Androy", "Anosy", "Menabe",
    "Diana", "Sava"
]

TYPES_SOL = [
    "Argileux", "Sableux", "Limoneux", "Latéritique",
    "Humifère", "Volcanique", "Alluvionnaire", "Mixte"
]


#Base de données

def lister_parcelles(agriculteur_id: int) -> list:
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT id, nom, surface_ha, type_sol, region, coordonnees_gps
            FROM parcelles
            WHERE agriculteur_id = ?
            ORDER BY nom ASC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def ajouter_parcelle(agriculteur_id, nom, surface_ha,
                     type_sol, region, coordonnees_gps):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO parcelles
                (agriculteur_id, nom, surface_ha, type_sol, region, coordonnees_gps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agriculteur_id, nom, surface_ha, type_sol, region, coordonnees_gps))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def modifier_parcelle(parcelle_id, nom, surface_ha,
                      type_sol, region, coordonnees_gps):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE parcelles
            SET nom = ?, surface_ha = ?, type_sol = ?, region = ?, coordonnees_gps = ?
            WHERE id = ?
        """, (nom, surface_ha, type_sol, region, coordonnees_gps, parcelle_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_parcelle(parcelle_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM parcelles WHERE id = ?", (parcelle_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def parcelle_a_des_cultures(parcelle_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM cultures WHERE parcelle_id = ?", (parcelle_id,))
        return c.fetchone()[0] > 0
    finally:
        conn.close()


#Widget champ stylisé

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

    def get(self):
        return self.entry.get()

    def set(self, valeur):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, valeur)

    def vider(self):
        self.entry.delete(0, tk.END)


#Page Parcelle

class ParcellePage(tk.Frame):

    COLONNES = [
        ("nom",             160, "Nom"),
        ("surface_ha",       90, "Surface"),
        ("type_sol",        120, "Type de sol"),
        ("region",          150, "Région"),
        ("coordonnees_gps", 160, "GPS"),
    ]

    def __init__(self, master, agriculteur_id):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id = agriculteur_id
        self.id_selectionne = None
        self._construire_interface()
        self._charger_tableau()

    def _construire_interface(self):
        BarreNavigation(self, "Gestion des Parcelles", self.master).pack(fill="x")
        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=16, pady=12)
        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 12))

        style = ttk.Style()
        style.configure("Parcelle.Treeview", font=("Helvetica", 10),
                        rowheight=30, background="white", fieldbackground="white")
        style.configure("Parcelle.Treeview.Heading", font=("Helvetica", 10, "bold"),
                        background="#E8F4ED", foreground="#1B4332")
        style.map("Parcelle.Treeview",
                  background=[("selected", "#2D6A4F")],
                  foreground=[("selected", "white")])

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            style="Parcelle.Treeview",
            selectmode="browse"
        )
        for col_id, largeur, titre in self.COLONNES:
            self.tableau.heading(col_id, text=titre, anchor="w",
                                 command=lambda c=col_id: self._trier_par(c))
            self.tableau.column(col_id, width=largeur, anchor="w", minwidth=60)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<<TreeviewSelect>>", self._on_selection)

        self.label_compteur = tk.Label(cadre, text="0 parcelle(s)",
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

        self.label_mode = tk.Label(cadre, text="Ajouter une parcelle",
                                   font=("Helvetica", 13, "bold"),
                                   bg="white", fg="#1B4332")
        self.label_mode.pack(anchor="w", pady=(0, 12))

        self.champ_nom = ChampFormulaire(cadre, "Nom de la parcelle *", width=28)
        self.champ_nom.pack(fill="x", pady=(0, 8))

        self.champ_surface = ChampFormulaire(cadre, "Surface (ha) * — ex: 1.5", width=28)
        self.champ_surface.pack(fill="x", pady=(0, 8))

        tk.Label(cadre, text="Type de sol", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_sol = ttk.Combobox(cadre, values=TYPES_SOL,
                                      state="readonly", width=27,
                                      font=("Helvetica", 10))
        self.combo_sol.pack(fill="x", pady=(0, 8))

        tk.Label(cadre, text="Région (Madagascar)", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_region = ttk.Combobox(cadre, values=REGIONS_MADAGASCAR,
                                         state="readonly", width=27,
                                         font=("Helvetica", 10))
        self.combo_region.pack(fill="x", pady=(0, 8))

        self.champ_gps = ChampFormulaire(
            cadre, "Coordonnées GPS — ex: -18.9161, 47.5362", width=28)
        self.champ_gps.pack(fill="x", pady=(0, 16))

        self.btn_principal = tk.Button(cadre, text="Ajouter la parcelle",
                                       font=("Helvetica", 11, "bold"),
                                       bg="#2D6A4F", fg="white",
                                       relief="flat", pady=10, cursor="hand2",
                                       command=self._soumettre)
        self.btn_principal.pack(fill="x", pady=(0, 6))

        self.btn_annuler = tk.Button(cadre, text="Annuler la modification",
                                     font=("Helvetica", 10),
                                     bg="#EEEEEE", fg="#555555",
                                     relief="flat", pady=8, cursor="hand2",
                                     command=self._reinitialiser)

    def _charger_tableau(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        parcelles = lister_parcelles(self.agriculteur_id)

        for p in parcelles:
            self.tableau.insert("", "end", iid=p["id"], values=(
                p["nom"],
                f"{p['surface_ha']} ha",
                p["type_sol"]        or "—",
                p["region"]          or "—",
                p["coordonnees_gps"] or "—",
            ))

        n = len(parcelles)
        self.label_compteur.config(text=f"{n} parcelle(s) enregistrée(s)")

        if not parcelles:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucune parcelle enregistrée", "", "", "", ""))
            self.tableau.tag_configure("placeholder", foreground="#AAAAAA",
                                       font=("Helvetica", 10, "italic"))

    def _on_selection(self, event):
        selection = self.tableau.selection()
        if not selection:
            return

        try:
            self.id_selectionne = int(selection[0])
        except ValueError:
            return

        valeurs = self.tableau.item(selection[0])["values"]

        self.champ_nom.set(valeurs[0])
        self.champ_surface.set(str(valeurs[1]).replace(" ha", "").strip())

        sol = valeurs[2] if valeurs[2] != "—" else ""
        self.combo_sol.set(sol if sol in TYPES_SOL else "")

        region = valeurs[3] if valeurs[3] != "—" else ""
        self.combo_region.set(region if region in REGIONS_MADAGASCAR else "")

        self.champ_gps.set(valeurs[4] if valeurs[4] != "—" else "")

        self.label_mode.config(text="Modifier la parcelle")
        self.btn_principal.config(text="Enregistrer les modifications", bg="#1565C0")
        self.btn_annuler.pack(fill="x")

    def _trier_par(self, colonne):
        lignes = [(self.tableau.set(k, colonne), k)
                  for k in self.tableau.get_children("")]
        lignes.sort()
        for index, (_, k) in enumerate(lignes):
            self.tableau.move(k, "", index)

    def _soumettre(self):
        if self.id_selectionne is None:
            self._ajouter()
        else:
            self._modifier_enregistrer()

    def _valider_et_collecter(self):
        nom     = self.champ_nom.get().strip()
        surface = self.champ_surface.get().strip()
        sol     = self.combo_sol.get()
        region  = self.combo_region.get()
        gps     = self.champ_gps.get().strip()

        if not nom:
            messagebox.showwarning("Champ manquant", "Le nom est obligatoire.")
            return None

        try:
            surface = float(surface)
            if surface <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Surface invalide",
                                 "La surface doit être un nombre positif.\nExemple : 1.5")
            return None

        return {"nom": nom, "surface": surface,
                "sol": sol, "region": region, "gps": gps}

    def _ajouter(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            ajouter_parcelle(self.agriculteur_id, data["nom"], data["surface"],
                             data["sol"], data["region"], data["gps"])
            messagebox.showinfo("Succès", f"Parcelle '{data['nom']}' ajoutée !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _modifier(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une parcelle.")

    def _modifier_enregistrer(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            modifier_parcelle(self.id_selectionne, data["nom"], data["surface"],
                              data["sol"], data["region"], data["gps"])
            messagebox.showinfo("Succès", f"Parcelle '{data['nom']}' modifiée !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une parcelle.")
            return

        if parcelle_a_des_cultures(self.id_selectionne):
            messagebox.showerror("Suppression impossible",
                                 "Cette parcelle a des cultures liées.\n"
                                 "Supprimez d'abord les cultures.")
            return

        nom = self.champ_nom.get()
        if not messagebox.askyesno("Confirmer",
                                   f"Supprimer '{nom}' définitivement ?"):
            return

        try:
            supprimer_parcelle(self.id_selectionne)
            messagebox.showinfo("Supprimé", f"Parcelle '{nom}' supprimée.")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    def _reinitialiser(self):
        for champ in [self.champ_nom, self.champ_surface, self.champ_gps]:
            champ.vider()
        self.combo_sol.set("")
        self.combo_region.set("")
        self.id_selectionne = None
        self.label_mode.config(text="Ajouter une parcelle")
        self.btn_principal.config(text="Ajouter la parcelle", bg="#2D6A4F")
        self.btn_annuler.pack_forget()
        self.tableau.selection_remove(self.tableau.selection())