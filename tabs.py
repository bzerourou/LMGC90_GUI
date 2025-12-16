from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLineEdit,
    QComboBox, QCheckBox, QLabel, QPushButton, QScrollArea, QTreeWidget
)
from PyQt6.QtCore import Qt

from updates import (
    update_material_fields, update_model_options_fields, update_model_elements,
    update_avatar_types, update_avatar_fields, update_polygon_fields,
    update_loop_fields, update_dof_options, update_contact_law,
    update_advanced_fields, update_granulo_fields,
    model_dimension_changed
)


from creations import (
    create_material, create_model, create_avatar, create_empty_avatar, create_loop,
    generate_granulo_sample, dof_force, create_contact_law, add_visibility_rule,
    add_postpro_command, delete_postpro_command, modify_selected, delete_selected
)

# ========================================
#  CREATION - TABS
# =========================================

def _create_material_tab(self):
    # === Matériau ===
    mat_tab = QWidget()
    ml = QVBoxLayout()
    self.mat_name = QLineEdit("TDURx"); self.mat_type = QComboBox(); self.mat_type.addItems(["RIGID", "ELAS", "ELAS_DILA", "VISCO_ELAS", "ELAS_PLAS", "THERMO_ELAS", "PORO_ELAS"])
    self.mat_density_label = QLabel("Densité :"); self.mat_density = QLineEdit("1000."); self.mat_props_label = QLabel("Propriétés (ex: young=1e9) :");self.mat_props = QLineEdit("")
    self.mat_type.currentTextChanged.connect(lambda : update_material_fields(self))      
    for label, widget in [
        ("Nom :", self.mat_name), ("Type :", self.mat_type)
    ]:
        ml.addWidget(QLabel(label)); ml.addWidget(widget)
    ml.addWidget(self.mat_density_label) ; ml.addWidget(self.mat_density)
    ml.addWidget(self.mat_props_label); ml.addWidget(self.mat_props)
    btn_layout = QHBoxLayout()
    create_btn = QPushButton("Créer")
    modify_btn = QPushButton("Modifier")
    delete_btn = QPushButton("Supprimer")
    create_btn.clicked.connect(lambda : create_material(self))
    modify_btn.clicked.connect(lambda :modify_selected(self))
    delete_btn.clicked.connect(lambda :delete_selected(self))
    for b in [create_btn, modify_btn, delete_btn]:
        btn_layout.addWidget(b)
    ml.addLayout(btn_layout)
    mat_tab.setLayout(ml)
    self.tabs.addTab(mat_tab, "Matériau")
    self.mat_tab = mat_tab

def _create_model_tab(self):
    # --- Modèle ---
    mod_tab = QWidget()
    mml = QVBoxLayout()
    self.model_name = QLineEdit("rigid")
    self.model_physics = QComboBox(); self.model_physics.addItems(["MECAx"])
    self.model_element = QComboBox()
    self.model_element.currentTextChanged.connect(lambda : update_model_options_fields(self))
    self.model_dimension = QComboBox(); self.model_dimension.addItems(["2", "3"])
    self.model_dimension.currentTextChanged.connect(lambda: model_dimension_changed(self))
    self.model_options = QLineEdit("")
    # Zone des options (scrollable)
    self.model_options_group = QGroupBox("Options du modèle")
    self.model_options_layout = QFormLayout()
    self.model_options_group.setLayout(self.model_options_layout)
    self.model_options_group.setVisible(False)
    mml.addWidget(self.model_options_group)
    for w in [QLabel("Nom:"), self.model_name, QLabel("Phys:"), self.model_physics,
                QLabel("Élément:"), self.model_element, QLabel("Dim:"), self.model_dimension,
                QLabel("Opts:"), self.model_options,
                ]:
        mml.addWidget(w)
    btn_layout = QHBoxLayout()
    create_mod_btn = QPushButton("Créer")
    modify_mod_btn = QPushButton("Modifier")
    delete_mod_btn = QPushButton("Supprimer")
    create_mod_btn.clicked.connect(lambda : create_model(self))
    modify_mod_btn.clicked.connect(lambda :modify_selected(self))
    delete_mod_btn.clicked.connect(lambda :delete_selected(self))
    for b in [create_mod_btn, modify_mod_btn, delete_mod_btn]:
        btn_layout.addWidget(b)
    mml.addLayout(btn_layout)
    mod_tab.setLayout(mml)
    self.tabs.addTab(mod_tab, "Modèle")
    self.mod_tab = mod_tab
    #initialisation des éléments
    update_model_elements(self)

