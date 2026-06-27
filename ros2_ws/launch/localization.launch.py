from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python import get_package_share_directory
from launch_ros.actions import Node
import os


def generate_launch_description():
    # Package configuration
    package_name = "navigation"
    config_dir = os.path.join(get_package_share_directory(package_name), "config")
    
    # File paths
    localization_config_file = os.path.join(config_dir, 'amcl_config.yaml')
    map_file = os.path.join(config_dir, "obs_map.yaml")
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map')
    
    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=map_file,
        description='Full path to map yaml file to load'
    )
    
    # Map server node
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_yaml_file}
        ],
    )
    
    # AMCL localization node
    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[localization_config_file]
    )
    
    # Lifecycle manager to manage map_server and amcl
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': ['map_server', 'amcl']}
        ]
    )
    
    # Create launch description
    ld = LaunchDescription()
    
    # Add launch arguments
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_map_yaml_cmd)
    
    # Add nodes
    ld.add_action(map_server)
    ld.add_action(amcl)
    ld.add_action(lifecycle_manager)
    
    return ld
