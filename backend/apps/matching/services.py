"""
AI Service Layer for Connector.

Dual-mode operation:
  - When OPENAI_API_KEY is configured → uses OpenAI GPT for intelligent parsing
  - Fallback → keyword-based intent parsing and tag extraction

This ensures the matching pipeline works end-to-end in development
(without an API key) and seamlessly upgrades to AI when configured.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger("apps")


# ---------------------------------------------------------------------------
# Keyword taxonomy used by the fallback engine
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "food": [
        "food",
        "meal",
        "grocery",
        "hunger",
        "eat",
        "cooking",
        "restaurant",
        "catering",
        "nutrition",
        "pantry",
        "ration",
    ],
    "shelter": [
        "shelter",
        "housing",
        "home",
        "rent",
        "accommodation",
        "homeless",
        "roof",
        "apartment",
    ],
    "medical": [
        "medical",
        "health",
        "doctor",
        "hospital",
        "clinic",
        "medicine",
        "nurse",
        "therapy",
        "dental",
        "emergency medical",
    ],
    "education": [
        "education",
        "tutoring",
        "school",
        "learning",
        "teach",
        "tutor",
        "course",
        "training",
        "literacy",
        "scholarship",
    ],
    "legal": [
        "legal",
        "lawyer",
        "law",
        "court",
        "advocate",
        "rights",
        "justice",
    ],
    "employment": [
        "job",
        "employment",
        "work",
        "hire",
        "career",
        "resume",
        "internship",
        "skill training",
    ],
    "transport": [
        "transport",
        "ride",
        "car",
        "travel",
        "delivery",
        "moving",
        "logistics",
        "ambulance",
    ],
    "financial": [
        "money",
        "loan",
        "financial",
        "fund",
        "donate",
        "grant",
        "microfinance",
        "payment",
        "zakat",
    ],
    "clothing": [
        "clothes",
        "clothing",
        "wear",
        "garment",
        "textile",
        "fabric",
    ],
    "technology": [
        "tech",
        "computer",
        "software",
        "internet",
        "phone",
        "repair",
        "programming",
        "web",
    ],
    "childcare": [
        "child",
        "daycare",
        "babysit",
        "kids",
        "nursery",
        "parenting",
    ],
    "elderly": [
        "elderly",
        "senior",
        "old age",
        "geriatric",
    ],
    "disability": [
        "disability",
        "accessible",
        "wheelchair",
        "impaired",
        "special needs",
    ],
    "mental_health": [
        "mental",
        "counseling",
        "depression",
        "anxiety",
        "stress",
        "psychological",
        "therapy",
    ],
    "community": [
        "community",
        "volunteer",
        "social",
        "event",
        "gathering",
        "outreach",
        "charity",
    ],
    "utilities": [
        "electric",
        "plumbing",
        "water",
        "gas",
        "repair",
        "maintenance",
        "handyman",
        "carpenter",
    ],
}


def _get_openai_client():
    """Return an OpenAI client if the API key is configured, else ``None``."""
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=api_key)
    except ImportError:
        logger.warning("openai package not installed — using keyword fallback")
        return None


class AIService:
    """AI service for intent parsing, tag generation, and match scoring."""

    # ------------------------------------------------------------------
    # Status Intent Parsing
    # ------------------------------------------------------------------
    @staticmethod
    def parse_status_intent(text: str, status_type: str = "need") -> dict:
        """
        Parse a status text and extract structured information.

        Returns::

            {
                "parsed_intent": str,
                "tags": list[str],
                "category": str,
                "urgency_hint": str,
            }
        """
        client = _get_openai_client()
        if client:
            return AIService._parse_with_openai(client, text, status_type)
        return AIService._parse_with_keywords(text, status_type)

    @staticmethod
    def _parse_with_openai(client, text: str, status_type: str) -> dict:
        """Use OpenAI to parse status intent."""
        try:
            model = getattr(settings, "OPENAI_MODEL", "gpt-4")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI assistant for a hyperlocal connection app. "
                            "Parse the user's status/broadcast and extract structured information. "
                            "Return ONLY a JSON object with these fields:\n"
                            '- "parsed_intent": A clear 1-sentence description of what the user needs/offers\n'
                            '- "tags": A list of 2-5 lowercase category tags (e.g., ["food", "shelter", "medical"])\n'
                            '- "category": The primary category (single word)\n'
                            '- "urgency_hint": One of "low", "medium", "high", "emergency"\n'
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Status type: {status_type}\nText: {text}",
                    },
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "parsed_intent": result.get("parsed_intent", ""),
                "tags": [t.lower().strip() for t in result.get("tags", [])],
                "category": result.get("category", "general").lower().strip(),
                "urgency_hint": result.get("urgency_hint", "medium"),
            }
        except Exception as e:
            logger.error("OpenAI parsing failed: %s", e)
            return AIService._parse_with_keywords(text, status_type)

    @staticmethod
    def _parse_with_keywords(text: str, status_type: str) -> dict:
        """Fallback: keyword-based intent extraction."""
        text_lower = text.lower()
        matched_categories = []
        matched_keywords = []

        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    if category not in matched_categories:
                        matched_categories.append(category)
                    if kw.lower() not in matched_keywords:
                        matched_keywords.append(kw.lower())
                    break  # one keyword is enough per category

        # Urgency detection
        urgency = "medium"
        emergency_words = [
            "emergency",
            "urgent",
            "critical",
            "asap",
            "immediately",
            "dying",
            "desperate",
        ]
        high_words = ["need", "help", "important", "soon", "quickly"]

        for word in emergency_words:
            if word in text_lower:
                urgency = "emergency"
                break

        if urgency == "medium":
            for word in high_words:
                if word in text_lower:
                    urgency = "high"
                    break

        primary_category = matched_categories[0] if matched_categories else "general"
        all_tags = matched_categories + [t for t in matched_keywords if t not in matched_categories]

        # Build human-readable intent description
        action = "needs" if status_type == "need" else "offers"
        if matched_categories:
            intent = f"User {action} {primary_category}-related assistance: " f"{text[:100]}"
        else:
            intent = f"User {action}: {text[:150]}"

        return {
            "parsed_intent": intent,
            "tags": all_tags[:5],
            "category": primary_category,
            "urgency_hint": urgency,
        }

    # ------------------------------------------------------------------
    # Profile Tag Generation
    # ------------------------------------------------------------------
    @staticmethod
    def generate_profile_tags(skills: list, interests: list, bio: str = "") -> list:
        """Generate category tags from profile data."""
        client = _get_openai_client()
        if client:
            return AIService._generate_tags_openai(client, skills, interests, bio)
        return AIService._generate_tags_keywords(skills, interests, bio)

    @staticmethod
    def _generate_tags_openai(client, skills, interests, bio) -> list:
        """Use OpenAI to generate profile tags."""
        try:
            model = getattr(settings, "OPENAI_MODEL", "gpt-4")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Given a user's skills, interests, and bio, generate "
                            "a list of 2-5 lowercase category tags for matching. "
                            'Return ONLY a JSON object: {"tags": ["tag1", "tag2"]}'
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Skills: {', '.join(skills)}\n" f"Interests: {', '.join(interests)}\n" f"Bio: {bio}"
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=100,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return [t.lower().strip() for t in result.get("tags", [])][:5]
        except Exception as e:
            logger.error("OpenAI tag generation failed: %s", e)
            return AIService._generate_tags_keywords(skills, interests, bio)

    @staticmethod
    def _generate_tags_keywords(skills, interests, bio) -> list:
        """Fallback: keyword-based tag generation from profiles."""
        combined_text = " ".join(skills + interests) + " " + bio
        combined_lower = combined_text.lower()

        tags = []
        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in combined_lower:
                    tags.append(category)
                    break
        return tags[:5] if tags else ["general"]

    # ------------------------------------------------------------------
    # Match Scoring
    # ------------------------------------------------------------------
    @staticmethod
    def compute_match_score(
        status_tags: list,
        profile_tags: list,
        profile_skills: list,
        profile_interests: list,
        distance_meters: float = None,
        status_type: str = "need",
    ) -> dict:
        """
        Compute relevance score between a status and a profile.

        Returns::

            {
                "score": float (0.0 – 1.0),
                "reason": str,
                "matched_tags": list,
            }
        """
        status_tag_set = {t.lower() for t in status_tags}
        profile_tag_set = {t.lower() for t in (profile_tags or [])}
        skill_set = {s.lower() for s in (profile_skills or [])}
        interest_set = {i.lower() for i in (profile_interests or [])}

        all_profile_terms = profile_tag_set | skill_set | interest_set
        matched = status_tag_set & all_profile_terms

        # Tag overlap score (60 % weight)
        if not status_tag_set:
            tag_score = 0.1
        else:
            tag_score = len(matched) / len(status_tag_set)

        # Distance proximity score (30 % weight)
        distance_score = 1.0
        if distance_meters is not None:
            if distance_meters <= 100:
                distance_score = 1.0
            elif distance_meters <= 500:
                distance_score = 0.8
            elif distance_meters <= 1000:
                distance_score = 0.6
            elif distance_meters <= 5000:
                distance_score = 0.4
            else:
                distance_score = 0.2

        # Complementary type bonus (10 % weight)
        type_bonus = 0.1 if status_type == "need" and skill_set else 0.0

        # Final weighted score
        score = (tag_score * 0.6) + (distance_score * 0.3) + type_bonus
        score = min(score, 1.0)

        # Human-readable reason
        reasons = []
        if matched:
            reasons.append(f"Matched tags: {', '.join(sorted(matched))}")
        if distance_meters is not None:
            reasons.append(f"Distance: {distance_meters:.0f}m away")
        if not reasons:
            reasons.append("Nearby user with potential relevance")

        return {
            "score": round(score, 3),
            "reason": ". ".join(reasons),
            "matched_tags": sorted(matched),
        }
