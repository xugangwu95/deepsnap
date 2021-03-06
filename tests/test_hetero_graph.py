import math
import unittest
from tests.utils import (
    generate_simple_hete_graph,
    generate_dense_hete_graph,
    generate_dense_hete_multigraph,
)
from deepsnap.batch import Batch
from torch.utils.data import DataLoader
from deepsnap.hetero_graph import HeteroGraph


class TestHeteroGraph(unittest.TestCase):
    def test_hetero_graph_basics(self):
        G = generate_simple_hete_graph()
        hete = HeteroGraph(G)

        self.assertEqual(hete.get_num_node_features('n1'), 10)
        self.assertEqual(hete.get_num_node_features('n2'), 12)
        self.assertEqual(hete.get_num_edge_features('e1'), 8)
        self.assertEqual(hete.get_num_edge_features('e2'), 12)
        self.assertEqual(hete.get_num_nodes('n1'), 4)
        self.assertEqual(hete.get_num_nodes('n2'), 5)
        self.assertEqual(len(hete.node_types), 2)
        self.assertEqual(len(hete.edge_types), 2)

        message_types = hete.message_types
        self.assertEqual(len(message_types), 7)
        self.assertEqual(hete.get_num_node_labels('n1'), 2)
        self.assertEqual(hete.get_num_node_labels('n2'), 2)
        self.assertEqual(hete.get_num_edge_labels('e1'), 3)
        self.assertEqual(hete.get_num_edge_labels('e2'), 3)
        self.assertEqual(hete.get_num_edges(message_types[0]), 3)
        self.assertEqual(len(hete.node_label_index), 2)

    def test_hetero_graph_batch(self):
        G = generate_simple_hete_graph()
        hete = HeteroGraph(G)

        heteGraphDataset = []
        for _ in range(30):
            heteGraphDataset.append(hete.clone())
        dataloader = DataLoader(
            heteGraphDataset,
            collate_fn=Batch.collate(),
            batch_size=3,
            shuffle=True,
        )

        self.assertEqual(len(dataloader), math.ceil(30 / 3))
        for data in dataloader:
            self.assertEqual(data.num_graphs, 3)

    def test_hetero_multigraph_split(self):
        G = generate_dense_hete_multigraph()
        hete = HeteroGraph(G)

        # node
        hete_node = hete.split(task='node')
        for node_type in hete.node_label_index:
            num_nodes = len(hete.node_label_index[node_type])
            num_nodes_reduced = num_nodes - 3
            node_0 = 1 + int(num_nodes_reduced * 0.8)
            node_1 = 1 + int(num_nodes_reduced * 0.1)
            node_2 = num_nodes - node_0 - node_1
            self.assertEqual(
                len(hete_node[0].node_label_index[node_type]),
                node_0,
            )
            self.assertEqual(
                len(hete_node[1].node_label_index[node_type]),
                node_1,
            )
            self.assertEqual(
                len(hete_node[2].node_label_index[node_type]),
                node_2,
            )

        # edge
        hete_edge = hete.split(task='edge')
        for edge_type in hete.edge_label_index:
            num_edges = int(hete.edge_label_index[edge_type].shape[1])
            num_edges_reduced = num_edges - 3
            edge_0 = 1 + int(num_edges_reduced * 0.8)
            edge_1 = 1 + int(num_edges_reduced * 0.1)
            edge_2 = num_edges - edge_0 - edge_1
            self.assertEqual(
                hete_edge[0].edge_label_index[edge_type].shape[1],
                edge_0,
            )
            self.assertEqual(
                hete_edge[1].edge_label_index[edge_type].shape[1],
                edge_1,
            )
            self.assertEqual(
                hete_edge[2].edge_label_index[edge_type].shape[1],
                edge_2,
            )

        # link prediction
        hete_link = hete.split(task='link_pred', split_ratio=[0.5, 0.3, 0.2])
        # calculate the expected edge num for each splitted subgraph
        hete_link_train_edge_num = 0
        hete_link_val_edge_num = 0
        hete_link_test_edge_num = 0
        for _, val in hete.edge_label_index.items():
            val_length = val.shape[1]
            val_length_reduced = val_length - 3
            hete_link_train_edge_num += 1 + int(0.5 * val_length_reduced)
            hete_link_val_edge_num += 1 + int(0.3 * val_length_reduced)
            hete_link_test_edge_num += (
                val_length
                - 2
                - int(0.5 * val_length_reduced)
                - int(0.3 * val_length_reduced)
            )

        self.assertEqual(
            len(hete_link[0].edge_label),
            hete_link_train_edge_num,
        )
        self.assertEqual(
            len(hete_link[1].edge_label),
            hete_link_val_edge_num,
        )
        self.assertEqual(
            len(hete_link[2].edge_label),
            hete_link_test_edge_num,
        )

    def test_hetero_graph_split(self):
        G = generate_dense_hete_graph()
        hete = HeteroGraph(G)

        hete_node = hete.split()
        for node_type in hete.node_label_index:
            num_nodes = len(hete.node_label_index[node_type])
            num_nodes_reduced = num_nodes - 3
            node_0 = 1 + int(num_nodes_reduced * 0.8)
            node_1 = 1 + int(num_nodes_reduced * 0.1)
            node_2 = num_nodes - node_0 - node_1
            self.assertEqual(
                len(hete_node[0].node_label_index[node_type]),
                node_0,
            )
            self.assertEqual(
                len(hete_node[1].node_label_index[node_type]),
                node_1,
            )
            self.assertEqual(
                len(hete_node[2].node_label_index[node_type]),
                node_2,
            )

        # node with specified split type
        node_split_types = ['n1']
        hete_node = hete.split(split_types=node_split_types)
        for node_type in hete.node_label_index:
            if node_type in node_split_types:
                num_nodes = len(hete.node_label_index[node_type])
                num_nodes_reduced = num_nodes - 3
                node_0 = 1 + int(num_nodes_reduced * 0.8)
                node_1 = 1 + int(num_nodes_reduced * 0.1)
                node_2 = num_nodes - node_0 - node_1
                self.assertEqual(
                    len(hete_node[0].node_label_index[node_type]),
                    node_0,
                )
                self.assertEqual(
                    len(hete_node[1].node_label_index[node_type]),
                    node_1,
                )
                self.assertEqual(
                    len(hete_node[2].node_label_index[node_type]),
                    node_2,
                )
            else:
                self.assertEqual(
                    len(hete_node[0].node_label_index[node_type]),
                    len(hete.node_label_index[node_type]),
                )
                self.assertEqual(
                    len(hete_node[1].node_label_index[node_type]),
                    len(hete.node_label_index[node_type]),
                )
                self.assertEqual(
                    len(hete_node[2].node_label_index[node_type]),
                    len(hete.node_label_index[node_type]),
                )

        # edge
        hete_edge = hete.split(task='edge')
        for edge_type in hete.edge_label_index:
            num_edges = int(hete.edge_label_index[edge_type].shape[1])
            num_edges_reduced = num_edges - 3
            edge_0 = 1 + int(num_edges_reduced * 0.8)
            edge_1 = 1 + int(num_edges_reduced * 0.1)
            edge_2 = num_edges - edge_0 - edge_1
            self.assertEqual(
                hete_edge[0].edge_label_index[edge_type].shape[1],
                edge_0,
            )
            self.assertEqual(
                hete_edge[1].edge_label_index[edge_type].shape[1],
                edge_1,
            )
            self.assertEqual(
                hete_edge[2].edge_label_index[edge_type].shape[1],
                edge_2,
            )

        # edge with specified split type
        edge_split_types = [('n1', 'e1', 'n1'), ('n1', 'e2', 'n2')]
        hete_edge = hete.split(task='edge', split_types=edge_split_types)
        for edge_type in hete.edge_label_index:
            if edge_type in edge_split_types:
                num_edges = int(hete.edge_label_index[edge_type].shape[1])
                num_edges_reduced = num_edges - 3
                edge_0 = 1 + int(num_edges_reduced * 0.8)
                edge_1 = 1 + int(num_edges_reduced * 0.1)
                edge_2 = num_edges - edge_0 - edge_1

                self.assertEqual(
                    hete_edge[0].edge_label_index[edge_type].shape[1],
                    edge_0,
                )
                self.assertEqual(
                    hete_edge[1].edge_label_index[edge_type].shape[1],
                    edge_1,
                )
                self.assertEqual(
                    hete_edge[2].edge_label_index[edge_type].shape[1],
                    edge_2,
                )
            else:
                self.assertEqual(
                    hete_edge[0].edge_label_index[edge_type].shape[1],
                    hete.edge_label_index[edge_type].shape[1],
                )
                self.assertEqual(
                    hete_edge[1].edge_label_index[edge_type].shape[1],
                    hete.edge_label_index[edge_type].shape[1],
                )
                self.assertEqual(
                    hete_edge[2].edge_label_index[edge_type].shape[1],
                    hete.edge_label_index[edge_type].shape[1],
                )

        # link_pred
        hete_link = hete.split(task='link_pred', split_ratio=[0.5, 0.3, 0.2])
        # calculate the expected edge num for each splitted subgraph
        hete_link_train_edge_num = 0
        hete_link_val_edge_num = 0
        hete_link_test_edge_num = 0
        for key, val in hete.edge_label_index.items():
            val_length = val.shape[1]
            val_length_reduced = val_length - 3
            hete_link_train_edge_num += 1 + int(0.5 * val_length_reduced)
            hete_link_val_edge_num += 1 + int(0.3 * val_length_reduced)
            hete_link_test_edge_num += (
                val_length
                - 2
                - int(0.5 * val_length_reduced)
                - int(0.3 * val_length_reduced)
            )

        self.assertEqual(
            len(hete_link[0].edge_label),
            hete_link_train_edge_num,
        )
        self.assertEqual(
            len(hete_link[1].edge_label),
            hete_link_val_edge_num,
        )
        self.assertEqual(
            len(hete_link[2].edge_label),
            hete_link_test_edge_num,
        )

    def test_hetero_graph_none(self):
        G = generate_simple_hete_graph(no_edge_type=True)
        hete = HeteroGraph(G)
        message_types = hete.message_types
        for message_type in message_types:
            self.assertEqual(message_type[1], None)


if __name__ == "__main__":
    unittest.main()
