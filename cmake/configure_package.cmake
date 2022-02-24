#
# Copyright (C) 2018 by George Cave - gcave@stablecoder.ca
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

# Performs multiple operation so other packages may find a package
# Usage: configure_package(NAMSPACE namespace TARGETS targetA targetb)
#   * It installs the provided targets
#   * It exports the provided targets under the provided namespace
#   * It installs the package.xml file
#   * It create and install the ${PROJECT_NAME}-config.cmake and ${PROJECT_NAME}-config-version.cmake
macro(configure_package)
  set(oneValueArgs NAMESPACE)
  set(multiValueArgs TARGETS)
  cmake_parse_arguments(ARG "" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

  if (ARG_TARGETS)
    install(TARGETS ${ARG_TARGETS}
            EXPORT ${PROJECT_NAME}-targets
            RUNTIME DESTINATION bin
            LIBRARY DESTINATION lib
            ARCHIVE DESTINATION lib)
    if (ARG_NAMESPACE)
      install(EXPORT ${PROJECT_NAME}-targets NAMESPACE "${ARG_NAMESPACE}::" DESTINATION lib/cmake/${PROJECT_NAME})
    else()
      install(EXPORT ${PROJECT_NAME}-targets DESTINATION lib/cmake/${PROJECT_NAME})
    endif()
  endif()

  install(FILES package.xml DESTINATION share/${PROJECT_NAME})

  # Create cmake config files
  include(CMakePackageConfigHelpers)
  configure_package_config_file(${CMAKE_CURRENT_LIST_DIR}/cmake/${PROJECT_NAME}-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake
    INSTALL_DESTINATION lib/cmake/${PROJECT_NAME}
    NO_CHECK_REQUIRED_COMPONENTS_MACRO)

  write_basic_package_version_file(${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake
    VERSION ${PROJECT_VERSION} COMPATIBILITY ExactVersion)

  install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake"
    DESTINATION lib/cmake/${PROJECT_NAME})

  install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake"
    DESTINATION share/${PROJECT_NAME}/cmake)

  if (ARG_TARGETS)
    if (ARG_NAMESPACE)
      export(EXPORT ${PROJECT_NAME}-targets NAMESPACE "${ARG_NAMESPACE}::" FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-targets.cmake)
    else()
      export(EXPORT ${PROJECT_NAME}-targets FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-targets.cmake)
    endif()

    install(FILES
      ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-targets.cmake
      DESTINATION share/${PROJECT_NAME}/cmake)

  endif()

  # Allows Colcon to find non-Ament packages when using workspace underlays
  file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/share/ament_index/resource_index/packages/${PROJECT_NAME} "")
  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/share/ament_index/resource_index/packages/${PROJECT_NAME} DESTINATION share/ament_index/resource_index/packages)
  file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/share/${PROJECT_NAME}/hook/ament_prefix_path.dsv "prepend-non-duplicate;AMENT_PREFIX_PATH;")
  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/share/${PROJECT_NAME}/hook/ament_prefix_path.dsv DESTINATION share/${PROJECT_NAME}/hook)
  file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/share/${PROJECT_NAME}/hook/ros_package_path.dsv "prepend-non-duplicate;ROS_PACKAGE_PATH;")
  install(FILES ${CMAKE_CURRENT_BINARY_DIR}/share/${PROJECT_NAME}/hook/ros_package_path.dsv DESTINATION share/${PROJECT_NAME}/hook)

endmacro()