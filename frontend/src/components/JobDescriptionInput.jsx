import Icon from './Icon.jsx';
export default function JobDescriptionInput({value, onChange}) {
  return <section className="input-card job-card" aria-labelledby="job-title">
    <div className="card-heading"><span className="card-icon"><Icon name="briefcase"/></span><div><h2 id="job-title">The opportunity</h2><p>The role you want to explore.</p></div><span className="step-tag">02</span></div>
    <div className="job-intro"><span className="small-kicker">WHAT TO INCLUDE</span><p>Paste the full job description, including the responsibilities, skills and qualifications.</p></div>
    <div className="label-row"><label htmlFor="job-text">Job description</label><span>Required</span></div>
    <textarea id="job-text" value={value} onChange={event => onChange(event.target.value)} placeholder={'Paste the job description here…\n\nInclude the skills and responsibilities mentioned in the posting.'} spellCheck="false" aria-describedby="job-hint"/>
    <div className="input-bottom"><span id="job-hint">More context makes the comparison more useful.</span><span>{value.length.toLocaleString()} characters</span></div>
  </section>;
}
