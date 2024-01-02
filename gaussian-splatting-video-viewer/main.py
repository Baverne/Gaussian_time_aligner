import glfw
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import imgui
import numpy as np
import util
import imageio
import util_gau
import tkinter as tk
from tkinter import filedialog
import os
import time
import threading
import sys
import glob
import argparse
import open3d as o3d
import gc

# Add the directory containing main.py to the Python path
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

# Change the current working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


g_width, g_height = 1280, 720
g_camera = util.Camera(g_height, g_width)
g_program = None
g_scale_modifier = 1.
g_auto_sort = False
g_show_control_win = True
g_show_help_win = True
g_render_mode_tables = ["Gaussian Ball", "Billboard", "Depth", "SH:0", "SH:0~1", "SH:0~2", "SH:0~3 (default)"]
g_render_mode = 6

dir_path = os.path.join(os.path.dirname(__file__), "splats")
file_names = os.listdir(dir_path)

subfolders = [ f.path for f in os.scandir(dir_path) if f.is_dir() ]
files = glob.glob(os.path.expanduser("./splats/*"))

sorted_time = files
n_frames = len(sorted_time)

splat_idx = 2

splats_buffer = []

frame_idx = 0

def impl_glfw_init():
    window_name = "NeUVF editor"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    # glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    global window
    window = glfw.create_window(
        int(g_width), int(g_height), window_name, None, None
    )
    glfw.make_context_current(window)
    glfw.swap_interval(0)
    # glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL);
    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window

def cursor_pos_callback(window, xpos, ypos):
    g_camera.process_mouse(xpos, ypos)

def mouse_button_callback(window, button, action, mod):
    if imgui.get_io().want_capture_mouse:
        return
    pressed = action == glfw.PRESS
    g_camera.is_leftmouse_pressed = (button == glfw.MOUSE_BUTTON_LEFT and pressed)
    g_camera.is_rightmouse_pressed = (button == glfw.MOUSE_BUTTON_RIGHT and pressed)

def wheel_callback(window, dx, dy):
    g_camera.process_wheel(dx, dy)

def key_callback(window, key, scancode, action, mods):
    if action == glfw.REPEAT or action == glfw.PRESS:
        if key == glfw.KEY_Q:
            g_camera.process_roll_key(1)
        elif key == glfw.KEY_E:
            g_camera.process_roll_key(-1)

def update_camera_pose():
    if g_camera.is_pose_dirty:
        view_mat = g_camera.get_view_matrix()
        util.set_uniform_mat4(g_program, view_mat, "view_matrix")
        util.set_uniform_v3(g_program, g_camera.position, "cam_pos")
        g_camera.is_pose_dirty = False

def update_camera_intrin():
    if g_camera.is_intrin_dirty:
        proj_mat = g_camera.get_project_matrix()
        util.set_uniform_mat4(g_program, proj_mat, "projection_matrix")
        util.set_uniform_v3(g_program, g_camera.get_htanfovxy_focal(), "hfovxy_focal")
        g_camera.is_intrin_dirty = False

def window_resize_callback(window, width, height):
    gl.glViewport(0, 0, width, height)
    g_camera.update_resolution(height, width)

def load_ith_gaussian(i):
    global splats_buffer, dir_path, sorted_time
    gc.collect()
    print(sorted_time[i].split("splats\\")[1])
    # Load the gaussian splat corresponding to the ith frame and delete the previous one in the buffer
    splats_buffer.append(util_gau.load_ply(dir_path + "\\" + sorted_time[i].split("splats\\")[1] + "\\point_cloud\\iteration_7000\\point_cloud.ply"))
    if len(splats_buffer) > 2:
        del splats_buffer[0]

def main():
    global g_program, g_camera, g_scale_modifier, g_auto_sort, \
        g_show_control_win, g_show_help_win, \
        g_render_mode, g_render_mode_tables, splats, n_frames, frame_idx, splat_idx
        
    imgui.create_context()
    if args.hidpi:
        imgui.get_io().font_global_scale = 1.5
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    root = tk.Tk()  # used for file dialog
    root.withdraw()
    
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_scroll_callback(window, wheel_callback)
    glfw.set_key_callback(window, key_callback)
    
    glfw.set_window_size_callback(window, window_resize_callback)

    # Load and compile shaders
    g_program = util.load_shaders('shaders/gau_vert.glsl', 'shaders/gau_frag.glsl')

    # Vertex data for a quad
    quad_v = np.array([
        -1,  1,
        1,  1,
        1, -1,
        -1, -1
    ], dtype=np.float32).reshape(4, 2)
    quad_f = np.array([
        0, 1, 2,
        0, 2, 3
    ], dtype=np.uint32).reshape(2, 3)
    
    # List all files in the directory
    

    
    load_ith_gaussian(0)
    load_ith_gaussian(1)
    load_ith_gaussian(2)

    update_gaussian_data(splats_buffer[0])
    
    # load quad geometry
    vao, buffer_id = util.set_attributes(g_program, ["position"], [quad_v])
    util.set_faces_tovao(vao, quad_f)
    
    # set uniforms
    util.set_uniform_1f(g_program, g_scale_modifier, "scale_modifier")
    util.set_uniform_1int(g_program, g_render_mode - 3, "render_mod")
    update_camera_pose()
    update_camera_intrin()
    
    # settings
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    
    # return

    frame(vao, quad_f, window, impl)

    impl.shutdown()
    glfw.terminate()
    


