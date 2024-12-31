from ast_node_define import *

class Verilog_AST:
    def __init__(self):
        self._add_root()
        self._map__name_2_varnode = {}
        self._map__treeid_2_node = {}
        self._map__name_2_varroot = {}
        self.ordered_subcircuit_id_head = []
        self.ordered_subcircuit_id_tail = []
        self.input_list = []
        self.register_list = []
        self.output_wire_list = []
        self.output_list = []
        self.observe_point_list = []

    def _add_root(self):
        root = Verilog_AST_Node()
        root.tag == "root"
        root._set_tree(self)
        self._root = root

    @property
    def root(self):
        return self._root

    def var_node(self,var_name:str):
        return self._map__name_2_varnode[var_name]

    def subtreeroot_node(self,idx:int):
        return self._map__treeid_2_node[idx]

    def varroot_node(self,var_name:str):
        return self._map__name_2_varroot[var_name]

    def input_append(self,node):
        self.input_list.append(node)

    def register_append(self,node):
        self.register_list.append(node)

    def observe_point_append(self,node):
        self.observe_point_list.append(node)

    def output_append(self,node):
        self.output_list.append(node)

    def output_wire_append(self,node):
        self.output_wire_list.append(node)

    def show_var_value(self):
        for varname in self._map__name_2_varnode:
            value = self._map__name_2_varnode[varname].value
            print(varname,value)

    def show_register_fault_list(self):
        for node in self.register_list:
            print(node.name, node.fault_list)
