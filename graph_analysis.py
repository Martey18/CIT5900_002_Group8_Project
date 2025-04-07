import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
import re
import os
import time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


def extract_keywords(title, min_word_length=3, max_keywords=5):
    """
    Extract keywords from a research title

    Parameters:
    title (str): Research paper title
    min_word_length (int): Minimum length of keywords
    max_keywords (int): Maximum number of keywords to return

    Returns:
    list: List of keywords
    """
    # Ensure title is a string
    if title is None:
        return []

    title = str(title)

    # Convert to lowercase
    title = title.lower()

    # Remove special characters and numbers
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\d+', ' ', title)

    # Tokenize
    tokens = word_tokenize(title)

    # Get stopwords and add custom stopwords
    stop_words = set(stopwords.words('english'))
    custom_stop_words = {
        'and', 'the', 'in', 'of', 'for', 'on', 'to', 'with', 'a', 'an',
        'that', 'this', 'these', 'those', 'some', 'all', 'any',
        'u', 's', 'us', 'vs', 'research', 'study', 'analysis', 'using', 'based'
    }
    stop_words.update(custom_stop_words)

    # Initialize lemmatizer
    lemmatizer = WordNetLemmatizer()

    # Filter stopwords, short words, and lemmatize
    filtered_tokens = []
    for token in tokens:
        if (
                token not in stop_words and  # Filter stopwords
                len(token) >= min_word_length and  # Filter short words
                token.isalpha()  # Ensure only letters
        ):
            # Lemmatization
            lemma = lemmatizer.lemmatize(token)
            filtered_tokens.append(lemma)

    # Calculate word frequency
    word_freq = Counter(filtered_tokens)

    # Select most common words as keywords
    keywords = [word for word, freq in word_freq.most_common(max_keywords)]

    return keywords


class ResearchOutput:
    """
    Class to represent a research output with all relevant metadata
    """

    def __init__(self, output_title, output_year, project_rdc, keywords=None, authors=None, doi=None, abstract=None,
                 output_venue=None, citations=0, project_id=None, project_status=None, project_title=None,
                 project_start_year=None, project_end_year=None, project_pi=None, output_type=None,
                 output_status=None, output_biblio=None):
        self.title = output_title
        self.year = int(output_year) if output_year and not pd.isna(output_year) else None
        self.agency = project_rdc  # Using ProjectRDC as the agency
        self.keywords = [kw.strip() for kw in keywords.split(';')] if keywords and not pd.isna(keywords) else []
        self.authors = [author.strip() for author in authors.split(';')] if authors and not pd.isna(authors) else []
        self.doi = doi
        self.abstract = abstract
        self.journal = output_venue
        self.citations = citations

        # Additional attributes from CSV
        self.project_id = project_id
        self.project_status = project_status
        self.project_title = project_title
        self.project_start_year = project_start_year
        self.project_end_year = project_end_year
        self.project_pi = project_pi
        self.output_type = output_type
        self.output_status = output_status
        self.output_biblio = output_biblio

    def __repr__(self):
        return f"ResearchOutput({self.title}, {self.year})"

    def __hash__(self):
        # Hash based on title and year (assuming these uniquely identify a research output)
        return hash((self.title, self.year))

    def __eq__(self, other):
        if not isinstance(other, ResearchOutput):
            return False
        return self.title == other.title and self.year == other.year


