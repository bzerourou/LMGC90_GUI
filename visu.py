import sys
import os
import subprocess
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMessageBox
)
from pylmgc90 import pre

from project import save_project_as
# ========================================
# VISUALISATION
# ========================================

def visu_lmgc(self):
    
    self.statusBar().showMessage("Visualisation du modèle...")
    QApplication.processEvents()
    try:
        
        pre.visuAvatars(self.bodies)
    except Exception as e:
        QMessageBox.critical(self, "Erreur", f"Visu : {e}")

def open_paraview(self):
    try:
        dir_path = self.current_project_dir or os.getcwd()
        pvd = os.path.join(dir_path, 'DISPLAY', 'rigids.pvd')
        if not os.path.exists(pvd):
            QMessageBox.warning(self, "Erreur", "rigids.pvd introuvable\nExécutez le script")
            return
        exe = self._find_paraview()
        if not exe:
            QMessageBox.critical(self, "Erreur", "ParaView non trouvé")
            return
        subprocess.run([exe, pvd], check=True)
        QMessageBox.information(self, "Succès", "ParaView ouvert")
    except Exception as e:
        QMessageBox.critical(self, "Erreur", f"ParaView : {e}")

def _find_paraview(self):
    if shutil.which('paraview'): return 'paraview'
    import glob
    for p in [r"C:\Program Files\ParaView*\bin\paraview.exe"]:
        for f in glob.glob(p):
            if os.path.exists(f): return f
    return None

def generate_datbox(self): 
    if not self.project_dir:
        QMessageBox.warning(self, "Attention", "Enregistrez d'abord le projet pour définir un dossier de sortie.")
        return save_project_as()

    if not self.bodies_objects:
        QMessageBox.warning(self, "Attention", "Aucun avatar créé. Le fichier Datbox sera vide.")
        # On continue quand même ? Oui, pour permettre des tests vides

    try:
        self.statusBar().showMessage("Génération du fichier Datbox en cours...")
        QApplication.processEvents()

        # --- Récupération des conteneurs ---
        mats_container = self.materials
        mods_container = self.models
        bodies_container = self.bodies
        tacts_container = self.contact_laws
        sees_container = self.visibilities_table

        # --- Post-pro : si tu as des commandes ---
        if hasattr(self, 'postpro_commands') and self.postpro_creations:
            # postpro_commands est une liste de dicts { 'name': str, 'step': int }
            for cmd in self.postpro_creations:
                self.postpro_commands.addCommand(pre.postpro_command(cmd['name'], freq=cmd['step']))

        # --- Écriture du fichier ---
        datbox_path = os.path.join(self.project_dir, "DATBOX")
        pre.writeDatbox(
            dim=self.dim,
            mats=mats_container,
            mods=mods_container,
            bodies=bodies_container,
            tacts=tacts_container,
            sees=sees_container,
            post=self.postpro_commands,
            datbox_path=datbox_path  # Optionnel : si tu veux un nom spécifique, sinon il génère automatiquement
        )

        self.statusBar().showMessage(f"Datbox généré : {datbox_path}", 8000)
        QMessageBox.information(self, "Succès", f"Fichier Datbox généré avec succès !\nChemin : {datbox_path}")

    except Exception as e:
        QMessageBox.critical(self, "Erreur Datbox", f"Échec de la génération :\n{e}")
        self.statusBar().showMessage("Échec génération Datbox")

def about(self):
    QMessageBox.information(self, "À propos", "LMGC90_GUI v0.2.6 \n par Zerourou B, email : bachir.zerourou@yahoo.fr \n© 2025 - Open Source")
