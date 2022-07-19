import time
import threading,queue
import numpy as np
import cv2

# ------------------------------
# Kamera Tread
# ------------------------------

class Camera_Thread:

    # PENTING: antrian jauh lebih efisien daripada deque
    # versi antrian berjalan pada 35% dari 1 prosesor
    # versi deque berjalan pada 108% dari 1 prosesor


    # ------------------------------
    # INTRUKSI PENGGUNA
    # ------------------------------

    
# Menggunakan variabel pengguna (lihat di bawah):
    # Atur nomor sumber kamera (defaultnya adalah kamera 0).
    # Atur lebar dan tinggi piksel kamera (defaultnya adalah 640x480).
    # Tetapkan frame rate target (maks) (default adalah 30).
    # Atur jumlah frame untuk disimpan di buffer (defaultnya adalah 4).
    # Atur variabel buffer_all: True = no frame loss, untuk membaca file, jangan membaca frame lain sampai buffer memungkinkan
    # False = memungkinkan kehilangan bingkai, untuk membaca kamera, simpan saja pembacaan bingkai terbaru

# Mulai utas kamera menggunakan self.start().

# Dapatkan frame berikutnya dalam menggunakan self.next(black=True,wait=1).
    # Jika hitam, nilai bingkai default adalah bingkai hitam.
    # Jika tidak hitam, nilai bingkai default adalah Tidak Ada.
    # Jika batas waktu, tunggu hingga batas waktu detik hingga frame dimuat ke buffer.
    # Jika tidak ada bingkai di buffer, kembalikan nilai bingkai default.


    # Hentikan kamera menggunakan self.stop()

    # ------------------------------
    # Variabel Pengguna
    # ------------------------------

    # Setup Kamera
    camera_source = 0
    camera_width = 640
    camera_height = 480
    camera_frame_rate = 30
    camera_fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    # main opsi kedua: camera_fourcc = cv2.VideoWriter_fourcc(*"YUYV")

    # buffer setup
    buffer_length = 5
    buffer_all = False

    # ------------------------------
    # Variabel Sistem
    # ------------------------------

    # kamera
    camera = None
    camera_init = 0.5

    # buffer
    buffer = None

    # state kendali
    frame_grab_run = False
    frame_grab_on = False

    # hitung dan banyaknya frame, frame rate, loop
    frame_count = 0
    frames_returned = 0
    current_frame_rate = 0
    loop_start_time = 0

    # ------------------------------
    # Fungsi
    # ------------------------------

    def start(self):

        # buffer
        if self.buffer_all:
            self.buffer = queue.Queue(self.buffer_length)
        else:
            # hanya frame terakhir
            self.buffer = queue.Queue(1)

        # setup kamera
        self.camera = cv2.VideoCapture(self.camera_source)
        self.camera.set(3,self.camera_width)
        self.camera.set(4,self.camera_height)
        self.camera.set(5,self.camera_frame_rate)
        self.camera.set(6,self.camera_fourcc)
        time.sleep(self.camera_init)

        # gambar kamera varsial
        self.camera_width  = int(self.camera.get(3))
        self.camera_height = int(self.camera.get(4))
        self.camera_frame_rate = int(self.camera.get(5))
        self.camera_mode = int(self.camera.get(6))
        self.camera_area = self.camera_width*self.camera_height

        # frame hitam (sebagai filler)
        self.black_frame = np.zeros((self.camera_height,self.camera_width,3),np.uint8)

        # memasang run state
        self.frame_grab_run = True
        
        # memulai thread
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def stop(self):

        # memasang matikan loop state
        self.frame_grab_run = False
        
        # biarkan loop berhenti
        while self.frame_grab_on:
            time.sleep(0.1)

        # tutup kamera bila kamera belum berhenti sepenuhnya
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
        self.camera = None

        # drop buffer
        self.buffer = None

    def loop(self):

        # menload frame saat mulai
        frame = self.black_frame
        if not self.buffer.full():
            self.buffer.put(frame,False)

        # status
        self.frame_grab_on = True
        self.loop_start_time = time.time()

        # frame rate
        fc = 0
        t1 = time.time()

        # loop
        while 1:

            # pematian eksternal
            if not self.frame_grab_run:
                break

            # true buffered mode (untuk files, bukan loss)
            if self.buffer_all:

                # buffer penuh, pause dan loop
                if self.buffer.full():
                    time.sleep(1/self.camera_frame_rate)

                # atau menload buffer dengan frame selanjutnya
                else:
                    
                    grabbed,frame = self.camera.read()

                    if not grabbed:
                        break

                    self.buffer.put(frame,False)
                    self.frame_count += 1
                    fc += 1

            # false buffered mode (untuk kamera, loss diperbolehkan)
            else:

                grabbed,frame = self.camera.read()
                if not grabbed:
                    break

                #membuka sebuah spot pada buffer
                if self.buffer.full():
                    self.buffer.get()

                self.buffer.put(frame,False)
                self.frame_count += 1
                fc += 1

            # memperbarui frame membaca rate
            if fc >= 10:
                self.current_frame_rate = round(fc/(time.time()-t1),2)
                fc = 0
                t1 = time.time()

        # shut down
        self.loop_start_time = 0
        self.frame_grab_on = False
        self.stop()

    def next(self,black=True,wait=0):

        #default frame hitam
        if black:
            frame = self.black_frame

        #bukan frame default
        else:
            frame = None

        # dapatkan dari buffer (gagal bila kosong)
        try:
            frame = self.buffer.get(timeout=wait)
            self.frames_returned += 1
        except queue.Empty:
            #print('Queue Empty!')
            #print(traceback.format_exc())
            pass

        # tamat
        return frame
