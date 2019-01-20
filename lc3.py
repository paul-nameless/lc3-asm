#!/usr/bin/env python3
import array
import sys
import os

from collections import namedtuple


MAX_LINE_LENGTH = 4096
UINT16_MAX = 2 ** 16


REGS = {
    'R0': 0x0,
    'R1': 0x1,
    'R2': 0x2,
    'R3': 0x3,
    'R4': 0x4,
    'R5': 0x5,
    'R6': 0x6,
    'R7': 0x7,
}

TRAPS = {
    'GETC': 0x20,
    'OUT': 0x21,
    'PUTS': 0x22,
    'IN': 0x23,
    'PUTSP': 0x24,
    'HALT': 0x25,
}

OPS = {
    # 0x0
    'BR':  0x0,    # 0b0 branch
    # 'BR':  0b0000000,    # 0b0 branch
    # 'BRn': 0b0000100,    # 0b0 branch if n
    # 'BRz': 0b0000010,    # 0b0 branch
    # 'BRp': 0b0000001,    # 0b0 branch
    # 'BRzp': 0b0000011,    # 0b0 branch
    # 'BRnp': 0b0000101,    # 0b0 branch
    # 'BRnz': 0b0000110,    # 0b0 branch
    # 'BRnzp': 0b0000111,    # 0b0 branch
    'BRn': 0x0,    # 0b0 branch if n
    'BRz': 0x0,    # 0b0 branch
    'BRp': 0x0,    # 0b0 branch
    'BRzp': 0x0,    # 0b0 branch
    'BRnp': 0x0,    # 0b0 branch
    'BRnz': 0x0,    # 0b0 branch
    'BRnzp': 0x0,    # 0b0 branch

    'ADD': 0x1,   # 0b1 add
    'LD': 0x2,    # 0b10 load
    'ST': 0x3,    # 0b11 store
    'JSR': 0x4,   # 0b100 jump register
    'JSRR': 0x4,  # 0b100 jump register
    'AND': 0x5,   # 0b101 bitwise and
    'LDR': 0x6,   # 0b110 load register
    'STR': 0x7,   # 0b111 store register
    'RTI': 0x8,   # 0b1000 unused
    'NOT': 0x9,   # 0b1001 bitwise not
    'LDI': 0xA,   # 0b1010 load indirect
    'STI': 0xB,   # 0b1011 store indirect
    'RET': 0xC,   # 0b1100 return
    'JMP': 0xC,   # 0b1100 jump
    'RES': 0xD,   # 0b1101 reserved (unused)
    'LEA': 0xE,   # 0b1110 load effective address
    'TRAP': 0xF,  # ob1111 execute trap

    **TRAPS
}


DOTS = {
    '.ORIG': None,  # write handlers?
    '.END': None,
    '.FILL': None,
    '.BLKW': None,
    '.STRINGZ': None
}


class Type:
    LABEL = 'label'
    OP = 'op'
    DOT = 'dot'
    CONST = 'const'
    REG = 'reg'
    STR = 'str'


Token = namedtuple('Tok', 't, v')


def tok_op_args(line):
    args = []
    for arg in line.split(','):
        arg = arg.strip()
        if not arg:
            continue
        if arg in REGS:
            args.append(Token(Type.REG, arg))
        elif arg.startswith('#'):
            args.append(Token(Type.CONST, int(arg[1:])))
        elif arg.startswith('x'):
            args.append(Token(Type.CONST, int('0' + arg, 16)))
        elif arg.startswith('b'):
            args.append(Token(Type.CONST, int('0' + arg, 2)))
        else:
            args.append(Token(Type.LABEL, arg))
    return args


def tok_dot_args(arg):
    arg = arg.strip()
    if not arg:
        return []
    if arg.startswith('"'):
        arg = arg.replace('\\n', '\n')
        return [Token(Type.STR, arg.replace('"', ''))]
    elif arg.startswith('\''):
        return [Token(Type.STR, arg.replace('\'', ''))]
    elif arg.startswith('x'):
        return [Token(Type.CONST, int('0' + arg, 16))]
    elif arg.startswith('b'):
        return [Token(Type.CONST, int('0' + arg, 2))]
    elif arg.startswith('#'):
        return [Token(Type.CONST, int(arg[1:], 10))]
    else:
        return [Token(Type.CONST, int(arg, 10))]
    return []


def tok(line):
    line = line.strip()
    if not line or line.startswith(';'):
        return None
    line, *_ = line.split(';', maxsplit=1)
    res = line.split(' ', maxsplit=1)

    if len(res) == 1:
        token, other = res[0].strip(), ''
    else:
        token, other = res[0].strip(), res[1].strip()

    if token in OPS:
        return [Token(Type.OP, token)] + tok_op_args(other)
    elif token.startswith('.'):
        return [Token(Type.DOT, token.upper())] + tok_dot_args(other)
    else:
        if other:
            return [Token(Type.LABEL, token)] + tok(other)
        else:
            return [Token(Type.LABEL, token)]


def check_syntax(tokens):
    pass


