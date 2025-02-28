from ast_construct import *
from ast_analyzer import *

from lxml import etree
import json


class AstDump:
    def __init__(self,ast):
        self.ast = ast

    def dump(self):
        etree.indent(self.ast,space="  ")
        with open("new_ast_dump.xml","w") as fp:
            fp.write(etree.tostring(self.ast.find("."),pretty_print=True).decode())
        print("  Dumped <new_ast_dump.xml>!")


class AstDumpFsimSigTable:
    def __init__(self,ast,sig_list_dir):
        self.ast = ast
        self.signal_table = {"input":{},"ff":{},"output":{}}
        self.sig_list_dir = sig_list_dir

    def dump_sig_dict(self):
        clk_name = "clk"
        optimize_sig = "__Vdfg"
        for var in self.ast.findall(".//var"):
            width = int(var.attrib["width"])
            if optimize_sig in var.attrib["name"]:
                continue
            elif clk_name == var.attrib["name"]:
                continue
            elif var.attrib["sig_type"] == "register":
                self.signal_table["ff"][var.attrib["name"]] = width
            elif "dir" in var.attrib:
                if var.attrib["dir"] == "input":
                    self.signal_table["input"][var.attrib["name"]] = width
                elif var.attrib["dir"] == "output":
                    self.signal_table["output"][var.attrib["name"]] = width
                
        print("Dumped Signal Table.")
        sig_table_dir = self.sig_list_dir + "fsim_sig_table.json"
        f = open(sig_table_dir,"w")
        f.write(json.dumps(self.signal_table, indent=4))
        f.close()
        print(f"  - dumped file = {sig_table_dir}")



class AstDumpPySimSigTable:
    def __init__(self,ast,sig_list_dir):
        self.ast = ast
        self._dict__varname_2_width = {}
        self.get_dict__var_width()
        self.sig_list_dir = sig_list_dir

    def ast_process(self):
        # start scheduling
        self.preprocessor = AstSchedulePreprocess(self.ast)
        self.preprocessor.preprocess()

        # flatten composite signals to packed registers
        self.flattener = AstArrayFlatten(self.ast)
        self.flattener.module_var_flatten()


    def get_dict__var_width(self):
        for var in self.ast.findall(".//module//var"):
            width = int(var.attrib["width"])
            name = var.attrib["name"]
            self._dict__varname_2_width[name] = width

    def dump_sig_dict(self):
        print("Dumped Varname Dict.")
        varname_2_width = {}
        clk_name = "clk"
        optimize_sig = "__Vdfg"
        for varname in self._dict__varname_2_width:
            if optimize_sig in varname:
                continue
            if clk_name == varname:
                continue
            varname_2_width[varname] = self._dict__varname_2_width[varname]

        sig_table_dir = self.sig_list_dir + "pysim_sig_table.json"
        f = open(sig_table_dir,"w")
        f.write(json.dumps(varname_2_width, indent=4))
        f.close()
        print(f"  - dumped file = {sig_table_dir}")

    def process(self):
        self.ast_process()
        self.dump_sig_dict()

