import {spawnSync} from 'node:child_process';
const c=spawnSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\n\n',encoding:'utf8',env:{...process.env,GIT_TERMINAL_PROMPT:'0',GCM_INTERACTIVE:'never'}});
const row=c.stdout.split('\n').find(l=>l.startsWith('password='));
const headers={Accept:'application/vnd.github+json','User-Agent':'project-upload-review','X-GitHub-Api-Version':'2022-11-28'};if(row)headers.Authorization=`Bearer ${row.slice(9)}`;
for(const path of ['/repos/nhahub/NHA-5-189','/repos/nhahub/NHA-5-189/pages','/repos/nhahub/NHA-5-189/actions/workflows']){
 const r=await fetch('https://api.github.com'+path,{headers});const b=await r.json();
 console.log(JSON.stringify({path,status:r.status,...(path.endsWith('/NHA-5-189')?{default_branch:b.default_branch,private:b.private,permissions:b.permissions,has_pages:b.has_pages}:path.endsWith('/pages')?{html_url:b.html_url,cname:b.cname,build_type:b.build_type}:{workflows:b.workflows?.map(w=>({name:w.name,path:w.path,state:w.state})),message:b.message})}));
}
