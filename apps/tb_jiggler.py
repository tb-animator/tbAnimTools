'''tbAnimation Tools is a toolset for animators

*******************************************************************************

*******************************************************************************
'''

from . import *


class hotkeys(hotKeyAbstractFactory):
    def createHotkeyCommands(self):
        self.setCategory(self.helpStrings.category.get('keying'))
        self.commandList = list()
        self.addCommand(self.tb_hkey(name='tbJigglerUI', annotation='',
                                     category=self.category,
                                     command=['jiggleTool.showUI()']))

        return self.commandList

    def assignHotkeys(self):
        return

class Jiggler(toolAbstractFactory):
    """
    Use this as a base for toolAbstractFactory classes
    """
    # __metaclass__ = abc.ABCMeta
    __instance = None
    toolName = 'jiggleTool'
    subfolder = 'jiggleData'
    hotkeyClass = hotkeys()
    funcs = Functions()
    start_time = 0
    last_time = 0

    def __new__(cls):
        if Jiggler.__instance is None:
            Jiggler.__instance = object.__new__(cls)

        Jiggler.__instance.val = cls.toolName
        return Jiggler.__instance

    def __init__(self):
        self.hotkeyClass = hotkeys()
        self.funcs = Functions()
        self.initData()

    """
    Declare an interface for operations that create abstract product
    objects.
    """

    def initData(self):
        super(Jiggler, self).initData()
        self.presetDir = os.path.normpath(os.path.join(self.dataPath, self.subfolder))
        if not os.path.isdir(self.presetDir):
            os.mkdir(self.presetDir)

    def optionUI(self):
        return super(Jiggler, self).optionUI()

    def showUI(self):
        """Initializes and displays the full master control UI panel."""
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() in ["TheJigglerUI", "TheJigglerMiniUI"]:
                widget.close()
                widget.deleteLater()

        ui = TheJigglerWindow()
        ui.show()
        return ui

    def drawMenuBar(self, parentMenu):
        return None

# =====================================================================
# HIERARCHICAL BOUNDARY CHAIN PARSING ENGINE
# =====================================================================
def extract_hierarchical_chains(nodes):
    """
    Analyzes selected nodes to establish structural boundary rules. Finds the
    lowest selected tip elements and climbs up to the highest selected ancestor,
    automatically collecting all valid intermediate controls/joints along the
    path, even if they were skipped in the user's initial selection.
    """
    if not nodes:
        return []

    def is_valid_control(node_path):
        """Returns True if the node is a joint or has a shape node (control curve/locator)."""
        if not cmds.objExists(node_path):
            return False
        has_shape = bool(cmds.listRelatives(node_path, shapes=True))
        is_joint = cmds.nodeType(node_path) == "joint"
        return has_shape or is_joint

    # Resolve absolute long names to guarantee unique matching across deep hierarchies
    long_nodes = cmds.ls(nodes, long=True)

    # Filter selection down to valid controls/joints to establish our boundaries
    selected_valid = [n for n in long_nodes if is_valid_control(n)]
    if not selected_valid:
        return []

    selected_set = set(selected_valid)

    # Identify the true 'tips' of the current selection.
    tips = []
    for node in selected_valid:
        descendants = cmds.listRelatives(node, allDescendents=True, fullPath=True) or []
        if not any(d in selected_set for d in descendants):
            tips.append(node)

    chains = []
    for tip in tips:
        current_chain = [tip]
        temp_in_betweens = []

        curr = tip
        parent = cmds.listRelatives(curr, parent=True, fullPath=True)

        # Climb the hierarchy towards the scene root
        while parent:
            p_long = parent[0]
            p_valid = is_valid_control(p_long)
            p_selected = p_long in selected_set

            if p_valid:
                temp_in_betweens.append(p_long)

            if p_selected:
                current_chain.extend(temp_in_betweens)
                temp_in_betweens = []

            parent = cmds.listRelatives(p_long, parent=True, fullPath=True)

        current_chain.reverse()
        chains.append(current_chain)

    return chains


# =====================================================================
# META DATA ATTRIBUTE HELPER FUNCTIONS
# =====================================================================
def WRITE_METADATA(node, attr_name, value):
    """Safely adds and records persistent metadata variables directly to Maya nodes."""
    if not cmds.objExists(f"{node}.{attr_name}"):
        if isinstance(value, float):
            cmds.addAttr(node, longName=attr_name, attributeType='double', keyable=True)
        elif isinstance(value, bool):
            cmds.addAttr(node, longName=attr_name, attributeType='bool', keyable=True)
        elif isinstance(value, str):
            cmds.addAttr(node, longName=attr_name, dataType='string')

    if isinstance(value, str):
        cmds.setAttr(f"{node}.{attr_name}", value, type="string")
    else:
        cmds.setAttr(f"{node}.{attr_name}", value)


def READ_METADATA(node, attr_name, default_value):
    """Queries recorded simulation configuration metadata parameters from a node."""
    if cmds.objExists(f"{node}.{attr_name}"):
        return cmds.getAttr(f"{node}.{attr_name}")
    return default_value


