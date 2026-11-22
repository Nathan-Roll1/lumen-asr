from importlib.metadata import version
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys

from huggingface_hub import snapshot_download

rev = '71ad965f645275fd6b50ac730dcb91fb7154377f'
qa = {'platform':platform.platform(), 'machine':platform.machine(), 'hub_revision':rev,
      'product':'Lumen ASR v0.3.1 prerelease', 'python_runtime':version('mlx-qwen3-asr'), 'mlx':version('mlx')}
def save():
    Path('receipt.json').write_text(json.dumps(qa,indent=2)+'\n')
save()
exe = next(p for p in Path('mounted').glob('*.app/Contents/MacOS/*') if p.is_file())
raw = exe.read_bytes()
expected = Path('expected-worker.py').read_bytes()
pos = raw.find(expected)
assert pos>=0, (str(exe),len(raw),len(expected))
worker = raw[pos:pos+len(expected)].decode()
qa.update({'executable':exe.name,'worker_bytes':len(expected),'worker_sha256':hashlib.sha256(expected).hexdigest(),'embedded_worker_offset':pos})
save()
root=Path(snapshot_download('oruk/oruk-fourier-2b',revision=rev,
    allow_patterns=['mlx/8bit/*','onnx/sherpa-int8/tokenizer/merges.txt','onnx/sherpa-int8/tokenizer/vocab.json'],local_dir='download'))
folder=root/'mlx/8bit'
check='./target/debug/lumen-prerelease-model-chooser-check'
def ready():return subprocess.check_output([check,str(folder)],text=True).strip()=='true'
qa['unchanged_mlx_folder_accepted']=ready()
save()
assert not qa['unchanged_mlx_folder_accepted']
vocabdir=root/'onnx/sherpa-int8/tokenizer'
tokenizer=json.loads((folder/'tokenizer.json').read_text())['model']
assert tokenizer['vocab']==json.loads((vocabdir/'vocab.json').read_text())
raw_merges=[x for x in (vocabdir/'merges.txt').read_text().splitlines() if x and not x.startswith('#version:')]
mlx_merges=[' '.join(x) if isinstance(x,list) else x for x in tokenizer['merges']]
assert raw_merges==mlx_merges, (len(raw_merges),len(mlx_merges),raw_merges[:4],mlx_merges[:4])
qa['matched_vocab_tokens']=len(tokenizer['vocab'])
qa['matched_merges']=len(raw_merges)
for name in ('merges.txt','vocab.json'):shutil.copyfile(vocabdir/name,folder/name)
qa['accepted_with_original_tokenizer_files']=ready()
save()
assert qa['accepted_with_original_tokenizer_files']
# Lumen's product() invokes -u -c <embedded worker>. It uses audio_path in JSONL.
fixture=str(Path('jfk.wav').resolve())
request=json.dumps({'id':1,'audio_path':fixture})+'\n'
env=dict(os.environ, HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
with open('worker-stdout.jsonl','w') as out, open('worker-stderr.log','w') as err:
    p=subprocess.run([sys.executable,'-u','-c',worker,'--model',str(folder.resolve()),'--language','English'],input=request,text=True,stdout=out,stderr=err,env=env,timeout=360)
qa['worker_exitcode']=p.returncode
save()
print(Path('worker-stderr.log').read_text()[-4400:])
out=Path('worker-stdout.jsonl').read_text().strip()
print(out[:800])
res=json.loads(out.splitlines()[-1]) if out else {}
qa['worker_error']=res.get('error')
qa['transcription']=res.get('text')
qa['audio_fixture']='ggml-org/whisper.cpp samples/jfk.wav'
qa['worker_runtime_metrics']={key:res['qwen_metrics'].get(key) for key in ('runtime_version','decode_mode','finish_reason','worker_total_ms') } if res.get('qwen_metrics') else None
words=lambda x: re.findall(r"[a-z]+", x.lower())
ref='And so my fellow Americans ask not what your country can do for you ask what you can do for your country'
qa['reference_words']=len(words(ref))
qa['word_exact']=words(qa['transcription'] or '')==words(ref)
save()
print(json.dumps(qa,indent=2))
assert p.returncode==0 and qa['word_exact']
