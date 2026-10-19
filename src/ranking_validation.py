"""Evaluate an independent TF-IDF/skill-overlap baseline against supplied reference rankings.

Important: reference final_score is a constructed score, not verified human relevance.
"""
import argparse
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import ndcg_score
from sklearn.metrics.pairwise import cosine_similarity


def skills(value):
    if isinstance(value, list):
        return {str(x).strip().lower() for x in value if str(x).strip()}
    if pd.isna(value) or not str(value).strip():
        return set()
    try:
        obj = json.loads(value)
    except (ValueError, TypeError):
        try:
            obj = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return set()
    return {str(x).strip().lower() for x in obj} if isinstance(obj, list) else set()


def validate(cv_path, jobs_path, matches_path, output_dir):
    cv = pd.read_csv(cv_path)
    jobs = pd.read_csv(jobs_path)
    matches = pd.read_csv(matches_path)
    for frame, required in [(cv,['candidate_id','resume_text','clean_skills']),
                            (jobs,['job_id','job_text','clean_skills']),
                            (matches,['candidate_id','job_id','final_score'])]:
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f'Missing columns: {sorted(missing)}')
    cv = cv.drop_duplicates('candidate_id').set_index('candidate_id')
    jobs = jobs.drop_duplicates('job_id').set_index('job_id')
    pairs = matches[matches.candidate_id.isin(cv.index) & matches.job_id.isin(jobs.index)].copy()
    pairs = pairs.dropna(subset=['final_score']).drop_duplicates(['candidate_id','job_id'])
    if pairs.empty:
        raise ValueError('No candidate/job IDs overlap; use matching source files.')
    # Shared vector space, unlike separately fitting TF-IDF for each pair.
    resume_text = cv['resume_text'].fillna('').astype(str)
    job_text = jobs.loc[pairs.job_id.unique(),'job_text'].fillna('').astype(str)
    vectorizer = TfidfVectorizer(stop_words='english', max_features=50000, min_df=1)
    matrix = vectorizer.fit_transform(pd.concat([resume_text, job_text], ignore_index=True))
    cv_pos = {key:i for i,key in enumerate(cv.index)}
    job_pos = {key:i+len(cv) for i,key in enumerate(job_text.index)}
    pairs['tfidf_similarity'] = [float(cosine_similarity(matrix[cv_pos[c]], matrix[job_pos[j]])[0,0]) for c,j in zip(pairs.candidate_id,pairs.job_id)]
    cskills = cv.clean_skills.map(skills).to_dict()
    jskills = jobs.loc[job_text.index,'clean_skills'].map(skills).to_dict()
    pairs['skill_overlap'] = [len(cskills[c] & jskills[j]) / len(jskills[j]) if jskills[j] else 0.0 for c,j in zip(pairs.candidate_id,pairs.job_id)]
    # Fixed, transparent illustrative baseline, not optimized against reference labels.
    pairs['predicted_score'] = .7*pairs.tfidf_similarity + .3*pairs.skill_overlap
    scores=[]
    for cand,group in pairs.groupby('candidate_id'):
        if len(group)<2: continue
        truth=group.final_score.to_numpy(dtype=float)
        pred=group.predicted_score.to_numpy(dtype=float)
        rho = spearmanr(truth,pred).statistic if np.std(truth)>0 and np.std(pred)>0 else np.nan
        scores.append({'candidate_id':cand,'pairs':len(group),
                       'spearman':rho,
                       'ndcg_at_5':ndcg_score([truth],[pred],k=min(5,len(group))),
                       'top_1_agreement':bool(group.iloc[int(np.argmax(truth))].job_id == group.iloc[int(np.argmax(pred))].job_id)})
    summary=pd.DataFrame(scores)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    pairs.to_csv(out/'ranking_pair_predictions.csv',index=False)
    summary.to_csv(out/'ranking_metrics_by_candidate.csv',index=False)
    print(f'Valid pairs: {len(pairs)} | candidates evaluated: {len(summary)}')
    if len(summary):
        for col in ['spearman','ndcg_at_5','top_1_agreement']:
            print(f'{col}: {summary[col].mean():.4f}')
    print('NOTE: Reference scores are precomputed proxies; agreement is not independent human relevance validation.')
    return pairs,summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--cv',default='data/sample/small_cv.csv')
    parser.add_argument('--jobs',default='data/raw/job.csv')
    parser.add_argument('--matches',default='data/raw/matches.csv')
    parser.add_argument('--output',default='reports/ranking_validation')
    args=parser.parse_args()
    validate(args.cv,args.jobs,args.matches,args.output)