# =====================================================================
# CORE HIGH-PERFORMANCE PHYSICS SIMULATION ENGINE
# =====================================================================
def calculate_spring_simulation(target_ctrl, baker_node, result_node, stiffness, damping, trans_drag, time_offset, loop,
                                active_axes, unlock_root, is_root, lever_arm_vector):
    """
    Pure math execution block. Evaluates MFnAnimCurve memory vectors directly
    and updates result keys instantly without graph rebuilds or baking overhead.
    """
    start_frame = int(cmds.playbackOptions(q=True, min=True))
    end_frame = int(cmds.playbackOptions(q=True, max=True))
    duration = end_frame - start_frame

    sim_start = start_frame
    key_start = start_frame

    if loop:
        sim_start = start_frame - (duration * 3)

    cmds.cutKey(result_node, cl=True, at=['rx', 'ry', 'rz'])

    if loop:
        baker_curves = cmds.listConnections(baker_node, type="animCurve")
        if baker_curves:
            for curve in baker_curves:
                # 4 = Cycle with Offset (cycleRelative) -> Crucial for seamless translation looping
                cmds.setAttr(f"{curve}.preInfinity", 4)
                cmds.setAttr(f"{curve}.postInfinity", 4)

    curve_fns = {}
    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
        curves = cmds.listConnections(f"{baker_node}.{attr}", type="animCurve")
        if curves:
            sel_list = om2.MSelectionList()
            sel_list.add(curves[0])
            curve_fns[attr] = oma2.MFnAnimCurve(sel_list.getDependNode(0))
        else:
            curve_fns[attr] = None

    angular_velocity = om2.MVector(0, 0, 0)
    current_q = om2.MQuaternion()
    prev_euler = om2.MEulerRotation()

    prev_pos = om2.MVector(0, 0, 0)
    prev_vel = om2.MVector(0, 0, 0)

    for frame in range(sim_start, end_frame + 1):
        eval_time = frame - time_offset
        m_time = om2.MTime(eval_time, om.MTime.uiUnit())

        if curve_fns['tx'] and curve_fns['ty'] and curve_fns['tz']:
            tx = curve_fns['tx'].evaluate(m_time)
            ty = curve_fns['ty'].evaluate(m_time)
            tz = curve_fns['tz'].evaluate(m_time)
            current_pos = om2.MVector(tx, ty, tz)
        else:
            tx = cmds.getAttr(f"{baker_node}.tx", time=eval_time)
            ty = cmds.getAttr(f"{baker_node}.ty", time=eval_time)
            tz = cmds.getAttr(f"{baker_node}.tz", time=eval_time)
            current_pos = om2.MVector(tx, ty, tz)

        if curve_fns['rx'] and curve_fns['ry'] and curve_fns['rz']:
            rx_rad = curve_fns['rx'].evaluate(m_time)
            ry_rad = curve_fns['ry'].evaluate(m_time)
            rz_rad = curve_fns['rz'].evaluate(m_time)
            euler = om2.MEulerRotation(rx_rad, ry_rad, rz_rad)
        else:
            rx = cmds.getAttr(f"{baker_node}.rx", time=eval_time)
            ry = cmds.getAttr(f"{baker_node}.ry", time=eval_time)
            rz = cmds.getAttr(f"{baker_node}.rz", time=eval_time)
            euler = om2.MEulerRotation([math.radians(x) for x in (rx, ry, rz)])

        target_q = euler.asQuaternion()

        if frame == sim_start:
            prev_euler = euler
            current_q = target_q
            prev_pos = current_pos
            prev_vel = om2.MVector(0, 0, 0)

            if frame >= key_start:
                cmds.setKeyframe(result_node, at='rx', t=frame, v=math.degrees(euler.x))
                cmds.setKeyframe(result_node, at='ry', t=frame, v=math.degrees(euler.y))
                cmds.setKeyframe(result_node, at='rz', t=frame, v=math.degrees(euler.z))
            continue

        velocity = current_pos - prev_pos
        acceleration = velocity - prev_vel

        prev_pos = current_pos
        prev_vel = velocity

        UNIT_SCALER = 0.01
        inertial_force_world = -acceleration * -(trans_drag * UNIT_SCALER)
        inertial_force_local = inertial_force_world.rotateBy(current_q.inverse())

        local_torque = inertial_force_local ^ lever_arm_vector

        q_local_diff = current_q.inverse() * target_q
        local_euler = q_local_diff.asEulerRotation()

        eval_axes = ['rx', 'ry', 'rz'] if (unlock_root and is_root) else active_axes

        disp_local = om2.MVector(
            local_euler.x if 'rx' in eval_axes else 0.0,
            local_euler.y if 'ry' in eval_axes else 0.0,
            local_euler.z if 'rz' in eval_axes else 0.0
        )

        force = (disp_local * stiffness) - (angular_velocity * damping)
        force += local_torque

        # --- MATHEMATICAL SAFETY REGULATOR (FEEDBACK LOOP CATCHER) ---
        # 1. Clip extreme instantaneous force pops to prevent exponential overshoot explosion
        force_len = force.length()
        if force_len > 2.0:
            force = (force / force_len) * 2.0

        angular_velocity += force

        # 2. Hard velocity governor. Caps secondary jiggle rotation speed to 90 degrees max per frame.
        # This breaks divergence loops at the tips of low-stiffness chains immediately.
        vel_len = angular_velocity.length()
        if vel_len > 1.5708:
            angular_velocity = (angular_velocity / vel_len) * 1.5708
        # -------------------------------------------------------------

        update_euler = om2.MEulerRotation(
            angular_velocity.x if 'rx' in eval_axes else local_euler.x,
            angular_velocity.y if 'ry' in eval_axes else local_euler.y,
            angular_velocity.z if 'rz' in eval_axes else local_euler.z
        )

        current_q = current_q * update_euler.asQuaternion()
        out_euler = current_q.asEulerRotation()

        out_x = out_euler.x - round((out_euler.x - prev_euler.x) / (2.0 * math.pi)) * (2.0 * math.pi)
        out_y = out_euler.y - round((out_euler.y - prev_euler.y) / (2.0 * math.pi)) * (2.0 * math.pi)
        out_z = out_euler.z - round((out_euler.z - prev_euler.z) / (2.0 * math.pi)) * (2.0 * math.pi)
        out_euler = om2.MEulerRotation(out_x, out_y, out_z)

        prev_euler = out_euler

        if frame >= key_start:
            cmds.setKeyframe(result_node, at='rx', t=frame, v=math.degrees(out_euler.x))
            cmds.setKeyframe(result_node, at='ry', t=frame, v=math.degrees(out_euler.y))
            cmds.setKeyframe(result_node, at='rz', t=frame, v=math.degrees(out_euler.z))


def apply_rotation_spring(target_ctrls=list(), stiffness=0.15, damping=0.2, trans_drag=1.0, time_offset=0.0, loop=False,
                          chain=False, stiffness_end=None, damping_end=None, trans_drag_end=None, time_offset_end=None,
                          limit_axes=['rx', 'ry', 'rz'], unlock_root=True, custom_configs=None, skip_bake=False):
    """
    Initial configuration constructor. Uses structural ancestry chains to organize
    locators, performs optimized concurrent batch baking, and applies simulation.
    """
    parsed_chains = extract_hierarchical_chains(target_ctrls)
    if not parsed_chains:
        return []

    limit_axes = [ax.lower() for ax in limit_axes]
    start_frame = int(cmds.playbackOptions(q=True, min=True))
    end_frame = int(cmds.playbackOptions(q=True, max=True))

    created_results = []
    temp_bakers = dict()
    temp_constraints = dict()

    all_unique_controls = []
    for ch in parsed_chains:
        for ctrl in ch:
            if ctrl not in all_unique_controls:
                all_unique_controls.append(ctrl)

    # Pass 1: Setup temporary tracking assets for all structural items
    for target_ctrl in all_unique_controls:
        clean_name = target_ctrl.split("|")[-1].split(":")[-1]
        if ":" in target_ctrl:
            namespace = target_ctrl.split("|")[-1].rsplit(":", 1)[0]
            baker_node = f"{namespace}:{clean_name}_bakedTemp"
        else:
            baker_node = f"{clean_name}_bakedTemp"

        if not cmds.objExists(baker_node):
            baker_node = cmds.spaceLocator(name=baker_node)[0]
            cmds.setAttr(f"{baker_node}.visibility", False)

        cmds.matchTransform(baker_node, target_ctrl, pos=True, rot=True)

        if not skip_bake:
            old_constraints = cmds.listConnections(baker_node, type="parentConstraint")
            if old_constraints:
                cmds.delete(old_constraints)

            constraint = cmds.parentConstraint(target_ctrl, baker_node, mo=False)[0]
            temp_constraints[target_ctrl] = constraint

        temp_bakers[target_ctrl] = baker_node

    if temp_bakers and not skip_bake:
        cmds.bakeResults(list(temp_bakers.values()), t=(start_frame, end_frame), simulation=True)
        cmds.delete(list(temp_constraints.values()))

    # Pass 2: Process configuration profiles and track metadata structures
    for ch in parsed_chains:
        for i, target_ctrl in enumerate(ch):
            is_root = (i == 0)
            clean_name = target_ctrl.split("|")[-1].split(":")[-1]

            if custom_configs and target_ctrl in custom_configs:
                cfg = custom_configs[target_ctrl]
                current_k = cfg.get("stiffness", stiffness)
                current_c = cfg.get("damping", damping)
                current_drag = cfg.get("trans_drag", trans_drag)
                current_offset = cfg.get("offset", time_offset)
                loop_state = cfg.get("loop", loop)
                unlock_root_state = cfg.get("unlock_root", unlock_root)
                is_root = cfg.get("is_root", is_root)
                eval_axes = cfg.get("axes", limit_axes)
            else:
                loop_state = loop
                unlock_root_state = unlock_root
                eval_axes = limit_axes
                current_k = stiffness
                current_c = damping
                current_drag = trans_drag
                current_offset = time_offset

                if chain and len(ch) > 1:
                    k_end = stiffness * 0.3 if stiffness_end is None else stiffness_end
                    c_end = damping * 0.5 if damping_end is None else damping_end
                    drag_end = trans_drag * 0.5 if trans_drag_end is None else trans_drag_end
                    offset_end = time_offset + 2.0 if time_offset_end is None else time_offset_end

                    alpha = float(i) / float(len(ch) - 1)
                    current_k = stiffness + (alpha * (k_end - stiffness))
                    current_c = damping + (alpha * (c_end - damping))
                    current_drag = trans_drag + (alpha * (drag_end - trans_drag))
                    current_offset = time_offset + (alpha * (offset_end - time_offset))

            if ":" in target_ctrl:
                namespace = target_ctrl.split("|")[-1].rsplit(":", 1)[0]
                baker_node = f"{namespace}:{clean_name}_bakedTemp"
                result_node = f"{namespace}:{clean_name}_springResult"
            else:
                baker_node = f"{clean_name}_bakedTemp"
                result_node = f"{clean_name}_springResult"

            lever_arm = om2.MVector(1.0, 0.0, 0.0)
            if len(ch) > 1:
                neighbor_ctrl = ch[i + 1] if i < len(ch) - 1 else ch[i - 1]

                pos_curr = cmds.xform(target_ctrl, q=True, ws=True, t=True)
                pos_neigh = cmds.xform(neighbor_ctrl, q=True, ws=True, t=True)

                if i < len(ch) - 1:
                    world_vec = om2.MVector(pos_neigh[0] - pos_curr[0], pos_neigh[1] - pos_curr[1],
                                           pos_neigh[2] - pos_curr[2])
                else:
                    world_vec = om2.MVector(pos_curr[0] - pos_neigh[0], pos_curr[1] - pos_neigh[1],
                                           pos_curr[2] - pos_neigh[2])

                rot_ws = cmds.xform(target_ctrl, q=True, ws=True, ro=True)
                euler_ws = om2.MEulerRotation([math.radians(x) for x in rot_ws])
                q_ws = euler_ws.asQuaternion()

                lever_arm = world_vec.rotateBy(q_ws.inverse())
                if lever_arm.length() > 0.001:
                    lever_arm.normalize()

            if not cmds.objExists(result_node):
                result_node = cmds.duplicate(baker_node, name=result_node)[0]
                cmds.setAttr(f"{result_node}.visibility", True)
                cmds.orientConstraint(result_node, target_ctrl, mo=False)

            WRITE_METADATA(result_node, "spring_source_ctrl", target_ctrl)
            WRITE_METADATA(result_node, "spring_baker_node", baker_node)
            WRITE_METADATA(result_node, "spring_stiffness", float(current_k))
            WRITE_METADATA(result_node, "spring_damping", float(current_c))
            WRITE_METADATA(result_node, "spring_trans_drag", float(current_drag))
            WRITE_METADATA(result_node, "spring_offset", float(current_offset))
            WRITE_METADATA(result_node, "spring_loop", bool(loop_state))
            WRITE_METADATA(result_node, "spring_unlock_root", bool(unlock_root_state))
            WRITE_METADATA(result_node, "spring_is_root", bool(is_root))
            WRITE_METADATA(result_node, "spring_axes_config", ",".join(eval_axes))
            WRITE_METADATA(result_node, "spring_lever_arm", f"{lever_arm.x},{lever_arm.y},{lever_arm.z}")

            if not skip_bake:
                calculate_spring_simulation(target_ctrl, baker_node, result_node, current_k, current_c, current_drag,
                                            current_offset,
                                            loop_state, eval_axes, unlock_root_state, is_root, lever_arm)
            else:
                cmds.cutKey(result_node, cl=True, at=['rx', 'ry', 'rz'])

            created_results.append(result_node)

    cmds.currentTime(start_frame)
    return created_results


