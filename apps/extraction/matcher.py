# apps/extraction/matcher.py
import re
import logging
from difflib import SequenceMatcher
from django.utils import timezone

from apps.entities.models import Entity, Person, Organization, Alias, EntityType
from apps.extraction.services import calculate_entity_match_score

logger = logging.getLogger(__name__)

def normalize_text(text):
    if not text:
        return ""
    # Lowercase, alphanumeric characters only, stripped
    return re.sub(r'[^a-z0-9]', '', text.lower().strip())

def get_competing_candidates(donor_name, etype, exclude_id=None):
    """
    Returns a list of candidate dictionaries containing (entity, score, method)
    ordered by score descending.
    """
    candidates = []
    normalized_donor = normalize_text(donor_name)
    
    # We query all entities of the same type and score them
    for ent in Entity.objects.filter(entity_type=etype):
        if exclude_id and ent.id == exclude_id:
            continue
            
        score = calculate_entity_match_score(donor_name, ent.canonical_name)
        method = "FUZZY_NAME"
        
        # Check exact canonical name match
        if normalize_text(ent.canonical_name) == normalized_donor:
            score = 100.0
            method = "EXACT_NORMALIZED_NAME"
            
        # Check alias matches
        for alias in ent.aliases.all():
            if normalize_text(alias.alias_text) == normalized_donor:
                score = 100.0
                method = "EXACT_ALIAS"
                break
                
        if score >= 50.0: # Keep candidates with score >= 50%
            candidates.append({
                "entity": ent,
                "score": score,
                "method": method
            })
            
    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

