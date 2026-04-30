import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import random
import yaml
import threading
from ultralytics import YOLO

class YOLO11Trainer:
    def __init__(self, window):
        self.window = window
        self.window.title("YOLO11 Local Training Engine")
        self.window.geometry("500x300")

        self.source_folder = ""
        self.dataset_dir = os.path.abspath("YOLO_Rat_Dataset") # Master output folder

        # --- GUI LAYOUT ---
        tk.Label(window, text="1. Select Annotated Data Folder", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        self.btn_select = tk.Button(window, text="Browse...", command=self.select_folder, width=20)
        self.btn_select.pack()
        
        self.lbl_folder = tk.Label(window, text="No folder selected", fg="gray")
        self.lbl_folder.pack(pady=5)

        tk.Label(window, text="2. Set Training Epochs (Iterations)", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        # Link the box to a variable that has a default value
        self.epoch_var = tk.StringVar(value="50")
        self.spin_epochs = tk.Spinbox(window, from_=10, to=500, increment=10, width=10, textvariable=self.epoch_var)
        self.spin_epochs.pack()

        self.btn_train = tk.Button(window, text="3. Build Dataset & Start Training", command=self.start_training_thread, state=tk.DISABLED, bg="lightgreen", font=("Arial", 10, "bold"))
        self.btn_train.pack(pady=25)

        self.lbl_status = tk.Label(window, text="Status: Waiting for data...", fg="blue")
        self.lbl_status.pack()

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images and TXT files")
        if folder:
            self.source_folder = folder
            self.lbl_folder.config(text=folder)
            self.btn_train.config(state=tk.NORMAL)
            self.lbl_status.config(text="Status: Ready to build and train")

    def start_training_thread(self):
        """Training blocks the GUI. We run it in a separate thread so the window doesn't freeze."""
        self.btn_train.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.lbl_status.config(text="Status: Building Dataset Structure...", fg="orange")
        
        # Start the heavy lifting in a background thread
        threading.Thread(target=self.run_pipeline, daemon=True).start()

    def run_pipeline(self):
        try:
            epochs = int(self.spin_epochs.get())
            
            # Step 1: Build the Dataset Structure
            yaml_path = self.build_dataset_structure()
            
            # Step 2: Start Training
            self.lbl_status.config(text="Status: Training Model (Check Console/Terminal for progress)...", fg="orange")
            
            # Load the nano version of YOLO11 (fastest to train)
            model = YOLO("yolo11n.pt") 
            
            # Train the model locally
            model.train(data=yaml_path, epochs=epochs, imgsz=640, device="cpu") # remove device="cpu" if you have an NVIDIA GPU setup
            
            self.lbl_status.config(text="Status: Training Complete! Model saved in 'runs/detect/train/weights'", fg="green")
            messagebox.showinfo("Success", "Training Complete! Your custom model is best.pt")
            
        except Exception as e:
            self.lbl_status.config(text="Status: Error occurred.", fg="red")
            messagebox.showerror("Training Error", str(e))
            self.btn_train.config(state=tk.NORMAL)
            self.btn_select.config(state=tk.NORMAL)

    def build_dataset_structure(self):
        """Creates the train/val split and generates data.yaml"""
        # Create directories
        for split in ['train', 'val']:
            os.makedirs(os.path.join(self.dataset_dir, 'images', split), exist_ok=True)
            os.makedirs(os.path.join(self.dataset_dir, 'labels', split), exist_ok=True)

        # Get all images that have a matching .txt file
        valid_files = []
        for file in os.listdir(self.source_folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                base_name = os.path.splitext(file)[0]
                txt_path = os.path.join(self.source_folder, f"{base_name}.txt")
                if os.path.exists(txt_path):
                    valid_files.append(base_name)

        if not valid_files:
            raise ValueError("No matching image/txt pairs found in the selected folder.")

        # Shuffle and split (80% train, 20% val)
        random.shuffle(valid_files)
        split_idx = int(len(valid_files) * 0.8)
        train_files = valid_files[:split_idx]
        val_files = valid_files[split_idx:]

        # Helper function to copy files
        def copy_files(file_list, split_name):
            for base_name in file_list:
                # Find the exact image extension
                img_ext = next(ext for ext in ['.jpg', '.png', '.jpeg'] if os.path.exists(os.path.join(self.source_folder, f"{base_name}{ext}")))
                
                # Copy Image
                shutil.copy(os.path.join(self.source_folder, f"{base_name}{img_ext}"),
                            os.path.join(self.dataset_dir, 'images', split_name, f"{base_name}{img_ext}"))
                # Copy Label
                shutil.copy(os.path.join(self.source_folder, f"{base_name}.txt"),
                            os.path.join(self.dataset_dir, 'labels', split_name, f"{base_name}.txt"))

        copy_files(train_files, 'train')
        copy_files(val_files, 'val')

        # Create data.yaml
        yaml_path = os.path.join(self.dataset_dir, "data.yaml")
        yaml_data = {
            "path": self.dataset_dir,
            "train": "images/train",
            "val": "images/val",
            "names": {0: "rat_head", 1: "rat_body"}
        }
        
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False)

        return yaml_path

if __name__ == "__main__":
    root = tk.Tk()
    app = YOLO11Trainer(root)
    root.mainloop()