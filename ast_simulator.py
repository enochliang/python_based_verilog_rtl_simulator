from ast_schedule import *
from abc import ABC, abstractmethod
import pickle
import json


class Verilog_AST_Construction_Exception(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"


class Verilog_AST_Base_Node:
    def __init__(self):
        self._tag = ""
        self._children = []
        self.attrib = dict()

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self,value:list):
        self._children = value

    def append(self,node):
        self._children.append(node)

    @abstractmethod
    def tag(self):
        pass

class Verilog_AST_Node(Verilog_AST_Base_Node):
    def __init__(self):
        Verilog_AST_Base_Node.__init__(self)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self,tag:str):
        self._tag = tag

class Verilog_AST_Control_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)

    @property
    def ctrl_sig_id(self):
        if len(self._children) < 1:
            return None
        else:
            return self._children[0]

class Verilog_AST_IF_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "if"
        self.__true_id = None
        self.__false_id = None

    @property
    def true_id(self):
        if len(self._children) < 2:
            return None
        else:
            return self._children[1]

    @property
    def false_id(self):
        if len(self._children) < 3:
            return None
        else:
            return self._children[2]

class Verilog_AST_CASE_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "case"
        self.__caseitem_ids = []

    @property
    def caseitem_ids(self):
        return self.__caseitem_ids

    def append(self,idx:int):
        self.__caseitem_ids.append(idx)

class Verilog_AST_CASEITEM_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)
        self._tag = "caseitem"
        self.__condition_ids = []

    @property
    def condition_ids(self):
        return self.__condition_ids

    def add_condition(self,idx):
        self.__condition_ids.append(idx)

    @property
    def other_children(self):
        return self._children[len(self.__condition_ids):]


class Verilog_AST_Circuit_Node(Verilog_AST_Node):
    def __init__(self,width:int):
        Verilog_AST_Node.__init__(self)
        self._width = width
        self._value = "x"*self._width
        self._signed = False

    @property
    def signed(self):
        return self._signed

    @signed.setter
    def signed(self,value:bool):
        self._signed = value

    @property
    def width(self):
        return self._width

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,value:str):
        if len(value) == self._width:
            self._value = value
        else:
            raise Verilog_AST_Construction_Exception("value and width doesn't match.",0)

class Verilog_AST_Var_Node(Verilog_AST_Circuit_Node):
    def __init__(self,width:int):
        Verilog_AST_Circuit_Node.__init__(self,width)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self,value:str):
        self.__name = value

class Verilog_AST_Varref_Node(Verilog_AST_Circuit_Node):
    def __init__(self,width:int):
        Verilog_AST_Circuit_Node.__init__(self,width)
        self._tag = "varref"

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self,value:str):
        self.__name = value

    @property
    def ref_id(self):
        return self.__ref_id

    @ref_id.setter
    def ref_id(self,value:int):
        self.__ref_id = value

class Ast2SimulatorBase(AstAnalyzer):
    def __init__(self,ast):
        AstAnalyzer.__init__(self,ast)
        ast_scheduler = AstSchedule(ast)
        ast_scheduler.proc()
        self.ast = ast_scheduler.ast
        self.subcircuit_num = ast_scheduler.subcircuit_num
        self.ordered_subcircuit_id_head = ast_scheduler.ordered_subcircuit_id_head
        self.ordered_subcircuit_id_tail = ast_scheduler.ordered_subcircuit_id_tail

