from ast_node_define import *

class Verilog_AST:
    def __init__(self):
        self._add_root()
        self._map__name_2_varnode = {}
        self._map__treeid_2_node = {}
        self._map__name_2_varroot = {}


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


