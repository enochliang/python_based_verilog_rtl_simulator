from ast_checker import AstChecker
from ast_analyzer import AstAnalyzer
from ast_nodeclassify import *

import pprint
from copy import deepcopy
import json


class AstDump:
    def __init__(self,ast):
        self.ast = ast

    def output(self,ast):
        with open("output.xml","w") as fp:
            fp.write(etree.tostring(ast.find("."),pretty_print=True).decode())

class AstNodeRemover:
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)

    def remove_integer(self):
        for var in self.ast.findall(".//module/var"):
            basicdtype_name = self.analyzer.get_basic_dtypename__node(var)
            if basicdtype_name == "integer":
                self.remove_ast_node(var)

    def remove_initial(self):
        for initial in self.ast.findall(".//initial"):
            self.remove_ast_node(initial)

    def remove_comment_node(self):
        for comment in self.ast.findall(".//comment"):
            self.remove_ast_node(comment)

    def remove_empty_initial(self):
        for initial in self.ast.findall(".//initial"):
            if len(initial.getchildren()) == 0:
                self.remove_ast_node(initial)

    def remove_param_var(self):
        for var in self.ast.findall(".//var"):
            if "param" in var.attrib:
                self.remove_ast_node(var)
            elif "localparam" in var.attrib:
                self.remove_ast_node(var)

    def remove_sentree(self):
        for always in self.ast.findall(".//always"):
            sentree = always.find(".//sentree")
            if sentree != None:
                self.remove_ast_node(sentree)

    def remove_ast_node(self,node):
        node.getparent().remove(node)




class AstNodeMerger:
    def __init__(self,ast):
        self.ast = ast
        self.remover = AstNodeRemover(self.ast)
        self.analyzer = AstAnalyzer(self.ast)

    def merge_multi_name_var(self):
        # Merge the <varref> that have different names but refer to same signal
        # Unify their names
        print("[AST Schedule Preprocess] start merging multi-named signals...")
        signal_merge_dict = dict()
        signal_buckets = list()

        analyzer = AstAnalyzer(self.ast)
        input_set = set(analyzer.get_sig__input_port())
        lv_signal_set = set(analyzer.get_sig__lv())

        all_signal_set = input_set | lv_signal_set

        for assignalias in self.ast.findall(".//topscope//assignalias"):
            v1 = assignalias.getchildren()[0].attrib["name"]
            v2 = assignalias.getchildren()[1].attrib["name"]
            bucket_idx = [i for i,s in enumerate(signal_buckets) if (v1 in s or v2 in s)]
            bucket_idx = bucket_idx if bucket_idx == [] else bucket_idx[0]
            if bucket_idx == []:
                i = len(signal_buckets)
                signal_buckets.append(set())
                signal_buckets[i].add(v1)
                signal_buckets[i].add(v2)
            else:
                signal_buckets[bucket_idx].add(v1)
                signal_buckets[bucket_idx].add(v2)
        for i,s in enumerate(signal_buckets):
            main_signal = [v for v in s if v in all_signal_set][0]
            signal_merge_dict[main_signal] = s

        # Merging Node with Same Name
        for main_sig in signal_merge_dict:
            self._show_merge_info(main_sig,signal_merge_dict[main_sig])
            for sig in signal_merge_dict[main_sig]:
                # Remove <varscope>
                if sig != main_sig:
                    for varref in self.ast.findall(f".//varref[@name='{sig}']"):
                        varref.attrib["name"] = main_sig
                    varscope = self.ast.find(f".//topscope//varscope[@name='{sig}']")
                    self.remover.remove_ast_node(varscope)
                    var = self.ast.find(f".//var[@name='{sig}']")
                    self.remover.remove_ast_node(var)
        print("-"*80)

    def _show_merge_info(self,main_sig, merge_sig):
        indent = len(f"  - merging: {main_sig} <= ")
        for idx, sig in enumerate(merge_sig):
            if idx == 0:
                print(f"  - merging: {main_sig} <= {sig}")
            else:
                print(" "*indent+f"{sig}")
        print()

    def merge_initial_var_const(self):
        for init_assign in self.ast.findall(".//initial/assign"):
            lv_node = init_assign.getchildren()[1]
            lv_name = lv_node.attrib["name"]
            rv_node = init_assign.getchildren()[0]
            for varref in self.ast.findall(f".//varref[@name='{lv_name}']"):
                varref.getparent().replace(varref,rv_node)
            for var in self.ast.findall(f".//var[@name='{lv_name}']"):
                self.remover.remove_ast_node(var)
            for varscope in self.ast.findall(f".//topscope//varscope[@name='{lv_name}']"):
                self.remover.remove_ast_node(varscope)


