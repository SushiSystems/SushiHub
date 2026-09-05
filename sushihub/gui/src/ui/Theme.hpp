/** @file Theme.hpp
 *  @brief Declares the one place the application's palette, rounding and spacing are set.
 *  @author Mustafa Garip
 */

#pragma once

#include <imgui.h>

#include <string_view>

namespace SushiHub
{
namespace Gui
{
namespace Theme
{

/** @brief Applies the dark palette, the corner rounding and the spacing to the current style. */
void apply();

/** @brief Returns the width in pixels the sidebar keeps at every window size. */
float sidebar_width();

/** @brief Returns the radius in pixels every rounded corner shares. */
float corner_radius();

/**
 * @brief Returns the colour a message carries by its severity.
 * @param level One of info, success, warn or error; anything else reads as info.
 */
ImVec4 level_colour(std::string_view level);

/** @brief Returns the colour text that is present but not worth reading is drawn in. */
ImVec4 dimmed_colour();

/** @brief Returns the colour a heading and a section title are drawn in. */
ImVec4 accent_colour();

}
}
}
