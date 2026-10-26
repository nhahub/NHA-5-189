import {useRef} from 'react';
import Icon from './Icon.jsx';

export default function ResumeInput({value, onChange, onFile, onClear, file, parsing}) {
  const picker = useRef(null);
  return <section className="input-card" aria-labelledby="resume-title">
    <div className="card-heading"><span className="card-icon"><Icon name="document"/></span><div><h2 id="resume-title">Your resume</h2><p>A little context about your experience.</p></div><span className="step-tag">01</span></div>
    <div className="upload-area">
      <span className="upload-icon"><Icon name="upload" size={22}/></span>
      <div><strong>Start with your resume</strong><p>TXT, DOCX or text-based PDF · Up to 10 MB</p></div>
      <button type="button" className="button button-small button-outline" onClick={() => picker.current.click()}>Choose file</button>
      <input ref={picker} className="visually-hidden" type="file" accept=".txt,.docx,.pdf" tabIndex={-1} aria-label="Choose resume file" onChange={event => { const selected = event.target.files[0]; event.target.value = ''; if (selected) onFile(selected); }}/>
    </div>
    <div className={`file-status ${parsing.state === 'error' ? 'error-text' : ''}`} aria-live="polite" aria-atomic="true">
      {file && <span className="filename">{file}</span>}
      <span>{parsing.message || 'Or paste your resume below. You can edit extracted text.'}</span>
      {(file || value) && <button type="button" className="text-button" onClick={onClear}>Clear resume</button>}
    </div>
    <div className="label-row"><label htmlFor="resume-text">Resume text</label><span>Editable</span></div>
    <textarea id="resume-text" value={value} onChange={event => onChange(event.target.value)} placeholder="Paste your experience, projects, education and skills here…" spellCheck="false" aria-describedby="resume-hint"/>
    <div className="input-bottom"><span id="resume-hint">Review extracted text before analyzing.</span><span>{value.length.toLocaleString()} characters</span></div>
  </section>;
}