class AstInfoMarker:
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)

    def mark_var_sig_type(self):
        register_name_set = set(self.analyzer.get_sig__ff())
        for var in self.ast.findall(".//var"):
            var_name = var.attrib["name"]
            if var_name in register_name_set:
                var.attrib["sig_type"] = "register"
            else:
                var.attrib["sig_type"] = "wire"

    def mark_comb_subcircuit_lv_name(self):
        self.mark_wireassign_lv_name()
        self.mark_comb_always_lv_name()

    def mark_wireassign_lv_name(self):
        for contassign in self.ast.findall(".//contassign"):
            lv_node = contassign.getchildren()[1]
            lv_sig_name = self.analyzer.get_sig_name(lv_node)
            contassign.attrib["lv_name"] = lv_sig_name

    def mark_comb_always_lv_name(self):
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") != None:
                continue
            assign = always.find(".//assign")
            lv_node = assign.getchildren()[1]
            lv_sig_name = self.analyzer.get_sig_name(lv_node)
            always.attrib["lv_name"] = lv_sig_name

    def mark_always_type(self):
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") != None:
                always.attrib["type"] = "ff"
            else:
                always.attrib["type"] = "comb"

    def mark_width(self):
        dtypeid_2_width_dict = self.analyzer.get_dict__dtypeid_2_width()
        for node in self.ast.iter():
            if "dtype_id" in node.attrib:
                dtype_id = node.attrib["dtype_id"]
                node.attrib["width"] = str(dtypeid_2_width_dict[dtype_id])

class AstNumberer:
    def __init__(self,ast):
        self.ast = ast

    def numbering_subcircuit(self) -> int: 
        print("[AST Schedule Preprocess] start numbering subcircuits...")
        self.subcircuit_num = 0
        for sub_circuit in self.ast.findall(".//contassign") + self.ast.findall(".//always"):
            sub_circuit.attrib["subcircuit_id"] = str(self.subcircuit_num)
            self.subcircuit_num += 1
        print(f"  - finished. total number of subcircuit = {self.subcircuit_num}")
        print("-"*80)
        return self.subcircuit_num

    #def numbering_assignment(self):
    #    print("[AST Schedule Preprocess] start numbering assignment...")
    #    self.assignment_num = 0
    #    for assign in self.ast.findall(".//contassign") + self.ast.findall(".//always//assign") + self.ast.findall(".//always//assigndly"):
    #        assign.attrib["assignment_id"] = str(self.assignment_num)
    #        self.assignment_num += 1
    #    print(f"  - finished. total number of assignment = {self.assignment_num}")
    #    print("-"*80)


    #def numbering_circuit_node(self):
    #    print("[AST Schedule Preprocess] start numbering circuit node...")
    #    self.circuit_node_num = 0
    #    self.numbering_var_node()
    #    self.numbering_ctrl_node()
    #    self.numbering_op_node()
    #    print(f"  - finished. total number of circuit node = {self.circuit_node_num}")
    #    print("-"*80)

    #def numbering_var_node(self):
    #    for var in self.ast.findall(".//module//var"):
    #        var.attrib["circuit_node_id"] = str(self.circuit_node_num)
    #        var_name = var.attrib["name"]
    #        # Also give node id to all of its <varref>
    #        for varref in self.ast.findall(f".//varref[@name='{var_name}']"):
    #            varref.attrib["circuit_node_id"] = str(self.circuit_node_num)
    #        self.circuit_node_num += 1

    #def numbering_ctrl_node(self):
    #    for if_node in self.ast.findall(".//always//if"):
    #        ctrl_node = if_node.getchildren()[0]
    #        for node in ctrl_node.iter():
    #            if node.tag != "varref":
    #                node.attrib["circuit_node_id"] = str(self.circuit_node_num)
    #                self.circuit_node_num += 1

    #def numbering_op_node(self):
    #    for assign in self.ast.findall(".//contassign") + self.ast.findall(".//always//assign") + self.ast.findall(".//always//assigndly"):
    #        for node in assign.iter():
    #            if (not "assign" in node.tag) and node.tag != "varref":
    #                node.attrib["circuit_node_id"] = str(self.circuit_node_num)
    #                self.circuit_node_num += 1

