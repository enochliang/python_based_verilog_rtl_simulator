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

class SigTablePrepare(AstNodeClassify):
    def __init__(self,ast,sig_list_dir,design_dir):
        AstNodeClassify.__init__(self)

        self.ast = ast

        # duplicate ast -> get self.my_ast
        self.ast_duplicator = AstDuplicate(self.ast,design_dir)
        self.my_ast = None

        # sig list
        self.sig_list = sig_list_dir + "/"

        # dump ast to xml file
        self.ast_dumper = AstDump(self.ast,design_dir)

        # dump wrapper sig list
        self.fsim_sig_dumper = AstDumpFsimSigTable(self.ast,self.sig_list)

        # dump simulator sig list
        self.pysim_sig_dumper = AstDumpPySimSigTable(self.ast,self.sig_list)

    def prepare(self):
        self.ast_duplicator.duplicate()
        self.my_ast = self.ast_duplicator.my_ast

        self.ast_dumper.dump()
        self.pysim_sig_dumper.dump_sig_dict()
        self.fsim_sig_dumper.dump_sig_dict()



if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument
    parser.add_argument("-l", "--siglist_dir", type=str, help="siglist dir")        # Positional argument
    parser.add_argument("--design_dir", type=str, help="siglist dir") 

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(FaultSimulator.__dict__.keys()))
    if args.siglist_dir:
        siglist_dir = args.siglist_dir
        design_dir = args.design_dir

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)

        sig_prep = SigTablePrepare(ast,siglist_dir,design_dir)
        sig_prep.prepare()

