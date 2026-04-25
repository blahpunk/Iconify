from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .converter import DEFAULT_SIZES, IconifyOptions, convert_image, normalize_sizes


class IconifyApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=20)
        self.root = root
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.shape = tk.StringVar(value="square")
        self.radius = tk.IntVar(value=18)
        self.padding = tk.IntVar(value=0)
        self.background = tk.StringVar(value="transparent")
        self.sizes = tk.StringVar(value=",".join(str(size) for size in DEFAULT_SIZES))
        self.status = tk.StringVar(value="Choose an image to begin.")
        self._build()

    def _build(self) -> None:
        self.root.title("Iconify")
        self.root.minsize(620, 430)
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        title = ttk.Label(self, text="Iconify", font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 18))

        ttk.Label(self, text="Source image").grid(row=1, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.input_path).grid(row=1, column=1, sticky="ew", padx=10)
        ttk.Button(self, text="Browse", command=self._choose_input).grid(row=1, column=2, sticky="ew")

        ttk.Label(self, text="Output icon").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(self, textvariable=self.output_path).grid(row=2, column=1, sticky="ew", padx=10, pady=(12, 0))
        ttk.Button(self, text="Save As", command=self._choose_output).grid(row=2, column=2, sticky="ew", pady=(12, 0))

        ttk.Label(self, text="Shape").grid(row=3, column=0, sticky="w", pady=(18, 0))
        shape_frame = ttk.Frame(self)
        shape_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=(18, 0))
        for value in ("square", "rounded", "circle", "squircle"):
            ttk.Radiobutton(shape_frame, text=value.title(), value=value, variable=self.shape).pack(side="left", padx=(0, 14))

        ttk.Label(self, text="Corner radius").grid(row=4, column=0, sticky="w", pady=(18, 0))
        ttk.Scale(self, variable=self.radius, from_=0, to=50, orient="horizontal").grid(
            row=4, column=1, sticky="ew", padx=10, pady=(18, 0)
        )
        ttk.Label(self, textvariable=self.radius).grid(row=4, column=2, sticky="w", pady=(18, 0))

        ttk.Label(self, text="Padding").grid(row=5, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(self, variable=self.padding, from_=0, to=45, orient="horizontal").grid(
            row=5, column=1, sticky="ew", padx=10, pady=(12, 0)
        )
        ttk.Label(self, textvariable=self.padding).grid(row=5, column=2, sticky="w", pady=(12, 0))

        ttk.Label(self, text="Sizes").grid(row=6, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(self, textvariable=self.sizes).grid(row=6, column=1, columnspan=2, sticky="ew", padx=10, pady=(12, 0))

        ttk.Label(self, text="Background").grid(row=7, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(self, textvariable=self.background).grid(row=7, column=1, columnspan=2, sticky="ew", padx=10, pady=(12, 0))

        button_row = ttk.Frame(self)
        button_row.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(24, 0))
        button_row.columnconfigure(0, weight=1)
        ttk.Button(button_row, text="Convert", command=self._convert).grid(row=0, column=1, sticky="e")

        status = ttk.Label(self, textvariable=self.status, foreground="#345")
        status.grid(row=9, column=0, columnspan=3, sticky="w", pady=(18, 0))

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose source image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        source = Path(path)
        self.input_path.set(str(source))
        if not self.output_path.get():
            self.output_path.set(str(source.with_suffix(".ico")))

    def _choose_output(self) -> None:
        initial = self.output_path.get() or "icon.ico"
        path = filedialog.asksaveasfilename(
            title="Save icon",
            defaultextension=".ico",
            initialfile=Path(initial).name,
            filetypes=[("Windows icon", "*.ico"), ("All files", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _convert(self) -> None:
        if not self.input_path.get():
            messagebox.showwarning("Iconify", "Choose a source image first.")
            return

        self.status.set("Converting...")
        thread = threading.Thread(target=self._convert_worker, daemon=True)
        thread.start()

    def _convert_worker(self) -> None:
        try:
            output = convert_image(
                self.input_path.get(),
                IconifyOptions(
                    output=Path(self.output_path.get()) if self.output_path.get() else None,
                    shape=self.shape.get(),
                    radius=int(self.radius.get()),
                    sizes=normalize_sizes(self.sizes.get()),
                    background=self.background.get(),
                    padding=int(self.padding.get()),
                ),
            )
        except Exception as exc:
            message = str(exc)
            self.root.after(0, lambda: self._fail(message))
            return
        self.root.after(0, lambda: self._succeed(output))

    def _succeed(self, output: Path) -> None:
        self.output_path.set(str(output))
        self.status.set(f"Created {output}")
        messagebox.showinfo("Iconify", f"Created:\n{output}")

    def _fail(self, message: str) -> None:
        self.status.set("Conversion failed.")
        messagebox.showerror("Iconify", message)


def run() -> None:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.25)
        ttk.Style().theme_use("vista" if root.tk.call("tk", "windowingsystem") == "win32" else "clam")
    except tk.TclError:
        pass
    IconifyApp(root)
    root.mainloop()
