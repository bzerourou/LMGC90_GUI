from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QLineEdit, QPushButton, QFormLayout, QDialogButtonBox, QGroupBox,
    QFileDialog, QStyle
)
from PyQt6.QtCore import Qt

class PreferencesDialog(QDialog):
    def __init__(self, current_units, current_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préférences du projet")
        self.resize(800, 600)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # --- CRÉATION DES ONGLETS VERTICAUX ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West) # <--- C'est ici que ça se joue !
        
        # On agrandit un peu la police des onglets pour que ce soit lisible
        self.tabs.setStyleSheet("QTabBar::tab { height: 80px; width: 100px; }")

        # --- ONGLET 1 : GÉNÉRAL (Chemins) ---
        self.tab_general = QWidget()
        self._init_general_tab(current_paths)
        self.tabs.addTab(self.tab_general, "Général")

        # --- ONGLET 2 : UNITÉS ---
        self.tab_units = QWidget()
        self._init_units_tab(current_units)
        self.tabs.addTab(self.tab_units, "Unités")

        main_layout.addWidget(self.tabs)

        # --- BOUTONS (OK / Annuler) ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def _init_general_tab(self, paths):
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # Champ 1 : Répertoire par défaut des projets
        self.path_project_dir = QLineEdit(paths.get('default_dir', ''))
        btn_browse_proj = QPushButton("...")
        btn_browse_proj.setFixedWidth(30)
        btn_browse_proj.clicked.connect(lambda: self.browse_folder(self.path_project_dir))
        
        h_proj = QHBoxLayout()
        h_proj.addWidget(self.path_project_dir)
        h_proj.addWidget(btn_browse_proj)
        
        form.addRow("Dossier Projets :", h_proj)
        
        # Champ 2 : (Optionnel) Chemin vers l'exécutable Python ou LMGC90
        self.path_exec = QLineEdit(paths.get('lmgc90_exec', ''))
        btn_browse_exec = QPushButton("...")
        btn_browse_exec.setFixedWidth(30)
        btn_browse_exec.clicked.connect(lambda: self.browse_folder(self.path_exec)) # ou browse_file
        
        h_exec = QHBoxLayout()
        h_exec.addWidget(self.path_exec)
        h_exec.addWidget(btn_browse_exec)
        
        form.addRow("Chemin Exécutable :", h_exec)
        
        # Ajout au layout
        grp = QGroupBox("Chemins et Répertoires")
        grp.setLayout(form)
        layout.addWidget(grp)
        layout.addStretch() # Pousse tout vers le haut
        self.tab_general.setLayout(layout)

    def _init_units_tab(self, units):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Système d'unités du projet</b>"))
        
        form = QFormLayout()
        self.unit_inputs = {}
        labels  = ["Longueur", "Masse", "Temps", "Volume", "Force", "Pression/Contrainte", "Densité", "Énergie", "Température",
                            "Flux ther" ,"Moment inertie" ,"Couple" ,"Vitesse","Viscosité"]
        for lbl in labels:
            le = QLineEdit(units.get(lbl, ""))
            form.addRow(f"{lbl} :", le)
            self.unit_inputs[lbl] = le
            
        layout.addLayout(form)
        
        # Boutons SI / CGS
        hbox = QHBoxLayout()
        btn_si = QPushButton("Appliquer SI (m, kg, s)")
        btn_cgs = QPushButton("Appliquer CGS (cm, g, s)")
        
        btn_si.clicked.connect(self.set_si)
        btn_cgs.clicked.connect(self.set_cgs)
        
        hbox.addWidget(btn_si)
        hbox.addWidget(btn_cgs)
        layout.addLayout(hbox)
        
        self.tab_units.setLayout(layout)

    # --- UTILITAIRES ---
    def browse_folder(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if d:
            line_edit.setText(d)

    def set_si(self):
        defaults = {
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
        for k, v in defaults.items():
            if k in self.unit_inputs: self.unit_inputs[k].setText(v)

    def set_cgs(self):
        defaults = {
            "Longueur": "cm", 
            "Masse": "g", 
            "Temps": "s",
            "Volume" : "m^3",
            "Force": "dyn", 
            "Pression/Contrainte": "dyn/cm^2", 
            "Densité": "g/cm^3", 
            "Énergie": "erg",
            "Température": "K",
            "Flux ther" : "W",
            "Moment inertie" : "gcm^2",
            "Couple" : "dyne.cm" ,
            "Vitesse" : "cm/s",
            "Viscosité" : "poise"
        }
        for k, v in defaults.items():
            if k in self.unit_inputs: self.unit_inputs[k].setText(v)

    # --- GETTERS (Pour récupérer les données) ---
    def get_units_data(self):
        return {k: v.text() for k, v in self.unit_inputs.items()}

    def get_paths_data(self):
        return {
            'default_dir': self.path_project_dir.text(),
            'lmgc90_exec': self.path_exec.text()
        }