
import sys



from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton
from PyQt6.QtCore import Qt
from pylmgc90 import pre



#class GUI
class LMGCUniversalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LMGC90_GUI v0.1')
        self.setGeometry(100, 100, 800, 600)
        # Barre de menu 
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu= menu_bar.addMenu("Fichier")
        file_menu.addAction("Nouveau Projet")
        file_menu.addAction("Ouvrir Projet")
        file_menu.addAction("Sauvegarder Projet")
        # barre d'outils 
        project_toolbar = QToolBar("Actions projet")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, project_toolbar)
        new_btn = QPushButton("Nouveau")
        new_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        new_btn.clicked.connect(self.newProject)
        project_toolbar.addWidget(new_btn)

    def newProject(self):
        self.current_project_dir = None


if __name__ == "__main__" :
    app = QApplication (sys.argv)
    window = LMGCUniversalGUI()
    window.show()
    sys.exit(app.exec())