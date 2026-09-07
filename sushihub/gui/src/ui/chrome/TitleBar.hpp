/** @file TitleBar.hpp
 *  @brief Declares the row at the top of the window that names the application and the workspace.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the application's identity, the open workspace and the signed-in account. */
class TitleBar
{
public:
    /**
     * @brief Draws one row carrying the name, @p workspace in a chip and @p account at the right.
     * @param workspace The path the window is open on, shown as it was given.
     * @param account The signed-in identity, or an empty string when nobody is signed in.
     */
    void draw(const std::string& workspace, const std::string& account);

    /** @brief Returns the row's height in pixels at the current font size. */
    static float height();
};

}
}
