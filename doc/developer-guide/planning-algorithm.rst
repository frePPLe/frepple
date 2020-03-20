==================
Planning algorithm
==================

Different solvers and algorithms can be used with the frePPle models. It is
possible to build create extensions to the solver, or to create a completely
new solver altogether. The solvers can be loaded as plugin modules without
touching or recompiling the main application.

FrePPLe comes with a default solver, which implements a heuristic search
algorithm.

The algorithm solves demand per demand. All demands are first sorted based on
a) their priority (lower values first) and b) their due date (earlier due dates
first). When planning a single demand, the algorithm basically consists of a
set of recursive functions structured in a ask-reply pattern, as illustrated
in the example below. The indention is such that the ask and its matching
reply are represented at the same level.

The ask in each of the above steps consists of 1) ask-quantity and 2) ask-date.
The reply used in each of the above steps consists of 1) reply-quantity and 2)
reply-date. The reply-quantity represents how much of the requested quantity
can be made available at the requested date. The reply-date is useful when the
ask can not -or only partially- be met: it then indicates the earliest date
when the missing quantity might be feasible.


**Pseudo-code of the algorithm**:

    | Every demand has a certain delivery operation associated with it, either
      directly or indirectly by specifying a delivery operation for the
      requested item.
    | The demand **asks this operation** for the requested quantity on the
      due date of the demand.

        (*) The operation first checks for the lead time constraints.

        The operation will **ask each of the loads** to verify the
        capacity availability.

            A load passes on the question and **asks the resource**.

                 The **resource replies** whether the capacity is
                 available or not.

            The **load replies** the result back to operation.

        The operation will **ask each of the flows** to check the availability
        of consumed materials.

            A flow passes on the question too and **asks the buffer**.

                | The buffer checks the inventory situation.
                | If material is available no further recursion is required.
                | If the required material isn’t available the buffer will
                  **ask an operation** for a new replenishment.
                | Each buffer has a field indicating which operation is to
                  be used to generate replenishments.
                | Depending on the buffer inventory profile, safety stock
                  requirements, etc... the operation may be asked for different
                  quantities and on different dates than the original demand.

                    When an operation is asked to generate a replenishment it
                    evaluates the lead time, material and capacity constraints.
                    This results in a recursive ask-sequence similar as the one
                    starting with the line marked with (*)

                        ...

                        | The maximum recursion depth will be the same as the
                          number of levels in the bill-of-material of the end
                          item.
                        | In some cases the iteration can be stopped at an
                          intermediate level.
                        | Eg. When sufficient inventory is
                          found in a buffer and no replenishment needs to be
                          asked: a positive reply can be returned immediately.
                        | Eg. When an operation would need to be planned in the
                          past (ie lead time constraint violated) a negative
                          reply can be returned immediately.

                    The operation collects the replies from all its flows,
                    loads and -indirectly- from all entities nested at the
                    deeper recursion levels. A final **reply of the operation**
                    is generated.

            Based on the reply of the replenishing operation the buffer
            evaluates whether or not the replenishments are possible, and
            **replies back to the flow**. Sometimes a buffer may need to ask
            multiple times for a replenishment before an answer can be returned.

        The flow picks up the buffer reply and **replies to the operation**.

    From the reply of all its loads and flows the operation returns a **reply**
    **to the demand**. The interaction between material, lead time and capacity
    constraints is pretty complex and an operation may require several
    ask-reply iterations over its flows and loads before a final answer can
    be returned.

    The answer of the operation indicates how much of the requested demand
    quantity can be satisfied on the requested date. Depending on the planning
    result and the demand parameters (such as allow/disallow satisfying the
    demand late or in multiple deliveries) we can now decide to commit all
    operation plans created during the whole ask-reply sequence.

    If we’re not happy with the reply the operation plans created are undone
    again and we can go back to the first step and ask for the remaining
    material or at a later date.
