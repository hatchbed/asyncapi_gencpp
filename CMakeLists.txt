cmake_minimum_required(VERSION 3.1)
project(asyncapi_gencpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR})

### Install ###

include(${PROJECT_SOURCE_DIR}/cmake/configure_package.cmake)
configure_package()