/** @file Theme.hpp
 *  @brief Declares the one place the application's palette, rounding and spacing are set.
 *  @author Mustafa Garip
 */

#pragma once

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

}
}
}