def asm_pass_one(code):
    symbol_table = {}
    lines = []
    lc = 0  # location counter
    for line_number, line in enumerate(code.splitlines(), 1):
        # assert len(line) > MAX_LINE_LENGTH, 'line is too long'

        tokens = tok(line)
        if not tokens:
            continue
        if tokens[0].v == '.END':
            break

        print(f'{hex(lc):>6} ({line_number}): {line.strip():<44} | {tokens}')

        check_syntax(tokens)

        if tokens[0].t == Type.LABEL:
            symbol_table[tokens[0].v] = lc

        if tokens[0].t != Type.LABEL:
            if tokens[0].v == '.ORIG':
                lc = tokens[1].v
            elif tokens[0].t == Type.OP:
                lc += 1
            elif tokens[0].v == '.BLKW':
                lc += tokens[1].v
        else:
            if tokens[1].v == '.STRINGZ':
                lc += len(tokens[2].v) + 1
            if tokens[1].v == '.FILL':
                lc += 1
            if tokens[1].t == Type.OP:
                lc += 1

        lines.append((tokens, lc))

    print(f'{"":>6}  {".END":<44}')
    print('LC:', hex(lc))
    return symbol_table, lines


def encode_op(tokens, symbol_table, lc):
    if tokens[0].v in TRAPS:
        return OPS['TRAP'] << 12 | TRAPS[tokens[0].v]
    opcode = OPS[tokens[0].v] << 12
    if tokens[0].v == 'RTI':
        return opcode
    if tokens[0].v == 'TRAP':
        return opcode | tokens[1].v & 0b11111111
    if tokens[0].v == 'RET':
        return opcode | 0b111 << 6
    if tokens[0].v == 'JMP':
        return opcode | REGS[tokens[1].v] << 6
    if tokens[0].v == 'NOT':
        return opcode | REGS[tokens[1].v] << 9 | REGS[tokens[2].v] << 6 | 0x3f
    if tokens[0].v == 'JSR':
        pcoffset11 = ((symbol_table[tokens[1].v] - lc) & 0b11111111111)
        return opcode | 1 << 11 | pcoffset11
    if tokens[0].v == 'JSRR':
        return opcode | REGS[tokens[1].v] << 6
    if tokens[0].v in ('LDR', 'STR'):
        dr = REGS[tokens[1].v] << 9
        base_r = REGS[tokens[2].v] << 6
        assert tokens[3].v < 2 ** 5
        offset6 = ((UINT16_MAX + tokens[3].v) & 0b111111)
        return opcode | dr | base_r | offset6
    if tokens[0].v in ('ADD', 'AND'):
        dr = REGS[tokens[1].v] << 9
        sr1 = REGS[tokens[2].v] << 6
        if tokens[3].t == Type.REG:
            sr2 = REGS[tokens[3].v]
            return opcode | dr | sr1 | sr2
        else:
            assert tokens[3].v < 2 ** 5
            imm5 = ((UINT16_MAX + tokens[3].v) & 0b11111)
            return opcode | dr | sr1 | 1 << 5 | imm5
    if tokens[0].v.startswith('BR'):
        if tokens[0].v == 'BR':
            opcode |= 1 << 11
            opcode |= 1 << 10
            opcode |= 1 << 9

        if 'n' in tokens[0].v:
            opcode |= 1 << 11
        if 'z' in tokens[0].v:
            opcode |= 1 << 10
        if 'p' in tokens[0].v:
            opcode |= 1 << 9
        return opcode | ((symbol_table[tokens[1].v] - lc) & 0b111111111)
    if tokens[0].v in ('LD', 'LEA', 'LDI', 'ST', 'STI'):
        dr = REGS[tokens[1].v] << 9
        return opcode | dr | ((symbol_table[tokens[2].v] - lc) & 0b111111111)


def asm_pass_two(symbol_table, lines):
    print('####-PASS TWO-####')
    data = array.array("H", [])
    data.append(lines[0][0][1].v)
    for tokens, lc in lines[1:]:
        print(tokens)
        if tokens[0].t == Type.DOT and tokens[0].v == '.END':
            break
        if tokens[0].t == Type.OP:
            print('ENCODE_OP:', hex(encode_op(tokens, symbol_table, lc)))
            data.append(encode_op(tokens, symbol_table, lc))
        if tokens[0].v == '.BLKW':
            print('ENCODE_BLKW:')
            for _ in range(tokens[1].v):
                data.append(0x0)
        if tokens[0].t == Type.LABEL:
            if tokens[1].v == '.STRINGZ':
                print('ENCODE_STRINGZ', tokens[2].v)
                encoded = tokens[2].v.encode()
                for c in encoded:
                    data.append(c)
                data.append(0)

            if tokens[1].v == '.FILL':
                print('ENCODE_FILL_OP:', tokens[2].v)
                data.append(tokens[2].v)
            elif tokens[1].t == Type.OP:
                print('ENCODE_LABEL_OP:', hex(
                    encode_op(tokens[1:], symbol_table, lc)))
                data.append(encode_op(tokens[1:], symbol_table, lc))

    data.byteswap()
    return data


def main():
    if len(sys.argv) < 2:
        print('lc3.py [image-file]')
        exit(2)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print('No such file')
        exit(1)

    with open(file_path) as f:
        code = f.read()

    symbol_table, lines = asm_pass_one(code)
    print('Pass one finished')
    print('Symbol_Table:', {a: hex(b) for a, b in symbol_table.items()})
    # exit(0)

    bin_data = asm_pass_two(symbol_table, lines)
    print(bin_data.tobytes().hex())
    file_name = os.path.splitext(file_path)[0]
    file_name = f'{file_name}-out.obj'

    with open(file_name, 'wb') as f:
        f.write(bin_data.tobytes())
    print('Saved', file_name)


if __name__ == '__main__':
    main()
