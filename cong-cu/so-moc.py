# So moc chu (can-chu.py tren may moi) voi moc Mac (A4/K14): lech toi da / TB tung chu, exit 1 neu vuot tran.
#   python3 so-moc.py <moc-mac.json> <moc-moi.json> [tran_giay=0.08]
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); tran=float(sys.argv[3]) if len(sys.argv)>3 else 0.08
if len(a)!=len(b) or [x['w'] for x in a]!=[x['w'] for x in b]: sys.exit(f'LOI: danh sach chu khac nhau ({len(a)} vs {len(b)})')
ds=[abs(x['s']-y['s']) for x,y in zip(a,b)]; de=[abs(x['e']-y['e']) for x,y in zip(a,b)]
xau=[(x['w'],x['s'],y['s']) for x,y,d in zip(a,b,ds) if d>tran]; xau_e=[(x['w'],x['e'],y['e']) for x,y,d in zip(a,b,de) if d>tran]
print(f"so moc: {len(a)} chu; lech bat dau max {max(ds)*1000:.0f} ms, TB {sum(ds)/len(ds)*1000:.0f} ms; lech ket thuc max {max(de)*1000:.0f} ms, TB {sum(de)/len(de)*1000:.0f} ms; tran {tran*1000:.0f} ms")
if xau or xau_e: print('VUOT TRAN: bat dau',xau[:8],'| ket thuc',xau_e[:8]); sys.exit(1)
print('DAT: moc chu khop Mac trong tran')
