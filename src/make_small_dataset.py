import pandas as pd

cv = pd.read_csv("data/cv.csv")
jobs = pd.read_csv("data/job.csv")
matches = pd.read_csv("data/matches.csv")

# Take a small sample
small_cv = cv.head(30)
small_jobs = jobs.head(10)

# Keep only matches related to those selected CVs and jobs
small_matches = matches[
    matches["candidate_id"].isin(small_cv["candidate_id"]) &
    matches["job_id"].isin(small_jobs["job_id"])
]

# Save them as new files
small_cv.to_csv("data/small_cv.csv", index=False)
small_jobs.to_csv("data/small_jobs.csv", index=False)
small_matches.to_csv("data/small_matches.csv", index=False)

print("Small dataset created successfully.")
print("CVs:", small_cv.shape)
print("Jobs:", small_jobs.shape)
print("Matches:", small_matches.shape)