class AstModifier(AstNodeRemover,AstNodeMerger,AstInfoMarker,AstNumberer):
    def __init__(self,ast):
        AstModifier.super().__init__(self,ast)
        self.ast = ast




class AstSchedulePreprocess:
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)
        self.checker = AstChecker(self.ast)
        self.remover = AstNodeRemover(self.ast)
        self.merger = AstNodeMerger(self.ast)
        self.marker = AstInfoMarker(self.ast)
        self.numberer = AstNumberer(self.ast)

    def proc(self):
        self.preprocess()

    def preprocess(self):
        self.checker.check_simple_design()

        self.remover.remove_comment_node()
        self.remover.remove_integer()
        self.remover.remove_empty_initial()
        self.remover.remove_param_var()

        self.merger.merge_multi_name_var()
        self.merger.merge_initial_var_const()

        self.marker.mark_var_sig_type()
        self.marker.mark_comb_subcircuit_lv_name()
        self.marker.mark_always_type()
        self.marker.mark_width()

        self.remover.remove_sentree()

        self.subcircuit_num = self.numberer.numbering_subcircuit()




    #def find_register_var(self):
    #    return self.analyzer.get_sig__ff()

    #def find_input_var(self):
    #    return self.analyzer.get_sig__input_port()

    #def _find_dst_var_node(self,lv_node):
    #    if lv_node.tag == "arraysel" or lv_node.tag == "sel":
    #        target_node = lv_node.getchildren()[0]
    #        return self.analyzer.get_sig_node(target_node)
    #    elif lv_node.tag == "varref":
    #        return lv_node
    #    else:
    #        raise Unconsidered_Case(f"node tag = {lv_node.tag}",0)


