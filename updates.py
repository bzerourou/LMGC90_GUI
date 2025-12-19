from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QComboBox, QCheckBox, QLabel, QPushButton, QScrollArea, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
# ========================================
# UTILITAIRES
# ========================================
''' Evaluer en toute sécurité une chaîne de caractères en dictionnaire 
    text : str : chaîne à évaluer
'''
def _safe_eval_dict(self, text):
  
    if not text.strip():
        return {}

    import math
    import numpy as np

    local = {
        "math": math,
        "np": np,
        "__builtins__": {}
    }

    
    # Ajout des variables dynamiques de l'utilisateur
    local.update(self.dynamic_vars)

    # Ajout des variables classiques de l'interface (r, color, etc.)
    try:
        local['r'] = float(self.avatar_radius.text() or 0)
    except: pass
    try:
        local['color'] = self.avatar_color.text() or "BLUEx"
    except: pass
    # ... ajoute les autres si tu veux

    try:
        exec(f"props = dict({text})", {}, local)
        return local.get('props', {})
    except Exception as e:
        raise ValueError(f"Expression invalide : {e}\nVariables disponibles : {', '.join(local.keys())}")

''' Met à jour la barre de statut avec un message temporaire'''
def update_status(self, msg):
    self.statusBar().showMessage(msg, 5000)

''' Met à jour les types d'avatars disponibles selon la dimension du modèle
    dimension : str : "2" ou "3"'''
def update_avatar_types(self, dimension):
    self.avatar_type.blockSignals(True)
    self.avatar_type.clear()
    if dimension == "2":
        self.avatar_type.addItems(self.avatar_types_2d)
    else:
        self.avatar_type.addItems(self.avatar_types_3d)
    self.avatar_type.blockSignals(False)
    
    update_avatar_fields(self, self.avatar_type.currentText())

''' Met à jour les champs affichés dans l'onglet Avatar selon le type sélectionné
    avatar_type : str : type d'avatar sélectionné'''
