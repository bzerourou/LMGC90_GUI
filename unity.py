
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton

class UnitsOptionsDialog(QDialog):
    def __init__(self, current_units, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options du projet - Unités")
        self.resize(400, 300)
        
        layout = QVBoxLayout()

        # --- Description ---
        layout.addWidget(QLabel("Définissez le système d'unités pour ce projet.\n"
                                "LMGC90 ne fait pas de conversion, soyez cohérent !"))

        # --- Formulaire ---
        form_layout = QFormLayout()
        self.inputs = {}
        
        # Liste des unités à gérer
        self.unit_labels = ["Longueur", "Masse", "Temps", "Volume", "Force", "Pression/Contrainte", "Densité", "Énergie", "Température",
                            "Flux ther" ,"Moment inertie" ,"Couple" ,"Vitesse","Viscosité"]
        
        # Création des champs
        for label in self.unit_labels:
            le = QLineEdit()
            le.setText(current_units.get(label, ""))
            form_layout.addRow(f"{label} :", le)
            self.inputs[label] = le
            
        layout.addLayout(form_layout)

        # --- Boutons Rapides (SI / CGS) ---
        quick_btn_layout = QHBoxLayout()
        btn_si = QPushButton("Tout en SI (m, kg, s)")
        btn_cgs = QPushButton("Tout en CGS (cm, g, s)")
        
        btn_si.clicked.connect(self.set_si)
        btn_cgs.clicked.connect(self.set_cgs)
        
        quick_btn_layout.addWidget(btn_si)
        quick_btn_layout.addWidget(btn_cgs)
        layout.addLayout(quick_btn_layout)

        # --- Boutons Valider / Annuler ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def set_si(self):
        """Remplit les champs avec le Système International"""
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
        for label, val in defaults.items():
            self.inputs[label].setText(val)

    def set_cgs(self):
        """Remplit les champs avec le système CGS"""
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
        for label, val in defaults.items():
            self.inputs[label].setText(val)

    def get_data(self):
        """Récupère les données saisies"""
        return {label: self.inputs[label].text() for label in self.unit_labels}