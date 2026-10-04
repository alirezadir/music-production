#!/usr/bin/env python3
"""remake-stems: LALAL.AI API v1 production stem pipeline."""
import argparse, os, sys, time
from pathlib import Path
import requests

API="https://www.lalal.ai/api/v1/"
MODELS=("auto","orion","perseus","phoenix","andromeda")
LEVELS=("deep_extraction","clear_cut")

def api(method,path,key,timeout,**kw):
    h=kw.pop("headers",{}); h["X-License-Key"]=key
    r=requests.request(method,API+path,headers=h,timeout=timeout,**kw)
    if r.status_code!=200: raise RuntimeError(f"{path}: HTTP {r.status_code}: {r.text}")
    return r.json()

def upload(path,key,timeout):
    with path.open("rb") as f:
        d=api("POST","upload/",key,timeout,
              headers={"Content-Disposition":f'attachment; filename="{path.name}"'},data=f)
    return d["id"]

def start(source,stem,key,model,level,dereverb,timeout):
    p={"stem":stem,"extraction_level":level,"splitter":model}
    if dereverb: p["dereverb_enabled"]=True
    return api("POST","split/stem_separator/",key,timeout,
               json={"source_id":source,"presets":p})["task_id"]

def wait(task,key,timeout,poll,quiet):
    while True:
        d=api("POST","check/",key,timeout,json={"task_ids":[task]})
        s=d["result"][task]; status=s.get("status")
        if status=="success": return s["result"]["tracks"]
        if status=="cancelled": raise RuntimeError(f"Task {task} cancelled")
        if status!="progress": raise RuntimeError(f"Unknown task status: {status}")
        if not quiet: print(f"      progress: {int(s.get('progress',0))}%")
        time.sleep(poll)

def norm(x): return str(x).strip().lower().replace("-","_").replace(" ","_")

def pair(tracks,stem):
    aliases={"vocals":{"vocals","vocal"},"drum":{"drum","drums"},"bass":{"bass"}}[stem]
    hit=[t for t in tracks if norm(t.get("label")) in aliases]
    if len(hit)!=1:
        raise RuntimeError(f"Cannot identify {stem} from API labels: {[t.get('label') for t in tracks]}")
    rest=[t for t in tracks if t is not hit[0]]
    if len(rest)!=1:
        raise RuntimeError(f"Expected exactly one complement; labels: {[t.get('label') for t in tracks]}")
    return hit[0],rest[0]

def download(track,dst,timeout,overwrite):
    if dst.exists() and not overwrite:
        raise RuntimeError(f"Output exists: {dst} (use --overwrite or --resume)")
    tmp=Path(str(dst)+".part"); dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        with requests.get(track["url"],stream=True,timeout=timeout) as r:
            if r.status_code!=200: raise RuntimeError(f"Download HTTP {r.status_code}")
            with tmp.open("wb") as f:
                for c in r.iter_content(1024*1024):
                    if c: f.write(c)
        tmp.replace(dst)
    finally:
        if tmp.exists(): tmp.unlink()

def split(inp,stem,a,b,args,key):
    source=None
    try:
        if not args.quiet: print(f"      upload {inp.name}")
        source=upload(inp,key,args.timeout)
        task=start(source,stem,key,args.splitter,args.extraction_level,args.dereverb,args.timeout)
        if not args.quiet: print(f"      task {task}")
        x,y=pair(wait(task,key,args.timeout,args.poll_interval,args.quiet),stem)
        if not args.quiet: print(f"      labels: {x.get('label')} + {y.get('label')}")
        download(x,a,args.timeout,args.overwrite)
        download(y,b,args.timeout,args.overwrite)
    finally:
        if args.delete_remote and source:
            try: api("POST","delete/",key,args.timeout,json={"source_id":source})
            except Exception as e:
                print(f"WARNING: remote cleanup failed: {e}",file=sys.stderr)

