// UI wording only. The engine's skill lists and calculations remain unchanged.
const guidance = {
  'node.js': {title: 'Node.js', text: 'If you have used Node.js, describe an API or application you built. Otherwise, consider practicing with a small backend project.'},
  sql: {title: 'SQL', text: 'If you have used SQL, describe how you queried or analyzed data. Otherwise, practice filtering, joins, and aggregations.'},
  testing: {title: 'Testing', text: 'If you have testing experience, mention the tools and types of tests you wrote. Otherwise, practice writing tests for a small project.'},
  python: {title: 'Python', text: 'If you have used Python, describe a script, analysis or application you worked on. Otherwise, practice with a small project using sample data.'},
  javascript: {title: 'JavaScript', text: 'If you have used JavaScript, describe an interactive feature or application you built. Otherwise, practice adding an interaction to a small web page.'},
  git: {title: 'Git', text: 'If you have used Git, describe how you tracked changes or collaborated on a project. Otherwise, practice commits, branches and merging in a small repository.'},
};

export function getSkillGuidance(skill) {
  const specific = Object.hasOwn(guidance, skill) ? guidance[skill] : null;
  return {
    title: specific?.title ?? skill,
    context: 'Mentioned in the job description; not found in your resume.',
    advice: specific?.text ?? `If you have used ${skill}, add truthful evidence from a relevant project or responsibility. Otherwise, consider learning and practicing it.`,
  };
}