def load_data_from_pandas(csv_file):
    """
    Load data from a pandas dataframe

    Parameters:
    csv_file (str): Path to the CSV file

    Returns:
    list: List of ResearchOutput objects
    """
    outputs = []
    total_rows = 0
    valid_rows = 0

    try:
        # Read CSV using pandas
        df = pd.read_csv(csv_file)
        total_rows = len(df)

        # Process each row
        for i, row in df.iterrows():
            try:
                # Skip rows with missing essential data
                if pd.isna(row['OutputTitle']):
                    print(f"Warning: Row {i + 2} is missing OutputTitle. Skipping this row.")
                    continue

                # Extract keywords from title
                keywords = []
                if not pd.isna(row['OutputTitle']):
                    keywords = extract_keywords(row['OutputTitle'])
                    keywords_str = '; '.join(keywords)
                else:
                    keywords_str = ""

                # Create research output object
                output = ResearchOutput(
                    output_title=row['OutputTitle'],
                    output_year=row['OutputYear'] if not pd.isna(row['OutputYear']) else None,
                    project_rdc=row['ProjectRDC'] if not pd.isna(row['ProjectRDC']) else None,
                    keywords=keywords_str,
                    authors=row['Authors'] if not pd.isna(row['Authors']) else None,
                    doi=row['DOI'] if not pd.isna(row['DOI']) else None,
                    abstract=row['Abstract'] if not pd.isna(row['Abstract']) else None,
                    output_venue=row['OutputVenue'] if not pd.isna(row['OutputVenue']) else None,
                    citations=0,  # Assuming no citation data in the CSV
                    project_id=row['ProjectID'] if not pd.isna(row['ProjectID']) else None,
                    project_status=row['ProjectStatus'] if not pd.isna(row['ProjectStatus']) else None,
                    project_title=row['ProjectTitle'] if not pd.isna(row['ProjectTitle']) else None,
                    project_start_year=row['ProjectStartYear'] if not pd.isna(row['ProjectStartYear']) else None,
                    project_end_year=row['ProjectEndYear'] if not pd.isna(row['ProjectEndYear']) else None,
                    project_pi=row['ProjectPI'] if not pd.isna(row['ProjectPI']) else None,
                    output_type=row['OutputType'] if not pd.isna(row['OutputType']) else None,
                    output_status=row['OutputStatus'] if not pd.isna(row['OutputStatus']) else None,
                    output_biblio=row['OutputBiblio'] if not pd.isna(row['OutputBiblio']) else None
                )
                outputs.append(output)
                valid_rows += 1
            except Exception as e:
                print(f"Error processing row {i + 2}: {e}")

        print(f"CSV processing complete: Processed {total_rows} rows, {valid_rows} valid entries")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

    return outputs


def calculate_similarity(output1, output2):
    """
    Calculate similarity score between two research outputs

    Parameters:
    output1 (ResearchOutput): First research output
    output2 (ResearchOutput): Second research output

    Returns:
    float: Similarity score between the outputs
    """
    similarity_score = 0

    # Check agency/RDC (weight: 1)
    if output1.agency and output2.agency and output1.agency == output2.agency:
        similarity_score += 1

    # Check year - closer years get higher scores (weight: up to 1)
    if output1.year and output2.year:
        year_diff = abs(output1.year - output2.year)
        if year_diff == 0:
            similarity_score += 1
        elif year_diff <= 2:
            similarity_score += 0.5

    # Check authors (weight: 1 per shared author, max 3)
    shared_authors = set(output1.authors) & set(output2.authors)
    author_score = min(len(shared_authors), 3)
    similarity_score += author_score

    # Check project PI (weight: 1)
    if output1.project_pi and output2.project_pi and output1.project_pi == output2.project_pi:
        similarity_score += 1

    # Check output venue (weight: 1)
    if output1.journal and output2.journal and output1.journal == output2.journal:
        similarity_score += 1

    # Check project ID (weight: 3)
    if output1.project_id and output2.project_id and output1.project_id == output2.project_id:
        similarity_score += 3

    # Check keywords overlap (weight: 0.5 per shared keyword, max 2)
    if output1.keywords and output2.keywords:
        shared_keywords = set(output1.keywords) & set(output2.keywords)
        keyword_score = min(len(shared_keywords) * 0.5, 2)
        similarity_score += keyword_score

    return similarity_score


def build_networkx_graph(research_outputs, similarity_threshold=0.5):
    """
    Build a NetworkX graph from research outputs with weighted edges

    Parameters:
    research_outputs (list): List of ResearchOutput objects
    similarity_threshold (float): Minimum similarity score to create an edge

    Returns:
    networkx.Graph: Graph representing the research output network
    """
    G = nx.Graph()

    # Add all research outputs as nodes
    for output in research_outputs:
        G.add_node(output,
                   title=output.title,
                   year=output.year,
                   agency=output.agency,
                   keywords=output.keywords,
                   authors=output.authors,
                   journal=output.journal,
                   project_id=output.project_id,
                   project_pi=output.project_pi)

    # Add edges between nodes that share attributes
    edge_count = 0
    for i, output1 in enumerate(research_outputs):
        for j, output2 in enumerate(research_outputs[i + 1:], i + 1):
            similarity = calculate_similarity(output1, output2)
            if similarity >= similarity_threshold:
                G.add_edge(output1, output2, weight=similarity)
                edge_count += 1

    print(f"Graph construction complete: {len(G.nodes())} nodes, {edge_count} edges")
    return G


