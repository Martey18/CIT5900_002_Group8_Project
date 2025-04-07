# CIT5900_002_Group8_Project


Project 2: Web Scraping, Text Processing, API Integration, and Graph Analysis


Course: CIT 5900-002
Instructor: Kaihua Ding, PhD
04/06/2025
University of Pennsylvania




Liam Rivard: rivardl1@seas.upenn.edu, Yi-Hsuan Cheng: yihcheng@seas.upenn.edu, Shreyash Khatiwada: Shreyk@sas.upenn.edu, Xinyi Wang: xinyi888@seas.upenn.edu, Nii Martey Armah: na554@seas.upenn.edu 

Web Scraping Overview
This component is designed to scrape research paper metadata from the Research Papers in Economics (RePEc) website and filter the results based on several criteria. The final output is saved to a CSV file for further analysis. The code leverages the requests, BeautifulSoup, regex, pandas, and other standard Python libraries to extract data reliably while adhering to best practices for error handling and rate limiting.

Data Sources
RePEc Website Pages:
The scraper processes 7 pages (from wpaper.html for page 1 to wpaper7.html) from the RePEc listings hosted at https://ideas.repec.org/s/cen/. Each page contains a list of paper entries, with metadata such as titles and links.
Researchers CSV:
A CSV file is hosted on GitHub containing information about valid researchers and project titles. This CSV is loaded into a pandas DataFrame from the URL:
https://raw.githubusercontent.com/dingkaihua/fsrdc-external-census-projects/master/metadata/Researchers.csv.
From this file, the code extracts a set of valid researcher names (from the columns PI and Researcher) and valid paper titles (from the Title column).

Criteria for data selection
1. The abstract must include at least one of the predefined FSRDC keywords. The keywords used for data selection are shown below:
 [‘longitudinal business database’, ‘annual business survey’, ‘american housing survey’, ‘annual survey of manufactures’, ‘american community survey’, ‘census of manufactures’, ‘census edited file’, ‘census of wholesale trade’, ‘census of services’, ‘current population survey’, ‘census of retail trade’, ‘decennial census’, ‘survey of business owners’, ‘census of mining’, ‘master address file extract’, ‘university of michigan’]
2. At least one of the authors of the paper must appear in the combined list of PI and researchers from the Researchers.csv file.
3. The paper must be unique, meaning its title should not match any of the titles already present in the Researchers.csv file.

Code Explanation
Loading Valid Researchers and Titles:
The script first downloads the Researchers.csv using requests with SSL verification disabled (for testing) and wraps the content with io.StringIO for reading into pandas.
It builds two sets:
Valid Researchers: Normalized (stripped, lowercased, and with periods removed) names from both PI and Researcher columns.
Valid Titles: Normalized titles from the Title column to help detect duplicate or irrelevant papers.
Scraping Paper Links:
The code iterates through pages 1 to 7 of the RePEc listings.
It uses BeautifulSoup to locate <ul> elements with the class list-group paperlist and then each <li> element (class list-group-item downfree) containing an <a> tag.
For each <a> tag found, it extracts the relative URL and converts it to an absolute URL, and also collects the paper title.
Processing Each Paper:
For each paper link, the script fetches the detailed page and extracts:
Abstract: From the <div id="abstract-body">.
Authors and Year: Using the <div id="biblio-body"> with a regex (r”(.+?),\s*(\d{4})”) to capture the authors and a four-digit year.
Citations: From the <a> element with id="cites-tab" using a regex (r”(\d+)\s+Citations”) to extract the number of citations.
The code checks if the abstract contains any pre-defined FSRC keywords. If so, it selects the first matched keyword, and using a mapping dictionary, it assigns a corresponding datacode for each dataname.
Author Normalization:
The authors string is split on "&", and each author is normalized by stripping whitespace, lowercasing, and removing periods. The paper is only retained if at least one of these normalized names exists in the valid researchers set.
Title Check:
The paper’s title (normalized) is compared against the valid titles set to prevent duplicate or irrelevant entries.
Output:
Papers that meet all criteria (contain FSRC keywords, have valid authors, and non-duplicate titles) are appended to the results list.
Finally, the results are converted into a pandas DataFrame and saved as a CSV file web_scraping.csv. The CSV file contains the following columns: title, authors, abstract, year, dataname, datacode, citations, url.








