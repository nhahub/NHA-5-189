// UI wording only. The engine's skill lists and calculations remain unchanged.
const guidance = {
  'node.js': {title: 'Node.js', text: 'If you have Node.js experience, highlight a relevant application or API project. Otherwise, consider developing this skill through a practical project.'},
  sql: {title: 'SQL', text: 'If you have SQL experience, highlight how you queried or analyzed data. Otherwise, practice filtering, joins, and aggregations.'},
  testing: {title: 'Testing', text: 'If you have testing experience, mention the tools and types of tests you wrote. Otherwise, practice writing tests for a small project.'},
  python: {title: 'Python', text: 'If you have Python experience, highlight a relevant script, analysis or application. Otherwise, practice with a small project using sample data.'},
  javascript: {title: 'JavaScript', text: 'If you have JavaScript experience, highlight an interactive feature or application. Otherwise, practice adding an interaction to a small web page.'},
  git: {title: 'Git', text: 'If you have used Git, highlight how you tracked changes or collaborated. Otherwise, practice commits, branches and merging in a small repository.'},
};

export function getSkillGuidance(skill) {
  const specific = Object.hasOwn(guidance, skill) ? guidance[skill] : null;
  return {
    title: specific?.title ?? skill,
    advice: specific?.text ?? `If you have experience with ${skill}, highlight a relevant project or responsibility. Otherwise, consider developing this skill through practice.`,
  };
}
