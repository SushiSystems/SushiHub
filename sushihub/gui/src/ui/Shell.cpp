/** @file Shell.cpp
 *  @brief Defines the sidebar, the pane and the routing between them.
 *  @author Mustafa Garip
 */

#include "ui/Shell.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

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

}

Shell::Shell()
    : screen_names_{"Status", "Modules", "Dependencies", "Licence", "Projects"},
      active_index_(0)
{
}

void Shell::draw()
{
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
    return screen_names_[active_index_];
}

void Shell::draw_sidebar()
{
    ImGui::BeginChild("##sushihub_gui_sidebar", ImVec2(Theme::sidebar_width(), 0.0F),
                      ImGuiChildFlags_Borders);
    ImGui::TextUnformatted("SushiStack");
    ImGui::Separator();

    for (std::size_t index = 0; index < screen_names_.size(); ++index)
    {
        const bool selected = index == active_index_;
        if (ImGui::Selectable(screen_names_[index].c_str(), selected))
        {
            active_index_ = index;
        }
    }

    ImGui::EndChild();
}

void Shell::draw_pane()
{
    ImGui::BeginChild("##sushihub_gui_pane", ImVec2(0.0F, 0.0F), ImGuiChildFlags_Borders);
    ImGui::TextUnformatted(active_screen().c_str());
    ImGui::Separator();
    ImGui::EndChild();
}

}
}
