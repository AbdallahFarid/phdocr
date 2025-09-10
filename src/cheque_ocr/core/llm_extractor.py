"""
LLM-based field extraction for cheque OCR.
Uses Replicate API with Llama-3-8B for intelligent field extraction.
"""

import json
import os
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMFieldExtractor:
    """Extract cheque fields using Replicate LLM API."""
    
    def __init__(self, api_token: str = None):
        """Initialize LLM extractor.
        
        Args:
            api_token: Replicate API token (defaults to env variable)
        """
        # Load API token from argument or environment
        self.api_token = api_token or os.getenv('REPLICATE_API_TOKEN')
        self.model_name = "meta/meta-llama-3-70b-instruct"
        self.logger = logging.getLogger(__name__)
        
        if not self.api_token:
            self.logger.warning("No Replicate API token found. Set REPLICATE_API_TOKEN environment variable.")
        
    def is_server_available(self) -> bool:
        """Check if Replicate API is available."""
        return bool(self.api_token)
    
    def extract_fields(self, ocr_results: List[Dict]) -> Dict[str, Any]:
        """Extract cheque fields using LLM.
        
        Args:
            ocr_results: List of OCR results with text, confidence, and bbox
            
        Returns:
            Dictionary with extracted fields
        """
        if not self.is_server_available():
            self.logger.warning("Replicate API not available, falling back to spatial extraction")
            return self._fallback_extraction(ocr_results)
        
        # Prepare OCR text for LLM
        ocr_text = self._format_ocr_for_llm(ocr_results)
        
        # Create prompt
        prompt = self._create_extraction_prompt(ocr_text)
        
        try:
            # Call Replicate API
            response = self._call_replicate_api(prompt)
            
            # Parse LLM response
            extracted_fields = self._parse_llm_response(response)
            
            # Add raw OCR results
            extracted_fields['raw_ocr_results'] = ocr_results
            
            return extracted_fields
            
        except Exception as e:
            self.logger.error(f"Replicate API extraction failed: {e}")
            return self._fallback_extraction(ocr_results)
    
    def _format_ocr_for_llm(self, ocr_results: List[Dict]) -> str:
        """Format OCR results for LLM processing."""
        formatted_lines = []
        
        for i, result in enumerate(ocr_results):
            text = result['text'].strip()
            confidence = result['confidence']
            
            # Skip very low confidence or empty text
            if confidence < 0.3 or len(text) < 2:
                continue
                
            # Add position info for context
            center_x = result.get('center_x', 0)
            center_y = result.get('center_y', 0)
            
            formatted_lines.append(f"[{i+1}] '{text}' (conf: {confidence:.2f}, pos: {center_x:.0f},{center_y:.0f})")
        
        return "\n".join(formatted_lines)
    
    def _create_extraction_prompt(self, ocr_text: str) -> str:
        """Create extraction prompt for LLM."""
        return f"""You are an expert at extracting information from bank cheques. Below is the OCR text extracted from a cheque image, with confidence scores and approximate positions.

OCR Results:
{ocr_text}

Please extract the following fields from this cheque:
1. PAYEE_NAME: The name of the person/entity receiving the payment
2. AMOUNT_NUMERICAL: The numerical amount (e.g., 12,345,678.00)
3. DATE: The date on the cheque (format: DD-MM-YYYY or similar)

Important guidelines:
- Look for proper names (capitalized words, typically 2-3 words) for PAYEE_NAME
- Avoid extracting written amounts in words as PAYEE_NAME
- For AMOUNT_NUMERICAL, look for large numbers with commas or decimal points
- Ignore words like "CURRENCY", "PAY", "DATE", "BANK" as payee names
- If a field cannot be found, return empty string

Respond ONLY with a JSON object in this exact format:
{{"payee_name": "extracted name or empty", "amount_numerical": "extracted amount or empty", "date": "extracted date or empty"}}"""

    def _call_replicate_api(self, prompt: str) -> str:
        """Call the Replicate API."""
        import replicate
        
        # Set API token
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        input_data = {
            "prompt": prompt,
            "temperature": 0.1,
            "max_tokens": 200,
            "top_p": 0.9
        }
        
        # Run the model
        output = replicate.run(
            self.model_name,
            input=input_data
        )
        
        # Join the output if it's a generator/list
        if hasattr(output, '__iter__') and not isinstance(output, str):
            return "".join(output)
        else:
            return str(output)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured fields."""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Structure the response
            fields = {
                'payee_name': {
                    'text': parsed.get('payee_name', ''),
                    'confidence': 0.9  # High confidence for LLM extraction
                },
                'amount_numerical': {
                    'text': parsed.get('amount_numerical', ''),
                    'confidence': 0.9
                },
                'date': {
                    'text': parsed.get('date', ''),
                    'confidence': 0.9
                },
                'amount_written': {
                    'text': '',  # LLM doesn't extract written amount for now
                    'confidence': 0.0
                }
            }
            
            return fields
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            raise
    
    def _fallback_extraction(self, ocr_results: List[Dict]) -> Dict[str, Any]:
        """Fallback extraction when LLM is not available."""
        import re
        
        fields = {
            'payee_name': {'text': '', 'confidence': 0.0},
            'amount_numerical': {'text': '', 'confidence': 0.0},
            'amount_written': {'text': '', 'confidence': 0.0},
            'date': {'text': '', 'confidence': 0.0},
            'raw_ocr_results': ocr_results
        }
        
        # Simple fallback logic
        for result in ocr_results:
            text = result['text'].strip()
            confidence = result['confidence']
            
            # Date extraction
            if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
                if confidence > fields['date']['confidence']:
                    fields['date'] = {'text': text, 'confidence': confidence}
            
            # Amount extraction (look for numbers with 4+ digits)
            if re.search(r'\d{4,}', text) and confidence > 0.7:
                number_match = re.search(r'[\d,]+\.?\d*', text)
                if number_match and confidence > fields['amount_numerical']['confidence']:
                    fields['amount_numerical'] = {
                        'text': number_match.group(),
                        'confidence': confidence
                    }
            
            # Name extraction (proper names)
            words = text.split()
            if (len(words) >= 2 and len(words) <= 4 and
                all(word[0].isupper() and len(word) > 1 for word in words if word.isalpha()) and
                not any(char.isdigit() for char in text) and
                not any(word.lower() in ['pay', 'date', 'bank', 'currency'] for word in words)):
                
                if confidence > fields['payee_name']['confidence']:
                    fields['payee_name'] = {'text': text, 'confidence': confidence}
        
        return fields
