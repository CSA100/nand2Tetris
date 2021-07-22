import os, sys

class Parser: 
    #parsers a single .vm input file 
    def __init__(self, infilename):
        # opens input file and gets ready to parse it
        self.infilename = infilename
        self.infile = []

        # cleaning up any comments and empty lines in the input file and storing each line in an array
        infile = open(self.infilename + '.vm')
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
        infile.close()

        self.totalcommandcount = len(self.infile)
        self.currentcommandcount = 0
        self.currentcommand = ''
    
    def hasMoreCommands(self):
        # checks if there are more commands left to be parsed
        if(self.currentcommandcount < self.totalcommandcount):
            return True
        return False
    
    def advance(self):
        # reads the next command of the input and makes it the current command
        self.currentcommand = self.infile[self.currentcommandcount]
        self.currentcommandcount += 1
    
    def commandType(self):
        # returns the type of the current command
        if self.currentcommandcount == 0:
            raise Exception('Please advance the parser to the first command before calling this method')

        arithmetic_strings = ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']

        currentCommand = self.currentcommand.split()[0]

        if any(currentCommand == string for string in arithmetic_strings):
            return 'C_ARITHMETIC'
    
        elif 'push' == currentCommand:
            return 'C_PUSH'
        elif 'pop' == currentCommand:
            return 'C_POP'

        elif 'label' == currentCommand:
            return 'C_LABEL'
        elif 'if-goto' == currentCommand:
            return 'C_IF'
        elif 'goto' == currentCommand:
            return 'C_GOTO'

        elif 'function' == currentCommand:
            return 'C_FUNCTION'
        elif 'return' == currentCommand:
            return 'C_RETURN'
        elif 'call' == currentCommand:
            return 'C_CALL'

        raise Exception('Command type not known.')
    
    def arg1(self):
        # Returns the first argument of the current command.
        # In the case of C_ARITHMETIC, the command itself is returned.
        # Should not be called if the current command in C_RETURN
        split_command = self.currentcommand.split()

        arg1 = split_command[0]

        if len(split_command) > 1:
            arg1 = split_command[1]
        
        return arg1

    def arg2(self):
        # Returns the second argument of the current command
        # Should only be called if command is one of the following types:
        # C_PUSH, C_POP, C_FUNCTION, C_CALL
        return int(self.currentcommand.split()[2])

