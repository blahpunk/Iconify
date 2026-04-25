from __future__ import annotations

import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageTk

from . import cli_install
from .converter import IconifyOptions, convert_image, render_icon_preview

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
TRANSPARENT = "transparent"


class IconifyApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=18)
        self.root = root
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.shape = tk.StringVar(value="square")
        self.radius = tk.IntVar(value=18)
        self.padding = tk.IntVar(value=0)
        self.background = tk.StringVar(value=TRANSPARENT)
        self.status = tk.StringVar(value="Choose an image to begin.")
        self._preview_job: str | None = None
        self._preview_image: ImageTk.PhotoImage | None = None
        self._last_preview_error = ""
        self._build()
        self._wire_preview_updates()
        self.root.after(300, self._maybe_prompt_cli_install)

    def _build(self) -> None:
        self.root.title("Iconify")
        self.root.minsize(820, 520)
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.columnconfigure(0, minsize=340)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        title = ttk.Label(self, text="Iconify", font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="nsew", padx=(0, 18))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Source image").grid(row=0, column=0, sticky="w")
        ttk.Entry(controls, textvariable=self.input_path).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(controls, text="Browse", command=self._choose_input).grid(row=1, column=2, sticky="ew", padx=(8, 0), pady=(4, 0))

        ttk.Label(controls, text="Output icon").grid(row=2, column=0, sticky="w", pady=(16, 0))
        ttk.Entry(controls, textvariable=self.output_path).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(controls, text="Save As", command=self._choose_output).grid(row=3, column=2, sticky="ew", padx=(8, 0), pady=(4, 0))

        ttk.Label(controls, text="Shape").grid(row=4, column=0, sticky="w", pady=(18, 0))
        shape_frame = ttk.Frame(controls)
        shape_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))
        for value in ("square", "rounded", "circle", "squircle"):
            ttk.Radiobutton(shape_frame, text=value.title(), value=value, variable=self.shape).pack(side="left", padx=(0, 12))

        ttk.Label(controls, text="Corner radius").grid(row=6, column=0, sticky="w", pady=(18, 0))
        ttk.Scale(controls, variable=self.radius, from_=0, to=50, orient="horizontal").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Label(controls, textvariable=self.radius, width=4).grid(row=7, column=2, sticky="e", pady=(6, 0))

        ttk.Label(controls, text="Padding").grid(row=8, column=0, sticky="w", pady=(16, 0))
        ttk.Scale(controls, variable=self.padding, from_=0, to=45, orient="horizontal").grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        ttk.Label(controls, textvariable=self.padding, width=4).grid(row=9, column=2, sticky="e", pady=(6, 0))

        ttk.Label(controls, text="Background").grid(row=10, column=0, sticky="w", pady=(16, 0))
        ttk.Entry(controls, textvariable=self.background).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(controls, text="Color", command=self._choose_color).grid(row=11, column=2, sticky="ew", padx=(8, 0), pady=(4, 0))

        cli_row = ttk.Frame(controls)
        cli_row.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(24, 0))
        ttk.Button(cli_row, text="Install CLI", command=self._install_cli).pack(side="left")
        ttk.Button(cli_row, text="Test CLI", command=self._test_cli).pack(side="left", padx=(8, 0))
        ttk.Button(cli_row, text="Uninstall CLI", command=self._uninstall_cli).pack(side="left", padx=(8, 0))

        button_row = ttk.Frame(controls)
        button_row.grid(row=13, column=0, columnspan=3, sticky="ew", pady=(18, 0))
        button_row.columnconfigure(0, weight=1)
        ttk.Button(button_row, text="Convert", command=self._convert).grid(row=0, column=1, sticky="e")

        ttk.Label(controls, textvariable=self.status, foreground="#345", wraplength=320).grid(
            row=14, column=0, columnspan=3, sticky="w", pady=(18, 0)
        )

        preview_frame = ttk.Frame(self)
        preview_frame.grid(row=1, column=1, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.preview = tk.Canvas(preview_frame, highlightthickness=1, highlightbackground="#9aa6b2", bg="#f5f7fa")
        self.preview.grid(row=0, column=0, sticky="nsew")
        self.preview.bind("<Configure>", lambda _event: self._schedule_preview())
        self._draw_empty_preview()

    def _wire_preview_updates(self) -> None:
        for variable in (self.input_path, self.shape, self.radius, self.padding, self.background):
            variable.trace_add("write", lambda *_args: self._schedule_preview())

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

    def _choose_color(self) -> None:
        current = self._normalized_background()
        if current == TRANSPARENT:
            current = "#ffffff"
        _rgb, hex_value = colorchooser.askcolor(color=current, title="Choose background color")
        if hex_value:
            self.background.set(hex_value.lower())

    def _maybe_prompt_cli_install(self) -> None:
        if cli_install.cli_prompt_suppressed() or cli_install.found_cli():
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Install command line access")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.grid(sticky="nsew")
        ttk.Label(
            frame,
            text="Install the iconify command for terminal use?",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(
            frame,
            text="This copies the packaged app to a user install location and adds the command to your user PATH.",
            wraplength=420,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 14))

        dont_ask = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Do not ask again", variable=dont_ask).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(0, 16)
        )

        def close_with_suppression() -> None:
            if dont_ask.get():
                cli_install.set_cli_prompt_suppressed(True)
            dialog.destroy()

        def install_and_close() -> None:
            if dont_ask.get():
                cli_install.set_cli_prompt_suppressed(True)
            dialog.destroy()
            self._install_cli()

        ttk.Button(frame, text="Install", command=install_and_close).grid(row=3, column=0, sticky="e")
        ttk.Button(frame, text="Not Now", command=close_with_suppression).grid(row=3, column=1, sticky="e", padx=(8, 0))
        ttk.Button(frame, text="Never Ask", command=lambda: (cli_install.set_cli_prompt_suppressed(True), dialog.destroy())).grid(
            row=3, column=2, sticky="e", padx=(8, 0)
        )

    def _install_cli(self) -> None:
        ok, message = cli_install.install_cli()
        self.status.set(message)
        if ok:
            messagebox.showinfo("Iconify", message)
        else:
            messagebox.showwarning("Iconify", message)

    def _test_cli(self) -> None:
        ok, message = cli_install.test_cli()
        self.status.set(message)
        if ok:
            messagebox.showinfo("Iconify", message)
        else:
            messagebox.showwarning("Iconify", message)

    def _uninstall_cli(self) -> None:
        ok, message = cli_install.uninstall_cli()
        self.status.set(message)
        if ok:
            messagebox.showinfo("Iconify", message)
        else:
            messagebox.showwarning("Iconify", message)

    def _convert(self) -> None:
        if not self.input_path.get():
            messagebox.showwarning("Iconify", "Choose a source image first.")
            return
        if not self._validate_background():
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
                    background=self._normalized_background(),
                    padding=int(self.padding.get()),
                ),
            )
        except Exception as exc:
            message = str(exc)
            self.root.after(0, lambda: self._fail(message))
            return
        self.root.after(0, lambda: self._succeed(output))

    def _schedule_preview(self) -> None:
        if self._preview_job:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(90, self._update_preview)

    def _update_preview(self) -> None:
        self._preview_job = None
        if not self.input_path.get():
            self._draw_empty_preview()
            return
        if not self._valid_background_value():
            self._draw_message("Enter #ffffff or transparent")
            return

        canvas_size = max(64, min(self.preview.winfo_width(), self.preview.winfo_height()) - 42)
        try:
            image = render_icon_preview(
                self.input_path.get(),
                canvas_size,
                shape=self.shape.get(),
                radius=int(self.radius.get()),
                background=self._normalized_background(),
                padding=int(self.padding.get()),
            )
        except Exception as exc:
            message = str(exc)
            if message != self._last_preview_error:
                self.status.set(message)
                self._last_preview_error = message
            self._draw_message("Preview unavailable")
            return

        self._last_preview_error = ""
        preview = self._checkerboard(canvas_size)
        preview.alpha_composite(image)
        self._preview_image = ImageTk.PhotoImage(preview)
        self.preview.delete("all")
        x = self.preview.winfo_width() // 2
        y = self.preview.winfo_height() // 2
        self.preview.create_image(x, y, image=self._preview_image)
        self.status.set("Preview ready.")

    def _draw_empty_preview(self) -> None:
        self._draw_message("Preview")

    def _draw_message(self, message: str) -> None:
        self.preview.delete("all")
        self.preview.create_text(
            max(1, self.preview.winfo_width() // 2),
            max(1, self.preview.winfo_height() // 2),
            text=message,
            fill="#536273",
            font=("Segoe UI", 14),
        )

    def _validate_background(self) -> bool:
        if self._valid_background_value():
            return True
        messagebox.showerror("Iconify", "Background must be a hex color like #ffffff or transparent.")
        return False

    def _normalized_background(self) -> str:
        value = self.background.get().strip().lower()
        return value if value else TRANSPARENT

    def _valid_background_value(self) -> bool:
        value = self.background.get().strip().lower()
        return value in {"", TRANSPARENT} or HEX_COLOR.fullmatch(value) is not None

    @staticmethod
    def _checkerboard(size: int) -> Image.Image:
        image = Image.new("RGBA", (size, size), "#ffffff")
        draw = ImageDraw.Draw(image)
        block = max(8, size // 24)
        for y in range(0, size, block):
            for x in range(0, size, block):
                if (x // block + y // block) % 2:
                    draw.rectangle((x, y, x + block - 1, y + block - 1), fill="#edf1f5")
        return image

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
