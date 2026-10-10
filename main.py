
import os
import tempfile
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image
from pathlib import Path


class PNGConverter(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Fake PNG Converter")
        self.geometry("720x600")
        self.minsize(600, 500)

        self.files = []
        self.replace_var = tk.BooleanVar(value=False)

        ctk.CTkLabel(
            self,
            text="Fake PNG Converter",
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(24, 5))

        ctk.CTkLabel(
            self,
            text="Drop gambar di bawah untuk mengonversi",
        ).pack(pady=(0, 18))

        # Drag-and-drop area
        self.drop_area = ctk.CTkFrame(
            self, height=130, border_width=2
        )
        self.drop_area.pack(
            fill="x", padx=25, pady=5
        )
        self.drop_area.pack_propagate(False)

        self.drop_label = ctk.CTkLabel(
            self.drop_area,
            text="⬇\nDrag & Drop file gambar di sini\natau klik tombol Pilih File",
            font=("Segoe UI", 16),
        )
        self.drop_label.pack(expand=True, fill="both")

        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind(
            "<<Drop>>", self.handle_drop
        )
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind(
            "<<Drop>>", self.handle_drop
        )

        ctk.CTkButton(
            self,
            text="Pilih File",
            command=self.select_files,
        ).pack(pady=10)

        self.file_label = ctk.CTkLabel(
            self, text="Belum ada file dipilih"
        )
        self.file_label.pack(pady=4)

        ctk.CTkCheckBox(
            self,
            text="Replace file asli jika ekstensi .png",
            variable=self.replace_var,
        ).pack(pady=8)

        ctk.CTkLabel(
            self,
            text="Tanpa replace: hasil disimpan sebagai file PNG baru di folder asal.",
            wraplength=650,
        ).pack(pady=3)

        self.progress = ctk.CTkProgressBar(
            self, width=500
        )
        self.progress.pack(pady=(16, 5))
        self.progress.set(0)

        self.status = ctk.CTkLabel(
            self, text="Siap"
        )
        self.status.pack(pady=5)

        ctk.CTkButton(
            self,
            text="Konversi ke PNG",
            height=42,
            command=self.convert_files,
        ).pack(pady=15)

    def add_files(self, paths):
        supported = {
            ".png", ".jpg", ".jpeg", ".webp",
            ".bmp", ".gif", ".tif", ".tiff"
        }

        for path in paths:
            p = Path(path)
            if p.is_file() and p.suffix.lower() in supported:
                if str(p.resolve()) not in [
                    str(Path(f).resolve()) for f in self.files
                ]:
                    self.files.append(str(p))

        self.file_label.configure(
            text=f"{len(self.files)} file dipilih"
        )

    def handle_drop(self, event):
        paths = self.tk.splitlist(event.data)
        self.add_files(paths)

    def select_files(self):
        paths = filedialog.askopenfilenames(
            title="Pilih gambar",
            filetypes=[
                ("File gambar", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff"),
                ("Semua file", "*.*"),
            ],
        )
        self.add_files(paths)

    def convert_files(self):
        if not self.files:
            messagebox.showwarning(
                "Peringatan", "Pilih atau drop file terlebih dahulu."
            )
            return

        replace = self.replace_var.get()

        if replace and any(
            Path(f).suffix.lower() == ".png" for f in self.files
        ):
            confirm = messagebox.askyesno(
                "Konfirmasi Replace",
                "File .png asli akan ditimpa secara permanen.\n"
                "Sebaiknya buat backup terlebih dahulu.\n\nLanjutkan?",
            )
            if not confirm:
                return

        total = len(self.files)
        success = 0
        errors = []

        self.progress.set(0)

        for index, file in enumerate(self.files, start=1):
            source = Path(file)
            temp_path = None

            try:
                # Decode the actual image, regardless of its extension.
                with Image.open(source) as image:
                    image.load()
                    png_image = image.convert(
                        "RGBA" if "A" in image.getbands() else "RGB"
                    )

                # Replace only PNG-named files when explicitly enabled.
                if replace and source.suffix.lower() == ".png":
                    destination = source
                else:
                    destination = source.with_suffix(".png")

                    # Never overwrite an unrelated existing file.
                    if destination.exists():
                        raise FileExistsError(
                            f"{destination.name} sudah ada."
                        )

                # Write to a temporary PNG first.
                fd, temp_name = tempfile.mkstemp(
                    suffix=".png", dir=str(destination.parent)
                )
                os.close(fd)
                temp_path = Path(temp_name)

                png_image.save(temp_path, format="PNG")
                png_image.close()

                # Atomic replacement after successful encoding.
                os.replace(temp_path, destination)
                temp_path = None
                success += 1

            except Exception as error:
                errors.append(f"{source.name}: {error}")

            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

            self.progress.set(index / total)
            self.status.configure(
                text=f"Memproses {index}/{total}"
            )
            self.update_idletasks()

        self.status.configure(text="Konversi selesai")

        result = f"Berhasil: {success}/{total}"

        if errors:
            result += "\n\nGagal:\n" + "\n".join(errors[:8])

        messagebox.showinfo("Hasil Konversi", result)


if __name__ == "__main__":
    app = PNGConverter()
    app.mainloop()
