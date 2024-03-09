from pathlib import Path

import typer
from dumbo_asp.primitives.models import Model
from dumbo_asp.primitives.programs import SymbolicProgram
from dumbo_asp.queries import explanation_graph, pack_xasp_navigator_url
from dumbo_utils.console import console
from dumbo_utils.url import compress_object_for_url
from xasp.entities import Explain

from dumbo_runlim import utils
from dumbo_runlim.utils import run_experiment

programs = {
    "ucore 4x4": """
%*
3 . . .
. . . 2
1 . . .
. . . 1
*%
given((1,1), 3).
given((2,4), 2).
given((3,1), 1).
given((4,4), 1).

{assign((Row, Col), Value) : Value = 1..4} = 1 :- Row = 1..4; Col = 1..4.
:- given(Cell, Value), not assign(Cell, Value).

:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
:- block(Block, _); Value = 1..4; not assign(Cell, Value) : block(Block, Cell).

block((row, Row), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((col, Col), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..4; Col = 1..4; Row' = (Row-1) / 2; Col' = (Col-1) / 2.
    """,
    "ucore 9x9": """
given((1, 1), 6).
given((1, 3), 9).
given((1, 4), 8).
given((1, 6), 7).
given((2, 4), 6).
given((2, 9), 1).
given((3, 2), 3).
given((3, 3), 5).
given((3, 6), 2).
given((3, 8), 7).
given((4, 2), 6).
given((4, 3), 8).
given((4, 7), 1).
given((4, 9), 2).
given((5, 1), 3).
given((5, 6), 5).
given((6, 4), 2).
given((6, 7), 3).
given((6, 8), 6).
given((7, 1), 8).
given((7, 2), 5).
given((7, 3), 4).
given((7, 4), 7).
given((7, 5), 2).
given((7, 7), 6).
given((7, 8), 9).
given((8, 4), 5).
given((8, 5), 9).
given((8, 9), 8).
given((9, 1), 2).
given((9, 3), 6).
given((9, 4), 4).
given((9, 5), 3).
given((9, 7), 7).
given((9, 8), 1).
given((9, 9), 5).

{assign((Row, Col), Value) : Value = 1..9} = 1 :- Row = 1..9; Col = 1..9.
:- given(Cell, Value), not assign(Cell, Value).

:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
:- block(Block, _); Value = 1..9; not assign(Cell, Value) : block(Block, Cell).

block((row, Row), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((col, Col), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..9; Col = 1..9; Row' = (Row-1) / 3; Col' = (Col-1) / 3.
    """,
    "xasp 4x4": """
%*
3 . . .
. . . 2
1 . . .
. . . 1
*%
given((1,1), 3).
given((2,4), 2).
given((3,1), 1).
given((4,4), 1).

assign((Row, Col), Value) :- Row = 1..4; Col = 1..4; Value = 1..4; not assign'((Row, Col), Value).
assign'((Row, Col), Value) :- Row = 1..4; Col = 1..4; Value = 1..4; not assign((Row, Col), Value).
:- assign(Cell, Value), assign(Cell, Value'), Value < Value'.
:- Row = 1..4; Col = 1..4; Cell = (Row, Col); assign'(Cell, 1); assign'(Cell, 2); assign'(Cell, 3); assign'(Cell, 4).   
:- given(Cell, Value), assign'(Cell, Value).

:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
at_least_one(Block, Value) :- block(Block, Cell); assign(Cell, Value).
at_least_one'(Block, Value) :- block(Block, Cell); Value = 1..4; not at_least_one(Block, Value).
:- block(Block, Cell); Value = 1..4; at_least_one'(Block, Value).

block((row, Row), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((col, Col), (Row, Col)) :- Row = 1..4, Col = 1..4.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..4; Col = 1..4; Row' = (Row-1) / 2; Col' = (Col-1) / 2.
    """,
    "xasp 9x9": """
given((1, 1), 6).
given((1, 3), 9).
given((1, 4), 8).
given((1, 6), 7).
given((2, 4), 6).
given((2, 9), 1).
given((3, 2), 3).
given((3, 3), 5).
given((3, 6), 2).
given((3, 8), 7).
given((4, 2), 6).
given((4, 3), 8).
given((4, 7), 1).
given((4, 9), 2).
given((5, 1), 3).
given((5, 6), 5).
given((6, 4), 2).
given((6, 7), 3).
given((6, 8), 6).
given((7, 1), 8).
given((7, 2), 5).
given((7, 3), 4).
given((7, 4), 7).
given((7, 5), 2).
given((7, 7), 6).
given((7, 8), 9).
given((8, 4), 5).
given((8, 5), 9).
given((8, 9), 8).
given((9, 1), 2).
given((9, 3), 6).
given((9, 4), 4).
given((9, 5), 3).
given((9, 7), 7).
given((9, 8), 1).
given((9, 9), 5).

assign((Row, Col), Value) :- Row = 1..9; Col = 1..9; Value = 1..9; not assign'((Row, Col), Value).
assign'((Row, Col), Value) :- Row = 1..9; Col = 1..9; Value = 1..9; not assign((Row, Col), Value).
:- assign(Cell, Value), assign(Cell, Value'), Value < Value'.
:- Row = 1..9; Col = 1..9; Cell = (Row, Col); assign'(Cell, 1); assign'(Cell, 2); assign'(Cell, 3); assign'(Cell, 4); assign'(Cell, 5); assign'(Cell, 6); assign'(Cell, 7); assign'(Cell, 8); assign'(Cell, 9).   
:- given(Cell, Value), assign'(Cell, Value).

:- block(Block, Cell); block(Block, Cell'), Cell != Cell'; assign(Cell, Value), assign(Cell', Value).
at_least_one(Block, Value) :- block(Block, Cell); assign(Cell, Value).
at_least_one'(Block, Value) :- block(Block, Cell); Value = 1..9; not at_least_one(Block, Value).
:- block(Block, Cell); Value = 1..9; at_least_one'(Block, Value).

block((row, Row), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((col, Col), (Row, Col)) :- Row = 1..9, Col = 1..9.
block((sub, Row', Col'), (Row, Col)) :- Row = 1..9; Col = 1..9; Row' = (Row-1) / 3; Col' = (Col-1) / 3.
    """
}


