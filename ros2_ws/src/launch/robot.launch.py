from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import os

pkg_name = "aut_robot"

def include_rsp_launch():
    rsp_file = "rsp.launch.py"
    rsp_path = os.path.join(get_package_share_directory(pkg_name), "launch", rsp_file)
    return IncludeLaunchDescription(PythonLaunchDescriptionSource([rsp_path]))

def generate_launch_description():
    rsp_launch = include_rsp_launch()

    # ===== MICRO-ROS AGENT (ESP32 Communication) =====
    micro_ros_agent = ExecuteProcess(
        cmd=['ros2', 'run', 'micro_ros_agent', 'micro_ros_agent',
             'serial', '--dev', '/dev/ttyUSB1', '-b', '115200'],
        output='screen',
        shell=False
    )
    # ===== MICRO-ROS AGENT (ESP32 Communication - WIFI) =====
    # Uncomment if using WiFi instead of Serial
    # micro_ros_agent_wifi = ExecuteProcess(
    #     cmd=['ros2', 'run', 'micro_ros_agent', 'micro_ros_agent',
    #          'udp4', '--port', '8888', '-v6'],
    #     output='screen',
    #     shell=False
    # )

    #===== ODOMETRY CALCULATOR (From ESP32 Encoders) =====
    odometry_node = Node(
        package='aut_robot',
        executable='diff_drive_odometry.py',
        name='diff_drive_odometry',
        output='screen',
        parameters=[{
            'wheel_radius': 0.0845,  # 32.5mm wheel radius
            'wheel_base': 0.55,      # 16cm between wheels
            'ticks_per_revolution': 400  # ✅ ADD THIS - YOUR ENCODER CPR
        }]
    )

    # ===== REAL LIDAR (USB1 for lidar) =====
    lidar = Node(
        name='sllidar_node',
        package='sllidar_ros2',
        executable='sllidar_node',
        output='screen',
        parameters=[{
            'serial_port': '/dev/ttyUSB0',
            'serial_baudrate': 115200,
            'frame_id': 'laser_frame',
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Sensitivity'
        }]
    )

    # ===== CMD_VEL MAPPER =====
    cmd_vel_mapper = Node(
        package="aut_robot",
        executable="cmd_vel_mapper",
        output="screen"
    )

    return LaunchDescription([
        rsp_launch,
        micro_ros_agent,                                    # ✅ Start ESP32 agent first
        micro_ros_agent_wifi,                             # Uncomment if using WiFi
        TimerAction(period=2.0, actions=[odometry_node]),   # ✅ Wait 2s, then start odometry
        lidar,                                              # ✅ LIDAR
        cmd_vel_mapper                                      # ✅ Command mapper
    ])
