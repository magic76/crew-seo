import {readFile,unlink} from 'node:fs/promises';
import {join} from 'node:path';
const endpoint='https://hicrewapps.com/api/private-gsc';
let stage='config',httpStatus=null;
const path=join(process.env.RUNNER_TEMP??'','affiliate-gsc.json');
try{
 if(process.env.GITHUB_REPOSITORY!=='magic76/crew-seo'||process.env.GITHUB_REF!=='refs/heads/main'||!process.env.RUNNER_TEMP)throw Error('Not authorized');
 const body=await readFile(path,'utf8');if(Buffer.byteLength(body)>128*1024||JSON.parse(body).property!=='sc-domain:hicrewapps.com')throw Error('Invalid report');
 stage='deployment-ready';const ready=await fetch(endpoint,{method:'HEAD',redirect:'error',signal:AbortSignal.timeout(20000)});httpStatus=ready.status;if(ready.status!==204)throw Error('Unavailable');
 stage='identity';const url=new URL(process.env.ACTIONS_ID_TOKEN_REQUEST_URL);if(url.protocol!=='https:')throw Error('Invalid token endpoint');url.searchParams.set('audience',endpoint);
 const identity=await fetch(url,{headers:{Authorization:'Bearer '+process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN},redirect:'error',signal:AbortSignal.timeout(10000)});httpStatus=identity.status;if(!identity.ok)throw Error('OIDC unavailable');const jwt=(await identity.json()).value;
 stage='private-upload';const res=await fetch(endpoint,{method:'POST',redirect:'error',headers:{Authorization:'Bearer '+jwt,'Content-Type':'application/json'},body,signal:AbortSignal.timeout(20000)});httpStatus=res.status;
 if(!res.ok||(await res.json()).ok!==true)throw Error('Upload failed');
 console.log('Affiliate GSC private upload verified. No report data logged.');
}catch{console.error('Affiliate GSC upload failed at '+stage+(httpStatus?' HTTP '+httpStatus:''));process.exitCode=1;}finally{if(process.env.RUNNER_TEMP)await unlink(path).catch(()=>{});}
