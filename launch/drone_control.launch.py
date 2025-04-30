import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # Paths
    ardupilot_gz_bringup_dir = get_package_share_directory('ardupilot_gz_bringup')
    drone_control_dir = get_package_share_directory('drone_control')

    # Include the iris_maze launch file from ardupilot_gz_bringup
    iris_maze_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ardupilot_gz_bringup_dir, 'launch', 'iris_maze.launch.py')
        ),
        launch_arguments={
            'rviz': 'true',
            'use_gz_tf': 'true',
            'mavproxy_args': '--master tcp:127.0.0.1:5760 --sitl 127.0.0.1:5501 --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551',
        }.items()
    )

    # MAVROS node
    mavros_node = Node(
        package='mavros',
        executable='mavros_node',
        name='mavros',
        output='screen',
        parameters=[
            {'fcu_url': 'udp://:14550@127.0.0.1:14550'},
            {'gcs_url': ''},
            {'target_system_id': 1},
            {'target_component_id': 1},
            {'plugin_whitelist': ['sys_status', 'heartbeat', 'command', 'global_position', 'setpoint_position', 'local_position', 'imu', 'gps']},
        ],
        # arguments=['--ros-args', '--log-level', 'debug']
    )

    # Takeoff node
    takeoff_node = Node(
        package='drone_control',
        executable='takeoff_node.py',
        name='takeoff_node',
        output='screen'
    )

    # RViz node
    rviz_config_path = os.path.join(drone_control_dir, 'rviz', 'drone_control.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    return LaunchDescription([
        iris_maze_launch,
        mavros_node,
        takeoff_node,
        rviz_node
    ])