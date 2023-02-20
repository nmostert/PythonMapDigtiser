import tkinter as tk            # Used to create a window
from tkinter import filedialog  # Used for opening file dialog
from PIL import Image, ImageTk  # Used for handling image data
import math                     # Used for calculating rotation
import numpy as np              # Used for affine transform matrix operations
import os                       # Used for directory operations
import platform

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.master.geometry("600x400")

        self.pil_image = None   # Image data to be displayed
        self.my_title = "Python Image Viewer"

        # Window settings
        self.master.title(self.my_title)

        # Execution content
        self.create_menu()   # Create a menu
        self.create_widget()    # Create a widget

        # Initial affine transformation matrix
        self.reset_transform()

    def menu_open_clicked(self, event=None):
        # File -> Open
        filename = tk.filedialog.askopenfilename(
            filetypes=[("Image file", ".bmp .png .jpg .tif"),
                       ("Bitmap", ".bmp"),
                       ("PNG", ".png"),
                       ("JPEG", ".jpg"),
                       ("Tiff", ".tif")],
            # set the filter for file types that can be selected,
            # including image files such as BMP, PNG, JPG, and TIF
            initialdir=os.getcwd()
            # set the initial directory of the file dialog window
            # to the current working directory
            )

        # Set the image file
        self.set_image(filename)

    def menu_quit_clicked(self):
        # Close the window
        self.master.destroy()

    # Define the create_menu method
    def create_menu(self):
        # Generate an instance named menu_bar from the Menu class
        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=tk.OFF)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.file_menu.add_command(label="Open",
                                   command=self.menu_open_clicked,
                                   accelerator="Ctrl+O")
        self.file_menu.add_separator()  # Add a separator
        self.file_menu.add_command(label="Exit",
                                   command=self.menu_quit_clicked)

        # Shortcut (Ctrol-O button) to open a file
        self.menu_bar.bind_all("<Control-o>", self.menu_open_clicked)
        self.master.config(menu=self.menu_bar)  # Place the menu bar

    # Define the create_widget method
    def create_widget(self):
        # Status bar (added to parent)
        frame_statusbar = tk.Frame(self.master, bd=1, relief=tk.SUNKEN)
        self.label_image_info = \
            tk.Label(frame_statusbar, text="image info",
                     anchor=tk.E, padx=5)
        self.label_image_pixel = tk.Label(frame_statusbar,
                                          text="(x, y)", anchor=tk.W, padx=5)
        self.label_image_info.pack(side=tk.RIGHT)
        self.label_image_pixel.pack(side=tk.LEFT)
        frame_statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Canvas
        self.canvas = tk.Canvas(self.master, background="black")
        # equivalent to Dock.Fill in Windows Forms
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Mouse events
        # ============

        # MouseDown
        self.master.bind("<Button-1>", self.mouse_down_left)

        # MouseDrag (moving while pressing button)
        self.master.bind("<B1-Motion>", self.mouse_move_left)

        # MouseMove
        self.master.bind("<Motion>", self.mouse_move)

        # MouseDoubleClick
        self.master.bind("<Double-Button-1>", self.mouse_double_click_left)

        # MouseWheel
        # self.master.bind("<MouseWheel>", self.mouse_wheel)
        # Adding linux support
        if platform.system() == "Linux":
            self.master.bind("<Button-4>", self.mouse_wheel_linux)
            self.master.bind("<Button-5>", self.mouse_wheel_linux)
        else:
            self.master.bind("<MouseWheel>", self.mouse_wheel)

    def set_image(self, filename):
        '''Open an image file'''
        if not filename:
            return

        # Open the file using PIL.Image
        self.pil_image = Image.open(filename)

        # Set the affine transformation matrix to fit the entire image
        self.zoom_fit(self.pil_image.width, self.pil_image.height)

        # Display the image
        self.draw_image(self.pil_image)

        # Set the window title to the filename
        self.master.title(f"{self.my_title} - {os.path.basename(filename)}")

        # Display image information in the status bar
        self.label_image_info["text"] = \
            f"{self.pil_image.format} : {self.pil_image.width} x"\
            "{self.pil_image.height} {self.pil_image.mode}"

        # Set the current directory
        os.chdir(os.path.dirname(filename))

    # -------------------------------------------------------------------------
    # Mouse events
    # -------------------------------------------------------------------------

    def mouse_down_left(self, event):
        ''' Left button down event '''
        self.__old_event = event

    def mouse_move_left(self, event):
        ''' Left button drag event '''
        if self.pil_image is None:
            return
        self.translate(event.x - self.__old_event.x,
                       event.y - self.__old_event.y)
        self.redraw_image()  # Redraw image
        self.__old_event = event

    def mouse_move(self, event):
        ''' Mouse move event '''
        if self.pil_image is None:
            return

        image_point = self.to_image_point(event.x, event.y)
        if image_point != []:
            self.label_image_pixel["text"] = \
                f"({image_point[0]:.2f}, {image_point[1]:.2f})"
        else:
            self.label_image_pixel["text"] = "(--, --)"

    def mouse_double_click_left(self, event):
        ''' Double click left button event '''
        if self.pil_image is None:
            return
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.redraw_image()  # Redraw image

    def mouse_wheel(self, event):
        '''
        Mouse wheel event for Windows
        Not tested for OSX
        '''
        if self.pil_image is None:
            return
        if event.state != 9:  # 9 is the Shift key in Windows
            if event.delta < 0:
                # Zoom in on rotation down
                self.scale_at(1.25, event.x, event.y)
            else:
                # Zoom out on rotation up
                self.scale_at(0.8, event.x, event.y)
        else:
            if event.delta < 0:
                # Rotate counterclockwise on rotation down
                self.rotate_at(-5, event.x, event.y)
            else:
                # Rotate clockwise on rotation up
                self.rotate_at(5, event.x, event.y)
        self.redraw_image()  # Redraw image

    def mouse_wheel_linux(self, event):
        ''' Mouse wheel event for Linux (X11 based)'''
        if self.pil_image is None:
            return
        if event.state != 17:  # 17 is the Shift key for X11
            if event.num == 5:
                # Zoom in on rotation down
                self.scale_at(1.25, event.x, event.y)
            else:  # event.num 4 is up
                # Zoom out on rotation up
                self.scale_at(0.8, event.x, event.y)
        else:
            if event.num == 5:
                # Rotate counterclockwise on rotation down
                self.rotate_at(-5, event.x, event.y)
            else:
                # Rotate clockwise on rotation up
                self.rotate_at(5, event.x, event.y)
        self.redraw_image()  # Redraw image

    # -------------------------------------------------------------------------
    # Affine transformation for image display
    # -------------------------------------------------------------------------

    def reset_transform(self):
        """
        Reset the affine transformation to its initial state
        (scale 1, no translation).
        """
        self.mat_affine = np.eye(3)

    def translate(self, offset_x, offset_y):
        """Translate."""
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale(self, scale: float):
        """Scale."""
        mat = np.eye(3)
        mat[0, 0] = scale
        mat[1, 1] = scale

        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale_at(self, scale: float, cx: float, cy: float):
        """Scale around the point (cx, cy)."""

        # Move to the origin
        self.translate(-cx, -cy)
        # Scale
        self.scale(scale)
        # Move back
        self.translate(cx, cy)

    def rotate(self, deg: float):
        """Rotate."""
        mat = np.eye(3)
        mat[0, 0] = math.cos(math.pi * deg / 180)
        mat[1, 0] = math.sin(math.pi * deg / 180)
        mat[0, 1] = -mat[1, 0]
        mat[1, 1] = mat[0, 0]

        self.mat_affine = np.dot(mat, self.mat_affine)

    def rotate_at(self, deg: float, cx: float, cy: float):
        """Rotate around the point (cx, cy)."""

        # Move to the origin
        self.translate(-cx, -cy)
        # Rotate
        self.rotate(deg)
        # Move back
        self.translate(cx, cy)

    def zoom_fit(self, image_width, image_height):
        """Display the image in the widget."""

        # Get the size of the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if (image_width * image_height <= 0) or \
                (canvas_width * canvas_height <= 0):
            return

        # Initialize the affine transformation
        self.reset_transform()

        scale = 1.0
        offsetx = 0.0
        offsety = 0.0

        if (canvas_width * image_height) > (image_width * canvas_height):
            # The widget is wider than the image (fit the image vertically)
            scale = canvas_height / image_height
            # Center the image horizontally
            offsetx = (canvas_width - image_width * scale) / 2
        else:
            # The widget is taller than the image (fit the image horizontally)
            scale = canvas_width / image_width
            # Center the image vertically
            offsety = (canvas_height - image_height * scale) / 2

        # Scale
        self.scale(scale)
        # Center the image
        self.translate(offsetx, offsety)

    def to_image_point(self, x, y):
        """Convert the canvas coordinates to the image coordinates."""
        if self.pil_image is None:
            return []
        # Convert from canvas coordinates to image coordinates
        # (inverse of the affine transformation)
        mat_inv = np.linalg.inv(self.mat_affine)
        image_point = np.dot(mat_inv, (x, y, 1.))
        if image_point[0] < 0 or image_point[1] < 0 or \
                image_point[0] > self.pil_image.width or \
                image_point[1] > self.pil_image.height:
            return []

        return image_point

    # -------------------------------------------------------------------------
    # Drawing
    # --------------------------------------------------------------------------

    def draw_image(self, pil_image):
        """Draw the image on the canvas."""

        if pil_image is None:
            return

        self.pil_image = pil_image

        # Get the size of the canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Compute the affine transformation matrix from the canvas to the image
        # (by taking the inverse of the affine transformation matrix
        # from the image to the canvas)
        mat_inv = np.linalg.inv(self.mat_affine)

        # Convert the numpy array to a tuple for the affine transformation
        affine_inv = (
            mat_inv[0, 0], mat_inv[0, 1], mat_inv[0, 2],
            mat_inv[1, 0], mat_inv[1, 1], mat_inv[1, 2]
        )

        # Apply the affine transformation to the PIL image data
        dst = self.pil_image.transform(
            (canvas_width, canvas_height),  # Output size
            Image.AFFINE,  # Affine transformation
            affine_inv,  # Affine transformation matrix (from output to input)
            Image.NEAREST  # Interpolation method (nearest neighbor)
        )

        # Create a PhotoImage object from the transformed image
        im = ImageTk.PhotoImage(image=dst)

        # Draw the image on the canvas
        item = self.canvas.create_image(
            0, 0,  # Image display position (upper-left corner coordinates)
            anchor='nw',  # Anchor, with the upper-left corner as the origin
            image=im  # Image data to be displayed
        )

        self.image = im

    def redraw_image(self):
        """Redraw the image on the canvas."""
        if self.pil_image is None:
            return
        self.draw_image(self.pil_image)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
