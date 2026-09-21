/** @file NavRail.cpp
 *  @brief Defines the rail's entries, their hover fill and the accent bar the active one carries.
 *  @author Mustafa Garip
 */

#include "ui/chrome/NavRail.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Draws the accent bar down the left edge of the item just submitted. */
void draw_active_bar()
{
    const ImVec2 top = ImGui::GetItemRectMin();
    const ImVec2 bottom = ImGui::GetItemRectMax();
    const ImVec2 corner(top.x + ImGui::GetFontSize() * 0.2F, bottom.y);
    ImGui::GetWindowDrawList()->AddRectFilled(top, corner, ImGui::GetColorU32(Theme::accent()));
}

}

float NavRail::width()
{
    return ImGui::GetFontSize() * 11.0F;
}

bool NavRail::draw(const std::vector<const char*>& names, std::size_t& active)
{
    bool changed = false;

    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::rail());
    ImGui::BeginChild("##sushihub_nav_rail", ImVec2(width(), 0.0F), ImGuiChildFlags_None,
                      ImGuiWindowFlags_NoScrollbar);

    ImGui::PushStyleColor(ImGuiCol_Header, Theme::panel_raised());
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, Theme::panel());
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, Theme::panel_raised());
    ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing,
                        ImVec2(ImGui::GetFontSize() * 0.3F, ImGui::GetFontSize() * 0.3F));

    ImGui::Dummy(ImVec2(0.0F, ImGui::GetFontSize() * 0.4F));

    for (std::size_t index = 0; index < names.size(); ++index)
    {
        const bool selected = index == active;
        ImGui::PushStyleColor(ImGuiCol_Text, selected ? Theme::ink() : Theme::ink_dim());
        const bool clicked = ImGui::Selectable(names[index], selected, ImGuiSelectableFlags_None,
                                               ImVec2(0.0F, ImGui::GetFontSize() * 1.8F));
        ImGui::PopStyleColor();

        if (selected)
        {
            draw_active_bar();
        }
        if (clicked && !selected)
        {
            active = index;
            changed = true;
        }
    }

    ImGui::PopStyleVar();
    ImGui::PopStyleColor(3);
    ImGui::EndChild();
    ImGui::PopStyleColor();

    return changed;
}

}
}
