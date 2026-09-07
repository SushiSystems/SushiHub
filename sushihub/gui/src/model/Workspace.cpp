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

namespace
{

/** @brief Pairs a screen with the arguments its run follows `--json` with. */
struct ScreenCommand
{
    /** @brief Holds the screen name the run is kept under. */
    const char* screen;

    /** @brief Holds the subcommand and whatever follows it, in command-line order. */
    std::vector<std::string> arguments;
};

/** @brief Returns the screens whose run is not the subcommand of the same name. */
const std::vector<ScreenCommand>& screen_commands()
{
    static const std::vector<ScreenCommand> table{{"projects", {"projects", "list"}}};
    return table;
}

}

Workspace::Workspace(std::string hub_executable)
    : hub_executable_(std::move(hub_executable))
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
    return hub_executable_;
}

std::vector<std::string> Workspace::argv_for(std::string_view screen) const
{
    std::vector<std::string> argv{hub_executable_, "--json"};

    for (const ScreenCommand& entry : screen_commands())
    {
        if (screen == entry.screen)
        {
            argv.insert(argv.end(), entry.arguments.begin(), entry.arguments.end());
            return argv;
        }
    }

    argv.push_back(std::string(screen));
    return argv;
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
