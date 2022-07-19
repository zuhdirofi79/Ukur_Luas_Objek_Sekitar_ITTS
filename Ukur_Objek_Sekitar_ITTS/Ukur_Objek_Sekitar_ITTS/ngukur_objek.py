# KELOMPOK 7

# Ilham Akbar Maulana (1202202104)
# Qowiy Muhammad Rofi Z. (1202200029)
# Adiputra Renaldi Ignasius T. (1202200009)

#-------------------------------
# tahap imports
#-------------------------------

# beberapa package/builtins yang diperlukan
import os,sys,time,traceback
from math import hypot

# wajib menginstalasi pip terlebih dahulu
# python3 -m pip install opencv-python
# jalankan command di atas pada terminal/command promt
import numpy as np
import cv2

# import local clayton librarys
import frame_capture
import frame_draw

#-------------------------------
# persiapan camera
#-------------------------------

# dapatkan camera id dari argv[1]
# contoh "python3 camruler.py 2"


camera_id = 0
if len(sys.argv) > 1:
    camera_id = sys.argv[1]
    if camera_id.isdigit():
        camera_id = int(camera_id)

# camera thread setup
camera = frame_capture.Camera_Thread()
camera.camera_source = camera_id # men-set camera number yang benar
#men-set resolusi p x l camera
#camera.camera_width,camera.camera_height =  640, 480
#camera.camera_width,camera.camera_height = 1280, 720
#camera.camera_width,camera.camera_height = 1280,1024 
camera.camera_width,camera.camera_height = 1920,1080
camera.camera_frame_rate = 30
#camera.camera_fourcc = cv2.VideoWriter_fourcc(*"YUYV")
camera.camera_fourcc = cv2.VideoWriter_fourcc(*"MJPG")

# mulai camera thread
camera.start()

# inisialisasi nilai pada camera (shortcuts di bawah ini)
width  = camera.camera_width
height = camera.camera_height
area = width*height
cx = int(width/2)
cy = int(height/2)
dm = hypot(cx,cy) # jarak piksel maksimal
frate  = camera.camera_frame_rate
print('CAMERA:',[camera.camera_source,width,height,area,frate])

#-------------------------------
# gambarkan frame/modul teks
#-------------------------------

draw = frame_draw.DRAW()
draw.width = width
draw.height = height

#-------------------------------
# menkonversi (pixels ke measure)
#-------------------------------

# desainator unit jarak
unit_suffix = 'mm'

# kalibrasi setiap N pixels
pixel_base = 10

# jarak pandang maksimum dari tengah ke tepi terjauh
# seharusnya dilakukan teknik measuring pada unit_suffix 
cal_range = 72

# inisialisasi nilai kalibrasi {pixels:scale}
# ini berdasarkan ukuran frame dan the cal_range
cal = dict([(x,cal_range/dm) for x in range(0,int(dm)+1,pixel_base)])

# kalibrasi nilai loop
# di dalam main loop menggunakan program di bawah ini
cal_base = 5
cal_last = None

# memperbarui kalibrasi
def cal_update(x,y,unit_distance):

    # dasarnya
    pixel_distance = hypot(x,y)
    # fungsi hypot(): menghitung sisi miring dari segitiga siku-siku.
    scale = abs(unit_distance/pixel_distance) 
    # fungsi abs(): untuk mendapatkan nilai absolut Python atau nilai positif dari suatu angka.
    target = baseround(abs(pixel_distance),pixel_base) 
    # baseround() mirip dengan fungsi round(): mengembalikan nilai berupa bilangan integer atau float

    # nilai rendah-tinggi pada jarak
    low  = target*scale - (cal_base/2)
    high = target*scale + (cal_base/2)

    # dapatkan titik mulai dari yang rendah di pixels
    start = target
    if unit_distance <= cal_base:
        start = 0
    else:
        while start*scale > low:
            start -= pixel_base

    # dapatkan titik selesai yang tinggi di pixels
    stop = target
    if unit_distance >= baseround(cal_range,pixel_base):
        high = max(cal.keys())
    else:
        while stop*scale < high:
            stop += pixel_base

    # mengatur skala
    for x in range(start,stop+1,pixel_base):
        cal[x] = scale
        print(f'CAL: {x} {scale}')

