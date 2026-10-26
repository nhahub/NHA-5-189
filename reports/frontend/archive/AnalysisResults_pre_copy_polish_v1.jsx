import {useEffect, useRef} from 'react';
import SkillList from './SkillList.jsx';
import ImprovementSuggestions from './ImprovementSuggestions.jsx';
const percent = value => `${(value * 100).toFixed(1)}%`;
export default function AnalysisResults({result}) {
  const heading = useRef(null);
  useEffect(() => { heading.current?.focus({preventScroll: true}); }, [result]);
  const hasJobSkills = result.job_skills.length > 0;
  return <section className="results" aria-labelledby="results-title">
    <div className="results-heading"><div><span className="eyebrow">YOUR COMPARISON</span><h2 id="results-title" ref={heading} tabIndex={-1}>A clearer view of your skill evidence</h2></div><span className="complete-tag">Analysis complete</span></div>
    <div className="metrics">
      <article className="metric assessment"><span className="metric-label">Model assessment</span><h3>{result.model_classification}</h3><p>An experimental estimate based on this text comparison, not a hiring decision.</p></article>
      <article className="metric"><span className="metric-label">Job-skill coverage</span><strong>{result.job_skill_coverage === null ? 'Unavailable' : percent(result.job_skill_coverage)}</strong><p>{hasJobSkills ? 'Recognized job skills also found in your resume.' : 'Insufficient extracted job-skill evidence. This is not a confirmed mismatch.'}</p></article>
      <article className="metric"><span className="metric-label">TF-IDF text similarity</span><strong>{percent(result.tfidf_text_similarity)}</strong><p>Shared vocabulary between the two texts. Separate from skill coverage and model assessment.</p></article>
    </div>
    <div className="result-card">
      <div className="skill-columns"><section><div className="skill-heading"><h3>Matched skills</h3><span className="count teal">{result.matched_skills.length}</span></div><p>Mentioned in both texts.</p><SkillList skills={result.matched_skills} tone="matched" empty="No matched skills found."/></section>
      <section><div className="skill-heading"><h3>Not found in your resume</h3><span className="count amber">{result.job_skills_not_found.length}</span></div><p>Job mentions to review, not confirmed missing abilities.</p><SkillList skills={result.job_skills_not_found} tone="missing" empty={hasJobSkills ? 'No detected skill gaps within the recognized dictionary.' : 'No job skills detected.'}/></section></div>
      <p className="evidence-note">{result.skill_evidence_note} An empty gap list does not establish that every job requirement is met.</p>
      <ImprovementSuggestions suggestions={result.suggestions} hasJobSkills={hasJobSkills}/>
      <div className="extracted"><details><summary>Extracted resume skills <span>{result.resume_skills.length}</span></summary><SkillList skills={result.resume_skills} empty="No resume skills detected."/></details><details><summary>Extracted job skills <span>{result.job_skills.length}</span></summary><SkillList skills={result.job_skills} empty="No job skills detected."/></details></div>
    </div>
  </section>;
}