def update_avatar_fields(self, avatar_type): 
        if self._initializing:
            return
        
        # Liste des widgets à gérer
        widgets = [
            self.avatar_hallowed,
        self.avatar_radius_label, self.avatar_radius,
        self.avatar_center_label, self.avatar_center,
        self.avatar_axis_label, self.avatar_axis,
        self.avatar_vertices_label, self.avatar_vertices,
        self.avatar_gen_type, self.avatar_gen,
        self.avatar_nb_vertices_label, self.avatar_nb_vertices,
        self.avatar_r_ovoid_label, self.avatar_r_ovoid,
        self.wall_length_label, self.wall_length,
        self.wall_height_label, self.wall_height,
    ]
        
        # Masquer tous les champs par défaut
        for widget in widgets:
            if widget is not None:
                widget.setVisible(False)
    # --- Valeurs par défaut ---
        self.avatar_center.setText("0.0,0.0" if self.dim == 2 else "0.0,0.0,0.0")
        self.avatar_color.setText("BLUEx")

    # Afficher les champs pertinents
        if avatar_type in ["rigidDisk", "rigidDiscreteDisk", "rigidCluster"]:
            self.avatar_radius_label.setVisible(True)
            self.avatar_radius.setVisible(True)
            self.avatar_center_label.setVisible(True)
            self.avatar_center.setVisible(True)
            self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
            self.avatar_color.setText("BLUEx")
            if avatar_type == "rigidDisk":
                self.avatar_hallowed.setVisible(True)
            else:
                self.avatar_hallowed.setVisible(False)
                
            if avatar_type == "rigidCluster":
                self.avatar_nb_vertices_label.setVisible(True)
                self.avatar_nb_vertices_label.setText("Nombre de disques : ")
                self.avatar_nb_vertices.setVisible(True)
                self.avatar_nb_vertices.setText("5")
        elif avatar_type == "rigidJonc" :
            self.avatar_radius_label.setVisible(False)
            self.avatar_radius.setVisible(False)
            self.avatar_axis_label.setVisible(True)
            self.avatar_axis.setVisible(True)              
            self.avatar_center_label.setVisible(True)
            self.avatar_center.setVisible(True)
            self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
            self.avatar_color.setText("VERTx")
        elif avatar_type == "rigidPolygon" :
            self.avatar_radius_label.setVisible(True)
            self.avatar_radius.setVisible(True)
            self.avatar_gen_type.setVisible(True)
            self.avatar_gen.setVisible(True)
            if self.avatar_gen.currentText()== 'regular' : 
                self.avatar_nb_vertices_label.setVisible(True)
                self.avatar_nb_vertices.setVisible(True)
                self.avatar_nb_vertices_label.setText("Nombre de vertices (>=3)")
            else : 
                self.avatar_nb_vertices_label.setVisible(False)
                self.avatar_nb_vertices.setVisible(False)
            self.avatar_center_label.setVisible(True)
            self.avatar_center.setVisible(True)
            self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
            self.avatar_color.setText("REDxx")
            #self.avatar_gen.setText('Regular')

        elif avatar_type == "rigidOvoidPolygon" :
            self.avatar_radius_label.setVisible(False)
            self.avatar_radius.setVisible(False)
            self.avatar_center_label.setVisible(True)
            self.avatar_center.setVisible(True)
            self.avatar_center.setText("0.0,0.0" if self.model_dimension.currentText() == "2" else "0.0,0.0,0.0")
            self.avatar_r_ovoid_label.setVisible(True)
            self.avatar_r_ovoid.setVisible(True)
            self.avatar_nb_vertices_label.setVisible(True)
            self.avatar_nb_vertices.setVisible(True)
            self.avatar_color.setText("CYANx")
        elif avatar_type in ["roughWall", "fineWall", "smoothWall", "granuloRoughWall"]:
            self.avatar_center_label.setVisible(True)
            self.avatar_center.setVisible(True)
            self.wall_length_label.setVisible(True)
            self.wall_length.setVisible(True)
            self.wall_height_label.setVisible(True)
            self.wall_height.setVisible(True)
            self.avatar_nb_vertices_label.setVisible(True)
            self.avatar_nb_vertices.setVisible(True)

            # --- Réinitialisation du texte selon le type ---
            if avatar_type == "granuloRoughWall":
                self.wall_height_label.setText("Rayons (rmin, rmax) :")
                self.wall_height.setText("rmin = 0.1, rmax = 0.2")
            elif avatar_type == "smoothWall":
                self.wall_height_label.setText("Hauteur (h) :")
                self.wall_height.setText("0.15")
            else:  # roughWall, fineWall
                self.wall_height_label.setText("Rayon (r) :")
                self.wall_height.setText("0.1")

            self.wall_length.setText("2.0")
            self.avatar_nb_vertices.setText("5")

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
    self.update_avatar_types(dim_text)    # remplissage du ComboBox des avatars
    # ré-initialise le texte du centre selon la dimension
    default_center = "0.0,0.0" if self.dim == 2 else "0.0,0.0,0.0"
    self.avatar_center.setText(default_center)
    self.update_model_elements()

''' Met à jour les champs affichés dans l'onglet Avatar selon le type de génération de polygone
    gen_type : str : type de génération sélectionné'''
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

''' Met à jour les champs de l'onglet Matériau selon le type sélectionné'''
def update_material_fields(self):
    if self.mat_type.currentText() == "RIGID":
        self.mat_name.setText("rigid")
        self.mat_props.setText("")
    elif self.mat_type.currentText() == "ELAS":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', young=0.1e+15, nu=0.2, anisotropy='isotropic'")
    elif self.mat_type.currentText() == "ELAS_DILA":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', young=0.1e+15, nu=0.2, anisotropy='isotropic',dilatation=1e-5, T_ref_meca=20.")
    elif self.mat_type.currentText() == "VISCO_ELAS":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', anisotropy='isotropic', young=1.17e11, nu=0.35,viscous_model='KelvinVoigt', viscous_young=1.17e9, viscous_nu=0.35")
    elif self.mat_type.currentText() == "ELAS_PLAS":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', anisotropy='isotropic', young=1.17e11, nu=0.35,critere='Von-Mises', isoh='linear', iso_hard=4.e8, isoh_coeff=1e8, cinh='none', visc='none'")
    elif self.mat_type.currentText() == "THERMO_ELAS":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', young=0.0, nu=0.0, anisotropy='isotropic', dilatation = 0.0,T_ref_meca = 0.0, conductivity='field', specific_capacity='field'")
    elif self.mat_type.currentText() == "PORO_ELAS":
        self.mat_name.setText("steel")
        self.mat_props.setText("elas='standard', young=0.0, nu=0.0, anisotropy='isotropic',hydro_cpl = 0.0, conductivity='field', specific_capacity='field'")
    elif self.mat_type.currentText() == "DISCRETE":
        self.mat_density.setEnabled(False)
        self.mat_density.setText("ignorée")
        self.mat_props.setText("masses=[0., 0., 0.], stiffnesses=[1e7, 1e7, 1e7], viscosities=[0., 0., 0.]")
    elif  self.mat_type.currentText() == "USER_MAT":
        self.mat_density.setEnabled(True)
        self.mat_density.setText("2000.")
        self.mat_props.setText("file_mat='elas.mat'")
    else:
        self.mat_density.setEnabled(True)
        self.mat_density.setText("2500.")

