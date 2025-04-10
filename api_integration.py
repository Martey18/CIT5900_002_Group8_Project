import json
import pandas as pd
import requests
import re
import time
import os

#########################
# Final Schema Columns
#########################
FINAL_COLUMNS = ['ProjectID', 'ProjectStatus', 'ProjectTitle', 'ProjectRDC', 
                 'ProjectStartYear', 'ProjectEndYear', 'ProjectPI', 'OutputTitle', 
                 'OutputBiblio', 'OutputType', 'OutputStatus', 'OutputVenue', 
                 'OutputYear', 'OutputMonth', 'OutputVolume', 'OutputNumber', 
                 'OutputPages', 'DOI', 'Authors', 'Abstract']

#########################
# OpenAlex API Functions
#########################
def reconstruct_abstract(abstract_dict):
    """Reconstructs an abstract from OpenAlex's abstract_inverted_index format."""
    if not isinstance(abstract_dict, dict):
        raise ValueError("Expected abstract_dict to be a dict")
    if not abstract_dict:
        return None
    try:
        word_positions = [(pos, word) for word, positions in abstract_dict.items() for pos in positions]
        sorted_words = sorted(word_positions, key=lambda x: x[0])
        return " ".join(word for _, word in sorted_words)
    except Exception as e:
        print(f"Error reconstructing abstract: {e}")
        return None

def fetch_openalex_data(keywords, per_page=50):
    """
    Fetches data from the OpenAlex API based on the provided keywords.
    Returns a DataFrame with the final schema.
    """
    url = f"https://api.openalex.org/works?filter=abstract.search:{keywords}&per_page={per_page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"OpenAlex API Request Exception: {e}")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Error decoding OpenAlex JSON: {e}")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    
    results = []
    for work in data.get("results", []):
        try:
            reconstructed_abs = reconstruct_abstract(work.get("abstract_inverted_index", {}))
            full_project_id = work.get("id", None)
            project_id = re.search(r'[^/]+$', full_project_id).group() if full_project_id else None
            results.append({
                "ProjectID": project_id,
                "ProjectStatus": work.get("status", None),
                "ProjectTitle": work.get("title", None),
                "ProjectRDC": work.get("rdc", None),
                "ProjectStartYear": work.get("start_year", None),
                "ProjectEndYear": work.get("end_year", None),
                "ProjectPI": work.get("authorships", [{}])[0].get("author", {}).get("display_name", None) if work.get("authorships") else None,
                "OutputTitle": work.get("title", None),
                "OutputBiblio": work.get("biblio", None),
                "OutputType": work.get("type", None),
                "OutputStatus": work.get("status", None),
                "OutputVenue": work.get("host_venue", {}).get("display_name", None),
                "OutputYear": work.get("publication_year", None),
                "OutputMonth": work.get("publication_month", None),
                "OutputVolume": work.get("biblio", {}).get("volume", None),
                "OutputNumber": work.get("biblio", {}).get("issue", None),
                "OutputPages": (work.get("biblio", {}).get("first_page", None) + "-" + work.get("biblio", {}).get("last_page", None)) if work.get("biblio", {}).get("first_page") else None,
                "DOI": work.get("doi", None),
                "Authors": ", ".join([author['author']['display_name'] for author in work.get("authorships", [])]) if work.get("authorships") else None,
                "Abstract": reconstructed_abs
            })
        except Exception as e:
            print(f"Error processing an OpenAlex work: {e}")
            continue
    df = pd.DataFrame(results, columns=FINAL_COLUMNS)
    # Basic test: Ensure we have the expected columns.
    assert set(df.columns) == set(FINAL_COLUMNS), "OpenAlex DataFrame does not match expected schema."
    return df

#########################
# CORE API Functions
#########################
def get_authors_str(authors_list):
    """Converts a list of authors (dicts or strings) to a comma-separated string."""
    names = []
    try:
        for author in authors_list:
            if isinstance(author, dict):
                name = author.get("name", None)
                if name:
                    names.append(name)
            else:
                names.append(str(author))
    except Exception as e:
        print(f"Error processing authors list: {e}")
        return None
    return ", ".join(names) if names else None

