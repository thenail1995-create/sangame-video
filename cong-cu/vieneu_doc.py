#!/usr/bin/env python3
"""Chay TRONG env con cua giong_may.py (`uv run --with vieneu==3.8.3`): doc loi -> wav 48 kHz bang VieNeu-TTS v3 Turbo (ONNX/CPU).
Ghim mo hinh: vieneu 3.8.3 goi hf_hub_download KHONG co revision (onnx_runtime_lite.py:_fetch) va codec khong cho truyen duong dan => boc hf_hub_download
TRUOC khi import vieneu, them revision ghim cho dung 2 repo cua no (giong preset nam trong wheel nen duoc ghim theo vieneu==3.8.3). Chi mang toi HuggingFace.
  python -I vieneu_doc.py --loi-file loi.txt --giong "Adam bựa" --ra x.wav"""
import argparse,pathlib,sys
GHIM={'pnnbao-ump/VieNeu-TTS-v3-Turbo':'61b85e3d937fbbacb387714180e8182823512523','OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX':'ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae'}   # gitleaks:allow (commit Hugging Face cong khai, khong phai khoa)
def ghim_mo_hinh(thay=None):
    import huggingface_hub as hh
    goc=hh.hf_hub_download; thay=thay if thay is not None else []
    def hf_hub_download(*a,**kw):
        rid=a[0] if a else kw.get('repo_id')
        if rid in GHIM and not kw.get('revision'): kw['revision']=GHIM[rid]; thay.append(rid)
        return goc(*a,**kw)
    hh.hf_hub_download=hf_hub_download
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--loi-file',required=True); ap.add_argument('--giong',required=True); ap.add_argument('--ra',required=True); a=ap.parse_args(argv)
    loi=pathlib.Path(a.loi_file).read_text(encoding='utf-8').strip()
    if not loi: sys.exit('LOI: loi rong')
    thay=[]; ghim_mo_hinh(thay)
    from vieneu import Vieneu
    v=Vieneu(); ids=[i for _,i in v.list_preset_voices()]
    if a.giong not in ids: sys.exit(f'LOI: giong {a.giong!r} khong co trong preset ({len(ids)} giong, vd {ids[:5]})')
    audio=v.infer(loi,voice=a.giong); v.save(audio,a.ra)
    print(f'VIENEU: {len(loi)} ky tu, giong {a.giong}, ghim revision cho {sorted(set(thay))}')
if __name__=='__main__': main()
