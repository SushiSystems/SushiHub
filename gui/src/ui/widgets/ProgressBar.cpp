/** @file ProgressBar.cpp
 *  @brief Defines the completed fraction a progress event is drawn with and its overlay.
 *  @author Mustafa Garip
 */

#include "ui/widgets/ProgressBar.hpp"

#include <imgui.h>

#include <algorithm>
#include <cfloat>
#include <string>

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

namespace
{

/** @brief Returns the completed fraction of @p progress, clamped to the drawable range. */
float completed_fraction(const ProgressEvent& progress)
{
    double fraction = 0.0;
    if (progress.fraction.has_value())
    {
        fraction = *progress.fraction;
    }
    else if (progress.count > 0)
    {
        fraction = static_cast<double>(progress.index) / static_cast<double>(progress.count);
    }
    return static_cast<float>(std::min(std::max(fraction, 0.0), 1.0));
}

/** @brief Returns the text drawn over the bar: the step and, when known, its position. */
std::string overlay_text(const ProgressEvent& progress)
{
    if (progress.count <= 0)
    {
        return progress.label;
    }
    return progress.label + " (" + std::to_string(progress.index) + "/" +
           std::to_string(progress.count) + ")";
}

}

void draw_progress(const ProgressEvent& progress)
{
    const std::string overlay = overlay_text(progress);
    ImGui::ProgressBar(completed_fraction(progress), ImVec2(-FLT_MIN, 0.0F), overlay.c_str());
}

}
}
}
