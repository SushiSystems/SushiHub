/** @file ProjectsScreen.hpp
 *  @brief Declares the screen that stands in until `ss projects` exists.
 *  @author Mustafa Garip
 */

#pragma once

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the empty state that names the wave the projects command arrives with. */
class ProjectsScreen
{
public:
    /** @brief Draws one frame of the screen. */
    void draw();
};

}
}
