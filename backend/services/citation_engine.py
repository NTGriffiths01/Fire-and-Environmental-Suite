"""
Comprehensive Citation Suggestion Engine for Fire and Environmental Safety
Supports ICC Fire Code, ACA Standards, and 105 CMR 451 regulations
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class CitationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CitationCategory(str, Enum):
    FIRE_DETECTION = "fire_detection"
    FIRE_SUPPRESSION = "fire_suppression"
    EMERGENCY_EGRESS = "emergency_egress"
    ELECTRICAL_SAFETY = "electrical_safety"
    HAZARDOUS_MATERIALS = "hazardous_materials"
    ENVIRONMENTAL = "environmental"
    STRUCTURAL = "structural"
    LIFE_SAFETY = "life_safety"

class CitationDatabase:
    """Comprehensive database of fire and environmental safety citations"""
    
    def __init__(self):
        self.citations = self._load_citations()
        self.keywords = self._build_keyword_index()
    
    def _load_citations(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive citation database"""
        return {
            # ICC Fire Code Citations
            "ICC-FC-901": {
                "title": "General Fire Protection Systems",
                "description": "Requirements for fire protection systems in correctional facilities",
                "category": CitationCategory.FIRE_SUPPRESSION,
                "severity": CitationSeverity.HIGH,
                "keywords": ["fire protection", "suppression", "system", "sprinkler", "general"],
                "regulation": "ICC Fire Code Section 901",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Fire protection systems shall be maintained in accordance with referenced standards",
                    "Systems shall be inspected monthly by qualified personnel",
                    "Annual testing required by certified technicians"
                ]
            },
            "ICC-FC-903": {
                "title": "Automatic Sprinkler Systems",
                "description": "Installation, maintenance, and testing of automatic sprinkler systems",
                "category": CitationCategory.FIRE_SUPPRESSION,
                "severity": CitationSeverity.CRITICAL,
                "keywords": ["sprinkler", "automatic", "water", "heads", "pipes", "pressure"],
                "regulation": "ICC Fire Code Section 903",
                "applicability": "All buildings except single-story non-residential",
                "requirements": [
                    "Automatic sprinkler systems required throughout facility",
                    "Monthly inspection of sprinkler heads and piping",
                    "Annual flow testing required",
                    "Quarterly inspection of fire department connections"
                ]
            },
            "ICC-FC-907": {
                "title": "Fire Alarm and Detection Systems",
                "description": "Fire alarm systems, smoke detectors, and notification appliances",
                "category": CitationCategory.FIRE_DETECTION,
                "severity": CitationSeverity.CRITICAL,
                "keywords": ["fire alarm", "smoke detector", "detection", "notification", "panel", "horn", "strobe"],
                "regulation": "ICC Fire Code Section 907",
                "applicability": "All occupancies as specified",
                "requirements": [
                    "Fire alarm systems required in all areas",
                    "Smoke detection in sleeping areas",
                    "Manual pull stations at exits",
                    "Audible and visual notification devices"
                ]
            },
            "ICC-FC-1030": {
                "title": "Means of Egress",
                "description": "Emergency exits, exit signs, and egress lighting",
                "category": CitationCategory.EMERGENCY_EGRESS,
                "severity": CitationSeverity.HIGH,
                "keywords": ["exit", "egress", "evacuation", "door", "corridor", "stairway", "lighting"],
                "regulation": "ICC Fire Code Section 1030",
                "applicability": "All buildings and structures",
                "requirements": [
                    "Exit access shall be maintained free of obstructions",
                    "Exit signs shall be illuminated and visible",
                    "Emergency lighting systems required",
                    "Doors shall swing in direction of egress travel"
                ]
            },
            "ICC-FC-605": {
                "title": "Electrical Systems",
                "description": "Electrical installations and fire safety requirements",
                "category": CitationCategory.ELECTRICAL_SAFETY,
                "severity": CitationSeverity.MEDIUM,
                "keywords": ["electrical", "wiring", "panel", "circuit", "breaker", "grounding", "outlet"],
                "regulation": "ICC Fire Code Section 605",
                "applicability": "All electrical installations",
                "requirements": [
                    "Electrical equipment shall be listed and approved",
                    "Electrical panels shall be accessible and labeled",
                    "Grounding and bonding as required",
                    "Arc-fault circuit interrupters where required"
                ]
            },
            "ICC-FC-5003": {
                "title": "General Hazardous Materials Requirements",
                "description": "Storage, handling, and use of hazardous materials",
                "category": CitationCategory.HAZARDOUS_MATERIALS,
                "severity": CitationSeverity.HIGH,
                "keywords": ["hazardous", "chemical", "storage", "flammable", "toxic", "corrosive"],
                "regulation": "ICC Fire Code Section 5003",
                "applicability": "All facilities using hazardous materials",
                "requirements": [
                    "Hazardous materials shall be stored per requirements",
                    "Secondary containment for liquid hazardous materials",
                    "Ventilation systems for hazardous material storage",
                    "Emergency response procedures posted"
                ]
            },
            
            # ACA Standards Citations
            "ACA-4-4210": {
                "title": "Fire Safety and Emergency Procedures",
                "description": "Comprehensive fire safety program for correctional facilities",
                "category": CitationCategory.LIFE_SAFETY,
                "severity": CitationSeverity.HIGH,
                "keywords": ["fire safety", "emergency", "procedures", "plan", "training", "drill"],
                "regulation": "ACA Standard 4-4210",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Written fire safety plan required",
                    "Monthly fire drills conducted",
                    "Staff training on fire safety procedures",
                    "Evacuation procedures posted"
                ]
            },
            "ACA-4-4211": {
                "title": "Fire Detection and Suppression Equipment",
                "description": "Installation and maintenance of fire detection and suppression systems",
                "category": CitationCategory.FIRE_SUPPRESSION,
                "severity": CitationSeverity.CRITICAL,
                "keywords": ["detection", "suppression", "equipment", "maintenance", "testing"],
                "regulation": "ACA Standard 4-4211",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Fire detection systems in all areas",
                    "Suppression systems as required by code",
                    "Monthly testing and inspection",
                    "Annual certification by qualified personnel"
                ]
            },
            "ACA-4-4212": {
                "title": "Evacuation Procedures",
                "description": "Emergency evacuation plans and procedures",
                "category": CitationCategory.EMERGENCY_EGRESS,
                "severity": CitationSeverity.HIGH,
                "keywords": ["evacuation", "emergency", "procedures", "plan", "routes", "assembly"],
                "regulation": "ACA Standard 4-4212",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Written evacuation procedures",
                    "Primary and alternate evacuation routes",
                    "Assembly areas designated",
                    "Special provisions for inmates with disabilities"
                ]
            },
            "ACA-4-4372": {
                "title": "Environmental Health and Safety",
                "description": "Environmental health and safety program requirements",
                "category": CitationCategory.ENVIRONMENTAL,
                "severity": CitationSeverity.MEDIUM,
                "keywords": ["environmental", "health", "safety", "air quality", "water", "waste"],
                "regulation": "ACA Standard 4-4372",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Environmental health and safety program",
                    "Air quality monitoring",
                    "Water quality testing",
                    "Waste management procedures"
                ]
            },
            "ACA-4-4373": {
                "title": "Hazardous Material Management",
                "description": "Management of hazardous materials in correctional facilities",
                "category": CitationCategory.HAZARDOUS_MATERIALS,
                "severity": CitationSeverity.HIGH,
                "keywords": ["hazardous", "materials", "chemicals", "storage", "handling", "disposal"],
                "regulation": "ACA Standard 4-4373",
                "applicability": "All correctional facilities",
                "requirements": [
                    "Hazardous material inventory maintained",
                    "Proper storage and handling procedures",
                    "Staff training on hazardous materials",
                    "Disposal procedures per regulations"
                ]
            },
            
            # 105 CMR 451 Citations
            "105-CMR-451.100": {
                "title": "Fire Safety in Correctional Facilities",
                "description": "Massachusetts fire safety regulations specific to correctional facilities",
                "category": CitationCategory.LIFE_SAFETY,
                "severity": CitationSeverity.CRITICAL,
                "keywords": ["fire safety", "correctional", "massachusetts", "regulations", "compliance"],
                "regulation": "105 CMR 451.100",
                "applicability": "All Massachusetts correctional facilities",
                "requirements": [
                    "Compliance with Massachusetts fire safety code",
                    "Monthly fire safety inspections",
                    "Documentation of all fire safety activities",
                    "Immediate correction of fire safety violations"
                ]
            },
            "105-CMR-451.200": {
                "title": "Fire Suppression Systems",
                "description": "Requirements for fire suppression systems in Massachusetts correctional facilities",
                "category": CitationCategory.FIRE_SUPPRESSION,
                "severity": CitationSeverity.CRITICAL,
                "keywords": ["suppression", "systems", "massachusetts", "sprinkler", "standpipe"],
                "regulation": "105 CMR 451.200",
                "applicability": "All Massachusetts correctional facilities",
                "requirements": [
                    "Automatic sprinkler systems required",
                    "Standpipe systems where required",
                    "Monthly inspection and testing",
                    "Annual certification required"
                ]
            },
            "105-CMR-451.300": {
                "title": "Emergency Egress Requirements",
                "description": "Emergency egress requirements for Massachusetts correctional facilities",
                "category": CitationCategory.EMERGENCY_EGRESS,
                "severity": CitationSeverity.HIGH,
                "keywords": ["egress", "emergency", "exits", "massachusetts", "correctional"],
                "regulation": "105 CMR 451.300",
                "applicability": "All Massachusetts correctional facilities",
                "requirements": [
                    "Minimum two means of egress from each area",
                    "Exit doors shall be readily openable",
                    "Emergency lighting systems required",
                    "Exit signs shall be illuminated"
                ]
            },
            "105-CMR-451.400": {
                "title": "Electrical Safety in Correctional Facilities",
                "description": "Electrical safety requirements for Massachusetts correctional facilities",
                "category": CitationCategory.ELECTRICAL_SAFETY,
                "severity": CitationSeverity.MEDIUM,
                "keywords": ["electrical", "safety", "massachusetts", "wiring", "grounding"],
                "regulation": "105 CMR 451.400",
                "applicability": "All Massachusetts correctional facilities",
                "requirements": [
                    "All electrical work by licensed electricians",
                    "Ground fault circuit interrupters required",
                    "Electrical panels properly labeled",
                    "Monthly electrical safety inspections"
                ]
            },
            "105-CMR-451.500": {
                "title": "Environmental Safety Requirements",
                "description": "Environmental safety requirements for Massachusetts correctional facilities",
                "category": CitationCategory.ENVIRONMENTAL,
                "severity": CitationSeverity.MEDIUM,
                "keywords": ["environmental", "safety", "massachusetts", "air quality", "ventilation"],
                "regulation": "105 CMR 451.500",
                "applicability": "All Massachusetts correctional facilities",
                "requirements": [
                    "Adequate ventilation systems",
                    "Air quality monitoring",
                    "Environmental hazard assessments",
                    "Waste management compliance"
                ]
            }
        }
    
    def _build_keyword_index(self) -> Dict[str, List[str]]:
        """Build keyword index for fast searching"""
        index = {}
        for citation_id, citation in self.citations.items():
            for keyword in citation["keywords"]:
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(citation_id)
        return index

