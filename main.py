import requests
import tempfile
import subprocess

#list of scripts raw files from github
scripts_to_run = ['https://raw.githubusercontent.com/Martey18/CIT5900_002_Group8_Project/refs/heads/main/web_scraping.py',
                  'https://raw.githubusercontent.com/Martey18/CIT5900_002_Group8_Project/refs/heads/main/api_integration.py',
                  'https://raw.githubusercontent.com/Martey18/CIT5900_002_Group8_Project/refs/heads/main/data_processing.py',
                  'https://raw.githubusercontent.com/Martey18/CIT5900_002_Group8_Project/refs/heads/main/graph_analysis.py',
                  'https://raw.githubusercontent.com/Martey18/CIT5900_002_Group8_Project/refs/heads/main/visualization.py']
script_names = ['web scraping','api integration','data processing','graph analysis','visualization']

#for loop to download each script to run
for i, script in enumerate(scripts_to_run):
    print(f"Downloading {script_names[i]} script: {script}")
    response = requests.get(script)
    #if script did not download exit since other scripts cannot run
    if response.status_code != 200:
        print(f"Script failed to download {script_names[i]} script from {script}")
        SystemExit
    #once script is loaded run it 
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_scpt:
        #Save temporary file 
        tmp_scpt.write(response.content)
        tmp_scpt.flush()
        print(f'Running {script_names[i]} script')
        #use subprocess to run
        result = subprocess.run(["python", tmp_scpt.name])
        #if error occurred, then exit since other scripts depend on outputs from first script
        if result.returncode != 0:
            print(f"{script_names[i]} exited with error code {result.returncode}")
            SystemExit
        else:
            print(f"{script_names[i]} finished successfully")
    #Alert that next phase is beginning
    if i != 4:
        print(f"Moving on to {script_names[i+1]}")
    else:
        print("All scripts executed")
        