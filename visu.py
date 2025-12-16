import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMessageBox
)
from pylmgc90 import pre
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

def about(self):
    QMessageBox.information(self, "À propos", "LMGC90_GUI v0.2.5 [stable]\n par Zerourou B, email : bachir.zerourou@yahoo.fr \n© 2025 - Open Source")
