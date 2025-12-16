import sys
import os
import subprocess
import json
import math
import shutil
from functools import partial
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QHBoxLayout, QSplitter, QTabWidget, QLineEdit, QComboBox, QCheckBox, QScrollArea,
    QLabel, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QInputDialog, QGroupBox, QFormLayout, QDialogButtonBox, QDialog
)
from PyQt6.QtCore import Qt
from pylmgc90 import pre

from preferences import PreferencesDialog

from tabs import (
    _create_material_tab, _create_model_tab, _create_avatar_tab,
    _create_empty_avatar_tab, _create_loop_tab, _create_granulo_tab,
    _create_dof_tab, _create_contact_tab, _create_visibility_tab,
    _create_postpro_tab, 
)
from updates import (
    update_model_elements,
    update_avatar_types, update_avatar_fields, 
    update_loop_fields, update_dof_options, update_contact_law,
    update_advanced_fields, update_granulo_fields, update_selections,
    update_model_tree, update_status, _safe_eval_dict
)

class LMGC90GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dim = 2
        self.current_selected = None
        self._initializing = True

        # --- Projet ---
        self.project_name = "Nouveau_Projet"
        self.project_dir = None  # Dossier du projet
        self.model_option_combos = {}   # ← à mettre dans __init__ ou _create_model_tab

        # ----modèle paramètres 
        self.ELEMENT_OPTIONS = {
        "Rxx2D": {}, 
        "Rxx3D": {}, 
        "T3xxx":  {"kinematic": ["small", "large"], "formulation": ["UpdtL", "TotaL"], "mass_storage": ["lump_", "coher"]},
        "Q4xxx":  {"kinematic": ["small", "large"], "formulation": ["UpdtL", "TotaL"], "mass_storage": ["lump_", "coher"]},
        "T6xxx":  {"kinematic": ["small", "large"], "formulation": ["UpdtL", "TotaL"], "mass_storage": ["lump_", "coher"]},
        "Q8xxx":  {"kinematic": ["small", "large"], "formulation": ["UpdtL", "TotaL"], "mass_storage": ["lump_", "coher"]},
        "Q9xxx":  {"kinematic": ["small"], "formulation": ["TotaL"]},
        "SPRG2":  {"kinematic": ["small", "large"], "formulation": ["UpdtL", "TotaL"]},
        "BARxx":  {"kinematic": ["large"], "formulation": ["UpdtL"], "mass_storage": ["lump_"]},
}

        self.GLOBAL_MODEL_OPTIONS = {
        "material": ["elas_", "elasd","J2iso", "J2mix","kvisc"],
        "anisotropy": ["iso__", "ortho"],
        "external_model": ["MatL_", "Demfi", "Umat_", "no___"],
        }

        # Paramètres par défaut de l'application
        self.app_settings = {
            'default_dir': os.getcwd(), # Dossier courant par défaut
            'lmgc90_exec': ''
        }
        # --- Unités par défaut (SI) ---
        self.project_units = {
            "Longueur": "m", 
            "Masse": "kg", 
            "Temps": "s",
            "Volume" : "m^3",
            "Force": "N", 
            "Pression/Contrainte": "Pa", 
            "Densité": "kg/m^3", 
            "Énergie": "J",
            "Température": "K",
            "Flux ther" : "W",
            "Moment inertie" : "kgm^2",
            "Couple" : "Nm" ,
            "Vitesse" : "m/s",
            "Viscosité" : "Ns/m^2"
        }
        
        self._init_containers()
        self._init_ui()
        self.setWindowTitle(f"LMGC90_GUI v0.2.5 - {self.project_name}")
        self.statusBar().showMessage("Prêt")

        update_selections(self)
        update_model_tree(self)
        self._initializing = False
        self.cleanup_operations()
        self.refresh_interface_units()
        

    def _init_containers(self):
        # --- Conteneurs LMGC90 ---
        self.bodies = pre.avatars()
        self.bodies_objects = []
        self.bodies_list = []
        self.avatar_creations = []
        self.bodies_dict = {}

        self.materials = pre.materials()
        self.material_objects = []
        self.material_creations = []
        self.mats_dict = {}

        self.models = pre.models()
        self.model_objects = []
        self.model_creations = []
        self.mods_dict = {}

        self.contact_laws = pre.tact_behavs()
        self.contact_laws_objects = []
        self.contact_creations = []

        self.visibilities_table = pre.see_tables()
        self.visibilities_table_objects = []
        self.visibility_creations = []

        self.operations = []
        self.current_project_dir = None
        self.script_path = None

        self.granulo_generations = []
        #postpro_commands
        self.postpro_creations = [] # Liste de dictionnaires {'name': str, 'step': int}

        # --- Boucles ---
        self.loop_creations = []  # Sauvegarde des boucles
        # ---stockage des groupes d'avatars créés par les boucles ===
        self.avatar_groups = {}    
        self.group_names = [] 
    def _init_ui(self):
        
        self.setGeometry(100, 100, 1000, 700)
        self.statusBar()

        # --- Menu ---
        menu = QMenuBar(self)
        self.setMenuBar(menu)
        file_menu = menu.addMenu("Fichier")
        file_menu.addAction("Nouveau", self.new_project)
        file_menu.addAction("Ouvrir", self.open_project)
        file_menu.addAction("Sauvegarder", self.save_project)
        file_menu.addAction("Sauvegarder sous...", self.save_project_as)
        file_menu.addAction("Quitter", self.close)
        tools_menu = menu.addMenu("Outils")
        tools_menu.addAction("Options ", self.open_options_dialog)
        menu.addMenu("Help").addAction("À propos", self.about)
        #racourci menu  
        file_menu.actions()[0].setShortcut("Ctrl+N")  # Nouveau
        file_menu.actions()[1].setShortcut("Ctrl+O")  # Ouvrir
        file_menu.actions()[2].setShortcut("Ctrl+S")  # Sauvegarder
        file_menu.actions()[3].setShortcut("Ctrl+Shift+S")  # Sauvegarder sous
        file_menu.actions()[4].setShortcut("Ctrl+Q")  # Quitter
        # --- Menu Outils ---
       

        # --- Toolbar ---
        tb = QToolBar("Actions")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        for text, icon, slot in [
            ("Nouveau", self.style().StandardPixmap.SP_FileIcon, self.new_project),
            ("Ouvrir", self.style().StandardPixmap.SP_DirOpenIcon, self.open_project),
            ("Sauvegarder", self.style().StandardPixmap.SP_DriveHDIcon, self.save_project),
            ("Script", self.style().StandardPixmap.SP_FileDialogDetailedView, self.generate_python_script),
            ("Exécuter", self.style().StandardPixmap.SP_MediaPlay, self.execute_python_script),
        ]:
            btn = QPushButton(text)
            btn.setIcon(self.style().standardIcon(icon))
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        # --- Arbre ---
        dock = QDockWidget("Arbre du modèle", self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Élément", "Type", "Détails"])
        self.tree.itemClicked.connect(self.activate_tab)
        dock.setWidget(self.tree)
        dock.setMinimumWidth(500)

        # --- Onglets ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)

        # creation des tabs
        _create_material_tab(self)
        _create_model_tab(self)
        _create_avatar_tab(self)
        _create_empty_avatar_tab(self)
        _create_loop_tab(self)
        _create_granulo_tab(self)
        _create_dof_tab(self)
        _create_contact_tab(self)
        _create_visibility_tab(self)
        _create_postpro_tab(self)
        
        # --- Rendu ---
        render_tabs = QTabWidget()
        splitter.addWidget(render_tabs)
        render_tab = QWidget()
        rl = QVBoxLayout()
        lmgc_vis_btn = QPushButton("LMGC visualisation")
        lmgc_vis_btn.clicked.connect(self.visu_lmgc)
        rl.addWidget(lmgc_vis_btn)
        paraview_btn = QPushButton("ParaView")
        paraview_btn.clicked.connect(self.open_paraview)
        rl.addWidget(paraview_btn)
        render_tab.setLayout(rl)
        render_tabs.addTab(render_tab, "Rendu")

        splitter.setSizes([400, 200])

    
    
    #=== GRANULO
    def refresh_granulo_combos(self):
        """Met à jour les listes déroulantes quand on clique sur l'onglet"""
        # Sauvegarde sélection actuelle
        cur_mat = self.gran_mat.currentText()
        cur_mod = self.gran_mod.currentText()
        
        self.gran_mat.clear()
        self.gran_mod.clear()
        
        # Remplissage
        self.gran_mat.addItems([m.nom for m in self.material_objects])
        self.gran_mod.addItems([m.nom for m in self.model_objects])
        
        # Restauration
        if cur_mat: self.gran_mat.setCurrentText(cur_mat)
        if cur_mod: self.gran_mod.setCurrentText(cur_mod)
        
    def generate_granulo_sample(self):
        if not self.material_objects or not self.model_objects:
            QMessageBox.warning(self, "Attention", "Veuillez créer au moins un Matériau et un Modèle d'abord.")
            return

        # Vérification Dimension 2D
        if self.dim != 2:
            QMessageBox.warning(self, "Attention", "Les fonctions de dépôt automatique (depositIn...) ne fonctionnent qu'en 2D pour l'instant.")
            return

        try:
            # 1. Récupération des paramètres
            nb = int(self.gran_nb.text())
            rmin = float(self.gran_rmin.text())
            rmax = float(self.gran_rmax.text())
            
            seed_txt = self.gran_seed.text().strip()
            seed = int(seed_txt) if seed_txt else None

            mat = self.material_objects[self.gran_mat.currentIndex()]
            mod = self.model_objects[self.gran_mod.currentIndex()]
            color = self.gran_color.text()

            self.statusBar().showMessage("Génération de la distribution et calcul du placement...")
            QApplication.processEvents()
            # 2. Génération de la liste des rayons
            radii = pre.granulo_Random(nb, rmin, rmax, seed)
            # 3. Calcul des positions (Dépôt)
            shape = self.gran_shape_type.currentText()
            coor = None
            container_params = {}

            if "Box2D" in shape:
                lx = float(self.gran_lx.text())
                ly = float(self.gran_ly.text())
                container_params = {'type': 'Box2D', 'lx': lx, 'ly': ly}
                nb_remaining, coor = pre.depositInBox2D(radii, lx, ly)
                
            elif "Disk2D" in shape:
                r = float(self.gran_r.text())
                container_params = {'type': 'Disk2D', 'r': r}
                nb_remaining, coor = pre.depositInDisk2D(radii, r)
                
            elif "Couette2D" in shape:
                rint = float(self.gran_rint.text())
                rext = float(self.gran_rext.text())
                container_params = {'type': 'Couette2D', 'rint': rint, 'rext': rext}
                nb_remaining, coor = pre.depositInCouette2D(radii, rint, rext)
                
            elif "Drum2D" in shape:
                r = float(self.gran_r.text())
                container_params = {'type': 'Drum2D', 'r': r}
                nb_remaining, coor = pre.depositInDrum2D(radii, r)

            if coor is None:
                raise ValueError("Le dépôt a échoué. Essayez de réduire la densité (moins de particules ou plus grand conteneur).")

            # 4. Création des Avatars (Particules)
            nb_remaining = np.shape(coor)[0]//2
            coor = np.reshape(coor,(nb_remaining,2))
            body = None

            avatar = self.avatar.currentText()
            for i in range(nb_remaining):
                if avatar == "rigidDisk" :
                    body = pre.rigidDisk(r=radii[i], center=coor[i], model=mod, material=mat, color=color)
                else : 
                    QMessageBox.information(self,"informations", f"les autres avatars ne sont pas encore implémentés")
                    break

                self.bodies.addAvatar(body)
                self.bodies_objects.append(body)
                self.bodies_list.append(body)
                
                # Ajout pour sauvegarde et script
                self.avatar_creations.append({
                    'type': 'rigidDisk',
                    'r': float(radii[i]),
                    'center': coor[i].tolist(),
                    'model': mod.nom,
                    'material': mat.nom,
                    'color': color,
                    'is_Hollow': False,
                    '__from_loop': True # Marqueur interne
                    
                })

                 #granulo_dict
            granulo_dict = {
                'type' : 'granulo',
                'nb': nb,
                'rmin' : rmin,
                'rmax' : rmax,
                'seed': seed,
                'container_params': container_params,
                'mat_name': mat.nom,
                'mod_name': mod.nom,
                'color': color,
                'avatar_type': avatar
            }
            if  avatar == "Box2D" :
                granulo_dict['lx'] = lx
                granulo_dict['ly'] = ly
            elif avatar == "Disk2D" :
                granulo_dict['r'] =  r,

            self.granulo_generations.append(granulo_dict)

            msg = f"{nb_remaining} particules générées."

            # 5. Création des Murs (Optionnel)
            if self.gran_wall_create.isChecked():
                if container_params['type'] == 'box':
                    lx, ly = container_params['lx'], container_params['ly']
                    wall_col = "WALLx"
                    
                    # Définition des 4 murs (Sol, Plafond, Gauche, Droite) avec rigidJonc
                    walls_defs = [
                        {'axe1': lx/2.0, 'axe2': 0.05, 'center': [0, -ly/2.0], 'angle': 0}, # Bas
                        {'axe1': lx/2.0, 'axe2': 0.05, 'center': [0, ly/2.0],  'angle': 0}, # Haut
                        {'axe1': ly/2.0, 'axe2': 0.05, 'center': [-lx/2.0, 0], 'angle': math.pi/2.0}, # Gauche
                        {'axe1': ly/2.0, 'axe2': 0.05, 'center': [lx/2.0, 0],  'angle': math.pi/2.0}, # Droite
                    ]

                    for w_def in walls_defs:
                        w = pre.rigidJonc(axe1=w_def['axe1'], axe2=w_def['axe2'], center=w_def['center'], 
                                          model=mod, material=mat, color=wall_col)
                        if w_def['angle'] != 0:
                            w.rotate( psi=w_def['angle'], center=w_def['center'])
                        
                        self.bodies.addAvatar(w)
                        self.bodies_objects.append(w)
                        self.bodies_list.append(w)
                        
                        # Sauvegarde
                        self.avatar_creations.append({
                            'type': 'rigidJonc', 'axe1': w_def['axe1'], 'axe2': w_def['axe2'],
                            'center': w_def['center'], 'model': mod.nom, 'material': mat.nom, 'color': wall_col
                        })
                    
                    msg += "\n+ 4 Murs (Boîte) créés."
                
                elif container_params['type'] in ['disk', 'drum', 'couette']:
                    msg += "\n(Info: La création automatique de murs circulaires n'est pas supportée, ajoutez un xKSID ou Polygone manuellement)."

            update_selections(self)
            update_model_tree(self)
            self.statusBar().showMessage("Dépôt terminé.")
            QMessageBox.information(self, "Succès", msg)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur Granulo", f"{e}")
    # ========================================
    # UTILITAIRES
    # ========================================

    ''' Met à jour les options disponibles selon l'action DOF sélectionnée
        action : str : action DOF sélectionnée'''
    def update_dof_options(self, action) :
        forces = {
            "translate" : "dx=0.0 , dy=2.0",
            "rotate" : "psi=math.pi/2.0, center=[0.0, 0.0]",
            "imposeDrivenDof" : "component=[1,2,3], dofty='vlocy'",
            "imposeInitValue" : "component= 1, value= 3.0"
        }
        self.dof_options.setText(forces.get(action, "dx=0.0, dy=2.0"))

    def model_dimension_changed(self, dim_text) :
        self.dim = int(dim_text)              # garde la dimension globale
        update_avatar_types(self, dim_text)    # remplissage du ComboBox des avatars
        # ré-initialise le texte du centre selon la dimension
        default_center = "0.0,0.0" if self.dim == 2 else "0.0,0.0,0.0"
        self.avatar_center.setText(default_center)
        update_model_elements(self)

  
    ''' Met à jour les champs affichés dans l'onglet Boucles selon le type de boucle sélectionné
        loop_type : str : type de boucle sélectionné'''
    def update_loop_fields(self, loop_type):
            """Affiche ou masque les champs selon le type de boucle"""
            is_manual = (loop_type == "Manuel")

            # Masquer tous les champs géométriques en mode Manuelle
            for item in getattr(self, 'geom_layout_items', []):
                if item and item.widget():
                    item.widget().setVisible(not is_manual)

            # En mode Manuelle : on force le stockage + on peut changer le nombre
            if is_manual:
                self.loop_store_group.setChecked(True)
                self.loop_store_group.setEnabled(False)
                self.loop_count.setEnabled(True)
                self.loop_count.setPlaceholderText("Combien d'avatars veux-tu créer à la main ?")
            else:
                self.loop_store_group.setEnabled(True)
                self.loop_count.setPlaceholderText("")


    def update_contact_law(self): 
        law = self.contact_type.currentText()
        if law in ["IQS_CLB", "IQS_CLB_g0"] :
            self.contact_properties.setText("fric=0.3")
        else : self.contact_properties.setText("")

    def open_options_dialog(self):
        """Ouvre la fenêtre de Préférences (Onglets verticaux)"""
        # On passe les unités ET les chemins actuels
        dialog = PreferencesDialog(self.project_units, self.app_settings, self)
        
        if dialog.exec():
            # 1. Récupération des données
            self.project_units = dialog.get_units_data()
            self.app_settings = dialog.get_paths_data()
            
            # 2. Mise à jour de l'interface (Unité des labels)
            self.refresh_interface_units()
            
            # 3. Confirmation
            path_msg = ""
            if self.app_settings['default_dir']:
                path_msg = f" | Dossier: {os.path.basename(self.app_settings['default_dir'])}"
                
            self.statusBar().showMessage(f"Préférences mises à jour{path_msg}", 5000)

    def refresh_interface_units(self):
        """Met à jour tous les labels de l'interface avec les unités actuelles"""
        u_len = self.project_units.get("Longueur", "m")
        u_mass = self.project_units.get("Masse", "kg")
        u_time = self.project_units.get("Temps", "s")
        u_temp = self.project_units.get("Température", "K")
        # Densité = Masse / Longueur^3
        u_cont = self.project_units.get("Pression/Contrainte", "Pa")
        u_dens = f"{u_mass}/{u_len}³" 
        
        # --- 1. Onglet Matériau ---
        if hasattr(self, 'mat_density'):
            self.mat_density_label.setText(f"Densité ({u_dens})")
            self.mat_props_label.setText(f"Propriétés ( ex : young = 1e9 ({u_cont}))")
            self.mat_props.setPlaceholderText(f"young ({u_cont}), dilatation (1/°{u_temp}), T_ref_meca (°{u_temp}) ")
            # Mise à jour des placeholders (textes grisés) pour guider l'exemple
            self.mat_props.setPlaceholderText(f"ex: young=1e9 ({u_cont}), nu=0.3")
                
        # --- 2. Onglet Avatar ---
        # Rayon / Axes (Longueur)
        if hasattr(self, 'avatar_radius_label'):
            self.avatar_radius_label.setText(f"Rayon ({u_len}) :")
        if hasattr(self, 'avatar_axis_label'):
            self.avatar_axis_label.setText(f"Axes ({u_len}) :")
        if hasattr(self, 'avatar_center_label'):
            self.avatar_center_label.setText(f"Centre x,y ({u_len}) :")
        # --- 3. Onglet Avatar vide ---
        if hasattr(self, 'empty_av_center_label') :
            self.empty_av_center_label.setText(f"Centre (x,y,z) ({u_len}):")
            self.params.setText(f"params ({u_len})")
        # --- 4. Onglet Boucles ---


        # --- 5. Onglet Granulométrie ---
        if hasattr(self, 'gran_rmin_label'):
            self.gran_rmin_label.setText(f"Rayon Min ({u_len}) :")
        if hasattr(self, 'gran_rmax_label'):
            self.gran_rmax_label.setText(f"Rayon Max ({u_len}) :")
        if hasattr(self, 'gran_lx'):
            self.gran_lx.setPlaceholderText(f"({u_len}) :")
        if hasattr(self, 'gran_ly'):
            self.gran_ly.setPlaceholderText(f"{u_len} : ")
         # --- 6. Onglet DOF ---



    # =======================================
    # PostPro Commabds 
    # =======================================

    def add_postpro_command(self):
        name = self.post_name.currentText()
        step_txt = self.post_step.text()
        
        # Validation simple
        if not step_txt.isdigit():
            QMessageBox.warning(self, "Erreur", "Le 'Step' doit être un nombre entier.")
            return
            
        step = int(step_txt)
        
        # 1. Ajout dans les données (pour la sauvegarde/script)
        command_data = {'name': name, 'step': step}
        self.postpro_creations.append(command_data)
        
        # 2. Ajout visuel dans l'arbre
        item = QTreeWidgetItem([name, str(step)])
        self.post_tree.addTopLevelItem(item)
        
        # Feedback
        self.statusBar().showMessage(f"Commande {name} ajoutée.")

    def delete_postpro_command(self):
        selected_item = self.post_tree.currentItem()
        if not selected_item:
            return
            
        # Trouver l'index pour supprimer de la liste de données
        index = self.post_tree.indexOfTopLevelItem(selected_item)
        
        if index >= 0:
            # Supprimer des données
            del self.postpro_creations[index]
            # Supprimer de l'affichage
            self.post_tree.takeTopLevelItem(index)
            self.statusBar().showMessage("Commande supprimée.")
        
    # ========================================
    # EMPTY AVATAR
    # ========================================

    def update_advanced_fields(self, dim_text=None):
        dim = 2 if not dim_text else int(dim_text)
        default = "0.0, 0.0" if dim == 2 else "0.0, 0.0, 0.0"
        if self.adv_center.text() in ["0.0, 0.0", "0.0, 0.0, 0.0"]:
            self.adv_center.setText(default)
        
    def add_contactor_row(self):
        row = QHBoxLayout()
        shape = QComboBox()
        shape.addItems(["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"])
        shape.currentTextChanged.connect(self.update_contactors_fields)
        row.addWidget(QLabel("Forme :"))
        row.addWidget(shape)

        color = QLineEdit("BLUEx")
        row.addWidget(QLabel("Couleur :"))
        row.addWidget(color)

        params = QLineEdit("byrd=0.3")  # ex: r=0.3 ou axe1=1.0,axe2=0.1
        self.params = QLabel("Params :")
        row.addWidget(self.params)
        row.addWidget(params)
       
        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_contactor_row(row))
        row.addWidget(remove_btn)

        widget = QWidget()
        widget.setLayout(row)
        self.contactors_layout.addWidget(widget)
    def update_contactors_fields(self):
        
        for i in range(self.contactors_layout.count()):
                row_widget = self.contactors_layout.itemAt(i).widget()
                if not row_widget: continue
                row = row_widget.layout()
                shape = row.itemAt(1).widget().currentText()
                params = row.itemAt(5).widget()
        if shape in ["DISKx", "xKSID"] :
            params.setText("byrd=0.3")
        if shape == "JONCx" : 
            params.setText("axe1=1.0,axe2=0.1")
        elif shape == "POLYG" :
            params.setText("nb_vertices=4, vertices=[[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]] ")
        elif shape == "PT2Dx" : 
            params.setText("")
    
    
    def remove_contactor_row(self, row_layout):
        for i in reversed(range(self.contactors_layout.count())):
            w = self.contactors_layout.itemAt(i).widget()
            if w and w.layout() == row_layout:
                w.deleteLater()

    def create_empty_avatar(self):
        try:
            dim = int(self.adv_dim.currentText())
            center = [float(x) for x in self.adv_center.text().split(',')]
            if len(center) != dim:
                raise ValueError(f"Attendu {dim} coordonnées")

            mat_idx = self.adv_material.currentIndex()
            mod_idx = self.adv_model.currentIndex()
            if mat_idx < 0 or mod_idx < 0:
                raise ValueError("Créez d'abord au moins un matériau et un modèle avant de créer un avatar vide !")
            mat  = self.material_objects[mat_idx]
            mod = self.model_objects[mod_idx]
            color = self.adv_color.text().strip() or "BLUEx"

            # Création de l'avatar "à la main"
            body = pre.avatar(dimension=dim)
            # Bulk
            if dim == 2:
                body.addBulk(pre.rigid2d())
            else:
                body.addBulk(pre.rigid3d())

            # Node principal
            body.addNode(pre.node(coor=np.array(center), number=1))

            # Groupes, modèle, matériau
            body.defineGroups()
            body.defineModel(model=mod)
            body.defineMaterial(material=mat)

            # Contacteurs
            for i in range(self.contactors_layout.count()):
                row_widget = self.contactors_layout.itemAt(i).widget()
                if not row_widget: continue
                row = row_widget.layout()
                shape = row.itemAt(1).widget().currentText()
                color_c = row.itemAt(3).widget().text().strip() or color
                params_text = row.itemAt(5).widget().text().strip()

                kwargs = _safe_eval_dict(self, params_text)
                if shape in  ["DISKx", "xKSID"]:
                    body.addContactors(shape=shape, color=color_c, byrd=float(kwargs.get('byrd')), shift=kwargs.get('shift'))
               
                elif shape == "JONCx":
                    body.addContactors(shape=shape, color=color_c, axe1=float(kwargs.get('axe1')), axe2=float(kwargs.get('axe2')),shift=kwargs.get('shift'))
                elif shape == "POLYG":
                    body.addContactors(shape=shape, color=color_c, vertices=np.array(kwargs.get('vertices')), nb_vertices=int(kwargs.get('nb_vertices')), shift=kwargs.get('shift'))
                elif shape in ["PT2Dx"]:
                    body.addContactors(shape=shape, color=color_c, shift=kwargs.get('shift'))
                
                else : raise ValueError(f"Contacteur {shape} non géré pour avatar vide")

            # CLÉ : calcul des propriétés rigides
            body.computeRigidProperties()

            # Ajout final
            self.bodies.addAvatar(body)
            self.bodies_objects.append(body)
            self.bodies_list.append(body)

            # Sauvegarde pour rechargement
            contactors_data = []
            for i in range(self.contactors_layout.count()):
                row_widget = self.contactors_layout.itemAt(i).widget()
                if not row_widget: continue
                row = row_widget.layout()
                shape = row.itemAt(1).widget().currentText()
                color_c = row.itemAt(3).widget().text().strip() or color
                params_text = row.itemAt(5).widget().text().strip()
                kwargs = _safe_eval_dict(self,params_text)

                contactors_data.append({
                    'shape': shape,
                    'color': color_c,
                    'params': kwargs
                })

            self.avatar_creations.append({
                'type': 'emptyAvatar',
                'dimension': dim,
                'center': center,
                'material': mat.nom,
                'model': mod.nom,
                'color': color,
                'contactors': contactors_data
            })

            update_selections(self)
            update_model_tree(self)
            QMessageBox.information(self, "Succès", "Avatar vide créé avec succès !")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Avatar vide : {e}")
    
    # ========================================
    # BOUCLES
    # ========================================
    
    def create_loop(self):
        if not self.avatar_creations:
            QMessageBox.critical(self, "Erreur", "Créez d'abord un avatar modèle")
            return

        try:
            loop_type = self.loop_type.currentText()
            model_idx = self.loop_avatar_type.currentIndex()
            model_av = self.avatar_creations[model_idx]
            mat = self.mats_dict[model_av['material']]
            mod = self.mods_dict[model_av['model']]

            n = int(self.loop_count.text())
            radius = float(self.loop_radius.text())
            step = float(self.loop_step.text())
            offset_x = float(self.loop_offset_x.text())
            offset_y = float(self.loop_offset_y.text())
            spiral_factor = float(self.loop_spiral_factor.text())
            # --- Générer centres ---
            centers = []
    
            if loop_type == "Cercle":
                for i in range(n):
                    angle = 2 * math.pi * i / n
                    x = offset_x + radius * math.cos(angle)
                    y = offset_y + radius * math.sin(angle)
                    centers.append([x, y])
            elif loop_type == "Grille":
                side = int(math.sqrt(n)) + 1
                for i in range(n):
                    x = offset_x + (i % side) * step
                    y = offset_y + (i // side) * step
                    centers.append([x, y])
            elif loop_type == "Ligne":
                for i in range(n):
                    if self.loop_inv_axe.isChecked() :
                        x = offset_x
                        y = offset_y +i * step
                    else: 
                        x = offset_x + i * step
                        y = offset_y
                    centers.append([x, y])
            elif loop_type == "Spirale":
                for i in range(n):
                    angle = 2 * math.pi * i / max(1, n//5)
                    r = radius + i * spiral_factor
                    x = offset_x + r * math.cos(angle)
                    y = offset_y + r * math.sin(angle)
                    centers.append([x, y])

            # Créer les avatars
            start_idx = len(self.avatar_creations)
            generated_indices = []
            for center in centers:
                av_type = model_av['type']
                props = {k: v for k, v in model_av.items() if k not in ['type', 'center', 'material', 'model', 'color']}
                #print(props)
                props['center'] = center

                if av_type == "rigidDisk":
                    body = pre.rigidDisk(r=model_av['r'], center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "rigidJonc" and 'axe1' in model_av and 'axe2' in model_av:
                    body = pre.rigidJonc(axe1=model_av['axe1'], axe2=model_av['axe2'], center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "rigidPolygon"   :
                    if  model_av['gen_type'] == "regular" :
                        body = pre.rigidPolygon( model=mod, material=mat, center=center,color=model_av['color'], generation_type= model_av['gen_type'], nb_vertices=int(model_av['nb_vertices']),radius=float(model_av['r']))
                    else : 
                        body = pre.rigidPolygon( model=mod, material=mat, center=center,color=model_av['color'], generation_type= model_av['gen_type'],vertices= np.array(model_av['vertices'], dtype=float) ,radius=float(model_av['r']))
                elif av_type == "rigidOvoidPolygon" :
                    body = pre.rigidOvoidPolygon(ra=float(model_av['ra']), rb=float(model_av['rb']), nb_vertices= int(model_av['nb_vertices']), center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "rigidDiscreteDisk" :
                    body = pre.rigidDiscreteDisk(r=float(props['r']), center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "roughWall" :
                    body = pre.roughWall(l=props['l'], r=float(props['r']), center=center, model=mod, material=mat, color=model_av['color'])
                
                elif av_type == "fineWall" and 'l' in model_av and 'r' in model_av:
                    body = pre.fineWall(
                        l=float(model_av['l']), r=float(model_av['r']), center=center,
                        model=mod, material=mat, color=model_av['color'],  nb_vertex= int(model_av['nb_vertex'])
                        )

                elif av_type == "smoothWall" and 'l' in model_av and 'h' in model_av:
                    body = pre.smoothWall(
                        l=float(model_av['l']), h=float(model_av['h']), center=model_av['center'],
                        model=mod, material=mat, color=model_av['color'], nb_polyg= int(model_av['nb_polyg'])
                        )

                elif av_type == "granuloRoughWall" :
                    body = pre.granuloRoughWall(
                        l=float(model_av['l']), rmin=float(model_av['rmin']), rmax= float(model_av['rmax']),
                        center=center, model=mod, material=mat, color=model_av['color'],
                        nb_vertex= int(model_av['nb_vertex'])
                    )
                else:
                    continue

                self.bodies.addAvatar(body)
                self.bodies_objects.append(body)
                self.bodies_list.append(body)
                # Copier le dict et mettre à jour le centre
                new_av = model_av.copy()
                new_av['center'] = center
                new_av['__from_loop'] = True
                self.avatar_creations.append(new_av)
                generated_indices.append(len(self.bodies_list)-1)
           
           #stockage dans la liste (si demandé)
            if loop_type != "Manuel":
                # Nom par défaut intelligent
                if self.loop_store_group.isChecked() and self.loop_group_name.text().strip():
                    group_name = self.loop_group_name.text().strip()
                else:
                    # Nom auto selon type + compteur
                    base_name = f"{loop_type.lower()}"
                    counter = sum(1 for g in self.group_names if g.startswith(base_name))
                    group_name = f"{base_name}_{counter + 1}"

                self.avatar_groups[group_name] = generated_indices
                if group_name not in self.group_names:
                    self.group_names.append(group_name)
                    self.group_names.sort()  # optionnel : tri alphabétique
            else:
                # Mode Manuel : on garde ta logique existante (déjà corrigée avant)
                group_name = self.loop_group_name.text().strip()
                if not group_name:
                    group_name = f"manuel_{len([g for g in self.group_names if g.startswith('manuel')])+1}"
                self.avatar_groups[group_name] = []
                if group_name not in self.group_names:
                    self.group_names.append(group_name)
           
            # --- Sauvegarder boucle ---
            loop_data = {
                'type': loop_type,
                'model_avatar_index': model_idx,
                'count': n,
                'radius': radius,
                'step': step,
                'invert_axis' : self.loop_inv_axe.isChecked(),
                'offset_x': offset_x,
                'offset_y': offset_y,
                'spiral_factor': spiral_factor,
                'generated_avatar_indices': generated_indices,
                'stored_in_group': group_name
            }
            # à revoir
            self.loop_creations.append(loop_data)
            

            if loop_type  == "Manuel":
                if not self.loop_store_group.isChecked():
                    QMessageBox.warning(self, "Attention", "En mode Manuel, les avatars sont toujours stockés dans une liste nommée.")
                    return
                try:
                    total_to_create = int(self.loop_count.text())
                    if total_to_create <= 0:
                        raise ValueError("Le nombre d'avatars doit être positif.")  
                except :
                    QMessageBox.critical(self, "Erreur", "Nombre d'avatars invalide pour le mode Manuel.")
                    return
            
                group_name = self.loop_group_name.text().strip()
                if not group_name:
                    group_name = f"groupe_{len(self.loop_creations)+1}"
           
                # créer le groupe
                self.avatar_groups[group_name] = []
                if group_name not in self.avatar_groups:
                    self.group_names.append(group_name)
           
                #sauver la boucle manuelle
                loop_data = {
                    'type': "Manuel",
                    'model_avatar_index': self.loop_avatar_type.currentIndex(),
                    'count': total_to_create, 
                    'created_count': 0,
                    'group_name': group_name,
                    'active': True
                }
                 # à voir 
                self.loop_creations.append(loop_data)

                QMessageBox.information(self, "Boucle manuelle activée",
                    f"Crée <b>{total_to_create}</b> avatars dans l’onglet Avatar.\n"
                    f"Ils seront automatiquement ajoutés au groupe : <b>{group_name}</b>\n\n"
                    f"Progression visible dans la barre de statut et dans l’arbre.")

                return

            update_selections(self)
            update_model_tree(self)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Boucle : {e}")
    # ========================================
    # PROJET
    # ========================================
    def new_project(self):
        name, ok = QInputDialog.getText(self, "Nouveau projet", "Nom du projet :", text="Mon_Projet")
        if not ok or not name.strip():
            return
        name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name.strip())
        if not name:
            name = "Projet"
        self.project_name = name
        self.project_dir = None
        # Reset UI
        for widget, default in [
            (self.mat_name, "TDURx"), (self.mat_density, "1000."), (self.mat_props, ""),
            (self.model_name, "rigid"), (self.model_element, "Rxx2D"), (self.model_options, ""),
            (self.avatar_radius, "0.1"), (self.avatar_center, "0.0,0.0"), (self.avatar_color, "BLUEx"),
            (self.contact_name, "iqsc0"), (self.contact_type, "fric=0.3"),
            (self.vis_alert, "0.1")
        ]:
            if isinstance(widget, QLineEdit):
                widget.setText(default)
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        self._init_containers()
        update_selections(self)
        update_model_tree(self)
        self.setWindowTitle(f"LMGC90_GUI v0.2.0 - {self.project_name}")
        update_status(self, "Nouveau projet créé")
        QMessageBox.information(self, "Succès", "Nouveau projet vide")

    def open_project(self):
        file, _ = QFileDialog.getOpenFileName(self, "Ouvrir projet", "", "Projet LMGC90 (*.lmgc90)")
        if not file:
            return
        #•print(file)
        # Recréer matériaux, modèles, avatars, etc.
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.project_dir = os.path.dirname(file)
            self.project_name = state.get("project_name", "Projet_sans_nom")
            self._init_containers()
            self._deserialize_state(state)
     

            self.setWindowTitle(f"LMGC90_GUI v0.2.0 - {self.project_name}")
            update_status(self, f"Projet chargé : {self.project_name}")
            update_model_tree(self)
            update_selections(self)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le projet :\n{e}")

    def save_project(self):
        # Si on n'a jamais sauvegardé → on force "Enregistrer sous"
        if not self.project_dir:
            return self.save_project_as()
        # Sinon : sauvegarde rapide dans le dossier déjà connu
        self.do_save()
        update_status(self, f"Projet sauvegardé : {self.project_name}.lmgc90")

    def save_project_as(self):
        # Demande un dossier
        dir_path = QFileDialog.getExistingDirectory(self, "Choisir le dossier du projet")
        if not dir_path:
         return  # Annulé

        # MET À JOUR LE DOSSIER DU PROJET
        self.project_dir = dir_path

        # Demande un nom de projet si ce n’est pas déjà fait
        if not hasattr(self, 'project_name') or self.project_name == "Nouveau_Projet":
            name, ok = QInputDialog.getText(self, "Nom du projet", "Nom du projet :", text="MonProjet")
            if not ok or not name.strip():
                return
            self.project_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name.strip())

        self.setWindowTitle(f"LMGC90_GUI v0.2.0 - {self.project_name}")
        self.do_save()
        update_status(self, f"Projet enregistré dans : {dir_path}")

    
    def do_save(self):
        """Fonction centrale qui fait vraiment la sauvegarde"""
        os.makedirs(self.project_dir, exist_ok=True)
        json_path = os.path.join(self.project_dir, f"{self.project_name}.lmgc90")

        state = self._serialize_state()

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec sauvegarde :\n{e}")
                return

        QMessageBox.information(self, "Succès", f"Projet sauvegardé !\n{json_path}")

        
    def _serialize_state(self):
        manual_avatars = [av for av in self.avatar_creations if not av.get('__from_loop', False)]
        return {
            'project_name': self.project_name,
            'materials': self.material_creations,
            'models': self.model_creations,
            'avatars': manual_avatars,
            'contact_laws': self.contact_creations,
            'visibility_rules': self.visibility_creations,
            'operations': self.operations,
            'loops' : self.loop_creations,
            'avatar_groups': self.avatar_groups,    
            'group_names' : self.group_names,
            'granulo_generations' : self.granulo_generations
        }

    def _deserialize_state(self, state):
        self.new_project()  # Reset complet
        #----Matériaux
        for m in state.get('materials', []):
            if not all(k in m for k in ['name', 'type', 'density']): continue
            if m['type'] == "RIGID":
                mat = pre.material(name=m['name'], materialType=m['type'], density=m['density'])
            elif m['type'] in  ['ELAS', 'ELAS_DILA', 'VISCO_ELAS', 'ELAS_PLAS', 'THERMO_ELAS', 'PORO_ELAS']:
                mat = pre.material( name=m['name'], materialType=m['type'], density=m['density'], args=m['props'])
            else : 
                mat = pre.material(  m.get('props', {}), name=m['name'], materialType=m['type'], args=m['props'])
            self.materials.addMaterial(mat); self.material_objects.append(mat)
            self.material_creations.append(m); self.mats_dict[m['name']] = mat

        #-----Modèles
        for m in state.get('models', []):
            if not all(k in m for k in ['name', 'physics', 'element', 'dimension']): continue
            if m['element'] in ["Rxx2D", "Rxx3D"] : 
                mod = pre.model(name=m['name'], physics=m['physics'], element=m['element'], dimension=m['dimension'])
            elif m['element'] in ["T3xxx", "Q4xxx","T6xxx","Q8xxx","Q9xxx","BARxx"] : 
                mod = pre.model(name=m['name'], physics=m['physics'], element=m['element'],
                              dimension=m['dimension'], 
                              external_model =  m['external_model'], 
                              kinematic = m['kinematic'], 
                              formulation = m['formulation'] , 
                              material = m['material'], 
                              anisotropy = m['anisotropy'], 
                              mass_storage = m['mass_storage'], )
            self.models.addModel(mod); self.model_objects.append(mod)
            self.model_creations.append(m); self.mods_dict[m['name']] = mod

        #-------Avatars
        manual_avatars = [av for av in state.get('avatars', []) if not av.get('__from_loop', False)]
        for av in manual_avatars:
            #if not all(k in av for k in ['type', ('r' or ('axe1' and 'axe2')), 'center', 'material', 'model', 'color']): continue
            mat = self.mats_dict.get(av['material']); mod = self.mods_dict.get(av['model'])
            if not mat or not mod: continue
            
            if av['type'] == "rigidDisk"  :
                if av['is_Hollow'] : 
                    body = pre.rigidDisk(r=av['r'], center=av['center'], model=mod, material=mat, color=av['color'], is_Hollow=True)
                else : body = pre.rigidDisk(r=av['r'], center=av['center'], model=mod, material=mat, color=av['color'])
            elif av['type'] == "rigidJonc" :
                body = pre.rigidJonc(axe1=av['axe1'], axe2=av['axe2'], center=av['center'], model=mod, material=mat, color=av['color'])
            elif av['type'] == "rigidPolygon"   :
                if  av['gen_type'] == "regular" :
                    body = pre.rigidPolygon( model=mod, material=mat, center=av['center'],color=av['color'], generation_type= av['gen_type'], nb_vertices=int(av['nb_vertices']),radius=float(av['r']))
                else : 
                    body = pre.rigidPolygon( model=mod, material=mat, center=av['center'],color=av['color'], generation_type= av['gen_type'],vertices= np.array(av['vertices'], dtype=float) ,radius=float(av['r']))
            elif av['type'] == "rigidOvoidPolygon" :
                body = pre.rigidOvoidPolygon(ra=float(av['ra']), rb=float(av['rb']), nb_vertices= int(av['nb_vertices']), center=av['center'], model=mod, material=mat, color=av['color'])
            elif av['type'] == "rigidDiscreteDisk" :
                body = pre.rigidDiscreteDisk(
                    r=float(av['r']), center=av['center'],
                    model=mod, material=mat, color=av['color'])
                
            elif av['type'] == "rigidCluster" :
                body = pre.rigidCluster(
                    r=float(av['r']), nb_disk= int(av['nb_disk']),
                    center=av['center'], model=mod, material=mat, color=av['color'])
                            
            elif av['type'] == "roughWall" :
                body = pre.roughWall(
                    l=float(av['l']), r=float(av['r']), center=av['center'],
                    model=mod, material=mat, color=av['color'], nb_vertex= int(av['nb_vertex']))
            elif av['type'] == "fineWall" :
                body = pre.fineWall(
                    l=float(av['l']), r=float(av['r']), center=av['center'],
                    model=mod, material=mat, color=av['color'],  nb_vertex= int(av['nb_vertex']))
            elif av['type'] == "smoothWall" :
                body = pre.smoothWall(
                    l=float(av['l']), h=float(av['h']), center=av['center'],
                    model=mod, material=mat, color=av['color'], nb_polyg= int(av['nb_polyg']))
            elif av['type'] == "granuloRoughWall" :
                body = pre.granuloRoughWall(
                    l=float(av['l']), rmin=float(av['rmin']), rmax= float(av['rmax']),
                    center=av['center'], model=mod, material=mat, color=av['color'],
                    nb_vertex= int(av['nb_vertex']))
            elif av['type'] == "emptyAvatar" :
                    body = pre.avatar(dimension=len(av['center']))
                    # Bulk
                    if len(av['center']) == 2:
                        body.addBulk(pre.rigid2d())
                    else:
                        body.addBulk(pre.rigid3d())

                    # Node principal
                    body.addNode(pre.node(coor=np.array(av['center']), number=1))

                    # Groupes, modèle, matériau
                    body.defineGroups()
                    body.defineModel(model=mod)
                    body.defineMaterial(material=mat)

                    # Contacteurs
                    for contactor in av.get('contactors', []):
                        shape = contactor['shape']
                        color_c = contactor['color']
                        params = contactor['params']

                        if shape == "DISKx":
                            body.addContactors(shape=shape, color=color_c, byrd=float(params.get('byrd')))
                        elif shape == "xKSID":
                            body.addContactors(shape=shape, color=color_c, byrd=float(params.get('byrd')))
                        elif shape == "JONCx":
                            body.addContactors(shape=shape, color=color_c, axe1=float(params.get('axe1')), axe2=float(params.get('axe2')))
                        elif shape == "POLYG":
                            body.addContactors(shape=shape, color=color_c, vertices=np.array(params.get('vertices')), nb_vertices=int(params.get('nb_vertices')))

            else : continue
            self.bodies.addAvatar(body); self.bodies_objects.append(body); self.bodies_list.append(body)
            av_copy = av.copy(); av_copy['__from_loop']=False
            self.avatar_creations.append(av_copy)

        # --- Recréer les boucles ---
        import math
        self.loop_creations = state.get('loops', [])
        for loop in self.loop_creations:
            idx = loop['model_avatar_index']
            if idx >= len(self.avatar_creations): continue
            model_av = self.avatar_creations[idx]
            mat = self.mats_dict.get(model_av['material'])
            mod = self.mods_dict.get(model_av['model'])
            if not mat or not mod: continue

            n = loop['count']; r = loop['radius']; s = loop['step']
            ox, oy = loop['offset_x'], loop['offset_y']
            sf = loop['spiral_factor']

            centers = []
            if loop['type'] == "Cercle":
                for i in range(n):
                    a = 2 * math.pi * i / n
                    centers.append([ox + r * math.cos(a), oy + r * math.sin(a)])
            elif loop['type'] == "Grille":
                side = int(math.ceil(math.sqrt(n)))
                for i in range(n):
                    centers.append([ox + (i % side) * s, oy + (i // side) * s])
            elif loop['type'] == "Ligne":
                invert = loop.get('invert_axis', False)
                for i in range(n):
                    if invert : 
                        centers.append([ox,  i * s +oy])
                    else :  
                        centers.append([ox + i * s, oy])
            elif loop['type'] == "Spirale":
                for i in range(n):
                    a = 2 * math.pi * i / max(1, n//5)
                    rr = r + i * sf
                    centers.append([ox + rr * math.cos(a), oy + rr * math.sin(a)])

            for center in centers:
                av_type = model_av['type']
                props = {k: v for k, v in model_av.items() if k not in ['type', 'center', 'material', 'model', 'color']}
                props['center'] = center
                body = None
                if av_type == "rigidDisk":
                    if model_av.get('is_Hollow', False) : 
                        body = pre.rigidDisk(r=props.get('r'), center=center, model=mod, material=mat, color=model_av['color'], is_Hollow=True)
                    else : body = pre.rigidDisk(r=props.get('r'), center=center, model=mod, material=mat, color=model_av['color'])
                
                elif av_type == "rigidJonc" :
                    body = pre.rigidJonc(axe1=model_av['axe1'], axe2=model_av['axe2'], center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "rigidPolygon"   :
                    if  model_av['gen_type'] == "regular" :
                        body = pre.rigidPolygon( model=mod, material=mat, center=center,color=model_av['color'], generation_type= model_av['gen_type'], nb_vertices=int(model_av['nb_vertices']),radius=float(model_av['r']))
                    else : 
                        body = pre.rigidPolygon( model=mod, material=mat, center=center,color=model_av['color'], generation_type= model_av['gen_type'],vertices= np.array(model_av['vertices'], dtype=float) ,radius=float(model_av['r']))
                elif av_type == "rigidDiscreteDisk":
                    body = pre.rigidDiscreteDisk(r=props.get('r'), center=center, model=mod, material=mat, color=model_av['color'])
                
                elif av_type == "rigidCluster" :
                    body = pre.rigidCluster(
                        r=float(props['r']), nb_disk= int(props['nb_disk']),
                        center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "roughWall" :
                    body = pre.roughWall(l=props['l'], r=float(props['r']), center=center, model=mod, material=mat, color=model_av['color'])
                elif av_type == "fineWall" :
                    body = pre.fineWall(
                        l=float(model_av['l']), r=float(model_av['r']), center=center,
                        model=mod, material=mat, color=model_av['color'],  nb_vertex= int(model_av['nb_vertex'])
                        )
                elif av_type == "smoothWall" :
                    body = pre.smoothWall(
                        l=float(model_av['l']), h=float(model_av['h']), center=center,
                        model=mod, material=mat, color=model_av['color'], nb_polyg= int(model_av['nb_polyg'])
                        )
                elif av_type == "granuloRoughWall" :
                    body = pre.granuloRoughWall(
                        l=float(model_av['l']), rmin=float(model_av['rmin']), rmax= float(model_av['rmax']),
                        center=center, model=mod, material=mat, color=model_av['color'],
                        nb_vertex= int(model_av['nb_vertex'])
                    )
                elif av_type == "emptyAvatar" :
                    body = pre.avatar(dimension=len(center))
                    # Bulk
                    if len(center) == 2:
                        body.addBulk(pre.rigid2d())
                    else:
                        body.addBulk(pre.rigid3d())

                    # Node principal
                    body.addNode(pre.node(coor=np.array(center), number=1))

                    # Groupes, modèle, matériau
                    body.defineGroups()
                    body.defineModel(model=mod)
                    body.defineMaterial(material=mat)

                    # Contacteurs
                    for contactor in model_av.get('contactors', []):
                        shape = contactor['shape']
                        color_c = contactor['color']
                        params = contactor['params']

                        if shape == "DISKx":
                            body.addContactors(shape=shape, color=color_c, byrd=float(params.get('byrd')))
                        elif shape == "xKSID":
                            body.addContactors(shape=shape, color=color_c, byrd=float(params.get('byrd')))
                        elif shape == "JONCx":
                            body.addContactors(shape=shape, color=color_c, axe1=float(params.get('axe1')), axe2=float(params.get('axe2')))
                        elif shape == "POLYG":
                            body.addContactors(shape=shape, color=color_c, vertices=np.array(params.get('vertices')), nb_vertices=int(params.get('nb_vertices')))

                else:
                    continue
                
                
                if body:
                    self.bodies.addAvatar(body)
                    self.bodies_objects.append(body)
                    self.bodies_list.append(body)
                    new_av = model_av.copy()
                    new_av['center'] = center
                    new_av['__from_loop'] = True
                    self.avatar_creations.append(new_av)
        
        #------Granulométrie 
        
        for granulo in state.get('granulo_generations', []): 
            #création de la granulométrie 
            nb = granulo.get('nb')
            rmin = granulo.get('rmin')
            rmax = granulo.get('rmax')
            #seed = granulo.get('seed') 
            radii = pre.granulo_Random(nb, rmin, rmax)
            #depot 
            params = granulo.get('container_params', {})
            shape = params.get('type')
            if "Box2D" in shape:
                nb_remaining, coor = pre.depositInBox2D(radii, params.get('lx'), params.get('ly'))
            elif "Disk2D" in shape:
                nb_remaining, coor = pre.depositInDisk2D(radii, params.get('r'))
            nb_remaining = np.shape(coor)[0]//2
            coor = np.reshape(coor, (nb_remaining, 2))
            #création des avatars 
            for i in range(nb_remaining):
                if granulo.get('avatar_type') == "rigidDisk" :
                    body = pre.rigidDisk(r=radii[i], center=coor[i], model=mod, material=mat, color=granulo.get('color'))
                    # remplir les listes 
                    if body:
                        self.bodies.addAvatar(body)
                        self.bodies_objects.append(body)
                        self.bodies_list.append(body)
                        self.avatar_creations.append({
                            'type': 'rigidDisk',
                            'r': float(radii[i]),
                            'center': coor[i].tolist(),
                            'model': mod.nom,
                            'material': mat.nom,
                            'color': granulo.get('color'),
                            'is_Hollow': False,
                            '__from_loop': True # Marqueur interne
                        })
 
        #------ Lois
        for law in state.get('contact_laws', []):
            if not all(k in law for k in ['name', 'law']): continue
            print(law)
            if 'fric' in law: 
                l = pre.tact_behav(name=law['name'], law=law['law'], fric=law['fric'])
                print("a fric ")
            else: 
                l = pre.tact_behav(name=law['name'], law=law['law'])
                print("na pas fric")

            self.contact_laws.addBehav(l); self.contact_laws_objects.append(l)
            self.contact_creations.append(law)

        #------ Visibilité
        for rule in state.get('visibility_rules', []):
            law = next((l for l in self.contact_laws_objects if l.nom == rule['behav']), None)
            if not law: continue
            st = pre.see_table(
                CorpsCandidat=rule['CorpsCandidat'], candidat=rule['candidat'], colorCandidat=rule.get('colorCandidat', ''),
                CorpsAntagoniste=rule['CorpsAntagoniste'], antagoniste=rule['antagoniste'], colorAntagoniste=rule.get('colorAntagoniste', ''),
                behav=law, alert=rule.get('alert', 0.1)
            )
            self.visibilities_table.addSeeTable(st); self.visibilities_table_objects.append(st)
            self.visibility_creations.append(rule)

        # Opérations
        self.operations = state.get('operations', [])
        for op in self.operations:
            idx = op['body_index']
            if 0 <= idx < len(self.bodies_list):
                body = self.bodies_list[idx]
                getattr(body, op['type'])(**op['params'])
        
        # to do (rechergerles les groupes d'avatars)
        self.avatar_groups = state.get('avatar_groups', {})
        self.group_names = state.get('group_names', list(self.avatar_groups.keys()))    

        #recréer les liens après recréation des avatars
        for loop in self.loop_creations:
            if loop.get('type') == "Manuel" and 'group_name' in loop:
                group_name = loop.get('group_name')
                if group_name not in self.avatar_groups:
                    self.avatar_groups[group_name] = []
                if group_name not in self.group_names:
                    self.group_names.append(group_name)
            #réactiver la boucle si pas encore terminée
            if loop.get('created_count', 0) < loop.get('count', 0) :
                loop['active'] = True
                                
        update_selections(self)
        update_model_tree(self)
    # ========================================
    # CRÉATIONS
    # ========================================
    def create_material(self):
        try:
            name = self.mat_name.text().strip()
            if not name:
                raise ValueError("Nom vide")

            mat_type = self.mat_type.currentText()
            density_text = self.mat_density.text().strip()
            props = _safe_eval_dict(self,self.mat_props.text())

            # --- Tous les matériaux standards (sauf DISCRET et USER_MAT) ---
            if mat_type in ["RIGID", "ELAS", "ELAS_DILA", "VISCO_ELAS", "ELAS_PLAS", "THERMO_ELAS", "PORO_ELAS"]:
                density = float(density_text) if density_text else 1000.
                mat = pre.material(name=name, materialType=mat_type, density=density, **props)

            # --- DISCRET : ne prend PAS density ---
            #elif mat_type == "DISCRETE":
            #    print(props)
            #    mat = pre.material(name=name, materialType='DISCRETE', masses=props.get('masses', []), stiffnesses=props.get('stiffnesses', []), viscosities=props.get('viscosities', [])  )

            # --- USER_MAT : EXIGE la densité, même si ta loi ne l'utilise pas ! ---
            #elif mat_type == "USER_MAT": 
            #    mat = pre.material(name=name, materialType='USER_MAT',  **props)

            else:
                raise ValueError(f"Type de matériau inconnu : {mat_type}")

            # Ajout commun
            self.materials.addMaterial(mat)
            self.material_objects.append(mat)
            self.mats_dict[name] = mat

            # Sauvegarde dans l'historique
            save_dict = {
                'name': name,
                'type': mat_type,
                'density': mat.density if hasattr(mat, 'density') else None,
                'props': props
            }
            self.material_creations.append(save_dict)

            update_selections(self)
            update_model_tree(self)

        except Exception as e:
            QMessageBox.critical(self, "Erreur Matériau", f"{e}")

    def create_model(self):
        try:
            # Récupérer toutes les options sélectionnées
            options = {}
            for opt_name, combo in self.model_option_combos.items():
                selected = combo.currentText()
                if selected:  # seulement si pas vide
                    options[opt_name] = selected
            element = self.model_element.currentText()
            name = self.model_name.text().strip()
            if not name: raise ValueError("Nom vide")
            props = _safe_eval_dict(self,self.model_options.text())
            if element in ["Rxx2D", "Rxx3D"]: 
                mod = pre.model(name=name, physics=self.model_physics.currentText(), element=element,
                            dimension=int(self.model_dimension.currentText()), **props)
            elif element in ["T3xxx","Q4xxx","T6xxx","Q8xxx","Q9xxx","BARxx"] :
                mod = pre.model(name=name, physics=self.model_physics.currentText(), element=element,
                              dimension=int(self.model_dimension.currentText()), 
                              external_model =  options['external_model'], 
                              kinematic = options['kinematic'], 
                              formulation = options['formulation'] , 
                              material = options['material'], 
                              anisotropy = options['anisotropy'], 
                              mass_storage = options['mass_storage'], 
                              **props)
            elif element in ["Rxx3D", "H8xxx", "SHB8x", "H20xx", "SHB6x", "TE10x", "DKTxx","BARxx"] :
                mod = pre.model(name=name, physics=self.model_physics.currentText(), element=element,
                              dimension=int(self.model_dimension.currentText()), 
                              external_model =  options['external_model'], 
                              kinematic = options['kinematic'], 
                              formulation = options['formulation'] , 
                              material = options['material'], 
                              anisotropy = options['anisotropy'], 
                              mass_storage = options['mass_storage'], 
                              **props)
            self.models.addModel(mod); self.model_objects.append(mod)
            model_dict = {'name': name, 'physics': self.model_physics.currentText(), 'element': self.model_element.currentText(),
                                        'dimension': int(self.model_dimension.currentText())}
            if element in ["T3xxx","Q4xxx","T6xxx","Q8xxx","Q9xxx","BARxx"] : 
                model_dict['kinematic'] = options['kinematic']
                model_dict['formulation'] = options['formulation']
                model_dict['external_model'] = options['external_model']
                model_dict['material'] = options['material']
                model_dict['anisotropy'] = options['anisotropy']
                model_dict['mass_storage'] = options['mass_storage']
            self.model_creations.append(model_dict)
            self.mods_dict[name] = mod
            update_selections(self); update_model_tree(self)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Modèle : {e}")

    def create_avatar(self):
        if not self.material_objects or not self.model_objects:
            QMessageBox.critical(self, "Erreur", "Créez un matériau et un modèle")
            return
        try:
            center = [float(x.strip()) for x in self.avatar_center.text().split(',')]
            #vertices = [float(x) for x in self.avatar_vertices.text().split(",")]
            if len(center) != self.dim: raise ValueError(f"Attendu {self.dim} coordonnées")
            props = _safe_eval_dict(self,self.avatar_properties.text())
            mat = self.material_objects[self.avatar_material.currentIndex()]
            mod = self.model_objects[self.avatar_model.currentIndex()]
            type = self.avatar_type.currentText()
            is_hollow = self.avatar_hallowed.isChecked()
            if type == "rigidDisk" :
                if is_hollow :
                   
        # Contacteur xKSID + coque creuse
                        body =  pre.rigidDisk(r=float(self.avatar_radius.text()), center=center, model=mod, material=mat,
                                    color=self.avatar_color.text(),is_Hollow=True)
                
                else :  body = pre.rigidDisk(r=float(self.avatar_radius.text()), center=center, model=mod, material=mat,
                                    color=self.avatar_color.text())
            
            elif type == "rigidJonc":
                center = [float(x) for x in self.avatar_center.text().split(",")]
                
                body = pre.rigidJonc(
                    axe1=float(self.avatar_axis.text().split(',')[0].split('=')[1].strip()),
                    axe2=float(self.avatar_axis.text().split(',')[1].split('=')[1].strip()),
                    center=center,
                    model=mod,
                    material=mat,
                    color=self.avatar_color.text(), **props
                )
            elif type == "rigidPolygon": 
                center = [float(x) for x in self.avatar_center.text().split(",")]
                
                if self.avatar_gen.currentText() == 'regular' :
                    body = pre.rigidPolygon(
                        model=mod,
                        material = mat, 
                        center = center,
                        color=self.avatar_color.text(),
                        generation_type=self.avatar_gen.currentText(),
                        nb_vertices= int(self.avatar_nb_vertices.text()),
                        radius= float(self.avatar_radius.text())               
                    )  
                else : 
                    raw = self.avatar_vertices.text().strip()
                    if not raw:
                        raise ValueError("Champ vertices obligatoire pour le mode full/bevel")
                    vertices_list = eval(raw, {"__builtins__": {}}, {})              # on accepte la même syntaxe que _safe_eval_dict
                    #if not isinstance(vertices, list) or not all(isinstance(p, list) for p in vertices):
                    #    raise ValueError("Vertices doit être une liste de listes [[x,y], …]")
                    vertices = np.array(vertices_list, dtype=float)
                    body = pre.rigidPolygon(
                        model=mod,
                        material = mat, 
                        center = center,
                        color=self.avatar_color.text(),
                        generation_type=self.avatar_gen.currentText(),
                        vertices= vertices,
                        radius= float(self.avatar_radius.text())               
                    )  

            elif type == "rigidOvoidPolygon": 
                body  = pre.rigidOvoidPolygon(
                    ra =float(self.avatar_r_ovoid.text().split(',')[0].split('=')[1].strip()),
                    rb =float(self.avatar_r_ovoid.text().split(',')[1].split('=')[1].strip()),
                    nb_vertices= int(self.avatar_nb_vertices.text()),
                    center = center,
                    model=mod,
                    material = mat, 
                    color = self.avatar_color.text()
                    
                )

            elif type == "rigidDiscreteDisk":
                body = pre.rigidDiscreteDisk(
                    r=float(self.avatar_radius.text()),
                    center=center,
                    model=mod, 
                    material=mat,
                    color=self.avatar_color.text(), 
                    **props
                )

            elif type == 'rigidCluster' :
                body = pre.rigidCluster(
                    r=float(self.avatar_radius.text()),
                    center=center,
                    model=mod,
                    material=mat,
                    color=self.avatar_color.text(),
                    nb_disk= int(self.avatar_nb_vertices.text()),
                )

            elif type == "roughWall":
                body = pre.roughWall(
                    l=float(self.wall_length.text()),
                    r=float(self.wall_height.text()),
                    center=center,
                    model=mod, material=mat,
                    color=self.avatar_color.text(),
                    nb_vertex= int(self.avatar_nb_vertices.text())
                )        

            elif type == "fineWall":
                body = pre.fineWall(
                    l=float(self.wall_length.text()),
                    r=float(self.wall_height.text()),
                    center=center,
                    model=mod, material=mat,
                    color=self.avatar_color.text(),
                    nb_vertex= int(self.avatar_nb_vertices.text())
                )  

            elif type == "smoothWall":
                body = pre.smoothWall(
                    l=float(self.wall_length.text()),
                    h=float(self.wall_height.text()),
                    nb_polyg= int(self.avatar_nb_vertices.text()),
                    center=center,
                    model=mod, material=mat,
                    color=self.avatar_color.text()
                )  

            elif type == "granuloRoughWall":
                body = pre.granuloRoughWall(
                    l=float(self.wall_length.text()),
                    rmin=float(self.wall_height.text().split(',')[0].split('=')[1].strip()),
                    rmax= float(self.wall_height.text().split(',')[1].split('=')[1].strip()),
                    center=center,
                    model=mod, material=mat, color=self.avatar_color.text(),
                    nb_vertex = int(self.avatar_nb_vertices.text())
                )
            
            self.bodies.addAvatar(body); self.bodies_objects.append(body); self.bodies_list.append(body)
            
            body_dict= {
                'type': type,
                'center': center,
                'material': mat.nom, 
                'model': mod.nom, 
                'color': self.avatar_color.text()
            }
            if type == "rigidDisk":
                body_dict['r']= self.avatar_radius.text()
                body_dict['is_Hollow'] = self.avatar_hallowed.isChecked()
            elif type == "rigidDiscreteDisk":
                body_dict['r']= self.avatar_radius.text()
            elif type ==  "rigidJonc" :
                body_dict['axe1'] = self.avatar_axis.text().split(',')[0].split('=')[1].strip()
                body_dict['axe2'] = self.avatar_axis.text().split(',')[1].split('=')[1].strip()
            elif type ==  "rigidPolygon"  and self.avatar_gen.currentText() == "regular":
                body_dict['nb_vertices'] = self.avatar_nb_vertices.text()
                #body_dict['theta'] = self.avatar_theta.text()
                body_dict['gen_type'] = self.avatar_gen.currentText()
                body_dict['r'] = self.avatar_radius.text()
                #print(body_dict['gen_type'])
            elif  type ==  "rigidPolygon" and self.avatar_gen.currentText() == "full":
                body_dict['vertices'] = vertices.tolist()
                #body_dict['theta'] = self.avatar_theta.text()
                body_dict['gen_type'] = self.avatar_gen.currentText()
                body_dict['r'] = self.avatar_radius.text()
                #print(body_dict['gen_type'])
            elif type == "rigidOvoidPolygon":
                body_dict['ra'] = self.avatar_r_ovoid.text().split(',')[0].split('=')[1].strip()
                body_dict['rb'] = self.avatar_r_ovoid.text().split(',')[1].split('=')[1].strip()
                body_dict['nb_vertices'] = self.avatar_nb_vertices.text()

            elif type == "rigidCluster" :
                body_dict['r'] = self.avatar_radius.text()
                body_dict['nb_disk'] = self.avatar_nb_vertices.text()

            elif type in ["fineWall" , "roughWall"] :
                body_dict['l'] = self.wall_length.text()
                body_dict['r'] = self.wall_height.text()
                body_dict['nb_vertex'] = self.avatar_nb_vertices.text()
            elif type == "smoothWall" :
                body_dict['l'] = self.wall_length.text()
                body_dict['h'] = self.wall_height.text()
                body_dict['nb_polyg'] = self.avatar_nb_vertices.text()
            elif type =="granuloRoughWall"  :
                body_dict['l'] = self.wall_length.text()
                body_dict['rmin']= self.wall_height.text().split(',')[0].split('=')[1].strip()
                body_dict['rmax'] = self.wall_height.text().split(',')[1].split('=')[1].strip()
                body_dict['nb_vertex'] = self.avatar_nb_vertices.text()
            else : 
                ValueError("Rigide non connue!")
            
            self.avatar_creations.append(body_dict)
          
            # to do : ajouter dans un groupe si demandé
            new_index = len(self.bodies_list)-1
            added_to_manual = False
            for loop in self.loop_creations:
                if loop.get('type') == 'Manuel' and loop.get('active', False):
                    group_name = loop['group_name']
                    if group_name not in self.avatar_groups:
                        self.avatar_groups[group_name] = []
                        if group_name not in self.group_order:
                            self.group_order.append(group_name)

                    self.avatar_groups[group_name].append(new_index)
                    loop['created_count'] = loop.get('created_count', 0) + 1

                    # Vérifie si on a atteint le nombre demandé
                    if loop['created_count'] >= loop['count']:
                        loop['active'] = False
                        QMessageBox.information(self, "Groupe complet !",
                            f"Le groupe <b>{group_name}</b> est terminé : {loop['count']} avatars créés.\n"
                            f"Tu peux maintenant l'utiliser dans DOF.")
                    update_model_tree(self)
                    added_to_manual = True
                    break  # un seul groupe manuel actif à la fois
            # mise à jour UI
            update_selections(self); update_model_tree(self)
        
            # message visuel si demandé si ajout manuel
            if added_to_manual:
                remaining = loop['count'] - loop['created_count']
                status = "terminé" if remaining == 0 else f"{remaining} avatars restants à créer"
                self.statusBar().showMessage(f"Avatar {new_index} ajouté au groupe manuel <{group_name}> ({status})", 3000)
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Avatar : {e}")

    def dof_force(self):
        if not self.bodies_objects:
            QMessageBox.critical(self, "Erreur", "Aucun avatar")
            return
        try:

            selected_text = self.dof_avatar_name.currentText()
            action = self.dof_avatar_force.currentText()
            params = _safe_eval_dict(self,self.dof_options.text())
            if not isinstance(params, dict):
                raise ValueError("Paramètres invalides")
            
            if selected_text.startswith("GROUPE:"):
                group_name = selected_text.split("GROUPE: ", 1)[1].split(" (", 1)[0]
                #print(group_name)
                indices = self.avatar_groups.get(group_name, [])
                #print(indices)
                if not indices:
                    raise ValueError(f"Groupe '{group_name}' vide ou inexistant")
                for idx in indices: 
                    body = self.bodies_list[idx]
                    getattr(body, action)(**params)
                self.operations.append({'target' : 'group', 'group_name': group_name, 'type': action, 'params': params})
                QMessageBox.information(self, "Succès", f"Action '{action}' appliquée au groupe '{group_name}' ({len(indices)} avatars)")
            else:
                #avatar individuel
                idx = self.dof_avatar_name.currentIndex()
                body = self.bodies_objects[idx]
                getattr(body, action)(**params)  
                self.operations.append({'target':'avatar', 'body_index': idx, 'type': action, 'params': params})
                QMessageBox.information(self, "Succès", f"Action '{action}' appliquée à l'avatar {idx}")    
            update_model_tree(self)
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"DOF : {e}")

    def create_contact_law(self):
        try:
            name = self.contact_name.text().strip()
            if not name: raise ValueError("Nom vide")
            props = _safe_eval_dict(self,self.contact_properties.text())
            type_contact =  self.contact_type.currentText()
            if  type_contact in ["IQS_CLB", "IQS_CLB_g0"] :
                law = pre.tact_behav(name=name, law=self.contact_type.currentText(), **props)
            else : law = pre.tact_behav(name=name, law=self.contact_type.currentText())
            
            law_dict = {'name': name, 'law': law.law}
            if type_contact in  ["IQS_CLB", "IQS_CLB_g0"] :
                law_dict['fric']= props.get('fric')

            self.contact_creations.append(law_dict)
            self.contact_laws.addBehav(law); self.contact_laws_objects.append(law)                          
            update_selections(self); update_model_tree(self)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Loi : {e}")

    def add_visibility_rule(self):
        if not self.contact_laws_objects:
            QMessageBox.critical(self, "Erreur", "Créez une loi")
            return
        try:
            law = self.contact_laws_objects[self.behav.currentIndex()]
            st = pre.see_table(
                CorpsCandidat=self.vis_corps_candidat.currentText(), candidat=self.vis_candidat.currentText(),
                colorCandidat=self.candidat_color.text(), CorpsAntagoniste=self.vis_corps_antagoniste.currentText(),
                antagoniste=self.vis_antagoniste.currentText(), colorAntagoniste=self.antagoniste_color.text(),
                behav=law, alert=float(self.vis_alert.text())
            )
            self.visibilities_table.addSeeTable(st); self.visibilities_table_objects.append(st)
            self.visibility_creations.append({
                'CorpsCandidat': st.CorpsCandidat, 'candidat': st.candidat, 'colorCandidat': st.colorCandidat,
                'CorpsAntagoniste': st.CorpsAntagoniste, 'antagoniste': st.antagoniste, 'colorAntagoniste': st.colorAntagoniste,
                'behav': law.nom, 'alert': st.alert
            })
            update_model_tree(self)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Visibilité : {e}")
  
    # ========================================
    # INTERACTION ARBRE
    # ========================================

    def activate_tab(self, item, column): 
        
        if item.parent() is None: 
            return
        parent_text = item.parent().text(0)
        name = item.text(0).split("-")[0]
        #print(name)
        
        data= item.data(0, Qt.ItemDataRole.UserRole)
        #print(data)
        type, idx = data if data else (None, None)
        #print(type)

        # essai de récupération de l'index
        if parent_text == "Matériaux":
            mat = self.material_objects[idx]
            #print(mat)
            if not mat: return
            self.tabs.setCurrentWidget(self.mat_tab)
            self.mat_name.setText(mat.nom)
            self.mat_type.setCurrentText(mat.materialType)
            self.mat_density.setText(str(mat.density))
            #self.mat_props.setText(str({k: v for k, v in mat.__dict__.items() if k not in ['nom', 'materialType', 'density']}))
            self.current_selected = ("material", mat)
        # essai avec chaine de cara
        elif parent_text == "Modèles":
            mod = next((m for m in self.model_objects if m.nom == name), None)
            if not mod: return
            self.tabs.setCurrentWidget(self.mod_tab)
            self.model_name.setText(mod.nom)
            self.model_physics.setCurrentText(mod.physics)
            self.model_element.setCurrentText(mod.element)
            self.model_dimension.setCurrentText(str(mod.dimension))
            self.current_selected = ("model", mod)

        elif parent_text == "Avatars":
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data[0] != "avatar":
                return
            idx = data[1]  # ← C’est l’indice exact, garanti correct !
            
            if idx < 0 or idx >= len(self.avatar_creations):
                return
            av = self.avatar_creations[idx]
            print(av['type'])
            self.tabs.setCurrentWidget(self.av_tab)
            # --- Mise à jour des champs ---
            self.avatar_type.blockSignals(True)
            self.avatar_type.setCurrentText(av['type'])
            self.avatar_type.blockSignals(False)
            update_avatar_fields(self, av['type'])
            self.avatar_center.setText(",".join(map(str, av['center'])))
            self.avatar_material.setCurrentText(av['material'])
            self.avatar_model.setCurrentText(av['model'])
            self.avatar_color.setText(av['color'])
            # --- Champs spécifiques selon le type ---
            if av['type'] in ["rigidDisk", "rigidDiscreteDisk"]:
                self.avatar_radius.setText(av.get('r', '0.1'))
                self.avatar_hallowed.setChecked(av.get('is_Hollow', False))
            elif av['type'] == "rigidJonc":
                self.avatar_axis.setText(f"axe1 = {av['axe1']}, axe2 = {av['axe2']}")
            elif av['type'] == "rigidPolygon":
                self.avatar_gen.setCurrentText(av['gen_type'])
                self.avatar_radius.setText(av['r'])
                if av['gen_type'] == "regular":
                    self.avatar_nb_vertices.setText(av['nb_vertices'])
                else:
                    self.avatar_vertices.setText(str(av['vertices']))
            elif av['type'] == "rigidOvoidPolygon":
                self.avatar_r_ovoid.setText(f"ra = {av['ra']}, rb = {av['rb']}")
                self.avatar_nb_vertices.setText(av['nb_vertices'])
            elif av['type'] in ["roughWall", "fineWall", "smoothWall", "granuloRoughWall"]:
                self.wall_length.setText(av['l'])
                if av['type'] == "granuloRoughWall":
                    self.wall_height.setText(f"rmin = {av['rmin']}, rmax = {av['rmax']}")
                elif av['type'] == "smoothWall":
                    self.wall_height.setText(av['h'])
                else:
                    self.wall_height.setText(av['r'])
                self.avatar_nb_vertices.setText(av.get('nb_vertex', av.get('nb_polyg', '10')))
            elif av['type'] == "rigidCluster":
                self.avatar_radius.setText(av['r'])
                self.avatar_nb_vertices.setText(av['nb_disk'])
            elif av['type'] == "emptyAvatar":
                # to do empty avatar
                    
                # === ON VA DANS L'ONGLET AVANCÉ ===
                self.tabs.setCurrentWidget(self.empty_tab)

                # Dimension
                self.adv_dim.setCurrentText(str(av['dimension']))

                # Centre
                self.adv_center.setText(",".join(map(str, av['center'])))

                # Couleur globale
                self.adv_color.setText(av.get('color', 'BLUEx'))

                # Matériau & Modèle
                self.adv_material.setCurrentText(av['material'])
                self.adv_model.setCurrentText(av['model'])

                # === Vider les anciens contacteurs ===
                while self.contactors_layout.count():
                    child = self.contactors_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                # === Recréer chaque contacteur ===
                for cont in av.get('contactors', []):
                    self.add_contactor_row()  # ajoute une ligne vide
                    # Récupérer la dernière ligne ajoutée
                    last_widget = self.contactors_layout.itemAt(self.contactors_layout.count() - 1).widget()
                    row = last_widget.layout()

                    # Shape
                    shape_combo = row.itemAt(1).widget()
                    shape_combo.setCurrentText(cont['shape'])

                    # Couleur
                    color_edit = row.itemAt(3).widget()
                    color_edit.setText(cont.get('color', av.get('color', 'BLUEx')))

                    # Paramètres (ex: r=0.3, axe1=1.0, etc.)
                    params_edit = row.itemAt(5).widget()
                    params_str = ", ".join(f"{k}={v}" for k, v in cont.get('params', {}).items())
                    params_edit.setText(params_str)

                self.current_selected = ("avatar", idx)

                pass
            
            self.current_selected = ("avatar", idx)


        elif parent_text == "Lois de contact":
            law = next((l for l in self.contact_laws_objects if l.nom == name), None)
            if not law: return
            self.tabs.setCurrentWidget(self.contact_tab)
            self.contact_name.setText(law.nom)
            self.contact_type.setCurrentText(law.law)
            if hasattr(law, 'fric') :
                self.contact_properties.setText(f"fric={law.fric}")
            else : self.contact_properties.setText("")
            self.current_selected = ("contact", law)
        
        elif parent_text == "Tables de visibilité":
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return
            typ, idx = data
            if typ != "visibility":
                return
            rule = self.visibility_creations[idx]
            # Aller à l'onglet Visibilité
            self.tabs.setCurrentWidget(self.vis_tab)

            # Remplir tous les champs
            self.vis_corps_candidat.setCurrentText(rule['CorpsCandidat'])
            self.vis_candidat.setCurrentText(rule['candidat'])
            self.candidat_color.setText(rule['colorCandidat'])

            self.vis_corps_antagoniste.setCurrentText(rule['CorpsAntagoniste'])
            self.vis_antagoniste.setCurrentText(rule['antagoniste'])
            self.antagoniste_color.setText(rule['colorAntagoniste'])

            # Trouver et sélectionner la bonne loi
            for i, law in enumerate(self.contact_laws_objects):
                if law.nom == rule['behav']:
                    self.behav.setCurrentIndex(i)
                    break
            self.vis_alert.setText(str(rule['alert']))
            # Important : on garde la référence pour Modifier/Supprimer
            self.current_selected = ("visibility", idx)

    def modify_selected(self):
        if not self.current_selected:
            QMessageBox.warning(self, "Sélection", "Sélectionnez un élément dans l'arbre")
            return
        typ, data = self.current_selected
        try:
            if typ == "material":
                mat = data
                mat.nom = self.mat_name.text()
                mat.materialType = self.mat_type.currentText()
                mat.density = float(self.mat_density.text())
                idx = self.material_objects.index(mat)
                self.material_creations[idx]['name'] = mat.nom
                self.material_creations[idx]['density'] = mat.density
                self.mats_dict[mat.nom] = mat
            elif typ == "model":
                mod = data
                mod.nom = self.model_name.text()
                mod.physics = self.model_physics.currentText()
                mod.element = self.model_element.text()
                mod.dimension = int(self.model_dimension.currentText())
                idx = self.model_objects.index(mod)
                self.model_creations[idx].update({"name": mod.nom, "physics": mod.physics,
                                                  "element": mod.element, "dimension": mod.dimension})
                self.mods_dict[mod.nom] = mod
            elif typ == "avatar":
                self.delete_selected()  # on supprime l'ancien
                self.create_avatar()     # on recrée avec les nouvelles valeurs
                return
            elif typ == "contact":
                law = data
                law.nom = self.contact_name.text()
                law.law = self.contact_type.currentText()
                law.fric = float(self.contact_properties.text().split('=')[1].strip())
                idx = self.contact_laws_objects.index(law)
                self.contact_creations[idx].update({"name": law.nom, "law": law.law, "fric": law.fric})
            elif typ == "visibility":
                self.delete_selected()
                self.add_visibility_rule()
                return

            update_model_tree(self)
            update_selections(self)
            QMessageBox.information(self, "Succès", "Modifié avec succès")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def delete_selected(self):
        if not self.current_selected:
            QMessageBox.warning(self, "Aucun", "Sélectionnez un élément")
            return
        typ, obj = self.current_selected
        reply = QMessageBox.question(self, "Confirmer", "Supprimer ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: 
            return

        if typ == "material":
            self.materials.remove(obj)
            self.material_objects.remove(obj)
            self.material_creations = [m for m in self.material_creations if m['name'] != obj.nom]
            self.mats_dict.pop(obj.nom, None)
        elif typ == "model":
            self.models.remove(obj)
            self.model_objects.remove(obj)
            self.model_creations = [m for m in self.model_creations if m['name'] != obj.nom]
            self.mods_dict.pop(obj.nom, None)
        elif typ == "avatar":
            idx = obj
            body = self.bodies_objects[idx]
            self.bodies.remove(body)
            self.bodies_objects.pop(idx)
            self.bodies_list.pop(idx)
            self.avatar_creations.pop(idx)
        elif typ == "contact":
            self.contact_laws.pop(obj)
            self.contact_laws_objects.pop(obj)
            self.contact_creations.pop(obj)
        elif typ == "visibility":
                idx = obj
                st = self.visibilities_table_objects[idx]
                self.visibilities_table.remove(st)
                self.visibilities_table_objects.pop(idx)
                self.visibility_creations.pop(idx)

        update_selections(self)
        update_model_tree(self)
        self.current_selected = None
        QMessageBox.information(self, "Succès", "Supprimé")
    # ========================================
    # CORRECTION ANCIENNES OPERATIONS   
    # ========================================
    
    def cleanup_operations(self):
        """Supprime les anciennes opérations corrompues et les convertit si possible"""
        new_ops = []
        for op in self.operations:
            # On garde seulement les opérations valides
            if isinstance(op, dict):
                if 'target' in op and op['target'] == 'group' and 'group_name' in op:
                    new_ops.append(op)
                elif 'body_index' in op and isinstance(op['body_index'], int):
                    new_ops.append(op)
                # Ancien format "GROUPE: nom" → on ignore (ou on peut tenter de réparer)
                elif isinstance(op.get('body_index'), str) and op['body_index'].startswith("GROUPE:"):
                    # Optionnel : extraire le nom si tu veux sauver
                    pass  # on ignore
                else:
                    new_ops.append(op)  # au cas où
        self.operations = new_ops

    # ========================================
    # ACTIONS/GENERATION SCRIPT
    # ========================================
    def _write_avatar_creation(self, f, i, av, container_name="bodies"):
        #avatar vide
        if av['type'] == 'emptyAvatar':
            self._write_empty_avatar_creation(f, i, av, container_name)
            return

        func = self._get_avatar_function(av)
        params = self._get_avatar_params(av)
        color = av['color']
        model = av['model']
        material = av['material']

        f.write(f"body = pre.{func}(center={av['center']}, ")
        f.write(f"model=mods['{model}'], material=mats['{material}'], color='{color}'")
        if params:
            f.write(", " + ", ".join(f"{k}={v}" for k, v in params.items()))
        f.write(")\n")
        f.write(f"{container_name}.addAvatar(body)\n")
        f.write(f"bodies_list.append(body)\n")
    
    def _write_empty_avatar_creation(self, f, i, av, container_name="bodies"):
        dim = av['dimension']
        center = av['center']
        mat_name = av['material']
        mod_name = av['model']
        color = av.get('color', 'BLUEx')
        number = len(self.bodies_list) - len([a for a in self.avatar_creations if a.get('type') != 'emptyAvatar']) + i + 1

        f.write(f"# --- Avatar vide (manuel) ---\n")
        f.write(f"body = pre.avatar(dimension={dim}, number={number})\n")

        # Bulk
        if dim == 2:
            f.write(f"body.addBulk(pre.rigid2d())\n")
        else:
            f.write(f"body.addBulk(pre.rigid3d())\n")

        # Node principal
        f.write(f"body.addNode(pre.node(coor=np.array({center}), number=1))\n")

        # Groupes, modèle, matériau
        f.write(f"body.defineGroups()\n")
        f.write(f"body.defineModel(model=mods['{mod_name}'])\n")
        f.write(f"body.defineMaterial(material=mats['{mat_name}'])\n")

        # Contacteurs
        for cont in av.get('contactors', []):
            shape = cont['shape']
            color_c = cont.get('color', color)
            params = cont.get('params', {})
            param_str = ", ".join(f"{k}={self._format_value_for_python(v)}" for k, v in params.items())
            if param_str:
                param_str = ", " + param_str
            f.write(f"body.addContactors(shape='{shape}', color='{color_c}'{param_str})\n")

        # FINAL : calcul des propriétés rigides
        f.write(f"body.computeRigidProperties()\n")

        f.write(f"{container_name}.addAvatar(body)\n")
        f.write(f"bodies_list.append(body)\n\n")
    
    def _format_value_for_python(self, value):
        """
        Retourne la valeur formatée correctement pour un script Python LMGC90
        - 'standard', 'isotropic', 'orthotropic' → entre quotes
        - Nombres → sans quotes
        - True/False → sans quotes
        - Tout le reste → entre quotes
        """
        if isinstance(value, (int, float)):
            # Nombre → on garde tel quel
            if value == int(value):
                return str(int(value))
            else:
                return f"{value:.15g}".rstrip('0').rstrip('.')
        
        if isinstance(value, bool):
            return "True" if value else "False"
        
        if value is None:
            return "None"
        
        if isinstance(value, str):
            # Les mots-clés spéciaux de pylmgc90 → entre quotes
            if value in ["standard", "isotropic", "orthotropic", "transverse", "UpdtL", "small", "large"]:
                return f"'{value}'"
            # Si ça commence par un chiffre → c'est une string numérique, on garde entre quotes
            if value.strip() and value.strip()[0].isdigit():
                return f"'{value}'"
            # Sinon, c'est une variable ou un mot → entre quotes
            return f"'{value}'"
        
        # Tout autre cas (listes, etc.)
        return repr(value)
    
    def generate_python_script(self):
        if not self.project_dir:
            QMessageBox.warning(self, "Attention", "Enregistrez d'abord le projet")
            return self.save_project_as()

        path = os.path.join(self.project_dir, f"{self.project_name}.py")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("# -*- coding: utf-8 -*-\n")
                f.write("from pylmgc90 import pre\n")
                f.write("import math\n")
                f.write("import numpy as np\n\n")

                # === Conteneurs ===
                f.write("mats = {}\nmods = {}\nlaws = {}\n")
                f.write("materials = pre.materials()\n")
                f.write("models    = pre.models()\n")
                f.write("bodies    = pre.avatars()\n")
                f.write("tacts     = pre.tact_behavs()\n")
                f.write("see_tables = pre.see_tables()\n\n")
                f.write("bodies_list = []\n\n")

                # === conteneurs nommés (groupes) ===
                f.write("# === Groupes d'avatars (conteneurs nommés) ===\n")
                group_containers = {}
                for group_name in self.avatar_groups.keys():
                    safe_name = group_name.replace(" ", "_").replace("-", "_")
                    f.write(f"{safe_name} = pre.avatars()   # groupe: {group_name}\n")
                    group_containers[group_name] = safe_name
                if not group_containers:
                    f.write("# Aucun groupe défini\n")
                f.write("\n")
                
                
                # === Matériaux ===
                f.write("# === Matériaux ===\n")
                for m in self.material_creations:
                    props_parts = []
                    if 'props' in m and m['props']:
                        for k, v in m['props'].items():
                            formatted = self._format_value_for_python(v)
                            props_parts.append(f"{k}={formatted}")
                    
                    props_str = ""
                    if props_parts:
                        props_str = ", " + ", ".join(props_parts)

                    f.write(f"mats['{m['name']}'] = pre.material(name='{m['name']}', "
                            f"materialType='{m['type']}', density={m['density']}{props_str})\n")
                    f.write(f"materials.addMaterial(mats['{m['name']}'])\n")
                f.write("\n")

                # === Modèles ===
                for m in self.model_creations:
                    props = ""
                    if 'options' in m and m['options']:
                        props = ", " + ", ".join(f"{k}={v}" for k, v in m['options'].items())
                    if m['element'] in ["Rxx2D", "Rxx3D"] : 
                        f.write(f"mods['{m['name']}'] = pre.model(name='{m['name']}', physics='{m['physics']}', "
                            f"element='{m['element']}', dimension={m['dimension']}{props})\n")
                    elif m['element'] in ["T3xxx", "Q4xxx","T6xxx","Q8xxx","Q9xxx","BARxx"] : 
                        f.write(f"mods['{m['name']}'] = pre.model(name='{m['name']}', physics='{m['physics']}', "
                              f"element='{m['element']}', dimension={m['dimension']}, external_model =  '{m['external_model']}', "
                              f"kinematic = '{m['kinematic']}', formulation = '{m['formulation']}' , "
                              f"material = '{m['material']}', anisotropy = '{m['anisotropy']}', mass_storage = '{m['mass_storage']}',{props})\n")
                    f.write(f"models.addModel(mods['{m['name']}'])\n")
                f.write("\n")

                # === Avatars individuels (hors boucles) ===
                f.write("# === Avatars créés manuellement ===\n")
                used_indices = set()
                for loop in self.loop_creations:
                    used_indices.update(loop.get('generated_avatar_indices', []))

                for i, av in enumerate(self.avatar_creations):
                    if i in used_indices:
                        continue
                    self._write_avatar_creation(f, i, av , "bodies")

                # === Boucles automatiques ===
                f.write("# === Boucles automatiques → remplissage des groupes ===\n")
                for loop_idx, loop in enumerate(self.loop_creations):
                    if loop['type'] == "Manuel":
                        continue  # Les manuels sont déjà créés individuellement

                    model_av = self.avatar_creations[loop['model_avatar_index']]
                    group_name = loop.get('stored_in_group')
                    if not group_name or group_name not in group_containers:
                        container = "bodies"
                    else:
                        container = group_containers[group_name]
                    f.write(f"\n# --- Boucle #{loop_idx +1} : {loop['type']} → groupe '{group_name or 'inconnu'}' ---\n")
                    f.write("centers = []\n")

                    ox = loop['offset_x']
                    oy = loop['offset_y']
                    n = loop['count']
                    
                    mat = self.mats_dict[model_av['material']]
                    mod = self.mods_dict[model_av['model']]
                    color = model_av['color']

                    f.write(f"\n# === Boucle : {loop['type']} → groupe '{loop.get('stored_in_group', 'inconnu')}' ===\n")
                    f.write(f"# {loop['count']} avatars du type {model_av['type']}\n")
                    f.write("centers = []\n")

                    if loop['type'] == "Cercle":
                        r = loop['radius']
                        f.write(f"for i in range({n}):\n")
                        f.write(f"    angle = 2*math.pi * i / {n}\n")
                        f.write(f"    centers.append([ {ox} + {r}*math.cos(angle), {oy} + {r}*math.sin(angle) ])\n")

                    elif loop['type'] == "Grille":
                        step = loop['step']
                        side = int(math.ceil(math.sqrt(n)))
                        f.write(f"for i in range({n}):\n")
                        f.write(f"    centers.append([ {ox} + (i % {side})*{step}, {oy} + (i // {side})*{step} ])\n")

                    elif loop['type'] == "Ligne":
                        step = loop['step']
                        inv = loop.get('invert_axis', False)
                        f.write(f"for i in range({n}):\n")
                        if inv:
                            f.write(f"    centers.append([ {ox}, {oy} + i*{step} ])\n")
                        else:
                            f.write(f"    centers.append([ {ox} + i*{step}, {oy} ])\n")

                    elif loop['type'] == "Spirale":
                        r0 = loop['radius']
                        factor = loop['spiral_factor']
                        f.write(f"for i in range({n}):\n")
                        f.write(f"    angle = 2*math.pi * i / max(1, {n}//5)\n")
                        f.write(f"    r = {r0} + i*{factor}\n")
                        f.write(f"    centers.append([ {ox} + r*math.cos(angle), {oy} + r*math.sin(angle) ])\n")

                    # === Génération des avatars dans la boucle ===
                    f.write(f"\nfor center in centers:\n")
                    f.write(f"    body = pre.{self._get_avatar_function(model_av)}(center=center, ")
                    f.write(f"model=mods['{mod.nom}'], material=mats['{mat.nom}'], color='{color}'")

                    # Paramètres spécifiques
                    params = self._get_avatar_params(model_av)
                    if params:
                        f.write(", " + ", ".join(f"{k}={v}" for k, v in params.items()))
                    f.write(")\n")
                    f.write(f"    {container}.append(body)\n")
                    f.write(f"bodies.__iadd__({container})\n")
                f.write("\n")

                # === Avatars manuels (mode boucle Manuel) → vont dans leur groupe ===
                f.write("\n# === Avatars crées en mode Manuel → ajout dans leur groupe ===\n")
                for group_name, indices in self.avatar_groups.items():
                    if not indices:
                        continue
                    safe_name = group_containers.get(group_name, "bodies")
                    for idx in indices:
                        if idx >= len(self.avatar_creations):
                            continue
                        av = self.avatar_creations[idx]
                        if av.get('__from_loop'):  # déjà ajouté via boucle auto
                            continue
                        self._write_avatar_creation(f, av, safe_name)
                
                # ===== Granulométrie 
                f.write("#=== Granulométrie =========\n")
                for gen in self.granulo_generations:
                    f.write(f"nb = {gen['nb']}\n")
                    f.write(f"rmin = {gen['rmin']}\n")
                    f.write(f"rmax = {gen['rmax']}\n")
                    f.write(f"seed = {gen['seed'] if gen['seed'] is not None else 'None'}\n")
                    f.write(f"radii = pre.granulo_Random(nb, rmin, rmax, seed)\n")
                    shape = gen['shape']
                    params = gen['container_params']
                    if "Box2D" in shape:
                        f.write(f"lx = {params['lx']}\n")
                        f.write(f"ly = {params['ly']}\n")
                        f.write(f"nb_remaining, coor = pre.depositInBox2D(radii, lx, ly)\n")
                    elif "Disk2D" in shape:
                        f.write(f"r = {params['r']}\n")
                        f.write("nb_remaining, coor = pre.depositInDisk2D(radii, r)\n")
                    mat_var = f"mats['{gen['mat_name']}']" 
                    mod_var = f"mods['{gen['mod_name']}']"
                    
                    f.write("\n# Création des avatars du lot\n")
                    f.write("nb_remaining = np.shape(coor)[0]//2\n")
                    f.write("coor = np.reshape(coor, (nb_remaining, 2))\n")
                    f.write("for i in range(nb_remaining):\n")
                    
                    if gen['avatar_type'] == "rigidDisk":
                        f.write(f"    body = pre.rigidDisk(r=radii[i], center=coor[i], model={mod_var}, material={mat_var}, color='{gen['color']}')\n")
                    f.write("    bodies.addAvatar(body)\n")
                
                # === Opérations DOF (individuelles + groupes) ===
                f.write("# === Conditions aux limites (DOF) ===\n")
                for op in self.operations:
                    action = op['type']
                    if not action: continue
                    params = op['params']
                    if not isinstance(params, dict):
                        f.write(f"# [IGNORE]: paramètres invalides pour l'opération {action} sur avatar #{idx}\n")
                    # Si c’est un groupe → on boucle sur les indices
                    params_str = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
                    if op.get('target') == 'group' or 'group_name' in op:
                            group_name = op['group_name'] or op.get('target_name')
                            if not group_name:
                                f.write(f"# [IGNORE]: nom de groupe manquant pour l'opération {action}\n")
                            # Nom sécurisé pour variable Python
                            container_var = group_containers.get(group_name, "bodies")
                            #print(container_var)
                            f.write(f"# {action} sur le groupe '{group_name}'\n")
                            f.write(f"{container_var}.{action}( {params_str})\n")

                    else:
                            # Avatar individuel
                            idx = op.get('body_index', -1)
                            f.write(f"# {action} sur avatar individuel #{idx}\n")
                            f.write(f"bodies[{idx}].{action}({params_str})\n")
                            
                           
                f.write("\n")

                # === Lois de contact ===
                for law in self.contact_creations:
                    fric = law.get('fric', 0.3)
                    f.write(f"laws['{law['name']}'] = pre.tact_behav(name='{law['name']}', law='{law['law']}', fric={fric})\n")
                    f.write(f"tacts.addBehav(laws['{law['name']}'])\n")
                f.write("\n")

                # === Tables de visibilité ===
                for rule in self.visibility_creations:
                    f.write(f"sv = pre.see_table(\n")
                    f.write(f"    CorpsCandidat='{rule['CorpsCandidat']}', candidat='{rule['candidat']}', colorCandidat='{rule.get('colorCandidat','')}',\n")
                    f.write(f"    CorpsAntagoniste='{rule['CorpsAntagoniste']}', antagoniste='{rule['antagoniste']}', colorAntagoniste='{rule.get('colorAntagoniste','')}',\n")
                    f.write(f"    behav=laws['{rule['behav']}'], alert={rule.get('alert', 0.1)}\n")
                    f.write(f")\n")
                    f.write(f"see_tables.addSeeTable(sv)\n")
                f.write("\n")

                # ==== Postpro_commands
                # Exemple de ce que devra faire votre générateur plus tard :
                f.write("\n# --- PostPro ---\n")
                f.write("post = pre.postpro_commands()\n")
                for cmd in self.postpro_creations:
                    f.write(f"post.addCommand(pre.postpro_command(name='{cmd['name']}', step={cmd['step']}))\n" )

                # === Écriture finale ===
                f.write("# Écriture du fichier .datbox\n")
                f.write("pre.writeDatbox(post = post, dim=2, mats=materials, mods=models, bodies=bodies, tacts=tacts, sees=see_tables)\n")

            self.script_path = path
            QMessageBox.information(self, "Succès", f"Script généré avec succès !\n{path}")

        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Erreur génération", f"{e}\n\n{traceback.format_exc()}")

    def _get_avatar_function(self, av):
        mapping = {
            "rigidDisk": "rigidDisk",
            "rigidJonc": "rigidJonc",
            "rigidPolygon": "rigidPolygon",
            "rigidOvoidPolygon": "rigidOvoidPolygon",
            "rigidDiscreteDisk": "rigidDiscreteDisk",
            "rigidCluster":  "rigidCluster",
            "roughWall": "roughWall",
            "fineWall": "fineWall",
            "smoothWall": "smoothWall",
            "granuloRoughWall": "granuloRoughWall",
        }
        return mapping.get(av['type'], "rigidDisk")

    def _get_avatar_params(self, av):
        params = {}
        if av['type'] == "rigidDisk":
            params['r'] = av.get('r', 0.1)
            if av.get('is_Hollow', False):
                params['is_Hollow'] = True

        elif av['type'] == "rigidJonc":
            params['axe1'] = av.get('axe1')
            params['axe2'] = av.get('axe2')
        elif av['type'] == "rigidPolygon":
            params['radius'] = av.get('r')
            params['generation_type'] = f"'{av.get('gen_type')}'"
            if av.get('gen_type') == "regular":
                params['nb_vertices'] = av.get('nb_vertices')
            else:
                params['vertices'] = f"np.array({av.get('vertices')})"
        elif av['type'] == "rigidOvoidPolygon":
            params['ra'] = av.get('ra')
            params['rb'] = av.get('rb')
            params['nb_vertices'] = av.get('nb_vertices')

        elif av['type'] == "rigidDiscreteDisk":
            params['r'] = av.get('r', 0.1)
        elif av['type'] == "rigidCluster":
            params['r']= av.get('r', 0.1)
            params['nb_disk'] = av.get('nb_disk', 5) 
        elif av['type'] in ["roughWall", "fineWall"]:
            params['l'] = av.get('l')
            params['r'] = av.get('r')
            params['nb_vertex'] = av.get('nb_vertex', 10)
        elif av['type'] == "smoothWall":
            params['l'] = av.get('l')
            params['h'] = av.get('h')
            params['nb_polyg'] = av.get('nb_polyg', 10)
        elif av['type'] == "granuloRoughWall":
            params['l'] = av.get('l')
            params['rmin'] = av.get('rmin')
            params['rmax'] = av.get('rmax')
            params['nb_vertex'] = av.get('nb_vertex', 10)
        return params

    def execute_python_script(self):
        path = self.script_path or os.path.join(self.current_project_dir or os.getcwd(), "lmgc_sim.py")
        file, _ = QFileDialog.getOpenFileName(self, "Exécuter", path, "Python (*.py)")
        if not file: return
        try:
            result = subprocess.run(['python', file], capture_output=True, text=True, check=True)
            QMessageBox.information(self, "Succès", result.stdout or "Exécuté sans sortie")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"{e}")

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

#######################################
#--------fonction main
##################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(10)
    font.setFamily("Segoe UI")
    app.setFont(font)
    win = LMGC90GUI()
    win.show()
    sys.exit(app.exec())