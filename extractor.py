import os
import pandas as pd
import time
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='extractor_log.log',
    filemode='a'
)
logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_report(report_text):
    """
    Use OpenAI to classify radiology reports as:
    0 - Normal
    1 - Abnormal
    2 - Uncertain/Has lines, catheters, tubes
    """
    prompt = """You are a senior radiologist. Please classify this chest X-ray report to one of the following categories:
    - 0 if you are sure it is normal
    - 1 if you are sure it is abnormal
    - 2 if you are not sure OR if the CXR has a line, catheter, or tube mentioned
    
    Comparison to previous CXR is not sufficient for classification unless it clearly states there are abnormalities or normality.
    err on the side of caution and classify as 2 if you are not sure.
    0 if you are sure it is normal with clear chest, no lines, catheters, or tubes, no masses or infiltrates.
    1 if you are sure it is abnormal with radiographic evidence of pneumonia, fluid overload, cardiomegaly, etc.
    suspicious findings are not enough to classify as 1.
    Disease in other parts of the body are not enough to classify as 1.
    
    Respond with ONLY the number (0, 1, or 2) representing your classification.
    
    Report: """
    
    # Retry mechanism for API calls
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Add rate limiting to avoid hitting API limits
            time.sleep(1)  # Increased sleep time to reduce API pressure
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Switch to gpt-3.5-turbo which is more reliable
                messages=[
                    {"role": "system", "content": "You are a senior radiologist who classifies chest X-ray reports."},
                    {"role": "user", "content": prompt + report_text}
                ],
                temperature=0.2,  # Slightly increased for more reliable responses
                max_tokens=10     # Using max_tokens which works with gpt-3.5-turbo
            )
            
            # Extract just the classification number
            result = response.choices[0].message.content.strip()
            logger.info(f"Raw API response: '{result}'")
            
            # Ensure we get a valid classification (0, 1, or 2)
            if result in ["0", "1", "2"]:
                return int(result)
            # Try to extract a digit if there's more text
            elif any(digit in result for digit in ["0", "1", "2"]):
                for digit in ["0", "1", "2"]:
                    if digit in result:
                        logger.warning(f"Extracted {digit} from response: '{result}'")
                        return int(digit)
                        
            # If we get here, no valid classification found
            logger.warning(f"Invalid classification received: '{result}'. Retrying...")
            retry_count += 1
                
        except Exception as e:
            logger.error(f"Error classifying report (attempt {retry_count+1}/{max_retries}): {str(e)}")
            retry_count += 1
            time.sleep(2)  # Wait longer between retries
    
    # If we've exhausted all retries, default to 2
    logger.error("All classification attempts failed. Defaulting to 2.")
    return 2
        
def main():
    try:
        # Load the Excel file
        logger.info("Loading Excel file...")
        file_path = "radiology_cleaned4.xlsx"
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Check if column already exists
        if "normal_0_abnormal_1_others_2" in df.columns:
            logger.info("Classification column already exists. Continuing with unclassified reports...")
        else:
            # Create new column with default value of None
            df["normal_0_abnormal_1_others_2"] = None
        
        # Count total reports to process
        total_reports = df.shape[0]
        reports_to_process = df[df["normal_0_abnormal_1_others_2"].isna()].shape[0]
        
        logger.info(f"Total reports: {total_reports}, Reports to process: {reports_to_process}")
        
        # Process each unclassified report
        count = 0
        for idx, row in df.iterrows():
            if pd.isna(df.at[idx, "normal_0_abnormal_1_others_2"]):
                report_text = row["REPORT"]
                if pd.isna(report_text) or not report_text.strip():
                    df.at[idx, "normal_0_abnormal_1_others_2"] = 2  # Mark empty reports as uncertain
                    continue
                    
                # Classify report
                try:
                    classification = classify_report(report_text)
                    df.at[idx, "normal_0_abnormal_1_others_2"] = classification
                    logger.info(f"Report {idx} classified as {classification}")
                except Exception as e:
                    logger.error(f"Failed to classify report {idx}: {str(e)}")
                    df.at[idx, "normal_0_abnormal_1_others_2"] = 2  # Default to uncertain
                
                # Save progress periodically
                count += 1
                if count % 5 == 0:  # Save more frequently
                    logger.info(f"Processed {count}/{reports_to_process} reports. Saving...")
                    df.to_excel("radiology_classified.xlsx", index=False, engine='openpyxl')
        
        # Save final result
        logger.info("Saving final results...")
        df.to_excel("radiology_classified.xlsx", index=False, engine='openpyxl')
        logger.info("Classification complete!")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        
if __name__ == "__main__":
    main()
