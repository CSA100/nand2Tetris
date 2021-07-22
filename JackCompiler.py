import os, sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pprint

class Tokenizer: 
    #breks input from a single .jack input file into Jack-language tokens as specified by the Jack grammar
    def __init__(self, infilename):
        # opens input file and gets ready to parse it
        self.infilename = infilename
        self.infile = []

        # cleaning up any single comments and empty lines in the input file and storing each line in an array
        infile = open(self.infilename + '.jack')
        for line in infile:

            line = line.strip()
            comment = line.find('//')
            newlinechar = line.find('\n')

            if line != '':
                comment = line.find('//')
                if comment == -1:
                    newlinechar = line.find('\n') 
                    if newlinechar != -1:
                        line = line[:newlinechar]
                    self.infile.append(line)
                elif comment != -1:
                    line = line[:comment]
                    newlinechar = line.find('\n')
                    if newlinechar != -1:
                        line = line[:newlinechar]
                    if line != '':
                        self.infile.append(line)

        # remove multi-line comments from the above array
        comment_started = False
        comment_lines = 0
        i = 0

        while i < len(self.infile):
            line = self.infile[i]
            if comment_started:
                comment_lines += 1
            if line.startswith('/*') and (not comment_started):
                comment_started = True
                comment_lines += 1
            if line.endswith('*/') and comment_started:
                comment_started = False
                if comment_lines == 1:
                    del self.infile[i]
                else:
                    del self.infile[i-comment_lines+1:i+1]
                i -= comment_lines
                comment_lines = 0
            i += 1

        # looping over above array to split out symbols into separate list items. 
        # except symbols inside strings
        j = 0
        while j < len(self.infile):
            line = self.infile[j]
            self.infile[j] = line.strip()

            containsString = line.count('"') == 2
            firstquot = line.find('"')
            secondquot = line.find('"', firstquot + 1)

            i = 0

            while i < len(line):
                if line[i] in ('{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<',
                                    '>', '=', '~'):
                    if containsString and (i < secondquot) and (i > firstquot):
                        i += 1
                    else:
                        parts = line.split(line[i], 1)
                        del self.infile[j]
                        self.infile.insert(j, parts[0])
                        self.infile.insert(j+1, line[i])
                        self.infile.insert(j+2, parts[1])
                        j += 1
                        break
                else:
                    i += 1
                
            j += 1

        # loop over to split keywords, identifiers, etc. i.e. splitting any blank spaces except for inside strings
        k = 0
        while k < len(self.infile):
            if self.infile[k].count('"') != 2:
                parts = self.infile[k].split()
                parts_length = len(parts)
                if parts_length > 1:
                    del self.infile[k]
                    self.infile[k:k] = parts
                    k = k + parts_length - 1
            else: 
                self.infile[k] = self.infile[k].strip()
            k += 1

        # loop over to remove empty strings
        self.infile = [line.strip() for line in  self.infile if line.strip() != '']

        infile.close()

        self.totaltokencount = len(self.infile)
        self.currenttokencount = 0
        self.currenttoken = ''
    
    def hasMoreTokens(self):
        # checks if there are more tokens left to be parsed
        if(self.currenttokencount < self.totaltokencount):
            return True
        return False
    
    def advance(self):
        # reads the next token of the input and makes it the current token
        self.currenttoken = self.infile[self.currenttokencount]
        self.currenttokencount += 1

    def lookAhead(self):
        # returns the token that is after the current token
        return self.infile[self.currenttokencount]

    def tokenType(self):
        # Returns the type of the current token
        if self.currenttoken in ('class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int',
                                 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if',
                                 'else', 'while', 'return'):
            return 'KEYWORD'

        elif self.currenttoken in ('{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<',
                                    '>', '=', '~'):
            return 'SYMBOL'

        elif self.currenttoken.isdigit():
            if int(self.currenttoken) in range (32768):
                return 'INT_CONST'

        elif self.currenttoken.startswith('"'):
            return 'STRING_CONST'

        elif not self.currenttoken[0].isdigit():
            return 'IDENTIFIER'
        
        else:
            raise Exception('Token type not found')

    def keyWord(self):
        # returns the keyword which is the current token. Only call when token type is KEYWORD

        if self.currenttoken in ('class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int',
                                 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if',
                                 'else', 'while', 'return'):
            return self.currenttoken
        else:
            raise Exception('Keyword not found')
    
    def symbol(self):
        # returns the character which is the current token. Only call when token type is SYMBOL

        if self.currenttoken in ('{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<',
                                    '>', '=', '~'):
            return self.currenttoken
        else: 
            raise Exception('Symbol not found')

    def identifier(self):
        # returns the identifier which is the current token. Only call when current token type is IDENTIFIER

        return self.currenttoken
    
    def intVal(self):
        # returns the integer value of the current token. Only call when current token type is INT_CONST

        return int(self.currenttoken)
    
    def stringVal(self):
        # returns the string value of the current token. Only call when current token type is STRING_CONST

        return self.currenttoken

