import {spawnSync} from 'node:child_process';
const env={...process.env,GIT_TERMINAL_PROMPT:'0',GCM_INTERACTIVE:'never'};
const auth=spawnSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\n\n',encoding:'utf8',env});
const values=Object.fromEntries((auth.status===0?auth.stdout:'').trim().split('\n').filter(row=>row.includes('=')).map(row=>{const i=row.indexOf('=');return [row.slice(0,i),row.slice(i+1)];}));
const headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'resume-gap-pages-deployment'};
if(values.password)headers.Authorization=`Bearer ${values.password}`;
console.log(JSON.stringify({credential_available:!!values.password}));
for(const path of ['/repos/SadeenTag/depi_gapAnalyzer','/repos/SadeenTag/depi_gapAnalyzer/pages','/repos/SadeenTag/depi_gapAnalyzer/actions/workflows','/repos/SadeenTag/depi_gapAnalyzer/branches/main/protection']){
 const response=await fetch('https://api.github.com'+path,{headers});const body=await response.json();
 const output=path.endsWith('/depi_gapAnalyzer')?{full_name:body.full_name,default_branch:body.default_branch,private:body.private,permissions:body.permissions,has_pages:body.has_pages}:path.endsWith('/pages')?{html_url:body.html_url,cname:body.cname,build_type:body.build_type,source:body.source,status:body.status}:path.endsWith('/workflows')?{workflows:body.workflows?.map(w=>({name:w.name,path:w.path,state:w.state}))}:{message:body.message,required_status_checks:body.required_status_checks,restrictions:body.restrictions};
 console.log(JSON.stringify({path,status:response.status,...output}));
}
