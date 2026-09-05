/** @file ModulesScreen.hpp
 *  @brief Declares the screen that turns each status row into an Add or an Update.
 *  @author Mustafa Garip
 */

#pragma once

#include "model/Workspace.hpp"
#include "ui/FormOpener.hpp"
#include "ui/widgets/TableView.hpp"

#include <string>
#include <vector>

namespace SushiHub
{
namespace Gui
{

/** @brief Draws the module rows of the status run with the command each row can be given. */
class ModulesScreen
{
public:
    /**
     * @brief Binds the screen to the workspace it reads and the shell it opens forms through.
     * @param forms The seam an Add or an Update button asks for a pre-filled form.
     */
    ModulesScreen(Workspace& workspace, FormOpener& forms);

    /** @brief Draws one frame of the screen. */
    void draw();

private:
    /** @brief Draws the Add and Update buttons that end @p row, keyed by the module it names. */
    void draw_row_actions(const TableEvent& table, const std::vector<std::string>& row);

    /** @brief References the workspace the status run is asked from. */
    Workspace& workspace_;

    /** @brief References the seam a row's button opens a form through. */
    FormOpener& forms_;
};

}
}