This shows the process of identifying valid research outputs. Out of 1236 papers, we scraped 90 papers that meet all the data selection criteria.

Error Handling and Best Practices
HTTP Request Handling:
The code checks for non-200 HTTP status codes for both the main pages and individual paper pages. It prints an error message and continues processing other pages or papers when an error occurs.
SSL Verification:
For the Researchers.csv download, SSL verification is disabled using verify=False (with appropriate warnings suppressed for testing). In a production environment, proper certificates should be installed.
Rate Limiting:
The script includes time.sleep(1) delays between requests to avoid overwhelming the target server and to mimic respectful scraping behavior.
Data Normalization:
Author names and titles are normalized (trimmed, lowercased, and punctuation cleaned) to ensure that matching against the valid lists from the CSV is as robust as possible.
Regex Usage:
Regular expressions are used to extract metadata (authors, year, citations) from the text of HTML elements. This approach helps accommodate minor variations in formatting.
API Integration

The goal of this step was to enrich our research outputs dataset with up-to-date metadata by connecting to external APIs. After evaluating several options—including Dimensions, ORCID, and others—I decided to concentrate on integrating data from the OpenAlex and CORE APIs. These two sources proved to be the easiest to work with and offered robust, well-documented endpoints, despite a few challenges along the way.

Design Decisions:

Initially, I explored multiple APIs such as Dimensions and ORCID because of their extensive metadata coverage. However, I encountered significant challenges in retrieving consistent data from these sources. The Dimensions API, while comprehensive, required additional configuration steps, and its documentation did not always provide clear guidance on handling pagination and error responses. Similarly, ORCID’s API structure was complex, and despite spending considerable time learning its nuances, I was unable to retrieve data reliably. As a result and due to time restraints, I decided to shift my focus toward OpenAlex and CORE, both of which offer simpler RESTful interfaces and more predictable responses.

For the implementation, I designed the code to follow a unified schema that includes the following columns:
['ProjectID', 'ProjectStatus', 'ProjectTitle', 'ProjectRDC', 'ProjectStartYear', 'ProjectEndYear', 'ProjectPI', 'OutputTitle', 'OutputBiblio', 'OutputType', 'OutputStatus', 'OutputVenue', 'OutputYear', 'OutputMonth', 'OutputVolume', 'OutputNumber', 'OutputPages', 'DOI', 'Authors', 'Abstract'].

I chose this schema to match the original ResearchOutputs file, so that data from different APIs and the ResearchOutputs excel file could be merged seamlessly. For each API, I mapped available fields to this schema. When data was not available, for example, fields like ProjectRDC or OutputVolume, I explicitly set them to None so that downstream processing (such as merging with the existing dataset) would work correctly.

Error Handling and Robustness:

Recognizing that API calls can be unpredictable, I implemented comprehensive error handling. For both OpenAlex and CORE APIs, I wrapped network requests in try/except blocks to catch exceptions such as connection errors or timeouts. I also incorporated checks for HTTP status codes. For instance, when the CORE API returns a 429 status code (indicating rate limiting), my code pauses execution for a short period before retrying the request, up to a maximum number of retries. This retry mechanism prevents the integration from failing entirely when the API temporarily restricts access.

Furthermore, I added assertions and tests after key operations. After each API call, I verify that the returned DataFrame contains the expected columns by comparing it with the predefined schema. These assertions ensure that any unexpected changes in the API response or errors in data processing are caught early. In the case of reading CSV files or merging data, additional error handling confirms the file exists and that the data is correctly formatted.

How the API Integration Works:

The integration code is modularized into several functions. For OpenAlex, the function fetch_openalex_data constructs a URL using the provided keywords, sends a GET request, and processes the JSON response to extract relevant metadata. It uses a helper function, reconstruct_abstract, to convert the inverted abstract index into a readable string. This metadata is then organized into a DataFrame following the final schema.

For the CORE API, the process is similar. The function fetch_core_data constructs a query (supporting multiple keywords combined with an “OR” operator), sends a GET request with the appropriate headers, and includes a retry mechanism if the server returns a rate limit error. The response is processed, and fields such as download URL, document type, and publisher name are used to populate columns like OutputBiblio, OutputType, and OutputVenue, respectively. I also ensure that the publication year is extracted either directly from the year_published field or parsed from published_date when necessary.

