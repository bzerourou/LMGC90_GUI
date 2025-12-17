import math
import numpy as np
from pylmgc90 import pre
from PyQt6.QtWidgets import QMessageBox, QApplication, QTreeWidgetItem

from updates import (
 _safe_eval_dict
)

from updates import (
    update_model_elements,
    update_avatar_types, update_avatar_fields,
    update_granulo_fields, update_selections,
    update_model_tree, update_status, _safe_eval_dict,
    update_contactors_fields, update_postpro_avatar_selector
)

# ========================================
# CRÉATIONS
# ========================================
def create_material(self):
    try:
        name = self.mat_name.text().strip()
        if not name:
            raise ValueError("Nom vide")
        if len(name)>5: 
            raise ValueError("Nom à 5 caractères")
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
        if len(name)>5 : raise ValueError("Nom à 5 caractères")
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
        if mod.element != "Rxx2D" :
            raise ValueError("élément finit non adapté pour un rigid avatar")

        is_hollow = self.avatar_hallowed.isChecked()
        if type == "rigidDisk" :
            if is_hollow :
                
    # Contacteur xKSID 
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
            raise ValueError(f"3D non supporté ")

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

# =========================
# GRANULO SAMPLE
# ===========================

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
            elif  avatar == "rigidPolygon": 
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

# =======================================
# PostPro Commabds 
# =======================================

def add_postpro_command(self):
    name = self.post_name.currentText()
    try:
        step = int(self.post_step.text())
        if step <= 0:
            raise ValueError
    except:
        QMessageBox.warning(self, "Erreur", "Le step doit être un entier positif.")
        return

    rigid_set = None
    if name in ["TORQUE EVOLUTION", "BODY TRACKING","NEW RIGID SETS"]:
        if not self.post_avatar_selector.isEnabled():
            QMessageBox.warning(self, "Erreur", "Sélectionnez un avatar ou groupe pour cette commande.")
            return
        data = self.post_avatar_selector.currentData()
        if not data:
            QMessageBox.warning(self, "Erreur", "Aucun avatar/groupe sélectionné.")
            return

        typ, value = data
        if typ == "avatar":
            rigid_set = [self.bodies_list[value]]  # pre attend une liste d'avatars
        elif typ == "group":
            indices = self.avatar_groups.get(value, [])
            rigid_set = [self.bodies_list[i] for i in indices if i < len(self.bodies_list)]

        if not rigid_set:
            QMessageBox.warning(self, "Erreur", "Aucun avatar valide dans la sélection.")
            return

    # Stockage de la commande
    cmd_dict = {
        'name': name,
        'step': step,
        'rigid_set': rigid_set  # None ou liste d'objets avatar
    }
    self.postpro_commands.append(cmd_dict)

    # Mise à jour de l'arbre
    item_text = name
    avatar_text = ""
    if rigid_set:
        if len(rigid_set) == 1:
            avatar_text = "1 avatar"
        else:
            avatar_text = f"{len(rigid_set)} avatars"
        if len(rigid_set) > 5:
            avatar_text += " (groupe)"
    tree_item = QTreeWidgetItem([item_text, str(step), avatar_text])
    self.post_tree.addTopLevelItem(tree_item)

    # Réinitialiser les champs
    self.post_step.setText("1")
    update_postpro_avatar_selector(self, name)

def delete_postpro_command(self):
    selected_items = self.post_tree.selectedItems()
    if not selected_items:
        QMessageBox.warning(self, "Sélection requise", "Sélectionnez une commande dans la liste pour la supprimer.")
        return

    # On prend le premier élément sélectionné (Qt permet la multi-sélection, mais on gère un par un)
    item = selected_items[0]
    index = self.post_tree.indexOfTopLevelItem(item)

    # Sécurité absolue contre l'IndexError
    if index < 0 or index >= len(self.postpro_commands):
        QMessageBox.critical(self, "Erreur interne", "Index de commande invalide. Réessayez ou redémarrez.")
        return

    reply = QMessageBox.question(self, "Confirmer", 
                                 f"Supprimer la commande '{self.postpro_commands[index]['name']}' ?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply != QMessageBox.StandardButton.Yes:
        return
    #Suppression sûre
    del self.postpro_commands[index]

    # Suppression dans l'arbre (plus fiable que takeTopLevelItem)
    self.post_tree.takeTopLevelItem(index)

    self.statusBar().showMessage("Commande post-pro supprimée", 3000)
# ==============
# CRUD
# ================
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