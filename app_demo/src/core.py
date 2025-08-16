# -*- coding: utf-8 -*-
"""
Chemical Classification Pipeline - OOP Version
Created by: User
Purpose: Process chemical data through classification, conversion, and merging
"""

import requests
import json
import os
import time
import pandas as pd
import glob
import datetime
from requests.exceptions import HTTPError, RequestException
from openpyxl import load_workbook
from CTSgetPy import CTSgetPy as ct

# ================== CONFIGURATION ==================
class Config:
    """Configuration class for all pipeline settings"""
    
    # API Settings
    CLASSYFIRE_SITE = 'http://classyfire.wishartlab.com'
    REQUEST_TIMEOUT = 10
    REQUEST_RETRIES = 3
    BACKOFF_FACTOR = 0.3
    API_DELAY = 6  # seconds between API calls
    
    # Folder Paths
    SOURCE_FOLDER = 'data/clean_result'
    GROUPING_FOLDER = 'data/grouping_result'
    FINAL_RESULT_FOLDER = 'data/final_result'
    CONVERT_RESULT_FOLDER = 'data/convert_result'
    METABOANALYST_FOLDER = 'data/metaboanalyst_pubchem'
    
    # Conversion Settings
    CONVERSION_SOURCE = 'InChIKey'
    CONVERSION_TARGETS = ['Human Metabolome Database', 'KEGG', 'PubChem CID', 'ChEBI']
    
    # Output Settings
    MERGE_OUTPUT_FILE = 'merge_result.csv'