def calculate_network_metrics(G):
    """
    Calculate various network metrics for the graph

    Parameters:
    G (networkx.Graph): Graph to analyze

    Returns:
    dict: Dictionary containing various network metrics
    """
    metrics = {}

    # Basic metrics
    metrics['node_count'] = G.number_of_nodes()
    metrics['edge_count'] = G.number_of_edges()
    metrics['density'] = nx.density(G)

    # Connected components
    connected_components = list(nx.connected_components(G))
    metrics['connected_components'] = len(connected_components)
    metrics['largest_component_size'] = len(max(connected_components, key=len)) if connected_components else 0

    # Calculate average degree
    degrees = [d for _, d in G.degree()]
    metrics['avg_degree'] = sum(degrees) / len(degrees) if degrees else 0
    metrics['max_degree'] = max(degrees) if degrees else 0

    # Calculate clustering coefficient
    metrics['avg_clustering'] = nx.average_clustering(G)

    # Calculate centrality measures (for largest connected component to avoid errors)
    if connected_components:
        largest_cc = max(connected_components, key=len)
        largest_cc_subgraph = G.subgraph(largest_cc)

        # Betweenness centrality
        betweenness = nx.betweenness_centrality(largest_cc_subgraph)
        metrics['max_betweenness'] = max(betweenness.values()) if betweenness else 0
        metrics['avg_betweenness'] = sum(betweenness.values()) / len(betweenness) if betweenness else 0

        # Closeness centrality
        closeness = nx.closeness_centrality(largest_cc_subgraph)
        metrics['max_closeness'] = max(closeness.values()) if closeness else 0
        metrics['avg_closeness'] = sum(closeness.values()) / len(closeness) if closeness else 0

        # Eigenvector centrality
        try:
            eigenvector = nx.eigenvector_centrality(largest_cc_subgraph, max_iter=300)
            metrics['max_eigenvector'] = max(eigenvector.values()) if eigenvector else 0
            metrics['avg_eigenvector'] = sum(eigenvector.values()) / len(eigenvector) if eigenvector else 0
        except:
            print("Eigenvector centrality calculation did not converge")
            metrics['max_eigenvector'] = None
            metrics['avg_eigenvector'] = None

    return metrics


def visualize_graph(G, output_file=None, title="Research Output Network"):
    """
    Visualize the graph with node sizes based on degree and colors based on year

    Parameters:
    G (networkx.Graph): Graph to visualize
    output_file (str): Path to save the visualization image
    title (str): Title for the visualization
    """
    plt.figure(figsize=(12, 10))

    # Get the largest connected component if the graph is too large
    if len(G) > 100:
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc)
        title += " (Largest Connected Component)"

    # Node positions using spring layout
    pos = nx.spring_layout(G, k=0.3, iterations=50, seed=42)

    # Node sizes based on degree
    node_sizes = [20 + 5 * G.degree(node) for node in G]

    # Node colors based on year
    years = [G.nodes[node].get('year', 2000) for node in G]

    # Filter out None values for calculations
    valid_years = [y for y in years if y is not None]

    if valid_years:
        min_year = min(valid_years)
        max_year = max(valid_years)
    else:
        min_year = 2000
        max_year = 2023

    year_range = max(1, max_year - min_year)

    # Handle None values in years
    normalized_years = []
    for year in years:
        if year is None:
            normalized_years.append(0)  # Default color for missing years
        else:
            normalized_years.append((year - min_year) / year_range)

    # Edge weights
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    normalized_weights = [0.5 + 1.5 * (weight / max_weight) for weight in edge_weights]

    # Draw the network
    nodes = nx.draw_networkx_nodes(G, pos,
                                   node_size=node_sizes,
                                   node_color=normalized_years,
                                   cmap=plt.cm.viridis,
                                   alpha=0.8)

    edges = nx.draw_networkx_edges(G, pos,
                                   width=normalized_weights,
                                   alpha=0.5,
                                   edge_color='grey')

    # Add labels to larger nodes
    large_nodes = [node for node in G if G.degree(node) > 3]
    labels = {node: G.nodes[node].get('title', '')[:15] + '...' for node in large_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family='sans-serif')

    # Add color bar for years
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(min_year, max_year))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=plt.gca())
    cbar.set_label('Publication Year')

    # Set title and layout
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()

    # Save or show the visualization
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Graph visualization saved to {output_file}")
    else:
        plt.show()


