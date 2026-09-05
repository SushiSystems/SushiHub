/** @file DependenciesScreen.cpp
 *  @brief Defines the doctor table's dimming rule and the install its rows offer.
 *  @author Mustafa Garip
 */

#include "ui/screens/DependenciesScreen.hpp"

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
constexpr const char* SCREEN = "doctor";

/** @brief Holds the heading of the column that carries a component's status. */
constexpr const char* STATUS_COLUMN = "Status";

/** @brief Holds the status of a component no present module asks for. */
constexpr const char* NOT_NEEDED = "NOT NEEDED";

/** @brief Holds the status of a component that is asked for and is not there. */
constexpr const char* MISSING = "MISSING";

/** @brief Holds the command that provisions what the modules declare. */
constexpr const char* INSTALL_COMMAND = "install";

/** @brief Returns @p row's cell at @p index, empty when the row is shorter than that. */
std::string cell_at(const std::vector<std::string>& row, std::size_t index)
{
    return index < row.size() ? row[index] : std::string();
}

}

DependenciesScreen::DependenciesScreen(Workspace& workspace, FormOpener& forms)
    : workspace_(workspace),
      forms_(forms)
{
}

void DependenciesScreen::draw()
{
    CommandRun& run = workspace_.run_for(SCREEN);
    run.poll();
    const RunState& state = run.state();

    const bool refresh = ImGui::Button("Run doctor again");
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted("Dimmed rows are what no present module asks for.");
    ImGui::PopStyleColor();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (std::size_t index = 0; index < state.tables.size(); ++index)
    {
        const TableEvent& table = state.tables[index];
        const std::size_t status_column = Widgets::column_index(table, STATUS_COLUMN);

        Widgets::TableDecoration decoration;
        decoration.emphasis = [status_column](const std::vector<std::string>& row)
        {
            return emphasis_of(row, status_column);
        };
        decoration.action_column = "Fix";
        decoration.action = [this, status_column](const std::vector<std::string>& row)
        {
            draw_row_action(row, status_column);
        };

        const std::string id = "##sushihub_gui_doctor_table_" + std::to_string(index);
        Widgets::draw_table(id.c_str(), table, decoration);
    }

    Widgets::draw_event_log("##sushihub_gui_doctor_log", state, 0.0F);

    if (refresh)
    {
        workspace_.refresh(SCREEN);
    }
}

Widgets::RowEmphasis DependenciesScreen::emphasis_of(const std::vector<std::string>& row,
                                                     std::size_t status_column)
{
    return cell_at(row, status_column) == NOT_NEEDED ? Widgets::RowEmphasis::dimmed
                                                     : Widgets::RowEmphasis::normal;
}

void DependenciesScreen::draw_row_action(const std::vector<std::string>& row,
                                         std::size_t status_column)
{
    if (cell_at(row, status_column) != MISSING)
    {
        return;
    }

    if (ImGui::SmallButton("Install"))
    {
        forms_.open_form(INSTALL_COMMAND, {});
    }
}

}
}