def find_best_entity_match(donor_name, donor_code, occupation="", employer="", city="", state="", zip_code=""):
    """
    Finds the best matching Entity for a given contributor according to matching priorities.
    Returns:
        - matched_entity: Entity object or None
        - match_method: String representing matching priority method
        - metrics: Dictionary of matching scores (score, name_score, location_score, employer_score, compatibility, committee_match, reason)
        - candidates: List of competing candidates [(entity, score, method)]
    """
    is_person = (donor_code == "IND")
    etype = EntityType.PERSON if is_person else EntityType.ORGANIZATION
    
    normalized_name = normalize_text(donor_name)
    
    # Match priority metrics initialization
    metrics = {
        "score": 0.0,
        "name_score": 0.0,
        "location_score": 0.0,
        "employer_score": 0.0,
        "entity_type_compatibility": True,
        "committee_id_match": False,
        "reason": ""
    }
    
    # 1. Check if there is an exact Committee ID match (for Organizations)
    committee_id = ""
    id_match = re.search(r'(?:ID#|I.D. NUMBER)\s*(\d+)', donor_name, re.IGNORECASE)
    if id_match:
        committee_id = id_match.group(1)
        
    if not is_person and committee_id:
        org = Organization.objects.filter(committee_id=committee_id).first()
        if org:
            metrics.update({
                "score": 100.0,
                "name_score": calculate_entity_match_score(donor_name, org.entity.canonical_name),
                "entity_type_compatibility": True,
                "committee_id_match": True,
                "reason": "Exact committee ID match found."
            })
            # Competing candidates
            candidates = get_competing_candidates(donor_name, etype, exclude_id=org.entity.id)
            return org.entity, "EXACT_COMMITTEE_ID", metrics, candidates

    # Fetch all competing candidates
    candidates = get_competing_candidates(donor_name, etype)
    
    # 2. Check exact canonical name match with compatible type
    for c in candidates:
        if c["method"] == "EXACT_NORMALIZED_NAME":
            metrics.update({
                "score": 100.0,
                "name_score": 100.0,
                "reason": "Exact normalized canonical name match."
            })
            # Remove chosen from candidates list for competing candidates report
            competing = [cand for cand in candidates if cand["entity"].id != c["entity"].id]
            return c["entity"], "EXACT_NORMALIZED_NAME", metrics, competing

    # 3. Check exact alias match
    for c in candidates:
        if c["method"] == "EXACT_ALIAS":
            metrics.update({
                "score": 100.0,
                "name_score": 100.0,
                "reason": "Exact alias match."
            })
            competing = [cand for cand in candidates if cand["entity"].id != c["entity"].id]
            return c["entity"], "EXACT_ALIAS", metrics, competing

    # Check and score metadata helper functions
    def calculate_location_score(ent):
        # Locate person or organization profile
        profile_city, profile_zip = "", ""
        if ent.entity_type == EntityType.PERSON and hasattr(ent, 'person_profile'):
            # Person has no direct location fields, we check notes or default
            pass
        elif ent.entity_type == EntityType.ORGANIZATION and hasattr(ent, 'organization_profile'):
            pass
            
        # Match location strings
        loc_score = 0.0
        if city and profile_city and city.lower() == profile_city.lower():
            loc_score += 50.0
        if zip_code and profile_zip and zip_code == profile_zip:
            loc_score += 50.0
        return loc_score

    def calculate_employer_score(ent):
        emp_score = 0.0
        if ent.entity_type == EntityType.PERSON and hasattr(ent, 'person_profile'):
            prof = ent.person_profile
            if occupation and prof.occupation and occupation.lower() == prof.occupation.lower():
                emp_score += 50.0
            # Also check notes for employer
            if employer and employer.lower() in prof.notes.lower():
                emp_score += 50.0
        return emp_score

    # 4. Check name plus city, state, or ZIP
    for c in candidates:
        ent = c["entity"]
        loc_score = calculate_location_score(ent)
        if c["score"] >= 85.0 and loc_score >= 50.0:
            metrics.update({
                "score": c["score"],
                "name_score": c["score"],
                "location_score": loc_score,
                "reason": "High name similarity plus location metadata match."
            })
            competing = [cand for cand in candidates if cand["entity"].id != ent.id]
            return ent, "NAME_AND_LOCATION", metrics, competing

    # 5. Check name plus occupation and employer
    for c in candidates:
        ent = c["entity"]
        emp_score = calculate_employer_score(ent)
        if c["score"] >= 85.0 and emp_score >= 50.0:
            metrics.update({
                "score": c["score"],
                "name_score": c["score"],
                "employer_score": emp_score,
                "reason": "High name similarity plus employment metadata match."
            })
            competing = [cand for cand in candidates if cand["entity"].id != ent.id]
            return ent, "NAME_AND_EMPLOYMENT", metrics, competing

    # 6. Check High fuzzy name similarity (score >= 95.0)
    for c in candidates:
        if c["score"] >= 95.0:
            metrics.update({
                "score": c["score"],
                "name_score": c["score"],
                "reason": f"High fuzzy name match score of {c['score']:.1f}%."
            })
            competing = [cand for cand in candidates if cand["entity"].id != c["entity"].id]
            return c["entity"], "HIGH_CONFIDENCE_FUZZY", metrics, competing

    # 7. Check Possible fuzzy name similarity (85.0 - 94.9)
    for c in candidates:
        ent = c["entity"]
        loc_score = calculate_location_score(ent)
        emp_score = calculate_employer_score(ent)
        if c["score"] >= 85.0:
            if loc_score >= 50.0 or emp_score >= 50.0:
                metrics.update({
                    "score": c["score"],
                    "name_score": c["score"],
                    "location_score": loc_score,
                    "employer_score": emp_score,
                    "reason": f"Possible name match of {c['score']:.1f}% supported by metadata."
                })
                competing = [cand for cand in candidates if cand["entity"].id != ent.id]
                return ent, "POSSIBLE_MATCH", metrics, competing

    # 8. No match found: fallback to provisional creation
    metrics.update({
        "score": 0.0,
        "reason": "No existing entity met name or metadata match thresholds."
    })
    return None, "NEW_PROVISIONAL_ENTITY", metrics, candidates