def update_model_options_fields(self):
    # Vider toutes les options
    for i in reversed(range(self.model_options_layout.count())):
        widget = self.model_options_layout.takeAt(i).widget()
        if widget:
            widget.setParent(None)

    elem = self.model_element.currentText()

    # === CORPS RIGIDES → AUCUNE OPTION ===
    rigid_elements = ["Rxx2D", "Rxx3D"]
    if elem in rigid_elements:
        self.model_options_group.setVisible(False)  # ← Cache complètement le groupe
        return  # → on sort, rien à afficher
    # === SINON : on affiche les options ===
    self.model_options_group.setVisible(True)
    specific = self.ELEMENT_OPTIONS.get(elem, {})
    # Options spécifiques à l’élément
    for opt, values in specific.items():
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentIndex(0)
        self.model_options_layout.addRow(f"{opt}:", combo)
        self.model_option_combos[opt] = combo

    # Options globales (toujours disponibles sauf pour rigides)
    for opt, values in self.GLOBAL_MODEL_OPTIONS.items():
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentIndex(0)
        self.model_options_layout.addRow(f"{opt}:", combo)
        self.model_option_combos[opt] = combo   # ← même dictionnaire

    # Champ libre
    self.external_fields_input = QLineEdit()
    self.model_options_layout.addRow("external_fields (comma):", self.external_fields_input)

def update_model_elements(self):
    dim = int(self.model_dimension.currentText())
    if dim == 2:
        elements = ["Rxx2D", "T3xxx", "Q4xxx","T6xxx","Q8xxx","Q9xxx","BARxx"]
    else:  # dim == 3
        elements = ["Rxx3D", "H8xxx", "SHB8x", "H20xx", "SHB6x", "TE10x", "DKTxx","BARxx"]

    current = self.model_element.currentText()
    self.model_element.blockSignals(True)   # ← IMPORTANT : bloque les signaux pendant le changement
    self.model_element.clear()
    self.model_element.addItems(elements)
    self.model_element.blockSignals(False)

    # Restaurer la sélection si possible, sinon choix par défaut
    if current in elements:
        self.model_element.setCurrentText(current)
    else:
        default = "Rxx2D" if dim == 2 else "Rxx3D"
        self.model_element.setCurrentText(default)

    # ← FORCER la mise à jour des options APRÈS le changement
    update_model_options_fields(self)

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

def update_granulo_fields(self):
        """Met à jour les champs de saisie selon la forme choisie"""
        # On vide le layout des paramètres
        while self.gran_params_layout.rowCount() > 0:
            self.gran_params_layout.removeRow(0)
        
        # recréer les champs
        self.gran_lx = QLineEdit("4.0")
        self.gran_ly = QLineEdit("4.0")
        self.gran_r = QLineEdit("2.0")
        self.gran_rint = QLineEdit("2.0")
        self.gran_rext = QLineEdit("4.0")
        shape = self.gran_shape_type.currentText()
        
        if shape in ["Box2D", "squareLattice2D","triangularLattice2D"]:
            self.gran_params_layout.addRow("Largeur (lx) :", self.gran_lx)
            self.gran_params_layout.addRow("Hauteur (ly) :", self.gran_ly)
        elif shape in ["Drum2D", "Disk2D"]:
            self.gran_params_layout.addRow("Rayon (r) :", self.gran_r)
        elif "Couette2D" in shape:
            self.gran_params_layout.addRow("Rayon Int (rint) :", self.gran_rint)
            self.gran_params_layout.addRow("Rayon Ext (rext) :", self.gran_rext)
def update_advanced_fields(self, dim_text=None):
        dim = 2 if not dim_text else int(dim_text)
        default = "0.0, 0.0" if dim == 2 else "0.0, 0.0, 0.0"
        if self.adv_center.text() in ["0.0, 0.0", "0.0, 0.0, 0.0"]:
            self.adv_center.setText(default)

