"""Original skill comparisons and shared TF-IDF tools."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def compare_skills(extracted_resume_skills, extracted_job_skills):
    # Compare extracted resume skills with extracted job skills

    matched_skills = list(
        set(extracted_resume_skills) & set(extracted_job_skills)
    )

    missing_skills = list(
        set(extracted_job_skills) - set(extracted_resume_skills)
    )

    print("Matched Skills:")
    print(matched_skills)

    print("\nMissing Skills:")
    print(missing_skills)
    return matched_skills, missing_skills

def filter_generic_skills(extracted_resume_skills, extracted_job_skills):
    # Remove generic words from extracted skills

    generic_skills = {
        "development",
        "services",
        "engineer",
        "database",
        "written",
        "direction",
        "financial"
    }

    extracted_resume_skills = [
        skill for skill in extracted_resume_skills
        if skill not in generic_skills
    ]

    extracted_job_skills = [
        skill for skill in extracted_job_skills
        if skill not in generic_skills
    ]

    print("Cleaned Resume Skills:")
    print(extracted_resume_skills)

    print("\nCleaned Job Skills:")
    print(extracted_job_skills)
    return extracted_resume_skills, extracted_job_skills

def calculate_skill_match(matched_skills, extracted_job_skills):
    # Calculate skill match percentage

    if len(extracted_job_skills) > 0:
        skill_match_percentage = (
            len(matched_skills) / len(extracted_job_skills)
        ) * 100
    else:
        skill_match_percentage = 0

    print("Skill Match Percentage:", round(skill_match_percentage, 2), "%")
    return skill_match_percentage
