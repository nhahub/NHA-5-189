import pandas as pd

cv = pd.read_csv("data/small_cv.csv")
jobs = pd.read_csv("data/small_jobs.csv")

print("----- RESUME -----")
print(cv.loc[0, "resume_text"])

print("\n----- JOB DESCRIPTION -----")
print(jobs.loc[0, "job_description"])