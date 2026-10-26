import {spawnSync} from 'node:child_process';
const knownRepo='SadeenTag/depi_gapAnalyzer';
const remote=spawnSync('git',['config','--get','remote.origin.url'],{encoding:'utf8'}).stdout.trim();
if(remote!==`https://github.com/${knownRepo}.git`)throw new Error('Remote changed; refusing deployment');
const auth=spawnSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\n\n',encoding:'utf8',env:{...process.env,GIT_TERMINAL_PROMPT:'0',GCM_INTERACTIVE:'never'}});
const values=Object.fromEntries((auth.status===0?auth.stdout:'').trim().split('\n').filter(x=>x.includes('=')).map(x=>{const i=x.indexOf('=');return[x.slice(0,i),x.slice(i+1)];}));
if(!values.password)throw new Error('GitHub authentication unavailable; authenticate with Git Credential Manager');
const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'resume-gap-pages-deployment','Authorization':`Bearer ${values.password}`};
const mode=process.argv[2]??'status';
async function api(path,options={}){const res=await fetch(`https://api.github.com/repos/${knownRepo}${path}`,{...options,headers:{...headers,...options.headers}});const body=res.status===204?{}:await res.json();return{status:res.status,body};}
if(mode==='configure'){
 let result=await api('/pages');
 if(result.status===404)result=await api('/pages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({build_type:'workflow'})});
 else if(result.status===200&&result.body.build_type!=='workflow')throw new Error('Existing Pages publishing source changed; review before replacing it');
 if(result.status!==200&&result.status!==201)throw new Error(`Pages configuration blocked: HTTP ${result.status}: ${result.body.message}`);
 console.log(JSON.stringify({http_status:result.status,html_url:result.body.html_url,cname:result.body.cname,build_type:result.body.build_type,source:result.body.source}));
}else if(mode==='status'){
 const pages=await api('/pages');console.log(JSON.stringify({kind:'pages',status:pages.status,html_url:pages.body.html_url,cname:pages.body.cname,build_type:pages.body.build_type}));
 const runs=await api('/actions/workflows/pages.yml/runs?per_page=5');
 console.log(JSON.stringify({kind:'runs',status:runs.status,runs:runs.body.workflow_runs?.map(r=>({id:r.id,head_sha:r.head_sha,status:r.status,conclusion:r.conclusion,html_url:r.html_url,created_at:r.created_at}))}));
}else if(mode==='jobs'){
 const result=await api(`/actions/runs/${process.argv[3]}/jobs`);console.log(JSON.stringify({status:result.status,jobs:result.body.jobs?.map(j=>({name:j.name,status:j.status,conclusion:j.conclusion,steps:j.steps?.map(s=>({name:s.name,status:s.status,conclusion:s.conclusion}))}))}));
}else if(mode==='deployment'){
 const deployments=await api('/deployments?environment=github-pages&per_page=5');
 if(deployments.status!==200)throw new Error(`Deployments unavailable: ${deployments.status}`);
 for(const deployment of deployments.body){const result=await api(`/deployments/${deployment.id}/statuses`);console.log(JSON.stringify({sha:deployment.sha,id:deployment.id,statuses:result.body.map(s=>({state:s.state,environment_url:s.environment_url,log_url:s.log_url}))}));}
}else throw new Error('Unknown mode');
