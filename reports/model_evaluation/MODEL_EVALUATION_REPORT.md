# Model Evaluation Report
## AI-Powered Resume–Job Skill Gap Analyzer

### 1. Introduction
This report evaluates the performance of the resume–job skill extraction and matching system developed during Milestone 2.

The evaluation covers skill extraction, text similarity, and ranking validation.

### 2. Skill Extraction Evaluation

The skill extraction module uses spaCy EntityRuler and a predefined skills dictionary to identify technical and soft skills.

The reported results after dictionary optimization are:

| Metric | Score |
|---|---:|
| Precision | 0.57 |
| Recall | 0.96 |
| F1-score | 0.70 |

The system demonstrates high recall, indicating that it identifies a large proportion of the expected skills. However, its lower precision indicates that some extracted terms are false positives.

### 3. Similarity Scoring

The system uses TF-IDF to represent resume and job-description text numerically and cosine similarity to measure textual similarity.

The ranking-validation baseline combines:

- TF-IDF cosine similarity: 70%
- Skill overlap: 30%

These weights describe the validation baseline and should not be interpreted as experimentally optimized weights.

### 4. Ranking Validation

Ranking predictions were compared with precomputed reference match scores.

| Evaluation Metric | Result |
|---|---:|
| Valid resume-job pairs | 348 |
| Candidates evaluated | 30 |
| Spearman correlation | 0.1809 |
| NDCG@5 | 0.9696 |
| Top-1 ranking agreement | 30% |

**Interpretation:**

- Spearman correlation indicates weak positive agreement between predicted and reference rankings.
- NDCG@5 indicates high relevance-weighted ranking performance relative to the available reference scores.
- Top-1 agreement indicates that 9 of 30 candidates received the same highest-ranked job as the reference ranking.

The reference scores are precomputed proxies rather than independently verified human relevance labels.

### 5. Limitations

- Skill extraction produces some false positives.
- Dictionary-based extraction may miss unfamiliar skills and equivalent terminology.
- TF-IDF relies primarily on lexical overlap rather than contextual meaning.
- Ranking validation currently covers only 30 candidates.
- Full-dataset validation and independent human relevance assessment remain future evaluation requirements.

### 6. Conclusion

Milestone 2 established a functional skill extraction and similarity-scoring baseline.

The evaluation highlights strong skill-extraction recall and limitations in precision and ranking agreement.

Milestone 3 will investigate sentence-transformer embeddings, contextual language models, skill equivalence, and semantic matching to address these limitations.

Any performance improvement must be demonstrated through comparative evaluation rather than assumed.