# membaca kalibrasi data lokal (mengimport dari dataset)
calfile = 'camruler_cal.csv' #mengambil dataset dari file ms.excel
if os.path.isfile(calfile):
    with open(calfile) as f:
        for line in f:
            line = line.strip()
            if line and line[0] in ('d',):
                axis,pixels,scale = [_.strip() for _ in line.split(',',2)]
                if axis == 'd':
                    print(f'LOAD: {pixels} {scale}')
                    cal[int(pixels)] = float(scale)

# konversi dari pixels ke units (konversi pixel ke satuan mm)
def conv(x,y):

    d = distance(0,0,x,y)

    scale = cal[baseround(d,pixel_base)]

    return x*scale,y*scale

# rounding ke base
def baseround(x,base=1):
    return int(base * round(float(x)/base))
    # baseround() mirip dengan fungsi round(): mengembalikan nilai berupa bilangan integer atau float


# mengatur jarak formula 2D
def distance(x1,y1,x2,y2):
    return hypot(x1-x2,y1-y2)

#-------------------------------
# mendefinisikan frame
#-------------------------------

# mendefinisikan tampilan frame video
framename = "Qowiy Ilham Adiputra_QOILAD PREDIKSI LUAS OBJEK"
cv2.namedWindow(framename,flags=cv2.WINDOW_NORMAL|cv2.WINDOW_GUI_NORMAL)

#-------------------------------
# key events
#-------------------------------

key_last = 0
key_flags = {'config':False, # c key
             'auto':False,   # a key
             'thresh':False, # t key
             'percent':False,# p key
             'norms':False,  # n key
             'rotate':False, # r key
             'lock':False,   # 
             }

def key_flags_clear():

    global key_flags

    for key in list(key_flags.keys()):
        if key not in ('rotate',):
            key_flags[key] = False

def key_event(key):

    global key_last
    global key_flags
    global mouse_mark
    global cal_last

    # config mode
    if key == 99:
        if key_flags['config']:
            key_flags['config'] = False
        else:
            key_flags_clear()
            key_flags['config'] = True #menkondisikan nilai true pada config
            cal_last,mouse_mark = 0,None

    # mode normalisasi
    elif key == 110:
        if key_flags['norms']:
            key_flags['norms'] = False
        else:
            key_flags['thresh'] = False
            key_flags['percent'] = False
            key_flags['lock'] = False
            key_flags['norms'] = True #menkondisikan nilai true pada norms
            mouse_mark = None

    # rotasi
    elif key == 114:
        if key_flags['rotate']:
            key_flags['rotate'] = False
        else:
            key_flags['rotate'] = True #menkondisikan nilai true pada rotate

    # auto mode
    elif key == 97:
        if key_flags['auto']:
            key_flags['auto'] = False
        else:
            key_flags_clear()
            key_flags['auto'] = True
            mouse_mark = None

    # auto percent
    elif key == 112 and key_flags['auto']:
        key_flags['percent'] = not key_flags['percent']
        key_flags['thresh'] = False
        key_flags['lock'] = False

    # auto threshold
    elif key == 116 and key_flags['auto']:
        key_flags['thresh'] = not key_flags['thresh']
        key_flags['percent'] = False
        key_flags['lock'] = False

    # log
    print('key:',[key,chr(key)])
    key_last = key
    
#-------------------------------
# mouse events
#-------------------------------

# mouse events
mouse_raw  = (0,0) # pixels dari kiri atas
mouse_now  = (0,0) # pixels dari tengah
mouse_mark = None  # klik terakhir (dari tengah)

# auto measure/ngukur mouse events
auto_percent = 0.2 
auto_threshold = 127
auto_blur = 5

# normalisasi mouse events
norm_alpha = 0
norm_beta = 255

