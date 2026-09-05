/** @file Workspace.cpp
 *  @brief Defines the per-screen run cache and the argument vector each screen asks for.
 *  @author Mustafa Garip
 */

#include "model/Workspace.hpp"

#include <utility>

namespace SushiHub
{
namespace Gui
{

Workspace::Workspace(std::string ss_executable)
    : ss_executable_(std::move(ss_executable))
{
}

CommandRun& Workspace::run_for(std::string_view screen)
{
    const auto found = runs_.find(screen);
    if (found != runs_.end())
    {
        return *found->second;
    }
    return open(screen);
}

void Workspace::refresh(std::string_view screen)
{
    const auto found = runs_.find(screen);
    if (found != runs_.end())
    {
        runs_.erase(found);
    }
    open(screen);
}

const std::string& Workspace::executable() const
{
    return ss_executable_;
}

std::vector<std::string> Workspace::argv_for(std::string_view screen) const
{
    return {ss_executable_, "--json", std::string(screen)};
}

CommandRun& Workspace::open(std::string_view screen)
{
    auto run = std::unique_ptr<CommandRun>(new CommandRun(argv_for(screen)));
    run->start();

    const auto inserted = runs_.emplace(std::string(screen), std::move(run));
    return *inserted.first->second;
}

}
}