def frame(vao, quad_f, window, impl):
    global g_program, g_camera, g_scale_modifier, g_auto_sort, \
        g_show_control_win, g_show_help_win, \
        g_render_mode, g_render_mode_tables, splats, n_frames, frame_idx, splat_idx
    
    start = time.time()
    
    frame_idx += 1
        
    # Every 20 frames, we load a new gaussian splat
    if frame_idx % 20 == 0:
        splat_idx = (splat_idx + 1) % n_frames
        load_ith_gaussian(splat_idx)
        
        # Load the data to openGL and sort the gaussians so they appear in the right order
        gaussian_data = splats_buffer[0].flat()
        util.set_storage_buffer_data(g_program, "gaussian_data", gaussian_data, bind_idx=0)
        sort_gaussian(splats_buffer[0])
        util.set_uniform_1int(g_program, splats_buffer[0].sh_dim, "sh_dim")

    glfw.poll_events()
    impl.process_inputs()
    imgui.new_frame()
    
    gl.glClearColor(0, 0, 0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    update_camera_pose()
    update_camera_intrin()
    
    gl.glUseProgram(g_program)
    gl.glBindVertexArray(vao)
    num_gau = len(splats_buffer[0])
    gl.glDrawElementsInstanced(gl.GL_TRIANGLES, len(quad_f.reshape(-1)), gl.GL_UNSIGNED_INT, None, num_gau)

    # imgui ui
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("Window", True):
            clicked, g_show_control_win = imgui.menu_item(
                "Show Control", None, g_show_control_win
            )
            clicked, g_show_help_win = imgui.menu_item(
                "Show Help", None, g_show_help_win
            )
            imgui.end_menu()
        imgui.end_main_menu_bar()
    
    if g_show_control_win:
        if imgui.begin("Control", True):
            imgui.text(f"fps = {imgui.get_io().framerate:.1f}")
            imgui.text(f"# of Gaus = {num_gau}")
            
            # camera fov
            changed, g_camera.fovy = imgui.slider_float(
                "fov", g_camera.fovy, 0.001, np.pi - 0.001, "fov = %.3f"
            )
            g_camera.is_intrin_dirty = changed
            update_camera_intrin()
            
            # scale modifier
            changed, g_scale_modifier = imgui.slider_float(
                "", g_scale_modifier, 0.1, 10, "scale modifier = %.3f"
            )
            imgui.same_line()
            if imgui.button(label="reset"):
                g_scale_modifier = 1.
                changed = True
                
            if changed:
                util.set_uniform_1f(g_program, g_scale_modifier, "scale_modifier")
            
            # render mode
            changed, g_render_mode = imgui.combo("shading", g_render_mode, g_render_mode_tables)
            if changed:
                util.set_uniform_1int(g_program, g_render_mode - 3, "render_mod")
            
            # sort button
            if imgui.button(label='sort splats[frame_idx]'):
                sort_gaussian(splats_buffer[0])
            imgui.same_line()
            changed, g_auto_sort = imgui.checkbox(
                    "auto sort", g_auto_sort,
                )
            if g_auto_sort:
                sort_gaussian(splats_buffer[0])
            
            if imgui.button(label='save image'):
                width, height = glfw.get_framebuffer_size(window)
                nrChannels = 3;
                stride = nrChannels * width;
                stride += (4 - stride % 4) if stride % 4 else 0
                gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 4)
                gl.glReadBuffer(gl.GL_FRONT)
                bufferdata = gl.glReadPixels(0, 0, width, height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
                img = np.frombuffer(bufferdata, np.uint8, -1).reshape(height, width, 3)
                imageio.imwrite("save.png", img[::-1])
            imgui.end()

    if g_show_help_win:
        imgui.begin("Help", True)
        imgui.text("Open Gaussian Splatting PLY file \n  by click 'open ply' button")
        imgui.text("Use left click & move to rotate camera")
        imgui.text("Use right click & move to translate camera")
        imgui.text("Press Q/E to roll camera")
        imgui.text("Use scroll to zoom in/out")
        imgui.text("Use control panel to change setting")
        imgui.end()
    
    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)
    
    end = time.time()
    
    # Display the app at a fixed framerate of 12 fps
    time.sleep(max(0, 1/12 - (end - start)))
    
    if not glfw.window_should_close(window):
        frame(vao, quad_f, window, impl)
    




def sort_gaussian(gaus):
    xyz = gaus.xyz
    view_mat = g_camera.get_view_matrix()
    xyz_view = view_mat[None, :3, :3] @ xyz[..., None] + view_mat[None, :3, 3, None]
    depth = xyz_view[:, 2, 0]
    index = np.argsort(depth)
    index = index.astype(np.int32).reshape(-1, 1)
    util.set_storage_buffer_data(g_program, "gi", index, bind_idx=1)
    

def update_gaussian_data(gaus):
    # load gaussian geometry
    num_gau = len(gaus)
    gaussian_data = gaus.flat()
    util.set_storage_buffer_data(g_program, "gaussian_data", gaussian_data, bind_idx=0)
    sort_gaussian(gaus)
    util.set_uniform_1int(g_program, gaus.sh_dim, "sh_dim")

if __name__ == "__main__":
    global args
    parser = argparse.ArgumentParser(description="NeUVF editor with optional HiDPI support.")
    parser.add_argument("--hidpi", action="store_true", help="Enable HiDPI scaling for the interface.")
    args = parser.parse_args()

    main()


