from CargadorDeDatos import *
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.colors as colors
import pandas as pd

cdf_campo = obtener_archivos_cdf_en_directorio('FIELDS_1min')
cdf_EPH = obtener_archivos_cdf_en_directorio('EPHEMERIS')

EPH_DAT = pd.DataFrame(cargar_datos_cdf(cdf_EPH, ['Epoch', 'RAD_AU','HG_LAT']))
MAG_DAT = cargar_datos_cdf(cdf_campo, ["epoch_mag_RTN_1min", "psp_fld_l2_mag_RTN_1min", 'psp_fld_l2_quality_flags' ])

chunks_Epoch_R     = EPH_DAT['Epoch']
chunks_R        = EPH_DAT['RAD_AU']
chunks_latitud = EPH_DAT['HG_LAT']

chunks_Epoch_B     = MAG_DAT['epoch_mag_RTN_1min']
chunks_Bv         = MAG_DAT['psp_fld_l2_mag_RTN_1min']
chunks_B_qf    = MAG_DAT['psp_fld_l2_quality_flags']


fechas_perihelio_todas = [
    datetime.fromisoformat('2018-11-05').timestamp(),#1-2
    datetime.fromisoformat('2019-04-04').timestamp(), #2-3
    datetime.fromisoformat('2019-09-01').timestamp(), #3-4
    datetime.fromisoformat('2020-01-29').timestamp(),# 4-5
    datetime.fromisoformat('2020-06-07').timestamp(), #5-6
    datetime.fromisoformat('2020-09-27').timestamp(), # 6-7
    datetime.fromisoformat('2021-01-17').timestamp(),  # 7-8
    datetime.fromisoformat('2021-04-29').timestamp(),  #8-9
    datetime.fromisoformat('2021-08-09').timestamp(), # 9 -10
    datetime.fromisoformat('2021-11-21').timestamp(),# 10 -11
    datetime.fromisoformat('2022-02-25').timestamp(), # 11 -12
    datetime.fromisoformat('2022-06-01').timestamp(),  # 12 - 13
    datetime.fromisoformat('2022-09-06').timestamp(), # 13 -14
    datetime.fromisoformat('2022-12-11').timestamp(),# 14 -15
    datetime.fromisoformat('2023-03-17').timestamp(),# 15
]

SMALL_SIZE =8
MEDIUM_SIZE = 18
BIGGER_SIZE = 30

