
import sys



from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton, QDockWidget, QTreeWidget, QSplitter, QTabWidget
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QVBoxLayout
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
        #new
        new_btn = QPushButton("Nouveau")
        new_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        new_btn.clicked.connect(self.newProject)
        project_toolbar.addWidget(new_btn)
        #open
        open_btn = QPushButton("Ouvrir")
        open_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon))
        open_btn.clicked.connect(self.openProject)
        project_toolbar.addWidget(open_btn)
        #save
        save_btn = QPushButton("Sauvegarder")
        save_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DriveHDIcon))
        save_btn.clicked.connect(self.saveProject)
        project_toolbar.addWidget(save_btn)
    
        #arbre de création 
        dock = QDockWidget("étapes de création ", self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.model_tree = QTreeWidget()
        self.model_tree.setHeaderLabels(["Nom/étape", "Type", "Détails"])
        self.model_tree.setColumnWidth(0, 200)
        dock.setWidget(self.model_tree)
       
        #tab des propriétés 
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)
        #onglets principaux
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)
        # matériau tab
        mat_tab = QWidget()
        mat_layout = QVBoxLayout()
        mat_tab.setLayout(mat_layout)
        self.tabs.addTab(mat_tab, "Matériau")
        #modèle tab
        model_tab = QWidget()
        model_layout = QVBoxLayout()
        model_tab.setLayout(model_layout)
        self.tabs.addTab(model_tab, "Modèle")
        #avatar tab
        avatar_tab = QWidget()
        avatar_layout = QVBoxLayout()
        avatar_tab.setLayout(avatar_layout)
        self.tabs.addTab(avatar_tab, "Avatar")
        #contact law tab
        contact_tab = QWidget()
        contact_layout = QVBoxLayout()
        contact_tab.setLayout(contact_layout)
        self.tabs.addTab(contact_tab, "Lois de contact")
        #Table de visibilité tab
        vis_tab = QWidget()
        vis_layout = QVBoxLayout()
        vis_tab.setLayout(vis_layout)
        self.tabs.addTab(vis_tab, "Table de visibilité")

    def newProject(self):
        self.current_project_dir = None
    
    def openProject(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Ouvrir un projet", "")
        if dir_path:
            self.current_project_dir = dir_path
    def saveProject(self):
        if self.current_project_dir is None:
            self.saveAsProject()
        else:
            self.doSave(self.current_project_dir)

    def saveAsProject(self):
            dir_path = QFileDialog.getExistingDirectory(self,"Sauvegarder le projet dans","")
            if dir_path:
                self.current_project_dir = dir_path
                self.doSave(dir_path)
    def doSave(self):
        try:
            QMessageBox.information(self, "Succès", f"Projet sauvegardé")
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde" )

if __name__ == "__main__" :
    app = QApplication (sys.argv)
    window = LMGCUniversalGUI()
    window.show()
    sys.exit(app.exec())