class SymbolTable:
    def __init__(self):
        self.classtable = {}
        self.subroutinetable = {}
        self.staticindex = 0
        self.fieldindex = 0
        self.argindex = 0
        self. varindex = 0

    def startSubroutine(self):
        # starts a new subroutine scope (i.e. resets the subroutine's symbol table)
        self.subroutinetable.clear()
        self.argindex = 0
        self.varindex = 0
        return
    
    def Define(self, name, type, kind):
        # defines a new identifier of a given name, type, and kind and assigns it a running index. STATIC and FIELD
        # identifiers have a class scope, while ARG and VAR identifiers have a subroutine scope.
        if (kind == 'STATIC'):
            self.classtable[name] = {"type": type, "kind": kind, "index": self.staticindex}
            self.staticindex += 1
        elif (kind == 'FIELD'):
            self.classtable[name] = {"type": type, "kind": kind, "index": self.fieldindex}
            self.fieldindex += 1
        elif (kind == 'ARG'):
            self.subroutinetable[name] = {"type": type, "kind": kind, "index": self.argindex}
            self.argindex += 1
        elif (kind == 'VAR'):
            self.subroutinetable[name] = {"type": type, "kind": kind, "index": self.varindex}
            self.varindex += 1
        else:
            raise Exception('kind not found')

        return
    
    def VarCount(self, kind):
        # returns the number of variables of the given kind already defined in the current scope
        if (kind == 'STATIC'):
            return self.staticindex 
        elif (kind == 'FIELD'):
            return self.fieldindex
        elif (kind == 'ARG'):
            return self.argindex
        elif (kind == 'VAR'):
            return self.varindex
        else:
            raise Exception('kind not found')
    
    def KindOf(self, name):
        # returns the kind of the named identifier in the current scope. if the identifier is unknown in the current
        # scope, returns NONE
        if name in self.subroutinetable:
            return self.subroutinetable[name]["kind"]
        elif name in self.classtable:
            return self.classtable[name]["kind"]
        else:
            return None
    
    def TypeOf(self, name):
        # Returns the type of the named identifier in the current scope.
        if name in self.subroutinetable:
            return self.subroutinetable[name]["type"]
        elif name in self.classtable:
            return self.classtable[name]["type"]
        else:
            raise Exception('name not found')
    
    def IndexOf(self, name):
        # Returns the index assigned to the named identifier
        if name in self.subroutinetable:
            return self.subroutinetable[name]["index"]
        elif name in self.classtable:
            return self.classtable[name]["index"]
        else:
            raise Exception('Name not found')

class VMWriter:
    def __init__(self, filename):
        # Opens a new file and prepares to write
        self.outfile = open(filename + '.vm', 'w')
        return
    
    def writePush(self, segment, index):
        # Writes a VM Push command
        self.outfile.write(f'push {segment} {index}\n')
        return
    
    def writePop(self, segment, index):
        # writes a VM Pop command
        self.outfile.write(f'pop {segment} {index}\n')
        return
    
    def writeArithmetic(self, command):
        # writes a VM arithmetic command
        self.outfile.write(f'{command}\n')
        return

    def writeLabel(self, label):
        # writes a VM lable command
        self.outfile.write(f'label {label}\n')
        return

    def writeGoto(self, label):
        # writes a VM goto command
        self.outfile.write(f'goto {label}\n')
        return

    def writeIf(self, label):
        # writes a VM if-goto command
        self.outfile.write(f'if-goto {label}\n')
        return

    def writeCall(self, name, nArgs):
        # writes a VM call command
        self.outfile.write(f'call {name} {nArgs}\n')
        return

    def writeFunction(self, name, nLocals):
        # writes VM function command
        self.outfile.write(f'function {name} {nLocals}\n')
        return

    def writeReturn(self):
        # writes a VM return command
        self.outfile.write('return\n')
        return

    def close(self):
        # closes the output file
        self.outfile.close()
        return


