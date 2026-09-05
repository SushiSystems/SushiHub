/** @file ProjectsScreen.cpp
 *  @brief Defines the projects table, the add form, and the editor a row opens.
 *  @author Mustafa Garip
 */

#include "ui/screens/ProjectsScreen.hpp"

#include "ui/Theme.hpp"
#include "ui/widgets/EventLog.hpp"
#include "ui/widgets/ProgressBar.hpp"

#include <imgui.h>

#include <algorithm>
#include <utility>

namespace SushiHub
{
namespace Gui
{

namespace
{

/** @brief Holds the screen this run is kept under, which the workspace maps to the listing. */
constexpr const char* SCREEN = "projects";

/** @brief Holds the subcommand every change to the registry goes through. */
constexpr const char* PROJECTS_COMMAND = "projects";

/** @brief Holds the subcommand that registers a directory. */
constexpr const char* ADD_COMMAND = "add";

/** @brief Holds the subcommand that drops a name from the registry. */
constexpr const char* REMOVE_COMMAND = "remove";

/** @brief Holds the option that lists a directory under something other than its own name. */
constexpr const char* NAME_OPTION = "--name";

/** @brief Holds the engine subcommand that opens one project. */
constexpr const char* EDITOR_COMMAND = "editor";

/** @brief Holds the option the editor takes the project directory under. */
constexpr const char* PROJECT_OPTION = "--project";

/** @brief Holds the heading of the column that names a project. */
constexpr const char* NAME_COLUMN = "Name";

/** @brief Holds the heading of the column that carries a project's directory. */
constexpr const char* PATH_COLUMN = "Path";

/** @brief Holds the heading of the column that says whether that directory is still there. */
constexpr const char* EXISTS_COLUMN = "Exists";

/** @brief Holds the cell of the Exists column that means the directory is still there. */
constexpr const char* PRESENT = "yes";

/** @brief Holds the key the result payload lists the projects under. */
constexpr const char* PROJECTS_KEY = "projects";

/** @brief Holds how much of the row the two fields of the add form leave to their labels. */
constexpr float LABEL_WIDTH = -220.0F;

/** @brief Returns @p row's cell at @p index, empty when the row is shorter than that. */
std::string cell_at(const std::vector<std::string>& row, std::size_t index)
{
    return index < row.size() ? row[index] : std::string();
}

/** @brief Reports whether @p row's directory is there; a table without the column says it is. */
bool is_present(const TableEvent& table, const std::vector<std::string>& row)
{
    const std::size_t column = Widgets::column_index(table, EXISTS_COLUMN);
    return column >= table.columns.size() || cell_at(row, column) == PRESENT;
}

/** @brief Returns the sentence a spawn that found no @p program is reported with. */
std::string spawn_failure(const char* program)
{
    return std::string(program) + " is not on the search path, so nothing was opened.";
}

}

ProjectsScreen::ProjectsScreen(Workspace& workspace)
    : workspace_(workspace)
{
}

ProjectsScreen::~ProjectsScreen()
{
    for (Editor& editor : editors_)
    {
        static_cast<void>(editor.process.release());
        static_cast<void>(editor.output.release());
    }
}

void ProjectsScreen::draw()
{
    collect_editors();

    CommandRun& run = workspace_.run_for(SCREEN);
    run.poll();
    const RunState& state = run.state();

    const bool refresh = ImGui::Button("Refresh");
    ImGui::SameLine();
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted("Open starts the engine on that row's directory; a dimmed row is gone.");
    ImGui::PopStyleColor();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (std::size_t index = 0; index < state.tables.size(); ++index)
    {
        const TableEvent& table = state.tables[index];
        Widgets::TableDecoration decoration;
        decoration.emphasis = [&table](const std::vector<std::string>& row)
        {
            return is_present(table, row) ? Widgets::RowEmphasis::normal
                                          : Widgets::RowEmphasis::dimmed;
        };
        decoration.action_column = "Project";
        decoration.action = [this, &table](const std::vector<std::string>& row)
        {
            draw_row_actions(table, row);
        };

        const std::string id = "##sushihub_gui_projects_table_" + std::to_string(index);
        Widgets::draw_table(id.c_str(), table, decoration);
    }

    draw_empty_state(state);
    draw_add_form();
    draw_action();

    if (!editor_error_.empty())
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour("error"));
        ImGui::TextWrapped("%s", editor_error_.c_str());
        ImGui::PopStyleColor();
    }

    Widgets::draw_event_log("##sushihub_gui_projects_log", state, 0.0F);

    const bool changed = adopt_action();
    if (refresh || changed)
    {
        workspace_.refresh(SCREEN);
    }
}

