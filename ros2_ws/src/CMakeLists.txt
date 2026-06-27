cmake_minimum_required(VERSION 3.8)
project(aut_robot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)  # ADD THIS LINE
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rclpy REQUIRED)              # ADD THIS LINE

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# C++ executable
add_executable(cmd_vel_mapper src/cmd_vel_mapper.cpp)
ament_target_dependencies(cmd_vel_mapper rclcpp geometry_msgs)

# Install C++ executables
install(TARGETS
   cmd_vel_mapper
   DESTINATION lib/${PROJECT_NAME}
)

# Install Python scripts (ADD THIS SECTION)
install(PROGRAMS
  scripts/diff_drive_odometry.py
  scripts/onemeter.py
  scripts/rotateright.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install directories
install(
  DIRECTORY
    urdf
    launch
    config
    src
    scripts
    rviz
    worlds
  DESTINATION
    share/${PROJECT_NAME}
)

# Install .sdf files specifically (FIXED)
install(
  DIRECTORY worlds/
  DESTINATION share/${PROJECT_NAME}/worlds
  FILES_MATCHING PATTERN "*.sdf"
)

ament_package()
