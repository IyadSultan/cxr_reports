import os
import pandas as pd
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_classification_direct():
    """
    Test the classification directly with the OpenAI API
    """
    print("Starting direct classification test...")
    
    # Load a small subset of the data
    try:
        df = pd.read_excel("radiology_cleaned4.xlsx", engine='openpyxl')
        test_sample = df.head(3)  # Just use 3 reports for testing
        
        print(f"Testing with {len(test_sample)} sample reports")
        
        # Test each report
        for idx, row in test_sample.iterrows():
            report_text = row["REPORT"]
            print("\n" + "-"*80)
            print(f"REPORT {idx + 1}:")
            print(report_text[:200] + "..." if len(report_text) > 200 else report_text)
            
            # Classify directly using the API
            prompt = """You are a senior radiologist. Please classify this chest X-ray report to one of the following categories:
            - 0 if you are sure it is normal
            - 1 if you are sure it is abnormal
            - 2 if you are not sure OR if the CXR has a line, catheter, or tube mentioned
            
            Comparison to previous CXR is not sufficient for classification unless it clearly states there are abnormalities or normality.
            Respond with ONLY the number (0, 1, or 2) representing your classification.
            
            Report: """ + report_text
            
            print("\nClassifying report...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a senior radiologist who classifies chest X-ray reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Raw API response: '{result}'")
            
            # Process the result
            if result in ["0", "1", "2"]:
                classification = int(result)
            elif any(digit in result for digit in ["0", "1", "2"]):
                for digit in ["0", "1", "2"]:
                    if digit in result:
                        classification = int(digit)
                        print(f"Extracted {digit} from response")
                        break
            else:
                classification = 2  # Default to uncertain
                print("Invalid response, defaulting to 2")
            
            print(f"\nCLASSIFICATION: {classification}")
            print("0: Normal, 1: Abnormal, 2: Uncertain/Has lines, catheters, tubes")
            
            # Wait between API calls
            time.sleep(1)
            
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")

def test_from_extractor():
    """
    Test using the main script's classify_report function
    """
    from extractor import classify_report
    
    print("Starting test classification using main function...")
    
    try:
        df = pd.read_excel("radiology_cleaned4.xlsx", engine='openpyxl')
        test_sample = df.head(3)  # Just use 3 reports for testing
        
        print(f"Testing with {len(test_sample)} sample reports")
        
        # Test each report
        for idx, row in test_sample.iterrows():
            report_text = row["REPORT"]
            print("\n" + "-"*80)
            print(f"REPORT {idx + 1}:")
            print(report_text[:200] + "..." if len(report_text) > 200 else report_text)
            
            # Classify and print the result
            classification = classify_report(report_text)
            print(f"\nCLASSIFICATION: {classification}")
            print("0: Normal, 1: Abnormal, 2: Uncertain/Has lines, catheters, tubes")
            
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")

if __name__ == "__main__":
    print("=== Testing Direct API Classification ===")
    test_classification_direct()
    
    print("\n\n=== Testing Classification Using Main Function ===")
    test_from_extractor() 