void ProjectsScreen::draw_add_form()
{
    ImGui::PushStyleColor(ImGuiCol_Text, Theme::accent_colour());
    ImGui::SeparatorText("Add a project");
    ImGui::PopStyleColor();

    ImGui::SetNextItemWidth(LABEL_WIDTH);
    ImGui::InputText("Path", path_.data(), path_.size());
    ImGui::SetNextItemWidth(LABEL_WIDTH);
    ImGui::InputText("Name", name_.data(), name_.size());

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted("A name left empty lists the directory under its own name.");
    ImGui::PopStyleColor();

    const bool typed = path_[0] != '\0';
    const bool busy = action_ != nullptr && !action_->state().finished;

    ImGui::BeginDisabled(!typed || busy);
    if (ImGui::Button("Add"))
    {
        std::vector<std::string> argv{workspace_.executable(), "--json", PROJECTS_COMMAND,
                                      ADD_COMMAND};
        if (name_[0] != '\0')
        {
            argv.push_back(NAME_OPTION);
            argv.push_back(std::string(name_.data()));
        }
        argv.push_back(std::string(path_.data()));
        start_action(std::move(argv));
    }
    ImGui::EndDisabled();

    if (!typed)
    {
        ImGui::SameLine();
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour("warn"));
        ImGui::TextUnformatted("A project needs a directory.");
        ImGui::PopStyleColor();
    }
}

void ProjectsScreen::draw_empty_state(const RunState& state)
{
    if (!state.result.has_value() || !state.tables.empty())
    {
        return;
    }

    const nlohmann::json& payload = state.result->payload;
    const auto projects = payload.find(PROJECTS_KEY);
    if (projects == payload.end() || !projects->is_array() || !projects->empty())
    {
        return;
    }

    ImGui::PushStyleColor(ImGuiCol_Text, Theme::dimmed_colour());
    ImGui::TextUnformatted("Nothing is registered yet. The form below takes the first directory.");
    ImGui::PopStyleColor();
}

void ProjectsScreen::draw_row_actions(const TableEvent& table,
                                      const std::vector<std::string>& row)
{
    const std::string name = cell_at(row, Widgets::column_index(table, NAME_COLUMN));
    const std::string path = cell_at(row, Widgets::column_index(table, PATH_COLUMN));
    const bool busy = action_ != nullptr && !action_->state().finished;

    if (!path.empty() && is_present(table, row))
    {
        if (ImGui::SmallButton("Open"))
        {
            open_editor(path);
        }
        ImGui::SameLine();
    }

    if (name.empty())
    {
        return;
    }

    ImGui::BeginDisabled(busy);
    if (ImGui::SmallButton("Remove"))
    {
        start_action({workspace_.executable(), "--json", PROJECTS_COMMAND, REMOVE_COMMAND, name});
    }
    ImGui::EndDisabled();
}

void ProjectsScreen::draw_action()
{
    if (action_ == nullptr)
    {
        return;
    }

    action_->poll();
    const RunState& state = action_->state();

    if (state.progress.has_value() && !state.finished)
    {
        Widgets::draw_progress(*state.progress);
    }

    for (const LineEvent& line : state.lines)
    {
        ImGui::PushStyleColor(ImGuiCol_Text, Theme::level_colour(line.level));
        ImGui::TextWrapped("%s", line.message.c_str());
        ImGui::PopStyleColor();
    }
}

void ProjectsScreen::start_action(std::vector<std::string> argv)
{
    action_ = std::unique_ptr<CommandRun>(new CommandRun(std::move(argv)));
    action_adopted_ = false;
    action_->start();
}

bool ProjectsScreen::adopt_action()
{
    if (action_ == nullptr || action_adopted_ || !action_->state().finished)
    {
        return false;
    }

    action_adopted_ = true;
    return true;
}

void ProjectsScreen::open_editor(const std::string& path)
{
    Editor editor;
    editor.output = std::unique_ptr<LineQueue>(new LineQueue());
    editor.process = Process::start({ENGINE_EXECUTABLE, EDITOR_COMMAND, PROJECT_OPTION, path},
                                    *editor.output);

    if (editor.process == nullptr)
    {
        editor_error_ = spawn_failure(ENGINE_EXECUTABLE);
        return;
    }

    editor_error_.clear();
    editors_.push_back(std::move(editor));
}

void ProjectsScreen::collect_editors()
{
    std::string dropped;
    for (Editor& editor : editors_)
    {
        while (editor.output->try_pop(dropped))
        {
        }
    }

    const auto exited = [](const Editor& editor)
    {
        return !editor.process->running();
    };
    editors_.erase(std::remove_if(editors_.begin(), editors_.end(), exited), editors_.end());
}

}
}
