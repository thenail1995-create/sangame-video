# Nap mo hinh Whisper 'small' voi REVISION GHIM (A4): Mac va GitHub nghe cung mot bo trong so.
#   from mo_hinh import nap_whisper ; wm = nap_whisper()
# Bien moi truong: WHISPER_REV (mac dinh REV_GHIM), WHISPER_DIR (thu muc cache HF; de trong = cache mac dinh cua may).
import os
REV_GHIM = '536b0662742c02347bc0e980a01041f333bce120'   # Systran/faster-whisper-small (da dung o Mac tu 10/10/2026)
REPO = 'Systran/faster-whisper-small'
def nap_whisper(compute=None):
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download
    rev = os.environ.get('WHISPER_REV') or REV_GHIM
    path = snapshot_download(REPO, revision=rev, cache_dir=os.environ.get('WHISPER_DIR') or None,
                             allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin', 'tokenizer.json', 'vocabulary.*'])
    return WhisperModel(path, device='cpu', compute_type=compute or os.environ.get('WHISPER_COMPUTE') or 'float32')
# Mo hinh NGHE KIEM D3 noi dung (Opus chot 11/10: small nghe giong sach CI thanh 'Dilux / mi le / khang'; large-v3-turbo nghe dung Deluxe, Mỹ, Hồng Kông 650). Small GIU cho can-chu / A2 (khong doi canh moc).
REV_TURBO = '0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf'   # mobiuslabsgmbh/faster-whisper-large-v3-turbo
REPO_TURBO = 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'
def ten_nghe_kiem(): return f'large-v3-turbo@{os.environ.get("WHISPER_TURBO_REV") or REV_TURBO}'     # dua vao khoa cache nghe_doan
def nap_whisper_nghe_kiem(compute=None):
    from faster_whisper import WhisperModel
    from huggingface_hub import snapshot_download
    rev = os.environ.get('WHISPER_TURBO_REV') or REV_TURBO
    path = snapshot_download(REPO_TURBO, revision=rev, cache_dir=os.environ.get('WHISPER_DIR') or None,
                             allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin', 'tokenizer.json', 'vocabulary.*'])
    return WhisperModel(path, device='cpu', compute_type=compute or os.environ.get('WHISPER_COMPUTE') or 'float32', cpu_threads=int(os.environ.get('WHISPER_THREADS') or 4))
def in_phien_ban():
    import importlib.metadata as m, subprocess, sys
    v = {p: m.version(p) for p in ['faster-whisper', 'ctranslate2', 'numpy', 'pillow', 'huggingface-hub']}
    ff = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True).stdout.split('\n')[0]
    return f"python {sys.version.split()[0]} | " + ' '.join(f'{k}={x}' for k, x in v.items()) + f" | whisper_rev={os.environ.get('WHISPER_REV') or REV_GHIM} | nghe_kiem={ten_nghe_kiem()} | {ff}"
if __name__ == '__main__': print(in_phien_ban())
