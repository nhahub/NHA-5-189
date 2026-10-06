"""Original evaluation calculations and printed comparisons."""

import ast
from sklearn.metrics import precision_score, recall_score, f1_score

def evaluate_single_resume(cv, extract_skills):
    # Compare extracted skills with the reference skills for one resume

    reference_skills = set(
        ast.literal_eval(cv.loc[0, "clean_skills"])
    )

    predicted_skills = set(
        extract_skills(cv.loc[0, "processed_resume"])
    )

    all_eval_skills = list(reference_skills | predicted_skills)

    y_true = [
        1 if skill in reference_skills else 0
        for skill in all_eval_skills
    ]

    y_pred = [
        1 if skill in predicted_skills else 0
        for skill in all_eval_skills
    ]

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    print("Precision:", round(precision, 2))
    print("Recall:", round(recall, 2))
    print("F1-score:", round(f1, 2))
    return precision, recall, f1

def evaluate_resumes(cv, extract_skills):
    # Evaluate the skill extractor on multiple resumes

    precision_scores = []
    recall_scores = []
    f1_scores = []

    for i in range(len(cv)):

        reference_skills = set(
            ast.literal_eval(cv.loc[i, "clean_skills"])
        )

        predicted_skills = set(
            extract_skills(cv.loc[i, "processed_resume"])
        )

        all_eval_skills = list(reference_skills | predicted_skills)

        y_true = [
            1 if skill in reference_skills else 0
            for skill in all_eval_skills
        ]

        y_pred = [
            1 if skill in predicted_skills else 0
            for skill in all_eval_skills
        ]

        precision_scores.append(
            precision_score(y_true, y_pred, zero_division=0)
        )

        recall_scores.append(
            recall_score(y_true, y_pred, zero_division=0)
        )

        f1_scores.append(
            f1_score(y_true, y_pred, zero_division=0)
        )

    print("Average Precision:", round(sum(precision_scores) / len(precision_scores), 2))
    print("Average Recall:", round(sum(recall_scores) / len(recall_scores), 2))
    print("Average F1-score:", round(sum(f1_scores) / len(f1_scores), 2))
    return precision_scores, recall_scores, f1_scores

def evaluate_optimized_resumes(cv, extract_skills_optimized):
    # Evaluate the optimized skill extractor on multiple resumes

    optimized_precision_scores = []
    optimized_recall_scores = []
    optimized_f1_scores = []

    for i in range(len(cv)):

        reference_skills = set(
            ast.literal_eval(cv.loc[i, "clean_skills"])
        )

        predicted_skills = set(
            extract_skills_optimized(cv.loc[i, "processed_resume"])
        )

        all_eval_skills = list(reference_skills | predicted_skills)

        y_true = [
            1 if skill in reference_skills else 0
            for skill in all_eval_skills
        ]

        y_pred = [
            1 if skill in predicted_skills else 0
            for skill in all_eval_skills
        ]

        optimized_precision_scores.append(
            precision_score(y_true, y_pred, zero_division=0)
        )

        optimized_recall_scores.append(
            recall_score(y_true, y_pred, zero_division=0)
        )

        optimized_f1_scores.append(
            f1_score(y_true, y_pred, zero_division=0)
        )

    optimized_precision = sum(optimized_precision_scores) / len(optimized_precision_scores)
    optimized_recall = sum(optimized_recall_scores) / len(optimized_recall_scores)
    optimized_f1 = sum(optimized_f1_scores) / len(optimized_f1_scores)

    print("Optimized Average Precision:", round(optimized_precision, 2))
    print("Optimized Average Recall:", round(optimized_recall, 2))
    print("Optimized Average F1-score:", round(optimized_f1, 2))
    return optimized_precision, optimized_recall, optimized_f1

def compare_evaluation_results(optimized_precision, optimized_recall, optimized_f1):
    # Compare model performance before and after optimization

    print("Before Optimization")
    print("Precision: 0.76")
    print("Recall: 0.98")
    print("F1-score: 0.85")

    print("\nAfter Optimization")
    print("Precision:", round(optimized_precision, 2))
    print("Recall:", round(optimized_recall, 2))
    print("F1-score:", round(optimized_f1, 2))