def _create_avatar_tab(self):
    # --- Avatar ---
    av_tab = QWidget()
    al = QVBoxLayout()
    self.avatar_types_2d = ["rigidDisk", "rigidJonc", "rigidPolygon", "rigidOvoidPolygon", "rigidDiscreteDisk", "rigidCluster",
                            "roughWall", "fineWall", "smoothWall", "granuloRoughWall"]
    self.avatar_types_3d = ["rigidSphere"]
    self.avatar_type = QComboBox()
    self.avatar_hallowed = QCheckBox("Avatar disque  creux (pour les disques)")
    self.avatar_radius_label = QLabel("Rayon");self.avatar_radius = QLineEdit("0.1")
    self.avatar_axis_label = QLabel("Axes :");self.avatar_axis = QLineEdit(("axe1 = 2.0, axe2 = 0.05"))
    self.avatar_vertices_label = QLabel("Vertices : ")
    self.avatar_vertices = QLineEdit("[[-0.5,-0.5],[0.5,-0.5],[0.5,0.5],[-0.5,0.5]]")
    self.avatar_nb_vertices_label  =  QLabel("Nombre de vertices : ")
    self.avatar_nb_vertices  = QLineEdit("5")
    self.avatar_r_ovoid_label = QLabel("Rayon Ellipse : ")
    self.avatar_r_ovoid = QLineEdit("ra = 1. , rb = 0.5")
    self.avatar_gen_type = QLabel("Type de génération ")
    self.avatar_gen = QComboBox()
    self.avatar_gen.addItems(["regular", "full", "bevel"] )
    self.avatar_gen.currentTextChanged.connect(update_polygon_fields)
    self.avatar_center_label = QLabel("Centre:");self.avatar_center = QLineEdit("0.0,0.0")
    self.avatar_material = QComboBox()
    self.avatar_model = QComboBox()
    self.avatar_color = QLineEdit("BLUEx")
    # --- Champs pour walls ---
    self.wall_length_label = QLabel("Longueur :")
    self.wall_length = QLineEdit("2.0")
    self.wall_height_label = QLabel("Rayon :")
    self.wall_height = QLineEdit("0.15")

    self.avatar_properties = QLineEdit("")

    for w in [QLabel("Type:"), self.avatar_type, self.avatar_hallowed,self.avatar_radius_label, self.avatar_radius,self.avatar_axis_label,self.avatar_axis, self.avatar_r_ovoid_label,self.avatar_r_ovoid,self.wall_length_label, self.wall_length,
                self.wall_height_label, self.wall_height,
                self.avatar_gen_type, self.avatar_gen, self.avatar_nb_vertices_label, self.avatar_nb_vertices, self.avatar_vertices_label, self.avatar_vertices, self.avatar_center_label, self.avatar_center, QLabel("Mat:"), self.avatar_material,
                QLabel("Mod:"), self.avatar_model, QLabel("Couleur:"), self.avatar_color,
                QLabel("Props:"), self.avatar_properties,
                ]:
        al.addWidget(w)
    btn_layout = QHBoxLayout()
    create_av_btn = QPushButton("Créer")
    modify_av_btn = QPushButton("Modifier")
    delete_av_btn = QPushButton("Supprimer")
    create_av_btn.clicked.connect(lambda :create_avatar(self))
    modify_av_btn.clicked.connect(lambda :modify_selected(self))
    delete_av_btn.clicked.connect(lambda :delete_selected(self))
    for b in [create_av_btn, modify_av_btn, delete_av_btn]:
        btn_layout.addWidget(b)
    al.addLayout(btn_layout)
    av_tab.setLayout(al)
    self.tabs.addTab(av_tab, "Avatar")
    self.av_tab = av_tab

    # Connecter le signal après la création des widgets, en bloquant les signaux
    self.avatar_type.blockSignals(True)
    update_avatar_types(self, self.model_dimension.currentText())
    self.avatar_type.blockSignals(False)
    self.avatar_type.currentTextChanged.connect(lambda text: update_avatar_fields(self, text))

    # Terminer l'initialisation
    self._initializing = False
    update_avatar_fields(self, self.avatar_type.currentText())

