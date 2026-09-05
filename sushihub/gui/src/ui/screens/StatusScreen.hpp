/** @file StatusScreen.hpp
 *  @brief Declares the screen that draws what `ss status` reports about the workspace.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/Workspace.hpp"
#include "ui/widgets/PromptDialog.hpp"

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the tables, the dependency line and the Refresh button of the status run. */
class StatusScreen
{
public:
    /** @brief Binds the screen to the workspace whose `status` run it draws. */
    explicit StatusScreen(Workspace& workspace);

    /** @brief Draws one frame of the screen. */
    void draw();

private:
    /** @brief Draws where the dependency tree sits, as the result payload reports it. */
    void draw_dependencies(const RunState& state);

    /** @brief References the workspace the run is asked from. */
    Workspace& workspace_;

    /** @brief Collects the answer to a question the run stops on. */
    Widgets::PromptDialog prompt_;
};

}
}