class CitationEngine:
    """Advanced citation suggestion engine with natural language processing"""
    
    def __init__(self):
        self.db = CitationDatabase()
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for finding violations"""
        return {
            "fire_alarm": re.compile(r'\b(fire\s+alarm|smoke\s+detector|detection\s+system|alarm\s+panel|pull\s+station)\b', re.IGNORECASE),
            "sprinkler": re.compile(r'\b(sprinkler|suppression|water\s+system|sprinkler\s+head|fire\s+pump)\b', re.IGNORECASE),
            "egress": re.compile(r'\b(exit|egress|evacuation|door|corridor|stairway|emergency\s+lighting)\b', re.IGNORECASE),
            "electrical": re.compile(r'\b(electrical|wiring|circuit|panel|breaker|outlet|grounding)\b', re.IGNORECASE),
            "hazmat": re.compile(r'\b(hazardous|chemical|flammable|toxic|corrosive|storage)\b', re.IGNORECASE),
            "environmental": re.compile(r'\b(environmental|air\s+quality|ventilation|water|waste)\b', re.IGNORECASE),
            "structural": re.compile(r'\b(structural|building|ceiling|wall|floor|foundation)\b', re.IGNORECASE),
            "maintenance": re.compile(r'\b(maintenance|repair|inspection|testing|cleaning)\b', re.IGNORECASE),
            "training": re.compile(r'\b(training|drill|procedure|plan|staff|education)\b', re.IGNORECASE),
            "documentation": re.compile(r'\b(document|record|log|report|certificate|permit)\b', re.IGNORECASE)
        }
    
    def suggest_citations(self, 
                         finding: str, 
                         facility_type: str = "correctional",
                         severity_filter: Optional[CitationSeverity] = None,
                         category_filter: Optional[CitationCategory] = None) -> List[Dict[str, Any]]:
        """
        Suggest relevant citations based on inspection findings
        
        Args:
            finding: The inspection finding text
            facility_type: Type of facility (correctional, detention, etc.)
            severity_filter: Filter by severity level
            category_filter: Filter by citation category
            
        Returns:
            List of suggested citations with relevance scores
        """
        suggestions = []
        
        # Score citations based on keyword matches
        keyword_scores = self._score_by_keywords(finding)
        
        # Score citations based on pattern matches
        pattern_scores = self._score_by_patterns(finding)
        
        # Combine scores
        combined_scores = {}
        for citation_id in set(list(keyword_scores.keys()) + list(pattern_scores.keys())):
            keyword_score = keyword_scores.get(citation_id, 0)
            pattern_score = pattern_scores.get(citation_id, 0)
            combined_scores[citation_id] = keyword_score + pattern_score
        
        # Apply filters and create suggestions
        for citation_id, score in combined_scores.items():
            if score > 0:  # Only include citations with positive scores
                citation = self.db.citations[citation_id]
                
                # Apply severity filter
                if severity_filter and citation["severity"] != severity_filter:
                    continue
                
                # Apply category filter
                if category_filter and citation["category"] != category_filter:
                    continue
                
                suggestions.append({
                    "id": citation_id,
                    "code": citation_id,
                    "title": citation["title"],
                    "description": citation["description"],
                    "category": citation["category"],
                    "severity": citation["severity"],
                    "regulation": citation["regulation"],
                    "applicability": citation["applicability"],
                    "requirements": citation["requirements"],
                    "relevance_score": score,
                    "keywords_matched": self._get_matched_keywords(finding, citation["keywords"])
                })
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Return top 10 suggestions
        return suggestions[:10]
    
    def _score_by_keywords(self, finding: str) -> Dict[str, float]:
        """Score citations based on keyword matches"""
        scores = {}
        finding_lower = finding.lower()
        
        for citation_id, citation in self.db.citations.items():
            score = 0
            for keyword in citation["keywords"]:
                if keyword in finding_lower:
                    # Weight by keyword importance and frequency
                    frequency = finding_lower.count(keyword)
                    importance = self._get_keyword_importance(keyword)
                    score += frequency * importance
            
            if score > 0:
                scores[citation_id] = score
        
        return scores
    
    def _score_by_patterns(self, finding: str) -> Dict[str, float]:
        """Score citations based on pattern matches"""
        scores = {}
        
        # Pattern to category mapping
        pattern_categories = {
            "fire_alarm": CitationCategory.FIRE_DETECTION,
            "sprinkler": CitationCategory.FIRE_SUPPRESSION,
            "egress": CitationCategory.EMERGENCY_EGRESS,
            "electrical": CitationCategory.ELECTRICAL_SAFETY,
            "hazmat": CitationCategory.HAZARDOUS_MATERIALS,
            "environmental": CitationCategory.ENVIRONMENTAL,
            "structural": CitationCategory.STRUCTURAL,
            "maintenance": CitationCategory.LIFE_SAFETY,
            "training": CitationCategory.LIFE_SAFETY,
            "documentation": CitationCategory.LIFE_SAFETY
        }
        
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(finding)
            if matches:
                category = pattern_categories.get(pattern_name)
                if category:
                    # Find citations in this category
                    for citation_id, citation in self.db.citations.items():
                        if citation["category"] == category:
                            if citation_id not in scores:
                                scores[citation_id] = 0
                            scores[citation_id] += len(matches) * 2  # Pattern matches are weighted higher
        
        return scores
    
    def _get_keyword_importance(self, keyword: str) -> float:
        """Get importance weight for a keyword"""
        # High importance keywords
        high_importance = ["fire", "smoke", "alarm", "sprinkler", "exit", "emergency", "hazardous", "electrical"]
        # Medium importance keywords
        medium_importance = ["safety", "system", "equipment", "maintenance", "inspection", "testing"]
        # Low importance keywords
        low_importance = ["general", "standard", "requirement", "procedure", "documentation"]
        
        if keyword in high_importance:
            return 3.0
        elif keyword in medium_importance:
            return 2.0
        elif keyword in low_importance:
            return 1.0
        else:
            return 1.5  # Default weight
    
    def _get_matched_keywords(self, finding: str, keywords: List[str]) -> List[str]:
        """Get list of keywords that matched in the finding"""
        finding_lower = finding.lower()
        matched = []
        for keyword in keywords:
            if keyword in finding_lower:
                matched.append(keyword)
        return matched
    
    def get_citation_by_id(self, citation_id: str) -> Optional[Dict[str, Any]]:
        """Get citation details by ID"""
        return self.db.citations.get(citation_id)
    
    def get_citations_by_category(self, category: CitationCategory) -> List[Dict[str, Any]]:
        """Get all citations in a specific category"""
        citations = []
        for citation_id, citation in self.db.citations.items():
            if citation["category"] == category:
                citations.append({
                    "id": citation_id,
                    "code": citation_id,
                    **citation
                })
        return citations
    
    def get_citations_by_severity(self, severity: CitationSeverity) -> List[Dict[str, Any]]:
        """Get all citations with specific severity"""
        citations = []
        for citation_id, citation in self.db.citations.items():
            if citation["severity"] == severity:
                citations.append({
                    "id": citation_id,
                    "code": citation_id,
                    **citation
                })
        return citations
    
    def search_citations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search citations by query string"""
        results = []
        query_lower = query.lower()
        
        for citation_id, citation in self.db.citations.items():
            score = 0
            
            # Search in title
            if query_lower in citation["title"].lower():
                score += 10
            
            # Search in description
            if query_lower in citation["description"].lower():
                score += 5
            
            # Search in keywords
            for keyword in citation["keywords"]:
                if query_lower in keyword:
                    score += 3
            
            # Search in requirements
            for requirement in citation["requirements"]:
                if query_lower in requirement.lower():
                    score += 2
            
            if score > 0:
                results.append({
                    "id": citation_id,
                    "code": citation_id,
                    "score": score,
                    **citation
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def validate_citation(self, citation_id: str) -> bool:
        """Validate if a citation ID exists"""
        return citation_id in self.db.citations
    
    def get_related_citations(self, citation_id: str) -> List[Dict[str, Any]]:
        """Get citations related to the given citation"""
        if citation_id not in self.db.citations:
            return []
        
        base_citation = self.db.citations[citation_id]
        related = []
        
        for other_id, other_citation in self.db.citations.items():
            if other_id == citation_id:
                continue
            
            # Related if same category
            if other_citation["category"] == base_citation["category"]:
                related.append({
                    "id": other_id,
                    "code": other_id,
                    "relation": "same_category",
                    **other_citation
                })
            
            # Related if similar keywords
            common_keywords = set(base_citation["keywords"]) & set(other_citation["keywords"])
            if len(common_keywords) >= 2:
                related.append({
                    "id": other_id,
                    "code": other_id,
                    "relation": "similar_keywords",
                    "common_keywords": list(common_keywords),
                    **other_citation
                })
        
        return related[:5]  # Return top 5 related citations