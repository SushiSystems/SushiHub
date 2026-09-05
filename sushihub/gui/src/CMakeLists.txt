find_package(imgui CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(OpenGL REQUIRED)

add_library(sushihub_gui_ui STATIC
    ui/Shell.cpp
    ui/Theme.cpp)
target_include_directories(sushihub_gui_ui PUBLIC "${CMAKE_CURRENT_LIST_DIR}")
target_link_libraries(sushihub_gui_ui
    PUBLIC imgui::imgui
    PRIVATE sushihub_gui_warnings)

add_executable(sushihub_gui main.cpp)
target_link_libraries(sushihub_gui
    PRIVATE sushihub_gui_ui glfw OpenGL::GL sushihub_gui_warnings)