# mouse callback
def mouse_event(event,x,y,flags,parameters):

    #print(event,x,y,flags,parameters)

    # event =  0 = lokasi terkini
    # event =  1 = klik kiri bawah
    # event =  2 = klik kanan bawah
    # event =  3 = bawah tengah
    # event =  4 = klik kiri atas
    # event =  5 = klik kanan atas
    # event =  6 = atas tengah
    # event = 10 = gulir tengah, flag nilai negative|positive = down|up

    # globals
    global mouse_raw
    global mouse_now
    global mouse_mark
    global key_last
    global auto_percent
    global auto_threshold
    global auto_blur
    global norm_alpha
    global norm_beta

    # memperbarui persentasi
    if key_flags['percent']:
        auto_percent = 5*(x/width)*(y/height)

    # memperbarui threshold
    elif key_flags['thresh']:
        auto_threshold = int(255*x/width)
        auto_blur = int(20*y/height) | 1 # memastikan ini ganjil dan setidaknya itu 1

    # memperbarui normalization
    elif key_flags['norms']:
        norm_alpha = int(64*x/width)
        norm_beta  = min(255,int(128+(128*y/height)))

    # memperbarui lokasi mouse
    mouse_raw = (x,y)

    # offset dari tengah
    # inversi y ke standard quadrants
    ox = x - cx
    oy = (y-cy)*-1

    # memperbarui lokasi mouse
    mouse_raw = (x,y)
    if not key_flags['lock']:
        mouse_now = (ox,oy)

    # klik event kiri
    # untuk membuat mouse melakukan measured saat klik kiri mouse
    if event == 1:

        if key_flags['config']:
            key_flags['lock'] = False
            mouse_mark = (ox,oy)

        elif key_flags['auto']:
            key_flags['lock'] = False
            mouse_mark = (ox,oy)

        if key_flags['percent']:
            key_flags['percent'] = False
            mouse_mark = (ox,oy)
            
        elif key_flags['thresh']:
            key_flags['thresh'] = False
            mouse_mark = (ox,oy)
            
        elif key_flags['norms']:
            key_flags['norms'] = False
            mouse_mark = (ox,oy)

        elif not key_flags['lock']:
            if mouse_mark:
                key_flags['lock'] = True
            else:
                mouse_mark = (ox,oy)
        else:
            key_flags['lock'] = False
            mouse_now = (ox,oy)
            mouse_mark = (ox,oy)

        key_last = 0

    # klik event kanan
    # mengembalikan mode default measured saat klik kanan mouse
    elif event == 2:
        key_flags_clear()
        mouse_mark = None
        key_last = 0

# register mouse callback
cv2.setMouseCallback(framename,mouse_event)

#-------------------------------
# main loop
#-------------------------------

