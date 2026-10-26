import {useEffect, useRef, useState} from 'react';
import {loadEngine} from './model.js';
import {parseResume} from './parsing/documents.js';
import ResumeInput from './components/ResumeInput.jsx';
import JobDescriptionInput from './components/JobDescriptionInput.jsx';
import AnalysisResults from './components/AnalysisResults.jsx';
import Icon from './components/Icon.jsx';

const EXAMPLE = {
  resume: 'Synthetic example — not a real resume.\n\nI build small applications with Python and JavaScript (JS). In a personal project, I used SQL to organize sample data and Git to track changes. I practice explaining technical work clearly and collaborating on projects.',
  job: 'Synthetic example — not a real job posting.\n\nJunior Software Developer\nBuild and maintain small applications using Python, JavaScript, SQL and Node.js. Use Git for version control, troubleshoot issues, and communicate with the team. The role also mentions software development and testing.',
};

export default function App() {
  const [resume, setResume] = useState(''), [job, setJob] = useState('');
  const [file, setFile] = useState(''), [parsing, setParsing] = useState({state: 'idle', message: ''});
  const [model, setModel] = useState({state: 'loading', engine: null}), [retry, setRetry] = useState(0);
  const [result, setResult] = useState(null), [analysis, setAnalysis] = useState('idle'), [error, setError] = useState('');
  const parseVersion = useRef(0), inputVersion = useRef(0), mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; parseVersion.current++; }; }, []);
  useEffect(() => {
    let active = true;
    setModel({state: 'loading', engine: null});
    loadEngine().then(engine => { if (active) setModel({state: 'ready', engine}); }).catch(() => { if (active) setModel({state: 'error', engine: null}); });
    return () => { active = false; };
  }, [retry]);
  function invalidate() { inputVersion.current++; setResult(null); setError(''); setAnalysis('idle'); }
  function editResume(value) { parseVersion.current++; setParsing({state: 'idle', message: file ? 'Text edited. Review your changes before analyzing.' : ''}); setResume(value); invalidate(); }
  function clearResume() { parseVersion.current++; setResume(''); setFile(''); setParsing({state: 'idle', message: ''}); invalidate(); }
  async function readFile(selected) {
    const version = ++parseVersion.current;
    setFile(selected.name); setParsing({state: 'reading', message: 'Reading your document…'}); setResume(''); invalidate();
    try {
      const text = await parseResume(selected);
      if (!mounted.current || version !== parseVersion.current) return;
      setResume(text); invalidate(); setParsing({state: 'ready', message: 'Text extracted. Review and edit it below.'});
    } catch (failure) {
      if (!mounted.current || version !== parseVersion.current) return;
      setParsing({state: 'error', message: failure.message});
    }
  }
  function clearAll() { clearResume(); setJob(''); }
  function loadExample() { parseVersion.current++; setResume(EXAMPLE.resume); setJob(EXAMPLE.job); setFile(''); setParsing({state: 'idle', message: 'Synthetic example loaded. You can edit it freely.'}); invalidate(); }
  async function analyze(event) {
    event.preventDefault();
    if (!resume.trim() || !job.trim()) { setError('Add both your resume text and the job description before analyzing.'); return; }
    if (model.state !== 'ready') { setError('Wait for the analyzer to load, or retry loading it below.'); return; }
    const version = inputVersion.current;
    setAnalysis('running'); setResult(null); setError('');
    await new Promise(resolve => requestAnimationFrame(() => setTimeout(resolve, 0)));
    if (!mounted.current || version !== inputVersion.current) return;
    try {
      const output = model.engine.analyze(resume, job);
      // Keep model diagnostics and internal scores out of application state and UI.
      const {diagnostics, model_features, classifier_score, ...feedback} = output;
      if (version === inputVersion.current) { setResult(feedback); setAnalysis('complete'); }
    } catch (failure) { setError(failure.message); setAnalysis('idle'); }
  }
  return <>
    <a className="skip-link" href="#analyzer">Skip to analyzer</a>
    <header className="site-header"><div className="header-inner"><a className="brand" href="#analyzer"><span className="brand-mark"><Icon name="document" size={24}/></span><span>Resume Skill Gap Analyzer<span className="brand-subtitle">A clearer next step</span></span></a><nav aria-label="Main navigation"><a href="#analyzer" className="active">Analyzer</a><a href="#how-it-works">How it works <span aria-hidden="true">↗</span></a></nav></div></header>
    <main>
      <section className="intro"><div><span className="eyebrow"><span className="tiny-line"/>FROM EXPERIENCE TO OPPORTUNITY</span><h1>See where your skills<br className="desktop-break"/> meet your next role.</h1><p>Compare your resume with a job description and see which skills to highlight or develop.</p></div><div className="privacy-note"><span className="privacy-icon"><Icon name="shield" size={23}/></span><div><strong>Your documents stay with you</strong><p>Text is processed in this browser.<br/>No uploads to a server. No account needed.</p></div></div></section>
      <form id="analyzer" onSubmit={analyze} noValidate>
        <div className="workspace-heading"><h2>Build your comparison</h2><span>Two texts. A practical starting point.</span></div>
        <div className="workspace"><ResumeInput value={resume} onChange={editResume} onFile={readFile} onClear={clearResume} file={file} parsing={parsing}/><JobDescriptionInput value={job} onChange={value => {setJob(value); invalidate();}}/></div>
        <div className="action-bar"><div className="secondary-actions"><button type="button" className="button button-outline" onClick={loadExample}><Icon name="spark" size={16}/>Load example</button><button type="button" className="button button-quiet" onClick={clearAll}>Clear all</button></div><div className="analyze-action"><span>Ready when you are.</span><button className="button button-primary" type="submit" disabled={model.state !== 'ready' || parsing.state === 'reading' || analysis === 'running'}>{analysis === 'running' ? 'Analyzing…' : 'Analyze resume'}<Icon name="arrow" size={18}/></button></div></div>
        <div className="status-row"><span className={`status-dot ${model.state}`}/><span role="status" aria-live="polite">{model.state === 'ready' ? 'Analyzer ready · Processing stays on your device' : model.state === 'loading' ? 'Loading the analyzer…' : 'The analyzer could not load. Check your connection and try again.'}</span>{model.state === 'error' && <button className="text-button" type="button" onClick={() => setRetry(value => value + 1)}>Retry loading</button>}</div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <span className="visually-hidden" role="status" aria-live="polite">{analysis === 'running' ? 'Analysis in progress.' : analysis === 'complete' ? 'Analysis complete. Results are below.' : 'Results will appear after analysis.'}</span>
      </form>
      {result ? <AnalysisResults result={result}/> : <section className="results-placeholder" aria-label="Results placeholder"><span className="placeholder-icon"><Icon name="document" size={23}/></span><div><h2>Your next steps start here</h2><p>Add both texts and analyze to explore matched skills, gaps and practical suggestions.</p></div></section>}
      <section id="how-it-works" className="how-it-works"><details><summary>How this comparison works <span aria-hidden="true">+</span></summary><div className="how-grid"><p><strong>1. Add your context</strong>Add your resume and the job description, then review both texts.</p><p><strong>2. Explore the comparison</strong>Review the assessment, shared vocabulary and skills identified in each text.</p><p><strong>3. Choose your next step</strong>Highlight relevant experience or choose a skill to develop.</p></div></details></section>
      <section id="methodology" className="how-it-works"><details><summary>Methodology <span aria-hidden="true">+</span></summary><p>Read about the assessment approach, evaluation and limitations in the <a className="text-button" href={`${import.meta.env.BASE_URL}methodology.html`}>project methodology</a>.</p></details></section>
    </main>
    <footer><div><strong>Resume Skill Gap Analyzer</strong><p>Explore how your experience connects with a role.</p></div><a className="text-button" href="#methodology">Methodology</a></footer>
  </>;
}
