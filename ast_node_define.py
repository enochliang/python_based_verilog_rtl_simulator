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
        else:
            self._value = "x"*self._width
        self._signed = False
        self.fault_list = []

    @property
    def node(self):
        if self._tag == "varref":
            return self.ref_node
        elif self._tag == "arraysel":
            target_node = self._children[0].node
            idx = int(self._children[1].value,2)
            return target_node.children[idx]
        elif self._tag == "var":
            return self
        elif self._tag == "const":
            return self
        else:
            return self

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

