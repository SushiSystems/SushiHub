/** @file ModulesScreen.hpp
 *  @brief Declares the screen that lists what `hub status` reports about each module.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/Workspace.hpp"
#include "ui/FormOpener.hpp"
#include "ui/Screen.hpp"

#include <nlohmann/json.hpp>

#include <string_view>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws one row per module, its presence, its detail line and its one action. */
class ModulesScreen final : public Screen
{
public:
    /**
     * @brief Binds the screen to the workspace it reads and the seam a row's action opens a
     *        form through; the form itself reports its run to the strip once it is submitted.
     */
    ModulesScreen(Workspace& workspace, FormOpener& forms);

    /** @brief Returns the name the rail shows this destination under. */
    const char* name() const override;

    /** @brief Draws one frame of the screen. */
    void draw() override;

private:
    /** @brief Draws one module's row from its entry in the status payload. */
    void draw_row(const nlohmann::json& module);

    /** @brief Draws the presence chip a row and an install card both use. */
    void draw_presence_chip(std::string_view presence);

    /** @brief Draws the one action a module's presence calls for: Clone, Update or Details. */
    void draw_row_action(const nlohmann::json& module, std::string_view presence);

    /** @brief Draws what the next clone would provision, when the payload reports anything to. */
    void draw_provision_note(const nlohmann::json& payload);

    /** @brief References the workspace the status run is asked from. */
    Workspace& workspace_;

    /** @brief References the seam a row's action opens a form through. */
    FormOpener& forms_;
};

}
}
