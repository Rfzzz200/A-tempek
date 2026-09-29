import json
import math
import os
import random

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Quad, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton

# ================= PENGATURAN =================
BG_FILE = "rafardhan.jpg"   # background bawaan (bisa diganti lewat menu gear)

# Aturan tiap mode dadu
MODE = {
    9: {"jumlah": 9, "k_max": 31, "maks": 54, "cols": 3},   # 9-31 = K, 32-54 = B
    1: {"jumlah": 1, "k_max": 3, "maks": 6, "cols": 1},     # 1-3 = K, 4-6 = B
}
# ==============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BIRU_DADU = (0.12, 0.75, 0.86, 1)
HIJAU_K = (0.20, 0.85, 0.50, 1)
ORANYE_B = (1.00, 0.55, 0.15, 1)
BIRU_TOMBOL = (0.16, 0.42, 1, 1)
ABU_TOMBOL = (0.25, 0.27, 0.33, 1)
GELAP = (0.13, 0.15, 0.22, 1)

EKSTENSI_GAMBAR = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

Window.clearcolor = (0.05, 0.06, 0.10, 1)


def cari_background():
    """Cari gambar bawaan di beberapa folder umum."""
    nama_dasar = os.path.splitext(BG_FILE)[0]
    folder = [
        BASE_DIR, os.getcwd(),
        "/storage/emulated/0/Download", "/storage/emulated/0/Pictures",
        "/storage/emulated/0/DCIM", "/storage/emulated/0", "/sdcard/Download",
    ]
    for f in folder:
        for e in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
            path = os.path.join(f, nama_dasar + e)
            if os.path.exists(path):
                return path
    return None


def folder_awal():
    for f in ("/storage/emulated/0/Download", "/storage/emulated/0",
              "/sdcard", BASE_DIR, os.getcwd()):
        if os.path.isdir(f):
            return f
    return "/"


def style_toggle(btn, *a):
    btn.background_color = BIRU_TOMBOL if btn.state == "down" else ABU_TOMBOL


