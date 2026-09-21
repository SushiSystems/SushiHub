/** @file RunLog.hpp
 *  @brief Declares which run the activity strip follows and what it is labelled.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/CommandRun.hpp"

#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Points at the run the strip reports, without owning it. */
class RunLog
{
public:
    /**
     * @brief Makes @p run the run the strip follows, under @p label.
     * @param run Stays owned by the workspace or the screen that started it.
     */
    void adopt(CommandRun& run, std::string label);

    /** @brief Reports whether a run has been adopted. */
    bool has_run() const;

    /**
     * @brief Returns the adopted run.
     * @pre has_run()
     */
    CommandRun& run();

    /** @brief Returns the command line the bar shows. */
    const std::string& label() const;

private:
    /** @brief Points at the adopted run, null until the first adoption. */
    CommandRun* run_ = nullptr;

    /** @brief Holds the command line the bar shows. */
    std::string label_;
};

}
}
