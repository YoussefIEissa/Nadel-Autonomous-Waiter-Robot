import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition

def generate_launch_description():
    
    package_name = "navigation"
    
    # File paths
    rviz_config_file = os.path.join(get_package_share_directory(package_name), "rviz", "nav.rviz")
    controller_yaml = os.path.join(get_package_share_directory(package_name), 'config', 'controller.yaml')
    bt_navigator_yaml = os.path.join(get_package_share_directory(package_name), 'config', 'bt_navigator.yaml')
    planner_yaml = os.path.join(get_package_share_directory(package_name), 'config', 'planner_server.yaml')
    recovery_yaml = os.path.join(get_package_share_directory(package_name), 'config', 'recovery.yaml')

    use_rviz = LaunchConfiguration("rviz", default=True)

    return LaunchDescription([
        # 🧭 Planner Server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[planner_yaml]
        ),

        # 🕹️ Controller Server
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[controller_yaml]
        ),

        # 🔁 Recovery Behaviors
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='recoveries_server',
            parameters=[recovery_yaml],
            output='screen'
        ),

        # 🌿 Behavior Tree Navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[bt_navigator_yaml]
        ),

        # ⚙️ Lifecycle Manager
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_pathplanner',
            output='screen',
            parameters=[{'autostart': True},
                        {'node_names': [
                            'planner_server',
                            'controller_server',
                            'recoveries_server',
                            'bt_navigator'
                        ]}]
        ),

        # 👁️ RViz2 Visualization
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen',
            condition=IfCondition(use_rviz)
        ),
    ])