from pathlib import Path

import pytest

from synse.sbn import (
    SBN_EDGE_TYPE,
    SBN_NODE_TYPE,
    SBNGraph,
    sbn_graphs_are_isomorphic,
    split_comments,
)

EXAMPLES_DIR = Path(__file__).parent / "examples"
NORMAL_EXAMPLE = Path(EXAMPLES_DIR / "normal_example.sbn").read_text()
ALL_EXAMPLES = [example.read_text() for example in EXAMPLES_DIR.glob("*.sbn")]


@pytest.mark.parametrize(
    "line, expected",
    [
        ("%%% This output was generated by the following command:", []),
        (
            "brown.a.01                               % A brown     [0-7]",
            [("brown.a.01", "A brown     [0-7]")],
        ),
        (
            "entity.n.01                                   %                 ",
            [("entity.n.01", None)],
        ),
        (
            "entity.n.01       EQU 7                  % 7 % der       [21-28]",
            [("entity.n.01       EQU 7", "7 % der       [21-28]")],
        ),
    ],
)
def test_split_comments(line, expected):
    assert split_comments(line) == expected


def test_parse_sense_simple_string():
    single_sense = "brown.a.01                             % A brown     [0-7]"
    G = SBNGraph().from_string(single_sense)

    box_id = (SBN_NODE_TYPE.BOX, 0)
    sense_id = (SBN_NODE_TYPE.SENSE, 0)

    # Should have the implict first box and the sense
    assert box_id in G.nodes
    assert sense_id in G.nodes

    # Sense and initial box should be connected
    edge_connection = (box_id, sense_id)
    assert edge_connection in G.edges

    edge_data = G.get_edge_data(*edge_connection)
    assert edge_data["type"] == SBN_EDGE_TYPE.BOX_CONNECT


def test_parse_reconstruct_name():
    test_string = (
        'musical_organization.n.01 Name "Steve Miller Band"'
        "                 % The Steve Miller Band [0-21]"
    )
    G = SBNGraph().from_string(test_string)

    name_const_id = (SBN_NODE_TYPE.NAME_CONSTANT, 0)

    assert name_const_id in G.nodes

    assert len(G.nodes) == 3  # box, sense, name
    # box->box-connect->sense, sense->role->name
    assert len(G.edges) == 2

    node_data = G.nodes.get(name_const_id)
    assert node_data["token"] == '"Steve Miller Band"'


@pytest.mark.parametrize("example_string", ALL_EXAMPLES)
def test_can_parse_full_file(example_string):
    # No exceptions means it works
    SBNGraph().from_string(example_string)


# @pytest.mark.parametrize("example_string", ALL_EXAMPLES)
# def test_can_create_png(tmp_path, example_string):
#     SBNGraph().from_string(example_string).to_png(tmp_path / "test.png")


@pytest.mark.parametrize("example_string", ALL_EXAMPLES)
def test_can_parse_and_reconstruct(tmp_path, example_string):
    starting_graph = SBNGraph().from_string(example_string)
    path = starting_graph.to_sbn(tmp_path / "test.sbn")
    reconstructed_graph = SBNGraph().from_path(path)

    assert sbn_graphs_are_isomorphic(starting_graph, reconstructed_graph)


@pytest.mark.parametrize("example_string", ALL_EXAMPLES)
def test_can_parse_and_reconstruct_with_comments(tmp_path, example_string):
    starting_graph = SBNGraph().from_string(example_string)
    path = starting_graph.to_sbn(tmp_path / "test.sbn", add_comments=True)
    reconstructed_graph = SBNGraph().from_path(path)

    assert sbn_graphs_are_isomorphic(starting_graph, reconstructed_graph)


def test_parse_indices():
    pass


def test_add_new_box():
    pass


def test_json_export(tmp_path):
    tmp_file = tmp_path / "tmp.json"

    G_string = SBNGraph().from_string(NORMAL_EXAMPLE)
    G_string.to_json(tmp_file)

    # Can export the file
    assert tmp_file.exists()

    # Check if nodes and edges are identical after reconstructing the graph
    G_json = SBNGraph().from_json(tmp_file)

    nodes_string = sorted(list(G_string.nodes.items()))
    nodes_json = sorted(list(G_json.nodes.items()))

    assert nodes_string == nodes_json

    edges_string = sorted(list(G_string.edges.items()))
    edges_json = sorted(list(G_json.edges.items()))

    assert edges_string == edges_json