class Card(BoxLayout):
    """Panel transparan dengan sudut membulat."""

    def __init__(self, warna=(0, 0, 0, 0.28), **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*warna)
            self._r = RoundedRectangle(radius=[dp(24)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size


class Die(Label):
    """Satu dadu biru (angka 1-6) seperti di Google."""

    def __init__(self, **kw):
        super().__init__(text="?", bold=True, color=(1, 1, 1, 1), **kw)
        with self.canvas.before:
            Color(0, 0, 0, 0.35)
            self._shadow = RoundedRectangle(radius=[dp(18)])
            Color(*BIRU_DADU)
            self._r = RoundedRectangle(radius=[dp(18)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        s = min(self.width, self.height) * 0.86
        x = self.x + (self.width - s) / 2
        y = self.y + (self.height - s) / 2
        self._r.size = (s, s)
        self._r.pos = (x, y)
        self._shadow.size = (s, s)
        self._shadow.pos = (x + dp(3), y - dp(4))
        self.font_size = s * 0.55


class GearButton(Button):
    """Tombol ikon gear (digambar sendiri, tidak butuh font/gambar)."""

    def __init__(self, **kw):
        super().__init__(text="", background_normal="", background_down="",
                         background_color=(0, 0, 0, 0), **kw)
        self.bind(pos=self._draw, size=self._draw, state=self._draw)

    def _draw(self, *a):
        self.canvas.after.clear()
        s = min(self.width, self.height)
        cx, cy = self.center_x, self.center_y
        alpha = 1.0 if self.state == "down" else 0.92
        with self.canvas.after:
            Color(GELAP[0], GELAP[1], GELAP[2], alpha)
            Ellipse(pos=(cx - s / 2, cy - s / 2), size=(s, s))
            Color(1, 1, 1, 1)
            r = s * 0.24
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            n = 8
            r0, r1, w = r * 0.8, s * 0.36, s * 0.06
            for i in range(n):
                ang = 2 * math.pi * i / n
                dx, dy = math.cos(ang), math.sin(ang)
                px, py = -dy, dx
                Quad(points=[
                    cx + dx * r0 + px * w, cy + dy * r0 + py * w,
                    cx + dx * r1 + px * w, cy + dy * r1 + py * w,
                    cx + dx * r1 - px * w, cy + dy * r1 - py * w,
                    cx + dx * r0 - px * w, cy + dy * r0 - py * w])
            Color(*GELAP)
            h = s * 0.1
            Ellipse(pos=(cx - h, cy - h), size=(2 * h, 2 * h))


class DaduApp(App):
    title = "Prediksi Dadu"

    # ---------------- Bangun tampilan ----------------
    def build(self):
        self.mode = 9
        self.bg_path = cari_background()
        self._muat_pengaturan()

        self.riwayat = []
        self.nomor_game = 0
        self.hitung_k = 0
        self.hitung_b = 0
        self.sedang_roll = False

        root = FloatLayout()

        # Background
        self.bg = Image(size_hint=(1, 1))
        if hasattr(self.bg, "fit_mode"):
            self.bg.fit_mode = "cover"
        else:
            self.bg.allow_stretch = True
            self.bg.keep_ratio = False
        root.add_widget(self.bg)
        self._pasang_background(self.bg_path)

        overlay = Card(warna=(0, 0, 0, 0.08), size_hint=(1, 1))
        overlay._r.radius = [0]
        root.add_widget(overlay)

        utama = BoxLayout(orientation="vertical",
                          padding=[dp(40), dp(24), dp(40), dp(40)],
                          spacing=dp(16))

        utama.add_widget(Label(
            text="[b]PREDIKSI DADU[/b]", markup=True,
            font_size=sp(34), color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(56)))
        self.lbl_sub = Label(markup=True, font_size=sp(16),
                             size_hint_y=None, height=dp(28))
        utama.add_widget(self.lbl_sub)
        utama.add_widget(Label(
            text="[i]by rfzz[/i]", markup=True,
            font_size=sp(14), color=(0.85, 0.9, 1, 0.9),
            size_hint_y=None, height=dp(22)))

        isi = BoxLayout(spacing=dp(16))

        # Kiri: kartu dadu
        kiri = Card(padding=dp(14), size_hint_x=0.58)
        self.grid = GridLayout(cols=3, spacing=dp(8))
        kiri.add_widget(self.grid)
        isi.add_widget(kiri)

        # Kanan: hasil
        kanan = Card(orientation="vertical", padding=dp(16),
                     spacing=dp(8), size_hint_x=0.42)
        self.lbl_judul_total = Label(text="TOTAL", font_size=sp(16),
                                     color=(0.8, 0.85, 1, 1),
                                     size_hint_y=None, height=dp(24))
        kanan.add_widget(self.lbl_judul_total)
        self.lbl_total = Label(text="-", bold=True, font_size=sp(72),
                               color=(1, 1, 1, 1))
        kanan.add_widget(self.lbl_total)
        self.lbl_hasil = Label(text="SIAP?", bold=True, font_size=sp(40),
                               color=(0.8, 0.85, 1, 1),
                               size_hint_y=None, height=dp(64))
        kanan.add_widget(self.lbl_hasil)

        self.btn = Button(
            text="ROLL", bold=True, font_size=sp(26),
            size_hint_y=None, height=dp(64),
            background_normal="", background_color=BIRU_TOMBOL)
        self.btn.bind(on_release=self.roll)
        kanan.add_widget(self.btn)

        self.lbl_stat = Label(text="K: 0   |   B: 0", font_size=sp(16),
                              color=(0.9, 0.9, 0.9, 1),
                              size_hint_y=None, height=dp(28))
        kanan.add_widget(self.lbl_stat)

        kanan.add_widget(Label(text="RIWAYAT (5 TERAKHIR)", font_size=sp(13),
                               color=(0.8, 0.85, 1, 1),
                               size_hint_y=None, height=dp(20)))
        self.lbl_riwayat = Label(text="-", font_size=sp(17), markup=True,
                                 color=(1, 1, 1, 1),
                                 halign="center", valign="middle",
                                 size_hint_y=None, height=dp(56))
        self.lbl_riwayat.bind(
            width=lambda w, v: setattr(w, "text_size", (v, None)))
        kanan.add_widget(self.lbl_riwayat)

        isi.add_widget(kanan)
        utama.add_widget(isi)
        root.add_widget(utama)

        # Ikon gear di pojok kanan atas
        gear = GearButton(size_hint=(None, None), size=(dp(60), dp(60)),
                          pos_hint={"right": 0.985, "top": 0.985})
        gear.bind(on_release=self.buka_pengaturan)
        root.add_widget(gear)

        self._bangun_dadu()
        self._update_teks_mode()
        return root

    # ---------------- Pengaturan tersimpan ----------------
    def _file_pengaturan(self):
        return os.path.join(self.user_data_dir, "pengaturan.json")

    def _muat_pengaturan(self):
        try:
            with open(self._file_pengaturan()) as f:
                d = json.load(f)
            if d.get("mode") in MODE:
                self.mode = d["mode"]
            bg = d.get("bg")
            if bg and os.path.exists(bg):
                self.bg_path = bg
        except Exception:
            pass

    def _simpan_pengaturan(self):
        try:
            with open(self._file_pengaturan(), "w") as f:
                json.dump({"mode": self.mode, "bg": self.bg_path}, f)
        except Exception:
            pass

    # ---------------- Background ----------------
    def _pasang_background(self, path):
        if path and os.path.exists(path):
            self.bg.source = path
            self.bg.opacity = 1
            try:
                self.bg.reload()
            except Exception:
                pass
        else:
            self.bg.source = ""
            self.bg.opacity = 0

    def buka_pilih_gambar(self, *a):
        fc = FileChooserListView(
            path=folder_awal(),
            filters=[lambda folder, nama: nama.lower().endswith(EKSTENSI_GAMBAR)])
        kotak = BoxLayout(orientation="vertical", spacing=dp(8))
        kotak.add_widget(fc)
        baris = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        b_batal = Button(text="Batal")
        b_pilih = Button(text="Pilih", background_normal="",
                         background_color=BIRU_TOMBOL)
        baris.add_widget(b_batal)
        baris.add_widget(b_pilih)
        kotak.add_widget(baris)
        pop = Popup(title="Pilih gambar background", content=kotak,
                    size_hint=(0.9, 0.9))

        def pilih(*_):
            if fc.selection:
                self.bg_path = fc.selection[0]
                self._pasang_background(self.bg_path)
                self._simpan_pengaturan()
                pop.dismiss()

        b_batal.bind(on_release=pop.dismiss)
        b_pilih.bind(on_release=pilih)
        pop.open()

    # ---------------- Menu gear ----------------
    def buka_pengaturan(self, *a):
        try:
            self._buka_pengaturan()
        except Exception as e:
            Popup(title="Error", size_hint=(0.7, 0.4),
                  content=Label(text=str(e), font_size=sp(14))).open()

    def _buka_pengaturan(self):
        kotak = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))

        kotak.add_widget(Label(
            text="Made by rfzz with claude ai", font_size=sp(16),
            color=(0.85, 0.9, 1, 1), size_hint_y=None, height=dp(30)))

        b_bg = Button(text="Ganti Background", font_size=sp(18),
                      size_hint_y=None, height=dp(56),
                      background_normal="", background_color=BIRU_TOMBOL)
        kotak.add_widget(b_bg)

        kotak.add_widget(Label(text="Pilih Dadu", font_size=sp(16),
                               size_hint_y=None, height=dp(28)))
        baris = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10))
        t9 = ToggleButton(text="Dadu 9D", group="mode", font_size=sp(18),
                          allow_no_selection=False,
                          state="down" if self.mode == 9 else "normal",
                          background_normal="", background_down="")
        t1 = ToggleButton(text="Dadu 1D", group="mode", font_size=sp(18),
                          allow_no_selection=False,
                          state="down" if self.mode == 1 else "normal",
                          background_normal="", background_down="")
        for t in (t9, t1):
            t.bind(state=style_toggle)
            style_toggle(t)
            baris.add_widget(t)
        kotak.add_widget(baris)

        kotak.add_widget(Label(
            text="9D: 9-31 = K, 32-54 = B\n1D: 1-3 = K, 4-6 = B",
            font_size=sp(13), color=(0.8, 0.85, 1, 1),
            size_hint_y=None, height=dp(44)))

        b_tutup = Button(text="Tutup", size_hint_y=None, height=dp(52))
        kotak.add_widget(b_tutup)

        pop = Popup(title="Pengaturan", content=kotak, size_hint=(0.62, 0.82))
        b_bg.bind(on_release=self.buka_pilih_gambar)
        t9.bind(on_release=lambda *_: self.set_mode(9))
        t1.bind(on_release=lambda *_: self.set_mode(1))
        b_tutup.bind(on_release=pop.dismiss)
        pop.open()

    # ---------------- Mode dadu ----------------
    def _bangun_dadu(self):
        cfg = MODE[self.mode]
        self.grid.clear_widgets()
        self.grid.cols = cfg["cols"]
        self.dadu = [Die() for _ in range(cfg["jumlah"])]
        for d in self.dadu:
            self.grid.add_widget(d)

    def _update_teks_mode(self):
        cfg = MODE[self.mode]
        k = cfg["k_max"]
        self.lbl_sub.text = (
            "[color=33dd80]K (Kecil) : %s[/color]    |    "
            "[color=ff8c26]B (Besar) : %d - %d[/color]" % (
                "1 - %d" % k if self.mode == 1 else "9 - %d" % k,
                k + 1, cfg["maks"]))
        self.lbl_judul_total.text = "TOTAL" if self.mode == 9 else "ANGKA"

    def set_mode(self, n):
        if n == self.mode:
            return
        Clock.unschedule(self._animasi)
        self.sedang_roll = False
        self.btn.disabled = False
        self.btn.text = "ROLL"
        self.mode = n
        self.riwayat = []
        self.nomor_game = 0
        self.hitung_k = 0
        self.hitung_b = 0
        self._bangun_dadu()
        self._update_teks_mode()
        self.lbl_total.text = "-"
        self.lbl_hasil.text = "SIAP?"
        self.lbl_hasil.color = (0.8, 0.85, 1, 1)
        self.lbl_stat.text = "K: 0   |   B: 0"
        self.lbl_riwayat.text = "-"
        self._simpan_pengaturan()

    # ---------------- Logika roll ----------------
    def roll(self, *a):
        if self.sedang_roll:
            return
        self.sedang_roll = True
        self.btn.disabled = True
        self.btn.text = "..."
        self.lbl_hasil.text = "MENGACAK..."
        self.lbl_hasil.color = (0.8, 0.85, 1, 1)
        self.tick = 0
        Clock.schedule_interval(self._animasi, 0.07)

    def _animasi(self, dt):
        self.tick += 1
        if self.tick < 16:
            for d in self.dadu:
                d.text = str(random.randint(1, 6))
            return True
        nilai = [random.randint(1, 6) for _ in self.dadu]
        for d, n in zip(self.dadu, nilai):
            d.text = str(n)
        self._tampilkan(sum(nilai))
        return False

    def _tampilkan(self, total):
        kecil = total <= MODE[self.mode]["k_max"]
        huruf = "K" if kecil else "B"
        warna = HIJAU_K if kecil else ORANYE_B

        self.lbl_total.text = str(total)
        self.lbl_hasil.text = "KECIL (K)" if kecil else "BESAR (B)"
        self.lbl_hasil.color = warna
        self.lbl_hasil.opacity = 0
        Animation(opacity=1, duration=0.4).start(self.lbl_hasil)

        if kecil:
            self.hitung_k += 1
        else:
            self.hitung_b += 1
        self.lbl_stat.text = "K: %d   |   B: %d" % (self.hitung_k, self.hitung_b)

        self.nomor_game += 1
        self.riwayat.append((self.nomor_game, huruf))
        self.riwayat = self.riwayat[-5:]
        self.lbl_riwayat.text = "   ".join(
            "G%d %s" % (n, "[color=33dd80][b]K[/b][/color]" if h == "K"
                        else "[color=ff8c26][b]B[/b][/color]")
            for n, h in self.riwayat)

        self.btn.text = "ROLL"
        self.btn.disabled = False
        self.sedang_roll = False


if __name__ == "__main__":
    DaduApp().run()
