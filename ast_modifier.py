from ast_analyzer import AstAnalyzer
from ast_dump import *
from exceptions import *

from lxml import etree

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

    def merge_multi_name_var(self,output=False):
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
            if output:
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

            circuit_lv_set = set(self.analyzer.get_sig__cir_lv())
            if lv_name in circuit_lv_set:
                raise ASTModificationError(f"Cannot merge the signal, because the signal is also in another subcircuit. sig_name = {lv_name}",0)

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

class AstArrayFlatten:
    def __init__(self,ast):
        self.ast = ast
        self.analyzer = AstAnalyzer(self.ast)
        self.ast_dumper = AstDump(self.ast)

    def module_var_flatten(self):
        """
        This function flatten all composite signals (e.g. array, struct...) into packed registers.
        """
        for var in self.ast.findall(".//module/var"):
            self._var_flatten(var)
        self.ast_dumper.dump()


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

    def _var_flatten(self,node):
        if node.tag == "none":
            return
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
        node.tag = "unpackarray"

        name = node.attrib["name"]
        sig_type = node.attrib["sig_type"]
        dtype = self.get_dtype_node(node)
        sub_dtype_id = dtype.attrib["sub_dtype_id"]

        const1 = dtype.find("./range/const[1]").attrib["name"]
        const2 = dtype.find("./range/const[2]").attrib["name"]
        const1 = self.analyzer.vnum2int(const1)
        const2 = self.analyzer.vnum2int(const2)

        if const1 > const2:
            for idx in range(const1+1):
                if const2 > idx:
                    new_child = etree.Element("none")
                else:
                    new_child = etree.Element("var")
                    new_child.attrib["name"] = f"{name}[{idx}]"
                    new_child.attrib["dtype_id"] = sub_dtype_id
                    new_child.attrib["width"] = str(self.analyzer.get_width__dtype_id(sub_dtype_id))
                    new_child.attrib["sig_type"] = sig_type
                node.append(new_child)
                self._var_flatten(new_child)
        else:
            for idx in range(const2+1):
                if const1 > idx:
                    new_child = etree.Element("none")
                else:
                    new_child = etree.Element("var")
                    new_child.attrib["name"] = f"{name}[{idx}]"
                    new_child.attrib["dtype_id"] = sub_dtype_id
                    new_child.attrib["width"] = str(self.analyzer.get_width__dtype_id(sub_dtype_id))
                    new_child.attrib["sig_type"] = sig_type
                node.append(new_child)
                self._var_flatten(new_child)
