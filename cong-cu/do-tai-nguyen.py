# Do RAM + dia DINH trong luc chay (A6). python3 do-tai-nguyen.py <file-ra>  — chay nen, ghi khi nhan SIGTERM.
import os,sys,time,signal,shutil
ra=sys.argv[1]; dinh_ram=0; dinh_dia=0; dia0=shutil.disk_usage('/').used; dem=0
def ram_dung_mb():
    try:
        m={l.split(':')[0]:int(l.split()[1]) for l in open('/proc/meminfo')}
        return (m['MemTotal']-m['MemAvailable'])//1024
    except Exception: return 0
def ghi(*_):
    open(ra,'w').write(f"RAM dinh {dinh_ram} MB; dia them dinh {dinh_dia/2**30:.1f} GB (dia dung {shutil.disk_usage('/').used/2**30:.1f}/{shutil.disk_usage('/').total/2**30:.0f} GB); {dem} mau\n"); sys.exit(0)
signal.signal(signal.SIGTERM,ghi); signal.signal(signal.SIGINT,ghi)
while True:
    dinh_ram=max(dinh_ram,ram_dung_mb()); dinh_dia=max(dinh_dia,shutil.disk_usage('/').used-dia0); dem+=1; time.sleep(2)
