import tkinter as tk
from tkinter import filedialog, messagebox
import os
import glob
from PIL import Image, ImageTk

class YOLOAnnotator:
    def __init__(self, window):
        self.window = window
        self.window.title("Rat Head & Body YOLO Annotator")

        # Image list
        self.image_paths = []
        self.current_index = 0

        self.current_image = None
        self.photo = None
        self.img_width = 0
        self.img_height = 0

        # Annotation step: 'head', 'body', or 'complete'
        self.current_step = 'head'

        # Head annotation
        self.head_bbox = None       # (x1, y1, x2, y2) in pixels
        self.head_rect_id = None    # Canvas item ID

        # Body annotation
        self.body_bbox = None
        self.body_rect_id = None

        # Temporary drawing state
        self.rect_start_x = None
        self.rect_start_y = None
        self.drawing_rect_id = None

        # --- GUI LAYOUT ---
        self.top_frame = tk.Frame(window)
        self.top_frame.pack(side=tk.TOP, pady=10)

        self.btn_load = tk.Button(self.top_frame, text="1. Load Image Folder", command=self.load_folder, width=20)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.lbl_progress = tk.Label(self.top_frame, text="Image: 0 / 0", width=15)
        self.lbl_progress.pack(side=tk.LEFT, padx=10)

        self.btn_prev = tk.Button(self.top_frame, text="<< Prev", command=self.prev_image, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_next = tk.Button(self.top_frame, text="Save & Next >>", command=self.save_and_next, state=tk.DISABLED, bg="lightgreen")
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.btn_clear_head = tk.Button(self.top_frame, text="Clear Head", command=self.clear_head, state=tk.DISABLED, bg="#ffcccc")
        self.btn_clear_head.pack(side=tk.LEFT, padx=5)

        self.btn_clear_body = tk.Button(self.top_frame, text="Clear Body", command=self.clear_body, state=tk.DISABLED, bg="#cce0ff")
        self.btn_clear_body.pack(side=tk.LEFT, padx=5)

        # Step indicator
        self.step_frame = tk.Frame(window)
        self.step_frame.pack(side=tk.TOP, pady=(0, 5))

        self.lbl_step = tk.Label(self.step_frame, text="Load a folder to begin.", font=("Arial", 11, "bold"), fg="gray")
        self.lbl_step.pack()

        # Canvas
        self.canvas = tk.Canvas(window, width=800, height=600, bg="gray")
        self.canvas.pack(padx=10, pady=10)

        # Mouse bindings for drawing
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Escape to skip current annotation step
        self.window.bind("<Escape>", self.on_escape)

    # --- STEP INDICATOR ---
    def update_step_label(self):
        if self.current_step == 'head':
            self.lbl_step.config(text="Step 1 of 2: Draw Head Bounding Box  (Esc to skip)", fg="green")
        elif self.current_step == 'body':
            self.lbl_step.config(text="Step 2 of 2: Draw Body Bounding Box  (Esc to skip)", fg="blue")
        elif self.current_step == 'complete':
            self.lbl_step.config(text="Annotations complete. Click Save & Next.", fg="gray")

    # --- FILE HANDLING ---
    def load_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder with Extracted Frames")
        if not folder_path:
            return

        search_path = os.path.join(folder_path, "*.[jp][pn]g")
        self.image_paths = sorted(glob.glob(search_path))
        search_path_upper = os.path.join(folder_path, "*.[JP][PN]G")
        self.image_paths.extend(sorted(glob.glob(search_path_upper)))

        if not self.image_paths:
            messagebox.showwarning("No Images", "Could not find any JPG or PNG images in that folder.")
            return

        self.current_index = 0
        self.btn_next.config(state=tk.NORMAL)
        self.btn_prev.config(state=tk.NORMAL)
        self.btn_clear_head.config(state=tk.NORMAL)
        self.btn_clear_body.config(state=tk.NORMAL)

        self.load_image()

    def load_image(self):
        self.reset_annotations()

        img_path = self.image_paths[self.current_index]
        self.current_image = Image.open(img_path)
        self.img_width, self.img_height = self.current_image.size

        self.canvas.config(width=self.img_width, height=self.img_height)
        self.photo = ImageTk.PhotoImage(self.current_image)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.lbl_progress.config(text=f"Image: {self.current_index + 1} / {len(self.image_paths)}")

        self.check_existing_annotation(img_path)
        self.update_step_label()

    def reset_annotations(self):
        """Clear all annotation state for a fresh image load."""
        self.head_bbox = None
        self.body_bbox = None
        self.head_rect_id = None
        self.body_rect_id = None
        self.drawing_rect_id = None
        self.rect_start_x = None
        self.rect_start_y = None
        self.current_step = 'head'

    # --- DRAWING LOGIC ---
    def on_mouse_down(self, event):
        if self.current_step == 'complete':
            return
        self.rect_start_x = event.x
        self.rect_start_y = event.y
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None

    def on_mouse_drag(self, event):
        if self.current_step == 'complete' or not self.rect_start_x:
            return
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
        color = "green" if self.current_step == 'head' else "blue"
        self.drawing_rect_id = self.canvas.create_rectangle(
            self.rect_start_x, self.rect_start_y, event.x, event.y,
            outline=color, width=2, dash=(4, 4)
        )

    def on_mouse_up(self, event):
        if self.current_step == 'complete' or not self.rect_start_x:
            return

        x1 = min(self.rect_start_x, event.x)
        y1 = min(self.rect_start_y, event.y)
        x2 = max(self.rect_start_x, event.x)
        y2 = max(self.rect_start_y, event.y)

        x1 = max(0, min(x1, self.img_width))
        y1 = max(0, min(y1, self.img_height))
        x2 = max(0, min(x2, self.img_width))
        y2 = max(0, min(y2, self.img_height))

        w = x2 - x1
        h = y2 - y1

        if w > 10 and h > 10:
            bbox = (x1, y1, x2, y2)
            if self.current_step == 'head':
                self.show_confirmation_dialog(
                    "Head Annotation Complete",
                    on_redraw=self.redraw_head,
                    on_finished=lambda: self.finish_head(bbox)
                )
            elif self.current_step == 'body':
                self.show_confirmation_dialog(
                    "Body Annotation Complete",
                    on_redraw=self.redraw_body,
                    on_finished=lambda: self.finish_body(bbox)
                )
        else:
            if self.drawing_rect_id:
                self.canvas.delete(self.drawing_rect_id)
                self.drawing_rect_id = None

    def redraw_head(self):
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None
        self.rect_start_x = None

    def redraw_body(self):
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None
        self.rect_start_x = None

    def finish_head(self, bbox):
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None
        if self.head_rect_id:
            self.canvas.delete(self.head_rect_id)
        self.head_bbox = bbox
        self.head_rect_id = self.canvas.create_rectangle(
            bbox[0], bbox[1], bbox[2], bbox[3], outline="green", width=3
        )
        self.current_step = 'body'
        self.update_step_label()

    def finish_body(self, bbox):
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None
        if self.body_rect_id:
            self.canvas.delete(self.body_rect_id)
        self.body_bbox = bbox
        self.body_rect_id = self.canvas.create_rectangle(
            bbox[0], bbox[1], bbox[2], bbox[3], outline="blue", width=3
        )
        self.current_step = 'complete'
        self.update_step_label()

    def on_escape(self, event):
        if self.current_step == 'complete':
            return
        if self.drawing_rect_id:
            self.canvas.delete(self.drawing_rect_id)
            self.drawing_rect_id = None
        self.rect_start_x = None

        if self.current_step == 'head':
            self.head_bbox = None
            self.current_step = 'body'
        elif self.current_step == 'body':
            self.body_bbox = None
            self.current_step = 'complete'

        self.update_step_label()

    def clear_head(self):
        if self.head_rect_id:
            self.canvas.delete(self.head_rect_id)
        self.head_bbox = None
        self.head_rect_id = None
        self.current_step = 'head'
        self.update_step_label()

    def clear_body(self):
        if self.body_rect_id:
            self.canvas.delete(self.body_rect_id)
        self.body_bbox = None
        self.body_rect_id = None
        if self.current_step == 'complete':
            self.current_step = 'body'
        self.update_step_label()

    # --- CONFIRMATION DIALOG ---
    def show_confirmation_dialog(self, title, on_redraw, on_finished):
        choice = [None]

        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text=title, font=("Arial", 12, "bold")).pack(pady=(20, 10), padx=30)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=(5, 20))

        def do_redraw():
            choice[0] = 'redraw'
            dialog.destroy()

        def do_finished():
            choice[0] = 'finished'
            dialog.destroy()

        tk.Button(btn_frame, text="Redraw", command=do_redraw, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Finished", command=do_finished, width=10, bg="lightgreen").pack(side=tk.LEFT, padx=10)

        # Center dialog over parent window
        self.window.update_idletasks()
        x = self.window.winfo_x() + self.window.winfo_width() // 2 - 150
        y = self.window.winfo_y() + self.window.winfo_height() // 2 - 75
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window()

        if choice[0] == 'redraw':
            on_redraw()
        elif choice[0] == 'finished':
            on_finished()

    # --- YOLO MATH & SAVING ---
    def save_and_next(self):
        img_path = self.image_paths[self.current_index]
        txt_path = os.path.splitext(img_path)[0] + ".txt"

        lines = []

        if self.head_bbox:
            x1, y1, x2, y2 = self.head_bbox
            cx = ((x1 + x2) / 2.0) / self.img_width
            cy = ((y1 + y2) / 2.0) / self.img_height
            w = (x2 - x1) / self.img_width
            h = (y2 - y1) / self.img_height
            lines.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        if self.body_bbox:
            x1, y1, x2, y2 = self.body_bbox
            cx = ((x1 + x2) / 2.0) / self.img_width
            cy = ((y1 + y2) / 2.0) / self.img_height
            w = (x2 - x1) / self.img_width
            h = (y2 - y1) / self.img_height
            lines.append(f"1 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

        with open(txt_path, 'w') as f:
            f.write('\n'.join(lines))

        print(f"Saved: {txt_path}")
        self.next_image()

    def check_existing_annotation(self, img_path):
        """Load and display any existing annotations for this image."""
        txt_path = os.path.splitext(img_path)[0] + ".txt"
        if not os.path.exists(txt_path) or os.path.getsize(txt_path) == 0:
            return

        with open(txt_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            class_id = int(parts[0])
            cx, cy, w, h = map(float, parts[1:])

            x_center_px = cx * self.img_width
            y_center_px = cy * self.img_height
            w_px = w * self.img_width
            h_px = h * self.img_height

            x1 = x_center_px - w_px / 2
            y1 = y_center_px - h_px / 2
            x2 = x_center_px + w_px / 2
            y2 = y_center_px + h_px / 2
            bbox = (x1, y1, x2, y2)

            if class_id == 0:
                self.head_bbox = bbox
                self.head_rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=3)
            elif class_id == 1:
                self.body_bbox = bbox
                self.body_rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=3)

        # Set step based on what's already annotated
        if self.head_bbox and self.body_bbox:
            self.current_step = 'complete'
        elif self.head_bbox:
            self.current_step = 'body'
        else:
            self.current_step = 'head'

    # --- NAVIGATION ---
    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()
        else:
            messagebox.showinfo("Done", "You have reached the last image!")

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()


if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOAnnotator(root)
    root.mainloop()