def parser():
    p=argparse.ArgumentParser(
      prog="remake-stems",
      description="Build deterministic remix/reconstruction stems with LALAL.AI API v1.",
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""Pipeline:
  1 input -> vocals + instrumental
  2 instrumental -> drums + instrumental_no_drums
  3 instrumental -> bass + instrumental_no_bass
  4 instrumental_no_drums -> secondary bass + instrumental_melodics

Examples:
  remake-stems "San-Francisco-HQ.wav"
  remake-stems song.wav -o ./stems --splitter andromeda
  remake-stems song.wav --resume --delete-remote
  remake-stems song.wav --extraction-level clear_cut
""")
    p.add_argument("input",type=Path,help="Input audio file")
    p.add_argument("-o","--output",type=Path,help="Output folder (default: <input parent>/<input stem>)")
    p.add_argument("--license",dest="license_key",help="License key; preferably set LALAL_LICENSE")
    p.add_argument("--splitter",choices=MODELS,default="auto",help="Stem-separator model (default: auto)")
    p.add_argument("--extraction-level",choices=LEVELS,default="deep_extraction")
    p.add_argument("--dereverb",action="store_true",help="Enable dereverb for all splits")
    p.add_argument("--delete-remote",action="store_true",help="Delete remote source/results after each stage")
    g=p.add_mutually_exclusive_group()
    g.add_argument("--overwrite",action="store_true",help="Replace existing outputs")
    g.add_argument("--resume",action="store_true",help="Reuse complete local stages")
    p.add_argument("--keep-secondary-bass",action="store_true",
                   help="Keep bass produced in step 4 (normally discarded)")
    p.add_argument("--poll-interval",type=float,default=5.0)
    p.add_argument("--timeout",type=int,default=60)
    p.add_argument("-q","--quiet",action="store_true")
    return p

def main():
    a=parser().parse_args(); inp=a.input.expanduser().resolve()
    if not inp.is_file(): sys.exit(f"ERROR: file not found: {inp}")
    key=a.license_key or os.getenv("LALAL_LICENSE")
    if not key: sys.exit("ERROR: set LALAL_LICENSE or pass --license")
    if a.poll_interval<=0 or a.timeout<=0: sys.exit("ERROR: timeout/poll must be > 0")
    base=inp.stem; ext=inp.suffix.lower() or ".wav"
    out=(a.output.expanduser().resolve() if a.output else inp.parent/base)
    out.mkdir(parents=True,exist_ok=True)
    f={
      "v":out/f"{base}_vocals_lalalai{ext}",
      "i":out/f"{base}_instrumental_lalalai{ext}",
      "d":out/f"{base}_drums_lalalai{ext}",
      "nd":out/f"{base}_instrumental_no_drums_lalalai{ext}",
      "b":out/f"{base}_bass_lalalai{ext}",
      "nb":out/f"{base}_instrumental_no_bass_lalalai{ext}",
      "m":out/f"{base}_instrumental_melodics_lalalai{ext}",
      "b2":out/f"{base}_bass_from_no_drums_lalalai{ext}"}
    done=lambda *k: all(f[x].is_file() for x in k)
    try:
        if not a.quiet: print(f"Remaking stems: {inp}\nOutput: {out}")
        print("\n[1/4] vocals + instrumental") if not a.quiet else None
        if not(a.resume and done("v","i")): split(inp,"vocals",f["v"],f["i"],a,key)
        print("\n[2/4] drums from instrumental") if not a.quiet else None
        if not(a.resume and done("d","nd")): split(f["i"],"drum",f["d"],f["nd"],a,key)
        print("\n[3/4] bass from instrumental") if not a.quiet else None
        if not(a.resume and done("b","nb")): split(f["i"],"bass",f["b"],f["nb"],a,key)
        print("\n[4/4] melodics from instrumental_no_drums") if not a.quiet else None
        if not(a.resume and done("m")):
            split(f["nd"],"bass",f["b2"],f["m"],a,key)
            if not a.keep_secondary_bass: f["b2"].unlink(missing_ok=True)
        if not a.quiet:
            print("\nDone:")
            for k in ("v","i","d","nd","b","nb","m"):
                print(f"  {f[k].name}")
        return 0
    except (RuntimeError,requests.RequestException,OSError,KeyError) as e:
        print(f"ERROR: {e}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
