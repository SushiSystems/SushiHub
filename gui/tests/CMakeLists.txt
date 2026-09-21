find_package(GTest CONFIG REQUIRED)
include(GoogleTest)

set(SUSHIHUB_GUI_FIXTURE_DIR "${CMAKE_CURRENT_LIST_DIR}/fixtures")

# One suite per layer: a target, its libraries, the fixture directory, and discovery.
function(sushihub_gui_add_test suite_name source_file)
    add_executable(${suite_name} "${source_file}")
    target_include_directories(${suite_name} PRIVATE "${CMAKE_CURRENT_LIST_DIR}")
    target_link_libraries(${suite_name}
        PRIVATE ${ARGN} GTest::gtest GTest::gtest_main sushihub_gui_warnings)
    target_compile_definitions(${suite_name}
        PRIVATE SUSHIHUB_GUI_FIXTURE_DIR="${SUSHIHUB_GUI_FIXTURE_DIR}")
    gtest_discover_tests(${suite_name})
endfunction()

sushihub_gui_add_test(sushihub_gui_bridge_test bridge_test.cpp sushihub_gui_bridge)
sushihub_gui_add_test(sushihub_gui_event_test event_test.cpp sushihub_gui_contract)
sushihub_gui_add_test(sushihub_gui_catalogue_test catalogue_test.cpp sushihub_gui_contract)
sushihub_gui_add_test(sushihub_gui_model_test model_test.cpp sushihub_gui_model)
sushihub_gui_add_test(sushihub_gui_install_facts_test install_facts_test.cpp sushihub_gui_model)
