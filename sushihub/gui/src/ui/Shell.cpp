/** @file Shell.cpp
 *  @brief Defines the sidebar, the pane and the routing between screens and generated forms.
 *  @author Mustafa Garip
 */

#include "ui/Shell.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

#include <algorithm>
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

/** @brief Holds the `ss` program the shell falls back to, found on the search path. */
constexpr const char* DEFAULT_EXECUTABLE = "ss";

/** @brief Holds the commands a hand-drawn screen already covers, so no form repeats them. */
const std::vector<std::string>& covered_commands()
{
    static const std::vector<std::string> covered{
        "doctor", "license", "login", "projects add", "projects list", "projects remove",
        "status", "whoami"};
    return covered;
}

/** @brief Reports whether a hand-drawn screen already covers @p command. */
bool is_covered(const std::string& command)
{
    const std::vector<std::string>& covered = covered_commands();
    return std::find(covered.begin(), covered.end(), command) != covered.end();
}

}

Shell::Shell()
    : Shell(DEFAULT_EXECUTABLE)
{
}

Shell::Shell(std::string ss_executable)
    : workspace_(ss_executable),
      catalogue_(ss_executable),
      status_screen_(workspace_),
      modules_screen_(workspace_, *this),
      dependencies_screen_(workspace_, *this),
      licence_screen_(workspace_),
      projects_screen_(workspace_),
      screen_names_{"Status", "Modules", "Dependencies", "Licence", "Projects"},
      active_index_(0)
{
    catalogue_.start();
}

void Shell::draw()
{
    catalogue_.poll();

    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(viewport->WorkPos);
    ImGui::SetNextWindowSize(viewport->WorkSize);

    ImGui::Begin("##sushihub_gui_frame", nullptr, FRAME_FLAGS);
    draw_sidebar();
    ImGui::SameLine();
    draw_pane();
    ImGui::End();
}

const std::string& Shell::active_screen() const
{
    return active_command_.empty() ? screen_names_[active_index_] : active_command_;
}

void Shell::open_form(const std::string& command, const std::vector<std::string>& arguments)
{
    GeneratedForm* form = form_for(command);
    if (form == nullptr)
    {
        return;
    }

    form->prefill_arguments(arguments);
    active_command_ = command;
}

void Shell::draw_sidebar()
{
    ImGui::BeginChild("##sushihub_gui_sidebar", ImVec2(Theme::sidebar_width(), 0.0F),
                      ImGuiChildFlags_Borders);
    ImGui::TextUnformatted("SushiStack");
    ImGui::Separator();

    for (std::size_t index = 0; index < screen_names_.size(); ++index)
    {
        const bool selected = active_command_.empty() && index == active_index_;
        if (ImGui::Selectable(screen_names_[index].c_str(), selected))
        {
            active_index_ = index;
            active_command_.clear();
        }
    }

    draw_command_list();
    ImGui::EndChild();
}

void Shell::draw_command_list()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::SeparatorText("Commands");
    ImGui::PopStyleColor();

    if (!catalogue_.finished())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
        ImGui::TextUnformatted("reading...");
        ImGui::PopStyleColor();
        return;
    }

    if (!catalogue_.error().empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour("error"));
        ImGui::TextWrapped("%s", catalogue_.error().c_str());
        ImGui::PopStyleColor();
        return;
    }

    for (const Command& command : catalogue_.catalogue().commands)
    {
        if (is_covered(command.name))
        {
            continue;
        }
        if (ImGui::Selectable(command.name.c_str(), active_command_ == command.name))
        {
            active_command_ = command.name;
        }
    }
}

void Shell::draw_pane()
{
    ImGui::BeginChild("##sushihub_gui_pane", ImVec2(0.0F, 0.0F), ImGuiChildFlags_Borders);

    if (!active_command_.empty())
    {
        GeneratedForm* form = form_for(active_command_);
        if (form != nullptr)
        {
            form->draw();
        }
    }
    else if (active_index_ == 0)
    {
        status_screen_.draw();
    }
    else if (active_index_ == 1)
    {
        modules_screen_.draw();
    }
    else if (active_index_ == 2)
    {
        dependencies_screen_.draw();
    }
    else if (active_index_ == 3)
    {
        licence_screen_.draw();
    }
    else
    {
        projects_screen_.draw();
    }

    ImGui::EndChild();
}

GeneratedForm* Shell::form_for(const std::string& command)
{
    const auto found = forms_.find(command);
    if (found != forms_.end())
    {
        return found->second.get();
    }

    for (const Command& entry : catalogue_.catalogue().commands)
    {
        if (entry.name != command)
        {
            continue;
        }
        auto form = std::unique_ptr<GeneratedForm>(
            new GeneratedForm(entry, workspace_.executable()));
        const auto inserted = forms_.emplace(command, std::move(form));
        return inserted.first->second.get();
    }

    return nullptr;
}

}
}
