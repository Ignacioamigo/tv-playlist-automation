#!/usr/bin/env python3
"""Inspect already resolved IPFS snapshots using an isolated local Kubo binary."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'.research/tools'
env=dict(os.environ,IPFS_PATH=str(base/'repo'))
binary=base/'ipfs'
def run(args,timeout=25):
    return subprocess.run([str(binary),*args],env=env,capture_output=True,text=True,timeout=timeout)


def main():
    records=json.loads((ROOT/'research/ipns-native.json').read_text())['results']
    roots={r['resolved']:r['name'] for r in records if r.get('resolved')}
    reports=[]
    directory=ROOT/'.research/ipfs';directory.mkdir(parents=True,exist_ok=True)
    log=(base/'daemon.log').open('a')
    daemon=subprocess.Popen([str(binary),'daemon','--migrate=false'],env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        for _ in range(40):
            if (base/'repo/api').exists():break
            if daemon.poll() is not None:raise RuntimeError('daemon stopped')
            time.sleep(.25)
        def inspect(item):
            root,name=item
            queue=[(root,0)]
            report={'name':name,'root':root,'listings':[],'files':[]}
            while queue and len(report['listings'])<8:
                path,depth=queue.pop(0)
                try: result=run(['--timeout=15s','ls',path],20)
                except subprocess.TimeoutExpired:continue
                report['listings'].append({'path':path,'output':result.stdout[:20000],'error':result.stderr[:500]})
                for line in result.stdout.splitlines():
                    parts=line.split(maxsplit=2)
                    if len(parts)!=3:continue
                    cid,size,filename=parts
                    if filename.endswith('/'):
                        if depth<3:queue.append((path+'/'+filename.rstrip('/'),depth+1))
                    elif filename.lower().endswith(('.m3u','.m3u8','.json','.txt')) and size.isdigit() and int(size)<2097152 and len(report['files'])<20:
                        try: content=run(['--timeout=20s','cat','--length=2097152','/ipfs/'+cid],25)
                        except subprocess.TimeoutExpired:continue
                        if content.returncode==0:
                            target=directory/(root.split('/')[-1]+'-'+filename.replace('/','_'))
                            target.write_text(content.stdout)
                            record={'path':path+'/'+filename,'cid':cid,'file':str(target.relative_to(ROOT)),'bytes':len(content.stdout.encode()),'extinf_count':content.stdout.count('#EXTINF:')}
                            report['files'].append(record)
                            print(json.dumps(record),flush=True)
            return report
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:reports=list(pool.map(inspect,roots.items()))
    finally:
        daemon.terminate()
        try:daemon.wait(timeout=10)
        except subprocess.TimeoutExpired:daemon.kill();daemon.wait()
        log.close()
        (ROOT/'research/ipfs-files.json').write_text(json.dumps({'snapshots':reports,'daemon_stopped':True},ensure_ascii=False,indent=2)+'\n')
        print('Nodo detenido.',flush=True)


if __name__=='__main__':main()
