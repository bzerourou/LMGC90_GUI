from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,  
     QPushButton,  QDialogButtonBox, 
     QTreeWidget, QTreeWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt


class DynamicVarsDialog(QDialog):
    def __init__(self, current_vars, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Variables dynamiques")
        self.resize(500, 400)
        self.current_vars = current_vars.copy()

        layout = QVBoxLayout()

        # Tableau des variables
        self.table = QTreeWidget()
        self.table.setHeaderLabels(["Nom", "Valeur"])
        self.table.setColumnWidth(0, 150)
        self.populate_table()
        layout.addWidget(self.table)

        # Boutons ajouter/supprimer
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(self.add_var)
        del_btn = QPushButton("Supprimer")
        del_btn.clicked.connect(self.del_var)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Boutons OK/Annuler
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def populate_table(self):
        self.table.clear()
        for name, value in self.current_vars.items():
            item = QTreeWidgetItem([name, str(value)])
            self.table.addTopLevelItem(item)

    def add_var(self):
        name, ok1 = QInputDialog.getText(self, "Nom de variable", "Entrez le nom (ex: thickness, offset) :")
        if not ok1 or not name.strip():
            return
        value, ok2 = QInputDialog.getText(self, "Valeur", f"Valeur pour {name} :")
        if not ok2:
            return
        try:
            # On accepte float, int, ou string
            if '.' in value or 'e' in value.lower():
                val = float(value)
            else:
                val = int(value)
        except:
            val = value  # string si pas numérique

        self.current_vars[name] = val
        self.populate_table()

    def del_var(self):
        selected = self.table.currentItem()
        if selected:
            name = selected.text(0)
            del self.current_vars[name]
            self.populate_table()

    def get_vars(self):
        return self.current_vars