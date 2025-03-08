import pandas as pd
import requests
import re
import time
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def classify_liver_metastasis(report):
    """
    Function to classify reports for liver metastasis using OpenAI API
    
    Args:
        report (str): The radiology report text
        api_key (str): OpenAI API key
        
    Returns:
        dict: Dictionary containing classification, explanation, and lesion count
    """
    # Create the system prompt
    system_prompt = "You are a radiologist specialized in cancer mets detection, classify these radiology reports as 0 if there is no liver metastasis, 1 if there is liver metastasis and 2 if not sure. In column 2 explain why this is your choice (e.g. The report does not mention liver lesions) and in column 3 the number of liver lesions you identified which you can leave blank if you are not sure)"
    
    # Prepare the API request body
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this radiology report: {report}"}
        ],
        "temperature": 0,
        "max_tokens": 200
    }
    
    # Make the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(
            url="https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body
        )
        
        # Parse the response
        if response.status_code == 200:
            content = response.json()
            result_text = content['choices'][0]['message']['content']
            
            # Extract classification, explanation, and lesion count from the response
            classification = None
            explanation = None
            lesion_count = None
            
            # Try to extract the classification (0, 1, or 2)
            class_match = re.search(r'\b[012]\b', result_text)
            if class_match:
                classification = int(class_match.group())
            
            # Extract explanation (everything after classification until any mention of lesion count)
            explanation_match = re.search(r'(?<=\b[012]\b).*?(?=(lesion|metastasis|count|number))', result_text, re.DOTALL)
            if explanation_match:
                explanation = explanation_match.group().strip()
            else:
                # If the regex didn't work, just take everything after the classification
                explanation = re.sub(r'^\b[012]\b', '', result_text).strip()
            
            # Try to extract lesion count
            count_match = re.search(r'\b(\d+)\b(?=\s+lesion)', result_text)
            if count_match:
                lesion_count = int(count_match.group(1))
            
            return {
                "classification": classification,
                "explanation": explanation,
                "lesion_count": lesion_count
            }
        else:
            print(f"API request failed with status code: {response.status_code}")
            return {
                "classification": "API Error",
                "explanation": f"API Error: {response.status_code}",
                "lesion_count": None
            }
    except Exception as e:
        print(f"Error during API request: {str(e)}")
        return {
            "classification": "API Error",
            "explanation": f"API Error: {str(e)}",
            "lesion_count": None
        }

def process_liver_metastasis(df, output_file,  batch_size=10):
    """
    Main function to process the dataframe for liver metastasis classification
    
    Args:
        df (pandas.DataFrame): DataFrame containing radiology reports
        output_file (str): Path to the output CSV file
        api_key (str): OpenAI API key
        batch_size (int): Number of reports to process in each batch
        
    Returns:
        pandas.DataFrame: Processed DataFrame with classification results
    """
    # Check if the report column exists
    if "report" not in df.columns:
        raise ValueError("Error: 'report' column not found in the dataframe")
    
    # Create a copy of the dataframe to avoid modifying the original
    dataset = df.copy()
    
    # Create new columns for classification, explanation, and lesion count
    dataset['liver_met_classification'] = None
    dataset['liver_met_explanation'] = None
    dataset['liver_lesion_count'] = None
    
    # Process in batches to avoid rate limiting
    total_rows = len(dataset)
    num_batches = (total_rows + batch_size - 1) // batch_size  # Ceiling division
    
    print(f"Processing {total_rows} reports in {num_batches} batches...")
    
    for batch_num in range(1, num_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(batch_num * batch_size, total_rows)
        
        print(f"Processing batch {batch_num} of {num_batches} (rows {start_idx + 1} to {end_idx})...")
        
        for i in range(start_idx, end_idx):
            report_text = dataset.loc[i, 'report']
            
            # Skip empty reports
            if pd.isna(report_text) or report_text == "":
                dataset.loc[i, 'liver_met_classification'] = 2  # Not sure
                dataset.loc[i, 'liver_met_explanation'] = "No report text available"
                dataset.loc[i, 'liver_lesion_count'] = None
                continue
            
            # Call the API to classify the report
            print(f"  Classifying report {i + 1} of {total_rows}...")
            result = classify_liver_metastasis(report_text)
            
            # Store the results
            dataset.loc[i, 'liver_met_classification'] = result['classification']
            dataset.loc[i, 'liver_met_explanation'] = result['explanation']
            dataset.loc[i, 'liver_lesion_count'] = result['lesion_count']
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)
        
        # Save the progress after each batch
        dataset.to_csv(output_file, index=False)
        print(f"Progress saved to {output_file}")
        
        # If not the last batch, add a longer delay between batches
        if batch_num < num_batches:
            print("Waiting 5 seconds before the next batch...")
            time.sleep(5)
    
    # Generate summary statistics
    summary = dataset['liver_met_classification'].value_counts().reset_index()
    summary.columns = ['liver_met_classification', 'count']
    
    # Add labels and percentages
    summary['label'] = summary['liver_met_classification'].map({
        0: "No liver metastasis",
        1: "Liver metastasis present", 
        2: "Uncertain"
    }).fillna("Error/NA")
    
    summary['percentage'] = summary['count'] / summary['count'].sum() * 100
    
    print("\nClassification Summary:")
    print(summary)
    
    # Save the final results
    dataset.to_csv(output_file, index=False)
    print(f"\nProcessing complete. Results saved to {output_file}")
    
    return dataset

# Main execution
if __name__ == "__main__":
    # Set your OpenAI API key (better to get from environment variable)
    
    
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
    
    # Load the data
    input_file = "data/liver_scans.csv"
    output_file = "data/liver_scans_results.csv"
    
    try:
        # Read the CSV file
        data = pd.read_csv(input_file)
        print(f"Loaded {len(data)} records from {input_file}")
        
        # Process the data
        results = process_liver_metastasis(data, output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")