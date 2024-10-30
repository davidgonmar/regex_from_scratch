from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EBX
from keystone import Ks, KS_ARCH_X86, KS_MODE_32
from keystone.keystone import *
from keystone import *
from regex import compile_regex, NFA, EPSILON

address = 0x1000


# generates assembly code for the regex
# eax -> adress
# exb -> length
def generate_assembly(nfa: NFA, address):
    assembly = []
    state_to_label = {}
    state_to_label[nfa.start] = "state_start"
    staten = 1
    assembly.append("jmp state_start")
    assembly.append("finish_accept:")
    # assembly.append("  ; we finished")
    # return success
    assembly.append("  mov ebx, 1")
    assembly.append("  ret")

    assembly.append("finish_fail:")
    # return fail
    assembly.append("  mov ebx, 0")
    assembly.append("  ret")

    for state in nfa.states:
        if state not in state_to_label:
            state_to_label[state] = f"state{staten}"
            if nfa.is_accept(state):
                state_to_label[state] += "_accept"
            staten += 1

    for state, state_address in state_to_label.items():
        assembly.append(state_address + ":")
        # assembly.append("  ; check if we finished")
        assembly.append("  cmp ecx, 0")
        if nfa.is_accept(state):
            assembly.append("  je finish_accept")
        else:
            assembly.append("  je finish_fail")
        for symbol, next_states in nfa.trasitions[state].items():
            for next_state in next_states:
                next_state_address = state_to_label[next_state]

                if symbol != EPSILON:
                    # assembly.append("  ; next state")

                    assembly.append("  mov edx, eax")
                    assembly.append("  add eax, 1")
                    assembly.append("  sub ecx, 1")
                    assembly.append(f"  cmp byte ptr [edx], '{symbol}'")
                    assembly.append(f"  je {next_state_address}")
                else:
                    pass
        # epsilon handling
        reachable_eps = nfa.epsilon_closure({state})
        reachable_eps = reachable_eps - {state}
        for next_state in reachable_eps:
            next_state_address = state_to_label[next_state]
            assembly.append(f"  jmp {next_state_address}")
    return assembly, address


def execute_assembly(assembly, address, string):
    print("\n".join(assembly))

    # Initialize Keystone for assembling the assembly code
    ks = Ks(KS_ARCH_X86, KS_MODE_32)
    machine_code, _ = ks.asm("\n".join(assembly))
    print(f"Machine code: {machine_code}")

    # Initialize Unicorn for emulation
    emu = Uc(UC_ARCH_X86, UC_MODE_32)

    # Calculate sizes
    code_size = len(machine_code)
    string_size = len(string)

    # Ensure address is aligned
    if address % 0x1000 != 0:
        raise ValueError("Address must be aligned to 4096 (0x1000)")

    # Total size needs to be a multiple of the page size
    total_size = (
        (code_size + string_size + 0xFFF) // 0x1000
    ) * 0x1000  # Align to the next page

    # Map memory for code and string
    emu.mem_map(address, total_size)

    # Write the machine code and the string to memory
    emu.mem_write(address, bytes(machine_code))
    emu.mem_write(address + code_size, str.encode(string))

    # Set registers
    emu.reg_write(
        UC_X86_REG_EAX, address + code_size
    )  # Set EAX to the start of the code
    emu.reg_write(UC_X86_REG_ECX, string_size)  # Set ECX to the length of the string
    emu.reg_write(UC_X86_REG_EBX, 10)
    print(emu.reg_read(UC_X86_REG_ECX))
    print(emu.reg_read(UC_X86_REG_EBX))
    print(emu.reg_read(UC_X86_REG_EAX))
    print(
        "decoded content of eax: ",
        emu.mem_read(emu.reg_read(UC_X86_REG_EAX), 1).decode("utf-8"),
    )
    # Start emulation
    try:
        emu.emu_start(address, address + code_size)
    except Exception as e:
        print(e)

    print(emu.reg_read(UC_X86_REG_ECX))
    print(emu.reg_read(UC_X86_REG_EBX))
    print(emu.reg_read(UC_X86_REG_EAX))

    # Read memory of EAX
    print("decoded content of eax: ", emu.mem_read(emu.reg_read(UC_X86_REG_EAX), 1))
    return emu.reg_read(UC_X86_REG_EBX)


def regex(pattern, string):
    nfa = compile_regex(pattern)
    nfa.vizualize()
    assembly, address = generate_assembly(nfa, 0x1000)
    return execute_assembly(assembly, address, string)


print(regex("a*", "aa"))