def fetch_core_data(keywords, limit=100, offset=0, api_key="uQXVRMa9IpkqghWnoxL2tm3CUj8dHr4F"):
    """
    Fetches a batch of CORE API outputs based on the provided keywords.
    Implements a retry mechanism for HTTP 429 errors.
    Returns a DataFrame with the final schema.
    """
    if isinstance(keywords, list):
        query = " OR ".join([f'fullText:"{kw}"' for kw in keywords])
    else:
        query = f'fullText:"{keywords}"'
    
    url = "https://api.core.ac.uk/v3/search/outputs"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"q": query, "limit": limit, "offset": offset}
    
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, params=params)
        except requests.RequestException as e:
            print(f"CORE API Request Exception at offset {offset}: {e}")
            return pd.DataFrame(columns=FINAL_COLUMNS)
        
        if response.status_code == 200:
            break
        elif response.status_code == 429:
            print(f"CORE API Error 429 at offset {offset}. Retrying in 5 seconds (attempt {retries+1})...")
            time.sleep(5)
            retries += 1
        else:
            print(f"CORE API Error {response.status_code}: {response.text}")
            return pd.DataFrame(columns=FINAL_COLUMNS)
    
    if response.status_code != 200:
        print(f"Failed to retrieve CORE data for offset {offset} after {max_retries} attempts.")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Error decoding CORE API JSON at offset {offset}: {e}")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    
    results = data.get("results", [])
    processed_results = []
    for item in results:
        try:
            project_id = item.get("id", None)
            project_title = item.get("title", None)
            authors_list = item.get("authors", [])
            authors_str = get_authors_str(authors_list)
            if authors_list:
                project_pi = authors_list[0].get("name", None) if isinstance(authors_list[0], dict) else authors_list[0]
            else:
                project_pi = None
            
            year_published = item.get("year_published", None)
            if not year_published or year_published == "":
                published_date = item.get("published_date", "")
                if published_date and "-" in published_date:
                    output_year = published_date.split("-")[0]
                else:
                    output_year = None
            else:
                output_year = year_published
            
            doi = item.get("doi", None)
            abstract = item.get("abstract", None)
            output_biblio = item.get("download_url", None)
            output_type = item.get("document_type", None)
            publisher_info = item.get("publisher", {})
            output_venue = publisher_info.get("name", None) if isinstance(publisher_info, dict) else None
            
            processed_results.append({
                "ProjectID": project_id,
                "ProjectStatus": None,
                "ProjectTitle": project_title,
                "ProjectRDC": None,
                "ProjectStartYear": None,
                "ProjectEndYear": None,
                "ProjectPI": project_pi,
                "OutputTitle": project_title,
                "OutputBiblio": output_biblio,
                "OutputType": output_type,
                "OutputStatus": None,
                "OutputVenue": output_venue,
                "OutputYear": output_year,
                "OutputMonth": None,
                "OutputVolume": None,
                "OutputNumber": None,
                "OutputPages": None,
                "DOI": doi,
                "Authors": authors_str,
                "Abstract": abstract
            })
        except Exception as e:
            print(f"Error processing a CORE API item at offset {offset}: {e}")
            continue
    df = pd.DataFrame(processed_results, columns=FINAL_COLUMNS)
    # Basic test: Ensure the DataFrame conforms to the expected schema.
    assert set(df.columns) == set(FINAL_COLUMNS), "CORE DataFrame schema mismatch."
    print(f"Retrieved {len(processed_results)} CORE outputs for offset {offset}.")
    return df

def fetch_core_data_all(keywords, total_results=300, batch_size=100, api_key="uQXVRMa9IpkqghWnoxL2tm3CUj8dHr4F"):
    """
    Retrieves CORE API outputs in batches and combines them into a single DataFrame.
    """
    all_dfs = []
    for offset in range(0, total_results, batch_size):
        df_batch = fetch_core_data(keywords, limit=batch_size, offset=offset, api_key=api_key)
        if df_batch.empty:
            print(f"No data returned for offset {offset}, stopping further requests.")
            break
        all_dfs.append(df_batch)
        time.sleep(1)
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"Total CORE outputs retrieved: {len(final_df)}")
        # Test to ensure the final DataFrame has the expected schema.
        assert set(final_df.columns) == set(FINAL_COLUMNS), "Final CORE DataFrame schema mismatch."
        return final_df
    else:
        print("No CORE outputs retrieved.")
        return pd.DataFrame(columns=FINAL_COLUMNS)