Data from both APIs are returned in a uniform DataFrame format. I then merge these DataFrames with the data obtained from a web scraping CSV file (which contains basic metadata such as Title, Authors, and Abstract). In the CSV transformation, I ensure that the first author is taken as the ProjectPI. Finally, all sources are merged into a single dataset that can be further analyzed or visualized.

Data Processing Overview

This component is designed to process the web scraped and api enhanced file and remove any papers that are in the 2024 dataset and confirm that the remaining paper are fsrdc research outputs. The code uses the pandas, regex, fuzzywuzzy and tqdm modules in Python.

Inputs
The script uses two inputs; the csv file from step 2 and the 2024 ResearchOutputs excel. Using try/except statements, both are loaded from github and saved to dataframes using pandas. Dataframes were used to perform the processing.

Uniqueness Check
Once files are loaded,  a uniqueness check is performed to remove any papers that are present in the 2024 dataset. Check is run on the DOIs and paper titles. Before checks are run, the dois have to be obtained and normalized and the titles have to be matched normalized also. 
For the Dois. Using the ‘OutputBiblio’ column in 2024 dataset, the doi is obtained (see image below). For local dataset, ‘DOI’ column is used to obtain the doi. Regex is then used to remove the http and doi.org portions. Then for both datasets, slashes and dots are removed. Titles from both datasets are also normalized to remove whitespace, punctuations and make it all lower case.



Once everything is normalized, a for loop with tqdm is run to loop through all rows in the local dataset and first check if it has an exact matching doi from the 2024 dataset. If it does not, then it performs a fuzzywuzzy sort ratio matching. It checks each title in the local dataset that did not have a matching doi to every title in the 2024 dataset. For the fuzzy matching, threshold was set at 90 to allow for some differences in titles that could occur from possible variations in record formatting. Once both checks are done, it selects only the papers that passed both tests and moves on to the next step.

FSRDC Output Check
This step of the script is where the abstract of the papers is checked for keywords. The full list of keywords is obtained manually from the ProjectAllMetadata excel workbook in the dataset sheet. In addition to the list of data names and datacodes, it also checks whether these words were mentioned in the abstract: 'Census Bureau', 'FSRDC', 'RDC', 'Census', 'IRS', 'BEA'. After the check, duplicates are removed based on the title to confirm that web search and api enhancement did not have multiple similar papers. And only papers that passed the fsrdc check are obtained.

Output
The only output is a csv file that is saved and the first 5 rows are printed out. Relevant columns included in the csv from processed data include Uniqueness and FSRDC_related.
Step 4: Graph Construction and Analysis
1. Graph Construction Methodology
The research output graph was constructed using NetworkX, with each node representing a unique research output. 
Connections between outputs were established based on a weighted similarity score calculated from multiple metadata attributes:

1. Agency/RDC match (weight: 1)
2. Temporal proximity (weight: up to 1, with exact year matches receiving highest scores)
3. Shared authors (weight: up to 3, scaling with the number of shared authors)
4. Project PI match (weight: 1)
5. Output venue match (weight: 1)
6. Project ID match (weight: 3, highest weight reflecting strong institutional connection)
7. Keyword overlap (weight: up to 2, scaling with the number of shared keywords)

Connections were established when the combined similarity score exceeded 0.5


2. Network Metrics Analysis

Number of nodes (research outputs)
287
Number of edges (connections)
2367
Network density
0.057674
Number of connected components
7
Size of largest component
281 nodes (97.9% of network)
Average degree
16.49
Average clustering coefficient
0.5095
Average betweenness centrality
0.005880
Average closeness centrality
0.384789
Average eigenvector centrality
0.033010


Average degree shows each research output connects to approximately 16 others

The clustering coefficient measures how much nodes tend to cluster together. A value of 0.5095 indicates that about 51% of possible connections among neighbors of a typical node actually exist. This high clustering suggests research outputs form tight-knit communities or research clusters

Betweenness centrality measures how often a node lies on the shortest path between other nodes. The low average value means most nodes aren't "bridges" between communities

