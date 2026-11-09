"""Lee los archivos de convergencia exportados por HFSS y escribe conv_v2.json."""
import os, re, json
D = "datos/P2_D1_Curva90_v2_CSV"
conv = {}
for f in sorted(os.listdir(D)):
    if f.endswith("convergencia.txt"):
        t = open(os.path.join(D, f)).read()
        filas = re.findall(r"^\s*(\d+)\|\s*(\d+)\|", t, re.M)
        conv[f.split("__")[0]] = dict(passes=int(re.search(r"Completed : (\d+)", t).group(1)),
                                      ds=float(re.search(r"Current   : ([\d.eE-]+)", t).group(1)),
                                      tets=int(filas[-1][1]))
json.dump(conv, open("conv_v2.json", "w"), indent=1)
print(conv)