class CodeWriter:
    def __init__(self, outfilename):
        self.filename = ''
        self.outfile = open(outfilename + '.asm', 'w')

        self.logic_label_number = 0
        self.logic_available_label = f"VMLABEL{self.logic_label_number}"

        self.label_prefix = '$'

        self.static_prefix = self.filename
        self.static_index = 0

    def setFileName(self, filename):
        # informs the CodeWriter that the current file being parsed has been changed
        self.filename = filename
        self.static_prefix = self.filename
        self.static_index = 0

    def writeArithmetic(self, command):
        # arg1 in variable names refers to the top value in the stack
        # arg2 refers to the second highest value

        set_a_to_arg1_address = '@SP\nA=M-1\n'                 # useful for unary operators

        set_d_to_arg1_and_decrement_SP = '@SP\nAM=M-1\nD=M\n'
        set_a_to_arg2_address = 'A=A-1\n'                      # use only after previous command
                                                               # A should be set to SP address first
        set_d_to_arg2_minus_arg1 = 'D=M-D\n'                   # can be called for checking inequalities
        set_m_to_true = 'M=-1\n'
        set_m_to_false = 'M=0\n'

        end_label = f'({self.logic_available_label})\n'
        set_a_to_end_label = f'@{self.logic_available_label}\n'

        def nextAvailableLabel(self):
        # changes the available label to a value that has not been used previously
            self.logic_label_number += 1
            self.logic_available_label = f"VMLABEL{self.logic_label_number}"
            return

        if command == 'neg':
            self.outfile.write(set_a_to_arg1_address + 'M=-M\n')
        elif command == 'not':
            self.outfile.write(set_a_to_arg1_address + 'M=!M\n')
        elif command == 'add':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + 'M=D+M\n')
        elif command == 'sub':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + 'M=M-D\n')
        elif command == 'or':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + 'M=D|M\n')
        elif command == 'and':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + 'M=D&M\n')
        elif command == 'eq':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + set_d_to_arg2_minus_arg1 
                               + set_m_to_true + set_a_to_end_label + 'D;JEQ\n' + '@SP\n' 
                               + 'A=M-1\n' + set_m_to_false + end_label)
            nextAvailableLabel(self)
        elif command == 'gt':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + set_d_to_arg2_minus_arg1 
                               + set_m_to_true + set_a_to_end_label + 'D;JGT\n' + '@SP\n' 
                               + 'A=M-1\n' + set_m_to_false + end_label)
            nextAvailableLabel(self)
        elif command == 'lt':
            self.outfile.write(set_d_to_arg1_and_decrement_SP + set_a_to_arg2_address + set_d_to_arg2_minus_arg1 
                               + set_m_to_true + set_a_to_end_label + 'D;JLT\n' + '@SP\n' 
                               + 'A=M-1\n' + set_m_to_false + end_label)
            nextAvailableLabel(self)
        else:
            raise Exception("Arithmetic Command Not Found")

    def writePushPop(self, command, segment, index):

        push_d_to_stack_and_increment_SP = '@SP\nA=M\nM=D\n@SP\nM=M+1\n'
        pop_stack_to_d_and_decrement_SP = '@SP\nAM=M-1\nD=M\n'
        if command == 'C_PUSH':
            if segment == 'constant':
                self.outfile.write('@' + str(index) + '\nD=A\n' + push_d_to_stack_and_increment_SP)
            elif segment == 'temp':
                self.outfile.write('@' + str(index) + '\nD=A\n@5\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            elif segment == 'argument':
                self.outfile.write('@' + str(index) + '\nD=A\n@ARG\nA=M\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            elif segment == 'local':
                self.outfile.write('@' + str(index) + '\nD=A\n@LCL\nA=M\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            elif segment == 'this':
                self.outfile.write('@' + str(index) + '\nD=A\n@THIS\nA=M\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            elif segment == 'that':
                self.outfile.write('@' + str(index) + '\nD=A\n@THAT\nA=M\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            elif segment == 'pointer':
                self.outfile.write('@' + str(index) + '\nD=A\n@3\nA=D+A\nD=M\n' + 
                                    push_d_to_stack_and_increment_SP)
            # elif segment == 'static':
            #     self.outfile.write('@' + str(index) + '\nD=A\n@16\nA=D+A\nD=M\n' + 
            #                         push_d_to_stack_and_increment_SP)
            elif segment == 'static':
                self.outfile.write(f"@{self.static_prefix}.{index}\n" + 'D=M\n' + 
                                    push_d_to_stack_and_increment_SP)
                self.static_index += 1
            else:
                raise Exception('Push Command Not Found')
            
        elif command == 'C_POP':
            if segment == 'temp':
                self.outfile.write('@' + str(index) + '\nD=A\n@5\nD=D+A\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'argument':
                self.outfile.write('@' + str(index) + '\nD=A\n@ARG\n\nD=D+M\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'local':
                self.outfile.write('@' + str(index) + '\nD=A\n@LCL\n\nD=D+M\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'this':
                self.outfile.write('@' + str(index) + '\nD=A\n@THIS\n\nD=D+M\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'that':
                self.outfile.write('@' + str(index) + '\nD=A\n@THAT\n\nD=D+M\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'pointer':
                self.outfile.write('@' + str(index) + '\nD=A\n@3\nD=D+A\n@13\nM=D\n' + 
                                    pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            # elif segment == 'static':
            #     self.outfile.write('@' + str(index) + '\nD=A\n@16\nD=D+A\n@13\nM=D\n' + 
            #                         pop_stack_to_d_and_decrement_SP + '\n@13\nA=M\nM=D\n')
            elif segment == 'static':
                self.outfile.write(pop_stack_to_d_and_decrement_SP + 
                                    f"@{self.static_prefix}.{index}\n" + 'M=D\n')
                self.static_index += 1
            else:
                raise Exception('Pop Command Not Found')
        else:
            raise Exception('Push Pop Command Not Found')
    
    def writeLabel(self, label):
        self.outfile.write('(' + self.label_prefix + label + ')\n')

    def writeGoto(self, label):
        self.outfile.write('@' + self.label_prefix + label + '\n0;JMP\n')

    def writeIf(self, label):
        self.outfile.write('@SP\nAM=M-1\nD=M\n@' + self.label_prefix + label + '\nD;JNE\n')

    def writeFunction(self, functionName, numLocals):
        self.label_prefix = functionName + '$'
        self.outfile.write('(' + functionName + ')\n')
        for i in range(numLocals):
            self.writePushPop('C_PUSH', 'constant', 0)

    def writeCall(self, functionName, numArgs):

        def nextAvailableLabel(self):
            # changes the available label to a value that has not been used previously
            self.logic_label_number += 1
            self.logic_available_label = f"VMLABEL{self.logic_label_number}"
            return
    
        return_label = self.logic_available_label
        nextAvailableLabel(self)

        # push return address 
        self.outfile.write(f'@{return_label}\n' + 'D=A\n' + '@SP\nA=M\nM=D\n@SP\nM=M+1\n')

        # push LCL
        self.outfile.write('@LCL\nD=M\n' + '@SP\nA=M\nM=D\n@SP\nM=M+1\n')

        # push ARG
        self.outfile.write('@ARG\nD=M\n' + '@SP\nA=M\nM=D\n@SP\nM=M+1\n')

        # push THIS
        self.outfile.write('@THIS\nD=M\n' + '@SP\nA=M\nM=D\n@SP\nM=M+1\n') 

        # push THAT
        self.outfile.write('@THAT\nD=M\n' + '@SP\nA=M\nM=D\n@SP\nM=M+1\n')    

        # set ARG to SP-numArgs-5
        self.outfile.write(f'@{numArgs}\nD=A\n@5\nD=D+A\n@SP\nD=M-D\n@ARG\nM=D\n' )

        # set LCL = SP
        self.outfile.write('@SP\nD=M\n@LCL\nM=D\n')

        # transfer control to called function/ goto functionName
        self.outfile.write(f'@{functionName}\n0;JMP\n')

        # declare label for the return address
        self.outfile.write(f"({return_label})\n")
    
    def writeReturn(self):
        # r15 is used to store 'frame'/ LCL's current value
        self.outfile.write('@LCL\nD=M\n@15\nM=D\n')

        # r14 is used to store the return address
        self.outfile.write('@5\nA=D-A\nD=M\n@14\nM=D\n')

        # take the return value from the function and place it at the arg 0 position
        self.writePushPop('C_POP', 'argument', 0)

        # restore stack pointer to arg 1 position
        self.outfile.write('@ARG\nD=M+1\n@SP\nM=D\n')

        # restore THAT
        self.outfile.write('@R15\nA=M-1\nD=M\n@THAT\nM=D\n')

        # restore THIS
        self.outfile.write('@R15\nD=M\n@2\nA=D-A\nD=M\n@THIS\nM=D\n')

        # restore ARG
        self.outfile.write('@R15\nD=M\n@3\nA=D-A\nD=M\n@ARG\nM=D\n')

        # restore LCL
        self.outfile.write('@R15\nD=M\n@4\nA=D-A\nD=M\n@LCL\nM=D\n')

        # goto return address
        self.outfile.write('@R14\nA=M\n0;JMP\n')


    def close(self):
        self.outfile.close()

##########################################################

infile = ''
inname = sys.argv[1]
cwdfiles = os.listdir('.')
vm_program_folder = []

if f'{inname}.vm' in cwdfiles:
    infile = inname
    parser = Parser(infile)
else:
    vm_program_folder = os.listdir(inname)
    vm_program_folder = [os.path.splitext(file) for file in vm_program_folder]
    vm_program_folder = [file[0] for file in vm_program_folder if file[1] == '.vm']
    os.chdir(inname)
    if 'Sys' in vm_program_folder:
        infile = 'Sys'
        vm_program_folder.remove('Sys')
    else:
        infile = vm_program_folder[0]
        vm_program_folder.pop(0)
    parser = Parser(infile)
    os.chdir('../')

code_writer = CodeWriter(inname)
code_writer.setFileName(infile)

##### VM Bootstrap Code #####

# # Set SP to 256
code_writer.outfile.write('@256\nD=A\n@SP\nM=D\n')

# # Call Sys.init
code_writer.writeCall('Sys.init', 0)

##### VM Bootstrap Code #####

while parser.hasMoreCommands():
    parser.advance()
    commandType = parser.commandType()
    if commandType == 'C_ARITHMETIC':
        code_writer.writeArithmetic(parser.arg1())
    if commandType == 'C_PUSH' or commandType == 'C_POP':
        code_writer.writePushPop(commandType, parser.arg1(), parser.arg2())

    if commandType == 'C_LABEL':
        code_writer.writeLabel(parser.arg1())
    if commandType == 'C_GOTO':
        code_writer.writeGoto(parser.arg1())
    if commandType == 'C_IF':
        code_writer.writeIf(parser.arg1())    
    
    if commandType == 'C_FUNCTION':
        code_writer.writeFunction(parser.arg1(), parser.arg2())
    if commandType == 'C_CALL':
        code_writer.writeCall(parser.arg1(), parser.arg2())
    if commandType == 'C_RETURN':
        code_writer.writeReturn()

if len(vm_program_folder) == 0:
    code_writer.close()
else:
    while len(vm_program_folder) != 0:
        infile = vm_program_folder[0]
        vm_program_folder.pop(0)
        os.chdir(inname)
        parser = Parser(infile)
        os.chdir('../')
        code_writer.setFileName(infile)
        while parser.hasMoreCommands():
            parser.advance()
            commandType = parser.commandType()
            if commandType == 'C_ARITHMETIC':
                code_writer.writeArithmetic(parser.arg1())
            if commandType == 'C_PUSH' or commandType == 'C_POP':
                code_writer.writePushPop(commandType, parser.arg1(), parser.arg2())

            if commandType == 'C_LABEL':
                code_writer.writeLabel(parser.arg1())
            if commandType == 'C_GOTO':
                code_writer.writeGoto(parser.arg1())
            if commandType == 'C_IF':
                code_writer.writeIf(parser.arg1())    
            
            if commandType == 'C_FUNCTION':
                code_writer.writeFunction(parser.arg1(), parser.arg2())
            if commandType == 'C_CALL':
                code_writer.writeCall(parser.arg1(), parser.arg2())
            if commandType == 'C_RETURN':
                code_writer.writeReturn()
    code_writer.close()


