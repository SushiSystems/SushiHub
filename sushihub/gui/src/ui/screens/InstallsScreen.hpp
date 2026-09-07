/** @file InstallsScreen.hpp
 *  @brief Declares the screen that draws sushiengine's and Sushi Hub's own install cards.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunLog.hpp"
#include "model/Workspace.hpp"
#include "ui/Screen.hpp"

#include <nlohmann/json.hpp>

#include <memory>
#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws one card for sushiengine and one for Sushi Hub itself, each with its actions. */
class InstallsScreen : public Screen
{
public:
    /** @brief Binds the screen to the workspace its runs are asked from and the strip's log. */
    InstallsScreen(Workspace& workspace, RunLog& run_log);

    /** @brief Returns the name the rail shows this destination under. */
    const char* name() const override;

    /** @brief Draws one frame of the screen. */
    void draw() override;

private:
    /** @brief Draws sushiengine's card from @p module, or a reading line when it has not arrived. */
    void draw_engine_card(const nlohmann::json* module);

    /** @brief Draws Sushi Hub's own card from @p module, or a reading line when it has not arrived. */
    void draw_hub_card(const nlohmann::json* module);

    /** @brief Draws a title row carrying @p title and, when @p presence is not empty, its chip. */
    void draw_title(const char* title, const std::string& presence);

    /** @brief Draws a four-cell definition grid of label and value pairs. */
    void draw_fields(const std::vector<std::pair<const char*, std::string>>& fields);

    /** @brief Draws @p labels as buttons right-aligned in the card, starting @p argv on a click. */
    void draw_actions(const std::vector<std::pair<std::string, std::vector<std::string>>>& actions);

    /** @brief Starts @p argv under @p label and hands the run to the activity strip. */
    void start_action(std::vector<std::string> argv, std::string label);

    /** @brief References the workspace the status and licence runs are asked from. */
    Workspace& workspace_;

    /** @brief References the strip's log every action adopts its run into. */
    RunLog& run_log_;

    /** @brief Owns the run the most recently pressed action started. */
    std::unique_ptr<CommandRun> action_run_;
};

}
}
