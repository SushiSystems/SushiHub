/** @file ModulesScreen.cpp
 *  @brief Defines the module rows, the per-row buttons and the forms they open.
 *  @author Mustafa Garip
 */

#include "ui/screens/ModulesScreen.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"
#include "ui/widgets/ProgressBar.hpp"

#include <imgui.h>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the command this screen reads, which is also its key in the workspace. */
constexpr const char* SCREEN = "status";

/** @brief Holds the heading of the column that names a module. */
constexpr const char* MODULE_COLUMN = "Module";

/** @brief Holds the command that brings a module into the workspace. */
constexpr const char* ADD_COMMAND = "add";

/** @brief Holds the command that brings a present module up to date. */
constexpr const char* UPDATE_COMMAND = "update";

/** @brief Returns @p row's cell at @p index, empty when the row is shorter than that. */
std::string cell_at(const std::vector<std::string>& row, std::size_t index)
{
    return index < row.size() ? row[index] : std::string();
}

}

ModulesScreen::ModulesScreen(Workspace& workspace, FormOpener& forms)
    : workspace_(workspace),
      forms_(forms)
{
}

void ModulesScreen::draw()
{
    CommandRun& run = workspace_.run_for(SCREEN);
    run.poll();
    const RunState& state = run.state();

    const bool refresh = ImGui::Button("Refresh");
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted("A row's button opens that module's form, already filled in.");
    ImGui::PopStyleColor();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (std::size_t index = 0; index < state.tables.size(); ++index)
    {
        const TableEvent& table = state.tables[index];
        Widgets::TableDecoration decoration;
        decoration.action_column = "Command";
        decoration.action = [this, &table](const std::vector<std::string>& row)
        {
            draw_row_actions(table, row);
        };

        const std::string id = "##sushihub_gui_modules_table_" + std::to_string(index);
        Widgets::draw_table(id.c_str(), table, decoration);
    }

    Widgets::draw_event_log("##sushihub_gui_modules_log", state, 0.0F);

    if (refresh)
    {
        workspace_.refresh(SCREEN);
    }
}

void ModulesScreen::draw_row_actions(const TableEvent& table, const std::vector<std::string>& row)
{
    const std::size_t module_column = Widgets::column_index(table, MODULE_COLUMN);
    const std::string module = cell_at(row, module_column < table.columns.size() ? module_column
                                                                                : 0);
    if (module.empty())
    {
        return;
    }

    if (ImGui::SmallButton("Add"))
    {
        forms_.open_form(ADD_COMMAND, {module});
    }
    ImGui::SameLine();
    if (ImGui::SmallButton("Update"))
    {
        forms_.open_form(UPDATE_COMMAND, {module});
    }
}

}
}