def iclp_2024_measure_ucore(program, answer_set, query):
    the_program = SymbolicProgram.parse(program)  # just to be fair, let's recompute everything at each iteration
    herbrand_base = the_program.herbrand_base
    graph = explanation_graph(the_program, answer_set, herbrand_base, Model.of_atoms(query))
    return graph


def iclp_2024_teardown_ucore(query, result):
    graph = result
    links = len(graph.filter(lambda atom: atom.predicate_name == "link"))
    assumptions = graph.as_facts.count("(assumption,")
    url = pack_xasp_navigator_url(graph, as_forest_with_roots=Model.of_atoms(query), with_chopped_body=True, with_backward_search=True,
                                  backward_search_symbols=(';', ' :-'))
    return links, assumptions, url


def iclp_2024_measure_xasp(program, answer_set, queries):
    explain = Explain.the_program(
        program,
        the_answer_set=answer_set,
        the_atoms_to_explain=Model.of_atoms(queries),
    )
    graph = explain.explanation_dag()
    return graph, explain


def iclp_2024_teardown_xasp(result):
    graph, explain = result
    links = len(graph.filter(lambda atom: atom.predicate_name == "link"))
    assumptions = len(explain.minimal_assumption_set())
    explain.compute_igraph()
    url = "https://xasp-navigator.netlify.app/#" + compress_object_for_url(explain.navigator_graph())
    return links, assumptions, url


def iclp_2024(
        output_file: Path = typer.Option(
            "output.csv", "--output-file", "-o",
            help="File to store final results",
        ),
) -> None:
    answer_sets = {key: Model.of_program(program) for key, program in programs.items()}
    queries = {key: answer_set.filter(lambda atom: atom.predicate_name == "assign")
               for key, answer_set in answer_sets.items()}

    res = {}

    def on_complete_task(task_id, resources, result):
        console.log(f"Task {task_id}: {resources}, links={result[0]}, assumptions={result[1]}")
        res[task_id] = (resources, result)

    def on_all_done():
        with open(output_file, "w") as file:
            file.write(f"task_id\treal_time\ttime\tmemory\tlinks\tassumptions\turl\n")
            for task_id, (resources, result) in res.items():
                links, assumptions, url = result
                file.write(f"{task_id}\t{resources.real_time_usage}\t{resources.time_usage}\t{resources.memory_usage}\t{links}\t{assumptions}\t{url}\n")
        utils.on_all_done()

    run_experiment(
        *(
            {
                "task_id": f"{key} {query}",
                "measure": (iclp_2024_measure_ucore, {
                    "program": programs[key],
                    "answer_set": answer_sets[key],
                    "query": query,
                }),
                "teardown": (iclp_2024_teardown_ucore, {
                    "query": query,
                }),
            } if "xasp" not in key else {
                "task_id": f"{key} {query}",
                "measure": (iclp_2024_measure_xasp, {
                    "program": programs[key],
                    "answer_set": answer_sets[key],
                    "queries": Model.of_atoms(query, str(query).replace("assign", "assign'")),
                }),
                "teardown": (iclp_2024_teardown_xasp, {
                }),

            } for key in queries.keys() for query in queries[key]
        ),
        on_complete_task=on_complete_task,
        on_all_done=on_all_done,
    )
