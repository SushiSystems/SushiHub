/** @file ActivityStrip.hpp
 *  @brief Declares the bar along the bottom of the window where every run reports.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunLog.hpp"

namespace SushiHub
{
namespace Gui
{
namespace Widgets
{

/** @brief Draws the adopted run as one line and, when opened, as a log of its events. */
class ActivityStrip
{
public:
    /**
     * @brief Draws one frame of the strip over the run @p log follows.
     * @param log Holds the run and its label; an empty log draws the idle line.
     */
    void draw(RunLog& log);

    /** @brief Returns the strip's current height in pixels, collapsed or expanded. */
    float height() const;

private:
    /** @brief Draws the single line: the caret, the label, the bar and the outcome. */
    void draw_summary(RunLog& log);

    /** @brief Records whether the event log under the summary line is shown. */
    bool expanded_ = false;
};

}
}
}
