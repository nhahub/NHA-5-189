"""Skill dictionaries and spaCy extraction; no datasets are loaded on import."""

import spacy

def build_skill_dictionary(cv, jobs):
    # Create a skill dictionary from resumes and job descriptions

    all_skills = set()

    for skills in cv["skills_list"]:
        all_skills.update(skills)

    for skills in jobs["skills_list"]:
        all_skills.update(skills)

    skill_dictionary = sorted(list(all_skills))

    print("Number of unique skills:", len(skill_dictionary))
    print("\nSample skills:")
    print(skill_dictionary[:30])
    return skill_dictionary

def create_skill_extractor(skill_dictionary):
    # Import spaCy and create an English NLP pipeline


    nlp = spacy.blank("en")

    # Add EntityRuler to recognize skills

    ruler = nlp.add_pipe("entity_ruler")

    # Create patterns for all skills in the dictionary

    patterns = []

    for skill in skill_dictionary:
        patterns.append({
            "label": "SKILL",
            "pattern": skill
        })

    ruler.add_patterns(patterns)

    print("Number of skill patterns:", len(patterns))
    return nlp

def extract_skills(text, nlp):

    doc = nlp(text)

    skills = []

    for ent in doc.ents:
        if ent.label_ == "SKILL":
            skills.append(ent.text)

    return list(set(skills))

def prepare_optimized_extractor(cv, jobs):
    # 1. Rebuild the skill dictionaries from your loaded data
    all_skills = set()
    for skills in cv["skills_list"]:
        all_skills.update(skills)
    for skills in jobs["skills_list"]:
        all_skills.update(skills)

    generic_skills = {"development", "services", "engineer", "database", "written",
                      "direction", "financial", "processes", "quality", "delivery",
                      "network", "meetings", "developing"}
    optimized_skill_dictionary = [s for s in all_skills if s not in generic_skills]

    # 2. Rebuild the optimized NLP pipeline
    optimized_nlp = spacy.blank("en")
    optimized_ruler = optimized_nlp.add_pipe("entity_ruler")

    optimized_patterns = [{"label": "SKILL", "pattern": skill} for skill in optimized_skill_dictionary]
    optimized_ruler.add_patterns(optimized_patterns)
    return optimized_nlp

def optimize_skill_dictionary(skill_dictionary):
    # Remove generic terms from the skill dictionary

    generic_skills = {
        "development",
        "services",
        "engineer",
        "database",
        "written",
        "direction",
        "financial",
        "processes",
        "quality",
        "delivery",
        "network",
        "meetings",
        "developing"
    }

    optimized_skill_dictionary = [
        skill for skill in skill_dictionary
        if skill not in generic_skills
    ]

    print("Original skills:", len(skill_dictionary))
    print("Optimized skills:", len(optimized_skill_dictionary))
    return optimized_skill_dictionary

def create_optimized_extractor(optimized_skill_dictionary):
    # Create a new optimized spaCy skill extractor

    optimized_nlp = spacy.blank("en")

    optimized_ruler = optimized_nlp.add_pipe("entity_ruler")

    optimized_patterns = []

    for skill in optimized_skill_dictionary:
        optimized_patterns.append({
            "label": "SKILL",
            "pattern": skill
        })

    optimized_ruler.add_patterns(optimized_patterns)

    print("Optimized skill patterns:", len(optimized_patterns))
    return optimized_nlp

def extract_skills_optimized(text, optimized_nlp):

    doc = optimized_nlp(text)

    skills = []

    for ent in doc.ents:
        if ent.label_ == "SKILL":
            skills.append(ent.text)

    return list(set(skills))
