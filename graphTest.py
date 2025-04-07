import unittest
from graph_analysis import (
    extract_keywords, ResearchOutput, calculate_similarity,
    build_networkx_graph, calculate_network_metrics
)


class TestGraphAnalysis(unittest.TestCase):

    def setUp(self):
        # Create sample research outputs for testing
        self.output1 = ResearchOutput(
            output_title="Economic Effects of Population Growth in Urban Areas",
            output_year=2010,
            project_rdc="CES",
            keywords="economic; population; growth; urban",
            authors="Smith, J.; Johnson, M.",
            doi="10.1234/5678",
            abstract="This study examines economic effects of population growth.",
            output_venue="Journal of Economics",
            citations=10,
            project_id="W123456789",
            project_pi="Smith, J."
        )

        self.output2 = ResearchOutput(
            output_title="Population Growth and Health Outcomes in Rural Areas",
            output_year=2012,
            project_rdc="CES",
            keywords="population; growth; health; rural",
            authors="Johnson, M.; Williams, R.",
            doi="10.5678/1234",
            abstract="This study examines health outcomes related to population growth.",
            output_venue="Health Economics Journal",
            citations=8,
            project_id="W987654321",
            project_pi="Johnson, M."
        )

        self.output3 = ResearchOutput(
            output_title="Economic Effects of Tax Policy in Urban Areas",
            output_year=2010,
            project_rdc="CES",
            keywords="economic; tax; policy; urban",
            authors="Smith, J.; Brown, T.",
            doi="10.9876/5432",
            abstract="This study examines economic effects of tax policies.",
            output_venue="Journal of Economics",
            citations=15,
            project_id="W123456789",
            project_pi="Smith, J."
        )

        self.outputs = [self.output1, self.output2, self.output3]

    def test_extract_keywords(self):
        """Test keyword extraction from title"""
        title = "Economic Effects of Population Growth in Urban Areas"
        keywords = extract_keywords(title)

        # Check that keywords were extracted
        self.assertGreater(len(keywords), 0)
        # Check if expected keywords are present
        self.assertTrue(any('economic' in kw for kw in keywords))
        self.assertTrue(any('population' in kw for kw in keywords))
        self.assertTrue(any('growth' in kw for kw in keywords))
        self.assertTrue(any('urban' in kw for kw in keywords))

        # Test with None title
        self.assertEqual(extract_keywords(None), [])

        # Test with non-string title
        self.assertGreaterEqual(len(extract_keywords(123)), 0)

    def test_research_output_creation(self):
        """Test ResearchOutput object creation"""
        output = self.output1

        self.assertEqual(output.title, "Economic Effects of Population Growth in Urban Areas")
        self.assertEqual(output.year, 2010)
        self.assertEqual(output.agency, "CES")
        self.assertEqual(len(output.keywords), 4)
        self.assertEqual(len(output.authors), 2)
        self.assertIn("Smith, J.", output.authors)

    def test_calculate_similarity(self):
        """Test similarity calculation between research outputs"""
        # Test similarity between outputs with same agency, some common authors, etc.
        similarity1_2 = calculate_similarity(self.output1, self.output2)
        similarity1_3 = calculate_similarity(self.output1, self.output3)

        # Output 1 and 3 should be more similar than 1 and 2
        self.assertGreater(similarity1_3, similarity1_2)

        # Both pairs should have positive similarity
        self.assertGreater(similarity1_2, 0)
        self.assertGreater(similarity1_3, 0)

        # Same object should have maximum similarity with itself
        self.assertGreater(calculate_similarity(self.output1, self.output1),
                           calculate_similarity(self.output1, self.output2))

    def test_build_networkx_graph(self):
        """Test graph construction from research outputs"""
        G = build_networkx_graph(self.outputs, similarity_threshold=0.1)

        # Check basic graph properties
        self.assertEqual(G.number_of_nodes(), 3)
        self.assertGreaterEqual(G.number_of_edges(), 1)

        # Test with high threshold (should result in fewer edges)
        G_high_threshold = build_networkx_graph(self.outputs, similarity_threshold=10)
        self.assertEqual(G_high_threshold.number_of_nodes(), 3)
        self.assertEqual(G_high_threshold.number_of_edges(), 0)

    def test_calculate_network_metrics(self):
        """Test calculation of network metrics"""
        G = build_networkx_graph(self.outputs, similarity_threshold=0.1)
        metrics = calculate_network_metrics(G)

        # Check that metrics dict contains expected keys
        self.assertIn('node_count', metrics)
        self.assertIn('edge_count', metrics)
        self.assertIn('density', metrics)
        self.assertIn('connected_components', metrics)

        # Check that metrics values make sense
        self.assertEqual(metrics['node_count'], 3)
        self.assertEqual(metrics['edge_count'], G.number_of_edges())
        self.assertGreaterEqual(metrics['density'], 0)
        self.assertLessEqual(metrics['density'], 1)


if __name__ == '__main__':
    unittest.main()