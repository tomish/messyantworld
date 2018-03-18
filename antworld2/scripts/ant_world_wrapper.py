#!/usr/bin/env python

## Simple talker demo that published std_msgs/Strings messages
## to the 'chatter' topic

import rospy
from std_msgs.msg import String
from AntWorld import AntWorld
import os
import cv2

class ant_world_wrapper:

  running = False

  def __init__(self):

    self.world = AntWorld()

    rospy.init_node('ant_world', anonymous=True)

    rospy.Subscriber("chatter", String, self.callback)

    pub = rospy.Publisher('chatter', String, queue_size=10)

    rate = rospy.Rate(1) # 1hz
    
    self.running = True
    
    while self.running and not rospy.is_shutdown():
      self.tick()
      hello_str = "hello world %s" % rospy.get_time()
      rospy.loginfo(hello_str)
      pub.publish(hello_str)
      rate.sleep()
        
    self.cleanup()
        
  def tick(self):
    if self.world.loop():
      self.world.draw()
      if self.world.shutdown():
        self.shutdown()
      frame = self.world.screengrab()
      cv2.imshow("Feed", frame)
      k = cv2.waitKey(1) & 0xff
          
  def callback(self, data):
    rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.data)

  def shutdown(self):
    self.running = False
    
  def cleanup(self):  
    self.world.cleanup()

if __name__ == '__main__':
  print "Dir:", os.getcwd()
  try:
      aww = ant_world_wrapper()
  except rospy.ROSInterruptException:
      pass
