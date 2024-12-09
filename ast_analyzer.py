from lxml import etree
import pprint 
import argparse
import json
from utils import *

class RTL_Coding_Style_Warning(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"
class Unconsidered_Case(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"


class AstAnalyzer:
    def __init__(self, ast: etree._ElementTree):
        self.ast = ast

    def vnum2int(self,num:str):
        return vnum2int(num)

    def vnum2bin(self,num:str):
        return vnum2bin(num)

    def show_all_submodname(self):
        return show_all_submodname(self.ast)

    def get_width__dtype_id(self,dtype_id:str):
        return get_width__dtype_id(self.ast,dtype_id)

    def get_width__node(self,node):
        return get_width__node(node)

    def get_width__dtype(self,dtype):
        return get_width__dtype(dtype)

    def get_shape__dtype(self,dtype):
        return get_shape__dtype(dtype)


    def get_dtype__not_logic(self,output=True) -> set:
        return get_dtype__not_logic(self.ast,output)

    def get_dtype__node(self,node):
        return get_dtype__node(node)


    def get_basic_dtypename__node(self,node):
        return get_basic_dtypename__node(node)

    def get_basic_dtypename__dtype(self,dtype):
        return get_basic_dtypename__dtype(dtype)

    def get_basic_dtype__dtype(self,dtype):
        return get_basic_dtype__dtype(dtype)


    def get_dict__dtypeid_2_width(self) -> dict:
        return get_dict__dtypeid_2_width(self.ast)

    def get_dict__dtypeid_2_shape(self) -> dict:
        return get_dict__dtypeid_2_shape(self.ast)

    def get_dict__signame_2_width(self,sig_list):
        return get_dict__signame_2_width(self.ast,sig_list)
 
    def get_dict__dtypetable(self,output=True) -> dict:
        return get_dict__signame_2_width(self.ast,output)

    def get_dict__signal_table(self):
        return get_dict__signal_table(self.ast)

    def search_basic_dtype(self,node):
        return search_basic_dtype(self.ast)

    def get_tag__all_under(self,target="verilator_xml",output=True) -> set:
        return get_tag__all_under(self.ast,target,output)

    def get_children_unique__under(self,target="verilator_xml",output=True) -> list:
        return get_children_unique__under(self.ast,target,output)

    def get_children__ordered(self,node):
        return get_children__ordered(node)

    def get_children__ordered_under(self,target="verilator_xml",output=True) -> list:
        return get_children__ordered_under(self.ast,target,output)

    def get_sig_node(self,node):
        return get_sig_node(node)

    def get_sig_name(self,node):
        return get_sig_name(node)
    
    def get_sig__all(self,output=True) -> set:
        return get_sig__all(self.ast,output)

    def get_sig__lv(self):
        return get_sig__lv(self.ast)

    def get_sig__input_port(self):
        return get_sig__input_port(self.ast)

    def get_sig__ff(self):
        return get_sig__ff(self.ast)
    
    def get_sig__output_port(self):
        return get_sig__output_port(self.ast)

    def get_subcircuits(self):
        return get_sig__output_port(self.ast)

    def ast_flattened(self):
        return ast_flattened(self.ast)


    def dump_signal_table(self, file_name, signal_table):
        with open(file_name,"w") as f:
            f.write(json.dumps(signal_table, indent=4))
            f.close()

def Verilator_AST_Tree(ast_file_path:str) -> etree._ElementTree:
    return etree.parse(ast_file_path)


if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(AstAnalyzer.__dict__.keys()))

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)
        print("#"*len("# Start analyzing ["+ast_file+"] #"))
        print("# Start parsing ["+ast_file+"] #")
        print("#"*len("# Start analyzing ["+ast_file+"] #"))
        analyzer = AstAnalyzer(ast)
        id_set = set()
        for type_ in ast.findall(".//basicdtype"):
            id_set.add(type_.attrib["name"])

        print(id_set)


