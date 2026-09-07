/** @file Screen.hpp
 *  @brief Declares the interface every destination in the rail implements.
 *  @author Mustafa Garip
 */

#pragma once

namespace SushiHub
{
namespace Gui
{

/** @brief Draws one destination of the window and names itself for the rail. */
class Screen
{
public:
    virtual ~Screen() = default;

    /** @brief Returns the name the rail shows this destination under. */
    virtual const char* name() const = 0;

    /** @brief Draws one frame of the screen into the region the shell has opened. */
    virtual void draw() = 0;
};

}
}
