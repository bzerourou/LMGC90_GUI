# ========================================
# PROJET
# ========================================

import json
import os
from PyQt6.QtWidgets import QInputDialog, QFileDialog, QMessageBox, QLineEdit, QComboBox

from updates import (
    update_selections, update_model_tree, update_status
)

from preferences import PreferencesDialog

from pylmgc90 import pre
import numpy as np


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
    self.setWindowTitle(f"LMGC90_GUI v0.2.7 - {self.project_name}")
    update_status(self, "Nouveau projet créé")
    QMessageBox.information(self, "Succès", "Nouveau projet vide")

def open_project(self):
    file, _ = QFileDialog.getOpenFileName(self, "Ouvrir projet", "", "Projet LMGC90 (*.lmgc90)")
    if not file:
        return
    # Recréer matériaux, modèles, avatars, etc.
    try:
        with open(file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        self.project_dir = os.path.dirname(file)
        self.project_name = state.get("project_name", "Projet_sans_nom")
        self._init_containers()
        _deserialize_state(self, state)
    

        self.setWindowTitle(f"LMGC90_GUI v0.2.7 - {self.project_name}")
        update_status(self, f"Projet chargé : {self.project_name}")
        update_model_tree(self)
        update_selections(self)
    except Exception as e:
        QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le projet :\n{e}")

def save_project(self):
    # Si on n'a jamais sauvegardé → on force "Enregistrer sous"
    if not self.project_dir:
        return save_project_as(self)
    # Sinon : sauvegarde rapide dans le dossier déjà connu
    do_save(self)
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
    do_save(self)
    update_status(self, f"Projet enregistré dans : {dir_path}")


def do_save(self):
    """Fonction centrale qui fait vraiment la sauvegarde"""
    os.makedirs(self.project_dir, exist_ok=True)
    json_path = os.path.join(self.project_dir, f"{self.project_name}.lmgc90")

    state = _serialize_state(self)

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
        'granulo_generations' : self.granulo_generations,
        'postpro_creations' : self.postpro_creations
    }

def _deserialize_state(self, state):
    new_project(self)  # Reset complet
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
        if 'fric' in law: 
            l = pre.tact_behav(name=law['name'], law=law['law'], fric=law['fric'])
        else: 
            l = pre.tact_behav(name=law['name'], law=law['law'])
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