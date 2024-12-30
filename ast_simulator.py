from ast_sim_prepare import *

class SimulatorExecute(SimulatorPrepare):
    """
    A simulator

    Methods:
        load_ordered_varname:

        execute_comb:          visit function of "combinational subcircuit entry node"
        execute_seq:           visit function of "sequential subcircuit entry node"

        execute_rtl:           visit function of general ast subcircuit node

        compute_rtl:           visit function of "right_value circuit nodes" and "braanch condition circuit node" (for logic value propagation)
        compute_lv_rtl:        visit function of "left_value circuit nodes" (for logic value propagation)

        execute_rtl_assign:    visit function of "assignment node"
        execute_rtl_if:        visit function of "if branch"
        execute_rtl_case:      visit function of "case branch"
        execute_rtl_block:     visit function of "code block"
        execute_rtl_caseitem:  visit function of "triggered caseitem"
        trigger_rtl_condition: visit function of ""
    """
    def __init__(self,ast):
        SimulatorPrepare.__init__(self,ast)

    def execute_comb(self,node):
        lv_name = node.attrib["lv_name"]
        init_value = self.my_ast.var_node(lv_name).value
        #print(lv_name,origin_value)
        self.execute_rtl(node)
        final_value = self.my_ast.var_node(lv_name).value
        if "__Vdfg" not in lv_name and init_value != final_value:
            print(f"lv_name = {lv_name}")
            print(f"    init_value = {init_value}")
            print(f"    final_value = {final_value}")
            raise SimulationError("computed value & dumped value mismatch.",6)

    def execute_seq(self,node):
        self.execute_rtl(node)

    #------------------------------------------------------

    # RTL simulation functions
    def execute_rtl(self,node):
        if "assign" in node.tag:
            self.execute_rtl_assign(node)
        elif node.tag == "if":
            self.execute_rtl_if(node)
        elif node.tag == "case":
            self.execute_rtl_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_rtl_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def execute_rtl_assign(self,node):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_rtl(right_node)
        self.compute_lv_rtl(left_node)

        #origin_value get right value result
        value = right_node.value
        width = len(value)
        self.assign_rtl_lv(left_node, value, width, 0)


    def assign_rtl_lv(self, node, value:str, width:int, start_bit:int = 0):
        if node.tag == "sel":
            start_bit = node.children[1].value
            if "x" in start_bit:
                value = node.children[0].value
                width = len(value)
                value = "x"*width
                self.assign_rtl_lv(node.children[0], value, width, 0)
            else:
                start_bit = int(node.children[1].value,2)
                width = int(node.children[2].value,2)
                self.assign_rtl_lv(node.children[0], value, width, start_bit)
        elif node.tag == "arraysel":
            idx = int(node.children[1].value,2)
            self.assign_rtl_lv(node.children[0].node.children[idx], value, width, start_bit)
        elif node.tag == "varref":
            self.assign_rtl_lv(node.ref_node, value, width, start_bit)
        elif node.tag == "var":
            origin_value = node.value
            if start_bit == 0:
                new_value = origin_value[:-width] + value
            else:
                new_value = origin_value[:-start_bit-width] + value + origin_value[-start_bit:]
            node.value = new_value
        else:
            raise SimulationError(f"Unknown signal node to assign: tag = {node.tag}.",5)

    # normal rtl simulation
    def execute_rtl_if(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)

    def execute_rtl_case(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = node.ctrl_node.value
        for child in node.caseitems:
            if self.execute_rtl_caseitem(child,value):
                break

    def execute_rtl_block(self,node):
        for child in node.children:
            self.execute_rtl(child)

    def trigger_rtl_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            self.compute_rtl(cond)
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def execute_rtl_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_rtl_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute_rtl(child)
        return flag


    # fault list propagation rtl simulation
    def execute_rtl_if(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)

    def execute_rtl_case(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = node.ctrl_node.value
        for child in node.caseitems:
            if self.execute_rtl_caseitem(child,value):
                break

    def execute_rtl_block(self,node):
        for child in node.children:
            self.execute_rtl(child)

    def trigger_rtl_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            self.compute_rtl(cond)
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def execute_rtl_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_rtl_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute_rtl(child)
        return flag

    def compute_rtl(self,node) -> None:
        """
        visitor of all nodes under "right_value" and "control_signal".
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_rtl(child)

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

    def compute_lv_rtl(self,node) -> None:
        """
        visitor of all nodes under "left_value".
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_lv_rtl(child)

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

    def get_value(self,node):
        if type(node) is str:
            return node
        else:
            return node.value


class FaultSimulatorExecute(SimulatorPrepare):
    """
    A simulator

    Methods:
        load_ordered_varname:

        execute_comb:          visit function of "combinational subcircuit entry node"
        execute_seq:           visit function of "sequential subcircuit entry node"

        (to be removed) execute_rtl:           visit function of general ast subcircuit node
        execute_rtl_comb:      
        execute_rtl_seq:

        compute_rtl:           visit function of "right_value circuit nodes" and "braanch condition circuit node" (for logic value propagation)
        compute_lv_rtl:        visit function of "left_value circuit nodes" (for logic value propagation)

        
        execute_rtl_assign:    visit function of "assignment node"
        (to be removed) execute_rtl_if:        visit function of "if branch"
        execute_rtl_seq_if:
        execute_rtl_comb_if:

        (to be removed) execute_rtl_case:      visit function of "case branch"
        execute_rtl_seq_case:
        execute_rtl_comb_case:

        execute_rtl_block:           visit function of "code block"
        execute_rtl_seq_true_block:  
        execute_rtl_seq_false_block: 

        execute_rtl_caseitem:  visit function of "triggered caseitem"
        execute_rtl_seq_true_caseitem:
        execute_rtl_seq_false_caseitem:
        trigger_rtl_condition: visit function of
    """
    def __init__(self,ast):
        SimulatorPrepare.__init__(self,ast)

    def execute_comb(self,node):
        lv_name = node.attrib["lv_name"]
        init_value = self.my_ast.var_node(lv_name).value
        self.execute_rtl_comb(node)

        # check if the calculated result match the dumped one.
        final_value = self.my_ast.var_node(lv_name).value
        if "__Vdfg" not in lv_name and init_value != final_value:
            print(f"lv_name = {lv_name}")
            print(f"    init_value = {init_value}")
            print(f"    final_value = {final_value}")
            raise SimulationError("computed value & dumped value mismatch.",6)

    def execute_seq(self,node):
        self.execute_rtl_seq(node)
        #self.execute_df(node)

    #------------------------------------------------------

    # RTL simulation functions

    def execute_rtl_seq(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.execute_rtl_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.execute_rtl_seq_if(node,ctrl_fault)
        elif node.tag == "case":
            self.execute_rtl_seq_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_rtl_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def execute_rtl_comb(self,node,ctrl_fault:dict):
        if "assign" in node.tag:
            self.execute_rtl_assign(node,ctrl_fault)
        elif node.tag == "if":
            self.execute_rtl_comb_if(node,ctrl_fault)
        elif node.tag == "case":
            self.execute_rtl_comb_case(node,ctrl_fault)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_rtl_comb_block(node,ctrl_fault)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    def execute_rtl_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_rtl(right_node)
        self.compute_lv_rtl(left_node)

        #origin_value get right value result
        value = right_node.value
        width = len(value)
        self.assign_rtl_lv(left_node, value, width, 0)

    def execute_fault_rtl_assign(self,node,ctrl_fault:dict):
        right_node = node.rv_node
        left_node = node.lv_node

        # visit
        self.compute_rtl(right_node)
        self.compute_lv_rtl(left_node)
        self.propagate_df(right_node)
        self.propagate_lv_df(left_node)

        #origin_value get right value result
        value = right_node.value
        width = len(value)
        self.assign_rtl_lv(left_node, value, width, 0)

    def assign_rtl_lv(self, node, value:str, width:int, start_bit:int = 0):
        if node.tag == "sel":
            start_bit = node.children[1].value
            if "x" in start_bit:
                value = node.children[0].value
                width = len(value)
                value = "x"*width
                self.assign_rtl_lv(node.children[0], value, width, 0)
            else:
                start_bit = int(node.children[1].value,2)
                width = int(node.children[2].value,2)
                self.assign_rtl_lv(node.children[0], value, width, start_bit)
        elif node.tag == "arraysel":
            idx = int(node.children[1].value,2)
            self.assign_rtl_lv(node.children[0].node.children[idx], value, width, start_bit)
        elif node.tag == "varref":
            self.assign_rtl_lv(node.ref_node, value, width, start_bit)
        elif node.tag == "var":
            origin_value = node.value
            if start_bit == 0:
                new_value = origin_value[:-width] + value
            else:
                new_value = origin_value[:-start_bit-width] + value + origin_value[-start_bit:]
            node.value = new_value
        else:
            raise SimulationError(f"Unknown signal node to assign: tag = {node.tag}.",5)

    # normal rtl simulation
    def execute_rtl_if(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)
    def execute_rtl_seq_if(self,node,ctrl_fault:dict):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node,)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)
    def execute_rtl_comb_if(self,node,ctrl_fault:dict):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)

    def execute_rtl_case(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = node.ctrl_node.value
        for child in node.caseitems:
            if self.execute_rtl_caseitem(child,value):
                break

    def execute_rtl_block(self,node):
        for child in node.children:
            self.execute_rtl(child)

    def trigger_rtl_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            self.compute_rtl(cond)
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def execute_rtl_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_rtl_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute_rtl(child)
        return flag


    # fault list propagation rtl simulation
    def execute_rtl_if(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = ctrl_node.value
        if "1" in value:
            self.execute_rtl(node.true_node)
        else:
            if node.false_node == None:
                pass
            else:
                self.execute_rtl(node.false_node)

    def execute_rtl_case(self,node):
        ctrl_node = node.ctrl_node
        self.compute_rtl(ctrl_node)
        value = node.ctrl_node.value
        for child in node.caseitems:
            if self.execute_rtl_caseitem(child,value):
                break

    def execute_rtl_block(self,node):
        for child in node.children:
            self.execute_rtl(child)

    def trigger_rtl_condition(self,node,ctrl_value:str):
        flag = False
        for cond in node.conditions:
            self.compute_rtl(cond)
            if cond.value == ctrl_value:
                flag = True
                break
        return (flag or (node.conditions == []))

    def execute_rtl_caseitem(self,node,ctrl_value:str):
        flag = self.trigger_rtl_condition(node,ctrl_value)
        if flag:
            for child in node.other_children:
                self.execute_rtl(child)
        return flag

    def compute_rtl(self,node) -> None:
        """
        visitor of all nodes under "right_value" and "control_signal".
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_rtl(child)

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

    def compute_lv_rtl(self,node) -> None:
        """
        visitor of all nodes under "left_value".
        """
        width = node.width
        result = "x"*width
        for child in node.children:
            self.compute_lv_rtl(child)

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
    def execute_df(self,node):
        if "assign" in node.tag:
            self.execute_df_assign(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    # Control fault propagation
    #
    def execute_seq_cf(self,node):
        if "assign" in node.tag:
            self.execute_seq_cf_assign(node)
        elif node.tag == "if":
            self.execute_seq_cf_if(node)
        elif node.tag == "case":
            self.execute_seq_cf_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_seq_cf_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)

    #------------------------------------------------------

    # Control fault propagation
    #
    def execute_comb_cf(self,node):
        if "assign" in node.tag:
            self.execute_comb_cf_assign(node)
        elif node.tag == "if":
            self.execute_comb_cf_if(node)
        elif node.tag == "case":
            self.execute_comb_cf_case(node)
        elif node.tag == "begin" or node.tag == "always":
            self.execute_comb_cf_block(node)
        else:
            raise SimulationError(f"Unknown node to execute: tag = {node.tag}.",0)
    #------------------------------------------------------

    def get_value(self,node):
        if type(node) is str:
            return node
        else:
            return node.value
    




class Simulator(SimulatorExecute):
    def __init__(self,ast):
        SimulatorExecute.__init__(self,ast)
        self.dumper = AstDumpSimulatorSigList(self.ast)

    def propagate(self):
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_head:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.execute_comb(entry_node)
        for subcircuit_id in self.my_ast.ordered_subcircuit_id_tail:
            entry_node = self.my_ast.subtreeroot_node(subcircuit_id)
            self.execute_seq(entry_node)

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

