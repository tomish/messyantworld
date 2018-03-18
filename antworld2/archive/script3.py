import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo

from numpy import *

from plyfile import PlyData

triangles = ()

vertices = ()

colours = ()

threes = ()

def Draw():
  print "Drawing"
  glBegin(GL_TRIANGLES)
  for tri in triangles:
    for i in tri:
      glColor3fv(colours[i])
      glVertex3fv(vertices[i])
  glEnd()
  print "Drawn"
    
def Draw2():
  glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

  #print "Drawing"
  
  global terrain, texture, indices, threes
  
  texture.bind()
  glEnableClientState( GL_COLOR_ARRAY )
  glColorPointer( 3, GL_FLOAT, 0, texture )
  texture.unbind()

  terrain.bind()
  glEnableClientState(GL_VERTEX_ARRAY)
  glVertexPointer( 3, GL_FLOAT, 0, None )
  terrain.unbind()

  indices.bind()

  glDrawElements(GL_TRIANGLES, len(indices) * 3, GL_UNSIGNED_INT, None)
  #glMultiDrawElements(GL_TRIANGLES, [0], GL_UNSIGNED_INT, None, 1)

  indices.unbind()

  glDisableClientState( GL_COLOR_ARRAY )
  glDisableClientState( GL_VERTEX_ARRAY )
  
  #print "Drawn"

def LoadMesh():
    print "Loading mesh"
    
    global vertices, colours, triangles, threes
    data = PlyData.read("../ground.ply")

    print "File loaded"
    
    vertices = [[vertex[0],vertex[1],vertex[2]] for vertex in data['vertex']]
    colours = [[vertex[3]/255.0,vertex[4]/255.0,vertex[5]/255.0] for vertex in data['vertex']]
    triangles = [[vertex[0],vertex[1],vertex[2]] for vertex in data['face'].data['vertex_indices']]
    threes = [3 for face in data['face'].data['vertex_indices']]

    print "Faces:", len(data['face'].data), "Triangles:", len(triangles)

    global terrain, texture, indices
    terrain =  vbo.VBO(array(vertices, dtype=float32))
    texture = vbo.VBO(array(colours, dtype=float32))
    indices = vbo.VBO(array(triangles), target=GL_ELEMENT_ARRAY_BUFFER)
    
    #data = PlyData.read("../vegetation_downsampled.ply")
    
    print "Loaded", len(indices)
    
    
def UpdateFPV():
    
    mouse_dx,mouse_dy = pygame.mouse.get_rel()
    if pygame.mouse.get_pressed()[1]:
        look_speed = .2
        buffer = glGetDoublev(GL_MODELVIEW_MATRIX)
        c = (-1 * mat(buffer[:3,:3]) * \
            mat(buffer[3,:3]).T).reshape(3,1)
        # c is camera center in absolute coordinates, 
        # we need to move it back to (0,0,0) 
        # before rotating the camera
        glTranslate(c[0],c[1],c[2])
        m = buffer.flatten()
        glRotate(mouse_dx * look_speed, m[1],m[5],m[9])
        glRotate(mouse_dy * look_speed, m[0],m[4],m[8])
        
        # compensate roll
        glRotated(-math.atan2(-m[4],m[5]) * \
            57.295779513082320876798154814105 ,m[2],m[6],m[10])
        glTranslate(-c[0],-c[1],-c[2])

    delta_y, delta_x = pygame.mouse.get_rel()
    rotation_direction.x = float(delta_x)
    rotation_direction.y = float(delta_y)
    
    pygame.mouse.set_pos([400, 300])

def main():
    pygame.init()
    display = (800,600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)

    glTranslatef(0.0,0.0, -5)
    
    gluLookAt(0.0,0.0, -5.0,
              0.0,0.0, 0.0,
              0.0,1.0, 0.0)
    
    LoadMesh()
    
    #pygame.event.set_grab(True)

    Draw2()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            if event.type == pygame.KEYDOWN:
                print "Key event"
                
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()
                
                if event.key == pygame.K_LEFT:
                    glTranslatef(-0.5,0,0)
                if event.key == pygame.K_RIGHT:
                    glTranslatef(0.5,0,0)

                if event.key == pygame.K_UP:
                    glTranslatef(0,1,0)
                if event.key == pygame.K_DOWN:
                    glTranslatef(0,-1,0)

            if event.type == pygame.MOUSEBUTTONDOWN:
                print "Mouse event"
                if event.button == 4:
                    glTranslatef(0,0,1.0)

                if event.button == 5:
                    glTranslatef(0,0,-1.0)
        
        Draw2()            
        #UpdateFPV()

        pygame.display.flip()
        pygame.time.delay(10)


main()
