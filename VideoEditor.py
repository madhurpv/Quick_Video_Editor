import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import numpy as np
from PIL import Image, ImageTk


copyright_image_default_path = "C:\\Users\\Dell\\Desktop\\New folder (18)\\CopyrightSymbol.png"
preview_placeholder_image_default_path = "Video_Frame_Placeholder.png"


def scale_new_width(original_height, original_width, new_height):
    return int((new_height / original_height) * original_width)
    

def overlay_image_alpha(background, overlay, position=(0, 0)):
    """Overlay an image with transparency (alpha channel) onto a background."""
    overlay_h, overlay_w = overlay.shape[:2]
    x, y = position
    
    # Get the alpha mask of the overlay image
    alpha_mask = overlay[:, :, 3] / 255.0  # Normalize the alpha to [0, 1]

    # Blend the images
    for c in range(0, 3):  # Process each channel (B, G, R)
        background[y:y + overlay_h, x:x + overlay_w, c] = \
            (1.0 - alpha_mask) * background[y:y + overlay_h, x:x + overlay_w, c] + \
            alpha_mask * overlay[:, :, c]
    
    return background

def process_frame(frame, new_width, new_height, copyright_checked, copyright_img):
    # Resize the frame to the new width and height
    frame_resized = cv2.resize(frame, (new_width, new_height))
    
    # Overlay the copyright image if checked
    #print(copyright_checked)
    #print(copyright_img)
    if copyright_checked and copyright_img is not None:
        #print("checked")
        # Position of the watermark: bottom right corner
        overlay_x = new_width - 400  # 400px wide image, so start at new_width - 400
        overlay_y = new_height - 80  # 80px height image, so start at new_height - 80
        frame_resized = overlay_image_alpha(frame_resized, copyright_img, position=(overlay_x, overlay_y))

    return frame_resized

def process_video(input_video_path, output_video_path, x, y, output_height, copyright_checked, copyright_img, render_preview_checked, progress_callback):
    # Open the input video
    cap = cv2.VideoCapture(input_video_path)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate the new width to maintain aspect ratio for the specified height
    new_height = output_height
    new_width = scale_new_width(original_height, original_width, new_height)
    
    # Set up codec and output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for saving as .mp4
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (new_width, new_height))
    
    
    # Calculate the frame numbers for the start (x) and end (y) times
    start_frame = int(x * fps)
    end_frame = int(y * fps)
    
    # Set the video to the start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    # Process the video from start to end time
    frame_count = start_frame
    total_frames_to_process = end_frame - start_frame
    while cap.isOpened():
        root.update()
        ret, frame = cap.read()
        if not ret:
            break

        frame_resized = process_frame(frame, new_width, new_height, copyright_checked, copyright_img)

        # Write the frame to the output file
        out.write(frame_resized)

        if render_preview_checked:
            frame_resized = cv2.resize(frame_resized, (500, 300))
            b,g,r = cv2.split(frame_resized)
            frame_resized = cv2.merge((r,g,b))
            frame_resized = Image.fromarray(frame_resized)
            frame_resized = ImageTk.PhotoImage(frame_resized)
            video_preview_label.configure(image=frame_resized)
            video_preview_label.image = frame_resized
        
        # Update progress
        progress_callback(frame_count - start_frame, total_frames_to_process)
        
        # Stop when we reach the end frame
        if frame_count >= end_frame:
            break
        
        frame_count += 1
    
    # Release the video objects
    cap.release()
    out.release()

def select_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    input_file_entry.delete(0, tk.END)
    input_file_entry.insert(0, file_path)

def select_output_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
    output_file_entry.delete(0, tk.END)
    output_file_entry.insert(0, file_path)

def select_copyright_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
    copyright_image_entry.delete(0, tk.END)
    copyright_image_entry.insert(0, file_path)

def start_processing():
    # Get input from the user
    input_video = input_file_entry.get()
    output_video = output_file_entry.get()
    copyright_image_path = copyright_image_entry.get()
    try:
        start_time = float(start_time_entry.get())
        end_time = float(end_time_entry.get())
        output_height = int(height_entry.get())
        copyright_checked = copyright_var.get()
        render_preview_checked = show_render_preview_var.get()
        #print("--- ", copyright_checked)

        if not copyright_image_path:
            copyright_image_path = copyright_image_default_path
        copyright_img = None
        copyright_img = cv2.imread(copyright_image_path, cv2.IMREAD_UNCHANGED)  # Read image with alpha channel
        copyright_img = cv2.resize(copyright_img, (400, 80))  # Resize to fixed size (400x80)

        # Validate times
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time.")
        
        if not input_video or not output_video:
            raise ValueError("Please select input and output files.")
        
        if output_height <= 0:
            raise ValueError("Height must be greater than 0.")
        
        # Set default copyright image path if not specified
        if copyright_checked and not copyright_image_path:
            copyright_image_path = copyright_image_default_path
        
        # Disable UI elements while processing
        start_button.config(state=tk.DISABLED)
        input_file_button.config(state=tk.DISABLED)
        output_file_button.config(state=tk.DISABLED)
        copyright_image_button.config(state=tk.DISABLED)

        # Start video processing
        progress_bar['value'] = 0
        process_video(input_video, output_video, start_time, end_time, output_height, copyright_checked, copyright_img, render_preview_checked, update_progress)
        
        # Enable UI elements after processing
        start_button.config(state=tk.NORMAL)
        input_file_button.config(state=tk.NORMAL)
        output_file_button.config(state=tk.NORMAL)
        copyright_image_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("Success", "Video processing completed successfully!")

    except ValueError as e:
        messagebox.showerror("Error", str(e))

