/** @file RunLog.cpp
 *  @brief Defines the adoption of a run and the reads the activity strip makes.
 *  @author Mustafa Garip
 */

#include "model/RunLog.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

void RunLog::adopt(CommandRun& run, std::string label)
{
    run_ = &run;
    label_ = std::move(label);
}

bool RunLog::has_run() const
{
    return run_ != nullptr;
}

CommandRun& RunLog::run()
{
    return *run_;
}

const std::string& RunLog::label() const
{
    return label_;
}

}
}
