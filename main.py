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
    QTreeWidget, QTreeWidgetItem, QSplitter, QTabWidget, QLineEdit, QComboBox,
    QLabel, QFileDialog, QMessageBox, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
from pylmgc90 import pre


class LMGC90GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dim = 2
        # Drapeau pour contrôler l'initialisation
        self._initializing = True
        self._init_containers()
        self._init_ui()
        self.update_selections()
        self.update_model_tree()

    def _init_containers(self):
        # --- Conteneurs LMGC90 ---
        self.bodies = pre.avatars()
        self.bodies_objects = []
        self.bodies_list = []
        self.avatar_creations = []

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

    def _init_ui(self):
        self.setWindowTitle("LMGC90_GUI v0.1.3 ")
        self.setGeometry(100, 100, 1000, 700)

        # --- Menu ---
        menu = QMenuBar(self)
        self.setMenuBar(menu)
        file_menu = menu.addMenu("Fichier")
        file_menu.addAction("Nouveau", self.new_project)
        file_menu.addAction("Ouvrir", self.open_project)
        file_menu.addAction("Sauvegarder", self.save_project)
        file_menu.addAction("Quitter", self.close)
        menu.addMenu("Help").addAction("À propos", self.about)

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
        dock.setWidget(self.tree)

        # --- Onglets ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)
        tabs = QTabWidget()
        splitter.addWidget(tabs)

        # === Matériau ===
        mat_tab = QWidget()
        ml = QVBoxLayout()
        self.mat_name = QLineEdit("TDURx"); self.mat_type = QComboBox(); self.mat_type.addItems(["RIGID", "ELASTIC"])
        self.mat_density = QLineEdit("1000."); self.mat_props = QLineEdit("")
        for label, widget in [
            ("Nom :", self.mat_name), ("Type :", self.mat_type), ("Densité :", self.mat_density),
            ("Propriétés (ex: young=1e9) :", self.mat_props)
        ]:
            ml.addWidget(QLabel(label)); ml.addWidget(widget)
        btn = QPushButton("Créer matériau"); btn.clicked.connect(lambda: self.create_material()); ml.addWidget(btn)
        mat_tab.setLayout(ml); tabs.addTab(mat_tab, "Matériau")

        # --- Modèle ---
        mod_tab = QWidget()
        mml = QVBoxLayout()
        self.model_name = QLineEdit("rigid")
        self.model_physics = QComboBox(); self.model_physics.addItems(["MECAx"])
        self.model_element = QLineEdit("Rxx2D")
        self.model_dimension = QComboBox(); self.model_dimension.addItems(["2", "3"])
        self.model_dimension.currentTextChanged.connect(self.model_dimension_changed)
        self.model_options = QLineEdit("")
        for w in [QLabel("Nom:"), self.model_name, QLabel("Phys:"), self.model_physics,
                  QLabel("Élément:"), self.model_element, QLabel("Dim:"), self.model_dimension,
                  QLabel("Opts:"), self.model_options,
                  ]:
            mml.addWidget(w)
        create_mod_btn = QPushButton("Créer modèle")
        create_mod_btn.clicked.connect(self.create_model)
        mml.addWidget(create_mod_btn)
        mod_tab.setLayout(mml)
        tabs.addTab(mod_tab, "Modèle")

        # --- Avatar ---
        av_tab = QWidget()
        al = QVBoxLayout()
        self.avatar_types_2d = ["rigidDisk", "rigidJonc", "rigidPolygon"]
        self.avatar_types_3d = ["rigidSphere"]
        self.avatar_type = QComboBox()
        self.avatar_radius_label = QLabel("Rayon");self.avatar_radius = QLineEdit("0.1")
        self.avatar_axis_label = QLabel("Axes :");self.avatar_axis = QLineEdit(("axe1 = 2.0, axe2 = 0.05"))
        self.avatar_vertices_label = QLabel("Vertices : ")
        self.avatar_vertices = QLineEdit("[[-0.5,-0.5],[0.5,-0.5],[0.5,0.5],[-0.5,0.5]]")
        self.avatar_nb_vertices_label  =  QLabel("Nombre de vertices : ")
        self.avatar_nb_vertices  = QLineEdit("5")
        self.avatar_gen_type = QLabel("Type de génération ")
        self.avatar_gen = QComboBox()
        self.avatar_gen.addItems(["regular", "full", "bevel"] )
        self.avatar_gen.currentTextChanged.connect(self.update_polygon_fields)
        self.avatar_center_label = QLabel("Centre:");self.avatar_center = QLineEdit("0.0,0.0")
        self.avatar_material = QComboBox()
        self.avatar_model = QComboBox()
        self.avatar_color = QLineEdit("BLUEx")

        self.avatar_properties = QLineEdit("")
        for w in [QLabel("Type:"), self.avatar_type, self.avatar_radius_label, self.avatar_radius,self.avatar_axis_label,self.avatar_axis,
                  self.avatar_gen_type, self.avatar_gen, self.avatar_nb_vertices_label, self.avatar_nb_vertices, self.avatar_vertices_label, self.avatar_vertices, self.avatar_center_label, self.avatar_center, QLabel("Mat:"), self.avatar_material,
                  QLabel("Mod:"), self.avatar_model, QLabel("Couleur:"), self.avatar_color,
                  QLabel("Props:"), self.avatar_properties,
                  ]:
            al.addWidget(w)
        create_av_btn = QPushButton("Créer avatar")
        create_av_btn.clicked.connect(self.create_avatar)
        al.addWidget(create_av_btn)
        av_tab.setLayout(al)
        tabs.addTab(av_tab, "Avatar")

        # Connecter le signal après la création des widgets, en bloquant les signaux
        self.avatar_type.blockSignals(True)
        self.update_avatar_types(self.model_dimension.currentText())
        self.avatar_type.blockSignals(False)
        self.avatar_type.currentTextChanged.connect(self.update_avatar_fields)

        # Terminer l'initialisation
        self._initializing = False
        self.update_avatar_fields(self.avatar_type.currentText())

        # --- DOF ---
        dof_tab = QWidget()
        dl = QVBoxLayout()
        self.dof_avatar_name = QComboBox()
        self.dof_avatar_force = QComboBox(); self.dof_avatar_force.addItems(["translate", "rotate", "imposeDrivenDof", "imposeInitValue"])
        self.dof_options = QLineEdit("dx=0.0, dy=2.0")
        
        self.dof_avatar_force.currentTextChanged.connect(self.update_dof_options)
        for w in [QLabel("Avatar:"), self.dof_avatar_name, QLabel("Action:"), self.dof_avatar_force,
                  QLabel("Params:"), self.dof_options,
                  ]:
            dl.addWidget(w)
        dof_btn = QPushButton("Appliquer")
        dof_btn.clicked.connect( self.dof_force)
        dl.addWidget(dof_btn)
        dof_tab.setLayout(dl)
        tabs.addTab(dof_tab, "DOF")
        #initialisation du texte 
        self.update_dof_options(self.dof_avatar_force.currentText())

        # --- Contact ---
        contact_tab = QWidget()
        cl = QVBoxLayout()
        self.contact_name = QLineEdit("iqsc0")
        self.contact_type = QComboBox(); self.contact_type.addItems(["IQS_CLB"])
        self.contact_properties = QLineEdit("fric=0.3")
        for w in [QLabel("Nom:"), self.contact_name, QLabel("Type:"), self.contact_type,
                  QLabel("Props:"), self.contact_properties,
                  ]:
            cl.addWidget(w)
        create_law_btn = QPushButton("Créer loi")
        create_law_btn.clicked.connect(lambda : self.create_contact_law())
        cl.addWidget(create_law_btn)
        contact_tab.setLayout(cl)
        tabs.addTab(contact_tab, "Contact")

        # --- Visibilité ---
        vis_tab = QWidget()
        vl = QVBoxLayout()
        self.vis_corps_candidat = QComboBox(); self.vis_corps_candidat.addItem("RBDY2")
        self.vis_candidat = QComboBox(); self.vis_candidat.addItem("DISKx")
        self.candidat_color = QLineEdit("BLUEx")
        self.vis_corps_antagoniste = QComboBox(); self.vis_corps_antagoniste.addItem("RBDY2")
        self.vis_antagoniste = QComboBox(); self.vis_antagoniste.addItem("DISKx")
        self.antagoniste_color = QLineEdit("VERTx")
        self.behav = QComboBox()
        self.vis_alert = QLineEdit("0.1")
        for w in [QLabel("Candidat:"), self.vis_corps_candidat, self.vis_candidat, self.candidat_color,
                  QLabel("Antagoniste:"), self.vis_corps_antagoniste, self.vis_antagoniste, self.antagoniste_color,
                  QLabel("Loi:"), self.behav, QLabel("Alerte:"), self.vis_alert,
                  ]:
            vl.addWidget(w)
        create_visi_btn = QPushButton("Ajouter table de visibilité")
        create_visi_btn.clicked.connect(self.add_visibility_rule)
        vl.addWidget(create_visi_btn)
        vis_tab.setLayout(vl)
        tabs.addTab(vis_tab, "Visibilité")

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

    # ========================================
    # UTILITAIRES
    # ========================================
    def _safe_eval_dict(self, text):
        if not text.strip():
            return {}
        #Autorise math, np, et les listes []
        import math
        import numpy as np

        local = {"math": math, "np": np, "__builtins__": {}}
        try:
            
            exec(f"props = dict({text})", {}, local)
            return local.get('props', {})
        except Exception as e:
            raise ValueError(f"Paramètres invalides : {e}")

    def _add_to_tree(self, parent, name, type_, details=""):
        QTreeWidgetItem(parent, [name, type_, details])


    def update_avatar_types(self, dimension):
        self.avatar_type.blockSignals(True)
        self.avatar_type.clear()
        if dimension == "2":
            self.avatar_type.addItems(self.avatar_types_2d)
        else:
            self.avatar_type.addItems(self.avatar_types_3d)
        self.avatar_type.blockSignals(False)
        
        self.update_avatar_fields(self.avatar_type.currentText())

    def update_avatar_fields(self, avatar_type): 
         if self._initializing:
            return
         
         # Liste des widgets à gérer
         widgets = [
            getattr(self, 'avatar_radius_label', None),
            getattr(self, 'avatar_radius', None),
            getattr(self, 'avatar_center_label', None),
            getattr(self, 'avatar_center', None),
            getattr(self, 'avatar_axis_label', None),
            getattr(self, 'avatar_axis', None),
            getattr(self, 'avatar_vertices_label', None),
            getattr(self, 'avatar_vertices', None),
            getattr(self, 'avatar_gen_type', None),
            getattr(self, 'avatar_gen', None),
            getattr(self,'avatar_nb_vertices_label', None),  
            getattr(self,'avatar_nb_vertices', None),
        ]
         
         # Masquer tous les champs par défaut
         for widget in widgets:
            if widget is not None:
                widget.setVisible(False)

        # Afficher les champs pertinents
         if avatar_type == "rigidDisk":
            if hasattr(self, 'avatar_center') and hasattr(self, 'avatar_radius'):
                self.avatar_radius_label.setVisible(True)
                self.avatar_radius.setVisible(True)
                self.avatar_center_label.setVisible(True)
                self.avatar_center.setVisible(True)
                self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
         if avatar_type == "rigidJonc" :
            if hasattr(self, 'avatar_center') and hasattr(self, 'avatar_axis'):
                self.avatar_axis_label.setVisible(True)
                self.avatar_axis.setVisible(True)              
                self.avatar_center_label.setVisible(True)
                self.avatar_center.setVisible(True)
                self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
                self.avatar_color.setText("VERTx")
         if avatar_type == "rigidPolygon" :
              if hasattr(self, 'avatar_vertices') and hasattr(self, 'avatar_gen'):
                self.avatar_radius_label.setVisible(True)
                self.avatar_radius.setVisible(True)
                self.avatar_gen_type.setVisible(True)
                self.avatar_gen.setVisible(True)
                if self.avatar_gen.currentText()== 'regular' : 
                    self.avatar_nb_vertices_label.setVisible(True)
                    self.avatar_nb_vertices.setVisible(True)
                else : 
                    self.avatar_nb_vertices_label.setVisible(False)
                    self.avatar_nb_vertices.setVisible(False)
                self.avatar_center_label.setVisible(True)
                self.avatar_center.setVisible(True)
                self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
                self.avatar_color.setText("REDxx")
                #self.avatar_gen.setText('Regular')

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
        self.update_avatar_types(dim_text)    # remplissage du ComboBox des avatars
        # ré-initialise le texte du centre selon la dimension
        default_center = "0.0,0.0" if self.dim == 2 else "0.0,0.0,0.0"
        self.avatar_center.setText(default_center)

    def update_polygon_fields(self, gen_type):
        if self.avatar_type.currentText() != "rigidPolygon":
            return

        # nb_vertices n’est utile que pour le mode *regular*
        show_nb = (gen_type == "regular")
        self.avatar_nb_vertices_label.setVisible(show_nb)
        self.avatar_nb_vertices.setVisible(show_nb)

        # le champ *vertices* (liste manuelle) n’est utile que pour *full* et *bevel*
        show_vertices = (gen_type in ("full", "bevel"))
        self.avatar_vertices_label.setVisible(show_vertices)
        self.avatar_vertices.setVisible(show_vertices)

        # valeur par défaut du nombre de vertices
        if show_nb and not self.avatar_nb_vertices.text().strip():
            self.avatar_nb_vertices.setText("5")
    # ========================================
    # PROJET
    # ========================================
    def new_project(self):
        self._init_containers()
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
        self.update_selections()
        self.update_model_tree()
        QMessageBox.information(self, "Succès", "Nouveau projet vide")

    def open_project(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Ouvrir projet")
        if not dir_path: return
        json_path = os.path.join(dir_path, "project.json")
        if not os.path.exists(json_path):
            QMessageBox.critical(self, "Erreur", "project.json introuvable")
            return
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self._deserialize_state(state)
            self.current_project_dir = dir_path
            self.update_selections()
            self.update_model_tree()
            QMessageBox.information(self, "Succès", "Projet chargé")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"JSON invalide : {e}")

    def save_project(self):
        if not self.current_project_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Sauvegarder dans")
            if not dir_path: return
            self.current_project_dir = dir_path
        self.do_save(self.current_project_dir)

    def do_save(self, dir_path):
        os.makedirs(dir_path, exist_ok=True)
        state = self._serialize_state()
        print(state)
        with open(os.path.join(dir_path, 'project.json'), 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        QMessageBox.information(self, "Succès", "Projet sauvegardé")

    def _serialize_state(self):
        return {
            'materials': self.material_creations,
            'models': self.model_creations,
            'avatars': self.avatar_creations,
            'contact_laws': self.contact_creations,
            'visibility_rules': self.visibility_creations,
            'operations': self.operations
        }

    def _deserialize_state(self, state):
        self.new_project()  # Reset complet
        # Matériaux
        for m in state.get('materials', []):
            if not all(k in m for k in ['name', 'type', 'density']): continue
            mat = pre.material(name=m['name'], materialType=m['type'], density=m['density'])
            self.materials.addMaterial(mat); self.material_objects.append(mat)
            self.material_creations.append(m); self.mats_dict[m['name']] = mat

        # Modèles
        for m in state.get('models', []):
            if not all(k in m for k in ['name', 'physics', 'element', 'dimension']): continue
            mod = pre.model(name=m['name'], physics=m['physics'], element=m['element'], dimension=m['dimension'])
            self.models.addModel(mod); self.model_objects.append(mod)
            self.model_creations.append(m); self.mods_dict[m['name']] = mod

        # Avatars
        for av in state.get('avatars', []):
            #if not all(k in av for k in ['type', ('r' or ('axe1' and 'axe2')), 'center', 'material', 'model', 'color']): continue
            mat = self.mats_dict.get(av['material']); mod = self.mods_dict.get(av['model'])
            if not mat or not mod: continue
            if av['type'] == "rigidDisk" and 'r' in av :
                body = pre.rigidDisk(r=av['r'], center=av['center'], model=mod, material=mat, color=av['color'])
            elif av['type'] == "rigidJonc" and 'axe1' in av and 'axe2' in av:
                body = pre.rigidJonc(axe1=av['axe1'], axe2=av['axe2'], center=av['center'], model=mod, material=mat, color=av['color'])
            elif av['type'] == "rigidPolygon"   :
                if  av['gen_type'] == "regular" :
                    body = pre.rigidPolygon( model=mod, material=mat, center=av['center'],color=av['color'], generation_type= av['gen_type'], nb_vertices=int(av['nb_vertices']),radius=float(av['r']))
                else : 
                    body = pre.rigidPolygon( model=mod, material=mat, center=av['center'],color=av['color'], generation_type= av['gen_type'],vertices= np.array(av['vertices'], dtype=float) ,radius=float(av['r']))
            else : continue
            self.bodies.addAvatar(body); self.bodies_objects.append(body); self.bodies_list.append(body)
            self.avatar_creations.append(av)

        # Lois
        for law in state.get('contact_laws', []):
            if not all(k in law for k in ['name', 'law', 'fric']): continue
            l = pre.tact_behav(name=law['name'], law=law['law'], fric=law['fric'])
            self.contact_laws.addBehav(l); self.contact_laws_objects.append(l)
            self.contact_creations.append(law)

        # Visibilité
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
    # ========================================
    # CRÉATIONS
    # ========================================
    def create_material(self):
        try:
            name = self.mat_name.text().strip()
            if not name: raise ValueError("Nom vide")
            props = self._safe_eval_dict(self.mat_props.text())
            mat = pre.material(name=name, materialType=self.mat_type.currentText(), density=float(self.mat_density.text()), **props)
            self.materials.addMaterial(mat); self.material_objects.append(mat)
            self.material_creations.append({'name': name, 'type': self.mat_type.currentText(), 'density': float(self.mat_density.text())})
            self.mats_dict[name] = mat
            self.update_selections(); self.update_model_tree()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Matériau : {e}")

    def create_model(self):
        try:
            name = self.model_name.text().strip()
            if not name: raise ValueError("Nom vide")
            props = self._safe_eval_dict(self.model_options.text())
            mod = pre.model(name=name, physics=self.model_physics.currentText(), element=self.model_element.text(),
                            dimension=int(self.model_dimension.currentText()), **props)
            self.models.addModel(mod); self.model_objects.append(mod)
            self.model_creations.append({'name': name, 'physics': self.model_physics.currentText(), 'element': self.model_element.text(),
                                        'dimension': int(self.model_dimension.currentText())})
            self.mods_dict[name] = mod
            self.update_selections(); self.update_model_tree()
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
            props = self._safe_eval_dict(self.avatar_properties.text())
            mat = self.material_objects[self.avatar_material.currentIndex()]
            mod = self.model_objects[self.avatar_model.currentIndex()]
            
            if self.avatar_type.currentText() == "rigidDisk" :
                body = pre.rigidDisk(r=float(self.avatar_radius.text()), center=center, model=mod, material=mat,
                                    color=self.avatar_color.text(), **props)
            
            elif self.avatar_type.currentText() == "rigidJonc":
                center = [float(x) for x in self.avatar_center.text().split(",")]
                
                body = pre.rigidJonc(
                    axe1=float(self.avatar_axis.text().split(',')[0].split('=')[1].strip()),
                    axe2=float(self.avatar_axis.text().split(',')[1].split('=')[1].strip()),
                    center=center,
                    model=mod,
                    material=mat,
                    color=self.avatar_color.text(), **props
                )
            elif self.avatar_type.currentText() == "rigidPolygon": 
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
                    import numpy as np
                    raw = self.avatar_vertices.text().strip()
                    print(raw)
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

            self.bodies.addAvatar(body); self.bodies_objects.append(body); self.bodies_list.append(body)
            body_dict= {
                'type': 'rigidDisk' if isinstance(body.bulks[0], pre.rigid2d) and body.dimension==2 and body.contactors[0].shape=='DISKx' else
                        'rigidJonc' if isinstance(body.bulks[0], pre.rigid2d) and  body.dimension==2 and body.contactors[0].shape=='JONCx'else 
                        'rigidPolygon' if isinstance(body.bulks[0], pre.rigid2d)  and body.dimension ==2  and body.contactors[0].shape=='POLYG' else 'unknown', 
                'center': center,
                'material': mat.nom, 
                'model': mod.nom, 
                'color': self.avatar_color.text()
            }
            if hasattr(body.contactors[0],'byrd') :
                body_dict['r']= self.avatar_radius.text()
            if hasattr(body.contactors[0],'axes') :
                body_dict['axe1'] = self.avatar_axis.text().split(',')[0].split('=')[1].strip()
                body_dict['axe2'] = self.avatar_axis.text().split(',')[1].split('=')[1].strip()
            if hasattr(body.contactors[0],'nb_vertices') and self.avatar_gen.currentText() == "regular":
                body_dict['nb_vertices'] = self.avatar_nb_vertices.text()
                #body_dict['theta'] = self.avatar_theta.text()
                body_dict['gen_type'] = self.avatar_gen.currentText()
                body_dict['r'] = self.avatar_radius.text()
                print(body_dict['gen_type'])
            if hasattr(body.contactors[0],'nb_vertices') and self.avatar_gen.currentText() == "full":
                body_dict['vertices'] = vertices.tolist()
                #body_dict['theta'] = self.avatar_theta.text()
                body_dict['gen_type'] = self.avatar_gen.currentText()
                body_dict['r'] = self.avatar_radius.text()
                print(body_dict['gen_type'])
            self.avatar_creations.append(body_dict)
            print(self.avatar_creations)
            self.update_selections(); self.update_model_tree()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Avatar : {e}")

    def dof_force(self):
        if not self.bodies_objects:
            QMessageBox.critical(self, "Erreur", "Aucun avatar")
            return
        try:
            idx = self.dof_avatar_name.currentIndex(); body = self.bodies_list[idx]
            action = self.dof_avatar_force.currentText(); params = self._safe_eval_dict(self.dof_options.text())
            if action == "imposeDrivenDof" and ('component' not in params or 'dofty' not in params):
                raise ValueError("imposeDrivenDof → component=[...], dofty='vlocy'")
            if action == "imposeInitDof" and ('component' not in params or 'dofty' not in params):
                raise ValueError("imposeInitDof → component=[...], dofty='vlocx', value=1.0")
            getattr(body, action)(**params)
            self.operations.append({'body_index': idx, 'type': action, 'params': params})
            self.update_model_tree()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"DOF : {e}")

    def create_contact_law(self):
        try:
            name = self.contact_name.text().strip()
            if not name: raise ValueError("Nom vide")
            props = self._safe_eval_dict(self.contact_properties.text())
            law = pre.tact_behav(name=name, law=self.contact_type.currentText(), **props)
            self.contact_laws.addBehav(law); self.contact_laws_objects.append(law)
            self.contact_creations.append({'name': name, 'law': law.law, 'fric': props.get('fric', 0.0)})
            self.update_selections(); self.update_model_tree()
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
            self.update_model_tree()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Visibilité : {e}")
    # ========================================
    # UI
    # ========================================
    def update_selections(self):
        for combo, items, enabled in [
            (self.avatar_material, [m.nom for m in self.material_objects], bool(self.material_objects)),
            (self.avatar_model, [m.nom for m in self.model_objects], bool(self.model_objects)),
            (self.behav, [l.nom for l in self.contact_laws_objects], bool(self.contact_laws_objects)),
            (self.dof_avatar_name, [f"Avatar {i} ({b.contactors[0].color})" for i, b in enumerate(self.bodies_objects)], bool(self.bodies_objects)),
        ]:
            combo.blockSignals(True); combo.clear(); combo.addItems(items); combo.setEnabled(enabled); combo.blockSignals(False)


    def update_model_tree(self):
        self.tree.clear()
        root = QTreeWidgetItem(["Modèle LMGC90", "", ""])
        for title, items, key in [
            ("Matériaux", self.material_objects, 'nom'),
            ("Modèles", self.model_objects, 'nom'),
            ("Avatars", self.bodies_objects, None),
            ("Lois", self.contact_laws_objects, 'nom'),
            ("Règles", self.visibilities_table_objects, None),
        ]:
            parent = QTreeWidgetItem(root, [title, "", f"{len(items)}"])
            for obj in items:
                name = getattr(obj, key, f"Objet {id(obj)}") if key else "Avatar"
                self._add_to_tree(parent, name, type(obj).__name__)
        self.tree.addTopLevelItem(root); root.setExpanded(True)
    # ========================================
    # ACTIONS
    # ========================================
    def generate_python_script(self):
        try:
            base = self.current_project_dir or os.getcwd()
            path = os.path.join(base, "lmgc_sim.py")
            with open(path, 'w', encoding='utf-8') as f:
                f.write("from pylmgc90 import pre\n")
                f.write("import numpy as np\n\n")
                f.write("mats, mods, laws = {}, {}, {}\n")
                f.write("materials = pre.materials(); models = pre.models(); bodies = pre.avatars()\n")
                f.write("tacts = pre.tact_behavs(); svs = pre.see_tables()\n\n")

                # Matériaux
                for m in self.material_creations:
                    f.write(f"mats['{m['name']}'] = pre.material(name='{m['name']}', materialType='{m['type']}', density={m['density']})\n")
                    f.write("materials.addMaterial(mats['" + m['name'] + "'])\n\n")

                # Modèles
                for m in self.model_creations:
                    f.write(f"mods['{m['name']}'] = pre.model(name='{m['name']}', physics='{m['physics']}', element='{m['element']}', dimension={m['dimension']})\n")
                    f.write("models.addModel(mods['" + m['name'] + "'])\n\n")

                # Avatars
                f.write("bodies_list = []\n")
                for i, av in enumerate(self.avatar_creations):
                    if av['type']  == 'rigidDisk' :
                        f.write(f"body{i} = pre.rigidDisk(r={av['r']}, center={av['center']}, ")
                        f.write(f"model=mods['{av['model']}'], material=mats['{av['material']}'], color='{av['color']}')\n")
                    if av['type']  == 'rigidJonc' :
                        f.write(f"body{i} = pre.rigidJonc(axe1={av['axe1']}, axe2 = {av['axe2']},center={av['center']}, ")
                        f.write(f"model=mods['{av['model']}'], material=mats['{av['material']}'], color='{av['color']}')\n")
                    if av['type'] == 'rigidPolygon' and av['gen_type'] == 'regular' : 
                        f.write(f"body{i} = pre.rigidPolygon(center={av['center']}, radius= {av['r']}, generation_type= '{av['gen_type']}', nb_vertices={av['nb_vertices']}, ")
                        f.write(f"model=mods['{av['model']}'], material=mats['{av['material']}'], color='{av['color']}')\n")
                    if av['type'] == 'rigidPolygon' and av['gen_type'] == 'full'  :
                        f.write(f"body{i} = pre.rigidPolygon(center={av['center']}, radius= {av['r']}, generation_type= '{av['gen_type']}', vertices=np.array({av['vertices']}), ")
                        f.write(f"model=mods['{av['model']}'], material=mats['{av['material']}'], color='{av['color']}')\n")
                    
                    f.write(f"bodies.addAvatar(body{i}); bodies_list.append(body{i})\n\n")

                # DOF
                for op in self.operations:
                    args = ", ".join(f"{k}={repr(v)}" for k, v in op['params'].items())
                    f.write(f"bodies_list[{op['body_index']}].{op['type']}({args})\n")

                # Contact & Visibilité
                for law in self.contact_creations:
                    f.write(f"laws['{law['name']}'] = pre.tact_behav(name='{law['name']}', law='{law['law']}', fric={law['fric']})\n")
                    f.write("tacts.addBehav(laws['" + law['name'] + "'])\n")
                for rule in self.visibility_creations:
                    f.write(f"svt = pre.see_table(CorpsCandidat='{rule['CorpsCandidat']}', candidat='{rule['candidat']}', ")
                    f.write(f"colorCandidat='{rule['colorCandidat']}', CorpsAntagoniste='{rule['CorpsAntagoniste']}', ")
                    f.write(f"antagoniste='{rule['antagoniste']}', colorAntagoniste='{rule['colorAntagoniste']}', ")
                    f.write(f"behav=laws['{rule['behav']}'], alert={rule['alert']})\n")
                    f.write("svs.addSeeTable(svt)")

                f.write("\npre.writeDatbox(2, materials, models, bodies, tacts, svs)\n")
            self.script_path = path
            QMessageBox.information(self, "Succès", f"Script généré :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Génération : {e}")

    def execute_python_script(self):
        path = self.script_path or os.path.join(self.current_project_dir or os.getcwd(), "lmgc_sim.py")
        file, _ = QFileDialog.getOpenFileName(self, "Exécuter", path, "Python (*.py)")
        if not file: return
        try:
            result = subprocess.run(['python', file], capture_output=True, text=True, check=True)
            QMessageBox.information(self, "Succès", result.stdout or "Exécuté sans sortie")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"{e}")

    def visu_lmgc(self):
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
        QMessageBox.information(self, "À propos", "LMGC90 GUI v0.1.3\n par Zerourou B, email : bachir.zerourou@yahoo.fr \n© 2025")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LMGC90GUI()
    win.show()
    sys.exit(app.exec())