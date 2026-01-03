"""
Safety and Crisis Detection Layer
Medical and Legal Compliance Module
"""
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Download NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"
    CRISIS = "crisis"

@dataclass
class SafetyResult:
    is_crisis: bool = False
    level: SafetyLevel = SafetyLevel.SAFE
    keywords: List[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CrisisResponse:
    message: str
    resources: List[str]
    emergency_contacts: List[str] = None
    immediate_actions: List[str] = None

class SafetyChecker:
    """Main safety analysis and crisis detection module"""
    
    def __init__(self):
        # Crisis keywords categorized by severity
        self.crisis_keywords = {
            "suicide": [
                "انتحار", "أقتل نفسي", "أريد أن أموت", "نهاية حياتي",
                "suicide", "kill myself", "want to die", "end my life",
                "لا أريد العيش", "better off dead", "لا فائدة من الحياة"
            ],
            "self_harm": [
                "أجرح نفسي", "أؤذي نفسي", "قطع", "حرق", "self-harm",
                "cut myself", "hurt myself", "bleeding intentionally"
            ],
            "abuse": [
                "اعتداء", "عنف منزلي", "ضرب", "تحرش", "إساءة",
                "abuse", "domestic violence", "beating", "harassment"
            ],
            "emergency_health": [
                "نوبة قلبية", "سكتة دماغية", "توقف تنفس", "جرح نازف",
                "heart attack", "stroke", "can't breathe", "bleeding severely"
            ]
        }
        
        # Warning patterns
        self.warning_patterns = {
            "depression": [
                "مكتئب", "حزين جدا", "لا معنى للحياة", "يأس",
                "depressed", "very sad", "no meaning", "hopeless"
            ],
            "anxiety": [
                "قلق شديد", "نوبة هلع", "خوف", "رهاب",
                "severe anxiety", "panic attack", "terrified", "phobia"
            ],
            "addiction": [
                "إدمان", "مخدرات", "كحول", "لا أستطيع التوقف",
                "addiction", "drugs", "alcohol", "can't stop"
            ]
        }
        
        # Crisis resources (Egypt-specific)
        self.crisis_resources = {
            "suicide": {
                "message": """🚨 أدرك أنك تمر بوقت صعب جداً. الرجاء التواصل فوراً مع:

📞 خط نجدة الطفل (المجلس القومي للطفولة والأمومة): 16000
📞 مصلحة الطب النفسي (وزارة الصحة): 08008880700
📞 مستشفى العباسية للصحة النفسية: 0226336255

📍 الذهاب لأقرب مستشفى حكومي أو قسم طوارئ نفسية
📍 التحدث مع صديق مقرب أو فرد عائلة الآن""",
                "resources": [
                    "المجلس القومي للطفولة والأمومة: 16000",
                    "مصلحة الطب النفسي: 08008880700",
                    "مستشفى العباسية: 0226336255",
                    "الخط الساخن للصحة النفسية: 0220816831"
                ]
            },
            "self_harm": {
                "message": """⚠️ إيذاء النفس هو علامة على معاناة عميقة. دعنا نطلب المساعدة معاً:

📞 مستشفى المعمورة للصحة النفسية (الإسكندرية): 034287000
📞 مستشفى 57357 (دعم نفسي للأطفال): 0225357000
📞 جمعية أصدقاء الصحة النفسية: 0227910885

💡 اقتراحات فورية:
• احتفظ بأدوات حادة بعيداً عن متناول اليد
• اتصل بصديق أو قريب الآن
• اذهب للمشي في مكان آمن""",
                "resources": [
                    "مستشفى المعمورة: 034287000",
                    "مستشفى 57357: 0225357000",
                    "جمعية أصدقاء الصحة النفسية: 0227910885"
                ]
            },
            "abuse": {
                "message": """🛡️ العنف والاعتداء غير مقبولين. المساعدة متاحة:

📞 المجلس القومي للمرأة: 15115
📞 وحدة مكافحة العنف ضد المرأة: 01148933222
📞 نجدة المرأة: ٠٨٨٨٨٨٨٨٨ (مركز المرأة بالقاهرة)

🚨 إذا كنت في خطر مباشر:
• اتصل بالشرطة: 122
• اذهب لجار أو مكان عام آمن
• احتفظ بأدلة إذا أمكن""",
                "resources": [
                    "المجلس القومي للمرأة: 15115",
                    "وحدة مكافحة العنف: 01148933222",
                    "الشرطة: 122"
                ]
            }
        }
        
        # Legal compliance messages
        self.legal_disclaimers = {
            "general": "TheraBot ليس بديلاً عن الاستشارة الطبية النفسية المتخصصة. في حالات الطوارئ، يرجى الاتصال بالسلطات المختصة.",
            "egypt": "بموجب القانون المصري، يتم الحفاظ على سرية المحادثات إلا في حالات الخطر الجسيم على النفس أو الآخرين.",
            "reporting": "في حالة الكشف عن نية انتحارية أو إيذاء الآخرين، قد يكون من واجبنا الإبلاغ للجهات المختصة."
        }
    
    def analyze_message(self, message: str) -> SafetyResult:
        """
        Analyze message for safety concerns and crisis indicators
        """
        message_lower = message.lower()
        
        # Check for crisis keywords
        crisis_detected = False
        crisis_type = None
        found_keywords = []
        
        for crisis_type_name, keywords in self.crisis_keywords.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    crisis_detected = True
                    crisis_type = crisis_type_name
                    found_keywords.append(keyword)
                    break
            if crisis_detected:
                break
        
        if crisis_detected:
            return SafetyResult(
                is_crisis=True,
                level=SafetyLevel.CRISIS,
                keywords=found_keywords,
                confidence=0.95,
                metadata={
                    "crisis_type": crisis_type,
                    "requires_immediate_action": True,
                    "legal_obligation": "report_required"
                }
            )
        
        # Check for warning patterns
        warning_score = 0
        warning_keywords = []
        
        for warning_category, patterns in self.warning_patterns.items():
            for pattern in patterns:
                if pattern.lower() in message_lower:
                    warning_score += 1
                    warning_keywords.append(pattern)
        
        # Determine safety level
        if warning_score >= 3:
            safety_level = SafetyLevel.DANGER
        elif warning_score >= 1:
            safety_level = SafetyLevel.WARNING
        else:
            safety_level = SafetyLevel.SAFE
        
        # Calculate confidence based on keyword matches and message length
        confidence = min(0.9, warning_score * 0.3)
        
        # Additional analysis
        metadata = self._additional_analysis(message)
        
        return SafetyResult(
            is_crisis=False,
            level=safety_level,
            keywords=warning_keywords,
            confidence=confidence,
            metadata=metadata
        )
    
    def _additional_analysis(self, message: str) -> Dict[str, Any]:
        """Perform additional linguistic and sentiment analysis"""
        metadata = {
            "message_length": len(message),
            "contains_questions": "؟" in message or "?" in message,
            "contains_negation": any(word in message.lower() for word in ["لا", "ليس", "لن", "never", "not", "no"]),
            "emotion_indicators": self._detect_emotion_indicators(message)
        }
        
        # Simple sentiment detection (for Arabic and English)
        negative_words_arabic = ["حزين", "تعيس", "يأس", "خوف", "قلق", "ألم", "معاناة"]
        negative_words_english = ["sad", "unhappy", "hopeless", "fear", "anxiety", "pain", "suffering"]
        
        negative_count = sum(1 for word in negative_words_arabic if word in message)
        negative_count += sum(1 for word in negative_words_english if word.lower() in message.lower())
        
        metadata["negative_word_count"] = negative_count
        metadata["sentiment_score"] = -negative_count * 0.2
        
        return metadata
    
    def _detect_emotion_indicators(self, message: str) -> List[str]:
        """Detect emotional indicators in text"""
        indicators = []
        
        # Exclamation marks intensity
        if "!!!" in message:
            indicators.append("high_intensity")
        elif "!!" in message:
            indicators.append("medium_intensity")
        elif "!" in message:
            indicators.append("low_intensity")
        
        # Capital letters (English)
        if message != message.upper() and any(c.isupper() for c in message if c.isalpha()):
            upper_ratio = sum(1 for c in message if c.isupper()) / sum(1 for c in message if c.isalpha())
            if upper_ratio > 0.3:
                indicators.append("emotional_emphasis")
        
        return indicators
    
    def get_crisis_response(self, safety_result: SafetyResult) -> CrisisResponse:
        """Generate appropriate crisis response based on analysis"""
        crisis_type = safety_result.metadata.get("crisis_type", "suicide")
        
        if crisis_type in self.crisis_resources:
            resource_info = self.crisis_resources[crisis_type]
            return CrisisResponse(
                message=resource_info["message"],
                resources=resource_info["resources"],
                emergency_contacts=["122", "123", "180"]  # Police, Ambulance, Fire
            )
        
        # Default crisis response
        return CrisisResponse(
            message="""🚨 يبدو أنك تمر بأزمة. الرجاء التواصل فوراً مع:

📞 الخط الساخن للصحة النفسية: 0220816831
📞 الإسعاف: 123
📞 الشرطة: 122

• لا تبق وحيداً في هذه اللحظة
• اذهب إلى مكان عام أو اتصل بصديق
• تذكر أن هذه المشاعر مؤقتة والمساعدة متاحة""",
            resources=[
                "الخط الساخن للصحة النفسية: 0220816831",
                "الإسعاف: 123",
                "الشرطة: 122"
            ]
        )
    
    def is_healthy(self) -> bool:
        """Health check for the safety module"""
        return True  # In production, add actual health checks
    
    def get_legal_disclaimer(self, context: str = "general") -> str:
        """Get appropriate legal disclaimer"""
        return self.legal_disclaimers.get(context, self.legal_disclaimers["general"])
