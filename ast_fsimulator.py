from ast_sim_prepare import *
from prob_functions import *

import pandas as pd

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
    # RTL simulation functions (for simulation entries)
    def exec_comb_entry(self,node):
        lv_name = node.attrib["lv_name"]
        self.exec_comb(node,{})

        # check if the calculated result match the dumped one.
        self.check_comb_value(lv_name)

    def exec_seq_entry(self,node):
        # sequential left value node to check
        self.target_node_set = set()

        self.exec_seq(node,{})

        # check if the calculated result match the dumped one.
        if self.check_seq_values():
            node.tostring()
            raise SimulationError(f"Py-simulator value mismatcch",0)


    #------------------------------------------------------------------------------
    # Computing Result Verification
    #------------------------------------------------------------------------------
    def check_comb_value(self,lv_name):
        init_value = self.my_ast.var_node(lv_name).cur_value
        final_value = self.my_ast.var_node(lv_name).value
        if "__Vdfg" not in lv_name and init_value != final_value:
            print(f"lv_name = {lv_name}")
            print(f"    init_value = {init_value}")
            print(f"    final_value = {final_value}")
            raise SimulationError("computed value & dumped value mismatch.",6)

    def check_seq_values(self):
        flag = False
        for target_node in self.target_node_set:
            if self.check_seq_value(target_node):
                flag = True
        self.target_node_set = set()
        return flag

    def check_seq_value(self,target_node):
        if target_node.value != target_node.next_value:
            print(f"Py-simulator value mismatch: signal name = {target_node.name}, final value = {target_node.value}, next value = {target_node.next_value}")
            return True
        else:
            return False


    #------------------------------------------------------------------------------
    # RTL simulation functions
    def exec_seq(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_seq_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_seq_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_seq_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_seq_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    def exec_seq_false(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_seq_false_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_seq_false_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_seq_false_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_seq_false_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def exec_comb(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_comb_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_comb_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_comb_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_comb_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    def exec_comb_false(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.exec_comb_false_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.exec_comb_false_if(node,ctrl_fault)
        elif node.tag == "case":
            self.exec_comb_false_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.exec_comb_false_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    #----------------------------------------------------------------------------------
    # assignment
    def exec_seq_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_in(right_node)
        self.compute_out(left_node)

        # data fault propagation
        self.prop_in_fault(right_node)

        #origin_value get right value result
        value = right_node.ivalue
        width = len(value)
        if left_node.width > width:
            value = (left_node.width - width)*"0" + value
            self.assign_value(node, value, node.width, 0)
        else:
            self.assign_value(left_node, value, width, 0)

        # get the target node to propagate fault to.
        target_node = self.get_target_node(left_node)
        # add left value node for checking
        self.target_node_set.add(target_node)
        
        # propagate data fault to target signal
        data_flist = right_node.fault_list
        self.assign_data_fault(target_node,data_flist)

        # propagate ctrl fault to target signal
        self.assign_seq_ctrl_fault(target_node,ctrl_fault)

        # selectional control fault
        self.prop_seq_sel_fault(left_node)

    def exec_comb_assign(self,node,ctrl_fault:dict):
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

        # get the target node to propagate fault to.
        target_node = self.get_target_node(left_node)

        # propagate fault to target signal
        data_flist = right_node.fault_list
        self.assign_data_fault(target_node,data_flist)

        # propagate ctrl fault to target signal
        self.assign_comb_ctrl_fault(target_node,ctrl_fault)

        # selectional control fault
        self.prop_comb_sel_fault(left_node)

    def exec_seq_false_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_in(right_node)
        self.compute_out(left_node)

        # get the target node to propagate fault to.
        target_node = self.get_target_node(left_node)

        # propagate ctrl fault to target signal
        self.assign_seq_ctrl_fault(target_node,ctrl_fault)

    def exec_comb_false_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_in(right_node)
        self.compute_out(left_node)

        # get the target node to propagate fault to.
        target_node = self.get_target_node(left_node)

        # propagate ctrl fault to target signal
        self.assign_comb_ctrl_fault(target_node,ctrl_fault)

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

    def assign_data_fault(self,node,flist):
        data_flist = dict()
        for f in flist:
            if f[1] == "stay":
                data_flist[(f[0],"data")] = flist[f]
            else:
                data_flist[f] = flist[f]
        node.fault_list = data_flist

    def assign_seq_ctrl_fault(self,node,flist:dict):
        ctrl_flist = dict()
        for f in flist:
            ctrl_flist[(f[0],"ctrl")] = flist[f]
        self.merge_flist(ctrl_flist, node.fault_list)

    def assign_comb_ctrl_fault(self,node,flist:dict):
        self.merge_flist(flist, node.fault_list)

    #--------------------------------------------------------------------------------------

    #--------------------------------------------------------------------------------------
    # Branches in rtl simulation
    #----------------------------------------------
    def compute_ctrl(self,branch_node):
        # compute for control signal value
        ctrl_node = branch_node.ctrl_node
        self.compute_in(ctrl_node)
        value = ctrl_node.ivalue
        return value

    def prop_if_cond_fault(self,branch_node):
        # compute for control signal value
        ctrl_node = branch_node.ctrl_node
        self.prop_in_fault(ctrl_node)
        return ctrl_node.fault_list

    # Execute IF Node
    def exec_seq_if(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)

        # get ctrl fault
        new_ctrl_fault = dict()
        cur_ctrl_fault = self.prop_if_cond_fault(node)
        self.merge_flist(ctrl_fault, new_ctrl_fault)
        self.merge_flist(cur_ctrl_fault, new_ctrl_fault)
        # TODO

        # execute the triggered block
        if "1" in value:
            self.exec_seq(node.true_node, new_ctrl_fault)
            if node.false_node != None:
                self.exec_seq_false(node.false_node, cur_ctrl_fault)
        else:
            if node.false_node != None:
                self.exec_seq(node.false_node, new_ctrl_fault)
            self.exec_seq_false(node.true_node, cur_ctrl_fault)

    def exec_seq_false_if(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)

        # execute the triggered block
        if "1" in value:
            self.exec_seq_false(node.true_node,ctrl_fault)
        else:
            if node.false_node != None:
                self.exec_seq_false(node.false_node,ctrl_fault)

    def exec_comb_if(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)

        # get ctrl fault
        new_ctrl_fault = dict()
        cur_ctrl_fault = self.prop_if_cond_fault(node)
        self.merge_flist(ctrl_fault, new_ctrl_fault)
        self.merge_flist(cur_ctrl_fault, new_ctrl_fault)
        # TODO


        # execute the triggered block, and then execute the false block
        if "1" in value:
            self.exec_comb(node.true_node, new_ctrl_fault)
            if node.false_node != None:
                self.exec_comb_false(node.false_node, cur_ctrl_fault)
        else:
            if node.false_node != None:
                self.exec_comb(node.false_node, new_ctrl_fault)
            self.exec_comb_false(node.true_node, cur_ctrl_fault)

    def exec_comb_false_if(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)

        # execute the triggered block
        if "1" in value:
            self.exec_comb_false(node.true_node,ctrl_fault)
        else:
            if node.false_node != None:
                self.exec_comb_false(node.false_node,ctrl_fault)

    #----------------------------------------------
    def prop_case_cond_fault(self,branch_node):
        # compute for control signal value
        ctrl_node = branch_node.ctrl_node
        self.prop_in_fault(ctrl_node)
        return ctrl_node.fault_list

    # Execute CASE Node
    def exec_seq_case(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)
        
        # get ctrl fault
        new_ctrl_fault = dict()
        cond_ctrl_fault = self.prop_case_cond_fault(node)
        cur_ctrl_fault = dict()

        # append ctrl fault into new_ctrl_fault
        self.merge_flist(ctrl_fault, new_ctrl_fault)
        self.merge_flist(cond_ctrl_fault, cur_ctrl_fault)

        # compute for condition signal values
        caseitem_trig_list = []  # stores (trigger flag, caseitem)s
        trigger_flag = False     #
        for child in node.caseitems:
            flag = self.prep_seq_caseitem(child,value)

            # get ctrl fault list from each <caseitem>
            castitem_flist = self.get_caseitem_flist(child)
            # append ctrl fault into new_ctrl_fault
            self.merge_flist(castitem_flist, cur_ctrl_fault)

            if flag and not trigger_flag:
                trigger_flag = flag
                caseitem_trig_list.append((True,child))
            else:
                caseitem_trig_list.append((False,child))

        # merge ctrl fault to new_ctrl_fault
        self.merge_flist(cur_ctrl_fault, new_ctrl_fault)

        # Execution:
        # execute the triggered block first
        for trigger, child in caseitem_trig_list:
            if trigger:
                self.exec_seq_caseitem(child,new_ctrl_fault)
        # execute the false blocks
        for trigger, child in caseitem_trig_list:
            if not trigger:
                self.exec_seq_false_caseitem(child,cur_ctrl_fault)

    def exec_seq_false_case(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)
        # compute for condition signal values
        caseitem_trig_list = []
        trigger_flag = False
        for child in node.caseitems:
            flag = self.prep_seq_caseitem(child,value)
            
            if flag and not trigger_flag:
                trigger_flag = flag
                caseitem_trig_list.append((True,child))
            else:
                caseitem_trig_list.append((False,child))
        # Execution:
        # only execute the triggered block
        for trigger, child in caseitem_trig_list:
            if trigger:
                self.exec_seq_false_caseitem(child,ctrl_fault)
                break


    def exec_comb_case(self,node,ctrl_fault:dict):
        # Preparing:
        # compute for control signal value
        value = self.compute_ctrl(node)

        # get ctrl fault
        new_ctrl_fault = dict()
        cond_ctrl_fault = self.prop_case_cond_fault(node)
        cur_ctrl_fault = dict()

        # append ctrl fault into new_ctrl_fault
        self.merge_flist(ctrl_fault, new_ctrl_fault)
        self.merge_flist(cond_ctrl_fault, cur_ctrl_fault)

        # compute for condition signal values
        caseitem_trig_list = []
        trigger_flag = False
        for child in node.caseitems:
            flag = self.prep_comb_caseitem(child,value)
            
            # get ctrl fault list from each <caseitem>
            castitem_flist = self.get_caseitem_flist(child)
            # append ctrl fault into new_ctrl_fault
            self.merge_flist(castitem_flist, cur_ctrl_fault)

            if flag and not trigger_flag:
                trigger_flag = flag
                caseitem_trig_list.append((True,child))
            else:
                caseitem_trig_list.append((False,child))

        # merge ctrl fault to new_ctrl_fault
        self.merge_flist(cur_ctrl_fault, new_ctrl_fault)

        # Execution:
        # execute the triggered block first
        for trigger, child in caseitem_trig_list:
            if trigger:
                self.exec_comb_caseitem(child,new_ctrl_fault)
        # execute the false blocks
        for trigger, child in caseitem_trig_list:
            if not trigger:
                self.exec_comb_false_caseitem(child,cur_ctrl_fault)

    def exec_comb_false_case(self,node,ctrl_fault:dict):
        # compute for control signal value
        value = self.compute_ctrl(node)
        # compute for condition signal values
        caseitem_trig_list = []
        trigger_flag = False
        for child in node.caseitems:
            flag = self.prep_comb_caseitem(child,value)
            if flag and not trigger_flag:
                trigger_flag = flag
                caseitem_trig_list.append((True,child))
            else:
                caseitem_trig_list.append((False,child))
        # Execution
        # only execute the triggered block
        for trigger, child in caseitem_trig_list:
            if trigger:
                self.exec_comb_false_caseitem(child,ctrl_fault)
                break

    #----------------------------------------------
    def prep_comb_caseitem(self,node,ctrl_value):
        # prepare the condition signals.
        trigger_flag = False
        for cond in node.conditions:
            self.compute_in(cond)
            if not trigger_flag and cond.value == ctrl_value:
                trigger_flag = True
        # trigger if the caseitem is default.
        if len(node.conditions) == 0:
            trigger_flag = True
        return trigger_flag

    def prep_seq_caseitem(self,node,ctrl_value):
        # prepare the condition signals.
        trigger_flag = False
        for cond in node.conditions:
            self.compute_in(cond)
            if not trigger_flag and cond.value == ctrl_value:
                trigger_flag = True
        # trigger if the caseitem is default.
        if len(node.conditions) == 0:
            trigger_flag = True
        return trigger_flag

    def get_caseitem_flist(self,node):
        new_flist = dict()
        for cond in node.conditions:
            self.prop_in_fault(cond)
            cond_flist = cond.fault_list
            self.merge_flist(cond_flist, new_flist)
        return new_flist


    #----------------------------------------------
    def exec_seq_caseitem(self,node,ctrl_fault:dict):
        for child in node.other_children:
            self.exec_seq(child,ctrl_fault)

    def exec_seq_false_caseitem(self,node,ctrl_fault:dict):
        for child in node.other_children:
            self.exec_seq_false(child,ctrl_fault)

    def exec_comb_caseitem(self,node,ctrl_fault:dict):
        for child in node.other_children:
            self.exec_comb(child,ctrl_fault)

    def exec_comb_false_caseitem(self,node,ctrl_fault:dict):
        for child in node.other_children:
            self.exec_comb_false(child,ctrl_fault)

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
            self.exec_seq_false(child,ctrl_fault)

    def exec_comb_false_block(self,node,ctrl_fault:dict):
        for child in node.children:
            self.exec_comb_false(child,ctrl_fault)


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


    #-----------------------------------------------------
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


    #-----------------------------------------------------
    # Data Write-event fault propagation
    def merge_flist(self, src_flist:dict, target_flist:dict):
        """
        Arguments:
          src_flist: "source fault list" that have to be merged into "target fault list"
          target_flist: pointer of "target fault list"

        Behaviour:
          target_flist <--merge--- src_flist & target_flist
        """
        for fault in src_flist:
            prob = src_flist[fault]
            if fault[1] == "stay":
                n_fault = (fault[0],"data")
            else:
                n_fault = fault
            if fault in target_flist:
                if prob > target_flist[n_fault]:
                    target_flist[n_fault] = prob
            else:
                target_flist[n_fault] = prob

    def merge_prob_flist(self, src_flist:dict, target_flist:dict, scaler:float):
        """
        Arguments:
          src_flist: "source fault list" that have to be merged into "target fault list"
          target_flist: pointer of "target fault list"
          scaler: 

        Behaviour:
          target_flist <--merge--- src_flist*scaler & target_flist
        """
        for fault in src_flist:
            prob = src_flist[fault]
            if fault[1] == "stay":
                n_fault = (fault[0],"data")
            else:
                n_fault = fault
            if fault in target_flist:
                if prob*scaler > target_flist[n_fault]:
                    target_flist[n_fault] = prob
            else:
                target_flist[n_fault] = prob*scaler

    def prop_in_fault(self,node):
        for child in node.children:
            self.prop_in_fault(child)
        new_flist = {}
        if node.tag == "varref":
            src_sig_flist = node.node.fault_list
            self.merge_flist(src_sig_flist, new_flist)
        elif node.tag == "arraysel":
            src_sig_flist = node.node.fault_list
            sel_sig_flist = node.children[1].node.fault_list
            self.merge_flist(src_sig_flist, new_flist)
            self.merge_flist(sel_sig_flist, new_flist)
        elif node.tag == "sel":
            src_sig_flist = node.children[0].node.fault_list
            bitsel_sig_flist = node.children[1].node.fault_list
            width_sig_flist = node.children[2].node.fault_list
            self.merge_flist(src_sig_flist, new_flist)
            self.merge_flist(bitsel_sig_flist, new_flist)
            self.merge_flist(width_sig_flist, new_flist)
        elif node.tag == "cond":
            if node.children[0].value == "x":
                pass
            elif node.children[0].value == "1":
                src_sig_flist = node.children[1].node.fault_list
                self.merge_flist(src_sig_flist, new_flist)
            else:
                src_sig_flist = node.children[2].node.fault_list
                self.merge_flist(src_sig_flist, new_flist)
            ctrl_sig_flist = node.children[0].node.fault_list
            self.merge_flist(ctrl_sig_flist, new_flist)
        elif node.tag == "const":
            pass
        elif node.tag in self.op__2_port:
            l_prob, r_prob = prob_2_op(node)
            l_flist = node.children[0].node.fault_list
            r_flist = node.children[1].node.fault_list
            self.merge_prob_flist(r_flist,new_flist,r_prob)
            self.merge_prob_flist(l_flist,new_flist,l_prob)
        elif node.tag in self.op__1_port:
            prob = prob_1_op(node)
            i_flist = node.children[0].node.fault_list
            self.merge_prob_flist(i_flist,new_flist,prob)
        else:
            raise SimulationError(f"Unknown op to compute: tag = {node.tag}.",3)
        node.fault_list = new_flist


    #----------------------------------------------------
    def prop_seq_sel_fault(self,node):
        pass

    def prop_comb_sel_fault(self,node):
        pass

    #----------------------------------------------------
    def fault_write(self,node):
        pass

    def fault_append(self,node):
        pass
    
    def fault_prop(self, target_fault_list ):
        pass
    
    def get_target_node(self,node):
        if node.tag == "sel":
            return node.children[0].node
        else:
            return node.node



class FaultSimulator(FaultSimulatorExecute):
    def __init__(self,ast):
        FaultSimulatorExecute.__init__(self,ast)

        # RW table dictionary
        self.rw_table = {"cycle":[],"rw_event":[]}

    def propagate(self):
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_head:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.exec_comb_entry(entry_node)
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_tail:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.exec_seq_entry(entry_node)

    def observe_fault_effect(self):
        cur_rw_events = []

        rw_events = {}
        for obs in self.my_ast.register_list:
            dst_reg_name = obs.name
            for fault, f_type in obs.fault_list:
                if fault not in rw_events:
                    prob = obs.fault_list[(fault, f_type)]
                    rw_events[fault] = [(dst_reg_name,f_type,prob)]
                else:
                    prob = obs.fault_list[(fault, f_type)]
                    rw_events[fault].append((dst_reg_name,f_type,prob))
        
        for r_event in rw_events:
            event = {"r":r_event, "w":[],"ctrl":[],"stay":[]}
            for w_event in rw_events[r_event]:
                dst_reg_name, f_type, prob = w_event
                if f_type == "data":
                    event["w"].append((dst_reg_name, prob))
                elif f_type == "ctrl":
                    event["ctrl"].append((dst_reg_name, prob))
                elif f_type == "stay":
                    event["stay"].append((dst_reg_name, prob))
                else:
                    print("Undefined W-event")
            cur_rw_events.append(event)
        return cur_rw_events

    def simulate_1_cyc(self,cyc:int):
        self.load_logic_value(cyc)
        self.load_next_logic_value(cyc+1)
        self.init_fault_list()
        #self.my_ast.show_register_fault_list()
        self.propagate()
        cur_rw_events = self.observe_fault_effect()

        self.rw_table["cycle"].append(cyc)
        self.rw_table["rw_event"].append(cur_rw_events)

    def dump_rw_table(self):
        rw_table_dir = "prob_rw_table.csv"
        df = pd.DataFrame(self.rw_table)
        df.to_csv(rw_table_dir)
        print(f"Dumped RW-table file: <{rw_table_dir}>")


    def simulate(self):
        self.preprocess()

        start_cyc = 3
        end_cyc = 485071
        for cyc in range(start_cyc,end_cyc+1):
            # simulation
            self.simulate_1_cyc(cyc)
        self.dump_rw_table()

    def simulate_test(self):
        self.preprocess()

        start_cyc = 5000
        end_cyc = 5127
        for cyc in range(start_cyc,end_cyc+1):
            # simulation
            self.simulate_1_cyc(cyc)
        self.dump_rw_table()

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(FaultSimulator.__dict__.keys()))

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)

        ast_sim = FaultSimulator(ast)
        ast_sim.simulate_test()
        #ast_sim.preprocess()
        #ast_sim.simulate_1_cyc(5127)
