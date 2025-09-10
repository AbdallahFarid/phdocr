"""
Cheque OCR System - Streamlit Web Interface

This module provides a user-friendly web interface for the Cheque OCR system
using Streamlit. Users can upload cheque images and view extracted information.
"""

import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import cv2
import sys
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import cheque OCR components
from src.cheque_ocr.utils.config_manager import ConfigManager


class ChequeOCRApp:
    """Streamlit app for Cheque OCR system."""
    
    def __init__(self):
        """Initialize the Cheque OCR app components."""
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from default config file."""
        config_path = Path(__file__).parent / "config"
        if not config_path.exists():
            # Create default config if it doesn't exist
            self._create_default_config(config_path / "default.ini")
        
        config_manager = ConfigManager(config_path)
        try:
            return config_manager.load_config("default")
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return config_manager.get_default_config()
    
    def _create_default_config(self, config_path):
        """Create default configuration file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write("""[ocr_settings]
use_gpu = false
language = en
model_version = PP-OCRv3
use_doc_orientation_classify = false
use_doc_unwarping = false
use_textline_orientation = false

[processing]
max_image_size = 10485760
min_confidence = 0.3
batch_size = 10
parallel_processing = false

[output]
csv_encoding = utf-8
include_confidence = true
date_format = %Y-%m-%d
include_headers = true

[logging]
level = INFO
console_output = true
log_file = logs/cheque_ocr.log
""")
    
    def process_image(self, image):
        """Process a single image and extract cheque information."""
        try:
            # Convert to OpenCV format if needed
            if isinstance(image, Image.Image):
                image_np = np.array(image)
                # Convert RGB to BGR for OpenCV
                image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            else:
                image_cv = image
            
            # Debug: Print image info
            print(f"Image shape: {image_cv.shape}")
            print(f"Image dtype: {image_cv.dtype}")
            print(f"Image min/max values: {image_cv.min()}/{image_cv.max()}")
            
            # Initialize OCR with minimal settings
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(lang='en')
            
            # Try the traditional ocr method first
            try:
                print("Trying traditional OCR method...")
                results = ocr.ocr(image_cv)
                print(f"OCR results: {results}")
                
                if results and len(results) > 0:
                    result = results[0]  # Get first result
                    ocr_results = []
                    
                    # Extract from PaddleOCR 3.x format
                    if 'rec_texts' in result and 'rec_scores' in result and 'rec_polys' in result:
                        rec_texts = result['rec_texts']
                        rec_scores = result['rec_scores']
                        rec_polys = result['rec_polys']
                        
                        for text, confidence, poly in zip(rec_texts, rec_scores, rec_polys):
                            if text and text.strip():
                                print(f"Found text: '{text}' with confidence: {confidence}")
                                
                                # Convert polygon to bbox format
                                bbox = [
                                    [float(poly[0][0]), float(poly[0][1])],  # top-left
                                    [float(poly[1][0]), float(poly[1][1])],  # top-right
                                    [float(poly[2][0]), float(poly[2][1])],  # bottom-right
                                    [float(poly[3][0]), float(poly[3][1])]   # bottom-left
                                ]
                                
                                ocr_results.append({
                                    'text': text.strip(),
                                    'confidence': float(confidence),
                                    'bbox': bbox,
                                    'center_x': float((bbox[0][0] + bbox[2][0]) / 2),
                                    'center_y': float((bbox[0][1] + bbox[2][1]) / 2),
                                    'width': float(bbox[2][0] - bbox[0][0]),
                                    'height': float(bbox[2][1] - bbox[0][1])
                                })
                    
                    if ocr_results:
                        # Implement intelligent field extraction
                        extracted_fields = self._extract_cheque_fields(ocr_results)
                        return extracted_fields, None
                    else:
                        return None, "OCR returned results but no valid text found."
                else:
                    return None, f"OCR returned empty results: {results}"
                    
            except Exception as ocr_error:
                print(f"OCR error: {ocr_error}")
                return None, f"OCR processing failed: {str(ocr_error)}"
            
        except Exception as e:
            print(f"General error: {e}")
            return None, f"Error processing image: {str(e)}"
    
    def _extract_cheque_fields(self, ocr_results):
        """Extract cheque fields using direct pattern matching (primary) with LLM fallback."""
        # Use direct pattern matching as primary method since it's more reliable
        fields = self._direct_pattern_extraction(ocr_results)
        
        # If direct pattern matching found all fields, return immediately
        if (fields['payee_name']['text'] and 
            fields['amount_numerical']['text'] and 
            fields['date']['text']):
            print("Direct pattern extraction successful - all fields found")
            return fields
        
        # Otherwise try LLM as fallback for missing fields
        print("Some fields missing, trying LLM extraction as fallback")
        try:
            from src.cheque_ocr.core.llm_extractor import LLMFieldExtractor
            llm_extractor = LLMFieldExtractor()
            llm_fields = llm_extractor.extract_fields(ocr_results)
            
            # Fill in missing fields from LLM
            for field in ['payee_name', 'amount_numerical', 'date']:
                if not fields[field]['text'] and llm_fields[field]['text']:
                    fields[field] = llm_fields[field]
                    print(f"LLM filled missing field: {field}")
            
            return fields
        except Exception as e:
            print(f"LLM fallback failed: {e}")
            return fields
    
    def _direct_pattern_extraction(self, ocr_results):
        """Extract cheque fields using direct pattern matching on exact OCR output."""
        import re
        
        # Initialize extracted fields
        fields = {
            'payee_name': {'text': '', 'confidence': 0.0},
            'amount_numerical': {'text': '', 'confidence': 0.0},
            'amount_written': {'text': '', 'confidence': 0.0},
            'date': {'text': '', 'confidence': 0.0},
            'raw_ocr_results': ocr_results
        }
        
        for result in ocr_results:
            text = result['text'].strip()
            confidence = result['confidence']
            
            print(f"Processing: '{text}' with confidence: {confidence}")
            
            # Extract payee name from pattern
            payee_match = re.search(r'\*\*([^*]+)\*\*', text)
            if payee_match and 'AGAINST' in text.upper():
                payee_name = payee_match.group(1).strip()
                # Verify it's a proper name (not a number)
                if not re.search(r'[\d,]+', payee_name):
                    fields['payee_name'] = {'text': payee_name, 'confidence': confidence}
                    print(f"Found payee: {payee_name}")
            
            # Extract amount from pattern
            amount_match = re.search(r'\*\*([\d,]+\.?\d*)\*\*', text)
            if amount_match:
                amount = amount_match.group(1).strip()
                # Verify it's a number with commas/decimals
                if re.search(r'[\d,]+', amount):
                    fields['amount_numerical'] = {'text': amount, 'confidence': confidence}
                    print(f"Found amount: {amount}")
            
            # Extract date from pattern
            date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
            if date_match:
                date_text = date_match.group().strip()
                if confidence > fields['date']['confidence']:
                    fields['date'] = {'text': date_text, 'confidence': confidence}
                    print(f"Found date: {date_text}")
            
            # Extract written amount (look for text with number words)
            number_words = ['million', 'thousand', 'hundred', 'only', 'dollars', 'pounds']
            if any(word in text.lower() for word in number_words) and len(text) > 15:
                if confidence > fields['amount_written']['confidence']:
                    clean_text = text.replace('*', '').strip()
                    fields['amount_written'] = {'text': clean_text, 'confidence': confidence}
                    print(f"Found written amount: {clean_text}")
        
        return fields
    
    
    def run(self):
        """Run the Streamlit app."""
        st.set_page_config(
            page_title="Cheque OCR System",
            layout="wide"
        )
        
        st.title("Cheque OCR System")
        st.markdown("""
        Upload an image of a cheque to extract structured information including:
        - Payee name
        - Amount
        - Date
        """)
        
        # Sidebar options
        st.sidebar.title("Settings")
        enable_preprocessing = st.sidebar.checkbox("Enable image preprocessing", value=True)
        show_confidence = st.sidebar.checkbox("Show confidence scores", value=True)
        show_extraction_methods = st.sidebar.checkbox("Show extraction methods", value=False)
        
        # File uploader
        uploaded_file = st.file_uploader("Upload a cheque image", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Display the uploaded image
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Uploaded Image")
                st.image(image, use_container_width=True)
            
            # Process the image
            with st.spinner("Processing image..."):
                # Save image to temp file for processing
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                    temp_path = temp_file.name
                    image.save(temp_path)
                    
                    # Process the image
                    if enable_preprocessing:
                        # Read with OpenCV for preprocessing
                        img_cv = cv2.imread(temp_path)
                        cheque_data, error = self.process_image(img_cv)
                    else:
                        cheque_data, error = self.process_image(image)
                
                # Remove temp file
                os.unlink(temp_path)
            
            # Display results
            with col2:
                st.subheader("Extracted Information")
                
                if error:
                    st.error(error)
                elif cheque_data:
                    # Create a clean display of the extracted data
                    data_dict = {
                        "Field": ["Payee Name", "Amount", "Date"],
                        "Value": [
                            cheque_data.get('payee_name', {}).get('text', 'Not detected'),
                            cheque_data.get('amount_numerical', {}).get('text', 'Not detected'),
                            cheque_data.get('date', {}).get('text', 'Not detected')
                        ]
                    }
                    
                    # Add confidence scores if requested
                    if show_confidence:
                        confidences = []
                        for field in ["payee_name", "amount_numerical", "date"]:
                            if field in cheque_data and 'confidence' in cheque_data[field]:
                                conf = f"{cheque_data[field]['confidence']:.2f}"
                                confidences.append(conf)
                            else:
                                confidences.append("N/A")
                        data_dict["Confidence"] = confidences
                    
                    # Add extraction methods if requested
                    if show_extraction_methods:
                        methods = ["Pattern Recognition", "Pattern Recognition", "Pattern Recognition"]
                        data_dict["Method"] = methods
                    
                    # Display as a table
                    df = pd.DataFrame(data_dict)
                    st.table(df)
                                
                    
                    # Show raw OCR results if requested
                    if show_extraction_methods and 'raw_ocr_results' in cheque_data:
                        with st.expander("Raw OCR Results"):
                            for i, result in enumerate(cheque_data['raw_ocr_results'][:10]):  # Show first 10
                                st.write(f"{i+1}. '{result['text']}' (confidence: {result['confidence']:.3f})")
                    
                    # Add download button for CSV
                    csv_data = self._generate_csv(cheque_data)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="cheque_data.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("Could not extract information from the image.")
        
        # Add batch processing option
        st.markdown("---")
        st.subheader("Batch Processing")
        st.markdown("Upload multiple cheque images for batch processing.")
        
        uploaded_files = st.file_uploader("Upload multiple cheque images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if uploaded_files:
            st.write(f"Uploaded {len(uploaded_files)} images for batch processing")
            
            if st.button("Process Batch"):
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Create container for results
                batch_results = []
                
                # Process each image
                for i, uploaded_file in enumerate(uploaded_files):
                    # Update progress
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing image {i+1} of {len(uploaded_files)}")
                    
                    # Process image
                    try:
                        image = Image.open(uploaded_file)
                        
                        # Save image to temp file for processing
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                            temp_path = temp_file.name
                            image.save(temp_path)
                            
                            # Process the image
                            if enable_preprocessing:
                                # Read with OpenCV for preprocessing
                                img_cv = cv2.imread(temp_path)
                                cheque_data, error = self.process_image(img_cv)
                            else:
                                cheque_data, error = self.process_image(image)
                        
                        # Remove temp file
                        os.unlink(temp_path)
                        
                        # Add to results
                        if error:
                            batch_results.append({
                                "filename": uploaded_file.name,
                                "success": False,
                                "error": error,
                                "data": None
                            })
                        else:
                            batch_results.append({
                                "filename": uploaded_file.name,
                                "success": True,
                                "error": None,
                                "data": cheque_data
                            })
                    
                    except Exception as e:
                        batch_results.append({
                            "filename": uploaded_file.name,
                            "success": False,
                            "error": str(e),
                            "data": None
                        })
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.text("Processing complete!")
                
                # Display batch results
                st.subheader("Batch Processing Results")
                
                # Create summary
                successful = sum(1 for r in batch_results if r["success"])
                st.write(f"Successfully processed {successful} out of {len(batch_results)} images")
                
                # Create dataframe for results
                data = []
                for result in batch_results:
                    if result["success"]:
                        cheque_data = result["data"]
                        overall_conf = np.mean([
                            cheque_data.get('payee_name', {}).get('confidence', 0.0),
                            cheque_data.get('amount_numerical', {}).get('confidence', 0.0),
                            cheque_data.get('date', {}).get('confidence', 0.0)
                        ])
                        data.append({
                            "Filename": result["filename"],
                            "Status": "Success",
                            "Payee": cheque_data.get('payee_name', {}).get('text', "Not detected"),
                            "Amount": cheque_data.get('amount_numerical', {}).get('text', "Not detected"),
                            "Date": cheque_data.get('date', {}).get('text', "Not detected"),
                            "Confidence": f"{overall_conf:.2f}"
                        })
                    else:
                        data.append({
                            "Filename": result["filename"],
                            "Status": "Failed",
                            "Payee": "-",
                            "Amount": "-",
                            "Date": "-",
                            "Confidence": "-",
                            "Error": result["error"]
                        })
                
                # Display as table
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                    
                    # Add download button for batch CSV
                    csv_data = self._generate_batch_csv(batch_results)
                    st.download_button(
                        label="Download Batch Results CSV",
                        data=csv_data,
                        file_name="batch_cheque_data.csv",
                        mime="text/csv",
                    )
        
        # Footer
        st.markdown("---")
        st.markdown("Cheque OCR System v2.0.0 | Powered by PaddleOCR")
    
    def _generate_csv(self, cheque_data):
        """Generate CSV data from cheque data."""
        data = {
            "Field": ["Payee Name", "Amount", "Date"],
            "Value": [
                cheque_data.get('payee_name', {}).get('text', ''),
                cheque_data.get('amount_numerical', {}).get('text', ''),
                cheque_data.get('date', {}).get('text', '')
            ],
            "Confidence": [
                cheque_data.get('payee_name', {}).get('confidence', 0.0),
                cheque_data.get('amount_numerical', {}).get('confidence', 0.0),
                cheque_data.get('date', {}).get('confidence', 0.0)
            ]
        }
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)
    
    def _generate_batch_csv(self, batch_results):
        """Generate CSV data from batch processing results."""
        data = []
        
        for result in batch_results:
            if result["success"]:
                cheque_data = result["data"]
                overall_conf = np.mean([
                    cheque_data.get('payee_name', {}).get('confidence', 0.0),
                    cheque_data.get('amount_numerical', {}).get('confidence', 0.0),
                    cheque_data.get('date', {}).get('confidence', 0.0)
                ])
                data.append({
                    "Filename": result["filename"],
                    "Status": "Success",
                    "Payee": cheque_data.get('payee_name', {}).get('text', ''),
                    "Amount": cheque_data.get('amount_numerical', {}).get('text', ''),
                    "Date": cheque_data.get('date', {}).get('text', ''),
                    "Confidence": f"{overall_conf:.2f}"
                })
            else:
                data.append({
                    "Filename": result["filename"],
                    "Status": "Failed",
                    "Error": result["error"],
                    "Payee": "",
                    "Amount": "",
                    "Date": "",
                    "Confidence": ""
                })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)


if __name__ == "__main__":
    app = ChequeOCRApp()
    app.run()
