/** @file Theme.cpp
 *  @brief Defines the dark palette, the corner rounding and the spacing.
 *  @author Mustafa Garip
 */

#include "ui/Theme.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{
namespace Theme
{

namespace
{

/** @brief Holds the width in pixels the sidebar keeps at every window size. */
constexpr float SIDEBAR_WIDTH = 220.0F;

/** @brief Holds the radius in pixels every rounded corner shares. */
constexpr float CORNER_RADIUS = 6.0F;

/** @brief Builds an opaque colour from three channel values in the zero-to-one range. */
ImVec4 opaque(float red, float green, float blue)
{
    return ImVec4(red, green, blue, 1.0F);
}

}

void apply()
{
    ImGuiStyle& style = ImGui::GetStyle();

    style.WindowRounding = CORNER_RADIUS;
    style.ChildRounding = CORNER_RADIUS;
    style.FrameRounding = CORNER_RADIUS;
    style.PopupRounding = CORNER_RADIUS;
    style.ScrollbarRounding = CORNER_RADIUS;
    style.GrabRounding = CORNER_RADIUS;
    style.TabRounding = CORNER_RADIUS;

    style.WindowPadding = ImVec2(14.0F, 14.0F);
    style.FramePadding = ImVec2(10.0F, 6.0F);
    style.ItemSpacing = ImVec2(10.0F, 8.0F);
    style.WindowBorderSize = 0.0F;
    style.ChildBorderSize = 1.0F;

    ImVec4* colours = style.Colors;
    colours[ImGuiCol_WindowBg] = opaque(0.086F, 0.090F, 0.106F);
    colours[ImGuiCol_ChildBg] = opaque(0.110F, 0.114F, 0.133F);
    colours[ImGuiCol_PopupBg] = opaque(0.110F, 0.114F, 0.133F);
    colours[ImGuiCol_Border] = opaque(0.180F, 0.188F, 0.216F);
    colours[ImGuiCol_Text] = opaque(0.878F, 0.886F, 0.910F);
    colours[ImGuiCol_TextDisabled] = opaque(0.451F, 0.463F, 0.502F);
    colours[ImGuiCol_FrameBg] = opaque(0.149F, 0.157F, 0.184F);
    colours[ImGuiCol_FrameBgHovered] = opaque(0.196F, 0.204F, 0.243F);
    colours[ImGuiCol_FrameBgActive] = opaque(0.235F, 0.247F, 0.294F);
    colours[ImGuiCol_Header] = opaque(0.184F, 0.318F, 0.518F);
    colours[ImGuiCol_HeaderHovered] = opaque(0.220F, 0.376F, 0.604F);
    colours[ImGuiCol_HeaderActive] = opaque(0.259F, 0.435F, 0.690F);
    colours[ImGuiCol_Button] = opaque(0.176F, 0.184F, 0.220F);
    colours[ImGuiCol_ButtonHovered] = opaque(0.220F, 0.376F, 0.604F);
    colours[ImGuiCol_ButtonActive] = opaque(0.259F, 0.435F, 0.690F);
    colours[ImGuiCol_Separator] = opaque(0.180F, 0.188F, 0.216F);
    colours[ImGuiCol_TitleBg] = opaque(0.086F, 0.090F, 0.106F);
    colours[ImGuiCol_TitleBgActive] = opaque(0.110F, 0.114F, 0.133F);
    colours[ImGuiCol_ScrollbarBg] = opaque(0.086F, 0.090F, 0.106F);
    colours[ImGuiCol_ScrollbarGrab] = opaque(0.196F, 0.204F, 0.243F);
    colours[ImGuiCol_TableHeaderBg] = opaque(0.149F, 0.157F, 0.184F);
    colours[ImGuiCol_TableBorderLight] = opaque(0.180F, 0.188F, 0.216F);
    colours[ImGuiCol_TableBorderStrong] = opaque(0.220F, 0.231F, 0.267F);
}

float sidebar_width()
{
    return SIDEBAR_WIDTH;
}

float corner_radius()
{
    return CORNER_RADIUS;
}

}
}
}
