/** @file Shell.hpp
 *  @brief Declares the window's frame: a sidebar of screen names and the pane beside it.
 *  @author Mustafa Garip
 */

#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the application frame and routes to the screen the sidebar selects. */
class Shell
{
public:
    /** @brief Names the screens the sidebar offers. */
    Shell();

    /** @brief Draws one frame of the sidebar and the active screen's pane. */
    void draw();

    /** @brief Returns the name of the screen the sidebar currently selects. */
    const std::string& active_screen() const;

private:
    /** @brief Draws the sidebar and records the screen the user selects. */
    void draw_sidebar();

    /** @brief Draws the pane the active screen owns. */
    void draw_pane();

    /** @brief Holds the screen names in the order the sidebar lists them. */
    std::vector<std::string> screen_names_;

    /** @brief Holds the index into screen_names_ of the screen being drawn. */
    std::size_t active_index_;
};

}
}
