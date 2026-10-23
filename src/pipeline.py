"""Original resume-job analysis with its dependencies supplied explicitly."""

from src.similarity import TfidfVectorizer, cosine_similarity

def analyze_match(resume_index, job_index, cv, jobs, extract_skills_optimized):

    # Extract skills using the optimized extractor
    resume_skills = extract_skills_optimized(
        cv.loc[resume_index, "processed_resume"]
    )

    job_skills = extract_skills_optimized(
        jobs.loc[job_index, "processed_job"]
    )

    # Find matched and missing skills
    matched = list(
        set(resume_skills) & set(job_skills)
    )

    missing = list(
        set(job_skills) - set(resume_skills)
    )

    # Calculate skill match percentage
    if len(job_skills) > 0:
        skill_score = (
            len(matched) / len(job_skills)
        ) * 100
    else:
        skill_score = 0

    # Prepare text for TF-IDF
    documents = [
        cv.loc[resume_index, "final_processed_resume"],
        jobs.loc[job_index, "final_processed_job"]
    ]

    # Convert text into TF-IDF vectors
    tfidf = TfidfVectorizer()

    matrix = tfidf.fit_transform(documents)

    # Calculate cosine similarity
    similarity = cosine_similarity(
        matrix[0:1],
        matrix[1:2]
    )[0][0] * 100

    # Store results
    result = {
        "resume_position": cv.loc[resume_index, "target_position"],
        "job_title": jobs.loc[job_index, "job_title"],
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_match_percentage": round(skill_score, 2),
        "text_similarity_percentage": round(similarity, 2)
    }

    # Display results
    print("Resume:", result["resume_position"])
    print("Job:", result["job_title"])

    print("\nMatched Skills:")
    print(result["matched_skills"])

    print("\nMissing Skills:")
    print(result["missing_skills"])

    print(
        "\nSkill Match Percentage:",
        result["skill_match_percentage"],
        "%"
    )

    print(
        "Text Similarity Percentage:",
        result["text_similarity_percentage"],
        "%"
    )

    return result
