from abc import ABC, abstractmethod
from exceptions import ASTConstructionError

class Verilog_AST_Base_Node:
    def __init__(self):
        self._tag = ""
        self._children = []
        self.attrib = dict()
        self._ast_tree = None

    @property
    def children(self):
        return self._children

    @abstractmethod
    def tag(self):
        pass

    def _set_tree(self,tree):
        self._ast_tree = tree

    def get_tree(self):
        return self._ast_tree

    def append(self, node):
        node._set_tree(self._ast_tree)
        self._children.append(node)

    @property
    def node(self):
        if self._tag == "varref":
            return self.ref_node
        elif self._tag == "arraysel":
            target_node = self._children[0].node
            if "x" in self._children[1].value:
                print("undetermined array index!")
                return None
            else:
                idx = int(self._children[1].value,2)
                return target_node.children[idx]
        elif self._tag == "var":
            return self
        else:
            return self

    def tostring(self,indent=0):
        cur_node = self.node
        #print("aaaa",self.tag, cur_node.tag)
        #if cur_node.tag == "unpackarray":
        #    print([child.name for child in  cur_node.children])
        self.info_tostring(cur_node,indent)
        for child in cur_node._children:
            child.tostring(indent+1)
        if len(self._children) > 0:
            print(" "*2*indent+f"</{cur_node.tag}>")

    def info_tostring(self,node,indent:int):
        s = " "*2*indent + f"<{node.tag} "
        if hasattr(self,"name"):
            s += f"name='{node.name}' "
        if "loc" in node.attrib:
            s += f"loc='{node.attrib['loc']}' "
        if hasattr(self,"_value"):
            s += f"value='{node.value}' next_value='{node.next_value}' cur_value='{node.cur_value}'"
        s += ">"
        print(s)





class Verilog_AST_Node(Verilog_AST_Base_Node):
    def __init__(self):
        Verilog_AST_Base_Node.__init__(self)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self,tag:str):
        self._tag = tag

class Verilog_AST_Assign_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)
        self._tag = "assign"

    @property
    def rv_node(self):
        return self._children[0]

    @property
    def lv_node(self):
        return self._children[1]


class Verilog_AST_Control_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)

    @property
    def ctrl_node(self):
        if len(self._children) < 1:
            return None
        else:
            return self._children[0]

class Verilog_AST_IF_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "if"

    @property
    def true_node(self):
        if len(self._children) < 2:
            return None
        else:
            return self._children[1]

    @property
    def false_node(self):
        if len(self._children) < 3:
            return None
        else:
            return self._children[2]

class Verilog_AST_CASE_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "case"

    @property
    def caseitems(self):
        if len(self._children) <= 1:
            return []
        else:
            return [ node for node in self._children[1:]]

class Verilog_AST_CASEITEM_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)
        self._tag = "caseitem"
        self.code_start_pos = 0

    @property
    def other_children(self):
        if len(self._children) == self.code_start_pos:
            return []
        else:
            return self._children[self.code_start_pos:]

    @property
    def conditions(self):
        return self._children[:self.code_start_pos]

    def append(self, node):
        node._set_tree(self._ast_tree)
        if isinstance(node, Verilog_AST_Circuit_Node):
            self.code_start_pos += 1
        self._children.append(node)

class Verilog_AST_Circuit_Node(Verilog_AST_Node):
    def __init__(self,width=None):
        Verilog_AST_Node.__init__(self)
        self._width = width
        if width == None:
            self._value = None
            self._next_value = None
            self._cur_value = None
        else:
            self._value = "x"*self._width
            self._next_value = "x"*self._width
            self._cur_value = "x"*self._width
        self._signed = False
        self._fault_list = {}


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
    def ivalue(self):
        target = self.node
        if target._tag == "var":
            if target.attrib["sig_type"] == "register":
                return target._cur_value
            else:
                return target._value
        elif target._tag == "unpackarray":
            raise SimulationError(f"Cannot directly access the value of an <unpackarray>",1)
        else:
            return target._value

    @property
    def value(self):
        target = self.node
        if target._tag == "var":
            return target._value
        elif target._tag == "unpackarray":
            raise SimulationError(f"Cannot directly access the value of an <unpackarray>",1)
        else:
            return target._value
    @value.setter
    def value(self,value:str):
        if len(value) == self._width:
            self._value = value
        else:
            raise ASTConstructionError(f"value and width doesn't match. tag = {self._tag}",0)

    @property
    def next_value(self):
        target = self.node
        if target._tag == "var":
            return target._next_value
        elif target._tag == "unpackarray":
            raise SimulationError(f"Cannot directly access the value of an <unpackarray>",1)
        else:
            return target._next_value
    @next_value.setter
    def next_value(self,value:str):
        if len(value) == self._width:
            self._next_value = value
        else:
            raise ASTConstructionError(f"value and width doesn't match. tag = {self._tag}",0)

    @property
    def cur_value(self):
        target = self.node
        if target._tag == "var":
            return target._cur_value
        elif target._tag == "unpackarray":
            raise SimulationError(f"Cannot directly access the value of an <unpackarray>",1)
        else:
            return target._cur_value
    @cur_value.setter
    def cur_value(self,value:str):
        if len(value) == self._width:
            self._cur_value = value
        else:
            raise ASTConstructionError(f"value and width doesn't match. tag = {self._tag}",0)

    @property
    def fault_list(self):
        target = self.node
        if target._tag == "var":
            return target._fault_list
        else:
            return target._fault_list

    @fault_list.setter
    def fault_list(self,value:list):
        self._fault_list = value

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
    def ref_node(self):
        return self.__ref_node

    @ref_node.setter
    def ref_node(self,node):
        self.__ref_node = node

