import Icon from './Icon.jsx';
import {getSkillGuidance} from '../feedbackGuidance.js';
export default function ImprovementSuggestions({suggestions, hasJobSkills}) {
  return <section className="feedback-section" aria-labelledby="improvements-title">
    <div className="section-title"><Icon name="spark"/><div><h3 id="improvements-title">Make your experience visible</h3><p>Practical next steps, grounded in the skills mentioned.</p></div></div>
    {suggestions.length ? <ol className="suggestion-list">{suggestions.map(suggestion => {
      const guidance = getSkillGuidance(suggestion.skill);
      return <li key={suggestion.skill}><h4>{guidance.title}</h4><p className="gap-context">{guidance.context}</p><p>{guidance.advice}</p></li>;
    })}</ol> : <p className="empty-note">{hasJobSkills ? 'No detected skill gaps within the recognized dictionary. This does not confirm that you meet every job requirement.' : 'No job skills detected. Add more job-description detail to explore skill gaps.'}</p>}
  </section>;
}