def _create_empty_avatar_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # === Dimension ===
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Dimension :"))
        self.adv_dim = QComboBox()
        self.adv_dim.addItems(["2", "3"])
        self.adv_dim.currentTextChanged.connect(lambda dim_text: update_advanced_fields(self, dim_text))
        dim_layout.addWidget(self.adv_dim)
        layout.addLayout(dim_layout)

        # === Centre (node principal) ===
        center_layout = QHBoxLayout()
        self.empty_av_center_label = QLabel("Centre (x,y,z) :")
        center_layout.addWidget(self.empty_av_center_label)
        self.adv_center = QLineEdit("0.0, 0.0")
        center_layout.addWidget(self.adv_center)
        layout.addLayout(center_layout)

        # === Couleur globale ===
        color_layout = QHBoxLayout()
        #color_layout.addWidget(QLabel("Couleur :"))
        self.adv_color = QLineEdit("BLUEx")
        #color_layout.addWidget(self.adv_color)
        layout.addLayout(color_layout)

        # === Matériau & Modèle ===
        matmod_layout = QHBoxLayout()
        matmod_layout.addWidget(QLabel("Matériau :"))
        self.adv_material = QComboBox()
        matmod_layout.addWidget(self.adv_material)
        matmod_layout.addWidget(QLabel("Modèle :"))
        self.adv_model = QComboBox()
        matmod_layout.addWidget(self.adv_model)
        layout.addLayout(matmod_layout)

        # === Contacteurs (liste dynamique) ===
        layout.addWidget(QLabel("Contacteurs à ajouter :"))
        self.contactors_list = QWidget()
        self.contactors_layout = QVBoxLayout()
        self.contactors_list.setLayout(self.contactors_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.contactors_list)
        layout.addWidget(scroll)

        add_contactor_btn = QPushButton("Ajouter un contacteur")
        add_contactor_btn.clicked.connect(self.add_contactor_row)
        layout.addWidget(add_contactor_btn)

        # === Bouton Créer ===
        create_btn = QPushButton("Créer avatar vide")
        create_btn.clicked.connect(lambda :create_empty_avatar(self))
        layout.addWidget(create_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Avatar vide")
        self.empty_tab = tab

        # Premier contacteur par défaut
        self.add_contactor_row()


def _create_loop_tab(self):
    # avatars boucles ---
    loop_tab = QWidget()
    ll = QVBoxLayout()
    self.loop_type = QComboBox()
    self.loop_type.addItems(["Cercle", "Grille", "Ligne", "Spirale", "Manuel"])
    self.loop_avatar_type = QComboBox()
    self.loop_count = QLineEdit("10")
    self.loop_radius = QLineEdit("2.0")
    self.loop_step = QLineEdit("1.0")
    self.loop_inv_axe = QCheckBox("inverser l'axe")
    self.loop_offset_x = QLineEdit("0.0")
    self.loop_offset_y = QLineEdit("0.0")
    self.loop_spiral_factor = QLineEdit("0.1")
    # stockage dans une liste nommée
    self.loop_store_group = QCheckBox("Stocker dans une liste nommée")
    self.loop_group_name = QLineEdit("granulats_cercle")
    self.loop_group_name.setPlaceholderText("Nom du groupe (ex: murs_gauche)")
    ll.addWidget(QLabel("Type de boucle :"))
    ll.addWidget(self.loop_type)
    ll.addWidget(QLabel("Nombre:  :"))
    ll.addWidget(self.loop_count)
    geom_widgets =  [
        
        ("Avatar à répéter :", self.loop_avatar_type),
        ("Rayon / Pas :", self.loop_radius),
        ("Pas X/Y :", self.loop_step),
        ("", self.loop_inv_axe),
        ("Offset X :", self.loop_offset_x),
        ("Offset Y :", self.loop_offset_y),
        ("Facteur spirale :", self.loop_spiral_factor),
    ]
    self.geom_layout_items = []
    for label_text, widget in geom_widgets:
        ll.addWidget(QLabel(label_text))
        ll.addWidget(widget)
        # On garde une référence pour les masquer facilement
        self.geom_layout_items.extend([ll.itemAt(ll.count()-2), ll.itemAt(ll.count()-1)])
    ll.addWidget(self.loop_store_group)
    hgroup = QHBoxLayout()
    hgroup.addWidget(QLabel("Nom du groupe :"))
    hgroup.addWidget(self.loop_group_name)
    ll.addLayout(hgroup)
    create_loop_btn = QPushButton("Créer boucle")
    create_loop_btn.clicked.connect(lambda :create_loop(self))
    ll.addWidget(create_loop_btn)
    loop_tab.setLayout(ll)
    self.tabs.addTab(loop_tab, "Boucles")
    # Connexion pour masquer/afficher les champs selon le type
    self.loop_type.currentTextChanged.connect(lambda loop_type: update_loop_fields(self, loop_type))
    update_loop_fields(self, self.loop_type.currentText())

def _create_dof_tab(self):
    # --- DOF ---
    dof_tab = QWidget()
    dl = QVBoxLayout()
    self.dof_avatar_name = QComboBox()
    self.dof_avatar_force = QComboBox(); self.dof_avatar_force.addItems(["translate", "rotate", "imposeDrivenDof", "imposeInitValue"])
    self.dof_options = QLineEdit("dx=0.0, dy=2.0")
    
    self.dof_avatar_force.currentTextChanged.connect(lambda action: update_dof_options(self, action))
    for w in [QLabel("Avatar:"), self.dof_avatar_name, QLabel("Action:"), self.dof_avatar_force,
                QLabel("Params:"), self.dof_options,
                ]:
        dl.addWidget(w)
    dof_btn = QPushButton("Appliquer")
    dof_btn.clicked.connect( lambda : dof_force(self))
    dl.addWidget(dof_btn)
    dof_tab.setLayout(dl)
    self.tabs.addTab(dof_tab, "DOF")
    #initialisation du texte 
    update_dof_options(self, self.dof_avatar_force.currentText())

def _create_contact_tab(self):    
    # --- Contact ---
    self.contact_tab = QWidget()
    cl = QVBoxLayout()
    self.contact_name = QLineEdit("iqsc0")
    self.contact_type = QComboBox(); self.contact_type.addItems(["IQS_CLB", "IQS_CLB_g0", "COUPLED_DOF"])
    self.contact_type.currentTextChanged.connect(lambda: update_contact_law(self))
    self.contact_properties = QLineEdit("fric=0.3")
    for w in [QLabel("Nom:"), self.contact_name, QLabel("Type:"), self.contact_type,
                QLabel("Props:"), self.contact_properties,
                ]:
        cl.addWidget(w)
    btns = QHBoxLayout()
    for text, slot in [("Créer", lambda : create_contact_law(self)), ("Modifier", lambda :modify_selected(self)), ("Supprimer", lambda :delete_selected(self))]:
        b = QPushButton(text); b.clicked.connect(slot); btns.addWidget(b)
    cl.addLayout(btns)
    self.contact_tab.setLayout(cl)
    self.tabs.addTab(self.contact_tab, "Contact")

def _create_visibility_tab(self) : 
    # --- Visibilité ---
    vis_tab = QWidget()
    vl = QVBoxLayout()
    self.vis_corps_candidat = QComboBox(); self.vis_corps_candidat.addItem("RBDY2")
    self.vis_candidat = QComboBox(); self.vis_candidat.addItems(["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"])
    self.candidat_color = QLineEdit("BLUEx")
    self.vis_corps_antagoniste = QComboBox(); self.vis_corps_antagoniste.addItem("RBDY2")
    self.vis_antagoniste = QComboBox(); self.vis_antagoniste.addItems(["DISKx", "xKSID", "JONCx", "POLYG", "PT2Dx"])
    self.antagoniste_color = QLineEdit("VERTx")
    self.behav = QComboBox()
    self.vis_alert = QLineEdit("0.1")
    for w in [QLabel("Candidat:"), self.vis_corps_candidat, self.vis_candidat, self.candidat_color,
                QLabel("Antagoniste:"), self.vis_corps_antagoniste, self.vis_antagoniste, self.antagoniste_color,
                QLabel("Loi:"), self.behav, QLabel("Alerte:"), self.vis_alert,
                ]:
        vl.addWidget(w)
    btns = QHBoxLayout()
    for text, slot in [("Ajouter", lambda :add_visibility_rule(self)), ("Modifier", lambda :modify_selected(self)), ("Supprimer", lambda :delete_selected(self))]:
        b = QPushButton(text); b.clicked.connect(slot); btns.addWidget(b)
    vl.addLayout(btns)
    vis_tab.setLayout(vl)
    self.tabs.addTab(vis_tab, "Visibilité")
    self.vis_tab =vis_tab

def _create_postpro_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()
    
    # --- Zone de saisie ---
    form_group = QGroupBox("")
    form = QFormLayout()
    
    self.post_name = QComboBox()
    # Liste des commandes standards LMGC90
    commands_list = [
        "SOLVER INFORMATIONS" 
    ] #, "VIOLATION EVOLUTION", "KINETIC ENERGY",
        #  "DISSIPATED ENERGY", "COORDINATION NUMBER", "BODY TRACKING",
        #  "TORQUE EVOLUTION", "DOUBLET TORQUE EVOLUTION", "CL CONTACTOR"
    self.post_name.addItems(commands_list)
    
    self.post_step = QLineEdit("1")
    self.post_step.setPlaceholderText("Fréquence d'écriture (ex: 1)")
    
    form.addRow("Type de commande :", self.post_name)
    form.addRow("Step (Fréquence) :", self.post_step)
    
    add_btn = QPushButton("Ajouter la commande")
    add_btn.clicked.connect(lambda :add_postpro_command(self))
    
    form_group.setLayout(form)
    layout.addWidget(form_group)
    layout.addWidget(add_btn)
    
    # --- Liste des commandes ajoutées ---
    layout.addWidget(QLabel("Commandes actives :"))
    self.post_tree = QTreeWidget()
    self.post_tree.setHeaderLabels(["Nom", "Step"])
    layout.addWidget(self.post_tree)
    
    # --- Bouton supprimer ---
    del_btn = QPushButton("Supprimer la commande sélectionnée")
    del_btn.clicked.connect(lambda :delete_postpro_command(self))
    layout.addWidget(del_btn)
    
    tab.setLayout(layout)
    self.tabs.addTab(tab, "Postpro")
    self.postpro_tab = tab
# ========================================
# GRANULOMETRIE
# ========================================

def _create_granulo_tab(self):
    tab = QWidget()
    layout = QVBoxLayout()

    # --- 1. Paramètres de Distribgit aution ---
    grp_dist = QGroupBox("1. Distribution des Particules")
    gl_dist = QFormLayout()
    
    self.gran_nb = QLineEdit("200")
    self.gran_rmin = QLineEdit("0.05")
    self.gran_rmax = QLineEdit("0.15")
    self.gran_seed = QLineEdit("") # Vide = None
    self.gran_seed.setPlaceholderText("Graine aléatoire (optionnel)")
    self.gran_rmin_label = QLabel("Rayon Min (r_min) :")
    self.gran_rmax_label = QLabel("Rayon Max (r_max) :")
    gl_dist.addRow("Nombre de particules :", self.gran_nb)
    gl_dist.addRow(self.gran_rmin_label, self.gran_rmin)
    gl_dist.addRow(self.gran_rmax_label, self.gran_rmax)
    gl_dist.addRow("Seed (entier) :", self.gran_seed)
    grp_dist.setLayout(gl_dist)
    layout.addWidget(grp_dist)

    # --- 2. Géométrie du Conteneur ---
    grp_geo = QGroupBox("2. Géométrie du Dépôt")
    vl_geo = QVBoxLayout()
    
    # Choix de la forme
    hl_type = QHBoxLayout()
    hl_type.addWidget(QLabel("Type de conteneur :"))
    self.gran_shape_type = QComboBox()
    self.gran_shape_type.addItems(["Box2D","Disk2D"])#,  "squareLattice2D", "triangularLattice2D","Couette2D", "Drum2D"])
    hl_type.addWidget(self.gran_shape_type)
    vl_geo.addLayout(hl_type)

    # Paramètres dynamiques (lx, ly, r, etc.)
    self.gran_params_widget = QWidget()
    self.gran_params_layout = QFormLayout()
    self.gran_params_widget.setLayout(self.gran_params_layout)
    vl_geo.addWidget(self.gran_params_widget)
    
    # Champs stockés en mémoire (on les affiche/cache selon le choix)
    self.gran_lx = QLineEdit("4.0")
    self.gran_ly = QLineEdit("4.0")
    self.gran_r = QLineEdit("2.0")
    self.gran_rint = QLineEdit("2.0")
    self.gran_rext = QLineEdit("4.0")

    grp_geo.setLayout(vl_geo)
    layout.addWidget(grp_geo)

    # --- 3. Propriétés Physiques ---
    grp_phy = QGroupBox("3. Propriétés Physiques")
    gl_phy = QFormLayout()
    
    self.gran_mat = QComboBox()
    self.gran_mod = QComboBox()
    self.gran_color = QLineEdit("BLUEx")
    self.avatar = QComboBox()
    self.avatar.addItems(["rigidDisk"]) #, "rigidPolygon", "rigidOvoidPolygon", "rigidDiscreteDisk", "rigidCluster"])
    self.gran_wall_create = QCheckBox("Créer les parois (murs) autour")
    self.gran_wall_create.setChecked(False)

    gl_phy.addRow("Matériau :", self.gran_mat)
    gl_phy.addRow("Modèle :", self.gran_mod)
    gl_phy.addRow("Couleur Particules :", self.gran_color)
    gl_phy.addRow("Type d'avatar :", self.avatar)
    #gl_phy.addRow(self.gran_wall_create)
    grp_phy.setLayout(gl_phy)
    layout.addWidget(grp_phy)

    # --- Bouton Action ---
    btn_gen = QPushButton("Générer le Dépôt")
    btn_gen.setStyleSheet("font-weight: bold; padding: 10px; background-color: #e1f5fe;")
    btn_gen.clicked.connect(lambda :generate_granulo_sample(self))
    layout.addWidget(btn_gen)

    # Scroll area (au cas où petit écran)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    container = QWidget()
    container.setLayout(layout)
    scroll.setWidget(container)

    final_layout = QVBoxLayout()
    final_layout.addWidget(scroll)
    tab.setLayout(final_layout)
    
    self.tabs.addTab(tab, "Granulométrie")
    self.gran_tab = tab

    # Connexions
    self.gran_shape_type.currentTextChanged.connect(lambda: update_granulo_fields(self))
    update_granulo_fields(self) # Init