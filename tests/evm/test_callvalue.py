import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import RLC, U256
from common import rand_fq


TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
    0xF0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0F,
)


@pytest.mark.parametrize("callvalue", TESTING_DATA)
def test_callvalue(callvalue: U256):
    randomness = rand_fq()

    bytecode = Bytecode().callvalue()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.Value, RLC(callvalue, randomness))
            .stack_write(1, 1023, RLC(callvalue, randomness))
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CALLVALUE,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
