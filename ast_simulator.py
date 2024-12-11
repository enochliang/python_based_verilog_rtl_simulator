from ast_define import *
from ast_construct import AstDuplicate
from ast_nodeclassify import *
from ast_dump import *
from exceptions import SimulationError
from utils import *

import argparse
import pickle
import json

class SimulatorLoadLogic(AstNodeClassify):
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


class SimulatorExecute(SimulatorLoadLogic):
    def __init__(self,ast):
        SimulatorLoadLogic.__init__(self,ast)

    def execute(self,node):
        if "assign" in node.tag:
            self.execute_assign(node)
        elif node.tag == "if":
            self.execute_if(node)
        elif node.tag == "case":
            self.execute_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.")

    def execute_assign(self,node):
        right_node = node.rv_node
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
        ctrl_node = self.get_node(node.ctrl_node)
        value = self.compute(ctrl_node)
        for child in node.caseitems:
            if self.execute_caseitem(child,value):
                break

    def execute_block(self,node):
        for child in node.children:
            self.execute(child)

    def trigger_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            if self.compute(cond) == ctrl_value:
                flag = True
                break
        return (flag or (node.condition_ids == []))

    def execute_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute(child)
        return flag

    def compute(self,node):
        pass


class SimulatorCompute(SimulatorExecute):
    def __init__(self,ast):
        SimulatorExecute.__init__(self,ast)

    def get_value(self,node):
        if node is str:
            return node
        else:
            return node.value

    def compute(self,node):
        print(node.tag)
        width = node.width
        if node.tag == "varref":
            ref_id = node.ref_id
            var_node = self.ast_node_list[ref_id]
            return var_node
        elif node.tag == "arraysel":
            sel_node = self.get_node(node.children[1])
            idx = int(self.get_value(self.compute(sel_node)),2)
            return self.get_node(node.children[0]).children[idx]
        elif node.tag == "sel":
            pass
        elif node.tag in self.op__2_port:
            left_node = self.get_node(node.children[0])
            right_node = self.get_node(node.children[1])
            r_value = self.get_value(self.compute(right_node))
            l_value = self.get_value(self.compute(left_node))
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
        self.check_width(result,width)
        return result

    def ast_or(self,lv,rv,width:int):
        print(lv,rv)
        result = ""
        for idx in range(width):
            result = result + self._or(rv[idx],lv[idx])
        self.check_width(result,width)
        return result

    def ast_xor(self,lv,rv,width:int):
        result = ""
        for idx in range(width):
            result = result + self._xor(rv[idx],lv[idx])
        self.check_width(result,width)
        return result

    def ast_not(iv):
        result = ""
        for idx in range(width):
            result = result + self._not(iv[idx])
        self.check_width(result,width)
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
        if "x" in rv:
            result = "x"*width
        else:
            offset = int(rv,2)
            result = lv[offset:] + "0"*offset
        self.check_width(result,width)
        return result

    def ast_shiftr(self,lv,rv,width:int):
        if "x" in rv:
            result = "x"*width
        else:
            offset = int(rv,2)
            result = "0"*offset + lv[:-(offset)]
        self.check_width(result,width)
        return result


    def _half_add(self,lv,rv,carry):
        if "x" in lv+rv+carry:
            if (lv+rv+carry).find("1") == 0:
                new_carry = "0"
            elif (lv+rv+carry).find("1") == 1:
                new_carry = "x"
            elif (lv+rv+carry).find("1") > 1:
                new_carry = "1"
            result = "x"
        else:
            if (lv+rv+carry).find("1")%2 == 1:
                result = "1"
            else:
                result = "0"
            if (lv+rv+carry).find("1") > 1:
                new_carry = "1"
            else:
                new_carry = "0"
        return result, new_carry

            

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

    def check_len(self,s:str,l:int):
        return len(s) == l

    def check_width(self,result:str,width:int):
        if not self.check_len(s,l):
            raise SimulationError("result width doesn't match the node output width.",0)

    def assign(self,node):
        pass

class Simulator(SimulatorCompute):
    def __init__(self,ast):
        SimulatorCompute.__init__(self,ast)
        self.dumper = AstDumpSimulatorSigList(self.ast)

    def simulate_1_cyc(self):
        t_set = set()
        for node in self.ast_node_list:
            t_set.add(type(node))
        for subcircuit_id in self.ordered_subcircuit_id_head:
            entry_id = self.my_ast._map__treeid_2_node[subcircuit_id]
            entry_node = self.get_node(entry_id)
            self.execute(entry_node)
        for subcircuit_id in self.ordered_subcircuit_id_tail:
            entry_id = self.my_ast._map__treeid_2_node[subcircuit_id]
            entry_node = self.get_node(entry_id)
            self.execute(entry_node)


    def process(self):
        self.dumper.dump_sig_dict()
        self.varname_list = self.load_ordered_varname()
        self.load_logic_value(100000)
        # simulation
        #self.simulate()


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

