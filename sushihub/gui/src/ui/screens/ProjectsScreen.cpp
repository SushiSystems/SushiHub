/** @file ProjectsScreen.cpp
 *  @brief Defines the empty state the projects screen shows until its command lands.
 *  @author Mustafa Garip
 */

#include "ui/screens/ProjectsScreen.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the sentence that names the wave the screen waits for. */
constexpr const char* EMPTY_STATE = "Projects arrive with wave 5";

/** @brief Holds the line that says what the screen will show once the command exists. */
constexpr const char* EXPLANATION =
    "This screen will list the projects the workspace holds once `ss projects` reports them.";

}

void ProjectsScreen::draw()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText(EMPTY_STATE);
    ImGui::PopStyleColor();

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextWrapped("%s", EXPLANATION);
    ImGui::PopStyleColor();
}

}
}