def update_selections(self):
        for combo, items, enabled in [
            (self.avatar_material, [m.nom for m in self.material_objects], bool(self.material_objects)),
            (self.avatar_model, [m.nom for m in self.model_objects], bool(self.model_objects)),
            (self.behav, [l.nom for l in self.contact_laws_objects], bool(self.contact_laws_objects)),
            (self.dof_avatar_name, [f"Avatar {i} ({b.contactors[0].color})" for i, b in enumerate(self.bodies_objects)], bool(self.bodies_objects)),
            (self.loop_avatar_type, [a['type'] for a in self.avatar_creations], bool(self.avatar_creations))
        ]:
            combo.blockSignals(True); combo.clear(); combo.addItems(items); combo.setEnabled(enabled); combo.blockSignals(False)

        # todo à compléter
        self.dof_avatar_name.blockSignals(True)
        self.dof_avatar_name.clear()
        for i, b in enumerate(self.bodies_objects):
            color = b.contactors[0].color if b.contactors else "????"
            self.dof_avatar_name.addItem(f"Avatar {i} ({color})")
        for name in self.group_names:
            count = len(self.avatar_groups.get(name, []))
            self.dof_avatar_name.addItem(f"GROUPE: {name} ({count} avatars)")
        self.dof_avatar_name.blockSignals(False)

        # Boucles
        self.loop_avatar_type.blockSignals(True)
        self.loop_avatar_type.clear()
        self.loop_avatar_type.addItems([a.get('type', 'Inconnu') for a in self.avatar_creations])
        self.loop_avatar_type.blockSignals(False)

        # empty avatar
        self.adv_material.blockSignals(True)
        self.adv_material.clear()
        self.adv_material.addItems([m.nom for m in self.material_objects])
        self.adv_material.blockSignals(False)

        self.adv_model.blockSignals(True)
        self.adv_model.clear()
        self.adv_model.addItems([m.nom for m in self.model_objects])
        self.adv_model.blockSignals(False)

# ========================================
# INTERACTION ARBRE
# ========================================

def update_model_tree(self):
    self.tree.clear()
    root = QTreeWidgetItem(["Modèle LMGC90", "", ""])

        # Matériaux
    mat_node = QTreeWidgetItem(root, ["Matériaux", "", f"{len(self.material_objects)}"])
    for i, mat in enumerate(self.material_objects):
        ma = self.material_creations[i]
        display_text = f"{mat.nom} - {ma['type']}"
        item = QTreeWidgetItem([display_text, "Matériau", f"ρ={mat.density}"])
        item.setData(0, Qt.ItemDataRole.UserRole, ("material", i))
        mat_node.addChild(item)

    # Modèles
    mod_node = QTreeWidgetItem(root, ["Modèles", "", f"{len(self.model_objects)}"])
    for i, mod in enumerate(self.model_objects):
        item = QTreeWidgetItem([mod.nom, "Modèle", f"{mod.element} dim={mod.dimension}"])
        item.setData(0, Qt.ItemDataRole.UserRole, ("model", i))
        mod_node.addChild(item)

    # Avatars (le plus critique)
    av_node = QTreeWidgetItem(root, ["Avatars", "", f"{len(self.bodies_objects)}"])
    for i, body in enumerate(self.bodies_objects):
        # il faut gérer l'erreur
        av = self.avatar_creations[i]
        color = body.contactors[0].color if body.contactors else "?????"
        name = f"{av['type']} — {color} — ({', '.join(map(str, av['center']))})"
        if av.get('type')=='emptyAvatar' : 
            # Affichage spécial pour avatars avancés
            cont_types = [c['shape'] for c in av.get('contactors', [])]
            name = f" Avatar vide  ({', '.join(cont_types)}) — {av['color']}"
        else : 
            color = body.contactors[0].color if body.contactors else "?????" 
            name = f"{av['type']} — {color} — ({', '.join(map(str, av['center']))})"
        item = QTreeWidgetItem([name, "Avatar", str(i)])
        item.setData(0, Qt.ItemDataRole.UserRole, ("avatar", i))
        av_node.addChild(item)

    # affichage des groupes d'avatars
    if self.avatar_groups:
        grp_node = QTreeWidgetItem(root, ["Groupes d'avatars", "", f"{len(self.avatar_groups)}"])
        # Tri alphabétique des noms de groupes
        for name in sorted(self.avatar_groups.keys()):
            count = len(self.avatar_groups[name])
            QTreeWidgetItem(grp_node, [f"{name} ({count} avatars)", "Groupe", ""])

    self.tree.addTopLevelItem(root)
    root.setExpanded(True)
    
    # Lois de contact
    law_node = QTreeWidgetItem(root, ["Lois de contact", "", f"{len(self.contact_laws_objects)}"])
    for i, law in enumerate(self.contact_laws_objects):
        if hasattr(law, 'fric'):
            info = f"fric={law.fric}"
        else : info = ""
        item = QTreeWidgetItem([law.nom, "Loi", info])
        item.setData(0, Qt.ItemDataRole.UserRole, ("contact", i))
        law_node.addChild(item)

    # Visibilités
    vis_node = QTreeWidgetItem(root, ["Tables de visibilité", "", f"{len(self.visibilities_table_objects)}"])
    for i, st in enumerate(self.visibilities_table_objects):
        txt = f"{st.candidat}({st.colorCandidat}) ↔ {st.antagoniste} → {st.behav}"
        item = QTreeWidgetItem([txt, "Visibilité", ""])
        item.setData(0, Qt.ItemDataRole.UserRole, ("visibility", i))
        vis_node.addChild(item)

    self.tree.addTopLevelItem(root); root.setExpanded(True)


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

