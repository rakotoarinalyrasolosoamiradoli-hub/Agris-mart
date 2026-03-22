import tkinter as tk
from tkinter import ttk, messagebox
import re
from database import get_connection
from widgets import BarreNavigation

PATRON_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ═══════════════════════════════════════════════════════
# FONCTIONS DB
# ═══════════════════════════════════════════════════════

def lister_ventes(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                ve.id,
                pr.nom              AS produit_nom,
                pa.nom              AS parcelle_nom,
                ve.acheteur,
                ve.quantite_vendue,
                ve.prix_unitaire,
                (ve.quantite_vendue * ve.prix_unitaire) AS total,
                ve.date_vente
            FROM ventes      ve
            JOIN recoltes    re ON ve.recolte_id  = re.id
            JOIN cultures    cu ON re.culture_id  = cu.id
            JOIN parcelles   pa ON cu.parcelle_id = pa.id
            JOIN produits    pr ON cu.produit_id  = pr.id
            WHERE pa.agriculteur_id = ?
            ORDER BY ve.date_vente DESC
        """, (agriculteur_id,))
        return c.fetchall()
    finally:
        conn.close()


def lister_recoltes_combo(agriculteur_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                re.id,
                re.quantite_obtenue,
                re.unite,
                pr.nom  AS produit_nom,
                pa.nom  AS parcelle_nom
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


def quantite_disponible(recolte_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            SELECT
                re.quantite_obtenue - COALESCE(SUM(ve.quantite_vendue), 0)
                AS reste
            FROM recoltes re
            LEFT JOIN ventes ve ON ve.recolte_id = re.id
            WHERE re.id = ?
            GROUP BY re.id
        """, (recolte_id,))
        resultat = c.fetchone()
        return float(resultat["reste"]) if resultat else 0.0
    finally:
        conn.close()


