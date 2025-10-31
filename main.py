
import sys, os
import subprocess, json
import pdb
import math

from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton, QDockWidget, QTreeWidget, QTreeWidgetItem, QSplitter, QTabWidget, QLineEdit, QComboBox, QLabel
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from pylmgc90 import pre



#class GUI
class LMGCUniversalGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # conteneurs LMGC90
        self.dim = 2
        self.center = []
        self.bodies = pre.avatars()
        self.bodies_objects = []
        self.avatar_creations= []
        self.materials = pre.materials()
        self.material_objects = []  # Liste pour objets pre.material
        self.material_creations =[]
        self.models = pre.models()
        self.model_objects = []  # Liste pour objets pre.model
        self.model_creations = []
        self.contact_laws = pre.tact_behavs()
        self.contact_laws_objects =[]
        self.contact_creations = []
        self.visibilities_table = pre.see_tables()
        self.visibilities_table_objects = []
        self.visibility_creations = []
        self.mats_dict = {}      # {nom: objet material}
        self.mods_dict = {}      # {nom: objet model}
        self.bodies_list = []    # [body1, body2, ...] dans l'ordre

        self.operations = []
        self.current_project_dir = None
        self._init_ui()
        self.update_selections()
        self.update_model_tree()
       

    def _init_ui(self):
        self.setWindowTitle('LMGC90_GUI v0.1.0')
        self.setGeometry(100, 100, 800, 600)
        # Barre de menu 
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        file_menu= menu_bar.addMenu("Fichier")
        file_menu.addAction("Nouveau Projet").triggered.connect(self.new_project)
        file_menu.addAction("Ouvrir Projet").triggered.connect(self.open_project)
        file_menu.addAction("Sauvegarder Projet").triggered.connect(self.save_project)
        file_menu.addAction("Quitter").triggered.connect(self.exit)
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("A propos").triggered.connect(self.apropos)
        
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
        # Barre d'outils actions
        action_toolbar = QToolBar("Actions")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, action_toolbar)
        generate_script_btn = QPushButton("Générer Script Python")
        generate_script_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        generate_script_btn.clicked.connect(self.generate_python_script)
        action_toolbar.addWidget(generate_script_btn)
        execute_script_btn = QPushButton("Exécuter Script Python")
        execute_script_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        execute_script_btn.clicked.connect(self.execute_python_script)
        action_toolbar.addWidget(execute_script_btn)

        #arbre de création 
        dock = QDockWidget("étapes de création ", self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.model_tree = QTreeWidget()
        self.model_tree.setHeaderLabels(["Nom/étape", "Type", "Détails"])
        self.model_tree.setColumnWidth(50, 100)
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
        avatar_layout.addWidget(self.avatar_properties_label)        
        avatar_layout.addWidget(self.avatar_properties)
        avatar_layout.addWidget(self.avatar_color_label)
        avatar_layout.addWidget(self.avatar_color)
        create_avatar_btn = QPushButton("Créer Avatar")
        create_avatar_btn.clicked.connect(self.create_avatar)
        avatar_layout.addWidget(create_avatar_btn)
        avatar_tab.setLayout(avatar_layout)
        self.tabs.addTab(avatar_tab, "Avatar")
        
        #avatar DOF tabs
        dof_tab = QWidget()
        dof_layout = QVBoxLayout()
        self.dof_avatar_name_label = QLabel("nom d'avatar :")
        self.dof_avatar_name = QComboBox()
        self.dof_avatar_force_label = QLabel("type de conditions :")
        self.dof_avatar_force = QComboBox()
        self.dof_avatar_force.addItems(["rotate", "translate", "imposeDrivenDof", "imposeInitDof"])
        self.dof_options_label = QLabel("Options :  coordonées de translation (exemple dx= , dy =) oubien paramètres de rotation (psi = , center = ) ")
        self.dof_options = QLineEdit("dx = 0.0,  dy = 0.0")
        #self.dof_rotation_label = QLabel("type de rotattion exemple angle d'Euler  : (psi = , center = ) ou bien (description = 'axis', alpha=, axis =, center = )")
        #self.dof_rotation = QLineEdit("psi = -math.pi/2, center = body.nodes[1].coor")
        dof_layout.addWidget(self.dof_avatar_name_label)
        dof_layout.addWidget(self.dof_avatar_name)
        dof_layout.addWidget(self.dof_avatar_force_label)
        dof_layout.addWidget(self.dof_avatar_force)
        dof_layout.addWidget(self.dof_options_label)
        dof_layout.addWidget(self.dof_options)
        #dof_layout.addWidget(self.dof_rotation_label)
        #dof_layout.addWidget(self.dof_rotation)
        create_dof_button = QPushButton("appliquer")
        create_dof_button.clicked.connect(self.dof_force)
        dof_layout.addWidget(create_dof_button)
        dof_tab.setLayout(dof_layout)
        self.tabs.addTab(dof_tab,"DOF d'un avatar")
        
        #contact law tab
        contact_tab = QWidget()
        contact_layout = QVBoxLayout()
        self.contact_name_lable  = QLabel("nom :")
        self.contact_name  = QLineEdit("iqsc0")
        contact_layout.addWidget(self.contact_name_lable)
        contact_layout.addWidget(self.contact_name)
        self.contact_type = QComboBox()
        self.contact_type.addItems(["FRICTION", "COHESION", "IQS_CLB", "PLANx", "GAP_SGR_CLB", "COUPLED_DOF", "RST_CLB"])
        self.contact_type.setCurrentIndex(2)
        self.contact_properties = QLineEdit("fric=0.3")
        contact_layout.addWidget(QLabel("Type de Loi:"))
        contact_layout.addWidget(self.contact_type)
        contact_layout.addWidget(QLabel("Propriétés (ex. fric=0.3, cn=1e6, ct=1e6):"))
        contact_layout.addWidget(self.contact_properties)
        create_contact_btn = QPushButton("Créer Loi de Contact")
        create_contact_btn.clicked.connect(self.create_contact_law)
        contact_layout.addWidget(create_contact_btn)
        contact_tab.setLayout(contact_layout)
        self.tabs.addTab(contact_tab, "Lois de Contact")

        #Table de visibilité tab
        vis_tab = QWidget()
        vis_layout = QVBoxLayout()
        self.vis_corps_candidat = QComboBox()
        self.vis_corps_candidat.addItem("RBDY2")
        self.vis_corps_antagoniste =QComboBox()
        self.vis_corps_antagoniste.addItem("RBDY2")
        self.candidat_color = QLineEdit("BLUEx")
        self.vis_candidat= QComboBox()
        self.vis_candidat.addItem("DISKx")

        self.vis_antagoniste = QComboBox()
        self.vis_antagoniste.addItem("DISKx")
        self.antagoniste_color = QLineEdit("VERTx")
        self.behav = QComboBox()
        self.vis_alert = QLineEdit("0.1")

        vis_layout.addWidget(QLabel("Corps candidat :"))
        vis_layout.addWidget(self.vis_corps_candidat)
        vis_layout.addWidget(QLabel("candidat :"))
        vis_layout.addWidget(self.vis_candidat)        
        vis_layout.addWidget(QLabel("candidat coleur :"))
        vis_layout.addWidget(self.candidat_color)        
        vis_layout.addWidget(QLabel("Corps antagoniste :"))
        vis_layout.addWidget(self.vis_corps_antagoniste)
        vis_layout.addWidget(QLabel("antagoniste :"))
        vis_layout.addWidget(self.vis_antagoniste)        
        vis_layout.addWidget(QLabel("antagoniste coleur :"))
        vis_layout.addWidget(self.antagoniste_color) 
        vis_layout.addWidget(QLabel("loi de contact  :"))       
        vis_layout.addWidget(self.behav)
        vis_layout.addWidget(QLabel("distance d'alerte  :")) 
        vis_layout.addWidget(self.vis_alert)       

        create_vis_btn = QPushButton("Ajouter à la Table de Visibilité")
        create_vis_btn.clicked.connect(self.add_visibility_rule)
        vis_layout.addWidget(create_vis_btn)
        vis_tab.setLayout(vis_layout)
        self.tabs.addTab(vis_tab, "Tableau de Visibilité")

        #rendu graphique
        render_tabs = QTabWidget()
        splitter.addWidget(render_tabs)
        render_tab = QWidget()
        render_layout = QVBoxLayout()
        #les boutons
        vis_btn = QPushButton("visualisation LMGC90")
        vis_btn.clicked.connect(self.try_lmgc_visualization)
        render_layout.addWidget(vis_btn)
        paraview_btn = QPushButton("exporter vers Paraview")
        paraview_btn.clicked.connect(self.open_paraview)
        render_layout.addWidget(paraview_btn)

        render_tab.setLayout(render_layout)
        render_tabs.addTab(render_tab,"rendu graphique")

        #ajuster    
        splitter.setSizes([300,100])

    def new_project(self):
        self.dim = 2
        self.current_project_dir = None
         # conteneurs LMGC90
        self.bodies = pre.avatars()
        self.bodies_objects = []
        self.avatar_creations = []
        self.materials = pre.materials()
        self.material_objects = []
        self.material_creations = []
        self.models = pre.models()
        self.model_objects =[]
        self.model_creations = []
        self.contact_laws = pre.tact_behavs()
        self.contact_laws_objects = []
        self.contact_creations = []
        self.visibilities_table = pre.see_tables()
        self.visibilities_table_objects = []
        self.visibility_creations = []
        self.dof_options = []
        #matériau
        self.mat_name.setText("TDURx")
        self.mat_type.setCurrentText("RIGID")
        self.mat_density.setText("1000.")
        self.mat_properties.setText("")
        #modèle
        self.model_name.setText("rigid")
        self.model_physics.setCurrentText("MECAx")
        self.model_element.setText("Rxx2D")
        self.model_dimension.setCurrentText("2")
        self.model_options.setText("")
        self.avatar_type.blockSignals(True)
        #avatar
        self.avatar_type.setCurrentText("rigidDisk")
        self.avatar_type.blockSignals(False)
        self.avatar_radius.setText("0.1")
        self.avatar_center.setText("0.0,0.0")
        self.avatar_color.setText("BLUEx")
        self.avatar_properties.setText("")

        #law
        self.contact_name.setText("iqsc0")
        self.contact_type.setCurrentText("IQS_CLB")
        self.contact_properties.setText("fric=0.3")
        # see_table
        self.vis_corps_candidat.setCurrentText("RBDY2")
        self.vis_corps_antagoniste.setCurrentText("RBDY2")
        self.candidat_color.setText("BLUEx")
        self.vis_candidat.setCurrentText("DISKx")
        self.vis_antagoniste.setCurrentText("DISKx")
        self.antagoniste_color.setText("VERTx")
        self.vis_alert.setText("0.1")

        self._initializing = True
        #self.update_avatar_fields(self.avatar_type.currentText())
        self._initializing = False
        self.update_model_tree()
        self.update_selections()
        QMessageBox.information(self, "Succès", f"Nouveau projet crée (vide)")
        
    
    def open_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Ouvrir un projet", "")
        if dir_path:
            self.current_project_dir = dir_path
            json_path  = os.path.join(dir_path, "project.json")
            if os.path.exists(json_path) :
                try : 
                    with open(json_path,  'r') as f : 
                        state = json.load(f)
                    self._deserialize_state(state)
                    self.update_model_tree()
                    self.update_selections()
                    QMessageBox.information(self, "Succès", f"Projet ouvert depuis {dir_path}")
                except Exception as e : 
                    QMessageBox.critical(self, "Erreur ", f" Erreur lors du chargement : {str(e)} ")
            else :
                QMessageBox.critical(self, "Erreur ", f"Aucun fichier project.json trouvé")
                
    def save_project(self):
        if self.current_project_dir is None:
            self.save_as_project()
        else:
            self.do_save(self.current_project_dir)

    def save_as_project(self):
            dir_path = QFileDialog.getExistingDirectory(self,"Sauvegarder le projet dans","")
            if dir_path:
                self.current_project_dir = dir_path
                self.do_save(dir_path)
    def do_save(self, dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
            state = self._serialize_state()
            print(state)
            json_path = os.path.join(dir_path, 'project.json')
            with open(json_path, 'w') as f : 
                json.dump(state, f , indent=4)
            
            QMessageBox.information(self, "Succès", f"Projet sauvegardé dans {dir_path}")
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}" )
    def exit(self):
        sys.exit()

    def _deserialize_state(self, state ) : 
        try : 
            self._initializing = True
            #matériau
            # pour LMGC90
            self.materials = pre.materials()
            self.material_objects = []
            self.material_creations = []
            for mat_dict in state.get('materials', []) :
                mat = pre.material(
                    name = mat_dict['name'],
                    materialType=mat_dict['type'],
                    density = mat_dict['density']
                )
                self.materials.addMaterial(mat)
                self.material_objects.append(mat)
                self.material_creations.append(mat_dict)
            #pour l'interface
            self.mat_name.setText(mat_dict['name'])
            #self.mat_type.setCurrentText(mat_dict['type'])
            self.mat_density.setText(str(mat_dict['density']))
            #modèle
            #pour LMGC90
            self.models = pre.models()
            self.model_objects = []
            self.model_creations = []
            for mod_dict in state.get('models', []) :
                mod = pre.model(
                    name = mod_dict['name'],
                    physics=mod_dict['physics'],
                    element = mod_dict['element'],
                    dimension= mod_dict['dimension'] 

                )
                self.models.addModel(mod)
                self.model_objects.append(mod)
                self.model_creations.append(mod_dict)
            #pour l'interface
            self.model_name.setText(mod_dict['name'])
            #self.model_physics.addItem(mod['physics'])
            self.model_element.setText(mod_dict['element'])
            #self.model_dimension.setText(str(mat_dict['density']))
            self.model_options.setText((mod_dict['options']))

            #avatar
            #pour LMGC90
            self.bodies = pre.avatars()
            self.bodies_objects = []
            self.avatar_creations = []
            for body_dict in state.get('bodies', []) :
                mat = next((m for m in self.material_objects if m.nom == body_dict['material']), None)
                mod = next((m for m in self.model_objects if m.nom == body_dict['model']), None)
                if not mat or not mod:
                    raise ValueError("Material or model not found for avatar")
                if body_dict['type'] == "rigidDisk" :
                    body = pre.rigidDisk(
                        r = body_dict['r'],
                        center=body_dict['coor'],
                        model = mod,
                        material= mat,
                        color= body_dict['color']
                )
                else :  
                    raise ValueError(f"Avatar non existant : {body_dict['type']}")
                #print(body_dict['coor'])
                self.bodies.addAvatar(body)
                self.bodies_objects.append(body)
                self.avatar_creations.append(body_dict)

                self.avatar_material.addItem(body_dict['material'])
                self.avatar_model.addItem(body_dict['model'])
                self.update_selections()
            #pour l'interface    
            self.avatar_radius.setText(str(body_dict['r']))
            self.avatar_center.setText(str(body_dict['coor']).replace('[','').replace(']',''))
            self.avatar_color.setText(body_dict['color'])
            
            #loi de contact 
            #pour LMGC90
            self.contact_laws = pre.tact_behavs()
            self.contact_laws_objects = []
            self.contact_creations = []
            for law_dict in state.get('contact_law', []) :
                law= pre.tact_behav(
                    name= law_dict['name'],
                    law = law_dict['type'],
                    fric = law_dict['fric']
                )
                self.contact_laws.addBehav(law)
                self.contact_laws_objects.append(law)
                self.contact_creations.append(law_dict)
            #pour l'interface
            self.contact_name.setText(law_dict['name'])
            self.contact_properties.setText(str(law_dict['fric']))

            # table de visibilité 
            #pour LMGC90
            self.visibilities_table = pre.see_tables()
            self.visibilities_table_objects = []
            self.visibility_creations = []
            for see_table_dict in state.get('visibility_table', []) :
                see_table = pre.see_table(
                    CorpsCandidat=  see_table_dict['corpsCandidat'],
                    #print(see_table_dict['corpsCandidat'])
                    candidat=  see_table_dict['candidat'],
                    #print(see_table_dict['candidat'])
                    colorCandidat= see_table_dict['candidatColor'],
                    #print(see_table_dict['candidatColor'])
                    CorpsAntagoniste=  see_table_dict['corpsAntagoniste'],
                    #print(see_table_dict['corpsAntagoniste'])
                    antagoniste=  see_table_dict['antagoniste'],
                    #print(see_table_dict['antagoniste'])
                    colorAntagoniste= see_table_dict['antagonisteColor'],
                    #print(see_table_dict['antagonisteColor'])
                    behav= law,
                    alert= see_table_dict['distance']

                )
                self.visibilities_table.addSeeTable(see_table)
                self.visibilities_table_objects.append(see_table)
                self.visibility_creations.append(see_table_dict)
                self.behav.addItem(see_table_dict['contact_name'])
                
            #pour les CL et CI
            self.operations = state.get('operations', [])
            for op in self.operations:
                body = self.bodies_objects[op['body_index']]
                type_ = op['type']
                params = op['params']
                if type_ == 'rotate':
                    body.rotate(**params)
                elif type_ == 'translate':
                    body.translate(**params)
                elif type_ == 'imposeDrivenDof':
                    body.imposeDrivenDof(**params)
                elif type_ == 'imposeInitValue':
                    body.imposeInitValue(**params)
                
            self.update_selections()

            QMessageBox.information(self, 'Succès', 'chargement du fichier json réussi')
        except Exception as e : 
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du chargement du fichier json : {str(e)}')

    def _serialize_state(self):
        #matériau
        materials_list =[]
        for mat in self.material_objects : 
            mat_dict = {
                'name' : mat.nom, 
                'type' : mat.materialType, 
                'density' : mat.density if hasattr(mat, 'density') else None,
                
            }
            materials_list.append(mat_dict)
        
        #modèles
        models_list = [{'name': mod.nom, 
                        'physics': mod.physics, 
                        'element': mod.element, 
                        'dimension': mod.dimension, 
                        'options': mod.options if hasattr(mod, 'options') else ""
                        } for mod in self.model_objects]
        #avatar
        bodies_list = []
        for body in self.bodies_objects :
            body_dict  = {
                'type' : 'rigidDisk' if body.contactors[0].shape == 'DISKx' and body.dimension==2 else 'unknown',
                
                'color' : body.contactors[0].color if hasattr(body.contactors[0], 'color') else 'unknown'
            }
            if hasattr(body.contactors[0], 'byrd') :
                body_dict['r'] = body.contactors[0].byrd
            if hasattr(body.contactors[0], 'shift') :
                body_dict['coor'] = self.center

            if hasattr(body.bulks[0].material, 'nom') :
                body_dict['material'] = body.bulks[0].material.nom
            if hasattr(body.bulks[0].model,'nom') :
                body_dict['model'] = body.bulks[0].model.nom
            bodies_list.append(body_dict)
        
       # contact 
        contact_laws_list = [{
            'name' :   law.nom,
            'type' :   law.law,
            'fric' : law.fric
        } for law in self.contact_laws_objects]
        

        #table visibilité
        see_table_list = []
        for see_table in self.visibilities_table_objects :
            see_table_dict = {
                'corpsCandidat' : see_table.CorpsCandidat,
                'candidat' : see_table.candidat,
                'candidatColor' : see_table.colorCandidat,
                'corpsAntagoniste' :see_table.CorpsAntagoniste,
                'antagoniste' : see_table.antagoniste,
                'antagonisteColor' : see_table.colorAntagoniste ,
                'contact_name' : see_table.behav,
                'distance' : see_table.alert         
        }
            see_table_list.append(see_table_dict)         
        
        #CL et CI 
        operations_list = []
        for op_table in self.operations : 
            op_dict = {
                'body_index' : op_table['body_index'] ,
                'type' : op_table['type'],
                'params' : op_table['params'],
                
            }
            operations_list.append(op_dict)

        
        return {
            'materials' : materials_list,
            'models' : models_list,
            'bodies' : bodies_list,
            'contact_law' : contact_laws_list,
            'visibility_table' : see_table_list,
            'operations' : operations_list, 
        }

    def create_material(self):
        try : 
            properties = eval("dict(" + self.mat_properties.text()+")") if self.mat_properties.text() else {}
            name = self.mat_name.text()
            type_ = self.mat_type.currentText()
            density = float(self.mat_density.text())
            mat = pre.material(name=name, 
                               materialType=type_, 
                               density = density, 
                               **properties)
            self.materials.addMaterial(mat)
            self.material_objects.append(mat)
            self.material_creations.append({
                'name': name,
                'type': type_,
                'density': density,
                #'properties': properties
            })
            self.mats_dict[name] = mat
            self.update_model_tree()
            self.update_selections()
            QMessageBox.information(self,"Succès",f"Matériau créer")
        except Exception as e: 
            QMessageBox.critical(self,"Erreur", f"Erreur lors de la création du matériau : {str(e)}")
   
   
    def update_model_tree(self):
        self.model_tree.clear()
        root = QTreeWidgetItem(self.model_tree, ["Etapes de création du modèle", "",""])
        root.setExpanded(True)
        #pour matériau
        mat_parent = QTreeWidgetItem(root, ["Matériaux", "", f"{len(self.materials)} créés"])
        mat_parent.setData(0, Qt.ItemDataRole.UserRole, 0)
        for mat in self.material_objects:
            QTreeWidgetItem(mat_parent, [mat.nom, mat.materialType, str(mat.density)])

        #pour modèle 
        mod_parent = QTreeWidgetItem(root, ["Modèles", "", f"{len(self.models)} créés"])
        mod_parent.setData(0, Qt.ItemDataRole.UserRole, 1)
        for mod in self.model_objects:
            QTreeWidgetItem(mod_parent, [mod.nom, mod.element, str(mod.dimension)])

        #pour avatar
        cont_parent = QTreeWidgetItem(root, ["Conteneurs", "", ""])
        QTreeWidgetItem(cont_parent, ["Materials", "", f"{len(self.materials)} éléments"])
        QTreeWidgetItem(cont_parent, ["Models", "", f"{len(self.models)} éléments"])
        bodies_cont = QTreeWidgetItem(cont_parent, ["Avatars/Bodies", "", f"{len(self.bodies)} corps"])
        bodies_cont.setData(0, Qt.ItemDataRole.UserRole, 2)
        for body in self.bodies_objects:
            details = []
            details.append(f"rayon : {str(body.bulks[0].avrd)}" )
            QTreeWidgetItem(bodies_cont, ["Corps", ", ".join(details)])
        
        #pour les lois
        contact_parent = QTreeWidgetItem(root, ["Lois de Contact", "", f"{len(self.contact_laws)} créées"])
        contact_parent.setData(0, Qt.ItemDataRole.UserRole, 3)
        for law in self.contact_laws_objects:
            QTreeWidgetItem(contact_parent, [law.nom, law.law])
        
        #pour la table de visibilté
        vis_parent = QTreeWidgetItem(root, ["Tableau de Visibilité", "", f"{len(self.visibilities_table)} règles"])
        vis_parent.setData(0, Qt.ItemDataRole.UserRole, 4)
        for see_table in self.visibilities_table_objects:
            QTreeWidgetItem(vis_parent, [f"detection", "Règle", f"Interaction: "])

    def create_model(self):
        try : 
            properties = eval("dict(" + self.model_options.text() +")") if self.model_options.text() else {}
            name = self.model_name.text()
            physics = self.model_physics.currentText()
            element = self.model_element.text()
            dimension = int(self.model_dimension.currentText())
            mod = pre.model(name= name, 
                            physics=physics,
                            element=element,
                            dimension=dimension,
                            **properties)
            self.models.addModel(mod)
            self.model_objects.append(mod)
            self.model_creations.append({
                'name': name,
                'physics': physics,
                'element': element,
                'dimension': dimension,
                'properties': properties
            })
            self.mods_dict[name] = mod
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

        #Update law Combobox
        self.behav.clear()
        if self.contact_laws_objects :
            for law in self.contact_laws_objects:
                self.behav.addItem(law.nom)
            self.behav.setCurrentIndex(0)
        else:
            self.behav.addItem("Aucune loi de contact disponible")
            self.behav.setEnabled(False)
           # Enable combo boxes if items are available
        self.avatar_material.setEnabled(bool(self.material_objects))
        self.avatar_model.setEnabled(bool(self.model_objects))    
        self.behav.setEnabled(bool(self.contact_laws_objects))
    
    
        #pour avatar dof
        self.dof_avatar_name.clear()
        if self.bodies_objects :
            for body in self.bodies_objects :
                self.dof_avatar_name.addItem(str(body)) 
            self.dof_avatar_name.setCurrentIndex(0)
        else : 
            self.dof_avatar_name.addItem("Aucun avatar disponible")
            self.dof_avatar_name.setEnabled(False)
        self.dof_avatar_name.setEnabled(bool(self.bodies_objects))    


    def create_avatar(self):
        try : 
            import numpy as np
            properties = eval("dict(" + self.avatar_properties.text() + ")") if self.avatar_properties.text() else {}
            avatar_type = self.avatar_type.currentText()
            text  = self.avatar_center.text().split(",")
            mat = self.material_objects[self.avatar_material.currentIndex()]
            mod= self.model_objects[self.avatar_model.currentIndex()]
            x = float(text[0])
            y = float(text[1])
            self.center = [x,y]
            color = self.avatar_color.text()

            if  avatar_type == "rigidDisk" and self.dim ==2:
                body = pre.rigidDisk(
                    r= float(self.avatar_radius.text()),
                    center = self.center ,
                    material=mat,
                    model=mod,
                    color=color,
                    **properties
                    
                )
            else : 
                raise ValueError(f"Avatar non existant : {avatar_type} ")
            self.bodies.addAvatar(body)
            self.bodies_objects.append(body)
            self.bodies_list.append(body)
            self.avatar_creations.append({
                'type': avatar_type,
                'r': float(self.avatar_radius.text()),
                'center': self.center,
                'material': mat.nom,
                'model': mod.nom,
                'color': color,
                'properties': properties
            }
            )
            self.update_model_tree()
            self.update_selections()

            QMessageBox.information(self, "Succès", f" Avatar {avatar_type} créer !")
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'avatar : {str(e)}")
        
    
    def dof_force (self):
        try :
            type_ = self.dof_avatar_force.currentText()
            body_index = self.dof_avatar_name.currentIndex()
            selected_body = self.bodies_objects[body_index]
            params_str = self.dof_options.text()
            params = eval("dict(" + params_str + ")") if params_str else {}
           
            if type_ == 'rotate':
                selected_body.rotate(**params)
            elif type_ == 'translate':
                selected_body.translate(**params)
            elif type_ == 'imposeDrivenDof':
                selected_body.imposeDrivenDof(**params)
            elif type_ == 'imposeInitValue':
                selected_body.imposeInitValue(**params)
            else:
                raise ValueError(f"Unknown DOF type: {type_}")
            self.operations.append({
                'body_index': body_index,
                'type': type_,
                'params': params,
            })
            QMessageBox.information(self, "Succès", f"CL ou CI appliquée")
        except Exception as e : 
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'application de la CL ou CI : {str(e)}")

        
    def create_contact_law(self):
        try :   
            properties = eval("dict(" + self.contact_properties.text() + ")" ) if self.contact_properties.text() else {}
            law  = pre.tact_behav(name = self.contact_name.text(),
                                law = self.contact_type.currentText(),
                                **properties
            )
            self.contact_laws.addBehav(law)
            self.contact_laws_objects.append(law)
            self.update_model_tree()
            self.update_selections()
            QMessageBox.information(self, "Succès", f"Loi de contact crée!")
        except Exception as e :
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de la loi : {str(e)}")

    def add_visibility_rule(self):
        try: 
            see_table = pre.see_table(CorpsCandidat=self.vis_corps_candidat.currentText(),
                                      candidat=self.vis_candidat.currentText(),
                                      colorCandidat=self.candidat_color.text(),
                                      CorpsAntagoniste=self.vis_corps_antagoniste.currentText(),
                                      antagoniste=self.vis_antagoniste.currentText(),
                                      colorAntagoniste=self.antagoniste_color.text(),
                                      behav=self.contact_laws_objects[self.behav.currentIndex()],
                                      alert=self.vis_alert.text())
            self.visibilities_table.addSeeTable(see_table)
            self.visibilities_table_objects.append(see_table)
            QMessageBox.information(self,"Succès",f"table de visibilté crée!")
        except Exception as e:
            QMessageBox.critical(self,"Erreur",f"erreur lors de la création de la table de visibilité :  {str(e)}")

    def try_lmgc_visualization(self):
        try :
            pre.visuAvatars(self.bodies)
            QMessageBox.information(self, "Succès", "Visualisation LMGC90 lancée (fenêtre externe).")
        except Exception as e:
            QMessageBox.critical(self,"Erreur",f"erreur lors de la visualisation :  {str(e)}")
    
    def generate_python_script(self):
        try:
           
            self.script_path = os.path.join(os.path.dirname(self.current_project_dir) or ".", "sample_gen.py")
            with open(self.script_path, 'w', encoding="utf-8") as f:
                f.write("from pylmgc90 import pre\nimport os\n")
                f.write("import math\n")
                f.write("# Conteneurs\n")
                f.write("materials = pre.materials()\n")
                f.write("models = pre.models()\n")
                f.write("bodies = pre.avatars()\n")
                f.write("tacts = pre.tact_behavs()\n")
                f.write("svs = pre.see_tables()\n\n")   
                f.write(f"dim = {self.dim}\n") 
                
                # --- Matériaux ---  
                f.write("# Matériaux\n")
                f.write("mats = {}\n")
                for mat_d in self.material_creations:
                    f.write(f"mat = pre.material(name='{mat_d['name']}', materialType='{mat_d['type']}', density={mat_d['density']})\n")
                    f.write(f"mats['{mat_d['name']}'] = mat\n")
                    f.write("materials.addMaterial(mat)\n")

                
                # --- modèles ---    
                f.write("# Modèles\n")
                f.write("mods = {}\n")
                for mod_d in self.model_creations:
                    f.write(f"mod = pre.model(name='{mod_d['name']}', physics='{mod_d['physics']}', element='{mod_d['element']}', dimension={mod_d['dimension']})\n")
                    f.write(f"mods['{mod_d['name']}'] = mod\n")
                    f.write("models.addModel(mod)\n")
                f.write("\n")
                
                # --- Avatars --- 
                f.write("\n# Avatars / Bodies\n")
                f.write("bodies_list = []\n")
                for av_d in self.avatar_creations:
                    f.write(f"body = pre.{av_d['type']}(r={av_d['r']}, center={repr(av_d['coor'])}, model=mods['{av_d['model']}'], material=mats['{av_d['material']}'], color='{av_d['color']}')\n")
                    f.write("bodies.addAvatar(body)\n")
                    f.write("bodies_list.append(body)\n")
                f.write("\n")
                # --- Conditions aux limites ---
                f.write("\n# Boundary Conditions\n")
                for op in self.operations:
                    i = op['body_index']
                    params_str = ", ".join(f"{k} = {repr(v)}" for k,v in op['params'].items())
                    f.write(f"bodies_list[{i}].{op['type']}({params_str})\n")

                # --- Lois de contact ---
                f.write("\n# Lois de Contact\n")
                f.write("laws = {}\n")
                for law_d in self.contact_creations:
                    f.write(f"law = pre.tact_behav(name='{law_d['name']}', law='{law_d['type']}', fric = {repr(law_d['fric'])})\n")
                    f.write(f"laws['{law_d['name']}'] = law\n")
                    f.write("tacts.addBehav(law)\n")

                # --- Visibilité ---
                f.write("\n# Tableau de Visibilité\n")
                for vis_d in self.visibility_creations:
                    f.write(f"rule = pre.see_table(CorpsCandidat='{vis_d['corpsCandidat']}', candidat='{vis_d['candidat']}', colorCandidat='{vis_d['candidatColor']}', CorpsAntagoniste='{vis_d['corpsAntagoniste']}', antagoniste='{vis_d['antagoniste']}', colorAntagoniste='{vis_d['antagonisteColor']}', behav=laws['{vis_d['contact_name']}'], alert={vis_d['distance']})\n")
                    f.write("svs.addSeeTable(rule)\n")
               
                
                
                f.write("\n\n")

                f.write("post = pre.postpro_commands()")

                f.write(f"\npre.writeDatbox(dim , materials, models, bodies, tacts, svs, post=post)\n")
            QMessageBox.information(self, "Succès", "Génération du script")
        except Exception as e:
            QMessageBox.critical(self,"Erreur",f"erreur lors de la génération du script: {str(e)}")
        
   
    def _get_creation_props(self, obj, creation_list, key, value):
        for item in creation_list:
            if item.get(key) == (value if key != 'name' else getattr(obj, 'nom', None)):
                props = item.get('properties', {})
                return {k: v for k, v in props.items() if v is not None}
        return {}
   
    def execute_python_script(self):
        try : 
            #chemin par défaut
            default_path = self.current_project_dir if self.current_project_dir else os.getcwd()
            if self.script_path and os.path.exists(self.script_path) :
                default_file = self.script_path
            else :
                default_file = os.path.join(default_path, "sample_gen.py")


            file_path, _ = QFileDialog.getOpenFileName(
                self, "Sélectionnez le script python à exécuter", default_file, "Python file (*.py)"
            )    

            if not file_path :
                QMessageBox.critical(self, "Erreur", "Aucun fichier sélectionné pour l'exécution ")
                return
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Erreur ",f"Le fichier {file_path} n'existe pas ")
                return 
            
            #exécuter le script 
            result = subprocess.run(
                ['python', file_path],
                capture_output= True,
                text=True,
                            check=True
            )
            #afficher la sortie 
            output = result.stdout.strip()
            if output :
                QMessageBox.information(self, "Succès", f"script exécuté :\n {output} ") 
            else : 
                QMessageBox.information(self, "Succès", f"script exécuté (aucune sortie)")    
        except Exception as e : 
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue : {str(e)}")

    def open_paraview(self):
        try:
            datbox_path = 'DISPLAY/' if self.current_project_dir is None else os.path.join(self.current_project_dir, 'DISPLAY/')
            if not os.path.exists(datbox_path):
                QMessageBox.warning(self, "Erreur", f"Pas de fichiers de sortie pour affichage !")
            import subprocess
            pvd_file = os.path.join(datbox_path, 'DISPLAY/rigids.pvd')
            if os.path.exists(pvd_file):
                subprocess.run(['paraview', pvd_file])
                QMessageBox.information(self, "Succès", "Paraview lancé.")
            else:
                QMessageBox.warning(self, "Avertissement", f"Fichier {pvd_file} non trouvé. Générez DISPLAY d'abord.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du lancement de Paraview : {str(e)}")
    def apropos(self):
        QMessageBox.information(self,"A propos", "LMGC90_GUI v0.1.0 developpé par B.Zerourou, email : bachir.zerourou@yahoo.fr")

if __name__ == "__main__" :
    app = QApplication (sys.argv)
    window = LMGCUniversalGUI()
    window.show()
    sys.exit(app.exec())