# =====================================================================
# NON-DESTRUCTIVE ANIMATION LAYER BAKING ENGINE
# =====================================================================
def bake_simulation_to_layer(target_ctrls=None):
    """
    Extracts positional values generated by active solvers, registers them onto a
    clean animation layer, and mutes solver networks to isolate the raw curves.
    """
    if not target_ctrls:
        target_ctrls = cmds.ls(os=True, long=True)
    if not target_ctrls:
        cmds.warning("No active target rig elements selected to receive baking sequences.")
        return

    valid_bakes = []
    for ctrl in target_ctrls:
        clean_name = ctrl.split("|")[-1].split(":")[-1]
        res_node = f"{ctrl.rsplit(':', 1)[0]}:{clean_name}_springResult" if ":" in ctrl else f"{clean_name}_springResult"

        if cmds.objExists(res_node):
            valid_bakes.append((ctrl, res_node))

    if not valid_bakes:
        cmds.warning("No active solver structures matching the selected nodes found.")
        return

    start_frame = int(cmds.playbackOptions(q=True, min=True))
    end_frame = int(cmds.playbackOptions(q=True, max=True))

    layer_name = "The_Jiggler_Bake_Layer"
    if not cmds.objExists(layer_name):
        base_layer = cmds.animLayer(query=True, root=True)
        if not base_layer:
            layer_name = cmds.animLayer(layer_name)
        else:
            layer_name = cmds.animLayer(layer_name, parent=base_layer)

    ctrls_to_bake = [item[0] for item in valid_bakes]

    cmds.select(ctrls_to_bake, r=True)
    cmds.animLayer(layer_name, edit=True, appendSelected=True)

    # Commit calculation channels directly into the target animation layer context
    cmds.bakeResults(
        ctrls_to_bake,
        t=(start_frame, end_frame),
        at=['rx', 'ry', 'rz'],
        simulation=True,
        destinationLayer=layer_name
    )

    # Use Blocked State (2) to safely isolate constraint network cleanly without errors
    muted_count = 0
    for ctrl, res_node in valid_bakes:
        connections = cmds.listConnections(ctrl, type="orientConstraint", source=False, destination=True) or []
        for c in set(connections):
            targets = cmds.orientConstraint(c, query=True, targetList=True) or []
            if res_node in targets:
                cmds.setAttr(f"{c}.nodeState", 2)  # Native Blocked State (Avoids warning 1)
                muted_count += 1

    print(f"Bake Complete: {len(ctrls_to_bake)} elements layered non-destructively to '{layer_name}'.")


# =====================================================================
# PATH MANAGEMENT HELPER
# =====================================================================
def get_presets_path_context():
    """Returns absolute directory paths to handle multi-environment distribution."""
    if '__file__' in globals():
        base_dir = Jiggler().presetDir
    else:
        base_dir = os.path.join(cmds.internalVar(userScriptDir=True), "jiggle_presets")

    return base_dir, os.path.join(base_dir, "spring_presets.json")


# =====================================================================
# INTERFACE ENGINE - MASTER CONTROL DECK
# =====================================================================
def get_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QWidget) if ptr else None


