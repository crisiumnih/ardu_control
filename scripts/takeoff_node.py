#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandTOL, SetMode
from geometry_msgs.msg import PoseStamped

class TakeoffNode(Node):
    def __init__(self):
        super().__init__('takeoff_node')
        self.state_sub = self.create_subscription(State, '/mavros/state', self.state_callback, 10)
        self.local_pos_pub = self.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)

        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')

        self.timer = self.create_timer(1.0, self.control_loop)

        self.current_state = None
        self.takeoff_commanded = False

        self.get_logger().info('Takeoff Node started')
    
    def state_callback(self, msg):
        self.current_state = msg
    
    def control_loop(self):
        if self.current_state is None:
            self.get_logger().info('Waiting for MAVROS state.')
            return
        if not self.current_state.connected:
            self.get_logger().info('Waiting for MAVROS connection.')
            return

        if self.current_state.mode != 'GUIDED':
            set_mode_req = SetMode.Request()
            set_mode_req.custom_mode = 'GUIDED'
            future = self.set_mode_client.call_async(set_mode_req)
            future.add_done_callback(self.mode_set_callback)
        elif not self.current_state.armed:
            arm_req = CommandBool.Request()
            arm_req.value = True
            future = self.arming_client.call_async(arm_req)
            future.add_done_callback(self.arm_callback)
        elif not self.takeoff_commanded:
            takeoff_req = CommandTOL.Request()
            takeoff_req.altitude = 4.0
            future = self.takeoff_client.call_async(takeoff_req)
            future.add_done_callback(self.takeoff_callback)

        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.z = 4.0
        self.local_pos_pub.publish(pose)
    
    def mode_set_callback(self, future):
        try:
            response = future.result()
            if response.mode_sent:
                self.get_logger().info('GUIDED mode set')
            else:
                self.get_logger().info('Failed to set GUIDED mode')
        except Exception as e:
            self.get_logger().error(f'Mode set failed: {e}')

    def arm_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info('Drone armed')
            else:
                self.get_logger().error('Arming failed')
        except Exception as e:
            self.get_logger().error(f'Arming failed: {e}')
    
    def takeoff_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info('Takeoff to 4m commanded')
                self.takeoff_commanded = True
            else:
                self.get_logger().error('Takeoff failed')
        except Exception as e:
            self.get_logger().error(f'Takeoff failed: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = TakeoffNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()