def detect_clusters(G, algorithm='louvain'):
    """
    Detect clusters in the research output graph

    Parameters:
    G (networkx.Graph): Graph to analyze
    algorithm (str): Cluster detection algorithm to use ('louvain' or 'greedy')

    Returns:
    dict: Mapping of nodes to cluster IDs
    """
    if algorithm == 'louvain':
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
            modularity = community_louvain.modularity(partition, G)
            print(f"Detected {len(set(partition.values()))} clusters with modularity {modularity:.4f}")
            return partition
        except ImportError:
            print("python-louvain package not found. Attempting to use python-louvain-community...")
            try:
                # Try the alternate package name
                import community.community_louvain as community_louvain
                partition = community_louvain.best_partition(G)
                modularity = community_louvain.modularity(partition, G)
                print(f"Detected {len(set(partition.values()))} clusters with modularity {modularity:.4f}")
                return partition
            except ImportError:
                print("Cluster detection packages not found. Please install with 'pip install python-louvain'")
                algorithm = 'greedy'

    if algorithm == 'greedy':
        communities = list(nx.algorithms.community.greedy_modularity_communities(G))
        print(f"Detected {len(communities)} clusters using greedy modularity algorithm")

        # Convert to a node->cluster dictionary format
        partition = {}
        for i, community in enumerate(communities):
            for node in community:
                partition[node] = i

        return partition


def visualize_clusters(G, partition, output_file=None, title="Research Clusters"):
    """
    Visualize the graph with clusters highlighted by colors

    Parameters:
    G (networkx.Graph): Graph to visualize
    partition (dict): Mapping of nodes to cluster IDs
    output_file (str): Path to save the visualization image
    title (str): Title for the visualization
    """
    plt.figure(figsize=(14, 12))

    # Node positions
    pos = nx.spring_layout(G, k=0.3, iterations=50, seed=42)

    # Get unique clusters
    clusters = set(partition.values())

    # Color map for clusters
    cmap = plt.colormaps['tab20'].resampled(len(clusters))

    # Draw nodes for each cluster
    for i, clust in enumerate(clusters):
        # Get list of nodes in the cluster
        clust_nodes = [node for node in G.nodes() if partition[node] == clust]

        # Skip if cluster is empty
        if not clust_nodes:
            continue

        # Draw nodes
        nx.draw_networkx_nodes(G, pos,
                               nodelist=clust_nodes,
                               node_size=[20 + 5 * G.degree(node) for node in clust_nodes],
                               node_color=[cmap(clust)] * len(clust_nodes),
                               alpha=0.8,
                               label=f"Cluster {clust + 1}")

    # Draw edges
    nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.3, edge_color='grey')

    # Add labels to cluster centers (node with highest degree in each cluster)
    labels = {}
    for clust in clusters:
        clust_nodes = [node for node in G.nodes() if partition[node] == clust]
        if clust_nodes:
            # Find node with highest degree in cluster
            center_node = max(clust_nodes, key=lambda n: G.degree(n))
            # Use title or first few characters as label
            labels[center_node] = G.nodes[center_node].get('title', '')[:15] + '...'

    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family='sans-serif')

    # Add legend (limited to avoid overcrowding)
    max_legend_items = min(10, len(clusters))
    plt.legend(scatterpoints=1, loc='lower right', ncol=2, fontsize=8,
               title="Top Clusters", title_fontsize=10)

    # Set title and layout
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()

    # Save or show the visualization
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Cluster visualization saved to {output_file}")
    else:
        plt.show()


def analyze_cluster_similarity(G, partition):
    """
    Analyze the similarity of research outputs within each cluster

    Parameters:
    G (networkx.Graph): Graph to analyze
    partition (dict): Mapping of nodes to cluster IDs

    Returns:
    dict: Dictionary with cluster similarity statistics
    """
    # Group nodes by cluster
    clusters = {}
    for node, clust_id in partition.items():
        if clust_id not in clusters:
            clusters[clust_id] = []
        clusters[clust_id].append(node)

    # Calculate statistics for each cluster
    cluster_stats = {}
    for clust_id, nodes in clusters.items():
        # Skip clusters with only one node
        if len(nodes) < 2:
            continue

        # Calculate all pairwise similarities within the cluster
        similarities = []
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i + 1:]:
                if G.has_edge(node1, node2):
                    similarities.append(G[node1][node2]['weight'])

        # Calculate statistics
        if similarities:
            cluster_stats[clust_id] = {
                'size': len(nodes),
                'avg_similarity': sum(similarities) / len(similarities),
                'max_similarity': max(similarities),
                'min_similarity': min(similarities),
                'edge_density': len(similarities) / (len(nodes) * (len(nodes) - 1) / 2)
            }

    return cluster_stats


