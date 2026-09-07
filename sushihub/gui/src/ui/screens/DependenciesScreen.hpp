/** @file DependenciesScreen.hpp
 *  @brief Declares the screen that draws what `hub doctor` found and what it did not.
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

/** @brief Draws the doctor table with the rows nothing needs dimmed and the rest installable. */
class DependenciesScreen
{
public:
    /**
     * @brief Binds the screen to the workspace it reads and the shell it opens forms through.
     * @param forms The seam an Install button asks for the install form.
     */
    DependenciesScreen(Workspace& workspace, FormOpener& forms);

    /** @brief Draws one frame of the screen. */
    void draw();

private:
    /** @brief Returns the emphasis @p row is drawn with, given where its status sits. */
    static Widgets::RowEmphasis emphasis_of(const std::vector<std::string>& row,
                                            std::size_t status_column);

    /** @brief Draws the Install button that ends @p row, when that row wants one. */
    void draw_row_action(const std::vector<std::string>& row, std::size_t status_column);

    /** @brief References the workspace the doctor run is asked from. */
    Workspace& workspace_;

    /** @brief References the seam the Install button opens the install form through. */
    FormOpener& forms_;
};

}
}