class AstArrayFlatten(Ast2SimulatorBase):
    def __init__(self,ast):
        Ast2SimulatorBase.__init__(self,ast)

    def output(self,ast):
        with open("output.xml","w") as fp:
            fp.write(etree.tostring(ast.find("."),pretty_print=True).decode())

    def module_var_flatten(self):
        for var in self.ast.findall(".//module/var"):
            self.var_flatten(var)

    def get_dtype_node(self,node):
        dtype_id = node.attrib["dtype_id"]
        dtype = self.ast.find(f".//typetable//*[@id='{dtype_id}']")
        dtype = self._get_dtype_node(dtype)
        return dtype

    def _get_dtype_node(self,dtype):
        if dtype.tag == "refdtype":
            sub_dtype_id = dtype.attrib["sub_dtype_id"]
            dtype = self.ast.find(f".//typetable//*[@id='{sub_dtype_id}']")
        return dtype

    def var_flatten(self,node):
        dtype = self.get_dtype_node(node)
        if dtype.tag == "basicdtype":
            pass
        elif dtype.tag == "unpackarraydtype":
            self.unpackarray_flatten(node)
        elif dtype.tag == "packarraydtype":
            self.packarray_flatten(node)

    def refdtype_flatten(self,node):
        name = node.attrib["name"]
        node.tag = ""
        dtype = self.get_dtype_node(node)
        sub_dtype_id = dtype.attrib["sub_dtype_id"]


    def unpackarray_flatten(self,node):
        name = node.attrib["name"]
        node.tag = "unpackarray"
        dtype = self.get_dtype_node(node)
        sub_dtype_id = dtype.attrib["sub_dtype_id"]
        const1 = dtype.find("./range/const[1]").attrib["name"]
        const2 = dtype.find("./range/const[2]").attrib["name"]
        const1 = AstAnalyzeFunc.vnum2int(const1)
        const2 = AstAnalyzeFunc.vnum2int(const2)
        if const1 > const2:
            for idx in range(const1,const2-1,-1):
                new_child = etree.Element("var")
                new_child.attrib["name"] = f"{name}[{idx}]"
                new_child.attrib["dtype_id"] = sub_dtype_id
                new_child.attrib["width"] = str(self.get_width__dtype_id(self.ast,sub_dtype_id))
                node.append(new_child)
                self.var_flatten(new_child)
        else:
            for idx in range(const1,const2+1,1):
                new_child = etree.Element("var")
                new_child.attrib["name"] = f"{name}[{idx}]"
                new_child.attrib["dtype_id"] = sub_dtype_id
                new_child.attrib["width"] = str(self.get_width__dtype_id(self.ast,sub_dtype_id))
                node.append(new_child)
                self.var_flatten(new_child)

class AstConstructAddVar(AstArrayFlatten):
    def __init__(self,ast):
        AstArrayFlatten.__init__(self,ast)
        self.module_var_flatten()
        self.output(self.ast)

        self._map__varrootname_2_id = {}

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
            self._map__varrootname_2_id[name] = self._append_var_node(var)

    def _append_var_node(self,node):
        width = int(node.attrib["width"])
        name = node.attrib["name"]
        children_id = []
        for child in node.getchildren():
            children_id.append(self._append_var_node(child))
        new_node_id = len(self.ast_node_list)
        new_var_node = Verilog_AST_Var_Node(width)
        new_var_node.tag = node.tag
        new_var_node.name = name
        new_var_node.children = children_id
        self.ast_node_list.append(new_var_node)
        return new_node_id

class AstConstructAddTree(AstConstructAddVar):
    def __init__(self,ast):
        AstConstructAddVar.__init__(self,ast)
        self._map__subcircuit_id_2_ast_id = {}

    def _add_ast_varref(self,node):
        name = node.attrib["name"]
        width = int(node.attrib["width"])
        ref_id = self._map__varrootname_2_id[name]
        new_node = Verilog_AST_Varref_Node(width)
        new_node.name = name
        new_node.ref_id = ref_id
        return new_node

    def _add_ast_circuit_node(self,node):
        width = int(node.attrib["width"])
        new_node = Verilog_AST_Circuit_Node(width)
        new_node.tag = node.tag
        if node.tag == "const":
            value = node.attrib["name"]
            value = AstAnalyzeFunc.vnum2bin(value)
            new_node.value = value
        return new_node

    def _add_ast_case(self):
        return Verilog_AST_CASE_Node()

    def _add_ast_if(self):
        return Verilog_AST_IF_Node()

    def _add_ast_caseitem(self,node,children_id):
        new_node = Verilog_AST_CASEITEM_Node()
        for idx, child in enumerate(node.getchildren()):
            if "dtype_id" in child.attrib:
                new_node.add_condition(children_id[idx])
        return new_node

    def add_ast_child(self,node):
        children = node.getchildren()
        children_id = []
        for child in children:
            children_id.append(self.add_ast_child(child))
        new_node_id = len(self.ast_node_list)

        if node.tag == "varref":
            new_node = self._add_ast_varref(node)
        elif "dtype_id" in node.attrib:
            new_node = self._add_ast_circuit_node(node)
        else:
            if node.tag == "case":
                new_node = self._add_ast_case()
            elif node.tag == "if":
                new_node = self._add_ast_if()
            elif node.tag == "caseitem":
                new_node = self._add_ast_caseitem(node,children_id)
            else:
                new_node = Verilog_AST_Node()
                new_node.tag = node.tag

        new_node.children = children_id
        self.ast_node_list.append(new_node)

        return new_node_id

    def append_ast_node(self):
        for subcircuit_id in range(self.subcircuit_num):
            entry_node = self.ast.find(f".//*[@subcircuit_id='{str(subcircuit_id)}']")
            entry_node_id = self.add_ast_child(entry_node)
            self._map__subcircuit_id_2_ast_id[subcircuit_id] = entry_node_id


