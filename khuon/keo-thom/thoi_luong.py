# Do dai video = do dai giong doc + duoi 1,23 s (ban v8.3: giong 23,89 s -> 25,12 s). Thay cho hang 25.12 ghi cung (dung.py, ghep08.py, am08.py, kiem).
import pathlib,subprocess
DUOI=1.23
def dai(giong=None):
    g=giong or pathlib.Path(__file__).resolve().parent/'dau-vao'/'giong.mp3'
    d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(g)],capture_output=True,text=True,check=True).stdout.strip())
    return round(d+DUOI,2)
if __name__=='__main__': print(dai())
