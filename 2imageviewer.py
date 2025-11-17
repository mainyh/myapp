"""Simple GUI to pick two folders and view their images side by side.

Dependencies: Pillow (pip install pillow)
"""

import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError as exc:  # pragma: no cover - pillow must be installed at runtime
    raise SystemExit(
        "Pillow 가 필요합니다. 먼저 `pip install pillow` 로 설치해주세요."
    ) from exc


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
FONT_FAMILY = "Pretendard"


class ImagePanel:
    """Encapsulates UI and state for one side of the viewer."""

    def __init__(self, root: tk.Frame, title: str):
        self.root = root
        self.title = title
        self.folder = ""
        self.images: list[str] = []
        self.index = 0
        self.photo_ref = None  # keep reference to avoid GC

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root)
        header.pack(fill="x", pady=(4, 2))

        tk.Label(header, text=self.title, font=(FONT_FAMILY, 10, "bold")).pack(side="left")
        tk.Button(header, text="폴더 선택", command=self.choose_folder).pack(
            side="right", padx=4
        )

        self.folder_label = tk.Label(
            self.root, text="선택된 폴더 없음", anchor="w", fg="gray"
        )
        self.folder_label.pack(fill="x", padx=4)

        self.canvas = tk.Label(self.root, bg="#f0f0f0", width=60, height=30)
        self.canvas.pack(expand=True, fill="both", padx=4, pady=6)

        controls = tk.Frame(self.root)
        controls.pack(fill="x", pady=(0, 8))
        tk.Button(controls, text="◀ 이전", command=self.prev_image).pack(side="left")
        tk.Button(controls, text="다음 ▶", command=self.next_image).pack(side="right")
        self.status = tk.Label(controls, text="0 / 0", anchor="center")
        self.status.pack(side="bottom", fill="x")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title=f"{self.title} 폴더 선택")
        if not folder:
            return
        self.folder = folder
        self.folder_label.config(text=folder, fg="black")
        self._load_images()

    def _load_images(self) -> None:
        self.images = [
            os.path.join(self.folder, f)
            for f in sorted(os.listdir(self.folder))
            if os.path.splitext(f.lower())[1] in IMAGE_EXTENSIONS
        ]
        self.index = 0
        if not self.images:
            self._update_status()
            messagebox.showinfo(self.title, "이미지 파일이 없습니다.")
            self._clear_canvas()
            return
        self.show_image()

    def _clear_canvas(self) -> None:
        self.canvas.config(image="", text="이미지 없음", compound="center", bg="#f0f0f0")
        self.photo_ref = None

    def _update_status(self) -> None:
        total = len(self.images)
        self.status.config(text=f"{self.index + 1 if total else 0} / {total}")

    def _load_and_resize(self, path: str) -> ImageTk.PhotoImage:
        img = Image.open(path)
        # Determine target size using widget dimensions; fallback to 600x600.
        width = max(self.canvas.winfo_width(), 200)
        height = max(self.canvas.winfo_height(), 200)
        img.thumbnail((width - 20, height - 20), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def show_image(self) -> None:
        if not self.images:
            self._clear_canvas()
            return

        path = self.images[self.index]
        try:
            photo = self._load_and_resize(path)
        except Exception as exc:  # pragma: no cover - runtime guard
            messagebox.showerror(self.title, f"이미지를 열 수 없습니다:\n{path}\n{exc}")
            return

        self.photo_ref = photo
        filename = os.path.basename(path)
        self.canvas.config(image=photo, text=filename, compound="bottom", bg="white")
        self._update_status()

    def next_image(self) -> None:
        if not self.images:
            return
        self.index = (self.index + 1) % len(self.images)
        self.show_image()

    def prev_image(self) -> None:
        if not self.images:
            return
        self.index = (self.index - 1) % len(self.images)
        self.show_image()


class DualImageViewer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        # Apply Pretendard as the default UI font.
        base_font = tkfont.nametofont("TkDefaultFont")
        base_font.configure(family=FONT_FAMILY, size=12)
        self.option_add("*Font", base_font)
        # Keep DPI scaling neutral so 폰트가 흐릿해지지 않도록 한다.
        self.tk.call("tk", "scaling", 1.0)
        self.title("Dual Image Viewer")
        self.geometry("1200x700")
        self._build_layout()

    def _build_layout(self) -> None:
        container = tk.Frame(self)
        container.pack(expand=True, fill="both")
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=0)

        left_frame = tk.LabelFrame(container, text="폴더 1")
        right_frame = tk.LabelFrame(container, text="폴더 2")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.left_panel = ImagePanel(left_frame, "폴더 1")
        self.right_panel = ImagePanel(right_frame, "폴더 2")

        # Shared controls to move both panels together.
        shared_controls = tk.Frame(container)
        shared_controls.grid(row=1, column=0, columnspan=2, pady=(0, 8))
        tk.Button(
            shared_controls, text="◀ 이전 (동시)", width=12, command=self.prev_both
        ).pack(side="left", padx=8)
        tk.Button(
            shared_controls, text="다음 ▶ (동시)", width=12, command=self.next_both
        ).pack(side="right", padx=8)

    def next_both(self) -> None:
        self.left_panel.next_image()
        self.right_panel.next_image()

    def prev_both(self) -> None:
        self.left_panel.prev_image()
        self.right_panel.prev_image()


def main() -> None:
    app = DualImageViewer()
    app.mainloop()


if __name__ == "__main__":
    main()
