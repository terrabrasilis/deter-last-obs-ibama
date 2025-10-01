# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 14:06:43 2020

@author: Luis Maurano
"""
#import wget

import psycopg2
import os
from datetime import date, datetime


now = datetime.now()
current_time = now.strftime("%H:%M:%S")
horai = now.strftime("%H:%M:%S")
print("Hora inicio =", current_time)


#define mes-ano
ano_mes = date.today().strftime("%Y_%m")

#define mes-ano
ano = ano_mes.split("_")[0]
mes = ano_mes.split("_")[1]

#define bioma
bioma = os.getenv("TARGET_BIOME")
assert bioma

# Data directory for writing downloaded data
DIR=os.path.realpath(os.path.join(os.path.dirname(__file__),"../data/"))
DIR=os.getenv("DATA_DIR", DIR)
assert DIR

dirtifs = f"{DIR}/{bioma}/" # setar aqui novo path

# database params
host=os.getenv("PGHOST")
database=os.getenv("PGDB")
port=os.getenv("PGPORT")
user=os.getenv("PGUSER")
password=os.getenv("PGPASSWORD")
assert host
assert database
assert port
assert user
assert password

con = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
assert con

#conecta BD em funcao do bioma
bbox = None
if bioma == 'Amazonia':
    bbox = "-75.0000735765536177 -18.2846686190823959 -41.6086164874900533 6.0000274456911082"
    
if bioma == 'Cerrado':
    bbox = "-60.2903525641267635 -24.3011939976840061 -41.3760722593129131 -2.4895619738332009"

assert bbox

#sql para selecionar datai e dataf das semanas
sql=f"""
WITH num_weeks AS (
	SELECT SUBSTRING(MAX(data)::text,6,5) as wks
	FROM public.cmask_week
)
SELECT week, mmdd1, mmdd2, mes
	FROM public.weeks
WHERE mmdd1 IN (SELECT wks FROM num_weeks) OR mes = '{str(mes)}'
ORDER BY id ASC
"""

print(sql)

cur = con.cursor()
cur.execute(sql)
campos = cur.fetchall()

# used to remove in the end
lista_tifnn = ""
lista_tif_base = ""

for campo in campos:
    week = campo[0]
    mes_week = int(campo[3])
    if mes_week==12 and mes=='01':
        datai = str(int(ano)-1) + "-" + str(campo[1])
        dataf = str(int(ano)-1) + "-" + str(campo[2])
    else:
        datai = str(ano) + "-" + str(campo[1])
        dataf = str(ano) + "-" + str(campo[2])
    

    #print (week, datai, dataf)

    
    query = "SELECT source, data"
    query += " FROM public.cmask_acervo"
    query += " where data >= '" + str(datai) + "' and data < '" + str(dataf) + "'"
    query += " AND bioma = '" + bioma + "'" 
    query += " ORDER BY data asc"
    print (query)
    
    cur.execute(query)
    fields = cur.fetchall()
    
    nlines = len(fields)

    if nlines == 0:
        #sys.exit("aa! errors!")
        print ("Sem mais candidatos")
        break
    

    
    for field in fields:
        nometif = field[0]
        tif_split = nometif.split(".")
        tif =  tif_split[0]
        lista_tifnn +=  dirtifs + "" +  tif + "_epsg4326_nn.tif "
        lista_tif_base +=  dirtifs + "" +  nometif + " "
        #print (nometif)
        
        # Resample with GDAL warp
        intif = dirtifs + nometif
        outtif = dirtifs + tif + "_epsg4326.tif"
        
        try:
            print('1) gdal calc para ' + tif )
            os.system("gdal_calc.py -A " + intif + " --type=Byte --overwrite --NoDataValue=0 --quiet --outfile=" +  dirtifs + tif + "_epsg32718_nn.tif  --quiet --overwrite --calc=\"((A==127)*127)\"")
        
            print('2) gdal warp para ' + tif )
            os.system("gdalwarp -t_srs EPSG:4326 -tr 0.000575656183491 0.000575656183491 -q -overwrite " +  dirtifs + tif + "_epsg32718_nn.tif -q " + dirtifs + tif + "_epsg4326_nn.tif")
        except Exception:
            print('tiff com problema ' + tif )
                
        
        # set tif como processado
        update = "UPDATE public.cmask_acervo SET processada = 1 WHERE source = '" + nometif + "'"
        cur = con.cursor()
        cur.execute(update)
        con.commit()
        
        os.system("rm  " + dirtifs + tif + "_epsg32718_nn.tif")
        
    #print(lista_tifnn)

    print('3) gdal build para ' + "naonuvem_" + bioma + "_" + str(datai) + ".vrt ")
    os.system("gdalbuildvrt  " + dirtifs + "naonuvem_" + bioma + "_" +  str(datai) + ".vrt -q -overwrite " + lista_tifnn + "")
    nnouttmp = "naonuvem_" + bioma + "_" + str(datai) + "_tmp.tif"
    nnouttmp1 = "naonuvem_" + bioma + "_" + str(datai) + "_tmp1.tif"
    nnout = "naonuvem_" + bioma + "_" + str(datai) + ".tif"
    nvrt = "naonuvem_" + bioma + "_" + str(datai) + ".vrt"
    qml = "naonuvem_" + bioma + "_" + str(datai) + ".qml"

    print('4) gdal translate para ' + "naonuvem_" + bioma + "_" + str(datai) + ".vrt ")
    os.system("gdal_translate -of GTiff -co \"COMPRESS=LZW\" -q -co BIGTIFF=YES " + dirtifs + "naonuvem_" + bioma + "_" + str(datai) + ".vrt " + dirtifs + nnouttmp)
    
    print('5) gdal warp para ' + "naonuvem_" + bioma + "_" + str(datai) + "_tmp.tif ")
    os.system("gdalwarp  -te " + bbox + " -overwrite -q -ot Byte " + dirtifs + nnouttmp + " " + dirtifs + nnouttmp1)
    
    print('6) gdal translate para ' + nnouttmp1  + " \n")
    os.system("gdal_translate -of GTiff -co \"COMPRESS=LZW\" -q -co BIGTIFF=YES " + dirtifs  + nnouttmp1 + " " + dirtifs + nnout)
    
    os.system("cp  " + dirtifs + "naonuvem_legenda_template.qml " +  dirtifs + qml) 
    os.system("rm  " + dirtifs + nnouttmp)
    os.system("rm  " + dirtifs + nnouttmp1)
    os.system("rm  " + dirtifs + nvrt)
    
    
    try:
        insert = "INSERT INTO public.cmask_week (nome_tiff, data, bioma, processada)  VALUES ('" + nnout + "', '" + str(datai) + "', '" + bioma + "', " + str(1) + ")"
        cur.execute(insert)
        con.commit()
    except Exception:
        print('tiff ja inserido ' + nnout )
        con.rollback()
    
    
os.system("rm  " + lista_tifnn + "")
os.system("rm  " + lista_tif_base + "")

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
print(bioma, "Hora fim  =", current_time)
        
