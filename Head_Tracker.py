import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import csv
import os
from PIL import Image, ImageTk
from ultralytics import YOLO

class RatInferenceTracker:
    def __init__(self, window):
        self.window = window
        self.window.title("Custom YOLO11 Rat Tracker")
        
        # Handle window closing to ensure video saves properly
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables
        self.model = None
        self.cap = None
        self.out_video = None # VideoWriter object
        self.out_video_path = ""
        self.is_playing = False
        self.video_path = ""
        self.tracking_data = [] # Stores [frame, timestamp, x, y, confidence]
        self.frame_count = 0
        self.fps = 30 # Default, will be updated when video loads

        # --- GUI LAYOUT ---
        self.top_frame = tk.Frame(window)
        self.top_frame.pack(side=tk.TOP, pady=10)

        self.btn_load_model = tk.Button(self.top_frame, text="1. Load best.pt Model", command=self.load_model, width=20)
        self.btn_load_model.pack(side=tk.LEFT, padx=5)

        self.btn_load_video = tk.Button(self.top_frame, text="2. Load Video", command=self.load_video, width=15, state=tk.DISABLED)
        self.btn_load_video.pack(side=tk.LEFT, padx=5)

        self.btn_play = tk.Button(self.top_frame, text="3. Start Tracking", command=self.toggle_play, width=15, state=tk.DISABLED, bg="lightgreen")
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(self.top_frame, text="Export CSV Data", command=self.save_csv, width=15, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(self.top_frame, text="Status: Please load model.", fg="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # Video Canvas
        self.canvas = tk.Canvas(window, width=640, height=480, bg="black")
        self.canvas.pack(padx=10, pady=10)

        self.window.mainloop()

    # --- SETUP & LOADING ---
    def load_model(self):
        model_path = filedialog.askopenfilename(title="Select your best.pt file", filetypes=[("PyTorch Model", "*.pt")])
        if model_path:
            try:
                self.lbl_status.config(text="Loading model...", fg="orange")
                self.window.update()
                self.model = YOLO(model_path)
                self.lbl_status.config(text="Model Loaded. Select Video.", fg="green")
                self.btn_load_video.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("Model Error", f"Failed to load model: {e}")

    def load_video(self):
        self.video_path = filedialog.askopenfilename(title="Select Video to Track", filetypes=[("Video", "*.mp4 *.avi *.mov")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = 0
            self.tracking_data = [["Frame", "Time_sec", "X_Center", "Y_Center", "Confidence"]] # CSV Headers
            
            # Get video dimensions for the VideoWriter
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Setup VideoWriter
            if self.out_video is not None:
                self.out_video.release() # Release previous video if one was loaded
                
            base_name = os.path.splitext(self.video_path)[0]
            self.out_video_path = f"{base_name}_annotated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec for .mp4
            self.out_video = cv2.VideoWriter(self.out_video_path, fourcc, self.fps, (width, height))
            
            # Read first frame to adjust canvas
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
                self.btn_play.config(state=tk.NORMAL)
                self.btn_save.config(state=tk.NORMAL)
                self.lbl_status.config(text="Ready to Track.", fg="green")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Reset to start

    # --- TRACKING LOOP ---
    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.lbl_status.config(text="Tracking Active...", fg="red")
            self.btn_play.config(text="Pause Tracking", bg="yellow")
            self.update_loop()
        else:
            self.lbl_status.config(text="Paused.", fg="blue")
            self.btn_play.config(text="Resume Tracking", bg="lightgreen")

    def update_loop(self):
        if self.is_playing and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_count += 1
                time_sec = round(self.frame_count / self.fps, 3)

                # 1. Run YOLO Inference
                results = self.model.predict(frame, verbose=False, conf=0.4) 

                # 2. Parse Results
                boxes = results[0].boxes
                
                if len(boxes) > 0:
                    best_box = boxes[0]
                    x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
                    conf = float(best_box.conf[0].cpu().numpy())
                    
                    # Calculate Center Point
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    # Save data
                    self.tracking_data.append([self.frame_count, time_sec, cx, cy, round(conf, 3)])

                    # Draw Bounding Box (Green)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    
                    # Draw Center Dot (Red)
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                    
                    # Draw text
                    cv2.putText(frame, f"Rat Head {conf:.2f}", (int(x1), int(y1)-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                else:
                    self.tracking_data.append([self.frame_count, time_sec, "", "", "0.0"])

                # Write the annotated frame to our output video file
                if self.out_video is not None:
                    self.out_video.write(frame)

                # 3. Display Frame
                self.display_frame(frame)
                
                self.window.after(1, self.update_loop)
            else:
                self.is_playing = False
                
                # IMPORTANT: Close the video file when finished
                if self.out_video is not None:
                    self.out_video.release()
                    self.out_video = None
                    
                self.lbl_status.config(text="Video Finished. Ready to save data.", fg="blue")
                self.btn_play.config(text="Start Tracking", state=tk.DISABLED, bg="lightgray")
                self.save_csv() 

    def display_frame(self, frame):
        h, w = frame.shape[:2]
        canvas_w, canvas_h = 640, 480
        scale = min(canvas_w/w, canvas_h/h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        frame_resized = cv2.resize(frame, (new_w, new_h))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        img = Image.fromarray(frame_rgb)
        self.photo = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(canvas_w//2, canvas_h//2, image=self.photo, anchor=tk.CENTER)

    # --- DATA EXPORT ---
    def save_csv(self):
        if len(self.tracking_data) <= 1:
            messagebox.showinfo("No Data", "No tracking data to save yet.")
            return
            
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        default_csv = f"{base_name}_tracking_data.csv"
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_csv,
            title="Save Tracking Data",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if save_path:
            with open(save_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(self.tracking_data)
            self.lbl_status.config(text=f"Data saved.", fg="green")
            
            # Notify user about BOTH the CSV and the Video
            msg = f"Tracking data saved to:\n{save_path}\n\nAnnotated video saved to:\n{self.out_video_path}"
            messagebox.showinfo("Export Successful", msg)

    # Cleanup when closing window
    def on_closing(self):
        if self.out_video is not None:
            self.out_video.release()
        if self.cap is not None:
            self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RatInferenceTracker(root)