def ajouter_vente(recolte_id, acheteur, quantite_vendue,
                  prix_unitaire, date_vente):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO ventes
                (recolte_id, acheteur, quantite_vendue,
                 prix_unitaire, date_vente)
            VALUES (?, ?, ?, ?, ?)
        """, (recolte_id, acheteur, quantite_vendue,
              prix_unitaire, date_vente))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def modifier_vente(vente_id, recolte_id, acheteur,
                   quantite_vendue, prix_unitaire, date_vente):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("""
            UPDATE ventes
            SET recolte_id      = ?,
                acheteur        = ?,
                quantite_vendue = ?,
                prix_unitaire   = ?,
                date_vente      = ?
            WHERE id = ?
        """, (recolte_id, acheteur, quantite_vendue,
              prix_unitaire, date_vente, vente_id))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def supprimer_vente(vente_id):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM ventes WHERE id = ?", (vente_id,))
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
# PAGE VENTE
# ═══════════════════════════════════════════════════════

class VentePage(tk.Frame):

    COLONNES = [
        ("produit_nom",    130, "Produit"),
        ("parcelle_nom",   130, "Parcelle"),
        ("acheteur",       130, "Acheteur"),
        ("quantite_vendue", 90, "Quantité"),
        ("prix_unitaire",   90, "Prix unit."),
        ("total",          110, "Total (Ar)"),
        ("date_vente",     100, "Date"),
    ]

    def __init__(self, master, agriculteur_id):
        super().__init__(master, bg="#F0F4F0")
        self.agriculteur_id = agriculteur_id
        self.id_selectionne = None
        self._recoltes      = []
        self._construire_interface()
        self._charger_combo()
        self._charger_tableau()

    def _construire_interface(self):
        BarreNavigation(self, "Gestion des Ventes", self.master).pack(fill="x")
        zone = tk.Frame(self, bg="#F0F4F0")
        zone.pack(fill="both", expand=True, padx=16, pady=12)
        self._construire_tableau(zone)
        self._construire_formulaire(zone)

    def _construire_tableau(self, parent):
        cadre = tk.Frame(parent, bg="#F0F4F0")
        cadre.pack(side="left", fill="both", expand=True, padx=(0, 12))

        style = ttk.Style()
        style.configure("Vente.Treeview", font=("Helvetica", 10), rowheight=30)
        style.configure("Vente.Treeview.Heading",
                        font=("Helvetica", 10, "bold"),
                        background="#E8F4ED", foreground="#1B4332")
        style.map("Vente.Treeview",
                  background=[("selected", "#2D6A4F")],
                  foreground=[("selected", "white")])

        self.tableau = ttk.Treeview(
            cadre,
            columns=[col[0] for col in self.COLONNES],
            show="headings",
            style="Vente.Treeview",
            selectmode="browse"
        )
        for col_id, largeur, titre in self.COLONNES:
            self.tableau.heading(col_id, text=titre, anchor="w")
            self.tableau.column(col_id, width=largeur, anchor="w", minwidth=60)

        scrollbar = ttk.Scrollbar(cadre, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<<TreeviewSelect>>", self._on_selection)

        self.label_compteur = tk.Label(cadre, text="0 vente(s)",
                                       font=("Helvetica", 9),
                                       bg="#F0F4F0", fg="#888888")
        self.label_compteur.pack(anchor="w", pady=(4, 0))

        # Label total général
        self.label_total = tk.Label(cadre, text="Total général : 0 Ar",
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

        self.label_mode = tk.Label(cadre, text="Ajouter une vente",
                                   font=("Helvetica", 13, "bold"),
                                   bg="white", fg="#1B4332")
        self.label_mode.pack(anchor="w", pady=(0, 12))

        # Combobox récolte
        tk.Label(cadre, text="Récolte *", font=("Helvetica", 9, "bold"),
                 bg="white", fg="#2D6A4F").pack(anchor="w", pady=(4, 2))
        self.combo_recolte = ttk.Combobox(cadre, state="readonly",
                                          width=27, font=("Helvetica", 10))
        self.combo_recolte.pack(fill="x", pady=(0, 4))
        self.combo_recolte.bind("<<ComboboxSelected>>",
                                self._on_recolte_change)

        # Label quantité disponible
        self.label_dispo = tk.Label(cadre, text="Disponible : —",
                                    font=("Helvetica", 9),
                                    bg="white", fg="#888888")
        self.label_dispo.pack(anchor="w", pady=(0, 8))

        # Champs texte
        self.champs = {}
        for cle, label in [
            ("acheteur",        "Acheteur *"),
            ("quantite_vendue", "Quantité vendue *"),
            ("prix_unitaire",   "Prix unitaire * (Ar)"),
            ("date_vente",      "Date * (AAAA-MM-JJ)"),
        ]:
            self.champs[cle] = ChampFormulaire(cadre, label, width=28)
            self.champs[cle].pack(fill="x", pady=(0, 8))

        # Lier les champs quantité et prix pour calcul automatique
        self.champs["quantite_vendue"].entry.bind(
            "<KeyRelease>", self._calculer_total)
        self.champs["prix_unitaire"].entry.bind(
            "<KeyRelease>", self._calculer_total)

        # Label total automatique
        self.label_calcul = tk.Label(cadre, text="Total : 0 Ar",
                                     font=("Helvetica", 11, "bold"),
                                     bg="white", fg="#1B4332")
        self.label_calcul.pack(anchor="w", pady=(0, 14))

        self.btn_principal = tk.Button(
            cadre, text="Enregistrer la vente",
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
        self._recoltes = lister_recoltes_combo(self.agriculteur_id)
        self.combo_recolte["values"] = [
            f"{r['produit_nom']} — {r['parcelle_nom']} "
            f"({r['quantite_obtenue']} {r['unite']})"
            for r in self._recoltes
        ]
        if self._recoltes:
            self.combo_recolte.current(0)
            self._on_recolte_change(None)

    def _charger_tableau(self):
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        ventes = lister_ventes(self.agriculteur_id)
        total_general = 0.0

        for v in ventes:
            self.tableau.insert("", "end", iid=v["id"], values=(
                v["produit_nom"],
                v["parcelle_nom"],
                v["acheteur"],
                v["quantite_vendue"],
                f"{v['prix_unitaire']} Ar",
                f"{v['total']:,.0f} Ar",
                v["date_vente"],
            ))
            total_general += v["total"]

        n = len(ventes)
        self.label_compteur.config(text=f"{n} vente(s) enregistrée(s)")
        self.label_total.config(
            text=f"Total général : {total_general:,.0f} Ar"
        )

        if not ventes:
            self.tableau.insert("", "end", tags=("placeholder",),
                                values=("Aucune vente enregistrée",
                                        "", "", "", "", "", ""))
            self.tableau.tag_configure("placeholder",
                                       foreground="#AAAAAA",
                                       font=("Helvetica", 10, "italic"))

    def _on_recolte_change(self, event):
        """Met à jour la quantité disponible quand la récolte change."""
        idx = self.combo_recolte.current()
        if idx < 0 or idx >= len(self._recoltes):
            return
        recolte_id = self._recoltes[idx]["id"]
        dispo = quantite_disponible(recolte_id)
        unite = self._recoltes[idx]["unite"]
        self.label_dispo.config(
            text=f"Disponible : {dispo} {unite}",
            fg="#2D6A4F" if dispo > 0 else "#C62828"
        )

    def _calculer_total(self, event=None):
        """Calcule et affiche le total en temps réel."""
        try:
            qte  = float(self.champs["quantite_vendue"].get())
            prix = float(self.champs["prix_unitaire"].get())
            total = qte * prix
            self.label_calcul.config(
                text=f"Total : {total:,.0f} Ar",
                fg="#1B4332"
            )
        except ValueError:
            self.label_calcul.config(text="Total : —", fg="#AAAAAA")

    def _get_recolte_id(self):
        idx = self.combo_recolte.current()
        if idx < 0 or idx >= len(self._recoltes):
            return None
        return self._recoltes[idx]["id"]

    def _on_selection(self, event):
        selection = self.tableau.selection()
        if not selection:
            return
        try:
            self.id_selectionne = int(selection[0])
        except ValueError:
            return

        valeurs = self.tableau.item(selection[0])["values"]

        # Retrouver la récolte dans le combo
        produit  = valeurs[0]
        parcelle = valeurs[1]
        for i, r in enumerate(self._recoltes):
            if r["produit_nom"] == produit and r["parcelle_nom"] == parcelle:
                self.combo_recolte.current(i)
                self._on_recolte_change(None)
                break

        self.champs["acheteur"].set(valeurs[2])
        self.champs["quantite_vendue"].set(str(valeurs[3]))
        # Retirer " Ar" du prix
        prix_brut = str(valeurs[4]).replace(" Ar", "").strip()
        self.champs["prix_unitaire"].set(prix_brut)
        self.champs["date_vente"].set(valeurs[6])
        self._calculer_total()

        self.label_mode.config(text="Modifier la vente")
        self.btn_principal.config(text="Enregistrer les modifications",
                                  bg="#1565C0")
        self.btn_annuler.pack(fill="x", pady=(0, 4))

    def _valider_et_collecter(self):
        recolte_id = self._get_recolte_id()
        acheteur   = self.champs["acheteur"].get().strip()
        qte        = self.champs["quantite_vendue"].get().strip()
        prix       = self.champs["prix_unitaire"].get().strip()
        date       = self.champs["date_vente"].get().strip()

        if not recolte_id:
            messagebox.showwarning("Champ manquant",
                                   "Sélectionnez une récolte.")
            return None

        if not acheteur:
            messagebox.showwarning("Champ manquant",
                                   "Le nom de l'acheteur est obligatoire.")
            return None

        try:
            qte = float(qte)
            if qte <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Quantité invalide",
                                 "La quantité doit être un nombre positif.")
            return None

        try:
            prix = float(prix)
            if prix <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Prix invalide",
                                 "Le prix doit être un nombre positif.")
            return None

        if not PATRON_DATE.match(date):
            messagebox.showerror("Format invalide",
                                 "Date invalide.\nFormat : AAAA-MM-JJ")
            return None

        # ── Vérification quantité disponible ──
        dispo = quantite_disponible(recolte_id)

        # En mode modification, on ajoute la quantité actuelle au disponible
        # pour ne pas bloquer une modification sur la même récolte
        if self.id_selectionne:
            qte_actuelle = float(
                self.tableau.item(self.id_selectionne)["values"][3]
            )
            dispo += qte_actuelle

        if qte > dispo:
            unite = self._recoltes[self.combo_recolte.current()]["unite"]
            messagebox.showerror(
                "Quantité insuffisante",
                f"Vous ne pouvez vendre que {dispo} {unite}.\n"
                f"Quantité disponible : {dispo} {unite}"
            )
            return None

        return {
            "recolte_id": recolte_id,
            "acheteur":   acheteur,
            "qte":        qte,
            "prix":       prix,
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
            ajouter_vente(data["recolte_id"], data["acheteur"],
                          data["qte"], data["prix"], data["date"])
            messagebox.showinfo("Succès", "Vente enregistrée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ajouter :\n{e}")

    def _modifier(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une vente.")

    def _modifier_enregistrer(self):
        data = self._valider_et_collecter()
        if not data:
            return
        try:
            modifier_vente(self.id_selectionne, data["recolte_id"],
                           data["acheteur"], data["qte"],
                           data["prix"], data["date"])
            messagebox.showinfo("Succès", "Vente modifiée avec succès !")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier :\n{e}")

    def _supprimer(self):
        if not self.id_selectionne:
            messagebox.showwarning("Aucune sélection",
                                   "Cliquez d'abord sur une vente.")
            return
        if not messagebox.askyesno("Confirmer",
                                   "Supprimer cette vente définitivement ?"):
            return
        try:
            supprimer_vente(self.id_selectionne)
            messagebox.showinfo("Supprimé", "Vente supprimée.")
            self._reinitialiser()
            self._charger_tableau()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    def _reinitialiser(self):
        for champ in self.champs.values():
            champ.vider()
        self.id_selectionne = None
        self.label_calcul.config(text="Total : 0 Ar", fg="#1B4332")
        if self._recoltes:
            self.combo_recolte.current(0)
            self._on_recolte_change(None)
        self.label_mode.config(text="Ajouter une vente")
        self.btn_principal.config(text="Enregistrer la vente", bg="#2D6A4F")
        self.btn_annuler.pack_forget()
        self.tableau.selection_remove(self.tableau.selection())