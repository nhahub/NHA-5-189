import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createInference} from '../frontend/src/inference/milestone3.mjs';
const base=new URL(process.argv[2]);
if(base.hostname!=='sadeentag.github.io'||base.pathname!=='/depi_gapAnalyzer/')throw new Error('Unexpected deployment URL');
const checked=[];
async function get(url){const res=await fetch(url,{cache:'no-store'});const bytes=Buffer.from(await res.arrayBuffer());checked.push({url:String(url),status:res.status,bytes:bytes.length,content_type:res.headers.get('content-type')});assert.equal(res.status,200,String(url));return bytes;}
const html=(await get(base)).toString('utf8');assert.ok(html.includes('Resume Skill Gap Analyzer'));
const queue=[...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(m=>new URL(m[1],base));
const seen=new Set();let worker=false,pdf=false,docx=false;
while(queue.length){const url=queue.shift();if(seen.has(String(url)))continue;seen.add(String(url));assert.equal(url.origin,base.origin);assert.ok(url.pathname.startsWith(base.pathname));const data=await get(url);worker ||= /pdf\.worker.*\.mjs/.test(url.pathname);pdf ||= /\/pdf-[^.]+\.js/.test(url.pathname);docx ||= /mammoth\.browser/.test(url.pathname);
 if(/\.(?:m?js)$/.test(url.pathname)){
  const source=data.toString('utf8');
  for(const match of source.matchAll(/(?:assets\/|\.\/)[A-Za-z0-9._-]+\.(?:mjs|js|css)/g))queue.push(match[0].startsWith('assets/')?new URL(match[0],base):new URL(match[0],url));
 }
}
assert.ok(worker&&pdf&&docx,'Worker and parsing assets must resolve');
const model=await get(new URL('models/milestone3/v1/assets.json',base));const sha=createHash('sha256').update(model).digest('hex');
const contract=JSON.parse(readFileSync('frontend/tests/model-contract.json','utf8'));assert.equal(sha,contract.assets_sha256);
assert.equal((await get(new URL('methodology.html',base))).toString('utf8').includes('Methodology and limitations'),true);
const engine=createInference(JSON.parse(model));const references=JSON.parse(readFileSync('frontend/tests/fixtures/synthetic-python-references.json','utf8'));
for(const ref of references){const result=engine.analyze(ref.resume,ref.job);assert.equal(result.model_classification,ref.expected.model_classification);for(const key of ['resume_skills','job_skills','matched_skills','job_skills_not_found'])assert.deepEqual(result[key],ref.expected[key]);for(const [key,value]of Object.entries(ref.expected.model_features))assert.ok(Math.abs(result.model_features[key]-value)<=1e-8+1e-7*Math.abs(value));}
const excluded=[];for(const path of ['tests/browser.html','src/main.jsx','data/raw/cv.csv','models/milestone3/v2/logistic_regression.joblib']){const response=await fetch(new URL(path,base));excluded.push({path,status:response.status});assert.equal(response.status,404,path);}
const result={site_url:String(base),checked,model_sha256:sha,local_node_inference_using_live_model:{synthetic_reference_cases:references.length,exact_classifications:true,exact_skill_lists:true,features_within_tolerance:true},parsing_assets_resolved:{pdf_worker:worker,pdf_chunk:pdf,docx_chunk:docx},excluded_paths:excluded,actual_browser_interactions:'not performed',checked_at_utc:new Date().toISOString()};
writeFileSync('.deployment-work/live-verification.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
