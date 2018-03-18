import bpy

tx = 0.0
ty = 0.0
tz = 10.0

rx = 1.0
ry = 0.0
rz = 0.0

fov = 20.0

pi = 3.14159265

scene = bpy.data.scenes["Scene"]

# Set render resolution
scene.render.resolution_x = 480
scene.render.resolution_y = 359

# Set camera fov in degrees
scene.camera.data.angle = fov*(pi/180.0)

# Set camera rotation in euler angles
scene.camera.rotation_mode = 'XYZ'
scene.camera.rotation_euler[0] = rx*(pi/180.0)
scene.camera.rotation_euler[1] = ry*(pi/180.0)
scene.camera.rotation_euler[2] = rz*(pi/180.0)

# Set camera translation
scene.camera.location.x = tx
scene.camera.location.y = ty
scene.camera.location.z = tz
