
 # ========================================
    # ACTIONS/GENERATION SCRIPT
    # ========================================

import math
import os
import subprocess
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QApplication


def _write_avatar_creation(self, f, i, av, container_name="bodies"):
    #avatar vide
    if av['type'] == 'emptyAvatar':
        _write_empty_avatar_creation(self, f, i, av, container_name)
        return

    func = _get_avatar_function(self, av)
    params = _get_avatar_params(self, av)
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
        param_str = ", ".join(f"{k}={_format_value_for_python(self,v)}" for k, v in params.items())
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
                        formatted = _format_value_for_python(self,v)
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
                _write_avatar_creation(self,f, i, av , "bodies")

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
                f.write(f"    body = pre.{_get_avatar_function(self, model_av)}(center=center, ")
                f.write(f"model=mods['{mod.nom}'], material=mats['{mat.nom}'], color='{color}'")

                # Paramètres spécifiques
                params = _get_avatar_params(self, model_av)
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
                    _write_avatar_creation(self, f, av, safe_name)
            
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

                elif "Couette2D" in shape : 
                    f.write(f"rint = {params['rint']}\n")
                    f.write(f"rext = {params['rext']}\n")
                    f.write("nb_remaining, coor = pre.depositInCouette2D(radii, rint, rext)\n")

                elif "Drum2D" in shape : 
                    f.write(f"r = {params['r']}\n")
                    f.write("nb_remaining, coor = pre.depositInDrum2D(radii, r)\n")
                    

                
                mat_var = f"mats['{gen['mat_name']}']" 
                mod_var = f"mods['{gen['mod_name']}']"
                
                f.write("\n# Création des avatars du lot\n")
                f.write("nb_remaining = np.shape(coor)[0]//2\n")
                f.write("coor = np.reshape(coor, (nb_remaining, 2))\n")
                f.write("for i in range(nb_remaining):\n")
                
                if gen['avatar_type'] == "rigidDisk":
                    f.write(f"    body = pre.rigidDisk(r=radii[i], center=coor[i], model=mods['{mod_var}'], material=mats['{mod_var}'], color='{gen['color']}')\n")
            
                elif gen['avatar_type'] == "rigidPolygon":
                    # On suppose que les paramètres sont stockés dans gen (ou on les récupère via l'index)
                    # Pour simplifier, on suppose que tu as sauvegardé les params nécessaires dans granulo_generations
                    gen_params = gen.get('model_params', {})
                    f.write(f"    body = pre.rigidPolygon(center=center, model=mods['{mod_var}'], material=mats['{mod_var}'], color='{color}',\n")
                    f.write(f"                               radius={gen_params.get('radius', 0.1)} * (r / {gen.get('ref_radius', 0.1)}),\n")
                    if gen_params.get('gen_type') == "regular":
                        f.write(f"                               generation_type='regular', nb_vertices={gen_params.get('nb_vertices')})\n")
                    else:
                        f.write(f"                               generation_type='{gen_params.get('gen_type')}', vertices=np.array({gen_params.get('vertices')}) * (r / {gen.get('ref_radius', 0.1)}))\n")

                elif gen['avatar_type'] == "rigidOvoidPolygon":
                    gen_params = gen.get('model_params', {})
                    scale = gen.get('ref_radius', 0.1)
                    f.write(f"    body = pre.rigidOvoidPolygon(center=center, model=mods['{mod_var}'], material=mats['{mod_var}'], color='{color}',\n")
                    f.write(f"                                 ra={gen_params.get('ra', 1.0)} ,\n")
                    f.write(f"                                 rb={gen_params.get('rb', 0.5)} ,\n")
                    f.write(f"                                 nb_vertices={gen_params.get('nb_vertices')})\n")

                elif gen['avatar_type'] == "rigidJonc":
                    gen_params = gen.get('model_params', {})
                    scale = gen.get('ref_radius', 0.1)
                    f.write(f"    body = pre.rigidJonc(center=center, model=mods['{mod_var}'], material=mats['{mod_var}'], color='{color}',\n")
                    f.write(f"                         axe1={gen_params.get('axe1', 1.0)} ,\n")
                    f.write(f"                         axe2={gen_params.get('axe2', 0.1)} )\n")

                elif gen['avatar_type'] == "emptyAvatar":
                    f.write(f"    # Avatar vide complexe — reconstruction manuelle recommandée\n")
                    f.write(f"    # body = pre.avatar(dimension=2)\n")
                    f.write(f"    # ... (contacteurs à recopier manuellement)\n")
                    f.write(f"    # body.computeRigidProperties()\n")
                    f.write(f"    # bodies.addAvatar(body)\n")
            
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
                if cmd['rigid_set'] is not None:
                    f.write(f"post.addCommand(pre.postpro_command(name='{cmd['name']}', step={cmd['step']}, rigid_set={cmd['rigid_set']} ))\n" )
                else : 
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
        self.statusBar().showMessage("Exécute le script...")
        QApplication.processEvents()
        path = self.script_path or os.path.join(self.current_project_dir or os.getcwd(), "lmgc_sim.py")
        file, _ = QFileDialog.getOpenFileName(self, "Exécuter", path, "Python (*.py)")
        if not file: return
        try:
            result = subprocess.run(['python', file], capture_output=True, text=True, check=True)
            QMessageBox.information(self, "Succès", result.stdout or "Exécuté sans sortie")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"{e}")