class AstConstruct(AstConstructAddTree):
    def __init__(self,ast):
        AstConstructAddTree.__init__(self,ast)

    def ast_construct(self):
        self.ast_node_list = []

        self.get_dict__var_width()
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
        for subcircuit_id in range(self.subcircuit_num):
            subcircuit = self.ast.find(f".//*[@subcircuit_id='{str(subcircuit_id)}']")
            for node in subcircuit.iter():
                ast_node_num += 1
        print(f"Total Number of AST Nodes = {ast_node_num}")

    def count_my_ast_node(self):
        self.count_my_var_node()
        self.count_my_subcircuit_node()

    def count_my_var_node(self):
        ast_var_num = 0
        for key, idx in self._map__varrootname_2_id.items():
            ast_var_num += len(self.iter_my_node(self.ast_node_list[idx]))
        print(f"Total Number of <var> in my ast = {ast_var_num}")

    def count_my_subcircuit_node(self):
        ast_node_num = 0
        for key, idx in self._map__subcircuit_id_2_ast_id.items():
            ast_node_num += len(self.iter_my_node(self.ast_node_list[idx]))
        print(f"Total Number of subcircuit nodes in my ast = {ast_node_num}")

    def iter_my_node(self,node):
        node_list = []
        node_list.append(node)
        for child_id in node.children:
            child_node = self.ast_node_list[child_id]
            node_list = node_list + self.iter_my_node(child_node)
        return node_list

class AstDumpSigList(AstConstruct):
    def __init__(self,ast):
        AstConstruct.__init__(self,ast)
        self._dict__varname_2_width = {}

    def get_dict__var_width(self):
        for var in self.ast.findall(".//module//var"):
            width = int(var.attrib["width"])
            name = var.attrib["name"]
            self._dict__varname_2_width[name] = width

    def dump_dict__varname_2_width(self):
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
        f = open("./sig_list/graph_sig_dict.json","w")
        f.write(json.dumps(varname_2_width, indent=4))
        f.close()

class SimulatorLoadLogic(AstDumpSigList,AstNodeClassify):
    def __init__(self,ast):
        AstDumpSigList.__init__(self,ast)
        AstNodeClassify.__init__(self)
        
        self.logic_value_file_dir = "../picorv32/pattern/"
        self.logic_value_file_head = "FaultFree_Signal_Value_C"
        self.logic_value_file_tail = ".txt"

    def load_logic_value(self):
        pass