class TheJigglerWindow(QDialog):
    def __init__(self, parent=get_maya_window()):
        super().__init__(parent)
        self.setWindowTitle("The Jiggler - Master Panel")
        self.setObjectName("TheJigglerUI")
        self.resize(900, 725)

        self._block_metadata_write = False
        self.presets_dir, self.presets_file_path = get_presets_path_context()

        self.init_ui()
        self.hook_live_metadata_signals()
        self.refresh_tracked_list()
        self._populate_presets_combo()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        # Top Bar Utility Utility Switch
        top_utility_layout = QHBoxLayout()
        top_utility_layout.addStretch()
        self.btn_switch_to_mini = QPushButton("Switch to Mini HUD View")
        self.btn_switch_to_mini.setStyleSheet("background-color: #444444; font-weight: bold; padding: 4px 12px;")
        self.btn_switch_to_mini.clicked.connect(self._toggle_to_mini_view)
        top_utility_layout.addWidget(self.btn_switch_to_mini)
        main_layout.addLayout(top_utility_layout)

        workspace_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(workspace_splitter, 1)

        # LEFT PANEL
        left_container = QWidget()
        left_panel = QVBoxLayout(left_container)
        left_panel.setContentsMargins(0, 0, 4, 0)
        left_panel.setSpacing(8)

        list_label = QLabel("Managed Simulation Objects:")
        list_label.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        left_panel.addWidget(list_label)

        self.tracked_list_widget = QListWidget()
        self.tracked_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tracked_list_widget.itemSelectionChanged.connect(self._on_list_selection_changed)
        left_panel.addWidget(self.tracked_list_widget)

        json_btn_layout = QHBoxLayout()
        self.btn_import_json = QPushButton("Import Setup Profile")
        self.btn_export_json = QPushButton("Export Setup Profile")
        self.btn_import_json.clicked.connect(self._import_from_json)
        self.btn_export_json.clicked.connect(self._export_to_json)
        json_btn_layout.addWidget(self.btn_import_json)
        json_btn_layout.addWidget(self.btn_export_json)
        left_panel.addLayout(json_btn_layout)

        self.btn_refresh = QPushButton("Scan Scene for Active Dynamics")
        self.btn_refresh.clicked.connect(self.refresh_tracked_list)
        left_panel.addWidget(self.btn_refresh)

        workspace_splitter.addWidget(left_container)

        # RIGHT PANEL
        right_container = QWidget()
        right_panel = QVBoxLayout(right_container)
        right_panel.setContentsMargins(4, 0, 0, 0)
        right_panel.setSpacing(10)

        preset_group = QGroupBox("Settings Preset Library (Local jiggle_presets subfolder)")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setSpacing(6)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(160)

        self.btn_save_preset = QPushButton("Save New")
        self.btn_remove_preset = QPushButton("Delete")
        self.btn_load_preset = QPushButton("Load Preset")

        self.btn_save_preset.clicked.connect(self._execute_save_preset)
        self.btn_remove_preset.clicked.connect(self._execute_remove_preset)
        self.btn_load_preset.clicked.connect(self._execute_apply_preset)

        preset_layout.addWidget(QLabel("Preset:"))
        preset_layout.addWidget(self.preset_combo, 1)
        preset_layout.addWidget(self.btn_save_preset)
        preset_layout.addWidget(self.btn_remove_preset)
        preset_layout.addWidget(self.btn_load_preset)
        right_panel.addWidget(preset_group)

        base_group = QGroupBox("Dynamic Simulation Parameters (Root Base Defaults)")
        base_grid = QGridLayout(base_group)
        self.stiffness_spin, self.stiffness_slider = self.add_float_row(base_grid, "Stiffness:", 0, 0.4, 0.01, 1.0)
        self.damping_spin, self.damping_slider = self.add_float_row(base_grid, "Damping:", 1, 0.25, 0.01, 1.0)
        self.trans_drag_spin, self.trans_drag_slider = self.add_float_row(base_grid, "Translation Drag:", 2, 0.0, -2.0,
                                                                          2.0)
        self.offset_spin, self.offset_slider = self.add_float_row(base_grid, "Time Delay Offset:", 3, 0.0, -10.0, 10.0)
        right_panel.addWidget(base_group)

        chain_group = QGroupBox("Chain Taper Mechanics")
        chain_layout = QVBoxLayout(chain_group)
        self.chain_toggle = QCheckBox("Taper Properties across Chains (Anatomical Root -> Tip)")
        chain_layout.addWidget(self.chain_toggle)

        self.taper_container = QWidget()
        taper_grid = QGridLayout(self.taper_container)
        taper_grid.setContentsMargins(15, 0, 0, 0)

        self.stiffness_end_spin, self.stiffness_end_slider = self.add_float_row(taper_grid, "Stiffness (Tip):", 0, 0.15,
                                                                                0.01, 1.0)
        self.damping_end_spin, self.damping_end_slider = self.add_float_row(taper_grid, "Damping (Tip):", 1, 0.10, 0.01,
                                                                            1.0)
        self.trans_drag_end_spin, self.trans_drag_end_slider = self.add_float_row(taper_grid, "Translation Drag (Tip):",
                                                                                  2, 0.2, -2.0, 2.0)
        self.offset_end_spin, self.offset_end_slider = self.add_float_row(taper_grid, "Time Delay Offset (Tip):", 3,
                                                                          2.0, -10.0, 10.0)

        self.taper_container.setEnabled(False)
        chain_layout.addWidget(self.taper_container)
        self.chain_toggle.toggled.connect(self.taper_container.setEnabled)

        self.unlock_root_toggle = QCheckBox("Unlock Root Dynamics (Forces 3-axis on base node)")
        self.unlock_root_toggle.setChecked(True)
        chain_layout.addWidget(self.unlock_root_toggle)
        right_panel.addWidget(chain_group)

        axis_group = QGroupBox("Evaluation Constraints (Local Vector Space)")
        axis_layout = QHBoxLayout(axis_group)
        self.chk_x = QCheckBox("X Axis")
        self.chk_y = QCheckBox("Y Axis")
        self.chk_z = QCheckBox("Z Axis")
        self.chk_x.setChecked(True)
        self.chk_y.setChecked(True)
        self.chk_z.setChecked(True)
        axis_layout.addWidget(self.chk_x)
        axis_layout.addWidget(self.chk_y)
        axis_layout.addWidget(self.chk_z)
        right_panel.addWidget(axis_group)

        env_group = QGroupBox("Execution & Cycle Strategy")
        env_layout = QVBoxLayout(env_group)
        self.loop_toggle = QCheckBox("Calculate Seamless Cycles (3x Settling Phase)")
        self.loop_toggle.setChecked(True)

        self.skip_bake_toggle = QCheckBox("Skip Initial Bake (Instant Setup Mode)")
        self.skip_bake_toggle.setChecked(False)

        env_layout.addWidget(self.loop_toggle)
        env_layout.addWidget(self.skip_bake_toggle)
        right_panel.addWidget(env_group)

        right_panel.addStretch()

        action_grid = QGridLayout()

        self.btn_add_new = QPushButton("Add New Sim from Selection")
        self.btn_add_new.setFixedHeight(34)
        self.btn_add_new.setStyleSheet("background-color: #3d6e4d; font-weight: bold; color: white;")
        self.btn_add_new.clicked.connect(self._execute_add_new)

        self.btn_apply_ui_taper = QPushButton("Apply UI / Taper to Selected")
        self.btn_apply_ui_taper.setFixedHeight(34)
        self.btn_apply_ui_taper.setStyleSheet("background-color: #5c3a70; font-weight: bold; color: white;")
        self.btn_apply_ui_taper.clicked.connect(self._execute_apply_ui_taper)

        self.btn_recalc = QPushButton("Recalculate Selected")
        self.btn_recalc.setFixedHeight(34)
        self.btn_recalc.setStyleSheet("background-color: #2b577a; font-weight: bold; color: white;")
        self.btn_recalc.clicked.connect(self._execute_recalculate)

        self.btn_deactivate = QPushButton("Deactivate Dynamics (Tweak)")
        self.btn_deactivate.setFixedHeight(34)
        self.btn_deactivate.setStyleSheet("background-color: #a64d4d; font-weight: bold; color: white;")
        self.btn_deactivate.clicked.connect(self._execute_deactivate_constraints)

        self.btn_bake_layer = QPushButton("Bake Out Simulation to Anim Layer")
        self.btn_bake_layer.setFixedHeight(38)
        self.btn_bake_layer.setStyleSheet(
            "background-color: #b36219; font-weight: bold; color: white; font-size: 11pt;")
        self.btn_bake_layer.clicked.connect(self._execute_bake_to_layer)

        self.btn_resim_all = QPushButton("Resim All Scene Objects")
        self.btn_resim_all.setFixedHeight(32)
        self.btn_resim_all.setStyleSheet("background-color: #555555; font-weight: bold; color: #e5e5e5;")
        self.btn_resim_all.clicked.connect(self._execute_resim_all)

        action_grid.addWidget(self.btn_add_new, 0, 0)
        action_grid.addWidget(self.btn_apply_ui_taper, 0, 1)
        action_grid.addWidget(self.btn_recalc, 1, 0)
        action_grid.addWidget(self.btn_deactivate, 1, 1)
        action_grid.addWidget(self.btn_bake_layer, 2, 0, 1, 2)
        action_grid.addWidget(self.btn_resim_all, 3, 0, 1, 2)
        right_panel.addLayout(action_grid)

        workspace_splitter.addWidget(right_container)
        workspace_splitter.setStretchFactor(0, 2)
        workspace_splitter.setStretchFactor(1, 3)

    def add_float_row(self, grid_layout, label_text, row_index, default_val, min_val, max_val):
        label = QLabel(label_text)
        label.setMinimumWidth(140)
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(1.0 if max_val > 10.0 else 0.1 if max_val > 1.0 else 0.01)
        spin.setValue(default_val)
        spin.setFixedWidth(65)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * 100), int(max_val * 100))
        slider.setValue(int(default_val * 100))

        spin.valueChanged.connect(lambda val: slider.setValue(int(val * 100)))
        slider.valueChanged.connect(lambda val: spin.setValue(val / 100.0))

        grid_layout.addWidget(label, row_index, 0)
        grid_layout.addWidget(slider, row_index, 1)
        grid_layout.addWidget(spin, row_index, 2)
        return spin, slider

    def hook_live_metadata_signals(self):
        self.stiffness_slider.sliderReleased.connect(
            lambda: self._write_ui_to_metadata("spring_stiffness", self.stiffness_spin.value()))
        self.stiffness_spin.editingFinished.connect(
            lambda: self._write_ui_to_metadata("spring_stiffness", self.stiffness_spin.value()))

        self.damping_slider.sliderReleased.connect(
            lambda: self._write_ui_to_metadata("spring_damping", self.damping_spin.value()))
        self.damping_spin.editingFinished.connect(
            lambda: self._write_ui_to_metadata("spring_damping", self.damping_spin.value()))

        self.trans_drag_slider.sliderReleased.connect(
            lambda: self._write_ui_to_metadata("spring_trans_drag", self.trans_drag_spin.value()))
        self.trans_drag_spin.editingFinished.connect(
            lambda: self._write_ui_to_metadata("spring_trans_drag", self.trans_drag_spin.value()))

        self.offset_slider.sliderReleased.connect(
            lambda: self._write_ui_to_metadata("spring_offset", self.offset_spin.value()))
        self.offset_spin.editingFinished.connect(
            lambda: self._write_ui_to_metadata("spring_offset", self.offset_spin.value()))

        self.loop_toggle.toggled.connect(lambda checked: self._write_ui_to_metadata("spring_loop", checked))
        self.unlock_root_toggle.toggled.connect(
            lambda checked: self._write_ui_to_metadata("spring_unlock_root", checked))
        self.chk_x.toggled.connect(self._write_axes_metadata)
        self.chk_y.toggled.connect(self._write_axes_metadata)
        self.chk_z.toggled.connect(self._write_axes_metadata)

    def _read_presets_from_disk(self):
        if os.path.exists(self.presets_file_path):
            try:
                with open(self.presets_file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                cmds.warning(f"Could not load presets file from path: {e}")
        return {}

    def _write_presets_to_disk(self, data):
        try:
            os.makedirs(self.presets_dir, exist_ok=True)
            with open(self.presets_file_path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            cmds.warning(f"Failed to save preset to disk array location. Verify permissions. Error: {e}")
            return False

    def _populate_presets_combo(self):
        self.preset_combo.clear()
        presets = self._read_presets_from_disk()
        if presets:
            self.preset_combo.addItems(sorted(presets.keys()))

    def _execute_save_preset(self):
        text, ok = QInputDialog.getText(self, "Save Profile Preset", "Preset Display Name:")
        if not ok or not text.strip():
            return

        name = text.strip()
        presets = self._read_presets_from_disk()

        presets[name] = {
            "stiffness": self.stiffness_spin.value(),
            "damping": self.damping_spin.value(),
            "trans_drag": self.trans_drag_spin.value(),
            "offset": self.offset_spin.value(),
            "loop": self.loop_toggle.isChecked(),
            "unlock_root": self.unlock_root_toggle.isChecked(),
            "chk_x": self.chk_x.isChecked(),
            "chk_y": self.chk_y.isChecked(),
            "chk_z": self.chk_z.isChecked(),
            "chain_toggle": self.chain_toggle.isChecked(),
            "stiffness_end": self.stiffness_end_spin.value(),
            "damping_end": self.damping_end_spin.value(),
            "trans_drag_end": self.trans_drag_end_spin.value(),
            "offset_end": self.offset_end_spin.value()
        }

        if self._write_presets_to_disk(presets):
            self._populate_presets_combo()
            self.preset_combo.setCurrentText(name)

    def _execute_remove_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        presets = self._read_presets_from_disk()
        if name in presets:
            del presets[name]
            self._write_presets_to_disk(presets)
            self._populate_presets_combo()

    def _execute_apply_preset(self):
        name = self.preset_combo.currentText()
        if not name:
            return
        presets = self._read_presets_from_disk()
        if name not in presets:
            return

        cfg = presets[name]
        self._block_metadata_write = True
        try:
            self.stiffness_spin.setValue(cfg.get("stiffness", 0.15))
            self.damping_spin.setValue(cfg.get("damping", 0.25))
            self.trans_drag_spin.setValue(cfg.get("trans_drag", 1.0))
            self.offset_spin.setValue(cfg.get("offset", 0.0))
            self.loop_toggle.setChecked(cfg.get("loop", True))
            self.unlock_root_toggle.setChecked(cfg.get("unlock_root", True))
            self.chk_x.setChecked(cfg.get("chk_x", True))
            self.chk_y.setChecked(cfg.get("chk_y", True))
            self.chk_z.setChecked(cfg.get("chk_z", True))
            self.chain_toggle.setChecked(cfg.get("chain_toggle", False))
            self.stiffness_end_spin.setValue(cfg.get("stiffness_end", 0.03))
            self.damping_end_spin.setValue(cfg.get("damping_end", 0.10))
            self.trans_drag_end_spin.setValue(cfg.get("trans_drag_end", 0.2))
            self.offset_end_spin.setValue(cfg.get("offset_end", 2.0))
        finally:
            self._block_metadata_write = False

    def _get_orient_constraint(self, res_node):
        target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
        if not target_ctrl or not cmds.objExists(target_ctrl):
            return None
        connections = cmds.listConnections(f"{target_ctrl}", type="orientConstraint", source=False, destination=True)
        if connections:
            for c in set(connections):
                targets = cmds.orientConstraint(c, q=True, targetList=True)
                if targets and res_node in targets:
                    return c
        return None

    def _execute_deactivate_constraints(self):
        """
        Deactivates live constraints cleanly using Blocked State (2). Also queries
        the driven transform nodes for blendParent channels, breaking active locks
        and grounding them to 0.0 so animators can immediately tweak keys.
        """
        selected_items = self.tracked_list_widget.selectedItems()
        nodes = [item.data(Qt.UserRole) for item in selected_items] if selected_items else cmds.ls(
            ["*_springResult", "*:*_springResult"], type="transform")

        if not nodes:
            cmds.warning("No dynamic simulation objects found to deactivate.")
            return

        count = 0
        for res_node in nodes:
            constraint = self._get_orient_constraint(res_node)
            if constraint:
                cmds.setAttr(f"{constraint}.nodeState", 2)  # Use Blocked State (2)
                count += 1

            # Ground and isolate blendParent parameters to allow non-destructive tweaks
            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            if target_ctrl and cmds.objExists(target_ctrl):
                blend_attrs = cmds.listAttr(target_ctrl, string="blendParent*") or []
                blend_attrs.extend(cmds.listAttr(target_ctrl, string="blendOrient*") or [])
                for attr in blend_attrs:
                    attr_path = f"{target_ctrl}.{attr}"

                    # Break incoming animation layer / driven key connections to weight attribute
                    incoming_plugs = cmds.listConnections(attr_path, plugs=True, source=True, destination=False) or []
                    for src_plug in incoming_plugs:
                        cmds.disconnectAttr(src_plug, attr_path)

                    # Ground the blend weight completely to hand direct control back to manual curves
                    try:
                        cmds.setAttr(attr_path, 0.0)
                    except Exception as e:
                        print(f"Skipped weight force layout initialization on {attr_path}: {e}")

        print(f"Deactivation Sequence Complete: Blocked {count} active dynamic constraints.")

    def _execute_activate_constraints(self):
        """
        Deactivates live constraints cleanly using Blocked State (2). Also queries
        the driven transform nodes for blendParent channels, breaking active locks
        and grounding them to 0.0 so animators can immediately tweak keys.
        """
        selected_items = self.tracked_list_widget.selectedItems()
        nodes = [item.data(Qt.UserRole) for item in selected_items] if selected_items else cmds.ls(
            ["*_springResult", "*:*_springResult"], type="transform")

        if not nodes:
            cmds.warning("No dynamic simulation objects found to activate.")
            return

        count = 0
        for res_node in nodes:
            constraint = self._get_orient_constraint(res_node)
            if constraint:
                cmds.setAttr(f"{constraint}.nodeState", 0)  # Use Blocked State (2)
                count += 1

            # Ground and isolate blendParent parameters to allow non-destructive tweaks
            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            if target_ctrl and cmds.objExists(target_ctrl):
                blend_attrs = cmds.listAttr(target_ctrl, string="blendParent*") or []
                blend_attrs.extend(cmds.listAttr(target_ctrl, string="blendOrient*") or [])
                for attr in blend_attrs:
                    attr_path = f"{target_ctrl}.{attr}"

                    # Break incoming animation layer / driven key connections to weight attribute
                    incoming_plugs = cmds.listConnections(attr_path, plugs=True, source=True, destination=False) or []
                    for src_plug in incoming_plugs:
                        cmds.disconnectAttr(src_plug, attr_path)

                    # Ground the blend weight completely to hand direct control back to manual curves
                    try:
                        cmds.setAttr(attr_path, 1.0)
                    except Exception as e:
                        print(f"Skipped weight force layout initialization on {attr_path}: {e}")

        print(f"Activation Sequence Complete: Enabled {count} active dynamic constraints.")

    def _execute_bake_to_layer(self):
        selected_items = self.tracked_list_widget.selectedItems()
        if selected_items:
            ctrls = []
            for item in selected_items:
                res_node = item.data(Qt.UserRole)
                source = READ_METADATA(res_node, "spring_source_ctrl", "")
                if source: ctrls.append(source)
        else:
            ctrls = cmds.ls(os=True, long=True)

        bake_simulation_to_layer(ctrls)

    def refresh_tracked_list(self):
        self.tracked_list_widget.clear()
        all_results = cmds.ls(["*_springResult", "*:*_springResult"], type="transform")

        for res in sorted(all_results):
            source = READ_METADATA(res, "spring_source_ctrl", "")
            if source:
                item = QListWidgetItem(f"{source.split('|')[-1]} -> [{res}]")
                item.setData(Qt.UserRole, res)
                self.tracked_list_widget.addItem(item)

    def _on_list_selection_changed(self):
        selected_items = self.tracked_list_widget.selectedItems()
        if not selected_items:
            return

        res_node = selected_items[-1].data(Qt.UserRole)

        if cmds.objExists(res_node):
            self._block_metadata_write = True
            try:
                self.stiffness_spin.setValue(READ_METADATA(res_node, "spring_stiffness", 0.4))
                self.damping_spin.setValue(READ_METADATA(res_node, "spring_damping", 0.25))
                self.trans_drag_spin.setValue(READ_METADATA(res_node, "spring_trans_drag", 0.0))
                self.offset_spin.setValue(READ_METADATA(res_node, "spring_offset", 0.0))
                self.loop_toggle.setChecked(READ_METADATA(res_node, "spring_loop", True))
                self.unlock_root_toggle.setChecked(READ_METADATA(res_node, "spring_unlock_root", True))

                axes_str = READ_METADATA(res_node, "spring_axes_config", "rx,ry,rz")
                self.chk_x.setChecked('rx' in axes_str)
                self.chk_y.setChecked('ry' in axes_str)
                self.chk_z.setChecked('rz' in axes_str)
            finally:
                self._block_metadata_write = False

    def _write_ui_to_metadata(self, attr_name, value):
        if self._block_metadata_write:
            return
        selected_items = self.tracked_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            res_node = item.data(Qt.UserRole)
            if cmds.objExists(res_node):
                WRITE_METADATA(res_node, attr_name, value)

    def _write_axes_metadata(self):
        if self._block_metadata_write:
            return
        selected_items = self.tracked_list_widget.selectedItems()
        if not selected_items:
            return
        axes_to_include = []
        if self.chk_x.isChecked(): axes_to_include.append('rx')
        if self.chk_y.isChecked(): axes_to_include.append('ry')
        if self.chk_z.isChecked(): axes_to_include.append('rz')
        axes_str = ",".join(axes_to_include)

        for item in selected_items:
            res_node = item.data(Qt.UserRole)
            if cmds.objExists(res_node):
                WRITE_METADATA(res_node, "spring_axes_config", axes_str)

    def _execute_add_new(self):
        sel = cmds.ls(os=True, long=True)
        if not sel:
            cmds.warning("Please select target animation control curves/objects first.")
            return

        axes_to_include = []
        if self.chk_x.isChecked(): axes_to_include.append('rx')
        if self.chk_y.isChecked(): axes_to_include.append('ry')
        if self.chk_z.isChecked(): axes_to_include.append('rz')

        apply_rotation_spring(
            target_ctrls=sel,
            stiffness=self.stiffness_spin.value(),
            damping=self.damping_spin.value(),
            trans_drag=self.trans_drag_spin.value(),
            time_offset=self.offset_spin.value(),
            loop=self.loop_toggle.isChecked(),
            chain=self.chain_toggle.isChecked(),
            stiffness_end=self.stiffness_end_spin.value(),
            damping_end=self.damping_end_spin.value(),
            trans_drag_end=self.trans_drag_end_spin.value(),
            time_offset_end=self.offset_end_spin.value(),
            limit_axes=axes_to_include,
            unlock_root=self.unlock_root_toggle.isChecked(),
            skip_bake=self.skip_bake_toggle.isChecked()
        )
        self.refresh_tracked_list()

    def _execute_apply_ui_taper(self):
        selected_items = self.tracked_list_widget.selectedItems()
        if not selected_items:
            cmds.warning("Select items from the left list panel to overwrite properties.")
            return

        res_to_ctrl = {}
        ctrl_to_res = {}
        for item in selected_items:
            res_node = item.data(Qt.UserRole)
            if cmds.objExists(res_node):
                ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
                if ctrl:
                    ctrl_long = cmds.ls(ctrl, long=True)[0]
                    res_to_ctrl[res_node] = ctrl_long
                    ctrl_to_res[ctrl_long] = res_node

        parsed_chains = extract_hierarchical_chains(list(res_to_ctrl.values()))

        axes_to_include = []
        if self.chk_x.isChecked(): axes_to_include.append('rx')
        if self.chk_y.isChecked(): axes_to_include.append('ry')
        if self.chk_z.isChecked(): axes_to_include.append('rz')
        axes_str = ",".join(axes_to_include)

        loop_state = self.loop_toggle.isChecked()
        unlock_root = self.unlock_root_toggle.isChecked()

        k_start, k_end = self.stiffness_spin.value(), self.stiffness_end_spin.value()
        c_start, c_end = self.damping_spin.value(), self.damping_end_spin.value()
        drag_start, drag_end = self.trans_drag_spin.value(), self.trans_drag_end_spin.value()
        offset_start, offset_end = self.offset_spin.value(), self.offset_end_spin.value()

        self._block_metadata_write = True
        try:
            for ch in parsed_chains:
                num_items = len(ch)
                use_taper = self.chain_toggle.isChecked() and num_items > 1

                for i, ctrl_long in enumerate(ch):
                    if ctrl_long not in ctrl_to_res:
                        continue
                    res_node = ctrl_to_res[ctrl_long]
                    target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
                    baker_node = READ_METADATA(res_node, "spring_baker_node", "")
                    is_root = (i == 0)

                    lever_str = READ_METADATA(res_node, "spring_lever_arm", "1.0,0.0,0.0")
                    lever_arm_vector = om.MVector([float(x) for x in lever_str.split(",")])

                    if use_taper:
                        alpha = float(i) / float(num_items - 1)
                        k = k_start + (alpha * (k_end - k_start))
                        c = c_start + (alpha * (c_end - c_start))
                        drag = drag_start + (alpha * (drag_end - drag_start))
                        offset = offset_start + (alpha * (offset_end - offset_start))
                    else:
                        k, c, drag, offset = k_start, c_start, drag_start, offset_start

                    WRITE_METADATA(res_node, "spring_stiffness", float(k))
                    WRITE_METADATA(res_node, "spring_damping", float(c))
                    WRITE_METADATA(res_node, "spring_trans_drag", float(drag))
                    WRITE_METADATA(res_node, "spring_offset", float(offset))
                    WRITE_METADATA(res_node, "spring_loop", bool(loop_state))
                    WRITE_METADATA(res_node, "spring_unlock_root", bool(unlock_root))
                    WRITE_METADATA(res_node, "spring_axes_config", axes_str)

                    calculate_spring_simulation(
                        target_ctrl=target_ctrl, baker_node=baker_node, result_node=res_node,
                        stiffness=k, damping=c, trans_drag=drag, time_offset=offset,
                        loop=loop_state, active_axes=axes_to_include, unlock_root=unlock_root,
                        is_root=is_root, lever_arm_vector=lever_arm_vector
                    )
        finally:
            self._block_metadata_write = False

    def _execute_recalculate(self):
        selected_items = self.tracked_list_widget.selectedItems()
        if not selected_items:
            cmds.warning("Select items from the left tracking panel list to recalculate.")
            return

        # Handle Animation Layer overrides dynamically to extract baseline animation channels safely
        layer_name = "The_Jiggler_Bake_Layer"
        layer_exists = cmds.objExists(layer_name)
        was_layer_muted = cmds.animLayer(layer_name, query=True, mute=True) if layer_exists else False

        if layer_exists:
            cmds.animLayer(layer_name, edit=True, mute=True)

        use_ui_settings = (len(selected_items) == 1)
        axes_to_include = []
        if self.chk_x.isChecked(): axes_to_include.append('rx')
        if self.chk_y.isChecked(): axes_to_include.append('ry')
        if self.chk_z.isChecked(): axes_to_include.append('rz')

        bakers_to_bake = {}
        constraints_to_restore = []

        for item in selected_items:
            res_node = item.data(Qt.UserRole)
            if not cmds.objExists(res_node): continue

            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            baker_node = READ_METADATA(res_node, "spring_baker_node", "")

            if cmds.objExists(target_ctrl) and cmds.objExists(baker_node):
                constraint = self._get_orient_constraint(res_node)
                if constraint:
                    cmds.setAttr(f"{constraint}.nodeState", 2)  # Clean Blocked State (No warning)
                    constraints_to_restore.append((constraint, res_node))

                cmds.matchTransform(baker_node, target_ctrl, pos=True, rot=True)
                old_p_const = cmds.listConnections(baker_node, type="parentConstraint")
                if old_p_const:
                    cmds.delete(old_p_const)

                p_const = cmds.parentConstraint(target_ctrl, baker_node, mo=False)[0]
                bakers_to_bake[target_ctrl] = (baker_node, p_const)

        if bakers_to_bake:
            start_frame = int(cmds.playbackOptions(q=True, min=True))
            end_frame = int(cmds.playbackOptions(q=True, max=True))
            cmds.bakeResults([v[0] for v in bakers_to_bake.values()], t=(start_frame, end_frame), simulation=True)
            cmds.delete([v[1] for v in bakers_to_bake.values()])

        for constraint, res_node in constraints_to_restore:
            cmds.setAttr(f"{constraint}.nodeState", 0)  # Re-enable constraint to live mode

        # Clear layer keyframe entries for target controls so live solvers drive them smoothly
        if layer_exists:
            for item in selected_items:
                res_node = item.data(Qt.UserRole)
                ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
                if ctrl and cmds.objExists(ctrl):
                    cmds.cutKey(ctrl, at=['rx', 'ry', 'rz'], animLayer=layer_name)
            cmds.animLayer(layer_name, edit=True, mute=was_layer_muted)

        for item in selected_items:
            res_node = item.data(Qt.UserRole)
            if not cmds.objExists(res_node): continue

            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            baker_node = READ_METADATA(res_node, "spring_baker_node", "")
            is_root = READ_METADATA(res_node, "spring_is_root", False)
            lever_str = READ_METADATA(res_node, "spring_lever_arm", "1.0,0.0,0.0")
            lever_arm_vector = om.MVector([float(x) for x in lever_str.split(",")])

            if use_ui_settings:
                k, c, drag, offset = self.stiffness_spin.value(), self.damping_spin.value(), self.trans_drag_spin.value(), self.offset_spin.value()
                loop_state, unlock_root, eval_axes = self.loop_toggle.isChecked(), self.unlock_root_toggle.isChecked(), axes_to_include

                WRITE_METADATA(res_node, "spring_stiffness", float(k))
                WRITE_METADATA(res_node, "spring_damping", float(c))
                WRITE_METADATA(res_node, "spring_trans_drag", float(drag))
                WRITE_METADATA(res_node, "spring_offset", float(offset))
                WRITE_METADATA(res_node, "spring_loop", bool(loop_state))
                WRITE_METADATA(res_node, "spring_unlock_root", bool(unlock_root))
                WRITE_METADATA(res_node, "spring_axes_config", ",".join(eval_axes))
            else:
                k = READ_METADATA(res_node, "spring_stiffness", 0.4)
                c = READ_METADATA(res_node, "spring_damping", 0.25)
                drag = READ_METADATA(res_node, "spring_trans_drag", 0.0)
                offset = READ_METADATA(res_node, "spring_offset", 0.0)
                loop_state = READ_METADATA(res_node, "spring_loop", True)
                unlock_root = READ_METADATA(res_node, "spring_unlock_root", True)
                eval_axes = READ_METADATA(res_node, "spring_axes_config", "rx,ry,rz").split(",")

            calculate_spring_simulation(target_ctrl, baker_node, result_node=res_node, stiffness=k, damping=c,
                                        trans_drag=drag, time_offset=offset, loop=loop_state, active_axes=eval_axes,
                                        unlock_root=unlock_root, is_root=is_root, lever_arm_vector=lever_arm_vector)

    def _execute_resim_all(self):
        all_results = cmds.ls(["*_springResult", "*:*_springResult"], type="transform")
        if not all_results:
            cmds.warning("No active spring simulation instances found in the current scene context.")
            return

        # Mute layered curves globally to isolate fundamental motion details cleanly
        layer_name = "The_Jiggler_Bake_Layer"
        layer_exists = cmds.objExists(layer_name)
        was_layer_muted = cmds.animLayer(layer_name, query=True, mute=True) if layer_exists else False

        if layer_exists:
            cmds.animLayer(layer_name, edit=True, mute=True)

        # deactivate any constraints just in case
        self._execute_deactivate_constraints()

        bakers_to_bake = {}
        constraints_to_restore = []

        for res_node in all_results:
            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            baker_node = READ_METADATA(res_node, "spring_baker_node", "")
            if not target_ctrl or not baker_node or not cmds.objExists(baker_node): continue

            constraint = self._get_orient_constraint(res_node)
            if constraint:
                cmds.setAttr(f"{constraint}.nodeState", 2)  # Clean Blocked State (No warning)
                constraints_to_restore.append((constraint, res_node))

            cmds.matchTransform(baker_node, target_ctrl, pos=True, rot=True)
            old_p_const = cmds.listConnections(baker_node, type="parentConstraint")
            if old_p_const:
                cmds.delete(old_p_const)

            p_const = cmds.parentConstraint(target_ctrl, baker_node, mo=False)[0]
            bakers_to_bake[target_ctrl] = (baker_node, p_const)

        if bakers_to_bake:
            start_frame = int(cmds.playbackOptions(q=True, min=True))
            end_frame = int(cmds.playbackOptions(q=True, max=True))
            cmds.bakeResults([v[0] for v in bakers_to_bake.values()], t=(start_frame, end_frame), simulation=True)
            cmds.delete([v[1] for v in bakers_to_bake.values()])

        for constraint, res_node in constraints_to_restore:
            cmds.setAttr(f"{constraint}.nodeState", 0)

        # Remove keys across the entire layered control list to restore dynamic computation behavior
        if layer_exists:
            for res_node in all_results:
                ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
                if ctrl and cmds.objExists(ctrl):
                    cmds.cutKey(ctrl, at=['rx', 'ry', 'rz'], animLayer=layer_name)
            cmds.animLayer(layer_name, edit=True, mute=was_layer_muted)

        for res_node in all_results:
            target_ctrl = READ_METADATA(res_node, "spring_source_ctrl", "")
            baker_node = READ_METADATA(res_node, "spring_baker_node", "")
            if not target_ctrl or not baker_node or not cmds.objExists(baker_node): continue

            is_root = READ_METADATA(res_node, "spring_is_root", False)
            lever_str = READ_METADATA(res_node, "spring_lever_arm", "1.0,0.0,0.0")
            lever_arm_vector = om2.MVector([float(x) for x in lever_str.split(",")])

            k = READ_METADATA(res_node, "spring_stiffness", 0.40)
            c = READ_METADATA(res_node, "spring_damping", 0.25)
            drag = READ_METADATA(res_node, "spring_trans_drag", 0.0)
            offset = READ_METADATA(res_node, "spring_offset", 0.0)
            loop_state = READ_METADATA(res_node, "spring_loop", True)
            unlock_root = READ_METADATA(res_node, "spring_unlock_root", True)
            eval_axes = READ_METADATA(res_node, "spring_axes_config", "rx,ry,rz").split(",")

            calculate_spring_simulation(target_ctrl, baker_node, result_node=res_node, stiffness=k, damping=c,
                                        trans_drag=drag, time_offset=offset, loop=loop_state, active_axes=eval_axes,
                                        unlock_root=unlock_root, is_root=is_root, lever_arm_vector=lever_arm_vector)

        self._execute_activate_constraints()

    def _export_to_json(self):
        all_results = cmds.ls(["*_springResult", "*:*_springResult"], type="transform")
        if not all_results: return

        profile_data = {}
        for res in all_results:
            source = READ_METADATA(res, "spring_source_ctrl", "")
            if not source: continue
            profile_data[source] = {
                "stiffness": READ_METADATA(res, "spring_stiffness", 0.15),
                "damping": READ_METADATA(res, "spring_damping", 0.25),
                "trans_drag": READ_METADATA(res, "spring_trans_drag", 1.0),
                "offset": READ_METADATA(res, "spring_offset", 0.0),
                "loop": READ_METADATA(res, "spring_loop", True),
                "unlock_root": READ_METADATA(res, "spring_unlock_root", True),
                "is_root": READ_METADATA(res, "spring_is_root", False),
                "axes": READ_METADATA(res, "spring_axes_config", "rx,ry,rz").split(","),
                "lever_arm": READ_METADATA(res, "spring_lever_arm", "1.0,0.0,0.0")
            }

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Profile", "", "JSON (*.json)")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(profile_data, f, indent=4)

    def _import_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON (*.json)")
        if not file_path or not os.path.exists(file_path): return

        with open(file_path, 'r') as f:
            profile_data = json.load(f)

        valid_profiles = {k: v for k, v in profile_data.items() if cmds.objExists(k)}
        if valid_profiles:
            apply_rotation_spring(target_ctrls=list(valid_profiles.keys()), custom_configs=valid_profiles)
            self.refresh_tracked_list()

    def _toggle_to_mini_view(self):
        self.close()
        show_mini_ui()


# =====================================================================
# INTERFACE ENGINE - STREAMLINED FAST EXECUTOR HUD (MINI VIEW)
# =====================================================================
class TheJigglerMiniWindow(QDialog):
    def __init__(self, parent=get_maya_window()):
        super().__init__(parent)
        self.setWindowTitle("The Jiggler - HUD")
        self.setObjectName("TheJigglerMiniUI")
        self.setFixedWidth(240)

        self.presets_dir, self.presets_file_path = get_presets_path_context()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        header_label = QLabel("Preset Quick-Bake Layer")
        header_label.setStyleSheet("font-weight: bold; color: #dddddd; font-size: 10pt;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Scroll panel framework to prevent clipping if the preset collection expands
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_container = QWidget()
        self.buttons_layout = QVBoxLayout(scroll_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(6)

        self._build_preset_macro_buttons()

        scroll_area.setWidget(scroll_container)
        layout.addWidget(scroll_area, 1)

        layout.addWidget(QFrame(frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))

        # Backdoor hook to switch back to full master options deck
        self.btn_switch_to_main = QPushButton("Open Master Deck panel...")
        self.btn_switch_to_main.setStyleSheet("background-color: #333333; font-size: 8pt; padding: 3px;")
        self.btn_switch_to_main.clicked.connect(self._toggle_to_master_view)
        layout.addWidget(self.btn_switch_to_main)

    def _read_presets_from_disk(self):
        if os.path.exists(self.presets_file_path):
            try:
                with open(self.presets_file_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _build_preset_macro_buttons(self):
        presets = self._read_presets_from_disk()

        if not presets:
            empty_lbl = QLabel("No local presets found.\nSave presets inside the\nMaster Panel first.")
            empty_lbl.setStyleSheet("color: #777777; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.buttons_layout.addWidget(empty_lbl)
            return

        for name in sorted(presets.keys()):
            btn = QPushButton(name)
            btn.setFixedHeight(38)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b505e; 
                    font-weight: bold; 
                    color: #e2e2e2; 
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #4b6678;
                }
                QPushButton:pressed {
                    background-color: #2b3a45;
                }
            """)
            # Python scoping workaround logic to bind variables correctly within generation blocks
            btn.clicked.connect(lambda checked=False, p_name=name: self._execute_macro(p_name))
            self.buttons_layout.addWidget(btn)

        self.buttons_layout.addStretch()

    def _execute_macro(self, preset_name):
        sel = cmds.ls(os=True, long=True)
        if not sel:
            cmds.warning("Please select structural target rig elements first.")
            return

        presets = self._read_presets_from_disk()
        if preset_name not in presets:
            return

        cfg = presets[preset_name]

        axes_to_include = []
        if cfg.get("chk_x", True): axes_to_include.append('rx')
        if cfg.get("chk_y", True): axes_to_include.append('ry')
        if cfg.get("chk_z", True): axes_to_include.append('rz')

        # Handle layered channels dynamically during instant hot-button recalculation
        layer_name = "The_Jiggler_Bake_Layer"
        layer_exists = cmds.objExists(layer_name)
        was_layer_muted = cmds.animLayer(layer_name, query=True, mute=True) if layer_exists else False

        if layer_exists:
            cmds.animLayer(layer_name, edit=True, mute=True)

        # 1. Spawn calculation structures and solve equations safely using Blocked state
        apply_rotation_spring(
            target_ctrls=sel,
            stiffness=cfg.get("stiffness", 0.15),
            damping=cfg.get("damping", 0.25),
            trans_drag=cfg.get("trans_drag", 1.0),
            time_offset=cfg.get("offset", 0.0),
            loop=cfg.get("loop", True),
            chain=cfg.get("chain_toggle", False),
            stiffness_end=cfg.get("stiffness_end", 0.03),
            damping_end=cfg.get("damping_end", 0.10),
            trans_drag_end=cfg.get("trans_drag_end", 0.2),
            time_offset_end=cfg.get("offset_end", 2.0),
            limit_axes=axes_to_include,
            unlock_root=cfg.get("unlock_root", True),
            skip_bake=False
        )

        if layer_exists:
            for ctrl in sel:
                cmds.cutKey(ctrl, at=['rx', 'ry', 'rz'], animLayer=layer_name)
            cmds.animLayer(layer_name, edit=True, mute=was_layer_muted)

        # 2. Immediately commit simulation non-destructively to layer and clear workspace
        bake_simulation_to_layer(sel)

    def _toggle_to_master_view(self):
        self.close()
        show_ui()


# =====================================================================
# WINDOW MANAGERS
# =====================================================================
def show_ui():
    """Initializes and displays the full master control UI panel."""
    for widget in QApplication.topLevelWidgets():
        if widget.objectName() in ["TheJigglerUI", "TheJigglerMiniUI"]:
            widget.close()
            widget.deleteLater()

    ui = TheJigglerWindow()
    ui.show()
    return ui


def show_mini_ui():
    """Initializes and displays the compact micro HUD view."""
    for widget in QApplication.topLevelWidgets():
        if widget.objectName() in ["TheJigglerUI", "TheJigglerMiniUI"]:
            widget.close()
            widget.deleteLater()

    ui = TheJigglerMiniWindow()
    ui.show()
    return ui


# Clean entry encapsulation block allowing programmatic library loads
if __name__ == '__main__':
    show_ui()

