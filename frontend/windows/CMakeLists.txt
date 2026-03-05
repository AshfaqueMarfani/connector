cmake_minimum_required(VERSION 3.14)
project(connector_app LANGUAGES CXX)

set(BINARY_NAME "connector_app")

cmake_policy(VERSION 3.14...3.25)

set(CMAKE_INSTALL_PREFIX "${CMAKE_BINARY_DIR}/install" CACHE PATH "..." FORCE)

add_subdirectory("flutter")

# Application build
add_subdirectory("runner")

# Generated plugin build
add_subdirectory("flutter/ephemeral/.plugin_symlinks" EXCLUDE_FROM_ALL)

# === Installation ===
set(BUILD_BUNDLE_DIR "$<TARGET_FILE_DIR:${BINARY_NAME}>")
install(CODE "
  file(REMOVE_RECURSE \"${BUILD_BUNDLE_DIR}/\")
  " COMPONENT Runtime)

install(TARGETS ${BINARY_NAME} RUNTIME DESTINATION "${BUILD_BUNDLE_DIR}"
  COMPONENT Runtime)

install(FILES "${FLUTTER_ICU_DATA_FILE}" DESTINATION "${BUILD_BUNDLE_DIR}"
  COMPONENT Runtime)

install(FILES "$<TARGET_FILE:flutter_wrapper_app>" DESTINATION "${BUILD_BUNDLE_DIR}"
  COMPONENT Runtime)
