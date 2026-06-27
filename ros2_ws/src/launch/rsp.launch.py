import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    ####### DATA INPUT ##########
    urdf_file_name = 'waiter_robot.xacro'
    package_name = "aut_robot"
    ####### DATA INPUT END ##########

    print("Fetching URDF ==>")
    robot_desc_path = os.path.join(get_package_share_directory(package_name), "urdf", urdf_file_name)
    
    # Process xacro and wrap in ParameterValue
    robot_description_content = Command(['xacro ', robot_desc_path])
    robot_description = ParameterValue(robot_description_content, value_type=str)

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'use_sim_time': False, 'robot_description': robot_description}],
        output="screen"
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': False}],
        output="screen"
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_node,
    ])
