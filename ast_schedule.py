from ast_checker import AstChecker
from ast_analyzer import AstAnalyzer
from ast_nodeclassify import *
from ast_modifier import *

import pprint
from copy import deepcopy
import json


class AstSchedulePreprocess:
    """ In this class, it only modifies "self.ast". """
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)
        self.checker = AstChecker(self.ast)
        self.remover = AstNodeRemover(self.ast)
        self.merger = AstNodeMerger(self.ast)
        self.marker = AstInfoMarker(self.ast)
        self.numberer = AstNumberer(self.ast)

    def preprocess(self):
        """ 
        Preprocess "self.ast" before scheduling.
            Input:  self.ast
            Output: self.ast
        """
        self.checker.check_simple_design()

        #TODO
        # split comb always block

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



class AstScheduleSubcircuit:
    def __init__(self,ast):
        """
        In this class, it makes a duplicate ast -> self.ast_schedule. 
        It will only modifies self.ast_schedule during scheduling.
        """
        self.ast = ast
        self.preprocessor = AstSchedulePreprocess(self.ast)
        self.analyzer = AstAnalyzer(self.ast)
        self.remover = AstNodeRemover(self.ast)

        self.preprocessor.preprocess()
        self.subcircuit_num = self.preprocessor.subcircuit_num


    def schedule_subcircuit(self):
        """
        Schedule <always> & <contassign>.
            Input:  self.ast_schedule
            Output: self.ordered_subcircuit_id_tail
                    self.ordered_subcircuit_id_head
        """
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

    def schedule(self):
        self.schedule_subcircuit()
        total_ast_node = 0
        for var in self.ast.findall(".//var"):
            total_ast_node += 1

    


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

        ast_scheduler = AstSchedule(ast)
        ast_scheduler.schedule()


