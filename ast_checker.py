from ast_analyzer import *
import argparse

class Unwanted_Coding_Style(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"


class AstChecker(AstAnalyzer):

    def __init__(self, ast: etree._ElementTree):
        AstAnalyzer.__init__(self,ast)


    def _get_info(self):
        pprint.pp(self.__dir__())


    def _show_loc_info(self,node):
        # Input:  lxml node
        # Output: the location of statement in the RTL code
        if "loc" in node.attrib:
            loc = node.attrib["loc"]
            _file = loc.split(",")[0]
            _file = self.ast.find(f".//file[@id='{_file}']").attrib["filename"]
            n_line = loc.split(",")[1]
            print(f"    File = {_file}, at line {n_line}.")


    def _ast_preprocess(self):
        self._remove_comment_node()
        self._remove_empty_initial()

    def _remove_comment_node(self):
        for comment in self.ast.findall(".//comment"):
            comment.getparent().remove(comment)

    def _remove_empty_initial(self):
        for initial in self.ast.findall(".//initial"):
            if len(initial.getchildren()) == 0:
                initial.getparent().remove(initial)

    def _check_circuit_flattened(self):
        print("[Checker Task] start checking the ast is flattened...")
        if self.ast_flattened():
            print("  - [Checker Report] pass!")
        else:
            print("  - [Checker Report] warning the ast is not flattened.")
        print("-"*80)

    def _check_circuit_no_voiddtype(self):
        print("[Checker Task] start checking that there are no voiddtype variable in the circuit...")
        flag = False
        void_d_type = self.ast.find(".//basicdtype/voiddtype")
        if void_d_type != None:
            type_id = void_d_type.attrib["id"]
            for always in self.ast.findall(".//always"):
                for node in always.iter():
                    if "dtype_id" in node.attrib and node.attrib["dtype_id"] == type_id:
                        print("  - [Checker Report] warning: found a voiddtype variable in the circuit.")
                        self._show_loc_info(node)
                        flag = True
            for contassign in self.ast.findall(".//contassign"):
                for node in contassign.iter():
                    if "dtype_id" in node.attrib and node.attrib["dtype_id"] == type_id:
                        print("  - [Checker Report] warning: found a voiddtype variable in the circuit.")
                        self._show_loc_info(node)
                        flag = True
        else:
            pass
        if not flag:
            print("  - [Checker Report] pass: no voiddtype variable in the circuit.")
        print("-"*80)

    def _check_circuit_no_taskref(self):
        print("[Checker Task] start checking that there are no <taskref> in the circuit...")
        flag = False
        for always in self.ast.findall(".//always"):
            for node in always.iter():
                if node.tag == "taskref":
                    print("  - [Checker Report] warning: found a <taskref> in the circuit.")
                    self._show_loc_info(node)
                    flag = True
        for contassign in self.ast.findall(".//contassign"):
            for node in contassign.iter():
                if node.tag == "taskref":
                    print("  - [Checker Report] warning: found a <taskref> in the circuit.")
                    self._show_loc_info(node)
                    flag = True
        if not flag:
            print("  - [Checker Report] pass: no <taskref> in the circuit.")
        print("-"*80)

    def _check_circuit_no_funcref(self):
        print("[Checker Task] start checking that there are no <funcref> in the circuit...")
        flag = False
        for always in self.ast.findall(".//always"):
            for node in always.iter():
                if node.tag == "funcref":
                    print("  - [Checker Report] warning: found a <funcref> in the circuit.")
                    self._show_loc_info(node)
                    flag = True
        for contassign in self.ast.findall(".//contassign"):
            for node in contassign.iter():
                if node.tag == "funcref":
                    print("  - [Checker Report] warning: found a <funcref> in the circuit.")
                    self._show_loc_info(node)
                    flag = True
        if not flag:
            print("  - [Checker Report] pass: no <funcref> in the circuit.")
        print("-"*80)

    def check_dtype(self,output=True) -> set:
        # Make a List of Packed dtype That Doesn't Start With Zero Bit.
        dtypes = set()
        for dtype in self.ast.findall(".//basicdtype"):
            if "right" in dtype.attrib:
                if not dtype.attrib["right"] == "0":
                    dtypes.add((("id",dtype.attrib["id"]),("left",dtype.attrib["left"]),("right",dtype.attrib["right"])))
        if output:
            print("Print Packed dtype That Doesn't Start With Zero Bit.")
            for dtype in dtypes:
                print(dtype)
        return dtypes


    def check_tag_all_x_are_under_y(self,x:str,y:str):
        target_nodes = self.ast.findall(".//"+x)
        flag = False
        for x_node in target_nodes:
            if not y in self.ast.getpath(x_node):
                print("Found a <"+x+"> not under <"+y+">")
                flag = True
        if not flag:
            print("ALL <"+x+"> are under <"+y+">")

    def _check_ff_always_only_1_block_triggered(self):
        lv_set = set()
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") == None:
                continue
            
    def _check_ff_always_no_blking_assign(self):
        print("[Checker Task] start Checking No Blocking Assignment in Clock Triggered Always Block...")
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") == None:
                continue
            for assign in always.findall(".//assign"):
                print("  - [Checker Report] warning: found a <assign> under clock triggered always block.")
                self._show_loc_info(assign)
        self._show_ff_always_seq_signal()
        print("-"*80)

    def _show_ff_always_seq_signal(self):
        for always in [always for always in self.ast.findall(".//always") if not (always.find(".//sentree") is None)]:
            # Find out all left signals of blocking assignment.
            blk_lv_var_set = set()
            for assign in always.findall(".//assign"):
                for lv_var in [var.attrib["name"] for var in assign.getchildren()[1].iter() if var.tag == "varref"]:
                    blk_lv_var_set.add(lv_var)

            if blk_lv_var_set == set():
                continue
            else:
                print("Signals assigned by blocking assignment = ")
                pprint.pp(blk_lv_var_set)

            # Find out dependent signals of those signals we found in the above part
            dependent_var_set = set()
            # The target signals on the right of assignment
            for assign in always.findall(".//assign") + always.findall(".//assigndly"):
                if set([var.attrib["name"] for var in assign.getchildren()[0].iter() if (var.tag == "varref") and (var.attrib["name"] in blk_lv_var_set)]) != set():
                    dependent_var_set = dependent_var_set | set([var.attrib["name"] for var in assign.getchildren()[1].iter() if (var.tag == "varref")])
            # The target signals in the control signal of branches (case & if)
            for branch_node in always.findall(".//case") + always.findall(".//if"):
                if set([var for var in branch_node.getchildren()[0].iter() if (var.tag == "varref") and (var.attrib["name"] in blk_lv_var_set)]) != set():
                    for assign in branch_node.findall(".//assign") + branch_node.findall(".//assigndly"):
                        dependent_var_set = dependent_var_set | set([var.attrib["name"] for var in assign.getchildren()[1].iter() if (var.tag == "varref")])
            # The target signals in the control signal of (case(1'b1))
            for case_node in always.findall(".//case"):
                if case_node.getchildren()[0].tag != "const":
                    continue
                else:
                    dep_case_flag = False
                    for caseitem_node in case_node.findall(".//caseitem"):
                        if len(caseitem_node.getchildren()) > 0 and caseitem_node.getchildren()[0].tag in {"assign","assigndly","if","case"}:
                            continue
                        else:
                            if len(caseitem_node.getchildren()) > 0 and set([var for var in caseitem_node.getchildren()[0].iter() if (var.tag == "varref") and (var.attrib["name"] in blk_lv_var_set)]) != set():
                                dep_case_flag = True
                                break
                    if dep_case_flag:
                        for assign in case_node.findall(".//assign") + case_node.findall(".//assigndly"):
                             dependent_var_set = dependent_var_set | set([var.attrib["name"] for var in assign.getchildren()[1].iter() if (var.tag == "varref")])

            # Find out the signals that are not dependent to the signals
            lv_var_set = set()
            for assign in always.findall(".//assign") + always.findall(".//assigndly"):
                for lv_var in [var.attrib["name"] for var in assign.getchildren()[1].iter() if var.tag == "varref"]:
                    lv_var_set.add(lv_var)
            
            print("Dependent Signals = ")
            pprint.pp(dependent_var_set)

            # Construct a Dependency Dict
            dep_dict = {}
            for assign in always.findall(".//assigndly"):
                cur_lv_var_set = set([var for var in assign.getchildren()[1].iter() if var.tag == "varref"])
                cur_blk_lv_var_set = set([var for var in assign.getchildren()[1].iter() if var.tag == "varref" and var.attrib["name"] in blk_lv_var_set])
                for blk_lv_var in cur_blk_lv_var_set:
                    if blk_lv_var in dep_dict:
                        for lv_var in cur_blk_lv_var_set:
                            dep_dict[blk_lv_var].add(lv_var)
                    else:
                        dep_dict[blk_lv_var] = cur_blk_lv_var_set
            #for case_node in always.findall(".//case"):

            print("Dependency Dictionary = ")
            pprint.pp(dep_dict)
                    
            print("Signals Can be Moved Out = ")
            pprint.pp(lv_var_set - dependent_var_set - blk_lv_var_set)

    def _check_circuit_no_loop(self):
        print("[Checker Task] start checking no loop in the circuit...")
        while_nodes = self.ast.findall(".//while")
        for while_node in while_nodes:
            print("  - [Checker Report] warning: found a <while> in the circuit.")
            self._show_loc_info(while_node)
        if len(while_nodes) == 0:
            print("  - [Checker Report] pass: no <while> in the circuit.")
        print("-"*80)


    #def _check_no_array(self):
    #    print("[Checker Task] start Checking No Array in The Design...")
    #    if not self.ast.find(".//arraysel") == None:
    #        print("  - [Checker Report] warning: found an <arraysel>.")
    #        array_name = self.ast.find(".//arraysel").getchildren()[0].attrib["name"]
    #        self._show_loc_info(self.ast.find(".//arraysel"))
    #        raise Unwanted_Coding_Style(f"  Array Name = {array_name}",0)
    #    else:
    #        print("Pass: No Array in Design.")
    #    print("-"*80)


    #def _check_sel_no_muxdec(self):
    #    print("[Checker Task] start Checking No MUX or DEC in <sel>...")
    #    flag = False
    #    for sel in self.ast.findall(".//sel"):
    #        # Check if there is a variable in the bit selection braket.
    #        if not [c.tag for c in sel.getchildren()][1:] == ["const","const"]:
    #            print("  Warning: Found a <sel> with MUX or DEC!")
    #            self._show_loc_info(sel)
    #            sel_ctrl_signal = sel.getchildren()[1].find(".//varref").attrib["name"]
    #            print(f"    The variable in side bit selection braket = {sel_ctrl_signal}")
    #            flag = True
    #    if not flag:
    #        print("Pass: No MUX or DEC in <sel>")
    #    print("-"*80)

    def _check_assign_no_concat_lv(self):
        """Check all left value of assignment. 
        All of them should be a single <varref> on the left."""
        print("[Checker Task] start checking Left Side of Assignment is not a <concat>...")
        assignments = self.ast.findall(".//assign") + self.ast.findall(".//assigndly") + self.ast.findall(".//contassign")
        flag = False
        for assign in assignments:
            lv = assign.getchildren()[1]
            tag = lv.tag
            if tag == "concat":
                print("  - [Checker Report] warning: found a <concat> on the left of assignment!")
                self._show_loc_info(lv)
                flag = True
        if not flag:
            print("  - [Checker Report] pass: All Left Values are Single <varref>")
        print("-"*80)

    #def _check_lv_single_var(self):
    #    """Check all left value of assignment. 
    #    All of them should be a single <varref> on the left."""
    #    print("[Checker Task] start Checking Left Side of Assignment is A Single <varref>...")
    #    assignments = self.ast.findall(".//assign") + self.ast.findall(".//assigndly") + self.ast.findall(".//contassign")
    #    flag = False
    #    for assign in assignments:
    #        lv = assign.getchildren()[1]
    #        tag = lv.tag
    #        if not tag == "varref":
    #            print("  Warning: Found a Left Value Not a Single <varref>!")
    #            print("    Tag = "+tag)
    #            self._show_loc_info(lv)
    #            if tag == "sel":
    #                print(f'    var = {assign.getchildren()[1].getchildren()[0].attrib["name"]}')
    #            flag = True
    #    if not flag:
    #        print("Pass: All Left Values are Single <varref>")
    #    print("-"*80)




    #def _check_lv_only_left(self):
    #    print("[Checker Task] start Checking No Sequantial-Assignments Always-Block \n(All Left-Value Signals Should Be On the Left of Assignment in An Always-Block)...")
    #    for assign in self.ast.findall(".//always//assign") + self.ast.findall(".//always//assigndly"):
    #        assign.getchildren()[1].attrib["LV"] = "true"
    #    flag = False
    #    for always in self.ast.findall(".//always"):
    #        lv_set = set()
    #        for assign in always.findall(".//assign") + always.findall(".//assigndly"):
    #            lv_set.add(assign.getchildren()[1].attrib["name"])

    #        for node in always.iter():
    #            if(node.tag == "varref" and node.attrib["name"] in lv_set):
    #                if("LV" in node.attrib):
    #                    pass
    #                else:
    #                    print("  Warning: Found Left Value on the Right Side of Assignment.")
    #                    print("    Variable Name = "+node.attrib["name"])
    #                    flag = True
    #    if not flag:
    #        print("Pass: Left-Values Only on the Left of Assignment.")
    #    print("-"*80)

    def _check_ff_always_no_sel_lv(self):
        print("[Checker Task] start checking no bit selection on the left of <assigndly>")
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") == None:
                continue
            for assign in always.findall(".//assigndly"):
                if assign.getchildren()[1].tag == "sel":
                    print("  - [Checker Report] warning: found a <sel> on the left of <assigndly>.")
                    lv_name = AstAnalyzer.get_sig_name(assign.getchildren()[1])
                    print(f"    lv-name = {lv_name}")
                    self._show_loc_info(assign.getchildren()[1])


    #def _check_ff_always_only_one_lv(self):
    #    print("[Checker Task] start checking each sequential <always> only has 1 Left-Value...")
    #    flag = False
    #    for always in self.ast.findall(".//always"):
    #        if always.find(".//sentree") == None:
    #            continue
    #        lv_set = set()
    #        for assign in always.findall(".//assign") + always.findall(".//assigndly"):
    #            for lv_var in assign.getchildren()[1].findall(".//varref"):
    #                name = lv_var.attrib["name"]
    #                lv_set.add(name)
    #        if len(lv_set) > 1:
    #            print("  Warning: More than 1 Left-Value in the <always>")
    #            print("    LVs in this <always> = ")
    #            pprint.pp(lv_set)
    #            flag = True
    #    if not flag:
    #        print("Pass: Each FF <always> only has 1 Left-Value")
    #    print("-"*80)

    def _check_always_begin_end(self):
        print("[Checker Task] start checking code block has <begin...end> ...")
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") != None:
                if always.getchildren()[1].tag != "begin":
                    print("  - [Checker Report] warning: found an <always> doesn't have <begin...end>.")
                    self._show_loc_info(always)
            else:
                if always.getchildren()[0].tag != "begin":
                    print("  - [Checker Report] warning: found an <always> doesn't have <begin...end>.")
                    self._show_loc_info(always)



    def _check_comb_always_only_one_lv(self):
        print("[Checker Task] start checking each combinational <always> only has 1 Left-Value...")
        flag = False
        for always in self.ast.findall(".//always"):
            if always.find(".//sentree") != None:
                continue
            lv_set = set()
            for assign in always.findall(".//assign"):
                name = AstAnalyzeFunc.get_sig_name(assign.getchildren()[1])
                lv_set.add(name)

            if len(lv_set) > 1:
                print("  - [Checker Report] warning: found more than 1 left-value in the <always>.")
                print("    left-values in this <always> = ")
                pprint.pp(lv_set)
                self._show_loc_info(always)
                flag = True

        if not flag:
            print("  - [Checker Report] pass: each comb <always> only has 1 left-value.")
        print("-"*80)


    #def _check_ff_always_fullcase(self):
    #    print("[Checker Task] start checking each sequential <always> is FULLCASE...")
    #    flag = False
    #    for always in self.ast.findall(".//always"):
    #        if always.find(".//sentree") == None:
    #            continue
    #        child = [i.tag for i in always.getchildren()]
    #        if "if" in child or "case" in child:
    #            if "assign" in child:
    #                print("  Warning: Always not fullcase")
    #                self._show_loc_info(always.find("assign"))
    #                flag = True
    #    if not flag:
    #        print("Pass: Each FF <always> is FULLCASE")
    #    print("-"*80)


    #def _check_comb_always_no_seq_assign(self):
    #    print("[Checker Task] start checking no sequential assignments under each combinational <always>...")
    #    flag = False
    #    for always in self.ast.findall(".//always"):
    #        if always.find(".//sentree") != None:
    #            continue
    #        child = [i.tag for i in always.getchildren()]
    #        if "if" in child or "case" in child:
    #            if "assign" in child:
    #                print("  Warning: Found Sequential Assignments.")
    #                loc = always.find("assign").attrib["loc"]
    #                file_id = loc.split(",")[0]
    #                loc = ",".join(loc.split(",")[1:])
    #                print("    Assignment: "+self.ast.find(".//files//file[@id='"+file_id+"']").attrib["filename"]+","+loc)
    #                flag = True
    #        for block in always.findall(".//begin") + always.findall(".//caseitem"):
    #            if len(block.findall("./if") + block.findall("./case")) > 1:
    #                print("  Warning: Found Multiple <if> or <case> under <begin>")
    #                print(f"    Always Block: {always.attrib}")
    #                flag = True
    #    if not flag:
    #        print("Pass: Each Comb <always> is FULLCASE")
    #    print("-"*80)


    #def _check_comb_always_fullcase(self):
    #    print("[Checker Task] start checking each combinational <always> is FULLCASE...")
    #    for always in self.ast.findall(".//always"):
    #        if always.find(".//sentree") != None:
    #            continue
    #        for branch in always.findall(".//if") + always.findall(".//case"):
    #            if branch.tag == "if":
    #                if len(branch.getchildren()) < 3:
    #                    print("    Branch Tag = <if>")
    #                    self._show_loc_info(branch)
    #                    
    #                    #raise RTL_Coding_Style_Warning("Found a <if> without <else> case item.",1)
    #            if branch.tag == "case":
    #                last_item = branch.getchildren()[-1]
    #                ctrl_dtype = branch.getchildren()[0].attrib["dtype_id"]
    #                dtype = self.ast.find(f".//basicdtype[@id='{ctrl_dtype}']")
    #                if "left" in dtype.attrib:
    #                    width = int(dtype.attrib["left"]) - int(dtype.attrib["right"]) + 1
    #                    fullcase_num = pow(2,width)
    #                else:
    #                    fullcase_num = 2
    #                
    #                if len(last_item.getchildren()) != 1: # The <case> doesn't have a <default> under it.
    #                    if len(branch.findall("./caseitem/const")) < fullcase_num: # The <case> has less than fullcase_num of <caseitem> under it.
    #                        print("    Branch Tag = <case>")
    #                        self._show_loc_info(branch)
    #                        #raise RTL_Coding_Style_Warning("Found a <case> without <default> case item, and not full case.",1)
    #                    
    #    print("Pass: Each Comb <always> is FULLCASE")
    #    print("-"*80)

    def _check_assign_no_param(self):
        print("[Checker Task] start checking no parameter under assignments...")
        flag = False
        for assign in self.ast.findall(".//contassign") + self.ast.findall(".//assignalias") + self.ast.findall(".//always//assign") + self.ast.findall(".//always//assigndly"):
            for var in assign.findall(".//varref"):
                if "param" in var.attrib or "localparam" in var.attrib:
                    print("Warning: Found Parameter under assignment!")
                    print("  parameter = "+var.attrib["name"])
                    flag = True

        if not flag:
            print("Pass: No parameter under assignments")
        print("-"*80)


    #def _check_non_blocking_always_assignment(self):
    #    print("[Checker Task] start checking each non-blocking <always> only has <assigndly> in it...")
    #    flag = False
    #    for sentree in self.ast.findall(".//always/sentree"):
    #        nonblk_always = sentree.getparent()
    #        assign = nonblk_always.find(".//assign")
    #        if assign != None:
    #            print("  Warning: Found a <assign> in Non-blocking <always>.")
    #            flag = True
    #    if not flag:
    #        print("Pass: All Assignment in non-blocking <always> is <assigndly>")
    #    print("-"*80)


    #def _check_always_only_one_assign(self):
    #    flag = False
    #    for always in self.ast.findall(".//always"):
    #        assign_num = len(always.findall(".//assign"))
    #        assigndly_num = len(always.findall(".//assigndly"))

    #        if assigndly_num + assign_num > 1:
    #            print("  Error: Found Multiple Assignment in <always>")
    #            if assigndly_num > 1:
    #                lv_name = always.find(".//assigndly").getchildren()[1].attrib["name"]
    #                print("    Error: Found Multiple <assigndly> in <always>")
    #            if assign_num > 1:
    #                lv_name = always.find(".//assign").getchildren()[1].attrib["name"]
    #                print("    Error: Found Multiple <assign> in <always>")
    #            flag = True

    #            print("    LV = "+lv_name)
    #    if not flag:
    #        print("Pass: Only 1 assignment in Each <always>.")
    #    print("-"*80)


    def _check_param_not_in_circuit(self):
        print("[Checker Task] start Checking Parameter are all replaced by <const>.")
        flag = False
        for var in self.ast.findall(".//var[@param='true']") + self.ast.findall(".//var[@localparam='true']"):
            var_name = var.attrib["name"]
            if self.ast.find(f".//varref[@name='{var_name}']") != None:
                flag = True
                print("    Warning: Found a parameter in <varref>.")
        if not flag:
            print("Pass: No Parameter in the Circuit.")
        print("-"*80)


    #def _check_initial_no_multidriven(self):
    #    for assign in self.ast.findall(".//initial//assign"):
    #        lv_node = assign.getchildren()[0]


    def _check_initial_simple(self):
        print("[Checker Task] start checking <initial> only has 1 <assign>.")
        for initial in self.ast.findall(".//initial"):
            if AstAnalyzeFunc.get_children__ordered(initial) != ["assign"]:
                self._get_loc_info(initial)
                print("  - [Checker Report] warning: found an <initial> not only assigns one signal.")
        for assign in self.ast.findall(".//initial//assign"):
            if self.get_children__ordered(assign) != ["const","varref"]:
                self._get_loc_info(initial)
                print("  - [Checker Report] warning: found an <initial/assign> not assigns <varref> with a <const>.")
        print("-"*80)
            

    def check_simple_design(self):
        print("#########################################")
        print("#    Start Checking Simple Design ...   #")
        print("#########################################")
        self._ast_preprocess()

        self._check_circuit_flattened()
        self._check_circuit_no_voiddtype()
        self._check_circuit_no_taskref()
        self._check_circuit_no_funcref()
        self._check_circuit_no_loop()
        self._check_assign_no_concat_lv()
        self._check_comb_always_only_one_lv()
        self._check_ff_always_no_blking_assign()
        self._check_initial_simple()
        self._check_assign_no_param()
        self._check_param_not_in_circuit()


if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")
    
    # Step 2: Define arguments
    parser.add_argument('--func',action='store_true')
    parser.add_argument("-f", "--file", type=str, help="AST path")                  # Positional argument

    # Step 3: Parse the arguments
    args = parser.parse_args()

    if args.func:
        pprint.pp(list(AstChecker.__dict__.keys()))

    if args.file:
        ast_file = args.file
        ast = Verilator_AST_Tree(ast_file)
        print("#"*len("# Start parsing ["+ast_file+"] #"))
        print("# Start parsing ["+ast_file+"] #")
        print("#"*len("# Start parsing ["+ast_file+"] #"))
        checker = AstChecker(ast)
        checker.check_simple_design()
        #checker.get_info()