Closeness centrality measures how close a node is to all other nodes in the network. The moderate value suggests research outputs are reasonably well-connected to the broader research community

Eigenvector centrality measures a node's influence based on its connections to other influential nodes. Low average eigenvector centrality suggests the network may have a pronounced hierarchical structure, where a small fraction of research outputs serve as "core" or "hub" nodes, while the majority of research outputs occupy "peripheral" positions


3. Community Detection & Clustering
We applied the Louvain method for community detection, identifying 15 clusters with modularity 0.5125. Each cluster contains research outputs with strong internal similarity.
This method optimizes modularity, a quality measure that reflects how well the graph is divided into communities. It starts by assigning each node to its own community and iteratively merges communities to maximize modularity.

The following is the content printed out by the code runtime, which includes the 5 largest clusters with their top keywords, common projects and year range

Largest Research Clusters:
----------------------------------------------------------------------
Cluster 1: 52 research outputs
  Top keywords: effect, job, growth
  Common projects: W2326890393, 215201262
  Year range: 1996 - 1996

Cluster 2: 44 research outputs
  Top keywords: state, index, economy
  Common projects: 639366213, 619649390

Cluster 3: 40 research outputs
  Top keywords: health, population, national
  Common projects: W2049165791, W2051239218
  Year range: 1978 - 2018

Cluster 4: 36 research outputs
  Top keywords: data, report, study
  Common projects: W2118502261, W1555600854
  Year range: 1987 - 2004

Cluster 5: 30 research outputs
  Top keywords: census, impact, comparison
  Common projects: W2153019931, W2162107892
  Year range: 1990 - 2020



4. Visualization 
The network visualization uses node sizes to represent degree, and color gradients for publication years. 

Nodes with higher connectivity are more central.
Edge lengths are determined by a spring layout, shorter edges indicate stronger connections between research outputs (higher similarity scores)




The cluster visualization highlights the community structure within the research network.
Each distinct color represents a different research cluster identified by the Louvain community detection algorithm
Node sizes remain proportional to degree centrality





5. Code Flow
Data Loading and Preprocessing:
load_data_from_pandas() reads the CSV file containing research output data
For each row, a ResearchOutput object is created to encapsulate all metadata
extract_keywords() uses nltk package to identify important terms from ‘OutputTitle’ column
Graph Construction:
build_networkx_graph() creates a NetworkX graph with research outputs as nodes
calculate_similarity() determines the strength of connection between any two outputs
Edges are added between nodes when similarity exceeds the threshold
Network Analysis:
calculate_network_metrics() computes various metrics to characterize the network
Basic metrics (density, component count, etc.) provide overview of network structure
Centrality metrics identify influential nodes in the network
Cluster Analysis:
detect_clusters() identifies cohesive communities within the network
Multiple algorithms are supported (Louvain and greedy modularity)
Results are analyzed to identify key themes within each cluster
Visualization:
visualize_graph() creates a visual representation of the entire network
visualize_clusters() shows the community structure with color-coding
Node sizes, colors, and edge weights reflect important properties of the data
6. Testing
We used unittest in this step to verify the core methods below
Test code is named graphTest.py in the submission. All 5 tests were passed.

Keyword Extraction Tests: Verify that important keywords are correctly identified from research titles
Research Output Tests: Ensure object creation and attribute handling work properly
Similarity Calculation Tests: Validate that similarity scores correctly reflect relationships between outputs
Graph Construction Tests: Check that the network building process creates the expected structure
Metrics Calculation Tests: Confirm that network metrics are computed correctly



Step 5: Data Analysis & Visualization
This portion of Project 2 focuses on Step 5: Data Analysis & Visualization. We take the final ProcessedData.csv produced after Steps 1–4 (web scraping, API integration, data processing, and FSRDC checks) and transform the relevant columns into graphical insights.

Unlike earlier steps, where we attempted to gather or clean data, Step 5 is about exploring the curated dataset:
Generating descriptive statistics
Checking missing values
Converting columns to the right data types
Creating histograms, box plots, bar charts, line charts
(Optionally) performing statistical tests if sufficient numeric data is present

The key output of this step is a series of plots (and summarized console output) that help us uncover distribution patterns, outliers, or trends in FSRDC research outputs.