# loop
while 1:

    # dapatkan frame
    frame0 = camera.next(wait=1)
    if frame0 is None:
        time.sleep(0.1)
        continue

    # normalisasi
    cv2.normalize(frame0,frame0,norm_alpha,norm_beta,cv2.NORM_MINMAX)

    # rotasi 180
    if key_flags['rotate']:
        frame0 = cv2.rotate(frame0,cv2.ROTATE_180)

    # memulai teks blok dari atas kiri
    text = []

    # tampilan pemilik kamera
    text.append(f'Kamera milik Qowiy, Ilham, Adiputra')

    # teks kamera
    fps = camera.current_frame_rate
    text.append(f'KAMERA: {camera_id} {width}x{height} {fps}FPS')

    # teks mouse
    text.append('')
    if not mouse_mark:
        text.append(f'KLIK TERAKHIR: KOSONG') 
        # menampilkan status default kosong bilamana klik kiri mouse belum dilakukan
    else:
        text.append(f'KLIK TERAKHIR: {mouse_mark} PIXELS') 
        # menampilkan koordinat (x,y) klik kiri mouse yang terakhir
    text.append(f'XY TERKINI: {mouse_now} PIXELS')

    #-------------------------------
    # normalisasi mode
    #-------------------------------
    if key_flags['norms']:

        # print
        text.append('')
        text.append(f'MODE NORMILISASI')
        text.append(f'ALPHA (min): {norm_alpha}')
        text.append(f'BETA (max): {norm_beta}')
        # penskalaan minimum dan maksimum
        # norm_alpha (minimum) = 0
        # norm_beta (maksimum) = 255

        
    #-------------------------------
    # config mode
    #-------------------------------
    if key_flags['config']:

        # quadrant crosshairs
        draw.crosshairs(frame0,5,weight=2,color='red',invert=True)
        # crosshairs = CrossHair bekerja dengan berulang kali memanggil fungsi user dengan input simbolis. 
        # Crosshair adalah alat analisis untuk Python yang mengaburkan batas antara pengujian dan tipe sistem.


        # crosshairs aligned (terotasi) ke jarak maksimum 
        draw.line(frame0,cx,cy, cx+cx, cy+cy,weight=1,color='red')
        draw.line(frame0,cx,cy, cx+cy, cy-cx,weight=1,color='red')
        draw.line(frame0,cx,cy,-cx+cx,-cy+cy,weight=1,color='red')
        draw.line(frame0,cx,cy, cx-cy, cy+cx,weight=1,color='red')

        # garis kursor mouse (parallel selaras ke crosshairs)
        mx,my = mouse_raw
        draw.line(frame0,mx,my,mx+dm,my+(dm*( cy/cx)),weight=1,color='green')
        draw.line(frame0,mx,my,mx-dm,my-(dm*( cy/cx)),weight=1,color='green')
        draw.line(frame0,mx,my,mx+dm,my+(dm*(-cx/cy)),weight=1,color='green')
        draw.line(frame0,mx,my,mx-dm,my-(dm*(-cx/cy)),weight=1,color='green')
    
        # teks data
        text.append('')
        text.append(f'MODE KONFIG')

        # cal last
        if not cal_last:
            cal_last = cal_base
            caltext = f'KONFIG: Klik pada D = {cal_last}'

        # cal continue
        elif cal_last <= cal_range:
            if mouse_mark:
                cal_update(*mouse_mark,cal_last)
                cal_last += cal_base
            caltext = f'KONFIG: Klik pada D = {cal_last}'

        # selesai
        else:
            key_flags_clear()
            cal_last == None
            with open(calfile,'w') as f:
                data = list(cal.items())
                data.sort() 
                # Fungsi sort(): untuk pengurutan, dapat digunakan mengurutkan daftar dalam naik(ascending) dan turun (descending)
                for key,value in data:
                    f.write(f'd,{key},{value}\n')
                f.close()
            caltext = f'KONFIG: Lengkap.'

        # tambahkan caltext
        draw.add_text(frame0,caltext,(cx)+100,(cy)+30,color='red')

        # tanda mouse terhapus
        mouse_mark = None     

    #-------------------------------
    # auto mode
    #-------------------------------
    elif key_flags['auto']:
        
        mouse_mark = None

        # teks data pada auto mode
        text.append('')
        text.append(f'MODE AUTO')
        text.append(f'UNITS: {unit_suffix}')
        text.append(f'PERSENTASE MINIMAL: {auto_percent:.2f}')
        text.append(f'THRESHOLD: {auto_threshold}')
        text.append(f'GAUSS BLUR: {auto_blur}')
        
        # frame abu
        frame1 = cv2.cvtColor(frame0,cv2.COLOR_BGR2GRAY)

        # frame blur
        frame1 = cv2.GaussianBlur(frame1,(auto_blur,auto_blur),0)

        # threshold frame nilai n dari 255 (85 = 33%)
        frame1 = cv2.threshold(frame1,auto_threshold,255,cv2.THRESH_BINARY)[1]

        # inversi
        frame1 = ~frame1

        # mencari kontur pada gambar thresholded
        contours,nada = cv2.findContours(frame1,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        
        # crosshairs kecil (setelah menangkap frame1)
        draw.crosshairs(frame0,5,weight=2,color='green')    
    
        # loop pada kontur
        for c in contours:

            # kontur data (dari kiri atas)
            x1,y1,w,h = cv2.boundingRect(c)
            x2,y2 = x1+w,y1+h
            x3,y3 = x1+(w/2),y1+(h/2)

            # persentase area
            percent = 100*w*h/area
            
            # apabila kontur terlalu kecil, maka abaikan
            if percent < auto_percent:
                    continue

            # apabila kontur terlalu besar, maka abaikan
            elif percent > 60:
                    continue

            # konversi ke tengah, lalu beri jarak
            x1c,y1c = conv(x1-(cx),y1-(cy))
            x2c,y2c = conv(x2-(cx),y2-(cy))
            xlen = abs(x1c-x2c)
            ylen = abs(y1c-y2c)
            alen = 0
            if max(xlen,ylen) > 0 and min(xlen,ylen)/max(xlen,ylen) >= 0.95:
                alen = (xlen+ylen)/2              
            carea = xlen*ylen

            # plot
            draw.rect(frame0,x1,y1,x2,y2,weight=2,color='red')

            # tambahkan dimensi
            draw.add_text(frame0,f'{xlen:.2f}',x1-((x1-x2)/2),min(y1,y2)-8,center=True,color='red')
            draw.add_text(frame0,f'Luas: {carea:.2f}',x3,y2+8,center=True,top=True,color='red')
            if alen:
                draw.add_text(frame0,f'Avg: {alen:.2f}',x3,y2+34,center=True,top=True,color='green')
            if x1 < width-x2:
                draw.add_text(frame0,f'{ylen:.2f}',x2+4,(y1+y2)/2,middle=True,color='red')
            else:
                draw.add_text(frame0,f'{ylen:.2f}',x1-4,(y1+y2)/2,middle=True,right=True,color='red')

    #-------------------------------
    # dimensi mode
    #-------------------------------
    else:

        # crosshairs kecil
        draw.crosshairs(frame0,5,weight=2,color='green')    

        # garis kursor mouse
        draw.vline(frame0,mouse_raw[0],weight=1,color='green')
        draw.hline(frame0,mouse_raw[1],weight=1,color='green')
       
        # menggambar
        if mouse_mark:

            # lokasi
            x1,y1 = mouse_mark
            x2,y2 = mouse_now

            # konversi ke jarak
            x1c,y1c = conv(x1,y1)
            x2c,y2c = conv(x2,y2)
            xlen = abs(x1c-x2c)
            ylen = abs(y1c-y2c)
            llen = hypot(xlen,ylen)
            alen = 0
            if max(xlen,ylen) > 0 and min(xlen,ylen)/max(xlen,ylen) >= 0.95:
                alen = (xlen+ylen)/2              
            carea = xlen*ylen

            # cetak jarak
            text.append('')
            text.append(f'PANJANG X: {xlen:.2f}{unit_suffix}')
            text.append(f'PANJANG Y: {ylen:.2f}{unit_suffix}')
            text.append(f'PANJANG L: {llen:.2f}{unit_suffix}')

            # konversi ke lokasi plot
            x1 += cx
            x2 += cx
            y1 *= -1
            y2 *= -1
            y1 += cy
            y2 += cy
            x3 = x1+((x2-x1)/2)
            y3 = max(y1,y2)

            # garis weight
            weight = 1
            if key_flags['lock']:
                weight = 2

            # plot
            draw.rect(frame0,x1,y1,x2,y2,weight=weight,color='red')
            draw.line(frame0,x1,y1,x2,y2,weight=weight,color='green')

            # tambahkan dimensi
            draw.add_text(frame0,f'{xlen:.2f}',x1-((x1-x2)/2),min(y1,y2)-8,center=True,color='red')
            draw.add_text(frame0,f'Luas: {carea:.2f}',x3,y3+8,center=True,top=True,color='red')
            if alen:
                draw.add_text(frame0,f'Avg: {alen:.2f}',x3,y3+34,center=True,top=True,color='green')           
            if x2 <= x1:
                draw.add_text(frame0,f'{ylen:.2f}',x1+4,(y1+y2)/2,middle=True,color='red')
                draw.add_text(frame0,f'{llen:.2f}',x2-4,y2-4,right=True,color='green')
            else:
                draw.add_text(frame0,f'{ylen:.2f}',x1-4,(y1+y2)/2,middle=True,right=True,color='red')
                draw.add_text(frame0,f'{llen:.2f}',x2+8,y2-4,color='green')

    # tambahkan kunci penggunaan
    text.append('')
    text.append(f'N = NORMALISASI')
    text.append(f'A = AUTO-MODE')
    text.append(f'C = CONFIG-MODE')
    if key_flags['auto']:
        text.append(f'P = PERSENTASE MINIMAL')
        text.append(f'T = THRESHOLD')
        text.append(f'G = GAUSS BLUR')
    text.append(f'R = ROTASI')
    text.append(f'Q = KELUAR')
   
   
    


    # gambarkan teks blok kiri atas
    draw.add_text_top_left(frame0,text)

    # menampilkan
    cv2.imshow(framename,frame0)

    # delay dan aksi kunci
    key = cv2.waitKey(1) & 0xFF

    # esc ==  27 == quit
    # q   == 113 == quit
    if key in (27,113):
        break

    # key data
    #elif key != 255:
    elif key not in (-1,255):
        key_event(key)

#-------------------------------
# mematikan sequence
#-------------------------------

# menutup kamera
camera.stop()

# menutup all windows
cv2.destroyAllWindows()

# selesai
exit()

#-------------------------------
# tamat
#-------------------------------