def main():
    """
    Main function to execute graph construction and analysis
    """
    print("Project 2 - Step 4: Graph Construction and Analysis")
    print("=" * 70)

    # Step 1: Load data from CSV file
    print("\nLoading research output data...")
    # Read CSV file using pandas function
    csv_file = 'ProcessedData.csv'  # Update this with your actual file path
    research_outputs = load_data_from_pandas(csv_file)

    if not research_outputs:
        print("Error: No valid research outputs found. Please check your data file.")
        return

    print(f"Successfully loaded {len(research_outputs)} research outputs")

    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Step 2: Build the graph
    print("\nBuilding research output graph...")
    start_time = time.time()
    G = build_networkx_graph(research_outputs, similarity_threshold=0.5)
    print(f"Graph building completed in {time.time() - start_time:.2f} seconds")

    # Step 3: Calculate network metrics
    print("\nCalculating network metrics...")
    metrics = calculate_network_metrics(G)

    # Print metrics
    print("\nNetwork Metrics Summary:")
    print("-" * 70)
    print(f"Number of nodes (research outputs): {metrics['node_count']}")
    print(f"Number of edges (connections): {metrics['edge_count']}")
    print(f"Network density: {metrics['density']:.6f}")
    print(f"Number of connected components: {metrics['connected_components']}")
    print(f"Size of largest component: {metrics['largest_component_size']} nodes" +
          f" ({metrics['largest_component_size'] / metrics['node_count'] * 100:.1f}% of network)")
    print(f"Average degree: {metrics['avg_degree']:.2f}")
    print(f"Average clustering coefficient: {metrics['avg_clustering']:.4f}")

    if metrics.get('avg_betweenness') is not None:
        print(f"Average betweenness centrality: {metrics['avg_betweenness']:.6f}")
    if metrics.get('avg_closeness') is not None:
        print(f"Average closeness centrality: {metrics['avg_closeness']:.6f}")
    if metrics.get('avg_eigenvector') is not None:
        print(f"Average eigenvector centrality: {metrics['avg_eigenvector']:.6f}")

    # Step 4: Visualize the graph
    print("\nVisualizing research output network...")
    visualize_graph(G, output_file='output/research_network.png')

    # Step 5: Cluster detection
    print("\nDetecting research clusters...")
    try:
        # First try with louvain algorithm
        partition = detect_clusters(G, algorithm='louvain')

        # If louvain fails, try with greedy algorithm
        if not partition:
            print("Trying alternative cluster detection method...")
            partition = detect_clusters(G, algorithm='greedy')

        if partition:
            visualize_clusters(G, partition, output_file='output/research_clusters.png')

            # Analyze clusters
            clusters = {}
            for node, clust_id in partition.items():
                if clust_id not in clusters:
                    clusters[clust_id] = []
                clusters[clust_id].append(node)

            # Print summary of top clusters
            print("\nLargest Research Clusters:")
            print("-" * 70)
            sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
            for i, (clust_id, nodes) in enumerate(sorted_clusters[:5], 1):
                # Get the most common keywords and project IDs in this cluster
                keywords = []
                project_ids = []
                for node in nodes:
                    keywords.extend(node.keywords if hasattr(node, 'keywords') else [])
                    if hasattr(node, 'project_id') and node.project_id:
                        project_ids.append(node.project_id)

                # Count frequencies
                keyword_counts = {}
                for kw in keywords:
                    if kw:  # Skip empty keywords
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

                project_id_counts = {}
                for pid in project_ids:
                    if pid:  # Skip empty project IDs
                        project_id_counts[pid] = project_id_counts.get(pid, 0) + 1

                # Get top 3 keywords and projects
                top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                top_projects = sorted(project_id_counts.items(), key=lambda x: x[1], reverse=True)[:2]

                print(f"Cluster {i}: {len(nodes)} research outputs")
                print(f"  Top keywords: {', '.join(kw for kw, _ in top_keywords) if top_keywords else 'N/A'}")
                print(f"  Common projects: {', '.join(pid for pid, _ in top_projects) if top_projects else 'N/A'}")

                # Get year range if years are available
                years = [node.year for node in nodes if hasattr(node, 'year') and node.year is not None]
                if years:
                    print(f"  Year range: {min(years)} - {max(years)}")
                print()

        else:
            print("No clusters detected or cluster detection failed.")

    except Exception as e:
        print(f"Error in cluster detection: {e}")
        print("Skipping cluster visualization...")

    print("\nAnalysis complete. Visualizations saved to the 'output' directory.")


# Run the main function if this file is executed directly
if __name__ == "__main__":
    main()