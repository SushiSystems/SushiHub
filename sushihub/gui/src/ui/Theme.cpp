/** @file Theme.cpp
 *  @brief Defines the palette every widget reads and the style it is applied to.
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
constexpr float CORNER_RADIUS = 4.0F;

/** @brief Holds how much of the font size the horizontal padding inside a frame takes. */
constexpr float FRAME_PADDING_X = 0.8F;

/** @brief Holds how much of the font size the vertical padding inside a frame takes. */
constexpr float FRAME_PADDING_Y = 0.5F;

/** @brief Builds an opaque colour from a hexadecimal 0xRRGGBB literal. */
ImVec4 from_hex(unsigned int rgb)
{
    return ImVec4(static_cast<float>((rgb >> 16) & 0xFFU) / 255.0F,
                  static_cast<float>((rgb >> 8) & 0xFFU) / 255.0F,
                  static_cast<float>(rgb & 0xFFU) / 255.0F,
                  1.0F);
}

}

void apply()
{
    ImGuiStyle& style = ImGui::GetStyle();

    style.WindowRounding = 0.0F;
    style.ChildRounding = CORNER_RADIUS;
    style.FrameRounding = CORNER_RADIUS;
    style.PopupRounding = CORNER_RADIUS;
    style.ScrollbarRounding = CORNER_RADIUS;
    style.GrabRounding = CORNER_RADIUS;
    style.TabRounding = CORNER_RADIUS;

    const float font_size = ImGui::GetFontSize();

    style.WindowPadding = ImVec2(14.0F, 14.0F);
    style.FramePadding = ImVec2(font_size * FRAME_PADDING_X, font_size * FRAME_PADDING_Y);
    style.ItemSpacing = ImVec2(10.0F, 8.0F);
    style.WindowBorderSize = 0.0F;
    style.ChildBorderSize = 1.0F;

    ImVec4* colours = style.Colors;
    colours[ImGuiCol_WindowBg] = ground();
    colours[ImGuiCol_ChildBg] = ground();
    colours[ImGuiCol_PopupBg] = panel();
    colours[ImGuiCol_Border] = line();
    colours[ImGuiCol_Text] = ink();
    colours[ImGuiCol_TextDisabled] = ink_faint();
    colours[ImGuiCol_FrameBg] = panel();
    colours[ImGuiCol_FrameBgHovered] = panel_raised();
    colours[ImGuiCol_FrameBgActive] = panel_raised();
    colours[ImGuiCol_Header] = panel_raised();
    colours[ImGuiCol_HeaderHovered] = panel_raised();
    colours[ImGuiCol_HeaderActive] = accent_soft();
    colours[ImGuiCol_Button] = panel();
    colours[ImGuiCol_ButtonHovered] = panel_raised();
    colours[ImGuiCol_ButtonActive] = accent_soft();
    colours[ImGuiCol_Separator] = line();
    colours[ImGuiCol_TitleBg] = rail();
    colours[ImGuiCol_TitleBgActive] = rail();
    colours[ImGuiCol_ScrollbarBg] = ground();
    colours[ImGuiCol_ScrollbarGrab] = line();
    colours[ImGuiCol_TableHeaderBg] = panel();
    colours[ImGuiCol_TableBorderLight] = line_soft();
    colours[ImGuiCol_TableBorderStrong] = line();
}

float sidebar_width()
{
    return SIDEBAR_WIDTH;
}

float corner_radius()
{
    return CORNER_RADIUS;
}

ImVec4 ground()
{
    return from_hex(0x101317U);
}

ImVec4 rail()
{
    return from_hex(0x0B0D10U);
}

ImVec4 panel()
{
    return from_hex(0x171B21U);
}

ImVec4 panel_raised()
{
    return from_hex(0x1D222AU);
}

ImVec4 line()
{
    return from_hex(0x272D36U);
}

ImVec4 line_soft()
{
    return from_hex(0x1F242CU);
}

ImVec4 ink()
{
    return from_hex(0xDFE4EAU);
}

ImVec4 ink_dim()
{
    return from_hex(0x8A95A3U);
}

ImVec4 ink_faint()
{
    return from_hex(0x626D7BU);
}

ImVec4 accent()
{
    return from_hex(0xEF7A55U);
}

ImVec4 accent_ink()
{
    return from_hex(0x1A0F0AU);
}

ImVec4 accent_soft()
{
    return from_hex(0x3A2018U);
}

ImVec4 ok()
{
    return from_hex(0x5FAE86U);
}

ImVec4 warn()
{
    return from_hex(0xD3A244U);
}

ImVec4 critical()
{
    return from_hex(0xCF5F61U);
}

ImVec4 info()
{
    return from_hex(0x6F9FD0U);
}

ImVec4 level_colour(std::string_view level)
{
    if (level == "success")
    {
        return ok();
    }
    if (level == "warn")
    {
        return warn();
    }
    if (level == "error")
    {
        return critical();
    }
    return ink();
}

ImVec4 dimmed_colour()
{
    return ink_dim();
}

ImVec4 accent_colour()
{
    return accent();
}

}
}
}