class AstScheduleSubcircuit:
    def __init__(self,ast):
        self.ast = ast
        self.preproc = AstSchedulePreprocess(self.ast)
        self.analyzer = AstAnalyzer(self.ast)
        self.remover = AstNodeRemover(self.ast)
        self.preproc.preprocess()
        self.subcircuit_num = self.preproc.subcircuit_num

    def proc(self):
        self.schedule_subcircuit()
        total_ast_node = 0
        for var in self.ast.findall(".//var"):
            total_ast_node += 1

    def schedule_subcircuit(self):
        self.ast_schedule = deepcopy(self.ast)
        self.subcircuit_id_list = [subcircuit_id for subcircuit_id in range(self.subcircuit_num)]
        self.ordered_subcircuit_id_list = []
        self.ordered_subcircuit_id_tail = []
        self.ordered_subcircuit_id_head = []

        self._schedule_ff_always()
        self._schedule_comb_subcircuit()
        print(f"finished. total scheduled subcircuit number = {len(self.ordered_subcircuit_id_list)}")

    def _schedule_ff_always(self):
        for always in self.ast_schedule.findall(".//always[@type='ff']"):
            subcircuit_id = int(always.attrib["subcircuit_id"])
            self.subcircuit_id_list.remove(subcircuit_id)
            self.ordered_subcircuit_id_tail.append(subcircuit_id)

    def _schedule_comb_subcircuit(self):
        self._remove_comb_dst_var_node()
        self._remove_ctrl_register()
        self._remove_src_register()
        self._remove_ctrl_input_port()
        self._remove_src_input_port()
        self._remove_comb_lv_on_the_right()
        while(self.subcircuit_id_list != []):
            new_ready_subcircuit_list = self._find_ready_subcircuit()
            self._update_ready_node(new_ready_subcircuit_list)
            self._remove_ready_node(new_ready_subcircuit_list)

        self.ordered_subcircuit_id_head = self.ordered_subcircuit_id_list
        self.ordered_subcircuit_id_list = self.ordered_subcircuit_id_list + self.ordered_subcircuit_id_tail


    def _remove_ready_node(self,ready_subcircuit_list):
        ready_sig_name_set = set([ready_subcircuit[1] for ready_subcircuit in ready_subcircuit_list])
        for subcircuit_id in self.subcircuit_id_list:
            subcircuit = self.ast_schedule.find(f".//*[@subcircuit_id='{subcircuit_id}']")
            for varref in subcircuit.findall(".//varref"):
                var_name = varref.attrib["name"]
                if var_name in ready_sig_name_set:
                    self.remover.remove_ast_node(varref)
    

    def _remove_comb_dst_var_node(self):
        for assign in self.ast_schedule.findall(".//contassign") + self.ast_schedule.findall(".//always//assign"):
            lv_node = assign.getchildren()[1]
            dst_var_node = self.analyzer.get_sig_node(lv_node)
            self.remover.remove_ast_node(dst_var_node)

    def _remove_ctrl_input_port(self):
        input_name_set = set(self.analyzer.get_sig__input_port())
        for input_name in input_name_set:
            for varref in self.ast_schedule.findall(f".//always//varref[@name='{input_name}']"):
                if not "assign" in self.ast_schedule.getpath(varref):
                    self.remover.remove_ast_node(varref)

    def _remove_src_input_port(self):
        input_name_set = set(self.analyzer.get_sig__input_port())
        for assign in self.ast_schedule.findall(".//contassign") + self.ast_schedule.findall(".//always//assign"):
            for varref in assign.findall(".//varref"):
                var_name = varref.attrib["name"]
                if var_name in input_name_set:
                    self.remover.remove_ast_node(varref)

    def _remove_ctrl_register(self):
        register_name_set = set(self.analyzer.get_sig__ff())
        for register_name in register_name_set:
            for varref in self.ast_schedule.findall(f".//always//varref[@name='{register_name}']"):
                if not "assign" in self.ast_schedule.getpath(varref):
                    self.remover.remove_ast_node(varref)

    def _remove_src_register(self):
        register_name_set = set(self.analyzer.get_sig__ff())
        for assign in self.ast_schedule.findall(".//contassign") + self.ast_schedule.findall(".//always//assign"):
            for varref in assign.findall(".//varref"):
                var_name = varref.attrib["name"]
                if var_name in register_name_set:
                    self.remover.remove_ast_node(varref)

    def _remove_comb_lv_on_the_right(self):
        for always in self.ast_schedule.findall(".//always[@type='comb']"):
            lv_name = always.attrib["lv_name"]
            for varref in always.findall(f".//varref[@name='{lv_name}']"):
                self.remover.remove_ast_node(varref)

    def _find_ready_subcircuit(self):
        new_ready_subcircuit_list = []
        for subcircuit_id in self.subcircuit_id_list:
            subcircuit = self.ast_schedule.find(f".//*[@subcircuit_id='{str(subcircuit_id)}']")
            if subcircuit.tag == "always" and subcircuit.attrib["type"] == "ff":
                continue
            if subcircuit.find(".//varref") == None:
                subcircuit_id = int(subcircuit.attrib["subcircuit_id"])
                lv_name = subcircuit.attrib["lv_name"]
                new_ready_subcircuit_list.append((subcircuit_id,lv_name))
        return new_ready_subcircuit_list

    def _update_ready_node(self,ready_subcircuit_list):
        ready_subcircuit_id_list = [ready_subcircuit[0] for ready_subcircuit in ready_subcircuit_list]
        for ready_subcircuit_id in ready_subcircuit_id_list:
            self.subcircuit_id_list.remove(ready_subcircuit_id)
            self.ordered_subcircuit_id_list.append(ready_subcircuit_id)


class AstSchedule(AstScheduleSubcircuit):
    def __init__(self,ast):
        AstScheduleSubcircuit.__init__(self,ast)


    


if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument("ast", type=str, help="AST path")                  # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    ast_file = args.ast
    ast = Verilator_AST_Tree(ast_file)


    ast_scheduler = AstSchedule(ast)
    ast_scheduler.output()


