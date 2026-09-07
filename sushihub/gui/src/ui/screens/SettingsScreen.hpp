/** @file SettingsScreen.hpp
 *  @brief Declares the screen that carries the four machine settings and the doctor table.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/RunLog.hpp"
#include "model/Workspace.hpp"
#include "ui/Screen.hpp"
#include "ui/screens/DeviceGrant.hpp"
#include "ui/widgets/PromptDialog.hpp"

#include <functional>
#include <string>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the account, the workspace, the alias and the dependencies, and what doctor found. */
class SettingsScreen : public Screen
{
public:
    /**
     * @brief Binds the screen to the workspace its runs come from and the log they report through.
     * @param log Receives every run a row starts, so the activity strip follows it.
     */
    SettingsScreen(Workspace& workspace, RunLog& log);

    const char* name() const override;

    void draw() override;

private:
    /** @brief Draws what a row's control column holds. */
    using Control = std::function<void()>;

    /** @brief Draws one row: @p title over @p sentence, then @p value, then @p control. */
    void draw_row(const char* title, const char* sentence, const std::string& value,
                  const Control& control);

    /** @brief Draws the Sushi ID row and the sign-in or sign-out it offers. */
    void draw_account_row();

    /** @brief Draws the workspace row and the change that only `hub`'s own start makes. */
    void draw_workspace_row();

    /** @brief Draws the alias row and the toggle the installer, not this screen, acts on. */
    void draw_alias_row();

    /** @brief Draws the dependency count row and the provision it starts. */
    void draw_dependencies_row();

    /** @brief Draws the sign-in run's grant, its question and nothing else. */
    void draw_sign_in();

    /** @brief Draws @p grant's code at two and a half times the text size with its two buttons. */
    void draw_grant(const DeviceGrant& grant);

    /** @brief Draws every doctor row as an index, a dependency, a note and a coloured state. */
    void draw_doctor_table();

    /** @brief Starts @p command afresh and hands its run to the log under @p label. */
    void start(const char* command, std::string label);

    /** @brief References the workspace every run is asked from. */
    Workspace& workspace_;

    /** @brief References the log the strip reports this screen's runs through. */
    RunLog& log_;

    /** @brief Collects the answer to a question the sign-in stops on. */
    Widgets::PromptDialog prompt_;

    /** @brief Records that the sign-in run has been started at least once. */
    bool signing_in_ = false;

    /** @brief Holds what the alias toggle shows, which nothing yet reads back. */
    bool alias_enabled_ = true;
};

}
}