# ================== STEP 1: CHEMICAL CLASSIFICATION ==================
class ChemicalClassifier:
    """Handle chemical classification using ClassyFire API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.site = config.CLASSYFIRE_SITE
        
    def get_classification(self, inchikey: str, format: str = 'json') -> dict:
        """
        Get chemical classification from ClassyFire API
        
        Args:
            inchikey: InChI key for the chemical
            format: Response format (default: json)
            
        Returns:
            Dictionary containing classification data
        """
        url = f'{self.site}/entities/{inchikey}.{format}'
        headers = {'Accept': f'application/{format}'}
        
        for attempt in range(self.config.REQUEST_RETRIES):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=self.config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except HTTPError as http_err:
                if response.status_code in [404, 500, 504, 408]:
                    print(f"HTTP error occurred: {http_err}")
                    return {}
                else:
                    print(f"HTTP error occurred: {http_err}")
                    return {}
                    
            except RequestException as req_err:
                print(f'Request error occurred: {req_err}')
                if attempt < self.config.REQUEST_RETRIES - 1:
                    time.sleep(self.config.BACKOFF_FACTOR * (2 ** attempt))
                else:
                    return {}
    
    def process_classification_files(self):
        """Process all Excel files in source folder for classification"""
        # Create output folder if it doesn't exist
        if not os.path.exists(self.config.GROUPING_FOLDER):
            os.makedirs(self.config.GROUPING_FOLDER)
        
        # Get all Excel files
        src_files = [f for f in os.listdir(self.config.SOURCE_FOLDER) 
                    if f.endswith(('.xlsx','.csv','.txt'))]
        
        for file in src_files:
            self._process_single_file(file)
    
    def _process_single_file(self, filename: str):
        """Process a single Excel file for classification"""
        file_path = os.path.join(self.config.SOURCE_FOLDER, filename)
        #df = pd.read_excel(file_path)
        df = pd.read_csv(file_path, sep = '\t' )
        if 'Title' not in df.columns and 'Name' in df.columns:
            df.rename(columns={'Name': 'Title'}, inplace=True)

        
        # Filter rows where title is not unknown
        filtered_df = df[df['Title'] != 'Unknown']
        
        # Initialize data containers
        classification_data = {
            'title': [],
            'inchikey': [],
            'Kingdom': [],
            'Superclass': [],
            'class': [],
            'subclass': [],
            'intermediate_nodes': [],
            'direct_parents': []
        }
        
        # Process each row
        for _, row in filtered_df.iterrows():
            title = row['Title']
            inchikey = row['InChIKey']
            
            # Get classification
            res = self.get_classification(inchikey)
            print(json.dumps(res, indent=4))
            
            # Extract classification data
            classification_info = self._extract_classification_info(res)
            
            # Append data
            classification_data['title'].append(title)
            classification_data['inchikey'].append(inchikey)
            classification_data['Kingdom'].append(classification_info['kingdom'])
            classification_data['Superclass'].append(classification_info['superclass'])
            classification_data['class'].append(classification_info['class'])
            classification_data['subclass'].append(classification_info['subclass'])
            classification_data['intermediate_nodes'].append(classification_info['intermediate_nodes'])
            classification_data['direct_parents'].append(classification_info['direct_parent'])
            
            # Delay between API calls
            time.sleep(self.config.API_DELAY)
        
        # Save results
        self._save_classification_results(classification_data, filename)
    
    def _extract_classification_info(self, res: dict) -> dict:
        """Extract classification information from API response"""
        kingdom = res.get('kingdom', {}).get('name', '') if res.get('kingdom') else ''
        superclass = res.get('superclass', {}).get('name', '') if res.get('superclass') else ''
        class_ = res.get('class', {}).get('name', '') if res.get('class') else ''
        subclass = res.get('subclass', {}).get('name', '') if res.get('subclass') else ''
        direct_parent = res.get('direct_parent', {}).get('name', '') if res.get('direct_parent') else ''
        
        intermediate_nodes = []
        if 'intermediate_nodes' in res:
            for node in res['intermediate_nodes']:
                intermediate_nodes.append(node.get('name', ''))
        
        return {
            'kingdom': kingdom,
            'superclass': superclass,
            'class': class_,
            'subclass': subclass,
            'direct_parent': direct_parent,
            'intermediate_nodes': '; '.join(intermediate_nodes)
        }
    
    def _save_classification_results(self, data: dict, filename: str):
        """Save classification results to CSV file"""
        result_df = pd.DataFrame(data)
        output_file_path = os.path.join(
            self.config.GROUPING_FOLDER, 
            filename.replace('.xlsx', '.csv')
        )
        result_df.to_csv(output_file_path, index=False)
        print(f'Saved processed data to {output_file_path}')


# ================== STEP 2: DATA MERGING ==================
class DataMerger:
    """Handle merging of classification data with original data"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def merge_classification_data(self):
        """Merge classification data with original Excel files"""
        # Build InChIKey dictionary from classification results
        inchikey_dict = self._build_inchikey_dictionary()
        
        # Process original Excel files
        self._process_original_files(inchikey_dict)
    
    def _build_inchikey_dictionary(self) -> dict:
        """Build dictionary mapping InChIKey to classification data"""
        inchikey_dict = {}
        
        for root, dirs, files in os.walk(self.config.GROUPING_FOLDER):
            for file in files:
                if file.endswith((".csv",'.xlsx','.txt')):
                    file_path = os.path.join(root, file)
                    src_df = pd.read_csv(file_path, sep=',')
                    
                    for _, row in src_df.iterrows():
                        inchikey = row["inchikey"]
                        if inchikey not in inchikey_dict:
                            inchikey_dict[inchikey] = []
                        
                        # Add classification levels if they exist
                        for level in ["direct_parents", "Kingdom", "Superclass", "class", "subclass"]:
                            if row[level]:
                                inchikey_dict[inchikey].append(row[level])
        
        return inchikey_dict
    
    def _process_original_files(self, inchikey_dict: dict):
        """Process original Excel files and add classification data"""
        # Create output folder
        if not os.path.exists(self.config.FINAL_RESULT_FOLDER):
            os.makedirs(self.config.FINAL_RESULT_FOLDER)
        
        for root, dirs, files in os.walk(self.config.SOURCE_FOLDER):
            for file in files:
                if file.endswith((".xlsx",'.csv', '.txt')):
                    file_path = os.path.join(root, file)
                    target_df = pd.read_csv(file_path,sep='\t')
                    
                    # Add Class column
                    target_df["Class"] = None
                    
                    # Fill classification data
                    for index, row in target_df.iterrows():
                        inchikey = row["InChIKey"]
                        if inchikey and (inchikey in inchikey_dict):
                            target_df.at[index, "Class"] = inchikey_dict[inchikey]
                    
                    # Save result
                    self._save_merged_file(target_df, file)
    
    def _save_merged_file(self, df: pd.DataFrame, filename: str):
        """Save merged data to CSV file with timestamp"""
        current_datetime = datetime.datetime.now()
        base_filename = os.path.basename(filename)
        if base_filename.endswith((".xlsx",'.csv','.txt')):
            base_filename = base_filename[:-5]
        
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        export_file_name = f"{base_filename}_{formatted_datetime}.csv"
        export_file_path = os.path.join(self.config.FINAL_RESULT_FOLDER, export_file_name)
        
        df.to_csv(export_file_path, index=False)
        print(f"The file saved at {export_file_path}")


