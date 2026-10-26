import Icon from './Icon.jsx';
import {getSkillGuidance} from '../feedbackGuidance.js';
export default function ImprovementSuggestions({suggestions, hasJobSkills}) {
  return <section className="feedback-section" aria-labelledby="improvements-title">
    <div className="section-title"><Icon name="spark"/><div><h3 id="improvements-title">Recommended Improvements</h3><p>Choose a next step for each skill.</p></div></div>
    {suggestions.length ? <ol className="suggestion-list">{suggestions.map(suggestion => {
      const guidance = getSkillGuidance(suggestion.skill);
      return <li key={suggestion.skill}><h4>{guidance.title}</h4><p>{guidance.advice}</p></li>;
    })}</ol> : <p className="empty-note">{hasJobSkills ? 'No additional skill suggestions were identified.' : 'Add more job-description detail to explore skill gaps.'}</p>}
  </section>;
}
