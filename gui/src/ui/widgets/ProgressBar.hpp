/** @file ProgressBar.hpp
 *  @brief Declares the bar one progress event is drawn as.
 *  @author Mustafa Garip
 */

#pragma once

#include "contract/Event.hpp"

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/**
 * @brief Draws @p progress as a bar labelled with its step and its position in the run.
 * @param progress The latest step; its fraction is used when it carries one, its
 *        position among the steps otherwise.
 */
void draw_progress(const ProgressEvent& progress);

}
}
}