class CompilationEngine:
    def __init__(self, outfilename, tokenizer, symboltable, vmwriter):
        # the next routine called must be compile class
        self.outfile = open(outfilename + '.xml', 'w')
        self.classname = outfilename

        self.root = None
        self.currentelement = None

        self.symboltable = symboltable
        self.vmwriter = vmwriter

        self.currentfunction = ''
        self.currentlabelcount = 0

        self.tokenizer = tokenizer
        self.tokenizer.advance()

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'class'):
            self.compileClass()
        else:
            raise Exception('Expected a class declaration')

        
    def prettify(self, elem):
        # Return a pretty-printed XML string for the Element.

        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent="  ")
        return pretty.replace('<?xml version="1.0" ?>\n', '')

    def addSubElement(self, tag, text=False):
        # adds the given element and text to the xml tree

        add_element = ET.SubElement(self.currentelement, tag)
        if(text):
            add_element.text = f' {text} '
        return add_element

    def compileClass(self):
        # compiles a complete class

        self.root = ET.Element('class')
        self.currentelement = self.root

        self.addSubElement('keyword', 'class')
        self.tokenizer.advance()

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: class\ndefined')
            self.tokenizer.advance()
        else: 
            raise Exception('Expected an identifier')

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '{'): 
            self.addSubElement('symbol', '{')
            self.tokenizer.advance()

            while not ((self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}')):
                
                if self.tokenizer.tokenType() == "KEYWORD":
                    if self.tokenizer.keyWord() in ('static', 'field'):
                        self.compileClassVarDec()
                        continue
                    elif self.tokenizer.keyWord() in ('method', 'function', 'constructor'):
                        self.compileSubroutine()
                        continue
                    else:
                        raise Exception('Expected class variable declaration or subroutine')
                self.tokenizer.advance()
               
        else:
            raise Exception('Expected symbol: {')

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}'): 
            self.addSubElement('symbol', '}')
        else:
            raise Exception('Expected } for class dec')

        self.outfile.write(self.prettify(self.root))
        self.outfile.close()

        self.vmwriter.close()

    def compileClassVarDec(self):
        # compiles a static or field declaration
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('classVarDec')

        name = None
        kind = None
        type = None

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('field', 'static')):
            self.addSubElement('keyword', self.tokenizer.keyWord())
            kind = self.tokenizer.keyWord().upper()
            self.tokenizer.advance() 
        else:
            raise Exception('Expected keyword, field or static for classVarDec')

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            type = self.tokenizer.identifier()
            self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: class\nused')
            self.tokenizer.advance()
        elif (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('int', 'char', 'boolean')):
            self.addSubElement('keyword', self.tokenizer.keyWord())
            type = self.tokenizer.keyWord()
            self.tokenizer.advance()
        else:
            raise Exception('Expected an identifier or keyword for handleType')

        isVarName = True

        while not ((self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';')):

            if isVarName:
                if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                    name = self.tokenizer.identifier()
                    self.symboltable.Define(name, type, kind)
                    self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: {kind}\ndefined\n {self.symboltable.IndexOf(name)}') 
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected a VarName for classVarDec')
            else:
                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ','):
                    self.addSubElement('symbol', ',')
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected , for classVarDec')
            
            isVarName = not isVarName

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
            self.addSubElement('symbol', ';')
            self.tokenizer.advance()
        else:
            raise Exception('Expected ; for classVarDec')

        self.currentelement = previouselement
        return
    
    def compileSubroutine(self):
        # compiles a complete method, function or constructor
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('subroutineDec')

        self.symboltable.startSubroutine()
        self.currentlabelcount = 0

        functionName = None
        nLocals = None
        type = None

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('constructor',
        'function', 'method')):
            type = self.tokenizer.keyWord()
            self.addSubElement('keyword', type)
            self.tokenizer.advance()
        else:
            raise Exception('Expected keyword: constructor, function or method for subroutineDec')

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'void'):
            self.addSubElement('keyword', 'void')
            self.tokenizer.advance()
        else:
            if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: class\nused')
                self.tokenizer.advance()
            elif (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('int', 'char', 'boolean')):
                self.addSubElement('keyword', self.tokenizer.keyWord())
                self.tokenizer.advance()
            else:
                raise Exception('Expected an identifier or keyword for handleType')

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: subroutine\ndefined')
            functionName = f'{self.classname}.{self.tokenizer.identifier()}'
            self.currentfunction = functionName
            self.tokenizer.advance()
        else:
            raise Exception('Expected an identifier for subroutineDec')

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
                    self.addSubElement('symbol', '(')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected ( for subroutineDec')

        if type == 'method':
            self.symboltable.argindex += 1
        self.compileParameterList()

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
                    self.addSubElement('symbol', ')')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected ) for subroutineDec')

        self.currentelement = self.addSubElement('subroutineBody')

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '{'):
                    self.addSubElement('symbol', '{')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected { for subroutineBody')

        while True:
            if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'var'):
                self.compileVarDec()
                continue
            break

        nLocals = self.symboltable.VarCount('VAR')
        self.vmwriter.writeFunction(functionName, nLocals)

        if type == 'constructor':
            nField = self.symboltable.VarCount('FIELD')
            self.vmwriter.writePush('constant', nField)
            self.vmwriter.writeCall('Memory.alloc', 1)
            self.vmwriter.writePop('pointer', 0)
        elif type == 'method':
            self.vmwriter.writePush('argument', 0)
            self.vmwriter.writePop('pointer', 0)
            
        self.compileStatements()

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}'):
                    self.addSubElement('symbol', '}')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected } for subroutineBody')

        self.currentelement = previouselement
        return

    def compileParameterList(self):
        # compiles a (possibly empty) parameter list, not including the enclosing "()"
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('parameterList')

        if not ((self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')')):
            while True:
                name = None
                type = None
                kind = None

                if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                    type = self.tokenizer.identifier()
                    self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: class\nused')
                    self.tokenizer.advance()
                elif (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('int', 'char', 'boolean')):
                    type = self.tokenizer.keyWord()
                    self.addSubElement('keyword', self.tokenizer.keyWord())
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected an identifier or keyword for handleType') 


                if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                    name = self.tokenizer.identifier()
                    kind = 'ARG'
                    self.symboltable.Define(name, type, kind) 
                    self.addSubElement('identifier', f'{name}\ncategory: ARG\ndefined\n{self.symboltable.IndexOf(name)}')
                    self.tokenizer.advance()
                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ','):
                    self.addSubElement('symbol', ',')
                    self.tokenizer.advance()
                else:
                    break
            
        self.currentelement = previouselement
        return

    def compileVarDec(self):
        # compiles a var declaration
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('varDec')

        name = None
        kind = None
        type = None

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'var'):
            self.addSubElement('keyword', 'var')
            kind = 'VAR'
            self.tokenizer.advance()
        else:
            raise Exception('Expected keyword, var for varDec')

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            type = self.tokenizer.identifier()
            self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: class\nused')
            self.tokenizer.advance()
        elif (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('int', 'char', 'boolean')):
            self.addSubElement('keyword', self.tokenizer.keyWord())
            type = self.tokenizer.keyWord()
            self.tokenizer.advance()
        else:
            raise Exception('Expected an identifier or keyword for handleType')

        isVarName = True

        while not ((self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';')):

            if isVarName:
                if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                    name = self.tokenizer.identifier()
                    self.symboltable.Define(name, type, kind)
                    self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: {kind}\ndefined\n {self.symboltable.IndexOf(name)}')
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected a VarName for varDec')
            else:
                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ','):
                    self.addSubElement('symbol', ',')
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected , for varDec')
            
            isVarName = not isVarName

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
            self.addSubElement('symbol', ';')
            self.tokenizer.advance()
        else:
            raise Exception('Expected ; for varDec')

        self.currentelement = previouselement
        return


    def compileStatements(self):
        # compiles a sequence of statements, not including the enclosing "{}"

        previouselement = self.currentelement
        self.currentelement = self.addSubElement('statements')

        statements = True

        while statements:
            if (self.tokenizer.tokenType()) == "KEYWORD" and (self.tokenizer.keyWord() in ('let', 'if', 'while',
            'do', 'return')):
                if self.tokenizer.keyWord() == 'let':
                    self.compileLet()
                    continue
                elif self.tokenizer.keyWord() == 'if':
                    self.compileIf()
                    continue
                elif self.tokenizer.keyWord() == 'while':
                    self.compileWhile()
                    continue
                elif self.tokenizer.keyWord() == 'do':
                    self.compileDo()
                    continue
                elif self.tokenizer.keyWord() == 'return':
                    self.compileReturn()
                    continue
            statements = False
        
        self.currentelement = previouselement
        return 
    
    def compileDo(self):
        # compiles a do statement

        previousElement = self.currentelement
        self.currentelement = self.addSubElement('doStatement')

        subroutine = ''
        nArgs = None
        scope = 'class'
        thisindex = 0

        case = 1
        classvarname = ''

        # case 1 is when the called subroutine is a method of the form method(...). In this case we call the
        # function CurrentClass.method
        # case 2 is when the called subroutine is a method of the form varname.method(...). In this case we call
        # the function vartype.method
        # case 3 is when the called subroutine is a function of the form classname.method(...). In this case we
        # call the function classname.method

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'do'):
            self.addSubElement('keyword', 'do')
            self.tokenizer.advance()
        else:
            raise Exception("Expected Keyword: do. For compileDo")

        if self.tokenizer.lookAhead() == '.':
            if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                name = self.tokenizer.identifier()
                if name in self.symboltable.subroutinetable:
                    self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                    classvarname = self.symboltable.TypeOf(name)
                    thisindex = self.symboltable.IndexOf(name)
                    scope = 'local'
                    case = 2
                elif name in  self.symboltable.classtable:
                    self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                    classvarname = self.symboltable.TypeOf(name)
                    thisindex = self.symboltable.IndexOf(name)
                    scope = 'class'
                    case = 2
                else:
                    self.addSubElement('identifier', f'{name}\ncategory: class\nused')
                    classvarname = name
                    case = 3
                
                self.tokenizer.advance()

                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '.'):
                    self.addSubElement('symbol', '.')
                    self.tokenizer.advance()
                else:
                    raise Exception("Expected Symbol: . for do statement")
            else:
                raise Exception("Expected identifier for do statment")

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: subroutine\nused')

            if case == 1:
                subroutine = f'{self.classname}.{self.tokenizer.identifier()}'
            elif (case == 2) or (case == 3):
                subroutine = f'{classvarname}.{self.tokenizer.identifier()}'
            self.tokenizer.advance()
        else:
            raise Exception("Expected identifier for compile do")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
            self.addSubElement('symbol', '(')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ( for do statement")


        if case == 1:
            self.vmwriter.writePush('pointer', 0)
            nArgs = self.compileExpressionList()
            self.vmwriter.writeCall(subroutine, nArgs + 1)
        elif case == 2:
            if scope == 'class':
                self.vmwriter.writePush('this', thisindex)
            elif scope == 'local':
                self.vmwriter.writePush('local', thisindex)
            nArgs = self.compileExpressionList()
            self.vmwriter.writeCall(subroutine, nArgs + 1)
        elif case == 3:
            nArgs = self.compileExpressionList()
            self.vmwriter.writeCall(subroutine, nArgs)

        # if type == 'Method' and classused == '':
        #     self.vmwriter.writePush('pointer', 0)
        #     self.vmwriter.writeCall(f'{self.classname}.{subroutine}', nArgs + 1) 
        # elif type == 'Method' and classused != '':
        #     self.vmwriter.writePush('this', 0)
        #     self.vmwriter.writeCall(f'{subroutine}', nArgs + 1) 
        # else:
        #     self.vmwriter.writeCall(subroutine, nArgs)
        self.vmwriter.writePop('temp', 0)

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
            self.addSubElement('symbol', ')')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ) for do statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
            self.addSubElement('symbol', ';')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ; for compile do")

        self.currentelement = previousElement
        return
    
    def compileLet(self):
        # compiles a let statement
        previousElement = self.currentelement
        self.currentelement = self.addSubElement('letStatement')

        name = None
        kind = None
        index = None
        isArray = False
        segment = None

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'let'):
            self.addSubElement('keyword', 'let')
            self.tokenizer.advance()
        else:
            raise Exception("Expected Keyword: let. For let statement")

        if (self.tokenizer.tokenType() == 'IDENTIFIER'):
            name = self.tokenizer.identifier()
            kind = self.symboltable.KindOf(name)
            index = self.symboltable.IndexOf(name)
            
            if kind == 'VAR':
                segment = 'local'
            elif kind == 'ARG':
                segment = 'argument'
            elif kind == 'FIELD':
                segment = 'this'
            elif kind == 'STATIC':
                segment = 'static'

            self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n {self.symboltable.IndexOf(name)}')
            self.tokenizer.advance()
        else:
            raise Exception("Expected identifier For let statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '['):
            self.addSubElement('symbol', '[')
            self.tokenizer.advance()

            self.compileExpression()
            isArray = True
            self.vmwriter.writePush(segment, index)
            self.vmwriter.writeArithmetic('add')
            self.vmwriter.writePop('temp', 1)

            if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ']'):
                self.addSubElement('symbol', ']')
                self.tokenizer.advance()
            else:
                raise Exception('Expected ] for let statement')
        
        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '='):
            self.addSubElement('symbol', '=')
            self.tokenizer.advance()
        else:
            raise Exception('Expected = for let statment')
        
        self.compileExpression()

        if not isArray:
            self.vmwriter.writePop(segment, self.symboltable.IndexOf(name))
        else:
            self.vmwriter.writePush('temp', 1)
            self.vmwriter.writePop('pointer', 1)
            self.vmwriter.writePop('that', 0)

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
            self.addSubElement('symbol', ';')
            self.tokenizer.advance()
        else:
            raise Exception('Expected ; for let statment')

        
        self.currentelement = previousElement
        return

    def compileWhile(self):
        # compiles a while statement
        previousElement = self.currentelement
        self.currentelement = self.addSubElement('whileStatement')

        toplabel = None
        endlabel = None

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'while'):
            self.addSubElement('keyword', 'while')

            toplabel = f'Label.{self.currentfunction}.{self.currentlabelcount}'
            self.vmwriter.writeLabel(toplabel)
            self.currentlabelcount += 1

            endlabel = f'Label.{self.currentfunction}.{self.currentlabelcount}'
            self.currentlabelcount += 1
            self.tokenizer.advance()
        else:
            raise Exception("Expected Keyword: while. For while statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
            self.addSubElement('symbol', '(')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ( for while statement")

        self.compileExpression()
        self.vmwriter.writeArithmetic('not')
        self.vmwriter.writeIf(endlabel)

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
            self.addSubElement('symbol', ')')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ) for while statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '{'):
                    self.addSubElement('symbol', '{')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected { for while statement')

        self.compileStatements()
        self.vmwriter.writeGoto(toplabel)

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}'):
                    self.addSubElement('symbol', '}')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected } for while statement')

        self.vmwriter.writeLabel(endlabel)

        self.currentelement = previousElement
        return
    
    def compileReturn(self):
        # compiles a return statement
        previousElement = self.currentelement
        self.currentelement = self.addSubElement('returnStatement')

        isVoid = False

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'return'):
            self.addSubElement('keyword', 'return')
            self.tokenizer.advance()
        else:
            raise Exception("Expected Keyword: return. For return statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
            isVoid = True
            self.addSubElement('symbol', ';')
            self.tokenizer.advance()
        else:
            self.compileExpression()
            if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ';'):
                self.addSubElement('symbol', ';')
                self.tokenizer.advance()
            else:
                raise Exception("Expected ; for return statement")

        if isVoid:
            self.vmwriter.writePush('constant', 0)
        
        self.vmwriter.writeReturn()

        self.currentelement = previousElement
        return

    def compileIf(self):
        # compiles an if statement, possibly with a trailing else clause
        previousElement = self.currentelement
        self.currentelement = self.addSubElement('ifStatement')

        elselabel = f'Label.{self.currentfunction}.{self.currentlabelcount}'
        self.currentlabelcount += 1
        exitlabel = f'Label.{self.currentfunction}.{self.currentlabelcount}'
        self.currentlabelcount += 1

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'if'):
            self.addSubElement('keyword', 'if')
            self.tokenizer.advance()
        else:
            raise Exception("Expected Keyword: if. For if statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
            self.addSubElement('symbol', '(')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ( for if statement")

        self.compileExpression()
        self.vmwriter.writeArithmetic('not')
        self.vmwriter.writeIf(elselabel)

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
            self.addSubElement('symbol', ')')
            self.tokenizer.advance()
        else:
            raise Exception("Expected ) for if statement")

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '{'):
                    self.addSubElement('symbol', '{')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected { for if statement')

        self.compileStatements()
        self.vmwriter.writeGoto(exitlabel)
        self.vmwriter.writeLabel(elselabel) 

        if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}'):
                    self.addSubElement('symbol', '}')
                    self.tokenizer.advance()
        else:
            raise Exception('Expected } for if statement')

        if (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() == 'else'):
            self.addSubElement('keyword', 'else')
            self.tokenizer.advance()
            if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '{'):
                self.addSubElement('symbol', '{')
                self.tokenizer.advance()
            else:
                raise Exception('Expected { for if statement')

            self.compileStatements()

            if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '}'):
                        self.addSubElement('symbol', '}')
                        self.tokenizer.advance()
            else:
                raise Exception('Expected } for if statement')

        self.vmwriter.writeLabel(exitlabel)

        self.currentelement = previousElement
        return

    def compileExpression(self):
        # compiles an expression
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('expression')

        self.compileTerm()

        operatorlist = []

        while (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() in ('+', '-', '*', '/',
        '&', '|', '<', '>', '=')):
            operator = self.tokenizer.symbol()
            operatorlist.append(operator)
            self.addSubElement('symbol', operator)
            self.tokenizer.advance()

            self.compileTerm()

        while len(operatorlist) != 0:
            operator = operatorlist.pop()
            if operator == '+':
                self.vmwriter.writeArithmetic('add')
            elif operator == '*':
                self.vmwriter.writeCall('Math.multiply', 2)
            elif operator == '-':
                self.vmwriter.writeArithmetic('sub')
            elif operator == '/':
                self.vmwriter.writeCall('Math.divide', 2)
            elif operator == '&':
                self.vmwriter.writeArithmetic('and')
            elif operator == '|':
                self.vmwriter.writeArithmetic('or')
            elif operator == '<':
                self.vmwriter.writeArithmetic('lt')
            elif operator == '>':
                self.vmwriter.writeArithmetic('gt')
            elif operator == '=':
                self.vmwriter.writeArithmetic('eq')

        self.currentelement = previouselement
        return

    def compileTerm(self):
        # compiles a term. This routine is faced with a slight difficulty when faced with alternative parsing rules.
        # Specifilcally, if the current token is an identifier, the routine must distinguish between a variable, an
        # array entry, and a subroutine call. A single look-ahead token, which may be one of "[", "(" or "." suffices
        # to distinguish between the three possibilities. Any other token is not part of this term and should not
        # be advanced over.
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('term')

        if self.tokenizer.tokenType() == 'INT_CONST':
            integer = self.tokenizer.intVal()
            self.addSubElement('integerConstant', f'{integer}')
            self.vmwriter.writePush('constant', integer)
            self.tokenizer.advance()
        elif self.tokenizer.tokenType() == 'STRING_CONST':
            string = self.tokenizer.stringVal()[1:-1]
            self.addSubElement('stringConstant', string)

            self.vmwriter.writePush('constant', len(string))
            self.vmwriter.writeCall('String.new', 1)

            for char in string:
                self.vmwriter.writePush('constant', ord(char))
                self.vmwriter.writeCall('String.appendChar', 2)
            self.tokenizer.advance()
        elif (self.tokenizer.tokenType() == 'KEYWORD') and (self.tokenizer.keyWord() in ('true', 'false', 'null',
        'this')):
            self.addSubElement('keyword', self.tokenizer.keyWord())
            
            if self.tokenizer.keyWord() in ('false, null'):
                self.vmwriter.writePush('constant', 0)
            elif self.tokenizer.keyWord() == 'true':
                self.vmwriter.writePush('constant', 1)
                self.vmwriter.writeArithmetic('neg')
            elif self.tokenizer.keyWord() == 'this':
                self.vmwriter.writePush('pointer', 0)
            self.tokenizer.advance()
        elif (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() in ('-', '~')):
            unaryOp = self.tokenizer.symbol()
            self.addSubElement('symbol', self.tokenizer.symbol())
            self.tokenizer.advance()
            self.compileTerm()
            if unaryOp == '-':
                self.vmwriter.writeArithmetic('neg')
            elif unaryOp == '~':
                self.vmwriter.writeArithmetic('not')
        elif (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
            self.addSubElement('symbol', '(')
            self.tokenizer.advance()
            self.compileExpression()
            if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
                self.addSubElement('symbol', ')')
                self.tokenizer.advance()
            else:
                raise Exception('Expected ) for compile term')
        elif self.tokenizer.tokenType() == 'IDENTIFIER':
            nexttoken = self.tokenizer.lookAhead()
            if nexttoken in ('(', '.'):

                subroutine = ''
                nArgs = None
                scope = 'class'
                thisindex = 0

                case = 1
                classvarname = ''

                if nexttoken == '.':
                    if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                        name = self.tokenizer.identifier()
                        if name in self.symboltable.subroutinetable:
                            self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                            classvarname = self.symboltable.TypeOf(name)
                            thisindex = self.symboltable.IndexOf(name)
                            scope = 'local'
                            case = 2
                        elif name in self.symboltable.classtable:
                            self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                            classvarname = self.symboltable.TypeOf(name)
                            thisindex = self.symboltable.IndexOf(name)
                            scope = 'class'
                            case = 2
                        else:
                            self.addSubElement('identifier', f'{name}\ncategory: class\nused')
                            classvarname = name
                            case = 3 
                
                        self.tokenizer.advance()
                        
                    if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '.'):
                        self.addSubElement('symbol', '.')

                        subroutine += '.'
                        self.tokenizer.advance()
                    else:
                        raise Exception("Expected Symbol: . for term")
                else:
                    raise Exception("Expected identifier for term")

                if (self.tokenizer.tokenType() == 'IDENTIFIER'):
                    self.addSubElement('identifier', f'{self.tokenizer.identifier()}\ncategory: subroutine\nused')
                    
                    if case == 1:
                        subroutine = f'{self.classname}.{self.tokenizer.identifier()}'
                    elif (case == 2) or (case == 3):
                        subroutine = f'{classvarname}.{self.tokenizer.identifier()}'
                    self.tokenizer.advance()
                else:
                    raise Exception("Expected identifier for term")

                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '('):
                    self.addSubElement('symbol', '(')
                    self.tokenizer.advance()
                else:
                    raise Exception("Expected ( for term")

                if case == 1:
                    self.vmwriter.writePush('pointer', 0)
                    nArgs = self.compileExpressionList()
                    self.vmwriter.writeCall(subroutine, nArgs + 1)
                elif case == 2:
                    if scope == 'class':
                        self.vmwriter.writePush('this', thisindex)
                    elif scope == 'local':
                        self.vmwriter.writePush('local', thisindex)
                    nArgs = self.compileExpressionList()
                    self.vmwriter.writeCall(subroutine, nArgs + 1)
                elif case == 3:
                    nArgs = self.compileExpressionList()
                    self.vmwriter.writeCall(subroutine, nArgs)

                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')'):
                    self.addSubElement('symbol', ')')
                    self.tokenizer.advance()
                else:
                    raise Exception("Expected ) for term")
          
            elif nexttoken == '[':
                name = self.tokenizer.identifier()
                self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                
                kind = self.symboltable.KindOf(name)
                if kind == 'FIELD':
                    self.vmwriter.writePush('this', self.symboltable.IndexOf(name)) 
                elif kind == 'VAR':
                    self.vmwriter.writePush('local', self.symboltable.IndexOf(name)) 
                elif kind == 'STATIC':
                    self.vmwriter.writePush('static', self.symboltable.IndexOf(name)) 
                
                self.tokenizer.advance()

                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == '['):
                    self.addSubElement('symbol', '[')
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected [ for term')

                self.compileExpression()
                self.vmwriter.writeArithmetic('add')
                self.vmwriter.writePop('pointer', 1)
                self.vmwriter.writePush('that', 0)
                
                if (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ']'):
                    self.addSubElement('symbol', ']')
                    self.tokenizer.advance()
                else:
                    raise Exception('Expected ] for term')

            else:
                name = self.tokenizer.identifier()
                self.addSubElement('identifier', f'{name}\ncategory: {self.symboltable.KindOf(name)}\nused\n{self.symboltable.IndexOf(name)}')
                
                kind = self.symboltable.KindOf(name)
                if kind == 'VAR':
                    self.vmwriter.writePush('local', self.symboltable.IndexOf(name))
                elif kind == 'ARG':
                    self.vmwriter.writePush('argument', self.symboltable.IndexOf(name))
                elif kind == 'FIELD':
                    self.vmwriter.writePush('this', self.symboltable.IndexOf(name))
                elif kind == 'STATIC':
                    self.vmwriter.writePush('static', self.symboltable.IndexOf(name))
                self.tokenizer.advance()
        else:
            raise Exception('term not identified')

        self.currentelement = previouselement
        return

    def compileExpressionList(self):
        # compiles a (possibly empty) comma-separated list of expressions
        # returns the number of expressions in the list of expressions
        previouselement = self.currentelement
        self.currentelement = self.addSubElement('expressionList')

        numExpressions = 0

        if not ((self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ')')):

            self.compileExpression()
            numExpressions += 1

            while (self.tokenizer.tokenType() == 'SYMBOL') and (self.tokenizer.symbol() == ','):
                self.addSubElement('symbol', ',')
                self.tokenizer.advance()

                self.compileExpression()
                numExpressions += 1
                    
        self.currentelement = previouselement
        return numExpressions
    

    
# infile = sys.argv[1]
# tokenizer = Tokenizer(infile)
# CompilationEngine(infile, tokenizer)


############################################################################################################

infile = ''
inname = sys.argv[1]
cwdfiles = os.listdir('.')
jack_program_folder = []

if f'{inname}.jack' in cwdfiles:
    infile = inname
    tokenizer = Tokenizer(infile)
    symboltable = SymbolTable()
    vmwriter = VMWriter(infile)
    CompilationEngine(infile, tokenizer, symboltable, vmwriter)
else:
    jack_program_folder = os.listdir(inname)
    jack_program_folder = [os.path.splitext(file) for file in jack_program_folder]
    jack_program_folder = [file[0] for file in jack_program_folder if file[1] == '.jack']

    os.chdir(inname)

    while len(jack_program_folder) != 0:
        infile = jack_program_folder[0]
        jack_program_folder.pop(0)
        tokenizer = Tokenizer(infile)
        symboltable = SymbolTable()
        vmwriter = VMWriter(infile)
        CompilationEngine(infile, tokenizer, symboltable, vmwriter)
        



