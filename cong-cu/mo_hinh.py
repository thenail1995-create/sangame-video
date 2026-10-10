# Nap mo hinh Whisper 'small' voi REVISION GHIM (A4): Mac va GitHub nghe cung mot bo trong so.
#   from mo_hinh import nap_whisper ; wm = nap_whisper()
# Bien moi truong: WHISPER_REV (mac dinh REV_GHIM), WHISPER_DIR (thu muc cache HF; de trong = cache mac dinh cua may).
import os
REV_GHIM = '536b0662742c02347bc0e980a01041f333bce120'   # Systran/faster-whisper-small (da dung o Mac tu 10/10/2026)
REPO = 'Systran/faster-whisper-small'
def nap_whisper():
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download
    rev = os.environ.get('WHISPER_REV') or REV_GHIM
    path = snapshot_download(REPO, revision=rev, cache_dir=os.environ.get('WHISPER_DIR') or None,
                             allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin', 'tokenizer.json', 'vocabulary.*'])
    return WhisperModel(path, device='cpu', compute_type='int8')
def in_phien_ban():
    import importlib.metadata as m, subprocess, sys
    v = {p: m.version(p) for p in ['faster-whisper', 'ctranslate2', 'numpy', 'pillow', 'huggingface-hub']}
    ff = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split('\n')[0]
    return f"python {sys.version.split()[0]} | " + ' '.join(f'{k}={x}' for k, x in v.items()) + f" | whisper_rev={os.environ.get('WHISPER_REV') or REV_GHIM} | {ff}"
if __name__ == '__main__': print(in_phien_ban())
