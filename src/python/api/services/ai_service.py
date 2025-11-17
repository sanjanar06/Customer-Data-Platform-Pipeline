# Handles LLM-based personalization using Gemini API.
import json
from typing import Dict, Any
import google.generativeai as genai
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Initialize Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    logger.info("Gemini API initialized")
else:
    logger.warning("No GEMINI_API_KEY set. API will return mock responses.")
    model = None

class AIService:
    
    @staticmethod
    def build_personalization_prompt(profile: Dict[str, Any]) -> str:
        """
        Build a context-rich prompt for the LLM (RAG Augmentation step).
        
        Args:
            profile: Customer profile data
            
        Returns:
            Personalized prompt for LLM
        """
        # Extract key data
        identities = profile.get("identities", {})
        attributes = profile.get("attributes", {})
        computed = profile.get("computed_attributes", {})
        
        # Email (if available)
        email = identities.get("email", "unknown")
        
        # Computed metrics
        ltv = computed.get("lifetime_value", 0)
        engagement = computed.get("engagement_score", 0)
        event_metrics = computed.get("event_metrics", {})
        product_metrics = computed.get("product_metrics", {})
        
        # Recent activity
        last_event = profile.get("last_event_type", "unknown")
        products_viewed = product_metrics.get("products_viewed", [])
        products_purchased = product_metrics.get("products_purchased", [])
        
        # Engagement level
        if engagement > 70:
            engagement_level = "High"
        elif engagement > 40:
            engagement_level = "Medium"
        else:
            engagement_level = "Low"
        
        # Shopping pattern
        if ltv > 500:
            shopping_pattern = "Active buyer"
        elif event_metrics.get('total_events', 0) > 3:
            shopping_pattern = "Browser"
        else:
            shopping_pattern = "New visitor"
        
        # Build the prompt
        prompt = f"""You are an expert marketing AI for an e-commerce company specializing in electronics.

            Your task: Create a highly personalized offer for this customer based on their complete profile.

            CUSTOMER PROFILE:
            - Customer ID: {profile.get('master_profile_id')}
            - Email: {email}
            - Customer Value: ${ltv:,.2f}
            - Engagement Level: {engagement}/100 ({engagement_level})
            - Total Events: {event_metrics.get('total_events', 0)}
            - Last Activity: {last_event}

            BEHAVIOR INSIGHTS:
            - Products Viewed: {', '.join(products_viewed[:3]) if products_viewed else 'None'}
            - Products Purchased: {', '.join(products_purchased) if products_purchased else 'None'}
            - Shopping Pattern: {shopping_pattern}

            CONTEXT:
            - Recent activity shows interest in: {attributes.get('product_name', 'general browsing')}
            - Price range comfortable with: ${attributes.get('price', 'unknown')}

            YOUR TASK:
            Create a personalized offer that:
            1. Matches their shopping behavior and preferences
            2. Acknowledges their customer value tier
            3. Feels genuinely personal, not generic
            4. Includes specific product recommendations

            CRITICAL: Return ONLY valid JSON in this EXACT format (no markdown, no backticks):
            {{
            "offer_type": "upsell" or "cross-sell" or "loyalty" or "win-back" or "welcome",
            "title": "Compelling offer title",
            "message": "Personal message explaining the offer (2-3 sentences)",
            "products": ["Product 1", "Product 2", "Product 3"],
            "discount": "Discount amount (e.g., '15%' or '$50 off' or 'Buy 1 Get 1')",
            "reasoning": "Brief explanation of why this offer fits this customer"
            }}
            """
        return prompt
    
    @staticmethod
    def generate_personalized_offer(profile: Dict[str, Any]) -> Dict[str, Any]:
        
        # Build prompt with profile context
        prompt = AIService.build_personalization_prompt(profile)
        
        # If no API key, return mock response
        if not model:
            return AIService.generate_mock_offer(profile)
        
        try:
            # Call Gemini API
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                )
            )
            
            # Extract text
            response_text = response.text.strip()
            
            # Clean up response (remove markdown if present)
            if response_text.startswith("```"):
                # Remove markdown code blocks
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            # Parse JSON
            offer_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["offer_type", "title", "message"]
            for field in required_fields:
                if field not in offer_data:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Generated offer for profile {profile.get('master_profile_id')}")
            return offer_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response text: {response_text}")
            return AIService.generate_mock_offer(profile)
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return AIService.generate_mock_offer(profile)
    
    @staticmethod
    def generate_mock_offer(profile: Dict[str, Any]) -> Dict[str, Any]:
        computed = profile.get("computed_attributes", {})
        ltv = computed.get("lifetime_value", 0)
        
        if ltv > 1000:
            offer = {
                "offer_type": "loyalty",
                "title": "VIP Customer Exclusive",
                "message": "As one of our most valued customers, enjoy 20% off your next purchase plus free expedited shipping!",
                "products": ["Premium Accessories", "Extended Warranty", "Priority Support"],
                "discount": "20% off",
                "reasoning": "High-value customer (LTV > $1000) - reward loyalty with premium benefits"
            }
        elif ltv > 0:
            offer = {
                "offer_type": "cross-sell",
                "title": "Complete Your Setup",
                "message": "Based on your recent purchase, we've handpicked accessories that pair perfectly with your new device.",
                "products": ["Protective Case", "Screen Protector", "Charging Cable"],
                "discount": "15% off accessories",
                "reasoning": "Recent purchaser - perfect time for complementary products"
            }
        else:
            offer = {
                "offer_type": "welcome",
                "title": "Welcome! First Purchase Discount",
                "message": "Start your journey with us! Get 10% off your first order and free shipping on orders over $50.",
                "products": ["Trending Electronics", "Best Sellers", "New Arrivals"],
                "discount": "10% off first order",
                "reasoning": "New visitor - incentivize first purchase"
            }
        
        logger.info(f"Generated mock offer for profile {profile.get('master_profile_id')}")
        return offer