class SimulatorExecute(SimulatorLoadLogic):
    def __init__(self,ast):
        SimulatorLoadLogic.__init__(self,ast)


    def get_node(self,node_id):
        return self.ast_node_list[node_id]

    def execute_assign(self,node):
        right_node = self.get_node(node.children[0])
        width = right_node.width
        value = self.compute(right_node)

    def execute_if(self,node):
        ctrl_node = self.get_node(node.ctrl_sig_id)
        value = self.compute(ctrl_node)
        if "1" in value:
            true_node = self.get_node(node.true_id)
            self.execute(true_node)
        else:
            if node.false_id == None:
                pass
            else:
                false_node = self.get_node(node.false_id)
                self.execute(false_node)

    def execute_case(self,node):
        ctrl_node = self.get_node(node.ctrl_sig_id)
        value = self.compute(ctrl_node)
        for child_id in node.children[1:]:
            child_node = self.get_node(child_id)
            if self.execute_caseitem(child_node,value):
                break

    def execute_block(self,node):
        for child_id in node.children:
            child_node = self.get_node(child_id)
            self.execute(child_node)

    def execute(self,node):
        if "assign" in node.tag:
            self.execute_assign(node)
        else:
            if node.tag == "if":
                self.execute_if(node)
            elif node.tag == "case":
                self.execute_case(node)
            elif node.tag == "begin" or node.tag == "always":
                self.execute_block(node)
            else:
                print(f"Exception!!! tag = {node.tag}")

    def trigger_condition(self,node,ctrl_value:str):
        flag = False
        for condition_id in node.condition_ids:
            condition_node = self.get_node(condition_id)
            if self.compute(condition_node) == ctrl_value:
                flag = True
                break
        return (flag or (node.condition_ids == []))

    def execute_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_condition(node,ctrl_value)
        if flag:
            for child_id in node.other_children:
                child_node = self.get_node(child_id)
                self.execute(child_node)
        return flag

    def compute(self,node):
        pass


