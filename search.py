import os

def find_my_model():
    # Start looking in your main user folder (e.g., C:\Users\YourName)
    start_dir = os.path.expanduser("~") 
    print(f"Scanning {start_dir} and all subfolders. This might take a minute...")

    found_files = []
    
    # Walk through all directories
    for root, dirs, files in os.walk(start_dir):
        if "best.pt" in files:
            full_path = os.path.join(root, "best.pt")
            found_files.append(full_path)

    if found_files:
        print("\n🎉 FOUND IT! Here are the locations:")
        for path in found_files:
            print(f"-> {path}")
    else:
        print("\n❌ Could not find 'best.pt' anywhere in your user folders.")
        print("This usually means the training did not successfully finish 100%.")

if __name__ == "__main__":
    find_my_model()
    # This stops the window from instantly closing on Windows!
    input("\nPress Enter to exit...")