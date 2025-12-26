import sys
import os
import json
import math
from functools import partial
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QToolBar, QPushButton, QDockWidget,
    QTreeWidget, QHBoxLayout, QSplitter, QTabWidget, QLineEdit, QComboBox,
    QLabel, QWidget, QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from pylmgc90 import pre

from tabs import (
    _create_material_tab, _create_model_tab, _create_avatar_tab,
    _create_empty_avatar_tab, _create_loop_tab, _create_granulo_tab,
    _create_dof_tab, _create_contact_tab, _create_visibility_tab,
    _create_postpro_tab, 
)
from updates import (
    update_avatar_fields,
    update_selections, refresh_interface_units,
    update_model_tree, 
    update_contactors_fields,
    refresh_granulo_combos
)
from project import (
    new_project, open_project, save_project, save_project_as, open_options_dialog
)
from script_gen import (generate_python_script, execute_python_script
)
from visu import visu_lmgc, open_paraview, generate_datbox, about
from dynamic_vars import DynamicVarsDialog
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
        self.msg = ""
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
        self.setWindowTitle(f"LMGC90_GUI v0.2.7 - {self.project_name}")
        self.statusBar().showMessage("Prêt")

        update_selections(self)
        update_model_tree(self)
        self._initializing = False
        self.cleanup_operations()
        refresh_interface_units(self)
        

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
        self.postpro_commands = pre.postpro_commands()
        self.postpro_creations = [] # Liste de dictionnaires {'name': str, 'step': int}

        # --- Boucles ---
        self.loop_creations = []  # Sauvegarde des boucles
        # ---stockage des groupes d'avatars créés par les boucles ===
        self.avatar_groups = {}    
        self.group_names = [] 
        self.dynamic_vars = {}
    def _init_ui(self):
        
        self.setGeometry(100, 100, 1000, 700)
        self.statusBar()
        # --- Menu ---
        menu = QMenuBar(self)
        self.setMenuBar(menu)
        file_menu = menu.addMenu("Fichier")
        file_menu.addAction("Nouveau", lambda : new_project(self))
        file_menu.addAction("Ouvrir", lambda : open_project(self))
        file_menu.addAction("Sauvegarder", lambda : save_project(self))
        file_menu.addAction("Sauvegarder sous...", lambda : save_project_as(self))
        file_menu.addAction("Quitter", self.close)
        tools_menu = menu.addMenu("Outils")
        tools_menu.addAction("Options ", lambda : open_options_dialog(self))
        menu.addMenu("Help").addAction("À propos", lambda: about(self))
        tools_menu.addAction("Définir variables dynamiques", self.open_dynamic_vars_dialog)
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
            ("Nouveau", self.style().StandardPixmap.SP_FileIcon, lambda : new_project(self)),
            ("Ouvrir", self.style().StandardPixmap.SP_DirOpenIcon, lambda : open_project(self)),
            ("Sauvegarder", self.style().StandardPixmap.SP_DriveHDIcon, lambda : save_project(self)),
            ("Script", self.style().StandardPixmap.SP_FileDialogDetailedView, lambda : generate_python_script(self)),
            ("Exécuter", self.style().StandardPixmap.SP_MediaPlay, lambda :execute_python_script(self)),
            ("Générer DATBOX", self.style().StandardPixmap.SP_FileDialogStart, lambda : generate_datbox(self))
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
        lmgc_vis_btn.clicked.connect(lambda: visu_lmgc(self))
        rl.addWidget(lmgc_vis_btn)
        paraview_btn = QPushButton("ParaView")
        paraview_btn.clicked.connect(lambda : open_paraview(self))
        rl.addWidget(paraview_btn)
        render_tab.setLayout(rl)
        render_tabs.addTab(render_tab, "Rendu")
        splitter.setSizes([400, 200])
        self.tabs.currentChanged.connect(lambda index :self.on_tab_changed(index))
        refresh_granulo_combos(self)

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
        
    # ========================================
    # EMPTY AVATAR
    # ========================================   
    def on_tab_changed(self, index):
        """Appelé quand on change d'onglet → rafraîchit les ComboBox si on arrive sur Granulométrie"""
        if hasattr(self, 'gran_tab') and self.tabs.widget(index) == self.gran_tab:
            refresh_granulo_combos(self)
    
    def add_contactor_row(self):
        row = QHBoxLayout()
        shape = QComboBox()
        shape.addItems(["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"])
        shape.currentTextChanged.connect(lambda: update_contactors_fields(self))
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
    
    
    def remove_contactor_row(self, row_layout):
        for i in reversed(range(self.contactors_layout.count())):
            w = self.contactors_layout.itemAt(i).widget()
            if w and w.layout() == row_layout:
                w.deleteLater()

    def open_dynamic_vars_dialog(self):
        dialog = DynamicVarsDialog(self.dynamic_vars, self)
        if dialog.exec():
            self.dynamic_vars = dialog.get_vars()
            self.statusBar().showMessage(f"{len(self.dynamic_vars)} variables dynamiques définies", 5000)
    # ========================================
    # INTERACTION ARBRE
    # ========================================
    def activate_tab(self, item, column): 
        if item.parent() is None:
            return
    
        parent_text = item.parent().text(0)
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not data:
            return
        
        item_type, idx = data

        # === Matériaux ===
        if item_type == "material":
            mat = self.material_objects[idx]
            if not mat:
                return
            self.tabs.setCurrentWidget(self.mat_tab)
            self.mat_name.setText(mat.nom)
            self.mat_type.setCurrentText(mat.materialType)
            self.mat_density.setText(str(mat.density))
            self.current_selected = ("material", mat)

        # === Modèles ===
        elif item_type == "model":
            mod = self.model_objects[idx]
            if not mod:
                return
            self.tabs.setCurrentWidget(self.mod_tab)
            self.model_name.setText(mod.nom)
            self.model_physics.setCurrentText(mod.physics)
            self.model_element.setCurrentText(mod.element)
            self.model_dimension.setCurrentText(str(mod.dimension))
            self.current_selected = ("model", mod)

        # === Avatars ===
        elif item_type == "avatar":
            if idx < 0 or idx >= len(self.avatar_creations):
                return
            av = self.avatar_creations[idx]
            
            if av['type'] == "emptyAvatar":
                self._activate_empty_avatar_tab(av, idx)
            else:
                self._activate_avatar_tab(av, idx)
            
            self.current_selected = ("avatar", idx)

        # === Groupes ===
        elif item_type == "group":
            group_name = idx  # idx est en fait le nom du groupe ici
            indices = self.avatar_groups.get(group_name, [])
            QMessageBox.information(
                self, f"Groupe: {group_name}",
                f"Ce groupe contient {len(indices)} avatar(s).\n\n"
                f"Indices: {indices[:10]}{'...' if len(indices) > 10 else ''}"
            )

        # === Boucles ===
        elif item_type == "loop":
            if idx < 0 or idx >= len(self.loop_creations):
                return
            loop = self.loop_creations[idx]
            self.tabs.setCurrentWidget(self.tabs.widget(4))  # Onglet Boucles
            
            self.loop_type.setCurrentText(loop.get('type', 'Cercle'))
            self.loop_count.setText(str(loop.get('count', 10)))
            self.loop_radius.setText(str(loop.get('radius', 2.0)))
            self.loop_step.setText(str(loop.get('step', 1.0)))
            self.loop_offset_x.setText(str(loop.get('offset_x', 0.0)))
            self.loop_offset_y.setText(str(loop.get('offset_y', 0.0)))
            self.loop_spiral_factor.setText(str(loop.get('spiral_factor', 0.1)))
            
            if loop.get('stored_in_group'):
                self.loop_store_group.setChecked(True)
                self.loop_group_name.setText(loop['stored_in_group'])
            
            self.current_selected = ("loop", idx)

        # === Granulométrie (NOUVEAU) ===
        elif item_type == "granulo":
            if idx < 0 or idx >= len(self.granulo_generations):
                return
            gen = self.granulo_generations[idx]
            self.tabs.setCurrentWidget(self.gran_tab)
            
            # Remplir les champs
            self.gran_nb.setText(str(gen.get('nb', 200)))
            self.gran_rmin.setText(str(gen.get('rmin', 0.05)))
            self.gran_rmax.setText(str(gen.get('rmax', 0.15)))
            
            seed = gen.get('seed')
            self.gran_seed.setText(str(seed) if seed is not None else "")
            
            self.gran_shape_type.setCurrentText(gen.get('shape', 'Box2D'))
            
            # Paramètres du conteneur
            params = gen.get('container_params', {})
            if 'lx' in params:
                self.gran_lx.setText(str(params['lx']))
            if 'ly' in params:
                self.gran_ly.setText(str(params['ly']))
            if 'r' in params:
                self.gran_r.setText(str(params['r']))
            if 'rint' in params:
                self.gran_rint.setText(str(params['rint']))
            if 'rext' in params:
                self.gran_rext.setText(str(params['rext']))
            
            self.gran_color.setText(gen.get('color', 'BLUEx'))
            
            if gen.get('group_name'):
                self.gran_store_group.setChecked(True)
                self.gran_group_name.setText(gen['group_name'])
            
            self.current_selected = ("granulo", idx)

        # === Lois de contact ===
        elif item_type == "contact":
            law = self.contact_laws_objects[idx]
            if not law:
                return
            self.tabs.setCurrentWidget(self.contact_tab)
            self.contact_name.setText(law.nom)
            self.contact_type.setCurrentText(law.law)
            if hasattr(law, 'fric'):
                self.contact_properties.setText(f"fric={law.fric}")
            else:
                self.contact_properties.setText("")
            self.current_selected = ("contact", law)

        # === Visibilité ===
        elif item_type == "visibility":
            if idx < 0 or idx >= len(self.visibility_creations):
                return
            rule = self.visibility_creations[idx]
            self.tabs.setCurrentWidget(self.vis_tab)
            
            self.vis_corps_candidat.setCurrentText(rule['CorpsCandidat'])
            self.vis_candidat.setCurrentText(rule['candidat'])
            self.candidat_color.setText(rule['colorCandidat'])
            self.vis_corps_antagoniste.setCurrentText(rule['CorpsAntagoniste'])
            self.vis_antagoniste.setCurrentText(rule['antagoniste'])
            self.antagoniste_color.setText(rule['colorAntagoniste'])
            
            for i, law in enumerate(self.contact_laws_objects):
                if law.nom == rule['behav']:
                    self.behav.setCurrentIndex(i)
                    break
            
            self.vis_alert.setText(str(rule['alert']))
            self.current_selected = ("visibility", idx)

        # === Post-Processing ===
        elif item_type == "postpro":
            if idx < 0 or idx >= len(self.postpro_creations):
                return
            cmd = self.postpro_creations[idx]
            self.tabs.setCurrentWidget(self.postpro_tab)
            
            self.post_name.setCurrentText(cmd.get('name', ''))
            self.post_step.setText(str(cmd.get('step', 1)))
            
            # Sélection de l'avatar/groupe si applicable
            rigid_set = cmd.get('rigid_set')
            if rigid_set and hasattr(self, 'post_avatar_selector'):
                # Chercher l'index correspondant dans le sélecteur
                for i in range(self.post_avatar_selector.count()):
                    data = self.post_avatar_selector.itemData(i)
                    if data and data[0] == "avatar" and isinstance(rigid_set, list):
                        if len(rigid_set) == 1:
                            # Chercher l'index de cet avatar
                            for j, body in enumerate(self.bodies_list):
                                if body == rigid_set[0]:
                                    if data[1] == j:
                                        self.post_avatar_selector.setCurrentIndex(i)
                                        break
            
            self.current_selected = ("postpro", idx)

        # === Opérations DOF ===
        elif item_type == "operation":
            if idx < 0 or idx >= len(self.operations):
                return
            op = self.operations[idx]
            self.tabs.setCurrentWidget(self.tabs.widget(6))  # Onglet DOF
            
            # Sélectionner l'avatar ou groupe
            if op.get('target') == 'group':
                group_name = op.get('group_name', '')
                for i in range(self.dof_avatar_name.count()):
                    if f"GROUPE: {group_name}" in self.dof_avatar_name.itemText(i):
                        self.dof_avatar_name.setCurrentIndex(i)
                        break
            else:
                body_idx = op.get('body_index', 0)
                if body_idx < self.dof_avatar_name.count():
                    self.dof_avatar_name.setCurrentIndex(body_idx)
            
            self.dof_avatar_force.setCurrentText(op.get('type', 'translate'))
            
            # Restaurer les paramètres
            if 'params_text' in op:
                self.dof_options.setText(op['params_text'])
            elif 'params' in op:
                params_str = ", ".join(f"{k}={v}" for k, v in op['params'].items())
                self.dof_options.setText(params_str)
            
            self.current_selected = ("operation", idx)
        
        
    def _activate_avatar_tab(self, av, idx):
        """Active l'onglet avatar standard avec les données."""
        self.tabs.setCurrentWidget(self.av_tab)
        
        self.avatar_type.blockSignals(True)
        self.avatar_type.setCurrentText(av['type'])
        self.avatar_type.blockSignals(False)
        
        update_avatar_fields(self, av['type'])
        
        self.avatar_center.setText(",".join(map(str, av['center'])))
        self.avatar_material.setCurrentText(av['material'])
        self.avatar_model.setCurrentText(av['model'])
        self.avatar_color.setText(av['color'])
        
        # Champs spécifiques selon le type
        if av['type'] in ["rigidDisk", "rigidDiscreteDisk"]:
            self.avatar_radius.setText(str(av.get('r', '0.1')))
            if av['type'] == "rigidDisk":
                self.avatar_hallowed.setChecked(av.get('is_Hollow', False))
        
        elif av['type'] == "rigidJonc":
            self.avatar_axis.setText(f"axe1 = {av['axe1']}, axe2 = {av['axe2']}")
        
        elif av['type'] == "rigidPolygon":
            self.avatar_gen.setCurrentText(av.get('gen_type', 'regular'))
            self.avatar_radius.setText(str(av.get('r', '0.1')))
            if av.get('gen_type') == "regular":
                self.avatar_nb_vertices.setText(str(av.get('nb_vertices', '5')))
            else:
                self.avatar_vertices.setText(str(av.get('vertices', '[]')))
        
        elif av['type'] == "rigidOvoidPolygon":
            self.avatar_r_ovoid.setText(f"ra = {av['ra']}, rb = {av['rb']}")
            self.avatar_nb_vertices.setText(str(av.get('nb_vertices', '5')))
        
        elif av['type'] == "rigidCluster":
            self.avatar_radius.setText(str(av.get('r', '0.1')))
            self.avatar_nb_vertices.setText(str(av.get('nb_disk', '5')))
        
        elif av['type'] in ["roughWall", "fineWall"]:
            self.wall_length.setText(str(av.get('l', '2.0')))
            self.wall_height.setText(str(av.get('r', '0.1')))
            self.avatar_nb_vertices.setText(str(av.get('nb_vertex', '10')))
        
        elif av['type'] == "smoothWall":
            self.wall_length.setText(str(av.get('l', '2.0')))
            self.wall_height.setText(str(av.get('h', '0.1')))
            self.avatar_nb_vertices.setText(str(av.get('nb_polyg', '10')))
        
        elif av['type'] == "granuloRoughWall":
            self.wall_length.setText(str(av.get('l', '2.0')))
            self.wall_height.setText(f"rmin = {av['rmin']}, rmax = {av['rmax']}")
            self.avatar_nb_vertices.setText(str(av.get('nb_vertex', '10')))


    def _activate_empty_avatar_tab(self, av, idx):
        """Active l'onglet avatar vide avec les données."""
        self.tabs.setCurrentWidget(self.empty_tab)
        
        self.adv_dim.setCurrentText(str(av.get('dimension', 2)))
        self.adv_center.setText(",".join(map(str, av['center'])))
        self.adv_color.setText(av.get('color', 'BLUEx'))
        self.adv_material.setCurrentText(av['material'])
        self.adv_model.setCurrentText(av['model'])
        
        # Vider les anciens contacteurs
        while self.contactors_layout.count():
            child = self.contactors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Recréer chaque contacteur
        for cont in av.get('contactors', []):
            self.add_contactor_row()
            last_widget = self.contactors_layout.itemAt(
                self.contactors_layout.count() - 1
            ).widget()
            row = last_widget.layout()
            
            # Shape
            row.itemAt(1).widget().setCurrentText(cont['shape'])
            # Couleur
            row.itemAt(3).widget().setText(cont.get('color', av.get('color', 'BLUEx')))
            # Paramètres
            params_str = ", ".join(f"{k}={v}" for k, v in cont.get('params', {}).items())
            row.itemAt(5).widget().setText(params_str) 

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