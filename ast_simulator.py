from ast_define import *
from ast_construct import AstDuplicate
from ast_nodeclassify import *
from ast_dump import *
from utils import *
from exceptions import SimulationError
from rtl_functions import *

import argparse
import pickle
import json

class SimulatorExecute(AstNodeClassify):
    def __init__(self,ast):
        AstNodeClassify.__init__(self)

        self.ast = ast

        # duplicate ast -> get self.my_ast
        self.ast_duplicator = AstDuplicate(self.ast)
        self.ast_duplicator.duplicate()
        self.my_ast = self.ast_duplicator.my_ast

        # dump simulator sig list
        self.sig_dumper = AstDumpSimulatorSigList(self.ast)
       
        # TODO
        self.logic_value_file_dir = "../picorv32/pattern/"
        self.logic_value_file_head = "FaultFree_Signal_Value_C"
        self.logic_value_file_tail = ".txt"

    def load_ordered_varname(self) -> list:
        varname_list = []
        f = open("./sig_list/simulator_sig_dict.json","r")
        for varname in json.load(f).keys():
            varname_list.append(varname)
        f.close()
        return varname_list

    def load_logic_value_file(self,cycle,width:int=7) -> list:
        # Fetch logic value dump file at the specific clock cycle
        target_filename = self.logic_value_file_dir + self.logic_value_file_head + f"{cycle:0{width}}" + self.logic_value_file_tail
        f = open(target_filename,"r")
        logic_value_list = f.readlines()
        logic_value_list = [value.strip() for value in logic_value_list]
        f.close()
        new_logic_value_list = []

        for idx in range(len(self.varname_list)):
            new_logic_value_list.append( (self.varname_list[idx], logic_value_list[idx]) )
        return new_logic_value_list

    def load_logic_value(self,cycle,width:int=7):
        logic_value_list = self.load_logic_value_file(cycle,width)
        for varname, value in logic_value_list:
            var = self.my_ast.var_node(varname)
            var.value = value


    def execute_comb(self,node):
        self.execute_rtl(node)
        #self.execute_df(node)


    def execute_seq(self,node):
        self.execute_rtl(node)
        #self.execute_df(node)

    #------------------------------------------------------

    # RTL simulation functions
    def execute_rtl(self,node):
        if "assign" in node.tag:
            self.execute_rtl_assign(node)
        elif node.tag == "if":
            self.execute_rtl_if(node)
        elif node.tag == "case":
            self.execute_rtl_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_rtl_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def execute_rtl_assign(self,node):
        right_node = node.rv_node

        # visit
        self.compute_rtl(right_node)
        #self.propagate_df(right_node)

        # get right value result
        value = right_node.value
        #fault_list = right_node.fault_list

    def execute_rtl_if(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)

    def execute_rtl_case(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = node.ctrl_node.value
        for child in node.caseitems:
            if self.execute_rtl_caseitem(child,value):
                break

    def execute_rtl_block(self,node):
        for child in node.children:
            self.execute_rtl(child)

    def trigger_rtl_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            self.compute_rtl(cond)
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def execute_rtl_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_rtl_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute_rtl(child)
        return flag

    def compute_rtl(self,node) -> None:
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_rtl(child)

        if node.tag == "varref":
            pass
        elif node.tag == "arraysel":
            pass
            #array_node = node.children[0]
            #idx = int(node.children[1].value,2)
        elif node.tag == "sel":
            if "x" in node.children[1].value:
                result = "x" * width
            else:
                var_value = node.children[0].value
                start_bit = int(node.children[1].value,2)
                bit_width = int(node.children[2].value,2)
                if start_bit == 0:
                    result = var_value[-1-bit_width:]
                else:
                    result = var_value[-(start_bit+1)-bit_width:-(start_bit+1)]
        elif node.tag in self.op__2_port:
            result = val_2_op(node)
        elif node.tag in self.op__1_port:
            result = val_1_op(node)
        else:
            if node.tag == "cond":
                c_value = node.children[0].value
                c_value.replace("z","x")
                if c_value == "1":
                    result = node.children[1].value
                elif c_value == "0":
                    result = node.children[2].value
                else:
                    result = "x"*width
            elif node.tag == "const":
                pass
            else:
                raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",3)
        
        if result is not None:
            if len(result) == width:
                node.value = result
            else:
                raise SimulationError(f"result and width mismatch: tag = {node.tag}, result = {result}, width = {width}.",4)

    #------------------------------------------------------

    # Data Write-event fault propagation
    #
    def execute_df(self,node):
        if "assign" in node.tag:
            self.execute_df_assign(node)
        elif node.tag == "if":
            self.execute_df_if(node)
        elif node.tag == "case":
            self.execute_df_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_df_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    # Control fault propagation
    #
    def execute_seq_cf(self,node):
        if "assign" in node.tag:
            self.execute_seq_cf_assign(node)
        elif node.tag == "if":
            self.execute_seq_cf_if(node)
        elif node.tag == "case":
            self.execute_seq_cf_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_seq_cf_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    # Control fault propagation
    #
    def execute_comb_cf(self,node):
        if "assign" in node.tag:
            self.execute_comb_cf_assign(node)
        elif node.tag == "if":
            self.execute_comb_cf_if(node)
        elif node.tag == "case":
            self.execute_comb_cf_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_comb_cf_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    def get_value(self,node):
        if type(node) is str:
            return node
        else:
            return node.value
    


    def check_len(self,s:str,l:int):
        return len(s) == l

    def check_width(self,result:str,width:int):
        if not self.check_len(s,l):
            raise SimulationError("result width doesn't match the node output width.",0)

class Simulator(SimulatorExecute):
    def __init__(self,ast):
        SimulatorExecute.__init__(self,ast)
        self.dumper = AstDumpSimulatorSigList(self.ast)

    def fault_list_init(self):
        for node in self.my_ast.register_list:
            name = node.name


    def simulate_1_cyc(self):
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_head:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.execute_comb(entry_node)
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_tail:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.execute_seq(entry_node)


    def process(self):
        self.dumper.dump_sig_dict()
        self.varname_list = self.load_ordered_varname()
        self.load_logic_value(100000)
        # simulation
        self.simulate_1_cyc()


if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(Simulator.__dict__.keys()))

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)

        ast_sim = Simulator(ast)
        ast_sim.process()

