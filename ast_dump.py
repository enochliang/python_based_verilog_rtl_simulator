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


class AstDumpWrapperSigList:
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)

    def get_dict__signal_table(self):
        self.signal_table = self.analyzer.get_dict__signal_table()

    def dump_sig_dict(self):
        self.get_dict__signal_table()
        print("Dumped Signal Table.")
        print(self.signal_table)



class AstDumpSimulatorSigList:
    def __init__(self,ast):
        self.ast = ast
        self._dict__varname_2_width = {}
        self.get_dict__var_width()

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
        f = open("./sig_list/simulator_sig_dict.json","w")
        f.write(json.dumps(varname_2_width, indent=4))
        f.close()
        print("  - dumped file = ./sig_list/simulator_sig_dict.json")

    def process(self):
        self.ast_process()
        self.dump_sig_dict()

