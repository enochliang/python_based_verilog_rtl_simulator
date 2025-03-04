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

class SimulatorPrepare(AstNodeClassify):
    def __init__(self,ast,logic_value_file_dir,sig_list_dir,design_dir):
        AstNodeClassify.__init__(self)

        self.ast = ast

        # duplicate ast -> get self.my_ast
        self.ast_duplicator = AstDuplicate(self.ast,design_dir)
        self.my_ast = None

        # dump ast to xml file
        self.ast_dumper = AstDump(self.ast,design_dir)


        # TODO
        self.sig_list_dir = sig_list_dir
        self.logic_value_file_dir = logic_value_file_dir
        self.logic_value_file_head = "ff_value_C"
        self.logic_value_file_tail = ".txt"

    def preprocess(self):
        self.ast_duplicator.duplicate()
        self.my_ast = self.ast_duplicator.my_ast

        #self.ast_dumper.dump()
        self.load_ordered_varname()

    def load_ordered_varname(self):
        self.varname_list = []
        f = open(self.sig_list_dir + "/pysim_sig_table.json","r")
        for varname in json.load(f).keys():
            self.varname_list.append(varname)
        f.close()

    def load_logic_value_file(self,cycle,width:int=7,output=False) -> list:
        # Fetch logic value dump file at the specific clock cycle
        target_filename = self.logic_value_file_dir + "/" + self.logic_value_file_head + f"{cycle:0{width}}" + self.logic_value_file_tail
        if output:
            print(f"reading file for current cycle: {target_filename}")
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
            # debugging
            var.cur_value = value


    def load_next_logic_value_file(self,cycle,width:int=7,output=False) -> list:
        # Fetch logic value dump file at the specific clock cycle
        target_filename = self.logic_value_file_dir + "/" + self.logic_value_file_head + f"{cycle:0{width}}" + self.logic_value_file_tail
        if output:
            print(f"reading file for next cycle: {target_filename}")
        f = open(target_filename,"r")
        logic_value_list = f.readlines()
        logic_value_list = [value.strip() for value in logic_value_list]
        f.close()
        new_logic_value_list = []

        for idx in range(len(self.varname_list)):
            new_logic_value_list.append( (self.varname_list[idx], logic_value_list[idx]) )
        return new_logic_value_list

    def load_next_logic_value(self,cycle,width:int=7):
        logic_value_list = self.load_next_logic_value_file(cycle,width)
        for varname, value in logic_value_list:
            var = self.my_ast.var_node(varname)
            var.next_value = value


    def init_fault_list(self):
        for node in self.my_ast.register_list:
            fault_name = node.name
            width = node.width
            if node.value == "x"*width:
                node.fault_list = {}
                node.cur_fault_list = {}
            else:
                node.fault_list = {(fault_name,"stay"):1.0}
                node.cur_fault_list = {(fault_name,"stay"):1.0}


if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument
    parser.add_argument("--logic_value_dir", type=str, help="AST path")             # Positional argument
    parser.add_argument("--sig_list_dir", type=str, help="AST path")                # Positional argument
    parser.add_argument("--design_dir", type=str, help="AST path")                # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(FaultSimulator.__dict__.keys()))

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)

        sim_prep = SimulatorPrepare(ast,args.logic_value_dir,args.sig_list_dir,args.design_dir)
        sim_prep.preprocess()

