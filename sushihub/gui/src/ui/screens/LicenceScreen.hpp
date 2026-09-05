/** @file LicenceScreen.hpp
 *  @brief Declares the screen that shows who is signed in, what they hold, and how to sign in.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/Workspace.hpp"
#include "ui/screens/DeviceGrant.hpp"
#include "ui/widgets/PromptDialog.hpp"

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the whoami and licence runs and drives a sign-in through the device grant. */
class LicenceScreen
{
public:
    /** @brief Binds the screen to the workspace its three runs are asked from. */
    explicit LicenceScreen(Workspace& workspace);

    /** @brief Draws one frame of the screen. */
    void draw();

private:
    /** @brief Draws one read-only run under @p title: its tables, its lines, its progress. */
    void draw_report(const char* title, const char* screen);

    /** @brief Draws the sign-in button and, once it is pressed, the run it started. */
    void draw_sign_in();

    /** @brief Draws @p grant's code at twice the text size with the button that opens it. */
    void draw_grant(const DeviceGrant& grant);

    /** @brief References the workspace every run is asked from. */
    Workspace& workspace_;

    /** @brief Collects the answer to a question the sign-in stops on. */
    Widgets::PromptDialog prompt_;

    /** @brief Records that the sign-in run has been started at least once. */
    bool signing_in_ = false;
};

}
}
