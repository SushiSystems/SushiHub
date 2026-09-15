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
    /** @brief Holds one button of a card: its label and the program line it starts. */
    struct Action
    {
        /** @brief Holds the text the button shows. */
        const char* label;

        /** @brief Holds the program and arguments the button starts. */
        std::vector<std::string> argv;
    };

    /** @brief Starts the online status once the offline one has finished, and polls it. */
    void advance_update_check(const CommandRun& offline);

    /** @brief Returns the payload to draw: the online one once it arrives, else the offline one. */
    const nlohmann::json* current_payload(const CommandRun& offline) const;

    /** @brief Reports whether the online status has been started and has not answered yet. */
    bool checking() const;

    /** @brief Draws sushiengine's card from @p module, or a reading line when it has not arrived. */
    void draw_engine_card(const nlohmann::json* module, bool checked);

    /** @brief Draws Sushi Hub's own card from @p hub, or a reading line when it has not arrived. */
    void draw_hub_card(const nlohmann::json* hub, bool checked);

    /** @brief Draws a title row carrying @p title and, when @p presence is not empty, its chip. */
    void draw_title(const char* title, const std::string& presence);

    /** @brief Draws a dimmed "reading..." line under the title. */
    void draw_reading();

    /** @brief Draws a four-cell definition grid of label and value pairs. */
    void draw_fields(const std::vector<std::pair<const char*, std::string>>& fields);

    /** @brief Draws @p actions as buttons right-aligned in the card. */
    void draw_actions(const std::vector<Action>& actions);

    /** @brief Starts @p argv and hands the run to the activity strip. */
    void start_action(const std::vector<std::string>& argv);

    /** @brief References the workspace the offline status run is asked from. */
    Workspace& workspace_;

    /** @brief References the strip's log every run this screen starts is adopted into. */
    RunLog& run_log_;

    /** @brief Owns the `hub status --check-updates` run, null until the offline run finishes. */
    std::unique_ptr<CommandRun> update_check_;

    /** @brief Owns the run the most recently pressed action started. */
    std::unique_ptr<CommandRun> action_run_;
};

}
}