plt.rc('font', size=MEDIUM_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MEDIUM_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

fig, axs = plt.subplots(3,5, figsize=(13,8), sharex=True,sharey=True)
polinomios = []
Rs_del_pol = []

desv_pend = []
desv_inter = []
for n, fecha_referencia in enumerate(fechas_perihelio_todas):
    #fecha_referencia = datetime.fromisoformat('2021-04-29').timestamp()
    tiempo_anterior = fecha_referencia - timedelta(days=40).total_seconds()
    tiempo_posterior = fecha_referencia + timedelta(days=1).total_seconds()

    # Filtrar los "chunks" de EPH_DAT
    indices_filtrados_R, data_filtrada_R = filtrar_chunks(chunks_Epoch_R, chunks_R, tiempo_anterior, tiempo_posterior)
    indices_filtrados_latit, datafiltrados_latit = filtrar_chunks(chunks_Epoch_R,chunks_latitud, tiempo_anterior, tiempo_posterior)
    # Filtrar los "chunks" de FIELDS
    indices_filtrados_B, data_filtrada_B = filtrar_chunks(chunks_Epoch_B, chunks_Bv, tiempo_anterior, tiempo_posterior)
    indices_filtrados_flags, data_filtrada_flags = filtrar_chunks(chunks_Epoch_B, chunks_B_qf, tiempo_anterior, tiempo_posterior)


    n_datos= 0
    tmp1 = []
    for i, chunk in enumerate(data_filtrada_B):
        for j, dat in enumerate(chunk):
            if data_filtrada_flags[i][j] == 0: ## 0 significa sin flags
                val = np.sqrt(dat[0]**2 + dat[1]**2 + dat[2]**2)
                if val <= np.sqrt(3)*1e6:
                    tmp1.append(val)
    print( 'Plot: ', n,' procesado con ', len(tmp1), ' totales de datos guardados')

    def yfit(x, poli):
        return np.power(10, poli(np.log10(x)))

    R = np.array(data_filtrada_R[0]) ## al R no es necesario tratarlo ya que contiene un solo chunk
    Lat = np.array(datafiltrados_latit[0])
    B = np.array(tmp1)

    R, B = igualar_longitud_arrays(R,B)
    R, B = eliminar_nan_correspondientes(R, B)


    if B.size != 0:
        R_bins = np.logspace(np.log10(np.min(R)), np.log10(np.max(R)), 100)
        B_bins = np.logspace(np.log10(np.min(B)), np.log10(np.max(B)), 100)

        logx = np.log10(R)
        logy = np.log10(B)
        coeffs, Vmatrix = np.polyfit(logx,logy,deg=1, cov= 'unscaled')
        poly = np.poly1d(coeffs)
        polinomios.append(poly)
        Rs_del_pol.append(R)
        desv_pend.append(np.sqrt(Vmatrix[1 ,1]))
        desv_inter.append(np.sqrt(Vmatrix[0,0]))
        a = n//5
        b = n%5
        ax = axs[a,b]
        ax.plot(R, yfit(R, poly), '--', label='y='+str(poly), c='black'  )
        h, xedges,yedges,im = ax.hist2d(R, B, bins=(R_bins, B_bins), norm= colors.LogNorm(), cmap='plasma', density=True)

        ax.text(0.2, 0.3, f'N={n+1}', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlim(0.04,0.9)
        ax.tick_params(axis='x', labelrotation=35)

        my_ticks = np.logspace(np.log10(np.min(R)), np.log10(np.max(R)), 3)
        my_labels = ['%.2f' % elem for elem in my_ticks]
        ax.set(xticks = my_ticks, xticklabels=my_labels)
        date = datetime.fromtimestamp(fecha_referencia).date()
        ax.legend()


fig.supxlabel('Distancia radial en UA')
fig.supylabel('Magnitud de campo magnético en nT')
fig.subplots_adjust(wspace=0,hspace=0, left=0.1, right=0.84,top=0.99,bottom=0.16)
cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
fig.autofmt_xdate(rotation=35)
fig.colorbar(im, cax=cbar_ax,label='Densidad de puntos normalizada')
#plt.tight_layout()
#plt.savefig('Gráficos\Finales\Acercamiento.png')    
plt.show()

plt.figure(figsize=(9,9))
plt.title('Evolución de las pendientes encontradas')
plt.xlabel('N° Alejamiento')
plt.ylabel('Pendiente recta ajustada')
plt.grid(True)
i=1
fechas = [] 
y = []
for p, t in zip(polinomios, fechas_perihelio_todas):
    #print(p[0], p[1], p)
    fechas.append(datetime.fromtimestamp(t))
    y.append(p[1])
    i+=1 

plt.tight_layout()
print(desv_pend)
#plt.errorbar(np.arange(1,len(y)+1), y, yerr=desv_pend,barsabove=True,capsize=1.)
#plt.plot(np.arange(1,len(y)+1), y, color='black', marker='o', linestyle='dashed',
#         linewidth=1, markersize=5) 
#plt.savefig('Gráficos\Finales\Pendientes2.png')    
#plt.show()

plt.figure(figsize=(9,9))
plt.title('Evolución de los interceptos encontradas') 
plt.xlabel('Número de Acercamientos')
plt.ylabel('Intercepto recta ajustada')
plt.grid(True)
i=1
x = []
y = []
for p, r in zip(polinomios, Rs_del_pol):
    #print(p[0], p[1], p)
    x.append(i)
    y.append(p[0])
    i+=1
    
plt.tight_layout()
#plt.errorbar(np.arange(1,len(y)+1), y, yerr=desv_inter,barsabove=True,capsize=1.)
#plt.plot(np.arange(1,len(y)+1), y,color='black', marker='o', linestyle='dashed',
#         linewidth=1, markersize=5)


#plt.savefig('Gráficos\Finales\Interceptos2.png')    
#plt.show()
