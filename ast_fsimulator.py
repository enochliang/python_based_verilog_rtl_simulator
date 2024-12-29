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
    def __init__(self,ast):
        AstNodeClassify.__init__(self)

        self.ast = ast

        # duplicate ast -> get self.my_ast
        self.ast_duplicator = AstDuplicate(self.ast)
        self.ast_duplicator.duplicate()
        self.my_ast = self.ast_duplicator.my_ast

        # dump simulator sig list
        self.sig_dumper = AstDumpSimulatorSigList(self.ast)
        self.ast_dumper = AstDump(self.ast)
       
        # TODO
        self.logic_value_file_dir = "../picorv32/pattern/"
        self.logic_value_file_head = "FaultFree_Signal_Value_C"
        self.logic_value_file_tail = ".txt"

    def load_ordered_varname(self):
        self.varname_list = []
        f = open("./sig_list/simulator_sig_dict.json","r")
        for varname in json.load(f).keys():
            self.varname_list.append(varname)
        f.close()

    def load_logic_value_file(self,cycle,width:int=7) -> list:
        # Fetch logic value dump file at the specific clock cycle
        target_filename = self.logic_value_file_dir + self.logic_value_file_head + f"{cycle:0{width}}" + self.logic_value_file_tail
        print(f"reading file: {target_filename}")
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

    def init_fault_list(self):
        for node in self.my_ast.register_list:
            fault_name = node.name
            node.fault_list = {(fault_name,"stay"):1.0}