Data and Code Structure

Following the project recommendation for a modular design, we placed our Step 5 code in a module named visualization.py. Within it, we defined a function called run_step5_analysis(csv_file="ProcessedData.csv") that encapsulates all our analysis logic (loading data, plotting, printing statistics, etc.). Our main.py script then imports and calls this function after Steps 1–4. An example snippet:
# main.py (excerpt)

from visualization import run_step5_analysis

def main():
    # Steps 1–4 would be invoked here...
    # step1_scraping.run_scraping()
    # step2_api_integration.merge_api_data()
    # step3_data_processing.perform_entity_resolution()
    # ...
    
    # Step 5: Data Analysis & Visualization
    run_step5_analysis("ProcessedData.csv")

if __name__ == "__main__":
    main()

This approach ensures our entry point (main.py) orchestrates each step seamlessly while keeping Step 5’s code self-contained in its own module.
Methodology
Data Loading
We invoke run_step5_analysis("ProcessedData.csv"), which calls pd.read_csv() to load the final curated dataset.
First, we print the head of the DataFrame (df.head()), .info(), and .describe() to verify the data shape, column types, and basic numeric summaries (e.g., means, medians, standard deviations) for any numeric columns.
Missing Value Inspection
We call df.isnull().sum() to count how many null/NaN values exist in each column.
This step guides us in deciding which plots or analyses are feasible. For instance, if a column is empty, we skip the corresponding plots.
Column-Specific Handling & Type Conversion
Our dataset typically contains columns like FuzzScores, OutputYear, and FSRDC_related (because Steps 1–4 produced them).
For numeric columns (FuzzScores, OutputYear), we apply pd.to_numeric(..., errors='coerce') to ensure they’re recognized as floats or ints.
For boolean columns like FSRDC_related, we convert strings to bool if needed, ensuring the column can be used in a bar chart.
Visualizations
FuzzScores
Histogram: Plots the distribution of fuzzy-match scores used in deduplication. This reveals how many titles are near-duplicates (high scores) vs. entirely different (lower scores).
Box Plot: Shows the median, interquartile range, and potential outliers for these scores.
OutputYear
Histogram: Depicts how many new FSRDC outputs appear in each year. If the dataset only partially includes years, this still gives a partial timeline.
Line Chart: We group the DataFrame by OutputYear, count the records, and plot a simple line marking the total outputs over time—helpful for time-series analysis.
FSRDC_related
Bar Chart: If FSRDC_related is a boolean, we show how many records are flagged as True vs. False. This helps gauge coverage of truly FSRDC-related research.
Statistical Analysis (Optional)
Because citations is not included in our final dataset, we omit correlation or t-tests referencing citation counts.
If, in the future, columns like citations, authors_count, or page_count become available, we could easily reintroduce correlation tests (e.g., Pearson’s) or group comparisons (t-tests, ANOVA).
Key Insights & Observations
From these visualizations, we can discover:
FuzzScores Distribution
Are most scores clustered around ~50–60, suggesting partial title overlaps but not duplicates? Or are some near 90, indicating possible near-duplicate references? The box plot clarifies overall spread.
Yearly Trends
The OutputYear histogram and line chart might show increasing research output in certain periods (e.g., a spike around 2010–2015).
If older publications are missing, we might see a truncated timeline. This can direct us to fill data gaps or refine the year-extraction steps in prior phases.
FSRDC Coverage
If nearly all entries in ProcessedData.csv are marked FSRDC_related = True, that confirms the dataset is strongly aligned with the FSRDC usage criteria. If not, we might investigate how some entries got included despite not being FSRDC-related.
Missing Data
By looking at the missing-value summary, we see which fields are incomplete. This can hint at potential expansions (e.g., adding or cleaning up certain metadata fields in Step 2 or Step 3)
Conclusion 
This Step 5 code and methodology complete our pipeline by delivering clear, interpretable visual representations of ProcessedData.csv. We rely on pandas for summarization, matplotlib for plotting, and minimal type conversion or error handling to ensure stable run time. 
By modularizing this analysis in visualization.py and calling it from main.py, we maintain a clean and extensible structure, ready to adapt to future expansions or changing data.
