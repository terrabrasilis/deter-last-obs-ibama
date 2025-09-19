# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 11:20:25 2020

@author: Luis Maurano
"""

from osgeo import gdal
import os
import psycopg2
from datetime import date, datetime

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
horai = now.strftime("%H:%M:%S")

print("Current Time =", current_time)

today = date.today()

#define bioma
bioma = os.getenv("TARGET_BIOME")
assert bioma


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

#conecta PG
tabledeter = None
if bioma == 'Amazonia':
    tabledeter = 'deter_agregate.deter'
    
if bioma == 'Cerrado':
    tabledeter = 'aggregate.deter'

assert tabledeter

ndias = -1
deltad = 7

classes_nuvem = {
127: "NaoNuvem"
}

# obtem ultima data processada
consulta = "SELECT max(data) FROM public.last_day_processed"

cur = con.cursor()
cur.execute(consulta)
campos = cur.fetchall()

datai = None
for campo in campos:
    datai = str(campo[0])

assert datai

# Data directory for writing downloaded data
DIR=os.path.realpath(os.path.join(os.path.dirname(__file__),"../data/"))
DIR=os.getenv("DATA_DIR", DIR)
assert DIR

dirtifs = f"{DIR}/{bioma}/" # setar aqui novo path

consulta = "  SELECT * FROM public.cmask_week"
consulta += " WHERE data <= '" + str(today) + "'" 
consulta += " AND data >= (date_trunc('month', '" + str(today) + "' ::date) + interval '1 month' - interval '370 day')::date" 
#consulta += " AND data >= '2023-08-01'"
consulta += " AND bioma = '" + bioma + "'" 
consulta += " order by data desc"

cur = con.cursor()
cur.execute(consulta)
rows = cur.fetchall()

# set defult values
pixelvalue = None
view_date = None

for row in rows:
    rastername = row[0]
    dataobs = row[0][18:28]
    print ("fazendo... " +rastername)
    
    #sql para pegar focos
    sql = "SELECT id, last_obs, ST_X(ST_PointOnSurface(geom)) as lon, ST_Y(ST_PointOnSurface(geom)) as lat, view_date"
    sql += " FROM " + tabledeter
    sql += " WHERE id >=0" 
    sql += " AND view_date > '" + datai + "'" 
    #sql += " AND view_date <= (date_trunc('month', '" + datai + "'::date) + interval '2 month' - interval '1 day')::date"
    sql += " AND  view_date <= view_date - INTERVAL '-15 days'"
    sql += " AND satellite IN ('AMAZONIA-1','CBERS-4A','CBERS-4')"
    sql += " AND last_obs = " + str(ndias)
    sql += " order by view_date asc"

    print(sql ,'\n')

    cur = con.cursor()
    cur.execute(sql)
    campos = cur.fetchall()
    nlines = len(campos)

    if nlines == 0:
        #sys.exit("aa! errors!")
        print ("Sem mais candidatos")
        break

    # tiff 
    driver = gdal.GetDriverByName('GTiff')
    filename = dirtifs+rastername #path to raster
    dataset = gdal.Open(filename)
    band = dataset.GetRasterBand(1)

    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    transform = dataset.GetGeoTransform()

    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]

    data = band.ReadAsArray(0, 0, cols, rows)

    for campo in campos:
        id = str(campo[0])
        nuv_mesant = campo[1]
        
        if  nuv_mesant == -1:
            ndias = 0
            nuv_mesant = 0
            
        lon = float(campo[2])
        lat = float(campo[3])
        col = int((lon - xOrigin) / pixelWidth)
        row = int((yOrigin - lat ) / pixelHeight)
        view_date = str(campo[4])
        
        try:
            pixelvalue = data[row][col]
        except Exception:
            print ("error no id " + id)
            pass
        
        #print (id,lat,lon,pixelvalue)
        #sql para updae na tabela com classe prodes

        try:
            assert pixelvalue # test if pixel value is ok
            pixelclasse = classes_nuvem[pixelvalue]
            #print (id,lat,lon,pixelvalue,pixelclasse, col, row)
            pixelvalue = nuv_mesant + ndias
     
            if nuv_mesant > 0:
                continue
                
            query = "UPDATE " + tabledeter + " set last_obs = " + str(pixelvalue) + " WHERE id = " + id + ";"
            cur.execute(query)
            print ("1 )" + rastername ,'\n' + query ,'\n')
            con.commit()
        except KeyError:
            pixelvalue = nuv_mesant + deltad
            query = "UPDATE " + tabledeter + " set last_obs = " + str(pixelvalue) + " WHERE id = " + id + ";"
            cur.execute(query)
            print ("2 )" + rastername,'\n' + query,'\n')
            con.commit()
            pass
        
    ndias += deltad
    
if ndias >= 0:
    assert view_date
    query = "INSERT INTO public.last_day_processed  (data, processed)  VALUES ('" + str(view_date) + "', '" + str(now) + "')" 
    cur.execute(query)
    con.commit()
else:
    print ("Sem poligonos para processar")  
   # query = "UPDATE public.last_day_processed set data = '" + str(view_date) + "', processed = '" + str(now) + "' WHERE id = 1"


    
#con.commit()
cur.close()
con.close()

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
print("Current Time =", current_time)
