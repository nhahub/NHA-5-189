import pandas as pd

cv = pd.read_csv("data/cv.csv")
jobs = pd.read_csv("data/job.csv")
matches = pd.read_csv("data/matches.csv")

print("CV shape:", cv.shape)
print("Jobs shape:", jobs.shape)
print("Matches shape:", matches.shape)

print("\nCV columns:")
print(cv.columns.tolist())

print("\nJob columns:")
print(jobs.columns.tolist())

print("\nMatches columns:")
print(matches.columns.tolist())