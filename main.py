
import sys



from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton, QDockWidget, QTreeWidget, QSplitter, QTabWidget, QLineEdit, QComboBox, QLabel
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from pylmgc90 import pre



#class GUI
class LMGCUniversalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # conteneurs LMGC90
        self.bodies = pre.avatars()
        self.materials = pre.materials()
        self.models = pre.models()
        self.contact_laws = pre.see_tables()
        self.visibilities_table = pre.tact_behavs()
        self.current_project_dir = None

        self.setWindowTitle('LMGC90_GUI v0.1')
        self.setGeometry(100, 100, 800, 600)
        # Barre de menu 
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu= menu_bar.addMenu("Fichier")
        file_menu.addAction("Nouveau Projet").triggered.connect(self.newProject)
        file_menu.addAction("Ouvrir Projet").triggered.connect(self.openProject)
        file_menu.addAction("Sauvegarder Projet").triggered.connect(self.saveProject)
        file_menu.addAction("Quitter").triggered.connect(self.exit)
        
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
        self.mat_name = QLineEdit("TDURx")
        self.mat_type = QComboBox()
        self.mat_type.addItems(["RIGID"])
        self.mat_density = QLineEdit("1000.")
        self.mat_properties = QLineEdit("")
        mat_tab.setLayout(mat_layout)
        self.tabs.addTab(mat_tab, "Matériau")
        mat_layout.addWidget(QLabel("Nom matériau:"))
        mat_layout.addWidget(self.mat_name)
        mat_layout.addWidget(QLabel("Type:"))
        mat_layout.addWidget(self.mat_type)
        mat_layout.addWidget(QLabel("Densité:"))
        mat_layout.addWidget(self.mat_density)
        mat_layout.addWidget(QLabel("Propriétés (ex. young=1e9, poisson=0.3):"))
        mat_layout.addWidget(self.mat_properties)
        create_mat_btn = QPushButton("Créer matériau")
        create_mat_btn.clicked.connect(self.create_Material)
        mat_layout.addWidget(create_mat_btn)
        #modèle tab
        model_tab = QWidget()
        model_layout = QVBoxLayout()
        self.model_name = QLineEdit("RIGID")
        self.model_physics = QComboBox()
        self.model_physics.addItems(["Rigid"])  #"MECAx", "THERx", "POROx", 
        self.model_element = QLineEdit("Rxx2D")
        self.model_dimension = QComboBox()
        self.model_dimension.addItems(["2", "3"])
        #self.model_dimension.currentTextChanged.connect(self.update_avatar_types)
        self.model_options = QLineEdit("")
        model_layout.addWidget(QLabel("Nom du Modèle:"))
        model_layout.addWidget(self.model_name)
        model_layout.addWidget(QLabel("Physics:"))
        model_layout.addWidget(self.model_physics)
        model_layout.addWidget(QLabel("Element:"))
        model_layout.addWidget(self.model_element)
        model_layout.addWidget(QLabel("Dimension:"))
        model_layout.addWidget(self.model_dimension)
        model_layout.addWidget(QLabel("Options (ex. kinematic='small', formulation='UpdtL'):"))
        model_layout.addWidget(self.model_options)
        create_model_btn = QPushButton("Créer modèle")
        create_model_btn.clicked.connect(self.create_model)
        model_layout.addWidget(create_model_btn)
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

        #rendu graphique
        render_tabs = QTabWidget()
        splitter.addWidget(render_tabs)
        render_tab = QWidget()
        render_layout = QVBoxLayout()
        #les boutons
        vis_btn = QPushButton("visualisation LMGC90")
        render_layout.addWidget(vis_btn)
        paraview_btn = QPushButton("exporter vers Paraview")
        render_layout.addWidget(paraview_btn)
        render_tab.setLayout(render_layout)
        render_tabs.addTab(render_tab,"rendu graphique")

        #ajuster    
        splitter.setSizes([300,50])

        

    def newProject(self):
        self.current_project_dir = None
         # conteneurs LMGC90
        self.bodies = pre.avatars()
        self.matrials = pre.materials()
        self.models = pre.models()
        self.contact_laws = pre.see_tables()
        self.visibilities_table = pre.tact_behavs()
        
    
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
    def exit(self):
        sys.exit()

    def create_Material(self):
        try : 
            properties = eval("dict(" + self.mat_properties.text()+")") if self.mat_properties.text() else {}
            mat = pre.material(name=self.mat_name.text(), materialType=self.mat_type.currentText(), density = float(self.mat_density.text()), **properties)
            self.materials.addMaterial(mat)
            self.update_model_tree()
            QMessageBox.information(self,"Succès",f"Matériau créer")
        
        except Exception as e: 
            QMessageBox.critical(self,"Erreur", f"Erreur lors de la création du matériau")
    def update_model_tree(self):
        print("ici la mise à jour de l'arbre de création")

    def create_model(self):
        print("modèle créer")

if __name__ == "__main__" :
    app = QApplication (sys.argv)
    window = LMGCUniversalGUI()
    window.show()
    sys.exit(app.exec())