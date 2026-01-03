"""
Therapist Response Engine
LLM-ready response generation logic
"""
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from safety import SafetyResult, SafetyLevel

class TherapyStyle(Enum):
    SUPPORTIVE = "supportive"
    CBT = "cbt"
    SOLUTION_FOCUSED = "solution_focused"
    MINDFULNESS = "mindfulness"

@dataclass
class ChatResponse:
    message: str
    therapy_style: TherapyStyle
    safety_level: SafetyLevel
    metadata: Dict[str, Any]

class TherapistEngine:
    """
    AI Therapist Engine with multiple therapy styles
    and safety-aware response generation
    """
    
    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.therapy_techniques = self._load_therapy_techniques()
        
    def _load_response_templates(self) -> Dict[str, List[str]]:
        """Load response templates for different contexts"""
        return {
            "empathy": [
                "أتفهم ما تمر به. يمكن أن تكون هذه المشاعر صعبة حقاً.",
                "يبدو أن هذا الوضع يؤثر عليك بشدة. شكراً لمشاركتي إياه.",
                "ما تشعر به الآن أمر مفهوم في ظل هذه الظروف.",
                "لا بد أن هذا يؤلمك. أنا هنا لأسمعك.",
                "شجاعة كبيرة أن تتحدث عن هذا. أقدّر ثقتك بي."
            ],
            "validation": [
                "مشاعرك حقيقية ومهمة. كل شخص يستحق أن يُسمع.",
                "لا يوجد مشاعر 'صحيحة' أو 'خاطئة'. ما تشعر به الآن هو رد فعلك الطبيعي.",
                "في مثل هذه المواقف، من الطبيعي أن تشعر بهذه الطريقة.",
                "رد فعلك على هذا الموقف يظهر مدى أهميته بالنسبة لك.",
                "الاعتراف بالمشاعر هو الخطوة الأولى نحو التعامل معها."
            ],
            "exploration": [
                "هل يمكنك أن تخبرني المزيد عن ذلك؟",
                "كيف يؤثر هذا على حياتك اليومية؟",
                "متى بدأت تشعر بهذه الطريقة؟",
                "هل هناك جوانب أخرى من هذا الموقف تود مناقشتها؟",
                "كيف تتعامل عادة مع مثل هذه المشاعر؟"
            ],
            "reframing": [
                "هل فكرت في النظر إلى هذا الموقف من زاوية مختلفة؟",
                "ماذا لو كان هذا التحدي فرصة للنمو؟",
                "أحياناً نرى الأمور أسوأ مما هي عليه. هل هناك جوانب إيجابية؟",
                "كيف ستنظر إلى هذا الموقف بعد سنة من الآن؟",
                "ما الذي يمكنك التعلمه من هذه التجربة؟"
            ],
            "coping": [
                "هل جربت تمارين التنفس العميق عندما تشعر بالتوتر؟",
                "الكتابة عن مشاعرك قد تساعد في تنظيمها.",
                "النشاط البدني الخفيف يمكن أن يحسن المزاج.",
                "التحدث مع صديق مقرب قد يخفف العبء.",
                "تقسيم المشكلة إلى أجزاء صغيرة قد يجعلها أكثر قابلية للإدارة."
            ],
            "hope": [
                "الأوقات الصعبة مؤقتة، حتى لو لم تبدو كذلك الآن.",
                "لديك نقاط قوة قد تساعدك في تخطي هذا التحدي.",
                "طلب المساعدة هو علامة قوة، ليس ضعفاً.",
                "كل تجربة، حتى الصعبة منها، تساهم في نموك الشخصي.",
                "هناك دائمًا إمكانية للتغيير والنمو."
            ]
        }
    
    def _load_therapy_techniques(self) -> Dict[TherapyStyle, List[str]]:
        """Load therapy techniques by style"""
        return {
            TherapyStyle.SUPPORTIVE: [
                "التعاطف والاستماع النشط",
                "التحقق من المشاعر",
                "تقدير الجهد والشجاعة",
                "التطبيع والتطمين",
                "التشجيع والتقوية"
            ],
            TherapyStyle.CBT: [
                "تحديد الأفكار الآلية",
                "اختبار الأدلة والواقع",
                "إعادة الهيكلة المعرفية",
                "التسجيل الذاتي للأفكار",
                "تجارب السلوك"
            ],
            TherapyStyle.SOLUTION_FOCUSED: [
                "أسئلة المعجزة",
                "تحديد الاستثناءات",
                "قياس التقدم",
                "البحث عن الموارد",
                "بناء السيناريوهات المفضلة"
            ],
            TherapyStyle.MINDFULNESS: [
                "الوعي باللحظة الحالية",
                "الملاحظة بدون حكم",
                "تمارين التنفس الواعي",
                "مسح الجسم",
                "التأمل في المشاعر"
            ]
        }
    
    def generate_response(self, user_message: str, 
                         safety_context: SafetyResult,
                         chat_history: List[Dict[str, Any]] = None) -> ChatResponse:
        """
        Generate therapeutic response based on user input and safety context
        """
        # Determine therapy style based on safety level and history
        therapy_style = self._determine_therapy_style(safety_context, chat_history)
        
        # Select response components based on context
        response_components = self._select_response_components(
            user_message, safety_context, therapy_style
        )
        
        # Construct final response
        response_message = self._construct_response(response_components, therapy_style)
        
        # Add safety disclaimer if needed
        if safety_context.level in [SafetyLevel.WARNING, SafetyLevel.DANGER]:
            response_message += self._add_safety_disclaimer(safety_context)
        
        return ChatResponse(
            message=response_message,
            therapy_style=therapy_style,
            safety_level=safety_context.level,
            metadata={
                "response_components": response_components,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    def _determine_therapy_style(self, safety_context: SafetyResult, 
                               chat_history: Optional[List[Dict]] = None) -> TherapyStyle:
        """Determine appropriate therapy style based on context"""
        
        if safety_context.level == SafetyLevel.CRISIS:
            return TherapyStyle.SUPPORTIVE
        
        if safety_context.level == SafetyLevel.DANGER:
            return TherapyStyle.SUPPORTIVE
        
        if safety_context.level == SafetyLevel.WARNING:
            # For warning level, use supportive with some CBT elements
            return random.choice([TherapyStyle.SUPPORTIVE, TherapyStyle.CBT])
        
        # For safe conversations, vary therapy style based on conversation history
        if chat_history and len(chat_history) > 5:
            # After initial conversation, introduce different styles
            styles = [TherapyStyle.SUPPORTIVE, TherapyStyle.CBT, 
                     TherapyStyle.SOLUTION_FOCUSED, TherapyStyle.MINDFULNESS]
            
            # Prefer CBT and solution-focused for ongoing conversations
            weights = [0.2, 0.3, 0.3, 0.2]
            return random.choices(styles, weights=weights)[0]
        
        # Default to supportive for new conversations
        return TherapyStyle.SUPPORTIVE
    
    def _select_response_components(self, user_message: str, 
                                  safety_context: SafetyResult,
                                  therapy_style: TherapyStyle) -> List[str]:
        """Select appropriate response components"""
        components = []
        
        # Always start with empathy for safety levels above safe
        if safety_context.level != SafetyLevel.SAFE:
            components.append("empathy")
        
        # Add validation for emotional content
        negative_words = ["حزين", "قلق", "خوف", "sad", "anxious", "afraid"]
        if any(word in user_message.lower() for word in negative_words):
            components.append("validation")
        
        # Add exploration for detailed responses
        if len(user_message.split()) > 10:  # Longer messages
            components.append("exploration")
        
        # Style-specific components
        if therapy_style == TherapyStyle.CBT:
            components.append("reframing")
        elif therapy_style == TherapyStyle.SOLUTION_FOCUSED:
            components.extend(["exploration", "hope"])
        elif therapy_style == TherapyStyle.MINDFULNESS:
            components.append("coping")
        
        # Ensure at least one component
        if not components:
            components = ["empathy", "exploration"]
        
        # Remove duplicates and limit to 3 components
        unique_components = list(dict.fromkeys(components))
        return unique_components[:3]
    
    def _construct_response(self, components: List[str], 
                          therapy_style: TherapyStyle) -> str:
        """Construct coherent response from components"""
        response_parts = []
        
        for component in components:
            if component in self.response_templates:
                template = random.choice(self.response_templates[component])
                response_parts.append(template)
        
        # Connect parts smoothly
        if len(response_parts) == 1:
            return response_parts[0]
        elif len(response_parts) == 2:
            connectors = [" ", " كما أن "]
            return response_parts[0] + random.choice(connectors) + response_parts[1]
        else:
            connectors = [" ", " بالإضافة إلى ذلك، ", " أيضاً، "]
            response = response_parts[0]
            for i, part in enumerate(response_parts[1:], 1):
                if i == len(response_parts) - 1:
                    response += " وأخيراً، " + part
                else:
                    response += random.choice(connectors) + part
            return response
    
    def _add_safety_disclaimer(self, safety_context: SafetyResult) -> str:
        """Add appropriate safety disclaimer"""
        if safety_context.level == SafetyLevel.DANGER:
            return "\n\n⚠️ ملاحظة هامة: أنا هنا لأقدم الدعم والاستماع، لكنني لست بديلاً عن المتخصصين. إذا استمرت هذه المشاعر، أنصح بشدة بالتواصل مع مختص."
        elif safety_context.level == SafetyLevel.WARNING:
            return "\n\n💡 تذكر: رعاية الصحة النفسية مهمة. لا تتردد في طلب مساعدة متخصصة إذا احتجت إليها."
        return ""
    
    def is_healthy(self) -> bool:
        """Health check for therapist engine"""
        return True
    
    def get_available_styles(self) -> Dict[str, List[str]]:
        """Get information about available therapy styles"""
        return {
            style.value: techniques 
            for style, techniques in self.therapy_techniques.items()
        }
    
    def analyze_conversation_pattern(self, chat_history: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation patterns for insights"""
        if not chat_history:
            return {"pattern": "new_conversation", "depth": 0}
        
        user_messages = [msg for msg in chat_history if msg["role"] == "user"]
        
        analysis = {
            "message_count": len(user_messages),
            "avg_message_length": sum(len(msg["content"]) for msg in user_messages) / max(len(user_messages), 1),
            "topics": self._extract_topics(chat_history),
            "emotional_tone": self._assess_emotional_tone(chat_history)
        }
        
        return analysis
    
    def _extract_topics(self, chat_history: List[Dict]) -> List[str]:
        """Extract main topics from conversation"""
        # Basic topic extraction based on keywords
        topic_keywords = {
            "علاقات": ["زوج", "زوجة", "أم", "أب", "صديق", "علاقة", "أسرة"],
            "عمل": ["عمل", "وظيفة", "مدير", "زملاء", "راتب", "مشروع"],
            "قلق": ["قلق", "توتر", "خوف", "هلع", "مستقبل"],
            "اكتئاب": ["حزن", "يأس", "فقدان الأمل", "لا معنى", "تعاسة"],
            "صحة": ["نوم", "أكل", "صحة", "مرض", "ألم", "تعب"]
        }
        
        topics = []
        all_text = " ".join([msg["content"] for msg in chat_history])
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # Return top 3 topics
    
    def _assess_emotional_tone(self, chat_history: List[Dict]) -> str:
        """Assess overall emotional tone of conversation"""
        positive_words = ["سعيد", "فرح", "أمل", "تحسن", "شكراً", "أفضل"]
        negative_words = ["حزين", "قلق", "خوف", "يأس", "مشكلة", "صعب"]
        
        all_text = " ".join([msg["content"] for msg in chat_history]).lower()
        
        positive_count = sum(1 for word in positive_words if word in all_text)
        negative_count = sum(1 for word in negative_words if word in all_text)
        
        if negative_count > positive_count * 2:
            return "negative"
        elif positive_count > negative_count * 2:
            return "positive"
        else:
            return "neutral"
