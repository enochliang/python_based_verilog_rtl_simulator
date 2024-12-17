from ast_define import *
from ast_schedule import *
from utils import *
from exceptions import SimulationError

import argparse
import pickle
import json


class ScheduledAst:
    def __init__(self,ast):
        self.ast = ast

        # start scheduling
        self.ast_scheduler = AstSchedule(self.ast)
        self.ast_scheduler.schedule()

        # get results of schduling
        self.subcircuit_num = self.ast_scheduler.subcircuit_num
        self.ordered_subcircuit_id_head = self.ast_scheduler.ordered_subcircuit_id_head
        self.ordered_subcircuit_id_tail = self.ast_scheduler.ordered_subcircuit_id_tail

        # flatten composite signals to packed registers
        self.flattener = AstArrayFlatten(self.ast)
        self.flattener.module_var_flatten()




class AstConstructBase:
    def __init__(self,ast):
        # the ready ast for new ast feature construction should be scheduled & array-flattened
        self.scheduled_ast = ScheduledAst(ast)
        self.ast = self.scheduled_ast.ast

        self.analyzer = AstAnalyzer(self.ast)

        # the new defined ast data structure
        self.my_ast = Verilog_AST()
        self.my_ast.ordered_subcircuit_id_head = self.scheduled_ast.ordered_subcircuit_id_head
        self.my_ast.ordered_subcircuit_id_tail = self.scheduled_ast.ordered_subcircuit_id_tail


class AstConstructAddVar(AstConstructBase):
    def __init__(self,ast):
        AstConstructBase.__init__(self,ast)

    def append_var_node(self):
        print("start adding <var> nodes into ast... ")
        for var in self.ast.find(".//module").getchildren():
            if var.tag == "always":
                continue
            if var.tag == "contassign":
                continue
            if var.tag == "initial":
                continue
            if var.tag == "assignalias":
                continue
            if "param" in var.attrib:
                continue
            if "localparam" in var.attrib:
                continue
            if var.tag == "topscope":
                continue
            name = var.attrib["name"]
            varrootnode = self._append_var_node(var)
            self.my_ast._map__name_2_varroot[name] = varrootnode
            self.my_ast.root.append(varrootnode)


    def _append_var_node(self,node):
        width = int(node.attrib["width"])
        name = node.attrib["name"]

        new_var_node = Verilog_AST_Var_Node(width)
        new_var_node.tag = node.tag
        new_var_node.name = name

        for child in node.getchildren():
            new_var_node.append(self._append_var_node(child))

        if new_var_node.tag == "var":
            self.my_ast._map__name_2_varnode[name] = new_var_node
            if node.attrib["sig_type"] == "register":
                self.my_ast.register_append(new_var_node)
            if "dir" in node.attrib and node.attrib["dir"] == "output":
                if node.attrib["sig_type"] == "wire":
                    self.my_ast.output_wire_append(new_var_node)
                self.my_ast.output_append(new_var_node)

        return new_var_node

