import PyPDF2
import pdfplumber
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
import json

class PolicyPDFParser:
    def __init__(self):
        self.extraction_patterns = {
            'carrier': [
                r'(?i)carrier[:\s]+([^\n\r]+)',
                r'(?i)insurance\s+company[:\s]+([^\n\r]+)',
                r'(?i)underwriter[:\s]+([^\n\r]+)'
            ],
            'policy_number': [
                r'(?i)policy\s+number[:\s]+([^\n\r]+)',
                r'(?i)policy\s+#[:\s]+([^\n\r]+)',
                r'(?i)policy\s+no[:\s]+([^\n\r]+)'
            ],
            'effective_date': [
                r'(?i)effective\s+date[:\s]+([^\n\r]+)',
                r'(?i)inception\s+date[:\s]+([^\n\r]+)',
                r'(?i)start\s+date[:\s]+([^\n\r]+)'
            ],
            'expiration_date': [
                r'(?i)expiration\s+date[:\s]+([^\n\r]+)',
                r'(?i)expiry\s+date[:\s]+([^\n\r]+)',
                r'(?i)end\s+date[:\s]+([^\n\r]+)'
            ],
            'premium': [
                r'(?i)premium[:\s]*\$?([\d,]+\.?\d*)',
                r'(?i)total\s+premium[:\s]*\$?([\d,]+\.?\d*)',
                r'(?i)annual\s+premium[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'deductible': [
                r'(?i)deductible[:\s]*\$?([\d,]+\.?\d*)',
                r'(?i)deductible\s+amount[:\s]*\$?([\d,]+\.?\d*)'
            ],
            'coverage_limits': [
                r'(?i)coverage\s+limit[:\s]*\$?([\d,]+\.?\d*)',
                r'(?i)liability\s+limit[:\s]*\$?([\d,]+\.?\d*)',
                r'(?i)property\s+limit[:\s]*\$?([\d,]+\.?\d*)'
            ]
        }
    
    def parse_policy_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a policy PDF and extract key information
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted policy information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Extract text using both PyPDF2 and pdfplumber for better coverage
        text_pypdf2 = self._extract_text_pypdf2(file_path)
        text_pdfplumber = self._extract_text_pdfplumber(file_path)
        
        # Combine texts, preferring pdfplumber as it's generally more accurate
        combined_text = text_pdfplumber if text_pdfplumber else text_pypdf2
        
        if not combined_text:
            raise ValueError("Could not extract text from PDF")
        
        # Extract structured information
        extracted_data = self._extract_structured_data(combined_text)
        
        # Add metadata
        extracted_data['file_path'] = file_path
        extracted_data['file_size'] = os.path.getsize(file_path)
        extracted_data['extraction_timestamp'] = datetime.now().isoformat()
        extracted_data['raw_text'] = combined_text[:1000]  # Store first 1000 chars for reference
        
        return extracted_data
    
    def _extract_text_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def _extract_text_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            return ""
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from text using regex patterns"""
        extracted_data = {}
        
        for field, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    value = match.group(1).strip()
                    if value:
                        extracted_data[field] = value
                        break
        
        # Try to parse dates
        extracted_data = self._parse_dates(extracted_data)
        
        # Try to parse numeric values
        extracted_data = self._parse_numeric_values(extracted_data)
        
        # Extract coverage information
        extracted_data['coverage_details'] = self._extract_coverage_details(text)
        
        return extracted_data
    
    def _parse_dates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse date strings into standardized format"""
        date_fields = ['effective_date', 'expiration_date']
        
        for field in date_fields:
            if field in data:
                parsed_date = self._parse_date_string(data[field])
                if parsed_date:
                    data[f"{field}_parsed"] = parsed_date.isoformat()
        
        return data
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse various date string formats"""
        # Common date formats
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%m/%d/%y', '%m-%d-%y', '%Y/%m/%d',
            '%B %d, %Y', '%b %d, %Y',
            '%d %B %Y', '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        # Try to extract date using regex if standard formats fail
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if len(match.group(3)) == 2:  # 2-digit year
                        year = int(match.group(3))
                        if year < 50:
                            year += 2000
                        else:
                            year += 1900
                    else:
                        year = int(match.group(3))
                    
                    month = int(match.group(1))
                    day = int(match.group(2))
                    
                    # Handle different date formats
                    if month > 12:  # Day/month swapped
                        month, day = day, month
                    
                    return datetime(year, month, day)
                except ValueError:
                    continue
        
        return None
    
    def _parse_numeric_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse numeric values from strings"""
        numeric_fields = ['premium', 'deductible', 'coverage_limits']
        
        for field in numeric_fields:
            if field in data:
                try:
                    # Remove currency symbols and commas
                    clean_value = re.sub(r'[^\d.]', '', data[field])
                    if clean_value:
                        data[f"{field}_parsed"] = float(clean_value)
                except ValueError:
                    pass
        
        return data
    
    def _extract_coverage_details(self, text: str) -> Dict[str, Any]:
        """Extract detailed coverage information"""
        coverage_info = {}
        
        # Look for coverage types
        coverage_types = [
            'property', 'liability', 'business interruption', 'equipment breakdown',
            'cyber liability', 'directors and officers', 'employment practices',
            'general liability', 'professional liability', 'umbrella'
        ]
        
        for coverage_type in coverage_types:
            pattern = rf'(?i){re.escape(coverage_type)}[:\s]*\$?([\d,]+\.?\d*)'
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(re.sub(r'[^\d.]', '', match.group(1)))
                    coverage_info[coverage_type] = value
                except ValueError:
                    pass
        
        # Look for endorsements/riders
        endorsement_patterns = [
            r'(?i)endorsement[:\s]+([^\n\r]+)',
            r'(?i)rider[:\s]+([^\n\r]+)',
            r'(?i)additional\s+coverage[:\s]+([^\n\r]+)'
        ]
        
        endorsements = []
        for pattern in endorsement_patterns:
            matches = re.findall(pattern, text)
            endorsements.extend([m.strip() for m in matches if m.strip()])
        
        if endorsements:
            coverage_info['endorsements'] = endorsements
        
        # Look for exclusions
        exclusion_patterns = [
            r'(?i)exclusion[:\s]+([^\n\r]+)',
            r'(?i)not\s+covered[:\s]+([^\n\r]+)',
            r'(?i)excluded[:\s]+([^\n\r]+)'
        ]
        
        exclusions = []
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, text)
            exclusions.extend([m.strip() for m in matches if m.strip()])
        
        if exclusions:
            coverage_info['exclusions'] = exclusions
        
        return coverage_info
    
    def validate_extraction(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and score the quality of extracted data"""
        validation_result = {
            'is_valid': True,
            'confidence_score': 0.0,
            'missing_fields': [],
            'warnings': []
        }
        
        required_fields = ['carrier', 'policy_number']
        optional_fields = ['effective_date', 'expiration_date', 'premium']
        
        # Check required fields
        for field in required_fields:
            if field not in extracted_data or not extracted_data[field]:
                validation_result['missing_fields'].append(field)
                validation_result['is_valid'] = False
        
        # Calculate confidence score
        total_fields = len(required_fields) + len(optional_fields)
        found_fields = 0
        
        for field in required_fields + optional_fields:
            if field in extracted_data and extracted_data[field]:
                found_fields += 1
        
        validation_result['confidence_score'] = found_fields / total_fields
        
        # Add warnings for low confidence
        if validation_result['confidence_score'] < 0.5:
            validation_result['warnings'].append("Low confidence extraction - manual review recommended")
        
        return validation_result