class FaultSimulatorExecute(SimulatorPrepare):
    """
    A simulator

    Methods:
        load_ordered_varname:

        exec_comb_entry:          visit function of "combinational subcircuit entry node"
        exec_seq_entry:           visit function of "sequential subcircuit entry node"

        (to be removed) execute_rtl:           visit function of general ast subcircuit node
        exec_comb:      
        exec_seq:

        compute_in:           visit function of "right_value circuit nodes" and "braanch condition circuit node" (for logic value propagation)
        compute_out:        visit function of "left_value circuit nodes" (for logic value propagation)

        
        exec_assign:    visit function of "assignment node"
        exec_comb_assign_cf:
        exec_seq_assign_cf:

        exec_seq_if:
        exec_comb_if:

        exec_seq_case:
        exec_comb_case:

        prep_seq_caseitem:
        prep_comb_caseitem:
        exec_comb_caseitem:  visit function of "triggered caseitem"
        exec_seq_caseitem:
        exec_seq_true_caseitem:
        exec_seq_false_caseitem:
        trigger_condition: visit function of

        exec_comb_block:
        exec_seq_block:
        exec_seq_true_block:  
        exec_seq_false_block: 
    """
    def __init__(self,ast):
        SimulatorPrepare.__init__(self,ast)

    #-----------------------------------------------------------------------------
    def exec_comb_entry(self,node):
        lv_name = node.attrib["lv_name"]
        init_value = self.my_ast.var_node(lv_name).value
        self.exec_comb(node,{})

        # check if the calculated result match the dumped one.
        final_value = self.my_ast.var_node(lv_name).value
        if "__Vdfg" not in lv_name and init_value != final_value:
            print(f"lv_name = {lv_name}")
            print(f"    init_value = {init_value}")
            print(f"    final_value = {final_value}")
            raise SimulationError("computed value & dumped value mismatch.",6)

    def exec_seq_entry(self,node):
        self.exec_seq(node,{})
        #self.execute_df(node)
    #------------------------------------------------------------------------------


    #------------------------------------------------------------------------------
    # RTL simulation functions
    def exec_seq(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_seq_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_seq_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_seq_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def exec_comb(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_comb_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_comb_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_comb_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def exec_seq_false(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_seq_cf_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_seq_false_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_seq_false_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_seq_false_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #----------------------------------------------------------------------------------


    #----------------------------------------------------------------------------------
    # assignment
    def exec_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_in(right_node)
        self.compute_out(left_node)

        # data fault propagation
        self.prop_in_fault(right_node)

        #origin_value get right value result
        value = right_node.value
        width = len(value)
        self.assign_value(left_node, value, width, 0)

        # propagate fault to target signal
        target_node = self.get_target_lv(left_node)
        self.assign_data_fault(target_node)
        self.append_ctrl_fault(target_node)

        # selectional control fault
        self.prop_sel_fault(left_node)

    def exec_seq_cf_assign(self,node,ctrl_fault:dict):
        left_node = node.lv_node
        # visit
        self.compute_out(left_node)
        # origin_value get right value result
        self.prop_sel_fault()

    #--------------------------------------------------------------------------------
    def assign_value(self, node, value:str, width:int, start_bit:int = 0):
        # Assign left value to target signal.
        if node.tag == "sel":
            start_bit = node.children[1].value
            if "x" in start_bit:
                value = node.children[0].value
                width = len(value)
                value = "x"*width
                self.assign_value(node.children[0], value, width, 0)
            else:
                start_bit = int(node.children[1].value,2)
                width = int(node.children[2].value,2)
                self.assign_value(node.children[0], value, width, start_bit)
        elif node.tag == "arraysel":
            idx = int(node.children[1].value,2)
            self.assign_value(node.children[0].node.children[idx], value, width, start_bit)
        elif node.tag == "varref":
            self.assign_value(node.ref_node, value, width, start_bit)
        elif node.tag == "var":
            origin_value = node.value
            if start_bit == 0:
                new_value = origin_value[:-width] + value
            else:
                new_value = origin_value[:-start_bit-width] + value + origin_value[-start_bit:]
            node.value = new_value
        else:
            raise SimulationError(f"Unknown signal node to assign: tag = {node.tag}.",5)
    #--------------------------------------------------------------------------------------



    def compute_ctrl(branch_node):
        # compute for control signal value
        ctrl_node = branch_node.ctrl_node
        self.compute_in(ctrl_node)
        value = ctrl_node.value
        return value

    #--------------------------------------------------------------------------------------
    # Branches in rtl simulation
    #----------------------------------------------
    #   Execute IF Node
    def exec_seq_if(self,node,ctrl_fault:dict):
        # compute for control signal value
        value = self.compute_ctrl(node)

        # execute the triggered block
        if "1" in value:
            self.exec_seq(node.true_node,{})
        else:
            if node.false_node == None:
                pass
            else:
                self.exec_seq(node.false_node,{})

    def exec_comb_if(self,node,ctrl_fault:dict):
        # compute for control signal value
        value = self.compute_ctrl(node)

        # execute the triggered block
        if "1" in value:
            self.exec_comb(node.true_node, ctrl_fault)
        else:
            if node.false_node == None:
                pass
            else:
                self.exec_comb(node.false_node, ctrl_fault)
    #----------------------------------------------
    #   Execute CASE Node
    def exec_seq_case(self,node,ctrl_fault:dict):
        # compute for control signal value
        value = self.compute_ctrl(node)

        # compute for condition signal values
        for child in node.caseitems:
            self.prep_seq_caseitem(child)

        # execute the triggered block
        for child in node.caseitems:
            if self.exec_seq_caseitem(child,value):
                break

    def exec_comb_case(self,node,ctrl_fault:dict):
        # compute for control signal value
        value = self.compute_ctrl(node)

        # compute for condition signal values
        for child in node.caseitems:
            self.prep_comb_caseitem(child)

        # execute the triggered block
        for child in node.caseitems:
            if self.exec_comb_caseitem(child,value):
                break
    #----------------------------------------------
    def prep_comb_caseitem(self,node):
        # prepare the condition signals.
        for cond in node.conditions:
            self.compute_in(cond)




    #----------------------------------------------
    def trigger_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def exec_seq_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.exec_seq(child,{})
        return flag

    def exec_comb_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.exec_comb(child,{})
        return flag
    #------------------------------------------------------------------------------


    #------------------------------------------------------------------------------
    # execution of code block
    def exec_seq_block(self,node,ctrl_fault:dict):
        for child in node.children:
            self.exec_seq(child,ctrl_fault)

    def exec_comb_block(self,node,ctrl_fault:dict):
        for child in node.children:
            self.exec_comb(child,ctrl_fault)

    def exec_seq_false_block(self,node,ctrl_fault:dict):
        for child in node.children:
            self.exec_comb(child,ctrl_fault)
    #------------------------------------------------------------------------------


    # fault list propagation rtl simulation
    # rtl computation
    def compute_in(self,node) -> None:
        """
        visitor of all nodes under "right_value" and "control_signal".

        function:
        prepare all signals on the right side of assignment.
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_in(child)

        if node.tag == "varref":
            return
        elif node.tag == "arraysel":
            return
        elif node.tag == "sel":
            result = val_sel(node)
        elif node.tag == "cond":
            result = val_cond(node)
        elif node.tag == "const":
            return
        elif node.tag in self.op__2_port:
            result = val_2_op(node)
        elif node.tag in self.op__1_port:
            result = val_1_op(node)
        else:
            raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",3)
        
        self.check_width(node,result)
        node.value = result

    def compute_out(self,node) -> None:
        """
        visitor of all nodes under "left_value".

        function:
        prepare all selection signals of target signal.
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_out(child)

        if node.tag == "varref":
            return
        elif node.tag == "arraysel":
            return
        elif node.tag == "sel":
            result = val_sel(node)
        elif node.tag == "cond":
            result = val_cond(node)
        elif node.tag == "const":
            return
        elif node.tag in self.op__2_port:
            result = val_2_op(node)
        elif node.tag in self.op__1_port:
            result = val_1_op(node)
        else:
            raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",3)
        
        self.check_width(node,result)
        node.value = result

    # checking function
    def check_width(self,node,result):
        #if result is not None:
        width = node.width
        if not self.check_len(result,width):
            if "loc" in node.attrib:
                print(f"loc = {node.attrib['loc']}")
            raise SimulationError(f"result and width mismatch: tag = {node.tag}, result = {result}, width = {width}.",4)

    def check_len(self,s:str,l:int):
        return len(s) == l


    #------------------------------------------------------
    # Data Write-event fault propagation
    #
    def prop_in_fault(self,node):
        for child in node.children:
            self.prop_in_fault(child)

        if node.tag == "varref":
            return
        elif node.tag == "arraysel":
            new_fault_list = {}
            


            return
        elif node.tag == "sel":
            result = val_sel(node)
        elif node.tag == "cond":
            result = val_cond(node)
        elif node.tag == "const":
            return
        elif node.tag in self.op__2_port:
            l_prob, r_prob = prob_2_op(node)
        elif node.tag in self.op__1_port:
            prob = prob_1_op(node)
        else:
            raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",3)

    def fault_prop(self, target_fault_list ):
        pass
    #------------------------------------------------------
    # Control fault propagation
    #
    #def exec_seq_entry_cf(self,node):
    #    if "assign" in node.tag:
    #        self.exec_seq_entry_cf_assign(node)
    #    elif node.tag == "if":
    #        self.exec_seq_entry_cf_if(node)
    #    elif node.tag == "case":
    #        self.exec_seq_entry_cf_case(node)
    #    elif node.tag == "begin" or node.tag == "always":
    #        self.exec_seq_entry_cf_block(node)
    #    else:
    #        raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    #------------------------------------------------------

    # Control fault propagation
    #
    def exec_comb_entry_cf(self,node):
        if "assign" in node.tag:
            self.exec_comb_entry_cf_assign(node)
        elif node.tag == "if":
            self.exec_comb_entry_cf_if(node)
        elif node.tag == "case":
            self.exec_comb_entry_cf_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_comb_entry_cf_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    #def get_value(self,node):
    #    if type(node) is str:
    #        return node
    #    else:
    #        return node.value
    




class Simulator(FaultSimulatorExecute):
    def __init__(self,ast):
        FaultSimulatorExecute.__init__(self,ast)
        self.dumper = AstDumpSimulatorSigList(self.ast)

    def propagate(self):
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_head:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.exec_comb_entry(entry_node)
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_tail:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.exec_seq_entry(entry_node)

    def simulate_1_cyc(self,cyc:int):
        self.load_logic_value(cyc)
        self.init_fault_list()
        #self.my_ast.show_register_fault_list()
        self.propagate()

    def simulate(self):
        self.preprocess()
        for cyc in range(500,485080):
            # simulation
            self.simulate_1_cyc(cyc)

    def preprocess(self):
        self.dumper.dump_sig_dict()
        self.load_ordered_varname()

    def process(self):
        self.preprocess()
        self.simulate_1_cyc(8517)
        #self.ast_dumper.dump()
        #self.dumper.dump_sig_dict()
        #self.load_ordered_varname()
        #self.my_ast.show_var_value()
        # simulation
        #self.simulate_1_cyc(8517)


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
        ast_sim.simulate()

