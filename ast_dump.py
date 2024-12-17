from ast_construct import *

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

    def process(self):
        self.ast_process()
        self.dump_sig_dict()

class AstDumpRegList:
    def __init__(self,ast):
        self.ast = ast
        self.preprocessor = AstSchedulePreprocess(self.ast)
        self.flattener = AstArrayFlatten(self.ast)

    def ast_process(self):
        # start scheduling
        self.preprocessor = AstSchedulePreprocess(self.ast)
        self.preprocessor.preprocess()

        # flatten composite signals to packed registers
        self.flattener = AstArrayFlatten(self.ast)
        self.flattener.module_var_flatten()

    def get_input_port(self):
        for var in self.ast.findall(".//module//var[@dir='input']"):
            pass


    def get_ff(self):
        for var in self.ast.findall(".//module//var[@type='register']"):
            pass

    def get_output_port(self):
        for var in self.ast.findall(".//module//var[@dir='output']"):
            pass

    def dump_sig_dict(self):
        pass

    def process(self):
        self.ast_process()
        self.dump_sig_dict()