class SimulatorCompute(SimulatorExecute):
    def __init__(self,ast):
        SimulatorExecute.__init__(self,ast)

    def compute(self,node):
        width = node.width
        if node.tag in self.op__2_port:
            left_node = self.get_node(node.children[0])
            right_node = self.get_node(node.children[1])
            r_value = self.compute(right_node)
            l_value = self.compute(left_node)
            r_value = r_value.replace("z","x")
            l_value = l_value.replace("z","x")
            if "x" in r_value+l_value:
                result = "x"*width
            elif "z" in r_value+l_value:
                result = "z"*width
            elif node.tag == "and":
                result = self.ast_and(l_value,r_value,width)
            elif node.tag == "or":
                result = self.ast_or(l_value,r_value,width)
            elif node.tag == "xor":
                result = self.ast_xor(l_value,r_value,width)
            elif node.tag == "add":
                result = self.ast_add(l_value,r_value,width)
            elif node.tag == "sub":
                result = self.ast_sub(l_value,r_value,width)
            elif node.tag == "muls":
                result = self.ast_muls(l_value,r_value,width)
            elif node.tag == "shiftl":
                result = self.ast_shiftl(l_value,r_value,width)
            elif node.tag == "shiftr":
                result = self.ast_shiftr(l_value,r_value,width)
            elif node.tag == "shiftrs":
                result = self.ast_shiftrs(l_value,r_value,width)
            elif node.tag == "eq":
                result = self.ast_eq(l_value,r_value)
            elif node.tag == "neq":
                result = self.ast_neq(l_value,r_value)
            elif node.tag == "gt":
                result = self.ast_gt(l_value,r_value)
            elif node.tag == "gte":
                result = self.ast_gte(l_value,r_value)
            elif node.tag == "lte":
                result = self.ast_lte(l_value,r_value)
            elif node.tag == "lt":
                result = self.ast_lt(l_value,r_value)
            elif node.tag == "concat":
                result = self.ast_concat(l_value,r_value)
            else:
                result = ""
        elif node.tag in self.op__1_port:
            input_node = self.get_node(node.children[0])
            i_value = self.compute(input_node)
            if "x" in i_value:
                result = "x"*width
            elif "z" in i_value:
                result = "z"*width
            elif node.tag == "not":
                result = self.ast_not(i_value)
        else:
            if node.tag == "arraysel":
                result = self.ast_arraysel(l_value,r_value,width)
            elif node.tag == "sel":
                result = self.ast_sel()
            result = ""
        
        return result

    # computation part
    def ast_and(self,lv,rv,width:int):
        result = ""
        for idx in range(width):
            result = result + self._and(rv[idx],lv[idx])
        return result

    def ast_or(self,lv,rv,width:int):
        result = ""
        for idx in range(width):
            result = result + self._or(rv[idx],lv[idx])
        return result

    def ast_xor(self,lv,rv,width:int):
        result = ""
        for idx in range(width):
            result = result + self._xor(rv[idx],lv[idx])
        return result

    def ast_not(iv):
        result = ""
        for idx in range(width):
            result = result + self._not(iv[idx])
        return result

    def _and(self,lv,rv):
        rv = rv.replace("z","x")
        lv = lv.replace("z","x")
        if rv+lv == "xx":
            return "x"
        elif "x" in rv+lv:
            if "0" in rv+lv:
                return "0"
            else:
                return "x"
        else:
            return "1"

    def _or(self,lv,rv):
        rv = rv.replace("z","x")
        lv = lv.replace("z","x")
        if rv+lv == "xx":
            return "x"
        elif "x" in rv+lv:
            if "1" in rv+lv:
                return "1"
            else:
                return "x"
        else:
            return "0"

    def _xor(self,lv,rv):
        rv = rv.replace("z","x")
        lv = lv.replace("z","x")
        if "x" in rv+lv:
            return "x"
        else:
            if rv == lv:
                return "0"
            else:
                return "1"

    def _not(self,v):
        v = v.replace("z","x")
        if v == "x":
            return "x"
        else:
            if v == "1":
                return "0"
            else:
                return "1"

    def ast_shiftl(self,lv,rv,width:int):


    def ast_add(self,lv,rv,width:int):
        if rv[0] == "1":
            rv = "-0b"+rv
        if lv[0] == "1":
            lv = "-0b"+lv
        result = int(rv, 2) + int(lv, 2)
        result = f"{result:0{width}b}"
        result = format(result & int("1"*width,2),f"{width}b")
        return result

    def ast_sub(self,lv,rv,width:int):
        if rv[0] == "1":
            rv = "-0b"+rv
        if lv[0] == "1":
            lv = "-0b"+lv
        result = int(rv, 2) - int(lv, 2)
        result = f"{result:0{width}b}"
        result = format(result & int("1"*width,2),f"{width}b")
        return result

    def ast_muls(self,lv,rv,width:int):
        if rv[0] == "1":
            rv = "-0b"+rv
        if lv[0] == "1":
            lv = "-0b"+lv
        result = int(rv, 2) * int(lv, 2)
        result = f"{result:0{width}b}"
        result = format(result & int("1"*width,2),f"{width}b")
        return result

    def ast_eq(self,lv,rv):
        if rv == lv:
            return "1"
        else:
            return "0"

    def ast_neq(self,lv,rv):
        if rv != lv:
            return "1"
        else:
            return "0"

    def ast_gt(self,lv,rv):
        for idx in range(width):
            if lv[idx]+rv[idx] == "10":
                return "1"
            elif "x" in lv[idx]+rv[idx]:
                return "x"
        return "0"

    def ast_lt(self,lv,rv):
        for idx in range(width):
            if lv[idx]+rv[idx] == "01":
                return "1"
            elif "x" in lv[idx]+rv[idx]:
                return "x"
        return "0"

    def ast_gte(self,lv,rv):
        lt = self.ast_lt(lv,rv,width)
        if lt == "x":
            return "x"
        elif lt == "1":
            return "0"
        else:
            return "1"

    def ast_lte(self,lv,rv):
        gt = self.ast_gt(lv,rv,width)
        if gt == "x":
            return "x"
        elif gt == "1":
            return "0"
        else:
            return "1"



    def ast_concat(self,lv,rv):
        return lv+rv

    #def eq_len(x:str,y:str):
    #    return len(x) == len(y)

    #def check_eq_len(x:str,y:str):
    #    if not self.eq_len(x,y):
    #        raise 

    def assign(self,node):
        pass

class Simulator(SimulatorCompute):
    def __init__(self,ast):
        SimulatorCompute.__init__(self,ast)

    def simulate(self):
        t_set = set()
        for node in self.ast_node_list:
            t_set.add(type(node))
        print(t_set)
        for subcircuit_id in self.ordered_subcircuit_id_head:
            entry_id = self._map__subcircuit_id_2_ast_id[subcircuit_id]
            entry_node = self.get_node(entry_id)
            self.execute(entry_node)
        for subcircuit_id in self.ordered_subcircuit_id_tail:
            entry_id = self._map__subcircuit_id_2_ast_id[subcircuit_id]
            entry_node = self.get_node(entry_id)
            self.execute(entry_node)


    def process(self):
        self.ast_construct()
        self.dump_dict__varname_2_width()
        
        # simulation
        self.simulate()


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

