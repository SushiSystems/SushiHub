/** @file main.cpp
 *  @brief Opens the window, runs the frame loop over the shell, and tears both down.
 *  @author Mustafa Garip
 */

#include "ui/Shell.hpp"
#include "ui/Theme.hpp"

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

#include <GLFW/glfw3.h>

#include <cstdio>

namespace
{

/** @brief Holds the title the window bar shows. */
constexpr const char* WINDOW_TITLE = "SushiStack";

/** @brief Holds the GLSL version string the OpenGL3 backend compiles its shaders against. */
constexpr const char* GLSL_VERSION = "#version 130";

/** @brief Writes one GLFW failure to stderr. */
void report_glfw_error(int code, const char* description)
{
    std::fprintf(stderr, "glfw error %d: %s\n", code, description);
}

}

/** @brief Runs the application until the window closes and returns the process exit code. */
int main()
{
    glfwSetErrorCallback(report_glfw_error);
    if (glfwInit() == GLFW_FALSE)
    {
        return 1;
    }

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 2);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);
#endif

    GLFWwindow* window = glfwCreateWindow(1280, 800, WINDOW_TITLE, nullptr, nullptr);
    if (window == nullptr)
    {
        glfwTerminate();
        return 1;
    }

    glfwMakeContextCurrent(window);
    glfwSwapInterval(1);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGui::GetIO().IniFilename = nullptr;
    SushiHub::Gui::Theme::apply();

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init(GLSL_VERSION);

    SushiHub::Gui::Shell shell;

    while (glfwWindowShouldClose(window) == GLFW_FALSE)
    {
        glfwPollEvents();

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        shell.draw();

        ImGui::Render();

        int width = 0;
        int height = 0;
        glfwGetFramebufferSize(window, &width, &height);
        glViewport(0, 0, width, height);
        glClearColor(0.086F, 0.090F, 0.106F, 1.0F);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(window);
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}