class AstConstructAddTree(AstConstructAddVar):
    def __init__(self,ast):
        AstConstructAddVar.__init__(self,ast)

    def _add_ast_varref(self,node):
        name = node.attrib["name"]
        width = int(node.attrib["width"])
        ref_node = self.my_ast.varroot_node(name)
        new_node = Verilog_AST_Varref_Node(width)
        new_node.name = name
        new_node.ref_node = ref_node
        return new_node

    def _add_ast_circuit_node(self,node):
        width = int(node.attrib["width"])
        new_node = Verilog_AST_Circuit_Node(width)
        new_node.tag = node.tag
        if node.tag == "const":
            value = node.attrib["name"]
            value = self.analyzer.vnum2bin(value)
            new_node.value = value
            if node.attrib["loc"] == "e,2491,39,2491,45":
                print(f"value = {new_node.value}")


        return new_node

    def _add_ast_case(self):
        return Verilog_AST_CASE_Node()

    def _add_ast_if(self):
        return Verilog_AST_IF_Node()

    def _add_ast_caseitem(self):
        return Verilog_AST_CASEITEM_Node()

    def _add_ast_assign(self,node):
        return Verilog_AST_Assign_Node()

    def add_ast_child(self,node):
        if node.tag == "always":
            new_node = Verilog_AST_Node()
            new_node.tag = node.tag
            if "lv_name" in node.attrib:
                new_node.attrib["lv_name"] = node.attrib["lv_name"]
        elif node.tag == "varref":
            new_node = self._add_ast_varref(node)
        elif "contassign" in node.tag:
            new_node = self._add_ast_assign(node)
            if "lv_name" in node.attrib:
                new_node.attrib["lv_name"] = node.attrib["lv_name"]
        elif "assign" in node.tag:
            new_node = self._add_ast_assign(node)
            new_node
        elif "dtype_id" in node.attrib:
            new_node = self._add_ast_circuit_node(node)
        elif node.tag == "case":
            new_node = self._add_ast_case()
        elif node.tag == "if":
            new_node = self._add_ast_if()
        elif node.tag == "caseitem":
            new_node = self._add_ast_caseitem()
        else:
            new_node = Verilog_AST_Node()
            new_node.tag = node.tag

        if "loc" in node.attrib:
            new_node.attrib["loc"] = node.attrib["loc"]
        children = node.getchildren()
        for child in children:
            new_node.append(self.add_ast_child(child))

        return new_node

    def append_ast_node(self):
        for subcircuit_id in range(self.scheduled_ast.subcircuit_num):
            entry_node = self.ast.find(f".//*[@subcircuit_id='{str(subcircuit_id)}']")
            my_entry_node = self.add_ast_child(entry_node)
            self.my_ast.root.append(my_entry_node)
            self.my_ast._map__treeid_2_node[subcircuit_id] = my_entry_node

class AstConstruct(AstConstructAddTree):
    def __init__(self,ast):
        AstConstructAddTree.__init__(self,ast)

    def construct(self):
        self.append_var_node()
        self.append_ast_node()
        self.count_xml_ast_node()
        self.count_my_ast_node()

    def count_xml_ast_node(self):
        self.count_xml_var_node()
        self.count_xml_subcircuit_node()

    def count_xml_var_node(self):
        var_num = 0
        for var in self.ast.find(".//module").getchildren():
            if var.tag == "always":
                continue
            if var.tag == "contassign":
                continue
            if var.tag == "initial":
                continue
            if var.tag == "assignalias":
                continue
            if "param" in var.attrib:
                continue
            if "localparam" in var.attrib:
                continue
            if var.tag == "topscope":
                continue
            for node in var.iter():
                var_num += 1
        print(f"Total Number of <var> = {var_num}")

    def count_xml_subcircuit_node(self):
        ast_node_num = 0
        for subcircuit_id in range(self.scheduled_ast.subcircuit_num):
            subcircuit = self.ast.find(f".//*[@subcircuit_id='{str(subcircuit_id)}']")
            for node in subcircuit.iter():
                ast_node_num += 1
        print(f"Total Number of AST Nodes = {ast_node_num}")

    def count_my_ast_node(self):
        self.count_my_var_node()
        self.count_my_subcircuit_node()

    def count_my_var_node(self):
        ast_var_num = 0
        for key, node in self.my_ast._map__name_2_varroot.items():
            ast_var_num += len(self.iter_my_node(node))
        print(f"Total Number of <var> in my ast = {ast_var_num}")

    def count_my_subcircuit_node(self):
        ast_node_num = 0
        for key, node in self.my_ast._map__treeid_2_node.items():
            ast_node_num += len(self.iter_my_node(node))
        print(f"Total Number of subcircuit nodes in my ast = {ast_node_num}")

    def iter_my_node(self,node):
        node_list = []
        node_list.append(node)
        for child in node.children:
            node_list = node_list + self.iter_my_node(child)
        return node_list


class AstDuplicate(AstConstruct):
    def __init__(self,ast):
        AstConstruct.__init__(self,ast)

        # self.my_ast is ready

    def duplicate(self):
        self.construct()


