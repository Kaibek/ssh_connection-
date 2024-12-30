import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
import os

def compress_file(file_path, archive_name):
    """Функция для сжатия одного файла в ZIP-архив."""
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, os.path.basename(file_path))

def select_file_and_compress():
    """Открывает диалоговое окно для выбора файла и затем сжимает его."""
    global root
    file_path = filedialog.askopenfilename(title="Выберите файл для сжатия",
                                           filetypes=[("Все файлы", "*.*")])
    if file_path:
        archive_name = os.path.splitext(file_path)[0] + ".zip"
        compress_file(file_path, archive_name)
        messagebox.showinfo("Успех!", f"Файл '{file_path}' успешно сжат в архив '{archive_name}'.")

root = tk.Tk()
root.title("Архиватор файлов")

button = tk.Button(root, text="Выбрать файл для сжатия", command=select_file_and_compress)
button.pack(pady=10)

root.mainloop()



