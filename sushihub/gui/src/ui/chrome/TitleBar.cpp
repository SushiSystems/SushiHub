/** @file TitleBar.cpp
 *  @brief Defines the accent dot, the version, the workspace chip and the account of the top row.
 *  @author Mustafa Garip
 */

#include "ui/chrome/TitleBar.hpp"

#include "ui/Theme.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the text shown when no account is signed in. */
constexpr const char* NO_ACCOUNT = "Sign in";

/** @brief Draws the accent dot that opens the row and advances the cursor past it. */
void draw_dot()
{
    const float radius = ImGui::GetFontSize() * 0.25F;
    const ImVec2 origin = ImGui::GetCursorScreenPos();
    const ImVec2 centre(origin.x + radius, origin.y + ImGui::GetFontSize() * 0.5F);
    ImGui::GetWindowDrawList()->AddCircleFilled(centre, radius,
                                                ImGui::GetColorU32(Theme::accent()));
    ImGui::Dummy(ImVec2(radius * 2.0F, ImGui::GetFontSize()));
}

/** @brief Draws @p text in @p colour on one line without wrapping. */
void draw_text(const char* text, const ImVec4& colour)
{
    ImGui::PushStyleColor(ImGuiCol_Text, colour);
    ImGui::TextUnformatted(text);
    ImGui::PopStyleColor();
}

/** @brief Draws @p path inside a bordered chip and advances the cursor past it. */
void draw_workspace_chip(const std::string& path)
{
    const float pad_x = ImGui::GetFontSize() * 0.5F;
    const float pad_y = ImGui::GetFontSize() * 0.2F;
    const ImVec2 text_size = ImGui::CalcTextSize(path.c_str());
    const ImVec2 origin = ImGui::GetCursorScreenPos();
    const ImVec2 corner(origin.x + text_size.x + pad_x * 2.0F,
                        origin.y + text_size.y + pad_y * 2.0F);

    ImDrawList* draw_list = ImGui::GetWindowDrawList();
    draw_list->AddRectFilled(origin, corner, ImGui::GetColorU32(Theme::panel()),
                             Theme::corner_radius());
    draw_list->AddRect(origin, corner, ImGui::GetColorU32(Theme::line()),
                       Theme::corner_radius());
    draw_list->AddText(ImVec2(origin.x + pad_x, origin.y + pad_y),
                       ImGui::GetColorU32(Theme::ink_dim()), path.c_str());

    ImGui::Dummy(ImVec2(corner.x - origin.x, corner.y - origin.y));
}

}

float TitleBar::height()
{
    return ImGui::GetFontSize() * 2.4F;
}

void TitleBar::draw(const std::string& version, const std::string& workspace,
                    const std::string& account)
{
    ImGui::PushStyleColor(ImGuiCol_ChildBg, Theme::rail());
    ImGui::BeginChild("##sushihub_title_bar", ImVec2(0.0F, height()), ImGuiChildFlags_None,
                      ImGuiWindowFlags_NoScrollbar);

    ImGui::SetCursorPosY(ImGui::GetFontSize() * 0.6F);
    ImGui::Indent(ImGui::GetFontSize() * 0.8F);

    draw_dot();
    ImGui::SameLine();
    draw_text("Sushi Hub", Theme::ink());
    if (!version.empty())
    {
        ImGui::SameLine();
        draw_text(version.c_str(), Theme::ink_faint());
    }

    ImGui::SameLine(0.0F, ImGui::GetFontSize());
    ImGui::SetCursorPosY(ImGui::GetFontSize() * 0.4F);
    draw_workspace_chip(workspace);

    const std::string identity = account.empty() ? std::string(NO_ACCOUNT) : account;
    const float right = ImGui::GetContentRegionMax().x - ImGui::CalcTextSize(identity.c_str()).x -
                        ImGui::GetFontSize();
    ImGui::SameLine(right);
    ImGui::SetCursorPosY(ImGui::GetFontSize() * 0.6F);
    draw_text(identity.c_str(), account.empty() ? Theme::ink_faint() : Theme::ink_dim());

    ImGui::Unindent(ImGui::GetFontSize() * 0.8F);
    ImGui::EndChild();
    ImGui::PopStyleColor();
}

}
}
