/** @file NavRail.hpp
 *  @brief Declares the left rail that lists the window's destinations and holds the chosen one.
 *  @author Mustafa Garip
 */

#pragma once

#include <cstddef>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws one entry per destination and reports which one the user picked. */
class NavRail
{
public:
    /**
     * @brief Draws @p names as entries and marks the one @p active indexes.
     * @param active Read for the marked entry and written with the entry the user clicks.
     * @return Whether @p active changed during this frame.
     */
    bool draw(const std::vector<const char*>& names, std::size_t& active);

    /** @brief Returns the rail's width in pixels at the current font size. */
    static float width();
};

}
}
