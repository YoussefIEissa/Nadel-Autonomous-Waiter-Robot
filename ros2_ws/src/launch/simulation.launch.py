import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from pathlib import Path


def generate_launch_description():
    pkg_name = "aut_robot"
    spawn_node = "create"

    # Paths
    rsp_file = "rsp.launch.py"
    rsp_path = os.path.join(get_package_share_directory(pkg_name), "launch", rsp_file)
    world_file = "maze.sdf"
    world_path = os.path.join(get_package_share_directory(pkg_name), "worlds", world_file)
    rviz_config_file = os.path.join(get_package_share_directory(pkg_name), "rviz", "show_robot.rviz")

    use_rviz = LaunchConfiguration("rviz", default=True)

    # Set Gazebo resource path
    robot_dir = get_package_share_directory(pkg_name)
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[str(Path(robot_dir).parent.resolve())]
    )
    
    # CRITICAL FIX: Add IGN_GAZEBO_SYSTEM_PLUGIN_PATH for ros2_control
    ign_plugin_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        value=[os.path.join(get_package_share_directory('ign_ros2_control'), 'lib')]
    )

    # Launch robot_state_publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([rsp_path])
    )

    # Launch Gazebo using ros_gz_sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ]),
        launch_arguments={
            'gz_args': f'-r {world_path}'  # Use your world file
        }.items()
    )


    
    # Spawn the robot into Gazebo
    spawn_entity = Node(
        package="ros_gz_sim",
        executable=spawn_node,
        arguments=[
            "-topic", "robot_description",
            "-name", "waiter_robot",
            "-z", "0.1"
        ],
        output="screen"
    )

    # Bridge for lidar
    bridge_lidar = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='lidar_bridge',
        arguments=['/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan'],
        output='screen'
    )

    # Bridge for clock (IMPORTANT for use_sim_time)
    bridge_clock = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',  # ← ADD THIS
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # Spawn diff_drive_controller with delay
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
        output="screen"
    )

    # Spawn joint_state_broadcaster with delay
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
        output="screen"
    )

    # Launch RViz2
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config_file],
        output="screen",
        condition=IfCondition(use_rviz)
    )

    # Delay controller spawners to wait for Gazebo and ros2_control plugin
    delayed_diff_spawner = TimerAction(
        period=5.0,  # Wait 5 seconds after spawn_entity finishes
        actions=[diff_drive_spawner]
    )
    
    delayed_joint_spawner = TimerAction(
        period=6.0,  # Wait 6 seconds
        actions=[joint_broad_spawner]
    )

    return LaunchDescription([
        gz_resource_path,
        ign_plugin_path,  # CRITICAL: This makes ros2_control plugin loadable
        rsp,
        gazebo,
        spawn_entity,
        bridge_lidar,
        bridge_clock,
        delayed_diff_spawner,  # Delayed controller spawning
        delayed_joint_spawner,
        rviz,
    ])
