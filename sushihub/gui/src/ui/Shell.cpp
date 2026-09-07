/** @file Shell.cpp
 *  @brief Defines the frame's three bands and the routing of a form request to the commands screen.
 *  @author Mustafa Garip
 */

#include "ui/Shell.hpp"

#include "ui/Theme.hpp"
#include "ui/screens/InstallsScreen.hpp"
#include "ui/screens/ModulesScreen.hpp"
#include "ui/screens/SettingsScreen.hpp"

#include <imgui.h>

#include <filesystem>
#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the flags that pin the frame window to the viewport with no decoration. */
constexpr ImGuiWindowFlags FRAME_FLAGS =
    ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove |
    ImGuiWindowFlags_NoCollapse | ImGuiWindowFlags_NoBringToFrontOnFocus |
    ImGuiWindowFlags_NoNavFocus | ImGuiWindowFlags_NoScrollbar;

/** @brief Holds the `hub` program the shell falls back to, found on the search path. */
constexpr const char* DEFAULT_EXECUTABLE = "hub";

/** @brief Holds the index of the commands screen in the rail. */
constexpr std::size_t COMMANDS_INDEX = 3;

/** @brief Returns the directory the window reports itself as open on. */
std::string workspace_path()
{
    std::error_code failure;
    const std::filesystem::path here = std::filesystem::current_path(failure);
    return failure ? std::string() : here.string();
}

}

const std::vector<std::string>& covered_commands()
{
    static const std::vector<std::string> covered{
        "doctor", "license", "login", "logout", "status", "whoami"};
    return covered;
}

Shell::Shell()
    : Shell(DEFAULT_EXECUTABLE)
{
}

Shell::Shell(std::string hub_executable)
    : workspace_(hub_executable),
      catalogue_(hub_executable),
      commands_(nullptr),
      active_index_(0)
{
    auto commands = std::unique_ptr<CommandsScreen>(
        new CommandsScreen(catalogue_, covered_commands(), workspace_.executable(),
                           run_log_));
    commands_ = commands.get();

    screens_.emplace_back(new InstallsScreen(workspace_, run_log_));
    screens_.emplace_back(new ModulesScreen(workspace_, *this));
    screens_.emplace_back(new SettingsScreen(workspace_, run_log_));
    screens_.emplace_back(std::move(commands));

    screen_names_.reserve(screens_.size());
    for (const std::unique_ptr<Screen>& screen : screens_)
    {
        screen_names_.push_back(screen->name());
    }

    catalogue_.start();
}

void Shell::draw()
{
    catalogue_.poll();

    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(viewport->WorkPos);
    ImGui::SetNextWindowSize(viewport->WorkSize);

    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0.0F, 0.0F));
    ImGui::Begin("##sushihub_gui_frame", nullptr, FRAME_FLAGS);
    ImGui::PopStyleVar();

    title_bar_.draw(workspace_path(), std::string());
    draw_body();
    strip_.draw(run_log_);

    ImGui::End();
}

const char* Shell::active_screen() const
{
    return screens_[active_index_]->name();
}

void Shell::open_form(const std::string& command, const std::vector<std::string>& arguments)
{
    if (commands_ == nullptr)
    {
        return;
    }
    commands_->open_form(command, arguments);
    active_index_ = COMMANDS_INDEX;
}

void Shell::draw_body()
{
    const float body_height = ImGui::GetContentRegionAvail().y - strip_.height();

    ImGui::BeginChild("##sushihub_gui_body", ImVec2(0.0F, body_height), ImGuiChildFlags_None,
                      ImGuiWindowFlags_NoScrollbar);

    rail_.draw(screen_names_, active_index_);

    ImGui::SameLine(0.0F, 0.0F);
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::ground());
    ImGui::BeginChild("##sushihub_gui_screen", ImVec2(0.0F, 0.0F), ImGuiChildFlags_None);
    screens_[active_index_]->draw();
    ImGui::EndChild();
    ImGui::PopStyleColor();

    ImGui::EndChild();
}

}
}