# ================== STEP 3: CHEMICAL CONVERSION ==================
class ChemicalConverter:
    """Handle chemical identifier conversion using CTS API"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def convert_identifiers(self):
        """Convert InChIKey to other chemical identifiers"""
        file_list = glob.glob(os.path.join(self.config.FINAL_RESULT_FOLDER, '*'))
        
        if len(file_list) == 0:
            print('[ERROR] No files in the final_result folder to process')
            return
        
        # Create output folder
        if not os.path.exists(self.config.CONVERT_RESULT_FOLDER):
            os.makedirs(self.config.CONVERT_RESULT_FOLDER)
        
        for file_path in file_list:
            self._convert_single_file(file_path)
    
    def _convert_single_file(self, file_path: str):
        """Convert identifiers in a single file"""
        df = pd.read_csv(file_path)
        print(f"Processing {file_path}")
        
        # Convert to each target identifier
        for target in self.config.CONVERSION_TARGETS:
            print(f"Converting to {target}")
            
            # Get conversion results
            res = self._transform_inchikey(df['InChIKey'].tolist(), target)
            df[target] = None
            
            # Map results back to DataFrame
            for key, value in res[target].items():
                if key != 'nan':
                    row_indices = df.index[df['InChIKey'] == key].tolist()
                    if row_indices:
                        df.at[row_indices[0], target] = value
        
        # Save converted data
        output_filename = os.path.basename(file_path)
        export_file_path = os.path.join(self.config.CONVERT_RESULT_FOLDER, output_filename)
        df.to_csv(export_file_path, index=False)
        print(f"Saved converted data to {export_file_path}")
    
    def _transform_inchikey(self, identifiers: list, target: str) -> dict:
        """Transform InChIKey to target identifier using CTS API"""
        if identifiers:
            result = ct.CTSget(self.config.CONVERSION_SOURCE, target, identifiers)
        else:
            result = {}
        return result


# ================== STEP 4: DATA AGGREGATION ==================
class DataAggregator:
    """Handle final data aggregation and merging"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def aggregate_data(self):
        """Aggregate all converted data into final merged file"""
        csv_files = [f for f in os.listdir(self.config.CONVERT_RESULT_FOLDER) 
                    if f.endswith((".csv",".txt"))]
        
        if not csv_files:
            print("No CSV files found to aggregate")
            return
        
        print("Starting to merge these files:")
        print(csv_files)
        
        # Initialize output DataFrame
        df_output = pd.DataFrame(columns=['Title', 'PubChem CID'])
        
        # Process each file
        for file_name in csv_files:
            file_path = os.path.join(self.config.CONVERT_RESULT_FOLDER, file_name)
            df_input = pd.read_csv(file_path)
            if 'Title' not in df_input.columns and 'Name' in df_input.columns:
                df_input.rename(columns={'Name': 'Title'}, inplace=True)
            
            column_name = file_name.split('.')[0]
            df_output[column_name] = ''
            
            # Merge data
            df_output = self._merge_file_data(df_input, df_output, column_name)
        
        # Save final result
        self._save_aggregated_data(df_output)
    
    def _merge_file_data(self, df_input: pd.DataFrame, df_output: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """Merge data from a single file into output DataFrame"""
        for _, row in df_input.iterrows():
            title = row['Title']
            area = row['Area']
            cid = row['PubChem CID']
            
            # Check if title already exists
            existing_row = df_output.loc[df_output['Title'] == title]
            
            if not existing_row.empty:
                # Update existing row
                df_output.at[existing_row.index[0], column_name] = area
            else:
                # Create new row
                new_row = pd.DataFrame({
                    'Title': [title],
                    'PubChem CID': [cid],
                    column_name: [area]
                })
                df_output = pd.concat([df_output, new_row], ignore_index=True)
        
        return df_output
    
    def _save_aggregated_data(self, df_output: pd.DataFrame):
        """Save aggregated data to final output file"""
        if not os.path.exists(self.config.METABOANALYST_FOLDER):
            os.makedirs(self.config.METABOANALYST_FOLDER)
        
        export_file_path = os.path.join(
            self.config.METABOANALYST_FOLDER, 
            self.config.MERGE_OUTPUT_FILE
        )
        
        df_output.to_csv(export_file_path, index=False)
        print(f"Merging data completed. Final file saved at: {export_file_path}")


# ================== MAIN PIPELINE ==================
class ChemicalAnalysisPipeline:
    """Main pipeline orchestrating all processing steps"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.classifier = ChemicalClassifier(self.config)
        self.merger = DataMerger(self.config)
        self.converter = ChemicalConverter(self.config)
        self.aggregator = DataAggregator(self.config)
    
    def run_full_pipeline(self):
        """Run the complete chemical analysis pipeline"""
        print("=== Starting Chemical Analysis Pipeline ===")
        
        try:
            print("\n1. Running chemical classification...")
            self.classifier.process_classification_files()
            
            print("\n2. Merging classification data...")
            self.merger.merge_classification_data()
            
            print("\n3. Converting chemical identifiers...")
            self.converter.convert_identifiers()
            
            print("\n4. Aggregating final data...")
            self.aggregator.aggregate_data()
            
            print("\n=== Pipeline completed successfully! ===")
            
        except Exception as e:
            print(f"Pipeline failed with error: {e}")
            raise
    
    def run_step(self, step_number: int):
        """Run a specific step of the pipeline"""
        steps = {
            1: self.classifier.process_classification_files,
            2: self.merger.merge_classification_data,
            3: self.converter.convert_identifiers,
            4: self.aggregator.aggregate_data
        }
        
        if step_number in steps:
            print(f"Running step {step_number}...")
            steps[step_number]()
            print(f"Step {step_number} completed.")
        else:
            print(f"Invalid step number: {step_number}")


# ================== USAGE EXAMPLE ==================
def main():
    """Main function to run the pipeline"""
    # Initialize pipeline with default config
    pipeline = ChemicalAnalysisPipeline()
    
    # Run full pipeline
    pipeline.run_full_pipeline()
    
    # Or run individual steps:
    # pipeline.run_step(1)  # Classification only
    # pipeline.run_step(2)  # Merging only
    # pipeline.run_step(3)  # Conversion only
    # pipeline.run_step(4)  # Aggregation only


if __name__ == "__main__":
    main()