def get_preview():
    input_video = input_file_entry.get()
    frame_number = int(previewframe_entry.get())
    copyright_checked = copyright_var.get()
    copyright_image_path = copyright_image_entry.get()
    if not copyright_image_path:
        copyright_image_path = copyright_image_default_path

    copyright_img = cv2.imread(copyright_image_path, cv2.IMREAD_UNCHANGED)  # Read image with alpha channel
    #print(copyright_img.shape)
    copyright_img = cv2.resize(copyright_img, (400, 80))  # Resize to fixed size (400x80)
    
    cap = cv2.VideoCapture(input_video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number-1)
    res, frame = cap.read()

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_number >= total_frames:
        frame_number = total_frames-1

    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate the new width to maintain aspect ratio for the specified height
    new_height = int(height_entry.get())
    new_width = scale_new_width(original_height, original_width, new_height)

    frame_resized = process_frame(frame, new_width, new_height, copyright_checked, copyright_img)
    frame_resized = cv2.resize(frame_resized, (500, 300))
    b,g,r = cv2.split(frame_resized)
    frame_resized = cv2.merge((r,g,b))
    frame_resized = Image.fromarray(frame_resized)
    frame_resized = ImageTk.PhotoImage(frame_resized)
    video_preview_label.configure(image=frame_resized)
    video_preview_label.image = frame_resized
    
    

def update_progress(current, total):
    progress_percentage = (current / total) * 100
    progress_bar['value'] = progress_percentage
    root.update_idletasks()

# Create the GUI window
root = tk.Tk()
root.title("Video Resizer, Trimmer, and Watermark")

# Create and place the input file selection
tk.Label(root, text="Input Video File").grid(row=0, column=0, padx=10, pady=5)
input_file_entry = tk.Entry(root, width=40)
input_file_entry.grid(row=0, column=1, padx=10, pady=5)
input_file_button = tk.Button(root, text="Browse", command=select_input_file)
input_file_button.grid(row=0, column=2, padx=10, pady=5)

# Create and place the output file selection
tk.Label(root, text="Output Video File").grid(row=1, column=0, padx=10, pady=5)
output_file_entry = tk.Entry(root, width=40)
output_file_entry.grid(row=1, column=1, padx=10, pady=5)
output_file_button = tk.Button(root, text="Browse", command=select_output_file)
output_file_button.grid(row=1, column=2, padx=10, pady=5)

# Copyright image file selection
tk.Label(root, text="Copyright Image File (optional)").grid(row=2, column=0, padx=10, pady=5)
copyright_image_entry = tk.Entry(root, width=40)
copyright_image_entry.grid(row=2, column=1, padx=10, pady=5)
copyright_image_entry.insert(-1, copyright_image_default_path)
copyright_image_button = tk.Button(root, text="Browse", command=select_copyright_image)
copyright_image_button.grid(row=2, column=2, padx=10, pady=5)

# Start and end time entries
tk.Label(root, text="Start Time (seconds)").grid(row=3, column=0, padx=10, pady=5)
start_time_entry = tk.Entry(root)
start_time_entry.grid(row=3, column=1, padx=10, pady=5)

tk.Label(root, text="End Time (seconds)").grid(row=4, column=0, padx=10, pady=5)
end_time_entry = tk.Entry(root)
end_time_entry.grid(row=4, column=1, padx=10, pady=5)

# Height entry
tk.Label(root, text="Output Height (pixels)").grid(row=5, column=0, padx=10, pady=5)
height_entry = tk.Entry(root)
height_entry.grid(row=5, column=1, padx=10, pady=5)

# Copyright checkbox
copyright_var = tk.BooleanVar()
copyright_check = tk.Checkbutton(root, text="Include Copyright Image", variable=copyright_var)
copyright_check.grid(row=6, column=0, columnspan=3, padx=10, pady=5)

show_render_preview_var = tk.BooleanVar()
show_render_preview_check = tk.Checkbutton(root, text="Show Render Preview", variable=show_render_preview_var)
show_render_preview_check.grid(row=7, column=0, columnspan=3, padx=10, pady=5)

# Progress bar
progress_bar = Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

# Start button
start_button = tk.Button(root, text="Start Processing", command=start_processing)
start_button.grid(row=9, column=0, columnspan=3, padx=10, pady=20)




placeholder_img = cv2.imread(preview_placeholder_image_default_path)
placeholder_img = cv2.resize(placeholder_img, (500, 300))
b,g,r = cv2.split(placeholder_img)
placeholder_img = cv2.merge((r,g,b))
placeholder_img = Image.fromarray(placeholder_img)
video_preview_image = ImageTk.PhotoImage(image=placeholder_img) 

# Put it in the display window
video_preview_label = tk.Label(root, image=video_preview_image)
video_preview_label.grid(row=10, column=2, padx=10, pady=5, rowspan=8, columnspan=8)
video_preview_label.image = video_preview_image

tk.Label(root, text="Preview").grid(row=12, column=0, padx=10, pady=5, columnspan=2)

tk.Label(root, text="Frame Number : ").grid(row=13, column=0, padx=10, pady=5)
previewframe_entry = tk.Entry(root)
previewframe_entry.grid(row=13, column=1, padx=10, pady=5)

preview_button = tk.Button(root, text="Preview", command=get_preview)
preview_button.grid(row=14, column=0, columnspan=2, padx=10, pady=20)


# Start the Tkinter main loop
root.mainloop()