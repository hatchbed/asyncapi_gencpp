# asyncapi_gencpp
C++ code generator for [Async API](https://www.asyncapi.com/) messages from a specification file.

The generator is implemented as as python3 script with the following usage:

```
usage: asyncapi_gencpp.py [-h] spec prefix outdir

positional arguments:
  spec        AsyncAPI specification file
  prefix      Include file prefix
  outdir      Output directory
```

The script will generate C++ data structures and code for parsing and writing
the JSON objects described in the `components` and `messages` sections of the
asyncapi spec file.  Low level JSON parsing code is handled using the header
only [nlohmann json](https://github.com/nlohmann/json) library.

The generated objects are returned as std::optional<> to deal with parsing
failures, and so will be dependent on C++17.

The generator can also be used directly in cmake using a provided macro.


## Example Usage:

#### asyncapi.yaml
```
components:
  schemas:
    pose:
      type: object
      properties:
        position:
          $ref: '#/components/schemas/vector3'
        orientation:
          type: object
          properties:
            - w:
              type: number
            - x:
              type: number
            - y:
              type: number
            - z:
              type: number
          required:
            - w
            - x
            - y
            - z
      required:
        - position
        - orientation
    vector3:
      type: object
      properties:
        x:
          type: number
        y:
          type: number
        z:
          type: number
      required:
        - x
        - y
        - z
```

#### CMakeLists.txt
```
project(example)
find_package(asyncapi_gencpp REQUIRED)

# asyncapi_gencpp macro provided via find_package(asyncapi_gencpp)
asyncapi_gencpp(${PROJECT_SOURCE_DIR}/api/asyncapi.yaml ${PROJECT_NAME}/msg ${CMAKE_CURRENT_BINARY_DIR}/include)

add_executable(main src/main.cpp)
add_dependencies(main ${PROJECT_NAME}_gencpp)

```

#### main.cpp
```
#include <iostream>
#include <example/msg/messages.h>  // This header includes all of the includes for the generated code, but individual
                                   // message headers can also be include as needed.

int main(int argc, char **argv) {

  // serialize to JSON
  example::msg::Pose pose;
  pose.position.x = 0.0;
  pose.position.y = 0.0;
  pose.position.z = 0.0;
  pose.orientation.w = 1.0;
  pose.orientation.x = 0.0;
  pose.orientation.y = 0.0;
  pose.orientation.z = 0.0;
  std::string json_string = pose.dump();

  // deserialize from JSON
  auto pose2 = example::msg::Pose::fromJson(json_string);
  if (pose2) {
    std::cout << "position: \n";
    std::cout << " x: " << pose2->position.x << "\n";
    std::cout << " y: " << pose2->position.y << "\n";
    std::cout << " z: " << pose2->position.z << "\n";
    std::cout << "orientation: \n";
    std::cout << " w: " << pose2->orientation.w << "\n";
    std::cout << " x: " << pose2->orientation.x << "\n";
    std::cout << " y: " << pose2->orientation.y << "\n";
    std::cout << " z: " << pose2->orientation.z << "\n";
  }

  return 0;
}

```

For a more complete example see the [rpad](https://github.com/hatchbed/rpad) library.

## ROS Support

This library is agnostic to ROS, but is packaged to work in a ROS1 or ROS2
workspace.