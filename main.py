


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
        self.material_objects = []  # Liste pour objets pre.material
        self.models = pre.models()
        self.model_objects = []  # Liste pour objets pre.model
        self.contact_laws = pre.see_tables()
        self.visibilities_table = pre.tact_behavs()
        self.current_project_dir = None
        self._init_ui()
        self.update_selections()
       

    def _init_ui(self):
        self.setWindowTitle('LMGC90_GUI v0.1')
        self.setGeometry(100, 100, 800, 600)
        # Barre de menu 
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu= menu_bar.addMenu("Fichier")
        file_menu.addAction("Nouveau Projet").triggered.connect(self.new_project)
        file_menu.addAction("Ouvrir Projet").triggered.connect(self.open_project)
        file_menu.addAction("Sauvegarder Projet").triggered.connect(self.save_project)
        file_menu.addAction("Quitter").triggered.connect(self.exit)
        
        # barre d'outils 
        project_toolbar = QToolBar("Actions projet")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, project_toolbar)
        #new
        new_btn = QPushButton("Nouveau")
        new_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        new_btn.clicked.connect(self.new_project)
        project_toolbar.addWidget(new_btn)
        #open
        open_btn = QPushButton("Ouvrir")
        open_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirOpenIcon))
        open_btn.clicked.connect(self.open_project)
        project_toolbar.addWidget(open_btn)
        #save
        save_btn = QPushButton("Sauvegarder")
        save_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DriveHDIcon))
        save_btn.clicked.connect(self.save_project)
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
        create_mat_btn.clicked.connect(self.create_material)
        mat_layout.addWidget(create_mat_btn)
        #modèle tab
        model_tab = QWidget()
        model_layout = QVBoxLayout()
        self.model_name = QLineEdit("rigid")
        self.model_physics = QComboBox()
        self.model_physics.addItems(["MECAx"])  #"THERx", "POROx", 
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
        self.avatar_type = QComboBox()
        self.avatar_types_2d = ["rigidDisk",]# "rigidPolygon", "rigidPlan", "rigidJonc"]
        self.avatar_types_3d = ["rigidSphere", "rigidPolyhedron", "rigidCylinder", "rigidPlan"]
        self.avatar_type.addItems(self.avatar_types_2d)
        # Widgets pour propriétés
        self.avatar_radius_label = QLabel("Rayon (disk/sphere/polygon/jonc/cylinder):")
        self.avatar_radius = QLineEdit("0.1")
        self.avatar_center_label = QLabel("Centre (ex. 0.0,0.0 ou 0.0,0.0,0.0):")
        self.avatar_center = QLineEdit("0.0,0.0")
        self.avatar_material_label = QLabel("matériau:")
        self.avatar_material = QComboBox()
        self.avatar_model_label = QLabel("modèle:")
        self.avatar_model = QComboBox()
        #self.avatar_dimension_label = QLabel("Dimension plan (ex. 1.0,0.0 ou 1.0,0.0,0.0):")
        #self.avatar_dimension = QLineEdit("1.0,0.0")
        #self.avatar_vertices_label = QLabel("Vertices polyèdre (ex. [[0,0,0],[1,0,0],[0,1,0]]):")
        #self.avatar_vertices = QLineEdit("[[0,0,0],[1,0,0],[0,1,0]]")
        #self.avatar_faces_label = QLabel("Faces polyèdre (ex. [[0,1,2]]):")
        #self.avatar_faces = QLineEdit("[[0,1,2]]")
        #self.avatar_height_label = QLabel("Hauteur (cylinder):")
        #self.avatar_height = QLineEdit("1.0")
        self.avatar_properties_label = QLabel("Options  :")
        self.avatar_properties = QLineEdit("")
        self.avatar_color_label = QLabel("Couleur:")
        self.avatar_color = QLineEdit("BLUEx")
        
        avatar_layout.addWidget(QLabel("Type d'Avatar:"))
        avatar_layout.addWidget(self.avatar_type)
        avatar_layout.addWidget(self.avatar_radius_label)
        avatar_layout.addWidget(self.avatar_radius)
        avatar_layout.addWidget(self.avatar_center_label)
        avatar_layout.addWidget(self.avatar_center)
        avatar_layout.addWidget(self.avatar_material_label)
        avatar_layout.addWidget(self.avatar_material)
        avatar_layout.addWidget(self.avatar_model_label)
        avatar_layout.addWidget(self.avatar_model)
        #avatar_layout.addWidget(self.avatar_dimension_label)
        #avatar_layout.addWidget(self.avatar_dimension)
        #avatar_layout.addWidget(self.avatar_vertices_label)
        #avatar_layout.addWidget(self.avatar_vertices)
        #avatar_layout.addWidget(self.avatar_faces_label)
        #avatar_layout.addWidget(self.avatar_faces)
        #avatar_layout.addWidget(self.avatar_height_label)
        #avatar_layout.addWidget(self.avatar_height)
        avatar_layout.addWidget(self.avatar_properties_label)        
        avatar_layout.addWidget(self.avatar_properties)
        avatar_layout.addWidget(self.avatar_color_label)
        avatar_layout.addWidget(self.avatar_color)
        create_avatar_btn = QPushButton("Créer Avatar")
        create_avatar_btn.clicked.connect(self.create_avatar)
        avatar_layout.addWidget(create_avatar_btn)
        avatar_tab.setLayout(avatar_layout)
        self.tabs.addTab(avatar_tab, "Avatar")
        #contact law tab
        # Onglet Lois de Contact
        contact_tab = QWidget()
        contact_layout = QVBoxLayout()
        self.contact_type = QComboBox()
        self.contact_type.addItems(["FRICTION", "COHESION", "IQS_CLB", "PLANx", "GAP_SGR_CLB", "COUPLED_DOF", "RST_CLB"])
        self.contact_properties = QLineEdit("mu=0.3")
        contact_layout.addWidget(QLabel("Type de Loi:"))
        contact_layout.addWidget(self.contact_type)
        contact_layout.addWidget(QLabel("Propriétés (ex. mu=0.3, cn=1e6, ct=1e6):"))
        contact_layout.addWidget(self.contact_properties)
        create_contact_btn = QPushButton("Créer Loi de Contact")
        create_contact_btn.clicked.connect(self.create_contact_law)
        contact_layout.addWidget(create_contact_btn)
        contact_tab.setLayout(contact_layout)
        self.tabs.addTab(contact_tab, "Lois de Contact")

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

        

    def new_project(self):
        self.current_project_dir = None
         # conteneurs LMGC90
        self.bodies = pre.avatars()
        self.materials = pre.materials()
        self.models = pre.models()
        self.contact_laws = pre.see_tables()
        self.visibilities_table = pre.tact_behavs()
        
    
    def open_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Ouvrir un projet", "")
        if dir_path:
            self.current_project_dir = dir_path
    def save_project(self):
        if self.current_project_dir is None:
            self.save_as_project()
        else:
            self.doSave(self.current_project_dir)

    def save_as_project(self):
            dir_path = QFileDialog.getExistingDirectory(self,"Sauvegarder le projet dans","")
            if dir_path:
                self.current_project_dir = dir_path
                self.doSave(dir_path)
    def do_save(self):
        try:
            QMessageBox.information(self, "Succès", f"Projet sauvegardé")
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde" )
    def exit(self):
        sys.exit()

    def create_material(self):
        try : 
            properties = eval("dict(" + self.mat_properties.text()+")") if self.mat_properties.text() else {}
            mat = pre.material(name=self.mat_name.text(), 
                               materialType=self.mat_type.currentText(), 
                               density = float(self.mat_density.text()), 
                               **properties)
            self.materials.addMaterial(mat)
            self.material_objects.append(mat)
            self.update_model_tree()
            self.update_selections()
            QMessageBox.information(self,"Succès",f"Matériau créer")
            print(self.materials)
        except Exception as e: 
            QMessageBox.critical(self,"Erreur", f"Erreur lors de la création du matériau : {str(e)}")
    def update_model_tree(self):
        print("ici la mise à jour de l'arbre de création")

    def create_model(self):
        try : 
            properties = eval("dict(" + self.model_options.text() +")") if self.model_options.text() else {}
            mod = pre.model(name= self.model_name.text(), 
                            physics=self.model_physics.currentText(),
                            element=self.model_element.text(),
                            dimension=int(self.model_dimension.currentText()),
                            **properties)
            self.models.addModel(mod)
            self.model_objects.append(mod)
            self.update_model_tree()
            self.update_selections()
            QMessageBox.information(self,"Succès", f"Création du modèle : ")
        except Exception as e : 
            QMessageBox.critical(self,"Erreur", f"Erreur lors de la création du modèle : {str(e)}")
    
    def update_selections(self):
        """Met à jour les ComboBox avec les matériaux et modèles disponibles."""
    # Update Material ComboBox
        self.avatar_material.clear()
        if self.material_objects:
            for mat in self.material_objects :
                self.avatar_material.addItem(mat.nom)  # Add material name
            self.avatar_material.setCurrentIndex(0)  # Select first material by default
        else:
            self.avatar_material.addItem("Aucun matériau disponible")
            self.avatar_material.setEnabled(False)  # Disable if no materials

        # Update Model ComboBox
        self.avatar_model.clear()
        if self.model_objects:        
            for mod in self.model_objects:
                self.avatar_model.addItem(mod.nom)  # Add model name
            self.avatar_model.setCurrentIndex(0)  # Select first model by default
        else:
            self.avatar_model.addItem("Aucun modèle disponible")
            self.avatar_model.setEnabled(False)  # Disable if no models

        # Enable combo boxes if items are available
        self.avatar_material.setEnabled(bool(self.material_objects))
        self.avatar_model.setEnabled(bool(self.model_objects))
    def create_avatar(self):
        try : 
            properties = eval("dict(" + self.avatar_properties.text() + ")") if self.avatar_properties.text() else {}
            avatar_type = self.avatar_type.currentText()
            if  avatar_type == "rigidDisk":
                center = [float(x) for x in self.avatar_center.text().split(",")]
                body = pre.rigidDisk(
                    r=float(self.avatar_radius.text()),
                    center = center,
                    material=self.material_objects[self.avatar_material.currentIndex()],
                    model=self.model_objects[self.avatar_model.currentIndex()],
                    color=self.avatar_color.text(),
                    **properties
                    
                )
            self.bodies.addAvatar(body)
            self.update_model_tree()
           
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'avatar : {str(e)}")
        
    def create_contact_law(self):
        print("button law cliqued")
if __name__ == "__main__" :
    app = QApplication (sys.argv)
    window = LMGCUniversalGUI()
    window.show()
    sys.exit(app.exec())