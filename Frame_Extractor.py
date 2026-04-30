import cv2
import os
import math

def extract_frames_evenly(video_path, target_count=50):
    # 1. Open Video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return

    # 2. Get Video Properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total Frames in Video: {total_frames}")

    if total_frames < target_count:
        print("Warning: Video is shorter than target count. Saving all frames.")
        step = 1
    else:
        # Calculate the jump size (e.g., if 1000 frames, step = 20)
        step = total_frames / target_count

    # 3. Create Output Folder
    output_folder = "training_images"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 4. Loop and Extract
    count = 0
    saved_count = 0
    
    current_frame_pos = 0.0 # Float to track exact position

    while saved_count < target_count:
        # Move directly to the calculated frame position
        # We use an integer index for set(), but keep float for precision in the loop
        frame_idx = int(current_frame_pos)
        
        # Safety check: Don't go past the end
        if frame_idx >= total_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            break

        # Save the frame
        filename = f"{output_folder}/frame_{saved_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Saved {filename} (Source Frame: {frame_idx})")
        
        saved_count += 1
        current_frame_pos += step

    cap.release()
    print(f"Done! Extracted {saved_count} frames to '{output_folder}'")

# --- Usage ---
# Replace with your actual video filename
video_filename = "C:/Users/brend/Desktop/Folders/Python Projects/Head_Tracker/Videos/okn 1080 2.mp4" 

# Check if file exists to avoid errors
if os.path.exists(video_filename):
    extract_frames_evenly(video_filename)
else:
    # Build a dummy file so you can copy-paste this block and it runs immediately
    # (In reality, just change the string above)
    print(f"Please change 'video_filename' to your actual file path.")