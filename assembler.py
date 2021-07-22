import os, sys

# To translate from assembly to machine code:
# First change working directory to the directory containing the .asm file.
# Then run the assembler with the name of the file to be translated as the first command line argument.
# the .hack file will be generated in the current working directory

class Parser:
    def __init__(self, infilename):
        # opens input file and gets ready to parse it
        self.infilename = infilename
        self.infile = []

        # cleaning up any comments and empty lines in the input file and storing each line in an array
        infile = open(self.infilename + '.asm')
        for line in infile:
            line = line.strip()
            if line != '':
                if line[0] != '/':
                    newlinechar = line.find('\n')
                    if newlinechar != -1:
                        line = line[:newlinechar] + line[newlinechar + 2:]
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
        if self.currentcommand[0] == '@':
            return 'A_COMMAND'
        if self.currentcommand[0] == '(':
            return 'L_COMMAND'
        return 'C_COMMAND'

    def symbol(self):
        # returns the symbol or the decimal of the current A or L command
        if self.commandType() == 'A_COMMAND':
            return self.currentcommand[1:]
        if self.commandType() == 'L_COMMAND':
            return self.currentcommand[1:-1]
        raise Exception('This method can only be called if the current command is of type A_COMMAND or L_COMMAND')

    def dest(self):
        # returns the dest mnemonic in the current C_COMMAND
        if self.commandType() == 'C_COMMAND':
            equalindex = self.currentcommand.find('=')
            if equalindex == -1:
                return 'null'
            return self.currentcommand[:equalindex]
        raise Exception("This method can only be called if the current command is of type C_COMMAND")

    def comp(self):
        # returns the comp mnemonic in the current C_COMMAND
        if self.commandType() == 'C_COMMAND':
            equalindex = self.currentcommand.find('=')
            colonindex = self.currentcommand.find(';')
            if (equalindex != -1) & (colonindex != -1):
                return self.currentcommand[equalindex + 1:colonindex]
            if colonindex != -1:
                return self.currentcommand[:colonindex]
            if equalindex != -1:
                return self.currentcommand[equalindex + 1:]  
        raise Exception("This method can only be called if the current command is of type C_COMMAND")

    def jump(self):
        # returns the jump mnemonic in the current C_COMMAND
        if self.commandType() == 'C_COMMAND':
            colonindex = self.currentcommand.find(';')
            if colonindex == -1:
                return 'null'
            return self.currentcommand[colonindex + 1:]
        raise Exception("This method can only be called if the current command is of type C_COMMAND")

class Code:
    def __init__(self):
        self.desttable = {
                          'null': '000', 
                          'M': '001',
                          'D': '010',
                          'MD': '011',
                          'A': '100',
                          'AM': '101',
                          'AD': '110',
                          'AMD': '111'
                          }
        self.jumptable = {
                          'null': '000', 
                          'JGT': '001',
                          'JEQ': '010',
                          'JGE': '011',
                          'JLT': '100',
                          'JNE': '101',
                          'JLE': '110',
                          'JMP': '111'
                          }
        self.comptable = {
                          '0': '0101010', 
                          '1': '0111111',
                          '-1': '0111010',
                          'D': '0001100',
                          'A': '0110000',
                          '!D': '0001101',
                          '!A': '0110001',
                          '-D': '0001111',
                          '-A': '0110011',
                          'D+1': '0011111',
                          'A+1': '0110111',
                          'D-1': '0001110',
                          'A-1': '0110010',
                          'D+A': '0000010',
                          'D-A': '0010011',
                          'A-D': '0000111',
                          'D&A': '0000000',
                          'D|A': '0010101',
                          'M': '1110000',
                          '!M': '1110001',
                          '-M': '1110011',
                          'M+1': '1110111',
                          'M-1': '1110010',
                          'D+M': '1000010',
                          'D-M': '1010011',
                          'M-D': '1000111',
                          'D&M': '1000000',
                          'D|M': '1010101',
                          }
    def dest(self, input):
        return self.desttable[input]

    def comp(self, input):
         return self.comptable[input]

    def jump(self, input):
         return self.jumptable[input]

class SymbolTable:
    def __init__(self):
        self.table = {
            'SP': 0,
            'LCL': 1,
            'ARG': 2,
            'THIS': 3,
            'THAT': 4,
            'R0': 0,
            'R1': 1,
            'R2': 2,
            'R3': 3,
            'R4': 4,
            'R5': 5,
            'R6': 6,
            'R7': 7,
            'R8': 8,
            'R9': 9,
            'R10': 10,
            'R11': 11,
            'R12': 12,
            'R13': 13,
            'R14': 14,
            'R15': 15,
            'SCREEN': 16384,
            'KBD': 24576
        }
        self.available_ram_address = 16
    
    def addEntry(self, symbol, address):
        self.table[symbol] = address
        return

    def contains(self, symbol):
        if symbol in self.table.keys():
            return True
        return False

    def getAddress(self, symbol):
        return self.table[symbol]
        
asmfile = sys.argv[1] # name of .asm file to be converted taken in as command line argument
coder = Code()
symbols = SymbolTable()
hackfile = open(asmfile + '.hack', 'w')

firstparse = Parser(asmfile)
commandcount = 0

while firstparse.hasMoreCommands():
    firstparse.advance()
    if firstparse.commandType() == 'L_COMMAND':
        address = commandcount 
        symbol = firstparse.symbol()
        symbols.addEntry(symbol, address)
        continue
    commandcount += 1

secondparse = Parser(asmfile)

while secondparse.hasMoreCommands():
    secondparse.advance()
    if secondparse.commandType() == 'A_COMMAND':
        symbol = secondparse.symbol()
        if symbol.isdigit():
            aregister1 = bin(int(symbol))[2:].zfill(15)
            hackfile.write('0' + aregister1 + '\n')
        elif symbols.contains(symbol):
            address = symbols.getAddress(symbol)
            aregister2 = bin(address)[2:].zfill(15)
            hackfile.write('0' + aregister2 + '\n')
        else:
            symbols.addEntry(symbol, symbols.available_ram_address)
            aregister3 = bin(symbols.available_ram_address)[2:].zfill(15)
            hackfile.write('0' + aregister3 + '\n')
            symbols.available_ram_address += 1
    
    if secondparse.commandType() == 'C_COMMAND':
        dest = coder.dest(secondparse.dest())
        comp = coder.comp(secondparse.comp())
        jump = coder.jump(secondparse.jump())
        hackfile.write('111' + comp + dest + jump + '\n')
    
    continue

hackfile.close()














