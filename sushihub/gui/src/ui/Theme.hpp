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

/** @brief Returns the colour the window and every screen region sit on. */
ImVec4 ground();

/** @brief Returns the colour the navigation rail sits on. */
ImVec4 rail();

/** @brief Returns the colour a card and a frame sit on. */
ImVec4 panel();

/** @brief Returns the colour a card that is hovered or selected sits on. */
ImVec4 panel_raised();

/** @brief Returns the colour a border and a separator are drawn in. */
ImVec4 line();

/** @brief Returns the colour a divider inside a card is drawn in. */
ImVec4 line_soft();

/** @brief Returns the colour body text is drawn in. */
ImVec4 ink();

/** @brief Returns the colour a label and a secondary line are drawn in. */
ImVec4 ink_dim();

/** @brief Returns the colour the faintest text, an absent state included, is drawn in. */
ImVec4 ink_faint();

/** @brief Returns the colour the active entry and the primary action carry. */
ImVec4 accent();

/** @brief Returns the colour text on an accent fill is drawn in. */
ImVec4 accent_ink();

/** @brief Returns the colour an accent fill that must stay quiet carries. */
ImVec4 accent_soft();

/** @brief Returns the colour a ready or successful state is drawn in. */
ImVec4 ok();

/** @brief Returns the colour a state that needs attention is drawn in. */
ImVec4 warn();

/** @brief Returns the colour a failed or missing state is drawn in. */
ImVec4 critical();

/** @brief Returns the colour an informational state is drawn in. */
ImVec4 info();

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
