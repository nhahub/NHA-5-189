export default function SkillList({skills, tone = '', empty}) {
  return skills.length ? <ul className={`skill-list ${tone}`}>{skills.map(skill => <li key={skill}>{skill}</li>)}</ul> : <p className="empty-note">{empty}</p>;
}
