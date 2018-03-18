import pygame
import numpy as np
import os

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from plyfile import PlyData

'''
First person camera controls from http://3dengine.org/Spectator_(PyOpenGL)
'''
class AntWorld:

    # Max fov=180 without fisheye
    def __init__(self, w=900, h=600, fov=170, filepath=".", ply_files=["ground.ply"]):
        self.filepath = filepath
        self.ply_files = ply_files

        pygame.init()
        display = (w, h)
        self.screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

        glMatrixMode(GL_PROJECTION)
        aspect = w / h
        # gluPerspective(fov, aspect, 0.1, 50.0)
        gluPerspective(fov, aspect, 0.001, 100000.0)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glMatrixMode(GL_MODELVIEW)

        # By default we are staring down at the ground -> look up
        glRotate(-90, 1, 0, 0)
        # The nest is to our left -> turn to face it (roughly)
        glRotate(-90, 0, 0, 1)
        glTranslatef(0.0, 0.0, 1)

        self.components = []
        self.load_mesh()

    def load_from_ply(self, ply_file_name):
        v_dict = {}
        cache_file = os.path.join(self.filepath, ply_file_name + '.npz')
        print cache_file + " loaded"

        if os.path.isfile(cache_file):
            cached = np.load(cache_file)
            xyz = cached['v']
            colours = cached['c']
            triangles = cached['i']
        else:
            # Todo: I think some code in here is causing the Numpy deprecation warning (perhaps use copy() or fromiter())
            plydata = PlyData.read(os.path.join(self.filepath, ply_file_name))

            xyz_data = plydata['vertex'][['x','y','z']]
            xyz = xyz_data.view(np.float32).reshape(plydata['vertex'].data.shape + (-1,))

            colour_data = plydata['vertex'][['red','green','blue']]
            colours = (colour_data.view(np.uint8).reshape(plydata['vertex'].data.shape + (-1,)) / 255.).astype(np.float32)

            tri_data = plydata['face']['vertex_indices']
            triangles = np.fromiter(tri_data, [('data', tri_data[0].dtype, (3,))], count=len(tri_data))['data']

            np.savez_compressed(cache_file, v=xyz, c=colours, i=triangles)
            print ply_file_name + " loaded"

        v_dict['v'] = vbo.VBO(xyz)
        v_dict['c'] = vbo.VBO(colours)
        v_dict['i'] = vbo.VBO(triangles, target=GL_ELEMENT_ARRAY_BUFFER)
        return v_dict

    def simple_lights(self):
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.45, 0.0, 1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 10.0, 10.0, 10.0))
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

    def simple_camera_pose(self):
        """ Pre-position the camera (optional) """
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(array([0.741, -0.365, 0.563, 0, 0, 0.839,
                             0.544, 0, -0.671, -0.403, 0.622,
                             0, -0.649, 1.72, -4.05, 1]))

    def load_mesh(self):
        print "Loading Meshes"

        for filename in self.ply_files:
            self.components.append(self.load_from_ply(filename))

        print "Meshes Loaded"

    def draw(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw all components (ground, nest, etc)
        for component in self.components:
            component['c'].bind()
            glEnableClientState(GL_COLOR_ARRAY)
            glColorPointer(3, GL_FLOAT, 0, component['c'])
            component['c'].unbind()

            component['v'].bind()
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, None)
            component['v'].unbind()

            component['i'].bind()
            glDrawElements(GL_TRIANGLES,
                           len(component['i']) * 3,
                           GL_UNSIGNED_INT,
                           None)
            # glMultiDrawElements(GL_TRIANGLES, [0], GL_UNSIGNED_INT, None, 1)
            component['i'].unbind()

            glDisableClientState(GL_COLOR_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)

    def loop(self):
        pygame.display.flip()
        pygame.event.pump()
        self.keys = dict((chr(i), int(v)) for i, v in
                         enumerate(pygame.key.get_pressed()) if i < 256)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        return True

    def controls_3d(self, mouse_button=1, w_key='w', s_key='s', a_key='a',
                    d_key='d'):
        """ The actual camera setting cycle """
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[mouse_button]:
            look_speed = .2
            buff = glGetDoublev(GL_MODELVIEW_MATRIX)
            c = (-1 * np.mat(buff[:3, :3]) *
                 np.mat(buff[3, :3]).T).reshape(3, 1)
            # c is camera center in absolute coordinates,
            # we need to move it back to (0,0,0)
            # before rotating the camera
            glTranslate(c[0], c[1], c[2])
            m = buff.flatten()
            glRotate(mouse_dx * look_speed, m[1], m[5], m[9])
            glRotate(mouse_dy * look_speed, m[0], m[4], m[8])

            # compensate roll (doesn't seem to work as suggested)
            # glRotated(-math.atan2(-m[4],m[5]) *
            #    57.295779513082320876798154814105, m[2], m[6], m[10])

            glTranslate(-c[0], -c[1], -c[2])

        # move forward-back or right-left
        # fwd =   .1 if 'w' is pressed;   -0.1 if 's'
        fwd = .1 * (self.keys[w_key] - self.keys[s_key])
        strafe = .1 * (self.keys[a_key] - self.keys[d_key])
        if abs(fwd) or abs(strafe):
            m = glGetDoublev(GL_MODELVIEW_MATRIX).flatten()
            glTranslate(fwd*m[2], fwd*m[6], fwd*m[10])
            glTranslate(strafe*m[0], strafe*m[4], strafe*m[8])

    def run(self):
        """game main loop"""
        while world.loop():
            world.draw()
            world.controls_3d(0, 'w', 's', 'a', 'd')
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        quit()
            if world.keys['q']:
                self.screengrab()

    def shutdown(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
        return False

    def cleanup(self):
        pygame.quit()

    def screengrab(self):
        surface = self.screen

        w = surface.get_width()
        h = surface.get_height()

        pixel_list = glReadPixels(0, 0, w, h, GL_RGB, GL_FLOAT)
        P = np.flipud(np.array(pixel_list).reshape(h, w, 3))
        np.save('temp.npy', P)  # Use screenshot_inspector.ipynb to view

        print "Took screenshot" # Todo: It is taking several screenshots. Try limit this to 1


if __name__ == '__main__':

    print "Pygame version: " + pygame.ver

    #ply_files = ["ground.ply", "bushes_nest.ply", "vegetation_downsampled.ply"]
    ply_files = ["ground.ply", "bushes_nest.ply", "vegetation.ply"]

    world = AntWorld(ply_files=ply_files)
    world.run()