def update_postpro_avatar_selector(self, command_name):
    """Active et remplit le sélecteur d'avatars seulement pour certaines commandes"""
    needs_avatar = command_name in ["TORQUE EVOLUTION", "BODY TRACKING","NEW RIGID SETS"]

    self.post_avatar_label.setVisible(needs_avatar)
    self.post_avatar_selector.setVisible(needs_avatar)
    self.post_avatar_selector.setEnabled(needs_avatar)

    if needs_avatar:
        self.post_avatar_selector.clear()
        # Ajouter les avatars individuels
        for i, body in enumerate(self.bodies_objects):
            color = body.contactors[0].color if body.contactors else "????"
            self.post_avatar_selector.addItem(f"Avatar {i} ({color})", ("avatar", i))
        # Ajouter les groupes
        for group_name in sorted(self.avatar_groups.keys()):
            count = len(self.avatar_groups[group_name])
            self.post_avatar_selector.addItem(f"GROUPE: {group_name} ({count} avatars)", ("group", group_name))
    else:
        self.post_avatar_selector.clear()

def refresh_granulo_combos(self):
    if not hasattr(self, 'gran_tab'):
        return

    # Matériaux
    cur_mat = self.gran_mat.currentText() if hasattr(self, 'gran_mat') else None
    self.gran_mat.blockSignals(True)
    self.gran_mat.clear()
    self.gran_mat.addItems([m.nom for m in self.material_objects])
    if cur_mat:
        self.gran_mat.setCurrentText(cur_mat)
    self.gran_mat.blockSignals(False)

    # Modèles
    cur_mod = self.gran_mod.currentText() if hasattr(self, 'gran_mod') else None
    self.gran_mod.blockSignals(True)
    self.gran_mod.clear()
    self.gran_mod.addItems([m.nom for m in self.model_objects])
    if cur_mod:
        self.gran_mod.setCurrentText(cur_mod)
    self.gran_mod.blockSignals(False)
    refresh_granulo_avatar_combo(self)

def refresh_granulo_avatar_combo(self):
  
    """Met à jour le ComboBox du type d'avatar dans l'onglet Granulométrie avec les avatars manuels"""
    if not hasattr(self, 'avatar') or self.avatar is None:
        return

    current_data = self.avatar.currentData()  # On garde l'index sélectionné

    self.avatar.blockSignals(True)
    self.avatar.clear()

    manual_avatars = []
    for idx, avatar_dict in enumerate(self.avatar_creations):  # ← renommé 'av' en 'avatar_dict'
        if avatar_dict.get('__from_loop', False) or avatar_dict.get('__from_granulo', False):
            continue

        desc = avatar_dict['type']
        if avatar_dict.get('color'):
            desc += f" — {avatar_dict['color']}"
        center = avatar_dict.get('center', [])
        if center:
            center_str = ', '.join(f"{x:.3g}" for x in center)
            desc += f" — ({center_str})"

        manual_avatars.append((desc, idx))

    if not manual_avatars:
        self.avatar.addItem("Aucun avatar manuel créé", -1)
    else:
        for desc, idx in manual_avatars:
            self.avatar.addItem(desc, idx)

    # Restaurer la sélection si possible
    if current_data is not None and current_data >= 0 and current_data < len(self.avatar_creations):
        av_dict = self.avatar_creations[current_data]
        if not av_dict.get('__from_loop', False) and not av_dict.get('__from_granulo', False):
            self.avatar.setCurrentIndex(self.avatar.findData(current_data))

    self.avatar.blockSignals(False)

   
