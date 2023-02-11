from ..instruction import Instruction
from ...util import FQ, Bn256AddGas, G1, point_add
from ..table import (
    CallContextFieldTag,
    FixedTableTag,
    CopyDataTypeTag,
    RW,
)


def bn256Add(instruction: Instruction):
    result_length = FQ(64)
    gas_cost = FQ(Bn256AddGas)

    instruction.fixed_lookup(
        FixedTableTag.PrecompileInfo,
        FQ(instruction.curr.execution_state),
        instruction.call_context_lookup(CallContextFieldTag.CalleeAddress, RW.Read),
        FQ(Bn256AddGas),
    )
    caller_id = instruction.call_context_lookup(CallContextFieldTag.CallerId, RW.Read)
    call_data_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset, RW.Read)
    return_data_offset = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataOffset, RW.Read
    )
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.ReturnDataLength, RW.Read
    )

    # get two points from input
    a = bytearray(
        [instruction.memory_lookup(RW.Read, call_data_offset.expr() + idx).n for idx in range(64)]
    )
    b = bytearray(
        [
            instruction.memory_lookup(RW.Read, call_data_offset.expr() + idx).n
            for idx in range(64, 128)
        ]
    )

    # convert input to points
    point_a = point_b = G1()
    point_a.unmarshal(a)
    point_b.unmarshal(b)

    # add two points and get result
    point_c = point_add(point_a, point_b)
    result = point_c.marshal()

    # store result to memory
    for idx in range(64):
        instruction.is_equal(
            instruction.memory_lookup(RW.Write, return_data_offset.expr() + idx), FQ(result[idx])
        )

    instruction.copy_lookup(
        caller_id,
        CopyDataTypeTag.Memory,
        instruction.curr.call_id,
        CopyDataTypeTag.Memory,
        return_data_offset,
        return_data_offset + result_length,
        FQ(0),
        result_length,
        instruction.curr.rw_counter + instruction.rw_counter_offset,
    )

    instruction.rw_counter_offset += 2 * int(result_length)

    instruction.step_state_transition_to_restored_context(
        rw_counter_delta=instruction.rw_counter_offset,
        return_data_offset=return_data_offset,
        return_data_length=return_data_length,
        gas_left=instruction.curr.gas_left - gas_cost,
        caller_id=caller_id,
    )