#########################
# Web Scraping CSV Functions
#########################
def transform_web_scraping_data(csv_file):
    """
    Reads the CSV file (with columns Title, Authors, Abstract) and transforms it to match the final schema.
    For ProjectPI, the first author (if available) is used.
    """
    if not os.path.exists(csv_file):
        print(f"Error: CSV file '{csv_file}' not found.")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV file '{csv_file}': {e}")
        return pd.DataFrame(columns=FINAL_COLUMNS)
    
    transformed_rows = []
    for _, row in df.iterrows():
        try:
            title = row.get("Title", None)
            authors = row.get("Authors", None)
            abstract = row.get("Abstract", None)
            if authors and isinstance(authors, str):
                pi = authors.split(",")[0].strip()
            else:
                pi = None
            transformed_rows.append({
                "ProjectID": None,
                "ProjectStatus": None,
                "ProjectTitle": title,
                "ProjectRDC": None,
                "ProjectStartYear": None,
                "ProjectEndYear": None,
                "ProjectPI": pi,
                "OutputTitle": title,
                "OutputBiblio": None,
                "OutputType": None,
                "OutputStatus": None,
                "OutputVenue": None,
                "OutputYear": None,
                "OutputMonth": None,
                "OutputVolume": None,
                "OutputNumber": None,
                "OutputPages": None,
                "DOI": None,
                "Authors": authors,
                "Abstract": abstract
            })
        except Exception as e:
            print(f"Error processing a row in CSV: {e}")
            continue
    df_transformed = pd.DataFrame(transformed_rows, columns=FINAL_COLUMNS)
    # Test to ensure transformed CSV data matches the expected schema.
    assert set(df_transformed.columns) == set(FINAL_COLUMNS), "Web scraping CSV DataFrame schema mismatch."
    return df_transformed

#########################
# Merge Functions
#########################
def merge_api_data(openalex_df, core_df):
    """
    Merges OpenAlex and CORE API data (both in the final schema) into a single DataFrame.
    """
    try:
        combined_df = pd.concat([openalex_df, core_df], ignore_index=True)
        # Test that combined DataFrame has the final columns.
        assert set(combined_df.columns) == set(FINAL_COLUMNS), "Combined API DataFrame schema mismatch."
        return combined_df
    except Exception as e:
        print(f"Error merging API data: {e}")
        return pd.DataFrame(columns=FINAL_COLUMNS)

def merge_with_web_scraping(web_csv_file, api_df, output_file):
    """
    Merges the web_scraping CSV data (transformed to the final schema) with the API data
    and saves the result as a CSV file.
    """
    web_df = transform_web_scraping_data(web_csv_file)
    try:
        merged_df = pd.concat([web_df, api_df], ignore_index=True)
        # Ensure merged_df has the final schema.
        assert set(merged_df.columns) == set(FINAL_COLUMNS), "Merged DataFrame schema mismatch."
    except Exception as e:
        print(f"Error merging with web scraping data: {e}")
        merged_df = pd.DataFrame(columns=FINAL_COLUMNS)
    try:
        merged_df.to_csv(output_file, index=False)
        print(f"Merged data saved to {output_file}")
    except Exception as e:
        print(f"Error saving merged data to CSV: {e}")
    return merged_df

#########################
# Main Execution Block
#########################
if __name__ == "__main__":
    try:
        # Define keywords for API searches.
        openalex_keywords = "FSRDC|Census|IRS|BEA|RDC|confidentiality review|U.S. Census Bureau|Census Bureau|Bureau of Economic Analysis|[RDC]"
        core_keywords = ["FSRDC", "Census", "BEA", "RDC", "U.S. Census Bureau", "Bureau of Economic Analysis"]
        
        # Fetch data from OpenAlex.
        openalex_df = fetch_openalex_data(openalex_keywords, per_page=50)
        print("OpenAlex data retrieved:")
        print(openalex_df.head())
        assert not openalex_df.empty, "OpenAlex DataFrame is empty."
        
        # Fetch data from CORE API (using total_results=300 to avoid infinite retries).
        core_df = fetch_core_data_all(core_keywords, total_results=300, batch_size=100, 
                                      api_key="uQXVRMa9IpkqghWnoxL2tm3CUj8dHr4F")
        print("CORE API data retrieved:")
        print(core_df.head())
        # It's acceptable if core_df is empty, but warn if so.
        if core_df.empty:
            print("Warning: CORE API returned no data.")
        
        # Merge the API outputs.
        combined_api_df = merge_api_data(openalex_df, core_df)
        print("Combined API data:")
        print(combined_api_df.head())
        
        # Merge with the web_scraping CSV file.
        merged_df = merge_with_web_scraping("web_scraping.csv", combined_api_df, "Updated_CombinedOutputs.csv")
        print("Final merged DataFrame:")
        print(merged_df.head())
    except AssertionError as ae:
        print(f"Assertion Error: {ae}")
    except Exception as e:
        print(f"An unexpected error occurred in main execution: {e}")
