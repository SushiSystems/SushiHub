/** @file Browser.hpp
 *  @brief Declares the one call that hands a link to whatever the desktop opens links with.
 *  @author Mustafa Garip
 */

#pragma once

#include <string>

namespace SushiHub
{
namespace Gui
{

/**
 * @brief Opens @p url in the desktop's registered handler for it.
 * @param url An absolute link; it is never passed through a shell.
 * @return Whether the desktop accepted the request, which is not whether a page appeared.
 */
bool open_in_browser(const std::string& url);

}
}
