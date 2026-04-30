import tkinter as tk
from tkinter import filedialog, messagebox
import os
import glob
from PIL import Image, ImageTk

class YOLOAnnotator:
    def __init__(self, window):
        self.window = window
        self.window.title("Rat Head YOLO Annotator")
        
        # Variables
        self.image_paths = []
        self.current_index = 0
        self.class_id = 0 # 0 for "rat_head"
        
        self.current_image = None
        self.photo = None
        self.img_width = 0
        self.img_height = 0
        
        # Drawing Variables
        self.rect_start_x = None
        self.rect_start_y = None
        self.rect_id = None
        self.current_bbox = None # Store as (x1, y1, x2, y2)

        # --- GUI LAYOUT ---
        # Top Panel (Controls)
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
        
        self.btn_clear = tk.Button(self.top_frame, text="Clear Box", command=self.clear_box, state=tk.DISABLED)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # Canvas for Image
        # We start with a default size, but it will resize to fit the image
        self.canvas = tk.Canvas(window, width=800, height=600, bg="gray")
        self.canvas.pack(padx=10, pady=10)

        # Mouse Bindings for Drawing
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    # --- 1. FILE HANDLING ---
    def load_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder with Extracted Frames")
        if not folder_path: return

        # Get all jpg and png files
        search_path = os.path.join(folder_path, "*.[jp][pn]g")
        self.image_paths = sorted(glob.glob(search_path))
        
        # Also check for uppercase extensions
        search_path_upper = os.path.join(folder_path, "*.[JP][PN]G")
        self.image_paths.extend(sorted(glob.glob(search_path_upper)))

        if not self.image_paths:
            messagebox.showwarning("No Images", "Could not find any JPG or PNG images in that folder.")
            return

        self.current_index = 0
        self.btn_next.config(state=tk.NORMAL)
        self.btn_prev.config(state=tk.NORMAL)
        self.btn_clear.config(state=tk.NORMAL)
        
        self.load_image()

    def load_image(self):
        """Loads the image and checks if an annotation already exists."""
        self.clear_box() # Reset drawing
        
        img_path = self.image_paths[self.current_index]
        self.current_image = Image.open(img_path)
        
        self.img_width, self.img_height = self.current_image.size
        
        # Resize Canvas to match image exactly to keep math simple
        self.canvas.config(width=self.img_width, height=self.img_height)
        
        self.photo = ImageTk.PhotoImage(self.current_image)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.lbl_progress.config(text=f"Image: {self.current_index + 1} / {len(self.image_paths)}")
        
        # Check if we already labeled this image previously
        self.check_existing_annotation(img_path)

    # --- 2. DRAWING LOGIC ---
    def on_mouse_down(self, event):
        self.rect_start_x = event.x
        self.rect_start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)

    def on_mouse_drag(self, event):
        if self.rect_start_x:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(
                self.rect_start_x, self.rect_start_y, event.x, event.y, 
                outline="red", width=3
            )

    def on_mouse_up(self, event):
        if self.rect_start_x:
            x1 = min(self.rect_start_x, event.x)
            y1 = min(self.rect_start_y, event.y)
            x2 = max(self.rect_start_x, event.x)
            y2 = max(self.rect_start_y, event.y)
            
            # Ensure the box is inside the image bounds
            x1 = max(0, min(x1, self.img_width))
            y1 = max(0, min(y1, self.img_height))
            x2 = max(0, min(x2, self.img_width))
            y2 = max(0, min(y2, self.img_height))

            w = x2 - x1
            h = y2 - y1

            if w > 10 and h > 10: # Ignore accidental clicks
                self.current_bbox = (x1, y1, x2, y2)
                # Change color to green to show it's locked in
                self.canvas.itemconfig(self.rect_id, outline="green")
            else:
                self.clear_box()

    def clear_box(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = None
        self.current_bbox = None

    # --- 3. YOLO MATH & SAVING ---
    def save_and_next(self):
        if self.current_bbox is not None:
            # 1. Get pixel coordinates
            x1, y1, x2, y2 = self.current_bbox
            
            # 2. YOLO Math (Normalize to 0.0 - 1.0)
            center_x = ((x1 + x2) / 2.0) / self.img_width
            center_y = ((y1 + y2) / 2.0) / self.img_height
            width = (x2 - x1) / self.img_width
            height = (y2 - y1) / self.img_height
            
            # 3. Format string: <class> <x> <y> <w> <h>
            yolo_string = f"{self.class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}"
            
            # 4. Save to .txt file with the exact same name as the image
            img_path = self.image_paths[self.current_index]
            txt_path = os.path.splitext(img_path)[0] + ".txt"
            
            with open(txt_path, "w") as f:
                f.write(yolo_string)
            print(f"Saved: {txt_path}")
            
        else:
            # If no box is drawn, create an empty txt file to tell YOLO "nothing here"
            img_path = self.image_paths[self.current_index]
            txt_path = os.path.splitext(img_path)[0] + ".txt"
            open(txt_path, 'w').close()
            print(f"Saved empty background frame: {txt_path}")

        self.next_image()

    def check_existing_annotation(self, img_path):
        """If a .txt file already exists, draw the box on the screen."""
        txt_path = os.path.splitext(img_path)[0] + ".txt"
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
            with open(txt_path, "r") as f:
                line = f.readline().strip().split()
                if len(line) == 5:
                    _, cx, cy, w, h = map(float, line)
                    
                    # Reverse the YOLO math to get pixels back
                    x_center_pixel = cx * self.img_width
                    y_center_pixel = cy * self.img_height
                    w_pixel = w * self.img_width
                    h_pixel = h * self.img_height
                    
                    x1 = x_center_pixel - (w_pixel / 2)
                    y1 = y_center_pixel - (h_pixel / 2)
                    x2 = x_center_pixel + (w_pixel / 2)
                    y2 = y_center_pixel + (h_pixel / 2)
                    
                    self.current_bbox = (x1, y1, x2, y2)
                    self.rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=3)

    # --- 4. NAVIGATION ---
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