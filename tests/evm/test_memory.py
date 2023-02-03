import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
    RWTableTag,
    CallContextFieldTag,
)
from zkevm_specs.util import rand_fq, RLC, U64, GAS_COST_COPY, memory_expansion, memory_word_size

TESTING_DATA = (
    (
        Opcode.MLOAD,
        0,
        0xFF,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MLOAD,
        1,
        0xFF00,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MSTORE,
        0,
        0xFF,
        bytes.fromhex("00000000000000000000000000000000000000000000000000000000000000FF"),
    ),
    (
        Opcode.MSTORE,
        1,
        0xFF,
        bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000FF"),
    ),
)


@pytest.mark.parametrize("opcode, offset, value, memory", TESTING_DATA)
def test_memory(opcode: Opcode, offset: int, value: int, memory: bytes):
    randomness = rand_fq()

    offset_rlc = RLC(offset, randomness)
    value_rlc = RLC(value, randomness)
    call_id = 1
    curr_memory_size = 0
    length = offset

    is_mload = opcode == Opcode.MLOAD
    is_mstore8 = opcode == Opcode.MSTORE8
    is_store = 1 - is_mload
    is_not_mstore8 = 1 - is_mstore8

    bytecode = Bytecode()
    rw_dictionary = RWDictionary(1).stack_read(call_id, 1022, offset_rlc)
    (bytecode, rw_dictionary) = (
        (bytecode.mload(offset_rlc), rw_dictionary.stack_write(call_id, 1022, value_rlc))
        if is_mload
        else (
            bytecode.mstore(offset_rlc, value_rlc),
            rw_dictionary.stack_read(call_id, 1023, value_rlc),
        )
    )

    bytecode = bytecode.stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)
    rw_dictionary = rw_dictionary.call_context_read(call_id, CallContextFieldTag.TxId, call_id)

    if is_not_mstore8:
        for idx in range(32):
            if is_mload:
                rw_dictionary.memory_read(call_id, curr_memory_size + idx, memory[idx])
            else:
                rw_dictionary.memory_write(call_id, curr_memory_size + idx, memory[idx])

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_dictionary.rws,
    )

    # print(sorted(tables.rw_table, key=lambda x: x.rw_counter.n))

    next_mem_size, memory_gas_cost = memory_expansion(curr_memory_size, offset + 32)
    gas = Opcode.MLOAD.constant_gas_cost() + memory_gas_cost

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.MEMORY,
                rw_counter=1,
                call_id=call_id,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=33,
                stack_pointer=1022,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=35,
                call_id=call_id,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=34,
                stack_pointer=1022 if is_mload else 1023,
                memory_size=next_mem_size,
                gas_left=0,
            ),
        ],
    )
